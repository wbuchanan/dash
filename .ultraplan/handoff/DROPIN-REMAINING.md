# dash vs `twoway`: what remains (verified at HEAD 357c368)

## 1. Verdict

dash is not yet a drop-in replacement, but most of the structural work is finished. It parses the full `twoway` syntax and draws 40 plot types. The saved page and the served app now draw from one shared code path. Most of the blockers REMAINING.md listed are verified fixed.

Five kinds of gap remain:

- **Silently wrong output in common use.** Line plots are joined in x order rather than data order. The lpoly bandwidth and the lpolyci band are wrong. `function` evaluates `^` from the right. Computations on a date variable run in epoch milliseconds. `by()` panels get independent scales. `axis(2)` options land on the first axis.
- **Options accepted but not drawn.** About 80 accepted `twoway` options are not drawn, including `horizontal`, `connect()`, `text()`, the `t*` options on tsline, named styles and multi-y stylelists. Most are named in a note, but a few are dropped with no note: region sub-options, rbar `barwidth()`, `hover()`-only variables, and date `format()`.
- **Default look.** The default appearance differs from Stata's schemes on every graph.
- **Security and lifecycle of the served app.** It has no credential, can be orphaned, and leaves files world-readable.
- **Installation.** Installs on externally-managed Pythons (PEP 668) fail; Windows, Linux and Stata versions before 19 have never been tested.

## 2. What REMAINING.md said vs now

- **Tally (hand-counted, approximate):** about 537 REMAINING.md items.
  - About 333 are resolved: about 318 DONE and 15 OBSOLETE.
  - About 204 are still OPEN or PARTIAL. Many of these repeat each other across REMAINING's §2, S05/S07/S09 and 05-04 sections.
  - GAPS2.md, TWOWAY_COVERAGE_AUDIT.md and a critic pass (CRIT) added more open items. Everything is merged into the task list below.
- **Headline blockers now resolved:**
  - Per-plot `if` is now honoured by every computed layer (REM-HL-5, §5, 06-06).
  - The standalone/served parity guard now covers every plot type. Served `function`, `pci`, `tsrline` and the fpfitci band draw, and every type draws under `by()` (HL-4, §4, B1, 15-03).
  - `net install` now puts schemes where the renderer finds them, and a real net-install release gate exists (§1, S02, S16-06).
  - An unknown `scheme()` is now an error, validated in Stata (§3, S11).
  - Rate-limiter eviction is fixed, and caps now exist for `by()` groups, tabs and dropdown options (§6).
  - Dates no longer crash: 24 of 35 plot types used to abort on a date x. Dates are now supported in server mode (08-04, 08-05).
  - The axis-label grammar and the secondary axis now work in the served app (09-02, 09-07).
  - Canvas and HTML escaping is fixed (09-07).
  - Server dispatch now runs through the shared GlyphMapper (15-03).
  - Scheme text sizes and colours reach both modes (11-04).

## 3. Prioritized task list

### P0: wrong output, security, install, saved/served divergence

1. **Line-type plots are joined in x order, not data order; `sort(varlist)` is ignored.** line, connected, area, rline, rarea and rconnected always sort by x, so `twoway line y x` without `sort` draws a different picture, with no note. Tests pin the x order (see Decisions). Effort M. Sources: GAPS2-A1-a, AUDIT-08, REM-§2-S06-sort, REM-S06-b, GAPS2-A4-o, GAPS2-B12-e, AUDIT-10, GAPS2-G15-b, GAPS2-A1-c. [Closed in WP-29: BUGS.md "line, connected, area, rline, rarea and rconnected are joined in x order, never in the data's order as twoway joins them, and sort(varlist) is ignored", commit b0d170d; residuals: P2.30]
2. **`by()` panels use independent scales by default.** A plain `by(foreign)` autoranges each panel separately; axes are shared only when ticks or a range are given explicitly. `by(, yrescale)` is named in the note and ignored. Effort M. Sources: GAPS2-B4-a, GAPS2-B4-b. [Closed in WP-29: BUGS.md "by() panels are drawn on independent scales by default, and by(, yrescale) is named and ignored", commit ab53f25; residuals: none]
3. **Unlabelled variables get blank axis titles, legend keys named after the plot type, and blank tooltip labels.** `twoway` uses the variable name. The test data helper gives every variable a label, which hides this. Effort S. Sources: REM-08-05-C3b, REM-08-05-C3a, REM-08-05-M3. [Closed in WP-29: BUGS.md "An unlabelled variable gets a blank axis title, a legend key named after the plot type and a blank tooltip label, where twoway uses the variable name", commit 8d3593e; residuals: none]
4. **`xtitle(, size())` or `ytitle(, color())` with no text deletes the default title.** For example, `ytitle(, size(large))` removes the y title in both modes. Effort S. Sources: CRIT-01. [Closed in WP-29: BUGS.md "A title sub-option with no text, such as ytitle(, size(large)), deletes the default axis title", commit e908b78; residuals: none]
5. **`axis(2)` on `ylabel`/`yscale`/`yline`/`xtick` is applied to axis 1.** `yscale(log axis(2))` logs the primary axis, and the note names only `axis(2)`. `ytitle(, axis(2))` is already routed correctly. Effort M. Sources: REM-09-02-AXIS-N, GAPS2-B15-a, AUDIT-27, GAPS2-B22-c. [Closed in WP-29: BUGS.md "axis(2) on ylabel(), yscale(), yline() and xtick() is applied to the first axis", commit 3208b2b; residuals: none]
6. **`function` evaluates `^` right to left and accepts `pi` and `e`.** `2^3^x` at x=2 draws 512 where Stata gives 64. `pi*x` draws, where `twoway` refuses it r(111). Effort S. Sources: GAPS2-A6-d, GAPS2-C5-g, GAPS2-A6-c. [Closed in WP-29: BUGS.md "function evaluates ^ from the right and accepts pi and e, which twoway refuses", commit 96aa267; residuals: P2.31]
7. **The lpoly/lpolyci default bandwidth is wrong.** It ignores `kernel()` and `degree()` (10–90% too small, e.g. biweight degree 2: 63.8 vs 302.5). Even the Epanechnikov degree 0/1 default is off by −22% to +14%, and 185 vs 77 on a 7-observation sample (see Decisions). Effort M. Sources: GAPS2-A9-a, GAPS2-A9-b, GAPS2-C1, GAPS2-C13, AUDIT-24, GAPS2-C12-e. [Closed in WP-29: BUGS.md "The lpoly and lpolyci default bandwidth ignores kernel() and degree() and misses Stata's rule of thumb", commit 758cf59; residuals: P2.36]
8. **Computed layers on a date variable run in milliseconds.** histogram/kdensity densities are per ms, and `width()`, `start()` and `bwidth()` are read as ms. lpoly/lpolyci draw nothing. histogram/kdensity put the date axis on Y. Effort M. Sources: REM-08-05-C6d, REM-08-04-C2, REM-08-05-C6c, REM-08-04-C3a, REM-08-04-C12. [Closed in WP-29: BUGS.md "Computed layers on a date variable run in epoch milliseconds, so densities are per ms, width(), start() and bwidth() are read as ms, and lpoly draws nothing", commit cd210ea; residuals: P2.32]
9. **The lpolyci band is a bootstrap percentile band, not Stata's analytic band.** Band width is 0.51–1.33× Stata's, and edges are off by up to 2.25 mpg. `pwidth()` and `var()` are ignored. It costs about 100× lpoly. Effort L. Sources: AUDIT-23, GAPS2-A10-a, GAPS2-C7-a, GAPS2-C7-b, GAPS2-A10-b, GAPS2-C7-c, GAPS2-C7-e. [Closed in WP-29: BUGS.md "The lpolyci band is a bootstrap percentile band, not Stata's analytic band, and pwidth() and var() are ignored", commit e32be3a; residuals: P2.36]
10. **A variable named only in `hover()` is never exported.** Both routes and both modes drop it silently, with rc 0 and no note. Two cscripts (DL-03e, AL-19) pin the defect and must change. Effort S. Sources: REM-09-07-HOVER-EXPORT, GAPS2-G16-res, REM-09-07-HOVER-TEST. [Closed in WP-29: BUGS.md "A variable named only in hover() is never exported, so its tooltip field is empty in both modes", commit 735c534; residuals: P2.33]
11. **The saved page embeds rows that `if`/`in` exclude.** Every row of each drawn variable is in the HTML source, and the help does not disclose it. Effort M. Sources: GAPS2-I2-a, GAPS2-I2-b. [Closed in WP-29: BUGS.md "The saved page embeds every row of each drawn variable, including rows that if and in exclude", commit cbeef4e; residuals: P2.39]
12. **The served app has no credential, and its files are world-readable.** Any local account can open a session and read the data. The app and the spec/data JSON are written 0644; on macOS the per-user 0700 temp directory mitigates this, and the shared-/tmp case on Linux is unmeasured. The help's "only this machine" wording understates this (see Decisions). Effort M. Sources: GAPS2-I3-a, GAPS2-I3-b, GAPS2-I3-c, AUDIT-87. [Closed in WP-29: BUGS.md "The served app has no credential, so any local account can open a session and read the data", commit 7f5c8f5; BUGS.md "The served app, spec and data files are written with the default umask, readable by other accounts where the temp directory is shared", commit fd51038; residuals: P2.35, P2.38]
13. **Server lifecycle.**
    - Killing Stata leaves the server running, holding its port and the data.
    - Temp files survive a crash.
    - Break in GUI Stata cannot stop `dash serve`: sfi `pollstd` is never called.
    - The messages tell GUI users to press Ctrl+C.

    Effort M. Sources: GAPS2-F2a, GAPS2-F2b, GAPS2-F4, GAPS2-H2a, GAPS2-F9c, GAPS2-H2b. [Closed in WP-29: BUGS.md "The served app outlives a killed Stata, its files survive a crash, and Break cannot stop dash serve", commits ece0752 (F2), c595259 (F4); residuals: P2.35]
14. **One-line preview pages are never deleted and are 0644.** 39 orphans of about 1.2 MB each were observed. Nothing prunes them and nothing documents them. Effort S. Sources: GAPS2-X3-a, GAPS2-X3-b, GAPS2-X3-c. [Closed in WP-29: BUGS.md "One-line preview pages are never deleted and are written 0644, each a copy of the graph's data", commit fd51038; residuals: P2.35]
15. **After a filter move, the saved page registers per-plot rows rather than the intersection.** In a linked `by()` graph, or a linked graph with its own graph-level qualifier, a layer with its own `if` then draws rows outside its panel. The served app is correct. Effort S. Sources: REM-06-06-C7. [Closed in WP-29: BUGS.md "After a filter move the saved page registers a layer's own if rows, not their intersection with its panel or graph qualifier", commit 3cff164; residuals: none]
16. **The `colorvar()` range ignores qualifiers.** On the saved page it spans every row under a per-plot `if`. In both modes it ignores a linked graph's graph-level qualifier. Which colour key `twoway` draws under `by()` is UNCLEAR (not measured). Effort S. Sources: REM-06-06-C8b, REM-06-06-C8b-link. [Closed in WP-29: BUGS.md "The colorvar() colour range ignores a per-plot if on the saved page and a linked graph's qualifier in both modes", commit 85dc7d2; residuals: P2.34]
17. **Saved-page fits go stale after a filter move, with no cue.** Filtered points sit under a fit computed on all rows. The full refit is a decision (see Decisions); a visible stale cue is the small fix. Effort S (cue). Sources: GAPS2-C4, GAPS2-E4a, GAPS2-E4c, AUDIT-38. [Closed in WP-29: BUGS.md "Fits, smooths and densities on the saved page stay fitted to all rows after a filter move, with no cue", commit b242b99; residuals: none]
18. **The served redraw keeps build-time bar/rbar widths.** After a move, bar widths stay 56 where the qualified saved draw gives 168. An emptied lowess panel keeps its style. bar and rbar are not in the moved-layer tests. Effort S. Sources: REM-15-03-C15. [Closed in WP-29: BUGS.md "The served redraw keeps build-time bar and rbar widths and an emptied layer's style after a filter move", commit 2d52fbe; residuals: P2.37]
19. **`dash_setup` fails on externally-managed Pythons (PEP 668, e.g. Homebrew).** There is no detection and no `venv()` option. The manual fallback names a bare, unquoted `python`, and the single-quoted hint breaks in cmd.exe. The `--user` site is not added to the path, there is no ensurepip hint, and the help gives no guidance. Effort M. Sources: GAPS2-H7a, GAPS2-H7b, GAPS2-H7c, GAPS2-H7d, GAPS2-H7e, GAPS2-H7f, GAPS2-H7g. [Closed in WP-29: BUGS.md "dash_setup fails on PEP 668 externally managed Pythons, and the commands it prints fail too", commit 4d74922; residuals: P2.40]
20. **KPI `sd`, `var`, `iqr`, `cv` and `sum` of a date are computed in epoch ms.** `sd` is 86,400,000× Stata's value on a %td variable. Effort S. Sources: GAPS2-E1-residual. [Closed in WP-29: BUGS.md "KPI sd, var, iqr, cv and sum of a date variable are computed in epoch milliseconds", commit 529875d; residuals: none]

### P1: common `twoway` usage not honoured

1. **Stylelists across an expanded varlist.** `scatter mpg turn weight, mcolor(red blue) msymbol(O T)` gives every y the whole list. The renderer then refuses "red blue" and draws scheme defaults, with a misleading note. The same holds for line style lists, the `.`/`=` shorthands, and a single-y list (where `twoway` uses the first element). Effort M. Sources: REM-S06-c, GAPS2-D8-a, GAPS2-D8-b, GAPS2-D8-c, GAPS2-D8-d, GAPS2-D8-e. [Closed in WP-30: BUGS.md "A style list over several y variables, such as mcolor(red blue), is given whole to every series and refused, where twoway gives each series its own element", commit e8953d4; BUGS.md "Per-series value lists such as mlabel(make rep78), jitter(2 3), base(10 20) and barwidth(1 2) are refused r(198), where twoway applies them series by series", commit 8bd6b5a; residuals: P2.60, P2.64, P2.14, P2.21]
2. **Default look differs from the schemes.**
   - The title is bold and left-aligned (Stata centres it and does not bold it).
   - Axis titles are italic.
   - Subtitle, note and caption sit at x=0.
   - Bokeh minor ticks are drawn and tick geometry is Bokeh's.
   - s2color's vertical y tick labels are missing, as is stcolor's dashed grid.
   - s1rcolor's ticks are invisible (black on black), and economist's y axis is wrong.
   - Markers are drawn at alpha 0.8, and `fintensity()` is applied as alpha.

   Effort M. Sources: GAPS2-D17-a, GAPS2-D17-b, GAPS2-D17-c, GAPS2-D17-d, REM-11-04-A1-ALIGN, GAPS2-B29, GAPS2-D16-a, GAPS2-D16-c, GAPS2-D16-d, GAPS2-D12-a, GAPS2-D12-b, GAPS2-D12-c, GAPS2-B25-c, GAPS2-D11-a, GAPS2-D11-b. [Closed in WP-30: BUGS.md "The default chrome differs from every scheme: a bold left-aligned title, italic axis titles, Bokeh's minor ticks and tick geometry, and the schemes' tick angles, grid patterns, tick colours and economist axes missing", commit 6a777a3; BUGS.md "Markers are drawn at alpha 0.8, and fintensity() and the schemes' bar and area intensities are applied as transparency, where Stata blends them opaquely", commit 870e778; residuals: P2.62, P2.2, P2.5]
3. **The default ticker and range padding are Bokeh's, not natscale.** Every default axis gets BasicTicker and 10% padding. Effort M. Sources: GAPS2-B25-a, GAPS2-B25-b. [WP-29 note (S10): twoway's by() common scale includes fit lines (c15); dash's shared range (P0.2, commit ab53f25) does not yet] [Closed in WP-30: BUGS.md "Default numeric axes use Bokeh's ticker and 10 percent padding, not twoway's natscale ticks and plot-region margin, and fit lines are left out of the axis range", commit bde085e; BUGS.md "Default %td to %ty date axes keep Bokeh's DatetimeTicker, not twoway's tsnatscale ticks", commit 8573347; residuals: P2.65, P2.19]
4. **Scheme keys do not reach every layer type.**
   - sttrans opacity is missing on fits, spikes, ranges, immediates and bands.
   - Histograms ignore the scheme's histogram colour, intensity and line width.
   - Hollow and sm* p# symbols are drawn filled and full size.
   - rarea is drawn at alpha 0.5.
   - Marker-label size and colour are fixed at 10px #444444.
   - The ColorBar has no chrome.
   - Unconsumed user-scheme directives are ignored silently.

   Effort M. Sources: GAPS2-D18-a, GAPS2-D18-b, GAPS2-D18-c, GAPS2-D18-d, AUDIT-76, GAPS2-D19-a, GAPS2-D19-b, GAPS2-D5-g, GAPS2-D5-h, REM-11-04-B13-RAREA, REM-11-04-B1, REM-S11-e2, GAPS2-D10-b, GAPS2-D10-a, REM-11-04-C11. [WP-29 note (S12): the empty histogram key colour stays here (P0.18 residual)] [Closed in WP-30: BUGS.md "The scheme's opacity, histogram colour, intensity and width, and its hollow and sm symbols do not reach fits, spikes, ranges, immediates, histograms or rarea", commit 638970a; BUGS.md "Marker-label size and colour are fixed, the colour key has no scheme chrome, and unread user-scheme directives are ignored silently", commit c0518a7; residuals: P2.10, P2.11, P2.66]
5. **Axis format fallbacks.**
   - Default ticks ignore the variable's display format: weight %9.0fc gives 2000, not 2,000.
   - %g/%gc formats are never used as the fallback.
   - `xlabel(, format(%td…))` is silently ignored.
   - A numeric `format()` on a date axis writes epoch ms.
   - The help's log example promises commas that dash does not write.

   Effort S. Sources: REM-09-02-FMT-a, REM-09-02-FMT-b, GAPS2-G10-a, GAPS2-G10-b, REM-09-02-DATE-FORMAT, REM-08-04-C6b, GAPS2-B8-b, REM-08-04-C6a, GAPS2-G10-c. [Closed in WP-30: BUGS.md "Default tick labels ignore the variable's display format, xlabel(, format(%td)) is ignored silently, and a numeric format() on a date axis writes epoch milliseconds", commit 34832ad; P1.5.7 closed in the same commit; residuals: P2.45, P2.63]
6. **tsline time-axis options.** `tlabel`, `ttick`, `tmlabel`, `tmtick`, `ttitle`, `tscale` and `tline` are undeclared and only named in the note. They need folding onto the x equivalents, with date-literal expansion. Effort M. Sources: REM-§2-S09-tlabel, REM-§2-S09-ttick, REM-§2-S09-tline, REM-§2-S09-ttitle, REM-S09-73-tsaxis-a, REM-S09-73-tsaxis-b, REM-05-04-S09-a, REM-05-04-S09-b, GAPS2-A4-q, GAPS2-B14-a, GAPS2-B14-b, GAPS2-B14-c, REM-15-03-E5. [Closed in WP-30: BUGS.md "The tsline time-axis options tlabel, ttick, tmlabel, tmtick, ttitle, tscale and tline are undeclared and only named in the note", commit c565897; residuals: P2.2, P2.83]
7. **Time-series operators in plot varlists are refused r(101).** This covers `line D.close date`, `tsline D.gdp` and `lfit y L.x`, and the help does not document it. Effort M. Sources: GAPS2-G4-a, GAPS2-G4-b, GAPS2-G4-c. [Closed in WP-30: BUGS.md "Time-series operators in plot varlists, such as line D.close date and lfit y L.x, are refused r(101)", commit acd868f; residuals: P2.14, P2.28, P2.78]
8. **`connect()`, `cmissing()` and `recast()` are not honoured.** `scatter y x, c(l)` draws no line, stairsteps and `connect(L)` panel lines are impossible, and missing values are always bridged. Effort M. Sources: REM-§2-S06-connect, REM-S05-04-connect, GAPS2-A4-l, GAPS2-A4-m, GAPS2-A4-n, GAPS2-B12-b, GAPS2-B12-c, GAPS2-B12-d, AUDIT-09, AUDIT-11, AUDIT-12, GAPS2-G15-a. [WP-29 note (S02): P0.1 (commit b0d170d) made the six joining types join in the data's order and honour sort(varlist); connect() on scatter, cmissing() and recast() stay here] [Closed in WP-30: BUGS.md "connect() and cmissing() are not honoured: scatter y x, c(l) draws no line, stairsteps and connect(L) cannot be drawn, and cmissing(n) never breaks a line", commit fa52891; BUGS.md "recast() is not honoured, and recast() on lfitci, qfitci, lpolyci and fpfitci is accepted where twoway refuses it", commit f20751d; residuals: P2.42, P2.43, P2.44, P2.79, P2.90]
9. **`horizontal` is not drawn on any type.** It is common on bar, rcap, rspike and dropline. Effort L. Sources: REM-§2-S06-horizontal, REM-S06-a, GAPS2-A7, GAPS2-B12-a, AUDIT-15. [WP-29 note (S04, S05): `horizontal` on function (S04) and computed layers on a date axis (S05, P0.8 commit cd210ea) stay here] [Closed in WP-30: BUGS.md "horizontal is not drawn on any plot type, and vertical is named as unsupported", commit 7229a0c; BUGS.md "The filter-move redraws of both modes write vertical geometry only, so a horizontal layer cannot keep its orientation after a move", commit a5e3757; residuals: P2.9, P2.52 note]
10. **`text()` and `ttext()` annotations are not drawn.** Effort M. Sources: REM-§2-S09-text, REM-S09-73-text, GAPS2-B20-a, AUDIT-13, REM-§2-S09-ttext, GAPS2-B20-b. [Closed in WP-30: BUGS.md "text() and ttext() annotations are not drawn", commit 56b3597; residuals: P2.46 (closed), P2.85, P2.21 note]
11. **SMCL and TeX in graph text.** `{bf:}`, `{it:}`, `{sup:}`, `{&beta}` and `{c #}` are drawn literally. `$$…$$` in a title triggers MathJax, which grows the page from 1.3 MB to 3.1 MB. Effort M. Sources: GAPS2-D3-a, GAPS2-D3-b, GAPS2-D3-c, GAPS2-D3-d, GAPS2-D3-e, GAPS2-J2, GAPS2-B13, GAPS2-J5. [Closed in WP-30: BUGS.md "TeX delimiters in titles, labels and keys are typeset as mathematics through MathJax where twoway draws them as typed, and the saved page carries the TeX engine", commit 3bdffb5; BUGS.md "SMCL in graph text, such as {bf:}, {it:}, {sup:}, {&beta} and {c #}, is drawn literally", commit a0224b5; residuals: P2.47, P2.48, P2.58, P2.70]
12. **Size units.** Numbers are read as pixels and keywords use a private pixel ladder: `msize(medium)` gives 11px against a default of 8. `#pt`, `*#` and `vhuge` are refused, `mlabgap` is read as px, and `vvvthin` is missing (see Decisions). Effort M. Sources: GAPS2-D2-a, GAPS2-D2-b, GAPS2-D2-c, GAPS2-D2-d, GAPS2-D2-e, GAPS2-B9. [Closed in WP-30: BUGS.md "Marker, text and gap sizes are read as pixels on a private ladder, and #pt, *# and vhuge are refused, where twoway reads Stata's relative size units", commit a1dcb2f; BUGS.md "Line widths use a private ladder without vvvthin or none and read numbers as pixels, and negative widths twoway refuses are accepted", commit 37e9fa4; residuals: P2.13, P2.61, P2.21; P2.49 written closed]
13. **Colour syntax.** `navy*.5`, `*.5`, CMYK, HSV and bg/fg are refused. An unreadable scheme colour falls back to #000000. Effort M. Sources: GAPS2-D7-a, GAPS2-D7-b, GAPS2-D7-c, GAPS2-D7-d, GAPS2-D7-e. [Closed in WP-30: BUGS.md "Stata colour forms such as navy*.5, CMYK, HSV, bg and fg are refused, and an unknown colour is drawn in the scheme's default where twoway draws it black with a note", commit d680274; BUGS.md "A bare *# or %# colour, such as mcolor(*.5), is refused or loses the site's default colour, where twoway adjusts that default", commit f3a0403; residuals: P2.71]
14. **Named styles.** `pstyle()` works only on the four CI fits. `lstyle`, `mstyle`, `mlstyle`, `astyle`, `alstyle`, `bstyle` and `dstyle` are not read. Effort L. Sources: REM-§2-S09-lstyle, REM-§2-S09-mstyle, REM-§2-S09-areastyle, REM-S09-73-namedstyles, REM-05-04-S09-g, GAPS2-B11-a, GAPS2-B11-b, GAPS2-B11-c, GAPS2-D6, AUDIT-29, AUDIT-30. [Closed in WP-30: BUGS.md "pstyle() works only on the four CI fits, and lstyle, mstyle, mlstyle, astyle, alstyle, bstyle and their siblings are not read", commit f4216a8; BUGS.md "Style names other than p1-p15, such as ci, histogram, refline and p1bar, are not read by pstyle() and the other style options", commit 38bbb05; residuals: P2.8, P2.9, P2.12, P2.74]
15. **`by()` sub-options and chrome.**
    - `rows`, `holes`, `colfirst`, `title`, `note`, `legend()`, `i*` axes and `compact` are named in the note and ignored.
    - Every panel draws a legend and repeats both axes.
    - Panel labels are appended to the graph title, and there is no "Graphs by" note.
    - Composite and missing panels are titled differently from `twoway`.
    - Facet aspect ratios miss the automatic layout.

    Effort L. Sources: GAPS2-B16-a, GAPS2-B16-b, GAPS2-B16-c, GAPS2-B16-d, GAPS2-B16-e, GAPS2-B26-d, GAPS2-B31-a, GAPS2-B31-b, GAPS2-B31-c, GAPS2-B31-d, AUDIT-71, AUDIT-72, REM-10-03. [WP-29 note (S03, S07, S10): dash draws an explicit axis-2 title on every by() panel where twoway draws none (r7, s1-s3), and the future "Graphs by" note must use `_dash_var_label` (`Graphs by Group` / `Graphs by g`); twoway draws no colorvar key under by() unless by(, clegend(on)), and then one key showing the first panel's mapping, where dash draws one per panel (S07, P0.16 commit 85dc7d2); P0.2 (commit ab53f25) closed the shared-scale part of by(): outer-axes-only display on shared panels stays here, and YRESCALE and two style() are accepted where twoway refuses them] [Closed in WP-30: BUGS.md "by() panel labels are appended to the graph title, there is no Graphs by note, composite and missing panels are titled differently, and by(, title()) is ignored", commit e7c6ed3; BUGS.md "by() rows, holes, colfirst, compact, iscale and imargin are named and ignored, bad by() arguments are accepted, and faceted graphs miss the automatic layout", commit 1326b97; BUGS.md "Under by() every panel draws a legend and repeats both axes, and by(, legend()) and the i* axis options are named and ignored", commit 52d5b6a; residuals: P2.4, P2.18, P2.69, P2.77, P2.81, P2.84, P2.89]
16. **Legend keys and default titles do not match `twoway`'s text.**
    - lowess, lpoly, mband, mspline and function are all keyed "Fitted values".
    - histogram and kdensity are keyed by the variable label, where `twoway` writes "Density" and "kdensity var".
    - The pc family and scatteri/pci are keyed by the type name.
    - The y title comes from the first layer even when the layers' labels differ.
    - Range types get no y title.

    Effort S. Sources: GAPS2-A13-a, GAPS2-A13-b, GAPS2-A13-c, GAPS2-A13-d, GAPS2-A13-e, GAPS2-A13-f, GAPS2-C10-a, GAPS2-C10-b, GAPS2-C10-c, GAPS2-C10-d. [WP-29 note (S03, S10): P0.3 (commit 8d3593e) closed the histogram and kdensity keys and the unlabelled-variable names; until this item lands, unlabelled multi-layer graphs and second axes take their first layer's name as title where twoway draws none when the layers differ (a25, k9); dash draws no default title on yaxis(2) where twoway titles it by its layers' variables (S10)] [Closed in WP-30: BUGS.md "Legend keys and default axis titles do not follow twoway: fits are keyed Fitted values, pc and immediate types by their type name, the y title follows the first layer, and range types get none", commit ace9c19; residuals: P2.50, P2.51, P2.52]
17. **Bar and range geometry.**
    - bar and rbar default to 0.8× the smallest x gap, not 1 x-unit.
    - rbar ignores `barwidth()` with no note.
    - bar's base is 0, not `twoway`'s rule.
    - rcap cap width ignores `msize()`, and rcapsym draws caps `twoway` does not.
    - When 0 is outside the data, area, bar, spike and dropline draw from 0 and extend the axis to it.

    Effort M. Sources: GAPS2-A3-a, GAPS2-A3-b, GAPS2-A3-c, GAPS2-A3-d, GAPS2-A3-e, GAPS2-A3-f, AUDIT-44, AUDIT-42. [WP-29 note (S05, S12): barwidth() on a date axis (S05); P0.18 (commit 2d52fbe) fixed the served redraw widths only: twoway's one-x-unit bar width stays here] [Closed in WP-30: BUGS.md "bar and rbar default to 0.8 of the smallest x gap, rbar ignores barwidth() without a note, rcap caps ignore msize(), and rcapsym draws caps twoway does not", commit 624837e; BUGS.md "bar, area, spike and dropline draw from 0 rather than twoway's default base, and a 0 outside the data extends the axis to it", commit b3fc476; residuals: P2.21, P2.7]
18. **Common axis sub-options.** `nolabels`, `noticks`, `xscale(off)`, `noline`, axis line colour, width and pattern, `alt` and `titlegap` are not honoured. `angle(rvertical)`, `angle(stacked)` and other anglestyle names are dropped silently. `labcolor`, `tlength`, `tposition` and `add` are not honoured; `add` replaces the default ticks instead of adding to them. Effort M. Sources: GAPS2-B21-c, REM-09-02-NOLABELS-NOTICKS, REM-09-02-SCALE-OFF, REM-09-02-SCALE-LINE, REM-09-02-SCALE-TITLEGAP, GAPS2-B23-b, GAPS2-B23-c, GAPS2-B23-d, GAPS2-B23-e, GAPS2-B23-f, REM-09-02-LABEL-ANGLE, GAPS2-D9-a, REM-09-02-LABEL-LABCOLOR, REM-09-02-LABEL-TICKGEOM, REM-09-02-LABEL-ADD, GAPS2-B21-e, GAPS2-B21-f, AUDIT-28. [WP-29 note (S05, S10): `add` on an axis(2)-routed label (ylabel(…, axis(2) add)) is named, not drawn (P0.5 commit 3208b2b)] [Closed in WP-30: BUGS.md "The axis look sub-options nolabels, noticks, off, noline, line colour, width and pattern, alt, titlegap, labcolor, tlength and tposition are not honoured, and anglestyle names are dropped silently", commit ebde0e9; BUGS.md "The add sub-option replaces the default ticks instead of adding to them, and an axis(2) add is named and not drawn", commit a34192b; residuals: P2.20, P2.72]
19. **Sub-option abbreviations are not recognised.** This covers legend `c()`, `r()`, `lab()` and `posi()`; axis `labs()`, `glc()` and similar; and xline's `lc()`, `lp()` and `lw()`. Effort S. Sources: GAPS2-B17-a, GAPS2-B21-d, REM-09-02-LABSIZE-ABBREV, GAPS2-B22-b. [Closed in WP-30: BUGS.md "Sub-option abbreviations such as legend(c(2) posi(6)), ylabel(, labs(small)) and xline(5, lc(red)) are not recognised", commit ecb8aec; residuals: P2.59, P2.5]
20. **`plotregion()`/`graphregion()` sub-options are dropped with no note.** `margin()`, `style(none)`, graphregion `lcolor`/`lwidth`, the `i*` options and the abbreviations `fc()`/`lc()` all have no effect, and nothing is reported. Effort M. Sources: GAPS2-B18-a, GAPS2-B18-b, GAPS2-B18-c, GAPS2-B18-d, GAPS2-B18-e, GAPS2-B18-f, AUDIT-66. [Closed in WP-30: BUGS.md "plotregion() and graphregion() styling sub-options such as style(none), lcolor(), lwidth(), fc() and lc() are dropped with no note", commit 2207ddb; BUGS.md "plotregion(margin()) and graphregion(margin()) have no effect and no note, and the plot region's inner box is not drawn", commit 6e2af0c; residuals: P2.53, P2.76, P2.77, P2.80, P2.92]
21. **`xline`/`yline` limits.** Numlists such as `xline(2000(500)3000)` draw nothing. `lstyle`, `noextend` and `lalign` are only named. Effort S. Sources: GAPS2-B22-a, GAPS2-B22-d, GAPS2-B22-e, AUDIT-64. [Closed in WP-30: BUGS.md "xline() and yline() numlists such as xline(2000(500)3000) draw nothing, and lstyle() and lalign() are only named", commit 78f9045; BUGS.md "xline() and yline() noextend, extend and style() are only named, so every line spans the whole frame", commit 10ab4ce; residuals: P2.54, P2.82]
22. **`function` evaluates only 10 functions.** `normalden`, `normal`, `ln`, `_pi`, `c(pi)`, comparisons, `cond`, `min`, `max`, `round`, `int`, `scalar()` and `_b[]` all draw nothing. Evaluating in Stata at registration is a candidate fix. Effort M. Sources: GAPS2-A6-a, GAPS2-A6-b, GAPS2-C5-a, GAPS2-C5-b, GAPS2-C5-c, GAPS2-C5-d, GAPS2-C5-e, GAPS2-C5-f, AUDIT-53. [WP-29 note (S04): P0.6 (commit 96aa267) evaluates every function layer of a Stata-built spec with Stata's own generator (stored points), which closes these sources there; the points-free fallback still knows ten functions] [Closed in WP-30 by disposition (M12): WP-29 P0.6, commit 96aa267; BUGS.md "The points-free function fallback knows ten functions and draws any other in silence", commit 47677f8; residuals: P2.14, P2.7, P2.31, P2.68]
23. **Date-axis residuals.**
    - scatteri/pci/pcarrowi coordinates and `function range()` are drawn at raw SIF values (1970).
    - Range and pc plots with date y get no date axis.
    - A layer on `yaxis(2)`/`xaxis(2)` turns the primary date axis numeric, and the secondary date axis shows epoch ms.
    - A date layer beside a numeric layer on one axis is drawn at epoch ms with no warning.
    - Base 0 is 1970, not 1960.
    - A date `colorvar` key shows ms.
    - Fallback tooltips ignore formats.
    - The histogram tooltip always says "Count".

    Effort M. Sources: REM-08-04-C7, REM-08-04-C7b, REM-08-04-C3b, REM-08-04-C3c, REM-08-04-C4, REM-08-04-B2b, REM-08-04-B7a, REM-08-04-B4, REM-08-05-M1, REM-08-05-C7c, REM-08-05-C10, REM-08-05-M2. [WP-29 note (S04, S05): P0.8 (commit cd210ea) computes date layers in Stata units; still open here: xlabel(minmax) on a mixed numeric axis whose first layer's variable is a date reads epoch ms, function/scatteri/pci/pcarrowi on a date axis, and histogram and fit tooltips in epoch ms; each fix should reuse `_dash_units_to_axis`] [Closed in WP-30: BUGS.md "Dates on range, pc, immediate and second axes are drawn at raw or millisecond positions, and a date layer beside a numeric one is drawn in epoch milliseconds", commit 7aa8875; BUGS.md "A date colour key shows epoch milliseconds, fallback tooltips ignore display formats, and the histogram tooltip always says Count", commit cc3c900; residuals: P2.20, P2.63]
24. **`mlabvposition(varname)` is not drawn.** It and `mlabtextstyle` are declared and pending but never serialised, and no test checks that declared options reach the spec. Effort M. Sources: REM-§2-S09-mlabvpos, REM-S09-73-mlabpos, REM-05-04-S09-r, GAPS2-A4-p, GAPS2-B27-c, AUDIT-33, REM-05-04-B6. [Closed in WP-30: BUGS.md "mlabvposition(varname) and mlabtextstyle() are declared and pending but never serialised or drawn", commit 390d964; residuals: P2.12, P2.55, P2.28, P2.75, P2.91]
25. **Scheme resolution.** `scheme(NAME)` never tries Stata's own `scheme-NAME.scheme` file name. Six StataCorp schemes, including meta and stcolor_mv, are refused r(198) where `twoway` draws them. An inherited `c(scheme)` that Stata found is drawn as s2color. `#include` has the same limits. The error message does not list the valid names. Effort M. Sources: REM-§3-f, GAPS2-X5-a, GAPS2-X5-c, GAPS2-X5-d, REM-§3-e. [Closed in WP-30: BUGS.md "Six StataCorp schemes, among them meta and stcolor_mv, are refused r(198) where twoway draws them", commit 438d27e; BUGS.md "scheme(NAME) is looked for in two places only, never along Stata's ado-path or under Stata's scheme-NAME.scheme file name, and its refusal does not list the valid names", commit 15c4f7b; P1.25.6 closed in commit 15c4f7b; residuals: P2.55, P2.73]
26. **Notes do not reliably reach the user.**
    - `dash build, server` reports no option or empty-layer notes.
    - The served child's stderr never reaches Stata.
    - Notes print as raw UserWarnings with internal paths.
    - A session `warnings` filter of "ignore" silences them; one of "error" turns a note into r(7102).

    Effort M. Sources: GAPS2-F5a, GAPS2-F5b, GAPS2-X4-a, GAPS2-X4-b, GAPS2-X4-c, GAPS2-X4-d, GAPS2-I-sum-logging, GAPS2-F5c. [WP-29 note (S12): the served app still prints no empty-layer note where the saved page notes "drew nothing" (bar/rbar/rarea with its own if keeping no row; CORPUS entries dropped by S12)] [Closed in WP-30: BUGS.md "Notes print as raw Python warnings with internal paths, a warnings filter of ignore hides them, and one of error turns a note into r(7102)", commit dd7c165; BUGS.md "dash build, server and dash serve report no option or empty-layer notes, and the served child's stderr never reaches Stata", commit 824e0be; the WP-29 S12 note closed under M6; residuals: P2.26, P2.38]
27. **Drop-in command-form gaps.**
    - `set graphics off` and batch mode still open a browser.
    - A `twoway`/`tw`/`graph twoway` prefix is refused.
    - `saving(n, asis)` writes a file literally named "n, asis.html".
    - `dash build, saving(f, replace)` is refused.
    - `..` and `&` in a saving path are refused where `twoway` accepts them.

    Effort S. Sources: CRIT-04, CRIT-02, CRIT-03, CRIT-09, GAPS2-I14-a, GAPS2-I14-b. [Closed in WP-30: BUGS.md "The drop-in command form fails: a twoway prefix is refused, saving(name, asis) writes a file named after the whole argument, dash build, saving(f, replace) is refused, and batch mode opens a browser", commit 6906236; residuals: P2.56]
28. **No `graph export` companion.** `graph export` after dash fails r(601), or silently exports a stale earlier graph. There is no `r(filename)` and no SVG backend (see Decisions). Effort L. Sources: GAPS2-J7-a, GAPS2-J7-c, GAPS2-E10c, GAPS2-J7-b, GAPS2-E10b. [Closed in WP-30: BUGS.md "dash returns no r(filename), and graph export after dash fails r(601) or silently exports an earlier Stata graph", commit eea99ce; BUGS.md "Neither mode offers a vector export: the toolbar saves only a PNG at the screen's resolution", commit fd4fff0; residuals: P3.4, P3.11]
29. **Security hardening.** Both CSPs keep `unsafe-inline`; they need hashes or a nonce, plus a browser test. `%` and `!` in saving paths reach Windows `start` via cmd.exe; whether they expand there is UNCLEAR (unmeasured on Windows). The help does not state saving()'s character rule. Effort M. Sources: GAPS2-I12-a, GAPS2-I12-b, GAPS2-I12-c, GAPS2-I14-c, GAPS2-I14-d. [Closed in WP-30: BUGS.md "Both content security policies allow inline scripts, and percent and exclamation signs in a saving path reach the Windows shell", commit 0e8fbaf; residuals: P2.87]
30. **Dependency window is open-ended.** There is no bokeh ceiling and no run-time `bokeh.__version__` check. The text-sink XSS safety is verified only on 3.8 and 3.9. The setup gate never reports "outside the verified range". dash also depends on Bokeh internals (`match_host`, `templates.FILE`). Effort S. Sources: GAPS2-H4b, GAPS2-H4c, GAPS2-H4d, GAPS2-H4e, GAPS2-I7-a, GAPS2-I7-b, GAPS2-K5-a, GAPS2-K5-b, GAPS2-K5-c. [WP-29 note (S09): dash_setup does no hash-pinned installs (OQ7)] [Closed in WP-30: BUGS.md "The bokeh dependency has no ceiling or run-time version check, and the Bokeh internals dash's security relies on are not checked", commit 61f5c21; residuals: P2.88, P3.9]
31. **Served-app resource limits.** There is no concurrent-session cap and no unused-session lifetime. Each session re-decodes the whole dataset. One event loop is blocked by recomputes: lowess takes 27.7 s and lpolyci 8.7 s at N=100k. Effort L. Sources: GAPS2-F3a, GAPS2-F3b, GAPS2-F3c, GAPS2-F3d, GAPS2-I4-a, GAPS2-I4-b, GAPS2-G14-d, GAPS2-C-intro-served-cost. [Closed in WP-30: BUGS.md "The served app has no session cap or idle lifetime and decodes the whole dataset again for every session", commit 842e1d9; BUGS.md "One reader's filter-move recompute blocks the served event loop for every other reader", commit e371f8d; the lpolyci part by WP-29 P0.9, commit e32be3a; residuals: P2.41, P2.57, P2.86]
32. **No render-time dependency guards.** A missing numpy, pandas or bokeh gives a bare ModuleNotFoundError. An old Python gives a SyntaxError. `dash_setup`'s first Python call is uncaptured. Effort S. Sources: GAPS2-H6a, GAPS2-H6b, GAPS2-H6c, GAPS2-H6d. [Closed in WP-30: BUGS.md "A missing numpy, pandas or bokeh or an old Python fails with a bare ModuleNotFoundError or SyntaxError, and dash_setup's first Python call is uncaptured", commit 9dc17da; residuals: P2.40, P2.67]
33. **Python floor 3.13 excludes 3.11/3.12 users.** Setup reports failure although dash may still render (see Decisions). Effort S. Sources: GAPS2-H4g. [Closed in WP-30: BUGS.md "The Python floor of 3.13 turns away 3.11 and 3.12 users, and dash_setup reports failure although dash may render", commit dcbca5d; residuals: P3.9]
34. **Never tested off macOS arm64.** Windows, Linux, Intel Mac and GUI Stata are untested. `arch -arm64` and the maintainer's path are hard-coded in the runners. Whether anything actually breaks is UNCLEAR. Effort XL. Sources: GAPS2-H-intro-platforms, GAPS2-H-intro-gui, GAPS2-K1-a, GAPS2-K1-b. [WP-29 note (S08, S09, S13): WP-29's private files, lifecycle, launch from the open file, preview pruning, served key and dash_setup PEP 668 paths are unmeasured on Linux and Windows (Windows paths run on macOS by monkeypatching or as pure functions; Debian's ensurepip-less venv and the GUI locale unmeasured); GUI Break was verified only through a patched pollstd (LC-03)] [Closed in WP-30: BUGS.md "The certification runners hard-code arch -arm64 and the maintainer's paths, so they run on no other machine", commit 44f8ab0 under M4; measurement: the platform package; residuals: P3.7]
35. **`version 16.0` is declared, but only StataNow 19.5 is ever run.** Every truth fixture is also 19.5-only (see Decisions). Effort L. Sources: GAPS2-H-intro-stataver, GAPS2-J8-e, GAPS2-K3-d. [Closed in WP-30: BUGS.md "dash declares Stata 16.0, but only StataNow 19.5 has ever run it or made its truth fixtures", commit 1f05b63 under M2; measurement: the platform package; residuals: none]

### P2: less common options, edge cases, rarely used plot types

1. **Silent dashboard drops.** `layout(s1:1,1 s2:1,1)` drops a graph with no warning. `tabs()` drops unknown names and ignores `layout()` inside a tab. Effort S. Sources: REM-S12-b, GAPS2-E15a, GAPS2-E15b, GAPS2-E15c, AUDIT-82.
2. **Minor ticks and labels (`xmtick`, `ymtick`, `xmlabel`, `ymlabel`) are not drawn.** Bokeh has no labelled minor ticks, so the label half is only partly closable. Effort L. Sources: REM-§2-S09-xymlabel, REM-§2-S09-xymtick, REM-S09-73-minorticks, REM-09-02-MINOR-a, REM-09-02-MINOR-b, GAPS2-B10-a, GAPS2-B10-b, GAPS2-D16-b, AUDIT-61, REM-09-02-T-FEATURES. [WP-29 note (S10): ymlabel/ymtick with axis(2) are validated, not drawn: route them through `_dash_route_axis_options`'s family table (P0.5 commit 3208b2b)] [WP-30 note (S58): `tmlabel()`/`tmtick()` stored and named until minor ticks are drawn (S51; item 6; D16-b)]
3. **Edge titles `t1title` through `r2title` are not drawn.** Effort M. Sources: REM-§2-S09-b1b2title, REM-§2-S09-l1l2title, REM-§2-S09-r1r2title, REM-§2-S09-t1t2title, REM-S09-73-alttitles-tb, REM-S09-73-alttitles-lr, GAPS2-B19-a, GAPS2-B19-b, AUDIT-57.
4. **Textbox sub-options on titles.** `position`, `ring`, `justification` and `span`, and the box, frame and margin options, are not drawn. Effort M. Sources: GAPS2-D17-e, AUDIT-59, AUDIT-60. [WP-30 note (S58): D17-e (item 2); `_dash_textbox_place` is the clock table `title(, position())` will reuse, clocks 2-4/8-10 need a Label beside the frame (S15); `subtitle(, ring(0) pos())` (S28)]
5. **Legend sub-options.**
   - `holes`, `colfirst`, `title`, `region`, `color`, key geometry, `bplacement`, `span`, `stack`, `note` and `caption` are not honoured.
   - The scheme's `cols` is dropped when `pos()` is given.
   - Corner positions are centred on a side, and `pos(0)` goes top-right.
   - The key size is fixed.

   Effort M. Sources: GAPS2-B17-b, GAPS2-B17-c, GAPS2-B17-d, GAPS2-B17-e, GAPS2-B17-f, GAPS2-B17-g, GAPS2-B17-h, GAPS2-B17-i, CRIT-10, AUDIT-65, GAPS2-B26-a, GAPS2-B26-b, GAPS2-B26-c, GAPS2-D16-e. [WP-30 note (S58): D16-e legend key size; B17's open legend parts (holes(), colfirst, textfirst, stack, key gaps, symbol sizes, textwidth, region(), bplacement(), span, titles) (S10); B26-a..c placement (scheme cols with position(), corners, pos(0) ring(0))]
6. **Fit options.** `atobs`, `estcmd()`, `estopts()` and `predopts()` are not honoured, including fpfit's `estopts(degree())`. Neither are `ciplot()`, `fitplot()` and `nofit`. Effort L. Sources: REM-§2-S07-atobs, REM-§2-S07-est, REM-§2-S07-ciplot, REM-S07-13-fitopts, REM-S07-13-ciplot, REM-05-04-S07-c, REM-05-04-S07-d, REM-05-04-S07-e, GAPS2-A4-a, GAPS2-A4-b, GAPS2-A4-c, GAPS2-A4-d, GAPS2-C3-a, GAPS2-C3-b, GAPS2-C9-a, GAPS2-C9-b, AUDIT-20, AUDIT-21.
7. **Distribution and area odds.** kdensity `area()` and `boundary`, histogram `gap()`, function `droplines()`/`base()`, area `nodropbase`, and bar `baroffset`/`mwidth` are not honoured. Effort M. Sources: REM-§2-S07-area, REM-S07-13-kdarea, REM-05-04-S07-b, GAPS2-A4-e, GAPS2-A4-f, GAPS2-A4-g, GAPS2-A4-h, GAPS2-A4-j, GAPS2-A4-k, GAPS2-C3-c, GAPS2-C9-c, GAPS2-C9-d, AUDIT-22, AUDIT-54, AUDIT-55, REM-§2-S09-droplines, REM-S09-73-droplines, REM-05-04-S09-c, REM-§2-S09-bargeom, REM-05-04-S09-j, REM-§2-S09-nodropbase, REM-05-04-S09-t, REM-S09-73-bar-misc. [WP-29 note (S04): function `droplines()` is still refused or ignored after P0.6] [WP-30 note (S58): `droplines()` on function, `nodropbase` (S26/S27)]
8. **Arrowheads.**
   - pcbarrow heads fill black: a quick bug fix.
   - `msize()`, `mcolor()`, `mfcolor()`, `mlcolor()` and `mlwidth()` are silently not read.
   - `mangle`, `barbsize` and `headlabel` are not drawn.
   - A pc row missing only its second point is dropped entirely.

   Effort M. Sources: GAPS2-A2-a, GAPS2-A2-b, GAPS2-A2-c, GAPS2-A2-d, GAPS2-A2-e, GAPS2-A2-f, REM-§2-S09-arrowhead, REM-§2-S09-headlabel, REM-S09-73-pcarrow, REM-05-04-S09-i, GAPS2-B27-a, GAPS2-B27-b, AUDIT-35, AUDIT-36, AUDIT-45. [WP-30 note (S58): `bmlinestyle()`, arrowheads by `mstyle()` (S32/S36)]
9. **`dot` is drawn as a plain scatter with no dot rows.** The difference is undocumented, and the `d*` options, `ndots` and `dotextend` have nothing to style. Effort L. Sources: REM-05-04-DOTGEOM, GAPS2-A14-a, GAPS2-A14-b, GAPS2-A14-c, GAPS2-A14-d, REM-§2-S09-dotcolor, REM-§2-S09-dotsym, REM-§2-S09-ndots, REM-S09-73-dot-a, REM-S09-73-dot-b, REM-S09-73-dot-c, REM-05-04-S09-o, REM-05-04-S09-p, AUDIT-43. [WP-30 note (S58): drawing `dstyle()`/`dlstyle()` (S36, item 14); `horizontal` on dot keeps dot's geometry (S49)]
10. **`colorvar()` coverage.**
    - It is not drawn on line, bar, spike, range or pc types.
    - `clegend`, `plegend`, `colorstart`, `colorend`, `colorrule`, `colorfillonly`, `colorkeysrange`, `colorlist`, `coloruseplegend` and `pcycle` are not honoured.
    - `colorformissing()` is not aliased to dash's working `colormissing()`: a quick win.
    - `colorvar(i.var)` is refused r(111).

    Effort L. Sources: GAPS2-A8-a, GAPS2-A8-b, GAPS2-A8-c, GAPS2-A8-d, AUDIT-16, REM-§2-S09-clegend, REM-§2-S09-colorramp, REM-§2-S09-colormisc, REM-§2-S09-colorlist, REM-§2-S09-pcycle, REM-S09-73-colorvar-a, REM-S09-73-colorvar-b, REM-S09-73-pcycle, REM-05-04-S09-k, REM-05-04-S09-l, REM-05-04-S09-m, REM-05-04-S09-u, GAPS2-B11-e, GAPS2-B11-f, GAPS2-B14-f, GAPS2-X2-r2, AUDIT-19, AUDIT-M1, AUDIT-M2, REM-11-04-B5. [WP-30 note (S58): the colour key's title up its right side and its label-side axis line (S33); B11's `colorlist()`/`coloruseplegend`]
11. **Marker symbol set.** `point`/`p` draws a full 8px circle, `V` is a filled triangle, and sm* and lower-case shorthands draw at full size. `arrow` and `|` are refused, and pipe draws horizontal. `star`, `asterisk`, `hexagon` and `dot` are accepted where `twoway` refuses them. Effort M. Sources: GAPS2-D5-a, GAPS2-D5-b, GAPS2-D5-c, GAPS2-D5-d, GAPS2-D5-e, GAPS2-D5-f, GAPS2-D5-lc. [WP-30 note (S58): sm* sizes closed by P1.4a for the scheme and `msymbol()` (IR-4); `x`/`smx`, `v`/`smv` geometry measured (S24); the lower-case shorthands, point, V, pipe, arrow stay (item 4)]
12. **Line and marker misc.**
    - `lpattern` formulas (`-.`) are refused, including in schemes, and named pattern geometry differs.
    - `mlpattern`, `lwidth(none)` and msangle anglestyle names are not honoured.
    - `mlalign`, `mwidth`, `mlabstyle` and `mlabtextstyle` are not honoured.
    - The alignment options have no Bokeh equivalent.
    - Area outline options work only on the CI bands.

    Effort M. Sources: GAPS2-D4-a, GAPS2-D4-b, GAPS2-D4-c, GAPS2-D4-d, GAPS2-B11-d, AUDIT-32, CRIT-06, CRIT-07, REM-§2-S09-mlabstyle, REM-05-04-S09-s, REM-S09-73-marker, GAPS2-B27-d, AUDIT-34, REM-§2-S09-align, REM-S09-73-areastyle, REM-05-04-S09-h, REM-S09-73-fitarea. [WP-30 note (S58): `lwidth(none)` closed by P1.12b; `mlabtextstyle` closed by P1.24; area/rarea outlines of a named style, a series style's label role, `mlabstyle()`, `mlalign`, `mwidth` and B11's `mlpattern()` stay (item 24)]
13. **Sizing.** `scale()`, `fxsize()`, `fysize()` and the overhangs are not applied; whether the overhangs are no-ops is UNCLEAR. `aspectratio()` shapes the figure rather than the plot region, is dropped when xsize/ysize are given, and `aspectratio(#, placement())` is refused. Sizes are fixed to a 4-inch reference. Effort M. Sources: REM-§2-S10-fxfysize, REM-§2-S10-scale, REM-S10-a, REM-S10-b, GAPS2-B33-a, GAPS2-B33-b, GAPS2-B33-c, GAPS2-D14-a, GAPS2-D14-b, GAPS2-B30-a, GAPS2-B30-b, GAPS2-B30-c, AUDIT-68, AUDIT-69, REM-05-04-C1. [WP-30 note (S58): graphsize reference closed by P1.12a; `xsize()`/`ysize()` do not change the reference length of absolute units (S08 Q1, kept); `scale()`]
14. **dash refuses values `twoway` accepts.**
    - `range(varname)` and a `.` end in `range()`
    - `degree()` above 3, `n(1)`, and `n()` above _N on lpoly
    - `bwidth(0)`, and lowess `bwidth()` above 1
    - several variables in `mlabel()`, and scatteri `2/2`
    - `msize(1e400)`, and bounds checked on types that do not draw the option
    - `level()` bounds applied to every CI type
    - weight expressions, and `yaxis(1 2)`

    Effort M. Sources: GAPS2-A15-a, GAPS2-A15-b, GAPS2-A15-c, GAPS2-A15-e, GAPS2-A15-g, GAPS2-A15-h, GAPS2-A15-i, GAPS2-A15-j, GAPS2-A15-k, GAPS2-A15-l, GAPS2-C11-a, GAPS2-C11-b, GAPS2-C11-c, GAPS2-C11-d, GAPS2-C11-e, GAPS2-C11-f, GAPS2-C11-g, GAPS2-A12-c, GAPS2-C7-d, GAPS2-G17, GAPS2-B15-c, AUDIT-25, AUDIT-41, AUDIT-47, AUDIT-49, AUDIT-51, AUDIT-52. [WP-29 note (S04, S11): `range(varname)` on function is still refused (S04); the degree 4-7 rule-of-thumb constants (SD-7) are in `_LPOLY_ROT_CONSTANTS` but dormant until degree() above 3 is accepted] [WP-30 note (S58): `fintensity(1e400)` (S16); `[aw=L.x]` reusing `_dash_tsop_gen` (S42, item 7); an `mlabel()` element naming several variables, per-element jitter/barwidth bounds, `jitterseed(1 2)` (S20); `barwidth(0)`/`(-1)` (S14); `range(varname)` on function (S26); `msize(1e400)` (S08)]
15. **Axes 3–9 are refused.** Effort L. Sources: GAPS2-A15-f, GAPS2-B15-b, AUDIT-26.
16. **Weighted scatter markers are not size-scaled.** Also, `jitter()` is not drawn on rscatter, rcapsym, pcscatter and pccapsym. Effort M. Sources: GAPS2-G18, AUDIT-40, GAPS2-A8-e, AUDIT-46.
17. **Missing plot types:**
    - rpcap and rpspike: M
    - sunflower: M (also falls to the generic "unrecognised" message)
    - matamatrix: M (gives a misleading r(101))
    - heatmap: L
    - contour and contourline: XL

    Effort XL. Sources: GAPS2-A5-a, GAPS2-A5-b, GAPS2-A5-c, GAPS2-A5-d, GAPS2-A5-e, AUDIT-01, AUDIT-02, AUDIT-03, AUDIT-04, AUDIT-05.
18. **Extended missing values `.a`–`.z` are merged into one.** This affects `by(, missing)` panels, marker labels, filters and tooltips. Effort M. Sources: GAPS2-G12-a, GAPS2-G12-b, GAPS2-G12-c, GAPS2-B27-e, AUDIT-37. [WP-29 note (S06): a hover-only variable's .a-.z still show as . in a tooltip] [WP-30 note (S58): `.a`-`.z` panels (S28)]
19. **Date `#N` tick choice matches `twoway` only 52–66% of the time on %td–%th.** There are also three natscale misses on auto. Effort L. Sources: GAPS2-B24-a, GAPS2-B24-b, AUDIT-63. [WP-30 note (S58): S44's commit 8573347 is its baseline (item 3); the %tm add case (S52: 480 492 … against twoway's 480 498 516 534)]
20. **Axis edge cases.**
    - `minmax` uses only the first layer, and ticks are not recomputed after a filter move.
    - `##5` is read as `#5`.
    - Quoted label text triggers sub-options: `xlabel(1 "grid")` turns the grid on.
    - Multi-line tick labels are drawn with their quotes.
    - `labgap`, label and tick styles, `alternate`, grid styles and `gmin` are not drawn.
    - Label forms `twoway` refuses are drawn anyway.
    - `angle(Vertical)` is accepted.

    Effort M. Sources: REM-09-02-MINMAX-VAR, REM-09-02-MINMAX-FILTER, REM-09-02-MINOR-c, REM-09-02-SUBOPT-IN-LABEL, CRIT-05, REM-09-02-LABEL-LABGAP, REM-09-02-LABEL-STYLES, REM-09-02-LABEL-ALT, GAPS2-B21-g, GAPS2-B21-h, GAPS2-B21-i, GAPS2-B21-j, GAPS2-B21-k, GAPS2-B1-res, GAPS2-D9-b. [WP-30 note (S58): B21's open items (labgap, label/tick/grid styles, gmin/gmax, custom, alternate); all-layer `minmax` (item 23, S35); the axis line style (S31); REM-09-02-SUBOPT-IN-LABEL closed by P1.19; the `angle(Vertical)` bullet struck (P1.18a)]
21. **Options on types that do not take them are accepted silently.** `bwidth`, `n`, `range`, `base` and `level` on scatter give rc 0 and no note, and `kernel()` is written to the spec, where `twoway` refuses r(198) (see Decisions). Effort S. Sources: GAPS2-A12-a, GAPS2-A12-b, GAPS2-C15, AUDIT-78. [WP-29 note (S11): pwidth()/var() on lpoly, scatter, lfitci and kdensity keep the unsupported note where twoway refuses r(198) (SD-5, D9)] [WP-30 note (S58): the sweep (item 1); D-13c and a negative width refused on every type (S13); `barwidth()` on rspike/rscatter/rarea/rline/rconnected/scatter/line (S14); `zlabel()` repeats (S17 a, b); `xvar()`/`xva()` (S18); scalar `base()` on rbar/histogram and `barwidth()` on rspike (S20); `pst()`/`ps()`/`as()` (S32); `base()` on dot/function (S27); an abbreviation of text() such as `tex()` named where twoway refuses (S56); an unknown `cmissing()` refused at parse under nodraw and `cm(n)` named where twoway refuses r(198) (S40)]
22. **Locale and text settings.** `set dp comma` is never read. %tC ignores leap seconds (up to 27 s), and the help says otherwise. The `graph set` fontface setting is not read. Effort M. Sources: GAPS2-J1-c, GAPS2-G7-a, GAPS2-G7-b, CRIT-08. [WP-30 note (S58): `{stSans}`/`{stSerif}`/`{stMono}` map to fixed families; reading `graph set` fonts should feed them (S29)]
23. **Secondary-axis range does not follow a filter move (both modes).** Effort M. Sources: REM-09-07-Y2-FILTER-CALLBACK, GAPS2-E6a, REM-09-07-Y2-TEST-GAP.
24. **Documented saved/served residuals.** Under `layout(bs)` with `filterposition(left)`, the header sits beside the sidebar in the saved page and above it in the served app. The saved page keeps its histogram bins and kdensity grid after a filter move. Panels emptied by a filter stay drawn. Effort M. Sources: GAPS2-E14-residual, AUDIT-81, GAPS2-E4b, AUDIT-39, GAPS2-E6b. [WP-29 note (S12): the saved page now marks a histogram or kdensity whose sample a move reduced, keyed (bins unfiltered)/(grid unfiltered) (P0.17 commit b242b99); it still does not recompute them] [WP-30 note (S58): a graph removed with `graph drop` that the console's Graph window still shows is exported by `graph export` without dash's stale-graph note (S22, P1.28a)]
25. **Interaction edge cases.** Brushing a histogram dims the bars and drives nothing. Concurrent brushes are not intersected. Saved-page JS errors fail silently. Saved sliders are not throttled. Effort M. Sources: GAPS2-E5a, GAPS2-E5b, GAPS2-E11, GAPS2-E12.
26. **Environment robustness.**
    - `BOKEH_RESOURCES=cdn` silently blanks the served page.
    - Other Bokeh environment variables are not reported, and `BOKEH_MINIFIED`/`BOKEH_DEV` change the saved page silently.
    - `/health` is shallow.
    - The browser-launch return code is unchecked.

    Effort S. Sources: GAPS2-F12a, GAPS2-I1-a, GAPS2-I1-b, GAPS2-F12b, GAPS2-K4-a, GAPS2-K4-b, GAPS2-I-sum-health, GAPS2-F-intro-health, REM-S14-b. [WP-30 note (S58): S23's relay is their route]
27. **Session hygiene.** Four Mata functions are unprefixed. The repair step drops other packages' functions of the same names. `sys.argv` is overwritten, and `_dash_*` names are left in `__main__`. Effort S. Sources: GAPS2-X7-a, GAPS2-X7-b, GAPS2-X7-c, GAPS2-X7-d, GAPS2-X7-e.
28. **Data and memory.**
    - Working columns are generated in the user's data, so r(900) is possible at `c(maxvar)`.
    - Variables named `x`, `y`, `top` and similar are shadowed in `hover()`/`mlabel()`.
    - Numbers are embedded as JSON text, rendering needs about 0.5 GB per million values, and the strL check loops per observation.
    - A faceted computed-only graph is counted in full against the cells limit.

    Effort M. Sources: GAPS2-G1-res-a, GAPS2-G1-res-b, GAPS2-G14-a, GAPS2-G14-b, GAPS2-G14-c, GAPS2-G3-res. [WP-29 note (S06): P0.10 (commit 735c534): hover()'s own variables count only where a layer can show them or csv is given, but a graph made only of computed or literal layers that hover() names is still counted by its plotted rows (G3's touched rule, DL-03e's 74)] [WP-30 note (S58): a temporary-frame move runs `_dash_tsop_gen` in the user's frame first (S42); a position variable named x or y on rscatter's stacked source (S37); G14-a..c]
29. **Packaging basics.** There is no README with an install command, no LICENSE, and `dash.pkg` has no Author, KW or Stata version. A `.pyc` is written into PLUS/py. A failed setup does not say what it installed and cannot roll back. Effort S. Sources: GAPS2-J8-b, GAPS2-J8-c, GAPS2-J8-d, GAPS2-H10a, GAPS2-H10b, GAPS2-H10c, GAPS2-H8a, GAPS2-H8b.
30. **Join-order edge cases.** rarea with exactly one bound missing on a row leaves that row out of both bounds where twoway's polygon keeps the other (O1); points whose sort keys tie keep the data's order where twoway's order is random; connected's markers paint in data order under sort (O6); `sort() sort()` with every copy empty is unpinned. Effort S. Sources: WP-29-S02 (P0.1 residuals), BUGS.md "line, connected, area, rline, rarea and rconnected are joined in x order, never in the data's order as twoway joins them, and sort(varlist) is ignored" residual. [WP-30 note (S58): the WP-29 residuals WP-30 closed (R58-8): P1.16 (commit ace9c19) for BUGS.md:2742/:2748/:2754; P1.23a (7aa8875) for :2771's minmax and function/scatteri/pci parts; P1.17a (624837e) for BUGS.md:504 and the bar-width notes; P1.15c (52d5b6a) for the axis-2-title and clegend notes]
31. **function layer residuals.** Under by() the expression is evaluated once where twoway evaluates it once per panel (FX-24); a malformed y-form is echoed as typed rather than as twoway's token. Effort S. Sources: WP-29-S04 (P0.6 residuals), BUGS.md "function evaluates ^ from the right and accepts pi and e, which twoway refuses" residual. [WP-30 note (S58): by() per-panel evaluation of `function` stays (S26)]
32. **Fractional period values are floored on load.** A %t date variable holding a non-integer value is floored when loaded; twoway's drawing of such a value was not measured in WP-29. Effort S. Sources: WP-29-S05 (P0.8 residuals), BUGS.md "Computed layers on a date variable run in epoch milliseconds, so densities are per ms, width(), start() and bwidth() are read as ms, and lpoly draws nothing" residual.
33. **hover() given twice in one layer.** hover() written inside a layer's parentheses and again after the comma keeps only the rightmost list. Effort S. Sources: WP-29-S06 (P0.10 residuals), BUGS.md "A variable named only in hover() is never exported, so its tooltip field is empty in both modes" residual.
34. **colorvar() refusals and key text.** Two colorvar plots in one graph are drawn where twoway refuses them ("multiple contour, patch, or colorvar plots not allowed", r(198)); an empty colorvar plot draws no key where twoway stops r(3001) in `_calc_levels()`; an all-missing plot's key shows "(missing)" where twoway shows the title alone; a string colorvar is dash's own (twoway r(7)). Measured on StataNow 19.5. Effort S. Sources: WP-29-S07 (P0.16 residuals), BUGS.md "The colorvar() colour range ignores a per-plot if on the saved page and a linked graph's qualifier in both modes" residual.
35. **Private-files and lifecycle residuals.** In a c(tmpdir) others can write without a sticky bit (noted to the user), another account that replaces `dash-<uid>` can replace the spec or data between dash.ado's write and the renderer's read, or deny the launch (it can no longer change what dash serve runs); a folder left by an error, Break or crash stays until the next dash command, or a later session once its Stata has ended, sweeps it; a crash in the 0.25 s between `/health` answering and the launcher's next pass leaves the app (0600, in its private run folder) until that sweep; on a disk that keeps no permissions (noted) the copies are not private and dash serve's copies stay until the command ends; F2's erase of `app.py` still waits for `/health` and the banner although the child no longer reads the file; the newest five preview pages of a session stay until `dash clear` or the session's end is noticed, and on Windows another session's pages are pruned by age alone (a day). A `.py` run by hand is opened by name and imports from its folder, as the help says. Effort M. Sources: WP-29-S08 (P0.12b, P0.13, P0.14 residuals), BUGS.md "The served app, spec and data files are written with the default umask, readable by other accounts where the temp directory is shared" residual, BUGS.md "The served app outlives a killed Stata, its files survive a crash, and Break cannot stop dash serve" residual, BUGS.md "One-line preview pages are never deleted and are written 0644, each a copy of the graph's data" residual.
36. **lpoly/lpolyci edge divergences from Stata.** twoway counts a gaussian weight toward the two-observation rule only above about 1e-14, so `lpoly mpg weight, kernel(gaussian) bwidth(1)` draws 3 points in Stata and 23 in dash (SD-10); exact fits differ where Stata's round-off decides (D1 `ylin=2*weight+1` degree 0, D2 `yw=weight` degree 0/1, D3 `mpg*1e-150` degree 2: a zero line); lpolyci rows whose pilot has no residual degrees of freedom are pinched where Stata is often missing (D4), and the pilot's round-off moves the se at 2 of 50 rows of `r1000_d2_bw600` (D5); `if _n==1, pwidth(0)` is refused r(198) where twoway counts first, r(2001) (D6); invalid-option messages name the option in dash's words (D7); `pwidth(+800)` is accepted where twoway gives r(3000) (D8). Effort M. Sources: WP-29-S11 (P0.7, P0.9 residuals), BUGS.md "The lpoly and lpolyci default bandwidth ignores kernel() and degree() and misses Stata's rule of thumb" residual, BUGS.md "The lpolyci band is a bootstrap percentile band, not Stata's analytic band, and pwidth() and var() are ignored" residual.
37. **lpoly with its own if on a small subset draws an empty line.** On the test frame's five domestic rows (`if foreign == 0`) dash's lpoly draws an empty line before any filter move; whether twoway draws a curve there is not measured. Measure against twoway, then fix or document. Effort S. Sources: WP-29-S12 (P0.18 move corpus, entry "lpoly with its own if emptied" omitted).
38. **Served-key residuals.** Under a hand-run `python app.py` each refused request logs one redacted WARNING line, with no throttle; under `bokeh serve` only Gate B applies, so `/autoload.js` and `/metadata` answer 200 with the refusal page and no data; a keyless websocket attempt may inflate up to 262,144 bytes before refusal; under `bokeh serve` without `DASH_SERVE_TOKEN` the self-made link names no `--prefix`, waits for the first page request when the first session came over a websocket, cannot be made under `--unix-socket` or a port under 1024 (one line says so; every session stays refused), and its page stays blank unless the server was started with `--allow-websocket-origin 127.0.0.1:<port>` (the app prints that hint); a link folder made for a self-made key outlives a SIGKILL of its process, and a SIGTERM of a hand-run `python app.py`, which skips the app's cleanup; on a disk that keeps no permissions the link file is written anyway, readable by other accounts while the server runs, with one note naming it; when no link file can be written anywhere the link and its key are printed once, after a warning, to the starter's output (and so into Stata's Results and any open log under dash serve). Effort M. Sources: WP-29-S13 (P0.12a residuals), BUGS.md "The served app has no credential, so any local account can open a session and read the data" residual. [WP-30 note (S58): S23's relay is their route]
39. **Embedded-rows residuals.** Rows selected only for computed layers are embedded on the saved page (no JS refit, decision M3); the served `.py` and its data JSON hold every row on disk (written privately where the system allows); `$dash_max_cells` counts every exported row, not the planned ones; the saved and served dataset-size notes may differ on qualified data; a served mapper copy's `index` is a position in its layer's source while the served brush reads it as a row label (a line's first point read observation 1's price, 4749, for observation 3's 4816; a Line takes no box or lasso hit, so not reached from a browser; no leak). Effort S. Sources: WP-29-S14 (P0.11 residuals), BUGS.md "The saved page embeds every row of each drawn variable, including rows that if and in exclude" residual.
40. **dash_setup residuals.** The served child is `sys.executable`, Homebrew's base Python under a Homebrew venv link, and works only through Stata's exported `PYTHONPATH` (OQ4); `Unmet:` lists warnings when a failure also occurred (OQ6). A `dash_setup_lib.py` or `bokeh.py` in the working directory is found first, by Stata's and Python's own rule. Effort S. Sources: WP-29-S09 (P0.19 residuals), BUGS.md "dash_setup fails on PEP 668 externally managed Pythons, and the commands it prints fail too" residual. [WP-30 note (S58): its failure now ends in one line naming `dash_setup` (S25)]
41. **Carried columns are handed to Bokeh as lists.** GlyphMapper._carry_cols turns every carried column (the row id, hover() and mlabel variables) into a Python list with .tolist(), and bokeh 3.8 validates such a list item by item: a million-row line took 2.04-2.56 s under Stata's Python (bokeh 3.8.0), 7.5 of 7.7 s of it in that validation, and 0.8 s for four cases under bokeh 3.9; keep numeric carried columns as arrays. Effort S. Sources: WP-29-S15 (make test, 02oct2026), BUGS.md "line, connected, area, rline, rarea and rconnected are joined in x order, never in the data's order as twoway joins them, and sort(varlist) is ignored" residual. [WP-30 note (S58): `.tolist()`, the index lists and the per-session move snapshot stay (S46)]

42. **cmissing(n) on area/rarea and connect() on rarea are noted, not drawn.** cmissing(n) on area and rarea, and connect() other than direct (c(J) included) on rarea, are named in the note, not drawn; S40's cases. Effort M. Sources: WP-30 register P1.8.3; WP-30-S40 (P1.8a residuals); BUGS.md "connect() and cmissing() are not honoured…" residual.

43. **cmissing(n) at estimator-generated missing points.** cmissing(n) on lowess, lpoly, lpolyci, fpfit, fpfitci, lfitci, qfitci (and mband, mspline), whose own missing points twoway breaks at, is named, not drawn. Effort M. Sources: WP-30 register P1.8.7; WP-30-S40.

44. **recast() from histogram to range types.** histogram recast to a range type or an unknown name stays named; twoway draws it. Effort M. Sources: WP-30 register P1.8.7; WP-30-S45 (P1.8b residuals).

45. **One format-writer model per distinct tick format.** each distinct format ships its own ~33 KB writer model; S17's fallback tooltips add one per distinct (fmt, kind); share one per page. Effort M. Sources: WP-30 register P1.5.3; WP-30-S17, S18.

46. **An empty trailing `|| , options` refused.** Written closed. [Closed in WP-30: commit 4fda248 ("Read a || piece with no plot as twoway does"; test_parser.cscript P1A-85, parser_twoway_truth.json); no BUGS.md entry] Sources: WP-30 register P1.10.6.

47. **SMCL beyond graph_text's documented tags drawn as typed.** {hline}, {space}, {dup}, {cmd:}/{hi:}, {ccl}, {center:}, links drawn as typed. Effort M. Sources: WP-30 register P1.11.2; WP-30-S29.

48. **The served bundle ships bokeh-mathjax.** 1.79 MB per session, unused by dash text since P1.11a; the saved page with `$$…$$` text measured 3,087,832 bytes at c96facd against 1,301,750 plain. Effort S. Sources: WP-30 register P1.11.6; WP-30-S09.

49. **Nonselection/muted glyphs keep creation values.** Written closed. [Closed in WP-30: BUGS.md "Marker, text and gap sizes are read as pixels on a private ladder, and #pt, *# and vhuge are refused, where twoway reads Stata's relative size units", commit a1dcb2f] Sources: WP-30 register P1.12.6.

50. **Keys twoway merges.** keys with the same text and style are not merged (E7's probes). Effort M. Sources: WP-30 register P1.16.2; WP-30-S19.

51. **Histogram-only legends.** a histogram-only graph draws a legend; twoway draws none. Effort S. Sources: WP-30 register P1.16.2; WP-30-S19.

52. **The first-used axis side.** the first-used axis is not drawn left/bottom. Effort M. Sources: WP-30 register P1.16.2; WP-30-S19. [WP-30 note (S58): under `horizontal` with `yaxis(2)` twoway titles the x axis from the first layer ("Xvar…") where dash draws none (S49)]

53. **graphregion() outer margin and i* options.** graphregion(margin()) is not drawn exactly; the graphregion i* options and inner box are named, not drawn (Bokeh boxes clip to the frame); IR-2 strikes the bgcolor half (drawn by P1.20a). Effort M. Sources: WP-30 register P1.20.2; WP-30-S38, S47.

54. **An out-of-range xline/yline is clipped.** clipped at the frame; twoway draws it outside the plot region. Effort M. Sources: WP-30 register P1.21.7; WP-30-S39, S50.

55. **User and third-party `*.style` files.** textboxstyle and color-*.style files on the ado-path are not read (noted as unknown). Effort M. Sources: WP-30 register P1.24.3, P1.25.7; WP-30-S34, S37.

56. **`dash twoway` alone refused.** twoway draws an empty graph. Effort S. Sources: WP-30 register P1.27.8; WP-30-S12.

57. **A served session's make_document runs on the event loop.** 1.6-4.6 s at 100-200k rows (register); S57 measured session open at 100k rows; the 200k and three-session latencies not measured. Effort M. Sources: WP-30 register P1.31.11; WP-30-S46, S57. [WP-30 note (S58, corrected by the follow-up): the 80 MB per-session growth bound is pinned by test_served_resources.py::TestPerSessionMemory::test_growth_at_most_80_mb (release tier) over 200k rows of 3 variables, one scatter and a dropdown (research m2): 63.9 MB under bokeh 3.9, 70.5 MB under 3.8; with three scatter layers growth is 150.7 MB per session, above the bound (the per-session lists, P2.41)]

58. **`$name` in drawn labels.** twoway macro-expands `$name` in a variable or value label it draws (value label `$$f$$` drawn `$$$`); dash draws the stored text. Effort S. Sources: WP-30-S09.

59. **Legend and title sub-option edges.** `title("T", prefix suffix)` prints twoway's "option prefix ignored…" line, dash none; `legend(label(1))` blanks key 1 in twoway; values nested in `legend(region())`/`legend(title())` unchecked; `legend(po(9) top)` names `top` first. Effort S. Sources: WP-30-S10 (R-S10-1..4); BUGS.md P1.19 residual.

60. **Stylelist element edges.** an unknown `msymbol()` element draws the p# symbol (twoway: circle); glued `=` forms (`red=blue`, `red=`) and `(red)` elements reach the renderer as one unknown element (twoway r(198) for `(red)`); a misplaced `..` echo differs in blank count only. (The blank quoted element is refused since S11, ratification row 32.). Effort M. Sources: WP-30-S11; BUGS.md P1.1a residual.

61. **Line-width edges.** the draw-time 10,000-unit bound (D-13b); `*#` on a sub-0.3 pt default (D-13e); `tlwidth()`/`glwidth()` on every axis and the colour key named, not drawn (D-13f). Effort S. Sources: WP-30-S13; BUGS.md P1.12b residual.

62. **pstyle(p#) CI bands under intensity above full.** under a scheme whose `intensity p#bar` is above full (D-16e); kept: no landed section closed it. Effort S. Sources: WP-30-S16.

63. **Axis-format edges.** `%d`/`%tb…` axis formats drawn `%9.0g` with a note (twoway writes dates); `xvarformat(bogus)` noted and `%9.0g` (twoway: `bogus not found`, no labels). **Struck part:** a horizontal histogram's tooltip naming its bins on x, closed by S55 (P1.9b, commit a5e3757; test_horizontal_moves.py::TestTheTooltipFollowsTheTurn::test_a_turned_histogram_answers_along_its_bins). Effort S. Sources: WP-30-S18, S17 (c); BUGS.md P1.5 residual.

64. **Value-list refusals in dash's words or codes.** lowess/kdensity `bwidth()`/`level()`/`degree()` lists; `base(abc)` r(198) vs r(4026); rbar `barwidth(.)` r(198) vs r(199); `mlabel(make..)` r(198) vs r(101); `mlabel(L.mpg)` r(198) vs r(111); `mlabposition(13)`'s note vs `named style 13 not found in class clockdir`. Effort M. Sources: WP-30-S20; BUGS.md P1.1b residual.

65. **natscale residuals.** `xtick(#N)`/`xlabel(minmax)` held after a move (twoway re-places under `if`); the margin a build-time fraction, up to ~0.8% of the width off on resize (ratified A6); a user scheme's `special by_knot1/by_slope*` and `gsize *margin` unread; an axis with no finite value keeps Bokeh's autorange after a move; by(, style(rescale) noyrescale)'s x count not modelled. Effort M. Sources: WP-30-S21; BUGS.md P1.3a residual.

66. **rarea and rbar outlines.** twoway strokes them (rarea `#1A476F` 17.28 under s2color); dash draws none. Effort S. Sources: WP-30-S24; BUGS.md P1.4a residual.

67. **Hand-run version note; pre-3.7 SyntaxError.** a renderer or app run by hand prints no numpy/pandas version note; Python < 3.7 by hand stops with a SyntaxError whose shown line carries the remedy (low). Effort S. Sources: WP-30-S25; BUGS.md P1.32 residual.

68. **Extend the points-free function fallback.** research option B: comparisons, `!`, `cond`, n-ary min/max, round, int, ln, normal, normalden, c(pi), missing codes; 1e-12 in the normal tails. Effort M. Sources: WP-30-S26; manifest item 22; BUGS.md P1.22 residual.

69. **A one-panel by() with an empty value label.** drawn without panel chrome (the no-faceting sentinel). The filled label box is not a residual: S53 draws it (Q-28.1, ratification row 36). Effort S. Sources: WP-30-S28, S53.

70. **Exact inline style runs and raised text (TeX route).** a style or raised run on part of a text, and raised text with no Unicode form, are drawn in the text's own style. Effort L. Sources: WP-30-S29; manifest item 11; BUGS.md P1.11b residual.

71. **Colour edges.** a user scheme's hex `color background/foreground` resolving `bg`/`fg`; a comma colour inside a structured sub-option (`title(…, color("1,2,3"))`, region, `xline(…, lcolor())`, `ylabel(, labcolor("255,0,0"))`) noted and drawn black where twoway refuses r(198); navy*52's clamp and the `color foreground bg` cycle (UNCLEAR); `mcolor("red",blue)` one unknown colour. Effort M. Sources: WP-30-S30 (1-4), S31 R-S31-5; BUGS.md P1.13a, P1.18a residuals.

72. **Axis-look edges.** two `yscale(alt)` toggle back in twoway; `gsize axis_title_gap` unread (default gap from Bokeh's 5 px); `zlabel()`/`zscale()` look words named; `xtick()`'s labcolor/labels/nolabels named; `mlabangle()`'s h/v/rh/rv unmeasured; `fill`, `outergap()`, `extend`/`noextend`/`fextend` and the axis `lstyle()` named. Effort M. Sources: WP-30-S31 R-S31-1,2,3,4,6,7; BUGS.md P1.18a residual.

73. **scheme.class's `c(adoarchive)` branch.** unmeasured. Effort S. Sources: WP-30-S34; BUGS.md P1.25b residual.

74. **The other Stata style names.** 57 Stata-known style names outside S36's table (fpall, sunflower, plotregion, …) drawn in default attributes (D-36c); a general resolver over the 161 style files; any label-colour difference under `pstyle(ci)`/histogram. Effort L. Sources: WP-30-S36; manifest item 14; BUGS.md P1.14b residual.

75. **A range layer labelled by its own variable.** `rscatter y y2 x, mlabel(y)`: twoway r(102) `rscatter requires 3 variables`; dash draws. Effort S. Sources: WP-30-S37; BUGS.md P1.24 residual.

76. **Region intensity and shading.** `intensity()`, `iintensity()`, `shadestyle()`, `ishadestyle()`, `marginonly` named, not drawn (Q-38.1). Effort M. Sources: WP-30-S38; review g06.

77. **by()'s overall regions.** `by(, graphregion() plotregion())` and `by(…, regions)` stay named (IR-9). Effort M. Sources: WP-30-S38; manifest item 15; BUGS.md P1.15c, P1.20a residuals.

78. **Option variables with operators.** `mlabel(L.make)` (twoway r(111)), `colorvar(L.mpg)`/`by(L.foreign)` (r(101)); dash r(198). Effort S. Sources: WP-30-S42; BUGS.md P1.7 residual.

79. **recast() on pci and pcarrowi; multi-word recast notes.** twoway draws `pci …, recast(pcarrow)` as arrows; its note names a multi-word value differently (scatterline for line scatter). Effort S. Sources: WP-30-S45; BUGS.md P1.8b residual.

80. **Margin forms twoway draws.** `margin(L+10)` (drawn zero with a note), `margin(1 2 3)`, `margin(1 2 3 4 5)`; `margin(allsides-ms)`, r(7) in twoway, drawn as its style file says. Effort S. Sources: WP-30-S47; BUGS.md P1.20b residual.

81. **by() layout edges.** a panel's plot-region margin uses f(panels), not f(full_n)/`iscale()`; per-row label offsets not scaled; the second `iscale()` note not copied; subtitleformat(), the shrink options and other bystyles named. Effort M. Sources: WP-30-S48; BUGS.md P1.15b residual.

82. **A one-end-extended reference line on zoom-out.** an asymmetric user scheme's extended end stays at the last re-finish's frame. Effort S. Sources: WP-30-S50; BUGS.md P1.21b residual.

83. **Date literals in y-options.** `ylabel(2000m1)` accepted; twoway r(198). Effort S. Sources: WP-30-S51; BUGS.md P1.6 residual.

84. **by() legend and axes.** `by(, legend(ring(0)))` drawn beside the array; the overall legend not clickable; `by_alternate_*` axes. Effort M. Sources: WP-30-S53; BUGS.md P1.15c residual.

85. **`tstyle()` on added text.** drawn through `SchemeParser.textbox_style` (S37's table); the other undrawn textbox sub-options noted. **Struck part:** Bokeh's clipping of an off-frame Label (no batch gate found it). Effort S. Sources: WP-30-S56; BUGS.md P1.10 residual.

86. **Served worker races.** library-internal `catch_warnings` (pandas, numpy) can swap `warnings.filters` for one block (Python 3.14's `-X context_aware_warnings` removes it); a free-threaded interpreter recomputes inline; a brush made while a move waits is cleared when drawn. Effort M. Sources: WP-30-S57; BUGS.md P1.31b residual.

87. **CSP: 'unsafe-eval' and style 'unsafe-inline'.** script-src keeps `'unsafe-eval'`, style-src `'unsafe-inline'`; the launcher's header cannot carry the nonce (blocked on Bokeh). Effort L. Sources: WP-30-S04; manifest item 29.

88. **Hash-pinned installs; the bokeh 3.10 verification.** dash_setup does no hash-pinned installs (WP-29 OQ7); the ceiling is <3.10 because 3.10 was not verified: raising it needs S41's scratch-environment leg (kept: S41 did not verify 3.10). Effort S. Sources: WP-30-S41; manifest item 30; BUGS.md P1.30 residual.

89. **by() panel-label box restyling.** `subtitle(, fcolor() lcolor() nobox)` restyles twoway's box; dash names them. Effort S. Sources: WP-30-S53 (ratification row 36); BUGS.md P1.15c residual.

90. **A recast density or histogram after a move.** the saved page marks a recast kdensity or histogram stale after a filter move where the un-recast one is recounted. Effort S. Sources: BUGS.md P1.8b residual.

91. **Bar marker labels at 12 o'clock.** twoway's bar labels default to 12 o'clock where dash draws them at 3, so a missing mlabvposition() row on bar falls back to 3. Effort S. Sources: BUGS.md P1.24 residual ("filed by the closeout").

92. **s1color's plot region and per-panel notes.** s1color's unfilled plot region (shadestyle plotregion none, not in the scheme files) is filled with color plotregion; the served app repeats a sub-option note once per by() panel. Effort S. Sources: BUGS.md P1.20a residual.

### P3: docs, tests, paperwork

1. **Retire or fix `scripts/regen_option_surface.py`.** Running it strips working code and kills the ignored-option note. Only a comment guards it. Effort S. Sources: REM-05-04-C3.
2. **Make the help's Unsupported list and the note accurate.**
   - Generate the list and check it both ways. About 35–40 undeclared ignored options are missing from it (ciplot, ttitle, xvarformat, ndots and others).
   - The note adds `()` to bare flags.
   - The note should print canonical names, not the typed prefix.
   - `vertical` and tsline `sort` should not be named; `twoway` ignores both.
   - The kernel-flag text is stale.

   Effort M. Sources: REM-§2-help-undeclared, REM-05-04-HELPLIST, GAPS2-A4-r, GAPS2-B14-g, GAPS2-C9-f, REM-S05-04-notefmt, REM-05-04-B5, REM-§2-S06-vertical, REM-S05-04, GAPS2-A1-c, AUDIT-M3, REM-05-04-B2, REM-05-04-C12, REM-§2-S09-xymtick, REM-§2-S09-varformat, REM-§2-S09-varlabel, REM-S08-a, REM-S08-b, REM-05-04-S09-d, REM-05-04-S09-e, GAPS2-A4-i, GAPS2-B14-d, GAPS2-B14-e, GAPS2-C9-e.

   Implementing `xvarformat()`/`xvarlabel()` and the y forms is S if chosen over documenting them. [WP-29 note (S02): sort and sort() are still named on mspline, mband, lfit, qfit, lowess, lpoly and fpfit although twoway's output is identical with and without them (M5)] [WP-30 note (S58): loses `xvarformat()`/`yvarformat()` (P1.5)]
3. **Stale versions, docstrings and tracking documents.**
   - dash_render.py still says 1.0.0 with the old dependency floors.
   - The ServerAppBuilder security and origin docstrings are wrong, and a dead `title_safe` variable remains.
   - The app header and banner say `bokeh serve` and localhost.
   - GAPS.md's executive summary, ROADMAP's open count, the BUGS "Not fixed" preambles and test_geometry_visual.md are stale; the CSP claim there was not re-probed.
   - CHANGELOG has no S06 entry.

   Effort S. Sources: REM-01-03-version, GAPS2-H4f, GAPS2-J8-h, REM-09-07-SERVER-ESCAPE-DOCSTRING, GAPS2-F9a, GAPS2-F9b, GAPS2-F9d, GAPS2-K11-a, GAPS2-K11-b, GAPS2-K11-c, GAPS2-K11-d, REM-S06-d. [WP-30 note (S58): S08's dead served `_SIZE_MAP` global and `OptionTranslator._SIZE_MAP` (needs `_generate_app_source`); `_GSIZE_PT`'s `third_tiny` 1 pt and `ehuge`; `svg_truth.py`'s `svg_fills` docstring (Stata 19.5 writes polygons, S24); R58-14's "named in a warning" (dash.sthlp 1312-1313, 2123, 2919, 2962, 2967, 3023; three test lines pin it) and `test/cert_helpers.do:101-110`; 58-05's kept names: `_dash_graph_color` (test_colour_grammar.py calls it, so it is not dead) and the served template comment "lowess, scatteri and pci pass no label" inside the emitted template text (scatteri now passes a label); dash_render.py's docstring "Version: 1.0.0" (GAPS2-H4f's version string)]
4. **Help content gaps.**
   - Qualifier semantics: an overlay example, and how qualifiers behave with `link()`.
   - Date-axis precedence: log overridden on a date axis, and %tC.
   - A false claim that a flood "cannot flood the log" (Tornado logs every 429).
   - No iframe note, no Author section, and Jump To lists 16 of 30 sections.

   Effort S. Sources: REM-06-06-B7, REM-08-04-B5, GAPS2-F9e, GAPS2-J7-d, GAPS2-J8-a, GAPS2-J8-f, GAPS2-J8-g. [WP-30 note (S58): J7-d's iframe sentence (S22)]
5. **Examples coverage.** No example uses bar, fpfit, the immediates, pccapsym, pcbarrow, pcscatter, tsline, csv, weights or serve. The feature_tour header is stale, and no test checks coverage. Effort S. Sources: GAPS2-J10-a, GAPS2-J10-b, GAPS2-J10-c, GAPS2-J10-d, GAPS2-J10-e, GAPS2-J10-f, GAPS2-J10-g, GAPS2-J10-h, GAPS2-J10-i.
6. **Stata-side end-to-end tests are missing for:**
    - `dash build, server` and `dash serve` layer output
    - computed layers on %t variables
    - the serve start line in the Stata log
    - a served build from an installed tree
    - per-type `by()` parity
    - an `inspect.getsource` fallback

   Effort M. Sources: REM-§4-i, REM-08-04-C10, REM-08-04-C13, REM-08-05-C15, GAPS2-I1-e, REM-15-03-B12, REM-15-03-C14a, REM-15-03-C14b, REM-B1-testgap.
7. **Truth fixtures.**
   - 14 fixtures have no committed generator, and there is no `make truth` target.
   - Nothing checks fixture metadata, and absolute paths sit in the extract do-files.
   - The visual truth covers only 4 of 20 schemes, with no histogram render.
   - There is no Stata truth for weighted bands, six kernels, pattern lengths or on-edge values.

   Effort L. Sources: GAPS2-K3-a, GAPS2-K3-b, GAPS2-K3-c, GAPS2-K1-c, GAPS2-K1-d, GAPS2-D0-fixture, GAPS2-D19-c, GAPS2-D4-e, GAPS2-C12-a, GAPS2-C12-b, GAPS2-C12-c, GAPS2-C12-d, GAPS2-C14-b. [WP-30 note (S58): loses the extractor-path part (IR-8), keeping the `W29_REPO` convention; `abbrev_truth.json`'s `mls` (S32); `value_truth.json` connect/recast rows and `regen_option_surface.py:102` (S40/S45); K3's generator parts (S03)]
8. **Test-harness gaps.**
   - A server fixture leaks a process when `__enter__` fails.
   - Report-truth is not checked against ServerAppBuilder.
   - There are no tests of linked computed layers with qualifiers.
   - The axis truth test is vacuous, and the dead-key and minmax-with-qualifier guards are missing.
   - Scheme-key enumeration is hand-written, and the CSS guard has no served arm.
   - There is no dispatch AST count and no self-contained-app test; the allowance and copied-method guards are weak.
   - Tracking-document drift is unchecked.

   Effort M. Sources: REM-14-01, REM-05-04-C9b, REM-06-06-A5, REM-06-06-B6d, REM-09-02-T-TRUTH, REM-09-02-T-SERVER, REM-09-02-T-DEADKEY, REM-09-02-T-MINMAXQ, REM-08-04-C9, REM-11-04-B7, REM-11-04-B9, REM-11-04-C10, REM-15-03-B10, REM-15-03-B11, REM-15-03-C12b, REM-15-03-C13, GAPS2-K11-e.
9. **CI, linting and browser coverage.** There is no CI, no pyflakes/ruff (51 findings in the renderer), no bandit and no secret scan. Dev dependencies are undeclared, and there is no environment surface in the adversarial registry. Only headless Chrome is tested; interaction runs under node stand-ins, and load at scale is unmeasured. Effort L. Sources: GAPS2-K-intro-a, GAPS2-K-intro-b, GAPS2-J-intro-a, GAPS2-G14-e, GAPS2-I9-a, GAPS2-I9-b, GAPS2-K10-d, GAPS2-K5-d, GAPS2-I1-f. [WP-30 note (S58): the two requirements files and the bokeh window comment exist (S05/S41); the next bokeh minor needs S41's re-verification leg; K5-d (IR-16); the hash-pinned installs move to P2.88]
10. **Code structure.** dash_render.py is one 32k-line module, and the server app is emitted as string literals. Facet orchestration is duplicated, and the JS and Python statistics have no shared case table. Effort XL. Sources: GAPS2-K10-a, GAPS2-K10-b, GAPS2-K10-c, GAPS2-K10-e, REM-15-03-A2.
11. **Dashboard extensions (not `twoway` parity).**
    - KPI cards take no weights and lack kurtosis, semean and range.
    - There is no multi-select filter, "(missing)" option, slider direction or reset button.
    - Only one link group is allowed, and the brush cannot act as a filter.
    - There is no print stylesheet, and the PNG export has no KPIs or header.

    Effort L. Sources: GAPS2-E7a, GAPS2-E7b, GAPS2-G13, GAPS2-E13a, GAPS2-E13b, GAPS2-E13c, GAPS2-E13d, GAPS2-E9, GAPS2-E5c, GAPS2-E5d, GAPS2-J7-e, GAPS2-E10a, AUDIT-84, GAPS2-K-intro-c. [WP-30 note (S58): the beforeprint layout of every tab (item 28, S22); the SVG has the PNG's omissions (S54); E10a; J7-e]
12. **Accessibility (no ARIA or alt text) and English-only interface.** Effort L. Sources: GAPS2-J-intro-b, GAPS2-J-intro-c. [WP-29 note (S12): the stale cue's role=status line (aria-live) inside the shadow DOM is not checked with a screen reader]

By design, no task needed: AUDIT-50, AUDIT-56, AUDIT-70, AUDIT-73, AUDIT-77, AUDIT-79, AUDIT-80, AUDIT-83, AUDIT-85, AUDIT-86, REM-S11-c.

## 4. Decisions needed

- **The 79 accepted-but-ignored options (REM-§2-decision).** Choose (a) implement all, or (b) implement the high-value subset and formally re-disposition the rest in ROADMAP/CHANGELOG. Of the named subset, `text`, `ttitle`/`tlabel`, the edge titles, `mstyle`, `lstyle`, `gap`, `fxsize`, `fysize` and `scale` are still open. [WP-30 note: drawn since WP-30: text/ttext (P1.10), the t-options (P1.6), named styles (P1.14a/b), mlabvposition/mlabtextstyle (P1.24), connect/cmissing/recast (P1.8a/b), horizontal (P1.9a/b), axis look and add (P1.18a/b), region styling (P1.20a/b), reference-line sub-options (P1.21a/b), x/yvarformat (P1.5); the rest stay named (P2 rows)]
  - Candidates to re-disposition (accept and report): the stroke-alignment options (Bokeh has no equivalent) and `play()` (AUDIT-14).
- **Line join order (P0.1).** Following `twoway`'s data order means flipping the tests that pin x order, and it changes existing dashboards. [Decided for WP-29: M1, MATCH twoway. line, connected, area, rline, rarea, rconnected (and every other connecting type) join in data order unless `sort` or `sort(varlist)` is given; `sort(varlist)` is honoured. Existing tests that pin x order are FLIPPED (with the reason), never deleted.; commit b0d170d]
- **lpoly bandwidth (P0.7).** Option (a): take Stata's `r(bwidth)` from `lpoly …, nograph` at registration. This is exact at build time, but the served recompute after a filter move and the saved page still need a rule. Option (b): port Stata's rule of thumb per kernel and degree to Python. Rule (b) is compiled Mata, so the port is only partly verifiable. [Decided for WP-29: M2, PORT Stata's arithmetic to Python: the per-kernel, per-degree rule-of-thumb default bandwidth, and lpolyci's analytic CI band with `pwidth()` and `var()`. Verified against Stata truth fixtures. Must hold in served recomputes after a filter move. The bootstrap band is removed.; commit 758cf59]
- **lpolyci band (P0.9).** Implement the analytic band (which also removes the ~100× cost), or keep the bootstrap as a documented difference. [Decided for WP-29: M2, PORT Stata's arithmetic to Python: the per-kernel, per-degree rule-of-thumb default bandwidth, and lpolyci's analytic CI band with `pwidth()` and `var()`. Verified against Stata truth fixtures. Must hold in served recomputes after a filter move. The bootstrap band is removed.; commit e32be3a]
- **Saved-page refit (P0.17, DISCOVERY Q3).** Keep it deferred with a visible stale cue, or port every estimator to JS (XL). [Decided for WP-29: M3, A VISIBLE STALE CUE on computed layers (fits, smooths, densities that are frozen) on the saved page after a filter move. The served app keeps refitting. No JavaScript estimator port.; commit b242b99]
- **Unbinned `colorvar()` (DISCOVERY Q5).** dash maps it continuously; `twoway` bins it at the z-axis ticks. Sources: GAPS2-X2-r1, GAPS2-A8-f, AUDIT-18.
- **Third-party and PLUS schemes (DISCOVERY Q30).** They are currently refused, and an inherited `c(scheme)` falls back to s2color. Sources: GAPS2-X5-b, AUDIT-74. [Decided for WP-30: M7, the whole ado-path: scheme(NAME) and an inherited c(scheme) are found along Stata's ado-path under name, containment, regular-file and size guards; P1.25b, commit 15c4f7b]
- **Refuse vs note.** `twoway` refuses typos, options it rejects outright (`title2`, `ciopts`, …) and options on inapplicable types, but dash notes them (TP-07). Sources: AUDIT-07, GAPS2-B28-a, GAPS2-B28-b, GAPS2-B28-c, GAPS2-A12-d, AUDIT-58, P2.21. [Decided for WP-30: M5, refuse like twoway: input twoway refuses is refused with twoway's rc and words in WP-30's new code (P1.1, 5, 6, 8, 9, 10, 13, 15, 18, 19, 20, 21, 24, 27); the remaining sweep is P2.21]
- **"Drew nothing" notes where `twoway` is silent.** Keep the deliberate report or match `twoway`. Sources: GAPS2-A11, GAPS2-C8. [Decided for WP-30: M6, match twoway: silent where twoway draws the same picture and prints nothing (P1.26b, commit 824e0be; P1.18a, commit ebde0e9); GAPS2 A11/C8 stays open (BUGS.md:2559)]
- **Size units (P1.12).** Moving to Stata's relative units changes the look of every existing dashboard. [Decided for WP-30: M1, match Stata: Stata's relative size units and each scheme's look (P1.12a a1dcb2f, P1.12b 37e9fa4; P1.2a 6a777a3, P1.2b 870e778; P1.3a bde085e, P1.3b 8573347)]
- **Served-app authentication (P0.12).** Add a token or cookie (changes the user experience), or formally scope dash as single-user and document it. [Decided for WP-29: M4, A per-launch secret TOKEN required by the served app (Stata opens the tokenized URL); the app, spec and data files are written 0600 inside a 0700 directory. *Ratified answers of 01oct2026 (binding reading):* the token is never missing, because an app started by hand makes its own (S13 K-1..K-8); and "0600 inside a 0700 directory" holds wherever the location allows: a location that is not private is noted, never refused, and a folder the user names is never refused or re-moded (S08 R-8). *Round 2 (01oct2026, binding):* the key is never printed, except once, after a warning line, when no link file can be written anywhere, and the server keeps serving (S13 K-9, answer A); dash starts its served app only from the bytes it read through a descriptor it opened and verified, never by path (S08 R-9, answer B).; commit 7f5c8f5; also fd51038]
- **`graph export` companion (P1.28).** Headless-browser export (a dependency dash cannot ship) vs documented non-support plus `r(filename)`. [Decided for WP-30: M8, document plus an SVG button: r(filename), the stale-graph note, Save as SVG on every toolbar (P1.28a eea99ce, P1.28b fd4fff0); scripted export is the platform package]
- **Support floor.** Should Python stay at 3.13 or return to 3.11 (P1.33)? Should the declared minimum Stata be raised to 19, or should Stata 16–18 and BE be tested (P1.35)? Also choose a bokeh ceiling policy (P1.30). [Decided for WP-30: M2, Stata 19 declared and enforced (P1.35, 1f05b63); M3, Python floor measured: 3.11 (P1.33, dcbca5d); M9, bokeh 3.8 to <3.10, raised only after re-verification (P1.30, 61f5c21)]
- **Accessibility and localisation scope (P3.12).**

## 5. Chunks that failed to report

None.