# Changelog

## 2.0, 24sep2026 (release candidate)

Changes since the 2.0 of 27mar2026 (the version number is unchanged; `adoupdate` compares the Distribution-Date, now 20260924). Items marked with a work package number
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

<!-- WP-28 B1 -->
<!-- WP-28 B2 -->
<!-- WP-28 B3 -->
<!-- WP-28 B5 -->
<!-- WP-28 B6 -->
<!-- WP-28 B7 -->
<!-- WP-28 C2 -->
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
<!-- WP-28 E1 -->
<!-- WP-28 E2 -->
<!-- WP-28 E3 -->
<!-- WP-28 E14 -->
<!-- WP-28 G6 -->
<!-- WP-28 G16 -->
<!-- WP-28 X1 -->
<!-- WP-28 X2 -->

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

### New

- Six more schemes, twenty in all: s1manual, s2manual, s2gmanual, s2color8,
  sttrans (with its 20% colour opacity) and stgcolor_alt. (WP-17)
- `scheme(mytheme)` finds `mytheme.scheme` in the working directory on
  `dash scatter`, `dash build` and a graph's own `scheme()` (WP-17).
  `c(scheme)` is the default scheme, and `dash build` accepts `scheme()`
  (S11).
- New plot types `pcarrowi` and `pccapsym`. `contour`, `contourline`,
  `heatmap`, `rpcap` and `rpspike` are refused by name, with what to use
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

- `scheme(nosuchthing)` and an unknown `theme()` are now r(198) on every
  entry point, not a warning. An unknown session `c(scheme)` still warns and
  uses s2color. (WP-17)
- Option values are validated as twoway validates them. A bad value such as
  `msize(abc)` or `yaxis(3)` is r(198) or r(111), naming the option. A style
  name dash cannot draw is noted and the default is used (WP-15).
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
<!-- WP-28 G2 -->

### Removed

- `dash_setup` no longer installs or checks scipy or statsmodels. No
  statistical layer uses them. (WP-18)
- The `T()`, `B()`, `L()` and `R()` graph-level title spellings are gone. A
  third `t()`, `b()`, `l()` or `r()` is named as unsupported. (WP-23)
- The `sc`, `li` and `hist` plot-type keys are no longer read from a
  hand-written spec. Stata-side abbreviations are unchanged. (WP-26)

### Requirements

- Python 3.8 or later, linked to Stata (`dash_setup` checks this). (WP-06)
- bokeh >= 3.0, numpy >= 1.23 and pandas >= 2.0. pandas was >= 1.5; 1.x
  cannot store dash's date columns. (WP-25)
- scipy and statsmodels are no longer needed (WP-18), and neither is
  jsonio: dash writes its data from Stata's own Python (WP-27).
<!-- WP-28 K2 -->

### Fixed in WP-28

Failures the GAPS2 audit of 25sep2026 found that WP-28 fixed without
changing a drawn result; the results that changed are the WP-28 group
under Results that change, the behaviour changes and the floor sit in
their own lists.

<!-- WP-28 E14 served -->
<!-- WP-28 F1 -->
<!-- WP-28 G3 -->
<!-- WP-28 G5 -->

### Fixed in WP-28

- A Unicode variable name (`größe`) now works in `filter()`, `dash kpi`,
  `by()`, `hover()` and `colorvar()`, in both the saved page and the
  served app: `filter()` and `dash kpi` used to refuse it with r(198),
  and the renderers drew no panels, tooltip field, widget or colours for
  it, in silence. (WP-28, G5)

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
