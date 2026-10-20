# Stata ground truth for WP-33..WP-49 (research phase)

> Measured 20oct2026 on this machine: StataNow 19.5, console batch
> (`scripts/stata_slot.sh`, which runs `arch -arm64 /usr/local/bin/stata-mp -b do`),
> repo at s3-bugs `090d928`. Default scheme `stcolor` (no scheme set in the
> profile). Every do-file ran in its own folder under the session scratchpad
> `.../scratchpad/r2/<run>/`; logs, SVGs, pages and the parsed JSON (`res.json`,
> `svgsum.json`) stay there. No repository file other than this report was
> written. No persistent preference was changed.

Shared probe harness (all runs). `P id cmd` prints `##BEGIN id`, runs
`capture noisily <cmd>`, prints `##RC id <rc>`, and (twoway runs) exports
`svg/<id>.svg` when rc is 0. `parse_probe.py` collects each probe's rc and the
lines printed between the markers ("first line" below = the first of them).
dash runs have `global dash_nobrowser 1` and
`adopath ++ "/Users/billy/Desktop/Programs/StataPrograms/d/dash"`.

---

## 1. Corpus inventory (twoway vs dash gallery)

### 1a. Help files

Extraction (`corpus/extract_help.py`, `classify.py`, `final_help.py`):
runnable examples are the `{stata "gr_example <ds>: <cmd>":...}` and
`{stata "gr_example2 <name>":...}` links (also `{stata `"gr_example ..."'...}`
with compound quotes, e.g. twoway_contour.sthlp:259). The `{cmd:. ...}` lines
are display text: many are schematic (`{it:yvar}`), and the linked command
can differ from the display (scatter.sthlp:502 shows `connect(l)`, the link
runs `c(l)`). Use the link text, not the `{cmd:}` line.

- `gr_example <ds>: <cmd>` (g/gr_example.ado): `preserve`, `sysuse <ds>,
  clear`, run `<cmd>`, `restore`. Always sysuse, one line.
- `gr_example2 <name>` (g/gr_example2.ado, 88 programs): each program sets up
  its own data (`sysuse`, `webuse lifeexp2` once, or `input`/generated data),
  may run `gen`/`replace` first, and writes the graph command under
  `#delimit ;` across several lines. The command must be taken from the
  program body (between `Xeq` and `;`), not the help file.
- `tsline_ex <name>` (t/tsline_ex.ado, 5 programs: arma, calories,
  calories2, calories3, rcalories): `sysuse tsline1`/`tsline2`, then tsline.
- `gr_example3` exists (version 18 programs for graph bar etc.), no twoway use.
- Dangling: addplot_option.sthlp links `gr_example2 plotop1..3`, which no ado
  defines in this release.

Counts (heatmap and sunflower help files excluded; non-twoway graphs —
graph bar/hbar/box/hbox/pie/matrix/combine/dot, qnorm, graph editor — dropped):

| Source | Links kept | Notes |
|---|---|---|
| twoway-family help (t/twoway_*.sthlp minus `__gen`, s/scatter, l/line, t/tsline, g/graph_twoway) | 122 | 95 `gr_example`, 22 `gr_example2`, 5 `tsline_ex` |
| [G-3]/intro help reached from them (added_text_options, axis_label_options, axis_scale_options, by_option, clegend_option, legend_options, marker_label_options, region_options, scale_option, title_options, symbolstyle, graph_text, graph_intro, graph_display, gph_files, graph_editor, whatsnew7to8) | 98 | 82 `gr_example`, 16 `gr_example2` |
| Total | 220 | 198 distinct (same named example linked from several files) |
| Dropped as non-twoway | 41 | |

Datasets (help corpus): all `sysuse` (shipped in ado/base) except one:
auto (93 uses), lifeexp (24), sp500 (26), sandstone (20; shipped as
s/sandstone.dta, so `gr_example sandstone:` works), uslifeexp (18),
uslifeexp2 (9), tsline2 (4), gnp96 (3), nlswide1 (3), pop2000 (3), surface (3),
autornd (2), network1 (2), network1a, nlsw88, tsline1; **webuse: lifeexp2**
(gr_example2 grintro6).

### 1b. g.pdf ([G-2] graph twoway entries and [G-3] option entries)

Extraction (`corpus/gpdf.py`): `pdftotext -layout g.pdf` (2.8 s, 35,215
lines). Pages split on form feed; each page's first line is the running
header `<entry> — <title> <page>`, which assigns pages to entries; the
Contents pages give each entry's section ([G-2]/[G-3]). Commands are lines
`^\s*\. <cmd>`; a command continues on following lines indented 4+ columns
deeper than its prompt, up to a blank line, a new prompt or an output line
starting `(`. Whitespace is collapsed (layout mode pushes trailing words
far right, e.g. `saving(yx)` at g.txt:888).

Artifacts the harness must handle: g.pdf never uses `///` or `#delimit` in
prompted examples (the 21 `///` hits are unprompted schematic syntax);
quotes come out curly — `”` for both open and close double quotes (97
graph commands contain one), `’`/`‘` for single quotes — map them back to
`"`, `'` and `` ` ``; data is loaded as
`use https://www.stata-press.com/data/r19/<name>` even for shipped datasets
(map to `sysuse` when the .dta is in ado/base).

| | Count |
|---|---|
| Entries scanned | 91 (43 [G-2] graph twoway*, 48 [G-3]); heatmap/sunflower excluded; [G-2] graph twoway tsline has 0 prompts (tsline lives in [TS]) |
| Prompted commands in them | 805 |
| Graph commands (first word twoway/tw/scatter/line/graph twoway/plot type) | 480 |
| ... of which schematic (yvar, xvar, `...`, placeholders) | 135 |
| ... runnable | 345 (305 distinct) |
| ... spanning more than one line | 84 |
| first words of runnable | twoway 164, scatter 155, line 20, graph 5, histogram 1 |

Largest entries: graph twoway scatter 63 graph commands, graph twoway 35,
by option 29, axis choice 28, legend 23, axis label 18, axis scale 17,
colorvar 14, graph twoway line 12, clegend 10, region 10, marker label 10.

Datasets (g.pdf): auto 35, sp500 17, lifeexp 11, uslifeexp 5, gnp96 3,
pop2000 3, sandstone 3, uslifeexp2 3, nlsw88 2, nlswide1 2, network1 2,
autornd, cancer, census, network1a, surface (all shipped, sysuse);
**webuse: lbw** (colorvar options, g.txt:25061) **and nhanes2l** (colorvar
options, g.txt:24865).

### 1c. Repository `examples/`

14 do-files (basic_scatter, bootstrap_equal_cols, bootstrap_kpi_hero,
bootstrap_responsive, bootstrap_stacked, comprehensive_demo, feature_tour,
full_dashboard, geometry_responsive, kelly22ex_categorical,
multi_graph_dashboard, plot_types_tour, serve_dashboard, sp500_dates).
They hold 195 `dash` lines: 120 graph commands (every plot type dash draws
appears; plot_types_tour has one per type), 45 `dash kpi`, 14 `dash clear`,
14 `dash build`; 13 files use `name()`, i.e. they are dashboards, and many
graph lines carry dash-only options, so their twoway twin needs the dash
words stripped. Data: sysuse auto, sysuse sp500 only.

### 1d. Totals and webuse

Help 198 distinct + g.pdf 305 distinct runnable + examples 120 graph lines
(+ the audit's probe commands) ≈ 620 before cross-source de-duplication.
Distinct datasets: 18 shipped (sysuse) + 3 webuse (lifeexp2, lbw, nhanes2l).

webuse from console batch works here: `webuse query` → prefix
`https://www.stata-press.com/data/r19`; `webuse lifeexp2` rc 0,
`webuse sandstone` rc 0. Stata keeps no cache: webuse is a `use <URL>` each
time (nothing left in STATATMP, no .dta under ~/Library); the planned
git-ignored cache has to be written by the harness (`webuse x` + `save`).

---

## 2. twoway SVG export in console batch (`svg1/svg1.do`, `det/det.do`)

```
sysuse auto, clear
twoway (scatter mpg weight if foreign==0) (scatter mpg weight if foreign==1) (lfit mpg weight), title("T") ytitle("Y") xtitle("X")
graph export "sc_legend_a.svg", replace      // and again as _b; _c in a second session
scatter mpg weight, by(foreign)
graph export "by_foreign.svg", replace
```

- `graph export x.svg` works in batch, rc 0, message `file x.svg saved as SVG format`.
- **Default size is 7.5 x 4.5 in, not 5.5 x 4** (scheme stcolor; `graph describe`
  prints `size: 4.5 x 7.5`): `<svg width="7.500in" height="4.500in"
  viewBox="0 0 5400 3240">`. Units: 720 viewBox units per inch (10 per
  point). `xsize(8) ysize(4)` → `8.000in x 4.000in`, viewBox 5760 x 2880;
  `width(1000)` → `width="1000px" height="600px"`, same viewBox. Q57's
  "5.5 x 4" is s2color's size; the stcolor default here is 7.5 x 4.5.
- **Deterministic**: the same command exported twice in one session and again
  in a second session is byte-identical (cmp), scatter and by() alike. No
  path, user or time in the file; `<desc>Stata Graph - <name></desc>` carries
  the graph name.
- Structure: flat list in paint order, no `<g>`, no clipPath, no
  dasharray. Elements: `<rect>` (background, graph region, plot region —
  each as a fill rect then a stroke rect inset by half the stroke; legend box;
  by() panel rects and the shaded strip `#F0F0F0` behind panel titles),
  `<line>` (axis lines, ticks, and grid lines — stcolor grid lines are written
  as many short dash segments, e.g. 64.8 units on, 32.4 off, at
  `stroke:#F0F0F0;stroke-width:9.72`; 252 of the 263 lines in the scatter are
  grid segments, so the comparator must merge collinear segments), `<circle>`
  (each marker is two circles: a fill disc `r=21.74 fill:#1A85FF` and a ring
  `r=16.88 fill:none;stroke:#1A85FF;stroke-width:9.72`), `<path d=" M.. L..">`
  for connected lines (the lfit), `<text>` for every label.
- Text: axis tick labels, titles, legend keys and by() panel titles are all
  `<text x y style="font-family:'Helvetica';font-size:112.56px;fill:#000000"
  text-anchor="middle|end">label</text>`; y title has
  `transform="rotate(-90 x,y)"`; title 157.44px. Tick labels sit next to
  their tick `<line>` (same x for x ticks, y + 39.43 for y ticks), so ticks
  and labels pair by coordinate. Numeric labels keep their display format
  (`2,000`).
- Colours are hex in `style` (`fill:` / `stroke:`); stroke widths scale with
  graph size (6.48 at 7.5x4.5, 5.76 at 8x4, 7.20 at 5x5 for the axis line).
- Scatter sample: 152 circles (74 markers x 2 + 2 legend keys x 2), 1 path
  (lfit), 263 lines, 7 rects, 14 texts (4 y labels, 4 x labels, 2 axis
  titles, 3 legend texts, title). The legend's line key is a `<line>`.
- by() sample: 148 circles, 399 lines, 9 rects (2 panel plot regions,
  2 panel-title strips), 17 texts (y labels once, x labels per panel,
  `Domestic`, `Foreign`, axis titles once, `Graphs by Car origin`).
- Samples kept: `scratchpad/r2/svg1/sc_legend_a.svg`, `by_foreign.svg`
  (and `by_foreign.png`).

---

## 3. Zero observations (`zero_tw/zero_tw.do`, `zero_dash/zero_dash.do`, generated by `gen_zero.py`)

Data: `sysuse auto`, `gen t=_n`, `tsset t`, `gen ymiss=.`, `gen ydom = mpg if !foreign`.
Per type T with variables V (xy types `mpg weight`; range `mpg turn weight`;
rpcap/rpspike `mpg turn trunk weight`; pc types `mpg weight turn length`;
tsline `mpg`; tsrline `mpg turn`; kdensity/histogram `mpg`; contour(line)
`mpg weight length`; `_h` = `, horizontal`), each run as `twoway ...` and
`dash ...` (400 probes each):

- a `T V if 0`
- b1 `(T V if 0) (scatter mpg weight)`; b2 `(scatter mpg weight) (T V if 0)`
- c `T V || scatter mpg weight || if 0` (graph-wide if)
- d `T V in 1 if foreign` (in selects row 1, the if excludes it)
- f `T` with every y missing (`ymiss`)
- e1 `T` on `ydom`, `by(foreign)` (Foreign panel has no plottable row)
- e2 `T V if 0, by(foreign)` (every panel empty)

### twoway's answers

| Types | a, b1, b2, c, d | f (all y missing) | e1 (one panel empty) | e2 (all empty, by) |
|---|---|---|---|---|
| scatter line connected area bar spike dropline dot lowess rarea rbar rspike rcap rcapsym rscatter rline rconnected rpcap rpspike pcspike pccapsym pcarrow pcbarrow pcscatter tsline tsrline kdensity histogram contour contourline; bar/area/spike/dropline/rbar/rarea/rcap/histogram horizontal | rc 0, draws | rc 0, draws | rc 0, both panels drawn | r(198) `nothing to graph` |
| lfit qfit lfitci qfitci | rc 0, draws, after `(note:  regress could not fit model)` | same | same, 2 panels | r(198) `nothing to graph` |
| fpfit fpfitci | r(198): `(note:  fracpoly could not fit model)` then `observation numbers out of range` | rc 0, draws, with the note | rc 0, 2 panels, note | r(198) `nothing to graph` |
| lpoly lpolyci | r(2000) `no observations` | r(2000) `no observations` | rc 0, **1 panel** (the empty group's panel is dropped) | r(198) `nothing to graph` |
| mband mspline | r(198) `bands must be between 1 and 200` | rc 0, draws | rc 0, 2 panels | r(198) `nothing to graph` |
| function scatteri pci pcarrowi | `if 0` is ignored: a and b1 draw the function/points (scatteri 4 circles; function 1 path); c draws the function/points and an empty scatter | n/a | n/a | r(198) `nothing to graph` |

What "draws" means (from the SVGs, `zero_tw/svgsum.json`):
- a/c/d of scatter-like types: plot region, the two axis lines and both axis
  titles; no ticks, no labels, no glyphs (scatter: 2 lines, 0 labels).
- histogram `if 0`: y axis ticked `-1` and `1`, y title `Density`, x title
  `x` (not the variable label), no x labels.
- f (all y missing): the x axis is ticked and labelled from the x data
  (2,000..5,000); the y axis has only its title (`ymiss`). kdensity f: no
  labels at all, titles `kdensity ymiss` and `x`.
- b1/b2: the non-empty plot is drawn and the empty plot keeps its legend key
  (scatter b1: legend `Mileage (mpg)` twice). An empty first plot still
  drives axis titles and label formats: b1 contour draws x labels `2000`
  (not `2,000`) and no axis titles and no contour key; b1 histogram has y
  title `Density`, no x title, x labels `2000`.
- e1 by(): both panels drawn, the empty one with axes only (except
  lpoly/lpolyci, 1 panel).

### dash today (rc + first line)

389 of 400 probes give twoway's rc and first message line (draws where
twoway draws; the same r(2000)/r(198) words where it refuses). The 11 gaps:

| Probe | twoway | dash |
|---|---|---|
| contour a, b1, b2, c, d, f, e1 | rc 0, draws | r(7102) Python traceback; last line `RuntimeError: dash_render: failed to build figure '': lower_level and upper_level cannot be NaN` |
| e2 of function, scatteri, pci, pcarrowi (`if 0, by(foreign)`) | r(198) `nothing to graph` | rc 0, draws (function prints `(note:  dash: plot 1 (function) drew nothing: it needs the points Stata computes ...)`) |

contourline draws in both (dash adds its `contourline: the legend's keys ... are not drawn` note).
Wording differences on the drawn fits: twoway prints
`(note:  regress could not fit model)`; dash prints
`dash: plot 1 (lfit): (note:  regress could not fit model)` (P17 territory).
Picture spot checks (`zpic/`, Bokeh model read from saved pages): `scatter
mpg weight if 0` — dash axes with titles and no ticks (as twoway); f
`scatter ymiss weight` — dash draws no x ticks where twoway labels x
2,000..5,000; `histogram mpg if 0` — dash y ticks −1, 1 (as twoway) but x
title `Mileage (mpg)` where twoway writes `x`; b1 scatter — 2 legend items
(as twoway); e1 lpoly — 1 figure (as twoway), e1 scatter — 2 (as twoway).

Bottom line for P12/Q21-Q22: twoway does **not** refuse zero observations
for 34 of the 40 data types (horizontal variants and the immediates aside) — it draws an empty graph (rc 0), also for one
empty plot among several, a graph-wide `|| if 0`, an `in`/`if` that selects
nothing, and an all-missing y. It refuses only lpoly/lpolyci (r(2000) `no
observations`), fpfit/fpfitci (r(198) `observation numbers out of range`,
after a note) and mband/mspline (r(198) `bands must be between 1 and 200`);
by() with every panel empty is r(198) `nothing to graph` for every type.
An r(2000) refusal for every type (Q22) would therefore differ from twoway
in most cases and need the help note D40 describes; copying twoway per case
(Q21) means: draw the empty graph, refuse the six types and the all-empty
by() exactly as above. dash already copies twoway's rc in 389/400 cases.

---

## 4. Time-series operators (`ts/ts.do`, generated from `test/fixtures/ts_operator_truth.json` plus 22 new probes)

All 99 fixture probes were re-run in twoway and in dash with the fixture's
datasets (`_zt_data`, copied from `scripts/extract_ts_operator_truth.do`:
sp = sp500 tsset t; spd = tsset date; us = sorted by close; nt = no tsset;
xt = xtset; au = auto), plus on `sysuse gnp96` (`tsset date`, %tq):

```
N01 line gnp96 date           N02 line D.gnp96 date        N03 area d.gnp96 date
N04 line L.gnp96 date         N05 line L.gnp96 gnp96       N06 replace gnp96=. in 1; line gnp96 date
N07 replace gnp96=. in L; line gnp96 date                   N08 replace gnp96=. in 1; area gnp96 date
N09 scatter D.gnp96 date      N10 line D.gnp96 L.gnp96     N11 tsline D.gnp96
N12 sort gnp96; line D.gnp96 date                           N13 tsset, clear; line D.gnp96 date
N14 tsset, clear; line gnp96 date                           N15 line D.gnp96 date if date >= tq(1970q1)
N16 line F.gnp96 date         N17 line S4.gnp96 date       N18 line D.gnp96 date, sort
N19 rarea L.gnp96 gnp96 date  N20 bar D.gnp96 date
S01 (sp500, tsset date) line D.close L.close                S02 line D.close date
```

Verdict: **twoway allows time-series operators in twoway graphs**, and the
operator forms it accepts and refuses are exactly those dash accepts and
refuses: 121 of 121 probes agree on rc and first line (twoway's answers
also match the 18oct2026 fixture exactly: 64 rc 0, no drift).

- Accepted (rc 0): operators on y and x of scatter line connected area bar
  spike dropline dot lfit qfit lfitci qfitci mspline mband, the r-types, the
  pc-types, tsline, tsrline; L. D. F. S#. L(1/2). DL. D2. L0. and
  lower case; `line D.gnp96 date`, `area d.gnp96 date`, `line L.gnp96
  gnp96`, `line D.close L.close`, `bar D.gnp96 date`, `rarea L.gnp96 gnp96
  date` (N01-N11, N14-N20, S01-S02 all rc 0 in both).
- Refused in both with the same words: fpfit fpfitci lowess lpoly lpolyci
  histogram kdensity r(101) `factor-variable and time-series operators not
  allowed`; an operated x with `sort` on scatter/line/connected/area/bar/
  spike/dropline/dot/mspline/mband/r-types r(198) (same line, then `option
  sort() incorrectly specified`) while lfit/qfit/lfitci/qfitci and the pc-types take it (tsline/tsrline
  with `sort` draw); by() with an operated variable r(5) `not sorted`;
  data not sorted by the time variable r(5) `not sorted` (N12); not tsset
  r(111) `time variable not set` (N13; N14 without an operator draws); a
  string r(109); `i.` r(101); `X.` r(198) `X:  operator invalid`.
- Only difference: on B01-B03 and B05 (by() with an operator) dash prints a
  second line after twoway's `not sorted`: `dash: twoway refuses by() with a
  time-series operator in a plot variable; generate the variable first ...`
  (kept under Q43).

### P1(8): date-axis ticks with a missing y at an end row

twoway's x tick labels from the SVG text; dash's from the saved page's
Bokeh model (`DatetimeAxis` → `FixedTicker.ticks`, ms since 1970, converted
to %tq; `pageticks.py`, `tscmp.py`):

| Probe | twoway x labels | dash x ticks |
|---|---|---|
| N01 line gnp96 date | 1970q1 1980q1 1990q1 2000q1 | same |
| N02 line D.gnp96 date | 1970q1 1980q1 1990q1 2000q1 | 1967q2 1976q1 1984q4 1993q3 2002q2 |
| N03 area d.gnp96 date | 1970q1 ... 2000q1 | 1967q2 (35 quarters) 2002q2 |
| N04 L., N09 scatter D., N11 tsline D., N18 D. with sort, N19 rarea L., N20 bar D. | 1970q1 ... 2000q1 | 1967q2 ... 2002q2 |
| N06 plain `line gnp96 date`, first y missing; N08 area, first y missing | 1970q1 ... 2000q1 | 1967q2 ... 2002q2 |
| N07 plain line, last y missing; N16 `line F.gnp96 date` | 1970q1 ... 2000q1 | 1965q1 1970q1 ... 2000q1 (8 ticks, 5-year step) |
| N15 `D.` with `if date >= tq(1970q1)` | 1970q1 ... 2000q1 | same |
| N17 `line S4.gnp96 date` (first 4 rows missing) | 1970q1 ... 2000q1 | same |
| N14 no tsset, `line gnp96 date` | 1970q1 ... 2000q1 | same |
| S02 sp500 `line D.close date` (daily) | 01jan2001 01apr2001 01jul2001 01oct2001 01jan2002 | same |
| N05, N10, S01 numeric x | 4000..10000 / 1000..1400 | same values |

So the audit's TR-4 cause is confirmed: a missing y in the first or last
row, operator or not, moves dash off Stata's ticks (N06/N07/N08 have no
operator). S4. (four missing rows) happens to
land back on Stata's ticks.

---

## 5. dash-only words (`words/words.do`, 69 forms + title("'90s"))

Each on `scatter mpg weight` (sysuse auto) unless named; twoway rc + first
line vs dash rc + first line (dash's `dashboard saved` lines omitted).
Class: **S** = dash-only synonym of a twoway spelling (twoway's form in
brackets); **E** = dash extension with no twoway spelling; **V** = a value
form, not a word; **=** = twoway's own word (control or found here).

| Word (probe) | twoway | dash | Class |
|---|---|---|---|
| ytitle2() yti2() ylabel2() yla2() yscale2() ysc2() xtitle2() xti2() xlabel2() xla2() xscale2() xsc2() ytick2() xtick2() ymlabel2() xmlabel2() ymtick2() xmtick2() yline2() xline2() | r(198) `option <word>() not allowed` (each) | rc 0, `(note:  dash: graph '': <word>() (<base>(..., axis(2))) is not drawn: no layer is on yaxis(2).` | S [`<base>(..., axis(2))`] |
| tlabel2() ttick2() tline2() tscale2() ttitle2() | r(198) `option <word>() not allowed` | rc 0, note naming xlabel2()/xtick2()/xline2()/xscale2()/xtitle2() | S [`tlabel(..., axis(2))` etc.] |
| tlabel() ttitle() (control) | rc 0 | rc 0 | = |
| marker(S) | r(198) `option marker() not allowed` | rc 0 | S [msymbol()] |
| malpha(50) | r(198) `option malpha() not allowed` | rc 0 | S-like [mcolor(%50)] |
| lalpha(50) on line | r(198) `option lalpha() not allowed` | rc 0 | S-like [lcolor(%50)] |
| falpha(50) on area | r(198) `option falpha() not allowed` | rc 0 | S-like [fcolor(%50)] |
| jseed(1) | r(198) `option jseed() not allowed` | rc 0 | S [jitterseed()] |
| mlg(3) (with mlabel) | r(198) `option mlg() not allowed` | rc 0 | S [mlabgap()] |
| plotbgcolor(gs14), pbgc(gs14) | r(198) `option plotbgcolor() not allowed` / `option pbgc() not allowed` | rc 0 | S-like [plotregion(fcolor())] |
| cv(price), colv(price) | r(198) `option cv() not allowed` / `option colv() not allowed` | rc 0 | S [colorvar()] |
| colpalette(viridis) | r(198) `option colpalette() not allowed` | rc 0 | E (nearest twoway: colorlist()/colorrule()) |
| colornlevels(5) | r(198) `option colornlevels() not allowed` | rc 0 | S [colorlevels()] |
| colormissing(red) | r(198) `option colormissing() not allowed` | rc 0 | S [colorformissing()] |
| hover(make) | r(198) `option hover() not allowed` | rc 0 | E |
| table | r(198) `option table not allowed` | rc 0 | E |
| bw(5) on bar, bw(2) on histogram, bw(5) on spike | r(198) `option bw() not allowed` | rc 0 (folded into barwidth) | S [barwidth()] |
| bw(5) on scatter | r(198) `option bw() not allowed` | rc 0, `(note:  dash: ignoring unsupported option(s): bw())` | accepted-with-note |
| kernel(GAUSSIAN) on kdensity | r(198) `invalid kernel function` | rc 0 | V (case of kernel(gaussian)) |
| xsize(()) | r(198) `option(s) ( ) not allowed` | rc 0, `(note:  dash: graph option xsize(()) is not a number; using None instead.)` | V |
| colorvar(make) (string) | r(7) `'make' found where numeric variable expected` | rc 0 | V (extension: string colorvar) |
| `if price<0, colorvar(price)` | r(3001) `_calc_levels():  3001  incorrect number of arguments` | rc 0 | V |
| title("'90s") | r(100) `) required` | rc 0 | V |
| scheme(nosuchscheme) | rc 0, `(note: scheme nosuchscheme not found, using s2color)` | r(198) `dash: scheme() must be one of economist, meta, ...` | reverse: dash refuses what twoway draws |
| theme(dark), link(g2), filter(foreign), title2(), subtitle2() on the one-line form | r(198) `option <w>() not allowed` | r(198) `option <w>() not allowed` (same) | = (dash refuses them here too) |
| colorallowmultiple, colorotherlabel("Other") (with colordiscrete), colorkeysreverse | rc 0 | rc 0 | = (undocumented twoway words, not dash-only) |
| colorvarminmax, colorformissing(), colorlevels(), jitterseed(), mlabgap(), msymbol(), barwidth(), kernel(gaussian), ttext() (controls) | rc 0 | rc 0 | = |

Count: 25 second-axis/t-axis spellings (S), marker/jseed/mlg/cv/colv/
colornlevels/colormissing/bw (8 S), malpha/lalpha/falpha/plotbgcolor/pbgc
(5 S-like), colpalette/hover/table (3 E), and 5 value forms (V), all
accepted by dash and refused by twoway; scheme(unknown) goes the other way.

---

## 6. twoway__contour_gen (`contour/contour.do`, `contour3/c3.do`)

Location: `/Applications/StataNow/ado/base/t/twoway__contour_gen.ado`
(v1.0.15, 66 lines). Syntax:

```
twoway__contour_gen zvar yvar xvar [if] [in], cuts(numlist) [gen(z y x levels)] [line] [heatmap] [interp(string)]
```

- **Replaces the dataset** (`keep if/in`, `keep varlist`, then the Mata
  routines `_contour_filled()` / `_contour_line()` / `_contour_heatmap()`
  in the compiled library, `getmata` back). Output: four variables, default
  names `z y x levels`: polygon vertices in rows, one polygon per run of
  rows separated by an all-missing row. Filled: `levels` is the band index
  1..k+1 for k cuts; line: one polyline per run, `levels` the cut index
  1..k, `z` the cut value. `interp()` default `thinplatespline` (set in
  `zyx2view_g.class:17`), also `shepard`, `none`.
- Caller: `zyx2view_g.class` `reset_dserset` (lines 252-346) runs it under
  `preserve` on the plot's serset and stores the result as the derived serset
  (`.dserset`). Cuts: `ccuts()` when given, else the z axis's major tick
  values, interior ticks only when the axis uses a rule (levels()).
  **Cuts are computed only when the graph is drawn**: after `twoway contour
  ..., nodraw`, `.Graph.plotregion1.plot1.lastcuts` is empty and the dserset
  id is `.`; after a drawn graph (batch draws invisibly) lastcuts is
  `7700 7800 7900 8000` (default), `7606.5 7657 7707.5 7758 7808.5 7859
  7909.5 7960 8010.5` (levels(10)), `7500 ... 8000` (ccuts(7500(100)8000)),
  and `serset dir` lists the derived serset `z y x levels`.

Timings (sandstone, `sysuse sandstone`, 6,400 points on a regular 80 x 80
grid, no duplicate nodes; cuts 7700 7800 7900 8000):

| Run | Time |
|---|---|
| twoway contour depth northing easting, draw + export | 0.86 s (levels(10) 0.87; interp(shepard) 0.79; interp(none) 0.78; ccuts(...) 0.81) |
| twoway contourline (default / levels(10) / shepard) | 0.26 / 0.29 / 0.25 s |
| twoway__contour_gen filled, thinplatespline / shepard / none | 0.23 / 0.23 / 0.22 s → 32,689 rows (27,021 vertices, 5,668 separators; levels 1-5) |
| twoway__contour_gen line, any interp | 0.09 s → 598 rows (575 vertices; levels 1-4) |
| dash contour (today: seeded 1,000-point subsample, 100 x 100 grid) | 3.5 s; contourline 1.3 s |

On gridded data `interp()` does not matter (same output; 40 x 40 grid of
1,600 points: 0.03 s each). On scattered points it dominates and grows about
as n^4:

| Scattered n | thinplatespline | shepard | none |
|---|---|---|---|
| 100 | 0.74 s (55,168 rows) | 0.37 s | 0.03 s (1,846 rows) |
| 200 | 9.7 s (210,410 rows) | 7.7 s | 0.22 s |
| 400 | 143 s (821,123 rows) | 128 s | 0.86 s |
| 1,000 | twoway contour's own draw had not finished after 12 min CPU; stopped | | |

How dash could call it at registration: `frame put z y x if <touse>,
into(<tmp>)` (or preserve), compute the cuts as twoway does (ccuts(), else
the z axis's interior natscale ticks for levels(); `.lastcuts` is not
available without drawing), `frame <tmp>: twoway__contour_gen z y x,
cuts(<cuts>) gen(z y x levels) interp(<interp>) [line]`, then read the four
columns (Python `sfi` from the frame, or a temp .dta) and split on the
all-missing rows into polygons (`levels` gives the fill band). Cost is
trivial for every help example (sandstone, gridded); for scattered data
above a few hundred points it is as slow as twoway itself (minutes to
hours), so Q26's "Stata grid at build" is only practical for gridded data
or interp(none).

---

## 7. aspectratio() with xsize()/ysize() (`svg1/svg1.do`)

`scatter mpg weight, aspectratio(r) xsize(w) ysize(h)`; plot-region rect and
axis-line lengths from the SVG (720 units/in):

| Command | Page | Plot region (= axis lines) | H/W |
|---|---|---|---|
| default (no aspectratio) | 7.5 x 4.5 in | 6.616 x 3.685 in (4763.81 x 2653.26), at x 522.8, y 113.4 | 0.557 |
| aspectratio(2) xsize(8) ysize(4) | 8 x 4 in | **1.726 x 3.276 in** (1242.54 x 2358.36), at x 2440.6..3683.2, y 100.8..2459.2 | 1.898 |
| aspectratio(1) xsize(5) ysize(5) | 5 x 5 in | **4.018 x 4.018 in** (2893.16 x 2893.16), at x 580.8, y 153.4 | 1.000 |

The ratio 2 applies inside the plot region's margins: with equal margins m,
(2358.36 − 2m)/(1242.54 − 2m) = 2 gives m = 63.4 units (0.088 in). dash today
(saved-page model): aspectratio(2) xsize(8) ysize(4) → `frame_width 167,
frame_height 334, width None, height None, min_height 160, max_height 560`,
and Bokeh prints `ERROR:bokeh.core.validation.check:E-1023
(MIN_PREFERRED_MAX_HEIGHT): Expected min_height <= height <= max_height`
(also for aspectratio(1) xsize(5) ysize(5): frame 430 x 430, same error); rc 0.
Whether the browser paints a 0 px plot was not re-measured.

---

## 8. a(b)c label rules crossing zero (`svg1/svg1.do`, `lab/lab.do`)

```
clear; set obs 11; gen x=_n; gen y=(_n-6)/10; gen y7=(_n-6)*.14
scatter y x, ylabel(-.3(.1).3)       -> -.3 -.2 -.1 0 .1 .2 .3
scatter y7 x, ylabel(-.7(.1).7)      -> -.7 -.6 -.5 -.4 -.3 -.2 -.1 0 .1 .2 .3 .4 .5 .6 .7
scatter y x, ylabel(-.3(.1).3) ytick(-.3(.05).3)  -> labels as the first
```

twoway writes `0`. dash's saved page has y `FixedTicker.ticks`
`[-0.3, -0.19999999999999998, -0.09999999999999998, 5.551115123125783e-17,
0.10000000000000003, 0.2, 0.3000000000000001]` and for −.7(.1).7 a zero
tick at `1.1102230246251565e-16` (plus residue on every other tick); no
`major_label_overrides`, so the label text comes from the page's formatter
(not executed here).

---

## Could not measure

- twoway contour on 1,000+ scattered points: stopped after 12 min CPU at
  n = 1,000; scaling measured at 100/200/400 only.
- Browser-painted pixels (zero-obs pages, the aspectratio frame, the
  formatter's text for 5.551e-17): only the saved page's Bokeh model was read.
- g.pdf counts rest on a layout heuristic (prompt + indentation); a handful
  of continuation or schematic misclassifications are possible.
- The by() zero-obs case "one panel empty" was made with a missing y; an
  `if` cannot empty one by() group without removing it from the by() sample.
