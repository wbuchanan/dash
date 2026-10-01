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

1. **Line-type plots are joined in x order, not data order; `sort(varlist)` is ignored.** line, connected, area, rline, rarea and rconnected always sort by x, so `twoway line y x` without `sort` draws a different picture, with no note. Tests pin the x order (see Decisions). Effort M. Sources: GAPS2-A1-a, AUDIT-08, REM-§2-S06-sort, REM-S06-b, GAPS2-A4-o, GAPS2-B12-e, AUDIT-10, GAPS2-G15-b, GAPS2-A1-c.
2. **`by()` panels use independent scales by default.** A plain `by(foreign)` autoranges each panel separately; axes are shared only when ticks or a range are given explicitly. `by(, yrescale)` is named in the note and ignored. Effort M. Sources: GAPS2-B4-a, GAPS2-B4-b.
3. **Unlabelled variables get blank axis titles, legend keys named after the plot type, and blank tooltip labels.** `twoway` uses the variable name. The test data helper gives every variable a label, which hides this. Effort S. Sources: REM-08-05-C3b, REM-08-05-C3a, REM-08-05-M3.
4. **`xtitle(, size())` or `ytitle(, color())` with no text deletes the default title.** For example, `ytitle(, size(large))` removes the y title in both modes. Effort S. Sources: CRIT-01.
5. **`axis(2)` on `ylabel`/`yscale`/`yline`/`xtick` is applied to axis 1.** `yscale(log axis(2))` logs the primary axis, and the note names only `axis(2)`. `ytitle(, axis(2))` is already routed correctly. Effort M. Sources: REM-09-02-AXIS-N, GAPS2-B15-a, AUDIT-27, GAPS2-B22-c.
6. **`function` evaluates `^` right to left and accepts `pi` and `e`.** `2^3^x` at x=2 draws 512 where Stata gives 64. `pi*x` draws, where `twoway` refuses it r(111). Effort S. Sources: GAPS2-A6-d, GAPS2-C5-g, GAPS2-A6-c.
7. **The lpoly/lpolyci default bandwidth is wrong.** It ignores `kernel()` and `degree()` (10–90% too small, e.g. biweight degree 2: 63.8 vs 302.5). Even the Epanechnikov degree 0/1 default is off by −22% to +14%, and 185 vs 77 on a 7-observation sample (see Decisions). Effort M. Sources: GAPS2-A9-a, GAPS2-A9-b, GAPS2-C1, GAPS2-C13, AUDIT-24, GAPS2-C12-e.
8. **Computed layers on a date variable run in milliseconds.** histogram/kdensity densities are per ms, and `width()`, `start()` and `bwidth()` are read as ms. lpoly/lpolyci draw nothing. histogram/kdensity put the date axis on Y. Effort M. Sources: REM-08-05-C6d, REM-08-04-C2, REM-08-05-C6c, REM-08-04-C3a, REM-08-04-C12.
9. **The lpolyci band is a bootstrap percentile band, not Stata's analytic band.** Band width is 0.51–1.33× Stata's, and edges are off by up to 2.25 mpg. `pwidth()` and `var()` are ignored. It costs about 100× lpoly. Effort L. Sources: AUDIT-23, GAPS2-A10-a, GAPS2-C7-a, GAPS2-C7-b, GAPS2-A10-b, GAPS2-C7-c, GAPS2-C7-e.
10. **A variable named only in `hover()` is never exported.** Both routes and both modes drop it silently, with rc 0 and no note. Two cscripts (DL-03e, AL-19) pin the defect and must change. Effort S. Sources: REM-09-07-HOVER-EXPORT, GAPS2-G16-res, REM-09-07-HOVER-TEST.
11. **The saved page embeds rows that `if`/`in` exclude.** Every row of each drawn variable is in the HTML source, and the help does not disclose it. Effort M. Sources: GAPS2-I2-a, GAPS2-I2-b.
12. **The served app has no credential, and its files are world-readable.** Any local account can open a session and read the data. The app and the spec/data JSON are written 0644; on macOS the per-user 0700 temp directory mitigates this, and the shared-/tmp case on Linux is unmeasured. The help's "only this machine" wording understates this (see Decisions). Effort M. Sources: GAPS2-I3-a, GAPS2-I3-b, GAPS2-I3-c, AUDIT-87.
13. **Server lifecycle.**
    - Killing Stata leaves the server running, holding its port and the data.
    - Temp files survive a crash.
    - Break in GUI Stata cannot stop `dash serve`: sfi `pollstd` is never called.
    - The messages tell GUI users to press Ctrl+C.

    Effort M. Sources: GAPS2-F2a, GAPS2-F2b, GAPS2-F4, GAPS2-H2a, GAPS2-F9c, GAPS2-H2b.
14. **One-line preview pages are never deleted and are 0644.** 39 orphans of about 1.2 MB each were observed. Nothing prunes them and nothing documents them. Effort S. Sources: GAPS2-X3-a, GAPS2-X3-b, GAPS2-X3-c.
15. **After a filter move, the saved page registers per-plot rows rather than the intersection.** In a linked `by()` graph, or a linked graph with its own graph-level qualifier, a layer with its own `if` then draws rows outside its panel. The served app is correct. Effort S. Sources: REM-06-06-C7.
16. **The `colorvar()` range ignores qualifiers.** On the saved page it spans every row under a per-plot `if`. In both modes it ignores a linked graph's graph-level qualifier. Which colour key `twoway` draws under `by()` is UNCLEAR (not measured). Effort S. Sources: REM-06-06-C8b, REM-06-06-C8b-link.
17. **Saved-page fits go stale after a filter move, with no cue.** Filtered points sit under a fit computed on all rows. The full refit is a decision (see Decisions); a visible stale cue is the small fix. Effort S (cue). Sources: GAPS2-C4, GAPS2-E4a, GAPS2-E4c, AUDIT-38.
18. **The served redraw keeps build-time bar/rbar widths.** After a move, bar widths stay 56 where the qualified saved draw gives 168. An emptied lowess panel keeps its style. bar and rbar are not in the moved-layer tests. Effort S. Sources: REM-15-03-C15.
19. **`dash_setup` fails on externally-managed Pythons (PEP 668, e.g. Homebrew).** There is no detection and no `venv()` option. The manual fallback names a bare, unquoted `python`, and the single-quoted hint breaks in cmd.exe. The `--user` site is not added to the path, there is no ensurepip hint, and the help gives no guidance. Effort M. Sources: GAPS2-H7a, GAPS2-H7b, GAPS2-H7c, GAPS2-H7d, GAPS2-H7e, GAPS2-H7f, GAPS2-H7g.
20. **KPI `sd`, `var`, `iqr`, `cv` and `sum` of a date are computed in epoch ms.** `sd` is 86,400,000× Stata's value on a %td variable. Effort S. Sources: GAPS2-E1-residual.

### P1: common `twoway` usage not honoured

1. **Stylelists across an expanded varlist.** `scatter mpg turn weight, mcolor(red blue) msymbol(O T)` gives every y the whole list. The renderer then refuses "red blue" and draws scheme defaults, with a misleading note. The same holds for line style lists, the `.`/`=` shorthands, and a single-y list (where `twoway` uses the first element). Effort M. Sources: REM-S06-c, GAPS2-D8-a, GAPS2-D8-b, GAPS2-D8-c, GAPS2-D8-d, GAPS2-D8-e.
2. **Default look differs from the schemes.**
   - The title is bold and left-aligned (Stata centres it and does not bold it).
   - Axis titles are italic.
   - Subtitle, note and caption sit at x=0.
   - Bokeh minor ticks are drawn and tick geometry is Bokeh's.
   - s2color's vertical y tick labels are missing, as is stcolor's dashed grid.
   - s1rcolor's ticks are invisible (black on black), and economist's y axis is wrong.
   - Markers are drawn at alpha 0.8, and `fintensity()` is applied as alpha.

   Effort M. Sources: GAPS2-D17-a, GAPS2-D17-b, GAPS2-D17-c, GAPS2-D17-d, REM-11-04-A1-ALIGN, GAPS2-B29, GAPS2-D16-a, GAPS2-D16-c, GAPS2-D16-d, GAPS2-D12-a, GAPS2-D12-b, GAPS2-D12-c, GAPS2-B25-c, GAPS2-D11-a, GAPS2-D11-b.
3. **The default ticker and range padding are Bokeh's, not natscale.** Every default axis gets BasicTicker and 10% padding. Effort M. Sources: GAPS2-B25-a, GAPS2-B25-b.
4. **Scheme keys do not reach every layer type.**
   - sttrans opacity is missing on fits, spikes, ranges, immediates and bands.
   - Histograms ignore the scheme's histogram colour, intensity and line width.
   - Hollow and sm* p# symbols are drawn filled and full size.
   - rarea is drawn at alpha 0.5.
   - Marker-label size and colour are fixed at 10px #444444.
   - The ColorBar has no chrome.
   - Unconsumed user-scheme directives are ignored silently.

   Effort M. Sources: GAPS2-D18-a, GAPS2-D18-b, GAPS2-D18-c, GAPS2-D18-d, AUDIT-76, GAPS2-D19-a, GAPS2-D19-b, GAPS2-D5-g, GAPS2-D5-h, REM-11-04-B13-RAREA, REM-11-04-B1, REM-S11-e2, GAPS2-D10-b, GAPS2-D10-a, REM-11-04-C11.
5. **Axis format fallbacks.**
   - Default ticks ignore the variable's display format: weight %9.0fc gives 2000, not 2,000.
   - %g/%gc formats are never used as the fallback.
   - `xlabel(, format(%td…))` is silently ignored.
   - A numeric `format()` on a date axis writes epoch ms.
   - The help's log example promises commas that dash does not write.

   Effort S. Sources: REM-09-02-FMT-a, REM-09-02-FMT-b, GAPS2-G10-a, GAPS2-G10-b, REM-09-02-DATE-FORMAT, REM-08-04-C6b, GAPS2-B8-b, REM-08-04-C6a, GAPS2-G10-c.
6. **tsline time-axis options.** `tlabel`, `ttick`, `tmlabel`, `tmtick`, `ttitle`, `tscale` and `tline` are undeclared and only named in the note. They need folding onto the x equivalents, with date-literal expansion. Effort M. Sources: REM-§2-S09-tlabel, REM-§2-S09-ttick, REM-§2-S09-tline, REM-§2-S09-ttitle, REM-S09-73-tsaxis-a, REM-S09-73-tsaxis-b, REM-05-04-S09-a, REM-05-04-S09-b, GAPS2-A4-q, GAPS2-B14-a, GAPS2-B14-b, GAPS2-B14-c, REM-15-03-E5.
7. **Time-series operators in plot varlists are refused r(101).** This covers `line D.close date`, `tsline D.gdp` and `lfit y L.x`, and the help does not document it. Effort M. Sources: GAPS2-G4-a, GAPS2-G4-b, GAPS2-G4-c.
8. **`connect()`, `cmissing()` and `recast()` are not honoured.** `scatter y x, c(l)` draws no line, stairsteps and `connect(L)` panel lines are impossible, and missing values are always bridged. Effort M. Sources: REM-§2-S06-connect, REM-S05-04-connect, GAPS2-A4-l, GAPS2-A4-m, GAPS2-A4-n, GAPS2-B12-b, GAPS2-B12-c, GAPS2-B12-d, AUDIT-09, AUDIT-11, AUDIT-12, GAPS2-G15-a.
9. **`horizontal` is not drawn on any type.** It is common on bar, rcap, rspike and dropline. Effort L. Sources: REM-§2-S06-horizontal, REM-S06-a, GAPS2-A7, GAPS2-B12-a, AUDIT-15.
10. **`text()` and `ttext()` annotations are not drawn.** Effort M. Sources: REM-§2-S09-text, REM-S09-73-text, GAPS2-B20-a, AUDIT-13, REM-§2-S09-ttext, GAPS2-B20-b.
11. **SMCL and TeX in graph text.** `{bf:}`, `{it:}`, `{sup:}`, `{&beta}` and `{c #}` are drawn literally. `$$…$$` in a title triggers MathJax, which grows the page from 1.3 MB to 3.1 MB. Effort M. Sources: GAPS2-D3-a, GAPS2-D3-b, GAPS2-D3-c, GAPS2-D3-d, GAPS2-D3-e, GAPS2-J2, GAPS2-B13, GAPS2-J5.
12. **Size units.** Numbers are read as pixels and keywords use a private pixel ladder: `msize(medium)` gives 11px against a default of 8. `#pt`, `*#` and `vhuge` are refused, `mlabgap` is read as px, and `vvvthin` is missing (see Decisions). Effort M. Sources: GAPS2-D2-a, GAPS2-D2-b, GAPS2-D2-c, GAPS2-D2-d, GAPS2-D2-e, GAPS2-B9.
13. **Colour syntax.** `navy*.5`, `*.5`, CMYK, HSV and bg/fg are refused. An unreadable scheme colour falls back to #000000. Effort M. Sources: GAPS2-D7-a, GAPS2-D7-b, GAPS2-D7-c, GAPS2-D7-d, GAPS2-D7-e.
14. **Named styles.** `pstyle()` works only on the four CI fits. `lstyle`, `mstyle`, `mlstyle`, `astyle`, `alstyle`, `bstyle` and `dstyle` are not read. Effort L. Sources: REM-§2-S09-lstyle, REM-§2-S09-mstyle, REM-§2-S09-areastyle, REM-S09-73-namedstyles, REM-05-04-S09-g, GAPS2-B11-a, GAPS2-B11-b, GAPS2-B11-c, GAPS2-D6, AUDIT-29, AUDIT-30.
15. **`by()` sub-options and chrome.**
    - `rows`, `holes`, `colfirst`, `title`, `note`, `legend()`, `i*` axes and `compact` are named in the note and ignored.
    - Every panel draws a legend and repeats both axes.
    - Panel labels are appended to the graph title, and there is no "Graphs by" note.
    - Composite and missing panels are titled differently from `twoway`.
    - Facet aspect ratios miss the automatic layout.

    Effort L. Sources: GAPS2-B16-a, GAPS2-B16-b, GAPS2-B16-c, GAPS2-B16-d, GAPS2-B16-e, GAPS2-B26-d, GAPS2-B31-a, GAPS2-B31-b, GAPS2-B31-c, GAPS2-B31-d, AUDIT-71, AUDIT-72, REM-10-03.
16. **Legend keys and default titles do not match `twoway`'s text.**
    - lowess, lpoly, mband, mspline and function are all keyed "Fitted values".
    - histogram and kdensity are keyed by the variable label, where `twoway` writes "Density" and "kdensity var".
    - The pc family and scatteri/pci are keyed by the type name.
    - The y title comes from the first layer even when the layers' labels differ.
    - Range types get no y title.

    Effort S. Sources: GAPS2-A13-a, GAPS2-A13-b, GAPS2-A13-c, GAPS2-A13-d, GAPS2-A13-e, GAPS2-A13-f, GAPS2-C10-a, GAPS2-C10-b, GAPS2-C10-c, GAPS2-C10-d.
17. **Bar and range geometry.**
    - bar and rbar default to 0.8× the smallest x gap, not 1 x-unit.
    - rbar ignores `barwidth()` with no note.
    - bar's base is 0, not `twoway`'s rule.
    - rcap cap width ignores `msize()`, and rcapsym draws caps `twoway` does not.
    - When 0 is outside the data, area, bar, spike and dropline draw from 0 and extend the axis to it.

    Effort M. Sources: GAPS2-A3-a, GAPS2-A3-b, GAPS2-A3-c, GAPS2-A3-d, GAPS2-A3-e, GAPS2-A3-f, AUDIT-44, AUDIT-42.
18. **Common axis sub-options.** `nolabels`, `noticks`, `xscale(off)`, `noline`, axis line colour, width and pattern, `alt` and `titlegap` are not honoured. `angle(rvertical)`, `angle(stacked)` and other anglestyle names are dropped silently. `labcolor`, `tlength`, `tposition` and `add` are not honoured; `add` replaces the default ticks instead of adding to them. Effort M. Sources: GAPS2-B21-c, REM-09-02-NOLABELS-NOTICKS, REM-09-02-SCALE-OFF, REM-09-02-SCALE-LINE, REM-09-02-SCALE-TITLEGAP, GAPS2-B23-b, GAPS2-B23-c, GAPS2-B23-d, GAPS2-B23-e, GAPS2-B23-f, REM-09-02-LABEL-ANGLE, GAPS2-D9-a, REM-09-02-LABEL-LABCOLOR, REM-09-02-LABEL-TICKGEOM, REM-09-02-LABEL-ADD, GAPS2-B21-e, GAPS2-B21-f, AUDIT-28.
19. **Sub-option abbreviations are not recognised.** This covers legend `c()`, `r()`, `lab()` and `posi()`; axis `labs()`, `glc()` and similar; and xline's `lc()`, `lp()` and `lw()`. Effort S. Sources: GAPS2-B17-a, GAPS2-B21-d, REM-09-02-LABSIZE-ABBREV, GAPS2-B22-b.
20. **`plotregion()`/`graphregion()` sub-options are dropped with no note.** `margin()`, `style(none)`, graphregion `lcolor`/`lwidth`, the `i*` options and the abbreviations `fc()`/`lc()` all have no effect, and nothing is reported. Effort M. Sources: GAPS2-B18-a, GAPS2-B18-b, GAPS2-B18-c, GAPS2-B18-d, GAPS2-B18-e, GAPS2-B18-f, AUDIT-66.
21. **`xline`/`yline` limits.** Numlists such as `xline(2000(500)3000)` draw nothing. `lstyle`, `noextend` and `lalign` are only named. Effort S. Sources: GAPS2-B22-a, GAPS2-B22-d, GAPS2-B22-e, AUDIT-64.
22. **`function` evaluates only 10 functions.** `normalden`, `normal`, `ln`, `_pi`, `c(pi)`, comparisons, `cond`, `min`, `max`, `round`, `int`, `scalar()` and `_b[]` all draw nothing. Evaluating in Stata at registration is a candidate fix. Effort M. Sources: GAPS2-A6-a, GAPS2-A6-b, GAPS2-C5-a, GAPS2-C5-b, GAPS2-C5-c, GAPS2-C5-d, GAPS2-C5-e, GAPS2-C5-f, AUDIT-53.
23. **Date-axis residuals.**
    - scatteri/pci/pcarrowi coordinates and `function range()` are drawn at raw SIF values (1970).
    - Range and pc plots with date y get no date axis.
    - A layer on `yaxis(2)`/`xaxis(2)` turns the primary date axis numeric, and the secondary date axis shows epoch ms.
    - A date layer beside a numeric layer on one axis is drawn at epoch ms with no warning.
    - Base 0 is 1970, not 1960.
    - A date `colorvar` key shows ms.
    - Fallback tooltips ignore formats.
    - The histogram tooltip always says "Count".

    Effort M. Sources: REM-08-04-C7, REM-08-04-C7b, REM-08-04-C3b, REM-08-04-C3c, REM-08-04-C4, REM-08-04-B2b, REM-08-04-B7a, REM-08-04-B4, REM-08-05-M1, REM-08-05-C7c, REM-08-05-C10, REM-08-05-M2.
24. **`mlabvposition(varname)` is not drawn.** It and `mlabtextstyle` are declared and pending but never serialised, and no test checks that declared options reach the spec. Effort M. Sources: REM-§2-S09-mlabvpos, REM-S09-73-mlabpos, REM-05-04-S09-r, GAPS2-A4-p, GAPS2-B27-c, AUDIT-33, REM-05-04-B6.
25. **Scheme resolution.** `scheme(NAME)` never tries Stata's own `scheme-NAME.scheme` file name. Six StataCorp schemes, including meta and stcolor_mv, are refused r(198) where `twoway` draws them. An inherited `c(scheme)` that Stata found is drawn as s2color. `#include` has the same limits. The error message does not list the valid names. Effort M. Sources: REM-§3-f, GAPS2-X5-a, GAPS2-X5-c, GAPS2-X5-d, REM-§3-e.
26. **Notes do not reliably reach the user.**
    - `dash build, server` reports no option or empty-layer notes.
    - The served child's stderr never reaches Stata.
    - Notes print as raw UserWarnings with internal paths.
    - A session `warnings` filter of "ignore" silences them; one of "error" turns a note into r(7102).

    Effort M. Sources: GAPS2-F5a, GAPS2-F5b, GAPS2-X4-a, GAPS2-X4-b, GAPS2-X4-c, GAPS2-X4-d, GAPS2-I-sum-logging, GAPS2-F5c.
27. **Drop-in command-form gaps.**
    - `set graphics off` and batch mode still open a browser.
    - A `twoway`/`tw`/`graph twoway` prefix is refused.
    - `saving(n, asis)` writes a file literally named "n, asis.html".
    - `dash build, saving(f, replace)` is refused.
    - `..` and `&` in a saving path are refused where `twoway` accepts them.

    Effort S. Sources: CRIT-04, CRIT-02, CRIT-03, CRIT-09, GAPS2-I14-a, GAPS2-I14-b.
28. **No `graph export` companion.** `graph export` after dash fails r(601), or silently exports a stale earlier graph. There is no `r(filename)` and no SVG backend (see Decisions). Effort L. Sources: GAPS2-J7-a, GAPS2-J7-c, GAPS2-E10c, GAPS2-J7-b, GAPS2-E10b.
29. **Security hardening.** Both CSPs keep `unsafe-inline`; they need hashes or a nonce, plus a browser test. `%` and `!` in saving paths reach Windows `start` via cmd.exe; whether they expand there is UNCLEAR (unmeasured on Windows). The help does not state saving()'s character rule. Effort M. Sources: GAPS2-I12-a, GAPS2-I12-b, GAPS2-I12-c, GAPS2-I14-c, GAPS2-I14-d.
30. **Dependency window is open-ended.** There is no bokeh ceiling and no run-time `bokeh.__version__` check. The text-sink XSS safety is verified only on 3.8 and 3.9. The setup gate never reports "outside the verified range". dash also depends on Bokeh internals (`match_host`, `templates.FILE`). Effort S. Sources: GAPS2-H4b, GAPS2-H4c, GAPS2-H4d, GAPS2-H4e, GAPS2-I7-a, GAPS2-I7-b, GAPS2-K5-a, GAPS2-K5-b, GAPS2-K5-c.
31. **Served-app resource limits.** There is no concurrent-session cap and no unused-session lifetime. Each session re-decodes the whole dataset. One event loop is blocked by recomputes: lowess takes 27.7 s and lpolyci 8.7 s at N=100k. Effort L. Sources: GAPS2-F3a, GAPS2-F3b, GAPS2-F3c, GAPS2-F3d, GAPS2-I4-a, GAPS2-I4-b, GAPS2-G14-d, GAPS2-C-intro-served-cost.
32. **No render-time dependency guards.** A missing numpy, pandas or bokeh gives a bare ModuleNotFoundError. An old Python gives a SyntaxError. `dash_setup`'s first Python call is uncaptured. Effort S. Sources: GAPS2-H6a, GAPS2-H6b, GAPS2-H6c, GAPS2-H6d.
33. **Python floor 3.13 excludes 3.11/3.12 users.** Setup reports failure although dash may still render (see Decisions). Effort S. Sources: GAPS2-H4g.
34. **Never tested off macOS arm64.** Windows, Linux, Intel Mac and GUI Stata are untested. `arch -arm64` and the maintainer's path are hard-coded in the runners. Whether anything actually breaks is UNCLEAR. Effort XL. Sources: GAPS2-H-intro-platforms, GAPS2-H-intro-gui, GAPS2-K1-a, GAPS2-K1-b.
35. **`version 16.0` is declared, but only StataNow 19.5 is ever run.** Every truth fixture is also 19.5-only (see Decisions). Effort L. Sources: GAPS2-H-intro-stataver, GAPS2-J8-e, GAPS2-K3-d.

### P2: less common options, edge cases, rarely used plot types

1. **Silent dashboard drops.** `layout(s1:1,1 s2:1,1)` drops a graph with no warning. `tabs()` drops unknown names and ignores `layout()` inside a tab. Effort S. Sources: REM-S12-b, GAPS2-E15a, GAPS2-E15b, GAPS2-E15c, AUDIT-82.
2. **Minor ticks and labels (`xmtick`, `ymtick`, `xmlabel`, `ymlabel`) are not drawn.** Bokeh has no labelled minor ticks, so the label half is only partly closable. Effort L. Sources: REM-§2-S09-xymlabel, REM-§2-S09-xymtick, REM-S09-73-minorticks, REM-09-02-MINOR-a, REM-09-02-MINOR-b, GAPS2-B10-a, GAPS2-B10-b, GAPS2-D16-b, AUDIT-61, REM-09-02-T-FEATURES.
3. **Edge titles `t1title` through `r2title` are not drawn.** Effort M. Sources: REM-§2-S09-b1b2title, REM-§2-S09-l1l2title, REM-§2-S09-r1r2title, REM-§2-S09-t1t2title, REM-S09-73-alttitles-tb, REM-S09-73-alttitles-lr, GAPS2-B19-a, GAPS2-B19-b, AUDIT-57.
4. **Textbox sub-options on titles.** `position`, `ring`, `justification` and `span`, and the box, frame and margin options, are not drawn. Effort M. Sources: GAPS2-D17-e, AUDIT-59, AUDIT-60.
5. **Legend sub-options.**
   - `holes`, `colfirst`, `title`, `region`, `color`, key geometry, `bplacement`, `span`, `stack`, `note` and `caption` are not honoured.
   - The scheme's `cols` is dropped when `pos()` is given.
   - Corner positions are centred on a side, and `pos(0)` goes top-right.
   - The key size is fixed.

   Effort M. Sources: GAPS2-B17-b, GAPS2-B17-c, GAPS2-B17-d, GAPS2-B17-e, GAPS2-B17-f, GAPS2-B17-g, GAPS2-B17-h, GAPS2-B17-i, CRIT-10, AUDIT-65, GAPS2-B26-a, GAPS2-B26-b, GAPS2-B26-c, GAPS2-D16-e.
6. **Fit options.** `atobs`, `estcmd()`, `estopts()` and `predopts()` are not honoured, including fpfit's `estopts(degree())`. Neither are `ciplot()`, `fitplot()` and `nofit`. Effort L. Sources: REM-§2-S07-atobs, REM-§2-S07-est, REM-§2-S07-ciplot, REM-S07-13-fitopts, REM-S07-13-ciplot, REM-05-04-S07-c, REM-05-04-S07-d, REM-05-04-S07-e, GAPS2-A4-a, GAPS2-A4-b, GAPS2-A4-c, GAPS2-A4-d, GAPS2-C3-a, GAPS2-C3-b, GAPS2-C9-a, GAPS2-C9-b, AUDIT-20, AUDIT-21.
7. **Distribution and area odds.** kdensity `area()` and `boundary`, histogram `gap()`, function `droplines()`/`base()`, area `nodropbase`, and bar `baroffset`/`mwidth` are not honoured. Effort M. Sources: REM-§2-S07-area, REM-S07-13-kdarea, REM-05-04-S07-b, GAPS2-A4-e, GAPS2-A4-f, GAPS2-A4-g, GAPS2-A4-h, GAPS2-A4-j, GAPS2-A4-k, GAPS2-C3-c, GAPS2-C9-c, GAPS2-C9-d, AUDIT-22, AUDIT-54, AUDIT-55, REM-§2-S09-droplines, REM-S09-73-droplines, REM-05-04-S09-c, REM-§2-S09-bargeom, REM-05-04-S09-j, REM-§2-S09-nodropbase, REM-05-04-S09-t, REM-S09-73-bar-misc.
8. **Arrowheads.**
   - pcbarrow heads fill black: a quick bug fix.
   - `msize()`, `mcolor()`, `mfcolor()`, `mlcolor()` and `mlwidth()` are silently not read.
   - `mangle`, `barbsize` and `headlabel` are not drawn.
   - A pc row missing only its second point is dropped entirely.

   Effort M. Sources: GAPS2-A2-a, GAPS2-A2-b, GAPS2-A2-c, GAPS2-A2-d, GAPS2-A2-e, GAPS2-A2-f, REM-§2-S09-arrowhead, REM-§2-S09-headlabel, REM-S09-73-pcarrow, REM-05-04-S09-i, GAPS2-B27-a, GAPS2-B27-b, AUDIT-35, AUDIT-36, AUDIT-45.
9. **`dot` is drawn as a plain scatter with no dot rows.** The difference is undocumented, and the `d*` options, `ndots` and `dotextend` have nothing to style. Effort L. Sources: REM-05-04-DOTGEOM, GAPS2-A14-a, GAPS2-A14-b, GAPS2-A14-c, GAPS2-A14-d, REM-§2-S09-dotcolor, REM-§2-S09-dotsym, REM-§2-S09-ndots, REM-S09-73-dot-a, REM-S09-73-dot-b, REM-S09-73-dot-c, REM-05-04-S09-o, REM-05-04-S09-p, AUDIT-43.
10. **`colorvar()` coverage.**
    - It is not drawn on line, bar, spike, range or pc types.
    - `clegend`, `plegend`, `colorstart`, `colorend`, `colorrule`, `colorfillonly`, `colorkeysrange`, `colorlist`, `coloruseplegend` and `pcycle` are not honoured.
    - `colorformissing()` is not aliased to dash's working `colormissing()`: a quick win.
    - `colorvar(i.var)` is refused r(111).

    Effort L. Sources: GAPS2-A8-a, GAPS2-A8-b, GAPS2-A8-c, GAPS2-A8-d, AUDIT-16, REM-§2-S09-clegend, REM-§2-S09-colorramp, REM-§2-S09-colormisc, REM-§2-S09-colorlist, REM-§2-S09-pcycle, REM-S09-73-colorvar-a, REM-S09-73-colorvar-b, REM-S09-73-pcycle, REM-05-04-S09-k, REM-05-04-S09-l, REM-05-04-S09-m, REM-05-04-S09-u, GAPS2-B11-e, GAPS2-B11-f, GAPS2-B14-f, GAPS2-X2-r2, AUDIT-19, AUDIT-M1, AUDIT-M2, REM-11-04-B5.
11. **Marker symbol set.** `point`/`p` draws a full 8px circle, `V` is a filled triangle, and sm* and lower-case shorthands draw at full size. `arrow` and `|` are refused, and pipe draws horizontal. `star`, `asterisk`, `hexagon` and `dot` are accepted where `twoway` refuses them. Effort M. Sources: GAPS2-D5-a, GAPS2-D5-b, GAPS2-D5-c, GAPS2-D5-d, GAPS2-D5-e, GAPS2-D5-f, GAPS2-D5-lc.
12. **Line and marker misc.**
    - `lpattern` formulas (`-.`) are refused, including in schemes, and named pattern geometry differs.
    - `mlpattern`, `lwidth(none)` and msangle anglestyle names are not honoured.
    - `mlalign`, `mwidth`, `mlabstyle` and `mlabtextstyle` are not honoured.
    - The alignment options have no Bokeh equivalent.
    - Area outline options work only on the CI bands.

    Effort M. Sources: GAPS2-D4-a, GAPS2-D4-b, GAPS2-D4-c, GAPS2-D4-d, GAPS2-B11-d, AUDIT-32, CRIT-06, CRIT-07, REM-§2-S09-mlabstyle, REM-05-04-S09-s, REM-S09-73-marker, GAPS2-B27-d, AUDIT-34, REM-§2-S09-align, REM-S09-73-areastyle, REM-05-04-S09-h, REM-S09-73-fitarea.
13. **Sizing.** `scale()`, `fxsize()`, `fysize()` and the overhangs are not applied; whether the overhangs are no-ops is UNCLEAR. `aspectratio()` shapes the figure rather than the plot region, is dropped when xsize/ysize are given, and `aspectratio(#, placement())` is refused. Sizes are fixed to a 4-inch reference. Effort M. Sources: REM-§2-S10-fxfysize, REM-§2-S10-scale, REM-S10-a, REM-S10-b, GAPS2-B33-a, GAPS2-B33-b, GAPS2-B33-c, GAPS2-D14-a, GAPS2-D14-b, GAPS2-B30-a, GAPS2-B30-b, GAPS2-B30-c, AUDIT-68, AUDIT-69, REM-05-04-C1.
14. **dash refuses values `twoway` accepts.**
    - `range(varname)` and a `.` end in `range()`
    - `degree()` above 3, `n(1)`, and `n()` above _N on lpoly
    - `bwidth(0)`, and lowess `bwidth()` above 1
    - several variables in `mlabel()`, and scatteri `2/2`
    - `msize(1e400)`, and bounds checked on types that do not draw the option
    - `level()` bounds applied to every CI type
    - weight expressions, and `yaxis(1 2)`

    Effort M. Sources: GAPS2-A15-a, GAPS2-A15-b, GAPS2-A15-c, GAPS2-A15-e, GAPS2-A15-g, GAPS2-A15-h, GAPS2-A15-i, GAPS2-A15-j, GAPS2-A15-k, GAPS2-A15-l, GAPS2-C11-a, GAPS2-C11-b, GAPS2-C11-c, GAPS2-C11-d, GAPS2-C11-e, GAPS2-C11-f, GAPS2-C11-g, GAPS2-A12-c, GAPS2-C7-d, GAPS2-G17, GAPS2-B15-c, AUDIT-25, AUDIT-41, AUDIT-47, AUDIT-49, AUDIT-51, AUDIT-52.
15. **Axes 3–9 are refused.** Effort L. Sources: GAPS2-A15-f, GAPS2-B15-b, AUDIT-26.
16. **Weighted scatter markers are not size-scaled.** Also, `jitter()` is not drawn on rscatter, rcapsym, pcscatter and pccapsym. Effort M. Sources: GAPS2-G18, AUDIT-40, GAPS2-A8-e, AUDIT-46.
17. **Missing plot types:**
    - rpcap and rpspike: M
    - sunflower: M (also falls to the generic "unrecognised" message)
    - matamatrix: M (gives a misleading r(101))
    - heatmap: L
    - contour and contourline: XL

    Effort XL. Sources: GAPS2-A5-a, GAPS2-A5-b, GAPS2-A5-c, GAPS2-A5-d, GAPS2-A5-e, AUDIT-01, AUDIT-02, AUDIT-03, AUDIT-04, AUDIT-05.
18. **Extended missing values `.a`–`.z` are merged into one.** This affects `by(, missing)` panels, marker labels, filters and tooltips. Effort M. Sources: GAPS2-G12-a, GAPS2-G12-b, GAPS2-G12-c, GAPS2-B27-e, AUDIT-37.
19. **Date `#N` tick choice matches `twoway` only 52–66% of the time on %td–%th.** There are also three natscale misses on auto. Effort L. Sources: GAPS2-B24-a, GAPS2-B24-b, AUDIT-63.
20. **Axis edge cases.**
    - `minmax` uses only the first layer, and ticks are not recomputed after a filter move.
    - `##5` is read as `#5`.
    - Quoted label text triggers sub-options: `xlabel(1 "grid")` turns the grid on.
    - Multi-line tick labels are drawn with their quotes.
    - `labgap`, label and tick styles, `alternate`, grid styles and `gmin` are not drawn.
    - Label forms `twoway` refuses are drawn anyway.
    - `angle(Vertical)` is accepted.

    Effort M. Sources: REM-09-02-MINMAX-VAR, REM-09-02-MINMAX-FILTER, REM-09-02-MINOR-c, REM-09-02-SUBOPT-IN-LABEL, CRIT-05, REM-09-02-LABEL-LABGAP, REM-09-02-LABEL-STYLES, REM-09-02-LABEL-ALT, GAPS2-B21-g, GAPS2-B21-h, GAPS2-B21-i, GAPS2-B21-j, GAPS2-B21-k, GAPS2-B1-res, GAPS2-D9-b.
21. **Options on types that do not take them are accepted silently.** `bwidth`, `n`, `range`, `base` and `level` on scatter give rc 0 and no note, and `kernel()` is written to the spec, where `twoway` refuses r(198) (see Decisions). Effort S. Sources: GAPS2-A12-a, GAPS2-A12-b, GAPS2-C15, AUDIT-78.
22. **Locale and text settings.** `set dp comma` is never read. %tC ignores leap seconds (up to 27 s), and the help says otherwise. The `graph set` fontface setting is not read. Effort M. Sources: GAPS2-J1-c, GAPS2-G7-a, GAPS2-G7-b, CRIT-08.
23. **Secondary-axis range does not follow a filter move (both modes).** Effort M. Sources: REM-09-07-Y2-FILTER-CALLBACK, GAPS2-E6a, REM-09-07-Y2-TEST-GAP.
24. **Documented saved/served residuals.** Under `layout(bs)` with `filterposition(left)`, the header sits beside the sidebar in the saved page and above it in the served app. The saved page keeps its histogram bins and kdensity grid after a filter move. Panels emptied by a filter stay drawn. Effort M. Sources: GAPS2-E14-residual, AUDIT-81, GAPS2-E4b, AUDIT-39, GAPS2-E6b.
25. **Interaction edge cases.** Brushing a histogram dims the bars and drives nothing. Concurrent brushes are not intersected. Saved-page JS errors fail silently. Saved sliders are not throttled. Effort M. Sources: GAPS2-E5a, GAPS2-E5b, GAPS2-E11, GAPS2-E12.
26. **Environment robustness.**
    - `BOKEH_RESOURCES=cdn` silently blanks the served page.
    - Other Bokeh environment variables are not reported, and `BOKEH_MINIFIED`/`BOKEH_DEV` change the saved page silently.
    - `/health` is shallow.
    - The browser-launch return code is unchecked.

    Effort S. Sources: GAPS2-F12a, GAPS2-I1-a, GAPS2-I1-b, GAPS2-F12b, GAPS2-K4-a, GAPS2-K4-b, GAPS2-I-sum-health, GAPS2-F-intro-health, REM-S14-b.
27. **Session hygiene.** Four Mata functions are unprefixed. The repair step drops other packages' functions of the same names. `sys.argv` is overwritten, and `_dash_*` names are left in `__main__`. Effort S. Sources: GAPS2-X7-a, GAPS2-X7-b, GAPS2-X7-c, GAPS2-X7-d, GAPS2-X7-e.
28. **Data and memory.**
    - Working columns are generated in the user's data, so r(900) is possible at `c(maxvar)`.
    - Variables named `x`, `y`, `top` and similar are shadowed in `hover()`/`mlabel()`.
    - Numbers are embedded as JSON text, rendering needs about 0.5 GB per million values, and the strL check loops per observation.
    - A faceted computed-only graph is counted in full against the cells limit.

    Effort M. Sources: GAPS2-G1-res-a, GAPS2-G1-res-b, GAPS2-G14-a, GAPS2-G14-b, GAPS2-G14-c, GAPS2-G3-res.
29. **Packaging basics.** There is no README with an install command, no LICENSE, and `dash.pkg` has no Author, KW or Stata version. A `.pyc` is written into PLUS/py. A failed setup does not say what it installed and cannot roll back. Effort S. Sources: GAPS2-J8-b, GAPS2-J8-c, GAPS2-J8-d, GAPS2-H10a, GAPS2-H10b, GAPS2-H10c, GAPS2-H8a, GAPS2-H8b.

### P3: docs, tests, paperwork

1. **Retire or fix `scripts/regen_option_surface.py`.** Running it strips working code and kills the ignored-option note. Only a comment guards it. Effort S. Sources: REM-05-04-C3.
2. **Make the help's Unsupported list and the note accurate.**
   - Generate the list and check it both ways. About 35–40 undeclared ignored options are missing from it (ciplot, ttitle, xvarformat, ndots and others).
   - The note adds `()` to bare flags.
   - The note should print canonical names, not the typed prefix.
   - `vertical` and tsline `sort` should not be named; `twoway` ignores both.
   - The kernel-flag text is stale.

   Effort M. Sources: REM-§2-help-undeclared, REM-05-04-HELPLIST, GAPS2-A4-r, GAPS2-B14-g, GAPS2-C9-f, REM-S05-04-notefmt, REM-05-04-B5, REM-§2-S06-vertical, REM-S05-04, GAPS2-A1-c, AUDIT-M3, REM-05-04-B2, REM-05-04-C12, REM-§2-S09-xymtick, REM-§2-S09-varformat, REM-§2-S09-varlabel, REM-S08-a, REM-S08-b, REM-05-04-S09-d, REM-05-04-S09-e, GAPS2-A4-i, GAPS2-B14-d, GAPS2-B14-e, GAPS2-C9-e.

   Implementing `xvarformat()`/`xvarlabel()` and the y forms is S if chosen over documenting them.
3. **Stale versions, docstrings and tracking documents.**
   - dash_render.py still says 1.0.0 with the old dependency floors.
   - The ServerAppBuilder security and origin docstrings are wrong, and a dead `title_safe` variable remains.
   - The app header and banner say `bokeh serve` and localhost.
   - GAPS.md's executive summary, ROADMAP's open count, the BUGS "Not fixed" preambles and test_geometry_visual.md are stale; the CSP claim there was not re-probed.
   - CHANGELOG has no S06 entry.

   Effort S. Sources: REM-01-03-version, GAPS2-H4f, GAPS2-J8-h, REM-09-07-SERVER-ESCAPE-DOCSTRING, GAPS2-F9a, GAPS2-F9b, GAPS2-F9d, GAPS2-K11-a, GAPS2-K11-b, GAPS2-K11-c, GAPS2-K11-d, REM-S06-d.
4. **Help content gaps.**
   - Qualifier semantics: an overlay example, and how qualifiers behave with `link()`.
   - Date-axis precedence: log overridden on a date axis, and %tC.
   - A false claim that a flood "cannot flood the log" (Tornado logs every 429).
   - No iframe note, no Author section, and Jump To lists 16 of 30 sections.

   Effort S. Sources: REM-06-06-B7, REM-08-04-B5, GAPS2-F9e, GAPS2-J7-d, GAPS2-J8-a, GAPS2-J8-f, GAPS2-J8-g.
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

   Effort L. Sources: GAPS2-K3-a, GAPS2-K3-b, GAPS2-K3-c, GAPS2-K1-c, GAPS2-K1-d, GAPS2-D0-fixture, GAPS2-D19-c, GAPS2-D4-e, GAPS2-C12-a, GAPS2-C12-b, GAPS2-C12-c, GAPS2-C12-d, GAPS2-C14-b.
8. **Test-harness gaps.**
   - A server fixture leaks a process when `__enter__` fails.
   - Report-truth is not checked against ServerAppBuilder.
   - There are no tests of linked computed layers with qualifiers.
   - The axis truth test is vacuous, and the dead-key and minmax-with-qualifier guards are missing.
   - Scheme-key enumeration is hand-written, and the CSS guard has no served arm.
   - There is no dispatch AST count and no self-contained-app test; the allowance and copied-method guards are weak.
   - Tracking-document drift is unchecked.

   Effort M. Sources: REM-14-01, REM-05-04-C9b, REM-06-06-A5, REM-06-06-B6d, REM-09-02-T-TRUTH, REM-09-02-T-SERVER, REM-09-02-T-DEADKEY, REM-09-02-T-MINMAXQ, REM-08-04-C9, REM-11-04-B7, REM-11-04-B9, REM-11-04-C10, REM-15-03-B10, REM-15-03-B11, REM-15-03-C12b, REM-15-03-C13, GAPS2-K11-e.
9. **CI, linting and browser coverage.** There is no CI, no pyflakes/ruff (51 findings in the renderer), no bandit and no secret scan. Dev dependencies are undeclared, and there is no environment surface in the adversarial registry. Only headless Chrome is tested; interaction runs under node stand-ins, and load at scale is unmeasured. Effort L. Sources: GAPS2-K-intro-a, GAPS2-K-intro-b, GAPS2-J-intro-a, GAPS2-G14-e, GAPS2-I9-a, GAPS2-I9-b, GAPS2-K10-d, GAPS2-K5-d, GAPS2-I1-f.
10. **Code structure.** dash_render.py is one 32k-line module, and the server app is emitted as string literals. Facet orchestration is duplicated, and the JS and Python statistics have no shared case table. Effort XL. Sources: GAPS2-K10-a, GAPS2-K10-b, GAPS2-K10-c, GAPS2-K10-e, REM-15-03-A2.
11. **Dashboard extensions (not `twoway` parity).**
    - KPI cards take no weights and lack kurtosis, semean and range.
    - There is no multi-select filter, "(missing)" option, slider direction or reset button.
    - Only one link group is allowed, and the brush cannot act as a filter.
    - There is no print stylesheet, and the PNG export has no KPIs or header.

    Effort L. Sources: GAPS2-E7a, GAPS2-E7b, GAPS2-G13, GAPS2-E13a, GAPS2-E13b, GAPS2-E13c, GAPS2-E13d, GAPS2-E9, GAPS2-E5c, GAPS2-E5d, GAPS2-J7-e, GAPS2-E10a, AUDIT-84, GAPS2-K-intro-c.
12. **Accessibility (no ARIA or alt text) and English-only interface.** Effort L. Sources: GAPS2-J-intro-b, GAPS2-J-intro-c.

By design, no task needed: AUDIT-50, AUDIT-56, AUDIT-70, AUDIT-73, AUDIT-77, AUDIT-79, AUDIT-80, AUDIT-83, AUDIT-85, AUDIT-86, REM-S11-c.

## 4. Decisions needed

- **The 79 accepted-but-ignored options (REM-§2-decision).** Choose (a) implement all, or (b) implement the high-value subset and formally re-disposition the rest in ROADMAP/CHANGELOG. Of the named subset, `text`, `ttitle`/`tlabel`, the edge titles, `mstyle`, `lstyle`, `gap`, `fxsize`, `fysize` and `scale` are still open.
  - Candidates to re-disposition (accept and report): the stroke-alignment options (Bokeh has no equivalent) and `play()` (AUDIT-14).
- **Line join order (P0.1).** Following `twoway`'s data order means flipping the tests that pin x order, and it changes existing dashboards.
- **lpoly bandwidth (P0.7).** Option (a): take Stata's `r(bwidth)` from `lpoly …, nograph` at registration. This is exact at build time, but the served recompute after a filter move and the saved page still need a rule. Option (b): port Stata's rule of thumb per kernel and degree to Python. Rule (b) is compiled Mata, so the port is only partly verifiable.
- **lpolyci band (P0.9).** Implement the analytic band (which also removes the ~100× cost), or keep the bootstrap as a documented difference.
- **Saved-page refit (P0.17, DISCOVERY Q3).** Keep it deferred with a visible stale cue, or port every estimator to JS (XL).
- **Unbinned `colorvar()` (DISCOVERY Q5).** dash maps it continuously; `twoway` bins it at the z-axis ticks. Sources: GAPS2-X2-r1, GAPS2-A8-f, AUDIT-18.
- **Third-party and PLUS schemes (DISCOVERY Q30).** They are currently refused, and an inherited `c(scheme)` falls back to s2color. Sources: GAPS2-X5-b, AUDIT-74.
- **Refuse vs note.** `twoway` refuses typos, options it rejects outright (`title2`, `ciopts`, …) and options on inapplicable types, but dash notes them (TP-07). Sources: AUDIT-07, GAPS2-B28-a, GAPS2-B28-b, GAPS2-B28-c, GAPS2-A12-d, AUDIT-58, P2.21.
- **"Drew nothing" notes where `twoway` is silent.** Keep the deliberate report or match `twoway`. Sources: GAPS2-A11, GAPS2-C8.
- **Size units (P1.12).** Moving to Stata's relative units changes the look of every existing dashboard.
- **Served-app authentication (P0.12).** Add a token or cookie (changes the user experience), or formally scope dash as single-user and document it.
- **`graph export` companion (P1.28).** Headless-browser export (a dependency dash cannot ship) vs documented non-support plus `r(filename)`.
- **Support floor.** Should Python stay at 3.13 or return to 3.11 (P1.33)? Should the declared minimum Stata be raised to 19, or should Stata 16–18 and BE be tested (P1.35)? Also choose a bokeh ceiling policy (P1.30).
- **Accessibility and localisation scope (P3.12).**

## 5. Chunks that failed to report

None.