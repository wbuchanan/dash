# GAPS2 -- what dash is meant to deliver, and what it delivers

*Audit of 25 September 2026, at commit `91d97be` (branch `s3-bugs`). A second gap analysis, after `GAPS.md` (21 September 2026), whose findings the 27 work packages of `ROADMAP.md` closed or deferred.*

## What dash is meant to deliver

- **A drop-in `twoway`.** "dash accepts the same syntax as twoway and produces an interactive HTML file instead of a static Stata graph window" (dash.sthlp, Description); a Stata user pastes a working `twoway` command and expects the same picture and the same numbers (.ultraplan/PRD.md). The parity target is Stata's own `twoway` -- its plot types, options, estimators, schemes and answers to invalid input.
- **An interactive dashboard.** Several graphs, KPI cards, filters, linking and brushing, tabs, layouts, hover, export (dash.sthlp: Dashboard Options through Exporting).
- **Offline.** "The HTML file works offline in any modern browser -- no server, internet connection, or special software is required" (dash.sthlp, Description); and, optionally, a live served app (`dash serve`).
- **Installable.** `net install`/SSC, with `dash_setup` preparing Python (dash_setup.sthlp).
- **Engineered to the project rules.** Security first, rate limiting, a unit test for every function and end-to-end tests, logging, environment checks at start-up, hardened UTF-8 input, a health endpoint, adversarial tests (AGENTS.md / CLAUDE.md).

## How this was measured

Eleven auditors, one per area below, each listed what the documents promise for their area and checked every promise against the code, the tests and small Python probes run under Stata's own interpreter. A separate skeptic per area then tried to refute each finding against the code and corrected its severity, closability and plan (80 of the 191 findings were corrected, 1 was refuted). A completeness critic re-read every intent source for what the eleven missed (7 more, all verified). Findings reported under two areas were merged: 191 findings were **152 distinct gaps** (the duplicate map is in the appendix). At the maintainer's request 30 of them, and the 7 duplicate entries that pointed at them, were then removed from this document (25 September 2026), leaving **122**; their identifiers are not reused, so the numbering has gaps. No Stata was run for this audit: where a claim about `twoway`'s behaviour needed Stata, it cites Stata's own help or ado files or a measurement already recorded in this repository, and says "unmeasured" otherwise.

Severity is `GAPS.md`'s scale: **S1** silently wrong output, or a documented feature broken outright; **S2** a documented or accepted capability that does not work but fails visibly or is reported; **S3** fidelity, hygiene, coverage or documentation drift. Effort: **S** hours, **M** a day or two, **L** several days or more.

## Summary

**122 gaps: 19 S1, 47 S2, 56 S3.** 91 can be closed completely; 31 only partly, because of a limit outside dash (below); **none was judged impossible to close at all**. Effort: 42 S, 67 M, 13 L.

Most of these are new: `BUGS.md` held 4 open entries, all S3, when this audit began, and its release guard (no open S1 or S2) holds only for defects recorded there. The S1 and S2 gaps below are not yet recorded in `BUGS.md`.

| Area | Gaps | S1 | S2 | S3 |
|---|---|---|---|---|
| A. Plot types and twoway parity per type | 13 | 2 | 6 | 5 |
| B. Graph-level twoway options | 28 | 7 | 13 | 8 |
| C. Statistical fidelity | 5 | 1 | 2 | 2 |
| D. Schemes and visual fidelity | 16 | 2 | 6 | 8 |
| E. Dashboard features and interactivity | 13 | 2 | 1 | 10 |
| F. Served mode (dash serve) | 6 | 1 | 4 | 1 |
| G. Data handling and scale | 13 | 1 | 4 | 8 |
| H. Installation, setup, platforms, packaging | 5 | 0 | 3 | 2 |
| I. Security and robustness | 6 | 0 | 3 | 3 |
| J. Documentation, accessibility, browser and offline claims | 4 | 0 | 1 | 3 |
| K. Engineering quality, testing, maintainability | 7 | 1 | 1 | 5 |
| X. Cross-cutting (completeness critic) | 6 | 2 | 3 | 1 |

### The S1 gaps -- silently wrong output -- first

| ID | Gap | Closable | Effort |
|---|---|---|---|
| [A1](#a1) | line, connected, area and the range line and area types are always joined in x order, never in the data's order as twoway joins them | yes | M |
| [A9](#a9) | lpoly and lpolyci default bandwidth only approximates Stata's rule of thumb, and ignores degree() and kernel() (severity from C1) | partly | M |
| [B1](#b1) | Axis-label rules misread quoted numeric text, multi-line labels and numlist forms | yes | M |
| [B2](#b2) | Label/tick values do not widen the axis; xscale/yscale(range()) narrows or inverts it | yes | M |
| [B3](#b3) | Textbox sub-option abbreviations (and bcolor/lstyle/lalign/prefix/suffix) are drawn as part of the title/axis-title text | yes | S |
| [B4](#b4) | by() panels are drawn on independent scales by default | yes | M |
| [B5](#b5) | legend order() text and label()-after-order() are applied to the wrong keys | yes | M |
| [B6](#b6) | xtitle("") / ytitle("") do not remove the axis title | yes | S |
| [B7](#b7) | ytitle2()/xtitle2() draw their quote marks and ignore textbox grammar | yes | S |
| [C2](#c2) | histogram silently drops the maximum observation when the computed last bin edge falls a few units in the last place below the data's maximum | yes | S |
| [D1](#d1) | A user or third-party scheme's quoted values (RGB colours, %opacity) are dropped without a warning | yes | S |
| [D2](#d2) | Size options are read on a private pixel ladder: numbers as pixels, keywords off the scheme's scale, and Stata's units refused | yes | M |
| [E1](#e1) | KPI fmt() accepts formats the card then does not apply, and %w.0g rounds the card to one significant digit | yes | M |
| [E2](#e2) | exclude() leaves excluded graphs and cards showing rows from a filter state that no longer exists | yes | M |
| [F1](#f1) | dash serve returns rc 0 when no server ran (port in use or app crash); the app clamps an out-of-range --port instead of refusing it | yes | S |
| [G1](#g1) | Internal column names can overwrite a user variable, and dash's working columns need room in the user's dataset | yes | M |
| [K2](#k2) | The declared minimums (Python 3.8, bokeh 3.0) are false: every render needs Bokeh 3.6+, hence Python 3.10+, and the served app also crashes at import on 3.8/3.9 (severity from H1) | yes | S |
| [X1](#x1) | Dropdown filters rewrite string codes that look like numbers, drop the categories "None", "nan" and "NaT", and on the saved page cannot select small numbers | yes | S |
| [X2](#x2) | colorvar(): colordiscrete with colorcuts() is read as intervals, and cuts below the minimum are kept. twoway's colorlevels(), colorvarminmax, colorrule() and z-axis options are not drawn, and its default z-tick levels are replaced (documented) by a continuous map | partly | M |

### What limits the 'partly closable' gaps

No gap is impossible to close outright, but 31 can be closed only in part. The limits fall into a few kinds:

- **Stata's compiled internals.** `natscale`/`_tsnatscale` (the `#N` tick rules), lpoly's rule-of-thumb bandwidth, and contour's surface interpolation are compiled Mata with no source shipped. dash can only fit a model to measured answers, or compute the result in Stata at build time and embed it (A5, A9, B24). Options that run arbitrary Stata estimators (`estcmd()`, `estopts()`, `predopts()`) can be honoured only at build time, not after an in-browser filter move (A4).
- **Bokeh/BokehJS.** One legend per figure, no `textfirst`/`stack` legend keys, no labels on minor ticks, no per-tick label styling, no whole-canvas border, one font style per text object (no mixed SMCL `{bf:}`/`{it:}` in a line), no arrowhead marker, and a plot-region aspect ratio known only after browser layout (B10, B11, B16-B18, B21, B23, B30, B33, D3, D5, D14). The in-page PNG button captures figure canvases, not HTML widgets (E10).
- **The offline page.** A saved page recomputes in the browser with no Python, so each estimator must be re-implemented in JavaScript to refit after a filter move, a second implementation to keep in step (C4, K10). Every drawn row must be embedded, bounded by browser memory (G3, G14, I2).
- **Processes and packaging.** pip has no transactional rollback (H8). One event loop and the GIL serialize served recomputes (F3). BokehJS needs `unsafe-eval` in its Content Security Policy (I12).
- **Intentional bounds.** The `n()` and `bin()` caps are deliberate resource limits (A15).

## The gaps, by area

Each gap below says what is intended and what dash does, with evidence; whether it can be closed, and if only partly, what stops it; a short plan; and whether it is already tracked. A gap reported under two areas appears in full once, and the other entry points to it.

## A. Plot types and twoway parity per type

dash is meant to draw every twoway plot type with twoway's syntax, type-specific options and picture (dash.sthlp Plot types; the PRD calls it a "drop-in replacement"). It draws 40 types in both modes, with twoway's names, abbreviations, variable counts and empty-sample answers. Most computed statistics match Stata at a given bandwidth: the fits and their stdp/stdf/stdr bands, lowess, mspline, mband, fpfit/fpfitci, kdensity, histogram and lpoly. Several things are missing:
- Six twoway types and Mata-matrix plots are refused.
- `function` evaluates only 10 math functions.
- Nothing can be drawn horizontal.
- Line and area types are joined in x order instead of the data's order.
- Some geometry and styling differs from twoway without any note: dot rows, bar and rbar width, rcap and rcapsym caps, and arrowheads.
- lpoly's default bandwidth is approximate, and lpolyci's band is a bootstrap.
- About 40 type options are named in the note but not drawn.
- `colorvar()` is drawn on 4 types only.
- Legend keys and axis titles differ from twoway's.
- dash does not check which types an option applies to.

| ID | Gap | Sev | Closable | Effort |
|---|---|---|---|---|
| A1 | line, connected, area and the range line and area types are joined in x order, never the data's order | S1 | yes | M |
| A2 | pcarrow/pcbarrow/pcarrowi arrowheads ignore the marker options; pcbarrow's heads are filled black | S2 | yes | M |
| A3 | Bar and cap geometry: rbar ignores `barwidth()`; bar/rbar widths, rcap cap width and rcapsym caps are not twoway's | S2 | yes | M |
| A4 | Many type-specific options are named in the note and not drawn; most are missing from the help's unsupported list | S2 | partly | L |
| A5 | Six twoway types and `matamatrix()` plots are not drawn | S2 | partly | L |
| A6 | `function` draws nothing for most Stata expressions | S2 | yes | M |
| A7 | `horizontal` is not drawn on any plot type | S2 | see B12 | - |
| A8 | `colorvar()` is drawn on 4 types; `jitter()` is not drawn on rscatter, rcapsym, pcscatter, pccapsym | S2 | yes | L |
| A9 | lpoly/lpolyci default bandwidth only approximates Stata's rule of thumb and ignores `degree()`/`kernel()` | S2 | partly | M |
| A10 | lpolyci's band is a bootstrap percentile band; `pwidth()` and `var()` are not read | S2 | see C7 | - |
| A11 | All-missing scatter, constant-x lowess and constant kdensity print "drew nothing" where twoway is silent | S3 | yes | S |
| A12 | An option twoway refuses on a type is dropped in silence | S3 | yes | M |
| A13 | Default legend keys and axis titles per plot type are dash's own, not twoway's | S3 | yes | M |
| A14 | `dot` is drawn as a plain scatter: no dot rows, and `dotextend()`, `ndots()` and the d-options are not drawn | S3 | yes | M |
| A15 | dash refuses values on some types that twoway draws | S3 | partly | M |

<a id="a1"></a>
### A1. line, connected, area and the range line and area types are always joined in x order, never in the data's order as twoway joins them

- **Gap:** twoway joins line, connected, area, rline, rarea and rconnected in the data's order, and `sort` gives x order (line.sthlp:223, 302). Only tsline/tsrline sort by time, and they ignore `sort(varlist)` (twoway_tsline_parse.class:32, :21-22). dash sorts every layer by x (`sort_values(xvar)` in `map_line`, dash_render.py:7313, and likewise in `map_area`, `map_rline` and `map_rarea`). In a probe with x in data order 2,5,3,6,1, all five types are joined 1,2,3,5,6, while connected's markers keep the data order. The help documents this (dash.sthlp:3035-3046), but no note is printed at run time, so a path plot such as a Phillips curve is silently redrawn. dash also names `sort(varlist)` on tsline/tsrline, where twoway ignores it.
- **Closable:** yes -- keep the source's row order unless `sort` is given.
- **Plan:**
  1. Keep row order in `map_line`, `map_area`, `map_rline` and `map_rarea` unless `sort` is given; tsline/tsrline sort by time.
  2. Carry `__dash_row__` so the filter callback and the served redraw keep that order.
  3. Honour bare `sort`, stop naming `sort(varlist)` on tsline/tsrline, and rewrite dash.sthlp's "Connection order" paragraph and the `map_line` docstring.
  4. Test path order against twoway serset/SVG on unsorted auto and on a time path, with and without `sort`, in both modes and after a filter move, with a 1e6-row bound.
- **Tracked:** GAPS.md E1 (`sort(varlist)` deferred); BUGS.md:2441-2443 (bare `sort` not named on the eight types); the data-order default is new.

<a id="a2"></a>
### A2. Arrowheads of pcarrow, pcbarrow and pcarrowi ignore the marker options, and pcbarrow's heads are filled black

- **Gap:** In twoway (twoway_pcarrow.sthlp:148-170):
  - `msize()` sizes the head, `mangle()` sets its angle (default 28.64°) and `barbsize()` sets how much is filled.
  - `mcolor()`, `mfcolor()`, `mlcolor()` and `mlwidth()` colour the head, and `headlabel` moves labels to it.
  - s2color draws an outline-only head (`parrowbarb zero`).

  dash draws:
  - A fixed `OpenHead(size=10)` in the line colour (dash_render.py:11034). pcarrowi uses the same code (:11391).
  - A `NormalHead` at both ends for pcbarrow (:11105-11106), which Bokeh fills black by default.

  `msize()`, `mcolor()` and `mfcolor()` are dropped with no note. `mangle()`, `barbsize()` and `headlabel` are named in the note.
- **Closable:** yes -- stock Bokeh heads cover size, colour, open vs filled and `headlabel`. `mangle()` and a partial `barbsize()` need custom head geometry, because stock heads have a fixed angle of about 26.6° and are either fully filled or not filled.
- **Plan:**
  1. Build each head as an `OpenHead` or a filled `NormalHead`. Size it in px from `msize()` using the scheme's parrow symbolsize, colour it with twoway's precedence, and draw the same head at both ends of pcbarrow.
  2. Apply `_apply_mlabel_opts` at (x2, y2) for `headlabel`.
  3. For `mangle()` and a partial `barbsize()`, draw heads as a patches glyph whose vertices a shared CustomJS recomputes in screen space, in both modes. If this step is deferred, document the ~2° difference.
  4. Declare `mangle()` and `barbsize()`, and replace P4-20 (test/test_phase4_plots.py:257).
  5. Test head size, angle and colour against twoway SVG under s2color and s1mono, in both modes, including pcarrowi.
- **Tracked:** new.

<a id="a3"></a>
### A3. Bar and cap geometry: rbar ignores barwidth(); bar and rbar default widths, rcap cap width and rcapsym's caps are not twoway's

- **Gap:** In twoway:
  - `barwidth()` defaults to 1 x-unit on bar and rbar (twoway_bar.sthlp:123-133, twoway_rbar.sthlp:118-121).
  - rcap's `msize()` sets the cap width.
  - rcapsym draws a spike plus end markers, with no cap lines.

  dash, with no note in any of these cases:
  - Uses 0.8 × the smallest x gap as the width on bar (dash_render.py:7566-7568) and rbar (:10011-10014).
  - Never reads `barwidth()` on rbar, although it declares `barwidth()` for every type (dash.ado:909).
  - Sizes rcap caps at ±0.2 × the smallest gap in data units and ignores `msize()` (:10143-10147).
  - Adds two cap segments to rcapsym.

  With no `base()`, dash starts bars at 0, where twoway applies its own base rule.
- **Closable:** yes.
- **Plan:**
  1. In `map_bar` and `map_rbar`, default the width to 1 x-unit (converted to ms on a date axis). Read `barwidth()`/`bw()` on rbar, follow twoway's measured base rule, and drop the spacing-derived width from the filter callback and the served redraw.
  2. In `map_rcap`, draw caps in screen units from `msize()` and the scheme's symbolsize.
  3. In `map_rcapsym`, remove the cap segments.
  4. Update the tests that pin the old widths, and document any remaining difference.
  5. Build a twoway SVG fixture and test against it in both modes:
     - bar widths at x spacing .1, 1 and 5
     - rbar with `barwidth(.3)`
     - rcap with `msize(small|large)`
     - rcapsym with no cap lines
     - the base when every y is above 0
     - a %td x axis
- **Tracked:** BUGS.md:504 (bar default width recorded as a divergence, not acted on); rbar `barwidth()`, rcap `msize()` and rcapsym caps are new.

<a id="a4"></a>
### A4. Many type-specific twoway options are named in the note and not drawn, and most are missing from the help's unsupported list (also reported as C3, C9)

- **Gap:** twoway's per-type help files list these options, which dash does not draw:
  - Fits: `nofit`, `fitplot()`, `ciplot()`, `atobs`, `estcmd()`/`estopts()`/`predopts()`.
  - kdensity: `area()`, `boundary`. histogram: `gap()`.
  - function: `droplines()`, `yvarformat()`/`xvarformat()`.
  - bar: `baroffset()`. area: `nodropbase`.
  - General: `connect()`, `cmissing()`, `recast()`, `sort(varlist)`, `mlabvposition()`.
  - tsline's t-options, and pc `headlabel`.

  19 of these are neither declared nor read (grep), so they fall to the catch-all and are named in the note. Five are on the pending list (dash.ado:1031-1077). dash.sthlp:514-515 says the full list is in "Unsupported Stata twoway options", but that section (:2939-3098) omits `fitplot()`, `ciplot()`, `baroffset()`, `ndots()`, `gap()`, `yvarformat()`/`xvarformat()`, `mangle()`, `barbsize()`, the t-options and `headlabel`. Only some are documented as named elsewhere (dash.sthlp:1803-1808, :472).
- **Closable:** partly -- `estcmd()`, `estopts()` and `predopts()` pass estimator options that only Stata can run. They can be honoured for the view Stata computes at registration, but not on saved-page or served filter moves. Every other option, `atobs` included, can be drawn in both renderers.
- **Plan:**
  1. Do the presentation options first:
     - `nofit`, and `fitplot()`/`ciplot()` with `recast()`, in `_render_ci_band`.
     - `connect(J|stairstep|l)` and `cmissing(n)` in `map_line`.
     - tsline's t-options, mapped onto the x-options using the tsset unit.
  2. Then `atobs`, `baroffset()`, `gap()`, `droplines()`, `yvarformat()`/`xvarformat()`, kdensity `area()`/`boundary`, `headlabel`, `sort(varlist)` and `mlabvposition()`.
  3. Compute `estcmd()`/`estopts()`/`predopts()` in Stata at registration, and name them on filter moves.
  4. Generate dash.sthlp's unsupported list from `_dash_rep_und_tab`, the pending list and the undeclared type options. Extend test_help_conformance.py to check it in both directions.
  5. Test each option against live twoway in test_twoway_option_parity.cscript, in both modes.
- **Tracked:** Partly closed in WP-29 (P0.1, commit b0d170d): sort(varlist) is honoured; open: nofit, fitplot(), ciplot(), atobs, estcmd()/estopts()/predopts(), kdensity area()/boundary, histogram gap(), function droplines() and yvarformat()/xvarformat(), baroffset(), nodropbase, connect(), cmissing(), recast(), mlabvposition(), the tsline t-options and pc headlabel, and the help unsupported list; was: GAPS.md E1 (`connect`, `cmissing`, `recast`, `sort`, `mlabvposition` deferred by WP-27); the others are new.

<a id="a5"></a>
### A5. Six twoway plot types and Mata-matrix plots are not drawn (contour, contourline, heatmap, rpcap, rpspike, sunflower; matamatrix())

- **Gap:** graph_twoway.sthlp:60-61 and 78-80 list contour, contourline, heatmap, rpcap and rpspike as twoway plot types. `twoway sunflower` and `matamatrix()` plots have help files but are Stata-undocumented. dash handles them as follows:
  - The five listed types are refused by name, r(198) (dash.ado:3200-3222, `_dash_undrawn_plottype`), as documented at dash.sthlp:343-353.
  - `sunflower` reaches the generic "unrecognised plot type" message (dash.ado:3223-3230) and is missing from the help's Not drawn list.
  - `matamatrix` appears nowhere in the code or help (grep 0), so it is read as a varlist and refused.
- **Closable:** partly -- contour and contourline interpolate in compiled Mata with no shipped source (twoway__contour_gen.ado:35-45). dash can take twoway's exact output at registration, but those layers stay static on filter moves. The other types have no such limit.
- **Plan:**
  1. rpcap/rpspike: parse them as a 4-variable family in `_dash_plottype_families`, using the variable roles twoway_y3xview_parse assigns (measured). Draw with `map_rcap`/`map_rspike` plus `map_scatter`.
  2. heatmap and sunflower: port twoway__heatmap_gen.ado (`calc_xy_lev`) and twoway__sunflower_gen.ado to a shared Python/JS helper. Draw heatmap as rect/quad with a ColorBar, and sunflower petals as segments.
  3. contour/contourline: call `twoway__contour_gen` under preserve, export the polygons and lines as literal records, draw them with patches/multi_line, and say in a note that the layer is static under filters.
  4. `matamatrix()`: read the matrix columns by value in Mata into reserved export columns. Until then, refuse `sunflower` and `matamatrix()` by name.
  5. Test with a cscript comparing each generator's output and serset with live twoway, pytest in both modes, and a time bound for contour over 1e6 rows.
- **Tracked:** GAPS.md F1 (closed by refusing the five by name); sunflower and `matamatrix()` are new.

<a id="a6"></a>
### A6. `function` draws nothing for most Stata expressions: normalden(), ln(), _pi, comparisons, cond(), min(), round(), _b[] ... (also reported as C5)

- **Gap:** `twoway function` takes any Stata expression (twoway_function.sthlp), for example `normalden(x)` or `_b[_cons]+_b[x]*x`. `map_function` (dash_render.py:11775-11985) accepts only `x`, `pi`, `e` and 10 functions (`_SAFE_FUNCS`, :11821).
  - Probe over range(0.1 2): `normalden(x)`, `ln(x)`, `_pi`, `c(pi)`, `cond()`, comparisons, `min()`, `round()`, `int()`, `invlogit()`, `normal()`, `_b[]` and `scalar()` each draw 0 points. The only report is the "drew nothing" note documented at dash.sthlp:327-328.
  - `pi` and `e` are drawn as constants that Stata does not define.
  - `2^3^x` is read right-associated (512 at x=2).
  - twoway's answers for those last two cases are unmeasured.
- **Closable:** yes -- twoway's own generator `twoway__function_gen` can be called at registration. A function does not depend on the data, so the points stay exact on filter moves.
- **Plan:**
  1. In `_dash_process_segment`'s function branch (after `_dash_fn_refuse`), evaluate the expression with `twoway__function_gen` under preserve, with `range()`, `n()` and `generate()`. Pass the expression by value through Mata.
  2. Store the (x, y) pairs as literal records, as scatteri's values are, within the `n()` cap. `map_function` draws them, and the expression evaluator stays only for hand-written specs.
  3. Use the same route for `range(varname)`, `droplines()` and `horizontal`.
  4. Test the stored points against `twoway__function_gen` in a cscript over this corpus: `normalden`, `ln`, `_pi`, `c(pi)`, `cond`, comparisons, `min`/`max`, `int`/`round`, `invlogit`, `chi2den`, `_b[]` after regress, `scalar()`, `2^3^x`, `1/0` and sqrt of negatives. Add pytest in both modes and adversarial cases: the RNG state is unchanged, 10,000 points, and backticks or `$` in the expression.
- **Tracked:** new (the empty-layer note is documented at dash.sthlp:327-328).

**A7. `horizontal` is not drawn on any plot type** -- same gap as B12; see there.

<a id="a8"></a>
### A8. colorvar() is drawn on 4 types, and jitter() is not drawn on rscatter, rcapsym, pcscatter or pccapsym

- **Gap:** twoway lists the colorvar options on bar, spike, dropline, rbar, rcap, rline, pcarrow and other types, and it jitters the markers of rscatter, rcapsym, pcscatter and pccapsym. `_dash_fold_typed` draws `colorvar()` only on scatter, connected, rconnected and dot (dash.ado:1676) and names it in the note on the other 36 types. It names `jitter()` on the four types (:1685-1692). Both are documented (dash.sthlp:2470-2479). Where `colorvar()` is drawn, an unbinned colorvar is mapped continuously, while twoway bins at its z-axis ticks (dash.sthlp:2505-2508).
- **Closable:** yes -- Bokeh can colour segments, vbar and multi_line per element.
- **Plan:**
  1. Apply `_apply_colorvar` to the glyphs of bar, rbar, spike, rspike, rcap, dropline, the pc family, rscatter and rcapsym. For line, draw per-pair segments coloured by the endpoint twoway uses (measure which).
  2. Keep the note where twoway draws no colour (area and lfit, measured).
  3. Pass `jitter()` on the four types through `_apply_jitter`.
  4. By default, bin an unbinned colorvar at twoway's z-axis ticks (a bin column and a ColorBar with those ticks). Keep continuous colouring as an option.
  5. Test the colour of each mark against twoway SVG for each type, and jitter extents under a fixed seed, in both modes.
- **Tracked:** GAPS.md F4 colorvar row (closed by naming it); drawing on the other types is new.

<a id="a9"></a>
### A9. lpoly and lpolyci default bandwidth only approximates Stata's rule of thumb, and ignores degree() and kernel() (also reported as C1, C13)

- **Gap:** dash.sthlp:1817-1819 promises a default bandwidth.
  - Stata's rule of thumb ([R] lpoly eq. (3)) uses a w0 window, a global degree p+3 fit, the exponent 1/(2p+3) and a kernel constant, computed in compiled Mata (`_lpoly_work`, lpoly.ado:311).
  - dash's `_default_lpoly_bwidth` (dash_render.py:8653-8710) uses a fixed `_LPOLY_ROT_C = 0.65` times a global quartic fit to the power 1/5. It has no window, no kernel constant and no degree term, and uses range/10 below 8 observations.
  - dash.sthlp:1955-1970 records differences of −9.7% to −22% and +5.7% to +14.2% against `r(bwidth)`, and 185 against 77.4 on 7 cars. No note is printed at run time.
  - Only the default kernel, degree(1) and gaussian are measured.
- **Closable:** partly -- eq. (3) read literally gives 396.6 against Stata's 70.64 (auto mpg on weight), so the exact value comes only from Stata at registration. A filter move recomputed in JS or Python stays approximate until a fitted port is shown to match.
- **Plan:**
  1. In dash.ado, run `lpoly y x [if] [weight], nograph degree() kernel()` for each layer and by() panel. Store `r(bwidth)` in the spec and use it for the unfiltered view in both modes.
  2. Rewrite `_default_lpoly_bwidth(x, y, w, degree, kernel)` on eq. (3)'s structure. Fit it to `r(bwidth)` for 4 datasets × 8 kernels × degrees 0-3, weighted and unweighted, stored in stat_truth.json. Use it only for filter moves, and call it approximate in the help unless it matches to 1e-6.
  3. Pass `degree` and `kernel` from `map_lpoly` and `map_lpolyci`.
  4. Update dash.sthlp's Default bandwidth paragraph and the docstring. Tests hold the registered value to `r(bwidth)` exactly, and the filter-move value to the measured tolerance.
- **Tracked:** GAPS.md A4 (the rule of thumb "stays as it was"); dash.sthlp Default bandwidth.

**A10. lpolyci's band is a bootstrap percentile band, not Stata's, and pwidth() and var() are not read** -- same gap as C7; see there.

<a id="a11"></a>
### A11. An all-missing scatter, a constant-x lowess and a constant kdensity print a 'drew nothing' note where twoway is silent (also reported as C8)

- **Gap:** dash.sthlp:235-238 says that when twoway draws a smoother empty in silence, dash is silent too. twoway draws a constant-x lowess and a constant kdensity with no message (BUGS.md:2559-2561), and an all-missing scatter too (rc 0, per EC-03's docstring). `_dash_note_empty_layer` (dash_render.py:20610) still prints "drew nothing" for all three, and test_pipeline_integration.py EC-03, EC-04 and EC-05 (:778-921) pin that note.
- **Closable:** yes.
- **Plan:**
  1. Measure twoway's rc, log text and serset for the three cases.
  2. Either mark them silent through `_mark_silent` (dash_render.py:7990), as `map_lpolyci` does, or keep the note and document it at dash.sthlp:235-238 as a deliberate difference.
  3. Update EC-03 to EC-05 to match, in both modes.
- **Tracked:** BUGS.md:2559 (open, S3).

<a id="a12"></a>
### A12. An option twoway refuses on a type is dropped in silence (bwidth(), n(), bands(), range(), base(), level(), kernel() ...) (also reported as C15)

- **Gap:** twoway refuses an option on a type that does not take it, with r(198), and dash.sthlp:505-513 promises that anything not honoured is named. Instead dash:
  - Ignores `bwidth()`, `n()`, `bands()`, `range()`, `base()` and `level()` on a scatter with no note (admitted at dash.sthlp:514-523). A probe of a scatter with `bwidth(3) kernel(gaussian) n(5) level(90)` renders with no warning.
  - Writes `kernel()` on a scatter to the spec (BUGS.md:2601).
  - Draws lpolyci `level(5)`, which twoway refuses (dash.sthlp:2064-2067).
  - Names refusals in a different order from twoway in mixed option lists (BUGS.md:2595).
- **Closable:** yes -- the fix belongs in `_dash_option_rules`.
- **Plan:**
  1. For every value option dash declares, measure which types twoway accepts it on, and store the result next to rejected_options.json.
  2. Encode that as an applicability list in `_dash_option_rules` (as for `discrete`/`stdp`/`mean`), and refuse elsewhere in twoway's words, r(198).
  3. Refuse lpolyci `level()` outside 10-99.99.
  4. Test each option × type cell against live twoway in a cscript, and add pytest that the spec never carries an inapplicable option.
- **Tracked:** BUGS.md open "kernel() on a type that takes no kernel is written to the spec without a note" (:2601); BUGS.md open "In a few mixed lists dash names another word than twoway names first" (:2595); ROADMAP WP-23 "Found on the way".

<a id="a13"></a>
### A13. Default legend keys and axis titles per plot type are dash's own, not twoway's (also reported as C10)

- **Gap:** twoway's defaults:
  - Keys: lowess "lowess y x", kdensity "kdensity var", lpoly "lpoly smooth: label", mband "Median bands", scatteri/pci "y".
  - Axis titles (axis_truth.json): no y title when the layers' y labels differ, and "y1 label/y2 label" for a range plot.

  dash's defaults:
  - Keys: "Fitted values" for every `_DASH_FIT_TYPES` type (dash_render.py:19500-19505), although that was measured only for lfit. kdensity is keyed by its variable label, the pc family by its type name (the lookup reads `yvar1`, not `y1var`), and scatteri as "scatteri".
  - Axis titles: `_dash_axis_labels` (:16003-16038) titles y from the first layer, so scatter+lfit gets y="mpg". Range types get no y title.
- **Closable:** yes.
- **Plan:**
  1. Measure the legend key and both axis titles for all 40 types, alone and with a scatter, from twoway SVG/.Graph output, and store them in axis_truth.json.
  2. Replace `_DASH_FIT_TYPES` with a per-type key rule built from the variable labels.
  3. In `_dash_axis_labels`, join range and pc y labels with "/", and draw no y title when the layers' labels differ.
  4. Update the label assertion in test_immediate_dashboards.py (:512-523), and test both modes against the fixture.
- **Tracked:** Partly closed in WP-29 (P0.3, commit 8d3593e): histogram and kdensity keys and titles name the variable as twoway does; open: the fit, lowess, lpoly and mband keys, the pc and immediate keys, no y title when the layers labels differ, and y1/y2 range titles; was: new.

<a id="a14"></a>
### A14. `dot` is drawn as a plain scatter: no dot rows, and dotextend(), ndots() and the d-options are not drawn

- **Gap:** twoway_dot.sthlp draws a row of dots across the full y span at each x (`dotextend(yes)` is the default). `ndots()` sets the number of dots and the d-options (`dsymbol()`, `dcolor()`, `dsize()` ...) style them. dash.sthlp:186-197 lists dot among the types drawn as twoway describes. In fact `map_dot` (dash_render.py:10301-10328) returns `map_scatter` unchanged. `ndots()`, `dotextend()` and the d-options are undeclared (grep 0) and named in the note. dash.sthlp:1901-1903 mentions only `dotextend(no)`, so the missing dot rows in the default picture are not documented anywhere.
- **Closable:** yes.
- **Plan:**
  1. In `map_dot`, add a Scatter of small dots in the scheme's dot style at `ndots()` evenly spaced positions per x. They span the computed y range with `dotextend(yes)`, or run from `base()` to y with `dotextend(no)`.
  2. Declare the d-options, `dotextend()` and `ndots()` with twoway's abbreviations in `_dash_parse_plot_opts`.
  3. Recompute the rows on filter moves in both modes.
  4. Test dot count, spacing and colour against twoway SVG under s2color, s1mono and economist, with pytest in both modes.
- **Tracked:** new.

<a id="a15"></a>
### A15. dash refuses values on some types that twoway draws (also reported as C11)

- **Gap:** twoway accepts all of the following, and dash refuses each with r(198), as documented (dash.sthlp:604-633, 1822-1825, 302-303):
  - `range(varname)` on function and kdensity, and a `.` end in the fits' `range()`.
  - Any whole-number `degree()`.
  - `n()` from 1 with no upper bound, and `bin()` with no upper bound.
  - `yaxis()`/`xaxis()` from 1 to 9.
  - A lowess `bwidth()` of 0 or ≥1 (twoway reads it as 0.8), and a kdensity `bwidth(0)` (twoway uses the default).
  - `mlabel()` with several variables (twoway uses the first).
  - A scatteri numlist such as `2/2`.
  - `msize(1e400)`, and out-of-range `lwidth()`/`mlwidth()`/`msangle()` on types that draw no line or marker.

  So a pasted twoway command that uses any of these stops.
- **Closable:** partly -- the `n()` ≤ 10000 and `bin()` ≤ 1000 caps are deliberate resource-exhaustion bounds (CLAUDE.md rule 3, ROADMAP WP-19) and stay. Everything else can follow twoway, including axes 3-9.
- **Plan:**
  1. Resolve `range(varname)` to the variable's min and max, by value, in dash.ado. Replace a `.` end in the fits' `range()` with the observed min or max.
  2. Allow `degree()` up to a documented bound (e.g. 10) in `_compute_lpoly_fit`. Read a lowess `bwidth()` of 0 or ≥1 as 0.8, and a kdensity `bwidth(0)` as the default.
  3. For `mlabel(a b)`, use the first variable with a note. Evaluate scatteri numlists as twoway does, clamp `msize(1e400)` as twoway draws it, and check `lwidth()`/`mlwidth()`/`msangle()` only on types that draw them.
  4. Support `yaxis()`/`xaxis()` 3-9 with extra Bokeh ranges, placed as twoway places them (coordinate with the axes-area findings).
  5. Test each form against live twoway (serset equality), and move the help text from "refused" to "as twoway".
- **Tracked:** new (each refusal is documented in dash.sthlp).

## B. Graph-level twoway options

Area B covers twoway's graph-level options: titles and textboxes, axis labels, ticks, scales and titles, second axes, legend, `by()`, added lines, regions and sizing. Most of the core works in both render modes. That core is title/subtitle/note/caption text with `size()`/`color()`; `xlabel`/`ylabel` numlists, `#N`, `minmax` and value-"text" pairs with `format`/`labsize`/`angle`/`grid`; log/reverse/range scales; dash's own `*2` options; `legend` on/off/order/label/position/ring/cols/rows/size; `by()` with `cols`/`total`/`missing`; repeated `xline`/`yline`; region colours; and `xsize`/`ysize`/`aspectratio`. Most options dash does not implement are named in a note. Of the 33 gaps, 7 are S1 (silently wrong output), 16 are S2 (mostly named-but-not-drawn sub-option families, plus region sub-options dropped with no note) and 10 are S3 fidelity drift. Nearly all can be closed inside Bokeh. The real limits are `play()`, legend `textfirst`/`stack`, labels on minor ticks, a plot-region aspect ratio under responsive sizing, and twoway's compiled date-tick rule. No Stata was run for this audit: twoway's behaviour is cited from its help files and from measurements already recorded in the repo.

| ID | Gap | Sev | Closable | Effort |
|---|---|---|---|---|
| B1 | Axis-label rules misread quoted numeric text, multi-line labels and numlist forms | S1 | yes | M |
| B2 | Label/tick values do not widen the axis; `xscale`/`yscale(range())` narrows or inverts it | S1 | yes | M |
| B3 | Textbox sub-option abbreviations (and `bcolor`/`lstyle`/`lalign`/`prefix`/`suffix`) are drawn as part of the title/axis-title text | S1 | yes | S |
| B4 | `by()` panels are drawn on independent scales by default | S1 | yes | M |
| B5 | `legend` `order()` text and `label()`-after-`order()` are applied to the wrong keys | S1 | yes | M |
| B6 | `xtitle("")` / `ytitle("")` do not remove the axis title | S1 | yes | S |
| B7 | `ytitle2()`/`xtitle2()` draw their quote marks and ignore textbox grammar | S1 | yes | S |
| B8 | Date axes ignore the variable's display format and `xlabel(, format(%t...))` | S2 | see E3 | - |
| B9 | Explicit text `size()` uses a smaller scale than the scheme's defaults; relative and absolute sizes are refused | S2 | see D2 | - |
| B10 | Minor ticks and minor labels (`xmtick`/`ymtick`/`xmlabel`/`ymlabel`) are not drawn | S2 | partly | M |
| B11 | Named styles and colour lists are not read: `pstyle` (non-ci), `lstyle`, `mstyle`, `mlstyle`, `mlpattern`, `colorlist`, `coloruseplegend` | S2 | partly | M |
| B12 | Plot-level deferred options: `horizontal`/`vertical`, `recast()`, `connect()`, `cmissing(n)`, `sort(varlist)` | S2 | yes | L |
| B13 | SMCL markup in graph text (`{bf:}`, `{it:}`, `{sup:}`, `{&beta}`) is drawn literally | S2 | see D3 | - |
| B14 | The t-axis option family and twoway's advanced options are undeclared and missing from the help's "full list" | S2 | yes | M |
| B15 | `axis(#)` is not read, more than two axes are refused, and `yaxis(1 2)` is refused | S2 | yes | L |
| B16 | `by()` sub-options other than `cols`/`total`/`missing` are named but not honoured (`rows`, `holes`, `title`, `legend`, rescale, axes...) | S2 | partly | L |
| B17 | `legend()`: Stata's abbreviations and most sub-options are named but not drawn | S2 | partly | M |
| B18 | `plotregion()`/`graphregion()` sub-options, including Stata's abbreviations, are dropped with no note | S2 | partly | M |
| B19 | `t1title()` .. `r2title()` are not drawn | S2 | yes | S |
| B20 | `text()`/`ttext()` added text is not drawn | S2 | yes | M |
| B21 | `xlabel`/`ylabel`/`xtick` sub-options beyond `format`/`labsize`/`angle`/`grid` are not drawn (`valuelabel`, `nolabels`, colours, tick lengths...) | S2 | partly | M |
| B22 | `xline()`/`yline()`: numlist forms, Stata's abbreviations, `axis(2)`, `lstyle`/`style`/`noextend` are not drawn | S2 | yes | S |
| B23 | `xscale`/`yscale` sub-options other than `log`/`reverse`/`range` are not drawn | S2 | partly | M |
| B24 | `#N` ticks on %td-%th date axes follow a fitted model (about 60% agreement) | S3 | partly | L |
| B25 | Default axes are Bokeh's, not twoway's (tick positions, range padding, s2color vertical y labels) | S3 | yes | M |
| B26 | Legend placement differs from twoway's (explicit position, corners, `pos(0)`, `by()` graphs) | S3 | yes | M |
| B27 | Marker-label remainders: `headlabel`, pc* first-point labels, `mlabvposition`, `mlabtextstyle`, extended missing, value-labelled dates | S3 | yes | M |
| B28 | Options twoway refuses (`title2`, `subtitle2`, `mlabwidth`, `ciopts`, `blabel`, `at`, `xreverse`...) and unknown lower-case words are noted instead of refused | S3 | yes | M |
| B29 | Title and subtitle are left-aligned; textbox `position()`/`ring()`/`span`/`justification()` are not drawn | S3 | see D17 | - |
| B30 | `aspectratio()` shapes the whole figure, not the plot region, and gives way to `xsize`/`ysize` | S3 | partly | M |
| B31 | `by()` graph chrome differs from twoway's (panel labels, default note, repeated axes, missing-panel text) | S3 | yes | M |
| B33 | `scale()`, `fxsize()`, `fysize()`, `xoverhangs` and `yoverhangs` are not applied | S3 | partly | M |

<a id="b1"></a>
### B1. Axis-label rules misread quoted numeric text, multi-line labels and numlist forms

- **Gap:** In `axis_label_options.sthlp`, a rule is either a numlist (`a/b`, `a(b)c`, `a[b]c`, `a b to c`, `a b : c`) or value `"text"` pairs, where the text can be any string. dash.sthlp:2318-2327 promises Stata's vocabulary. `_dash_parse_axis_label_opt` (dash_render.py:16041-16075) flattens quoted and bare tokens alike, with these results:
  - `xlabel(1 "2019" 2 "2020" 3 "2021")` gives ticks [1,2,3,2019,2020,2021] with no labels and no warning.
  - A second label line is lost, and a compound-quoted label becomes a lone backtick.
  - `10 20 to 40` loses 30, and `1 2 : 5` uses `:` as a label.
  - `1/5` and `1[1]3` draw no ticks (they are named).
  - `xlabel2`/`ylabel2`/`xtick`/`ytick` share the parser.
- **Closable:** yes.
- **Plan:** 1. Tokenise with `_textbox_string_end`: a quoted or compound string is always label text, and consecutive strings are lines of one label. 2. Expand the numeric parts in dash.ado with Stata's `numlist` (or port the [U] numlist rules), write the expanded values into the spec, and keep the `_MAX_AXIS_TICKS` bound. 3. pytest each form in both modes. 4. cscript reading twoway's tick positions and label text (SVG) for the same rules.
- **Tracked:** Closed in WP-28, BUGS.md "Axis-label rules misread quoted numeric text, multi-line labels and numlist forms", commit 9cd93e8; residual deferred (WP-28): where twoway refuses a form outright (a second consecutive string, a label after an increment, single quotes, a bare word, a top-level comma list), dash draws what it can read and names the rest rather than refusing, because numlist's return code cannot tell those forms from ones twoway draws (a zero step is rc 0 in twoway); was: new.

<a id="b2"></a>
### B2. Label/tick values do not widen the axis; `xscale`/`yscale(range())` narrows or inverts it

- **Gap:** `axis_label_options.sthlp` says label and tick values widen the axis unless `norescale` is given. `axis_scale_options.sthlp` says `range()` only expands the scale and never narrows it; dash.sthlp:2333-2335 points users to `range()`. dash breaks both rules:
  - Explicit ticks only set a `FixedTicker` (dash_render.py:16783-16786). With `ylabel(0(20)100)` on mpg 12-41, 60-100 are never shown.
  - `_dash_apply_scale_ranges` (19017-19060) sets `Range1d(lo, hi)` exactly. `yscale(range(100))` gives an inverted axis (100 to 41), `range(20 30)` hides data outside 20-30, and `range(0)` ends exactly at the data maximum.
  - `yscale(r(0 100))` is named and ignored.
- **Closable:** yes.
- **Plan:** 1. After the layers are drawn (beside `_dash_finish_count_ticks`), set each axis extent to the hull of the drawn data, every label/tick position (unless `norescale`) and every `range()` value, never narrower than the data. 2. Treat `range(#)` as a value to include, not a bound; accept `r()` and missing values; handle log and date axes and `yscale2`/`xscale2`. 3. pytest in both modes. 4. cscript recording twoway's `.Graph.yaxis1` scale min/max for about 20 label/range combinations into a fixture, and assert against it.
- **Tracked:** Closed in WP-28, BUGS.md "Label and tick values do not widen the axis and xscale/yscale range() narrows or inverts it", commit 866601a; residual deferred (WP-28): the margin stays Bokeh's 5% of the span and the default ticker Bokeh's, not twoway's 2.2% of the canvas and its tick rule (B25); an axis without an explicit value keeps Bokeh's autorange; the %td probe (b2_td_range) and the by() probe (b2_by_range0) have no SVG fit and are recorded through .Graph only; was: new (dash.sthlp documents only the `xtick` case).

<a id="b3"></a>
### B3. Textbox sub-option abbreviations (and `bcolor`/`lstyle`/`lalign`/`prefix`/`suffix`) are drawn as part of the title/axis-title text

- **Gap:** `textbox_options.sthlp:41-77` and `title_options.sthlp` accept abbreviations such as `c()`, `si()`, `j()`, `m()`, `bc()`, `place()` and `orient()`, plus `prefix`/`suffix`, and axis titles also take `axis(#)`. dash.sthlp:519-525 promises that unimplemented sub-options are named. `_TEXTBOX_SUBOPTS` (dash_render.py:2438-2443) holds only full names and omits `bcolor`, `lstyle`, `lalign`, `prefix` and `suffix`, with these results:
  - `title("T", c(red))` draws the text `T\n,\nc(red)` in the scheme colour, with no warning.
  - `ytitle("Volume", axis(2))` titles the left axis with the whole tail as text.
  - After a full name, a later abbreviation is only named, not applied.
- **Closable:** yes.
- **Plan:** 1. Replace `_TEXTBOX_SUBOPTS` with a (full name, minimum abbreviation) table transcribed from `textbox_options.sthlp`, `title_options.sthlp` and `axis_title_options.sthlp`. 2. Normalise names in `_parse_textbox_opt` so `c()`/`si()` reach `_textbox_color`/`_textbox_size`; name the rest through `_dash_textbox`; route `axis(2)` to the `ytitle2`/`xtitle2` path. 3. pytest table over every spelling on all six text options, in both modes. 4. cscript comparing twoway's `.Graph.title` text and colour (or its SVG) with dash's output.
- **Tracked:** Closed in WP-28, BUGS.md "Textbox sub-option abbreviations are drawn as title text", commit d66a093; was: new.

<a id="b4"></a>
### B4. `by()` panels are drawn on independent scales by default

- **Gap:** twoway draws `by()` panels on one common scale unless `yrescale`/`xrescale` is given; test/test_natscale_axes.py:10-15 records both panels at 12-41, and dash.sthlp:2356-2358 promises one scale. In dash each panel gets its own `DataRange1d`. A common scale is imposed only for `#N` (`_dash_common_count_ticks`, dash_render.py:17355-17377), so Foreign mpg 72-99 and Domestic 12-39 are shown on different y ranges with no note, in both modes.
- **Closable:** yes.
- **Plan:** 1. After all panels are drawn, take the union extent per axis over every panel and share one range object across the panels, then place default ticks over it. 2. Implement `yrescale`/`xrescale` to keep independent ranges. 3. Use the same helper in the served app. 4. pytest asserting equal start/end across panels in both modes; cscript reading twoway's `.Graph.graphs[k].yaxis1` min/max.
- **Tracked:** new.

<a id="b5"></a>
### B5. `legend` `order()` text and `label()`-after-`order()` are applied to the wrong keys

- **Gap:** In `legend_options.sthlp:106-119, 216-298`, `order()` takes key numbers each followed by optional text, and `-` adds a text-only line. `label(# "text")` names key # whatever `order()` does, and `lastlabel()` overrides both. dash gets all of this wrong, with no warnings:
  - dash_render.py:15849 reads `order()` as `re.findall(r"\d+", ...)`. So `order(1 "Group 2" 3 "Three")` draws the keys mpg / Fitted values / price and ignores the texts.
  - `label()` is applied by displayed position after the reorder (15936-15946). So `order(2 1) label(1 "Data")` relabels the fit instead of the scatter.
  - `-` lines are dropped and `lastlabel()` is only named.
- **Closable:** yes.
- **Plan:** 1. Parse `order()` entries with `_textbox_string_end`/`_textbox_lines`: a key number followed by zero or more strings, or `-` plus strings for a text-only entry. 2. Build each key's text by key number (default, then `label(#)`, then `order()` text, then `lastlabel()`), and only then select and order the keys. 3. Draw `-` entries as `LegendItem`s backed by an invisible placeholder renderer, after checking that BokehJS draws a label-only row. 4. pytest in both modes; cscript comparing twoway's SVG legend text and order.
- **Tracked:** Closed in WP-28, BUGS.md "legend order() text and label() after order() are applied to the wrong keys", commit 0f8b376; residual deferred (WP-28): a layer that drew nothing has no key, so order() naming its number draws nothing where twoway draws the key; was: new.

<a id="b6"></a>
### B6. `xtitle("")` / `ytitle("")` do not remove the axis title

- **Gap:** `axis_title_options.sthlp:219-227` makes `xtitle("")` the standard way to remove an axis title, and dash.sthlp:455-458 treats empty text as clearing a title. `_dash_axis_labels` (dash_render.py:16036-16037) uses `x_label = x_text or x_default`, so `xtitle("")` still draws `weight` and `ytitle("")` still draws `mpg`, with no warning, in both modes. No test covers this.
- **Closable:** yes.
- **Plan:** 1. In `_dash_axis_labels`, tell an option given with empty text (raw value non-empty, `_textbox_lines` empty) from an absent option, and return `''` for the first; do the same for `ytitle2`/`xtitle2`. 2. pytest in both modes for `xtitle("")`, `ytitle("")`, `xtitle("", size(large))` and a histogram/kdensity default. 3. cscript: twoway's SVG for `scatter mpg weight, xtitle("") ytitle("")` has no axis-title text; assert that dash's `axis_label` is empty.
- **Tracked:** Closed in WP-28, BUGS.md "An empty xtitle() or ytitle() does not remove the axis title", commit 34a53a4; was: new.

<a id="b7"></a>
### B7. `ytitle2()`/`xtitle2()` draw their quote marks and ignore textbox grammar

- **Gap:** dash.sthlp:2403-2410 documents `ytitle2()`/`xtitle2()` as the second axis's title. dash.ado:693-699 declares them `string asis` so they can be read as textboxes. `_dash_add_secondary_axes` passes the raw value to `LinearAxis(axis_label=...)` (dash_render.py:17027-17028), with these results in both modes and with no warning:
  - `ytitle2("P2")` draws `"P2"` with its quotes.
  - `"a" "b"` is drawn as one quoted line.
  - `"P2", size(large)` is drawn verbatim.
- **Closable:** yes.
- **Plan:** 1. Read `{n}title2` through `_dash_textbox(raw, 'ytitle2'/'xtitle2')`, joining lines with newlines and naming unhonoured sub-options. 2. Apply `size()`/`color()` to the y2/x2 axis as `_dash_style_axis_titles` does for the primary axes. 3. pytest in both modes with quoted, multi-line, compound-quoted and sub-option strings. 4. Extend JSE-46 to compare the rendered right-axis label with twoway's SVG text for `ytitle("a" "b", axis(2))`.
- **Tracked:** Closed in WP-28, BUGS.md "ytitle2() and xtitle2() draw their quote marks and ignore textbox grammar", commit f1f5589; was: new.

**B8. Date axes ignore the variable's display format and `xlabel(, format(%t...))`** -- same gap as E3; see there.

**B9. Explicit text `size()` uses a smaller scale than the scheme's defaults; relative and absolute sizes are refused** -- same gap as D2; see there.

<a id="b10"></a>
### B10. Minor ticks and minor labels (`xmtick`/`ymtick`/`xmlabel`/`ymlabel`) are not drawn

- **Gap:** `axis_label_options.sthlp` documents `{x|y}mtick()` and `{x|y}mlabel()` with the same rule grammar as major labels. In dash they are pending (dash.ado:791-796) and named. `xtick()` already uses Bokeh's minor-tick channel (`_dash_apply_tick_option`, dash_render.py:16857), so the two have to be combined.
- **Closable:** partly -- Bokeh draws text only on major ticks, so minor labels in their own style need a second axis on the same range, or merging into the major labels (which gives them the major style).
- **Plan:** 1. Fold `xtick` and `xmtick` positions into one `CustomJSTicker` minor set, with the scheme's minor-tick length. 2. Draw `xmlabel` either by merging its positions into the major ticker with its own formatter text, or as an overlaid second axis with a smaller font. 3. pytest in both modes; cscript comparing twoway's SVG.
- **Tracked:** GAPS.md E1 (deferred).

<a id="b11"></a>
### B11. Named styles and colour lists are not read: `pstyle` (non-ci), `lstyle`, `mstyle`, `mlstyle`, `mlpattern`, `colorlist`, `coloruseplegend` (also reported as D6)

- **Gap:** twoway takes `pstyle(p#)`/`lstyle()`/`mstyle()`/`mlstyle()` from the scheme, draws `mlpattern()` on marker outlines, and colours `colorvar()` levels from `colorlist()`. In dash all of these are on the plot pending list (dash.ado:1025-1080) and named, except `pstyle` on the four ci types, which works; dash.sthlp Unsupported documents this. The gap is S2 because GAPS.md E1 grades accepted-but-inert options that way, and `pstyle(p#)`/`lstyle()` are common in published do-files.
- **Closable:** partly -- `coloruseplegend` (legend keys in a contour-line style) has no Bokeh counterpart beyond an ordinary discrete legend.
- **Plan:** 1. Resolve `pstyle(p#)` to the p# chain dash already builds from the parsed scheme; map `lstyle`/`mstyle`/`mlstyle` to their scheme sub-chains. 2. `mlpattern`: set `line_dash` on Scatter markers. 3. `colorlist`: use it as the palette for the `colorvar()` levels. 4. pytest in both modes; cscript comparing twoway's SVG styles.
- **Tracked:** GAPS.md E1 (deferred).

<a id="b12"></a>
### B12. Plot-level deferred options: `horizontal`/`vertical`, `recast()`, `connect()`, `cmissing(n)`, `sort(varlist)` (also reported as A7, G15)

- **Gap:** In twoway:
  - `horizontal` draws bar/spike/dropline/range types sideways.
  - `recast()` redraws a plot as another type.
  - `connect()` (including stairstep/stepstair) sets how points are joined.
  - `cmissing(n)` breaks lines at missing values.
  - `sort(varlist)` sets the join order.

  All are on dash's plot pending list (dash.ado:1025-1080) and named. dash.sthlp Unsupported documents that dash draws every plot upright, joins in x order and drops missing values.
- **Closable:** yes -- Bokeh has hbar/harea/Step glyphs and breaks lines at NaN.
- **Plan:** 1. `recast()`: re-dispatch the layer to the named type's mapper after checking that type's variables. 2. `cmissing(n)`: insert NaN rows at missing values. 3. `connect()`: map l/L/J/stairstep/stepstair/none to Line or Step glyphs. 4. `sort(varlist)`: stable sort by the varlist before joining. 5. `horizontal`: swap coordinates in the bar/spike/range/dropline mappers (hbar/harea); check each against twoway's SVG in a cscript.
- **Tracked:** Partly closed in WP-29 (P0.1, commit b0d170d): sort(varlist) sets the join order; open: horizontal/vertical, recast(), connect() and cmissing(n); was: GAPS.md E1 (deferred).

**B13. SMCL markup in graph text (`{bf:}`, `{it:}`, `{sup:}`, `{&beta}`) is drawn literally** -- same gap as D3; see there.

<a id="b14"></a>
### B14. The t-axis option family and twoway's advanced options are undeclared and missing from the help's "full list"

- **Gap:** twoway's help files define two groups of options that dash neither declares nor lists:
  - For tsline/tsrline: `tlabel()`, `ttick()`, `tmlabel()`, `tmtick()`, `ttitle()`, `tscale()`, `tline()` and `ttext()`.
  - In `advanced_options.sthlp`: `yvarlabel()`, `xvarlabel()`, `yvarformat()`, `xvarformat()` and `pcycle()`.

  dash.sthlp:515 calls its Unsupported section "the full list". None of the t* or var* options is declared (dash.ado:699-717), so they get only the generic "ignoring unsupported option(s)" note, and none appears in dash.sthlp. `pcycle()` is only counted as a graph-wide option (dash.ado:3937, dash.sthlp:473) and is not drawn. dash draws tsline/tsrline, so options like `tline(2001m1)` are ordinary usage.
- **Closable:** yes.
- **Plan:** 1. Declare the t* options in dash.ado; for tsline/tsrline, fold them onto x* after converting datelists with Stata's own date functions. 2. Implement `yvarlabel`/`xvarlabel` (legend and axis-title defaults), `yvarformat`/`xvarformat` (axis format fallback) and `pcycle` (style index modulus). 3. List anything left in dash.sthlp Unsupported and test_help_conformance.py. 4. cscript running tsline with `tline`/`tlabel` in twoway and dash and comparing positions.
- **Tracked:** REMAINING.md:128-131 (planning doc).

<a id="b15"></a>
### B15. `axis(#)` is not read, more than two axes are refused, and `yaxis(1 2)` is refused

- **Gap:** twoway addresses up to 9 axes with `axis(#)` on the label, title, scale, line and tick options, and allows `yaxis(1 2)`. dash.sthlp:2392-2399 documents dash's two-axis limit and its own `ytitle2()` etc. `axis(#)` is named, but the option is applied to the FIRST axis:
  - `ylabel(20 30, axis(2))` ticks the left axis, and `yscale(log axis(2))` makes the left axis log.
  - `yline(5000, axis(2))` is drawn on the default range.
  - `yaxis()`/`xaxis()` are validated as int 1..2 (dash.ado:1861), so `yaxis(3)` and `yaxis(1 2)` are refused.
- **Closable:** yes -- Bokeh supports any number of extra ranges and axes.
- **Plan:** 1. Route `axis(2)` on each axis option to the existing y2/x2 path, and generalise extra ranges to y2..y9/x2..x9. 2. Accept a `yaxis()`/`xaxis()` numlist: a layer drawn on axis 1 whose axis 2 shares its range object. 3. Keep dash's `*2` options as aliases. 4. pytest in both modes; cscript comparing twoway's `.Graph` axis counts, positions and ticks.
- **Tracked:** Partly closed in WP-29 (P0.5, commit 3208b2b): axis(2) on the label, title, scale, line and tick options is applied to the second axis; open: axes 3-9 and yaxis(1 2) are refused; was: dash.sthlp:2392-2399 (documented limit); REMAINING.md:2459 (`axis(#)` misrouted).

<a id="b16"></a>
### B16. `by()` sub-options other than `cols`/`total`/`missing` are named but not honoured (`rows`, `holes`, `title`, `legend`, rescale, axes...)

- **Gap:** `by_option.sthlp` defines `rows()`, `holes()`, `colfirst`, `compact`, `iscale()`, `imargin()`, the i*/noi* axis options, `yrescale`/`xrescale`/`norescale`, `noedgelabel` and `style()`. It also puts `title()`/`subtitle()`/`note()`/`caption()`/`legend()` inside `by()`: that is where a by-graph's title goes (by_option.sthlp:454-458). `_dash_parse_by` honours only `cols`, `total` and `missing` (dash_render.py:15478-15548) and names the rest:
  - `rows(1)`, `note("")`, `title("X")`, `yrescale`, `legend(off)` and `r(1)` have no effect.
  - `by(, title())` is stored but not drawn (JSE-46).

  dash.sthlp:1676-1679 documents this.
- **Closable:** partly -- a Bokeh `Legend` belongs to one figure, so a single `by()` legend must sit on one panel or on a legend-only figure; `compact`/`imargin`/`iscale` can only be approximated with borders and font scaling.
- **Plan:** 1. `rows(#)` sets cols = ceil(n/rows); `holes()` inserts `None` cells in `gridplot`; `colfirst` reorders the panels. 2. Draw `by(title/subtitle/note/caption)` once above or below the grid via `_dash_textbox`. 3. i*/noi* options set panel axis visibility (default: edge axes only); `yrescale`/`xrescale` unshare the ranges (see B4). 4. `by(, legend())` places the one common legend. 5. pytest in both modes; cscript comparing twoway's `.Graph.graphs[k]` layout and SVG.
- **Tracked:** Partly closed in WP-29 (P0.2, commit ab53f25): yrescale/xrescale are honoured; open: rows(), holes(), colfirst, compact, iscale(), imargin(), the i*/noi* axis options, noedgelabel, style(), and title()/subtitle()/note()/caption()/legend() inside by(); was: GAPS.md E3 (named remainder); dash.sthlp:1676-1679.

<a id="b17"></a>
### B17. `legend()`: Stata's abbreviations and most sub-options are named but not drawn

- **Gap:** `legend_options.sthlp:46-94` defines abbreviations (`c()`, `r()`, `lab()`, `pos()`...) and sub-options such as `holes()`, `colfirst`, `textfirst`, `stack`, key gaps, symbol sizes, `textwidth`, `region()`, `bplacement()`, `span`, legend titles and textbox options. `_DASH_LEGEND_SUBOPTS` (dash_render.py:18839-18841) holds only the full names on/off/position/pos/ring/order/label/cols/rows/size:
  - `legend(c(1))`, `r(1)`, `lab(1 "X")` and `posi(6)` are named and ignored.
  - `color()`, `holes()`, `colfirst`, `title()`, `region(fcolor())`, `bplacement()`, `textfirst` and `lastlabel()` are named and dropped.
- **Closable:** partly -- Bokeh's `Legend` has no text-before-symbol layout (`textfirst`), stacked key (`stack`), per-key symbol alignment (`symplacement`) or fixed text width (`textwidth`/`forcesize`); these can only be approximated.
- **Plan:**
  1. Match sub-options by Stata's minimum abbreviations, from a table transcribed from `legend_options.sthlp`.
  2. Map to Bokeh:
     - `title()`/`subtitle()` -> `Legend.title`
     - `region(...)` -> `background_fill_*`/`border_line_*`
     - `symxsize`/`symysize` -> glyph width/height
     - `keygap` -> `label_standoff`, `rowgap` -> `spacing`, `bmargin` -> `margin`
     - textbox `color()`/`size()` -> `label_text_*`
  3. `holes()` via placeholder items; `colfirst` by reordering items; `bplacement()` with `ring(0)` to the inside location.
  4. pytest in both modes; cscript measuring twoway's legend geometry and colours from SVG exports.
- **Tracked:** GAPS.md E3 (named remainder); abbreviations new.

<a id="b18"></a>
### B18. `plotregion()`/`graphregion()` sub-options, including Stata's abbreviations, are dropped with no note

- **Gap:** `region_options.sthlp` defines `color`/`fcolor`/`lcolor`/`lwidth`/`lpattern`/`lstyle`/`style`/`margin`, the inner i* options, and the abbreviations `c()`, `fc()`, `lc()`, `lw()`. dash.sthlp:504 says nothing is dropped silently. The `_extract_region_*` readers (dash_render.py:2785-2820) match only full names and report nothing. The following all change nothing, with no warning:
  - `plotregion(margin(zero))` and `graphregion(margin(l+10) lcolor(red) lwidth(thick))`
  - `plotregion(style(none))` and `graphregion(ifcolor(red))`
  - `plotregion(c(red))`, `graphregion(fc(red))`, `plotregion(lstyle(none))` and `plotregion(lc(red))`
- **Closable:** partly -- Bokeh has no border line around the whole canvas and no separate inner/outer graph region, so `graphregion` `lcolor`/`lwidth` and the i* options can only be approximated with CSS on the figure element.
- **Plan:** 1. Parse region sub-options with `_dash_by_tokens` and an abbreviation table. 2. Map `color`/`fcolor`/`lcolor`/`lwidth`/`lpattern` for both regions, `margin()` to `min_border_*` (Stata marginstyles in % of the graph), and `style(none)`/`lstyle(none)` to no fill or outline. 3. Name the rest through `_dash_report_suboptions`. 4. pytest in both modes; cscript comparing twoway's SVG.
- **Tracked:** GAPS.md E3 ("plotregion(), graphregion() ... still drop their sub-options in silence").

<a id="b19"></a>
### B19. `t1title()` .. `r2title()` are not drawn

- **Gap:** `title_options.sthlp` lists the t1/t2, b1/b2, l1/l2 and r1/r2 titles, with l/r drawn vertically. In dash they are on the pending list (dash.ado:769-790), named, and never drawn (dash.sthlp Unsupported, "Alternative titles"); the text is stored as typed (JSE-46).
- **Closable:** yes -- a Bokeh `Title` can go in any side panel and is drawn vertically on the left and right.
- **Plan:** 1. Add each as a `Title` in the above/below/left/right panel at its ring position, through `_dash_textbox` so sub-options work. 2. Take them off the pending lists and out of dash.sthlp Unsupported (test_unsupported_report_is_true.py and test_help_conformance.py enforce this). 3. pytest in both modes; cscript comparing twoway's SVG text positions and orientation.
- **Tracked:** GAPS.md E1 (deferred).

<a id="b20"></a>
### B20. `text()`/`ttext()` added text is not drawn

- **Gap:** `added_text_options.sthlp` defines `text(y x "text" ..., placement() yaxis() xaxis() ...)`, a common Stata annotation, and `ttext()` for time axes. In dash, `text()` is pending (dash.ado:789) and named, and the help suggests `note()`/`caption()` instead. `ttext()` is undeclared and gets the unknown-option note.
- **Closable:** yes -- Bokeh `Label`/`LabelSet` in data units can draw added text.
- **Plan:** 1. Parse the `y x "text" ["text"...]` groups and sub-options in dash.ado and write them as a list to the spec. 2. Draw them as `Label`/`LabelSet`:
   - `placement()` -> `text_align`/`text_baseline`
   - size/color/orientation/box through `_dash_textbox`
   - `yaxis/xaxis(2)` on the second ranges, and date values on date axes

   3. pytest in both modes, including escaping; cscript comparing twoway's SVG text positions.
- **Tracked:** GAPS.md E1 (deferred).

<a id="b21"></a>
### B21. `xlabel`/`ylabel`/`xtick` sub-options beyond `format`/`labsize`/`angle`/`grid` are not drawn (`valuelabel`, `nolabels`, colours, tick lengths...)

- **Gap:** `axis_label_options.sthlp` lists `valuelabel`, `[no]ticks`, `[no]labels`, `labcolor`, `labgap`, `labstyle`, the `labs()` abbreviation, tick length/position/colour/width/style, grid line styles, `gmin`/`gmax`, `gextend`, `alternate`, `norescale`, `custom` and `tstyle`. `_dash_parse_axis_spec` honours only `format`, `labsize`, `angle`, `grid` and `nogrid` (dash_render.py:16634-16637) and names the rest:
  - `xlabel(0 1, valuelabel)` draws 0 and 1, not Domestic/Foreign.
  - `labs(large)`, `nolabels`, `noticks`, `labcolor(red)`, `glcolor(red)` and `tlength(0)` are ignored.
- **Closable:** partly -- Bokeh styles every tick label on an axis alike, so `custom` (a different style per tick) cannot be exact, and `alternate` (staggered labels) can only be approximated with a formatter that adds a line break to every other label.
- **Plan:** 1. Accept the abbreviations (`labs`, `labc`, `val`, `tl`, `tp`, `glc`, `glw`, `glp`...). 2. Implement `valuelabel` from the data JSON's `valueLabels`: ticks at the coded values, text via `major_label_overrides`. 3. Map:
   - `nolabels`/`noticks`, `labcolor`
   - `labgap` -> `major_label_standoff`
   - `tlength`/`tposition` -> `major_tick_in`/`out`
   - tick and grid line colour/width/pattern, `gmin`/`gmax`

   4. pytest in both modes; cscript comparing twoway's SVG for each sub-option.
- **Tracked:** GAPS.md E3 (named remainder); REMAINING.md:2459.

<a id="b22"></a>
### B22. `xline()`/`yline()`: numlist forms, Stata's abbreviations, `axis(2)`, `lstyle`/`style`/`noextend` are not drawn

- **Gap:** In `added_line_options.sthlp`, the line position is a numlist, and the sub-options are `axis()`, `style()`, `[no]extend`, `lstyle()`, `lpattern()`, `lwidth()`, `lalign()` and `lcolor()`, with abbreviations. dash has `_DASH_REFLINE_SUBOPTS = {lcolor, lpattern, lwidth}` (dash_render.py:19069) and reads positions with `float()`:
  - `xline(3000, lc(red) lp(dash) lw(thick))` draws in the scheme default and names the three abbreviations.
  - `xline(2000(500)3000)` and `xline(2000/2002)` draw nothing (named).
  - `yline(5000, axis(2))` is drawn on the left axis's range.
  - `lstyle()` and `noextend` are named.
- **Closable:** yes.
- **Plan:** 1. Expand numlists in dash.ado with `numlist`, shared with the B1 fix. 2. Accept the abbreviations; map `lstyle`/`style` through the scheme's linestyle and addedlinestyle. 3. `axis(2)`: draw the `Span` with `y_range_name` 'y2'. 4. `noextend`: draw a `Segment` within the frame (an approximation, since a `Span` always spans the frame). 5. pytest in both modes; cscript comparing twoway's SVG line positions and styles.
- **Tracked:** Partly closed in WP-29 (P0.5, commit 3208b2b): yline(5000, axis(2)) is drawn on the second axis; open: numlist positions, the lc/lp/lw abbreviations, lstyle()/style() and noextend; was: GAPS.md E3 (named remainder).

<a id="b23"></a>
### B23. `xscale`/`yscale` sub-options other than `log`/`reverse`/`range` are not drawn

- **Gap:** `axis_scale_options.sthlp` defines `off`/`on`, `fill`, `alt`, `extend`/`fextend`/`noextend`, `noline`/`line`, `titlegap()`, `outergap()`, line style options, `axis(#)`, and the abbreviations `r()`/`rev`. dash has `_DASH_SCALE_SUBOPTS = {log, reverse, range}` (dash_render.py:18998):
  - `yscale(r(0 100))`, `off`, `noline`, `alt`, `lcolor(red)`, `titlegap(5)` and `rev` are named and ignored.
  - `yscale(log axis(2))` makes the LEFT axis log and leaves the right axis linear.
- **Closable:** partly -- `fill` (reserving space for a hidden axis) and `lalign` have no Bokeh counterpart and can only be approximated with `min_border`, and `extend`/`noextend` is approximate because a Bokeh axis always spans the frame.
- **Plan:** 1. Accept the abbreviations (`rev`, `r`, `noli`, `li`, `ex`, `noex`, `fex`, `titleg`, `outerg`, `lsty`, `lc`, `lw`, `lp`). 2. Map:
   - `off` -> `axis.visible=False`; `noline` -> `axis_line_color=None`
   - line colour/width/pattern -> `axis_line_*`
   - `titlegap` -> `axis_label_standoff`; `outergap` -> `min_border`
   - `alt` -> move the axis to the right or above

   3. Route `axis(2)` to `yscale2`/`xscale2`. 4. pytest in both modes; cscript comparing twoway's SVG.
- **Tracked:** GAPS.md E3 (named remainder); REMAINING.md:2447.

<a id="b24"></a>
### B24. `#N` ticks on %td-%th date axes follow a fitted model (about 60% agreement)

- **Gap:** dash.sthlp:2349-2356 says `#N` on a date axis follows twoway's time-series rule. The open BUGS.md entry (line 2523) records these misses:
  - dash agrees with `_tsnatscale` on only 52-66% of %td/%tw/%tm/%tq/%th ranges (98% of %ty).
  - There are three natscale misses on auto (strict xfails in test/test_natscale.py).

  `TestDateAxisTicks` in test/test_natscale_axes.py holds the agreement floors.
- **Closable:** partly -- `_tsnatscale` and `natscale` are compiled into Stata and undocumented, so dash can only approximate them from measured answers.
- **Plan:** 1. Measure structured sweeps per unit, varying span and N, into natscale_axes_truth.json. 2. Recover the calendar-step choice as a rule table rather than a fitted score. 3. Raise the floors in test_natscale_axes.py as agreement improves.
- **Tracked:** BUGS.md open: "#N ticks on a %td to %th date axis follow a fitted model...".

<a id="b25"></a>
### B25. Default axes are Bokeh's, not twoway's (tick positions, range padding, s2color vertical y labels)

- **Gap:** twoway's default axis uses natscale with about 5 ticks (scheme-s2color.scheme:290-292) and runs to the outermost tick, and s2color draws y tick labels vertically (scheme-s2color.scheme:1965). dash sets no default ticker: `_dash_count_ticker` is used only for an explicit `#N` (dash_render.py:16782). As a result:
  - Every axis keeps Bokeh's `BasicTicker` (6 ticks) and a `DataRange1d` with 10% padding. On auto's mpg, dash draws 15(5)40 where twoway draws 10(10)40 (BUGS.md `ylabel(#5, grid)` entry).
  - `anglestyle vertical_tick` has no consumer, so y labels are horizontal.
- **Closable:** yes.
- **Plan:** 1. Port `_dash_natscale_ticks` (and the date-unit rule) to a `CustomJSTicker` on every axis without `xlabel()`/`ylabel()`, so the initial view matches twoway and zoom/pan still re-ticks (a `FixedTicker`, as the `#N` path uses at dash_render.py:17281-17291, would not). 2. Set the initial `Range1d` to the hull of the data and the outermost default ticks, with no 10% padding. 3. Transcribe `anglestyle vertical_tick`/`horizontal_tick` into the shipped schemes via scripts/extract_scheme_truth.py and apply them to tick-label orientation. 4. Update the tests that pin Bokeh's defaults; assert against test/fixtures/natscale_truth.json plus new default-axis cases measured from twoway SVG exports, and a headless check that zooming still shows ticks.
- **Tracked:** new.

<a id="b26"></a>
### B26. Legend placement differs from twoway's (explicit position, corners, `pos(0)`, `by()` graphs)

- **Gap:** dash.sthlp:2284-2287 places the legend by clock position. In twoway the scheme's `legend_cols` applies at any position (s2color: 2), clock 1/5/7/11 are corners, `position(0) ring(0)` is the centre of the plot, and a `by()` graph gets one legend. dash differs on each point:
  - Scheme cols/rows are applied only when no `position()` is given (dash_render.py:15876-15906), so `legend(pos(6))` puts every key in one row.
  - `_dash_move_legend` always sets `location='center'` (15780), so corner positions are centred on a side.
  - `pos(0) ring(0)` goes to the top right.
  - Each `by()` panel carries its own legend.
- **Closable:** yes.
- **Plan:** 1. Keep the scheme's `legend_cols`/`rows` when `position()` is given without `cols()`/`rows()`. 2. Set the side-panel location from the clock: 11/1 at the ends of 'above', 7/5 at the ends of 'below', 2/4 and 8/10 at the ends of the sides; `pos(0) ring(0)` -> 'center'. 3. For `by()` graphs, draw the legend once (on the last panel or a legend-only figure) and read `by(, legend())`. 4. pytest per clock position in both modes; cscript comparing legend bounding boxes from twoway SVG exports for pos 0-12, ring 0/1, with and without `by()`.
- **Tracked:** new.

<a id="b27"></a>
### B27. Marker-label remainders: `headlabel`, pc* first-point labels, `mlabvposition`, `mlabtextstyle`, extended missing, value-labelled dates

- **Gap:** `marker_label_options.sthlp` defines `mlabvposition(varname)`, `mlabtextstyle()` and `headlabel` on pc* types. twoway also labels the first point when only the second is missing, draws `.a`-`.z` as their value label or name, and uses a date variable's value labels. dash differs on each, all documented in dash.sthlp:1747-1778:
  - `headlabel` is named; `mlabvposition`/`mlabtextstyle` are pending (dash.ado:1049-1050).
  - A pc* row with any missing coordinate is dropped.
  - Extended missing values are drawn as `.`.
  - A date variable's value label is ignored.
- **Closable:** yes -- dash.ado can pass a decoded string column.
- **Plan:** 1. `mlabvposition`: a per-row clock column mapped to per-row `text_align`/`text_baseline` and offsets in the `LabelSet`. 2. `headlabel`: label the (y2,x2) point. 3. pc*: keep the first point and its label when only the second is missing. 4. dash.ado passes a decoded string column for an mlabel variable holding extended missing values or value-labelled dates. 5. cscript comparing twoway's SVG labels for each case.
- **Tracked:** dash.sthlp:1747-1778 (documented); GAPS.md E1 (`mlabvposition`, `mlabtextstyle`).

<a id="b28"></a>
### B28. Options twoway refuses (`title2`, `subtitle2`, `mlabwidth`, `ciopts`, `blabel`, `at`, `xreverse`...) and unknown lower-case words are noted instead of refused

- **Gap:** twoway refuses `title2`, `subtitle2`, `mlabwidth`, `ciopts`, `blabel`, `at`, `xreverse` and unknown lower-case words with r(198); dash.sthlp Unsupported and 3096-3115 list them. dash names them in its note and draws the graph (the TP-07 rule), so a typo like `titel(x)` runs. The open BUGS.md entry (line 2595) also records dash naming a different first word than twoway in some mixed option lists.
- **Closable:** yes.
- **Plan:** 1. Revisit the TP-07 rule in light of twoway's refusal: refuse undeclared lower-case words with "option X not allowed", r(198), and keep the note only for twoway options dash does not draw. 2. Order the refusals the way twoway's parser meets them. 3. Update TP-07 in test_twoway_option_parity.cscript, and the help. 4. Measure each word against live twoway in the cscript.
- **Tracked:** BUGS.md open: "In a few mixed lists dash names another word than twoway names first...".

**B29. Title and subtitle are left-aligned; textbox `position()`/`ring()`/`span`/`justification()` are not drawn** -- same gap as D17; see there.

<a id="b30"></a>
### B30. `aspectratio()` shapes the whole figure, not the plot region, and gives way to `xsize`/`ysize`

- **Gap:** In `aspect_option.sthlp`, `aspectratio(#[, placement()])` constrains the plot region and applies together with `xsize()`/`ysize()`. test_graph_options.py:152-156 records Stata's `aspectratio(0.25)` region as 542x152, and dash.sthlp:2278-2280 promises "a square plot". `_dash_figure_aspect` (dash_render.py:12442-12488) differs in three ways:
  - It sets Bokeh's figure `aspect_ratio`, which covers the whole canvas, including titles, legend and axes.
  - It uses the `xsize`/`ysize` ratio first and silently drops `aspectratio` when both are given (this precedence is documented in dash.sthlp:2533-2545).
  - It refuses `placement()` as not a number.
- **Closable:** partly -- under responsive (`stretch_width`) sizing, Bokeh constrains only the outer canvas ratio and panel sizes are known only after BokehJS layout, so an exact plot-region ratio needs a resize callback or a fixed `frame_width`/`frame_height`. Absolute inches conflict with the responsive page by design.
- **Plan:** 1. Read the `placement()` sub-option. 2. Apply `xsize`/`ysize` to the canvas and `aspectratio` to the frame, via a `CustomJS` callback on `inner_width` that sets height = inner_width*ratio + (outer minus inner panel heights). 3. Measure frame dimensions in a headless browser test. 4. Compare against twoway's SVG plot-region rectangles for 10 ratios.
- **Tracked:** new (precedence and band documented in dash.sthlp:2533-2560).

<a id="b31"></a>
### B31. `by()` graph chrome differs from twoway's (panel labels, default note, repeated axes, missing-panel text)

- **Gap:** In `by_option.sthlp:462-515`, twoway labels each panel with its subtitle (so `subtitle("")` removes the label and `subtitle(, ring(0) pos(1))` moves it). It also adds a "Graphs by <var>" note, draws axis labels and titles on the outer edges only, titles the missing panel "(missing)", and joins several `by()` variables with ", ". dash differs:
  - The panel label is appended to the figure title as "T — 0" (dash_render.py:23306-23307), so `subtitle()` cannot reach it.
  - There is no "Graphs by" note.
  - Every panel repeats both axes, both axis titles and the legend.
  - The missing panel reads "Missing" and joined labels read "Domestic / 3" (documented, dash.sthlp:1654-1673).
- **Closable:** yes.
- **Plan:** 1. Draw the panel label as the panel's subtitle (a `Title` in the scheme's by-subtitle style), honouring `subtitle()`'s text, suffix and position. 2. Add the "Graphs by <label>" note, suppressible with `by(, note(""))`. 3. Hide inner axes and titles by default. 4. Use "(missing)" and ", ". 5. pytest in both modes; cscript comparing twoway's SVG text.
- **Tracked:** new (documented in part in dash.sthlp:1654-1673).

<a id="b33"></a>
### B33. `scale()`, `fxsize()`, `fysize()`, `xoverhangs` and `yoverhangs` are not applied

- **Gap:** `scale_option.sthlp` defines `scale(#)` to multiply text, marker and line sizes. `region_options.sthlp` defines `fxsize()`/`fysize()`, and `advanced_options.sthlp` defines `xoverhangs`/`yoverhangs`. In dash all five are on the graph pending list (dash.ado:760-790) and named; dash.sthlp Unsupported explains the choice.
- **Closable:** partly -- `fxsize`/`fysize` size a panel for `graph combine`, which dash's layout does not model, so they can only shrink the figure within its cell. Bokeh already sizes borders to fit tick labels, so the overhang options may have nothing left to do.
- **Plan:** 1. `scale(#)`: multiply every resolved text size, marker size and line width in the figure build. 2. `fxsize`/`fysize`: set the figure's max width/height as a percentage of its cell. 3. Check in a browser whether end labels can clip; if they cannot, document the overhang options as no-ops and stop naming them. 4. pytest, and a cscript comparing twoway's SVG sizes under `scale(1.5)`.
- **Tracked:** GAPS.md E1 (deferred).

## C. Statistical fidelity

The statistical layers should draw what twoway draws, with the same estimator, defaults, sub-options and weights, at any sample size, and should redraw when a filter moves. Most of this is delivered. lfit, qfit, lfitci and qfitci (with stdp, stdf or stdr, and with aw or fw weights), fpfit, fpfitci, lowess, lpoly at an explicit `bwidth()`, mspline, mband, kdensity and histogram all match Stata's recorded plot data (stat_truth.json has 52 sections, and all 815 statistical tests pass). Two gaps are S1: histogram silently drops the top observation on some bin grids, and the default lpoly bandwidth ignores `kernel()` and `degree()`. Also missing: `function` draws nothing for most Stata functions, the lpolyci band is a bootstrap, the saved page never redraws fitted lines when a filter moves, lowess and lpolyci recomputes block a served page at large N, several options that change the estimate are ignored, and the rest is option bounds, legend keys, missing Stata ground truth and two open S3 bugs.

| ID | Gap | Sev | Closable | Effort |
|---|---|---|---|---|
| C1 | Default lpoly/lpolyci bandwidth ignores `kernel()` and `degree()` | S1 | see A9 | - |
| C2 | histogram silently drops the maximum observation when the last computed edge falls a few ULPs below it | S1 | yes | S |
| C3 | Options that change the estimate are named in the note and then ignored | S2 | see A4 | - |
| C4 | Saved page never redraws fitted or smoothed lines on a filter move, and shows no cue that they are stale | S2 | partly | L |
| C5 | `function` evaluates only ten Python functions, and `x^y^z` is evaluated right to left | S2 | see A6 | - |
| C7 | lpolyci band is a bootstrap percentile band, not Stata's analytic band | S2 | partly | M |
| C8 | Constant-x lowess and constant kdensity print a "drew nothing" note where twoway is silent | S3 | see A11 | - |
| C9 | Drawing options of statistical plot types are not honoured, and several are missing from the help | S3 | see A4 | - |
| C10 | Smoother and histogram legend keys do not match Stata's | S3 | see A13 | - |
| C11 | Option values twoway accepts that dash refuses or reads differently | S3 | see A15 | - |
| C12 | Parts of the weighted and kernel options have no Stata ground truth | S3 | yes | M |
| C13 | Default epanechnikov degree 0/1 lpoly bandwidth approximates Stata's, and misses badly on small samples | S3 | see A9 | - |
| C14 | histogram puts a value that sits exactly on an interior bin edge in a different bar than Stata | S3 | yes | S |
| C15 | `kernel()` on a plot type with no kernel is written to the spec with no note | S3 | see A12 | - |

**C1. The default lpoly/lpolyci bandwidth ignores kernel() and degree(); Stata's scales with the kernel and uses a different estimator for degrees 2 and 3** -- same gap as A9; see there.

<a id="c2"></a>
### C2. histogram silently drops the maximum observation when the computed last bin edge falls a few units in the last place below the data's maximum

- **Gap:** Stata counts every observation as `floor((v - min)/h)`, folding 0 and `bin` into the first and last bars (twoway__histogram_gen.ado:198-200). dash.sthlp's histogram paragraph promises the same. dash's continuous branch builds its edges as `start + width*arange(n+1)` (dash_render.py:9750-9766) and counts with `np.histogram` (dash_render.py:9577) and a JavaScript recount (dash_render.py:14817-14824). Both drop any value above the last edge. On nlsw88 ttl_exp, `bin(27|51|54|83)` counts 2245 of 2246 rows, census pop `bin(75)` counts 49 of 50, and about 4% of random rounded layers lose a row. No note is printed, and density bars are rescaled to the rows that remain. A `start()` above the minimum but within reldif 1e-5 of it passes dash.ado:3832, and the rows below it are then dropped. Stata counts them in bar 0.
- **Closable:** yes. The discrete branch already uses Stata's rule (dash_render.py:9565-9575).
- **Plan:** 1. In `GlyphMapper.map_histogram`, count the continuous branch as `idx = floor((v - start)/h)`, clamp it to 0 and `bin-1`, then call `np.bincount`. Set the last edge to `start + h*bin` and remove the tolerance-based extra edge. 2. Apply the same rule in the `_FILTER_JS` recount (dash_render.py:14800-14824); the served app follows. 3. Add a property test (random data, `bin` 1..100, `width()`, `start()` just above the minimum) checking that frequency bars sum to N in the saved page, in the served app, and in the JavaScript run under node. Add regressions for nlsw88 ttl_exp `bin(27)` and census pop `bin(75)`. 4. Add twoway__histogram_gen `generate()` output for these cases to scripts/extract_stat_truth.do and pin it in test_statistical_truth.py.
- **Tracked:** Closed in WP-28, BUGS.md "A continuous histogram dropped the observation at its last edge, and the rows a tolerated start() lies above", commit b06b662; was: new. The discrete case was fixed in BUGS.md "histogram, discrete dropped the values past its last edge". The `start()` case is a residual of BUGS.md "A histogram start() above the variable's minimum was accepted and the rows below it silently dropped".

**C3. Options that change the estimate are named in the note and ignored: estopts(), predopts(), estcmd(), atobs, kdensity area() and boundary, lpolyci pwidth() and var()** -- same gap as A4; see there.

<a id="c4"></a>
### C4. The saved (offline) page never redraws fitted or smoothed lines when a filter moves, keeps histogram bins and the kdensity grid as built, and shows no cue that they are stale (also reported as E4)

- **Gap:** dash.sthlp's Description promises an interactive page that works "in any modern browser -- no server". In Stata, `histogram x if <filter>` re-derives its bins from the subset. On the saved page only histogram and kdensity carry `_dash_agg_config` (dash_render.py:9607, 9882), and they keep their build-time bins and grid. lfit, qfit, lfitci, qfitci, fpfit, fpfitci, lowess, lpoly, lpolyci, mband and mspline stay as fitted to every row (dash.sthlp:1314, 1327-1337). There is no build-time warning and no in-page cue, so the page shows filtered points under a fit that includes the rows the filter removed.
- **Closable:** partly. Every estimator can be ported to JavaScript, but a serverless page pays the full compute cost in the browser (seconds per filter move for lowess or dense lpoly grids at N≈1e5). A Web Worker keeps the page responsive without cutting that cost, so above a size threshold the page must show a cue instead of recomputing.
- **Plan:** 1. Port each estimator to `_FILTER_JS`, mirroring its Python mapper:
  - weighted least squares with stdp/stdf/stdr and a t quantile (port `_t_ppf`)
  - cross medians plus the natural spline
  - the lowess window loop and the lpoly grid loop
  - the screened 36-pair FP search
  - histogram rebinning from the kept rows' min and max, and the kdensity grid over their range

  2. Tag every computed renderer with `_dash_agg_config`/`_dash_agg_rows` so the filter callback re-estimates it. Use a Web Worker when N × window exceeds a threshold. 3. Above a size ceiling, or for an unported type, show a cue while a filter is active (dim the layer and add a legend suffix such as "all rows"), and print a build-time note. 4. Test the JavaScript under node against the Python mappers on the four fixture datasets and filtered subsets (as `TestFilterJavaScript` does, test_statistical_helpers.py:860), and against the Stata fixtures on subsets (qualified_stat_truth.json). Add a test that the cue appears for an unported type.
- **Tracked:** Partly closed in WP-29 (P0.17, commit b242b99): a frozen fit, smooth or density on the saved page shows a visible stale cue after a move that removed a row of its estimation sample, cleared when the move is undone; open by decision (WP-29 M3, DISCOVERY Q3): the saved page does not re-estimate them, and nothing is ported to _FILTER_JS; no build-time note is printed (DISCOVERY Q22); was: Deferred (WP-28): out of scope by decision (DISCOVERY Q3), with its duplicate E4; nothing is ported to _FILTER_JS on its account; was: new. dash.sthlp Server Mode documents it ("does not redraw a fitted line"); it is not in BUGS.md or GAPS.md.

**C5. function evaluates only ten Python functions: normalden(), normal(), ln(), _pi, comparisons, cond(), min(), max() and scalars draw nothing, and x^y^z is evaluated right to left** -- same gap as A6; see there.

<a id="c7"></a>
### C7. lpolyci's band is a bootstrap percentile band, not Stata's analytic band; pwidth() and var() are ignored, and the bootstrap costs 200 times the smooth (also reported as A10)

- **Gap:** twoway lpolyci draws m(x0) ± z·σ_m(x0) with the sandwich variance. σ²(x0) comes from a degree p+2 local fit at the pilot bandwidth `pwidth()` (default 1.5 × the rule-of-thumb bandwidth), or from `var()` ([R] lpoly Methods and formulas, eq. 4). Instead, `map_lpolyci` (dash_render.py:8932-9048) calls `_bootstrap_ci` (dash_render.py:5932), which works as follows:
  - It draws 200 resamples, with seed 42 or the layer's `jitterseed()`.
  - It fills missing predictions with the point estimate, which narrows the band where data are sparse.
  - Each resample derives its own rule-of-thumb bandwidth, where Stata fixes one.

  `pwidth()` and `var()` are ignored (dash.sthlp:1808, 2075). No fixture holds a Stata lpolyci band. At N=20000 it takes 6.5 s, against 0.24 s for lpoly.
- **Closable:** partly. The build-time draw can be exact, because dash.ado can take the band, `r(bwidth)` and `r(pwidth)` from Stata's own lpoly. A served filter move runs without Stata, though, so its default pilot bandwidth (computed in compiled Mata `_lpoly_work`) and eq. 4's σ² normalization can only be approximated. A served band is exact only when both `bwidth()` and `pwidth()` (or `var()`) are given.
- **Plan:** 1. In dash.ado, for each lpolyci layer (each `by()` panel, over the plot's sample and weights), run `lpoly y x [w] if <sample>, degree() kernel() bwidth() pwidth() var() n(#) generate(gx gy) se(gse) nograph`. Write gx, gy ± `invnormal((100+level)/200)*gse`, `r(bwidth)` and `r(pwidth)` into the spec, and have the renderer draw them. 2. For served recomputes, add `_lpoly_se(x, y, w, grid, h, pilot, degree, kernel, var)` implementing eq. 4, and reuse the build-time h and h* when the filter keeps every row. Fit the normalization to Stata output from extract_stat_truth.do (four datasets, degree 0/1/2, several kernels, with and without aw/fw). 3. Remove `_bootstrap_ci` from `map_lpolyci`, honour `pwidth()`/`var()`, take them off dash.sthlp's ignored list, and refuse `level()` outside 10-99.99. 4. Add `TestLpolyciAgainstStata`: about 1e-6 with explicit bandwidths and at build time, and within the rule-of-thumb tolerance for served defaults. Add a cost test holding lpolyci under 3× lpoly.
- **Tracked:** GAPS.md A4; ROADMAP.md WP-18 follow-up; BUGS.md:1237 ("The band is still a bootstrap"); documented at dash.sthlp:2075.

**C8. A constant-x lowess and a constant kdensity print dash's 'drew nothing' note, where twoway draws in silence** -- same gap as A11; see there.

**C9. Drawing options of the statistical plot types are not honoured, and several are missing from the help's list of unsupported options** -- same gap as A4; see there.

**C10. Legend keys of the smoothers and histogram do not match Stata's: mband, lowess, lpoly, mspline and function are keyed 'Fitted values', and histogram and kdensity by the variable's label** -- same gap as A13; see there.

**C11. Option values twoway accepts that dash refuses or reads differently** -- same gap as A15; see there.

<a id="c12"></a>
### C12. Parts of the weighted and kernel options have no Stata ground truth

- **Gap:** CLAUDE.md rule 4 and the project convention call for every estimator to be pinned to Stata's recorded plot data. stat_truth.json's weighted section covers only `[aw=]` and `[fw=]` for lfit, lfitci, qfit, fpfit, lpoly, lowess, kdensity and histogram. pweight bands are pinned only at the first and last grid rows, on auto only (test_help_claims_6.py:880-918). The following are unmeasured:
  - aw/fw qfitci, fpfitci and lpolyci bands
  - stdf/stdr with `[fw=]`
  - six of the eight kernels, which are checked only against formulas test_kernel_flags.py writes itself (value_truth.json holds only their return codes)
  - the lpoly default bandwidth for degree 2/3 and for kernels other than epanechnikov and gaussian
- **Closable:** yes. Every item can be measured by extending the extraction script.
- **Plan:** 1. Extend scripts/extract_stat_truth.do with:
  - `[pw=]` lfitci, qfitci and fpfitci at every grid point on the four datasets
  - aw/fw qfitci, fpfitci and lpolyci bands
  - stdf/stdr with `[fw=]`
  - kdensity and lpoly at an explicit `bwidth()` for all 8 kernels
  - lpoly `r(bwidth)` for 8 kernels × degree 0-3

  2. Add `TestPweightBands`, `TestKernelsAgainstStata` and `TestLpolyDefaultBandwidth` to test_statistical_truth.py, in both modes. 3. Record anything still unmeasurable in stat_truth.json's unverified section.
- **Tracked:** Partly closed in WP-29 (P0.7, commit 758cf59; P0.9, commit e32be3a): the lpoly default bandwidth for degree 2/3 and every kernel, and the aw/fw lpolyci bands; open: aw/fw qfitci and fpfitci bands, stdf/stdr with [fw=], and six of the eight kernels against Stata; was: new.

**C13. The default lpoly/lpolyci bandwidth for epanechnikov at degree 0/1 approximates Stata's rule of thumb, and misses badly on small samples** -- same gap as A9; see there.

<a id="c14"></a>
### C14. histogram puts a value that sits exactly on an interior bin edge in a different bar than Stata

- **Gap:** Stata assigns bars by `floor((v - min)/h)` in double precision (twoway__histogram_gen.ado:198), as dash's discrete histogram and mband already do. dash's continuous branch instead compares values against an edge array (`np.histogram`, dash_render.py:9577; the JavaScript loop at 14817-14824), so a value on an interior edge can land one bar off. 45 of 4795 random rounded datasets (0.9%) with `bin(2..39)` differ. For example, 21 values in {0.1..1.0} with `bin(27)` put the four 0.3 values in bar 5 instead of bar 6. This was compared with the ado's rule, not yet with Stata output.
- **Closable:** yes. The C2 fix closes it too.
- **Plan:** 1. Use C2's floor-and-clamp counter in `map_histogram`, the served copy and the JavaScript recount. 2. Add a fixture section of values on edges, read from twoway histogram's serset: x = 0(.1)1 with `bin(10)`, 200 values rounded to hundredths with `bin(20)`, the 21-value example with `bin(27)`, and nlsw88 ttl_exp with `bin(27)`. 3. Compare bar by bar in test_statistical_truth.py, and run the JavaScript twin under node as `TestFilterJavaScript` does (test_statistical_helpers.py:860).
- **Tracked:** new.

**C15. kernel() on a plot type that has no kernel is written to the spec with no note** -- same gap as A12; see there.

## D. Schemes and visual fidelity

dash says a dashboard "has the look" of the session's scheme. To do that it ships 20 translated StataCorp schemes, reads a user's `.scheme` file, and honours twoway's marker, line, colour and text options on Stata's size scale (dash.sthlp: scheme, markers, region_options). These are delivered and pinned by tests: colours, grids on or off, text sizes and colours, legend placement, CI bands, `xyline` and the plot-region border. Much else is not. Option sizes are read as pixels or taken from a private ladder, and quoted RGB values in user and third-party schemes are dropped without a warning. The colour, symbol, line-pattern and text-markup grammars are only partly supported, and several directives that shape Stata's default look are not carried. The visual truth fixture covers 4 of the 20 schemes, and only at the parser level.

| ID | Gap | Sev | Closable | Effort |
|---|---|---|---|---|
| D1 | A user or third-party scheme's quoted values (RGB colours, %opacity) are dropped without a warning | S1 | yes | S |
| D2 | Size options are read on a private pixel ladder: numbers as pixels, keywords off the scheme's scale, and Stata's units refused | S1 | yes | M |
| D3 | Graph-text markup: SMCL tags are drawn literally, while TeX delimiters are typeset as maths | S2 | partly | M |
| D4 | Line patterns: Stata's formula grammar is refused, mlpattern() is ignored, and dot geometry is off | S2 | yes | S |
| D5 | Marker symbols: arrow/arrowf/\| refused, pipe/point/V/sm* misdrawn, and scheme hollow and small symbols drawn filled at full size | S2 | partly | M |
| D6 | Named styles pstyle()/mstyle()/lstyle()/mlstyle() are not honoured, although dash already resolves every p# chain | S2 | see B11 | - |
| D7 | Stata colour forms beyond names, RGB and hex are refused: intensity *#, CMYK, HSV, bg/fg | S2 | yes | M |
| D8 | Style lists (msymbol(O D), mcolor(red blue), lpattern(solid dash)) are not split across y variables | S2 | yes | M |
| D9 | Tick-label angle() drops Stata's anglestyle names other than horizontal/vertical without a note | S2 | yes | S |
| D10 | A user scheme's directives that dash does not read are ignored without a word | S3 | yes | M |
| D11 | Markers are drawn at 80% opacity where Stata draws them opaque, and intensity is treated as alpha | S3 | yes | S |
| D12 | Scheme axis/grid directives are not carried: y tick-label rotation, dashed grid lines, tick colours | S3 | yes | M |
| D14 | Text and marker sizes are fixed at a 4-inch reference and do not scale with the figure; scale() is ignored | S3 | partly | L |
| D16 | Tick geometry and axis furniture are Bokeh's: minor ticks, inward tick stubs, economist's axis, legend key size | S3 | yes | M |
| D17 | Titles are bold and left-aligned, axis titles italic, and title/note positions ignore the scheme | S3 | yes | S |
| D18 | sttrans's %20 opacity reaches only some layer types | S3 | yes | S |
| D19 | twoway histogram ignores the scheme's histogram style (fill, outline, intensity, width) | S3 | yes | S |

<a id="d1"></a>
### D1. A user or third-party scheme's quoted values (RGB colours, %opacity) are dropped without a warning

- **Gap:** dash.sthlp:2813 tells users to copy another package's scheme into the working directory. Stata's colorstyle help recommends quoting `"R G B"`, and Stata's own sttrans scheme writes `color p1 "26 71 111 %20"`. `SchemeParser._parse_lines` (dash_render.py:3988-3993) takes `tokens[-1]` as the value, so `color background "255 0 0"` is stored under a malformed key and the directive is lost without a warning. In a probe, a copied `scheme-d3colors.scheme` drew every series #606060 with 0 warnings; 127 of the 129 local third-party schemes use quoted RGB.
- **Closable:** yes.
- **Plan:**
  1. Tokenise scheme lines as Stata does (category, key, then a value that may be quoted and carry ` %NN`), and strip the quotes.
  2. Accept `"R G B"`, `"R G B %NN"`, CMYK, `"hsv h s v"` and `colour*#` (shared with D7).
  3. Warn once for each directive line whose value cannot be read, naming the line, and never store a malformed key.
  4. Test that all 129 local third-party files parse with no malformed keys, and pin d3colors p1-p15 to the file's RGB values.
  5. Compare with Stata's SVG export of a scatter under the copied d3colors scheme.
- **Tracked:** Closed in WP-28, BUGS.md "A scheme's quoted values (RGB colours, %opacity) were dropped without a warning", commit 57590b9; residual deferred (WP-28): CMYK, hsv and colour*# scheme values are D7's (GAPS2 D7), not read here; third-party scheme files excluded by decision (DISCOVERY Q30); was: ROADMAP.md WP-16 notes (:2040, where the RGB misread was recorded and left unfixed for WP-17); otherwise new.

<a id="d2"></a>
### D2. Size options are read on a private pixel ladder: numbers as pixels, keywords off the scheme's scale, and Stata's units refused (also reported as B9)

- **Gap:** dash.sthlp:2773-2790 promises sizes "on Stata's own scale". Stata's size.sthlp makes a bare `#` a relative size (100 = min(width, height)) and allows `#pt`/`#in`/`#cm`/`#rs`/`*#`. dash reads numbers as pixels (`translate_msize`, dash_render.py:3279, returns `int(#)` px; `translate_lwidth`, :3315, passes numbers through) and takes keywords from a private `_SIZE_MAP` (`msize(medium)` gives 11 px against a default marker of 8 px). Probes: `msize(1.52778)` draws 1 px; `lwidth(.3)` draws 0.3 px against a 1.5 px default; `title(,size(large))` gives 15px, smaller than the 14pt default; units, `*#` and `vhuge` are refused. The `_LWIDTH_MAP` keyword ratios are not Stata's.
- **Closable:** yes.
- **Plan:**
  1. Add one option-size resolver next to `SchemeParser._gsize`/`_markersize_px`/`_lwidth`:
     - a keyword uses the ladder for its object: gsize for text, symbolsize for markers, linewidth for lines;
     - a number is in relative units;
     - `#pt`/`#in`/`#cm`/`#rs` are converted;
     - `*#` multiplies the scheme default.
  2. Route `translate_msize`, `translate_lwidth`, `_textbox_size`, `labsize`, `mlabsize`, `mlabgap` and `legend(size())` through it in both modes.
  3. Replace the `_LWIDTH_MAP` ratios with Stata's, keeping medium = 1.5 px as the anchor and adding vvvthin.
  4. Restate the px pins in test/test_options.py (:158, :190). Add a property test that an explicit keyword equals the scheme default of the same name.
  5. Compare size ratios with Stata's SVG export, as truth.json does, for `msize(1.52778)`, `msize(4pt)`, `lwidth(.3)`, `lwidth(1pt)`, `title(,size(12pt))` and `labsize(5)`.
- **Tracked:** GAPS.md G5 follow-up and ROADMAP.md:2048 (the `_LWIDTH_MAP` ratios only); the rest is new.

<a id="d3"></a>
### D3. Graph-text markup: SMCL tags are drawn literally, while TeX delimiters are typeset as maths (also reported as B13, J2, J5)

- **Gap:** Stata's graph_text.sthlp says all graph text supports `{bf:}`, `{it:}`, `{sup:}`, `{sub:}`, font tags, `{&alpha}` symbols and `{c #}`, and Stata draws `$$`, `\(` and `\[` as literal text. dash translates no SMCL: `title("{bf:Bold} {&alpha} R{sup:2}")` reaches `Title.text` unchanged. BokehJS 3.8 typesets `$$..$$`, `\[..\]` and `\(..\)` as TeX in titles, labels and axis labels, and `_dash_inert_tex` (dash_render.py:17456) breaks the delimiters only in widget titles.
- **Closable:** partly. Bokeh canvas text draws one font face and style per text object, so inline mixed bold, italic, superscript or subscript needs TeX through MathJax inlined in the offline page (~1.8 MB, drawn in MathJax's font). `{fontface "X"}` depends on the fonts installed on the viewer's machine.
- **Plan:**
  1. Add `_dash_graph_text()` and use it at every text sink in both modes:
     - `{&name}` and `{c #}` become Unicode;
     - a `{bf:}`/`{it:}` that wraps the whole string sets `text_font_style`;
     - font-family tags are stripped.
  2. Convert inline `{sup:}`/`{sub:}`/`{bf:}`/`{it:}` to TeX where MathJax is acceptable. Otherwise strip the tags and say so in a note.
  3. Break TeX delimiters (the word-joiner trick) in all other text.
  4. Test each sink and mode, including hostile tags. Compare with the text runs and font-weight in Stata's SVG.
- **Tracked:** new.

<a id="d4"></a>
### D4. Line patterns: Stata's formula grammar is refused, mlpattern() is ignored, and dot geometry is off

- **Gap:**
  - Stata's linepatternstyle.sthlp allows formula patterns built from `l _ - . #` (`"-."`, `"--.."`). Its linepattern-*.style files set relative on/off lengths (dot `.1 .7`, dash `2 1`), and `mlpattern()` is a twoway option.
  - `translate_lpattern` (dash_render.py:3344) accepts only the fixed pixel arrays in `_LPATTERN_MAP` (:3085). `lpattern(-.)`, `(--..)`, `(#)` and a scheme's `linepattern p1 "-."` are drawn solid with a note or warning. dash's dot is [2,4] px (1:2 against Stata's .1:.7), and `mlpattern()` is named in a note and drawn solid (dash.ado:1052).
  - Whether Stata scales pattern lengths with line width has not been measured.
- **Closable:** yes.
- **Plan:**
  1. Parse a formula (quotes stripped) into a dash list, using Stata's element lengths measured from its SVG export, where dashed lines are drawn as separate `<line>` segments.
  2. Derive the named patterns from the linepattern-*.style values on dash's relative-unit px scale. Measure at `lwidth(medium)` and `lwidth(vthick)` whether Stata scales lengths with line width, and apply that only if it does.
  3. Apply `mlpattern()` as the marker's `line_dash`, and remove it from the unsupported list and the help.
  4. Test formula parsing, a scheme's `linepattern p1 "-."` and `mlpattern()` in both modes against the measured segment lengths.
- **Tracked:** `mlpattern()`: GAPS.md E1 (deferred by WP-27); the formula grammar is new.

<a id="d5"></a>
### D5. Marker symbols: arrow/arrowf/| refused, pipe/point/V/sm* misdrawn, and scheme hollow and small symbols drawn filled at full size

- **Gap:**
  - Stata's symbolstyle.sthlp defines arrow/arrowf/pipe/V as line glyphs, point as a small dot, sm* as `msize(small)`, and hollow symbols as unfilled. dash.sthlp:2705 says the scheme's p1-p15 symbol cycle is consumed.
  - `_MARKER_MAP` (dash_render.py:2986-3040) refuses A/a/arrow/arrowf/|. It draws pipe as a horizontal bar, point and every sm* at 8 px, and V filled. It accepts star/asterisk/hexagon/dot, which twoway refuses.
  - The hollow flag comes only from `msymbol()` (:6219-6223), never from `p_symbols` (:4489). So s1mono's hollow p7-p10 are drawn filled and its sm* p11-p15 at full size; nine shipped schemes are affected.
- **Closable:** partly. Bokeh 3.8's `Scatter.defs` custom Path2D markers can draw arrow, arrowf, V and a vertical pipe exactly, but only on the canvas and SVG backends. Figures above 10,000 rows switch to WebGL (`_WEBGL_THRESHOLD`, dash_render.py:1986), and `defs` support in Bokeh 3.0 (accepted by dash_setup.ado:146) is unmeasured, so those figures get the nearest built-in shapes.
- **Plan:**
  1. Have `translate_msymbol` return shape, hollow flag, size factor and angle:
     - sm* size factor 1.04166/1.52778;
     - point: `dot` or a vtiny circle;
     - pipe: `dash` at π/2.
     Refuse star/asterisk/hexagon/dot as twoway does.
  2. Add `@arrow`, `@arrowf` and `@V` through `Scatter.defs`, as fixed CustomJS Path2D constants with no user text, for canvas and SVG figures in both modes. Fall back to the nearest built-in shape elsewhere, with one note.
  3. Have `SchemeParser` keep the hollow flag and size factor for each p#, and have every marker mapper apply `fill_alpha` 0 and the factor.
  4. Test p1-p15 under the nine mono schemes, every symbolstyle name, and a custom-marker figure in test/responsive_probe.py.
  5. Set the size factors and glyph geometry from a Stata SVG of each symbol, measured as truth.json measures markers.
- **Tracked:** new.

**D6. Named styles pstyle()/mstyle()/lstyle()/mlstyle() are not honoured, although dash already resolves every p# chain** -- same gap as B11; see there.

<a id="d7"></a>
### D7. Stata colour forms beyond names, RGB and hex are refused: intensity *#, CMYK, HSV, bg/fg

- **Gap:** Stata's colorstyle.sthlp lists `colorstyle*#`, a bare `*#`, CMYK `"# # # #"`, `"hsv # # #"` and bg/fg/background/foreground, and dash says it accepts twoway's syntax. `translate_mcolor` (dash_render.py:3182-3250) accepts only names, 3-number RGB and #hex. `navy*.5`, `"0 0 0 255"`, `"hsv 240 1 1"`, `bg`, `fg` and `stblue*.3` all raise `ValueError` and keep the scheme colour with a note. In a scheme file, `color p1 navy*.5` falls back to #000000 with a warning.
- **Closable:** yes.
- **Plan:**
  1. Implement `colour*#`. For # <= 1, reuse the measured `_blend_intensity` (dash_render.py:5747, 255-(255-c)*f). For # > 1 (darkening), measure from Stata SVG fills of `mcolor(navy*1.5)`.
  2. Add CMYK→RGB and HSV→RGB, using Stata's conversions measured the same way.
  3. Map bg/background and fg/foreground to the scheme's `color background`/`color foreground`.
  4. In `SchemeParser._color`, fall back to the included scheme's value, not #000000.
  5. Test each form in both modes against a fixture of Stata SVG fill values.
- **Tracked:** new.

<a id="d8"></a>
### D8. Style lists (msymbol(O D), mcolor(red blue), lpattern(solid dash)) are not split across y variables

- **Gap:** Stata's [G-4] stylelists style each y variable in turn (`scatter y1 y2 x, msymbol(O D) mcolor(red blue)`), with quoted elements and the shorthands `.`, `=` and `..`/`...`. A short list is padded, and extra elements are ignored. dash.ado:4018-4030 copies the same options JSON onto every y's plot, so both series draw the scheme defaults with notes such as 'mcolor(red blue) is not a recognised colour'. `lpattern(solid dash) lcolor(red blue)` draws both lines solid in the scheme colours, and a single-y `mcolor(red blue)`, which twoway draws red, is refused whole.
- **Closable:** yes.
- **Plan:**
  1. In dash.ado's multi-y `_yi` loop (:4022), tokenise each list-taking option with Stata's parser, keeping quoted and compound-quoted elements whole. Write the `_yi`-th element into that plot's JSON. This covers `msymbol`, `mcolor`, `mfcolor`, `mlcolor`, `msize`, `mlwidth`, `mlabel`, `mlabcolor`, `mlabsize`, `mlabposition`, `color`, `lcolor`, `lpattern`, `lwidth`, `connect`, `fcolor` and the other list-taking options.
  2. Implement the shorthands:
     - `.` drops the key, so the scheme default applies;
     - `=` repeats the previous element, and as the first element means `.`;
     - `..`/`...` repeat the previous element to the end;
     - a short list is padded with `.`;
     - extra elements are ignored.
  3. Keep a note only for an unknown element, naming it.
  4. Check with a cscript against twoway's SVG: `scatter mpg price weight, msymbol(O D) mcolor(red blue)`, `mcolor("255 0 0" =)`, `mcolor(red ..)`, and `line` with `lpattern(solid dash)`.
- **Tracked:** new.

<a id="d9"></a>
### D9. Tick-label angle() drops Stata's anglestyle names other than horizontal/vertical without a note

- **Gap:** Stata's axis_label_options `angle(anglestyle)` accepts case-sensitive names (forty_five, rvertical, ninety, ...), and dash.sthlp:2333 documents `angle()`. `_parse_axis_angle` (dash_render.py:2735-2762) lowercases the value and knows only horizontal, vertical and numbers. So `angle(forty_five)`, `angle(rvertical)` and `angle(ninety)` leave labels horizontal with no note, and `angle(Vertical)`, which Stata refuses, is accepted. `_DASH_ANGLESTYLES` (:2690) already holds the full table for `mlabangle`.
- **Closable:** yes. The table and `_dash_anglestyle_degrees` already exist.
- **Plan:**
  1. Make `_parse_axis_angle` use `_dash_anglestyle_degrees`, with case-sensitive names and the -360..360 bound.
  2. Name an unknown value in the note, as `mlabangle` does.
  3. Test every anglestyle name on the x/y labels and the second axes in both modes.
  4. Confirm with a cscript that twoway refuses wrongly cased names.
- **Tracked:** new.

<a id="d10"></a>
### D10. A user scheme's directives that dash does not read are ignored without a word

- **Gap:** dash.sthlp:2820-2875 describes what a user scheme may contain, and dash reports unsupported options (:2944-2950), so users expect scheme settings to apply or be reported. `SchemeParser` reads about 40 key families, and every other directive is stored and ignored without a word. Examples: `color label`/`gsize label` (marker labels are #444444 10 px under every scheme, so s1rcolor's `color label white` comes out dark grey on black), textbox styles, `clockdir p#` and numticks. A user scheme holding such lines parses with zero warnings.
- **Closable:** yes.
- **Plan:**
  1. Keep two tables in dash_render.py: the directives dash consumes, and the families that govern only non-twoway graphs (bar, box, pie, dot, matrix, combine). The second set is skipped silently, as twoway skips it.
  2. For a non-shipped scheme, warn once, naming the unread twoway directives. Cap the list and show it as plain text, not SMCL.
  3. Consume the marker-label keys (`color label`, `gsize label`, `clockdir p#label`) in both modes.
  4. Test with Stata's own scheme files copied in as user schemes: the note must list exactly the unconsumed twoway keys. Test that s1rcolor's marker labels are white.
- **Tracked:** new.

<a id="d11"></a>
### D11. Markers are drawn at 80% opacity where Stata draws them opaque, and intensity is treated as alpha

- **Gap:** Stata draws markers opaque. The s2color.png fixture holds exact #1A476F/#55752F/#90353B with no blended values (stcolor.png likewise), and Stata's intensity lightens a colour toward white instead of making it transparent. dash turns `intensity p inten80` into alpha (`SchemeParser.fill_alpha`, dash_render.py:4563; `_scheme_alpha`, :7110-7125). Scatter, connected and dot markers draw at 0.8 under s2color, stcolor, s1mono and economist, while dropline, scatteri and rscatter draw at 1.0. `fintensity()` also becomes alpha (`_apply_fill_opts`, :6295-6309).
- **Closable:** yes.
- **Plan:**
  1. Draw markers at alpha 1 unless the colour declares %NN (sttrans) or the user sets `malpha()`/%NN.
  2. Implement intensity for fills (`intensity p#bar`, `fintensity()`, ci_area) as an opaque blend toward white, reusing `_blend_intensity` (:5747). Keep alpha for declared opacity.
  3. Assert rendered alpha and colour for p1-p3 of the four measured schemes in test_scheme_visual_truth.py.
  4. Check against Stata's SVG fill-opacity for scatter, bar and area under s2color, stcolor and economist.
- **Tracked:** new.

<a id="d12"></a>
### D12. Scheme axis/grid directives are not carried: y tick-label rotation, dashed grid lines, tick colours

- **Gap:**
  - dash.sthlp:2685 says each carried directive is consumed where Stata consumes it.
  - Stata's schemes include three directives dash does not carry:
    - `anglestyle vertical_tick vertical` rotates y labels in 11 of the 20 shipped schemes (visible in s2color.png);
    - `linepattern major_grid dash` dashes the grid in 6 schemes (visible in stcolor.png);
    - `color tick white` makes s1rcolor's ticks white (scheme-s1rcolor.scheme:61-62).
  - None of these is in the shipped files, and `apply_to_figure` (dash_render.py:4987-5042) sets no label orientation, grid dash or tick colour. So s2color's y labels are horizontal, stcolor's grid is solid #f0f0f0, and s1rcolor's ticks are black on a #000000 region, where they cannot be seen.
- **Closable:** yes.
- **Plan:**
  1. Extend scripts/extract_scheme_truth.py to carry `anglestyle horizontal_tick/vertical_tick`, `linepattern major_grid/minor_grid`, `color tick/minortick` and `linewidth tick`. Regenerate the 20 files and their provenance.
  2. Add parser attributes, with `_FALLBACK_PROPS` at s2color's values.
  3. In `apply_to_figure`, set:
     - the y axis `major_label_orientation` to π/2 for 'vertical';
     - `grid_line_dash` via `translate_lpattern`;
     - the major and minor `tick_line_color`.
     Explicit `ylabel(,angle())` and grid options still win.
  4. Pin each scheme in test_scheme_rendered_output.py in both modes.
  5. Add label rotation, grid dasharray and tick colour to the Stata SVG measurement in test/fixtures/scheme_visual for all 20 schemes.
- **Tracked:** new.

<a id="d14"></a>
### D14. Text and marker sizes are fixed at a 4-inch reference and do not scale with the figure; scale() is ignored

- **Gap:**
  - Stata's size.sthlp makes sizes relative to the graph, and truth.json records stcolor's title at 4.86% of the graph height. `scale(#)` resizes all text, markers and lines.
  - dash fixes sizes in CSS pt/px at a 4-inch reference (dash.sthlp:2773-2783; `_MARKER_PX_ANCHOR` 8 px, dash_render.py:3701), while figures stretch to their container.
  - At 1200 px wide the s2color title is about 2.1% of the height, and at phone width the reverse. The marker-to-text ratio is 0.54 against Stata's 0.40.
  - `scale()` is only named in the note (dash.sthlp:2968-2976).
- **Closable:** partly. Bokeh font and marker sizes are absolute CSS/screen lengths with no plot-relative unit. True relative sizing on a responsive figure needs a CustomJS resize handler that rewrites every size, which is slow on large figures and must be replicated in the served app.
- **Plan:**
  1. Honour `scale(#)` by multiplying every scheme and option size at build time.
  2. Anchor sizes to the figure's nominal height (`ysize()` or graphsize y) instead of 4 inches, using Stata's anchor ratios.
  3. Optionally, add a bounded CustomJS on `inner_height` changes that rescales fonts and marker sizes, in both modes.
  4. Test the Bokeh models. Take headless-browser screenshots at two widths and compare title and marker size, as a percentage of height, with truth.json.
- **Tracked:** `scale()`: GAPS.md E1 (deferred by WP-27); relative sizing is new (the help documents the 4-inch reference).

<a id="d16"></a>
### D16. Tick geometry and axis furniture are Bokeh's: minor ticks, inward tick stubs, economist's axis, legend key size

- **Gap:**
  - What Stata draws:
    - ticks outside only, of length `gsize tick`;
    - no minor ticks unless `xmtick()`/`ymtick()` ask;
    - economist's y axis on the right with no line or ticks (`axisstyle vertical_default vertical_nolinetick`, `yesno alt_yaxes yes`, `tickposition axis_tick inside`; scheme-economist.scheme:276, :387, :299; economist.png);
    - legend line keys `gsize legend_key_xsize` long.
  - dash keeps Bokeh's defaults under every scheme: `major_tick_in` 2, `major_tick_out` 6, black minor ticks with `minor_tick_out` 4, economist's y axis on the left with a black line and ticks, and a legend `glyph_width` of 20 px.
  - dash.sthlp:2736-2740 and :2897-2899 document this.
- **Closable:** yes. Every item maps to a settable Bokeh property.
- **Plan:**
  1. Set `minor_tick_line_color` to None unless `xmtick()`/`ymtick()`/`xmlabel()`/`ymlabel()` ask for minor ticks.
  2. Set `major_tick_in` 0 and `major_tick_out` from `gsize tick`. Carry `tickposition axis_tick`: inside means out 0 and in > 0.
  3. Carry `axisstyle horizontal_default/vertical_default` (the *_nolinetick and *_notick variants) and `yesno alt_xaxes/alt_yaxes` in the extractor and shipped files:
     - vertical_nolinetick sets `axis_line_color` and `major_tick_line_color` to None;
     - `alt_yaxes yes` sets `y_axis_location` to 'right'.
  4. Set the legend `glyph_width`/`glyph_height` from `gsize legend_key_xsize/ysize`.
  5. Test the Bokeh models per scheme in both modes against Stata's SVG and economist.png, and restate dash.sthlp:2736-2740 and :2897-2899.
- **Tracked:** minor ticks and tick geometry are documented in dash.sthlp:2736 and :2897-2899; the rest is new.

<a id="d17"></a>
### D17. Titles are bold and left-aligned, axis titles italic, and title/note positions ignore the scheme (also reported as B29)

- **Gap:** Stata's textboxstyle-heading.style sets no bold weight. `horizontal heading center` applies in 19 of the 20 schemes; economist uses left, with `clockdir title_position 11` and `note_position 1`. Axis titles are upright (s2color.png). `apply_to_figure` (dash_render.py:5031-5042) sets only the title's colour and size, so every scheme keeps Bokeh's bold, left-aligned Title and italic axis labels. The subtitle, note and caption Labels sit at x=0 (:18988-18994), and `title()`'s `position()`, `justification()` and `ring()` are only named in a note.
- **Closable:** yes.
- **Plan:**
  1. Carry `horizontal heading/subheading/body/small_body` and `clockdir title/subtitle/caption/note_position` in the extractor and shipped files.
  2. In `apply_to_figure`, set `title.align` from the justification, and `text_font_style` and `axis_label_text_font_style` to 'normal'. Place the subtitle, note and caption by the scheme's justification and clock position.
  3. Honour `just()` and `position()` on title, subtitle, note and caption.
  4. Pin each scheme in both modes, and measure title anchor and weight from Stata's SVG for s2color, stcolor and economist.
- **Tracked:** new.

<a id="d18"></a>
### D18. sttrans's %20 opacity reaches only some layer types

- **Gap:** Under sttrans, Stata draws every p# colour at 20% opacity (`color p1 "26 71 111 %20"`; SVG fill-opacity 0.20). dash.sthlp:2705-2723 says dash carries this 'as Stata draws it', but :2718-2721 admits that range, spike, fit, band, density, function and immediate layers take the colour 'but not yet its opacity'. Probe: lfit, kdensity and function lines, rspike/spike/rcap segments, and scatteri/rscatter/dropline markers are drawn at alpha 1.0, and the rarea fill at 0.5. Scatter, connected, line, bar, area, histogram and dot already draw at 0.2.
- **Closable:** yes.
- **Plan:**
  1. Route the remaining mappers through `GlyphMapper._scheme_alpha`/`SchemeParser.default_alpha`, for line alpha as well as fill: rarea, rbar, rspike, rcap, rcapsym, rline, rconnected, rscatter, spike, dropline, the fits and ci bands, kdensity, function, scatteri, pci, pcspike, pccapsym and pcarrow. Dot already draws at 0.2.
  2. Keep the precedence of the user's %NN and `malpha()`.
  3. Extend test_scheme_resolution.py's sttrans rows to every plot type in both modes.
  4. Remove the 'not yet' sentence from dash.sthlp.
- **Tracked:** BUGS.md:907 (the WP-17 follow-up: routing each layer through `default_alpha`).

<a id="d19"></a>
### D19. twoway histogram ignores the scheme's histogram style (fill, outline, intensity, width)

- **Gap:** Stata's twoway_histogram_parse.class:188 applies `.style.setstyle, style(histogram)`, which chains to `color histogram`, `intensity histogram`, `color histogram_line` and `linewidth histogram`. The resulting styles are: s2color khaki fill with a stone outline; stcolor stc1 at inten90 with a vthin stc1*0.7 outline; s1mono gs8 with black. `map_histogram` draws the p1 colour (#1a476f, #1a85ff, #606060, #3e647d) at alpha 1.0 with a white 1 px outline (dash_render.py:9585-9591), and no shipped scheme carries `color histogram`. No Stata histogram render is in the fixtures, so the expected look rests on Stata's style files.
- **Closable:** yes.
- **Plan:**
  1. Add `color histogram`/`histogram_line`, `intensity histogram` and `linewidth histogram` to the extractor and the 20 files. Resolve `stc1*0.7` once D7's intensity forms exist.
  2. Have `map_histogram` use them in both modes, with explicit `fcolor()`/`lcolor()`/`color()` still winning.
  3. Pin them for each scheme.
  4. Measure a `twoway histogram mpg` SVG under s2color, stcolor, s1mono and economist into the scheme_visual fixture.
- **Tracked:** new.

## E. Dashboard features and interactivity

Area E covers the dashboard layer: the auto, r x c, placement and `layout(bs)` grids, `tabs()`, one `link()` group with box and lasso brushing, dropdown, slider and range filters (including date variables and `exclude()`), KPI cards (15 statistics plus p#, `fmt()`, `update()`, if/in), and a shared toolbar with PNG save, CSV and `hover()`. Most of it works in both modes and is heavily tested: node runs the JavaScript, the served callbacks are called directly, and the saved and served pages are compared. Two S1 defects remain. KPI `fmt()` writes `%w.0g` as one significant digit and drops other formats it accepts. After several filter moves, `exclude()` leaves graphs and cards showing a filter state that no longer exists. There are also two S2 gaps: dates and formatted numbers ignore Stata display formats, and the saved page does not refit computed layers. The other eleven are S3: structural limits, differences between the saved and served pages, incomplete export, silent callback errors and no in-browser end-to-end tests.

| ID | Gap | Sev | Closable | Effort |
|---|---|---|---|---|
| E1 | KPI `fmt()` accepts formats the card then does not apply, and `%w.0g` rounds the card to one significant digit | S1 | yes | M |
| E2 | `exclude()` leaves excluded graphs and cards showing rows from a filter state that no longer exists | S1 | yes | M |
| E3 | Dates and formatted numbers on date axes, filter widgets, KPI cards and tooltips ignore the variable's Stata display format | S2 | yes | L |
| E4 | The saved page does not re-estimate computed layers after a filter move | S2 | see C4 | - |
| E5 | A box or lasso selection on bars or histograms dims them and drives nothing, and concurrent selections are not combined | S3 | yes | M |
| E6 | A filter move keeps the build-time frame: the second axis keeps its unfiltered range, and `by()` panels emptied by a filter stay drawn | S3 | yes | M |
| E7 | KPI cards take no weights and lack statistics summarize and tabstat report | S3 | yes | M |
| E9 | Only one link group per dashboard | S3 | yes | L |
| E10 | PNG export is incomplete, and there is no vector or scripted export | S3 | partly | M |
| E11 | Saved-page callbacks fail silently | S3 | yes | S |
| E12 | Saved-page sliders recompute at every drag step, with no throttle | S3 | yes | S |
| E13 | The filter widget set is narrow: single-select only, no missing-value option, a >= slider only, no reset | S3 | yes | M |
| E14 | The saved page and the served app still present the dashboard differently | S3 | yes | M |
| E15 | `tabs()` drops unknown names and whole tabs silently, and ignores `layout()` inside a tab | S3 | yes | M |

<a id="e1"></a>
### E1. KPI `fmt()` accepts formats the card then does not apply, and `%w.0g` rounds the card to one significant digit

- **Gap:** dash.sthlp:1253-1255 says `fmt()` takes a numeric display format and refuses anything else. `dash kpi` accepts anything `confirm numeric format` accepts (dash.ado:2294-2312). Its log line uses Stata's `: display`, but the card is written by Python `format()` (`_dash_format_kpi_value`, dash_render.py:19609-19680) and, after a move, by `dash_numfmt`/`dash_py_g`. Probe: `fmt(%10.0g)` of 6165.2567 shows `6e+03` in both modes and after every move. `%9,2f`, `%21x` and `%16H` show the raw value. `%td` of 15000 shows `15000.0`. Date KPIs ignore `fmt()`. Without `fmt()` a variable's own %g format is dropped, so the card shows 6165.26 where `summarize` prints 6165.257. Stata's outputs are not yet recorded.
- **Closable:** yes -- the fix is one writer of Stata formats, or an r(198) refusal of any format the page cannot write.
- **Plan:**
  1. In the shared formatter from E3, implement `%w.dg` (the width-driven `%w.0g` rule first), the European comma, `%x`/`%H` (or refuse them) and %t pictures. Use it in `_dash_format_kpi_value` and `dash_numfmt`, and carry a variable's own %g format.
  2. Refuse with r(198) in `_dash_validate_value 'format'` any format the page cannot write, naming it.
  3. Add a cert test: the rendered card equals the Stata-side kpi display for each accepted format, in both modes and after a filter move.
  4. Record a fixture of Stata `display` outputs and compare the Python and node output against it: %9.0g, %10.0g, %8.0g, %9.2g, %9,2f, %12.0fc, %9.2e, %td and %tdCCYY-NN-DD applied to 6165.2567, 3.14159, 1e7 and -0.5.
- **Tracked:** Closed in WP-28, BUGS.md "KPI fmt() accepts formats the card then does not apply, and %w.0g rounds the card to one significant digit", commit ef92806; residual deferred (WP-28): a spread of a date variable is computed in milliseconds (outside E1, E3 and G6) -- closed in WP-29 (P0.20, commit 529875d); was: new

<a id="e2"></a>
### E2. `exclude()` leaves excluded graphs and cards showing rows from a filter state that no longer exists

- **Gap:** dash.sthlp:1128-1138 says `exclude()` keeps a filter from affecting the named graphs and cards, and that other filters' moves redraw them from the rows all filters keep. Each callback masks with all filters but writes only the targets it does not exclude (saved dash_render.py:23723-23771, :14346; served :26763-26772). An excluded item therefore keeps whatever the last non-excluding move wrote. Served probe: price to [4000,5000], then foreign=1, then price back to its full range gives g1=3, g2=5, k1=3, where the current widgets imply 5 under either rule. The saved page behaves the same by construction; its multi-move sequence is unmeasured because the node harness cannot chain moves.
- **Closable:** yes
- **Plan:**
  1. Define each target's mask as the AND of the filters whose `exclude()` does not name it. A link group is one target, and `by()` panels follow their owner (`_dash_excluded`).
  2. Saved page: in `_FILTER_JS`, compute one mask per distinct exclusion set and rewrite every graph, derived and aggregate source and every KPI on every move. Pass all targets with their exclusion sets in the callback args (dash_render.py:23723ff).
  3. Served app: do the same in `_on_filter_change`, calling `_dash_frame_filter_mask` with each target's widget subset.
  4. Replace `TestExcludeHoldsWhileItsOwnFilterMoves` with multi-move sequences in both modes: node carries source state across moves, and served `_fire` calls are chained. Assert that the state depends only on the current widget values.
  5. Record Stata truth on auto: `count if foreign==1`, `count if foreign==1 & inrange(price,4000,5000)`, and `summarize mpg` over each. Rewrite dash.sthlp:1135-1138.
- **Tracked:** Closed in WP-28, BUGS.md "An excluded graph or card keeps the rows of the last move made by a filter that does not exclude it", commit cdb3a3d; was: ROADMAP.md:3633 (WP-23; records only the single-move rule), documented at dash.sthlp:1135; the stale state after several moves is new.

<a id="e3"></a>
### E3. Dates and formatted numbers on date axes, filter widgets, KPI cards and tooltips ignore the variable's Stata display format (also reported as G11, B8)

- **Gap:** Values should appear in the variable's display format, as twoway, `list` and `summarize` show them, and dash.sthlp:1245-1250 says a date KPI is "shown as a date". The probe found none of this:
  - Dropdowns: a %td dropdown lists `2001-12-31 00:00:00` (dash_render.py:17595), and a %9.0fc dropdown lists `3799`.
  - Sliders: date sliders show `%d %b %Y` and step span/100 days for every kind (:2033-2054), so %tm/%tq/%ty sliders stop mid-period. A numeric RangeSlider shows `0[.]00`.
  - Tooltips use `{%F}` for every kind except tc (:19803), so %tC loses its time.
  - KPI dates use one fixed picture per kind (:322-330): '09 Jan 2002' where Stata shows 09jan2002, and 'Oct 2000' where Stata shows 2000m10.
  - Date axes use one DatetimeTickFormatter per kind (`_datetime_formatter_for`, :335-356), so a %tm axis reads 'Jan 2000' where twoway shows 2000m1.
- **Closable:** yes
- **Plan:**
  1. Write one Stata display-format formatter in Python with a JS twin. It covers %td, %tc, %tC, %tw, %tm, %tq, %th and %ty (default and custom pictures), and numeric formats with c and the European ','.
  2. Use it for:
     - dropdown labels (keeping the raw value)
     - KPI first paint and `dash_apply_kpis`
     - tooltips (CustomJSHover)
     - date-axis ticks (a CustomJSTickFormatter in place of `_datetime_formatter_for`)
     - slider labels
  3. For %tw/%tm/%tq/%th/%ty filters, use a numeric slider over the Stata period number (step 1) with this formatter instead of DateRangeSlider. The served app shares the functions.
  4. Record Stata truth: `display %tm 480`, `display %tq 160`, `display %tdDD/NN/CCYY 15000`, a %tC value, `display %9.0fc 4099`, and the twoway axis labels of a %tm variable. Compare the Python and node output, and the widget, card, axis and tooltip text, in both modes.
- **Tracked:** Closed in WP-28, BUGS.md "Dates and formatted numbers on date axes, filter widgets, KPI cards and tooltips ignore the variable's Stata display format", commit be6bee4; was: new (planned in REMAINING.md:1057, 1076, 2220 and phases/PHASE-12; not in BUGS.md or GAPS.md)

**E4. The saved page does not re-estimate computed layers after a filter move (fits stay fitted to all rows; histogram bins and kdensity grid are frozen)** -- same gap as C4; see there.

<a id="e5"></a>
### E5. A box or lasso selection on bars or histograms dims them and drives nothing, and concurrent selections are not combined

- **Gap:** dash.sthlp:1003-1037 and 1278-1283 say a brush selects observations and `update(brush)` cards follow whichever graph is brushed.
  - Box and lasso tools have `renderers='auto'`. Histogram and bar Quads get a dimmed nonselection glyph (alpha 0.15) but no selection callback, so a box-select over them dims the bars and no card follows (read from code; not measured in a browser).
  - `_BRUSH_JS` (dash_render.py:14935-14956) reads only the last-changed source. Two unlinked graphs' selections are therefore not intersected, and clearing one resets the card while the other still shows its selection.
  - Brushing as a cross-filter is not promised (dash.sthlp:855), so that part would be an enhancement.
- **Closable:** yes -- a line or area layer drawn as one BokehJS path has a standard workaround: overlay markers for the selected rows.
- **Plan:**
  1. Restrict box and lasso to observation renderers (`renderers=[...]` in the toolbar builder, both modes), or translate a bin or bar selection into the rows it holds.
  2. Keep each graph's selection, and intersect the non-empty ones in `_BRUSH_JS` and the served brush handler.
  3. Overlay markers for the selected rows on linked line and area layers.
  4. Optional: an opt-in brush-as-filter (e.g. `link(..., filter)`) that feeds `dash_filter_mask`.
  5. Add node and served tests. Stata truth: `count if inrange(x,a,b) & inrange(y,c,d)`, and `summarize` over it.
- **Tracked:** new (the partial behaviour is documented at dash.sthlp:855, 1005-1017)

<a id="e6"></a>
### E6. A filter move keeps the build-time frame: the second axis keeps its unfiltered range, and `by()` panels emptied by a filter stay drawn

- **Gap:** dash.sthlp:1325-1340 says a filter move redraws every layer from the rows that pass. twoway on that subset scales both axes to it and draws only the groups present.
  - `yaxis(2)`/`xaxis(2)` get a fixed Range1d from the unfiltered frame (dash_render.py:17023), and no callback touches it. Probe with `filter(foreign)`=0: y2 stays at 3419.7-11764.3 while the kept prices span 3799-5788, in both modes.
  - With `by(foreign)` and `filter(foreign)`=1, the emptied '0' panel stays drawn with 0 rows (served probe), where `twoway ... if foreign==1, by(foreign)` draws one panel.
- **Closable:** yes
- **Plan:**
  1. Make the y2 range a DataRange1d restricted to its own renderers, as `_dash_keep_primary_ranges` does for the first axis. Or recompute start, end and natscale ticks in both callbacks from `_dash_secondary_values`' logic, with a JS twin.
  2. Hide a `by()` panel whose rows are all filtered out and reflow the grid: rebuild the gridplot children in the served app, and toggle visibility and re-lay the GridPlot in the saved page's JS.
  3. Test in both modes: y2 start and end after a move equal a build on the filtered frame, and panel visibility follows the filter.
  4. Stata truth (unmeasured today): the axis ranges of `twoway ... if foreign==0` with `yaxis(2)`, and the `by()` panel count on the subset.
- **Tracked:** new (the y2 item is planned in REMAINING.md:1238)

<a id="e7"></a>
### E7. KPI cards take no weights and lack statistics summarize and tabstat report (also reported as G13)

- **Gap:** dash.sthlp:1245-1250 ties the cards to `summarize, detail`, and dash's graph layers honour weights. But `_dash_kpi` declares `syntax anything(name=statspec) [if] [in]` (dash.ado:6079), so `dash kpi mean(price) [aw=w]` is refused. `valid_stats` (dash.ado:6103) lacks kurtosis, semean, range, n and sum_w, and neither `_kpi_statistic` (dash_render.py:21232-21305) nor `dash_apply_kpis` has a weighted path. The KPI syntax is documented without weights (dash.sthlp:1194-1198), so this is a missing capability, not a broken one.
- **Closable:** yes
- **Plan:**
  1. Add `[aweight fweight iweight]` to `_dash_kpi`'s syntax, plus pweight for mean (`summarize` refuses pweight). Carry the weight type and variable in the KPI JSON.
  2. Add weighted mean, sum, sd, var and percentiles in `_kpi_statistic`, the served app and `dash_apply_kpis`, reusing `dash_wpctl`.
  3. Add kurtosis, semean and range.
  4. Record a Stata fixture from `summarize x [aw=w], detail` and `tabstat x, s(semean range kurt)`. Check it on first paint and after filter and brush moves in both modes, and add cscript refusals for the weight types `summarize` refuses.
- **Tracked:** new

<a id="e9"></a>
### E9. Only one link group per dashboard

- **Gap:** dash.sthlp:1024-1027 states the limit: `link()` may be given once. `_dash_link_names` returns one flat list (dash_render.py:17956-17972), and the served app keeps one `shared_source` (:25920-25933). Two independent brushing groups, such as a price pair and a quality pair, cannot be built.
- **Closable:** yes -- dash already collects repeated `filter()` options before `syntax`, and can do the same for `link()`.
- **Plan:**
  1. Accept `link(g1 g2 / g3 g4)`, or repeated `link()` options collected as `filter()` is, and refuse a name that sits in two groups.
  2. Build one shared source per group, with brush and KPI wiring, `exclude()` and the CSV per group. In the served app, `_shared` becomes a dict keyed by group.
  3. Add parity tests (test_mode_parity corpus) and node and served tests asserting that a selection in group A never changes group B.
  4. Stata truth: the selected rows equal `count if` over the box's bounds.
- **Tracked:** new (documented limitation, dash.sthlp:1024)

<a id="e10"></a>
### E10. PNG export is incomplete, and there is no vector or scripted export

- **Gap:** WP-21 BR-21.1 (ROADMAP.md:3230) is to get the chart out as an image for a paper or a deck. A Stata user expects `graph export`-style png/svg/pdf/eps at a chosen size, run from a do-file. The only export is the toolbar's Save. It leaves KPI cards in a grid blank, omits the title, filters and tab strip, and writes one PNG per grid (dash.sthlp:1082-1087). Figures are canvas or webgl only (dash_render.py:21956, 26154), so there is no SVG. The PNG is at device-pixel resolution, and there is no `dash export`.
- **Closable:** partly -- no browser writes EPS, and canvas or webgl figures are raster in any capture (vector output needs the `svg` backend, practical only for small data). A scripted export also needs a Chromium-family browser on the machine, which dash cannot ship.
- **Plan:**
  1. Draw KPI cards and the header on canvas (a small figure with Text glyphs) so they appear in the toolbar PNG.
  2. Add an opt-in `svg` build option (`output_backend='svg'`), refused above a row threshold.
  3. Add `dash export using file.png|pdf|svg [, width() height() scale()]`:
     - Build the saved page to a temp file.
     - Run headless Chrome with `--screenshot` or `--print-to-pdf`, found as `responsive_probe.find_chrome` does, with a `DASH_CHROME` override. Or use `export_svg` when selenium is present.
     - Otherwise refuse with r(601). Refuse EPS outright.
  4. Tests:
     - The grid's save target includes the KPI figure.
     - The svg backend is set.
     - Export is gated by the dependency probe.
     - The PNG's pixel size equals width x scale, and the PDF has one page (under a 'browser' marker).
- **Tracked:** documented at dash.sthlp:1082-1087; ROADMAP.md WP-21

<a id="e11"></a>
### E11. Saved-page callbacks fail silently

- **Gap:** CLAUDE.md rule 14 and WP-13 require honour-or-report. `_FILTER_JS`, `_BRUSH_JS` and the CSV script (dash_render.py:14012-14956) have no try/catch apart from a BigInt guard. An exception leaves sources half-written and cards stale, with only a browser-console error. BUGS.md:1767 records exactly this: a brush ReferenceError on every selection that only a test found.
- **Closable:** yes
- **Plan:**
  1. Wrap each callback body in try/catch. On an error, show a visible banner Div ("this dashboard could not update; reload the page"), and call `console.error` with the callback name and the filter state.
  2. In the served app, log the traceback with the app's logger and show the same banner.
  3. Tests: under node, force a throw with a bad argument and assert the banner text; check in test_csp.py that the CSP admits the banner.
- **Tracked:** new

<a id="e12"></a>
### E12. Saved-page sliders recompute at every drag step, with no throttle

- **Gap:** Interaction should stay responsive up to `$dash_max_cells` (5,000,000), and the served app throttles with `value_throttled` (dash_render.py:26981-26985). The saved widgets use `js_on_change("value")` (:15085, 15143, 15202), so every step re-masks and rebuilds every source and KPI. The auditor measured 80 ms per step at 1,000,000 rows for one 5-column source under node 24, before any BokehJS redraw (not re-run here).
- **Closable:** yes -- `value_throttled` works in standalone pages, and requestAnimationFrame coalescing needs no server.
- **Plan:**
  1. Above a row threshold, bind the saved callbacks to `value_throttled` or coalesce steps with requestAnimationFrame. Keep per-step updates below it.
  2. Document the threshold in dash.sthlp.
  3. Test that the callback attribute depends on n, and add a browser timing check once dash has an in-browser test suite.
- **Tracked:** new (the behaviour is documented at dash.sthlp:1316)

<a id="e13"></a>
### E13. The filter widget set is narrow: single-select only, no missing-value option, a >= slider only, no reset

- **Gap:** Stata users filter with `inlist()`, `missing()` and `<=`, and dashboard users expect a multi-select and a way to clear every filter. `type()` is dropdown, slider or range only (dash.sthlp:1105-1120; `_dash_filter_widget`, dash_render.py:17547-17667), and the dropdown is a single-choice Select. `_dash_dropdown_values` drops missing values (:1806-1812), so missing rows cannot be chosen. The slider keeps only x >= value, and Reset does not touch filters (dash.sthlp:1057-1058).
- **Closable:** yes -- Bokeh's MultiChoice and Button models work in both modes.
- **Plan:**
  1. Add `type(multi)`: a MultiChoice with a 'value in set' mask, shared by `dash_filter_mask`, `_dash_frame_filter_mask` and the CSV.
  2. Add a '(missing)' dropdown option when the column has missing values.
  3. Add a `direction(le)` sub-option for sliders.
  4. Add a 'Reset filters' button in both modes.
  5. Test in both modes and under node. Stata truth from a fixture on auto: `count if inlist(rep78,3,4)`, `count if missing(rep78)` and `count if price<=5000`.
- **Tracked:** new

<a id="e14"></a>
### E14. The saved page and the served app still present the dashboard differently (also reported as F7, F8, F14, J11)

- **Gap:** dash is meant to be one product with two renderers (GAPS.md D; ROADMAP M2), and dash.sthlp's table promises the same layout and toolbar. Five differences remain:
  1. The served page has no viewport meta (dash.sthlp:1489). Its template adds only the CSP (dash_render.py:2169-2194), while the saved page carries the tag (:2313).
  2. The served app dims unselected points at Bokeh's 0.1, not dash's 0.15, because `_apply_nonselection_dimming` (:21855) runs only when saving.
  3. rspike and rconnected markers show a selection only when saved (dash.sthlp:1015-1016).
  4. Served `layout(bs)` does not reflow at 992 px and lacks the KPI cells' minimum heights (:2363-2385).
  5. The saved `layout(bs)` page puts the filter bar above the title; test_mode_parity.py ALLOWED exempts this.
- **Closable:** yes
- **Plan:**
  1. Add the viewport `<meta>` to `_dash_served_template`'s preamble, next to the CSP meta.
  2. Call the dimming function from the generated app for linked figures.
  3. Draw rspike and rconnected markers from row-identity copies in the app, as the saved page does.
  4. Give the served bs GridBox a stylesheet with the 992 px half-row rule and the KPI minimum heights, as `_dash_reflow` does at 768 px. Move the saved bs filter bar below the header, and drop the ALLOWED exemption.
  5. Add each item to test_mode_parity.py and test_served_bs_layout.py, plus a headless-Chrome check at 375, 900 and 1440 px (test_responsive_layout.py).
- **Tracked:** Closed in WP-28, BUGS.md "The saved page and the served app present the dashboard differently", commit b565d21; residual deferred (WP-28): under layout(bs) with filterposition(left) the saved page draws the header inside the content column beside the sidebar where the served app draws it above sidebar and content (research amendment; dash.sthlp records it); was: documented at dash.sthlp:1486-1494 and 1015-1016; the bs items are in ROADMAP.md:3352 (WP-21 "Not done here, recorded for later"); not in BUGS.md

<a id="e15"></a>
### E15. `tabs()` drops unknown names and whole tabs silently, and ignores `layout()` inside a tab

- **Gap:** dash.sthlp:996 says "tabs() works with every layout()". `link()`, `layout()` and `exclude()` refuse unknown names with r(198), and nothing is drawn another way in silence (dash.sthlp:962-965).
  - `tabs()` drops unregistered names and emptied tabs silently (dash_render.py:18352-18354; documented at dash.sthlp:994-995; no dash.ado check). Probe: `tabs(A: g1 g2 zz / B: nosuch)` builds only tab A, with no warning, in both modes.
  - Every tab is a ceil(sqrt(n)) grid (:18377). `layout(1 3)`, or placements, with `tabs(A: g1 g2 g3)` gives a 2x2 grid in list order.
  - `_dash_auto_grid_cols` is not applied inside tabs, and a tab title cannot hold ':' or '/'.
- **Closable:** yes
- **Plan:**
  1. In dash.ado, refuse an unregistered `tabs()` name with r(198), naming it, and update dash.sthlp:994-996.
  2. Lay out each tab by the layout's r and c, or by its placements read as tab-local positions (refused when they collide), and by `_dash_auto_grid_cols` under auto. `_dash_tab_panels` is shared, so both modes change together.
  3. Allow quoted tab titles, parsed in dash.ado and `_dash_parse_tabs`.
  4. Tests: cscript refusals, and the saved and served grid shape per tab in test_layout_tabs.py and the parity corpus.
- **Tracked:** new (the silent drop is documented at dash.sthlp:995)

## F. Served mode (dash serve)

Served mode runs the registry as a live Bokeh Server app. There are two routes. `dash serve` blocks Stata, binds loopback and takes `port()`, `timeout()` and `nobrowser`. `dash build, server` writes a standalone `python app.py` that has /health, a CSP and security headers, origin checks and rate limits, and recomputes every layer and KPI from the filtered rows. That core works and is tested: the real launch, timeout, console SIGINT, headers, limits, and recompute parity with the saved page. The weak parts are the lifecycle around the launch (rc 0 on a failed launch, Break is never polled in the GUI, orphaned servers, output that never reaches Stata), operations (logging, env-var checks, a shallow /health, no cap on sessions, which fall short of AGENTS.md rules 14, 15, 17 and 18), and a few closable fidelity limits that are documented.

| ID | Gap | Sev | Closable | Effort |
|---|---|---|---|---|
| F1 | `dash serve` returns rc 0 when no server ran; the app clamps an out-of-range `--port` | S1 | yes | S |
| F2 | A killed Stata leaves the served app running, still holding the port and the data | S2 | yes | S |
| F3 | Each session reloads the whole dataset, sessions have no cap, one event loop serves all | S2 | partly | M |
| F4 | In the Stata GUI, Break cannot stop `dash serve`; the interface is never polled | S2 | yes | S |
| F5 | The served app's notes, warnings, URL and errors never reach Stata's Results window or log | S2 | yes | M |
| F7 | A served brush dims unselected points to Bokeh's 10% instead of dash's 15% | S3 | see E14 | - |
| F8 | A served `layout(bs)` grid does not reflow as the saved one does | S3 | see E14 | - |
| F9 | Help text, generated-app comments and messages disagree with how the served app works | S3 | yes | S |
| F12 | Start-up env-var check covers only `BOKEH_ALLOW_WS_ORIGIN` | S3 | see I1 | - |
| F14 | The served page declares no phone viewport | S3 | see E14 | - |

<a id="f1"></a>
### F1. `dash serve` returns rc 0 when no server ran (port in use or app crash); the app clamps an out-of-range `--port` instead of refusing it

- **Gap:** dash.sthlp:711-715 and 1353-1356 say `dash serve` blocks until the server stops, and a failed command should return a non-zero rc. In fact the launcher calls `_proc.wait()` and never reads `returncode` (dash_render.py:27701-27715), and nothing checks the port first (`_dash_serve_spec`, dash.ado:7252-7345). Probe with the port held by another socket: rc 0 after 1.7 s. The only trace was the child's `OSError: [Errno 48] Address already in use` on process stderr, which never reaches Stata. Both routes default to port 5006, so a leftover `app.py` makes a new `dash serve` "succeed" while the browser shows the old dashboard. Separately, `python app.py --port 80` serves on 1024 because of the clamp at dash_render.py:27371. The banner does name 1024, and `dash serve` refuses the port itself before reaching that clamp (dash.ado:7303-7306).
- **Closable:** yes.
- **Plan:** 1. In the launcher, treat any child exit other than 0 or a SIGINT/SIGTERM stop as failure: capture stderr through a PIPE and raise `RuntimeError` with its last lines. `_dash_serve` then errors with "no server started on port N: the port is in use". 2. Poll /health for up to 30 s and print the URL only once it answers. 3. Optionally test-bind 127.0.0.1:port first. 4. Make the app's argparse refuse `--port` outside 1024-65535 instead of clamping, and drop the unreachable clamp at 27680. 5. Tests: a pytest that runs the launcher against a held socket and asserts failure plus the message. A cscript asserts `capture dash serve, port(held) timeout(1) nobrowser` gives `_rc != 0`.
- **Tracked:** Closed in WP-28, BUGS.md "dash serve returns rc 0 when no server ran, and an out-of-range --port is clamped instead of refused", commit 8f130a7; was: new

<a id="f2"></a>
### F2. A killed Stata leaves the served app running, still holding the port and the data

- **Gap:** dash.sthlp:1353-1356 and 1496-1501 say Stata erases the temporary app, which embeds the data, when `dash serve` ends. The app is a `Popen` child with no parent-death watch (dash_render.py:27701; no getppid, atexit or signal handling). Probe: after SIGKILL of the launcher (what a GUI force-quit, crash or Task Manager kill does), /health still returned 200 and the app file with the base64 data was still on disk. The spec and data JSON tempfiles (dash.ado:7392) are left behind too. Under `timeout(0)` the orphan holds 5006 forever, which feeds F1. Closing a console terminal does stop the child, because SIGHUP goes to the process group.
- **Closable:** yes.
- **Plan:** 1. Start the child with `stdin=PIPE`. Behind a `--parent-watch` flag, a daemon thread in the app blocks on `sys.stdin.read()` and on EOF schedules `io_loop.stop` via `add_callback`. Do not use `os.kill(ppid, 0)`: on Windows it terminates the target process. 2. The launcher deletes the spec and data JSON once the app is written, and deletes the app file once /health answers. 3. Tests: SIGKILL the launcher (TerminateProcess on Windows CI), then assert /health stops within 5 s and that no file holding `_DATA_B64` or the data JSON remains. Keep the HC4-21 cscript check.
- **Tracked:** new

<a id="f3"></a>
### F3. Each session reloads the whole dataset, sessions have no cap, and one event loop serves them all (also reported as I4)

- **Gap:** AGENTS.md rules 3 and 18 and dash.sthlp:1440-1484 imply bounded resource use. `make_document` decodes the whole payload and builds a new DataFrame per session (dash_render.py:25846, `_load_spec_and_data()`). Probe at 200k x 3: a 17.8 MB app, 0.5-0.6 s and about 70 MB RSS per session (298 -> 380 -> 449 -> 519 MB). A live server showed about 130 MB and 1 s per session, and 1.15-1.53 s per dropdown move with the loop serving nothing else. The limiter bounds session creation (60 per client per minute), not open sessions. Bokeh discards only unconnected sessions (dash sets no `unused_session_lifetime`), so held websockets pile up without bound.
- **Closable:** partly. Model changes must be applied on the document's single event loop, and GIL-bound Python recomputation cannot be parallelized. `num_procs>1` forks (no Windows support) and copies the data into every process.
- **Plan:** 1. Decode the spec, frame and metadata once at import into a read-only module cache. 2. Add `--max-sessions N` (default about 20), counted in `make_document` and `on_session_destroyed`, with a "server busy" page past the cap, a per-client concurrent cap, and the option exposed on `dash serve`. 3. Set `unused_session_lifetime`/`check_unused_sessions` explicitly, and add a global recompute budget. 4. Optionally recompute in a `ThreadPoolExecutor` under `without_document_lock` and apply the result with `doc.add_next_tick_callback`. 5. Tests: N `pull_session`s grow RSS by much less than the data size per session, and the (N+1)th is refused. /health answers within 1 s during a 200k recompute.
- **Tracked:** new (BUGS.md "lowess and fpfit cost more than they need to..." closed only estimator cost and the per-session throttle)

<a id="f4"></a>
### F4. In the Stata GUI, Break cannot stop `dash serve` and Stata's interface is never polled while it blocks (also reported as H2)

- **Gap:** dash.sthlp:711-715, 1353-1356 and 737-738 say the server runs until Ctrl+C or `timeout()`, and a Stata user expects Break to end any command with r(1). The launcher blocks in `subprocess.wait()` (dash_render.py:27711-27715), catches only `KeyboardInterrupt`, and never calls `sfi.SFIToolkit.pollstd()`/`pollnow()`. Stata's sfi.py:5723-5746 says Break reaches Python only as a `BreakError` from those calls. The only recorded stop test (BUGS.md:1579) sends SIGINT to the console's process group. So in the GUI with the default `timeout(0)`, the likely only exit is to kill the child by hand. This is unmeasured in the GUI, because rule 22 forbids launching it.
- **Closable:** yes.
- **Plan:** 1. Replace `_proc.wait()` with `while proc.poll() is None: sfi.SFIToolkit.pollstd(); time.sleep(0.2)`, importing sfi only inside Stata. 2. On `BreakError`/`KeyboardInterrupt`, terminate and wait for the child, then re-raise so the command ends with r(1). 3. Say "press Break" in dash.ado:7422 and dash.sthlp. 4. Tests: a stub sfi whose `pollstd` raises `BreakError` after N calls, asserting the child is gone and the port is free. `TestTheRealHandoffServes` must still pass. Record one manual GUI check.
- **Tracked:** new

<a id="f5"></a>
### F5. The served app's notes, warnings, URL and errors never reach Stata's Results window or log

- **Gap:** GAPS.md E2/E3/D6 (closed) and BUGS.md:1737-1741 require that ignored options and empty layers are reported. dash.sthlp:1403-1408 says the app reports `BOKEH_ALLOW_WS_ORIGIN` at start. The probe spec had `mcolor(notacolor)`, `msymbol(weird)`, `xlabel(0(1)10, nosuchsub)` and an empty `lfit`. On it, `DashRenderer.render()` gives 4 notes, but `ServerAppBuilder.build()` gives 0 (dash_render.py:24937-25015). The same 4 appear only per browser session inside the server. `dash serve` starts the child with inherited file descriptors (dash_render.py:27701), so the URL, limits, env warnings, refusals and tracebacks bypass Stata's Results window. Unflushed banner prints (27406-27411) were lost under a pipe plus SIGTERM.
- **Closable:** yes.
- **Plan:** 1. In `ServerAppBuilder.build`, run `make_document` once on a throwaway Document under `warnings.catch_warnings` and re-issue its notes in the building process. 2. Start the child with `stdout/stderr=PIPE`. A reader thread queues the lines, and the F4 poll loop prints them through `sys.stdout`. 3. Print the URL and /health URL from Stata once /health answers, and flush every banner print. 4. Tests: build-time warnings match `DashRenderer`'s across the `test_mode_parity` corpus. A cscript greps the `dash build, server` log (as HC5-08 does). A launcher test checks that a child line reaches `sys.stdout`.
- **Tracked:** new (related: GAPS.md D6 closed only in-process; closed BUGS.md entry "dash build, server never named the by() sub-options it ignores" fixed only `by()`)

**F7. A served brush dims unselected points to Bokeh's 10% instead of dash's 15%**: same gap as E14; see there.

**F8. A served `layout(bs)` grid does not reflow as the saved one does**: same gap as E14; see there.

<a id="f9"></a>
### F9. Help text, generated-app comments and messages disagree with how the served app actually works

- **Gap:** dash.sthlp:1373-1380 says to use `python app.py` because `bokeh serve app.py` lacks /health, the headers and the limits, and messages should be accurate in every front end. But:
  - The generated header says `# Launch with: bokeh serve <this_file.py>` first (dash_render.py:25199-25203).
  - `ServerAppBuilder`'s docstring says `allow_websocket_origin` is restricted to `localhost:{port}` (24219-24230), which is stale.
  - dash.ado:7422 prints "(Ctrl+C)" for every front end (see F4).
  - The banner always prints `http://localhost` whatever `--address` is (27406).
  - dash.sthlp:1470's "a flood cannot flood the log" is false: the served app writes one log line per 4xx response.
- **Closable:** yes. These are text-only fixes.
- **Plan:** 1. Point the header comment to `python app.py` and say what `bokeh serve` loses. 2. Update the docstring. 3. Change the message to "Break, or Ctrl+C in a console". 4. Print the bound address, and correct dash.sthlp:1470. 5. Extend test/test_tracking_documents.py (or add a pytest) to check the generated header and message text.
- **Tracked:** Partly closed in WP-29 (P0.13, commit c595259; P0.12a, commit 7f5c8f5): the message names Break for the GUI, and the banner prints the bound address; open: the generated header still names bokeh serve first, the ServerAppBuilder docstring is stale, and dash.sthlp still says a flood cannot flood the log; was: new

**F12. Start-up env-var verification covers only `BOKEH_ALLOW_WS_ORIGIN`; other Bokeh variables break the page silently**: same gap as I1; see there.

**F14. The served page declares no phone viewport, although dash already controls its template**: same gap as E14; see there.

## G. Data handling and scale

Area G is meant to carry Stata's data into the page faithfully: storage types, labels, formats, dates, missing values, Unicode names, frames, weights, time-series varlists, panels and large datasets. Most of that works. The sfi writer handles str#, strL and non-UTF-8 text, qualifiers are evaluated in Stata, seven of the eight %t kinds become real dates, labels reach filters, panels, legends and the CSV, and weights follow twoway's rules on the statistical layers. The gaps are at the edges. An internal column name can silently overwrite a user variable. String plot variables are accepted and time-series operators are refused, both the reverse of twoway. Unicode names fail in `filter()` and `dash kpi`. `%g`/float, `%tb`, `%tC` and extended missing values are not reproduced. The size limit counts exported values instead of embedded ones, and every dashboard draws the single dataset in memory at build.

| ID | Gap | Sev | Closable | Effort |
|---|---|---|---|---|
| G1 | Internal column names can overwrite a user variable, and dash's working columns need room in the user's dataset | S1 | yes | M |
| G2 | String variables are accepted as plot variables; twoway refuses them | S2 | yes | S |
| G3 | The data limit counts exported values, so large histograms, densities and fits are refused although the page would be small | S2 | partly | M |
| G4 | Time-series operators (L., F., D., S.) in a plot's varlist are refused; twoway draws them | S2 | yes | M |
| G5 | Unicode variable names are refused by filter() and dash kpi | S2 | yes | S |
| G6 | %g formats (Stata's default) and float storage are not reproduced; values show full double expansions | S3 | yes | M |
| G7 | %tC values are converted without leap seconds (off by up to 27 s) | S3 | yes | S |
| G10 | Axis ticks ignore the variable's display format unless xlabel()/ylabel() is given | S3 | yes | S |
| G11 | Dates are shown in fixed Bokeh patterns, not Stata's date text or the variable's own picture | S3 | see E3 | - |
| G12 | Extended missing values .a-.z are merged into one missing value | S3 | yes | M |
| G13 | KPI cards take no weights | S3 | see E7 | - |
| G14 | Large pages embed numbers as JSON text and are rendered inside Stata's process; browser load at the limits is unmeasured | S3 | partly | M |
| G15 | Panel (xtset) line idioms connect(L) and sort(id t) are not honoured | S3 | see B12 | - |
| G16 | Value labels are never drawn on axes or in tooltips | S3 | yes | S |
| G17 | Weight expressions are refused ([aw=price+1]); twoway takes an expression | S3 | yes | S |
| G18 | Weighted markers on scatter are not drawn | S3 | yes | M |

<a id="g1"></a>
### G1. Internal column names can overwrite a user variable, and dash's working columns need room in the user's dataset

- **Gap:** dash.sthlp:170-174 reserves only names that start with `__dashq`, so every other valid name should be read as data. But `_ROW_ID_COLUMN = "__dash_row__"` (dash_render.py:2008; JS `ROW_ID` at 14219) overwrites a user column of the same name in `_make_source` (21416). In the probe, a y holding 100..140 was drawn as 0..4 with no note. `__dash_pc_row__` and the `__mlabel__*` columns share the same namespace. The `__dashq<k>` qualifier columns (`_dash_qual_gen`, dash.ado:4220 onward) and the ustrfix strL (dash_render.py:1296-1300) are generated in the user's data, so data already at `c(maxvar)` would fail with r(900) (not measured).
- **Closable:** yes.
- **Plan:** 1. Rename the internal columns in both the Python and JS twins, using a character no Stata name can hold. Alternatively, reserve a `__dash` prefix and refuse it at export with r(110). 2. Build the qualifier, by()-ordered and ustrfix columns in a temporary frame (`frame put <needed vars>, into(tmp)`) and export from it, so nothing is added to the user's data. 3. pytest: variables named `__dash_row__` and `__mlabel__y` are drawn with their own values in both modes. 4. cscript: with `set maxvar 2048` and `c(k)==c(maxvar)`, a build with a plot qualifier, a by() qualifier and a non-UTF-8 strL succeeds and draws the rows twoway draws.
- **Tracked:** Closed in WP-28, BUGS.md "An internal column name could overwrite a user variable, and only __dashq was reserved", commit a158815; residual deferred (WP-28): the qualifier, by()-order and ustrfix columns are still generated in the data in memory, so a dataset at c(maxvar) may fail with r(900); a variable named like a drawn glyph field (x, y, x0, top, count, density and the like) draws its own values as a plot variable but is shadowed by the derived field in hover() and mlabel(); was: new

<a id="g2"></a>
### G2. String variables are accepted as plot variables; twoway refuses them

- **Gap:** twoway refuses a string y or x with r(109), "string variables not allowed" (`varlist(numeric ts)` at twoway_yxview_parse.class:120; `varname(numeric)` for histogram and kdensity). dash.ado:1271 declares `syntax varlist` without `numeric`, and `_dash_process_segment` has no type check. In the probe, a string x produced meaningless Scatter/Line/VBar glyphs with no note, and lfit and histogram crashed with "could not convert string to float".
- **Closable:** yes.
- **Plan:** 1. Declare `numeric` in the four varpart parsers per plot type, with twoway's message and r(109). 2. Keep `colorvar()`, `mlabel()`, `hover()` and `by()` accepting strings. 3. cscript: for each of the 38 types, put a string in each position and check that dash's rc and message match twoway's. 4. pytest: a hand-written spec with a string plot column gets a named refusal, not a traceback.
- **Tracked:** Closed in WP-28, BUGS.md "String variables are accepted as plot variables where twoway refuses them", commit b62c224; was: new

<a id="g3"></a>
### G3. The data limit counts exported values, so large histograms, densities and fits are refused although the page would be small

- **Gap:** The limits exist so that nothing "can grow without bound" (dash.sthlp:1504-1578). But `_dash_cell_cap` (dash.ado:2735-2754, called at 5920 and 6875) counts `_N` times (variables plus qualifier columns), whatever is drawn. As a result, `dash histogram x` on 5,000,001 obs is r(134) by default, and nothing can be drawn past 20M obs. Probe at 1e6 x 3: the page was 1.4 MB, but the note said "roughly 72 MB". The export was 57.3 MB of JSON, took 1.2 s and peaked at 1.35 GB RSS.
- **Closable:** partly. Rows that the page must hold (row-drawing layers, filters, link/brush, csv, hover) stay bounded by browser string and heap limits, so only graphs built from computed layers alone can escape the cap.
- **Plan:** 1. In dash.ado, count only the columns the page embeds. A computed-only graph with no filter, link or csv touching it counts only its drawn output. 2. Export in binary instead of JSON: a tempfile read with `pandas.read_stata`, or sfi arrays read into numpy. 3. Base the size note on what is embedded. 4. Test: a 6M-obs histogram builds, its bins equal `twoway__histogram_gen`'s and the page is under 2 MB; a 6M-obs scatter is still refused.
- **Tracked:** Closed in WP-28, BUGS.md "The data limit counts exported values, so large histograms, densities and fits are refused although the page would be small", commit 4e23bc0; residual deferred (WP-28): a by()-faceted graph is never treated as computed-only and is counted in full, as it was before this section -- the actual panel count is not known before the export, and multiplying the generic 120,000-cell bound by the by_groups LIMIT (100 by default) would read a two-panel by(foreign) on a plain kdensity or lpoly as 12,000,000, over the default cells limit on any dataset however small, which measurably regressed test/test_help_claims_6.py's by()-faceted lpoly grid before this residual was chosen; the export still writes every observation as JSON (DISCOVERY Q9), row-drawing layers, filters, link(), csv and hover() stay bounded by the limit, and the served app embeds every row -- WP-29 (P0.10, commit 735c534): hover()'s own variables count only where a layer can show them or csv is given; the graph itself is still treated as touched; was: new (the refusal is documented at dash.sthlp:1504-1578)

<a id="g4"></a>
### G4. Time-series operators (L., F., D., S.) in a plot's varlist are refused; twoway draws them

- **Gap:** dash.sthlp:135-142 promises twoway's syntax. twoway takes `varlist(numeric ts)` for yxview, zyx2view and the lfit/qfit/fpfit families (twoway_yxview_parse.class:120,123; twoway_lfit.sthlp:60), and `tsline` passes its varlist on to line. dash's varpart parsers (dash.ado:1273, 1298, 1329, 1358) declare `syntax varlist` without `ts`. So `dash line D.gdp year`, `dash tsline D.gdp` and `dash lfit y L.x` stop with r(101). This is `syntax`'s documented behaviour; it was not run in Stata.
- **Closable:** yes.
- **Plan:** 1. Declare `varlist(ts)` wherever twoway does, checking each parse class including mspline, mband and pc*. Keep histogram, kdensity, lowess and lpoly refusing. 2. Store each operator expression in the spec. At export, next to `_dash_qual_gen`, generate `double __dashts<k> = <expr>` under the current tsset/xtset, export it, drop it, and reserve the prefix. 3. In the renderer, map each column back to its expression for axis titles, tooltips and legend keys, using the text twoway shows (measure it). 4. cscript on sp500 (tsset) and grunfeld (xtset): L., F., D., S. and L2. across panel boundaries, plus `tsline D.x` and `lfit y L.x`, match twoway's serset/SVG, and `histogram D.x` stays r(101).
- **Tracked:** new

<a id="g5"></a>
### G5. Unicode variable names are refused by filter() and dash kpi

- **Gap:** Stata 14+ names may hold Unicode letters, and dash accepts them elsewhere (the by() check at dash_parse.mata:2916 uses `\p{L}`; tests use `[aw=größe]`). But `_dash_is_name` (dash_parse.mata:828-840) accepts ASCII only, so `filter(größe)` is refused as "not a valid Stata variable name", r(198). The KPI pattern at dash.ado:6094-6096 refuses `dash kpi mean(größe)` with "syntax is stat(varname)". Found by reading the code; not run in Stata.
- **Closable:** yes.
- **Plan:** 1. Replace both checks with `ustrregexm("^[\p{L}_][\p{L}\p{N}_]*$")` and `ustrlen<=32`, then `unab`/`confirm`. 2. Correct the refusal messages. 3. cscript: after `rename price größe`, `dash kpi mean(größe)` equals `summarize`, and `filter(größe, type(range))` and `type(dropdown)` build widgets. 4. pytest: the renderer builds a filter widget over a Unicode-named column.
- **Tracked:** Closed in WP-28, BUGS.md "Unicode variable names are refused by filter() and dash kpi and ignored by the renderer", commit 8d43e21; was: new

<a id="g6"></a>
### G6. %g formats (Stata's default) and float storage are not reproduced; values show full double expansions

- **Gap:** dash.sthlp:1782-1784 shows a value "in its display format where dash reproduces that format", and PHASE-11 BR-08.2 wants every format honoured. `%9.0g` is Stata's default, and `generate` makes floats. `_parse_stata_numeric_fmt` (dash_render.py:840-869) reads only `%w.d[f|e][c]`, and the writer sends no storage type. As a result:
  - A float 0.1 shows as 0.10000000149011612 in marker labels and dropdowns.
  - Tooltips use BokehJS's basic formatter, so 12345.67 becomes 1.235e+4.
  - `_dash_format_kpi_value(1234567.5,'%9.0g')` gives '1.23457e+06' where Stata's rule gives 1234568 (not measured).
- **Closable:** yes.
- **Plan:** 1. The writer sends each variable's storage type, and floats are shown as the shortest float32 repr. 2. Implement `%w.dg` and `%w.dgc` in Python and JS. 3. Use them in marker labels, tooltips, KPI cards, dropdown labels and the CSV. 4. Build a fixture of about 200 values under `display %9.0g`, `%8.0gc` and `%10.0g`, measured in Stata. Test on auto (price `%8.0gc`) and on generated floats.
- **Tracked:** Closed in WP-28, BUGS.md "%g formats (Stata's default) and float storage are not reproduced, so values show full double expansions", commit be6bee4; was: new

<a id="g7"></a>
### G7. %tC values are converted without leap seconds (off by up to 27 s)

- **Gap:** dash_render.py:432-439 converts `%tC` on `%tc`'s epoch and warns. test_dates.py:159 pins the warning, not the correct value. `Cofc()` offsets measured in test/fixtures/date_truth.json run from 9 to 27 s, and dash.sthlp never documents `%tC` or leap seconds.
- **Closable:** yes. Stata's `cofC()` does the conversion at export.
- **Plan:** 1. At export, convert with `cofC()` into a double column, or embed Stata's leap-second table and subtract. 2. Show Stata's `%tC` text, including 23:59:60. 3. Test against `display %tC` and `Cofc()` values added to date_truth.json. 4. Drop the warning.
- **Tracked:** new

<a id="g10"></a>
### G10. Axis ticks ignore the variable's display format unless xlabel()/ylabel() is given

- **Gap:** twoway labels default ticks in the variable's format (auto's price, `%8.0gc`, gives 5,000 10,000 15,000), a picture dash.sthlp:2349 cites. `_dash_apply_axis_options` applies a format only `if raw:` (dash_render.py:16981-16990), that is, only when `xlabel()`/`ylabel()` is given. In the probe, `%9.0fc`, `%9.2f` and `%8.0gc` with no `ylabel()` all got BasicTickFormatter, and `%8.0gc` never gets a pattern. Related drift: dash.sthlp:2349's `yscale(log) ylabel(#5)` example gets LogTickFormatter, with no comma format.
- **Closable:** yes.
- **Plan:** 1. Call `_dash_apply_axis_spec` with a default spec when `numeric_formats` holds the axis variable. 2. Add `%gc` through G6's formatter. 3. Compare twoway's SVG tick text for auto's price, weight and gear_ratio, in both modes.
- **Tracked:** new

**G11. Dates are shown in fixed Bokeh patterns, not Stata's date text or the variable's own picture** -- same gap as E3; see there.

<a id="g12"></a>
### G12. Extended missing values .a-.z are merged into one missing value

- **Gap:** twoway keeps `.a`-`.z` distinct. `by(x, missing)` draws one panel per missing code, titled with the value label or ".a" (bygraph_g.class:104-116, 430-454), and marker labels show the label or the code name. dash's writer reads with `missingval=None` and writes null (dash_render.py:1286-1289). So value labels for .a-.z (1178-1206) never match, and `_dash_by_groups` (1866-1890) puts every missing value into one panel. The single panel and the marker-label and CSV losses are documented (dash.sthlp:1650-1657, 1785-1787, 869). The merging of distinct codes in by() panels, dropdown filters and tooltips is not. `colorvar()`'s single missing category matches twoway, so it is not part of this gap.
- **Closable:** yes.
- **Plan:** 1. The writer keeps NaN for computation and adds a sparse `extendedMissing` map, `{var: {obs: "a"}}`. It reads Stata's raw missing doubles through sfi and decodes them with `Missing.getValue('.a')`...`'.z'`. 2. In the renderer, in both modes, key by() groups on (value, code) and title them with the value label, ".a", or the documented title for "."; marker labels, dropdown options and tooltips use the label or the code. Measure colorvar with colordiscrete. 3. Decide whether the CSV keeps an empty field or writes the code, and update dash.sthlp:869 and 1785-1787 to match. 4. cscript with labelled .a/.b in y and in the by() variable: panel count, panel titles and mlabel text equal twoway's SVG, and a dropdown lists .a and .b separately.
- **Tracked:** new (the marker-label and CSV parts are documented at dash.sthlp:1785-1787 and 869; the single Missing panel at 1650-1657)

**G13. KPI cards take no weights** -- same gap as E7; see there.

<a id="g14"></a>
### G14. Large pages embed numbers as JSON text and are rendered inside Stata's process; browser load at the limits is unmeasured

- **Gap:** CLAUDE.md rule 3 asks for bounded resources. dash.sthlp:1561-1570 puts 4M values at a 95 MB page and about 2 GB to render, and the 20M ceiling rests on Chrome's ~512 MB string limit. In the code:
  - `_make_source` (dash_render.py:21410-21413) sends columns through `.tolist()` as JSON decimals, about 20 B per value against about 10.7 B in binary. A 1e6-row scatter page was 47.6 MB.
  - The render runs inside Stata's Python (dash.ado:430, runpy) at about 0.5 GB per million values (1.67 GB peak at 1e6 x 3).
  - The binary-strL check calls StrLConnector once per observation (1304-1310).
  - The served app decodes the whole dataset on every session (25846).
  - Nothing measures browser load at 1M, 5M or 20M values.
- **Closable:** partly. Browser/V8 string and heap limits bound any page, and every scatter point must be embedded unless dash downsamples, which changes what is drawn.
- **Plan:** 1. Send numeric columns as float64 numpy arrays (Bokeh's binary encoding), and adapt the saved filter JS to typed arrays. 2. Measure load time and JS heap at 1M, 5M and 20M values with test/responsive_probe.py, and set the ceiling where a page still opens. 3. Cut peak memory inside Stata's Python: build sources from numpy without `tolist()`, read the data file in binary, and free the pandas frame before serialising. Keep to `python:` blocks only; any child process is started from inside the `python:` block and tested under Stata's interpreter. 4. Check binary strL in one Mata pass, and have the served app decode the data once per process, not per session. 5. Test page bytes per value, peak RSS per value, and mode parity.
- **Tracked:** new

**G15. Panel (xtset) line idioms connect(L) and sort(id t) are not honoured** -- same gap as B12; see there.

<a id="g16"></a>
### G16. Value labels are never drawn on axes or in tooltips

- **Gap:** twoway's `xlabel(1/5, valuelabel)` puts value labels at the ticks, and a user expects `hover(foreign)` to show Domestic/Foreign, as `list` and `browse` do. dash draws numbers on axes and in tooltips and names `xlabel(, valuelabel)` only in the note (dash.sthlp:672-679, difference 6). `_dash_build_hover` (dash_render.py:19839) takes no value labels.
- **Closable:** yes.
- **Plan:** 1. Read the `valuelabel` sub-option and fill `major_label_overrides` from the axis variable's label set, reusing the explicit tick-label path (dash_render.py:16783-16798). 2. For `hover()`, add a derived text column like the marker-label one. 3. Compare with twoway's SVG for `scatter mpg rep78, xlabel(1/5, valuelabel)` with a label set.
- **Tracked:** Closed in WP-28, BUGS.md "Value labels are never drawn on axes or in tooltips", commit 429d679; residual deferred (WP-28): on the one-line route a hover()-only variable is not exported (BUGS.md's earlier hover-export entry), so its labels cannot be shown -- closed in WP-29 (P0.10, commit 735c534), on every route; an x or y variable not named in hover() keeps its number in the tooltip; was: new (documented difference 6)

<a id="g17"></a>
### G17. Weight expressions are refused ([aw=price+1]); twoway takes an expression

- **Gap:** twoway reads `[aw=exp]`. dash refuses anything but one variable with r(198) (dash.ado:3713-3722). dash.sthlp:2186-2193 documents the refusal and says dash cannot evaluate the expression before the data leave Stata. That reason is stale: `_dash_qual_gen` (dash.ado:4220 onward) already evaluates Stata expressions into `__dashq` columns at build.
- **Closable:** yes.
- **Plan:** 1. Evaluate each distinct weight expression like a qualifier, into `double __dashw<k>` at export, under the same reserved-prefix rule. 2. Point `wexp` at that column. 3. Apply the fweight integer and sign checks to the evaluated values. 4. cscript: lfit, lfitci, kdensity and histogram with `[aw=price/1000]` and `[fw=int(price/1000)]`; fitted values equal twoway's serset.
- **Tracked:** GAPS.md A3 (documented refusal)

<a id="g18"></a>
### G18. Weighted markers on scatter are not drawn

- **Gap:** scatter.sthlp:917-925 (Weighted markers): a weight scales the marker's size, with aweights, fweights and pweights treated alike. dash.sthlp:2194-2201: on scatter and the other glyph layers the weight is accepted but not exported, and is named in the note as `[aweight]`. Markers are drawn at a single size.
- **Closable:** yes. Bokeh Scatter takes a per-row size field; only twoway's scaling rule must be measured.
- **Plan:** 1. Export the weight on scatter. 2. Measure twoway's rule from SVG marker radii, e.g. census `scatter drate medage [w=pop18p], msymbol(Oh)`: area proportional to the weight, with the scale reference measured. 3. Pass Bokeh a per-row size column in both modes, following filters. 4. Remove `[aweight]` from the note on scatter.
- **Tracked:** GAPS.md A3 (the WP-13 note on glyph layers)

## H. Installation, setup, platforms, packaging

This area promises a one-command setup: `dash_setup` finds Stata's Python, installs bokeh, numpy and pandas at their stated minimums, and checks dash's own files. It also promises a package ready for `net install` and `adoupdate` that runs wherever Stata 16+ and Python 3.8+ run. The packaging core works and is verified: the manifest, the file routing, schemes read from an installed tree, `adoupdate` through the release gate, and a setup summary that reports failures honestly. But everything was measured on one macOS arm64 machine, with StataNow 19.5 and Python 3.13/3.14. The served app crashes on Python 3.8/3.9, the declared minimums, other platforms, GUI Stata, Stata 16-18 and BE have never been tested, and `dash_setup` fails on PEP 668 Pythons.

| ID | Gap | Sev | Closable | Effort |
|---|---|---|---|---|
| H1 | The served app crashes on import under Python 3.8 and 3.9, and dash serve still returns rc 0 | S1 | see K2 | - |
| H2 | GUI Stata may have no way to stop dash serve: the documented Ctrl+C is a console key, and the wait loop never checks Break (unmeasured) | S2 | see F4 | - |
| H4 | The declared dependency minimums are untested, and the Bokeh-dependent security guards are verified only on Bokeh 3.8/3.9 | S2 | yes | M |
| H6 | dash starts without checking that Python can start or that its packages are installed | S2 | yes | S |
| H7 | dash_setup cannot install into PEP 668 'externally managed' Pythons, and the fixes it prints fail too | S2 | yes | M |
| H8 | A failed dash_setup leaves already-installed packages in place (rollback deferred) | S3 | partly | S |
| H10 | Loading the renderer leaves a 1.2 MB .pyc in PLUS/py that `ado uninstall` does not remove | S3 | yes | S |

**H1. The served app crashes on import under Python 3.8 and 3.9, and dash serve still returns rc 0** -- same gap as K2; see there.

**H2. GUI Stata may have no way to stop dash serve: the documented Ctrl+C is a console key, and the wait loop never checks Break (unmeasured)** -- same gap as F4; see there.

<a id="h4"></a>
### H4. The declared dependency minimums are untested, and the Bokeh-dependent security guards are verified only on Bokeh 3.8/3.9 (also reported as I7)

- **Gap:** `dash.pkg:17`, `dash.sthlp:3133-3134` and `dash_setup.ado:145-150` declare Python>=3.8, bokeh>=3.0, numpy>=1.23 and pandas>=2.0. Only two stacks were ever run: py3.13/bokeh 3.8 and py3.14/bokeh 3.9 (`test/conftest.py:207-212`). Both need Python 3.10+, so no tested stack covers Python 3.8-3.10 or bokeh 3.0-3.7. The security guards depend on Bokeh internals: text-sink XSS safety is pinned to `VERIFIED_BOKEH={'3.8.0','3.9.0'}` inside a test only (`test/test_label_sinks.py:153`), and the origin check replaces `match_host` (`dash_render.py:2283-2301`). There is no run-time `bokeh.__version__` check, and pip gets `bokeh>=3.0` with no upper bound (`dash_setup.ado:163`). Bokeh 3.8 and 3.9 already differed on websocket-origin admission.
- **Closable:** yes.
- **Plan:** 1. Pick a supported window and state it: raise the minimums to what is tested (e.g. Python>=3.10, bokeh>=3.8,<3.10), or add a nox/CI matrix over the minimums. 2. At renderer start, warn with a `UserWarning` when `bokeh.__version__` is outside the verified range. 3. Pass the upper bound to pip in `dash_setup`, and have `_dash_setup_gate` report "unverified" outside the range. 4. Run `test_label_sinks`, `test_csp`, the origin-check tests and `test_mode_parity` on each supported bokeh. 5. Update `dash.pkg`, both help files and CHANGELOG, then run `make gate` against each supported environment.
- **Tracked:** new.

<a id="h6"></a>
### H6. dash starts without checking that Python can start or that its packages are installed

- **Gap:** ROADMAP WP-07 BR-07.1 (`ROADMAP.md:703`) requires every dependency to be checked before use, with a message that names the fix. `_dash_python_ok` (`dash.ado:184-189`) checks only that `c(python_exec)` is non-empty. The renderer imports numpy, pandas and bokeh with no guard (`dash_render.py:73-107`), through uncaptured `python:` lines (`dash.ado:4196-4212`). Probe: under Python 3.8 without numpy you get `ModuleNotFoundError` and r(7102) with no mention of `dash_setup`. Python 3.6 gives a `SyntaxError`. `dash_setup`'s first Python call (`dash_setup.ado:76`) is uncaptured too, so setup stops before its summary.
- **Closable:** yes.
- **Plan:** 1. In `dash_render.py`, check `sys.version_info` first. Wrap the third-party imports in `try/except ImportError` and raise `SystemExit('dash: <pkg> is not installed for <sys.executable>; run dash_setup')`. 2. Add `_dash_require_deps` to `dash.ado`, run once per session and cached in a global on success. It sets a local from `importlib.util.find_spec` and `sys.version_info`. On failure it exits 198 through `_dash_say`, naming `c(python_exec)` and `dash_setup`. 3. Capture `dash_setup.ado:76`, retry it once, then report `c(python_exec)`, `c(machine_type)` and an architecture hint in `_dash_setup_summary`. 4. Tests: a pytest that runs the renderer under an interpreter without numpy and checks the message. A cscript that sets `sys.modules['bokeh']=None` and expects r(198) with the `dash_setup` remedy.
- **Tracked:** new (GAPS J4/WP-07 closed only the no-Python case).

<a id="h7"></a>
### H7. dash_setup cannot install into PEP 668 'externally managed' Pythons, and the fixes it prints fail too

- **Gap:** `dash_setup.sthlp` says setup installs the packages, retries with `--user`, and names a manual command. Measured: Homebrew Python refuses `pip install 'bokeh>=3.0'` with `externally-managed-environment`, with or without `--user`. So do Debian 12+ and Ubuntu 23.04+ `/usr/bin/python3`. The fallback it prints, `python -m pip install bokeh>=3.0` (`dash_setup.ado:192`), is unquoted, so the shell treats `>` as a redirect: bokeh installs unpinned and a file named `=3.0` appears. It also names `python`, which may not be Stata's interpreter. The upgrade hint uses single quotes, which cmd.exe ignores (`dash_setup.ado:223-224`). Also: no venv guidance in the help, a `--user` site created during the run is not on `sys.path`, and a Python without pip gets no `ensurepip` hint.
- **Closable:** yes.
- **Plan:** 1. Before calling pip, detect `EXTERNALLY-MANAGED` (in `sysconfig.get_path('stdlib')`) and whether pip is present (`find_spec('pip')`). 2. Add `dash_setup, venv(path)`: create the venv with `c(python_exec) -m venv`, install into it, then print or run `python set exec "<venv python>", permanently`, and document that Stata must restart. 3. Print every fix with `c(python_exec)` and the requirement in double quotes (`"bokeh>=3.0"`). 4. After a `--user` install, call `site.addsitedir(site.getusersitepackages())` and `importlib.invalidate_caches()` before re-checking. 5. Tests: the setup_sandbox pip recorder returns PEP 668 stderr and the test expects venv guidance with no `--user` retry. A pytest reproduces the refusal with `--dry-run --no-index`.
- **Tracked:** new.

<a id="h8"></a>
### H8. A failed dash_setup leaves already-installed packages in place (rollback deferred)

- **Gap:** GAPS.md J6 and ROADMAP WP-06 name rollback of a partial install, and WP-27 deferred it. `dash_setup.ado:152-205` installs one package at a time and exits r(198) at the first failure. Anything already installed stays, with no uninstall path and no list of what this run added.
- **Closable:** partly -- pip has no transactional install, and removing added packages can break other software, so a safe rollback is possible only in an environment dash owns.
- **Plan:** 1. Make a venv the recommended target (see H7), so rollback is deleting the venv. 2. For in-place installs, record the installed distributions first (`importlib.metadata`). On failure, list what was added and print the exact `pip uninstall` command. 3. Test with the setup_sandbox recorder: a pandas failure after bokeh installs reports bokeh as added.
- **Tracked:** GAPS.md J6 (rollback deferred by WP-27).

<a id="h10"></a>
### H10. Loading the renderer leaves a 1.2 MB .pyc in PLUS/py that `ado uninstall` does not remove

- **Gap:** `ado uninstall dash` should remove everything dash installed. Both load sites (`dash.ado:4203-4207`, `dash_setup.ado:615-619`) use `spec_from_file_location` plus `exec_module`, which caches bytecode. Probe: this wrote `plus/py/__pycache__/dash_render.cpython-313.pyc` (1,169,929 bytes). `stata.trk` lists only the files in `dash.pkg`, so the cache is left behind on uninstall.
- **Closable:** yes -- compiling without the cache costs 0.17 s.
- **Plan:** 1. Set `sys.dont_write_bytecode=True` around both loads and restore it afterwards, or `compile()` the source without caching. 2. Pytest: loading in a temp dir leaves no `__pycache__`. 3. Release gate: after `net install`, a build and `ado uninstall dash`, assert PLUS/py is empty.
- **Tracked:** new.

## I. Security and robustness

This area applies the project's security rules to saved pages and the served app. They cover hardened inputs, rate limits, logging, checks of environment variables, health checks and adversarial tests. Most of it is delivered and pinned by tests:
- AST whitelists for `function()` and hand-written `if`
- text sinks pinned on Bokeh 3.8.0 and 3.9.0
- a CSP on both pages
- UTF-8 gates
- path and scheme containment
- a bound on every build quantity
- a per-minute session limiter
- a loopback default
- an adversarial registry of 26 surfaces

Most of what remains is in the served app:
- no cap on concurrent sessions
- no credential, so a shared host is exposed
- `BOKEH_RESOURCES` is not checked, and a CDN value gives a blank page
- `/health` reports ok while pages fail

Outside the served app, a saved page silently carries the rows its `if`/`in` excludes. Logging, version pinning and the CSP are also weaker than the rules ask.

| ID | Gap | Sev | Closable | Effort |
|---|---|---|---|---|
| I1 | Environment variables that break the served app are not checked, and the checks that exist print where Stata cannot see them | S2 | yes | M |
| I2 | A saved page embeds every row of every used variable, including rows that `if`/`in` exclude, with no warning | S2 | partly | M |
| I3 | Served app: any local account can read the whole dataset, so loopback-only is not single-user on a shared host | S2 | partly | M |
| I4 | Served app: no cap on sessions open at once, and each session holds its own copy of the data | S2 | see F3 | - |
| I7 | Dependencies have no upper bound and no check at run time; text-sink safety is proven on Bokeh 3.8.0 and 3.9.0 only | S3 | see H4 | - |
| I9 | No automated check keeps secrets or private keys out of the repository | S3 | yes | S |
| I12 | The CSP keeps `script-src 'unsafe-inline'`, so it would not stop an injected script | S3 | partly | M |
| I14 | `saving()` character checks are too strict for twoway parity and too loose for the Windows opener | S3 | yes | S |

<a id="i1"></a>
### I1. Environment variables that break or weaken the served app are not verified, and the checks that exist print where Stata cannot see them (also reported as F12)

- **Gap:** Rule 15 asks for environment variables to be checked at start-up, and dash.sthlp:1409-1414 promises a start-up report on `BOKEH_ALLOW_WS_ORIGIN`. That is the only variable checked (dash_render.py:27378-27393).
  - Probe: with `BOKEH_RESOURCES=cdn`, the served page loads its scripts from cdn.bokeh.org. The page's own CSP (`script-src 'self'`) blocks them, so the dashboard is blank and the app says nothing.
  - Under `dash serve`, the child process inherits stdout and stderr (dash_render.py:27701). Even the documented origin report and its `*` warning therefore miss the Results window and the log (unmeasured in the GUI).
- **Closable:** yes. Bokeh reads `settings.resources` on every page (bokeh/server/tornado.py:619), so forcing `server` works.
- **Plan:**
  1. In the app's `__main__`, force `settings.resources` to `server` when it holds anything else, and say so. Also report the other set variables that change the page or its security: `BOKEH_SIGN_SESSIONS`, `BOKEH_SECRET_KEY`, `BOKEH_XSRF_COOKIES`, `BOKEH_DEV` and `BOKEH_BOKEHJS_PATH`.
  2. In `_dash_serve` (dash.ado), read `BOKEH_ALLOW_WS_ORIGIN` and `BOKEH_RESOURCES` through `: environment`, and echo the findings with `_dash_say`.
  3. Start the child with `stdout=PIPE, stderr=STDOUT`. Relay its lines from the main thread by polling, so that Break still reaches the `KeyboardInterrupt` handler.
  4. Tests:
     - a live-server test with `BOKEH_RESOURCES=cdn` asserting that every script src stays under `/static`
     - a cscript that runs `dash serve, timeout(1)` inside `log using` and asserts that the start line and the origin warning are in the log
     - an environment-variable surface in the adversarial matrix
- **Tracked:** new.

<a id="i2"></a>
### I2. Saved page embeds every row of every used variable, including rows the dashboard's if/in exclude, with no warning

- **Gap:** A Stata user expects a graph drawn with `if` to carry only the selected points, because a .gph keeps only its serset. dash.sthlp:880-884 warns about disclosure only for filters and `csv`.
  - The saved page's ColumnDataSource holds every row of each drawn variable, whatever `if`/`in` selects.
  - Probe: 2,000 rows with half selected gave a CDS of 2,000 rows. 10 rows with 5 selected put all 10 `mpg` values in the page.
  - The served app already sends only drawn rows, and the saved renderer already drops unused columns. The unused rows are what is still missing.
- **Closable:** partly. Rows that any layer, KPI, filter or `csv` can show must stay, and linked graphs share one source. So only rows outside every qualifier's selection can be removed.
- **Plan:**
  1. In `DashRenderer`, after `_dash_take_qual_columns`, compute for each shared source the union of all layer, graph and KPI qualifier masks. Use all rows when any user of that source has no qualifier or `csv` is on. Drop the other rows before building any ColumnDataSource.
  2. Before dropping, capture the whole-data values the renderer reads from `self.mapper.dataset`:
     - the mean of y for `lowess, adjust` (dash_render.py:8487-8491)
     - the _N behind `lpoly`'s grid cap (:8832-8834)

     Pass them as scalars to the mapper and to the saved page's filter recomputation.
  3. Give unlinked layers their own trimmed source where that is cheaper than a CDSView.
  4. Update dash.sthlp:880-884 and :1562: a saved page carries every observation of the drawn variables that any graph or card selects, and anyone can read it with view-source.
  5. Tests:
     - a pytest that parses docs_json and asserts that the CDS row count equals the union count
     - a regression test that `lowess adjust` and `lpoly n()` still match test/fixtures/qualified_stat_truth.json
     - a cscript comparing the CDS N with `count if` for each qualifier, and with twoway's serset N for a single-graph dashboard
- **Tracked:** new.

<a id="i3"></a>
### I3. Served app: any local account can read the whole dataset; loopback-only is not single-user on a shared host

- **Gap:** dash.sthlp:1387 says that loopback binding means "only this machine can reach it", and ROADMAP.md:3016-3017 (WP-20) targets a shared machine. The app has no credential.
  - Probe (probe_read.py): a `pull_session` to 127.0.0.1 with no Origin and no token received all 20 rows of `mpg`. Any local account can read the data while `dash serve` runs.
  - The app file and the spec/data JSON are written with the default umask (dash_render.py:25017). Where c(tmpdir) is a shared /tmp, another account can read the dataset from disk (unmeasured on Linux).
- **Closable:** partly. Stata's own tempfiles in c(tmpdir) are outside dash's control. Under `bokeh serve app.py` the script re-runs for every session, so it cannot create and announce its own secret, and the operator must supply one.
- **Plan:**
  1. In `__main__`, generate `secrets.token_urlsafe(32)`. In `make_document`, before the limiter and before any decoding, refuse a session that has neither `?token=` nor a matching cookie. Set the cookie as HttpOnly and SameSite=Strict through a Tornado transform, never in localStorage. Leave `/health` open.
  2. Under `bokeh serve`, read the secret from an environment variable the operator sets, and warn when it is unset.
  3. Keep the token out of argv. Open the browser through a 0600 temporary redirect file, and relay the URL with the token to the Stata log.
  4. Write the app and the spec/data JSON with `os.open(..., 0o600)`, and chmod the jsonio export. In dash.sthlp Server Mode, replace "only this machine" with "only holders of the link on this machine", and describe the shared-host case.
  5. Tests (no Stata counterpart):
     - live-server tests: a session without the token is refused, one with it is served, and `/health` still answers
     - a check that the app file's mode is 0600
     - adversarial entries for a forged or missing cookie
- **Tracked:** GAPS.md L10 records "no auth model" as the design. The multi-user and file-permission exposure is new.

**I4. Served app: no cap on sessions open at once, and each session holds its own decoded copy of the data** -- same gap as F3; see there.

**I7. Dependencies are unbounded and unverified at run time: text-sink safety is proven on Bokeh 3.8.0 and 3.9.0 only** -- same gap as H4; see there.

<a id="i9"></a>
### I9. No automated check keeps secrets or private keys out of the repository

- **Gap:** Rule 13 requires that no private key is ever committed. A grep of tracked files finds none today, but nothing enforces it. scripts/git-hooks/pre-push runs only `make check`, and test/ and scripts/ contain no gitleaks, detect-secrets, trufflehog or bandit step.
- **Closable:** yes. The existing pre-push hook makes a guard cheap to add.
- **Plan:**
  1. Add test/test_no_secrets.py. It greps the content of `git ls-files` for PEM headers, `AKIA...`, `ghp_...`, `sk-...` and generic secret assignments, with an allow-list for test fixtures.
  2. Add an optional bandit pass over dash_render.py and a generated app to `make check`, with the intentional eval (noqa S307) and subprocess sites baselined.
  3. Document both in AGENTS.md and the Makefile help.
  4. There is no Stata counterpart. Run in both pytest environments.
- **Tracked:** new.

<a id="i12"></a>
### I12. The CSP keeps script-src 'unsafe-inline', so it would not stop an injected script or handler

- **Gap:** dash.sthlp:1425-1432 presents the CSP as a protection. Yet `_DASH_CSP_STANDALONE` and `_DASH_CSP_SERVED` both allow `script-src 'unsafe-inline' 'unsafe-eval'` and `style-src 'unsafe-inline'` (dash_render.py:2095-2122). BUGS.md:1337 records that the WP-20 slider-title XSS handler ran because of `'unsafe-inline'`. Escaping is the only barrier, and it is pinned only on the verified Bokeh versions.
- **Closable:** partly. Three constraints remain:
  - `'unsafe-eval'` must stay, because CustomJS compiles callbacks with `new Function`.
  - `style-src` must keep `'unsafe-inline'`, because BokehJS creates `<style>` elements in shadow roots at run time.
  - The served page's inline scripts change with each session, so they need a nonce rather than hashes.
- **Plan:**
  1. Saved page: after `file_html` and the `layout(bs)` assembly, hash each executable inline `<script>`. Write `script-src 'sha256-...' 'unsafe-eval'` through `_dash_csp_meta`, and extend its character whitelist for base64 and quoted hashes.
  2. Served page: in `make_document`, set `doc.template_variables['nonce']`. Extend `_dash_served_template` to add nonce attributes, and put `'nonce-...'` in the meta policy. The header policy may keep `'unsafe-inline'`.
  3. Recheck in Chromium that CustomJS filters, hover, MathJax and the websocket run with no violation.
  4. Tests (no Stata counterpart):
     - test_csp.py asserts that script-src contains no `'unsafe-inline'` and that every inline script's hash is listed
     - a headless-browser test that an injected `<img onerror>` is blocked. The suite has no headless-browser harness yet, so this adds a dependency.
- **Tracked:** GAPS.md I3 (closed by WP-20 with `'unsafe-inline'` retained); BUGS.md:1337.

<a id="i14"></a>
### I14. saving() character checks are both too strict for twoway parity and too loose for the Windows opener

- **Gap:** twoway's `saving()` accepts any path the OS accepts, including `..` and `&` (unmeasured). Rule 16 asks for each check to match the hazard of the sink it guards.
  - Too strict: dash refuses a `..` segment (dash.ado:486-490). It also refuses `; & | < >` (:521, and `_dash_path_badchar` at dash_parse.mata:549), even when no browser or shell is involved. `_dash_open_page` quotes the path, so these characters would be literal anyway. As a result `saving("../out/d.html")` and `saving("R&D.html")` fail with r(198), and the help does not mention the character rule.
  - Too loose: `%` and `!` pass. cmd.exe expands `%NAME%` inside double quotes, so on Windows `start` could open a different file from the one written (unmeasured on Windows).
- **Closable:** yes.
- **Plan:**
  1. Keep only checks tied to a real sink: characters Stata expands (`` ` `` and `$`), the double quote, control characters and a leading `-`. Allow `..` and `; & | < >`.
  2. On Windows, refuse `%` (and `!`) in `_dash_open_page` only, with a message. Alternatively, open the page with Python's `os.startfile` and pass the path as data.
  3. Update dash.sthlp:786-788.
  4. Tests:
     - a cscript comparing dash's rc with twoway's rc for `saving("../x.gph")` and `saving("R&D.gph")` against their `.html` equivalents
     - `%` cases added to test_path_validation.cscript and to the SB-13..20 dry runs in test_serve_browser.cscript
- **Tracked:** GAPS.md E7 (closed by WP-08; the over-refusal and the Windows `%` case remain).

## J. Documentation, accessibility, browser and offline claims

This area covers the claims about where and how a dashboard can be opened (offline, in any modern browser, in any language through UTF-8), plus accessibility, export, and the package's own documentation and versioning. The offline claim holds. A saved page inlines BokehJS, loads nothing from outside the file and carries a `default-src 'none'` policy. `test_help_claims_1.py::TestTheSavedPageNeedsNoNetwork` and `test_csp.py` check this, and the default colours are colour-blind-safe. The rest falls short: KPI cards print European decimal-comma formats wrongly, browser support has only been tested in headless Chrome, and there is no accessibility work and no static or vector export. The interface text is English-only, and the distribution docs, examples and version metadata are incomplete or stale.

| ID | Gap | Sev | Closable | Effort |
|---|---|---|---|---|
| J1 | European decimal-comma formats (`%9,2f`, `%9,2fc`) and `set dp comma` are not honoured; a KPI card prints the raw double | S2 | yes | M |
| J2 | Stata graph-text markup (`{bf:}`, `{sup:}`, `{&alpha}`, ...) is drawn as literal text | S2 | see D3 | - |
| J3 | The served app cannot run on Python 3.8 or 3.9, though 3.8+ is the documented minimum | S2 | see K2 | - |
| J5 | A TeX delimiter pair in canvas text is typeset by MathJax; a saved page grows from 1.2 to 2.9 MB | S3 | see D3 | - |
| J7 | No static, vector or programmatic export for `graph export`, putdocx/putpdf or PDF reports | S3 | partly | L |
| J8 | Distribution docs incomplete: no author, README, install command, licence or minimum Stata version; 13 sections missing from Jump To | S3 | yes | S |
| J10 | The examples leave out 10 of the 40 plot types, csv, weights and server mode; feature_tour.do's header is stale | S3 | yes | S |
| J11 | The served page has no viewport tag | S3 | see E14 | - |

<a id="j1"></a>
### J1. European decimal-comma formats (`%9,2f`, `%9,2fc`) and `set dp comma` are not honoured; a KPI card silently prints the raw double

- **Gap:** The KPI `fmt()` option takes "a numeric Stata display format" (dash.sthlp), and `confirm numeric format` accepts `%9,2fc` (dash.ado:2299). In Stata, 21.297 under `%9,2f` shows as 21,30. `_parse_stata_numeric_fmt` (dash_render.py:853) matches only `%w.d(f|e)c?`, so `_dash_format_kpi_value` falls back to `str(value)`. Stata's correct text, which dash.ado:6331-6334 computes into `kpi['display']`, is overwritten at dash_render.py:23372-23376. A saved page shows `21.297297297297302`, the JavaScript recompute stays raw after a filter move, and `c(dp)` is never read.
- **Closable:** yes. Stata already computes the right text, and only the separator rule is missing on the Python and JavaScript side.
- **Plan:**
  1. Add `scripts/extract_format_locale_truth.do`: Stata `display` output for `%9,2f`, `%9,2fc`, `%-9,2f`, `%12,0fc` and `%9,2e`, and for `%9.2f`/`%9.2fc` under `set dp comma`, written to `test/fixtures/format_locale_truth.json`.
  2. Extend `_parse_stata_numeric_fmt` to accept `[.,]`. Route `_format_stata_numeric`, `_dash_format_kpi_value` and JS `dash_numfmt` (via `_kpi_js_number_format`) through one separator-swap rule. Until then, use `kpi['display']` on the first render.
  3. Serialise `c(dp)` into build_options in dash.ado, and apply it to `%w.df`/`%w.dfc` in both modes.
  4. Axis ticks: `NumeralTickFormatter(language='de')` or `CustomJSTickFormatter`.
  5. Tests: pytest against the fixture in both modes, a node test of the recompute, and a cscript comparing the KPI card text with `display`.
- **Tracked:** new

**J2. Stata graph-text markup (`{bf:}`, `{it:}`, `{sup:}`, `{sub:}`, `{&alpha}`, `{stSerif:}`, `{fontface}`) is drawn as literal text** -- same gap as D3; see there.

**J3. The served app (`dash serve`, `dash build server`) cannot run on Python 3.8 or 3.9, though 3.8+ is the documented and checked minimum** -- same gap as K2; see there.

**J5. A `$$..$$`, `\(..\)` or `\[..\]` pair in a title, note, axis title or tick label is typeset by MathJax, and a saved page grows from 1.2 to 2.9 MB** -- same gap as D3; see there.

<a id="j7"></a>
### J7. No static, vector or programmatic export: dash figures cannot reach `graph export`, putdocx/putpdf or PDF reports

- **Gap:** Stata users build papers with `graph export`, dyndoc `<<dd_graph>>` and putdocx/putpdf, and GAPS.md H1 names "a paper or a deck" as the use case for export. dash.sthlp:359-370 rules out a Stata graph, but the only image is the toolbar's screen-resolution PNG, saved by a manual click (dash.sthlp:1080-1087). The backend is canvas or webgl only (dash_render.py:21956), there is no `@media print` (tabs other than the active one do not print), and `dash` is not rclass (dash.ado:84), so the one-line form's temporary .html path is only displayed. A saved page has no frame-ancestors, so it can already be iframed in Quarto, Jupyter or dyndoc HTML; only the served app refuses framing.
- **Closable:** partly. Headless export (`bokeh.io.export_png`/`export_svg`) needs selenium plus a browser driver, which are outside dash's dependencies. The SVG backend is slow at the large n where dash switches to webgl. A Stata-drawn companion graph looks like twoway's figure, not dash's.
- **Plan:**
  1. Add a `twoway` companion option to dash.ado. It re-issues the plot specs without the dash-only options (`hover()`, filters, the repurposed `name()`) and with `name(..., replace)`, for `graph export`, dyndoc and putdocx. Document that without it, `graph export` does not see a dash figure.
  2. Add `output_backend(svg)` for figures under the webgl threshold.
  3. Make `dash` rclass, returning `r(filename)`. Document iframe embedding, and optionally add a frame-ancestors allow-list to the served launcher.
  4. Add a print stylesheet that expands every tab.
  5. Tests: a cscript that `dash ..., twoway` + `graph export x.svg` is byte-identical to `twoway <same>` + `graph export`, plus pytest for the SVG backend and `r(filename)`.
- **Tracked:** new (GAPS.md H1, closed by WP-21, delivered only PNG and CSV)

<a id="j8"></a>
### J8. Package documentation for distribution is incomplete: no author, README, install command, licence or minimum Stata version, and 13 help sections missing from Jump To

- **Gap:** The package is meant for net install or SSC (dash.pkg, stata.toc), and dash.sthlp:18's Jump To promises an "Author" section. The `*! Author:` lines say "(see dash.sthlp)" (dash.ado:28, dash_setup.ado:15, dash_render.py:57). But `{marker author}` (dash.sthlp:3154-3155) is titled "Also see" and names no one. There is no README, no LICENSE and no install command with a source. dash.pkg has no Author, Support, KW or Stata requirement. The 70 `version 16.0` statements imply Stata 16 support, which is never documented or tested. Jump To lists 16 of 30 titled sections; missing are, for example, Exporting, Tabs, Weights and Unsupported Stata twoway options.
- **Closable:** yes
- **Plan:**
  1. Add a real Author section (name, contact) under `{marker author}` ahead of Also see, in dash.sthlp and dash_setup.sthlp. Fix the three `*! Author:` lines, and add `d Author:`, `d Support:`, `d KW:` and `d Requires: Stata N` to dash.pkg.
  2. Add README.md (the install command with its `from()` URL, `dash_setup`, requirements, a quick example) and a LICENSE.
  3. Run the cert suite under Stata 16, 17 and 18, or raise `version` in dash.ado and dash_setup.ado to the oldest one tested. State the minimum in dash.sthlp's Dependencies and in dash.pkg.
  4. Add a viewerjumpto entry for every `{title:}`. Extend `test/test_help_claims_1.py` (:187) to assert that every title has a Jump To entry with an existing marker, and that the Author marker precedes a title naming an author.
- **Tracked:** new

<a id="j10"></a>
### J10. The examples leave out 10 of the 40 plot types, csv, weights and server mode, and feature_tour.do's header is stale

- **Gap:** feature_tour.do:4-12 says "A feature with no example is a feature nobody tries" and claims to cover what the other examples miss. With comments stripped, examples/*.do never uses bar, scatteri, pci, pcarrowi, pccapsym, pcbarrow, pcscatter, tsline, tsrline or fpfit, nor csv, a weight, `dash serve` or `dash build, server`. feature_tour.do names `dash serve` and pci/pcscatter only in its header comment (:9, :11), and counts "thirty-eight plot types" (:10) against forty (dash.sthlp:196-212). pytest still draws every type (e.g. test_every_plot_type_draws.py), so only the demonstrations are missing.
- **Closable:** yes
- **Plan:**
  1. Add `examples/plot_types_tour.do` covering bar, scatteri, pci, pcarrowi, pccapsym, pcbarrow and pcscatter; tsline and tsrline on `sysuse sp500` after `tsset`; fpfit; a weighted lfit; `dash build, csv`; and `dash build, saving(app.py) server`.
  2. Correct feature_tour.do's header (forty types, and what it actually covers).
  3. Add `test/test_examples_cover_features.py`: every plot type in the Plot types table, plus csv, weights and server, must appear in some example outside comments.
  4. Run the new example in Stata through `test_examples_run.cscript` and through `make gate` from an installed copy.
- **Tracked:** new (related GAPS.md F5, closed by WP-23, for the help's own examples)

**J11. The served page has no viewport tag; the help documents this as a limitation, but dash already rewrites that template and could add it** -- same gap as E14; see there.

## K. Engineering quality, testing, maintainability

This area should deliver a unit test for every function and end-to-end tests of every feature (AGENTS.md rules 4, 5, 14 and 15; ROADMAP WP-24..27). It also covers suites that run automatically under the Python Stata ships, user-facing logging, environment checks at start-up and a reproducible release gate. Most of the test side is delivered and is rigorous: about 16.7k pytest tests under two strict interpreters, 65 certification scripts (65/65 green on 24sep2026), name-checked function-to-test maps, mutation campaigns, and `make check`/`make gate` against a net-installed copy. The gaps are in how widely it runs, not how strict it is. Everything runs on one Apple-silicon Mac, one checkout path, one Stata (StataNow 19.5) and two pinned Python versions. Nothing runs the suites automatically, browser interactivity is tested only against node stand-ins, user logging is minimal, and the maintainer documents have drifted. The probes also found a real defect: the declared minimums (Python 3.8, bokeh 3.0) are false, because every render needs Bokeh 3.6+.

| ID | Gap | Sev | Closable | Effort |
|---|---|---|---|---|
| K1 | The certification runner is hard-coded to the maintainer's checkout, so `make cert` elsewhere tests another tree or fails | S2 | yes | S |
| K2 | The declared minimums (Python 3.8, bokeh 3.0) are false: every render needs Bokeh 3.6+, hence Python 3.10+, and the served app also crashes at import on 3.8/3.9 | S2 | yes | S |
| K3 | 15 of 22 Stata truth fixtures cannot be regenerated from the repository | S3 | yes | M |
| K4 | BOKEH_* environment variables change the output silently (rule 15) | S3 | yes | S |
| K5 | Dependencies are unpinned, the declared ranges are untested at both ends, and there is no lock or dev-requirements file | S3 | yes | M |
| K10 | Renderer structure: 27.7k lines in one file, about 2.4k lines of code written as strings, parallel Python and JS logic, and no linting | S3 | partly | L |
| K11 | The maintainer documents have drifted from the code | S3 | yes | S |

<a id="k1"></a>
### K1. The certification runner is hard-coded to the maintainer's checkout, so `make cert` elsewhere tests another tree or fails

- **Gap:** AGENTS.md rules 4-5 and ROADMAP WP-25 TR-25.1 say `make cert` tests the tree being committed and gates the change.
  - `test/run_all_cscripts.do:22-28` puts `/Users/billy/.../dash/` on the adopath and cds there. From a worktree it therefore tests the main checkout, while `scripts/cert_verdict.py` reads the worktree's list of registered scripts. The verdict can be green for a tree that was never tested. On any other machine the cd fails.
  - `arch -arm64` is hard-coded in `scripts/run_cert_suite.sh:18` and `scripts/stata_python_exec.sh`, which fails on an Intel Mac and on Linux.
  - Four `scripts/extract_*_truth.do` files hard-code the same path, and no test guards against absolute paths.
- **Closable:** yes. The fix is only how the path and the arch prefix are passed in.
- **Plan:**
  1. Make the repo root a required `args dashdir` of `run_all_cscripts.do`. It cannot default to `c(pwd)`, because Stata runs from a scratch directory and a do-file cannot learn its own path. `run_cert_suite.sh` passes `"$REPO"`.
  2. Use `arch -arm64` only when `uname -s` is Darwin and `uname -m` is arm64, in `run_cert_suite.sh`, `stata_python_exec.sh` and the Makefile help.
  3. Give `scripts/extract_*.do` the same root argument, and drop their StataJSON adopaths.
  4. Add a pytest guard that fails on any absolute `/Users/` path in test/*.do, *.cscript, scripts/*.do and scripts/*.sh.
  5. Copy the tree to a scratch directory, break its `dash.ado`, and run `make cert`: it must go red. A clean copy must go green.
- **Tracked:** new

<a id="k2"></a>
### K2. The declared minimums (Python 3.8, bokeh 3.0) are false: every render needs Bokeh 3.6+, hence Python 3.10+, and the served app also crashes at import on 3.8/3.9 (also reported as H1, J3)

- **Gap:** `dash_setup.sthlp:70`, `dash.pkg:17` and `dash_setup.ado:60,73,146` declare and enforce Python 3.8+ and bokeh>=3.0.
  - Every render, saved or served, imports `CustomJSTicker` through `_dash_finish_count_ticks` → `_dash_count_axes` (`dash_render.py:17217`, also `:16877`). That class exists only from Bokeh 3.6, and current Bokeh needs Python 3.10+.
  - A probe with it removed raises `RuntimeError: ... cannot import name 'CustomJSTicker'`. So an installed Bokeh 3.0-3.5 passes dash_setup, and then every dash command fails with r(7102).
  - The generated served app lacks `from __future__ import annotations` and has 55 annotations Python evaluates at import (PEP 585/604 syntax). It raises TypeError on 3.8 and 3.9.
  - The launcher ignores `_proc.returncode` (`:27706-27715`).
  - No test runs Python below 3.13 or Bokeh below 3.8.
- **Closable:** yes.
- **Plan:**
  1. Measure the real floor: in Python 3.10 venvs with bokeh 3.6.x and 3.7.x (pandas 2.0, numpy 1.23), run `test_every_plot_type_draws.py` and `test_server.py`.
  2. Raise the minimums everywhere they appear: `dash_setup.ado` (`min_bokeh`, `:60`/`:73`, `_dash_pymin` `:295`), `dash_setup.sthlp:70-80`, `dash.pkg:17`, and the `_dash_require_python` message in dash.ado. dash_setup should then report Bokeh 3.0-3.5 as below the minimum.
  3. Emit `from __future__ import annotations` as the first statement of the generated app. Add a pytest that ast-scans a generated app for annotations evaluated at import (`X | Y` or builtin generics).
  4. Check `_proc.returncode` in the launcher and raise a dash error naming the exit status. Add a pytest with an app that exits non-zero.
  5. Against Stata: `python set exec` a 3.10 venv at the floor, then run dash_setup, `dash scatter mpg weight, saving(a.html)` and `dash serve, timeout(1)`, and check /health. Downgrade to bokeh 3.5 and confirm dash_setup refuses it.
- **Tracked:** Closed in WP-28, BUGS.md "The declared minimums (Python 3.8, bokeh 3.0) are false: every render needs bokeh 3.6+, and the served app crashes at import on 3.8/3.9", commit b6f274f; residual deferred (WP-28): no interpreter or bokeh below the floor is run by any test (DISCOVERY Q8: no venv matrix); was: new

<a id="k3"></a>
### K3. 15 of 22 Stata truth fixtures cannot be regenerated from the repository

- **Gap:** ROADMAP WP-18/WP-24 hold tests to Stata's measured behaviour, so a truth must be re-measurable when Stata changes. GAPS.md L8 asked every fixture to say what it is.
  - Only 7 generators are committed: `scripts/extract_{abbrev,alias_spelling,axis,date,stat}_truth.do`, `extract_color_truth.py` and `extract_scheme_truth.py`.
  - 15 fixtures have no committed generator. Examples: `kpi_truth` names `/tmp/dash-kpi/p.do`, `kpi_pctile_truth` names a scratchpad probe, `rejected_options` has an absolute /Users/ corpus. `ci_band_style_truth` and `scheme_visual/truth.json` have none either.
  - Every truth was measured once, on StataNow 19.5.
- **Closable:** yes.
- **Plan:**
  1. Rewrite each probe named in a fixture's `_meta`/`_about`/`_source` as `scripts/extract_<name>.do` (or .py), taking the repo root as an argument (see K1).
  2. Add a `make truth` target that regenerates all of them through the console binary into a scratch directory.
  3. Add a pytest guard that every fixture's metadata names a committed generator and contains no absolute paths.
  4. Regenerate under StataNow 19.5 and diff against the committed fixtures. Then run under Stata 18.0 and 17 to find the version-dependent truths.
- **Tracked:** new

<a id="k4"></a>
### K4. BOKEH_* environment variables change the output silently (rule 15)

- **Gap:** AGENTS.md rule 15 says to verify environment variables at start-up. Of the BOKEH_* variables, dash reads only BOKEH_ALLOW_WS_ORIGIN (`dash_render.py:27372-27393`). The same one-scatter page is:
  - 1,228,258 bytes by default
  - 2,824,291 bytes with BOKEH_MINIFIED=false
  - 2,851,784 bytes with BOKEH_DEV=true
  - 1,230,645 bytes with BOKEH_SIMPLE_IDS=false

  No case raises a warning. The effect on served mode is unmeasured.
- **Closable:** yes.
- **Plan:**
  1. At renderer start-up, read MINIFIED, DEV, LOG_LEVEL, SIMPLE_IDS, RESOURCES and PY_LOG_LEVEL.
  2. Either force the values dash needs (e.g. `Resources(mode='inline', minified=True)`) or warn once, naming each variable and its effect.
  3. Add pytest cases with the variables monkeypatched, asserting page size and the warning. Add a certification case that runs `dash scatter` with one variable set.
- **Tracked:** new

<a id="k5"></a>
### K5. Dependencies are unpinned, the declared ranges are untested at both ends, and there is no lock or dev-requirements file

- **Gap:** `dash.pkg:17` promises that `bokeh>=3.0, numpy>=1.23, pandas>=2.0` work. Rule 15 and reproducibility apply too: the same do-file should give the same dashboard.
  - `dash_setup.ado:145-170` installs `pkg>=min` with no upper bound, and only when the package is missing.
  - Only two baselines are tested (`conftest.py:207-212`: Python 3.13/3.14, bokeh 3.8/3.9).
  - The floor is false (K2). The ceiling is unmeasured: a fresh dash_setup on Stata's Python 3.13 would install Bokeh 3.10.0.
  - The renderer replaces `bokeh.server.util.match_host` (`:2296-2300`) and extends `bokeh.core.templates.FILE` (`:2189`), so a future Bokeh can break it.
  - There is no requirements, constraints or lock file. pytest-xdist, node and Chrome are needed but declared nowhere.
- **Closable:** yes.
- **Plan:**
  1. Add a constraints file with tested ceilings (e.g. `bokeh<3.10`), used by dash_setup's pip call (`-c`) and shipped in dash.pkg. dash_setup warns when an installed version is above the ceiling.
  2. Add a nox/tox matrix (`make matrix`) over the floors (after K2: Python 3.10, bokeh 3.6, pandas 2.0, numpy 1.23) and the newest versions (bokeh 3.10, pandas 3.x, numpy 2.x). Raise the floors where they fail, and update `dash_setup.ado` and dash.pkg to match.
  3. Add requirements-dev.txt (pytest, pytest-xdist, packaging, scipy), and document node and Chrome in the Makefile help.
  4. Run `dash_setup` into fresh venvs at the floor and at the ceiling, `python set exec` each, and re-run `make gate` and `make cert`.
- **Tracked:** new

<a id="k10"></a>
### K10. Renderer structure: 27.7k lines in one file, about 2.4k lines of code written as strings, parallel Python and JS logic, and no linting

- **Gap:** AGENTS.md rules 1, 4 and 13 ask for code that can be verified and scrubbed, and the audit brief raised the duplication between the saved and served paths.
  - `dash_render.py` is 27,715 lines in 7 classes; GlyphMapper alone spans 5351-14979.
  - ServerAppBuilder (24207-27483) holds about 2,379 lines of Python as string literals. The app it generates is 20,353 lines (975 KB) even for 10 rows.
  - The served callbacks are reimplemented in JS for the saved page (`_FILTER_JS`, 792 lines, plus `_DASH_CSV_SAVED_JS`).
  - `_gopts_of` is defined four times (22580, 22842, 23948, and as a string at 27134).
  - No linter runs in `make check`. pyflakes reports 47 findings on `dash_render.py` and 54 on the generated app.
- **Closable:** partly. The saved page must recompute in the browser with no server and no Python, so the JS copy of the filter, KPI and histogram/density logic cannot be removed (Pyodide would add megabytes to every offline page). Only shared tests can keep the two copies in step.
- **Plan:**
  1. Move the template's string-literal code into a real module, `dash_app_template.py`, shipped in dash.pkg and copied into the app with `inspect.getsource`.
  2. Split `dash_render.py` by class into `dash_*.py` modules, so net install places them together in PLUS/d/.
  3. Add `ruff check` (pyflakes rules) over `dash_render.py` and a freshly generated app to `make check`, and fix the current findings.
  4. Build one case table (statistic, data, Stata's value) that drives both the node harness and the Python functions.
- **Tracked:** new

<a id="k11"></a>
### K11. The maintainer documents have drifted from the code

- **Gap:** GAPS.md M1 (closed by WP-23) required the tracking documents to describe reality, held by `test/test_tracking_documents.py`.
  - `GAPS.md:42-76` still presents eight closed gaps as current.
  - `ROADMAP.md:4194` says "19 remain open, all S3", while BUGS.md has 4 open.
  - 62 closed BUGS.md entries have Resolutions that begin "Not fixed".
  - `test/test_geometry_visual.md` adds a stale StataJSON adopath (`:15`). It also claims a file:// page will not load under the CSP (`:30`); a probe loaded one with 3 canvases and no errors.
  - `test_tracking_documents.py` checks none of these.
- **Closable:** yes.
- **Plan:**
  1. Replace GAPS.md's executive summary with a status table (closed / deferred / open) generated from the section headings.
  2. Add an S3-batch section to ROADMAP after WP-27 with the current open count.
  3. Strip the superseded "Not fixed yet" wording from closed BUGS.md resolutions. Add rules to `test_tracking_documents.py`: no [x] entry's Resolution starts with "Not fixed", and the counts in GAPS.md and ROADMAP.md match BUGS.md.
  4. Retire `test_geometry_visual.md` in favour of `test_responsive_layout.py`, or update it.
- **Tracked:** new (successor to GAPS.md M1)

## X. Cross-cutting (completeness critic)

This area collects gaps that no single feature area covered: dropdown filters, `colorvar()` compared with Stata 18, preview temp files, how the renderer's notes reach the user, where schemes are looked up, managing the registry, and keeping dash's names apart from everyone else's. There are seven gaps: two S1, three S2 and two S3. All seven can be closed at least in part. None is tracked in BUGS.md or GAPS.md.

| ID | Gap | Sev | Closable | Effort |
|---|---|---|---|---|
| X1 | Dropdown filters rewrite string codes that look like numbers, drop the categories "None", "nan" and "NaT", and on the saved page cannot select small numbers | S1 | yes | S |
| X2 | `colorvar()`: `colordiscrete` with `colorcuts()` is read as intervals, and cuts below the minimum are kept. twoway's `colorlevels()`, `colorvarminmax`, `colorrule()` and z-axis options are not drawn, and its default z-tick levels are replaced (documented) by a continuous map | S1 | partly | M |
| X3 | The one-line form without `saving()` leaves its preview page, a copy of the graph's data, in the temp directory after the command ends | S2 | partly | S |
| X4 | The renderer's notes are raw Python warnings: a warnings filter silences them or turns them into a failed render, and otherwise they print internal paths and source lines | S2 | yes | S |
| X5 | Third-party and personal schemes are not found where Stata finds them, or under Stata's own file name `scheme-NAME.scheme` | S2 | yes | M |
| X7 | dash puts unprefixed functions in the global Mata namespace and drops same-named functions of other packages, and leaves its state in the user's Python session | S3 | yes | S |

<a id="x1"></a>
### X1. Dropdown filters rewrite string codes that look like numbers, drop the categories "None", "nan" and "NaT", and on the saved page cannot select small numbers

- **Gap:** dash.sthlp:1109-1116 says `type(dropdown)` lists the variable's unique values and filters every graph, and that the saved page and the served app filter the same way. They do not.
  - `_dash_option_value` (dash_render.py:17413-17438) turns any value that reads as a whole number into integer text, string values included. So '01', '1.0' and ' 2' all become '1' or '2'.
  - `_dash_dropdown_values` (1806-1812) drops the categories 'nan', 'None' and 'NaT'.
  - On the saved page, the `String(col[i]) !== val` test (14131-14138) then keeps no row for '1' or '2'. The served mask (17669-17675) matches '01', '01' and '1.0' to '1'.
  - Python writes `5e-05` where JavaScript writes `0.00005`. So on the saved page a numeric value in [1e-6, 1e-4), or at 1e21 or above, selects nothing.
  - No note is printed. `colorvar()` also draws the string 'nan' as missing (6527).
- **Closable:** yes. Both sides of the comparison are dash's own code.
- **Plan:**
  1. Keep a string column's value as its exact text in `_dash_option_value`. Normalise only numeric values, using ECMAScript `Number::toString` rules, or compare numbers as numbers in both modes.
  2. Remove the 'nan'/'None'/'NaT' exclusion from `_dash_dropdown_values` and from the `colorvar` string path. Decide missingness from the dtype and None/NaN only, with `""` as Stata's missing string.
  3. Make `_DASH_FILTER_MASK_JS` and `_dash_dropdown_mask` one rule. Pin it with a pytest that runs both (node and pandas) on the same columns and compares the masks.
  4. Write a cscript with `str fips = string(_n,"%02.0f")`, the values '1', '1.0', 'None' and 'nan', and a double holding 5e-05. For each option it compares the rows kept (served, and saved via node or headless Chrome) with `count if fips == "<text>"`.
- **Tracked:** Closed in WP-28, BUGS.md "A dropdown rewrites string codes to numbers, drops the categories nan None and NaT, and cannot select small numbers on the saved page", commit cdb3a3d; was: new

<a id="x2"></a>
### X2. `colorvar()`: `colordiscrete` with `colorcuts()` is read as intervals, and cuts below the minimum are kept. twoway's `colorlevels()`, `colorvarminmax`, `colorrule()` and z-axis options are not drawn, and its default z-tick levels are replaced (documented) by a continuous map

- **Gap:** dash.sthlp:2491-2505 says `colorvar()`, `colordiscrete` and `colorcuts()` work as in Stata 18. Stata's colorvar_options.sthlp:111-133 says that under `colordiscrete` the cuts are the levels, every other value is drawn gray with missing, and cuts below the minimum are ignored.
  - dash_render.py:6457-6479 takes the interval path whatever `colordiscrete` says (6376). `colorvar(rep78) colordiscrete colorcuts(2 4)` gives ≤2 / 2–4 / >4, so rep78 = 1, 3 and 5 are coloured as ranges where twoway draws them gray.
  - `colorcuts(0 2 4)` keeps an empty '≤0' level. No note is printed for either case.
  - `colorlevels()`, `colorrule()`, `colorstart()`, `colorend()` and `colorvarminmax` are only named in a note (dash.sthlp:2501-2503). dash.ado declares no `zlabel()`, `ztitle()` or `zscale()`.
  - The unbinned default is a continuous 256-colour map (6424-6446), where twoway bins at the z axis's ticks. This is documented (dash.sthlp:2503-2507), so it is a divergence, not a silent error.
- **Closable:** partly.
  - The explicit forms can be matched exactly: `colordiscrete` with `colorcuts()`, `colorlevels(#)`, `colorvarminmax`, and dropping cuts below the minimum.
  - twoway's default levels depend on Stata's z-axis tick choice, which dash only approximates (B27's tick model). They also depend on `colorrule(hue)`'s interpolation, which has not been measured.
  - Replacing the continuous default reverses a documented design choice, unless the new behaviour goes behind an option.
- **Plan:**
  1. In the `colorvar` mapper (dash_render.py ~6376-6560), under `colordiscrete` with `colorcuts()`, make each cut a level and draw other values gray with missing. Drop cuts below the column minimum, and use the minimum if all cuts are below it.
  2. Add `colorlevels(#)` (#-1 equal cuts, and discrete levels under `colordiscrete`) and `colorvarminmax`, alongside `colornlevels()`.
  3. Optionally, either behind a switch or as the new default, bin at the z ticks from dash's tick model with `colorrule(hue)`. Keep `colpalette()` as the continuous option and update dash.sthlp:2503-2507.
  4. Declare `zlabel()`, `ztitle()` and `zscale()` and draw them on the colour key.
  5. On auto and nlsw88, run `twoway scatter` over a grid of these options and `graph export .svg`. Save each marker's fill group as a fixture, and have pytest compare dash's factor per observation and its number of levels.
- **Tracked:** Closed in WP-28, BUGS.md "colordiscrete with colorcuts() is read as intervals, cuts below the minimum are kept, and colorlevels(), colorvarminmax and the z options are not drawn", commit 7acdcb1; residual deferred (WP-28): colorrule(), colorstart() and colorend() are still only named in the note; the continuous default is kept by decision (DISCOVERY Q5); was: new

<a id="x3"></a>
### X3. The one-line form without `saving()` leaves its preview page, a copy of the graph's data, in the temp directory after the command ends

- **Gap:** dash.sthlp:824-829 says the one-line form without `saving()` or `name()` writes a temporary file and says where. AGENTS.md rules 1 and 13 already led to `dash serve`'s app using Stata-erased tempfile names (dash.ado:7401-7412, which counted 142 orphans and 18 MB). But dash.ado:5812-5813 writes `` "`saving_path_tmp'.html" ``, a name Stata never registered, and nothing erases it.
  - A read-only listing found 66 orphaned `St*.html` files of about 1.2 MB each in `c(tmpdir)`. Each one embeds every row of every variable the graph uses.
  - macOS's temp directory is private to the user (0700) and purged by the OS. Linux's default /tmp is shared.
- **Closable:** partly. The browser may reload the preview after the command returns, and ado code has no hook for Stata exiting. So the last preview can only be pruned later: by the next `dash`, by `dash clear`, or by a Python atexit handler, and whether atexit runs at Stata exit has not been measured.
- **Plan:**
  1. Write previews into a per-user directory under `c(tmpdir)` (`dash-previews-<user>`), created from Python with mode 0700 and files with mode 0600.
  2. Record each preview path in a global. Erase older previews on the next preview (keeping the last N), on `dash clear`, and from a Python atexit handler.
  3. Document in dash.sthlp where previews go and when they are removed.
  4. Write a cscript under `$dash_nobrowser` that makes three previews, runs `dash clear`, and asserts no preview or `St*.html` remains. A pytest checks the permission bits. Measure the atexit path once across a Stata exit.
- **Tracked:** new

<a id="x4"></a>
### X4. The renderer's notes are raw Python warnings: a warnings filter silences them or turns them into a failed render, and otherwise they print internal paths and source lines

- **Gap:** dash.sthlp:516-520, 543-548, 1135-1137 and 2825-2832, and ROADMAP WP-13 ("honour or report, never silence"), promise one clean note for anything dash cannot honour.
  - Every renderer note is `warnings.warn(..., UserWarning)`, run in the user's own Python session via `runpy.run_path` (dash.ado:422-431). dash sets no warnings filter of its own around `main()` (dash_render.py:27555ff).
  - Probe with default filters: `mcolor(boguscolour)` prints `.../dash_render.py:6130: UserWarning: dash: ...` and a source line.
  - Under `filterwarnings('ignore')` every note disappears and rc stays 0.
  - Under `simplefilter('error', UserWarning)` the render fails with r(7102).
  - test/run_all_cscripts.log holds 21 such Python-format lines, for example at 144860-144862.
- **Closable:** yes. The fix is a wrapper inside dash's own entry points.
- **Plan:**
  1. In `main()` and the generated app's `make_document`, render inside `warnings.catch_warnings(record=True)` with `simplefilter('always', UserWarning)`. The session's filters then neither hide nor escalate dash's notes, and `catch_warnings` restores the user's filters afterwards.
  2. Print each recorded `dash:` note through `sfi.SFIToolkit.displayln` as Stata text, de-duplicated as `_DASH_NOTED` does, falling back to stderr outside Stata. Re-emit other libraries' warnings unchanged.
  3. Add pytests that run `main()` after `filterwarnings('ignore')` and after `simplefilter('error')`. Each asserts the note text appears, rc is 0, and neither `UserWarning` nor `dash_render.py:` is printed.
  4. Write a cscript that sets `warnings.simplefilter("error")`, runs `dash scatter ..., mcolor(bogus)`, and asserts rc 0 and the note. Compare the wording with twoway's "named style ... not found" note.
- **Tracked:** new

<a id="x5"></a>
### X5. Third-party and personal schemes are not found where Stata finds them, or under Stata's own file name `scheme-NAME.scheme`

- **Gap:** dash.sthlp:2644-2647 says dash follows `c(scheme)`, and 2796-2810 says a scheme of your own works from the working directory. To match twoway, `scheme(NAME)` would also find `scheme-NAME.scheme` on the ado-path (blindschemes, schemepack, cleanplots, grstyle's `_GRSTYLE_`).
  - dash.ado:2264-2292 and `SchemeParser._resolve_path` (dash_render.py:3807-3811) try only `NAME.scheme` in the working directory and the package's own schemes/.
  - A scheme on the ado-path is therefore refused with r(198) when named. When it is inherited through `c(scheme)`, s2color is drawn with a note.
  - `scheme-NAME.scheme` is never tried, so the help's own remedy of copying the installed file into the working directory also fails. Only `scheme(scheme-plotplain.scheme)`, or renaming the file, works.
  - Refusing PLUS directories is documented as deliberate (2806-2809).
- **Closable:** yes. This gap is only about finding the file. How faithfully a found scheme is drawn is the rest of D78 and D80.
- **Plan:**
  1. Resolve NAME as `set scheme` does: the working directory (`NAME.scheme`, then `scheme-NAME.scheme`), then `findfile scheme-NAME.scheme` on the ado-path. Pass the absolute path in the spec.
  2. Extend `_resolve_path`'s allowlist to the ado-path directories Stata reports, read-only, size-capped, with realpath checks and no symlink escape. Resolve `#include` by the same search.
  3. Apply the same lookup to an inherited `c(scheme)` and update dash.sthlp:2796-2832.
  4. Write a cscript that puts `scheme-dashtest.scheme` in PERSONAL with distinctive colours, runs `set scheme dashtest` and `twoway scatter`, and exports `.svg`. It asserts that dash's colours equal the SVG's for both `scheme(dashtest)` and the inherited scheme. pytest keeps the traversal, symlink and size guards.
- **Tracked:** new

<a id="x7"></a>
### X7. dash puts unprefixed functions in the global Mata namespace and drops same-named functions of other packages, and leaves its state in the user's Python session

- **Gap:** AGENTS.md rules 1 and 13, and the usual package convention, say dash's names should not collide with or change another package's or the user's.
  - Mata: dash_parse.mata defines `_json_escape` (:255), `_is_utf8` (:430), `_expand_plottype_str` (:931) and `_first_comma_pos` (:1710) globally.
  - If a function with one of these names is already loaded, `run` stops with r(3000) (dash.ado:64-82). The repair step then drops those four names and reloads (dash.ado:293-299), deleting the other package's function for the rest of the session.
  - Python: dash.ado:422-431 overwrites `sys.argv` and keeps the renderer's whole namespace (`_dash_render_ns`) in `__main__`. Lines 4196-4210 also leave eight `_dash_*` temporaries there.
- **Closable:** yes. The fix is renames and cleanup within dash's own code.
- **Plan:**
  1. Rename the four functions to `_dash_*`, and update dash.ado's `_needed` list (232-244), the repair loop (296-299) and test/program_coverage_map.py.
  2. Have the repair step drop only `_dash_*()`.
  3. Run the renderer and the export through one helper that saves and restores `sys.argv`, does not keep the `run_path` namespace, and deletes its temporaries.
  4. Write a cscript that defines its own `_json_escape()` and `_is_utf8()`, runs `dash scatter`, and asserts dash works and the user's functions are unchanged (`mata describe` plus a call). Add a check that `sys.argv` and `dir()` of `__main__` are the same before and after a render.
- **Tracked:** new

## Appendix

### Findings merged as duplicates

| Entry | Same gap as |
|---|---|
| A7 | B12 |
| A10 | C7 |
| B8 | E3 |
| B9 | D2 |
| B13 | D3 |
| B29 | D17 |
| C1 | A9 |
| C3 | A4 |
| C5 | A6 |
| C8 | A11 |
| C9 | A4 |
| C10 | A13 |
| C11 | A15 |
| C13 | A9 |
| C15 | A12 |
| D6 | B11 |
| E4 | C4 |
| F7 | E14 |
| F8 | E14 |
| F12 | I1 |
| F14 | E14 |
| G11 | E3 |
| G13 | E7 |
| G15 | B12 |
| H1 | K2 |
| H2 | F4 |
| I4 | F3 |
| I7 | H4 |
| J2 | D3 |
| J3 | K2 |
| J5 | D3 |
| J11 | E14 |

### Findings refuted in verification

- **F: No non-blocking serve: one served dashboard per Stata session, no stop command, no idle shutdown** -- Nothing promises a non-blocking dash serve, a stop command or an idle shutdown. dash.sthlp:711-715 and 1353-1356 ('Blocking behavior') document blocking as the design. dash.sthlp:1358-1370 and 1627 ('Write server app to file (non-blocking)') give `dash build, server` plus `python app.py` as the non-blocking route, which already allows several dashboards at once, on different --port values. timeout() is documented as 'stop the server after # minutes' (dash.sthlp:737-738), not idle time, and the code matches (27400-27402). ROADMAP.md, .ultraplan/PRD.md, REMAINING.md and phases/*.md hold no request for a background serve (grep for non-blocking, background, 'serve stop' and idle finds only the help's own non-blocking route). Stata commands block until they finish, so a blocking command is what a Stata user expects. The part that really hurts, not being able to stop it from the GUI, is gap 1, and the orphan risk is gap 2. This is a feature request, not a gap between intent and delivery.
