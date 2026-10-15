# Changelog

## 0.1.0, 09oct2026 (release candidate)

Changes since the 2.0 of 27mar2026 (renumbered 0.1.0 in every shipped file, as dash.pkg declares; `adoupdate` compares the Distribution-Date, now 20261009). Items marked with a work package number
(WP-nn) are recorded in ROADMAP.md; items marked S07 to S16 are from the
conformance work that came before it; a bare commit hash marks a fix
recorded only in its commit.

### Results that change

Read this section first if you have published numbers or figures made with
2.0. Each item below produced different numbers, rows or pictures before
and now matches Stata.

**Statistical layers and their rows**

- In 2.0, `lfit`, `qfit`, `lfitci`, `qfitci`, `lowess`, `lpoly`, `lpolyci`,
  `fpfit`, `fpfitci`, `histogram`, `kdensity`, `mspline`, `mband` and `area`
  ignored the row view they were given. Only the first layer's `if`/`in` was
  read, and it was applied to the whole graph. A qualifier on any later layer,
  or on a graph joined by `link()`, left the layer computed from every row,
  with no warning. Each layer now computes from exactly the rows its own
  `if`/`in`, its `by()` panel or its graph's qualifier selects. For example,
  `dash (scatter mpg weight) (lfit mpg weight if foreign==1)` now equals
  `regress mpg weight if foreign==1`. (WP-02)
- `histogram mpg, by(foreign) link(_all)` drew identical bars in both panels.
  Linked panels now match the unlinked `by()` result. (WP-02)
- `mspline` is now Stata's estimator: a cubic spline through the cross
  medians of `bands()` bands, drawn at (K-1)`n()`+K points. It was a PCHIP
  curve through every point, with `bands()` and `n()` ignored (it was off by
  up to 14.0 mpg on auto). In `mband` and `mspline`, an observation on a band
  edge now belongs to the band above, as in Stata. (WP-18)
- `fpfit` fits repeated-power FP2 models and applies Stata's shift and
  scaling. Before, it never chose (p, p) and dropped rows with x <= 0.
  `fpfitci` draws Stata's analytic `stdp` t band instead of a bootstrap
  band. (WP-18)
- `lowess` is Stata's smoother: an index window, no robustness iterations,
  and ties in dataset order. It was statsmodels' lowess (off by 0.108 of the
  y range on auto). (WP-18)
- `lpoly` weights by sqrt(K) at degree 1 or higher, leaves a point missing
  when fewer than two observations have positive weight, and evaluates at
  `n()` points (default 50, capped at the dataset's _N). `kdensity` draws on
  [min, max] x `n()`. Before, `lpoly` squared the kernel weight and
  `kdensity` padded the grid by 3h. (WP-18)
- `histogram` defaults to Stata's bin rule and to density. 2.0 always drew
  10 bins of counts. A filtered density histogram renormalises to the rows
  the filter keeps. (S07)
- `kdensity` defaults to the epanechnikov kernel, Stata's bandwidth rule and
  300 points. 2.0 used a gaussian kernel with Scott's bandwidth. `lpoly`
  defaults to epanechnikov, and `bwidth()` is now in x units. (S07)
- `lfit`, `qfit`, `lfitci` and `qfitci` evaluate at 100 points over the
  observed range. The `lfitci` band had been about 90 times too wide on
  auto. The `qfitci` band had been about half Stata's width and is now the
  analytic `stdp`. (S07, S16)
- `mband` uses Stata's default band count (9 on auto, where 2.0 used 15) and
  plots each band at the median of x. The confidence level defaults to
  `c(level)`, where 2.0 hard-coded 95. `function` draws 300 points. (S07)

**Qualifiers, filters and KPIs**

- `if !missing(x)`, `if inlist(...)` and `if x < .` used to leave the graph
  unfiltered with a warning. They now select Stata's rows. (S09)
- These qualifiers now select Stata's rows. Before, the first three drew
  every row and the last selected none:
  - `if !x` and `if ~x` on a numeric variable;
  - a qualifier that abbreviates a variable name;
  - a qualifier holding a double-quoted literal, such as
    `make != "AMC Concord"`;
  - `inrange()` with a missing bound.

  (WP-23, WP-24, c0200c0)
- Saved-page range and slider filters treated a missing value as 0, and an
  untouched range filter dropped missing values once any filter moved. Both
  now match the served app and Stata. (WP-21)
- `if price > 4500, by(foreign)` faceted every observation on the saved
  page. It now facets the qualified rows. (WP-11)
- A KPI percentile now uses `_pctile`'s rule in both modes; the old rule
  disagreed with Stata at large n (WP-23). After `dash clear`, a
  re-registered KPI could keep the old KPI's `if`/`in` and show a
  conditional value; it no longer does (61f4284).

**Served dashboards (`dash serve`)**

- These served results now match the saved dashboard:
  - A served layer's own `if`/`in`, and a served KPI's `if`/`in`, were
    ignored.
  - Twenty plot types drew empty `by()` panels.
  - A served `histogram` ignored its qualifier.
  - `lfitci` under `set level 90` served a 95% band labelled "90% CI".

  (WP-10, WP-11, WP-12)
- The served app now draws the scheme. In 2.0 it drew Bokeh's default blue
  under every scheme. (S14)

**Geometry, dates and labels**

- `area`, `rline`, `rarea` and `tsrline` joined points in dataset order and
  crossed themselves on unsorted data. They now draw along x (WP-09).
  `tsline` is drawn against the time variable, and a second axis is no
  longer drawn on a 0-to-1 range for eighteen plot types (WP-23).
- `aspectratio()` was inverted: `aspectratio(0.5)` drew a plot twice as tall
  as wide. It is now height over width, as in Stata. (S10)
- `%td` and other date variables arrived as missing, so `dash line close
  date` on sp500 drew nothing. Dates are now drawn on date axes (S08).
  Under pandas 2.3, one far-future date no longer blanks a whole date
  column (WP-25).
- `mlabel()` labels are drawn where twoway draws them. There are no longer
  labels on `line`, `spike`, `area`, `rarea`, `rbar`, `rspike`, `rcap`,
  `rline`, `tsline` or `tsrline`. A value-labelled variable shows its labels,
  where it showed the codes. (4ede074)

**Colours, schemes and appearance**

- 52 of Stata's 92 named colours were the wrong colour, including 12 of
  s2color's 15 `p#` colours. For example, `gs10` was near-white. They now
  match Stata's style files. (a0f37b9)
- A `net install`ed copy could reach none of the shipped schemes and drew a
  fallback whatever `scheme()` said. The schemes now resolve from the
  installed copy. (WP-05)
- The scheme now sets marker symbol and size, alpha, line width, line
  pattern and legend chrome. In 2.0 these were the same fixed values under
  every scheme. Stata's point sizes replace six wrong `gsize` values.
  (S11)
- Scheme fidelity, measured against the build just before the change:
  - Minor grids are gone.
  - s1color, s1mono, s1rcolor and stmono1 draw no grid lines.
  - Figure titles take the scheme's heading colour and size.
  - Under s1rcolor, every text turns white.
  - economist's title grows from 7pt to 17.28pt, and its lines from 1.2px
    to 6px.
  - Legends move to the scheme's clock position and number of columns.
  - KPI cards take the scheme's legend colours: black with white text under
    s1rcolor, `#c6d3df` under economist.
  - Markers shrink from 5.82px to 5.45px under the st* schemes and grow from
    10.18px to 12.73px under economist.

  (WP-16)
- A graph with one series no longer draws a legend, as in twoway. Legend
  keys use variable labels and "Fitted values" / "95% CI". (S09)

**WP-28 (GAPS2 audit, 25sep2026)**

- `xlabel()`/`ylabel()` (and `xlabel2()`, `ylabel2()`, `xtick()`,
  `ytick()`) read Stata's own grammar: `xlabel(1 "2019" 2 "2020" 3 "2021")`
  drew six unlabelled ticks (1, 2, 3, 2019, 2020, 2021) and now draws three
  labelled ones; `xlabel(10 20 to 40)` drew 10 20 40 with `to` as a label,
  now 10 20 30 40; `xlabel(1/5)` and `xlabel(1[1]3)` drew the default ticks,
  now 1..5 and 1 2 3; `xlabel(#5 50 "fifty")` drew 50 alone, now the count
  ticks and 50 labelled "fifty"; a compound-quoted label was a lone
  backtick, now its text. (WP-28, B1)
- An axis now spans its data, its label and tick positions and every
  `range()` value, as twoway's does, padded 5% a side: `yscale(range(100))`
  on mpg (12-41) drew the axis from 100 down to 41, now 12 to 100;
  `yscale(range(20 30))` drew 20 to 30 and hid the other points, now the
  data's 12 to 41; `ylabel(0(20)100)` drew 12 to 41 (Bokeh's top 42.45)
  and never showed 60-100, now 0 to 100; `yscale(range(0))` ended at 41
  exactly, now 0 to 41 padded at both ends; `yscale(reverse range(0 50))`
  dropped the reverse, now 50 down to 0; `r()`, `rev` and `norescale` were
  named as not implemented, now drawn (twoway drops `norescale` from a lone
  `a(b)c` rule and widens that axis, and so does dash). `yscale2()`/
  `xscale2()` and `ylabel2()`/`xlabel2()` follow the same rule, a by()
  graph's panels share one extent, an axis with an explicit label, tick or
  range value is a fixed range that holds across filter moves, and the
  served app now limits its autoranges to the graph's own layers as the
  saved page does (a fit's extended grid no longer widens its x axis).
  (WP-28, B2)
- `title("T", c(red))` drew the three lines `T`, `,` and `c(red)` in the
  scheme's colour, and `ytitle("Volume", axis(2))` titled the left axis
  `Volume` / `,` / `axis(2)`; a textbox sub-option is now read under any
  of Stata's abbreviations, so the title is `T` in red and the right axis
  is titled `Volume`. (WP-28, B3)
- `legend(order(1 "Group 2" 3 "Three"))` drew the three keys `mpg`,
  `Fitted values` and `price` with their default text, now keys 1 and 3
  titled `Group 2` and `Three`; `legend(order(2 1) label(1 "Data"))`
  relabelled the fit, now the scatter; the text-only line of
  `legend(order(1 - "Note" 2))` was dropped, now drawn; and
  `legend(lastlabel(2 "L"))` was named as not implemented, now applied.
  Keys are numbered by Stata's plot number, a ci fit counting two.
  (WP-28, B5)
- `xtitle("")` still drew `weight` and `ytitle("")` still drew `mpg` (the
  variable's label); an axis title given with empty text now removes the
  title, as in twoway, while an absent option keeps the default.
  (WP-28, B6)
- `ytitle2("P2")` drew `"P2"` with its quote marks, `ytitle2("a" "b")` one
  quoted line and `ytitle2("P2", size(large))` the sub-option text as part
  of the label; `_dash_add_secondary_axes` now reads `ytitle2()`/`xtitle2()`
  through the same textbox reader every other text option uses, so the
  second axis draws `P2`, two lines, and a sized title, with no quotes.
  (WP-28, B7)
- A continuous `histogram` dropped the observation at its last edge
  when the computed edge fell a few units in the last place below the
  maximum, and the rows a tolerated `start()` lay above: `dash histogram
  ttl_exp, bin(27)` on nlsw88 counted 2245 of 2246 rows and `histogram pop,
  bin(75)` on census 49 of 50, with the density bars scaled to the rows
  that remained. Every observation is now counted as Stata counts it, bar
  `floor((v - start)/width)` clamped to the grid, in the page and after a
  filter move (2246 and 50). (WP-28, C2)
- A `.scheme` file in the working directory that wrote its colours the
  way Stata's own schemes do -- `color background "255 0 0"` or
  `color p1 "26 71 111 %20"` -- lost every such directive without a
  warning, and `scheme(myquoted)` drew the scheme's own `color background`
  and `color p` defaults in their place (measured on a copy of
  `schemes/s1rcolor.scheme`: background `#d9e8f0`, p1 `#000000`, p2
  `#000000`, 0 warnings). The value is now read as Stata reads it, so such
  a scheme draws its declared colours and opacities (background `#ff0000`,
  p1 `#1a476f` at 0.2, p2 `#00ff00` at 0.5), and a line dash cannot read is
  named once with its line number. (WP-28, D1)
- `dash kpi`: a card now shows the text Stata's `display` gives for its format, as the page opens, after every filter move and after a brush, saved and served: `dash kpi mean(price), fmt(%10.0g)` read `6e+03`, now `6165.2568`; `fmt(%9,2fc)` read `6,165.256756756757`, now `6.165,26`; without `fmt()` auto's mean price read `6165.26`, now `6,165.3` (its own `%8.0gc`); `min(when)` of a `%td` variable read `02 Jan 2000`, now `02jan2000`, and a date card honours `fmt()`; a missing date card read an empty card as the page opened and `—` after a move, now `.`; and the page's card rebuild now escapes its text. (WP-28, E1)
- `filter(..., exclude())`: an excluded graph or card kept the rows of the last move made by a filter that did not exclude it -- price to [4000,5000], foreign to 1, price back to its full range left an excluded graph at 3 rows (k1 3) where the widgets imply 5. Every graph, link group, by() panel, aggregate and derived layer and KPI card is now masked on every move by exactly the filters that do not exclude it, in both modes. (WP-28, E2)
- Display formats on widgets, tooltips and date axes: a `%td` dropdown listed `2001-12-31 00:00:00`, now `31dec2001`; a `%9.0fc` dropdown `3799`, now `3,799`; a `%tm` range slider stepped days and stopped mid-month, now steps one month over Stata's period numbers and reads `2000m1`; slider labels read `0[.]00`/`%d %b %Y`, now the variable's format; a `%tC` tooltip dropped its time (`{%F}`), now keeps it; a `%tm` axis read `Jan 2000`, now `2000m1` as twoway draws it; an explicit axis `format(%9.2e)` or `%g` was ignored, now written; two values with one display text were listed twice, now once, selecting both -- in both modes. (WP-28, E3)
- `dash build, layout(bs)` (the saved page): the filter bar now sits below
  the title and subtitle, where the served app and every other layout put
  it -- it sat above the title (a picture change, no numbers). (WP-28, E14)
- `%g` formats and float storage: a float 0.1 marker label and dropdown read `0.10000000149011612`, now `.1`; a tooltip wrote 12345.67 as `1.235e+4`, now `12345.67`; `mlabformat(%9.3g)` was named and not applied, now applied; by() titles of a date read `01 Jan 2000`, now `01jan2000`; the colour key's number labels used `:g`, now the variable's format; the CSV wrote a float as `0.10000000149011612`, now its float32 digits `0.1` (dates stay ISO 8601). (WP-28, G6)
- Value labels on axes and in tooltips: `xlabel(1/5, valuelabel)` was
  named in the note and drew 1..5, now draws the label set
  (Poor..Excellent on auto's `rep78`), on second axes and every `by()`
  panel too; `hover(foreign)` showed 0/1, now Domestic/Foreign, in both
  modes and after a filter move. (WP-28, G16)
- `filter(varname, type(dropdown))`: a string variable's codes '01', '1.0' and ' 2' were rewritten to '1' and '2' and their rows merged, the categories 'None', 'nan' and 'NaT' were not listed, and on the saved page a number below 1e-4 or at or above 1e21 selected no rows (5e-05 kept 0 rows saved, 1 served); the saved snapshot and CSV turned a string code into a number after a move (a dcount of codes merged '01' and '1'). Now numbers are compared as numbers and text exactly, every category is listed with the empty string as a blank entry, values sharing one display text are one entry, and snapshots keep text, in both modes. (WP-28, X1)
- `dash scatter mpg weight, colorvar(rep78) colordiscrete colorcuts(2 4)`
  drew three interval colours (`≤2`, `2–4`, `>4`), so rep78 = 1, 3 and 5
  were coloured as ranges; it now draws rep78 = 2 and rep78 = 4 in two
  colours and every other value gray, as twoway does.  `colorcuts(0 2 4)` on
  rep78 drew an empty `≤0` key entry; a cut below the variable's minimum is
  now dropped (and the minimum used if every cut is below it).
  `colorlevels(#)`, `colorvarminmax`, `zlabel()`, `ztitle()` and `zscale()`
  are now drawn and no longer named in the note; `colorcuts()` with
  `colorlevels()` is refused with r(198) in twoway's words.  The continuous
  default (no cuts, levels or `colordiscrete`) is unchanged. (WP-28, X2)
- `dash scatter mpg weight, colorvar(price) colorlevels(1)` was r(198), as
  were 0, -1 and 257, and colorlevels(101) to (256) drew that many levels;
  as in twoway, 0 and 1 now draw as if the option were absent, 2 to 100
  exactly, and a negative number or one over 100 as colorlevels(5).
  (follow-up to GAPS2 X2)

**WP-29 (drop-in P0, 30sep2026)**

- `dash line mpg weight`, and `connected`, `area`, `rline`, `rarea` and
  `rconnected`, on data not sorted by x joined their points in x order,
  the picture `twoway` draws only with `sort`; they now join them in the
  data's order, as `twoway` does. On the ten-car parity frame a line
  through weight 1800, 2010, 2200, ... now runs 2930, 3350, 2200, ...;
  after a move to Foreign, 1800, 2010, 2650, 3100, 3350 is now 3350,
  1800, 3100, 2010, 2650. `sort(varlist)` was ignored with a note; it is
  now honoured. rline's lower path on x = 2 5 3 6 1 7 with the upper
  bound missing at 5 was 1 2 6 7, now 2 5 6 1 7. The WP-09 line under
  "Geometry, dates and labels" ("They now draw along x") describes the
  order this replaces. (WP-29, P0.1)
- A by() graph's panels share one scale per axis, as twoway draws them: `dash scatter mpg weight, by(foreign)` drew Domestic on 12-34 and Foreign on 14-41 and now draws both on 12-41, with second axes shared too; `by(foreign, yrescale) ylabel(#5)` drew 10(10)40 on both panels and now draws 10(5)35 and 15(5)40; `by(, yrescale) yscale(range(0))` drew both panels from 0 and now leaves range() unapplied, with a note; by() panels now pan and zoom together (WP-29, P0.2)
- Unlabelled variables are named as twoway names them, in both modes: `dash scatter y x` on unlabelled data drew no axis titles, the key `scatter` and tooltip rows `''`, and now draws the titles `x` and `y`, the key `y` and the rows `x` and `y`; `(scatter y1 x) (scatter y2 x)` was keyed `scatter scatter` and is now keyed `y1 y2`; `(histogram mpg) (kdensity mpg)` was keyed by the variable twice and is now keyed `Density` and `kdensity mpg`; the served app's filter widgets were untitled and are now titled by the variable's label or name; a data file whose variableLabels is malformed aborted the build and now draws names.  Until P1.16, a multi-layer unlabelled graph draws its first layer's name as y title where twoway draws none. (WP-29, P0.3)
- A title option given only sub-options keeps twoway's default title, in both modes: `ytitle(, size(large))`, `xtitle(, color(red))`, `ztitle(, size(large))` and any title option given only sub-options drew no title (axis_label None, an empty key title), and now draw the default title styled by them, as in twoway; `ytitle(,)` drew a literal comma and `title(A,)` drew `A,`, and a comma followed by nothing or by another comma now opens an empty sub-option list (`ytitle(A,,)` is `ytitle(A)`); the second axis of a yaxis(2)/xaxis(2) graph had no title and Bokeh's 13px #444444 style, and is now titled by its layers' label (`Density` or `kdensity` varname for those layers) in the scheme's axis style, and untitled under by(). (WP-29, P0.4)
- `axis(2)` on an axis option is drawn on the second axis, in the saved page and the served app, before and after a filter move: `ylabel(20 30, axis(2))` was drawn as a [20, 30] ticker on the left axis with a note and now labels the right axis; `yscale(log axis(2))` logged the left axis and now logs the right one; `yline(5000, axis(2))` was drawn at 5000 on the left axis's scale and is now drawn on the right axis's; `xtick(160, axis(2))` ticked the bottom axis and now ticks the top one; `ylabel(10 20) ylabel(5000 10000, axis(2))` lost the first axis's labels and now keeps both lists; `ylabels()`, `yticks()` and `ylines()` were dropped with a note and are now read as `ylabel()`, `ytick()` and `yline()` (WP-29, P0.5)
- `dash function y = 2^3^x, range(0 2) n(3)` drew 2 8 512, now 1 8 64; `2^-1^2` .5, now .25; `0.1*3/0.3` 1.0000000000000002, now 1; `1e16+1-2` 9999999999999998, now 1e16; `normalden(x)`, `ln(x)`, `_pi*x`, `_b[]` and scalars drew nothing, now twoway's points (WP-29, P0.6)
- `dash lpoly mpg weight, kernel(biweight) degree(2)` used a default bandwidth of 63.80 and drew 34 points; it now uses Stata's rule of thumb, 302.45, and draws Stata's 50, for every kernel, degree, weight, by() panel and qualifier; `lpoly mpg weight in 1/7` used 185, now Stata's 77.35; `lpoly mpg foreign` drew a curve between the group means, now a line at 0 as twoway draws it; after a served move to Foreign the bandwidth was 26.88, now Stata's 287.78; and a local window whose powers of x are nearly collinear keeps the columns Stata's invsym keeps (foreign==1 biweight degree(2) was up to 8.857 mpg off Stata's curve) (WP-29, P0.7)
- `dash histogram date, width(30) start(14975)` on sysuse sp500 drew 15 bars
  with every row in the last, after the note that width(30) would need more
  than 1000 bins, and densities per millisecond (3.47e-11); it now draws
  twoway's 13 bars, 30 days wide from 14975, with densities per day
  (.0025538, .0028226, .002957, ...). Every computed layer of a date reads
  the variable, its weight, width(), start(), bin(), bwidth(), range() and
  n() in the date's Stata units. (WP-29, P0.8)
- `dash kdensity date, bwidth(10)` drew a curve of spikes up to 1.35e-04 (the
  bandwidth read as 10 milliseconds); it is now Stata's curve, per day.
  (WP-29, P0.8)
- `dash lpoly close date, bwidth(30)` drew nothing; it now draws Stata's curve
  (1325.6916 at 02jan2001 with n(5)). (WP-29, P0.8)
- `dash fpfit close date` read 1329.5113 at 02jan2001; it now reads Stata's
  1329.5387. (WP-29, P0.8)
- A histogram or kdensity of a date drew the date axis on y and the bars or
  curve in milliseconds on a numeric x axis; the date axis is now x, in the
  variable's own display format, and yline(), xline(), xlabel() and
  yscale(log) read the density and the dates as twoway does. (WP-29, P0.8)
- `dash (scatter close obs) (lfit close date)` drew the fit at 978393600000
  and beyond (epoch milliseconds) beside obs 1..248; it is now drawn at the
  day numbers 14977-15340, as twoway draws it. (WP-29, P0.8)
- `dash lpolyci mpg weight, degree(1) bwidth(500) pwidth(800)` drew a bootstrap percentile band 0.85 to 1.55 times Stata's width, its edges up to 44.7 mpg off at degree(1); it now draws Stata's analytic band; `pwidth()` and `var()` on lpolyci were named as ignored and are now honoured; `lpolyci ..., level(5)` was drawn and is now refused r(198) as twoway refuses it; two observations at `bwidth(1000)` drew nothing and now draw the smooth, with no band, as twoway does; and the band is about 70 times faster at N=20000 (WP-29, P0.9)
- `dash (scatter mpg weight) (scatter mpg weight if price>6000), by(foreign)`
  linked with a second graph, with the price range moved to 5,000-15,906:
  the saved page drew 23 observations in each panel's second plot, where
  `count` gives 14 and 9 and the served app draws them.  A plot's own
  `if`/`in` inside a linked `by()` panel, or inside a linked graph with its
  own `if`/`in`, now keeps to that panel's or graph's observations after
  every move, a second move and a reset; the saved page now draws 14 and 9.
  (WP-29, P0.15)
- `colorvar()`'s key is drawn from the observations the plot draws, as
  twoway draws it.  `dash (scatter mpg weight if foreign==1,
  colorvar(price)) (scatter mpg weight if foreign==0)` drew its colour bar
  over 3,291-15,906 on the saved page; it is now 3,748-12,990 in both
  modes, and `colordiscrete` on rep78 there gave levels 1-5 and is now
  3-5.  A linked graph with its own `if` and each linked `by()` panel were
  coloured over the whole dataset in both modes and now over their own
  observations.  `scatter y2 weight, colorvar(price) colorlevels(2)` with
  y2 missing on the 15,906 car cut at 8,895.5 and now cuts at 9,598.5, as
  twoway does (an observation whose y or x is missing counts).
  `rconnected` drew two keys and now draws one.  A missing value is drawn
  in `colormissing()`'s colour and is no longer a key level, and the
  derived colour column is now named under the reserved `__dash_cvar`
  prefix, one per layer, so a variable called `_cvar_price_bin` is never
  overwritten. (WP-29, P0.16)
- In the served app, after a filter move a bar's and an rbar's width follows the kept rows: dash bar mpg weight served with filter(foreign) drew the Foreign cars' bars 56 wide (the build's spacing), now 168, as the saved page draws them. A computed, bar or range layer left with no observations -- dash (scatter mpg weight) (lowess mpg weight if price >= 10000), or a served layer with its own if that selects nothing -- was drawn in Bokeh's #1f77b4 at width 1, now in its own scheme colour and width with its legend key (#90353b, 1.5 for the second plot under s2color), as twoway keys it (WP-29, P0.18)
- `dash kpi sd(date)` on sysuse sp500 read 9.10e+09; it now reads 105.3335,
  summarize's sd in days. Every KPI statistic of a date but count and
  dcount is taken of the variable's Stata values, saved and served, at
  first paint, after a filter move and after a brush. (WP-29, P0.20)
- `var(date)` read 8.28e+19, now 11095.14; `iqr(date)` 1.60e+10, now 185;
  `cv(date)` .0091564, now .0069496. (WP-29, P0.20)
- `sum(date)` read 2.46e+14, now 3758900, and its note now names the units,
  days since 01jan1960, where it named milliseconds since 01jan1970.
  (WP-29, P0.20)
- The mean of a %tm variable holding 2001m1 and 2001m3 read 2001m1; it now
  reads 2001m2. (WP-29, P0.20)

**WP-30 (drop-in P1, 03oct2026)**

- `dash scatter mpg turn weight, mcolor(red blue) msymbol(O T)` now draws mpg in red circles and turn in blue triangles, as twoway's stylelists do. Each series used to get the whole list, so both fell back to the scheme's colour and symbol with "not a recognised colour" notes. A lone value or a short list over several y now styles only the leading y, silently, as in twoway: `dash line mpg turn weight, lwidth(thick)` thickened both lines and now thickens mpg's alone. `.`, `=`, `..` and `...` mean what they mean in twoway, and a quoted element is one element. A plot type that draws one y uses the first element: `dash scatter mpg weight, mcolor(red blue)` drew the scheme's colour with a note and now draws red. An unquoted `mcolor(255 0 0)` is now three colours, as twoway reads it: it drew red, and now draws the series with the unknown colour 255 and a note; write `mcolor("255 0 0")`. (WP-30, P1.1a)
- A lone `mlabel()`, `jitter()`, `base()` or `barwidth()` value over several y now applies to the first y only, as twoway pads a list with `.`. `dash scatter mpg turn weight, mlabel(make)` labelled both series and now labels mpg's alone, and `dash bar mpg turn weight, base(50)` drew both series from 50 and now draws turn from its default base. Nothing is printed, as in twoway. (WP-30, P1.1b)
- Every graph's chrome is drawn from its scheme, in both modes and after a filter move: under the default s2color, `dash scatter mpg weight, title(T)` drew the title bold at the left and now draws it centred and not bold (left under economist); axis titles were italic and are now upright; subtitle(), note() and caption() were drawn at the plot's left edge and are now placed by the scheme's clock position and justification (the subtitle centred above, the note and caption at the left below, economist's note in its box at the top right beside the title); y tick labels were level and are now vertical under s2color, s2mono, s2gcolor, s1color, s1mono, s1rcolor, sj, s2manual, s1manual, s2gmanual and s2color8 (`ylabel(, angle(0))` keeps them level); ticks were 2 px inside and 6 px outside in black and are now the scheme's `gsize tick` (5.33 px for tiny, drawn as 5 whole pixels) outside, or inside under economist, in `color tick` (white under s1rcolor, where they could not be seen) at `linewidth tick`; the major grid was solid and is now dashed under the st* schemes that dash it; under economist the y axis was on the left with a black line and ticks and is now on the right with neither, and a yaxis(2) axis is on the left with its line and ticks. (WP-30, P1.2a)
- Markers are drawn opaque, as twoway draws them: `dash scatter mpg weight`, `connected`, `dot` and `rconnected` drew every marker at alpha 0.8 under every scheme but sttrans, and now draw them at 1.0; `mcolor(navy%50)`, `malpha()` and sttrans' %20 still set an opacity. (WP-30, P1.2b)
- Fills are the colour blended at the layer's intensity, opaque, as twoway draws them: `dash bar mpg rep78` filled its bars `#1a476f` and now fills them `#486c8c` under s2color (`#cccc00`, was `#ffff00` at alpha 0.8, under s1rcolor); `area`, `rbar` and `rarea` likewise (`#486c8c`, was `#1a476f`); a colour you give takes the intensity too: `fcolor(yellow)` and `color(yellow)` fill `#ffff33` (were `#ffff00`), `rbar, color(red)` fills `#ff3333` and keeps its `#ff0000` outline. Histograms stay at full intensity until their own scheme style is read. (WP-30, P1.2b)
- `fintensity()` is drawn as twoway draws it, an opaque colour, never an opacity: `fintensity(50)` on navy is `#8da3b7` (was navy at alpha 0.5), `fintensity(150)` `#112f4a` and `fintensity(1000)` `#03070b` (were clamped to navy), `fintensity(0)` and `fintensity(-5)` white (were invisible), under s1rcolor `fintensity(50)` `#0d2438`; `inten200` and `max` are read; an unknown name such as `inten75` draws full intensity with the note (was alpha 0.75). On confidence bands `lfitci, fintensity(150)` is `#808080` (was `#c0c0c0`) and, under s1rcolor, `fintensity(50)` `#282828` (was `#a8a8a8`). (WP-30, P1.2b)
- A user scheme's `intensity p#bar` and `intensity p#area` are read, above 100 too (`intensity p1bar inten200` fills navy bars `#0d2438`), and its `intensity bar` and `intensity area`, which twoway ignores, are no longer read: `intensity area inten40` drew areas at alpha 0.4 and now changes nothing. (WP-30, P1.2b)
- A brushed-away bar or area is dimmed in the colour it is drawn in (it was dimmed in the colour before intensity and `fcolor()`). (WP-30, P1.2b)

- `dash scatter mpg weight`, and every axis with no `xlabel()`/`ylabel()` rule, was ticked by Bokeh: y 15(5)40 and x 2000(500)4500 with minor ticks, over the data padded 5% a side (y 10.55 to 42.45). It is now ticked as twoway ticks it: y 10(10)40 and x 2000(1000)5000, with no minor ticks, over the hull of every drawn layer and its ticks (y 10 to 41, x 1760 to 5000), plus twoway's plot-region margin of 2.2% of the graph's smaller side (economist 0.6%, a by() panel's scaled by twoway's by() factor). A fit, CI band, `scatteri` point or `function` curve now widens the axis instead of being clipped, by() panels included: `(scatter price mpg) (lfit price mpg)` runs y from 0 to 15,906, not 2,660 to 16,537. `ylabel(#5)` keeps a margin past its outermost tick. A second axis without `ylabel2()` is ticked 0(5000)15000, not 4000(2000)16000. After every filter move, default and `#N` axes are re-ticked and re-ranged over the rows kept, in the saved page and the served app, second axes included (on the saved page a fit or histogram it does not recompute, marked "(unfiltered)", stays inside the range as drawn). An axis with explicit positions spans its data again. A zoom ticks the visible range by the same rule, and Reset returns to the last filter move's extent. (WP-30, P1.3a)

- Default date axes take twoway's calendar ticks: `dash line close date` on sp500 drew Bokeh's monthly ticks (2001-01-01, 2001-03-01, ... 2002-01-01) and now draws twoway's 01jan2001 01apr2001 01jul2001 01oct2001 01jan2002; every %td-%ty axis, second date axis and date-beside-number axis is #5 by dash's model of twoway's calendar rule (it agrees with Stata on 52-66% of daily to half-yearly ranges and 98% of yearly ones) and re-ticks after a filter move and on zoom in both modes. (WP-30, P1.3b)
- `twoway histogram mpg` and every other histogram layer is drawn in the scheme's histogram style, the same for every layer: s2color fill `#1a476f` with a white 1px outline (a second histogram `#90353b`) -> khaki `#cac27e` outlined stone `#d7d29e` at `linewidth histogram`; stcolor `#1a85ff` -> `#3191ff` outlined `#5faaff`; s1mono `#606060` -> `#808080` outlined black; an emptied histogram's key likewise. `color()`, `fcolor()`, `lcolor()` and `fintensity()` still win (WP-30, P1.4a)
- `twoway rarea` is drawn as opaque as `area`: fill opacity 0.5 -> 1 (0.2 under sttrans) (WP-30, P1.4a)
- Under `scheme(sttrans)`, fits, smooths, function, spikes, range caps and lines, paired-coordinate layers, arrow heads and immediate layers carry the scheme's 20% opacity: alpha 1.0 -> 0.2; the confidence band stays as it was, as twoway draws it (WP-30, P1.4a)
- The mono schemes' hollow symbols (s1mono's p7-p10 and the rest) are drawn hollow, and small symbols (`smcircle` and the rest, from the scheme or `msymbol()`) at Stata's size for them, about 0.71 of the full symbol (0.75 for `smtriangle`), after `msize()`: filled and full size -> hollow and small. scatteri, rscatter, pcscatter, dropline and rcapsym take the scheme's symbol cycle (circle -> the p# symbol) (WP-30, P1.4a)
- A user scheme's `color p#mark` no longer colours markers, as twoway does not read it; `color p#markfill` and `color p#markline` now colour a marker's fill and outline. `msymbol(Oh) malpha(50)` stays hollow (fill 0.5 -> 0) (WP-30, P1.4a)
- Marker labels take the scheme's marker-label colour and size, as twoway draws them: under s2color `dash scatter mpg weight, mlabel(make)` labels in #1a476f at Stata's small (8pt), where they were #444444 at 10px under every scheme; under s1rcolor in yellow #ffff00 on the black page, and under sttrans at the scheme's 20% opacity. `color plabel`, `color p#label`, `gsize plabel` and `gsize p#label` in a scheme of yours reach them, and `mlabsize(*2)` doubles the scheme's size. (WP-30, P1.4b)
- A colorvar() colour bar takes the scheme's text and ticks: its labels in the tick-label size and colour, its title in the axis-title size and colour, upright, its ticks in the scheme's tick colour, width and length, on the graph region. It was a white box at 95% opacity with 11px #444444 labels and a 13px italic #444444 title under every scheme, s1rcolor's black page included. (WP-30, P1.4b)
- Axis ticks are written in the display format twoway labels the axis with: `dash scatter mpg weight` wrote Bokeh's 2000 3000 4000 5000 and now writes weight's `%8.0gc` 2,000 3,000 4,000 5,000; a histogram's heights read 1.0e-04 (`%6.4g`), a fit or `scatteri` axis `%9.0g`, a second axis its first layer's format, with or without `ylabel2()`, and `xvarformat()`/`yvarformat()` are read. Every numeric axis of every dashboard changes from Bokeh's text to Stata's, and each distinct format adds one formatter, about 33 KB, to the page. (WP-30, P1.5)
- `format()` on a date axis writes the stored value as twoway does: `dash line close date, xlabel(, format(%9.0fc))` wrote epoch milliseconds (9.47e+11) and now writes 14,976; `xlabel(, format(%tdDD/NN/CCYY))` was dropped without a note and now writes 01/01/2001; `xlabel(, format(%td))` on a numeric axis was ignored and now writes dates; `xlabel(, format(%12s))` drew unformatted ticks and now draws `%9.0g`, with a note. (WP-30, P1.5)
- Narrow display formats with an explicit digit count write what Stata's `display` writes: `%6.4g` of .0001 wrote .0001 and now writes 1.0e-04, `%6.2e` of 12345 wrote 1.e+04 and now 1.2e+04, and `%10.1g` of 1.23 wrote 1 and now 1.2, on axis ticks, kpi `fmt()`, `mlabformat()`, tooltips and slider values. (WP-30, P1.5)


- `connect()` and `cmissing()` are drawn, in both modes and after filter moves (both were named in the note and ignored): `dash scatter y x, c(l)` drew markers only and now draws twoway's connected plot, its `clcolor()`, `clwidth()` and `sort` honoured; `c(J)`/`c(stairstep)` and `c(stepstair)` drew a straight line and now draw stairs, every point keeping its tooltip; `c(L)` now breaks the line wherever x drops; `c(i)` hides the line and keeps the key; `cmissing(n)` drew a bridged line and now breaks it at each missing value, on line, connected, tsline, rline, rconnected, tsrline, scatteri and a scatter given `connect()`; the fits take every `connect()` style (lfit steps over twoway's three points); per-y lists and `cmissings()` are read as twoway reads them. `function y=sqrt(x^2-1), range(-2 2)` drew a gap over the missing middle and now bridges it as twoway does (`cmissing(n)` breaks it). A linked connected layer with a missing value now shows the link selection on its markers. (WP-30, P1.8a)
- `recast()` is drawn: `dash scatter y x, recast(line)` drew markers and named the option, and now draws `line y x`; `kdensity x, recast(area)` drew a line and now draws an area; `lfit y x, recast(scatter)` drew a line and now draws the fitted points as markers; `recastas()` and `type()` are read as its synonyms, and an out-of-group or unknown name falls back as twoway does (a yx type to scatter, a range type to rspike, a pc type to pcspike) with twoway's two notes. (WP-30, P1.8b)
- `horizontal` is drawn on bar, rbar, spike, rspike, rcap, rcapsym, dropline, dot, area, rarea, histogram, kdensity, function, rline, rconnected, rscatter, tsrline, the pc types, pci and pcarrowi, as twoway draws it: `dash bar mpg rep78, horizontal` drew upright bars and named the option, and now draws bars along the y axis with the axes, default titles, date labels and second axes swapped, rcap caps across the spine and marker labels where twoway puts them; `vertical` is no longer named. (WP-30, P1.9a)
- TeX in graph text is drawn as typed, as twoway draws it: `dash scatter mpg weight, title("\(y\)") subtitle("\[z\]") note("\$\$ x \$\$")` drew typeset maths and wrote a 3,087,832-byte page carrying MathJax; it now draws the text as typed and the page is 1,302,025 bytes, against 1,301,893 for the same page in plain words. (WP-30, P1.11a)
- Stata's graph-text markup is drawn as twoway draws it. `dash scatter mpg weight, title("{&alpha} R{sup:2}") subtitle("{bf:Bold}")` drew `{&alpha} R{sup:2}` and `{bf:Bold}` as typed; the title is now `α R²` and the subtitle bold `Bold`. The same holds for axis titles, tick labels, legend keys and titles, by() panel titles, the colour key and marker labels (string variables, value labels, scatteri and pcarrowi), in the saved page and the served app, before and after a filter move; filter titles, dropdown options from value labels and tooltip row names show the characters without style tags. Markup on part of a text is drawn in the text's own style with one note; as in twoway, `{c 0}` cuts the text off at it and control codes are kept, carried in the page as escaped text. (WP-30, P1.11b)
- `dash scatter mpg weight` draws its markers at Stata's size, on one unit for every class (1 Stata unit = 2.88pt = 3.84px): the default marker is 5.87px under s2color (was 8), 4.0 under stcolor (was 5.45) and 9.33 under economist (was 12.73); `msize(medium)` is 5.87px (was 11) and `msize(large)` 9.33 (was 15); `msize(4pt)`, `msize(*2)` and `msize(vhuge)` draw 5.33, 11.73 and 21.33px where they were noted and drawn at the default. (WP-30, P1.12a)
- Text sizes are Stata's: `title("T", size(large))` is 14pt (was 15px), `size(5)` 14.4pt (was 5px), `ylabel(, labsize(medium))` and `mlabsize(medium)` 11pt (were 11px), `legend(size(large))` 14pt (was 15px). `#pt`, `#in`, `#cm`, `#rs`, `*#` and every gsize keyword (`vhuge`, `tenth`, `relative3`, `10-pt`, ...) are drawn where they were noted, `zlabel(, labsize())` is drawn on the colour bar where it was named, and under stcolor and economist `size(14pt)` keeps twoway's proportion to the scheme's sizes (12.44pt and 25.45pt). (WP-30, P1.12a)
- Marker labels sit where twoway puts them, the marker's radius plus the gap from their point: 5.6px from the point by default under s2color (was 4px), 22.1px with `mlabgap(5)` (was 9px); bar, pcarrow and pcbarrow labels sit half the layer's marker size from their point. (WP-30, P1.12a)
- An unknown or wrong-case size name draws the class's medium with the note, as twoway does (a marker the scheme's own default size, its bare `symbolsize`: medium, large under economist): `title("T", size(abc))` is 11pt (was the scheme's 14pt) and `msize(HUGE)` 5.87px (was 24px); a negative size draws nothing, silently (`msize(-1)` drew 1px). (WP-30, P1.12a)
- Points left out of a box or lasso selection keep their own look: with `msize(large) mcolor(red)` the unselected points are drawn large and red, faded (they were drawn at the scheme's default size and colour), a hollow `msymbol(Oh)` stays hollow (it was filled), and `lwidth()`, `lcolor()`, `fcolor()` and `colorvar()` reach them too, in the saved page and the served app. (WP-30, P1.12a)
- Line widths are drawn in Stata's units on Stata's own ladder, one unit 2.88 point (3.84 pixels) as for every other size. Under s2color the default line, marker outline, grid and reference line go from 1.5 to 1.15 pixels, axis lines, the plot-region border and bar outlines from 0.8 to 0.77, and economist's lines from 6.0 to 4.61. lwidth(thin) was 0.8 and is 0.77, lwidth(thick) 2.5 and now 3.07, lwidth(vvthick) 5.0 and now 9.98, lwidth(vvvthick) 6.6 and now 16.13. A number is Stata units, so lwidth(.3) was 0.3 pixels and is 1.15, and lwidth(2) was 2 and is 7.68. lwidth(vvvthin), lwidth(none), lwidth(1pt), lwidth(*2) and the in, cm and rs units are drawn where they were noted and ignored, a width under 0.3 point is drawn at 0.3 point, and a name is matched in its case, so lwidth(THICK) is noted and drawn at the scheme's width, as twoway draws it. This holds for lwidth(), mlwidth(), clwidth(), alwidth(), plotregion(lwidth()), xline() and yline(), and for a scheme's linewidth keys, in the saved dashboard and the served app. (WP-30, P1.12b)
- Stata's colour grammar is read in every colour option and scheme file: dash scatter mpg weight, mcolor(navy*.5) drew the scheme's #1a476f with a note, now #8da3b7; mcolor("85 40 0 144") (CMYK) and mcolor("hsv 209 .766 .435") draw #1a476f and #19456e; mcolor(fg) draws the scheme's foreground (white under s1rcolor); a scheme file's color p1 navy*.5 drew #000000, now #8da3b7. (WP-30, P1.13a)
- An unknown or wrong-case colour is drawn black with a note, as twoway draws it: mcolor(bogus), mcolor(Navy) and mcolor(grey) drew the scheme's colour (Navy and grey silently), now #000000; bar …, fcolor(bogus) draws #333333; title("T", color(bogus)), graphregion(color(bogus)) and xline(3000, lcolor(bogus)) draw black. A malformed hex code or multiplier keeps the default silently: mcolor(#f00) drew red, now the scheme's colour. (WP-30, P1.13a)
- A scheme file's unreadable colour is drawn as twoway draws it: color background bogus drew #d9e8f0, now #000000 with a note; color background #}a{b;c is drawn white, silently. (WP-30, P1.13a)
- A bare colour intensity or opacity adjusts the colour the element would otherwise draw, as in twoway: `dash scatter mpg weight, mcolor(*.5)` kept s2color's #1a476f and now draws #8da3b7 (navy at half intensity); `bar ..., fcolor(*.7)` draws #7f98ae where it drew #486c8c, `title("T", color(*.5))` #8f96a9, `graphregion(color(*.5))` #f5f9f9 and `xline(3000, lcolor(%50))` the reference-line colour at half opacity; a %# is now kept at marker labels, bars, areas, histograms, pc arrows, titles and reference lines, and an unknown colour on an area or a bar's color() draws black (#333333 at the intensity) with the note where the scheme's colour was kept. (WP-30, P1.13b)
- The named styles `p1`-`p15` are drawn on every plot type, as twoway draws them: `pstyle()`, `lstyle()`, `clstyle()`, `mstyle()`, `mlstyle()`, `astyle()`, `alstyle()`, `bstyle()` and `blstyle()` were ignored with a note (`pstyle()` was drawn only on the four ci fits); `dash scatter mpg weight, pstyle(p3)` drew `#1a476f` and now draws p3's `#55752f` under s2color. A named style and your own options combine in twoway's order: `mcolor(red) pstyle(p3)` is red and `color(red) mstyle(p4)` is p4. `p()`, named in the note before, is twoway's whole-plot style: `mcolor(red) p(p3)` draws p3, discarding the other style options. `al()` and `bl()` are now `alstyle()` and `blstyle()`, as in twoway (they were named as typed). A name other than `p1`-`p15` is noted and the layer keeps its own style. (WP-30, P1.14a)
- The style options take Stata's other style names and draw them as twoway does: every one of Stata's 76 line styles (lstyle(refline), lstyle(grid), lstyle(xyline), lstyle(none) ...), and ci, ci2, histogram, foreground, background, none and the p#line, p#bar, p#area, p#box, p#dot and p#arrow series forms. line mpg weight, lstyle(refline) under s2color was drawn in p1's #1a476f and is now #2d6d66, and pstyle(ci) now works on any plot. A name Stata does not know now draws twoway's default attributes with twoway's note, where the layer kept its own style: area mpg weight, astyle(bogus) is filled in the scheme's background colour (#eaf2f3 under s2color) and lstyle(bogus) is drawn as a thin black line. dstyle(), dlstyle() and bmlinestyle() are accepted and kept, and still named as not drawn (WP-30, P1.14b)
- dash scatter mpg weight, title("T") by(foreign rep78, missing) now labels each panel on its own row under T -- Domestic, 1 ... Foreign, (missing) -- where it titled them T — Domestic / 1 ... T — Foreign / Missing; subtitle() replaces, leads or follows the label as in twoway; by(, title() subtitle() note() caption()) are drawn once over the panels, where they were named and ignored, with twoway's note Graphs by Car origin and Repair record 1978 under them unless by(, note("")); and a string by() variable's "" values are left out of the panels and the Total panel unless missing is given, where they drew an untitled panel and were counted in Total (WP-30, P1.15a)
- by() graphs are laid out and sized as twoway does: `rows()`, `holes()`, `colfirst`, `compact`, `style(compact)` and `imargin()` place and space the panels (they were named and ignored); panel text, markers and lines are drawn at twoway's by() size, 0.85 of the plain graph's for 2 to 4 panels and 0.6 for 10 to 16 (they were full size), or at `iscale()`; `xsize()` and `ysize()` size the whole array (two panels of `xsize(12) ysize(3)` were 4:1 each and are now 2:1), and `layout(bs)` gives a wide faceted graph its own row. (WP-30, P1.15b)
- by() panels share their axes and keys as twoway's do: `dash (scatter mpg weight) (lfit mpg weight), by(foreign)` drew both axes, both axis titles and a legend on every panel, and now draws the y axis on the left panel, the x axis under each column, each axis title once and one legend for the array (placed by `by(, legend())` or the scheme), with `iyaxes`, `ixaxes`, `noedgelabel`, `ilegends` and the other by() axis options honoured instead of named; a second y axis and its title are no longer repeated on every panel; `colorvar()` under by() draws no colour key unless `by(, clegend(on))`, which draws one from the first panel; each panel's label is drawn in the scheme's shaded box across the top of the panel, as twoway draws it (s2color bluish gray; it was plain text); on a phone-width screen stacked panels keep their axes. (WP-30, P1.15c)
- Legend keys are twoway's text, in both modes: `dash (scatter mpg weight) (lowess mpg weight)` keyed the fit `Fitted values` and now `lowess mpg weight`; lpoly `lpoly smooth: Mileage (mpg)`, mband `Median bands`, mspline `Median spline` and fpfit `Predicted mpg` (and the lines of lpolyci and fpfitci) were `Fitted values`; `function z=x/100` was `Fitted values` and is now `z` (`y` with no name; any Stata name, `_y` and `ü` included); `(rcap mpg turn weight)` was `Mileage (mpg)` and `(pcspike mpg weight turn length)` `pcspike`, now both `Mileage (mpg)/Turn circle (ft.)`; pci was `pci` and is `y/yb`; scatteri was `scatteri` and is `y`, and `(scatteri 20 3000 25 3500), legend(on)` now draws its key; `dash function _y =` said `error in expression:` and now says twoway's `nothing found where expression expected`, r(111) as before. (WP-30, P1.16)
- Default axis titles follow twoway's rule on each axis: the first series' label when the last series' label is the same, else none: `dash (scatter mpg weight) (scatter price weight)` was titled `Mileage (mpg)` and now has no y title; `(scatter mpg weight) (lowess mpg weight)` loses its y title; `(lpoly mpg weight)` is titled `lpoly smooth: Mileage (mpg)` and `lpoly smoothing grid` (was `Mileage (mpg)` and `Weight (lbs.)`); `(rcap mpg turn weight)` and `(pcspike mpg weight turn length)` had no title and are titled `Mileage (mpg)/Turn circle (ft.)` (pcspike's x `Weight (lbs.)/Length (in.)`); `function y=x^2` is titled `y` and `x`; on `yaxis(2)`, `(scatter mpg weight) (lfit price weight, yaxis(2))` was titled `Price` and is `Fitted values`, and `(scatter mpg weight) (scatter mpg weight, yaxis(2)) (scatter price weight, yaxis(2))` was `Mileage (mpg)` and is untitled. (WP-30, P1.16)
- Bars and range caps are drawn at twoway's size. dash bar mpg weight drew each bar 0.8 times the smallest gap between the x values (56 on weights 1800-4080), now one x unit wide (1), as twoway draws it; on a date axis one unit is the variable's own, a day for %td, a millisecond for %tc, a week, month, quarter, half-year or year for %tw-%ty (a weekly %td bar was 5.6 days wide, now 1 day: barwidth(7) draws touching weekly bars), and barwidth() is read in those units (barwidth(3) on a %td axis drew 3 milliseconds, now 3 days). rbar reads barwidth() (barwidth(.3) was ignored). rcap's caps are as long as a marker of its msize(), the scheme's symbol size by default, and no longer change with the x spacing (they were 0.4 times the smallest gap and ignored msize()); rcapsym draws no caps (it drew two) and its markers start at the scheme's symbol size (they were 7 pixels). Widths and caps no longer change when a filter moves, in either mode. (WP-30, P1.17a)
- Bars, spikes, droplines and areas stand where twoway stands them. With no base(), dash drew them from 0 and stretched the y axis to 0: bar, spike, dropline and area of a y from 10 to 14 were drawn up from 0 on a y axis reaching 0; they are now drawn from 10, the end of twoway's scale (10 to 14) nearest 0, and the axis stops there, as twoway draws them (dash bar mpg weight now stands on 10). 0 is still used when the scale holds it (yscale(range(0)), a layer reaching 0); on a log axis the base is the scale's lower end, where dash drew from 0; on a date axis 0 is 01jan1960 (dash used 01jan1970); under by() the panels share the base of their common scale, each its own with yrescale; a yaxis(2) layer takes its own axis's. The base follows the axis when a filter moves, in both modes. (WP-30, P1.17b)
- xlabel(), ylabel(), xtick(), ytick() and their second-axis forms draw nolabels, noticks (labels and ticks win within one option), labcolor() with %# opacity, tlength() in Stata's size units and tposition(); xscale(), yscale() and their second-axis forms draw off, noline, the axis line's lcolor(), lwidth() and lpattern(), alt and titlegap(). Each was named in a "not implemented" note and not drawn. dash scatter mpg weight, ylabel(, angle(rvertical)) drew the labels at the scheme's own angle and now draws them at 270 degrees; every anglestyle name and twoway's h, v, rh and rv are read. ylabel(, angle(Vertical)) drew 90 degrees and is now noted and drawn at 0, also over a scheme's vertical labels. Under by(), xscale(off), yscale(off), nolabels, noticks and titlegap() are drawn as if absent, with no note, as twoway draws them. (WP-30, P1.18a)
- `add` adds to the default ticks: `dash scatter mpg weight, ylabel(25, add)` drew one tick at 25 and named `add` in a note, and now draws 10 20 30 40 and 25, as twoway does, on date axes (`xlabel(492, add)` on a `%tm` axis) and second axes (`ylabel(6000, axis(2) add)`, named before) too, before and after filter moves; `ylabel(50, add norescale)` draws 50 without widening the axis; after a rule (`ylabel(15(10)35, add)`) `add` has no effect, repeated `ylabel(…, add)` copies keep it, and `ylabel(0(10)100, norescale)` now widens the axis as twoway's lone rule does. (WP-30, P1.18b)
- plotregion() and graphregion() are drawn as twoway draws them, in both modes: `plotregion(c(red))` drew nothing (abbreviations were not read) and `plotregion(color(red))` filled only, and now both fill and outline in red; `fc()`, `lc()`, `lw()`, `lp()`, `ls()`, `sty()` and the other spellings work; `none` drew black and now draws nothing; `fcolor(red%50)` drew opaque red and now draws it at half opacity; `style(none)`, `lstyle(none)`, `lpattern()` and the graph region's outline were ignored and are drawn; repeated copies combine as twoway combines them (`plotregion(color(red)) plotregion(c(blue))` was red and is blue). `bgcolor()` is now twoway's canvas under the graph region: `bgcolor(red)` alone coloured the graph region red and now changes nothing visible, and `bgcolor(red) graphregion(color(none))` shows red. (WP-30, P1.20a)
- `plotregion(margin())` and the plot region's inner box are drawn: `dash scatter mpg weight, plotregion(margin(zero))` kept a 2.2% margin and `plotregion(margin(l+10))` changed nothing, with no note; now `margin(zero)` puts the data on the frame and `margin(l+10)` adds 10% of the graph's smaller side on the left (0.122 of it in all), copies add as in twoway, an unknown margin is noted and drawn as zero, `plotregion(ifcolor(red))` shades the inner plot region, and `graphregion(margin())` and the graphregion inner options are named as not drawn. (WP-30, P1.20b)
- xline() and yline() draw what twoway draws, in both modes: `xline(2000(500)3000)` drew nothing and named the positions, and draws lines at 2000, 2500 and 3000; `xline(2000 2500 to 3500)` dropped 3000 and draws it; `xline(3000 3000)` drew two lines and draws one; `yline(20, lcolor(red)) yline(10(5)40, lcolor(blue))` drew one blue line and draws a red line at 20 and seven blue ones; `lstyle(foreground)` was named and is drawn in the foreground style; reference lines were drawn over the markers and are drawn behind them. (WP-30, P1.21a)
- `xline()` and `yline()` with `noextend` or `style(unextended)` stop at the axis's scale, inset from the frame by the plot-region margin, as twoway draws them: `dash scatter mpg weight, xline(3000, noextend)` drew the line across the whole plot region and named `noextend`, and now draws it from 10 to 41 on the mpg scale (2.2% of the graph's smaller side short of each edge under s2color), following the axis after every filter move; `extend` and `style(extended)` win; a scheme's `yesno xyline_extend_low` and `xyline_extend_high` are read. (WP-30, P1.21b)
- Dates are placed in their Stata units on every axis. scatteri, pci and pcarrowi coordinates and function's range() on a date axis were drawn at 1970 (scatteri 1300 15400 at 15400 ms); they are now drawn at the dates they denote (01mar2002), and one outside 01jan0100 to 31dec9999 is drawn at its number, as twoway draws it (scatteri 1300 99999999 reaches 1.00e+08), with its axis's ticks there labelled by number where they read "."; only a value past the dates a browser can draw is left out, with a note. Range plots of a date y (rarea, rbar, rspike, rcap, rline, rconnected, rcapsym, rscatter, tsrline) and paired plots of a date y or x now get a date axis where dash drew milliseconds on a numeric axis. A yaxis(2) or xaxis(2) layer no longer turns the first date axis numeric, and a second axis of dates shows dates and reads ylabel(#5, axis(2)), yline(15200, axis(2)) and yscale(range(14900 15500) axis(2)) in days, where it showed numbers near 1e12. A date that shares an axis with a plain number is drawn at its Stata values, as twoway draws (scatter close date) (scatter close obs) (dash drew the dates near 9.8e11 beside 1 to 12), labelled in the first layer's date format, and xlabel(minmax) there ticks Stata values. An explicit base() of bar, spike, dropline or area on a date axis is a date (base(14970) is 26dec2000, where dash drew from 1970). (WP-30, P1.23a)
- dash scatter close open, colorvar(date): a date colour key's ticks, its colorcuts()/colorlevels() bounds, its colordiscrete levels and its zlabel() ticks are read and written in the variable's Stata units, as twoway writes them -- 15,000 ... 15,400, where dash wrote epoch milliseconds (9.78394e+11) -- and colorcuts(15100 15200) now cuts at those days instead of collapsing to the minimum; zlabel(, format(%td)) writes dates. (WP-30, P1.23b)
- Every numeric colour key is written in twoway's %8.0gc whatever the variable's display format (price at %9.0g keys ≤5,000, not ≤5000), and the colour bar is ticked at twoway's key ticks (0, 5,000, 10,000, 15,000) where Bokeh chose its own; zlabel(#N) places ticks by twoway's rule and zlabel(, format()) is honoured on every key. (WP-30, P1.23b)
- Tooltips of histogram, the fits and smooths and kdensity write values in the variable's display format (a date histogram's bins read 02jan2001, not 978393600000); a kdensity's rows are its variable and Density, not x and y; and a histogram's height row is named Density, Frequency, Fraction or Percent, as its y axis is titled, not Count. (WP-30, P1.23b)
- scheme(), a scheme named on one graph and the session's c(scheme) are found as Stata finds them: scheme-NAME.scheme, then NAME.scheme, in each directory of the ado-path in turn (BASE, SITE, the working directory, PERSONAL, PLUS, OLDPLACE and directories added with adopath, each with its first-letter subdirectory), and a scheme file's #include the same way. dash scatter mpg weight, scheme(w30x) with scheme-w30x.scheme in the working directory was refused r(198), and after set scheme of a PLUS, PERSONAL or third-party scheme an unschemed dashboard was drawn in s2color with a warning; each is now drawn in that scheme. A file in the working directory named like one of the twenty-six shipped schemes (s2color.scheme, scheme-s1mono.scheme) no longer replaces the shipped scheme, as in twoway; scheme(mono) and the other theme names draw a scheme file of that name when Stata finds one; and the refusal of a name Stata does not find lists the twenty-six schemes and the six themes. (WP-30, P1.25b)
- A dashboard whose graphs name different schemes is served with each graph in its own scheme, as the saved page draws it: served, scheme(s1rcolor) on the second graph drew it white in the first graph's s1mono. The warning that a dashboard draws one scheme is gone from both modes, and a graph's scheme(mono) draws s1mono on the saved page where it drew s2color with a note. (WP-30, P1.25b)

**WP-31 (drop-in GAPS3, 10oct2026)**

- pcarrow, pcbarrow and pcarrowi heads are drawn as twoway draws them, in the saved page and the served app: sized by msize() (the scheme's symbolsize parrow, 1.53 relative units, by default; they were a fixed 10 pixels), stroked in mcolor()/mlcolor() at mlwidth() and filled in mfcolor() or the series colour (pcbarrow's heads were black); mangle() sets the head angle (28.64 degrees by default; Bokeh's fixed 26.57-degree head is no longer used), barbsize() the barb depth (open strokes at zero) and headlabel moves the labels to the head. lcolor() and lwidth() now style the shaft alone, as in twoway; they coloured and widened the head too. (WP-31, C1)

- rbar ..., mwidth draws each bar as wide as a marker of its msize() in screen units (the scheme's symbol size by default), as twoway's rbar mwidth does: dash rbar yl yh weight, mwidth msize(large) drew one x unit per bar and ignored msize() in silence (mwidth was named), and now draws bars a large marker wide at any x spacing, zoom or filter move; barwidth() beside mwidth is read as that marker size. msize() on rbar without mwidth, and mwidth on histogram, are named; mwidth on any other type is refused, r(198), "option mwidth not allowed", as twoway refuses it. (WP-31, C2)

- dot ..., base(#) widens the y axis to include # as twoway does and no longer sits unread in the spec: dash dot mpg weight, base(50) drew the axis to 41, and now reaches 50 with the ticks unchanged and the dots where they were; recast() on dot is named in the note, as twoway reads it and draws the dot graph unchanged (it was dropped in silence). (WP-31, B5a)

- hover() given inside a layer and again after the comma kept only the rightmost list: dash (scatter mpg weight, hover(make)), hover(price) showed price alone in the tooltip, and now shows make and price, in the order written, each variable once, saved and served. (WP-31, A7)

- lfit and qfit on a saved page after a filter move: the build's fit, dimmed and keyed "(unfiltered)", is now the fit on the kept rows, as the served app draws it: dash scatter mpg weight || lfit mpg weight with a foreign dropdown moved to Foreign drew the all-cars line from 29.105 at weight 1800 and now draws regress mpg weight if foreign == 1's, on n() points over the kept rows' range or range(); a move leaving fewer than two rows draws no line. A recast() lfit or qfit keeps the mark. (WP-31, F1a)

- The fit options are drawn as twoway draws them, in the saved page and the served app: lfit mpg weight, atobs is evaluated at the observed weights (was: a 100-point grid, atobs named in the note); lfitci ..., nofit draws the band alone; fitplot() and ciplot() draw the line and the band as the type named; estopts(), predopts() and estcmd() are run by Stata at registration (fpfit mpg weight, estopts(degree(3)) draws fracpoly's degree-3 fit, was: the default fit with estopts() named) and the layer is drawn as registered after a filter move, marked as computed before the filter; atobs or predopts(residuals) with range() is refused, r(198), "may not combine atobs with range()", as twoway refuses it. (WP-31, C4)

- histogram mpg, gap(20) draws bars 0.8 of a bin wide (was: the full bin), and baroffset() moves histogram and bar bars by bar widths; kdensity mpg, area(74) draws the density 74 times higher and boundary runs it one bandwidth past the data (both were named and ignored); function droplines() draws its drop lines from base() or twoway's default base, and area ..., nodropbase closes the area on the line from its first point to its last, saved and served. gap() outside 0-100, area() not positive, boundary with range(), function base() not a number and a dropline outside range() are refused in twoway's words. (WP-31, C5)

- lfitci and qfitci on a saved page after a filter move: the build's line and band, dimmed and keyed "(unfiltered)" -> regress and predict on the kept rows, the band at level() with stdp, stdf or stdr, as the served app draws it; a move leaving two rows (lfitci) or three (qfitci) draws the line with no band. A band or line drawn as another type by ciplot() or fitplot() keeps the mark. (WP-31, F1b)

- area mpg weight, cmissing(n): the fill breaks at a missing row, one filled region per run of present rows, as twoway draws it (was: bridged, cmissing() named in the note); rarea draws connect() on both bounds (rarea lo hi x, connect(stairstep) is stepped, was: direct and named); lowess, lpoly, lpolyci, fpfit and fpfitci break their line, and the ci types their band, where their own result is missing (was: bridged, named). (WP-31, C6)

- histogram mpg, recast(rarea): drawn as an rarea over the bin centres from 0 to each bin's height, as twoway draws it (was: named, bars drawn); every range type is drawn so, rbar with the histogram's own bars and gap() and baroffset(), and an unknown name prints twoway's two notes and draws rspike; pci and pcarrowi with recast(pcarrow), (pcscatter), (pcbarrow), (pccapsym) or (pcspike) draw that type (was: named, drawn as typed). (WP-31, C7)

- `dash bar mpg weight, colorvar(rep78)`: bars coloured by rep78 with a colour key (was: the series colour, colorvar() named in the note); likewise line, spike, dropline, rbar, rcap, rspike, rline, rscatter, rcapsym, tsline, tsrline and the pc types, and `jitter()` moves the markers of rscatter, rcapsym, pcscatter and pccapsym (was: named); on area, rarea, the fits, kdensity, histogram, function, scatteri, pci and pcarrowi colorvar() is dropped without a word, as twoway drops it (was: named) (WP-31, C8a)
- `dash scatter y1 y2 x, colorvar(z)`: refused, r(198), "option colorvar() cannot be combined with multiple y variables in a scatter plot", as twoway refuses it (was: each y drawn coloured) (WP-31, C8a)

- lowess on a saved page after a filter move: the build's smooth (marked) -> Stata's lowess on the kept rows; above 200 million window operations the line is left empty (WP-31, F1c)

- `dash scatter mpg weight, colorvar(rep78) colordiscrete`: the levels in twoway's colours, hue from blue to red under s2color and stcolor (was: the scheme's p colours), and an unbinned colour bar in the same rule (was: viridis); colorrule(), colorstart(), colorend(), colorlist(), colorfillonly, colorformissing(), colorkeysrange, colorkeysreverse, colorotherlabel(), coloruseplegend, clegend(), plegend() and pcycle() are drawn (was: named in the note); colorvar(i.var) draws (was: r(111)); coloruseplegend without colordiscrete, an unknown colorrule(), and a second colorvar() layer without colorallowmultiple are refused, r(198), in twoway's words (WP-31, C8b)

- `dash dot mpg weight`: 75 dots per observation from the axis base to both ends of the scale, then the marker, as twoway draws them (was: markers only); dotextend(no) runs them to the value, ndots() sets their number and dstyle() dsymbol() dcolor() dfcolor() dsize() dlstyle() dlcolor() dlwidth() style them (were: named or unknown); ndots() other than a number and ndots() or dotextend() on a type twoway refuses them on are refused in twoway's words, r(198); baroffset() on dot is taken in silence (was: named) (WP-31, B5b)

- lpoly on a saved page after a filter move: the build's smooth (marked) -> Stata's local polynomial on the kept rows with its rule-of-thumb bandwidth recomputed; where that fit is exact the line is drawn at 0 (WP-31, F1d)

- `dash scatter mpg weight [aw=price]`: each marker sized by price as twoway sizes it, 1.5*sqrt(w/wmin) times the marker's size up to the scheme's max_wted_symsize, on scatter, connected, dot, dropline, rscatter, rcapsym, rconnected, pcscatter and pccapsym (was: one size, the weight named); on line, bar, area and the other markerless types the weight is taken and named nowhere (was: named); a marker plot with no weight above zero is r(198), as twoway stops it (WP-31, C9)

- lpolyci on a saved page after a filter move: the build's smooth and band (marked) -> lpoly's smooth and its analytic band on the kept rows; where the rule of thumb's fit is exact the line is drawn at 0 with no band (WP-31, F1e)

- `dash scatter mpg weight, xmtick(##5)`: no minor ticks and `xmtick()` named as unsupported -> four minor ticks between each pair of major ticks, as twoway draws them; `xmlabel()`, `ymtick()`, `ymlabel()`, `tmtick()`, `tmlabel()` and their axis(2) copies drawn too; `xlabel(##5)` -> twoway's note "##5 ignored, only allowed for minor ticks" and the default ticks (was: read as `#5`) (WP-31, D1)

- mband and mspline on a saved page after a filter move: the build's knots (marked) -> the cross medians and spline of the kept rows (WP-31, F1f)

- `dash scatter mpg weight, t1title("T1")`: not drawn, and named as unsupported -> drawn above the plot region in ring 1, as twoway draws it; `t2title()`, `b1title()`, `b2title()`, `l1title()`, `l2title()`, `r1title()` and `r2title()` likewise on their sides, the l and r titles turned on their side, inside the legend, note and caption, in the scheme's subheading and body boxes (WP-31, D2)

- fpfit and fpfitci on a saved page after a filter move: the build's fit (marked) -> fracpoly's degree-2 fit on the kept rows and its stdp band (WP-31, F1g)

- `dash scatter mpg weight, title("T", position(6))`: title above, note printed -> title below the plot region; `ring(0)`/`position(0)` inside the plot region, rings ordering the boxes, `box`, its colours, `margin()`, `linegap()`, `justification()`, `alignment()` and `tstyle()` drawn on `title()`, `subtitle()`, `note()` and `caption()` as twoway draws them (WP-31, D3)

- `dash scatter mpg weight, text(30 2000 "$x")` with the `$` kept for dash (`\$x` in a do-file, or `macval()`): drew $x -> draws the global's value, as twoway draws it, by text only; `text(..., tstyle(heading))`: named -> drawn in the heading's size and colour (WP-31, D13)

- dash scatter mpg weight || scatter price weight, legend(ring(0)): top right -> inside at the bottom centre, keys 13 x medsmall (WP-31, D4)

- dash histogram mpg || histogram price: a two-key legend -> no legend (WP-31, C13)

- dash scatter mpg weight, scale(1.5): unchanged -> every text, marker and line 1.5 x; aspectratio(1, placement(e)) xsize(8) ysize(4): refused "not a positive number" -> a square plot region at the right edge; fysize(50), fxsize(50): unchanged -> half the height, half the width (WP-31, D5)

<!-- WP-31 E11 -->

- Axis label, tick and grid sub-options are drawn. dash scatter mpg weight, ylabel(, labgap(large) tlwidth(thick) glwidth(thick) grid) drew the default gap and widths and printed a sub-option note, now twoway's gap (16 px further out) and widths and no note; xlabel(1500(500)5000, alternate) staggers the labels on two rows; ylabel(minmax) on two layers labelled the first layer's extremes, now every layer's (5 and 41 over mpg and trunk); ylabel(##5) drew the default labels, now twoway's note and no labels, as ylabel(none). (WP-31, D6)

- The axis-scale look is drawn. dash scatter mpg weight, yscale(alt) yscale(alt) moved the y axis to the right, now leaves it on the left as twoway does; yscale(noextend) drew the axis line across the whole frame, now from the first to the last tick (10 to 40); yscale(outergap(5)) was named in a note, now widens the border by twoway's 12.4 pt; yscale(lstyle(grid)) draws the grid's line; the default gap between an axis's labels and its title is the scheme's gsize axis_title_gap (1 pt under s2color; Bokeh's 5 px before). (WP-31, D7)

- lwidth(*#) multiplies the unfloored width before the 0.3 pt floor: dash scatter mpg weight, xline(3000, lwidth(*2)) under a scheme whose xyline is vvthin drew twice the floor (0.8 px), now the floor (0.4 px, 3.0 SVG units in twoway); tlwidth(*#), glwidth(*#) and yscale(lwidth(*#)) multiply the scheme's tick, grid and axis widths. (WP-31, E6)

<!-- WP-31 D8 -->

<!-- WP-31 C17 -->

<!-- WP-31 E3 -->

<!-- WP-31 C15 -->

<!-- WP-31 D9 -->

<!-- WP-31 D10 -->

<!-- WP-31 D11 -->

<!-- WP-31 D12 -->

<!-- WP-31 E1 -->

<!-- WP-31 E2 -->

<!-- WP-31 E5 -->

<!-- WP-31 E7 -->

<!-- WP-31 E8 -->

<!-- WP-31 E9 -->

<!-- WP-31 G1 -->

<!-- WP-31 G2 -->

<!-- WP-31 E10 -->

<!-- WP-31 D15 -->

<!-- WP-31 C11 -->

<!-- WP-31 C12 -->

<!-- WP-31 G6 -->

<!-- WP-31 G7 -->

<!-- WP-31 F2 -->

- `dash lfit mpg weight [aw=price-price]` (or any weight zero on every row): twoway's "(note:  regress could not fit model)" alone, and on kdensity and histogram nothing (was: also "74 observation(s) with a zero or negative weight are excluded", naming the internal column __dashw1) (WP-31, A5b)
- `dash scatter mpg weight [aw=price-price]`: r(101) "- not allowed", and `[aw=(price)]` r(198) "( invalid name", as twoway reads a weight on scatter, line, the other glyph types, mspline and mband (was: evaluated); `dash mspline mpg weight [aw=w]`: no note (was: "accepts the weight and does not use it"); a note naming a weight expression names it as typed (was: __dashw1) (WP-31, A5b)

<!-- WP-31 C10d -->

<!-- WP-31 C10e -->

<!-- WP-31 C4b -->

- mband and mspline on data with a missing y or x: the band count and the bands' x range from the complete rows only (auto with mpg missing in 10/12: mband 8 vertices, mspline 78) -> from every row with y or x, as twoway does (9 and 89) (WP-31, C6b)

- lpoly and lpolyci on a saved page after a filter move that leaves an exactly fitted rule of thumb (y an exact polynomial in x, or a few rows): the line drawn at 0 in silence -> the build's smooth and band, dimmed and keyed "(unfiltered)" (WP-31, C11b)

<!-- WP-31 C8c -->

- dash scatter mpg price weight, pcycle(1.5): refused "option seriesid() not allowed" -> drawn in p1 and p2, as twoway draws it; pcycle(0.5): refused -> every series in p1 (WP-31, C8d)

- `dash scatter mpg weight, colorvar(price) colorkeysreverse` drew its colour bar and named colorkeysreverse in the note ("drawn unreversed"); it now draws the same bar in silence, as twoway draws a key that is not discrete the same with colorkeysreverse as without it. (WP-31, C8e)

<!-- WP-31 B5c -->

<!-- WP-31 D1b -->

- Minor-label edges follow twoway: dash scatter mpg weight, xlabel(1000 2000 3000) xmtick(##5) drew the 20 ticks of the rule the list spells, now twoway's lone tick at 0 (xlabel(1000(1000)3000) is still a rule); ymlabel(##2, axis(2) angle(400)) was drawn, now refused r(198) "textangle must be between -360.000 and 360.000"; xmlabel(##2, format(%9.2f)) keeps its format after a filter move on the saved page. (WP-31, D1c)

- `dash scatter mpg weight, t1title("E", position(6))`: E above the plot, position() named -> E below the plot, as twoway draws it; `ring()` orders an edge title on its side (`ring(8)` outside the title); `span` and `nospan` inside an edge title are refused, "option(s) t1title_span(yes) not allowed", r(198), as twoway refuses them (WP-31, D2b)

- After a filter move a contour is cut where twoway cuts the rows kept, and its colour key follows: dash contour price mpg weight, filter(foreign) moved to Foreign kept the build's cuts 5000 10000 on the saved page and, in the served app, a key whose levels no longer matched the bands; both now cut at twoway's 6000 8000 10000 12000 and key them, within the key's first span. (WP-31, B4d)

<!-- WP-31 D13b -->

<!-- WP-31 D3b -->

<!-- WP-31 D4b -->

### Security

- Saved and served pages carry a `default-src 'none'` Content Security
  Policy. The served app's own launcher also sends `X-Frame-Options: DENY`,
  `X-Content-Type-Options: nosniff` and `Referrer-Policy: no-referrer` on
  every response. (WP-20)
- `dash serve` binds 127.0.0.1 by default. It had bound every interface
  while the help said loopback. (S16)
- Under bokeh 3.8, the served app admitted a websocket origin whose host
  only began with an allowed one (`localhost.evil.example`). This is fixed
  whatever Bokeh version runs (WP-25). The launcher warns when
  `BOKEH_ALLOW_WS_ORIGIN` replaces its origin list, and when that list
  admits every site (WP-24).
- The served `function` validator did not check keyword arguments, which
  allowed code execution when the document was built. Keyword arguments are
  now refused, as in the saved renderer. (S16)
- Labels can no longer become live markup. A TeX pair in a slider title, a
  MathJax pass in a Div, and a tooltip field built from a non-name are all
  closed. (WP-20)
- A KPI `color()` could inject CSS into a served card. The colour is now
  translated and sanitised in both modes. Scheme colours are validated as
  hex. (S15, S16)
- `dash_setup` ran a crafted version string or directory name as Python
  code. Values are now read with `sfi.Macro.getLocal`. (WP-20)
- User text is echoed as typed, never as SMCL (no live `{stata}` or
  `{browse}` links), and is never macro-expanded a second time. (WP-19,
  WP-20, WP-23)
- A qualifier's string literals were read as Python source by the renderer.
  They are now data. (WP-24)
- The served rate limiter could be flooded with forged `X-Forwarded-For`
  keys (10,120 sessions a minute against a nominal 60). It now limits per
  client, new clients and total sessions. (WP-19)
- In the `csv` download, a text cell that begins with `=`, `+`, `-`, `@`, a
  tab or a carriage return is prefixed with an apostrophe to guard against
  CSV injection. (WP-21)

- A saved page now holds only the observations its graphs, cards and filters select, and numbers its own rows; a served `link()` group sends only its rows. `filter(price, type(range))` under a graph `if price > 4500` spanned 3799-11385 and now 4749-11385, in both modes; a dropdown within its limit on its reach stays a dropdown; a filter that reaches no observation is greyed out (range, slider) or lists only All; a card following the brush counts the rows its graph shows (`update(brush)` on a layer with `in 3/8`, after a move to Foreign, 23.4 -> 25.66667). The served app numbers its rows as the saved page does, so no row number a browser receives shows where an excluded observation was (a layer `if price > 4500` sent `index` 1, 3, 4, 6, 7, 9 and now sends 0-5). With csv the page still holds every row. (WP-29, P0.11)
- The served app had no credential: while `dash serve`, `python app.py` or
  `bokeh serve app.py` ran, any program on the machine, under any local
  account, could open a session and read every row the dashboard draws
  (measured: `bokeh.client.pull_session`, with no credential and no Origin,
  received all 74 values of auto's `mpg`). The app now requires a key made
  new at every launch. Every page, session, /autoload.js and /metadata
  request without it is refused (403) before any data is read, and the key
  is compared in constant time. `dash serve` hands the key to the app over a
  pipe, never on a command line. It writes the link that holds it to a file
  only you can read, and opens that link at 127.0.0.1, never localhost,
  which another account can answer on ::1. The app never runs without a key:
  started by hand with none (`python app.py`, `bokeh serve app.py`), it
  makes its own and writes its link to a file only you can read, printing
  only that file's path. No Stata log and no server log holds the key, with
  one exception: when no file can be written anywhere to hold the link, dash
  prints the link once, after a warning that the key is now in that output
  and its log, and keeps serving. /health and BokehJS's static files stay
  open. (WP-29, P0.12a)
- dash's working copies of your data -- the specification and data files of
  every render, and `dash serve`'s application -- were written into
  c(tmpdir) with your umask (0644; 0664 under umask 002, which let another
  member of your group rewrite the application before it ran), under
  predictable names, and a symbolic link at such a name was followed. They
  are now written 0600, never through a link, a FIFO or another account's
  file, inside c(tmpdir)dash-<uid>/run-<pid>-<random>/, a folder only you
  can open (0700) that dash removes when the command ends. Where a location
  cannot be private -- a c(tmpdir) other accounts can change, or a disk that
  keeps no permissions -- dash still writes, 0600 wherever it can, and
  prints one note per command naming the location and the remedy; a
  dash-<uid> that is a link, not a folder or another account's is left alone
  and dash uses a private dash-<uid>-<random> folder beside it. As a guard
  against planted names, dash refuses (r(7102)) to write through a link,
  into a pipe or device, or over a hard-linked or another account's file,
  and `dash serve` no longer starts its application by name: it reads the
  file it wrote through a descriptor it checked (type, owner, identity, size
  and SHA-256) and hands that text to Python on the server's standard input,
  with neither the application's folder nor the working folder on Python's
  import path, so an application or module planted beside it is never run.
  The .py that dash build, server writes, which embeds every observation,
  was written with your umask too (0644); it is now written 0600 whatever
  the umask, replace creates a new file, and a symbolic link or another
  account's file at that name is refused (r(7102)) where it used to be
  written through. (WP-29, P0.12b)
- A server started by `dash serve` kept running after Stata was killed or
  crashed -- answering /health, holding its port and the data -- and left
  three copies of the data in c(tmpdir) (the specification, the data and a
  1.25 MB application, 0644). It now stops within about five seconds of the
  Stata that started it ending, however Stata ends, and dash erases the
  specification and data once the application is written and the application
  once the server answers (measured on macOS; Linux and Windows have not
  been measured). (WP-29, P0.13)
- The one-line form without saving() left its preview page (1.3 MB holding
  every row of the graph's variables, 0644) in c(tmpdir) for good, one per
  session, and a second preview overwrote the first. Previews now go to
  c(tmpdir)dash-<uid>/previews/ (0600 in 0700) under unique names; a session
  keeps its newest five, `dash clear` removes them except a page a browser
  was asked to open in the last minute, and the path printed under
  $dash_nobrowser moves there. (WP-29, P0.14)

- Text drawn on a graph no longer reaches a TeX engine. A `$$…$$`, `\(…\)` or `\[…\]` pair in a title, subtitle, note, caption, axis title, tick label, legend key, by() panel title or colour key was typeset by MathJax, whose html package makes `\href{javascript:…}` a live link and `\style{…}` a style attribute; every delimiter in that text is now broken by an invisible word joiner, in the saved page and the served app, before and after a filter move. (WP-30, P1.11a)
- Schemes are looked up by name only. A scheme() holding a blank, a quote, a slash or backslash, a colon or .. is refused r(198) before any file is looked for, and such an #include is read as s2color with Stata's note. A scheme file found along the ado-path is read only if it is a regular file of at most 1,048,576 bytes whose real path lies inside the directory it was found in, so a link out of that directory is not followed; otherwise a note says why and s2color is drawn. Scheme files are read as data and never run, and the ado-path directories are read at build time and never written into the saved page or the served app. (WP-30, P1.25b)
- A dashboard page no longer lets an injected script run. A saved page's
  Content Security Policy used to allow `'unsafe-inline'` scripts, so an
  inline script or event handler that reached the page ran; it now names
  each script dash writes by its SHA-256 hash, and dash refuses to write a
  page holding any other. A served page names a nonce made for each page it
  sends, under `python app.py` and `bokeh serve` alike. `'unsafe-eval'` and
  inline styles stay, because BokehJS needs them; a browser that supports
  only CSP level 1 shows a blank page. The page that forwards a browser to a
  served dashboard, and the page written for a dashboard with nothing to
  show, carry `default-src 'none'`. (WP-30, P1.29)
- On Windows, a dashboard whose path holds `%`, `!`, `^`, `&`, `|`, `<`, `>`
  or `;` is written but no longer opened: the command shell that opened it
  reads `%NAME%` even inside quotes, so it could open another file than the
  one written. dash prints the path instead. (WP-30, P1.29)
- The served app refuses to start, and a saved page is not written, when a bokeh release changes what dash's protections rely on: the page template's blocks that carry the Content-Security-Policy and script nonce (a template without them served a page with no policy), the saved page's head, the websocket origin matcher (a handler that stopped using it re-admitted look-alike origins; `bokeh serve app.py` now makes Bokeh's origin check exact as `python app.py` does, where under bokeh 3.8 it admitted any origin that began with an allowed host), and the key check's AuthProvider hook and token layout (a renamed hook let every request in). Each stops with one message naming the internal and `dash_setup`. The label, legend and tooltip injection checks run in a browser for every bokeh version in the window. (WP-30, P1.30)
- A served dashboard can no longer be exhausted by open sessions: it served every session (25 held sessions took 2 GB at 200k rows), and now admits at most `maxsessions()` at once, answering others with a static HTTP 503 after the key check, closes idle sessions, and decodes its data once and shares it read-only. (WP-30, P1.31a)

### New

- Six more schemes, twenty in all: s1manual, s2manual, s2gmanual, s2color8,
  sttrans (with its 20% colour opacity) and stgcolor_alt. (WP-17)
- `scheme(mytheme)` finds `mytheme.scheme` in the working directory on
  `dash scatter`, `dash build` and a graph's own `scheme()` (WP-17).
  `c(scheme)` is the default scheme, and `dash build` accepts `scheme()`
  (S11).
- New plot types `pcarrowi` and `pccapsym`. `contour`, `contourline`,
  `rpcap` and `rpspike` are refused by name, with what to use
  instead. (WP-22)
- Weights `[aw= fw= pw=]` work on the statistical layers, with twoway's
  per-type rules. (WP-18)
- New options `discrete` (`histogram`), `stdp`/`stdf`/`stdr` (`lfitci`,
  `qfitci`), `mean`/`noweight`/`adjust`/`logit` (`lowess`), and `bands()`
  and `n()` on `mspline`. (WP-18)
- `clcolor()`, `clpattern()` and `clwidth()` work as twoway defines them.
  `mlabangle()` and `mlabformat()` are honoured. (WP-22)
- Every figure has box zoom, undo, redo and a save button that writes
  `dashboard.png`. (WP-21)
- `dash build, csv` adds a Download CSV button that exports the filtered
  rows, in both modes. It is opt-in. (WP-21)
- `layout(bs)` is served with the saved page's rows and spans. (WP-21)
- Resource limits, each with a default, a ceiling and a global that moves
  the default: `dash_max_cells`, `dash_max_graphs`, `dash_max_plots`,
  `dash_max_filter_options`, `dash_max_by_groups`, `dash_max_tabs` and
  `dash_max_filters` (and `dash_max_bytes`, WP-27). The served app takes `--sessions-per-client`,
  `--new-clients-per-minute` and `--sessions-per-minute`. (WP-19)
- `$dash_nobrowser` keeps the browser shut. (WP-23)
- Date variables get date axes, date tooltips, and date slider and range
  filters. (S08)
- The full `xlabel()`/`ylabel()` grammar (`#N`, `minmax`, `a(b)c`,
  `format()`, `grid`) and `xscale(range())` are supported. So is `hover()`,
  which adds variables to the tooltip. (S09)
- `xsize()`, `ysize()`, `aspectratio()` and the scheme's graph size set a
  figure's proportions. The page has a viewport tag, so phones lay it out at
  their own width. (S10)
- `dash serve` inherits the preceding `dash build`'s options (WP-03). A KPI
  percentile may be any `pNN` strictly between 0 and 100, and the twoway
  abbreviations `mbands` and `fn` are accepted (WP-23).

- The time-axis options `tlabel()`, `ttick()`, `ttitle()`, `tscale()` and `tline()` (and `tlabel2()`-style and `axis(2)` forms) are drawn on every twoway graph, with date literals in the axis's own unit: `dash tsline y, tlabel(2000m1(12)2004m1) tline(2002m1)` named them in a note and drew neither, and now draws labels at 2000m1-2004m1 and a line at 2002m1, as twoway does, before and after filter moves; `tmlabel()` and `tmtick()` are accepted and named until minor ticks are drawn. (WP-30, P1.6)
- Time-series operators in plot varlists are drawn, as twoway draws them: `dash line D.close date`, `dash tsline D.close`, `dash lfit close L.close` and `dash scatter L(1/2).close t` were refused r(101) and now draw in both modes on scatter, line, connected, area, bar, spike, dropline, dot, the lfit/qfit/mspline/mband fits, the range and paired types, tsline and tsrline; each series is computed by Stata at build under tsset, titles and keys read "Closing price, D", and the CSV column is headed D.close. (WP-30, P1.7)
- `text()` and `ttext()` are drawn in both modes and after filter moves: `dash scatter mpg weight, text(30 3000 "AAA")` named `text()` as unsupported and drew nothing, and now draws AAA at that data point as twoway does, with placement, justification, orientation, size, colour, box, axis 2, date axes and every by() panel; repeated copies keep their own options; `ttext(12 2001m1 "event")` places a date literal in the x axis's own units. A new limit, `$dash_max_added_text` (default 1,000 texts times panels), bounds them. (WP-30, P1.10)
- Six more StataCorp schemes, twenty-six in all: meta, stcolor_meta, stcolor_mv, stcoloralias, stgcolor_meta and stgcolor_mv. scheme(meta) and the others were refused r(198), and a session set to one of them (set scheme stcolor_meta) was drawn as s2color with a warning; each is now drawn as twoway draws it in both modes (stcolor_meta's solid #c10534 yline(), stgcolor_meta's 3.987 x 2.392 proportions, meta's 8-point tick labels and legend at 4 o'clock), and an #include of one of them in a scheme file of yours resolves. stcoloralias is drawn as stcolor: its zyx2rule colorvar is not read, and twoway draws a colorvar() scatter the same under both. (WP-30, P1.25a)
- `dash` stores the file it wrote in `r(filename)`, as an absolute path:
  the one-line form's page (or its temporary preview), `dash build`'s
  page and `dash build, server`'s app. A command that writes a file notes
  once, when Stata holds a graph in memory, that `graph export` writes
  that graph and not the dashboard. The help gains Stored results and says
  what `graph export`, printing and the toolbar can and cannot do.
  (WP-30, P1.28a)
- Every dashboard toolbar, saved and served, has a Save as SVG button beside the PNG save: it downloads a vector SVG of the same figures (dashboard.svg, or g1.svg for a layout(bs) item), drawn from what is on screen after any filter move. Before, the only image was a PNG at the screen's resolution. dash draws no figure with an SVG backend, which would break the PNG save. (WP-30, P1.28b)
- `dash serve` takes `maxsessions(#)` (default 20) and `idletimeout(#)` minutes (default 60, 0 = never), and a served app takes `--max-sessions` and `--idle-timeout` (or `DASH_MAX_SESSIONS` and `DASH_IDLE_TIMEOUT` under `bokeh serve`); the app prints "preparing the dashboard (N rows, ...)" and builds once before it listens, so no reader pays the first build. (WP-30, P1.31a)

### Fixed

- A `(` inside a quoted option value no longer deletes later `||` layers.
  The word `filter(` inside a quoted title is no longer turned into a
  widget and cut from the title. (WP-01)
- `dash serve, port()`, `timeout()` and `nobrowser` work, and a real launch
  is tested. (WP-03, WP-23)
- A KPI given a graph's name no longer erases the graph. (WP-04)
- `dash_setup` no longer reports success after a failure. It passes the
  minimum versions to pip, retries with `--user`, shows pip's output, and
  checks that the renderer and schemes are installed (WP-06). It no longer
  hides dash's later warnings in the same session (WP-11).
- With no Python linked, `dash` says to run `dash_setup` instead of showing a
  raw Python error. A broken or partly loaded Mata library is repaired or
  named. (WP-07)
- Malformed UTF-8 (overlong forms, surrogates, code points above U+10FFFF) is
  refused with r(198). Control characters in titles are escaped and no
  longer break the build. (WP-08)
- A Windows `saving("C:\dir\out.html")` writes to that path, and
  `saving("my..report.html")` is accepted. (WP-08, WP-24)
- The served dashboard now matches the saved one in:
  - `pci` (which drew nothing) and `fpfitci`'s band;
  - hover tooltips for every plot type;
  - legend keys;
  - `mlabel()`;
  - `layout()` placement;
  - KPI `fmt()`;
  - `xlabel()`, `yaxis(2)` and `colorvar()`.

  (WP-09, WP-10, WP-12)
- After a served filter move:
  - computed layers are refit correctly;
  - each layer keeps its own `if` and `in`;
  - a brushed selection is cleared, as on the saved page;
  - linked `by()` graphs show the right rows.

  (WP-11, WP-23, 7c2c918)
- `lwidth(thick)` is kept on `lowess`, `mspline`, `mband` and `fpfit` when
  the curve cannot be computed. `rbar` honours its colour and line options.
  (WP-09)
- A `layout(bs)` page holding a KPI or a filter is no longer blank in the
  browser (WP-16). A saved dashboard with a filter renders when a date
  variable holds a missing value (WP-21).
- `xtick()` draws ticks beside the labels. `ylabel2()`/`xlabel2()` take
  `ylabel()`'s grammar. Filter labels may hold any character. (WP-23)
- `ylabel(#5, grid)` is no longer ignored. `title()` `size()` and `color()`
  and `xscale(range())` work in served mode. (WP-14)
- `scatteri`, `pci` and `pcarrowi` values are read as twoway reads them, and
  malformed values are refused where they used to crash the build
  (c036fb6). A dashboard of immediate graphs alone builds, with or without
  data in memory (a2c7502).
- A title or qualifier holding a double quote followed by an apostrophe is
  stored as typed. (WP-23)
- `name(g1, replace)` stores the graph as g1, so `layout()`, `tabs()`,
  `link()` and `exclude()` find it (0744eb6). `exclude()` protects its graph
  whatever order it was registered in (dbe24bc).
- A do-file running under `version 16` or `version 17` can name graphs and
  KPIs. (WP-19)
- `dash.pkg` carries a Distribution-Date, and its version matches
  `dash.ado`. (WP-05)

### Changed behaviour (may need your do-files changed)

- The twenty shipped schemes are now `dash-<name>.scheme` files, installed in
  `PLUS/d/` instead of `PLUS/s/<name>.scheme` and `PLUS/e/economist.scheme`.
  `scheme(s2color)` and `scheme(s2color.scheme)` work as before. (after WP-28)
- `scheme(nosuchthing)` and an unknown `theme()` are now r(198) on every
  entry point, not a warning. An unknown session `c(scheme)` still warns and
  uses s2color. (WP-17)
- Option values are validated as twoway validates them. A bad value such as
  `lwidth(-1)` or `yaxis(3)` is r(198) or r(111), naming the option. A style
  name dash cannot draw, such as `msize(abc)`, is noted and drawn, as in twoway (WP-15).
  `mlabel()` on `mspline` or `mband` is r(103), as in twoway (4ede074).
- `iweight` is refused with r(101) wherever twoway refuses it. So are
  weights on `lowess`, `aweight`/`pweight` on `histogram`, and `pweight` on
  `kdensity`, `lpoly` and `lpolyci`. A weight expression such as
  `[aw=price+1]` is r(198): generate the variable first. (WP-18)
- `dash bar price` or `dash scatter mpg` with a single variable is r(102) at
  registration. (WP-16)
- Naming rules:
  - Reusing an existing graph or KPI name needs `name(x, replace)`.
  - A command that gives `name()` twice is r(198), as in twoway.
  - Graph names are limited to 22 characters and KPI names to 18.
  - Names holding two underscores in a row, and the name `_all`, are
    refused.

  (WP-04, WP-19, a17c552, 9f48cf7, f92ef65)
- Unbalanced parentheses and stray text between plot groups are r(198), as
  in twoway. (WP-01)
- An option after the top-level comma now wins over the same option inside
  a plot group, as in twoway. (WP-04)
- `legend(top|bottom|left|right)` is r(198), naming the `position()` meant.
  (WP-23)
- `dash build` refuses these `layout()` values: one it cannot read, a
  placement naming no registered item, and a name repeated in `layout()`.
  (WP-20, WP-21)
- Past the resource limits, too many graphs or plots, or too many exported
  values, give r(134). Dropdowns, `by()` panels, tabs and filters are
  clamped with a warning. (WP-19)
- `bw()` means `bwidth()` on the bandwidth types and `barwidth()` on the bar
  family. `nodraw` is honoured without a note. (WP-13)
- A KPI draws one card, not one per `by()` panel. `update()` names a mode.
  (f92ef65)
- `saving()` into a directory that does not exist is r(603). (WP-23)
- A variable whose name begins `__dash` is refused with r(110) before any
  export, naming the variable and the prefix, and telling you to rename
  it: only names beginning `__dashq` were reserved before, so
  `dash scatter mpg weight if __dash_row__ > 0` used to build with the
  variable silently overwritten by dash's own row identity. Every column
  dash makes -- the qualifier columns, the row identity `__dash_row__`,
  and the marker-label and jitter columns, previously `__mlabel__*`,
  `__mlabel_values__`, `__mlabel_x__`, `__mlabel_y__`, `_x_jit` and
  `_y_jit` -- is now named under that one prefix (`__dash_mlabel_*`,
  `__dash_xjit`/`__dash_yjit`, `__dash_pc_row__`, `__dash_<type>_label`),
  so a variable named `__mlabel__y`, `_x_jit` or `top` now draws with its
  own values where it used to be read as label text or overwritten.
  (WP-28, G1)
- A string variable named as a plot variable (`dash scatter make mpg`,
  say) is refused with r(109), the same code and words `twoway` gives for
  the same command, on every route and in both renderers -- previously it
  was drawn as meaningless glyphs with no note, or crashed the render for
  a fit or a histogram. `colorvar()`, `mlabel()`, `hover()` and `by()`
  still take a string variable. (WP-28, G2)

- line, connected, area, rline, rarea and rconnected join their points
  in the data's order unless `sort` or `sort(varlist)` is given; add
  `sort` for the old picture along x. An invalid `sort()` is refused
  r(198) in `twoway`'s words (`sort(x*)`: `* invalid name`;
  `sort(nosuch)` on line: `variable nosuch not found`, `option sort()
  incorrectly specified`), where dash accepted it with a note.
  (WP-29, P0.1)
- `axis(#)` is refused as twoway refuses it, r(198), with twoway's message and in its order, where dash drew on the first axis with rc 0: an `axis()` naming an axis no layer is drawn on (`ylabels(20 30, axis(2)) not allowed, yaxis2 does not exist`), an `axis()` given twice, `AXIS()` in capitals, a second comma (`invalid 'axis'`), and the first axis's options on a graph whose every layer is on `yaxis(2)` (`ylabels(5000 10000) not allowed, yaxis1 does not exist`); the new options `ytick2()`, `xtick2()`, `yline2()` and `xline2()` are dash's spellings of the `axis(2)` forms (WP-29, P0.5)
- `pi`, `e`, `x**2`, `x%2`, `x//1`, a leading `+` and full-width names are refused with twoway's r(111), r(198) and r(133), and a too-long expression with r(130); registering a function evaluates it once, so a later data or estimate change does not move it, `runiform()` advances the random-number stream, data with at least n() observations are marked changed, and a graph whose points exceed c(macrolen) is refused r(134) (WP-29, P0.6)
- A served dashboard's address now needs its key: http://localhost:5006/,
  bookmarked or typed, answers 403. Open the link in the file `dash serve`,
  `python app.py` or `bokeh serve app.py` names (each prints the file's
  path, never the key), http://127.0.0.1:<port>/?token=<key>; under bokeh
  serve, start it with --allow-websocket-origin 127.0.0.1:<port> or the page
  stays blank. To choose the key, set DASH_SERVE_TOKEN (32 to 128 of A-Z a-z
  0-9 _ -) and open /?token=<that value> (/app?token=<that value> under
  bokeh serve); the app then writes no link file. `python app.py` stops with
  exit status 2, and bokeh serve refuses every session, when
  DASH_SERVE_TOKEN holds anything else. If the link file cannot be written
  anywhere, the server is no longer stopped: the link is printed once, after
  a warning line, and the dashboard keeps serving. (WP-29, P0.12a)

- A `..` or `...` anywhere but at the end of a style list is refused as twoway refuses it: `dash scatter mpg turn weight, mcolor(red .. blue)` was drawn with a note and is now `mcolor(red .. blue):  invalid syntax`, r(198). An element of a style list that a y uses is held to the option's bounds as one value is: `dash line mpg turn weight, lwidth(thick 20000)` was drawn and is now refused, r(198), as twoway refuses it. A quoted element of a style list that holds only blanks and that a y uses is refused: `dash scatter mpg turn weight, mcolor(" " blue)` was drawn and is now `dash: mcolor() element 1 is blank; use . for the default (got: " " blue)`, r(198); write `.` for the default. (WP-30, P1.1a)
- mlabel() now refuses what twoway refuses, with twoway's codes and words. `..` or `...` anywhere is `.. not allowed in option mlabel()`, r(198), and `=` is `=exp not allowed`, r(101); both were r(111), `variable .. not found`. A list of `.` alone is `too few variables specified`, r(102), where it was r(111). Every variable named must exist, even past the last y, r(111). On histogram and function, `mlabel(nosuch ..)` was dropped and is now refused, r(198), and on histogram `mlabel(= make)` is now refused `invalid syntax`, r(198). On mspline and mband the same checks now run before the r(103) refusal, so `mspline mpg weight, mlabel(make ..)` is r(198) where it was r(111). A list in barwidth() on rbar, histogram, rcap or rspike, or in base() on rbar or histogram, is now refused in twoway's words, `option barwidth() not allowed`, r(198), where dash said `must be a positive number`. (WP-30, P1.1b)
- A `format()` in `xlabel()`, `ylabel()`, `xtick()`, `ytick()`, their minor and `axis(2)` forms, or in the colour key's `zlabel()`, that twoway refuses is refused in its words, `invalid format, <fmt>`, r(198), such as `format(bogus)`, `format(%9.9f)` or `format(%2046.0f)`; dash named it in a note and drew unformatted ticks or the key. (WP-30, P1.5)
- `xvarformat()` and `yvarformat()` written after the plot groups' comma are refused as twoway refuses them, `option xvarformat() not allowed`, r(198); dash named them in its note and drew the graph. Inside a plot they are now honoured. (WP-30, P1.5)


- Date literals and time-axis forms twoway refuses are refused in twoway's words (all rc 0 before): a date literal in `xlabel()`, `xtick()`, `xmlabel()`, `xmtick()` (`invalid label specifier, :  2000m1:`, r(198)), `xline()` (`invalid line argument, 2002m1`, r(198)) or `xscale(range())` (`range() invalid -- invalid numlist`, r(121)); a t-option date literal when the first plot is lfit, qfit, lfitci, qfitci, lpoly, lpolyci, kdensity, function, scatteri, pci or pcarrowi, or on a numeric or `%tc` axis; an invalid literal (`tline(2000m13)`); `tline()` or `tscale(range())` literals on a `%-t` axis; `tm()` and `ts()` (`option tm() not allowed`, r(198)). (WP-30, P1.6)
- Operated plot variables are refused where twoway refuses them, in its words (all r(101) "factor-variable and time-series operators not allowed" before): no tsset ("time variable not set", r(111)); a string variable ("make:  may not use time-series operators on string variables", r(109)); a factor variable ("factor-variable operators not allowed", r(101)); by() with an operated variable ("not sorted", r(5)); a bare sort with an operated x on scatter, line and the other types that sort on x ("option sort() incorrectly specified", r(198)). (WP-30, P1.7)
- `connect()` and `cmissing()` are checked as twoway checks them (each was rc 0 with a note before): a misplaced `..` is refused (`connect(l .. J):  invalid syntax`, `cmissings(n .. y):  invalid syntax`, r(198)); an unknown `cmissing()` value is refused on the types twoway refuses it on, after twoway's two notes (` not allowed`, r(101)), and noted elsewhere; an unknown `connect()` name prints twoway's note and draws direct; `clwidth()` out of range on a scatter given `connect()` is refused (`gm_linewidth must be between 0.000 and  1.0e+04`, r(198)). (WP-30, P1.8a)
- `recast()`, `recastas()` and `type()` on lfitci, qfitci, lpolyci and fpfitci are refused as twoway refuses them (`recastas() option not allowed`, or `type() option not allowed`, r(198)), where dash took them with a note; `rec()`, `reca()` and `recas()` are refused with `option rec() not allowed`, r(198). (WP-30, P1.8b)
- `horizontal` and `vertical` are refused where twoway refuses them, in its words (both were accepted with a note): `horizontal vertical` together (`may not combine options horizontal and vertical`, r(198)); `horizontal` on scatter, line, connected, the fits and smoothers, scatteri and tsline, and `vertical` on those and on kdensity and function (`option horizontal not allowed`, r(198), naming the flag as typed), judged after `recast()` as twoway judges it. (WP-30, P1.9a)
- `text()` and `ttext()` are refused where twoway refuses them, r(198) in twoway's words, where dash accepted them with a note: a malformed point (`invalid point, BAD 30`), an axis pair the graph lacks (`text() option invalid, specified axis pair (2 1) not in graph`), an unknown sub-option (`option nosuch() not allowed`) and a ttext() date the axis cannot read (`2001m13 is not a number`); more than `$dash_max_added_text` texts times panels is refused r(134). (WP-30, P1.10)
- A `||` piece with no plot is read as twoway reads it: `dash scatter mpg weight || , title(T)` refused every option in the trailing `|| , options` piece ("unrecognised plot type ','"), and now gives the graph its options, as `|| if exp` gives its [if]; `(a) || line y x` is no longer refused as stray text, `(a) (b), opts || c` no longer folds c into the options, and `(a) | (b)`, which twoway refuses, is no longer accepted. (4fda248)
- A number in `msize()`, `mlabsize()`, `mlabgap()`, `size()`, `labsize()` or `legend(size())` is in Stata's relative units (1 = 3.84px), not pixels: `msize(10)` draws 38.4px where it drew 10px, and `mlabgap(5)` leaves 19.2px of gap where it left 5. A do-file written for dash's pixel reading needs its sizes divided by 3.84 or written as keywords. (WP-30, P1.12a)
- A line width twoway refuses is refused with twoway's message, gm_linewidth must be between 0.000 and  1.0e+04, r(198), and a second line naming the option. lwidth(*-1), lwidth(-1pt), mlwidth(-0.5in), clwidth(*-1), alwidth(-1pt) and lwidth(1e5rs) were drawn at the scheme's width with a note. lwidth(-1) and lwidth(10001), refused before in dash's own words, now print twoway's message first. As before, dash refuses a negative width on every plot type, where twoway refuses it only where it draws the line or outline. lwidth(*40000) and economist's lwidth(20000pt), which twoway refuses once it knows the default width and the graph's size, are noted and drawn at the default. (WP-30, P1.12b)
- A colour written with commas in a plot colour option is refused, as twoway refuses it: dash scatter mpg weight, mcolor(255,0,0) drew red, now stops with invalid '0', r(198). Write the triplet with blanks, mcolor("255 0 0"). (WP-30, P1.13a)
- by() arguments twoway refuses are refused in its words (each was accepted, most with a note): `rows()` with `cols()` (`may not specify both rows() and cols()`, r(198)); a `rows()` or `cols()` that is not one positive integer and a `holes()` that is not a list of up to 300 positive integers (`rows() invalid -- invalid number, outside of allowed range`, r(125), and twoway's r(121), r(123), r(126) forms); a repeated `rows()`, `cols()`, `holes()`, `style()`, `compact`, `iscale()`, `imargin()`, `colfirst`, `total`, `missing` or rescale word, or a capitalised sub-option such as `YRESCALE` or `TITLE()` (`option YRESCALE not allowed`, r(198)); an unknown by() sub-option such as `bogus` (`option bogus not allowed`, r(198)); `iscale()` below 0 or above 10,000 (`gm_linewidth must be between 0.000 and  1.0e+04`, r(198)). (WP-30, P1.15b)
- barwidth() on rcap and rcapsym is refused, r(198), with twoway's message option barwidth() not allowed, naming the spelling given (barw() to barwidth()); dash accepted it and drew nothing different. (WP-30, P1.17a)
- angle() outside -360 to 360 in xlabel(), ylabel(), xtick(), ytick(), xmlabel(), ymlabel(), xmtick(), ymtick() and their axis(2) forms is refused, r(198), with twoway's message textangle must be between -360.000 and 360.000; it was drawn. dash refuses it under nodraw too, where twoway checks it only when the graph is drawn. (WP-30, P1.18a)
- An xscale() or yscale() lwidth() below 0 or above 10000 is refused, r(198), with twoway's message gm_linewidth must be between 0.000 and 1.0e+04. (WP-30, P1.18a)
- An xscale() or yscale() sub-option twoway refuses, such as yscale(OFF), yscale(Alt), xscale(bogus) or a word given twice in one option, is refused, r(198), with twoway's message (option OFF not allowed); it was named in a note and drawn. (WP-30, P1.18a)
- `legend()` and the axis label and tick options (`xlabel()`, `ylabel()`, `xtick()`, `ytick()`, `xmlabel()`, `ymlabel()`, `xmtick()`, `ymtick()`, `zlabel()`) refuse what `twoway` refuses, with its return code and words, where `dash` named and ignored it: a sub-option in capitals (`legend(OFF)`: `option OFF not allowed`, r(198)); a spelling `twoway` does not accept (`legend(po(9))`, `ylabel(, a(45))`, `legend(garbage)`); one given twice in one option (`legend(c(2) cols(1))`: `option cols() not allowed`); the wrong form (`ylabel(, labs)`: `option labs incorrectly specified`); a bad `cols()`/`rows()`/`holes()` (`legend(c(red))`: r(121) `cols() invalid -- invalid number`); and a `label()` key that is no positive integer (r(198)). The titles and axis titles refuse the same three forms (`title("T", SIZE(small))`: `option SIZE() not allowed`, r(198)), and `ytitle("Y", prefix suffix)` is refused with `options prefix and suffix may not be combined`. A capitalised sub-option of `xline()`/`yline()` is no longer applied; it is named. (WP-30, P1.19)
- plotregion() and graphregion() refuse what twoway refuses, r(198) in twoway's words (all rc 0 before, most with no note): an unknown sub-option (`option bogus() not allowed`), a capitalised one (`option COLOR() not allowed`), one shorter than twoway's minimum (`option st() not allowed`), a sub-option given twice in one copy (`option c() not allowed`) and a word after a comma inside the region (`invalid 'lcolor'`). (WP-30, P1.20a)
- xline() and yline() refuse what twoway refuses, in its words (rc 0 before): `xline(abc)`, `xline(1(0)5)`, `xline(nan)` and more than 2,500 positions in one copy (`invalid line argument, …`, r(198)); `xline(, lcolor(red))` (`something required`, r(100)); an unknown, short, capitalised or repeated sub-option (`option foo not allowed`, `option LColor() not allowed`, r(198)). A dashboard whose reference-line positions times by() panels pass 10,000 is refused r(134); set global dash_max_reflines to draw more (at most 100,000). (WP-30, P1.21a)
- `mlabvposition()` is refused where twoway refuses it, in twoway's words (all rc 0 with a note before): on rarea, rbar, rcap, rcapsym, rconnected, rline, rscatter, rspike and tsrline (`rscatter requires 3 variables: y y2 x p9`, r(103)), on lfit, qfit, fpfit, lfitci, qfitci, fpfitci, mspline and mband (`too many variables specified: y x p9`, r(103)) and on lowess, lpoly, lpolyci and kdensity (`too many variables specified`, r(103)); a second copy (`option mlabvposition() not allowed`, r(198)); two names (`option mlabvposition():  too many names specified`, r(103)); an expression (`* invalid name`, r(198)); a variable that does not exist (`variable nosuch not found`, r(111)). (WP-30, P1.24)
- scheme() takes a scheme's name as Stata finds its file: a name holding a blank, a control character, a colon, a backtick or a dollar sign, or longer than 87 characters, such as scheme(my theme), was looked for as a file in the working directory and is now refused r(198) with the list of schemes; twoway does not find such a name either. Rename the file, for example to scheme-mytheme.scheme. (WP-30, P1.25b)
- dash prints its notes as twoway prints its notes. Each is one line, (note:  dash: ...), in text colour; it shows under quietly and set output error, and capture hides it. It never names dash's files or Python source lines. Before, the renderer's notes were red Python warnings (".../dash_render.py:8679: UserWarning: dash: mcolor(notacolor) is not a recognised colour; ..." and a source line) that quietly did not hide, and dash.ado's own notes ("dash: ignoring unsupported option(s): play()", "dash: note: ...") were hidden by quietly. dash's copies of twoway's own "(note:  regress could not fit model)" and "(note: scheme X not found, using s2color)" print as plain text that quietly hides, as twoway's do. A do-file that searches a log for "UserWarning", or for a line beginning "dash: ignoring unsupported option(s)" or "dash: note:", now finds "(note:  dash: ...)". (WP-30, P1.26a)
- A layer whose own if or in keeps no observation is drawn in silence in both modes, as twoway draws it. Before, the saved page printed "dash: graph 'g1' plot 3 (bar) drew nothing from 74 observations." for line, area, spike, dropline, rcap, rline, rscatter, pcspike, bar, rbar and rarea layers, and the served app printed nothing. twoway's own "(note:  regress could not fit model)" for such an lfit is still printed, in both modes. The served app run by python app.py, bokeh serve or dash serve prints each of its notes once per process, as (note:  dash: ...) on its standard error, where each session printed Python warnings with the app's path and source lines. (WP-30, P1.26b)
- In batch (c(mode) batch) and after `set graphics off`, dash opens no browser window, as twoway displays no graph there: `dash build` and the one-line form write the page and print where it is, a one-line preview adds that it is temporary and that saving() keeps a page, and `dash serve` starts without a browser. A do-file run with `stata -b` used to open one tab per dashboard. Interactive Stata, the console included, still opens the window. (WP-30, P1.27)
- saving() is read as twoway reads it, on the one-line form and on `dash build`: a sub-option other than replace and asis, written in full, in lower case and once each, is refused with twoway's "option bogus not allowed", r(198), and an unquoted name holding a blank with "invalid syntax,  file.html not allowed", r(198). `saving(n, bogus)` used to write a file named "n, bogus.html" and `saving(my file.html)` wrote "my file.html"; put such a name in quotes. (WP-30, P1.27)
- `twoway`, `tw`, `two`, `twow`, `twowa`, `graph`, `gr`, `gra` and `grap`, in any case, in front of the plots are refused as twoway refuses them after `twoway`, "twoway is not a twoway plot type", r(198): dash replaces twoway, so `dash twoway scatter mpg weight` is `twoway twoway scatter mpg weight`. They gave r(198), "unrecognised plot type". To run a command copied from a do-file, replace its `twoway` (or `graph twoway`) with `dash`. (WP-30, P1.27)
- `r()` after `dash` holds only `r(filename)`, and nothing after a
  registration, `dash kpi`, `dash clear`, `dash serve` or a refusal, as
  `twoway` clears `r()`. It used to hold dash's internal results, such as
  `r(fn)` naming dash.ado after the one-line form, `r(open)` and `r(flag)`
  after `dash build`, and `summarize`'s `r(mean)` after `dash kpi`.
  `saving(fig.png)`, or any suffix `graph export` writes, now writes
  fig.html with a note; the one-line form and `dash build` wrote
  fig.png.html silently. (WP-30, P1.28a)
- On a Stata older than 19, dash and dash_setup stop before doing anything else with "dash requires Stata 19 or later; this is Stata 18.5" (the running release) and r(9). Stata 16-18.5 used to run dash untested, and Stata 14-15 stopped with Stata's own "cannot run version 16.0 programs". A do-file that sets version 16 or 17 on Stata 19 is unaffected. (WP-30, P1.35)

- kernel() on scatter, line, connected, area, bar, spike, dropline, dot, tsline, tsrline, rarea, rbar, rspike, rcap, rline, rconnected, rcapsym, rscatter, pcspike, pccapsym, pcarrow, pcbarrow, pcscatter, pci, pcarrowi, scatteri, lfit, qfit, lfitci, qfitci, fpfit, fpfitci, lowess, mspline, mband, histogram and function is refused, r(198), with twoway's line option kernel() not allowed; dash accepted it and drew nothing different. (WP-31, C3)
- n() on scatter, line, connected, area, bar, spike, dropline, dot, tsline, tsrline, rarea, rbar, rspike, rcap, rline, rconnected, rcapsym, rscatter, pcspike, pccapsym, pcarrow, pcbarrow, pcscatter, pci, pcarrowi, scatteri, fpfit, lowess and histogram is refused, r(198), with twoway's line option n() not allowed; dash accepted it and drew nothing different. (WP-31, C3)
- level() on scatter, line, connected, area, bar, spike, dropline, dot, tsline, tsrline, rarea, rbar, rspike, rcap, rline, rconnected, rcapsym, rscatter, pcspike, pccapsym, pcarrow, pcbarrow, pcscatter, pci, pcarrowi, scatteri, lfit, qfit, fpfit, lowess, lpoly, mspline, mband, kdensity, histogram and function is refused, r(198), with twoway's line option level() not allowed; dash accepted it and drew nothing different. (WP-31, C3)
- bwidth() on scatter, line, connected, area, bar, spike, dropline, dot, tsline, tsrline, rarea, rbar, rspike, rcap, rline, rconnected, rcapsym, rscatter, pcspike, pccapsym, pcarrow, pcbarrow, pcscatter, pci, pcarrowi, scatteri, lfit, qfit, lfitci, qfitci, fpfit, fpfitci, mspline, mband, histogram and function is refused, r(198), with twoway's line option bwidth() not allowed; dash accepted it and drew nothing different. (WP-31, C3)
- bands() on scatter, line, connected, area, bar, spike, dropline, dot, tsline, tsrline, rarea, rbar, rspike, rcap, rline, rconnected, rcapsym, rscatter, pcspike, pccapsym, pcarrow, pcbarrow, pcscatter, pci, pcarrowi, scatteri, lfit, qfit, lfitci, qfitci, fpfit, fpfitci, lowess, lpoly, lpolyci, kdensity, histogram and function is refused, r(198), with twoway's line option bands() not allowed; dash accepted it and drew nothing different. (WP-31, C3)
- range() on scatter, line, connected, area, bar, spike, dropline, dot, tsline, tsrline, rarea, rbar, rspike, rcap, rline, rconnected, rcapsym, rscatter, pcspike, pccapsym, pcarrow, pcbarrow, pcscatter, pci, pcarrowi, scatteri, fpfit, fpfitci, lowess, lpoly, lpolyci, mspline, mband and histogram is refused, r(198), with twoway's line option range() not allowed; dash accepted it and drew nothing different. (WP-31, C3)
- base() on scatter, line, connected, tsline, tsrline, rarea, rbar, rspike, rcap, rline, rconnected, rcapsym, rscatter, pcspike, pccapsym, pcarrow, pcbarrow, pcscatter, pci, pcarrowi, scatteri, lfit, qfit, lfitci, qfitci, fpfit, fpfitci, lowess, lpoly, lpolyci, mspline, mband, kdensity and histogram is refused, r(198), with twoway's line option base() not allowed; dash accepted it and drew nothing different. (WP-31, C3)
- degree() on scatter, line, connected, area, bar, spike, dropline, dot, tsline, tsrline, rarea, rbar, rspike, rcap, rline, rconnected, rcapsym, rscatter, pcspike, pccapsym, pcarrow, pcbarrow, pcscatter, pci, pcarrowi, scatteri, lfit, qfit, lfitci, qfitci, fpfit, fpfitci, lowess, mspline, mband, kdensity, histogram and function is refused, r(198), with twoway's line option degree() not allowed; dash accepted it and drew nothing different. (WP-31, C3)
- bin() on scatter, line, connected, area, bar, spike, dropline, dot, tsline, tsrline, rarea, rbar, rspike, rcap, rline, rconnected, rcapsym, rscatter, pcspike, pccapsym, pcarrow, pcbarrow, pcscatter, pci, pcarrowi, scatteri, lfit, qfit, lfitci, qfitci, fpfit, fpfitci, lowess, lpoly, lpolyci, mspline, mband, kdensity and function is refused, r(198), with twoway's line option bin() not allowed; dash accepted it and drew nothing different. (WP-31, C3)
- width() on scatter, line, connected, area, bar, spike, dropline, dot, tsline, tsrline, rarea, rbar, rspike, rcap, rline, rconnected, rcapsym, rscatter, pcspike, pccapsym, pcarrow, pcbarrow, pcscatter, pci, pcarrowi, scatteri, lfit, qfit, lfitci, qfitci, fpfit, fpfitci, lowess, lpoly, lpolyci, mspline, mband and function is refused, r(198), with twoway's line option width() not allowed; dash accepted it, drew it as barwidth() on bar and rbar, and drew nothing different elsewhere. (WP-31, C3)
- start() on scatter, line, connected, area, bar, spike, dropline, dot, tsline, tsrline, rarea, rbar, rspike, rcap, rline, rconnected, rcapsym, rscatter, pcspike, pccapsym, pcarrow, pcbarrow, pcscatter, pci, pcarrowi, scatteri, lfit, qfit, lfitci, qfitci, fpfit, fpfitci, lowess, lpoly, lpolyci, mspline, mband, kdensity and function is refused, r(198), with twoway's line option start() not allowed; dash accepted it and drew nothing different. (WP-31, C3)
- barwidth() on scatter, line, connected, tsline, tsrline, rarea, rspike, rcap, rline, rconnected, rcapsym, rscatter, pcspike, pccapsym, pcarrow, pcbarrow, pcscatter, pci, pcarrowi, scatteri, lfit, qfit, lfitci, qfitci, fpfit, fpfitci, lowess, lpoly, lpolyci, mspline, mband, kdensity and function is refused, r(198), with twoway's line option barwidth() not allowed; dash accepted it and drew nothing different (on rcap and rcapsym it was already refused, naming the spelling typed). (WP-31, C3)

- colorvar() and by() with a time-series operator (colorvar(L.mpg), by(L.foreign)) are refused r(101), "factor-variable and time-series operators not allowed", as twoway refuses them; they were r(198) on tsset data and r(111) otherwise. mlabel(L.make) is r(111) "variable L not found", as in twoway; it was r(198) on tsset data. (WP-31, A6)

- A date literal in a y label, tick or scale option is refused as twoway refuses it: dash scatter mpg weight, ylabel(2000m1) drew, and is now refused, r(198), "invalid label specifier, :  2000m1:", as are ytick(), ymlabel(), ymtick() and their axis(2) forms; yscale(range(2000m1)) is r(121), "range() invalid -- invalid numlist"; a %tm y variable does not change it, as in twoway. (WP-31, A8)

- The thirteen shorter plot-type names only dash took -- ar, ba, sp, lfi, qfi, low, lpo, fp, kde, dr, tsl, tsrl and msp, and their longer prefixes short of the full name -- are refused, r(198), with twoway's line "lfi is not a twoway plot type"; dash drew them as area, bar, spike, lfit, qfit, lowess, lpoly, fpfit, kdensity, dropline, tsline, tsrline and mspline.  An unknown plot type is refused in the same words, followed by dash's Supported: list; it said "dash: unrecognised plot type '<word>'". (WP-31, A2)

- mlalign() is declared with twoway's minimum, mlal(): mlal(inside) was named in the note as mlal() and is now named as mlalign() until it is drawn; mla() and ml() stay mlabel(), as twoway binds them (measured: twoway scatter mpg weight, mla(center) says "variable center not found", r(111), as dash does). (WP-31, A4)

- title2() and subtitle2() are refused, "option title2() not allowed" and "option subtitle2() not allowed", r(198), as twoway refuses them, after the comma, inside a plot's parentheses and after a || segment's comma; dash named them as unsupported and drew the graph. (WP-31, D2)

- The axis label forms twoway refuses -- ylabel("a"), ylabel(1 "a" "b"), ylabel(#3 #4) and ylabel(1(1)) -- are refused, r(198), with twoway's "invalid label specifier, : <the part>:"; dash drew them. (WP-31, D6)

<!-- WP-31 C14 -->

<!-- WP-31 D14 -->

<!-- WP-31 D16 -->

<!-- WP-31 E1 -->

<!-- WP-31 E12 -->

<!-- WP-31 E4 -->

<!-- WP-31 E5 -->

<!-- WP-31 G7 -->

<!-- WP-31 H4 -->

- name() is declared with twoway's minimum, the full name: nam(), na() and a bare nam are refused, r(198), "option nam() not allowed", as twoway refuses them; dash took nam() as name(). dash kpi keeps nam(). b(), t(), l() and r() stay the 1 titles, as twoway reads them. (WP-31, A3b)

- aspectratio() is declared with twoway's minimum, aspect: asp(), aspe(), aspec() and a bare asp are refused, r(198), "option asp() not allowed", as twoway refuses them; dash took asp() as aspectratio(). (WP-31, A3c)

- `dash scatter mpg weight, jit(5)` (and j(), ji(), jitt(), jitte()): refused, r(198), "option jit() not allowed", as twoway refuses it; write jitter() in full (was: taken as jitter()) (WP-31, A3d)

<!-- WP-31 D16b -->

### Removed

- `dash_setup` no longer installs or checks scipy or statsmodels. No
  statistical layer uses them. (WP-18)
- The `T()`, `B()`, `L()` and `R()` graph-level title spellings are gone. A
  third `t()`, `b()`, `l()` or `r()` is named as unsupported. (WP-23)
- The `sc`, `li` and `hist` plot-type keys are no longer read from a
  hand-written spec. Stata-side abbreviations are unchanged. (WP-26)

### Requirements

- bokeh >= 3.8, numpy >= 2.3 and pandas >= 2.3, the versions the suites
  run under. Were 3.0, 1.23 and 2.0: every render imports
  `CustomJSTicker`, added in bokeh 3.6, so an installed 3.0-3.5 passed
  `dash_setup` and then failed every command; pandas is declared by dash
  itself because bokeh 3.9 no longer requires it. (WP-25, WP-28)
- scipy and statsmodels are no longer needed (WP-18), and neither is
  jsonio: dash writes its data from Stata's own Python (WP-27).
- The declared minimums are the tested ones -- Python 3.11 (3.13 until WP-30, P1.33), bokeh 3.8,
  numpy 2.3, pandas 2.3 -- everywhere they appear; `dash_setup` refuses
  anything below them, printing the exact `pip install` command for the
  Python Stata is linked to and installing nothing, and the generated
  server app opens with `from __future__ import annotations`. (WP-28, K2)

- `dash_setup` works on externally managed (PEP 668) Pythons -- Homebrew's,
  and the system Python of Debian 12, Ubuntu 23.04, Arch Linux and later. It
  inspects the linked Python first and, where pip installs are refused, runs
  no pip command, says why, and suggests `dash_setup, venv("~/.dash/venv")`.
  It was refused three times and printed pip's advice to pass
  `--break-system-packages`. (WP-29, P0.19)
- New option `dash_setup, venv(path)`. It creates or reuses a virtual
  environment, installs packaging, bokeh, numpy and pandas into it, verifies
  them and dash's schemes inside it, and prints the
  `python set exec "<path>/bin/python", permanently` line to type after
  restarting Stata. (WP-29, P0.19)
- Printed pip commands name `c(python_exec)` and are quoted for the shell,
  `<python> -m pip install 'bokeh>=3.8'` on macOS and Linux and double quotes
  on Windows. The failure line was `python -m pip install bokeh>=3.8`, which
  a shell runs as an unpinned install writing a file named `=3.8`. A Python
  without pip gets the `-m ensurepip --upgrade` line, and a managed Python
  gets no upgrade line pip would refuse. (WP-29, P0.19)
- pip runs with the interpreter Stata is linked to. It ran `sys.executable`,
  Homebrew's base interpreter under a venv-linked Stata. It now runs from a
  private temporary directory with Python's safe-path flag (a `pip/` package
  in Stata's working directory used to run in its place), without an
  inherited `PYTHONPATH`, from wheels only, never prompting, and with PEP
  668's protection forced on. Its output is decoded as UTF-8: a non-ASCII
  byte in pip's message ended `dash_setup` with r(7102). A package that
  `--user` installs is found in the same run. (WP-29, P0.19)
- `dash_setup, garbage(1)` is r(198), was r(101), because the command now
  takes an option. (WP-29, P0.19)

- bokeh has a ceiling: `dash_setup` installs `bokeh>=3.8,<3.10` (it installed `bokeh>=3.8`, which resolved to the unverified 3.10.0), the versions dash was verified on (any patch release of 3.8 or 3.9). A bokeh at or above 3.10 that you already have is left as it is and reported as "outside the verified range", a warning; `dash` then draws and prints one note. A bokeh below 3.8 is refused when `dash` runs (it used to render with no word). Only bokeh has a ceiling. (WP-30, P1.30)
- Python and its packages are checked before a dash command starts. Every command but `dash clear` stops with r(198) and one message naming what is missing, the Python it looked in and `dash_setup` when the linked Python cannot be started, is older than 3.11, or lacks numpy, pandas or bokeh or has one that fails to import; it used to stop with r(7102) and a Python traceback (`ModuleNotFoundError: No module named 'numpy'`) that named no remedy. A registration such as `dash scatter mpg weight, name(g1)` is now refused the same way. numpy or pandas below `dash_setup`'s minimum is named in a note and the command goes on. `dash serve` and a dashboard app run by hand (`python app.py`, `bokeh serve`) stop with the same one line instead of a traceback. `dash_setup` tries a first Python call that fails once more and reports a Python that cannot be started, with its path and, on a Mac, the processor it must be built for, instead of stopping before its summary. `dash clear` prunes dash's temporary files with the packages missing. (WP-30, P1.32)
- Python 3.11 or later (was 3.13). Both test suites, with the pins they run
  under and with a fresh install as `dash_setup` resolves it, pass under
  Python 3.11, the Stata pins under 3.12 too, and a Stata session linked to
  3.11 or 3.12 builds and serves dashboards (measured 07oct2026). numpy 2.3
  needs Python 3.11, so nothing older is supported. `dash_setup` no longer
  refuses 3.11 and 3.12. On a Python below the minimum it says to link a
  newer Python instead of suggesting `dash_setup, venv()`, which refused
  too. A served app's traceback shows the app's source lines on 3.11 and
  3.12, as on 3.13. (WP-30, P1.33)
- Stata 19 or later; tested on StataNow 19.5 (MP), macOS arm64, and measured on MP only. Every dash and dash_setup program declared version 16.0, which implied Stata 16 support that was never tested; all 91 now declare version 19. (WP-30, P1.35)

### Fixed in WP-31

Gaps the drop-in audit of 10oct2026 (GAPS3.md) recorded that WP-31 fixed
without changing a drawn result; the results that changed are the WP-31
group under Results that change, and the newly refused forms sit under
Changed behaviour.

- range(), n(), bwidth() and level() take the values twoway takes: range(. #) and range(# .) on lfit, qfit, lfitci and qfitci, the data's own end for the dot, and range(varname) on kdensity and function, the variable's minimum and maximum over the plot's sample (each refused before, r(198)); n(1) (n() needed 2); kdensity bwidth(0), the default rule; lowess bwidth() outside 0 to 1, drawn at .8 (bwidth(5) was refused); and any level() on lfitci, qfitci and fpfitci (dash refused level(0) and level(100)). A refused range() now gives twoway's return code and words. (WP-31, C10a)

- lpoly and lpolyci accept degree(4) to degree(7) with Stata's rule-of-thumb bandwidth for each (degree above 3 was refused); an mlabel() element may be a varlist pattern such as t* or make-foreign, labelling the following y's (it was r(111)); yaxis(1 2) and xaxis(1 2) draw the layer on both axes, one scale both read, as twoway does (refused before). (WP-31, C10b)

- scatteri, pci and pcarrowi read a coordinate p/q with p equal to q as twoway does, a division drawing 1 (0/0 is missing); dash refused it. (WP-31, C18)

- The lpoly rule-of-thumb constants for degree 4-7 are reachable and tested. (WP-31, F4)

- A weight expression is evaluated as twoway evaluates it: dash lfit mpg weight [aw=price+1] was refused, r(198), "must name one variable; dash cannot evaluate a weight expression", and is now fitted as twoway fits it, in the saved page and the served app, as are [aw=L.price] on tsset data and an expression on qfit, lfitci, qfitci, lpoly, lpolyci, fpfit, fpfitci, kdensity, histogram, mspline and mband; an expression Stata cannot evaluate is refused with Stata's code and words (nosuch not found, r(111)). (WP-31, A5)

- A time-series operator in an option's variable is refused as twoway refuses it, with or without tsset: dash scatter mpg weight, mlabel(L.make) said r(198) "mlabel() must name a variable, not a time-series expression" on tsset data and r(111) "variable L.make not found" otherwise, and now says twoway's "variable L not found", r(111); colorvar(L.mpg) and by(L.foreign) say "factor-variable and time-series operators not allowed", r(101). twoway draws none of them. (WP-31, A6)

- `dash` with no plot draws the empty graph `twoway` draws: `dash`, `dash, title(T)`, `dash if foreign==1` and `dash ||` were refused, r(198), "empty plot specification"; `dash twoway` is refused as `twoway twoway` is, "twoway is not a twoway plot type", r(198), since dash replaces twoway. (WP-31, A1)

- The option-abbreviation truth was an 18 Sep 2026 pre-fix record; it is regenerated live and every option minimum is pinned both ways. (WP-31, A3)

- yaxis(3) to yaxis(9) and xaxis(3) to xaxis(9) are drawn: dash scatter mpg weight, yaxis(3) was refused, r(198), "dash draws two axes", and is now drawn as twoway draws it, in the saved page and the served app -- with three or more y axes all on the left, axis 1 nearest the plot and the others outward in number order, with two the higher-numbered on the right (x axes alike, below and above), a layer naming several axes tying them into one scale; ylabel(), ytitle(), ytick(), yline() and yscale() with axis(3) to axis(9) reach that axis; yaxis(10) is refused with twoway's r(125) "yaxis() invalid -- invalid numlist has elements outside of allowed range". (WP-31, C10c)

- rpcap and rpspike are drawn: dash rpcap lo hi turn weight was refused, r(198), "a twoway plot type dash does not draw", and now draws a spike from y1 to y2 at x, caps as wide as the marker (rpcap) and the marker at y3, in the saved page and the served app, after a filter move too, with the y axis over all three; any other number of variables is refused in twoway's words, "you must specify four variables with twoway rpcap", r(102) or r(103). (WP-31, B1)

- sunflower is refused by name, r(198): "dash: 'sunflower' is a twoway plot type dash does not draw: it bins points into density petals. Use Stata's own sunflower command, which Stata recommends over twoway sunflower, or dash scatter y x with jitter() or colorvar()."; it was answered "sunflower is not a twoway plot type", although twoway draws it. (WP-31, B2)

- matamatrix() is refused by name, r(198), with advice to getmata the columns into variables: dash scatter matamatrix(M) was read as a variable list and refused, r(111), although twoway plots the matrix. (WP-31, B3)

- The contour surface twoway computes (the thin-plate spline with kernel r^2 log r and a linear trend, Shepard's 1/d^2 mean, the unique(x) x unique(y) grid, smallest-z duplicates, interp() read as twoway reads it) is available to the renderers, exact up to 1,000 distinct points and on a flagged 100x100 grid above; no plot type uses it until B4b. (WP-31, B4a)

- contour and contourline are drawn in both modes with twoway's surface, cuts, colours and key; dash refused both by name, r(198). ccuts() with levels(), a second contour, a weight and contour options on other types are refused in twoway's words, r(198) or r(101); above 1,000 distinct points a 100 x 100 grid is drawn and noted. (WP-31, B4b)

- A saved page recomputes contour and contourline after a filter move, as the served app does, up to 1,000 distinct points; above that the layer is marked (grid unfiltered). It kept them as built and marked them after every move. (WP-31, B4c)

<!-- WP-31 D14 -->

<!-- WP-31 D16 -->

<!-- WP-31 E13 -->

<!-- WP-31 G3 -->

<!-- WP-31 G4 -->

<!-- WP-31 G5 -->

<!-- WP-31 C16 -->

<!-- WP-31 F5 -->

<!-- WP-31 F3 -->

<!-- WP-31 H2t -->

<!-- WP-31 H2f -->

<!-- WP-31 H2k -->

<!-- WP-31 H2l -->

<!-- WP-31 H1 -->

<!-- WP-31 H2x -->

<!-- WP-31 K6 -->

<!-- WP-31 H3 -->

<!-- WP-31 H7 -->

<!-- WP-31 J1 -->

<!-- WP-31 J2 -->

<!-- WP-31 J3 -->

<!-- WP-31 J4 -->

<!-- WP-31 J5 -->

<!-- WP-31 J6 -->

<!-- WP-31 I2 -->

<!-- WP-31 I3 -->

<!-- WP-31 I4 -->

<!-- WP-31 I5 -->

<!-- WP-31 I7 -->

<!-- WP-31 K2 -->

<!-- WP-31 K3 -->

<!-- WP-31 K4 -->

<!-- WP-31 H6 -->

<!-- WP-31 I6 -->

<!-- WP-31 C18b -->

### Fixed in WP-30

Failures the drop-in re-audit of 30sep2026 ranked P1 that WP-30 fixed
without changing a drawn result; the results that changed are the WP-30
group under Results that change, and the security, behaviour, new and
requirement changes sit in their own lists.

- `mlabel()`, `jitter()`, `base()` and `barwidth()` take a list, one element per y of an expanded varlist, as in twoway. `dash scatter mpg turn weight, mlabel(make rep78)` labels mpg's markers with make and turn's with rep78, and `dash bar mpg turn weight, base(10 20) barwidth(1 2)` draws each series from its own base at its own width; each was refused r(198). `.`, `=`, `..` and `...` resolve as in twoway, so `jitter(2 ..)` and `base(10 =)` draw. A single-y plot takes the first element: `dash scatter mpg weight, mlabel(make foreign)` labels with make, where it was refused. `jitter(.)` and `barwidth(.)` now mean the default; they were refused. Elements past the last y are not checked: `dash scatter mpg weight, jitter(2 200)` draws. (WP-30, P1.1b)
- A layer drawn with `horizontal` keeps its tooltips right in both modes, before and after filter moves: `dash histogram mpg, horizontal` answered along x (`vline`) across bins stacked along y, and now answers along y (`hline`); a turned kdensity, function, area or pci named its tooltip rows in the other axis's roles (`dash kdensity mpg, horizontal` showed the density as mpg and mpg as the density; a turned area band had none), and now names them as the upright layer does. Turned layers, by() panels, `yaxis(2)` and a mixed-orientation date axis stay as drawn after any move. (WP-30, P1.9b)
- `twoway`'s sub-option abbreviations are read, in both modes and after any filter move: in `legend()` `c()`, `r()`, `lab()`, `posi()`, `s()`, `lastlab()`; in the axis labels and ticks `labs()`, `ang()`, `for()`, `g`, `nog`, `val`, `valuelabels`; in `xline()`/`yline()` `lc()`, `lp()`, `lw()`; in the textboxes `s()` is `size()`. Repeated copies merge by full name, the last winning, so `legend(lab(1 "A")) legend(lab(2 "B"))` keeps both. `rows()` beats `cols()`. In one copy `on` beats `off` and `grid` beats `nogrid`. Quoted label text is never read as a sub-option (`ylabel(10 "labsize(large)" 20)`). `legend(position(13))`, a non-numeric `ring()` and a non-integer `order()` word draw the default with `twoway`'s note. (WP-30, P1.19)
- A `function` layer drawn without Stata's points -- from a dashboard spec written by hand, or a graph whose stored points were removed, cannot be read or are not dash's -- that uses a function or name dash does not evaluate itself (`normalden(x)`, `c(pi)*x`, `cond()`, `min()`, `round()`, `scalar()`, `_b[]`, `pi`) still draws nothing, but now says why, saved and served, and in the log of `dash build, server`: `(note:  dash: graph 'g' plot 1 (function) drew nothing: it needs the points Stata computes for it when dash registers the graph, and this spec carries none; without them dash evaluates only x, _pi, numbers, + - * / ^ and sin(), cos(), tan(), exp(), log(), log10(), sqrt(), abs(), floor() and ceil(), and normalden() is not one of them.)`, where it printed only `(note:  dash: graph 'fn02' plot 1 (function) drew nothing.)`; and the note for stored points that are not dash's no longer says the layer "is drawn from its expression". Every function layer of a graph registered in Stata is drawn from twoway's own points, as since WP-29. (WP-30, P1.22)
- `mlabvposition(varname)` and `mlabtextstyle()` are drawn, in both modes and after filter moves: `dash scatter y x, mlabel(lab) mlabvposition(pos)` drew every label at 3 o'clock and named the option in the note, and now draws each row at the clock its value gives (a whole number 0-12; missing values and string variables at `mlabposition()`, else 3; any other number at 12 with a note), with `mlabgap()` along each row's direction; `mlabtextstyle(heading)` was named in the note and drawn in the marker-label default, and now draws the scheme's heading (under stcolor 1.75 times the default label size, black where the default is p1's blue), any of Stata's 37 text box styles, one per y as a style list. (WP-30, P1.24)
- A Python warnings filter set in the session no longer hides or escalates dash's notes. After python: warnings.filterwarnings("ignore") the note still prints. After python: warnings.simplefilter("error"), or with PYTHONWARNINGS=error, the dashboard is drawn (rc 0), where it failed with r(7102) and a 60-line traceback. Other packages' warnings still follow the session's filters, and a note raised twice in one command prints once. (WP-30, P1.26a)
- dash build, server prints the notes dash build prints for the same graphs (an option drawn differently, a fit twoway could not fit, a by() sub-option), from one drawing of the app it wrote; it printed none. dash serve relays the served app's notes, error lines and tracebacks to Stata while it serves, each note once and none its build already printed, with the key and query strings removed; before, the app's output reached Stata only when the launch failed. A served session no longer fails when PYTHONWARNINGS=error turns a dash note into an exception. (WP-30, P1.26b)
- A twoway command word in front of the plots is refused in twoway's own words, "<word> is not a twoway plot type", r(198), not "unrecognised plot type 'twoway'"; WP-30 had read twoway, tw, two and graph twoway off as a prefix, which was withdrawn on 14oct2026 because dash replaces twoway. (WP-30, P1.27)
- One saving() grammar serves the one-line form and `dash build` (HTML and server): `saving(f, asis)` wrote a file named "f, asis.html", `saving("n, replace")` wrote n.html with replace applied, and `dash build, saving(f, replace)` and `dash build, saving(f)` were refused, r(198). Now replace and asis are read as twoway reads them, a comma inside quotes stays in the name, `saving(, replace)` writes Graph.html, and `dash build` appends .html (.py with server) and replaces .gph as the one-line form does. (WP-30, P1.27)
- saving() accepts a `..` segment and ; & | < > in a path, as twoway does (`saving("../out/d.html")` and `saving("R&D.html")` were refused, r(198)); a double quote, backquote, $, any control character and a leading - are still refused, and dash serve's private app path still refuses `..`. The "To launch:" line of `dash build, server` puts the path in single quotes on a Mac and Unix, so a pasted line runs the file it names. (WP-30, P1.27)
- A filter move in a served dashboard no longer freezes the server for everyone: a lowess move at 100,000 observations held `/health`, every other session's moves, brushes and downloads, and new sessions for 8.1 s; recomputations now run on one worker thread per server process, one at a time in the order sessions asked, while the page shows "Updating..." and keeps its drawing, and `/health` answered within 0.015 s. A session's newer move replaces its waiting one; the longest wait is about the session limit times one recomputation (about 3 minutes with 20 sessions for lowess at 100,000 observations). (WP-30, P1.31b)
- The certification, release and test runners no longer hard-code the maintainer's checkout or arch -arm64. make cert tests the tree it is run in (DASH_REPO, else the current directory when it is a dash tree, else r(601)): it tested the main checkout, so a broken worktree or copy could pass. Stata is started by scripts/stata_batch.sh, which takes the binary from STATA_BIN (the Make variable STATA is now STATA_BIN) and chooses the arm64 slice from the machine and the binary. scripts/regen_option_surface.py and scripts/wire_option_reporting.py are retired and refuse to run. (WP-30, P1.34)

### Fixed in WP-29

Failures the drop-in re-audit of 30sep2026 ranked P0 that WP-29 fixed
without changing a drawn result; the results that changed are the WP-29
group under Results that change, and the security, behaviour and
requirement changes sit in their own lists.

- `dash scatter mpg weight, hover(rep78)` now shows rep78, by its value label, in the tooltip of the saved page and the served app, on the one-line route and through dash build and dash serve, before and after a filter move; a variable named only in hover() was never exported, and the tooltip left it out with rc 0 and no note (WP-29, P0.10)
- hover()'s variables now count toward the data limits: on the saved page when a layer of the graph can show them (or csv is given), in a served app always. `dash scatter mpg weight, hover(rep78 headroom trunk)` at `dash_max_cells 200` counted 148 values and built; it is now refused with 370 values (74 observations x 5 variables), r(134). `dash build` and `dash serve` refuse a hover() variable dropped after name() with r(111) where they left it out with rc 0. The CSV download carries the hover() columns (WP-29, P0.10)
- Break stops `dash serve` in every front end: the launcher polls Stata's
  interface while it waits, stops the server and ends the command with r(1),
  as any command interrupted by Break does; Ctrl+C in console Stata used to
  return 0, and GUI Stata's Break was never seen. Messages and the help name
  Break. (WP-29, P0.13)
- A saved page now marks a fitted or smoothed line, a histogram's bins and a density's grid that a filter move left computed from observations the filter removed: the layer is dimmed, its legend key gains (unfiltered), (bins unfiltered) or (grid unfiltered), the graph shows a caption and the filter area a status line. Before, dash (scatter mpg weight) (lfit mpg weight) with filter(foreign) kept the all-rows line (29.105 at weight 1800, where the Foreign cars' fit is 29.917) under the filtered points with no sign that it ignored the filter. The served app refits as before (WP-29, P0.17)

### Fixed in WP-28

Failures the GAPS2 audit of 25sep2026 found that WP-28 fixed without
changing a drawn result; the results that changed are the WP-28 group
under Results that change, the behaviour changes and the floor sit in
their own lists.

- The served app declares the saved page's viewport meta, dims unselected
  linked points to 15% (was Bokeh's 10%), shows a selection on rspike and
  rconnected's markers, and takes the saved `layout(bs)` half rows and KPI
  cell heights between 768 and 991 px; `filterposition(left)` under
  `layout(bs)` still places the title differently, recorded in the help.
  (WP-28, E14)
- `dash serve` returns r(198) and says why when no server started -- the
  port is in use, or the app stopped before it answered `/health` -- where
  it returned 0 after the app had died on process stderr; the server's
  address is printed once `/health` answers and the app's own output
  reaches the Results window, bounded; `--port` outside 1024-65535 is
  refused by `dash_render.py`, `main()`, a `build_options` port and the
  generated app instead of being moved (80 served on 1024). (WP-28, F1)
- The saved page's `$dash_max_cells` limit counts what the page will
  actually embed, not every exported variable times every observation: a
  graph made only of computed layers (`histogram`, `kdensity`, a fit or a
  smoother) that no `filter()`, `link()`, `csv` or `hover()` reaches draws
  its own bounded output, so `dash histogram x` now builds a saved page on
  more than 5,000,000 observations (measured: `set obs 6000000; dash
  histogram x, bin(50)` built a 1,441,675-byte page with rc 0) where
  `dash scatter y x` on the same 6,000,000 observations is still refused
  ("this dashboard would embed 6,000,000 values (6,000,000 observations x
  1 variable), more than the 5,000,000 dash embeds"). The size note
  reports embedded bytes the same way. The served app's count is
  unchanged, and its refusal now says a served app embeds every
  observation of every variable it uses. (WP-28, G3)
- A Unicode variable name (`größe`) now works in `filter()`, `dash kpi`,
  `by()`, `hover()` and `colorvar()`, in both the saved page and the
  served app: `filter()` and `dash kpi` used to refuse it with r(198),
  and the renderers drew no panels, tooltip field, widget or colours for
  it, in silence. (WP-28, G5)
- One Stata display-format writer, shared by the saved page and the served
  app (Python, with a JavaScript twin): `%w.df`, `%w.dg`, `%w.de` with `c`,
  the `0`/`-` flags and the comma decimal, and every `%t` picture, pinned
  row for row to `test/fixtures/format_truth.json`; the data export now
  carries each variable's storage type. (WP-28 S04)
- `dash kpi ..., fmt(%21x)`, `fmt(%16H)` and `fmt(%16L)` are refused with
  r(198) naming the format; a variable whose own display format is one of
  these is drawn in `%9.0g` with one note. (WP-28 S04)
- Marker labels of a variable with a `%g` or `%e` display format read as
  Stata writes them, and `mlabformat(%9.3e)` of 1234.5678 reads `1.23e+03`,
  not `1.235e+03`. (WP-28 S04)

### Fixed after WP-27 (the S3 batch, 24sep2026)

Every entry BUGS.md graded S3 at release was taken up; the work found and
fixed more, several of them S1 or S2. Results that change:

- A repeated option is read as twoway reads it: the last copy wins for most
  options, the copies merge for titles, axis labels, `legend()`, `xline()`
  and the like, and a unique option (`name()`, `saving()`, `scheme()`,
  `kernel()`, ...) refuses its second copy, r(198). Before, dash kept the
  first copy, sent a second `title()` or `xlabel()` to the second axis's
  option, and dropped one plot group's `legend(label())` beside another's.
- Under `by()`, a qualifier holding `_n`, a subscript or `in` selects the rows
  twoway selects, after a stable sort on the `by()` variables; the Total
  panel reads the data's own order.
- `log` is twoway's graph option `logging`; only `lo`, `logi` and `logit`
  turn on lowess's logit, which `log` used to.
- `ylabel(#N)` and `xlabel(#N)` ticks follow twoway's rule, measured against
  264 axes; `by()` panels share one scale; log and `%tc` axes follow it too.
  (`%td` to `%th` axes follow a fitted model of twoway's compiled routine,
  about 60% exact; an open entry.)
- A graph whose every layer is on `yaxis(2)` draws one axis, on the left.
- The next layer after a ci plot takes the colour twoway gives it, a ci band
  counting as a plot; a ci band is drawn in the scheme's ci style (grey
  under s2color) with its outline, and takes `acolor()`, `alcolor()`,
  `alwidth()`, `alpattern()` and `pstyle()` as twoway does.
- qfit, lfitci and qfitci on two observations draw twoway's fit; lowess,
  mspline and mband on one draw what twoway draws, silently; a kernel flag
  (`gaussian`, `bi`, ...) on lpoly, lpolyci and kdensity draws that kernel.
- Reference lines, the plot region's border and `note()`'s box follow the
  scheme; markers, bars and areas get the scheme's outline widths; a
  custom scheme's `linewidth p#`, `symbol p`, `symbolsize p#`, `color p#`
  and `linepattern p#` reach the plots Stata's chain reaches, and an
  `#include` is read where it stands, with Stata's note when it resolves
  nowhere.

Refused as twoway refuses them: a function name Stata does not have, or one
written with a blank before its parenthesis; an option value `-syntax-`
cannot bind; a range or paired-coordinate type given the wrong number of
variables (it ended in a Python traceback) and a fit given more than two;
empty samples where twoway refuses them; a plot option after a plot group's
comma; an option written in upper case; two kernel flags. A bare `sort` on
the connected types is no longer named as unsupported; `lwidth(vvvthick)` is
known; lowess and fpfit are faster on large data; a dataset with no
observations and a data file holding an out-of-range number load.

### Fixed in WP-27

Results that change:

- A qualifier is now evaluated by Stata itself, once, at build: the rows a
  layer, a graph or a KPI draws are the rows Stata's `if`/`in` selects, in
  saved and served dashboards alike. Before, the renderer translated the
  qualifier and disagreed with Stata on missing values (`rep78 > 3` drew 29
  rows where Stata selects 34), subscripts and functions (`mpg > mpg[_n-1]`,
  `strpos()`: every row drawn), `if 1`, a unary plus, deep nesting and a
  date compared with a number of 9999 or less. (WP-27)
- On a saved page, a filter now redraws line, tsline, area, bar, spike,
  dropline, range and paired-coordinate layers, a scatter with a missing
  value, and pcarrow/pcbarrow arrowheads; a date dropdown keeps its rows (it
  kept none). A line, tsline, connected or rconnected layer with its own
  `if`/`in` draws its own observations, and a labelled scatter labels only
  its own rows. A linked `by()` panel's line holds only its panel's rows.
  (WP-27)
- `lfit`, `qfit`, `lfitci` and `qfitci` of an x with no spread draw
  twoway's flat line at the mean, with the mean's interval as the band; they
  drew a sloped segment, or nothing. (WP-27)
- The served app draws dates as the saved page does -- date axes, tooltips,
  KPI cards and filters -- and a number given for a date axis (`xline()`,
  `xscale(range())`, `xlabel()`, `xtick()`) is read as a Stata date in the
  variable's unit, in both modes. (WP-27)
- Each layer's tooltip names its own variables, and `hover()` reaches the 23
  plot types whose marks are observations; the 17 computed and immediate
  types say so in a note. (WP-27)
- A served filter move keeps a jittered scatter's points where they were
  drawn, and a jittered scatter under `link()` takes part in linked
  selection. (WP-27)

Fixed and changed:

- The one-line form refuses an existing file named by `saving()` unless
  `replace` is given (after the comma, or as `saving(f, replace)`); it
  overwrote the file. A directory named by `saving()` is refused in both
  the one-line form and `dash build`. (WP-27)
- `by()` titles may hold `$`, a backtick, a backslash or a compound quote;
  a legend `label()` in compound quotes is drawn; a compound quote nested in
  another is read as twoway reads it. (WP-27)
- `kernel()` takes every abbreviation twoway takes; a weight's values are
  checked over the rows the graph's qualifier selects, so
  `(lfit mpg weight [fw=w]) if foreign==1` is accepted as in twoway; the
  one-line form honours `by(, cols())`. (WP-27)
- No saved or served dashboard scrolls sideways at 375, 768 or 1440 px: a
  grid or a `by()` panel grid too narrow for its columns stacks them into
  one, the filter bar wraps, and KPI cards narrow. (WP-27)
- Any string value Stata holds now reaches the page as typed. A value
  holding an unclosed compound quote, a lone backtick or apostrophe, or the
  closing pair stopped every build inside jsonio (r(132) or r(109)), and a
  strL arrived empty. dash now writes its data from Stata's own Python and
  no longer uses jsonio. (WP-27)
- `$dash_max_bytes` (default 50,000,000) limits the bytes of text a
  dashboard embeds, strL values included, with r(134) past it, as
  `$dash_max_cells` limits the values. (WP-27)
- A variable whose name begins `__dashq` is refused, r(110): dash reserves
  the prefix for the qualifier columns it exports and never shows. (WP-27)
- `make gate` net installs dash into a scratch PLUS and builds every example
  and one page per shipped scheme from the installed copy; `make release`
  runs `make check` and then the gate. (WP-27)
