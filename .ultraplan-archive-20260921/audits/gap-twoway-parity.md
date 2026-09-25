# `dash` vs. `twoway` — parity gap audit

Audit target: `/Users/billy/Desktop/Programs/StataPrograms/d/dash`
Files read in full or in relevant part: `dash.ado` (1649 ln), `dash_parse.mata` (1033 ln),
`dash_render.py` (10455 ln), `dash.sthlp` (744 ln).

**Every `rc=` value in this document was produced empirically** by running StataNow 19.5
against the package source (probe do-files in this scratchpad: `probe6.do`, `probe8.do`,
`probe9.do`, `probe10.do`, `probe13.do`–`probe19.do`). Claims not verified by execution are
marked `[code-read]`. Claims about Stata's own semantics that I could not verify by running
`twoway` are marked `[stata-semantics-uncertain]`.

---

## 0. Executive summary

| Metric | Count |
|---|---|
| twoway plot types **not accepted** (r(198) abort) | 4 confirmed (`contour`, `contourline`, `pccapsym`, `rbarm`) + the `twoway` prefix word itself |
| twoway plot types **accepted but broken/crash** | 3 (`tsline`/`tsrline` w/o tsset, `function` with `y=` prefix, standalone `scatteri`/`pci`/`pcscatter`) |
| Plot-type abbreviations Stata accepts that dash rejects | ≥ 12 (`sca`,`scat`,`scatt`,`scatte`,`lin`,`conn`,`connec`,`are`,`spi`,`histo`,`kdens`,`msplin`, …) |
| twoway options **rejected** by `syntax` → r(198) BLOCKER | **46 distinct full-name options confirmed by execution** (Table 2), plus 9 abbreviations (§2g) |
| Option-key abbreviations Stata accepts that dash rejects | ≥ 9 confirmed (`xlab`,`ylab`,`mlab`,`msym`,`lcol`,`lwid`,`titl`,`xtit`,`c()`) — structurally unbounded |
| Options accepted by `syntax` but **never read** by the renderer (pure no-ops) | **9** (Table 3) |
| Renderer code that reads keys `dash.ado` can never emit (dead code) | **9** (`bin`, `n`, `range`, `width`, `color`, `xrange`, `yrange`, `hover`, graph-level `scheme`) |
| Accepted + read but **semantically divergent** | **30 of the 35 cases checked** (Table 4) |

### The single most damaging structural facts

1. **`_dash_parse_plot_opts` (`dash.ado:293-326`) and `_dash_parse_graph_opts`
   (`dash.ado:230-246`) are closed allow-lists.** Stata's `syntax` aborts with r(198)
   on *any* option not in the list. There is no `capture`, no catch-all
   (`dash.ado:666-669` calls the parser bare). So every unlisted twoway option is a
   do-file-aborting BLOCKER, not a degradation.
2. **`dash.sthlp:668-671` states the opposite and is false**: *"No error is produced for
   unknown options, so existing Stata graph commands copy-pasted into `dash` will still
   run even when they contain options that have no Bokeh equivalent."* This is the
   central documented claim of drop-in compatibility and it is wrong. `dash.sthlp:719`
   even documents `nodraw` as "silently ignored"; it is in fact r(198).
3. **Every option key in dash's allow-list is all-lowercase**, so Stata's `syntax`
   permits **no abbreviation at all**. Abbreviation support is faked by a
   hard-coded 60-entry lookup table in Mata (`dash_parse.mata:179-247`) that recognises
   exactly *one* short form per option. Stata accepts every prefix down to the documented
   minimum (`xlab`, `xlabe`, `xlabel` …); dash accepts `xla` and `xlabel` **only**.
   `xlab(1 2 3)` → `option xlab() not allowed` r(198). This affects every option and is
   the largest single source of BLOCKERs by surface area.
4. **`name()` has completely different semantics.** In twoway, `name(fig1)` names the
   in-memory graph *and draws it*. In dash (`dash.ado:838-845`) `name()` suppresses all
   output and registers the graph for a later `dash build`. A user who copies
   `twoway scatter y x, name(fig1)` gets `dash: graph 'fig1' registered.` and **no
   dashboard at all**.
5. **`name(g1, replace)` — the form dash's own help and error message tell users to
   type — is impossible.** `dash.ado:857` validates the raw name against
   `^[a-zA-Z_][a-zA-Z0-9_]{0,31}$` *before* the replace sub-option is parsed at
   `dash.ado:864-870`. Verified: `dash scatter mpg weight, name(p5, replace)` →
   `dash: invalid graph name 'p5, replace'.` r(198). The error text at
   `dash.ado:880-883` recommends the exact syntax that cannot work.

---

## TABLE 1 — twoway plot types

Source of truth for acceptance: `_expand_plottype_str`, `dash_parse.mata:126-165`.
`""` return at `dash_parse.mata:165` → `dash.ado:550-558` prints
`dash: unrecognised plot type '<x>'` and `exit(198)`.
Renderer dispatch: `dash_render.py:6169-6207` (`dispatch`/`range_dispatch` maps) plus the
special-case branches at `dash_render.py:5929-5970`.

| # | plottype | Status | Evidence | Impact |
|---|---|---|---|---|
| 1 | `scatter` | yes | `dash_parse.mata:127`; disp `dash_render.py:6170` | — |
| 2 | `line` | yes | `dash_parse.mata:128`; `dash_render.py:6172` | — |
| 3 | `connected` | yes | `dash_parse.mata:129`; `dash_render.py:6174` | — |
| 4 | `area` | yes | `dash_parse.mata:130`; `dash_render.py:6175` | — |
| 5 | `bar` | yes (twoway-bar semantics, see T4-13) | `dash_parse.mata:131`; `map_bar` `dash_render.py:2131+` | — |
| 6 | `spike` | yes | `dash_parse.mata:132`; `dash_render.py:6177` | — |
| 7 | `dropline` | yes | `dash_parse.mata:151`; `dash_render.py:6189` | — |
| 8 | `dot` | yes | `dash_parse.mata:150`; `dash_render.py:6188` | — |
| 9 | `rarea` | yes | `dash_parse.mata:144`; `dash_render.py:6197` | — |
| 10 | `rbar` | yes | `dash_parse.mata:145`; `dash_render.py:6198` | — |
| 11 | `rspike` | yes | `dash_parse.mata:146`; `dash_render.py:6199` | — |
| 12 | `rcap` | yes | `dash_parse.mata:147`; `dash_render.py:6200` | — |
| 13 | `rcapsym` | yes | `dash_parse.mata:152`; `dash_render.py:6203` | — |
| 14 | `rline` | yes | `dash_parse.mata:148`; `dash_render.py:6201` | — |
| 15 | `rconnected` | yes | `dash_parse.mata:149`; `dash_render.py:6202` | — |
| 16 | `rscatter` | yes | `dash_parse.mata:162`; `dash_render.py:6205` | — |
| 17 | `pcspike` | yes | `dash_parse.mata:153`; `dash_render.py:5932-5938` | — |
| 18 | `pcarrow` | yes | `dash_parse.mata:154`; `dash_render.py:5932-5938` | — |
| 19 | `pcbarrow` | yes | `dash_parse.mata:155`; `dash_render.py:5932-5938` | — |
| 20 | **`pccapsym`** | **NOT ACCEPTED** | absent from `dash_parse.mata:126-165`; verified `_dash_expand_plottype("pccapsym")` → `""` | **BLOCKER** — completes the `pc*` family; users who use `pcspike` reach for it. `dash pccapsym y1 x1 y2 x2` → r(198). |
| 21 | `pcscatter` | accepted-but-broken | `dash_parse.mata:157`; parsed as a literal value list (`dash.ado:626-637, 710-727`) **not** as 4 varnames. `twoway pcscatter y1 x1 y2 x2` takes *variables*; dash's `_dash_parse_varpart_any` (`dash.ado:453-459`) accepts arbitrary tokens and `dash.ado:718-726` emits them as numeric literals `[[y,x],…]`, producing invalid JSON for varnames. | **SILENT** |
| 22 | `pci` | accepted-but-broken standalone | `dash_parse.mata:156`. `dash pci 20 3000 30 4000, saving(x.html)` → **r(198) `dash: no variables identified in plot specification.`** (`dash.ado:937-940`). Only works when combined with a var-bearing plot (verified rc=0 for `dash pci … \|\| scatter mpg weight`). | **BLOCKER** |
| 23 | `tsline` | accepted-but-broken | `dash_parse.mata:158`. Falls through to the *standard* varlist branch (`dash.ado:639-650`), so `dash tsline mpg` yields `xvar:""`. Renderer `map_tsline` → `map_line` → `source.data[""]` → **`KeyError: ''` → `RuntimeError: dash_render: failed to build figure '': ''`** (`dash_render.py:7043`) → Stata **r(7102)**. Verified. dash never consults `_dta[_TStvar]`. | **BLOCKER** |
| 24 | `tsrline` | accepted-but-broken | `dash_parse.mata:159`; routed to the 3-variable branch (`dash.ado:606-615`) requiring `min=2 max=3`. `twoway tsrline y1 y2` (2 vars, time implied) → dash produces `xvar:""` → same crash as #23. | **BLOCKER** |
| 25 | `mspline` | yes (but `bands()` rejected — see T2) | `dash_parse.mata:160`; `dash_render.py:6190` | — |
| 26 | `mband` | yes (but `bands()` rejected) | `dash_parse.mata:161`; `dash_render.py:6191` | — |
| 27 | `lfit` | yes | `dash_parse.mata:133`; `dash_render.py:6178` | — |
| 28 | `qfit` | yes | `dash_parse.mata:134`; `dash_render.py:6179` | — |
| 29 | `fpfit` | yes | `dash_parse.mata:140`; `dash_render.py:6184` | — |
| 30 | `lfitci` | accepted; all CI options rejected | `dash_parse.mata:135`; `dash_render.py:6180`. `ciopts()`, `level()`, `fitopts()`, `lineopts()`, `alpattern()`, `acolor()`, `clcolor()`, `n()` all → r(198). | **BLOCKER (options)** |
| 31 | `qfitci` | same as #30 | `dash_parse.mata:136` | **BLOCKER (options)** |
| 32 | `fpfitci` | same as #30 | `dash_parse.mata:141` | **BLOCKER (options)** |
| 33 | `lowess` | yes; `bwidth()` accepted | `dash_parse.mata:137`; `dash_render.py:6182` | — |
| 34 | `lpoly` | yes; `bwidth()`/`degree()` accepted | `dash_parse.mata:138`; `dash_render.py:6183` | — |
| 35 | `lpolyci` | accepted; CI options rejected | `dash_parse.mata:139`; `dash_render.py:6181` | **BLOCKER (options)** |
| 36 | `histogram` | accepted; **all histogram options rejected** | `dash_parse.mata:142`; `dash_render.py:6185`. See #Histogram note below. | **BLOCKER** |
| 37 | `kdensity` | accepted; `bwidth()` accepted, `n()`/`kernel()`/`width()` rejected | `dash_parse.mata:143`; `dash_render.py:6187` | **BLOCKER (options)** |
| 38 | `function` | accepted-but-broken | `dash_parse.mata:163`. Two separate blockers — see #Function note below. | **BLOCKER** |
| 39 | `scatteri` | accepted-but-broken standalone | `dash_parse.mata:164`. See #scatteri note below. | **BLOCKER + SILENT** |
| 40 | **`contour`** | **NOT ACCEPTED** | verified: `dash contour mpg weight price` → `dash: unrecognised plot type 'contour'.` r(198) | **BLOCKER** — a headline twoway plottype since Stata 12. |
| 41 | **`contourline`** | **NOT ACCEPTED** | verified `_dash_expand_plottype("contourline")` → `""` | **BLOCKER** |
| 42 | **`rbarm`** | **NOT ACCEPTED** | verified → `""` | **BLOCKER** |
| 43 | `histogram` as a **standalone command** | not applicable | Stata's `histogram` command (not `twoway histogram`) carries `discrete`, `normal`, `normopts()`, `kdensity`, `kdenopts()`, `addlabels`, `addlabopts()`, `gap()`, `by()`, `freq`, `percent`, `fraction`, `density`, `bin()`, `width()`, `start()`. **Every one of these is r(198) in dash.** | **BLOCKER** |
| 44 | `twoway` prefix form (`dash twoway scatter …`) | NOT ACCEPTED | `_expand_plottype_str("twoway")` → `""` → r(198). Users who write `twoway (scatter …)` and change only the first word get an unrecognised-plottype error. | **BLOCKER** |

### Plot-type abbreviations

`dash_parse.mata:126-165` hard-codes **one or two** short forms per type. Stata accepts
every prefix at or beyond the documented minimum abbreviation. Verified rejections
(`_dash_expand_plottype` → `""`, then r(198)):

| typed | dash | Stata `twoway` accepts? |
|---|---|---|
| `sc` | ✅ `scatter` | ✅ |
| `scat`, `scatt`, `scatte` | ❌ `""` → r(198) | ✅ |
| `li` | ✅ | ✅ |
| `lin` | ❌ | ✅ |
| `con` | ✅ | ✅ |
| `conn`, `connec`, `connect`, `connecte` | ❌ | ✅ |
| `hist` | ✅ | ✅ |
| `kde` | ✅ | ✅ |
| `kdens`, `kdensit` | ❌ | ✅ |
| `dotplot` | ❌ | n/a (separate command) |

Impact: **BLOCKER**, high frequency — `scat` and `conn` are common in real do-files.

### #Histogram note

* `dash histogram mpg, bin(20)` → **`option bin() not allowed` r(198)** (verified).
  `width()`, `start()`, `percent`, `frequency`, `density`, `fraction` — all r(198)
  (verified). So the *entire* `twoway histogram` option set is unreachable.
* The renderer nonetheless reads `options.get("bin", 10)` at `dash_render.py:3001` and
  `("barwidth", "width")` at `dash_render.py:2175-2176` — **dead code**, because neither
  `bin` nor `width` appears in the `syntax` allow-list (`dash.ado:293-326`) nor in the
  JSON serialisation key list (`dash.ado:476-482`).
* Default bin count is hard-coded **10** (`dash_render.py:3001`). Stata's default is a
  data-driven rule (`k = min(sqrt(N), 10*ln(N)/ln(10))`, rounded)
  `[stata-semantics-uncertain]` on the exact rounding, but definitely not a constant.
* Y axis is raw **counts** (`np.histogram` → `counts` at `dash_render.py:3003`, used as
  `top` at `dash_render.py:3012`). `twoway histogram x` defaults to **density**.
  → users get a differently-scaled y axis with no way to change it.

### #Function note

Two independent blockers, both verified:

1. `dash function y=x^2` → **`=exp not allowed` r(101)**. Cause: `dash.ado:455`
   `syntax anything(name=vals) [if] [in]` lacks `equalok`. The `y=` strip at
   `dash.ado:630` can never run. `twoway function y=x^2` is *the* canonical documented
   form. **BLOCKER.**
2. `dash function x^2, saving(x.html)` (the form that does parse) →
   **r(198) `dash: no variables identified in plot specification.`** (`dash.ado:937-940`)
   because `_dash_extract_vars` finds no varnames. **BLOCKER.**
3. `range()` and `n()` → r(198) (verified), yet `dash_render.py:5951-5962` reads
   `popts["range"]` and `popts["n"]` — dead code. Without them the x domain silently
   defaults to `[0, 1]` with 200 points (`dash_render.py:5950-5951`).

### #scatteri note

* `dash scatteri 20 3000 30 4000, saving(x.html)` → **r(198) "no variables identified"**
  (verified). Only works alongside a variable-bearing plot.
* Text labels are silently mis-paired. Verified:
  `dash scatteri 20 3000 "A" 30 4000 "B"` →
  `"values":[[20,3000],["A",30],[4000,"B"]]`. `dash.ado:718-726` blindly walks the token
  list two at a time; `dash.ado:714-717` only checks that the token count is *even*.
  twoway would place two markers with labels "A" and "B"; dash emits three malformed
  coordinate pairs including non-numeric JSON. **SILENT** (renders garbage / can crash).
* An odd token count (e.g. a `(3)` placement suffix, which twoway accepts) →
  `dash: scatteri requires even number of values (y x pairs), got 5.` r(198) (verified).

---

## TABLE 2 — twoway options REJECTED by `syntax` → r(198), aborting the do-file

Allow-lists: plot level `dash.ado:293-326`, graph level `dash.ado:230-246`,
`dash build` `dash.ado:1174-1185`.
**Every row below was executed.** The "Exact failure" column is the literal Stata output.

### 2a. Histogram / density / distribution options

| Option | Exact user-visible failure | Impact |
|---|---|---|
| `bin(#)` | `dash histogram mpg, bin(20)` → `option bin() not allowed` r(198) | BLOCKER |
| `width(#)` | `option width() not allowed` r(198) | BLOCKER |
| `start(#)` | `option start() not allowed` r(198) | BLOCKER |
| `percent` | `option percent not allowed` r(198) | BLOCKER |
| `frequency` | `option frequency not allowed` r(198) | BLOCKER |
| `density` | `option density not allowed` r(198) | BLOCKER |
| `fraction` | `option fraction not allowed` r(198) | BLOCKER |

### 2b. `function` / smoother / fit options

| Option | Exact failure | Impact |
|---|---|---|
| `range(a b)` | `option range() not allowed` r(198) | BLOCKER |
| `n(#)` | `option n() not allowed` r(198) | BLOCKER |
| `bands(#)` (`mspline`, `mband`) | `dash mspline mpg weight, bands(20)` → `option bands() not allowed` r(198) | BLOCKER |
| `level(#)` (`*ci`) | `option level() not allowed` r(198) | BLOCKER |
| `ciopts(…)` | `option ciopts() not allowed` r(198) | BLOCKER |
| `lineopts(…)` | `option lineopts() not allowed` r(198) | BLOCKER |
| `fitopts(…)` | `option fitopts() not allowed` r(198) | BLOCKER |
| `acolor()` / `alpattern()` (CI area style) | `option acolor() not allowed` / `option alpattern() not allowed` r(198) | BLOCKER |
| `at(varname)` (`lpoly`) | `option at() not allowed` r(198) | BLOCKER |
| `nograph` | `option nograph not allowed` r(198) | BLOCKER |

### 2c. Bar / area / orientation options

| Option | Exact failure | Impact |
|---|---|---|
| `horizontal` | `dash bar mpg weight, horizontal` → `option horizontal not allowed` r(198) | BLOCKER |
| `vertical` | `option vertical not allowed` r(198) | BLOCKER |
| `sort` | `dash line mpg weight, sort` → `option sort not allowed` r(198) | **BLOCKER, very high frequency** — `twoway line y x, sort` is boilerplate |
| `sort(varname)` | same (`sort` not in list at all) | BLOCKER |
| `ascategory` | `option ascategory not allowed` r(198) | BLOCKER |
| `asyvars` | `option asyvars not allowed` r(198) | BLOCKER |
| `over(varname)` | `option over() not allowed` r(198) | BLOCKER |
| `bargap(#)` | `option bargap() not allowed` r(198) | BLOCKER |
| `bcolor()` | `option bcolor() not allowed` r(198) | BLOCKER |
| `bstyle()` | `option bstyle() not allowed` r(198) | BLOCKER |
| `base(#)` | **ACCEPTED** (`dash.ado:303`) — see Table 4 | — |
| `barwidth(#)` | **ACCEPTED** (`dash.ado:302`) | — |

### 2d. Axis tick / label options

| Option | Exact failure | Impact |
|---|---|---|
| `xtick()` / `ytick()` | `option xtick() not allowed` / `option ytick() not allowed` r(198) | BLOCKER |
| `xmtick()` / `ymtick()` | `option xmtick() not allowed` / `option ymtick() not allowed` r(198) | BLOCKER |
| `xmlabel()` / `ymlabel()` | `option xmlabel() not allowed` / `option ymlabel() not allowed` r(198) | BLOCKER |
| `xlabel()`/`ylabel()` themselves | accepted — but every non-trivial value is silently dropped (Table 4) | SILENT |

### 2e. Graph-region / canvas options

| Option | Exact failure | Impact |
|---|---|---|
| `ysize(#)` | `option ysize() not allowed` r(198) | BLOCKER |
| `xsize(#)` | `option xsize() not allowed` r(198) | BLOCKER |
| `aspect(#)` | `option aspect() not allowed` r(198) — dash only takes `aspectratio()` (`dash.ado:239`) | BLOCKER |
| `text(y x "…")` | `option text() not allowed` r(198) | BLOCKER |
| `nodraw` | `option nodraw not allowed` r(198) — **contradicts `dash.sthlp:719-721`** | BLOCKER + doc bug |
| `play(recordingname)` | `option play() not allowed` r(198) | BLOCKER |
| `graphregion(margin(zero))` | accepted (only the *value* is dropped) | SILENT |
| `plotregion(margin(zero))` | accepted (value dropped) | SILENT |

### 2f. Marker / line style options

| Option | Exact failure | Impact |
|---|---|---|
| `mlwidth()` | `option mlwidth() not allowed` r(198). **Note**: `mlw()` *is* accepted but Mata maps it to the nonexistent `mlabwidth` (`dash_parse.mata:190`), a documented no-op. | BLOCKER + wrong mapping |
| `mlalign()` | `option mlalign() not allowed` r(198) | BLOCKER |
| `mlstyle()` | `option mlstyle() not allowed` r(198) | BLOCKER |
| `mstyle()` | `option mstyle() not allowed` r(198) | BLOCKER |
| `lstyle()` | `option lstyle() not allowed` r(198) | BLOCKER |
| `mlabangle()` | `option mlabangle() not allowed` r(198) | BLOCKER |
| `mlabvposition()` | `option mlabvposition() not allowed` r(198) | BLOCKER |
| `mlabtextstyle()` / `mlabstyle()` | not in list → r(198) `[code-read]` | BLOCKER |
| `clcolor()` / `clwidth()` / `clpattern()` (connected-line style) | `option clcolor() not allowed` etc. r(198) | BLOCKER |
| `c(…)` (min. abbrev of `connect()`) | `option c() not allowed` r(198) — `c` is absent from `_expand_optkey` | BLOCKER |
| `color()` | `option color() not allowed` r(198). **Renderer reads `options["color"]` at `dash_render.py:2109, 2204, 3015, 3432, 3499`** — dead code. `[stata-semantics-uncertain]`: I could not confirm whether plain `color()` is legal on all twoway plottypes, but the renderer clearly expects it. | BLOCKER + dead code |
| `mcolor()`, `msymbol()`, `msize()`, `mfcolor()`, `mlcolor()`, `lcolor()`, `lwidth()`, `lpattern()`, `lalpha()`, `fcolor()`, `fintensity()`, `falpha()` | ACCEPTED (`dash.ado:294-302`) | — |

### 2g. Option **abbreviations** Stata accepts and dash rejects

All verified r(198). This is a class, not a list — `_expand_optkey`
(`dash_parse.mata:179-247`) recognises exactly one short form per option and passes
everything else through unchanged into an all-lowercase `syntax` block that permits no
abbreviation.

| typed | dash result | dash's only accepted short form |
|---|---|---|
| `xlab(1 2 3)` | `option xlab() not allowed` r(198) | `xla` (`dash_parse.mata:212`) |
| `ylab(1 2 3)` | `option ylab() not allowed` r(198) | `yla` (`:213`) |
| `mlab(make)` | `option mlab() not allowed` r(198) | `mla` (`:185`) |
| `msym(Oh)` | `option msym() not allowed` r(198) | `ms` |
| `lcol(red)` | `option lcol() not allowed` r(198) | `lc` (`:202`) |
| `lwid(thick)` | `option lwid() not allowed` r(198) | `lw` (`:203`) |
| `titl(X)` | `option titl() not allowed` r(198) | `ti` (`:208`) |
| `xtit(W)` | `option xtit() not allowed` r(198) | `xti` (`:210`) |
| `c(l)` | `option c() not allowed` r(198) | (none) |

**Impact: BLOCKER, highest aggregate frequency of any finding.**

#### Mis-mapped abbreviations (wrong option silently selected)

| typed | dash maps to | Stata means | Evidence |
|---|---|---|---|
| `mlc(red)` | `mlabcolor` (marker **label** colour) | `mlcolor` (marker **outline** colour) | `dash_parse.mata:186` |
| `mlw(thin)` | `mlabwidth` — not a real Stata option, explicit no-op | `mlwidth` (marker outline width) | `dash_parse.mata:190`; `dash_render.py:1901-1905` |
| `mls(small)` | `mlabsize` | `mlstyle` (marker line style) | `dash_parse.mata:187` |
| `mlp(12)` | `mlabposition` | `mlstyle`-family; Stata's `mlabp()` is the label-position abbrev | `dash_parse.mata:188` |
| `m(oh)` | `marker` (dash-internal alias) | `msymbol` | `dash_parse.mata:193`; alias handled `dash_render.py:1401-1404` — works by accident |
| `fa(50)` | `falpha` | `falpha` — correct, but `falpha` is **never read** (Table 3) | `dash_parse.mata:197` |

Impact: **SILENT** (user's styling silently applied to the wrong property).

### 2h. Options with sub-options: accepted, sub-options ignored or leaked into output

These do **not** abort, but see Table 4 for what they actually do.
`title(, size() color() position() span())`, `caption(, span)`, `subtitle(, position())`,
`legend(order() size() position() ring() region() symxsize() colgap())`,
`xlabel(#N | minmax | none | a(b)c)`, `ylabel(, format() labsize() nogrid grid)`,
`xscale(range() noextend alt)`, `graphregion(margin())`, `plotregion(margin())`.

### 2i. `saving()` and `name()` — twoway forms that abort

| Form | Result | Impact |
|---|---|---|
| `saving(myfig)` (no extension — the normal twoway form) | `dash: saving() path must end in .html (got: myfig)` r(198) (`dash.ado:158-161`, verified via `_dash_validate_path`) | BLOCKER |
| `saving(myfig.gph)` | `dash: saving() path must end in .html (got: myfig.gph)` r(198) (verified) | BLOCKER |
| `saving(myfig.html, replace)` | r(198) — `_dash_validate_path` at `dash.ado:921` runs on the whole string `"myfig.html, replace"` which fails the `\.html$` test (verified). Note: `dash.ado:929-931` would have appended `.html`, but the validator already exited. | BLOCKER |
| `name(g1, replace)` | `dash: invalid graph name 'g1, replace'.` r(198) (verified; also `nam(g1, replace)` and `name(g1 , replace)`). Ordering bug: `dash.ado:857` before `dash.ado:867`. | **BLOCKER + self-contradicting error message at `dash.ado:880-883`** |
| `name(g1)` | rc=0 but **suppresses all rendering** (`dash.ado:840-842`) | **SILENT — user gets no graph** |

### 2j. `dash build` options documented but rejected

| Option | Result | Impact |
|---|---|---|
| `scheme(name)` on `dash build` | `dash build, saving(x.html) scheme(s1color)` → **`option scheme() not allowed` r(198)** (verified). Documented at `dash.sthlp:80`. `dash.ado:1174-1185` has `THEME()` but no `SCHEME()`. Meanwhile `dash_render.py:4993` *prefers* `build_options["scheme"]` over `theme` — a key `dash.ado` can never emit. | **BLOCKER + doc bug + dead code** |

---

## TABLE 3 — Accepted by `syntax`, serialized to JSON, but NEVER read by the renderer

Method: for each key in the plot-option serialisation list (`dash.ado:476-482`) and the
graph-option list (`dash.ado:510-514`), grep `dash_render.py` for any occurrence of the
bare string. Zero occurrences ⇒ pure no-op.

| # | Option | Accepted at | Serialized at | Renderer references | Impact |
|---|---|---|---|---|---|
| 1 | `falpha()` / `fa()` | `dash.ado:301` | `dash.ado:479` | **0** (`grep -c falpha dash_render.py` → 0) | SILENT — fill opacity on `area`/`rarea`/`bar` silently ignored |
| 2 | `pstyle()` | `dash.ado:310` | `dash.ado:482` | **0** | SILENT — whole-plot style silently ignored |
| 3 | `recast()` | `dash.ado:310` | `dash.ado:482` | **0** | SILENT (honestly documented at `dash.sthlp:697-699`) |
| 4 | `cmissing()` | `dash.ado:310` | `dash.ado:482` | **0** | SILENT (documented `dash.sthlp:679-681`) |
| 5 | `connect()` | `dash.ado:311` | `dash.ado:482` | **0** as an option key (only the *plottype* string `"connected"` matches) | SILENT (documented `dash.sthlp:675-677`) |
| 6 | `mlcolor()` | `dash.ado:295` | `dash.ado:476` | **0** | SILENT — marker outline colour ignored. Compounded by the `mlc→mlabcolor` mis-mapping, so *neither* spelling reaches a renderer. |
| 7 | `mlabwidth()` | `dash.ado:297` | `dash.ado:477` | 1 — `options.get("mlabwidth")  # consumed; no-op` at `dash_render.py:1905` | SILENT (explicit, commented) |
| 8 | `coloruseplegend` | `dash.ado:307` | `dash.ado:481` | 1 — `_use_plegend = bool(...)  # noqa: F841` at `dash_render.py:1590`, never used | SILENT |
| 9 | **graph-level `scheme()`** | `dash.ado:239` (graph) and `dash.ado:319` (plot) | `dash.ado:514`; verified in JSON: `"graph_options":{"name":"z1","scheme":"s1mono"}` | `graph_opts.get("scheme")` → **0**. The renderer only reads `build_options["scheme"]`/`["theme"]` at `dash_render.py:4991-4999`. And `dash build` rejects `scheme()` (Table 2j). | **SILENT — `scheme()` is unreachable through every path documented at `dash.sthlp:709-717`** |

### 3b. Inverse dead code — renderer reads keys `dash.ado` can never produce

| Key read | Renderer line | Why unreachable |
|---|---|---|
| `bin` | `dash_render.py:3001` | absent from `dash.ado:293-326` and `:476-482` |
| `n` | `dash_render.py:5959-5962` | idem |
| `range` | `dash_render.py:5951-5957` | idem |
| `width` | `dash_render.py:2175-2176` | idem |
| `color` | `dash_render.py:2109, 2204, 3015, 3432, 3499` | idem |
| `xrange` / `yrange` (graph) | `dash_render.py:5799-5817` | absent from `dash.ado:230-246` |
| `hover` (graph) | `dash_render.py:4940`, `6060+` | absent from `dash.ado:230-246` |
| `by_total` / `by_missing` (graph) | `dash_render.py:5464-5471` | only reachable via the `by()` string sub-option path |
| `scheme` (build) | `dash_render.py:4993` | `dash build` has no `scheme()` (`dash.ado:1174-1185`) |

---

## TABLE 4 — Accepted AND read, but behaviour DIVERGES from twoway

| # | Case | twoway semantics | dash behaviour | Evidence | Impact |
|---|---|---|---|---|---|
| 1 | **Multi-y varlist** `scatter y1 y2 x` | Plots **two** series: y1-vs-x and y2-vs-x | Plots **one**: yvar = first, xvar = **last**; every intermediate variable is silently discarded. Verified: `dash scatter mpg weight length` → `{"yvar":"mpg","xvar":"length"}`; `dash line mpg price weight length` → `{"yvar":"mpg","xvar":"length"}` (2 of 4 vars dropped). | `dash.ado:640-648` (`yvar = word(vl,1)`, `xvar = word(vl,nv)`) | **SILENT — worst data-loss finding.** Affects every plottype in the "standard" branch. |
| 2 | **Per-plot `if`** `(scatter y x if a) (scatter y x if b)` | Each layer filtered independently | Only the **first** layer's `if_expr` is promoted to graph level and then applied to **all** layers. Verified: `dash (scatter mpg weight if foreign==0) (scatter mpg weight if foreign==1), name(w1)` → `graph_options` carries `"if_expr":"foreign==0"`. Per-plot `if_expr` is stored in the JSON but never read — `dash_render.py:5281` reads only `graph_spec["if_expr"]`. | `dash.ado:828-835`; `dash_render.py:5250-5316` | **SILENT — second series renders the wrong subsample (or empty).** |
| 3 | **Per-plot `if` on a later layer only** `(scatter y x) (scatter y x if b)` | Second layer filtered | Promoted `if_expr` is `""` (first layer's), so **no** filter is applied anywhere. Verified: `name(w2)` → `"if_expr":""`. | same | **SILENT — filter vanishes** |
| 4 | **`xlabel()` / `ylabel()` numlist** `xlabel(1990(5)2020)` | Ticks at 1990,1995,…,2020 | `_parse_axis_label_opt` tokenises on whitespace/comma and `float()`s each token. `1990(5)2020` is one bare token → `float()` raises → dropped → **no ticker set at all**. Verified serialisation: `"ylabel":"0(10)40"`. | `dash_render.py:5548-5592` (esp. `:5578-5588`) | **SILENT** |
| 5 | `xlabel(#10)` | ~10 auto ticks | token `#10` → `float()` fails → dropped, no effect | `dash_render.py:5578-5588` | SILENT |
| 6 | `xlabel(minmax)` | ticks at min and max only | dropped, no effect | idem | SILENT |
| 7 | `xlabel(none)` | **suppress** tick labels | dropped → labels still drawn | idem | SILENT (opposite of intent) |
| 8 | `ylabel(, format(%9.0fc))` | formatted tick labels | token `format(%9.0fc)` → `float()` fails → dropped | idem | SILENT |
| 9 | `ylabel(, labsize(small))` / `xlabel(, nogrid)` / `xlabel(, grid)` | label size / grid control | all dropped; no grid control anywhere in the renderer | idem | SILENT |
| 10 | `xlabel(, angle(45))` | rotate labels | **works** — `_parse_axis_angle` at `dash_render.py:216-250`, applied `dash_render.py:5902-5904` | — | — |
| 11 | `xscale(range(0 100))` / `noextend` / `alt` | axis range / extension / side | `_parse_scale_opt` recognises **only** `log` and `reverse` (`raw.lower().split()`), everything else dropped. Verified serialisation: `"yscale":"range(0 50)"`. The renderer *does* have range support but keyed on a `xrange`/`yrange` graph option (`dash_render.py:5799-5817`) that `dash.ado` never emits. | `dash_render.py:203-213`, `:5640-5641` | **SILENT** |
| 12 | `xline(3000, lcolor(red) lpattern(dash))` | styled reference line | Line is drawn, but style sub-options are stripped: `_parse_refline` replaces `,` with space, splits, `float()`s each token and swallows `ValueError`. Every span is hard-coded `line_color="gray", line_dash="dashed"`. Verified serialisation: `"xline":"3000, lcolor(red) lpattern(dash)"`. | `dash_render.py:5834-5852` | COSMETIC/SILENT |
| 13 | `legend(off)` | legend hidden | Requires `legend_opt == "off"` **exactly** (`dash_render.py:6008`). `legend(off ring(0))`, `legend(pos(6) off)`, `legend(order(1 2) off)` fall to the `else` branch and the legend stays visible. Worse, `ring` is a *location* keyword in `loc_map` (`dash_render.py:6013`), so `legend(ring(0) pos(3))` silently relocates the legend to top-right. | `dash_render.py:6004-6055` | **SILENT** |
| 14 | `legend(order(…))` | reorder / select entries | `order()` is never parsed. Only `label(N "text")`, `cols(#)`, `rows(#)` and the bare words on/top/bottom/left/right/ring are read. Verified serialisation: `"legend":"order(2 1) pos(6) ring(0)"`. | `dash_render.py:6027-6055` | SILENT |
| 15 | `legend(position(#))` clock positions, `size()`, `region()`, `symxsize()`, `colgap()` | precise placement/styling | never parsed | idem | SILENT |
| 16 | **Default legend presence** | twoway shows no legend for a single-series plot | Every mapper passes `legend_label=yvar` unconditionally (`dash_render.py:1975, 2024, 2106, 2198, 3014, …`), so a bare `dash scatter mpg weight` renders a legend reading "mpg". Multi-layer graphs over the same y (e.g. `scatter mpg weight \|\| lfit mpg weight`) get two identically-labelled items, which Bokeh merges into one. | `dash_render.py:1975` et al. | COSMETIC/SILENT |
| 17 | `title("A", size(large) color(red))` | title "A", styled | Sub-options are concatenated **into the visible title text**. Verified: `"title":"My Title , size(large) color(red)"`, passed straight to `figure(title=html.escape(...))`. | `dash.ado:230` (`title(string)`); `dash_render.py:5644` | **SILENT — visibly corrupt output** |
| 18 | `title("Line 1" "Line 2")` | two-line title | Collapses to `Line 1 Line 2` on one line (quotes stripped by `string`). Verified. | `dash.ado:230`, `:247` | COSMETIC |
| 19 | `note("n=74", span)` / `caption("c", span)` | note text "n=74" | Quotes are **retained** (declared `string asis` at `dash.ado:232-233`) and sub-options concatenated. Verified: `"note":"\"n=74\", span"` → the rendered annotation literally reads `"n=74", span`. Inconsistent with `title`/`subtitle`, which are `string` and do strip quotes. | `dash.ado:232-233`; `dash_render.py:5859-5870` | **SILENT — visibly corrupt output** |
| 20 | `note()` **and** `caption()` together | note above caption, distinct rows | Both are emitted as `Label(x=0, y=0, x_units="screen", y_units="screen")` added to `"below"` in the same loop, so they **draw on top of each other**. | `dash_render.py:5859-5870` | COSMETIC |
| 21 | `subtitle()` | second title line under the title | Rendered as a screen-space `Label` at (0,0) added `"above"`, not as part of the title block. | `dash_render.py:5872-5882` | COSMETIC |
| 22 | `by(varlist, …)` | full faceting incl. `rows()`, `cols()`, `total`, `missing`, `compact`, `note()`, `legend()`, `ixaxis`/`iyaxis`, `yrescale`/`xrescale`, `holes()` | `_parse_by_raw` recognises **only** `cols(#)`/`col(#)`, `total`, `missing`. All other by-sub-options silently dropped. | `dash_render.py:5320-5352` | SILENT |
| 23 | `jitter(#)` | Stata adds spherical noise sized relative to the **plot region** | dash adds independent **rectangular uniform** noise sized as a % of each axis's **data range**, x and y separately. | `dash_render.py:1044-1074` | COSMETIC. `[stata-semantics-uncertain]` on Stata's exact noise distribution/scale; the *scale reference* (plot region vs data range) definitely differs. |
| 24 | `msymbol(Oh)` / `Sh` / `Dh` / `Th` (hollow) | hollow outline, no fill | Mapped to Bokeh `circle_dot`/`square_dot`/`diamond_dot`/`inverted_triangle` (`dash_render.py:396-405`), which are **filled**; `mcolor` then sets `fill_color` (`dash_render.py:1407-1418`) so hollow markers render solid. Also `Th`→`inverted_triangle` is wrong twice over (hollow *and* inverted). | `dash_render.py:393-427`, `:1419-1423` | SILENT |
| 25 | `msymbol()` case distinction (`O` vs `o`, `S` vs `s`) | large vs medium variants | `translate_msymbol` falls back to `.lower()` (`dash_render.py:594-598` → `_MARKER_MAP.get(v) or _MARKER_MAP.get(v.lower())`), so size distinction is lost | `dash_render.py:580-604` | COSMETIC |
| 26 | `msymbol(i)` / `msymbol(none)` | **invisible** markers (standard idiom on `connected`, `rcap`, `rcapsym`) | Not in `_MARKER_MAP`; `translate_msymbol` raises `ValueError`, caught and `pass`ed at `dash_render.py:1419-1422` → default marker still drawn. | `dash_render.py:393-427`, `:1419-1423` | **SILENT — markers appear that should not** |
| 27 | `msymbol(O D)` / `mcolor(navy red)` (style **lists**) | one style per series | Accepted (rc=0, verified) but treated as a single opaque string → `translate_*` fails → silently ignored | `dash_render.py:1419-1422` | SILENT |
| 28 | `mcolor(red%50)` opacity | 50% opacity | **works** — `parse_color_alpha` / `translate_mcolor` strip and apply `%` (`dash_render.py:1407-1418`, `:585-620`) | — | — |
| 29 | `lpattern()` free-form patterns (`"-."`, `"--..."`, `#`-forms) | arbitrary dash patterns | `_LPATTERN_MAP` (`dash_render.py:463-478`) covers 9 named values + 4 single-char aliases only; anything else silently ignored | `dash_render.py:463-478` | COSMETIC |
| 30 | `in` qualifier | `in 5`, `in -5/l`, `in f/10` | **works** — Stata's `syntax [in]` normalises to `N/M` before dash sees it (verified: `in 5` → `"5/5"`, `in -5/l` → `"70/74"`), and `dash_render.py:5273-5279` matches `^(\d+)/(\d+)$`. | `dash.ado:661-663`; `dash_render.py:5273-5279` | — |
| 31 | `graphregion(margin(zero))` / `plotregion(margin(zero))` | margins | Accepted; only `color()`/`fcolor()`/`lcolor()`/`lwidth()` sub-options are honoured (`dash.sthlp:599-607`). `margin()` silently dropped. | `dash_render.py:5684-5730` | COSMETIC |
| 32 | `bar` plottype | `twoway bar y x` = bars at x, height y | matches (`map_bar`, `dash_render.py:2131+`): `fig.vbar(x=xvar, top=yvar, bottom=base)`. **Not** confused with `graph bar` (which aggregates). Correct. But `horizontal`, `bargap()`, `bcolor()`, `bstyle()`, `over()`, `ascategory`, `asyvars` are all r(198) (Table 2c) — so users reaching for `graph bar`-style syntax get a hard abort rather than the right plot. | `dash_render.py:2131-2215` | — / BLOCKER on options |
| 33 | Range-plot variable **order** `rarea y1 y2 x` | lower, upper, x | **matches**: `dash.ado:606-615` assigns `yvar1=word 1`, `yvar2=word 2`, `xvar=word 3`. Verified: `dash rarea price mpg weight` → `{"yvar1":"price","yvar2":"mpg","xvar":"weight"}`. | `dash.ado:606-615, 692-698` | — |
| 34 | Range plots with 2 variables (`rarea y1 y2` under `tsset`) | time implied | `_dash_parse_varpart_3v` allows `min=2`, so `xvar` ends up `""` → renderer `KeyError` crash path (see Table 1 #24) | `dash.ado:430-436` | BLOCKER |
| 35 | `histogram` default bins / y-scale | data-driven bins, **density** | fixed 10 bins, raw **counts** | `dash_render.py:3001, 3003, 3012` | SILENT |

---

## 5. Cross-cutting defects worth their own line in the plan

| # | Finding | Evidence | Impact |
|---|---|---|---|
| A | `dash.sthlp:668-671` claims unknown options are silently ignored. They are r(198). This is the load-bearing "drop-in replacement" claim and it is false. | `dash.sthlp:668-671` vs `dash.ado:293-326` | **doc BLOCKER** |
| B | `dash.sthlp:719-721` documents `nodraw` as accepted-and-ignored; it is r(198). | verified | doc bug |
| C | `dash.sthlp:80` documents `dash build, scheme()`; it is r(198). | verified | doc bug |
| D | `dash.sthlp:47-52` documents `name(id[, replace])`; every form is r(198). | verified | doc bug |
| E | `name()` semantics silently invert twoway's (register vs draw). No warning is issued. | `dash.ado:838-845` | SILENT |
| F | `_dash_do_render` uses single-line `python: runpy.run_path(...)` (`dash.ado:143`). The single-line form echoes the expression's value, so **every render dumps the entire Python `globals()` dict** (tens of KB) into the Stata Results window / log. Reproduced in `probe12.log`. | `dash.ado:141-143` | COSMETIC but very noisy; also leaks environment detail into logs |
| G | Every renderer failure surfaces as raw Python traceback + Stata r(7102) rather than a `dash:`-prefixed diagnostic. e.g. `dash tsline mpg` → `KeyError: ''` / `RuntimeError: dash_render: failed to build figure '': ''`. | `dash_render.py:7043, 7698` | BLOCKER UX |
| H | The plot-level `syntax` block (`dash.ado:293-326`) duplicates the graph-level block, so plot-level options and graph-level options are indistinguishable. `dash (scatter y x, title(A)) (line y x, title(B))` silently keeps whichever segment writes last (`dash.ado:673-682` `c_local` overwrite). twoway rejects graph options inside a plot paren. | `dash.ado:673-682` | SILENT |

---

## 6. Recommended remediation ordering (drives the implementation plan)

1. **Replace the closed allow-lists with a tolerant parser.** Add a trailing
   `*` / catch-all to `_dash_parse_plot_opts` and `_dash_parse_graph_opts`, or pre-filter
   unknown keys in `_dash_expand_opts_str` and emit a single `dash: ignoring unsupported
   twoway option …` note. This alone converts ~46 BLOCKERs into documented no-ops and
   makes `dash.sthlp:668-671` true. Highest leverage by far.
2. **Replace the hard-coded abbreviation table** (`dash_parse.mata:179-247`) with real
   minimum-abbreviation matching (capitalise the minimum prefix in the `syntax` blocks and
   drop the Mata pre-expansion, or implement prefix matching against the full option list).
   Fixes the entire class in §2g and removes the four mis-mappings.
3. **Multi-y varlist** (`dash.ado:640-648`): emit one plot segment per y variable.
4. **Per-plot `if`/`in`** (`dash.ado:828-835`, `dash_render.py:5281`): consume per-plot
   qualifiers in the renderer instead of promoting only the first.
5. **`name(g1, replace)`**: move the replace parse (`dash.ado:864-870`) before the name
   validation (`dash.ado:857`), and split the name from its sub-options first.
6. **`saving()`**: accept extensionless and `.gph` paths and `, replace`; append `.html`
   before validating (`dash.ado:920-931`, `:158-161`).
7. **`tsline`/`tsrline`/2-var range plots**: read `_dta[_TStvar]` and error cleanly when
   unset instead of crashing with `KeyError: ''`.
8. **`function`**: add `equalok` to `dash.ado:455`; exempt variable-free plot types from
   the "no variables identified" check at `dash.ado:937-940`; wire up the already-present
   `range`/`n` renderer support.
9. **`scatteri`/`pci`**: same variable-free exemption; parse quoted label tokens instead
   of pairing blindly (`dash.ado:710-727`).
10. **Axis-label/scale parsing**: implement Stata numlist (`a(b)c`), `#N`, `minmax`,
    `none`, and the `format()`/`labsize()`/`grid` sub-options
    (`dash_render.py:5548-5592`, `:203-213`); wire `xscale(range())` to the already-present
    `xrange`/`yrange` code at `dash_render.py:5799-5817`.
11. **`legend()`**: tokenise properly — `off` anywhere, `order()`, `position(#)`,
    `ring()`, `size()` (`dash_render.py:6004-6055`); suppress the auto-legend for
    single-series graphs.
12. **`title()`/`note()`/`caption()`**: parse sub-options out of the value instead of
    printing them; separate the note/caption Labels (`dash_render.py:5859-5870`).
13. **Histogram**: accept `bin()`/`width()`/`start()`/`percent`/`frequency`/`density`/
    `fraction`; adopt Stata's default bin rule; default y to density.
14. **`scheme()`**: either read `graph_options["scheme"]` per graph
    (`dash_render.py:5628+`) or add `SCHEME()` to `dash build` (`dash.ado:1174-1185`) —
    currently neither path reaches `dash_render.py:4993`.
15. **Wire or remove the 9 no-op options** in Table 3 (`falpha`, `pstyle`, `recast`,
    `cmissing`, `connect`, `mlcolor`, `mlabwidth`, `coloruseplegend`, graph `scheme`) and
    the 9 dead renderer reads in Table 3b.
16. Add `contour`, `contourline`, `pccapsym`, `rbarm` — or give them a targeted
    "not supported by dash, use `twoway`" message rather than the generic unrecognised-type
    error.
17. Silence the `runpy.run_path` globals dump (`dash.ado:143`).

## 7. Regression tests to add (per CLAUDE.md rule 8, one per defect)

`test/test_twoway_parity.cscript` — one assertion per Table 2 row (option accepted,
rc==0), per Table 1 abbreviation, and for `name(g,replace)`, `saving(f)`, `saving(f.gph)`,
`function y=x^2`, standalone `scatteri`/`pci`/`function`, `tsline` under `tsset`.

`test/test_twoway_semantics.py` — JSON-level assertions for: multi-y expansion
(`scatter y1 y2 x` → 2 plot dicts), per-plot `if_expr` retention, `xlabel(1990(5)2020)`
tick expansion, `xscale(range())`, `legend(off …)` variants, `title()` sub-option
stripping, histogram bin rule + density, and the Table 3 no-op options once wired.
