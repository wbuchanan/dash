# Traceability Matrix

Bidirectional check: every audited defect traces to a task, and every task traces to an
audited defect. Findings come from eight parallel code audits plus direct empirical probing
against live StataNow 19.5; **[measured]** marks a finding reproduced by running the software.

## Summary

| | Count |
|---|---|
| Distinct defect classes identified | **118** |
| Covered by a task | **118** |
| Gaps at first validation pass | 6 |
| Gaps remaining | **0** |
| Tasks with no traceable finding | **3** (all approved — see §3) |
| Findings deliberately excluded | **4** (see §4) |
| Total tasks | 89 across 16 sections |

## 1. Requirement-to-task mapping

### Distribution and environment

| # | Finding | Evidence | Section | Tasks |
|---|---|---|---|---|
| 1 | `net install` produces a package that tracebacks on every command | **[measured]** `dash.pkg` omits `schemes/`; `:5004` fallback raises uncaught | S02 | 02-01..04 |
| 2 | `GlyphMapper.__init__:1142` has the same defect | code | S02 | 02-03 |
| 3 | pytest suite is RED — 14 failures from an unguarded `statsmodels` import `:2547` | **[measured]** | S01 | 01-02, 01-03 |
| 4 | cscript runner prints ALL TESTS PASSED having asserted nothing (`n_skip` never incremented, guards `exit 0`) | code | S01 | 01-04 |
| 5 | `test_adversarial.cscript` and `test_e2e_serve.cscript` are orphans | code | S01 | 01-05 |
| 6 | pytest and Stata use different Python interpreters | **[measured]** | S01 | 01-06 |
| 7 | `dash_setup`/`dash.pkg` declare `statsmodels` a hard dependency; only `lowess` needs it | code | S01 | 01-03 |
| 8 | `dash_setup` never compares the Python version despite `dash_setup.sthlp:34` | code | S16 | 16-02 |

### Rejected `twoway` syntax

| # | Finding | Evidence | Section | Tasks |
|---|---|---|---|---|
| 9 | 37 of 59 probed `twoway` commands abort with `r(198)`; 46 full-name options confirmed rejected | **[measured]** | S05 | 05-01..04 |
| 10 | `dash.sthlp:668-673` — "No error is produced for unknown options" — is false by construction | `dash.ado:293-326` closed allow-list, no `capture`, no catch-all | S05 | 05-02, 05-03, 05-06 |
| 11 | ~25 standard abbreviations hard-fail (`mlab` `msym` `xlab` `mcol` `lcol` …) | **[measured]** | S04 | 04-01..04 |
| 12 | 5 abbreviations **mis-mapped** to a different option (`mlc`→mlabcolor, `mlw`→mlabwidth, `mls`, `mlp`, `mlg`) | `dash_parse.mata:186-189` | S04 | 04-02, 04-03 |
| 13 | `dash.sthlp` documents 5 spellings that do not work + the `xla`/`xlab` contradiction | `:537`, `:538`, `:540`, `:543`, `:637` vs `:639` | S04 | 04-05 |
| 14 | KPI `nam()` / `upd()` documented, rejected | `dash.ado:1065`, `:1070` | S04 | 04-03 |
| 15 | ~12 plot-type abbreviations rejected (`scat` `conn` `lin` `kdens`) | `dash_parse.mata:126-167` | S04 | 04-04 |
| 16 | `contour`, `contourline`, `pccapsym`, `rbarm` not accepted | code | S05 | 05-01 |
| 17 | `play()` / `nodraw` documented as warn-and-ignore, actually `r(198)` | **[measured]** — neither string exists in the source | S05 | 05-03, 05-06 |
| 18 | 8 options accepted but sub-options discarded (`title(,size())`, `legend(order())`, `xlabel(#10)`, `xlabel(minmax)`, `ylabel(,format())`, `yscale(range())`, `graphregion(margin())`, numlist form) | **[measured]** | S09 | 09-01..04 |

### Silently discarded work

| # | Finding | Evidence | Section | Tasks |
|---|---|---|---|---|
| 19 | `scatter y1 y2 x` renders **one** series; `twoway` renders two | **[measured]** 1 colour vs 2 | S06 | 06-01, 06-02 |
| 20 | `layout(bs)` + `by()` **deletes the faceted graph entirely** | **[measured]** title and facet labels absent | S12 | 12-01, 12-02 |
| 21 | `dash function y=x^2` → `r(101)`; `:455` lacks `equalok` | **[measured]** | S06 | 06-03 |
| 22 | Variable-free plots (`scatteri`, `pci`, `function`) abort standalone | `:937-940` | S06 | 06-03 |
| 23 | `tsline` with no `tsset` → `r(7102)`; `_dta[_TStvar]` never read | **[measured]** | S06 | 06-03 |
| 24 | `name(id, replace)` impossible — validated before parsed | `:857-883` | S06 | 06-03 |
| 25 | `saving(myfig)`, `saving(f.gph)`, `saving(f.html, replace)` all `r(198)` | `:921` vs `:929`, `:158-161` | S06 | 06-04 |
| 26 | Path validator rejects `(` and `)` — breaks `Program Files (x86)` | `:150-178` | S06 | 06-04 |
| 27 | `scatteri` label text mis-paired → malformed JSON | `:710-727` | S06 | 06-05 |
| 28 | Per-plot `if` broken both ways — only layer 1 promoted, renderer never reads per-plot | `:828-835`, `dash_render.py:5281` | S06 | 06-06 |
| 29 | 9 options accepted and never read (`falpha` `pstyle` `recast` `cmissing` `connect` `mlcolor` `mlabwidth` `coloruseplegend` graph-level `scheme`) | grep | S05, S09, S11 | 05-05, 09-05, 11-02 |
| 30 | `link(_all)` silently unlinked in the production path | `render():7510-7512` (the three `_all` expansions are dead code + the server path) | S13 | 13-02 |
| 31 | `layout(name:row,col)` documented, validated, never implemented | `:6788-6800` | S12 | 12-03 |
| 32 | `tabs()` silently discarded unless `layout(bs)` | `:7372` | S12 | 12-03 |
| 33 | Tab labels force-`.title()`-cased | `:6692` | S12 | 12-03 |
| 34 | `_NONSELECTION_ALPHA` never ships — applied only in uncalled `_build_figures` | `:109`, `:7037` | S12 | 12-04, 12-05 |
| 35 | `_setup_sources` / `_build_figures` are dead, diverged duplicates | `:6824`, `:6955`, `:6970` | S12 | 12-04 |
| 36 | `filter()` + `by()` masks the wrong rows in faceted panels | `:4453-4471` vs `:7649-7654`, `:7616-7617` | S13 | 13-01, 13-03 |
| 37 | `dash kpi … if …` shows the unconditional statistic | **[measured]** 21.2973 vs Stata's 24.7727 | S13 | 13-04 |
| 38 | `p25`/`p75` KPIs display 0 after the first filter | `:4504-4528` | S13 | 13-04 |
| 39 | KPI precision changes on first filter (`fmt=""` vs `"%9.0f"`) | `:7118-7133` vs `:7277` | S13 | 13-04 |
| 40 | `dcount` always missing — `codebook` returns nothing in `r()` | `dash.ado:1110-1113` | S13 | 13-04 |
| 41 | `update(brush)` dead in **both** paths; `dash.sthlp:424` claims "Yes / Yes" | `:5030`, `:10232` | S13, S14 | 13-04, 15-04 |
| 42 | `filter(x, label())` read at `:7189`, never set | code | S13 | 13-05 |
| 43 | Unicode variable names silently dropped by `filter()` | `dash.ado:1351` | S13 | 13-05 |
| 44 | `dash clear` drops `_dash_*` not `dash_*` — orphan globals survive | `:1024-1053` | S13 | 13-05 |
| 45 | `if !missing()`, `inlist()`, `< .` fail the AST whitelist → render **unfiltered** | `:4318-4353` | S09 | 09-06 |
| 46 | `hover()` read at `:6063`, `:4940`; absent from `dash.ado` | grep | S09 | 09-07 |
| 47 | Dashboard title/subtitle **double HTML-escaped** in the Bootstrap path | `:7518-7519` vs `:6551`, `:6555` | S09 | 09-07 |
| 48 | Graph/axis titles escaped but drawn as **canvas text** | `:5638`, `:5610-5611` | S09 | 09-07 |
| 49 | Secondary-axis range from the **unfiltered** frame | `:5729`, `:5764` | S09 | 09-07 |
| 50 | `mlabel()` on `line` uses the **unsorted** source | `:2014`, `:2030` | S09 | 09-07 |
| 51 | Title/note sub-options leak into rendered text | Stata-side parse, `string` vs `string asis` | S09 | 09-03 |
| 52 | `note()`/`caption()` overlap; subtitle collides with title | `:5866-5867`, `:5878-5879` | S09 | 09-03 |
| 53 | `legend(off)` needs exact string equality | `:6008` | S09 | 09-04 |
| 54 | Every glyph passes `legend_label=yvar` — single-series plots get a legend `twoway` would not draw | code | S09 | 09-04 |
| 55 | Hollow markers render filled; `msymbol(i)`/`none` draws visible markers | code | S09 | 09-05 |
| 56 | `filterposition(left)` only effective in Bootstrap mode | `:7387`, `:6603`, `:7456-7458` | S12 | 12-03 |
| 57 | Log pollution — `python:` echoes `run_path`'s globals dict, ~10 KB per render | **[measured]** `dash.ado:143` | S14 | 14-04 |
| 58 | `dash build` has no `nobrowser`; no `_rc` check after six `shell` calls | `:1012-1014`, `:1475-1477`, `:1488` | S14 | 14-04 |

### Hardcoded values — statistical

| # | Finding | Evidence | Section | Tasks |
|---|---|---|---|---|
| 59 | Histogram fixed at 10 bins | **[measured]** Stata: 8 (auto/mpg), 33 (nlsw88/wage) | S07 | 07-01, 07-02, 07-03 |
| 60 | Histogram y-axis is raw counts; Stata's default is density; `percent`/`frequency`/`fraction` unreachable | `:3003` | S07 | 07-03 |
| 61 | CI level fixed at 95% in **four** places; `c(level)` never read; no `level()` | `:1343-1344`, `:2441`, `:8101`, `:8123` | S07 | 07-04 |
| 62 | Kernel fixed Gaussian; Stata's default is epanechnikov | `:3066`, `:2611` | S07 | 07-05 |
| 63 | `map_kdensity` ignores `bwidth()` although it is reachable | `:3068` | S07 | 07-05 |
| 64 | Filter-JS KDE uses Silverman, initial render uses Scott's — the curve jumps on an inert filter | `:4617` vs `:3068` | S07 | 07-05 |
| 65 | `lpoly bwidth()` treated as a fraction of x-range, not an absolute bandwidth | `:2667`, `:2604` | S07 | 07-05 |
| 66 | `_compute_lpoly_fit` `bwidth=0.5` fixed where Stata derives from data | `:2582` | S07 | 07-05 |
| 67 | `map_lowess` unguarded `float()` crashes the render on a non-numeric `bwidth` | `:2560` | S07 | 07-05 |
| 68 | `function` always over x ∈ [0,1]; `range()` unreachable; dead read | `:5951`, `:4121`, `:5953` | S07 | 07-06 |
| 69 | `function` grid 200; Stata's default is 300; `n()` unreachable | `:5952`, `:5960` | S07 | 07-06 |
| 70 | `x^2` parses as `BitXor` → silent empty line | `:4175-4181`, `:4241-4243` | S07 | 07-06 |
| 71 | `fpfit` truncated to 1st-99th percentile; 200 vs 150 points vs `fpfitci` | `:2880-2883`, `:2941-2944` | S07 | 07-06 |
| 72 | `fpfit`/`fpfitci` ignore `bwidth`/`degree`, contradicting `dash.sthlp:559-560` | `:2843`, `:2898` | S07 | 07-06 |
| 73 | `mband` invents equal-width bands; `bands()` absent | `:4085` | S07 | 07-06 |
| 74 | `n_boot` 200 vs 500 with contradicting docstrings; `seed=42` fixed | `:1303`, `:2513`, `:1304` | S07 | 07-06 |

### Hardcoded values — visual and geometric

| # | Finding | Evidence | Section | Tasks |
|---|---|---|---|---|
| 75 | 63 of 108 parsed scheme keys discarded; only 3 consumers exist | `:918-974` | S11 | 11-03, 11-04 |
| 76 | `default_symbol()` / `default_line_pattern()` have **zero call sites** | `:996`, `:1000` | S11 | 11-03 |
| 77 | Marker fixed `"circle"`; size fixed 8 (while `:3586` uses `medium`) | `:1936`, `:1971` | S11 | 11-03 |
| 78 | Line width literals 1.5/2.0 across 9 sites; dash always solid | `:2023`, `:2330` | S11 | 11-03 |
| 79 | `fill_alpha`/`bar_alpha`/`area_alpha` parsed, unread | `:1974`, `:2199`, `:2106` | S11 | 11-04 |
| 80 | `css_block()` selectors match **nothing** — 4 scheme values inert | `:1026-1035` vs `:6551`, `:6555`, `:6292-6300` | S11 | 11-04 |
| 81 | `colorvar` palettes ignore the scheme; colorbar fixed `"right"` | `:1727-1730`, `:1780-1781`, `:1769`, `:1797` | S11 | 11-04 |
| 82 | `legend_bg_color` / `legend_border_color` / `minor_grid_color` / `note_font_size` have zero consumers | `:923-924`, `:6004-6005` | S11 | 11-04 |
| 83 | `c(scheme)` never read — `set scheme` ignored | `dash.ado`, 11 `c(` hits, two idioms | S11 | 11-02 |
| 84 | `scheme()` on `dash build` → `r(198)` though documented | `:1174-1185` vs `dash.sthlp:79` | S11 | 11-02 |
| 85 | Graph-level `scheme()` serialized and never read | `:514` vs `:4990-5000` | S11 | 11-02 |
| 86 | `theme(dark)` documented, absent from the map → silent `s2color` | `dash.sthlp:248` vs `:4983-4989` | S11 | 11-02, 11-05 |
| 87 | `stcolor` — the Stata 18+ default — renders **every series black**; `dash` has no stcolor | `_color():863`, default `:934` | S03, S11 | 03-01..03, 11-01 |
| 88 | Translations cover 1.6% of a real Stata scheme; 75 of 108 keys are invented | measured against `scheme-s2color.scheme` (2,588 lines) | S03 | 03-01..04 |
| 89 | `p#stub → pstub → p# → p` resolution only partially implemented | code | S03, S11 | 03-03, 11-03 |
| 90 | Custom scheme by CWD base name documented, impossible | `dash.sthlp:708-713` vs `:747-760` | S11 | 11-05 |
| 91 | **No figure width/height/ratio anywhere**; `xsize()`/`ysize()` rejected; `graphsize` unparsed | **[measured]** `:5643-5650` | S10 | 10-01, 10-02 |
| 92 | Grid and Bootstrap thresholds fixed (`ceil(sqrt(n))`, 4 KPIs/row, 1/2-4/≥5 spans) | `:6767-6800`, `:6319-6364` | S10 | 10-03 |
| 93 | `md`-only breakpoint; cell height independent of span | `:6567-6571` | S10 | 10-03 |
| 94 | `fcolor(none)` paints an **opaque white blob** | `:386-387` | S09 | 09-05 |
| 95 | `mlabgap(small)` throws and is silently dropped | `:1893-1899` | S09 | 09-05 |
| 96 | `colormissing` defaults to literal `"grey"`, never translated → invalid CSS | `:1591` | S09 | 09-05 |
| 97 | `xline`/`yline` forced grey dashed; style sub-options discarded | `:5834-5853` | S09 | 09-05 |
| 98 | `mlcolor` unimplemented; marker border hijacks `lcolor` | `:1441-1449` | S09 | 09-05 |
| 99 | `base()` ignored by `dropline`; `barwidth()` ignored by `rbar`; markers ignored by `dropline`; cap width fixed 0.2 | `:3415`, `:3161`, `:3440`, `:3246`, `:3486` | S09 | 09-05 |
| 100 | Hover uses raw variable names, not labels; three hardcoded precisions | `:6078-6089`, `:6127-6131` | S08 | 08-05 |
| 101 | Slider step `(max-min)/100` ignores integrality | `:4809`, `:4862` | S13 | 13-05 |

### Formats and dates

| # | Finding | Evidence | Section | Tasks |
|---|---|---|---|---|
| 102 | **No date handling anywhere** — no `DatetimeAxis`, no `%td`, `map_tsline` is a pass-through | grep | S08 | 08-01..06 |
| 103 | `jsonio` has **no option** that emits display formats; `metaprint()` is a no-op | `jsonio.ado:238` gating bug; `javap` on the jar | S08 | 08-02 |
| 104 | `_load_data` never reads formats; `%9.0fc` lost everywhere | `:5061-5083` | S08 | 08-03, 08-04, 08-05 |
| 105 | Three master-JSON assemblies hardcode `theme`/`layout`/`filterposition` | `dash.ado:974`, `:1433`, `:1603` | S11, S14 | 11-02, 14-03 |

### Server mode

| # | Finding | Evidence | Section | Tasks |
|---|---|---|---|---|
| 106 | `bokeh serve` serves an **empty document**; `/health` 404 | **[measured]** `:10305-10313`, no `curdoc()` | S14 | 14-01, 14-02 |
| 107 | `dash serve` can never create a filter widget; every option hardcoded | `dash.ado:1487`, `:1603` | S14 | 14-03 |
| 108 | `dash build, server` **blocks Stata forever** and opens a browser | `dash.ado:142`, `:10408-10455` | S14 | 14-04 |
| 109 | `args.port` never forwarded — every app embeds 5006 | **[measured]** `:10356` | S14 | 14-04 |
| 110 | `allow_websocket_origin` fixed to `localhost:<port>` | `:10310`, `:10422` | S14 | 14-04 |
| 111 | `X-Forwarded-For` trusted unconditionally — rate limiter bypassable | `:7975-7979` | S14 | 14-05 |
| 112 | Temp `.py` containing the **base64 dataset** leaks permanently | `dash.ado:1633-1634` | S14 | 14-05 |
| 113 | Server-mode `saving()` bypasses the path validator | `dash.ado:1198-1207` | S14 | 14-05 |
| 114 | `scipy`/`statsmodels` at module scope of the generated app; missing statsmodels silently fakes a lowess curve | `:7882`, `:8147-8148` | S14 | 14-05 |
| 115 | `/health` uses deprecated `datetime.utcnow()` | **[measured]** `:7995` | S14 | 14-02 |
| 116 | **107 implementations for 38 behaviours**; drift already user-visible | counted | S15 | 15-01..04 |
| 117 | Server ignores the scheme entirely — every series `#1f77b4` | `:8678`, `:9680`, `:9778`; zero `scheme` hits >7738 | S15 | 15-03 |

### Documentation and tests

| # | Finding | Evidence | Section | Tasks |
|---|---|---|---|---|
| 118 | 17 documented-not-accepted, 14 documented-not-implemented, 16 implemented-not-documented, 19 wrong values, 180+ silent-failure sites of which 10 warn; landmine tests (no-assertion, tautological, both-ways-accepting, gap-concealing); zero regression coverage for dates, sizing, scheme consumption, the style cycle, mode parity and `tabs()` | audit | S16, S01, S11, S13 | 16-01..03, 01-05, 11-01, 13-06 |

## 2. Gap resolution log

| # | Gap | Resolution | Date |
|---|---|---|---|
| 1 | Double HTML-escaping in the Bootstrap path had no owner | Added to S09-07 | 2026-09-18 |
| 2 | Canvas-text escaping had no owner | Added to S09-07 | 2026-09-18 |
| 3 | Phantom `hover()` option had no owner | Added to S09-07 | 2026-09-18 |
| 4 | Secondary-axis range from unfiltered frame had no owner | Added to S09-07 | 2026-09-18 |
| 5 | `mlabel()` on `line` plots had no owner | Added to S09-07 | 2026-09-18 |
| 6 | `dash build` missing `nobrowser` had no owner | Added to S14-04 | 2026-09-18 |

## 3. Tasks beyond the finding set (approved)

| Task | What it adds | Why kept |
|---|---|---|
| 12-02 (second half) | A general guard asserting every registered graph appears in the assembled layout | Finding 20 is one instance of a class. The guard catches the rest, and cost almost nothing. |
| 11-04 (last part) | A test asserting every selector `css_block()` emits matches a class the HTML uses | Finding 80 recurred because nothing checked. A mechanical check stops it recurring. |
| 16-01 | A whole-file help-conformance test | Finding 118 is 66 divergences. Correcting them by hand without a mechanical check reproduces the problem within a release. |

Each is a **mechanism** that prevents a whole class of finding from returning, rather than a
new feature. All three were retained deliberately.

## 4. Findings deliberately excluded

| Finding | Why |
|---|---|
| `jsonio`'s `metaprint()` gating bug (`jsonio.ado:238`) | Real, and upstream. The decision is that `jsonio` is not modified; S08 works around it. Worth reporting to its maintainer separately. |
| Bokeh's own `CodeRunner` module-name behaviour | Not a `dash` defect; S14 adapts to it. |
| The broken local `statsmodels` install (missing `packaging`) | An environment problem, not a code defect. S01 fixes the **guard**, not the install. |
| `%tC` leap-second handling | Treated as `%tc` **and documented as such** (S08). Full leap-second correction is disproportionate; the requirement is that it not be silent. |

## 5. Validation result

**118 of 118 defect classes are covered. Zero gaps. Three tasks beyond the finding set, all
approved as recurrence-prevention mechanisms.**
