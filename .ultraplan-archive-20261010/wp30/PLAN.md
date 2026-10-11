# WP-30 Plan — close the drop-in P1 gaps

> Architect pass, 03oct2026. Branch `wp30-p1`, cut from `main` `c96facd` ("Merge branch 'wp29-p0'"). The source is `.ultraplan/handoff/DROPIN-REMAINING.md` §3 "### P1: common `twoway` usage not honoured" (lines 64-170), 35 items. Each item was researched at `c96facd`, with measured twoway truth, in `.ultraplan/wp30/research/p1-NN.md`. Beside this file:
> - `index.md`: the 58 sections, 22 batches, merge order, merge rules R1-R13, the queue, the cscript driver, the execution conventions (cited here as "index E1-E12") and the verification gates G0-G11. **Where this file and `index.md` differ, `index.md` wins.**
> - `manifest.json`: each section's scope, notes and edges, and the 22 residuals.
> - `decisions.md`: the maintainer's answers M1-M12 (binding).
> - `decision-register.md`: 235 per-question rulings and 5 cross-cutting ones (the architect ids A1-A137 mark those no M decision settles), the strict readings of the M decisions, and the new P2 residuals P2.42-P2.57.
>
> **Ratified (06oct2026).** The maintainer answered all 44 rows on 06oct2026: 35 as recommended; rows 4, 8, 12, 22, 25, 27, 32 and 36 CHANGED, and row 29 answered otherwise than recommended (the file stays; `_ROOT_ALSO` names it). The requirements below are rewritten to the answers, and each changed [Rn] tag reads "[Rn, changed]". No row is pending and none was struck.
>
> **Status (as written).** Written before the maintainer has answered the 44 rows of `index.md` "Decisions for maintainer ratification" (28 register rulings, the precondition P-1 as row 29, and 15 section maintainer questions as rows 30-41; consolidated 06oct2026). Row 29 is acted on before step 0a. A requirement below that rests on one of them is tagged **[Rn]** (the row number). Batch 1 is not cut while any row reads `pending` (A151). A struck row is re-planned in this file and in the section file it binds before that section's batch base is recorded, and IR-7 already says what a strike of row 26 changes. S58 drops the tags when it copies §6 into ROADMAP.md.

## 1. Context

dash is a Stata package that takes `twoway` syntax and draws interactive Bokeh dashboards in two modes that must agree:
- the **saved** standalone HTML page, where filters move through JavaScript callbacks;
- the **served** Bokeh app, written by `ServerAppBuilder`, where filters recompute in Python. The app receives the module-level helpers it needs through the served copy lists in `dash_render.py` (at `c96facd`: the constants tuple at 32884-33039, the functions tuple at 33077-33425, `_shared_stat_lines` at 33485; index R2).

**What WP-29 left.** WP-29 closed all 20 P0 items of DROPIN-REMAINING.md (ROADMAP.md:4448, `— DONE`) and was merged into `main` at `c96facd`. At that commit BUGS.md has 4 open entries, all graded `S3 (WP-27)` (BUGS.md:2523, :2559, :2595, :2601); the first, the tsnatscale model, is closed here by S44. WP-29 also wrote notes into thirteen P1 rows of DROPIN-REMAINING.md that this package inherits:
- P1.3: twoway's by() common scale includes fit lines; WP-29's shared range does not yet (c15).
- P1.4: the empty histogram key colour (a P0.18 residual).
- P1.8: P0.1 joins the six line types in data order; `connect()` on scatter, `cmissing()` and `recast()` stay open.
- P1.9: `horizontal` on `function` and on computed date layers.
- P1.15 and P1.16: the per-panel axis-2 title, the "Graphs by" note through `_dash_var_label`, the per-panel colour key, and default titles for unlabelled multi-layer graphs and `yaxis(2)`.
- P1.17: `barwidth()` on a date axis, and twoway's one-x-unit bar width.
- P1.18: `add` on an axis(2)-routed label (`ylabel(…, axis(2) add)`) is named, not drawn.
- P1.22: P0.6 evaluates every Stata-built `function` layer with Stata's own generator; the points-free fallback still knows ten functions.
- P1.23: P0.8 computes date layers in Stata units; `xlabel(minmax)` on a mixed axis, `function`/`scatteri`/`pci`/`pcarrowi` on a date axis and the histogram and fit tooltips stay open.
- P1.26: the served app prints no empty-layer note where the saved page notes "drew nothing".
- P1.30: no hash-pinned installs (WP-29 OQ7).
- P1.34: WP-29's private files, lifecycle, launch from the open file, preview pruning, served key and PEP 668 paths are unmeasured off macOS.

**The 35 P1 items, in seven groups:**
- **A. Input twoway accepts, which dash refuses or misreads:** P1.1 stylelists across an expanded varlist; P1.6 the tsline `t*` options; P1.7 time-series operators in plot varlists; P1.19 sub-option abbreviations; P1.27 the drop-in command form and the `saving()` grammar.
- **B. Options accepted but not drawn:** P1.8 `connect()`, `cmissing()` and `recast()`; P1.9 `horizontal`; P1.10 `text()` and `ttext()`; P1.14 named styles; P1.18 the common axis sub-options and `add`; P1.20 `plotregion()`/`graphregion()`; P1.21 `xline`/`yline` limits; P1.24 `mlabvposition()` and `mlabtextstyle()`.
- **C. The default look and its units (M1):** P1.2 scheme chrome and intensity; P1.3 the natscale/tsnatscale ticker and twoway's margin; P1.4 scheme keys on every layer; P1.12 Stata size units; P1.13 Stata's colour grammar; P1.17 bar and range geometry; P1.25 scheme resolution and the six missing StataCorp schemes.
- **D. Text, formats, dates and by():** P1.5 axis format fallbacks; P1.11 SMCL and TeX in graph text; P1.15 by() sub-options and chrome; P1.16 legend keys and default axis titles; P1.23 the date-axis residuals.
- **E. Messages and export:** P1.22 the `function` fallback (closed by disposition, M12); P1.26 notes that do not reach the user; P1.28 no `graph export` companion.
- **F. Security and the served app:** P1.29 a CSP without `'unsafe-inline'` and a safe Windows opener; P1.30 the open-ended bokeh window and unguarded Bokeh internals; P1.31 served-app session and memory limits and the blocked event loop.
- **G. Installation and floors:** P1.32 render-time dependency guards; P1.33 the Python floor; P1.34 portable runners (M4 shrinks it to this); P1.35 the Stata floor (M2 shrinks it to 19).

**Shape of the package** (`index.md` "Overview"):
- 58 sections: S01 (tracking foundation), S02-S57 (56 fix sections), S58 (closeout).
- 56 BUGS.md entries, one per fix section. Twenty items are split into parts (P1.15 into a, b and c), so an entry id is `P1.<n>`, `P1.<n>a`, `P1.<n>b` or `P1.15c` (A140).
- 63 fix commits: one per fix section, except that S05, S19, S37, S41, S42, S51 and S56 land as two (A156). With the plan commit (S00), S01 and the closeout's five or six commits, that makes 70 or 71 commits on `wp30-p1`.
- 22 batches (0-21), at most three sections each, with every dependency in an earlier batch.
- 84 CHANGELOG markers in six lists (A147).

WP-30 closes all 35 items: 32 by a fix in both modes, and three by the scope the maintainer set (P1.22 by M12, P1.34 by M4, P1.35 by M2).

## 2. Goals

1. **G1. Every P1 item closed.** Each item is fixed in both modes, before and after any filter move, or closed by its ratified disposition: P1.22 by WP-29 P0.6 plus a "needs Stata's points" note (M12); P1.34 by portable runners (M4); P1.35 by a declared and enforced Stata 19 floor (M2).
2. **G2. twoway truth wherever Stata draws or computes.** dash's value equals a fixture extracted from StataNow 19.5, stamped with the D12 `_meta` (including `stata_version`), checked in that section's block of `test/test_wp30_truth.cscript`. The pinned truths include:
   - stylelist and value-list resolution, and the time-series operator columns;
   - each shipped scheme's chrome, intensity, symbols, histogram style and margin keys;
   - natscale ticks and twoway's plot-region margin; the tsnatscale model's agreement floors;
   - axis display formats; size units; the colour grammar; named-style attributes;
   - by() panel labels, grid and refusals; legend keys and default titles; bar widths, bases and caps;
   - axis sub-options, abbreviations, region styles, reference lines and their extent;
   - date positions on every axis; `mlabvposition()`; the scheme lookup order;
   - the command form and `saving()` characters; graph-text glyphs; `connect()`, `recast()`, `horizontal`, `text()` and the `t*` options.
3. **G3. Refusals like twoway (M5).** In the areas WP-30 touches, input twoway refuses is refused with twoway's return code and message text, measured in StataNow 19.5. A valid twoway option dash cannot draw is named in a note, never refused. Every newly refused form gets a CHANGELOG line under "Changed behaviour (may need your do-files changed)".
4. **G4. Silence like twoway (M6).** Where twoway draws the same picture and prints nothing, dash prints nothing in either mode. Notes remain only for what dash draws differently, and they reach the user in twoway's `(note: …)` form through one channel, from saved builds, served builds and `dash serve` alike.
5. **G5. The scheme's look (M1).** Every shipped scheme's look (centred, unbolded title; natscale ticker and margin; no default alpha 0.8) and Stata's relative size units hold in both modes. Every look change gets a CHANGELOG line under "Results that change" that names the command, the old value and the new.
6. **G6. Hardened as it grows.** Every new or widened surface is hardened when it lands and has a security test that names its threat (index G9): the CSP and the Windows opener, the scheme lookup, the SMCL scanner, the `saving()` characters, the `text()` and reference-line limits, date tokens never run as Stata code, Bokeh internals that fail closed, and the session cap.
7. **G7. Declared floors that are true.** Stata 19 declared and enforced; the Python floor is the lowest version the matrix passes; the bokeh window is verified; missing dependencies fail with one clear message; no runner hard-codes an architecture prefix or the maintainer's path.
8. **G8. Red first, never red.** Each commit unit has at least one regression test that failed before its fix (project rule 7), with the failure text saved. A pinned test of today's behaviour is flipped with a reason, never deleted (R9). The tree is never red (project rule 4): every commit and every batch gate is green.

## 3. Non-goals

- **P2 and P3 of DROPIN-REMAINING.md**, including the new P2.42-P2.57 that the register files. A P1 fix that touches a P2/P3 area must not change its behaviour except where the P1 item requires it. The scope changes the register makes are recorded by S58: P2.11's sm* sizes, P2.12's `lwidth(none)` and P2.13's "4-inch reference" close here; P3.2 loses `xvarformat()`/`yvarformat()`; P3.7 loses its extractor-path part, because S02 converts every extractor (IR-8); P3.9, P3.11 and P2.14 gain work.
- **The refuse-versus-note sweep of the rest of the option surface** (P2.21). M5 applies only in the areas WP-30 touches.
- **P1.34's platform measurement (M4).** Linux, Windows, Intel Mac and GUI Stata, and WP-29's S08/S09/S13 paths there, move to one deferred platform package (P1.34.6), with P1.28's Chrome-driven export, P1.29's option B and the P1.33 Windows patch caveat. Windows rules are tested here as pure functions and dry runs only. Project rule 10 and the GUI-block hook are not edited (P1.34.1).
- **Stata before 19 (M2).** No Stata 14-18.5 binary is run, and no version-keyed truth or Break fallback below 18.5 is built. Stata 19.0 (non-Now) and BE/SE are declared, not measured.
- **A Chrome-driven `dash export` (M8)**, PNG size and resolution control, `output_backend(svg)` (measured to break the grid's PNG save) and a print stylesheet for inactive tabs (P3.11).
- **The manifest's residuals** as amended by IR-2, IR-3, IR-4 and IR-9, among them:
  - `dstyle()`/`dlstyle()` drawing, area outlines and a general resolver for all 161 Stata style files;
  - `tmlabel()`/`tmtick()` drawing (P2.2);
  - an exact `graphregion(margin())` and the graphregion `i*` options (P2.53);
  - by()'s overall regions and twoway's split of quoted value labels;
  - inline SMCL style runs and raised super/subscripts (no MathJax route);
  - `[aw=L.x]` (P2.14), `mlabstyle()` (P2.12), `zyx2rule`;
  - twoway's date tick choice beyond the fitted model's measured agreement (P2.19);
  - the points-free `function` fallback beyond its ten functions;
  - Python 3.10 and older; hash-pinned installs; the `<3.11` ceiling unless bokeh 3.10 is verified inside S41.
- **No version bump and no new release heading.** WP-30's lines go into the existing `## 0.1.0, 02oct2026 (release candidate)` of CHANGELOG.md. S58.6 moves the release date only if it must.

## 4. Binding decisions

| Id | Decision |
|---|---|
| M1 | P1.2, P1.3, P1.12: **match Stata.** dash adopts each scheme's look (centred, unbolded title; natscale ticker and padding; no default alpha 0.8) and Stata's relative size units (numbers and keywords in Stata units, `#pt`, `*#`, the full keyword ladder). Strict readings: size units take option B, one Stata unit for every class at the 4-inch reference (P1.12.1, IR-1); `bgcolor()` takes twoway's canvas semantics (P1.20.7, IR-2); explicit-value axes re-hull their data part after a move (P1.3.6). Every look change gets a CHANGELOG "Results that change" line. |
| M2 | P1.35: **raise the floor to 19.** dash declares `version 19` (all 91 `version 16.0` lines, P1.35.3) and refuses an older Stata with a clear message. Only `/usr/local/bin/stata-mp` (StataNow 19.5) is run; the Stata 14-18.5 binaries on this Mac are never run. |
| M3 | P1.33: **measure, then lower.** Both pytest suites run under Python 3.11 and 3.12 in scratch virtual environments; the floor becomes the lowest version that passes, with 3.13-only code given a fallback or guard. |
| M4 | P1.34: **defer.** WP-30 only makes the runners portable (no hard-coded `arch -arm64` or maintainer paths). Measuring Linux, Windows and Intel Mac moves to a later package. |
| M5 | DROPIN §4 refuse vs note (P1.1, 5, 6, 8, 9, 10, 13, 15, 18, 19, 20, 21, 24, 27): **refuse like twoway**, with twoway's return code and words, in the areas WP-30 touches. A valid twoway option dash cannot draw is still named in a note. The rest of the option surface (P2.21) is not swept. Every newly refused form gets a CHANGELOG "Changed behaviour" line. The register lists 26 M5 refusal rows. |
| M6 | A11/C8 (P1.26, P1.18): **match twoway: silent.** Where twoway draws the same picture and prints nothing (a layer whose own if/in keeps no row; scale(off), nolabels, noticks, titlegap ignored under by()), dash prints nothing in either mode. The register lists 11 M6 rows. |
| M7 | P1.25: **the whole ado-path.** scheme(NAME) and an inherited c(scheme) resolve along Stata's ado-path (BASE, SITE, PLUS, PERSONAL, OLDPLACE, added dirs, cwd) under both file names, with name, per-directory realpath containment and size guards; scheme files are parsed as data, never executed. |
| M8 | P1.28: **document plus an SVG button.** dash returns `r(filename)`; notes once when a Stata graph in memory would be what `graph export` writes; the help documents the limit; both modes gain a client-side "Save as SVG" toolbar action. No Chrome-driven `dash export`, no `output_backend(svg)`. |
| M9 | P1.30: **cap at the next unverified minor.** `dash_setup` installs `bokeh>=3.8,<3.10` (to `<3.11` if 3.10 is verified inside WP-30). At run time, above the window: a note and continue; below the floor: refused. |
| M10 | P1.33, P1.30: **downloads approved** (pip wheels, an arm64 Python 3.11), only into scratch virtual environments during execution, never installed elsewhere. |
| M11 | P1.27: **allow; keep the sink checks.** `saving()` accepts `..` and `; & \| < >` as twoway does, and keeps refusing a double quote, backquote, `$`, control characters and a leading `-`. On Windows a path holding a cmd metacharacter (including `%` and `!`) is written but not opened, and its path is printed. P2-80 and PV-04/05/14 are flipped with the reason, never deleted. |
| M12 | P1.22: **close by disposition.** The ten-function points-free fallback stays; anything else it meets gets a "needs Stata's points" note; P1.22 is recorded closed by WP-29 P0.6 plus that note. |
| A1-A137 | `decision-register.md`: the architect rulings on the P1 questions (A1-A132) and the cross-cutting X.1-X.5 (A133-A137: append-only copy lists with an existence test; the note channel first; per-section case-id ranges; one truth script; map entries in the same commit). A section file cites the register row it implements (P1.n.k, X.n). |
| A138-A156 | `index.md` "Architect decisions": the grouping into 58 sections (A138); batch rules (A139); entry, marker and commit-subject ids (A140, A141); one truth script as runner block `// 69.` (A142); case-id prefixes and ranges (A143); the tracking test and its allowance (A144); tracking documents are the closeout's (A145); the extra entries P1.5.7, P1.25.6 and P2.49 (A146); 84 markers in six lists (A147); map anchors (A148); the copy-list existence test (A149); the note channel first (A150); ratification before batch 1 (A151); one scheme regenerator per batch (A152); the axis-finisher chain (A153); the guard order at the top of `dash` (A154); help paragraph ownership (A155); two-commit sections (A156). |
| IR-1..IR-17 | `index.md` "Index reconciliations": how a section reads a manifest text that the register rules on differently. They bind every section file. |
| Ratification 1-44 | `index.md` "Decisions for maintainer ratification" (answered 06oct2026; rows 1-28 the register's rulings, 29 the P-1 precondition, 30-41 the section maintainer questions). Rows 1-28 are tagged **[Rn]** below; rows 30-41 bind the sections they name. |
| index E1-E12 | `index.md` "Execution conventions learned in WP-29": the queue at 6 CPUs, the landing routine, branch checks, GitNexus at each base and landing, Stata only through `scripts/stata_slot.sh`, the flaky-test rule, never staging the maintainer's uncommitted files, never committing to `main`, pulling from `main` before each full run, the message check, scratch evidence quoted, downloads into scratch only. |

## 5. User stories (package level)

Personas:
- the **twoway user** pastes a twoway command or do-file and expects twoway's picture, twoway's errors and twoway's silence;
- the **dashboard publisher** shares a saved page or runs a served app for others;
- the **installer** runs `dash_setup` and the first `dash` command on their machine;
- the **maintainer** keeps dash certified against Stata and releases it.

**A. Input grammar**
- **US-30.1** As a twoway user, I want `scatter mpg turn weight, mcolor(red blue) msymbol(O T)` to give each y its own element, with `.`, `=`, `..` and `...` meaning what they mean in twoway, and `mlabel()`, `jitter()`, `base()` and `barwidth()` lists read per series, so a multi-y do-file draws as in Stata. (P1.1)
- **US-30.2** As a twoway user, I want `legend(c(2) posi(6))`, `ylabel(, labs(small) ang(0))` and `xline(5, lc(red) lp(dash))` to work as abbreviations do in twoway, and a capitalised or misspelt sub-option refused as twoway refuses it. (P1.19)
- **US-30.3** As a twoway user with time series, I want `line D.close date`, `tsline L.gdp` and `lfit y L.x` drawn, labelled `D.close`, and `tlabel()`, `ttick()`, `ttitle()`, `tscale()` and `tline()` with date literals honoured on the time axis, with twoway's refusals where twoway refuses. (P1.6, P1.7)
- **US-30.4** As a twoway user, I want to put `twoway`, `tw` or `graph twoway` in front of my command, use `saving(f, replace)` and `saving(f, asis)` on every route, write to a path with `..` or `&`, and run my do-file in batch or with `set graphics off` without a browser opening. (P1.27)

**B. Options drawn**
- **US-30.5** As a twoway user, I want `scatter y x, c(l)`, stairsteps, `connect(L)` panel lines, `cmissing(n)` breaks and `recast()` drawn as twoway draws them, in both modes and after a filter move. (P1.8)
- **US-30.6** As a twoway user, I want `horizontal` drawn on bar, rbar, spike, rspike, rcap, rcapsym, dropline, area, rarea, histogram, kdensity and function, with the axes and titles swapped, and kept after a filter move. (P1.9)
- **US-30.7** As a twoway user, I want `text()` and `ttext()` annotations drawn where twoway puts them, with their size, colour, box and orientation, on every by() panel and after a move. (P1.10)
- **US-30.8** As a twoway user, I want `pstyle(p3)`, `lstyle(refline)`, `mstyle()` and the other named styles to style my layers as in twoway, and `mlabvposition(varname)` and `mlabtextstyle()` drawn. (P1.14, P1.24)
- **US-30.9** As a twoway user, I want `nolabels`, `noticks`, `labcolor()`, `tlength()`, `angle(rvertical)`, `xscale(off)`, `noline`, `alt`, `titlegap()` and `add` honoured; `plotregion()`/`graphregion()` sub-options drawn or named; and `xline(2000(500)3000, lstyle(foreground) noextend)` drawn as twoway draws it. (P1.18, P1.20, P1.21)

**C. Default look**
- **US-30.10** As a dashboard publisher, I want a graph drawn under any shipped scheme to look like Stata's graph: centred, unbolded titles, the scheme's ticks, grid and axes, natscale ticks with twoway's margin, opaque markers, opaque intensity fills, the scheme's histogram and range styles, one-x-unit bars and twoway's default base, so my readers see the same picture as in a Stata report. (P1.2, P1.3, P1.4, P1.17)
- **US-30.11** As a twoway user, I want `msize(medium)`, `msize(*1.5)`, `lwidth(0.5pt)`, `mlabgap()` and `navy*.5`, `*.5`, CMYK, HSV and `bg`/`fg` read in Stata's units and grammar, and an unknown colour drawn black with twoway's note. (P1.12, P1.13)
- **US-30.12** As a twoway user, I want `scheme(meta)`, `scheme(stcolor_mv)` and any scheme I installed (PLUS, PERSONAL, cwd, a third-party package) found as Stata finds it, and an error that lists the names that do exist; as a dashboard publisher, I want a scheme file never run as code. (P1.25)

**D. Text, formats, dates and by()**
- **US-30.13** As a twoway user, I want default tick labels in my variable's display format (`2,000` for `%9.0fc`), `xlabel(, format(%td…))` honoured, and dates placed in Stata units on every axis, in range and pc plots, scatteri, `function range()`, colour keys and tooltips. (P1.5, P1.23)
- **US-30.14** As a twoway user, I want `{bf:}`, `{it:}`, `{sup:}`, `{&beta}` and `{c #}` drawn as twoway draws them, and `$$…$$` drawn as typed; as a dashboard publisher, I want a saved page that carries no TeX engine and never feeds user text to one. (P1.11)
- **US-30.15** As a twoway user, I want legend keys such as "lowess mpg weight" and "Median bands" and default axis titles chosen by twoway's rule, including on range types and `yaxis(2)`. (P1.16)
- **US-30.16** As a twoway user, I want `by()` panels titled, laid out and sized as in twoway (`rows()`, `holes()`, `colfirst`, `iscale()`, `compact`), with one legend, outer axes only, a "Graphs by" note and twoway's refusals for bad by() arguments. (P1.15)

**E. Messages and export**
- **US-30.17** As a dashboard publisher, I want every note dash prints in twoway's `(note: …)` form, under `quietly` too, from `dash build, server` and `dash serve` as from a saved build, and not printed where twoway prints nothing. (P1.26)
- **US-30.18** As a twoway user, I want `r(filename)` after dash, a note when `graph export` would write an older Stata graph, and a "Save as SVG" button on every dashboard. (P1.28)
- **US-30.19** As a twoway user, I want a `function` layer that dash cannot draw without Stata's points to say so, naming the function, instead of drawing nothing in silence. (P1.22)

**F. Security and the served app**
- **US-30.20** As a dashboard publisher, I want my saved page and served app to block injected inline scripts, and a Windows path holding cmd metacharacters to be written but never passed to the shell. (P1.29)
- **US-30.21** As a dashboard publisher, I want my served app to stay responsive with many readers: a session cap with a busy page, idle sessions closed, the data decoded once, and one reader's slow refit not freezing the others. (P1.31)

**G. Installation and floors**
- **US-30.22** As an installer, I want `dash_setup` to install a Bokeh release dash was verified against, `dash` to tell me plainly when bokeh, numpy, pandas or Python is missing or too old and to name `dash_setup`, and the server to refuse to start if Bokeh changed the internals dash's security relies on. (P1.30, P1.32)
- **US-30.23** As an installer with Python 3.11 or 3.12, I want dash to accept my Python if the test suites pass on it, and `dash_setup` to stop sending me round the venv advice loop. (P1.33)
- **US-30.24** As an installer on Stata 16-18.5, I want one clear message that dash needs Stata 19, not an obscure failure later. (P1.35)
- **US-30.25** As the maintainer, I want every runner and extractor to run without my paths or a hard-coded architecture prefix, choosing the arch prefix from the binary itself. (P1.34)
- **US-30.26** As the maintainer, I want each P1 fix pinned by a test that failed before it, by Stata truth where Stata draws or computes, and by twoway's rc and words for every new refusal, so no P1 defect returns unnoticed.

## 6. Business requirements (package level)

Each requirement holds in **both modes** and **after any filter move** unless it says otherwise (BR-30.38). "Refused as twoway" means: with twoway's return code and message text as measured in StataNow 19.5, in twoway's order where the order was measured. "Noted" means one `(note: …)` line (BR-30.26).

- **BR-30.1** Stylelists and value lists (P1.1):
  - A style option given a list over an expanded varlist styles the k-th y with the k-th element. A lone value or a short list styles only the leading series; the rest keep their defaults, silently (twoway's padding).
  - The shorthands `.`, `=`, `..` and `...` resolve as twoway resolves them. A misplaced `..` is refused r(198) `<opt>(<value>):  invalid syntax`. A used quoted element of only blanks (`" "`) is refused r(198) `dash: <opt>() element <j> is blank; use . for the default (got: <value>)` [Q-11.1, ratification row 32, changed]; an unused one is not checked, and an empty `""` element is `.`, as in twoway.
  - A quoted or compound element is one element (`"hsv 240 1 1"`, `*.5`, `navy*.5%50`); an unquoted `255 0 0` is three elements. Single-y types take the first element. An unknown element draws twoway's default attributes, noted with the element named.
  - `malpha()`, `lalpha()`, `falpha()` and `jseed()` stay scalars applied to every series, as documented.
  - `mlabel(varlist)` is positional; `.` omits that series' labels; `..` is refused r(198) `.. not allowed in option mlabel()` and `=` r(101) `=exp not allowed`; every named variable must exist (r(111)).
  - `jitter()`, `base()`, `barwidth()` and `mlabposition()` are checked per element after the shorthands resolve, so `jitter(2 ..)` and `base(10 =)` draw. Elements past the number of y are ignored silently. rbar `barwidth()` lists and lowess `bwidth()` lists stay refused as twoway refuses them.
- **BR-30.2** Scheme chrome and intensity (P1.2), for each of the 26 shipped schemes:
  - the title is centred and not bold (economist: left); axis titles are upright; subtitle, note and caption are placed by the scheme's justification; economist's note sits in the title band;
  - no minor ticks unless asked; tick length, side, colour and width come from the scheme in Stata units; s2color's y labels are vertical (`ylabel(, angle(0))` is the escape); stcolor's grid is dashed; s1rcolor's ticks are visible; economist's axis sides, lines and ticks are the scheme's;
  - markers are opaque unless `%NN`, `sttrans` or `malpha()` asks otherwise (rconnected's markers included);
  - bar, area and histogram fills and the CI band blend the scheme's p#bar/p#area intensity opaquely, user colours included; `fintensity()` is an opaque blend; above 1 it darkens with twoway's measured clamp (navy at 6000 and above is #010304); it is never refused; negatives read as 0;
  - a user scheme's `intensity bar` and `intensity area` are not read, silently (twoway ignores both).
- **BR-30.3** Default ticks and padding (P1.3):
  - Default numeric, log and `%tc` axes, and y2/x2 axes without their own labels, take twoway's natscale choice with the scheme's tick count, and draw no minor ticks.
  - An axis range is the hull of every drawn layer, fits included, plus twoway's plot-region margin (r × min(W,H), r = 0.022; economist 0.006), placed within about 0.8% of the width of twoway's [R1]. Shared by() panels share one range over the union hull.
  - After every filter move, default and `#N` axes re-tick and re-range over the kept rows, y2/x2 included. An explicit-value axis re-hulls its data part and keeps its label positions (the help's "holds across filter moves" is rewritten). Zoom and pan re-tick by natscale over the visible range.
  - Budget [R3]: the served re-finish adds at most 0.2 s per figure per move at 500k rows; 100 saved by() panels settle within 1 s of WP-29's measured time.
  - `%td`, `%tw`, `%tm`, `%tq`, `%th` and `%ty` default axes take the fitted tsnatscale model [R2]. Its agreement with twoway is pinned at the measured floors (52-66% of `%td`-`%th` ranges, 98% of `%ty`) and stated in the help. The saved page and the served app give the same ticks on every one of the fixture's 12,000 answers.
- **BR-30.4** Scheme keys on every layer (P1.4):
  - `sttrans` opacity reaches fits, spikes, ranges, pc types and immediates; rarea follows area's rule (opaque; 0.2 under `sttrans`).
  - Histograms take the scheme's histogram colour, intensity, line colour and line width, and so does an empty histogram's key.
  - The scheme's hollow and `sm*` p# symbols are drawn hollow and at 0.707 size, and so is a user's `msymbol(sm*)`, after `msize()` (IR-4). The p# symbol cycle reaches scatteri, rscatter, pcscatter, dropline and rcapsym. Markers read p#markfill/p#markline, not p#mark. `msymbol(Oh)` with `malpha()` stays hollow.
  - The default marker-label size and colour come from the scheme's label keys in Stata text units, the same in both modes. The colour key's title, labels and ticks come from the scheme.
  - Every directive of a user, PLUS, third-party or shipped scheme is kept in the parsed scheme (none discarded), so later versions can draw it; a directive dash does not draw is not noted, in either mode [R4, changed].
- **BR-30.5** Axis formats (P1.5):
  - Default tick labels use the axis variable's display format (`weight` `%9.0fc` writes `2,000`), with twoway's `%g`/`%gc` fallback, on second axes, on range and pc first layers and in the text-label formatter. `xvarformat()`/`yvarformat()` are read.
  - Narrow `%g`, `%e` and `%f` fallbacks write what Stata writes (its own entry, P1.5.7).
  - `xlabel(, format(%td…))` is honoured. A numeric `format()` on a date axis writes the stored value.
  - `format(bogus)` is refused r(198) `invalid format, bogus`. A format twoway accepts but dash cannot write exactly (such as `%12s` on a numeric axis) draws `%9.0g`, noted. The help's log example is corrected.
- **BR-30.6** The `t*` options (P1.6):
  - `tlabel()`, `ttick()`, `tmlabel()`, `tmtick()`, `ttitle()`, `tscale()` and `tline()` are accepted on every twoway graph and apply to x axis 1 under twoway's base-format rule, with date literals in Stata units. The `axis(2)` forms route to the second axis. `tmlabel()`/`tmtick()` are accepted and named as not drawn until minor ticks are (P2.2). `tline()` is drawn under BR-30.21.
  - Refused as twoway: date literals where twoway's x axis is numeric (r(198), r(198), r(121) as measured), and where the first plot is lfit, kdensity or another type twoway refuses them for; a too-short `tm()` or `ts()` (r(198)); the left-aligned `%-t` form in `tline()` and `tscale(range())` (it is accepted in `tlabel()`/`ttick()`). A `format()` given with date literals is accepted or refused exactly as twoway's tickset format rules decide.
  - A date token is evaluated without ever running user text as a Stata command. `tscale(log)` on a date axis stays noted. The help lists every option.
- **BR-30.7** Time-series operators (P1.7):
  - `L.`, `F.`, `D.`, `S.` and their combinations, including `L(1/2).x`, are accepted in plot varlists on every type twoway accepts them on (measured; the line family, tsline and the lfit family), and drawn.
  - Titles, keys, notes and the CSV header show the expression as typed (`D.close`). `D.`/`S.` of a `%t` variable carry its format.
  - Refused as twoway: no `tsset` r(111) `time variable not set`; a string variable r(109); a factor variable r(101) `factor-variable operators not allowed`; operators on types twoway refuses them on r(101); `by()` with an operated variable r(5) `not sorted` (one hint line may follow); a bare `sort` with an operated x r(198).
  - Weights with operators stay refused (P2.14).
- **BR-30.8** `connect()`, `cmissing()` and `recast()` (P1.8):
  - `connect()` (`l`, `L`, `J`, `stairstep`, `stepstair`, `i`/`none`) and `cmissing()` are drawn on scatter, the line family, scatteri and the fits, per the measured truth: scatter `c(l)` draws the line; `J`, `stairstep` and `stepstair` draw stairs and keep today's tooltips (IR-3); `L` breaks where x drops; `cmissing(n)` breaks at missing values. `function` bridges interior missing regions by default and breaks under `cmissing(n)`.
  - Per-y lists follow BR-30.1; `cmissings()` is accepted; an unknown connect name is drawn direct, noted as twoway notes it; an unknown `cmissing()` value is refused r(101) in twoway's words.
  - `recast()` redraws base and range types as the target, with twoway's out-of-group fallbacks and notes (a yx type falls back to scatter, a range type to rspike, a pc type to pcspike; a range type cast to a yx name draws its first bound; `function` and `dot` ignore it). A derived type (fit, kdensity, function, histogram) keeps its computation and is drawn as the target. The key keeps the original series label. `recast(bar)` uses the one-x-unit width (BR-30.17).
  - `recast()` on lfitci, qfitci, lpolyci and fpfitci is refused r(198) `recastas() option not allowed`. Where twoway draws the same picture, dash is silent.
  - `cmissing(n)` on area/rarea and `connect()` on rarea stay noted (P2.42).
- **BR-30.9** `horizontal` (P1.9):
  - It is drawn on bar, rbar, spike, rspike, rcap, rcapsym, dropline, area, rarea, histogram, kdensity and function, with the axis variables, default titles, date kinds and y2 swapped and rcap caps perpendicular. Mixed orientation with a date axis matches twoway's truth.
  - `horizontal vertical` together is refused r(198) `may not combine options horizontal and vertical`. `horizontal` or `vertical` on a type twoway refuses them for is refused r(198) in twoway's words, judged on the type after `recast()` (`recast(bar) horizontal` is rc 0). `vertical` alone is accepted silently. The unsupported-option list and notes stop naming them.
  - After saved and served moves, turned layers keep their geometry; hover fields and the hover line follow the orientation; by() and `yaxis(2)` hold.
- **BR-30.10** `text()` and `ttext()` (P1.10):
  - Each copy is drawn at its position with its placement, orientation, size (Stata units), colour (BR-30.13), box and axis, on numeric and date axes (Stata units), on every by() panel with `iscale()`, after a move. Labels never extend the axis. Repeated copies keep their own sub-options. The scheme's text defaults apply. SMCL in the text follows BR-30.11.
  - Refused r(198) in twoway's words: a malformed point (`invalid point, BAD 30`), a missing axis pair, an unknown sub-option. A textbox sub-option that cannot be drawn is noted and listed in the help. Notes are raised once, in Stata, for both modes.
  - `ttext()` converts date literals under the first-plot or `xlabel()` format rule, with twoway's date refusals.
  - Limit `added_text` [R5]: default 1,000, ceiling 100,000, `$dash_max_added_text`; it counts texts × by() panels over the dashboard, and beyond it the command is refused r(134).
- **BR-30.11** SMCL and TeX (P1.11):
  - TeX delimiters (`$$…$$`, `\(…\)`) in any user text on the canvas are drawn as typed, never interpreted [R7]. The saved page ships no MathJax (a TeX title's page drops from about 3.1 MB to about 1.3 MB), and no user text reaches a TeX parser.
  - The graph-text tags `{bf:}`, `{it:}`, `{sup:}`, `{sub:}`, `{&name}`, `{c #}`, `{c name}` and the font tags (`{stSans}`, `{stSerif}`, `{stMono}`, `{stSymbol}`, `{fontface}`) are drawn as twoway draws them, in Unicode, with whole-string style and font set only where SMCL asks, at every canvas sink (titles, axis titles, tick labels, keys, panel labels, colour key) and in marker labels. A run Unicode cannot express gives one note per graph and sink kind. Other SMCL is drawn as typed and listed in the help (P2.47).
  - `{c 0}` empties the text and C0/C1 control codes are kept, as twoway does; every sink carries them escaped (`\uXXXX` in JSON/JS, HTML-escaped where HTML is written) [R8, changed]. dash-only page text translates characters and symbols and strips style tags; KPI and dashboard titles, `tabs()` and data-borne text (string tooltips, value-label columns, the CSV) stay raw, as the help states.
  - Hostile text (100,000 `{`, deep nesting) is handled in under one second.
- **BR-30.12** Size units (P1.12):
  - Numbers and keywords are Stata's relative units: one unit for every class at the 4-inch reference (rs = 2.88 pt; IR-1). The default marker goes from 8 to 5.87 px and the default line from 1.5 to 1.15 px.
  - `#pt`, `#in`, `#cm` and `#rs` convert at min(xsize, ysize) (graphsize when given); `*#` is relative; the full keyword ladder holds, `vhuge` included. Line widths follow Stata's linear ladder, `vvvthin` and `none` included, with a 0.3 pt hairline floor.
  - This holds for `msize()`, textbox `size()`, `labsize()`, `mlabsize()`, legend `size()`, title and axis-title sizes, colour-key label sizes and every line width (`lwidth()`, `mlwidth()`, `clwidth()`, `alwidth()`, region and reference-line widths, colour-key lines). `mlabgap()` is measured from the marker's edge.
  - An unknown size name draws the class's medium, noted as twoway notes it. Negative unit and multiplier forms are refused as twoway refuses them.
  - Brushed-away (nonselection) and muted copies of a glyph follow the option appliers: their size, width, colour, marker and dash are the drawn glyph's, with dash's nonselection alpha kept, in both modes (S08; later appliers reach them through S08's sync) [R27, changed]. P2.49 is not filed.
- **BR-30.13** Colour grammar (P1.13):
  - `colour*#` (with the clamp above 1), CMYK, HSV, quoted forms with intensity, `%` and `*` in either order, and `bg`/`fg`/`background`/`foreground` from the scheme are read in options and in scheme files. Invalid multipliers are ignored as twoway ignores them.
  - A bare `*#` or `%#` at any colour site (markers, lines, fills, CI bands, marker labels, titles, subtitles, notes, captions, axis titles, label and axis-line colours, graph and plot regions, the KPI, reference lines, `colormissing()`) takes the site's own base colour before intensity, composed with the intensity blend and a named style's base colour.
  - Colour names are case-sensitive, in options and in scheme files. An unknown or out-of-range colour draws black (bars #333333), noted, at every site. `grey`, `dimgrey`, `bluishgrey` and `ltbluishgrey` become unknown names (IR-6). `"255,0,128"` is refused r(198) in twoway's words. A short or invalid hex draws the default, silently. An unreadable scheme value draws #000000 for that key where twoway does.
  - The KPI keeps its case-insensitive Stata lookup ahead of CSS colour names.
- **BR-30.14** Named styles (P1.14):
  - `pstyle()` (and its `p()` alias: its own key, the first copy wins, applied last), `lstyle()`, `clstyle()`, `mstyle()`, `mlstyle()`, `astyle()`, `alstyle()`, `bstyle()` and `blstyle()` take `p1`-`p15` on every type, in twoway's factor order: explicit options win.
  - Every linestyle name of Stata's 76 shipped linestyle files resolves, and a table of the other Stata names (ci, ci2, histogram, foreground, background, grid, major_grid, minor_grid, refline, none and the p#line/bar/area/other/mark/box/dot/arrow forms) resolves (IR-14). `pstyle(ci)` and `ci2` work on non-CI types.
  - An unknown name draws twoway's default attributes for its class, noted once per layer.
  - `dstyle()`, `dlstyle()` and `bmlinestyle()` are accepted, kept in the spec and named as not drawn (P2.9, P2.8). Area and rarea outlines and pc arrowheads stay noted (P2.12, P2.8).
- **BR-30.15** by() (P1.15):
  - Panel labels are drawn as a centred panel title, not appended to the graph title. Composite labels are joined with ", ". Missing panels read "(missing)", and a string `""` group counts as missing in group panels and in Total. Date panel titles keep dash's date text [R9].
  - `by(, title() subtitle() note() caption())` are drawn once over the array. The "Graphs by <label>" note uses the variable's label, else its name, and `by(, note(""))` removes it. `by(, graphregion() plotregion())` stay named, not drawn (IR-9).
  - `rows()`, `cols()`, `holes()` and `colfirst` place panels as twoway does. `cols()` beyond the panel count is honoured up to the by() groups limit (100, ceiling 1,000), then clamped, noted [R9]. `iscale()`, `imargin()` and `compact` act in Stata units; `xsize()`/`ysize()` size the whole array.
  - Refused as twoway: `rows()` with `cols()` r(198) `may not specify both rows() and cols()`; out-of-range `rows()`, `cols()` or `holes()` r(125); capitalised forms (`YRESCALE`) and a repeated `style()` r(198).
  - Shared panels show outer axes and edge labels only, with the `i*`/`noi*` options and `noedgelabel`. Axis titles are drawn once, and no panel draws an axis-2 title. There is one legend, governed by `by(, legend())` (with `at()`) and the scheme's by-legend position. There is one colour key, only under `by(, clegend(on))`, showing panel 1's mapping, silently; a level has the same colour in every panel.
  - Each panel label is drawn in twoway's filled box from the scheme (S53, Q-28.1; ratification row 36, changed).
  - On a narrow screen the panels stack and every panel's axis labels show. Forms twoway ignores under by() are silent.
- **BR-30.16** Keys and default titles (P1.16):
  - lowess, lpoly, mband, mspline and function layers are keyed in twoway's text (for example "lowess mpg weight", "Median bands"); the pc family, scatteri and pci are keyed as twoway keys them; a function name may be any Unicode identifier of at most 32 characters.
  - Default axis titles follow twoway's first-equals-last rule per axis: no title when the layers' labels differ. Range types get a y title. `yaxis(2)` is titled by its own layers' variables [R10]. There is no opt-out.
  - Merged keys, histogram-only legends and first-used-axis placement stay open (P2.50-P2.52).
- **BR-30.17** Bar and range geometry (P1.17):
  - bar and rbar default to one x unit wide (in the variable's units on a date axis); rbar honours `barwidth()`; widths do not change after a move.
  - rcap's cap length follows `msize()`, defaulting to the scheme's p# symbol size; rcapsym draws no caps and sizes its end markers from the scheme. rcap `barwidth()` is refused r(198) `option barwidth() not allowed`.
  - The default base of bar, area, spike and dropline is twoway's: clamped into the axis scale (under by() the common minimum; per panel under `yrescale`; never 0 on a log axis), so a 0 outside the data no longer extends the axis. An explicit `base()` stays inside the range. On a date axis the default base is 01jan1960.
- **BR-30.18** Axis sub-options (P1.18):
  - `nolabels`/`labels`, `noticks`, `labcolor()`, `tlength()`, `tposition()`, the anglestyle names (`rvertical`, `stacked`, …), `xscale(off)`/`on`, `noline`/`line`, the axis line's colour, width and pattern, `alt` and `titlegap()` are drawn on every axis, second axes included. Tick-only positions honour `noticks`, `tlength()` and `tposition()`.
  - An anglestyle name is matched case-sensitively: `angle(Vertical)` is noted and drawn at 0, as twoway does (IR-5). Out-of-bound angles (`angle(400)`) and capitalised `NOLABELS`, `OFF` and `Alt` are refused r(198) in twoway's words. Under by() the `scale(off)`, `nolabels`, `noticks` and `titlegap()` that twoway ignores are silent.
  - `add` adds to the default ticks (date ticks included) and survives every re-tick after a move; an `axis(2)` label with `add` is drawn; a repeated `add` is kept; `a(b)c` rules and `norescale` on a lone rule draw as twoway draws them.
- **BR-30.19** Sub-option abbreviations (P1.19):
  - Legend, axis-label and tick, `xline`/`yline` and textbox sub-options accept twoway's abbreviations (`c()`, `r()`, `lab()`, `posi()`; `labs()`, `glc()`, `ang()`, `for()`, `g`, `nog`, `val`, `labc()`, `tl()`, `tp()`, `nolab`, `noli`, `titleg()`; `lc()`, `lp()`, `lw()`, `lst()`, `noex`, `la()`, `st()`; textbox `s()` is size).
  - Names match in lower case only. Capitalised names and spellings twoway refuses are refused r(198) in twoway's words. A sub-option dash honours, given a bad value, is refused with twoway's code (`legend(c(red))` r(121) `cols() invalid`).
  - Repeated copies merge by full name, the last copy winning; `rows()` beats `cols()`; quoted label text is never read as a sub-option. A note names the sub-option as the user typed it.
- **BR-30.20** `plotregion()` and `graphregion()` (P1.20):
  - Their sub-options and abbreviations (`fc()`, `lc()`, `c()`, `lw()`, `lp()`, `ls()`, `sty()`, `col()`, `fcol()`, `mar()`) are drawn: `color()` sets fill and outline; `none` paints nothing; `%NN` opacity; `style(none)`, `lstyle(none)` and the area-style names; `lpattern()`; the graph outline; widths on Stata's ladder. Repeated copies merge and margins add up.
  - Typos and a sub-option repeated within one copy are refused r(198) in twoway's words. Valid forms dash cannot draw (`lalign()`, `ilalign()`, `graphregion(margin())`, the graphregion `i*` options) are named in one note.
  - `bgcolor()` paints under the graph region, as twoway does: a region `none` shows `bgcolor()` if given, else the scheme's background, and a lone `bgcolor(red)` no longer shows (IR-2).
  - `plotregion(margin())` sets the plot-region margin (exact for zero; within BR-30.3's tolerance otherwise [R1]). The plotregion `i*` inner box is drawn at the finished range and follows it after a move.
  - Region styling writes only computed numbers and sanitised colours into the page.

- **BR-30.21** `xline()` and `yline()` (P1.21):
  - Numlist positions (`2000(500)3000`, `a/b`) are drawn; duplicates are dropped.
  - Refused as twoway, in twoway's order, r(198)/r(100)/r(123): invalid positions (including `nan`, `inf`, `1e400` and `1_000`, `invalid line argument`), more than 2,500 positions in one copy, and unknown, short, repeated or capitalised sub-options (`NOEXTEND`, `LSTYLE()`).
  - Abbreviations follow BR-30.19. `lstyle()` takes every linestyle name (BR-30.14). `lalign()` is accepted silently. Lines are drawn above the grid and below the glyphs, and never extend the axis.
  - `extend`/`noextend` and `style()` follow the scheme's xyline extend keys, over the finished axis and again after every move; under `margin(zero)`, `noextend` equals `extend`.
  - Limit `reflines` [R6]: default 10,000, ceiling 100,000, `$dash_max_reflines`; it counts positions × by() panels over the dashboard, and beyond it the command is refused r(134).
  - A line outside the range is clipped at the frame (P2.54).
- **BR-30.22** `function` without Stata's points (P1.22, closed by disposition under M12):
  - A Stata-built spec draws Stata's own points (WP-29 P0.6, unchanged).
  - The points-free fallback keeps its ten functions. Any other function draws nothing and gives one neutral note, in both modes, that reaches Stata: it says the layer needs Stata's points, lists what the fallback knows and names the function it met (true for `pi`, `e` and `sin (x)`).
  - The help states the rule and no longer promises a draw from the expression.
- **BR-30.23** Dates on every axis (P1.23):
  - Range and pc plots with a date y (or a pc date x) get a date axis. An `axis(2)` layer keeps the primary date axis. y2/x2 date axes show dates, take their own options and `#N` ticks, and range in date units.
  - scatteri, pci and pcarrowi coordinates, `function range()` and an explicit `base(#)` are placed in date units. A literal outside 0100-9999 on a date axis is drawn at its number as twoway draws it, with no note; only one past the browser's dates (|ms| > 8.64e15) is left out with one note [R12, changed].
  - A date layer beside a numeric layer on one axis is drawn in Stata units, labelled in the first layer's date format [R11], and `xlabel(minmax)` reads Stata units there. The mixed axis renders under the page's CSP.
  - A date colour variable's key, ticks and `colorcuts()`/levels boundaries are in Stata units; key text uses twoway's comma general format; `zlabel(, format(%t*))` is honoured.
  - Fallback tooltips (histogram, fits, kdensity) use the variable's display format. The histogram tooltip names its measure (Density, Frequency, Fraction or Percent), not "Count".
- **BR-30.24** `mlabvposition()` and `mlabtextstyle()` (P1.24):
  - `mlabvposition(varname)` places each row's label in both modes and after saved and served moves. One variable applies to every y and is never split. Offsets stay physical under `horizontal`.
  - A repeated `mlabvposition()` and the types twoway refuses it on are refused r(103) in twoway's words (naming the label variable when `mlabel()` is given), judged on the type after `recast()`.
  - `mlabtextstyle()` is a per-y list (BR-30.1) resolved from Stata's 37 shipped textboxstyle names on the scheme's marker-label defaults. A user textboxstyle file is noted (P2.55).
  - No declared plot option is silently dropped: each reaches the spec or the list of options named as not drawn.
- **BR-30.25** Scheme resolution (P1.25):
  - The six StataCorp schemes dash refused (meta, stcolor_meta, stcolor_mv, stcoloralias, stgcolor_meta, stgcolor_mv) are shipped and drawn as twoway draws them: 26 schemes in all. stcoloralias draws as stcolor (its `zyx2rule` is unread, documented).
  - `scheme(NAME)` and an inherited `c(scheme)` resolve along Stata's whole ado-path in Stata's order, as `scheme-NAME.scheme` then `NAME.scheme`, with the shipped StataCorp names first, so a working-directory `s2color.scheme` no longer overrides the shipped one. `#include` follows the same walk. An inherited `c(scheme)` always walks; an explicit theme alias loses to a file of that name and works when none exists.
  - A path, separator, `..` or quote in `scheme()` is refused. A file that is not regular, that resolves outside its directory, or that exceeds the size limit is refused. A scheme file is read as data and never run. The refusal lists the 26 names and the themes, and the help's remedy is corrected.
  - A served dashboard whose graphs use different schemes draws each graph with its own scheme, as the saved page does [R28] (its own entry, P1.25.6).
- **BR-30.26** Notes (P1.26):
  - A note is one `(note: …)` line in text colour, shown under `quietly` and `set output error`, hidden by `capture`, SMCL-escaped, and free of internal paths and source lines [R13]. A session `warnings` filter neither hides a note nor turns it into an error (no r(7102)). A repeated note prints once.
  - `dash build, server` prints the saved build's option and empty-layer notes, from one trial render [R14]. `dash serve` relays the child's notes, ERROR lines and tracebacks (redacted, at most 200 lines, de-duplicated against the build's), from the child's warm-up, never rendering twice. A trial that raises stops `dash serve` with r(198) and is noted under `dash build, server`. Access-log lines stay out.
  - A layer whose own if/in keeps no row is silent in both modes, as in twoway.
- **BR-30.27** Command form and `saving()` (P1.27):
  - Batch mode and `set graphics off` open no browser and print the path; interactive console Stata still opens one [R15]. A temporary preview is still written, and its line says it is temporary and names `saving()`.
  - A `twoway`, `tw`, `two` or `graph twoway` prefix is accepted. `twow`, `twowa`, `gra` and `grap` are refused r(199) `command X is unrecognized`, as twoway refuses them.
  - `saving(f, replace)` and `saving(f, asis)` are read as twoway reads them, on the one-line form, `dash build` (HTML and server) included. An unknown `saving()` sub-option is refused r(198) `option X not allowed`; an unquoted `saving(my file.html)` is refused as twoway refuses it.
  - Under M11 `saving()` accepts `..` and `; & | < >`, and keeps refusing a double quote, backquote, `$`, control characters and a leading `-`. The served "To launch" line is single-quoted on Mac and Unix.
  - `dash twoway` with nothing after it stays refused (P2.56).
- **BR-30.28** Export (P1.28):
  - dash returns `r(filename)`: the absolute path of what it wrote, set last, never holding the served key, empty when the command is refused, and documented as transient for previews [R16]. No other internal `r()` leaks from any subcommand.
  - One note per dash command, only when Stata holds a graph in memory, says that `graph export` would write that graph [R16]. A `saving()` name with an image extension writes `.html`, noted.
  - The help documents the export limit and that printing prints the active tab.
  - Every grid toolbar in both modes gains a "Save as SVG" action that runs under the page's CSP. There is no SVG backend, so the PNG save keeps working.
- **BR-30.29** Page security (P1.29):
  - The saved page's script policy lists a hash for every inline script and no `'unsafe-inline'`. An inline script without its hash stops the build with a named error and writes nothing.
  - The served page carries a per-document nonce: nonce-only if the browser test is clean, otherwise also `'self'` with the reason recorded [R17]. The `python app.py` header keeps its policy and the page's own policy governs [R17]. `'unsafe-eval'` and inline styles stay (BokehJS needs them) and are documented. The empty and redirect pages carry `default-src 'none'`.
  - In a browser, in both modes, an injected inline script or handler is blocked, and the page still renders, filters and exports. A browser that supports only CSP level 1 shows a blank page [R17].
  - On Windows a path holding a cmd metacharacter (`% ! ^ & | < > ;`) is written but never opened through the shell: the path is printed, `r(opened)` is 0, `r(why)` says why, and the command ends rc 0 (tested as a pure function and a dry run).
  - The help states the `saving()` character rule and what the CSP does and does not protect.
- **BR-30.30** The bokeh window (P1.30):
  - `dash_setup` installs `bokeh>=3.8,<3.10` (`<3.11` only if bokeh 3.10 is verified inside WP-30) into an environment dash created. A Python or environment dash did not create is never downgraded: above the window it is reported "outside the verified range" with rc 0 [R19]; a managed Python gets the managed guidance, never a pip line.
  - At run time, in both modes: above the window one note and the run continues; below 3.8 the command is refused, and so is the served app at start (`python app.py`, `bokeh serve`). "Verified" means major.minor [R18].
  - The text-sink injection checks run for every version in the window.
  - If a Bokeh release changes an internal dash relies on (host matching, the page template's blocks, the origin check, the auth hook, the BokehJS calls the ticker, the date transform and Save as SVG use), the server refuses to start with a named error [R19].
- **BR-30.31** Served capacity (P1.31):
  - The dataset is decoded once per app process. At most `maxsessions()` sessions run at once (default 20; 0 refused) under `dash serve`, `python app.py` and `bokeh serve` [R20]. Beyond the cap a static busy page answers (HTTP 503 with Retry-After, no auto-refresh) [R23].
  - A session with no filter, brush or CSV activity closes after `idletimeout()` minutes (default 60; 0 never), with a reload message [R20].
  - The app warms up before it listens and first prints "preparing the dashboard (N rows, …)".
  - Per-session memory growth stays at or below 80 MB at 200k rows × 3 layers (60.7 MB today, so the test is a regression guard). The estimator memo holds at most 64 MB per process and never runs in Stata's process [R22, changed].
  - A filter-move recompute never blocks other sessions or `/health`: one worker; the latest request per session wins; stale results are dropped; the session shows an "updating" cue. The worst wait (about 3 min at 20 × 8.7 s for lowess at 100k) is documented [R21].
  - Opening a session still runs on the event loop (P2.57).
- **BR-30.32** Dependency guards (P1.32):
  - A missing or unimportable numpy, pandas or bokeh, or a Python below the floor, gives one message naming `dash_setup`, from `dash` and from the generated app, never a bare `ModuleNotFoundError` or `SyntaxError`. bokeh below 3.8 is refused (BR-30.30). numpy or pandas below `dash_setup`'s minimums is noted, not refused [R24].
  - dash checks availability without running Python as a program, before it renders.
  - `dash_setup`'s first Python call is captured and summarised with the architecture hint.
  - `dash clear` still prunes with the packages missing.
- **BR-30.33** The Python floor (P1.33):
  - The declared floor is the lowest of 3.11 and 3.12 at which both pytest suites (with the dev pins and with the Stata pins), a fresh resolve as `dash_setup` installs, the Stata venv-link leg and one full certification run pass. `dash.pkg`, both help files, `dash_setup` and the version messages state it, and code that needs a newer Python has a fallback or guard.
  - `dash_setup` with a Python below the floor says to link Python <floor> or later and never suggests `venv()`.
  - The floor is measured once, in WP-30, by S05; the release gate gains no floor-Python leg, and the manual re-measure procedure is written in `scripts/floor_matrix.sh`'s header [R25, changed]. Downloads go only into scratch environments (M10).
- **BR-30.34** Portable runners (P1.34, closed under M4):
  - Every runner (`scripts/stata_slot.sh`, `run_cert_suite.sh`, `run_release_gate.sh`, `stata_python_exec.sh`, the Makefile, the header of `test/run_all_cscripts.do`, `measure_stata_coverage.py`, every extractor, `test/fixtures/twoway_corpus.do`) uses `STATA_BIN` if set, else `/usr/local/bin/stata-mp`, with an architecture prefix only when the binary's own architecture needs one (right under Rosetta). No runner selects a Stata 14-18.5 binary.
  - The repository root is `DASH_REPO`, else the current folder when it holds `dash.ado` and `test/run_all_cscripts.do`, else r(601).
  - No file under `scripts/`, `test/` or the Makefile holds `arch -arm64` or the maintainer's path (a guard test, no exemption list). The two option generators are retired and refuse to run [R26].
  - On this Mac the effective command is unchanged (the console binary in batch mode).
- **BR-30.35** The Stata floor (P1.35, closed under M2):
  - `dash` and `dash_setup` refuse a Stata below 19 as their first act, with `dash requires Stata 19 or later; this is Stata X.Y` and r(9).
  - Every program declares `version 19`; no `version 16.0` remains in dash.ado, dash_setup.ado or the generators that write one.
  - `dash.pkg` and both help files say "Stata 19 or later; tested on StataNow 19.5 (MP), macOS arm64" and "Measured on MP only".
  - Function points are unchanged by the new language level, and a full certification run is green after the sweep.
- **BR-30.36** Refusals (M5): every form WP-30 newly refuses (the register's 26 M5 rows and those of IR-17) is refused with twoway's return code and message text as measured in StataNow 19.5, has a test asserting both, and has a CHANGELOG line under "Changed behaviour (may need your do-files changed)". A valid twoway option dash cannot draw is noted, never refused. Outside the areas WP-30 touches, nothing is newly refused.
- **BR-30.37** Silence (M6): where twoway draws the same picture and prints nothing (the register's 11 M6 rows, among them a layer whose own if/in keeps no row, the by()-ignored axis forms, a lone style value over several y, the levels the single by() colour key leaves out, a user scheme's `intensity bar`/`intensity area`, and a short or invalid hex), dash prints nothing in either mode.
- **BR-30.38** Both modes: every behaviour in BR-30.1 to BR-30.35 that concerns drawing holds on the saved page and in the served app, before and after a filter move, and the two modes draw the same. No saved/served difference is allowed for in the parity test.
- **BR-30.39** Announced changes (M1, M5): every look change has a CHANGELOG line under "Results that change" naming the command, the old value and the new; every newly refused form has one under "Changed behaviour"; every new capability under "New"; the floors and the bokeh window under "Requirements"; every closed threat under "Security".
- **BR-30.40** Tracking: every WP-30 BUGS.md entry is closed with a Resolution naming tests that exist; every CHANGELOG marker is replaced; ROADMAP WP-30 is DONE; the GAPS2 ids it closes are marked with commits that exist; the manifest's residuals and P2.42-P2.57 are filed.

## 7. Foundation (S01) and closeout (S58) content

`index.md` holds the exact steps ("Batch 0", "How to execute", R1-R5). This section states what the two bookend sections must leave behind.

### S01 — Tracking foundation (one commit, `(WP-30 S01)`; changes no shipped file)

1. **BUGS.md.** Append the 56 open entries at the end of the file, in entry order (A140), in the five-field form. Each entry carries:
   - a title with no `"` in it;
   - **File Names and Line Numbers**: HEAD anchors at `c96facd` from the section's design;
   - **Description**: the DROPIN text and its source ids, matched by content where the ids have no literal anchor (the REM-08-04 ids to S35, the REM-08-05 ids to S17, GAPS2-B16-a..e to S28/S48/S53, GAPS2-D3-a..e to S09 and S29);
   - **Suggested fix**: one sentence naming its section;
   - **Resolution**: `Not fixed because WP-30 section <NN> has not landed. Graded S<n> (WP-30): <why>.`

   An open entry names no test file or case id, since the reference checker would read a test that does not exist yet as dangling. The extra entries of A146 are not S01's.
2. **CHANGELOG.md.** Place the 84 markers `<!-- WP-30 P1.<n>[a|b|c] -->` in the existing release `## 0.1.0, 02oct2026 (release candidate)`, in entry order within each list (R4): Results that change 34 (a `**WP-30 (drop-in P1, 03oct2026)**` group at the end of the list), Changed behaviour 24 (P1.17a carries one), Fixed in WP-30 10 (a new `### Fixed in WP-30` with a one-line introduction, directly above `### Fixed in WP-29`), New 7, Security 5, Requirements 4.
3. **`test/test_tracking_documents.py`.** Add `WP30_OPEN` (56 keys, entry id to title, one per line, in entry order), `WP30_LISTS`, `WP30_ALL`, `_WP30_MARKER`, `_WP30_OPEN_FORM` and `TestWp30Tracking`, mirroring WP-29's block: a stale allowance is red; an open entry keeps at least one marker; a closed entry has no marker and a Resolution holding `(WP-30, <id>)`; the marker reader is tested both ways. Extend the release allowance in `test_no_open_entry_is_s1_or_s2` to `WP29_OPEN` and `WP30_OPEN` (A144).
4. **`test/test_wp30_truth.cscript`.** The scaffold in R1's order: the `cscript` line, the `c(python_exec)` skip, `cert_helpers.do` and `cert_svg.do`, S01's own block (case `TF-01 PASS`), 56 stub blocks S02-S57 in section order (each printing its start and end lines), the marker line and the pass line. Register it as runner block `// 69.` after `// 68.`; move the hygiene pins 67 → 68 and 49 → 50 with their comments; add `TestTheWp30TruthScript` (the `WP30_ONLY` gate, section order, the marker last).
5. **Registries.** The map anchors of A148 in `test/function_test_map.py` and `test/program_coverage_map.py`, and `TestTheServedAppCarriesEveryName::test_every_listed_name_exists` (A149; measured green at `c96facd`: 145 constants and 312 functions defined).
6. **Verify.** `test_tracking_documents.py`, `test_cscript_hygiene.py`, `test_packaging.py`, `test_cert_verdict.py`, `test_function_test_map.py`, `test_program_coverage_map.py` and `test_statistical_helpers.py` are green; the driver run of the truth script prints `TF-01 PASS` and all 56 stubs' start and end lines; one full run through the queue is green; `gitnexus detect-changes` lists only these files.
7. **Commit** `Open the WP-30 P1 entries, markers and truth script (WP-30 S01)`. S01 does not touch ROADMAP.md (A145).

### S58 — Closeout (main checkout, one commit per step, `(WP-30 S58.<k>)`)

1. **S58.1 Tracking.** Confirm that every WP-30 entry is closed with its commit, then replace the map with `WP30_OPEN = {}` (with a docstring like WP-29's) and add `TestWp30Tracking::test_no_wp30_entry_remains_open`. Remove the map anchors left empty. BUGS.md then holds exactly 3 open entries: BUGS.md:2559, :2595 and :2601 (as at `c96facd`); P2.49 is not filed [R27, changed].
2. **S58.2 Tracking documents** (A145; AGENTS.md only under index E7):
   - **ROADMAP.md.** Insert `## WP-30 · Close the drop-in P1 gaps — DONE` directly above `## Traceability matrix` (ROADMAP.md:4763 at `c96facd`). It carries the header line `**GAPS2 closed:** <ids> · **Severity:** <counts of S01's grades> · **Effort:** XL · **Depends on:** WP-29`, the user stories, BR-30.1-BR-30.40 copied from §6 with the [Rn] tags removed and every struck row's amendment applied, TRs pointing at `index.md`, and AC-30.1-AC-30.15 mirroring §9. It also records the scope changes of P2.11-P2.14, P3.2, P3.7, P3.9 and P3.11, and one deferred platform package (P1.34.6) carrying the item-34, item-28 and item-35 residuals.
   - **GAPS2.md.** For each GAPS2 id a P1 source names, decide fully or partly closed, citing sub-items and commits. A fully closed id gets `- **Tracked:** Closed in WP-30, BUGS.md "<title>", commit <sha>`, a place in ROADMAP's `**GAPS2 closed:**`, and `(WP-30, <id>)` appended to that entry's Resolution; a partly closed id gets `Partly closed in WP-30 (P1.<n>, commit <sha>); open: <what>`.
   - **REMAINING.md, GAPS.md and DROPIN-REMAINING.md**: the REM ids and each P1 row annotated with its commits; P1.22 recorded closed by WP-29 P0.6 plus S26's note (and GAPS2.md:228 updated).
   - Run `test_tracking_documents.py`.
3. **S58.3 Residuals and the audit.** File the 22 manifest residuals as P2/P3 rows or in the platform package, as amended: IR-2 (item 20 keeps only the exact outer margin, P2.53), IR-3 (item 8 loses stairstep hover), IR-4 (item 4 keeps only the lower-case shorthands), IR-9 (by()'s overall regions become a P2 item). Add rows P2.42-P2.57. Tag TWOWAY_COVERAGE_AUDIT.md. Fix the stale `test/fixtures/rejected_options.json` rows S51 did not own.
4. **S58.4 CHANGELOG consolidated.** The lists are Results that change, Changed behaviour, New, Requirements (Stata 19, the measured Python floor, the bokeh window), Security and Fixed in WP-30. `grep -c '<!-- WP-30' CHANGELOG.md` prints 0.
5. **S58.5 Release gates** (nothing committed): `make test`, `make test-dev`, `make cert` (timed against the step-0b baseline) and `make gate` (no floor-Python leg [R25, changed]), once each, in that order, through the queue. A red result goes back to the owning section's fix cycle.
6. **S58.6** only if the release date must move: the release heading, `dash.pkg`'s Distribution-Date and the files the release pins.
7. **S58.7 Report.**
   - Record the release measurements: the saved page size with and without MathJax, render times, served memory and latency under the session cap, the certification run's duration and its change from the baseline, and per-block times from the truth script's start and end lines.
   - Re-check S02's path guard and S03's version pin; run `gitnexus detect-changes --scope compare --base-ref main --repo dash` and re-index; run the message checks of E13.
   - Report the merge command `git checkout main && git merge --no-ff wp30-p1` without running it (project rule 5).
   - List the residuals and partly closed GAPS2 ids, the deferred platform package, the documented divergences the rulings introduce (the tsnatscale agreement floors [R2], the plot-margin tolerance [R1], date panel titles [R9], the CSP level 1 blank page [R17]; date literals past the browser's dates (|ms| > 8.64e15) left out with a note [R12, changed]; control codes and literals outside 0100-9999 now mirror twoway [R8, changed], [R12, changed]), and every ratification row that was struck (none: all 44 were answered 06oct2026).

## 8. Risk register

`index.md` "Risk register summary" (RK-1..RK-14) covers what the batch plan controls; this register is the package's. Owners are sections.

| # | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| K1 | Many sections edit the same hot symbols of `dash_render.py`: 17 `_generate_app_source` editors, 9 `_make_figure_body` editors, the four appliers, `_build_filter_widgets`, `_build_sources_and_figures` | high | merge conflicts, lost hunks, a broken served app | One editor per batch for each (A139, R12); distinct copy-list anchors (R2); `git apply --index -3` per commit; impact at every batch base with HIGH/CRITICAL reported before editing; the full suite and the registry tests after every batch (G8) | merger; S18, S21, S23, S35, S38, S40, S47, S49, S56 |
| K2 | M1 changes the look of every published dashboard: marker and line sizes, title chrome, opacity, ticks, margins, bar widths and bases, keys and titles | certain | users see different pictures; pinned page digests move | Accepted by M1 and [R1], [R2], [R3], [R10]; a CHANGELOG "Results that change" line with old and new values per change (BR-30.39); the single-y page digest re-derived on the merged tree with a reason (R10); G3 parity | S08, S13, S14, S15, S16, S19, S21, S24, S27, S30, S43, S44 |
| K3 | M5 refusals stop do-files that ran before | high | user do-files fail | Refuse only measured twoway refusals, with twoway's rc and words, in the areas WP-30 touches (BR-30.36); one CHANGELOG "Changed behaviour" line per form; P2.21 keeps the rest of the surface unchanged | S10, S11, S12, S13, S14, S18, S20, S31, S38, S39, S40, S42, S45, S48, S49, S51, S56 |
| K4 | The natscale ticker, margin and after-move re-finish (red): five CRITICAL symbols, both modes | medium | wrong axes, slow moves | Batch 7's only finisher, template and figure-body editor, landing last; timed budgets [R3] and the 100-panel bound pinned; never landed without the after-move re-finish (RK-1) | S21 |
| K5 | The tsnatscale JS port (about 350 lines) disagrees with the Python model | medium | saved and served date ticks differ | Parity on the fixture's 12,000 answers, with the agreement floors pinned [R2]; no BokehJS view internals; date path only (RK-2) | S44 |
| K6 | The served worker races the event loop | medium | corrupted sessions or a deadlock | Alone in batch 20 after every served section; a thread-safety audit of the final move path; Bokeh's thread rules verified across the bokeh window; latency measured at N = 100k (RK-3) | S57 |
| K7 | Dropping `'unsafe-inline'` blanks a page, or later inline JS runs unhashed | medium | blank dashboards | A headless-browser test in both modes; an unhashed inline script fails the build (A98); S35, S53 and S54 re-run the browser check under the policy; CSP level 1 browsers named [R17] | S04, S35, S53, S54 |
| K8 | The version sweep changes the language level of 91 programs | medium | Stata results change silently | One commit; a full certification run in batch 1's gate; the pin that function points are unchanged; `test_version_floor.py` (RK-5) | S03 |
| K9 | New input surfaces open attacks: scheme files along the ado-path, the SMCL scanner, wider `saving()` characters, `text()` and reference-line counts, `t*` date tokens, served sessions, a property name in the redraw | medium | code execution, denial of service, path escape, script injection | Each landed with its threat test (G6, index G9): data-only scheme parsing with name, containment, regular-file and size guards; a linear-time scanner with hostile-input timing; the Windows opener before `saving()` widens; r(134) limits; date tokens never run as Stata code; a session cap; the redraw branches on a fixed name | S04, S12, S29, S34, S39, S46, S51, S55, S56 |
| K10 | Eleven scheme regenerations | medium | conflicting generated files | One regenerator per batch, landing last (S07 excepted, with reasons); never hand-patched; a conflict means a re-run of that section's extractor (A152, R7) | S07, S15, S21, S24, S30, S33, S36, S47, S50, S53, S56 |
| K11 | A name missing from a served copy list | medium | a served-only NameError | `test_every_listed_name_exists` (A149) and both served-name guards at each landing that touches them (G4) | every section that adds a module name |
| K12 | Notes and their test needles migrate twice | low | churn and missed notes | The note channel lands first, last in batch 2 (A150); every later note goes through it | S06 |
| K13 | twoway truth exists only for StataNow 19.5 MP on macOS arm64 | certain | other platforms and editions unknown | Fixtures stamp `stata_version`; the help says "Measured on MP only"; the platform package carries the rest (M2, M4) | S02, S03, S58 |
| K14 | A pinned test of today's behaviour is deleted instead of flipped | medium | lost coverage | A `Flipped:` line per test (R9); the collected test count never falls between landings | each section |
| K15 | Neither 3.11 nor 3.12 passes the floor matrix | medium | the floor stays 3.13; S25 reads it | The floor is whatever the matrix passes, never assumed; S25 reads the constant, not a number | S05, S25 |
| K16 | bokeh 3.10 cannot be verified in WP-30 | medium | the ceiling stays `<3.10` | M9 already allows it; recorded in the CHANGELOG and S58.7 | S41 |
| K17 | Downloads or a test interpreter change the maintainer's setup | low | a broken Stata–Python link | Scratch environments only (M10); never a `permanently` link; `stata19.rc` checked after each run (index E12) | S05, S41 |
| K18 | Budgets missed: the re-finish, per-session memory, the worker's wait | medium | slow or heavy dashboards | Measured at the batch base and pinned by timed tests [R3], [R21], [R22] | S21 (and S27, S35, S44, S47, S50, S52), S46, S57 |
| K19 | Machine contention: 100 pytest runs and 4 certification runs | high | stalls, false reds | The queue at 6 CPUs; runs never relaunched to check on them; one isolated re-run for the known flaky tests (index E1, E6) | orchestrator |
| K20 | Ratification rows struck after sections are written | closed (06oct2026) | re-planning mid-package | All 44 rows were answered 06oct2026 and none was struck; the eight changed rows are applied to the section files, the register, manifest.json and this plan before batch 1 (A151) | orchestrator |
| K21 | The manifest, register, research and this plan disagree | medium | a section builds the wrong form | `index.md` wins; IR-1..IR-17 bind; section files quote the IR rows they apply | each section |
| K22 | A section forgets its tracking duties (key, markers, Resolution) | medium | a red suite at landing | `TestWp30Tracking` fails the section's own G5 before its commit; two-commit sections close on their second commit (A156) | each section |
| K23 | A fix lands in one mode only | medium | saved and served pictures differ | `ALLOWED` in the parity test is never edited (R8); every drawing section adds CORPUS cases (G3) | each drawing section |
| K24 | The certification suite slows down | medium | release friction | Truth blocks gated by `WP30_ONLY` and timed per block; S58.7 reports the change against the baseline | S58 |

## 9. Success criteria and exit gates

ROADMAP's AC-30.k mirror these (S58.2). The gates G0-G11 are `index.md`'s.

- **E1 (AC-30.1)** The 56 entries S01 opened are closed, each with a Resolution `(WP-30, P1.<n>[abc])` naming tests that exist; `WP30_OPEN` is empty and pinned so. The extra entries are in place: P1.5.7 and P1.25.6 closed in their sections' fix commits; P2.49 is not filed, because S08 fixes it under P1.12a [R27, changed]. BUGS.md holds exactly 3 open entries.
- **E2 (AC-30.2)** Red first: each fix commit body opens with its saved failure text and a `Regression:` line per regression test (G1); every flipped test has a `Flipped:` line; guard tests are listed apart; there is no test-only commit; the collected test count never falls.
- **E3 (AC-30.3)** Truth: `test/test_wp30_truth.cscript` runs all 57 blocks with every case `PASS` and no SKIP on a machine with Python; every new fixture carries the D12 `_meta` stamp with `stata_version` and is committed; no fixture is hand-patched.
- **E4 (AC-30.4)** Parity: `test/test_mode_parity.py` is green with every drawing section's CORPUS cases; `ALLOWED` is unchanged; `_MUST_WARN` entries were edited only by the sections whose fixes silenced them.
- **E5 (AC-30.5)** Served names: `TestTheServedAppCarriesEveryName` (with `test_every_listed_name_exists`) and `TestTheServedAppDefinesEveryNameItReads` are green.
- **E6 (AC-30.6)** Refusals and silences: every M5 refusal row has a test asserting twoway's return code and message text as measured in 19.5, and a CHANGELOG "Changed behaviour" line; every M6 row has a test asserting no note in either mode.
- **E7 (AC-30.7)** Look: each shipped scheme's look truth passes (BR-30.2, BR-30.4); the size defaults are pinned (markers 5.87 px, lines 1.15 px); the tsnatscale floors and the 12,000-answer parity hold; the timed budgets of [R3] pass.
- **E8 (AC-30.8)** Security (G9): green, each named in its commit body:
  - the browser test of both modes (an injected inline script or handler is blocked; the page renders, filters, exports and saves as SVG); an unhashed inline script fails the build; `default-src 'none'` on the empty and redirect pages;
  - the Windows opener runs nothing for a path with a cmd metacharacter;
  - notes SMCL-escaped with no internal paths; relayed child output redacted and bounded;
  - TeX never interpreted; hostile SMCL handled in under one second; control codes kept as twoway keeps them and escaped at every HTML/JS sink [R8, changed];
  - the scheme lookup's name, containment, regular-file and size guards, with symlink, oversized, traversal and hostile-directive tests; scheme files never run;
  - region styling writes only computed numbers and sanitised colours;
  - the `reflines` and `added_text` limits refuse r(134);
  - date tokens never run as Stata code (no `_stata()` call takes user text);
  - Bokeh internals fail closed; below bokeh 3.8 refused at app start;
  - the session cap, idle close and busy page; the turned-bar redraw never reads a property name from page data; the worker's thread safety.
- **E9 (AC-30.9)** Floors: `grep -c 'version 16.0' dash.ado dash_setup.ado` prints 0 and 0; the Stata guard's refusal and the guard order are pinned; the declared Python floor equals the matrix's lowest pass; the bokeh window is declared once and checked at run time; the dependency guards are green; the runner path guard is green with no exemption list.
- **E10 (AC-30.10)** CHANGELOG.md holds no `<!-- WP-30` marker; every WP-30 line ends `(WP-30, P1.<n>[abc])`; each Results line names the command, the old value and the new.
- **E11 (AC-30.11)** Tracking documents: ROADMAP's WP-30 is headed DONE with §6's requirements and these criteria; every id in its `**GAPS2 closed:**` has a `Closed in WP-30` Tracked line with a commit that exists; partly closed ids say what is open; the 22 residuals (as amended) and P2.42-P2.57 are filed; DROPIN-REMAINING.md's P1 rows carry their commits; `test_tracking_documents.py` is green.
- **E12 (AC-30.12)** Release: `make test`, `make test-dev`, `make cert` and `make gate` are each green once on `wp30-p1`, through the queue; the certification time and its change from the step-0b baseline, the page sizes, render times and served memory and latency are recorded (S58.7).
- **E13 (AC-30.13)** Messages and scope: index G7's message check prints 0 on every commit message in `main..wp30-p1` and on the added lines of BUGS.md, CHANGELOG.md, dash.sthlp and dash_setup.sthlp; no commit, entry, CHANGELOG line or help line names a tool or vendor; the project instructions file, `.gitignore` and (outside index E7's rule) `AGENTS.md` are in no WP-30 commit.
- **E14 (AC-30.14)** GitNexus: impact ran at every batch base, every HIGH or CRITICAL result was reported before its edit and the approval recorded, every `UNKNOWN` was confirmed by grep; `detect-changes` at every landing named only the section's symbols; the final compare against `main` is recorded.
- **E15 (AC-30.15)** The merge command into `main` is reported and not run; every worktree and `wp30-s<NN>` branch is removed.

## 10. Traceability

Tests and fixtures are those the research and the manifest plan; the section file fixes the final names and case ids. Every section also fills its own block `S<NN>` of `test/test_wp30_truth.cscript` (written "truth S<NN>" below), adds CORPUS cases to `test/test_mode_parity.py` where it changes a drawing, and puts refusal and message cases into the existing cscript for its area (R1). No section creates or registers another cscript (A142). Each entry's DROPIN source ids are in its BUGS.md entry (S01).

| P1 | Entries → sections (batch) | BR | Tests and fixtures (planned) |
|---|---|---|---|
| P1.1 | P1.1a → S11 (4); P1.1b → S20 (7) | BR-30.1 | `test_stylelists.py` (new, S11); `stylelist_truth.json`; `test_value_lists.py` (new, S20); `value_list_truth.json`; `test_abbreviations.py` count pin flipped; HC2-18b and its `test_help_claims_2.py` mirror flipped; `test_varlist_expansion.cscript`; truth S11, S20 |
| P1.2 | P1.2a → S15 (5); P1.2b → S16 (6) | BR-30.2 | `test_scheme_chrome.py`, `test_svg_chrome.py`, `test_scheme_chrome_browser.py` (new), `chrome_truth.json` (S15); `test_intensity_blend.py` (new), `intensity_truth.json` (S16); `scheme_truth.json` and the 26 scheme files regenerated; `test_scheme_fidelity.py`; `test_server.py:4001` flipped; `test_help_claims_8.py`; truth S15, S16 |
| P1.3 | P1.3a → S21 (7); P1.3b → S44 (15) | BR-30.3 | `test_default_axes.py`, `test_natscale_js.py`, `test_default_axes_chrome.py` (new), `default_axes_truth.json` (S21); `test_date_axis_ticks.py` (new), `date_axes_truth.json` (S44); the tsnatscale fixture's 12,000 answers; `test_by_scales.py`, `test_axis_extents.py`; timed budget tests; closes BUGS.md:2523; truth S21, S44 |
| P1.4 | P1.4a → S24 (8); P1.4b → S33 (11) | BR-30.4 | `test_scheme_layer_alpha.py`, `test_histogram_scheme_style.py`, `test_scheme_symbol_traits.py` (new, S24); `scheme_layer_truth.json`; `test_label_key_chrome.py`, `test_unread_scheme_directives.py` (new, S33); TestTheSchemeOpacityStopsWhereTheHelpSays, `test_80_to_140_directives` and TestMarkColourIsForMarkers flipped; unread-directive silence cases (MK-06..MK-08) in `test_custom_scheme.cscript`; truth S24, S33 |
| P1.5 | P1.5 → S18 (6); P1.5.7 own closed entry | BR-30.5 | `test_axis_format_fallback.py` (new); `test_display_format_sites.py` (narrow writer); `axis_format_truth.json`; `format_truth.json` regenerated; truth S18 |
| P1.6 | P1.6 → S51 (18, two commits) | BR-30.6 | `test_taxis_options.py` (new); `taxis_truth.json`; `test_abbreviations.py`, `test_help_conformance.py`; stale `rejected_options.json` rows; truth S51 |
| P1.7 | P1.7 → S42 (15, two commits) | BR-30.7 | `test_ts_operators.py` (new); `ts_operator_truth.json`; CORPUS cases; refusals in `test_parser.cscript`; `test_help_claims_2.cscript`; truth S42 |
| P1.8 | P1.8a → S40 (14); P1.8b → S45 (16) | BR-30.8 | `test_connect_options.py` (new), `connect_truth.json` (S40); `test_recast.py` (new), `recast_truth.json` (S45); TestRecastKeepsTheSeriesLabel; `test_unsupported_report_is_true.py:95/99` and HC8-02's cmissing/connect/sort flipped (S40), `:137` and HC8-02's recast (S45); pending and declared pins (R10); truth S40, S45 |
| P1.9 | P1.9a → S49 (17); P1.9b → S55 (19) | BR-30.9 | `test_horizontal.py` (new), `horizontal_truth.json` (S49); `test_horizontal_moves.py` (new, S55); saved and served filter-move tests; CORPUS cases; truth S49, S55 |
| P1.10 | P1.10 → S56 (19, two commits) | BR-30.10 | `test_added_text.py` (new); `added_text_truth.json`; new sinks in `test_label_sinks.py`; the `added_text` limit in `test_resource_limits.py`; `test_unsupported_report_is_true.py` pins; `test_help_claims_8.cscript`; truth S56 |
| P1.11 | P1.11a → S09 (3); P1.11b → S29 (10) | BR-30.11 | `test_canvas_tex.py` (new, S09); TestTextSinks' TeX rows in `test_label_sinks.py` flipped; `test_graph_text.py` (new) with hostile-input timing; `graph_text_truth.json`; truth S09, S29 |
| P1.12 | P1.12a → S08 (3, brushed copies included [R27, changed]); P1.12b → S13 (5) | BR-30.12 | `test_size_units.py` (new), `size_units_truth.json` (S08); `test_line_width_units.py` (new), `line_width_truth.json` (S13); empty-option identity tests; CHANGELOG.md:522 corrected; S08's brushed-copy tests (S16 and S32 add theirs); truth S08, S13 |
| P1.13 | P1.13a → S30 (10); P1.13b → S43 (15) | BR-30.13 | `test_colour_grammar.py` (new), `colour_grammar_truth.json` (S30); `test_bare_intensity.py` (new), `bare_intensity_truth.json` (S43); `test_options.py:284-299`, `test_security_surface` and HC2-16p flipped; truth S30, S43 |
| P1.14 | P1.14a → S32 (11); P1.14b → S36 (12) | BR-30.14 | `test_named_styles.py` (new), `named_style_truth.json` (S32); `test_style_names.py` (new), `style_name_truth.json` (S36); empty-plan identity test; `test_ci_band_style.py`; pending and declared pins; truth S32, S36 |
| P1.15 | P1.15a → S28 (10); P1.15b → S48 (17); P1.15c → S53 (18) | BR-30.15 | `test_by_text.py`, `test_by_text_browser.py` (new), `by_text_truth.json` (S28); `test_by_grid.py`, `test_by_grid_browser.py` (new), `by_grid_truth.json` (S48); `test_by_axes_keys.py`, `test_by_axes_keys_browser.py` (new), `by_chrome_truth.json` (S53); refusals in `test_by_suboptions.cscript`; new sinks in `test_label_sinks.py`; `test_server_facets.py`; truth S28, S48, S53 |
| P1.16 | P1.16 → S19 (7, two commits) | BR-30.16 | `test_series_labels.py` (new); `series_label_truth.json`; `test_unlabelled_variables.py`, `test_server_layer_defects.py`; truth S19 |
| P1.17 | P1.17a → S14 (5); P1.17b → S27 (9) | BR-30.17 | `test_bar_range_geometry.py` (new); `bar_geometry_truth.json` (S14); `default_base_truth.json` (S27); `test_glyphs.py`, `test_range_plots.py`, `test_axis_extents.py`, `test_served_filter_move.py`; truth S14, S27 |
| P1.18 | P1.18a → S31 (11); P1.18b → S52 (18) | BR-30.18 | `test_axis_suboptions.py` (new), `axis_subopt_truth.json` (S31); `test_axis_add.py` (new), `axis_add_truth.json` (S52); refusals in `test_suboption_reporting.cscript`; `test_suboption_warnings.py`; the `tlabel(…, add)` cross case; truth S31, S52 |
| P1.19 | P1.19 → S10 (4) | BR-30.19 | `test_subopt_abbrev.py` (new); `subopt_abbrev_truth.json`; `test_textbox_grammar.py`; refusals in `test_suboption_reporting.cscript`; truth S10 |
| P1.20 | P1.20a → S38 (13); P1.20b → S47 (16) | BR-30.20 | `test_region_options.py`, `test_region_truth.py` (new), `region_truth.json` (S38); `test_region_margins.py` (new), `margin_truth.json` (S47); `test_option_validation.py:1089-1094` flipped (`bgcolor()`); an adversarial colour test; `test_twoway_option_parity.cscript`; truth S38, S47 |
| P1.21 | P1.21a → S39 (14); P1.21b → S50 (17) | BR-30.21 | `test_reference_lines.py` (new), `refline_truth.json` (S39); `test_refline_extent.py`, `test_refline_extent_chrome.py` (new), `refline_extent_truth.json` (S50); the `reflines` limit in `test_resource_limits.py`; refusals in `test_suboption_reporting.cscript`; truth S39, S50 |
| P1.22 | P1.22 → S26 (9), by disposition (M12) | BR-30.22 | note tests in `test_function_expr.py`; `function_expr_truth.json` (existing); CORPUS cases; truth S26 |
| P1.23 | P1.23a → S35 (12); P1.23b → S17 (6) | BR-30.23 | `test_date_axis_residuals.py` (new); `date_axis_truth.json` (S35); `test_key_text_chrome.py` (new), `key_text_truth.json` (S17); `test_date_range.py` colour-scale rows and `histogram_gets_the_bin_tooltip` flipped; the headless check under the CSP; truth S35, S17 |
| P1.24 | P1.24 → S37 (13, two commits) | BR-30.24 | `test_mlabvposition.py`, `test_mlabtextstyle.py` (new); `mlabvpos_truth.json`, `mlabtextstyle_truth.json`; the declared-option guard test; `test_unsupported_report_is_true.py`, `test_help_claims_8.py`; truth S37 |
| P1.25 | P1.25a → S07 (3); P1.25b → S34 (12); P1.25.6 own closed entry | BR-30.25 | `test_twenty_six_schemes.py` (new, S07); `test_scheme_lookup.py` (new, S34); `test_scheme_fidelity.py` (`EXPECTED_SCHEMES` 26); `test_scheme_resolution.py`; `scheme_truth.json` and six new scheme files; `scheme_lookup_truth.json` (new); `test_installed_layout.py`; `test_custom_scheme.cscript`; the served per-graph-scheme parity test; truth S07, S34 |
| P1.26 | P1.26a → S06 (2); P1.26b → S23 (8) | BR-30.26 | `test_note_channel.py` (new); NC-01..06 in `test_render_log_clean.cscript`; NC-07..19; `test_served_notes.py` (new), `test_serve_launcher.py`; 29 needles migrated; the own-if CORPUS entries restored; truth S06, S23 |
| P1.27 | P1.27 → S12 (4) | BR-30.27 | `test_command_form.py` (new); SB-31..40 and PV-35..44 in `test_path_validation.cscript`, `test_adversarial.cscript`, `test_serve_browser.cscript`, `test_nodraw_honoured.cscript`; P2-80 and PV-04/05/14 flipped; `twoway_command_form_truth.json`; `saving_chars_truth.json` (S04's); truth S12 |
| P1.28 | P1.28a → S22 (8); P1.28b → S54 (19) | BR-30.28 | `test_export_result.py` (new, S22); `test_export.cscript`; the `r()` leak test; `test_export_svg.py` (new); `_assert_nine_tools` in `test_toolbar.py` flipped; `graph_export_truth.json`; truth S22, S54 |
| P1.29 | P1.29 → S04 (2) | BR-30.29 | `test_csp.py`; `test_csp_browser.py`, `test_saving_chars.py` (new); SB-21..30 and PV-28..34 in `test_path_validation.cscript`; `saving_chars_truth.json` (new); truth S04 |
| P1.30 | P1.30 → S41 (14, two commits) | BR-30.30 | `test_bokeh_window.py`, `test_bokeh_internals.py`, `test_label_sinks_browser.py` (new); `VERIFIED_BOKEH` in `test_label_sinks.py`; `test_version_floor.py`, `test_setup_pep668.py`; HON-50..59 in `test_setup_honesty.cscript`; `test_setup_version_gate.cscript`; the bokeh 3.10 leg; truth S41 |
| P1.31 | P1.31a → S46 (16); P1.31b → S57 (20) | BR-30.31 | `test_served_resources.py` (new, S46) with the RSS and busy-page tests; `test_served_worker.py` (new, S57); `test_serve_options.cscript`; the worker's thread-safety and latency tests; truth S46, S57 |
| P1.32 | P1.32 → S25 (9) | BR-30.32 | `test_dependency_guards.py`; ENV-30..39 in `test_env_guards.cscript`; HON-40..49 in `test_setup_honesty.cscript`; `test_private_files.py` (`dash clear`); truth S25 |
| P1.33 | P1.33 → S05 (2, two commits) | BR-30.33 | `test_floor_matrix.py` (new); `conftest.py` baselines; `test_version_floor.py`, `test_setup_pep668.py`; HON-31..39 in `test_setup_honesty.cscript`; `test_setup_python_gate.cscript`; `test/requirements-dev.txt`, `test/requirements-stata.txt`; the floor-matrix logs; truth S05 |
| P1.34 | P1.34 → S02 (1), under M4 | BR-30.34 | `test_runner_portability.py` (new; the path guard); `test_cert_verdict.py`, `test_release_verdict.py`, `test_measure_stata_coverage.py` flipped; the environment override in `test_help_claims_1.py`/`_8.py`; truth S02 |
| P1.35 | P1.35 → S03 (1), under M2 | BR-30.35 | `test_version_floor.py` (`version 19` pins, the guard order); ENV-24..29 in `test_env_guards.cscript`; the function-points pin; batch 1's `make cert`; truth S03 |

Cross-cutting requirements trace as follows:
- BR-30.36 → E6 and every M5 section above;
- BR-30.37 → E6 and the M6 rows' sections S11, S15, S18, S20, S23, S30, S31, S33, S40, S53;
- BR-30.38 → E4 and every drawing section;
- BR-30.39 → E10 and S58.4;
- BR-30.40 → E1, E11 and S01, S58.
