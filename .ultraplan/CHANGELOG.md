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


---

## S09 — axes, legend, titles and reference lines

The largest cluster of silent failures in the package: options Stata's
`syntax` accepted, because they are declared `string asis`, arriving intact at
Python and having their contents thrown away by parsers that recognised two or
three keywords.

### The behaviour change everyone will notice

**A single-series plot no longer draws a legend.** Measured over 55 probes:
`twoway` draws a legend **if and only if the graph has two or more keys**. One
key, no legend, whatever else is passed — `legend(position(6))` on a one-key
plot draws nothing at all, and only `legend(on)` forces one. dash passed
`legend_label=<yvar>` from every glyph, so every single-series graph carried a
legend `twoway` would not draw.

Legend **keys** changed too. Stata labels a data series with the variable
LABEL, and fit layers with fixed text: `twoway (scatter mpg weight) (lfit mpg
weight)` keys read `["Mileage (mpg)", "Fitted values"]`, and `twoway lfitci`
reads `["95% CI", "Fitted values"]`. dash labelled everything with the raw
y-variable name, so a scatter and its own fit line merged into one key. The CI
key now carries the actual level, so `level(90)` reads "90% CI".

### Axis labelling: from three keywords to Stata's grammar

| form | before | after |
|---|---|---|
| `xlabel(#10)` | **0 ticks** | an adaptive ticker asked for 10 — Stata's `#N` is a *suggestion*, which is why it measures 8 on `weight` |
| `xlabel(minmax)` | **0 ticks** | 2, at the data bounds |
| `xlabel(none)` | 0 ticks *by accident* | 0 ticks *by intent*, and no gridlines, as measured |
| `xlabel(1990(5)2020)` | **0 ticks** | 7, at the right positions |
| `ylabel(, format(%9.0fc))` | nothing | thousands separators on the ticks |
| `xlabel(, labsize(large))` | nothing | a larger tick label |
| `xlabel(, grid)` / `nogrid` | nothing | gridlines on/off |
| `yscale(range(0 50))` | nothing | the axis range |
| `yscale(noextend)` / `alt` | silently dropped | reported |

The working range code that existed was keyed on `xrange`/`yrange` — keys
`dash.ado` has never emitted. A dead read is exactly what makes an option look
implemented, so they are gone and `range()` is wired instead.

### Text that was being mangled

- `title("My Title", size(large) color(red))` rendered the literal
  `My Title , size(large) color(red)`. `note("n=74", span)` rendered
  `"n=74", span`, quotes and all — the two differed because `title` is
  declared `string` and `note` is `string asis`. One parser now handles both,
  so they cannot diverge again, and `size()` and `color()` are applied.
- `title("R&D spend")` displayed as `R&amp;D spend`. Bokeh draws a figure
  title and axis labels as **canvas glyphs**, not HTML, so escaping them was
  the bug rather than the protection — `_axis_label` never escaped the
  variable labels it returns and was already correct. Verified with four XSS
  payloads that none appears literally in the output: Bokeh escapes model text
  again on its way into the embedded JSON.
- Under `layout(bs)`, `title("Price & Weight")` rendered `Price &amp; Weight`
  and an apostrophe rendered `&#x27;`. `render()` escaped the title and
  `_render_bootstrap_html` escaped it again. The title is now carried raw and
  escaped once, at each point of use.
- `note()` and `caption()` were both a `Label` at screen (0, 0) added
  `"below"` — drawn **on top of each other**. Measured: the note is ring(4)
  and the caption ring(5), so the caption sits below the note.

### Style options that reached nothing

- `xline(3000, lcolor(red) lpattern(solid))` — the sub-options were
  float-cast and discarded, forcing grey dashed. They are honoured, and the
  default is now **black** dashed, which is what Stata measures.
- `mlcolor()` did nothing while the marker border took its colour from
  `lcolor()`, the *connecting line* colour — wrong in both directions.
  `mlwidth()` is wired too.
- `fcolor(none)` painted an **opaque white blob**; it is transparent.
- `falpha()` — used nine times in `examples/comprehensive_demo.do` — was never
  read.
- `msymbol(Oh)`, `Sh`, `Dh` rendered **filled**: they mapped to Bokeh's
  `*_dot` markers. A hollow Stata marker is the solid shape with no fill.
- `msymbol(i)` and `msymbol(none)` drew a visible marker.
- `mlabgap(small)` threw and was silently dropped.
- **`colormissing(eltblue)` did not emit invalid CSS — it killed the whole
  render.** The value went to Bokeh untranslated, so any Stata colour name
  Bokeh does not happen to share raised out of the colour mapper and took the
  figure down with it.

### `if` qualifiers

`if !missing(rep78)`, `if inlist(rep78,1,2)` and `if rep78 < .` — the three
most common qualifier forms in real Stata code — all failed validation,
warned, and rendered the graph **unfiltered**. They now work, along with
`inrange()` and the `== .` / `>= .` missing idioms.

The AST whitelist that replaced a regex blacklist in commit `700e770` to close
an RCE is **unchanged**. The support is a translation applied *before*
validation, producing only comparisons and boolean combinators — node types
the validator already permitted. 18 adversarial expressions are rejected both
raw and after translation, per project rule 18.

### Two more

- The secondary axis range was computed from the **unfiltered** frame, so a
  qualified dual-axis graph's right-hand axis spanned data the graph does not
  show. It now comes from the active view.
- `hover()` was read by the renderer and **declared nowhere in `dash.ado`** —
  a dead read. Rather than delete it, the option is now declared and
  serialized, because the renderer's use of it (extra tooltip variables) is
  worth having.

### One place the plan's register was wrong

It said `map_line` sorts by x and then calls `_apply_mlabel_opts` with the
unsorted source, so "marker labels land on the wrong points". They do not:
each row of that source carries its own x, y and label together, so the
pairing was already correct. The real defect was narrower — the sorted source
dropped the label column, and the unsorted one still holds the NaN rows
`map_line` discarded, so labels appeared on points the line does not draw. The
label column is now carried across and the sorted source is used.

### Re-baselined

`test_single_y_output_matches_prefix_baseline` guards a single-y dashboard
against unintended change. Its digest moved because a single-series scatter no
longer draws a legend. The new digest is recorded with the reason in the test
file.


---

## S10 — figure geometry and layout sizing

### The starting point, measured

No generated dashboard contained a figure `width`, `height`, `frame_width` or
`aspect_ratio`: **67 Figure objects across 10 dashboards**, every one at
`sizing_mode="stretch_width"` and Bokeh's default height. There was no way —
by option, by scheme, or by data — for a user to influence plot proportions.

### `aspectratio()` was inverted

**Stata's `aspectratio()` is height/width. Bokeh's `aspect_ratio` is
width/height.** dash passed the value straight through, so every request came
out upside down: `aspectratio(0.5)` asks for a plot region half as tall as it
is wide, and dash drew one twice as tall as it is wide. Measured on a 600×600
export of a 6×6in graph: `aspectratio(0.25)` gives a plot region 542×152,
i.e. h/w = 0.28.

### What now sets a figure's proportions

Precedence, documented in `dash.sthlp`:

1. `xsize()` / `ysize()`, in inches. Either alone keeps the other from the
   scheme — `xsize(9)` under `stcolor` gives 4.5 × 9, as Stata does.
2. `aspectratio()`, with the reciprocal taken.
3. The active scheme's `graphsize x` / `graphsize y`. All 14 translated
   schemes carry Stata's own values, verified against Stata.

Proportions are carried as a **ratio**, not converted to fixed pixels:
pinning both dimensions would satisfy BR-10.1 and break BR-10.3, and BR-10.3
is the abstract's headline claim. The ratio is honoured within a height band
(`_MIN_FIGURE_HEIGHT` … `_MAX_FIGURE_HEIGHT`) so one square panel cannot fill
a whole screen, and a 10×2in panel on a phone does not collapse to a 73px
sliver — both measured.

### Layout

- The Bootstrap grid emitted **only an `md` breakpoint**, so a wide display
  was never used. The `.db-col-lg-*` CSS already existed and nothing emitted
  it. An `lg` tier is emitted now, and a narrow cell doubles up at `md` — four
  columns that work at 1440px are cramped at 768px.
- Graph row packing derives from each figure's **own** proportions: a panel
  wide enough to need a full row takes one, without pushing every other graph
  onto a row of its own.
- `_compute_grid`'s `ceil(sqrt(n))` stays as the default, now ratio-aware.
- The KPI-per-row limit is a named constant with a comment. Four per row is a
  legibility judgement, not a derivable quantity.
- Cell heights: a **graph** cell takes its height from the figure's ratio and
  carries no height class. Giving it a min-height left dead space — measured
  at 217px under a 10×2in panel in a full-width cell. A **KPI** card has no
  intrinsic height, so it keeps one, keyed to its span.

### Found by looking at it, which is the point of the section

**The dashboard had no `<meta name="viewport">`.** At an emulated 375px device
the page reported `window.innerWidth == 980`: a mobile browser lays out at its
980px default and zooms the whole page out to fit, so every breakpoint below
980 was unreachable on a phone and the text was unreadable. That is exactly
the claim the conference abstract makes. No structural assertion would have
caught it.

### Verified at three widths

`examples/geometry_responsive.do` (new) built from Stata and opened in a
browser at 375, 768 and 1440px. No horizontal scroll at any width; no cell
overlapping another; the wide panel wide and short and the square one square;
the whole dashboard usable on a phone. The procedure and the measured numbers
are recorded in `test/test_geometry_visual.md` so a later run has something to
compare against.

### Re-baselined

`test_single_y_output_matches_prefix_baseline` moved again: every figure now
carries an aspect ratio, and with no option given it comes from the scheme, so
every dashboard changes. The reason is recorded beside the digest.

---

## S11 — the renderer now consumes the translated schemes

Fourteen faithful scheme translations shipped in an earlier batch. Almost
nothing read them. Only *hue* varied across series: marker symbol, marker
size, line width, line pattern, fill intensity, the minor grid and the whole
legend were literals in the renderer, identical under every scheme.
`default_symbol()` and `default_line_pattern()` existed with **no call sites
at all** — they had been written to be unit-tested.

### Consumed now, with the key each value comes from

| drawn | scheme key | was |
|---|---|---|
| marker symbol | `symbol p#` | `"circle"` |
| marker size | `symbolsize p` | `8` |
| scatter alpha | `intensity p` | `0.7` |
| bar / histogram alpha | `intensity bar` | `0.8` |
| area alpha | `intensity area` | `0.5` |
| line width | `linewidth p` | `1.5` |
| line dash | `linepattern p#lineplot` | none |
| minor grid | `color minor_grid` | not drawn |
| legend background, border, label size | `color legend`, `color legend_line`, `gsize text` | Bokeh defaults |
| discrete `colorvar` palette | `color p1`–`p15` | Bokeh `Category10` |

A **mono** scheme is the one that shows how much this mattered: its whole
design is that the symbol and the dash distinguish the series, because the
colour does not. Colour schemes declare `circle` for every `p#`, so they are
unchanged — a fix that made every scheme cycle through symbols would have been
wrong.

### `p#lineplot` is not a fallback for `p#line`

Stata resolves a plain `twoway line` through
`linepattern p#lineplot → plineplot → p# → p`, while `linepattern p#line`
belongs to the **connecting line of `twoway connected`**. The first
implementation read `p#line`, which drew s2mono's three overlaid lines all
solid where Stata draws solid / dash / vshortdash. The obvious repair — try
`p#lineplot`, fall back to `p#line` — is wrong in the other direction:
s1mono and stmono1 declare a varied `p#line` cycle and no `lineplot` key, and
Stata draws their line plots solid. The chain is Stata's own, and it stops at
the shared `linepattern p`.

Two further traps, both now covered by tests:

- a **declared** `solid` translates to an empty dash list, so resolving the
  chain by truthiness treats it as absent and falls through to a dashed entry
  — which `scheme-s2gmanual.scheme` would trigger exactly;
- `color p#line` is likewise not the colour of a line plot. s1mono declares
  `color p#line black`; Stata draws #606060 / #a0a0a0 / #808080, and dash drew
  three identical black lines.

Of the fourteen schemes, **four** declare `lineplot` keys (s2mono and the
three that `#include` it: sj, stsj, stmono2). The other ten genuinely have
none, and say so in an HONEST GAPS section rather than carrying a guess.

### `_GSIZE_PT` disagreed with Stata

Six of its fourteen entries were wrong against Stata's own
`style/gsize-*.style` files, each of which states its point size in a comment:
tiny was 7pt against Stata's 4, vsmall 8 against 6, small 9 against 8, large
13 against 14, vlarge 15 against 16, huge 18 against 20. A scheme asking for
small text got a size Stata does not specify.

Marker sizes use the ratios from that corrected table with dash's own 8px
anchored at Stata's `medium` — which is what s2color asks for, so the default
dashboard is unchanged. Stata sizes a marker relative to a 4-inch-high graph,
which no browser has, so claiming absolute pixel fidelity here would have been
a fabrication.

### Scheme selection

- `SchemeParser.name` exists, so a caller can ask which scheme was actually
  used. Nothing could before, and a silent fallback was indistinguishable from
  a successful resolution.
- **`c(scheme)` is the default.** A Stata user has already chosen how their
  graphs look; dash was the one command in the session that ignored it.
  Precedence is `scheme()` → `theme()` → `c(scheme)` → s2color.
- `dash build` accepts `scheme()`. It only accepted `theme()`.
- A **graph-level** `scheme()` was parsed, escaped into `graph_options` and
  never read. It is honoured for the duration of that figure.
- An unknown `scheme()` or `theme()` is **reported**. Stata returns rc 0 with
  `note: scheme X not found, using s2color`, so dash does not abort either —
  but `theme(dark)`, which is documented in `dash.sthlp` and absent from the
  map, used to become s2color without a word. The message names the supported
  set.
- `dash.ado` stopped writing `"theme": "default"` when the user asked for no
  theme. `default` is a real theme name that resolves to s2color, so writing
  it made `c(scheme)` unreachable — a theme was always present.

### The scheme stylesheet was inert twice over

`css_block()` returned its own `<style>` element, and the Bootstrap head
embeds the result **inside another one**: measured, six `<style>` tokens with
one nested open, so CSS error recovery discarded the rule that followed it.
Its selectors were `.dash-title`, `.dash-subtitle` and `.kpi-card` while the
HTML emits `db-title`, `db-subtitle` and an unclassed KPI div, so all three
matched nothing even where the block was not nested.

`css_block()` now returns rules and `css_style_element()` wraps them; the KPI
card carries `db-kpi-card` in the initial render and in all four JS rebuild
paths; and the `layout(auto)` header gained the same classes the Bootstrap
one uses — it carried a hardcoded `#555` subtitle, so a scheme's title colour
reached one layout and not the other. A test now asserts mechanically that
every selector the block emits matches a class the document actually uses.

---

## Certification suite — it was reporting success while testing almost nothing

Not a planned section. Running the Stata suite to verify the KPI work turned
up that it printed `ALL TESTS PASSED (5 passed, 9 skipped)` while **nine of
fourteen scripts — every end-to-end one — had skipped**, and that the six
which then ran all failed.

### Why they skipped

Each Python-dependent script decided whether Python was available with
`capture python: pass`. That returns a nonzero rc inside the runner on a
machine where the very same session renders Bokeh output through `dash build`
seconds later. The guard now reads `c(python_exec)`, which is configuration
rather than execution and cannot fail for reasons unrelated to Python being
configured. A package check that genuinely must import something spends the
first call on a throwaway and retries.

On Apple silicon the suite must be run as `arch -arm64 stata-mp`: a long run
was observed launching the x86_64 slice, which then cannot load the arm64
`libpython`. Recorded in the runner's header.

### Why they failed once they ran

Every end-to-end script asked "does the dashboard contain this string?" by
reading the HTML line by line into a Stata local. A line of Bokeh output is
JSON dense with `"`, and sequences such as `"'` inside it terminate the
compound quotes the macro is expanded in — the document's own content was
being parsed as Stata code. Five scripts died with `too few quotes`, one with
`unknown function ()`, and the plain-quoted variant died with
`r(111) Security not found`, "Security" being a word from the page.

`test/cert_helpers.do` answers the question from Mata, where a line is a value
and nothing in it can be parsed as code, and exits 603 on a file it cannot
open — so a security check that reads no file now fails instead of reporting
"payload not found".

`test/test_cscript_hygiene.py` makes both classes of defect mechanical: no
script may decide Python's availability by running it, no macro holding a line
read from a file may be expanded in plain quotes, an import probe must retry,
and every `.cscript` must be wired into the runner.

### Four product defects the unmasked suite found

1. **A filter naming a non-variable was silently skipped.**
   `dash build, filter(<script>alert, type(dropdown))` returned **rc 0** and
   produced a dashboard carrying a filter that did nothing, with no message
   anywhere. It is now an error, like every other Stata command. The offending
   token is reduced to displayable characters before being echoed — echoing it
   raw is the same hazard the path validator had.

2. **The one-line form dropped `by()` and if-qualifier variables.**
   `_dash_do_render` extracted only *plot* variables from the spec, while
   `_dash_build` additionally ran `_dash_extract_qual_vars`. So
   `dash scatter mpg weight, by(foreign) saving(out.html)` serialised no
   `foreign` column, drew **one panel instead of two** and carried no value
   labels, while the identical graph through `dash build` drew two labelled
   panels. Two serialisation paths, one of them incomplete.

3. **`_dash_validate_path` never ran the check it was built for.** Its comment
   says the backtick and control characters are checked with `strpos+char()`
   rather than a regex to avoid the `too few quotes` crash — but three checks
   ran before it, each expanding the path inside plain double quotes, so a
   path containing `"` died in the first of them with r(132). It failed
   closed, but the user saw a quoting error rather than the diagnostic the
   program exists to give. A Mata byte scan now runs first, where the path is
   a value and cannot be parsed as code.

4. **`dash_setup`'s version gate was invalid Python.** `try`/`except` are
   compound statements and cannot be joined with `;` inside a `python: ///`
   continuation; the line raised `SyntaxError` and r(7102), so `pkgver` was
   never set and the comparison after it ran on an empty string. Nothing in
   `test/` covered either macro. `_dash_pkg_version` asks the same question
   with a lookup that needs no exception handling.

### Two checks that could never fail

Found while repairing them, and both now assert something real:

- **P1B-68** searched the HTML for the graph names `s1`, `s2`, `h1`. dash uses
  `name()` purely as a registry key and never puts it in the document; the
  hits were coincidences inside base64 data and the minified BokehJS bundle
  (`n.h1=d("h1")`), and `scatter.html` contains neither `s1` nor `s2` at all.
  It now asserts each graph's title, which the renderer does draw.
- **P1C-18** asserted that value labels appear for `scatter mpg foreign` —
  a case where Stata labels the axis `0` and `1`. It now checks by() panel
  titles, which is where Stata shows a value label, and that is what exposed
  defect 2 above.

### Re-baselined

`test_single_y_output_matches_prefix_baseline` moved again: marker symbol,
size, alpha, line width, dash pattern, the minor grid and the legend now all
come from the scheme, and `_GSIZE_PT` was corrected. Every dashboard changes.
The reason is recorded beside the digest.

### Result

16 of 16 certification scripts pass, 0 skipped. 2394 Python tests pass.

---

## Colour fidelity — 52 of 92 named colours were the wrong colour

`dash scatter mpg weight, mcolor(eltblue)` has to draw the blue Stata draws.
Measured against Stata's own `<ado>/base/style/color-<name>.style` files, each
of which sets its colour with a `set rgb "R G B"` line, **52 of the 92 named
colours disagreed**.

The grey ramp was the worst of it: `gs10` was `#f0f0f0`, a near-white, where
Stata's is `#a0a0a0`, a mid grey, and `gs14` and `gs15` were both pure white —
so a scheme built on greys rendered as a white page. Twelve of the fifteen
s2color `p#` colours were wrong too, so the default palette of the default
scheme was not Stata's: `eltblue` `#b7c9e2` against `#82c0e9`, `edkbg`
`#e8e3d2` against `#b2bfcb`, `emerald` `#50a050` against `#2d6d66`, `cranberry`
`#a00000` against `#c10534`.

The pattern is that the wrong values were plausible CSS colours — `green` was
`#00ff00`, the CSS keyword, where Stata's `green` is `#008000` — which is why
none of them ever looked obviously broken.

`_COLOR_MAP` is regenerated from those files by
`scripts/extract_color_truth.py`, and `test/test_color_fidelity.py` asserts
every entry against `test/fixtures/color_truth.json` so the check runs without
Stata. It also asserts the properties the ramp has to have — monotone, and
actually grey — which no single value comparison would catch.

Three existing tests asserted the wrong values and were corrected, each with
the style file that settles it recorded beside the change.

### `none` is not a colour

Stata's `color-none.style` sets `rgb "0 0 0"` and then says
`* values should not matter` — Stata never paints it. dash mapped the name to
white, which was invisible on a white background and an opaque blob
everywhere else; taking the style file literally would have painted it black.
`fcolor(none)` was already special-cased; `mcolor`, `mfcolor` and `lcolor`
were not, on either the marker or the line path. The token is handled in one
place now and means what Stata means by it.
