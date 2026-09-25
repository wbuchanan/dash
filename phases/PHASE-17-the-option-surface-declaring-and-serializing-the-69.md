# Phase 17 — The option surface — declaring and serializing the 69

**Purpose.** `dash` promises that a `twoway` command pasted into it still runs. At the
syntax layer that promise holds — 115 of 115 measured options are accepted with rc 0 and
nothing aborts — but the promise underneath it does not. Sixty-nine of the options the
ultraplan dispositioned "implement" are declared **nowhere**: they reach `dash.ado` only
through the trailing `*` catch-all, so their values are thrown away before any spec JSON
is written, and the sections that own them (S07, S09, S10) have nothing to read when they
land. This phase does the declaring half of task **05-04**: it puts those 69 into the one
canonical inventory, gives each a minimum abbreviation, a serializer entry and a
`_dash_pending` line, and proves the value round-trips into the spec. It also closes the
defect class 05-04 exists to prevent — an option *accepted and silently dropped* — in the
four places the adversarial pass found one: `saving()`, the `colorvar()` family in server
mode, `xsize()`/`ysize()` in server mode, and every plot option under `by()`. Finally it
declares the four single-letter title aliases `t() b() l() r()` in the plot syntax block,
which makes the folding code already sitting at `dash.ado:534-537` live instead of dead.

---

## At a glance

| | |
|---|---|
| **Work items** | 6 (numbered 1–6 below) |
| **Functional / deliverable** | 6 functional / 0 deliverable |
| **Effort mix** | 1 large (item 1) · 2 medium (items 3, 4) · 3 small (items 2, 5, 6) |
| **Renderers touched** | `stata` — items 1, 2, 6 (`dash.ado` + `scripts/regen_option_surface.py`). `server` — items 3, 4, 5 (the Python source `ServerAppBuilder` emits for `bokeh serve`). `DashRenderer` is **not** modified: it is the reference behaviour the three server items must match. |
| **Ultraplan tasks discharged** | **05-04** "Declare the options destined for later sections" (items 1–5) · **04-03**'s overturned DONE claim, the last functional gap in S04 (item 6) |
| **Sections at entry** | **S05** — 3 DONE / 3 PARTIAL; status line: *"05-04 not done ① — 92 options declared nowhere"*. **S04** — 3 DONE / 2 PARTIAL; status line: *"narrow"*. (Both splits are the post-appendix counts: `REMAINING.md`'s §status table still reads *"4 done, 1 partial"* for S04 and *"05-04 not done"* for S05, because Appendix C's 17 overturned DONE claims — 04-03, 05-01 and 05-05 among them — move "All to PARTIAL".) |
| **Depends on** | — nothing hard. `REMAINING.md` §Suggested order, step 4: *"S05-04 + S07/S09/S10 options. The bulk. Decide (a) or (b) from §2 first — that decision sizes everything after it."* |
| **Unblocks** | Phase **18** (abbreviations, generator and reporting), Phase **19** (S07 statistical options), Phase **20** (S09 axis and text options), Phase **21** (S09 style options), Phase **22** (geometry, sizing and layout). None of those four can read a value that never arrived. |

---

## Why this phase exists

Everything in this section is copied from `REMAINING.md`. A developer should not need to
open that file to know what is broken.

### The measured option surface

> Every one of the 115 options in `test/fixtures/rejected_options.json` was
> re-run through `dash` in Stata at HEAD and classified by dash's own report.
>
> | plan disposition | total | honoured | accepted + reported ignored |
> |---|---:|---:|---:|
> | accept-and-report | 4 | 0 | 4 ✅ *as intended* |
> | implement-S06 | 3 | 0 | **3** |
> | implement-S07 | 25 | 12 | **13** |
> | implement-S09-axes-text | 28 | 2 | **26** |
> | implement-S09-style | 50 | 3 | **47** |
> | implement-S10 | 5 | 2 | **3** |
> | **total** | **115** | **19** | **96** |
>
> **0 rejections.** The drop-in claim holds at the syntax layer and decision 4
> (accept, never abort, report together) is satisfied — but **92 options the
> plan said to implement are only accepted and reported**, so their values
> never reach the spec.
>
> — `REMAINING.md` §2, "Blocker — the option surface  [S05-04, S07, S09, S10]"

§2 also records that the choice of how far to go is the user's, and that it sizes the
phases *after* this one:

> **Two defensible ways to close this**, and the choice is the user's:
> **(a)** implement all 92 — the plan as written; **(b)** implement the high-value
> subset (`text` `ttitle`/`tlabel` family, the `b1/l1/r1/t1title` set,
> `mlabformat` `mstyle` `lstyle` `acolor` `gap` `fxsize` `fysize` `scale`) and
> formally re-disposition the rest to accept-and-report in the plan and help.

**That decision does not gate this phase.** Under (a) the 69 must be declared so their
sections can read them; under (b) they must be declared so the ignoring note can name a
real option instead of whatever prefix the user typed. Only the owning-section tag
changes — `S07`/`S09`/`S10` under (a), `IGNORE` under (b).

### The declaring half: 69 of 111, measured

> The reporting half is sound: all 115 options in
> `test/fixtures/rejected_options.json` are accepted with rc 0, and 96 are named
> in a `dash: ignoring unsupported option(s):` note. Nothing is silently dropped.
>
> The declaring half is not. `dash.ado` declares 158 option tokens across its
> `syntax` blocks and tracks 39 more in `_dash_pending`. Cross-referencing
> against the 111 options the plan dispositioned "implement":
>
> | disposition | total | declared | **not declared** |
> |---|---:|---:|---:|
> | implement-S06 | 3 | 3 | 0 |
> | implement-S07 | 25 | 12 | **13** |
> | implement-S09-axes-text | 28 | 15 | **13** |
> | implement-S09-style | 50 | 7 | **43** |
> | implement-S10 | 5 | 5 | 0 |
> | **total** | **111** | **42** | **69** |
>
> **Remaining: declare and serialize these 69.** They reach `dash.ado` only
> through the trailing `*` catch-all, so no value ever arrives in the spec JSON
> and the sections that own them have nothing to read — which is exactly the
> state 05-04 exists to end.
>
> - **S07 (13):** `adjust` `area` `atobs` `ciplot` `discrete` `estcmd` `estopts`
>   `fitplot` `logit` `mean` `nofit` `noweight` `predopts`
> - **S09 axes/text (13):** `droplines` `tlabel` `tline` `tmlabel` `tmtick`
>   `tscale` `ttext` `ttick` `ttitle` `xvarformat` `xvarlabel` `yvarformat`
>   `yvarlabel`
> - **S09 style (43):** `acolor` `alalign` `alpattern` `alstyle` `alwidth`
>   `astyle` `barbsize` `baroffset` `bstyle` `clegend` `colorend`
>   `colorfillonly` `colorformissing` `colorkeysrange` `colorlevels` `colorrule`
>   `colorstart` `colorvarminmax` `dcolor` `dfcolor` `dlalign` `dlcolor`
>   `dlstyle` `dlwidth` `dotextend` `dsize` `dstyle` `dsymbol` `gap`
>   `headlabel` `lalign` `mangle` `mlabangle` `mlabformat` `mlabstyle`
>   `mlabtextstyle` `mlabvposition` `mlalign` `mwidth` `ndots` `nodropbase`
>   `pcycle` `plegend`
>
> Each needs its S04 minimum abbreviation, a serializer entry, and a
> `_dash_pending` line so it stays reported until its section lands.
>
> > Corrects §2 of this file, which put the figure at 92 by treating every
> > reported option as undeclared. 27 of those are declared and serialized
> > already, and are reported because `_dash_pending` correctly says they are
> > awaiting their section.
>
> — `REMAINING.md` Appendix A, "05-04 — Declare the options destined for later sections · PARTIAL"

**69 is the number this phase works to.** Appendix B repeats the correction from the
other side:

> It states "92 options the plan said to implement are only accepted and reported,
> so their values never reach the spec". Measured, that is wrong for 23 of them:
> b1title b2title colorlist fxsize fysize horizontal l1title l2title lstyle
> mlstyle mstyle r1title r2title scale sort t1title t2title text vertical
> xmlabel xmtick ymlabel ymtick are reported as ignored AND already serialized
> with their value. The 05-04 gap is 69 options, not 92; the other 23 are
> waiting on S06/S09/S10 renderer work, not on dash.ado.
>
> — `REMAINING.md` Appendix B, 05-04

### The defect class 05-04 exists to prevent, found in four places

05-04's `<done>` condition is that *nothing is silently dropped in the interim*. The
adversarial pass found four live violations. All four are quoted in full under
`## Work items`; the shape of them:

| option(s) | honoured by | ignored by | on `_dash_pending`? | user is told |
|---|---|---|---|---|
| `saving()` | neither renderer | both | **no** | nothing |
| `colorvar` `colordiscrete` `colornlevels` `colorcuts` `colormissing` (+`colpalette`) | `DashRenderer` | the emitted server app | **no** | nothing |
| `xsize()` `ysize()` | `DashRenderer` | the emitted server app | **no** (deliberately removed) | nothing |
| `msymbol` `msize` `malpha` `jitter` `mlabel` `mlcolor` `mlwidth` | `DashRenderer`, and the server app **without** `by()` | the server app's faceted branch | n/a — they are implemented | nothing |

`REMAINING.md` names why the pending list cannot catch the last three by itself:

> The reporting contract is mode-blind and has no converse test. `_dash_pending`
> is computed in dash.ado before the renderer is chosen, so an option honoured in
> standalone and dropped in server mode is silently dropped with no note
> (measured instances: colorvar family, xsize, ysize, every plot option under
> by(), plus the already-recorded secondary-axis family).
>
> — `REMAINING.md` Appendix C, 05-04

The converse test itself — *every option dash declares must either change the rendered
output or be named on `_dash_pending`* — is an itemised deliverable owned by **Phase 18**.
This phase fixes the four instances; Phase 18 builds the guard that stops new ones.

`REMAINING.md` also records why `xsize()`/`ysize()` are not on the list today, and the
comment block is still in the source at `dash.ado:633-641`:

```
    // scheme(), xsize(), ysize(), xtick() and ytick() are NOT listed.  They
    // are twoway GRAPH-level options, and this program promotes them --
    // `sreturn local g_xsize' and friends just above, picked up by the
    // promotion loop in _dash_process_segment -- so however they are
    // written they reach the renderer and are honoured.  Naming them here
    // told a user who typed dash.sthlp's own example,
    //     dash scatter mpg weight, xsize(10) ysize(2)
    // that dash had ignored two options it had just applied.
```

That reasoning is correct for `DashRenderer` and false for `dash serve`, which is exactly
what item 5 is about.

### The four title aliases that were never declared

> | task | what the refutation found |
> |---|---|
> | 04-03 | `T() B() L() R()` never added to `_dash_parse_plot_opts`, so the folding code at `dash.ado:534-537` is dead |
>
> — `REMAINING.md` §"17 DONE claims the adversarial pass overturned"

Confirmed in the tree: `T(string) B(string) L(string) R(string)` are declared in the
**graph** syntax block at `dash.ado:301-302` and are absent from the **plot** syntax block
(`dash.ado:475`+). The folding code below it runs against locals that `syntax` never
creates, so it can never fire:

```stata
    // twoway accepts t(), b(), l() and r() as abbreviations of t1title(),
    // b1title(), l1title() and r1title().  Stata derives the minimum from the
    // leading run of capitals and the digit in "t1title" ends that run, so
    // "T1title" yields "t1", never "t".  The four single-letter forms are
    // declared separately and folded in here.  Measured against real twoway --
    // see test/fixtures/abbrev_truth.json.
    if `"`t'"' != "" & `"`t1title'"' == "" local t1title `"`t'"'
    if `"`b'"' != "" & `"`b1title'"' == "" local b1title `"`b'"'
    if `"`l'"' != "" & `"`l1title'"' == "" local l1title `"`l'"'
    if `"`r'"' != "" & `"`r1title'"' == "" local r1title `"`r'"'
```

### Section status at entry

> | # | Section | Tasks | Status | What is left |
> |---|---|---:|---|---|
> | 04 | Abbreviations | 5 | 4 done, 1 partial ② | narrow |
> | 05 | Option surface | 6 | **05-04 not done** ① | 92 options declared nowhere |
> | 07 | Statistical defaults | 6 | done ③, 13 options open ① | see §2 |
> | 09 | Axes, legend, titles | 7 | 1 done, 6 partial ②, **73 options open** ① | see §2 — largest single family; none of S09 reached `ServerAppBuilder` |
> | 10 | Geometry | 4 | 2 done, 2 partial ② | `fxsize` `fysize` `scale` ① |
>
> — `REMAINING.md` §"Status by section"

---

## Epics

| epic | goal | items |
|---|---|---|
| **E17.A — The declaring half** | Every option the plan dispositioned "implement" is declared by name, abbreviates like `twoway`, and arrives in the spec JSON with its value. | 1, 6 |
| **E17.B — Nothing accepted is silently dropped** | An option dash accepts either changes what the user sees, in the mode they asked for, or is named in the ignoring note. | 2, 4, 5 |
| **E17.C — The faceted branch honours its options** | `by()` stops being an option-eating branch: the facet loop draws through the same glyph layer as every other server plot. | 3 |

---

## User stories

### E17.A — The declaring half (items 1, 6)

**US-17.A1 — the paste survives with its meaning.**
*As a Stata user pasting a `twoway` command into `dash`, I want the options I typed to
reach the graph spec, so that when the feature lands I get the graph I asked for rather
than a graph that silently forgot half my command.*

- **Given** `dash scatter mpg weight, mlabel(make) mlabformat(%9.0fc) name(g1)`
  **When** I run `dash build, saving(d.html)`
  **Then** rc is 0, **and** the spec JSON for `g1`'s scatter carries
  `"mlabformat":"%9.0fc"` in its `options` object.
- **Given** any of the 69 options with a value, taken from that option's own probe in
  `test/fixtures/rejected_options.json`
  **When** I run the probe command
  **Then** the option's canonical name appears as a key in the spec JSON with the value I
  typed, **and** rc is 0.
- **Given** an option among the 69 that takes no argument (`adjust`, `atobs`, `discrete`,
  `logit`, `mean`, `nofit`, `noweight`, `colorfillonly`, `colorkeysrange`,
  `colorvarminmax`, `headlabel`, `mwidth`, `nodropbase` — 13, per the fixture's
  `takes_argument: false`)
  **When** I type it
  **Then** it is serialized as its own name, the way `syntax` returns a flag, and rc is 0.

**US-17.A2 — the note names something I can look up.**
*As a Stata user, I want the "ignoring unsupported option(s)" note to name the real
option, so that I can search `dash.sthlp` or `help twoway_options` for it.*

- **Given** I type an abbreviated form of one of the 69, e.g. `mlabf(%9.0fc)`
  **When** dash reports the option as pending its section
  **Then** the note names `mlabformat`, not `mlabf`.
- **Given** any of the 69 is declared but its owning section has not landed
  **When** I use it
  **Then** it is named on `_dash_pending` and reported, and the rendered output is
  byte-identical to the same command without it.

**US-17.A3 — `t()` means `t1title()` inside a plot.**
*As a Stata user pasting `(scatter mpg weight, t("Top"))`, I want the title to appear,
because `twoway` accepts `t()` as an abbreviation of `t1title()`.*

- **Given** `dash scatter mpg weight, t("Top") name(g1)` and the same with
  `t1title("Top")`
  **When** both are built
  **Then** the two spec JSONs agree on the `t1title` key.
- **Given** the same four aliases inside a plot's own parentheses
  **When** the plot is parsed by `_dash_parse_plot_opts`
  **Then** `b()`, `l()` and `r()` fold to `b1title`, `l1title`, `r1title` exactly as
  `t()` folds to `t1title`.

### E17.B — Nothing accepted is silently dropped (items 2, 4, 5)

**US-17.B1 — `saving()` tells me the truth.**
*As a Stata user who typed `saving()` out of habit, I want dash to either write that file
or tell me it did not, so that I do not go looking for a graph that was never written.*

- **Given** `dash scatter mpg weight, name(g1) saving(g1.gph)`
  **When** I build
  **Then** either the file is produced, **or** `saving` is named in the
  `dash: ignoring unsupported option(s):` note. Silence is a failure.

**US-17.B2 — the served dashboard is coloured like the saved one.**
*As a `dash serve` operator, I want `colorvar()` to map colours in the served app exactly
as it does in the saved HTML, so that the dashboard I demo is the dashboard I tested.*

- **Given** `dash scatter mpg weight, colorvar(rep78) colpalette(viridis) name(g1)`
  **When** I build with `server` and load the app
  **Then** the figure carries a colour mapper over `rep78` with the same palette the
  standalone renderer uses, **or** `colorvar` and its family are named in the note as
  pending for server mode.
- **Given** `colorvar(...)` naming something that is not a plain Stata identifier
  **When** the server app is generated
  **Then** the name is rejected by the same identifier check `DashRenderer` applies
  (`dash_render.py:3021-3022`) and never reaches the emitted source.

**US-17.B3 — the served figure has the proportions I asked for.**
*As a `dash serve` operator, I want `xsize()`/`ysize()` to shape the served figure, so
that a wide time-series strip is wide in both modes.*

- **Given** `dash scatter mpg weight, xsize(10) ysize(2) name(g1)`
  **When** I build in server mode
  **Then** the served figure's width-to-height ratio matches the standalone figure's,
  **or** `xsize`/`ysize` are named in the note for server mode.

### E17.C — The faceted branch honours its options (item 3)

**US-17.C1 — `by()` does not eat my options.**
*As a dashboard viewer, I want a faceted served plot to look like the unfaceted one, so
that adding `by(foreign)` changes the layout and nothing else.*

- **Given** `dash scatter mpg weight, msymbol(T) msize(10) malpha(0.4) mlabel(make)
  name(g1)` built in server mode
  **When** I add `by(foreign)` and rebuild
  **Then** each facet draws triangles at size 10 and alpha 0.4 with marker labels —
  the same glyph properties the unfaceted figure has.
- **Given** the same command in standalone mode
  **When** both dashboards are compared property by property
  **Then** the faceted server figure agrees with the faceted standalone figure on
  `marker`, `size`, `fill_alpha`, `line_color`, `line_width` and the presence of a
  `LabelSet`.

---

## Business requirements

Each is testable as written; the test that proves it is named in `## Test plan`.

| id | requirement |
|---|---|
| **BR-17.1** | No command that runs today may stop running. Every command in `test/fixtures/twoway_corpus.do` continues to return rc 0 from `dash` (the O2-01 core assertion), and the 115-option probe set still shows **0 rejections**. |
| **BR-17.2** | Each of the 69 options listed in `REMAINING.md` Appendix A is declared by name in `dash.ado` and its value appears in the spec JSON under its canonical name. |
| **BR-17.3** | Each of the 69 is named on a `_dash_pending` list with its owning section until that section lands, and reported in the `dash: ignoring unsupported option(s):` note. |
| **BR-17.4** | Serializing the 69 changes no rendered output: for every option on the pending list, two different values produce byte-identical dashboards (the existing `test_unsupported_report_is_true.py` contract). |
| **BR-17.5** | The ignoring note names canonical option names, never the abbreviation the user typed, for every option dash declares. |
| **BR-17.6** | `t()`, `b()`, `l()` and `r()` are accepted inside a plot's parentheses and resolve to `t1title`, `b1title`, `l1title`, `r1title`. |
| **BR-17.7** | `saving()` is either honoured or named in the note. It may not be accepted, serialized and ignored in silence. |
| **BR-17.8** | The `colorvar()` family (`colorvar`, `colordiscrete`, `colornlevels`, `colorcuts`, `colormissing`, `colpalette`) either behaves in `dash serve` as it does in `dash build`, or is reported as pending for server mode. |
| **BR-17.9** | `xsize()` and `ysize()` either shape the served figure as they shape the saved one, or are reported as pending for server mode. |
| **BR-17.10** | A served plot under `by()` honours the same plot options as the same plot without `by()`. No option may be honoured in one and discarded in the other. |
| **BR-17.11** | 05-03's reporting channel stays alive: `dash.ado` contains `sreturn local _pending` and `sreturn local _unknown` at **both** the graph and plot level after this phase, and `_dash_report_ignored` still fires. |
| **BR-17.12** | Option values are serialized through the existing escaping path only. No new hand-written JSON assembly is introduced (CLAUDE.md rules 1 and 16). |

---

## Technical requirements

### TR-17.1 — The inventory is the only supported entry point, and it is not safe to run yet

`dash.ado` repeats its option list in five places. `scripts/regen_option_surface.py` is
the single source of truth for all five; its own header says so:

```python
"""Regenerate dash.ado's option surface from one canonical inventory.

dash.ado repeats the option list in five places (two syntax blocks, two sreturn
blocks, the plot-option JSON key list, and the graph-level propagation loops).
Keeping them in sync by hand is how they drifted.  This script is the single
source of truth; run it, don't hand-edit those blocks.
"""
```

Its inventory today, measured by executing the two lists: **54 graph names, 70 plot names,
61 of them carrying an owning section** (`GRAPH` at `scripts/regen_option_surface.py:44`,
`PLOT` at `:67`, `PENDING = {n: s for n, s in GRAPH + PLOT if s}` at `:97`). The splice
steps it performs, in order:

| step | rewrites | target |
|---|---|---|
| 1 | graph syntax block | `dash.ado:_dash_parse_graph_opts`, from `syntax [, ///` to `\n    ]` |
| 2 | graph `sreturn` block | same program, from the first `sreturn local ` to `\nend` |
| 3 | plot syntax block | `dash.ado:_dash_parse_plot_opts`; declares **`PLOT_NAMES + GRAPH_NAMES`** |
| 4 | plot `sreturn` block | plot-level names, then graph-level names again with a `g_` prefix |
| 5 | plot-option JSON key list | `dash.ado:_dash_plot_opts_to_json` (`:854`), the `foreach key in ...` list |
| 6 | every graph-level propagation loop | all `foreach gkey in ` / `foreach gk in ` lists |
| 7 | *(computes `pending_lines` and never splices it)* | — dead; owned by Phase 18 |

Step 3 is why a mis-allocation between `GRAPH` and `PLOT` is recoverable: the plot block
declares the graph names too, and step 4 returns them as `g_*` for the promotion loop to
pick up. It changes **where** the value lands in the spec (`graph_options` versus the
plot's `options`), not whether it is accepted.

**Precondition — do not run the generator before Phase 18's fixes.** `REMAINING.md`
records two reasons, both measured:

> Fix the generator so it is idempotent before extending it. Re-running
> scripts/regen_option_surface.py against HEAD's dash.ado silently deletes
> hand-added declarations that are not in its inventory: `HOVer(string)`, the
> `T()/B()/L()/R()` title aliases, `PBGC/XLA2/XSC2/XTI2/YLA2/YSC2/YTI2`,
> `BINS(string)`, `sreturn local hover`, and — critically — `sreturn local
> _pending` and `sreturn local _unknown`, which are the only channel feeding
> `_dash_report_ignored`. Deleting those two lines disables 05-03's reporter
> entirely. Since the block comment in dash.ado says "Do not hand-edit … run the
> generator", this is the procedure a developer will follow to do the item above.
>
> — `REMAINING.md` Appendix B, 05-04

> Beyond HOVer/T/B/L/R/PBGC/XLA2.../BINS/`sreturn local hover`/`sreturn local
> _pending`/`sreturn local _unknown`, re-running scripts/regen_option_surface.py
> also deletes: (a) the whole level() validation block in _dash_parse_plot_opts
> (dash.ado:549-561), which is the only thing stopping `level(150)` becoming a
> Python exception inside the renderer; (b) the ENTIRE plot-level `local
> _dash_pending` accumulation (dash.ado:593-641) and `local _dash_unknown` (:642)
> plus its `sreturn local _pending`/`_unknown` (:770-771) — after a regen the
> whole file contains zero `sreturn local _pending`, so 05-03's reporter is dead
> at BOTH levels, not just graph level; (c) `sreturn local g_hover` (:750) and
> `hover` from all four graph propagation loops (:1129, :1399, :1415, :1469);
> (d) every alias-folding `if` (bins->bin, bw->barwidth, mlg->mlabgap,
> cv/colv->colorvar, pbgc->plotbgcolor, xla2/xsc2/xti2/yla2/ysc2/yti2,
> t/b/l/r->*1title). Separately, the script is not runnable as documented on any
> other checkout: REPO is a hardcoded absolute path
> (scripts/regen_option_surface.py:17) and the final `json.dump(...,
> open("/tmp/dash-wf/b2/option_inventory.json", "w"))` runs AFTER dash.ado has
> already been overwritten, so a missing directory leaves the repo mutated and
> the script traceback-ing.
>
> — `REMAINING.md` Appendix C, 05-04

> The generator's splice has ALREADY double-applied in the committed dash.ado —
> the generated blocks are duplicated at HEAD, not merely at risk of it. The
> "this block is generated by scripts/regen_option_surface.py" banner appears 4
> times (twice per syntax block), and `_dash_parse_graph_opts` contains the
> t()/b()/l()/r() alias-fold `if`-ladder twice in a row with two different
> comment headers. Both copies run, so behaviour is unchanged, but the file no
> longer matches what the generator would produce and the next regeneration diff
> will be unreadable. De-duplicate the splice markers before extending the
> inventory.
>
> — `REMAINING.md` Appendix C, 05-04

Those three items are **Phase 18's work items, not this phase's** — see
`## Risks and sequencing notes` for the two ways to sequence around them.

### TR-17.2 — Where each of the 69 goes

`REMAINING.md` gives the allocation rule verbatim:

> The t*/pc* family are graph-level (graph syntax block + the four `foreach
> gk`/`foreach gkey` propagation lists); the style family is plot-level (plot
> syntax block + `_dash_plot_opts_to_json`).

Applied:

| family | count | inventory list | owner tag | notes |
|---|---:|---|---|---|
| `tlabel` `tline` `tmlabel` `tmtick` `tscale` `ttext` `ttick` `ttitle` | 8 | `GRAPH` | `S09` | the t-axis family; `REMAINING.md` §2 records that "the 11 `t*`/`pcarrow` options were re-probed on `tsset` monthly data and `pcarrow` variables to rule out a harness artefact; all 11 are ignored" |
| `xvarformat` `xvarlabel` `yvarformat` `yvarlabel` `droplines` | 5 | decide at implementation | `S09` | the rule above names only the `t*`/`pc*` and style families. The four `*var*` options are axis-label controls; `droplines` belongs to a single plot. Settle each against `twoway`'s own grammar when the abbreviation probe runs, and record the choice in the generator's list. |
| `adjust` `area` `atobs` `ciplot` `discrete` `estcmd` `estopts` `fitplot` `logit` `mean` `nofit` `noweight` `predopts` | 13 | `PLOT` | `S07` | statistical estimation controls; they sit beside `bin`, `kernel`, `bands`, `at`, `ciopts`, `fitopts`, which are already `PLOT`/`S07` |
| the 43 style options | 43 | `PLOT` | `S09` | includes the `pcarrow` look options `barbsize`, `headlabel`, `mangle` |

### TR-17.3 — How a declaration is formed, and the abbreviation trap

`declare()` (`scripts/regen_option_surface.py:152`) capitalises the minimum abbreviation
and appends the type. Three sets drive it:

- `FLAGS` (`:31`) — no argument. **13 of the 69 belong here**, taken from the fixture's
  own `takes_argument: false` field: `adjust` `atobs` `discrete` `logit` `mean` `nofit`
  `noweight` `colorfillonly` `colorkeysrange` `colorvarminmax` `headlabel` `mwidth`
  `nodropbase`.
- `ASIS` (`:35`) — `(string asis)`, for anything that carries a numlist, a quoted label or
  nested parentheses. The `t*` family (`tlabel(2000m1(12)2004m1)`, `tline`, `ttext`,
  `ttick`, `tmtick`, `tmlabel`) and `colorcuts`-shaped members of the style family belong
  here; the fixture's probe command for each shows the shape it must survive, e.g.
  `dash tsline y, tlabel(2000m1(12)2004m1) name(g1)`.
- everything else — `(string)`.

The minimum comes from `base_min()` (`:110`), which reads
`test/fixtures/abbrev_truth.json` and **falls back to the full option name when there is
no truth entry**. None of the 69 has an entry today. Declaring them with no measurement
therefore produces all-caps, full-name declarations, which reproduces a defect the
adversarial pass already measured on two other options:

> fxsize()/fysize() are declared at a LONGER minimum than twoway's, so the
> abbreviated forms twoway accepts are silently thrown away. dash.ado declares
> `FXSIZE(string)` / `FYSIZE(string)` (all-caps = full name required); twoway's
> measured minimum is `fxsiz` / `fysiz`. A pasted `twoway ..., fxsiz(50)`
> therefore falls through the `*` catch-all in dash: rc 0, a note naming a
> non-existent option `fxsiz()`, and the value gone. … The abbreviation-probe
> item should be scoped to 71 options, not 69.
>
> — `REMAINING.md` Appendix C, 05-04

The abbreviation probe itself (`scripts/extract_abbrev_truth.do` →
`test/fixtures/abbrev_truth.json`) is **Phase 18's** deliverable. `resolve_minimums()`
(`:120`) asserts on ambiguity — `assert not ambiguous(mins), "measured minimums are
already ambiguous"` — so adding 69 names can hard-fail the generator, and
`REMAINING.md` warns it may force longer minimums than existing dash do-files use.

### TR-17.4 — The serialization path, and why nothing new may be hand-written

Once a name is in `PLOT`, step 5 rewrites the key list in `_dash_plot_opts_to_json`
(`dash.ado:854`), whose body already escapes every value:

```stata
        local val `"`s(`key')'"'
        if `"`val'"' != "" {
            _dash_json_str `"`val'"' _jv
            if `nparts' > 0 local parts `"`parts',"'
            local parts `"`parts'"`key'":"`_jv'""'
            local nparts = `nparts' + 1
        }
```

`_dash_json_str` (`dash.ado:224-235`) escapes backslash first, then `"`, tab, LF and CR.
Routing the 69 through the generator therefore puts them on the hardened path by
construction; a hand-written serializer entry would not (CLAUDE.md rules 1 and 16).

Graph-level names ride the four propagation loops that step 6 rewrites. They begin at
`dash.ado:1125` (`_dash_process_segment`, the `foreach gkey in` loop), `:1395`, `:1411`
and `:1465` (`_dash_plot`); `REMAINING.md` locates the same loops at `:1121`, `:1462` in
the item's *Where* field and at `:1129`, `:1399`, `:1415`, `:1469` in the Appendix C
`hover` item. All four lists must gain the new graph names or the value is parsed and then
dropped on the floor between `_dash_parse_plot_opts` and the spec.

Note the fifth, dead copy — it is **Phase 18's** item, and it must not be extended here by
mistake:

> `_dash_graph_opts_to_json` (dash.ado:891) is a fifth, DEAD, stale copy of the
> graph-option list that the generator does not maintain. … Nothing calls it
> today, so it is not a live bug, but it is a loaded gun for the next developer
> who reaches for the obvious-looking serializer.
>
> — `REMAINING.md` Appendix C, 05-04

### TR-17.5 — `_dash_pending`, and the test it will break on the way

Every newly declared option needs a line in the relevant `_dash_pending` accumulation
(plot-level at `dash.ado:593-641`, graph-level in `_dash_parse_graph_opts`) of the shape

```stata
    if `"`mlabformat'"' != "" local _dash_pending `"`_dash_pending' mlabformat"'
```

**Expected, and required, consequence:** `test/test_unsupported_report_is_true.py`
contains

```python
class TestTheListIsCoveredAndHonest:
    def test_every_pending_option_is_covered_here(self):
        """A new entry on the list must come with values to test it."""
        missing = sorted(set(_plot_pending() + _graph_pending())
                         - set(PLOT_VALUES))
```

`_pending()` (`:132`) parses the two blocks out of `dash.ado` by regex, so adding 69
entries makes this test fail until `PLOT_VALUES` gains 69 entries — two distinct values
per option, and a `ptype` to render them on. That is the test doing its job, and supplying
those values is part of item 1, not a reason to skip the pending lines. The second half of
the same file's contract then holds the line for BR-17.4: rendering with each pair of
values must produce the identical HTML hash, because the 69 are serialized and *not yet*
honoured.

### TR-17.6 — `t() b() l() r()` in the plot block (item 6)

Add `T(string) B(string) L(string) R(string)` to the `syntax` block of
`_dash_parse_plot_opts` (`dash.ado:475`+). The graph block already has them at
`dash.ado:301-302`; the plot block's folding ladder is already written at
`dash.ado:534-537` and becomes live the moment the four names are declared. Two
constraints:

1. They are **aliases, not prefixes** — `T1title` yields the minimum `t1`, never `t`,
   because the digit ends the leading run of capitals. That is why they are declared
   separately rather than by shortening `T1title`. The comment above the fold states the
   measurement and points at `test/fixtures/abbrev_truth.json`.
2. The generator does not know about them (TR-17.1), so after any regeneration they must
   be re-spliced — which is precisely Phase 18's idempotence item.

### TR-17.7 — `saving()` (item 2)

`SAVing(string)` is declared in both blocks, `saving` is in the generator's `GRAPH` list
at `scripts/regen_option_surface.py:46` with **no owning section**, so it never reaches
`PENDING`, and `dash_render.py` contains no consumer of it: the only two occurrences of
the string in the renderer are comments about `dash build, saving(app.py)`, i.e. the
build-time output path, not the graph option. Two acceptable resolutions, per the item:

- **implement** — write the HTML/py for that one graph to the named file; or
- **declare it pending** — add `("saving", "IGNORE")` to `GRAPH` and a `saving` line to
  the graph-level `_dash_pending` block so the note names it.

The second is the small-effort path and the one the item's tag (`S`) is sized for.

### TR-17.8 — the `colorvar()` family in server mode (item 4)

Measured in the tree at HEAD: over the emitted region (`class ServerAppBuilder`,
`dash_render.py:12265` onward) the literal strings `colorvar`, `colpalette`,
`colornlevels`, `colorcuts`, `colormissing`, `colordiscrete`, `_apply_colorvar` and
`_PALETTE_MAP` occur **0 times each**; over `DashRenderer` they occur 19, 2, 4, 4, 4, 6, 4
and 4 times. The standalone implementation is `GlyphMapper._apply_colorvar`
(`dash_render.py:2995`) with `_PALETTE_MAP` at `dash_render.py:2971`; the docstring
records the whole Stata-18 surface it covers:

```
        Supports Stata 18 colorvar_options:
            colorvar(varname)   — variable whose values drive the color mapping
            colordiscrete       — treat a numeric variable as discrete categories
            coloruseplegend     — add a plot legend instead of a ColorBar
            colornlevels(#)     — quantize continuous data into # equal-width levels
            colorcuts(numlist)  — custom cut-point boundaries for continuous data
            colormissing(color) — Bokeh color for missing/NaN values (default: grey)
            colpalette(name)    — palette name; see _PALETTE_MAP for supported keys

        Numeric columns default to a LinearColorMapper (viridis palette).
        String columns, or numeric columns with colordiscrete / colornlevels /
        colorcuts, use a CategoricalColorMapper (category10 palette).
```

`_PALETTE_MAP` has 21 keys (`viridis`→`Viridis256` … `paired`→`Paired_12`), so a port must
carry the map, not a subset.

**Security requirement, non-negotiable.** `_apply_colorvar` validates the variable name
before it is used as a column key:

```python
        # Security: validate varname is a safe Stata identifier
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", varname):
            return
```

(`dash_render.py:3021-3022`.) The server builder writes **Python source**, so an
unvalidated `colorvar()` value is worse there than in the standalone renderer: it would be
interpolated into a file that is later executed. Whichever route is taken, that
`re.fullmatch` check must run on the server path too, and must run before any value is
written into the emitted source.

**Measure before porting.** `_apply_colorvar` is a method of `GlyphMapper`, and the
emitted app copies `GlyphMapper` verbatim (`for _cls in (OptionTranslator, SchemeParser,
GlyphMapper):` at `dash_render.py:12407-12409`, via `inspect.getsource`), while
`map_scatter` calls `self._apply_colorvar(fig, r, plot_source, options)` at
`dash_render.py:3479-3480` and the emitted scatter branch now delegates
(`_r = _DASH_MAPPER.map_scatter(fig, csrc, yvar, xvar, opts, view=_sc_view,
color_idx=pi)`, `dash_render.py:14090-14092`). The port may therefore reduce to adding
call sites for the other plot types rather than copying code. **Establish which by
running the failing test in `## Test plan` first**; `REMAINING.md` is the source of record
where its statement and a later measurement disagree, and the test — not this note —
decides the size of the fix.

### TR-17.9 — `xsize()`/`ysize()` in server mode (item 5)

Standalone turns them into an aspect ratio in `_resolve_aspect_ratio`
(`dash_render.py:9228-9250`), with the precedence `dash.sthlp` documents —
`1. xsize()/ysize()  2. aspectratio()  3. the scheme's graphsize`
(`dash_render.py:9525-9527`):

```python
        xs = _stat_option_float(graph_opts, "xsize", None, "graph", lo=0.0)
        ys = _stat_option_float(graph_opts, "ysize", None, "graph", lo=0.0)
        for name, val in (("xsize", xs), ("ysize", ys)):
            if val is not None and val <= 0:
                # Stata returns r(198) for xsize(0) and xsize(-3).
                warnings.warn(...)
        # Either one alone keeps the scheme's value for the other, exactly as
        # Stata does: xsize(9) under stcolor gives 4.5 x 9.
```

The emitted app's figure kwargs honour `aspectratio` alone
(`dash_render.py:13839-13855`):

```python
            "        _raw_ar = go.get('aspectratio', '')",
            "        if _raw_ar:",
            "            try: _fig_kw['aspect_ratio'] = float(_raw_ar)",
            "            except (ValueError, TypeError): pass",
```

`REMAINING.md` records the related, still-open half — *"re-checked by string,
`graphsize_x`, `graphsize_y` and `_resolve_aspect_ratio` all occur **0** times in the
emitted app, so the scheme's graph size still does not reach `dash serve`"* — which is a
Phase 25 item. This phase's requirement is narrower: `xsize`/`ysize` either reach the
emitted `figure()` computation with standalone's precedence and its `<= 0` rejection, or
they go on the graph `_dash_pending` list as pending-for-server.

### TR-17.10 — the faceted branch (item 3)

The `by()` branch is a second, hand-written dispatch. Measured in the emitted source at
`dash_render.py:15138-15145`, the only two option keys it reads are `lcolor` and
`mcolor`:

```python
            "                opts = plot.get('options', {})",
            "                yvar_f = plot.get('yvar', '') or plot.get('var', '')",
            "                xvar_f = plot.get('xvar', '')",
            "                color = (_resolve_color(opts.get('lcolor') or opts.get('mcolor', ''))",
            "                         or _dash_scheme_color(pi, ptype))",
            "                _glyph_kw = {'view': _fac_view} if _fac_view is not None else {}",
            "                if ptype == 'scatter':",
            "                    _fac_fig.scatter(xvar_f, yvar_f, source=_fac_src, size=6, color=color, legend_label=yvar_f, **_glyph_kw)",
```

The three hardcoded constants the item names are all visible there and below: `size=6`
(scatter and the `dropline` marker at `:15200`), `width=0.8` (`vbar`, `:15149`) and
`line_width=_SCHEME_LINE_WIDTH` on every line-bearing branch. The fix routes the facet
loop through the copied `GlyphMapper` — `ServerAppBuilder._glyph_layer_lines`
(`dash_render.py:12315`), whose docstring states the same lesson this item re-learns:

```
        S15-03. The generated app used to carry 46 hand-written ``ptype``
        branches that re-implemented what ``GlyphMapper``'s 39 ``map_*``
        methods already do. They drifted, repeatedly and silently: served
        scatters at alpha 0.7 where the scheme says 0.8, areas at 0.4 against
        1.0, bars outlined white, a served ``lpolyci`` that drew no band at
        all. Each was found by measurement after the fact.
```

**Scope split with Phase 06.** Phase 06 owns the *plot-type* coverage of the facet chains
(the 17 types that "draw nothing under `by()`"). This item owns the *option* half: the
`options` dict must reach the glyph. Doing item 3 by delegating to `GlyphMapper` discharges
both, which is why it should be coordinated with Phase 06 rather than done twice.

### TR-17.11 — Invariants this phase may not break

| invariant | how it is checked |
|---|---|
| rc 0 across the corpus (decision 4) | `test/test_option_surface.cscript` O2-01 over `test/fixtures/twoway_corpus.do` |
| the reporter still fires at both levels | `grep -c "sreturn local _pending" dash.ado` ≥ 2; `test/test_option_report_paren.cscript` |
| `level()` validation survives | `dash scatter mpg weight, level(150)` still exits 198 from Stata, not from Python |
| existing abbreviations keep resolving | `test/test_abbreviations.cscript`, including the A7 collision guard |
| pending options change nothing | `test/test_unsupported_report_is_true.py`, both directions |
| no new JSON assembled by hand | every new key flows through `_dash_json_str` (`dash.ado:224`) |
| the emitted app stays self-contained | nothing imported from the package; classes are written into the file (`dash_render.py:12315`'s contract) |

---

## Work items

Six items, numbered as handed over. Tags are `[kind · renderer · effort]`.

---

**1. [functional · stata · large]** *(origin: ultraplan task 05-04; source: `REMAINING.md`
Appendix B)*

> Declare and serialize the 69 implement-dispositioned options that are declared nowhere.
> They are accepted only by the trailing `*` catch-all, so their values are thrown away
> and never reach the spec. Add each to `GRAPH`/`PLOT` in
> scripts/regen_option_surface.py with its owning section, regenerate, and confirm the
> value round-trips. The 69, by owner — S07 (13): adjust area atobs ciplot discrete
> estcmd estopts fitplot logit mean nofit noweight predopts. S09-axes-text (13):
> droplines tlabel tline tmlabel tmtick tscale ttext ttick ttitle xvarformat xvarlabel
> yvarformat yvarlabel. S09-style (43): acolor alalign alpattern alstyle alwidth astyle
> barbsize baroffset bstyle clegend colorend colorfillonly colorformissing
> colorkeysrange colorlevels colorrule colorstart colorvarminmax dcolor dfcolor dlalign
> dlcolor dlstyle dlwidth dotextend dsize dstyle dsymbol gap headlabel lalign mangle
> mlabangle mlabformat mlabstyle mlabtextstyle mlabvposition mlalign mwidth ndots
> nodropbase pcycle plegend. The t*/pc* family are graph-level (graph syntax block + the
> four `foreach gk`/`foreach gkey` propagation lists); the style family is plot-level
> (plot syntax block + `_dash_plot_opts_to_json`).

*Where:* `dash.ado:_dash_parse_graph_opts` (syntax block, `:281`),
`dash.ado:_dash_parse_plot_opts` (syntax block, `:475`),
`dash.ado:_dash_plot_opts_to_json` (`:854`), `dash.ado:_dash_plot` (gopts_json loop,
`:1462`), `dash.ado:_dash_process_segment` (g_* propagation loop, `:1121`),
`scripts/regen_option_surface.py:GRAPH`, `scripts/regen_option_surface.py:PLOT`.

*Evidence:* Appendix A's declared-versus-dispositioned table (111 → 42 declared, **69
not declared**) and the family lists, both quoted under `## Why this phase exists`. All
69 are present in `test/fixtures/rejected_options.json` with a `disposition`, a
`takes_argument` flag and at least one `dash_command` probe — confirmed by reading the
fixture, which is what makes the round-trip test drivable from data rather than from a
hand-written list.

---

**2. [functional · stata · small]** *(origin: 05-04; source: `REMAINING.md` Appendix C)*

> `saving()` is declared in BOTH syntax blocks, serialized into `graph_options`, read by
> neither renderer, and is NOT on either `_dash_pending` list — an
> accepted-but-silently-dropped option, the exact defect class 05-04's action text
> forbids creating. Either implement it (write the HTML/py for that one graph) or add
> `saving` to the graph-level `_dash_pending` block and to
> `scripts/regen_option_surface.py:GRAPH` with an owning section so the note names it.

*Where:* `dash.ado:_dash_parse_graph_opts` (`SAVing` declaration + `local _dash_pending`
block), `dash.ado:_dash_parse_plot_opts` (same),
`scripts/regen_option_surface.py:GRAPH`.

*Evidence:* the Appendix C item above. Confirmed in the tree: `("saving", None)` sits in
the generator's `GRAPH` list at `scripts/regen_option_surface.py:46` with no owning
section, so it cannot reach `PENDING`; `dash_render.py`'s only two mentions of `saving`
are comments about the build-time app path (`:16149`, `:16216`).

---

**3. [functional · server · medium]** *(origin: 05-04; source: `REMAINING.md` Appendix C)*

> The faceted (`by()`) branch of the emitted server app is a SECOND hand-written glyph
> dispatch that ignores the plot `options` dict entirely except for `lcolor`/`mcolor`.
> Every other serialized plot option is silently discarded on that path — `msymbol`,
> `msize`, `malpha`, `jitter`, `mlabel`, `mlcolor`, `mlwidth` all work in standalone AND
> in non-faceted server mode, then vanish the moment `by()` is added. The branch
> hardcodes `size=6`, `width=0.8`, `line_width=_SCHEME_LINE_WIDTH`. Fix: route the facet
> branch through the copied `GlyphMapper` (the `_glyph_layer_lines()` machinery S15-03
> already added for the unfaceted branch) instead of the inline `_fac_fig.scatter(...)`
> ladder.

*Where:* `dash_render.py:ServerAppBuilder` facet branch (emitted lines at
`dash_render.py:15133-15205`), `dash_render.py:ServerAppBuilder._glyph_layer_lines`.

*Evidence:* the Appendix C item, plus the emitted source quoted in TR-17.10 — `opts` is
read for `lcolor`/`mcolor` only at `:15141-15142`, `size=6` at `:15145`, `width=0.8` at
`:15149`, `_SCHEME_LINE_WIDTH` on every line branch from `:15147` to `:15213`. Related
finding, same root cause: *"the `by()` and `by(total)` facet loops are hand-written
copies that only ever learned a subset of the plot types"* (`REMAINING.md` Appendix B,
"Three findings worth pulling out first").

---

**4. [functional · server · medium]** *(origin: 05-04; source: `REMAINING.md` Appendix C)*

> The whole `colorvar()` colour-mapping family is absent from the emitted server app —
> `colorvar`, `colordiscrete`, `colornlevels`, `colorcuts`, `colormissing` are honoured
> by DashRenderer and ignored in server mode, and none of them is on `_dash_pending`, so
> server users get a plain single-colour plot with no note. (`colpalette` rides on
> `colorvar`, so it goes too; `coloruseplegend` is already on the pending list and is
> honest.) Fix: port `_apply_colorvar`/`_PALETTE_MAP` (dash_render.py:3011-3032) into
> ServerAppBuilder's emitted source, or make the note mode-aware.

*Where:* `dash_render.py:3011-3032` (colpalette/`_PALETTE_MAP`, the DashRenderer
implementation), `dash_render.py:ServerAppBuilder` (no colorvar handling),
`dash.ado:_dash_parse_plot_opts` `_dash_pending` block.

*Evidence:* the Appendix C item; the string counts and the security check in TR-17.8. See
TR-17.8's "measure before porting" note — the failing test, written first, sizes the fix.

---

**5. [functional · server · small]** *(origin: 05-04; source: `REMAINING.md` Appendix C)*

> `xsize()` and `ysize()` are honoured by DashRenderer and silently ignored in server
> mode, and neither is on the graph `_dash_pending` list. S10 is marked done for them on
> the strength of the standalone path only. Fix: carry xsize/ysize into the emitted app's
> `figure(width=, height=)` computation, or list them as pending-for-server.

*Where:* `dash_render.py:ServerAppBuilder` (figure sizing in the emitted source),
`dash.ado:_dash_parse_graph_opts` `_dash_pending` block.

*Evidence:* the Appendix C item; the standalone implementation and the emitted kwargs in
TR-17.9; and the deliberate omission from `_dash_pending` recorded in the comment block
at `dash.ado:633-641`, quoted under `## Why this phase exists`. Related Appendix C
finding, same comment block: *"xtick(), ytick(), xsize() and ysize() are serialized, emit
NO note, and are never read by the generated `bokeh serve` app"* — the `xtick`/`ytick`
half of that is owned by Phase 16.

---

**6. [functional · stata · small]** *(origin: ultraplan section S04, task 04-03; source:
`REMAINING.md` main body)*

> Add `T(string) B(string) L(string) R(string)` to `_dash_parse_plot_opts`'s syntax
> block. The folding code at `dash.ado:534-537` is already written and becomes live once
> they are declared.

*Where:* `dash.ado:_dash_parse_plot_opts`, `dash.ado:534-537`.

*Evidence:* the 04-03 row of `REMAINING.md`'s "17 DONE claims the adversarial pass
overturned" — *"`T() B() L() R()` never added to `_dash_parse_plot_opts`, so the folding
code at `dash.ado:534-537` is dead"*. Confirmed in the tree: declared at
`dash.ado:301-302` in the graph block, absent from the plot block; the fold and its
explanatory comment are quoted under `## Why this phase exists`.

---

## Test plan

Project rule 8 governs the order: **all six items are reported defects, so each one's
regression test is written first, must fail against HEAD, and must pass after the fix.**
Rule 4 governs breadth: every function this phase adds or changes gets a unit test. Each
test below is followed by its **mutation** — the specific edit that must kill it, which is
how it is proven non-vacuous.

### Harnesses that already exist and must keep passing

| file | what it gives this phase |
|---|---|
| `test/test_option_surface.cscript` | O2-01 (every command in `test/fixtures/twoway_corpus.do` returns rc 0) and the accept-and-report contract O2-03…O2-07. `REMAINING.md`: *"test/test_option_surface.cscript checks only rc 0 (O2-01/02) and the accept-and-report reporting contract (O2-03..O2-07)"* — no serialization assertion exists yet |
| `test/test_unsupported_report_is_true.py` | `PLOT_VALUES` (two values + a `ptype` per pending option), `_pending()` (`:132`, parses the `_dash_pending` blocks straight out of `dash.ado`), `_render()` (`:162-178`, hashes a rendered dashboard), `TestTheListIsCoveredAndHonest` |
| `test/fixtures/rejected_options.json` | 115 `rejected_options` records — `option`, `takes_argument`, `disposition`, `reason`, and per-record `probes` carrying a real `dash_command`. All 69 are present. Also `accepted_but_discarded` (9 records with `value_in_spec_json`), the shape a round-trip assertion can copy |
| `test/test_abbreviations.cscript` | the A7 collision guard, driven from `test/fixtures/abbrev_truth.json` |
| `test/test_mode_parity.py` | `CORPUS`, `_glyph_profile`, `_annotations`, `_chrome`, `TestTheTwoModesAgree` — the standalone/server property comparison. `REMAINING.md` records its blind spots: *"corpus covers 17/36 types, no `by()`/KPI/filter/`link()`/`tabs()`"* |
| `test/test_colorvar_legend.py` | the standalone colorvar behaviour to mirror (continuous `ColorBar`, discrete `Legend`, scheme chrome). Contains no `ServerAppBuilder` reference |
| `test/test_geometry.py` | `test_xsize_and_ysize_set_the_ratio`, `test_xsize_alone_keeps_the_scheme_ysize` — standalone only |
| `test/test_layout_facets.py` | facet layout coverage; standalone only (not among the 22 test files that mention `ServerAppBuilder`) |

### E17.A — The declaring half (items 1, 6)

**Write first (must fail today):**

1. `test/test_option_surface.cscript` — new check **O2-08**, "every 'implement' option is
   accepted, serialized with its value, and reported as ignored pending its section",
   which is 05-04's own `<verify>` clause. Drive it from
   `test/fixtures/rejected_options.json` so it cannot go stale: for each record whose
   `disposition` starts `implement-`, run the record's `probes[0].dash_command`, build the
   spec, and assert (a) rc 0, (b) the canonical option name is a key in the spec JSON with
   the typed value for argument-taking options and its own name for flags, (c) the name
   appears in the ignoring note while its section is pending. **Fails today for all 69** —
   they never reach the spec.
   *Mutation:* delete any one of the 69 from the generator's `GRAPH`/`PLOT` list and
   re-splice — O2-08 must fail naming exactly that option.
2. `test/test_option_surface.cscript` — new check **O2-09** for item 6: build
   `dash scatter mpg weight, t("Top") name(g1)` and
   `dash scatter mpg weight, t1title("Top") name(g1)` and assert the two spec JSONs agree
   on `t1title`; repeat for `b`/`b1title`, `l`/`l1title`, `r`/`r1title`. **Fails today** —
   the four names fall through the plot block's `*` catch-all.
   *Mutation:* remove `T(string)` from the plot syntax block again — the `t()` case must
   fail while the other three still pass, proving the check tests four things and not one.

**Unit tests (rule 4):**

3. New `test/test_option_inventory.py` — pure Python, no Stata, so it runs in the pytest
   suite:
   - `test_every_implement_dispositioned_option_is_in_the_inventory` — read the
     `disposition` field of every record in `test/fixtures/rejected_options.json`, import
     `GRAPH`/`PLOT` from `scripts/regen_option_surface.py`, and assert no
     `implement-*` option is missing from the union.
   - `test_every_pending_option_carries_its_owning_section` — assert each of the 69 has a
     non-`None` section tag, and that the tag matches the fixture's disposition
     (`implement-S07` → `S07`, `implement-S09-*` → `S09`, `implement-S10` → `S10`), or is
     `IGNORE` if the project took route (b) from §2.
   - `test_flag_options_are_declared_as_flags` — for every record with
     `takes_argument: false`, assert the name is in the generator's `FLAGS` set: the 13 are
     `adjust` `atobs` `discrete` `logit` `mean` `nofit` `noweight` `colorfillonly`
     `colorkeysrange` `colorvarminmax` `headlabel` `mwidth` `nodropbase`.
   - `test_the_declarations_reached_dash_ado` — parse the two `syntax` blocks out of
     `dash.ado` and assert every inventory name is declared in the block its list assigns
     it to, with graph names additionally present in the plot block (splice step 3) and in
     all four propagation loops (step 6).
   *Mutation:* drop `mlabformat` from `PLOT` — the first, second and fourth tests must
   fail; move `adjust` out of `FLAGS` — the third must fail.
4. `test/test_unsupported_report_is_true.py` — extend `PLOT_VALUES` with two values and a
   `ptype` for each of the 69 (values lifted from the fixture's probes, e.g.
   `tlabel` → `2000m1(12)2004m1` / `2001m1(6)2004m1` on `tsline`, `mlabformat` →
   `%9.0fc` / `%9.2f` on `scatter`, `gap` → `10` / `30` on `histogram`).
   `test_every_pending_option_is_covered_here` then passes, and the two-values-same-hash
   assertions prove BR-17.4: serializing changed nothing anyone can see.
   *Mutation:* make `DashRenderer` read one newly serialized key (e.g. apply `gap` to the
   histogram) — the hash comparison for that option must fail, which is what will happen,
   correctly, when Phase 19/20/21 implements it and removes it from `_dash_pending`.
5. `test/test_abbreviations.cscript` — the A7 collision guard must still pass after the
   inventory grows, and a new check A8 asserts that for each of the 69 the *declared*
   minimum is accepted (`dash scatter mpg weight, <min>(...)` returns rc 0 **and** the
   canonical key reaches the spec).
   *Mutation:* lengthen any declared minimum by one letter — A8 must fail for that option.

**Integration / cscript:**

6. `test/test_conformance.cscript` — unchanged expectations: zero `r(198)`, zero dropped
   series, zero dropped graphs across the conformance corpus. This is the BR-17.1 guard.
7. `test/test_option_report_paren.cscript` — must still pass, proving the reporter
   survived the inventory change (BR-17.11). Add a grep-style assertion that `dash.ado`
   contains `sreturn local _pending` at both levels; `REMAINING.md` records that a naive
   regeneration takes both away.
8. `test/test_examples_run.cscript` — all 12 example do-files still run with rc 0.

### E17.B — Nothing accepted is silently dropped (items 2, 4, 5)

**Write first (must fail today):**

9. `test/test_graph_options.py` — `test_saving_is_either_honoured_or_reported`: build a
   spec carrying `graph_options["saving"]` and assert that either the named file is
   written or `saving` appears on a pending list parsed out of `dash.ado` (reuse
   `_pending()` from `test_unsupported_report_is_true.py`). **Fails today** — neither is
   true.
   *Mutation:* remove `saving` from the pending block after the fix — the test must fail.
10. New `test/test_server_colorvar.py` — mirror of `test/test_colorvar_legend.py` against
    `ServerAppBuilder`: build the app source from a spec with
    `{"colorvar": "rep78", "colpalette": "viridis"}`, exec it, call `make_document`, and
    assert a `LinearColorMapper`/`CategoricalColorMapper` over `rep78` with the palette the
    standalone figure uses — or, if the project takes the note route, assert the family is
    named on the plot `_dash_pending` list and that the note fires in server mode.
    Parametrize over the five family members plus `colpalette`. **Run this before writing
    any port**: TR-17.8 explains why its result decides the size of item 4.
    *Mutation:* change the emitted palette key from the spec's `colpalette` to a constant —
    the palette assertion must fail.
11. New `test/test_server_colorvar.py::test_a_hostile_colorvar_never_reaches_the_source` —
    `colorvar("rep78'; import os; os.system('id')#")` must not appear in the generated app
    source, and the build must not raise. This is the CLAUDE.md rule 16 case for item 4 and
    it has no equivalent today.
    *Mutation:* delete the `re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", varname)` guard on the
    server path — the test must fail.
12. `test/test_server_build_options.py` —
    `test_xsize_and_ysize_shape_the_served_figure`: same spec through both renderers,
    asserting the served figure's ratio matches the standalone one that
    `test/test_geometry.py::test_xsize_and_ysize_set_the_ratio` already pins (`xsize(6)
    ysize(4)` → 1.5), or that both names are on the graph pending list. **Fails today** —
    `xsize` and `ysize` occur 0 times in the emitted source.
    *Mutation:* after the fix, invert the ratio in the emitted computation — the test must
    fail; and assert the `<= 0` case still warns rather than raising, matching
    `dash_render.py:9231-9241`.

**Unit tests (rule 4):**

13. `test/test_server_build_options.py` — `test_xsize_alone_keeps_the_scheme_ysize` in
    server mode, mirroring the standalone measurement `REMAINING.md` and the source both
    record (*"xsize(9) alone under stcolor gives 4.5 x 9"*).
14. New `test/test_option_inventory.py::test_no_declared_option_is_silently_dropped` — the
    narrow, phase-local form of the converse test Phase 18 will generalise: for the four
    families this phase touches (`saving`, the colorvar family, `xsize`/`ysize`, and the
    faceted plot options), assert each is either observable in the output of the mode under
    test or named on a pending list.
    *Mutation:* remove `saving` from both the renderer and the pending list — the test must
    fail.

**Integration / cscript:**

15. `test/test_serve_options.cscript` and `test/test_e2e_serve.cscript` — extend the served
    walk with a `colorvar()` command and an `xsize()`/`ysize()` command; assert rc 0, that
    the app builds, and that the note the user sees at the Stata prompt matches what the
    served app actually did.

### E17.C — The faceted branch honours its options (item 3)

**Write first (must fail today):**

16. New `test/test_server_facet_options.py::test_the_facet_branch_honours_plot_options` —
    build one spec twice, once with `by()` and once without, through `ServerAppBuilder`;
    exec both apps; and assert the facet figures carry the same `marker`, `size`,
    `fill_alpha`, `line_color`, `line_width` and `LabelSet` presence as the unfaceted
    figure for `msymbol`, `msize`, `malpha`, `jitter`, `mlabel`, `mlcolor`, `mlwidth`.
    **Fails today on all seven** — the branch reads `lcolor`/`mcolor` only.
    *Mutation:* re-hardcode `size=6` in the facet scatter call — the `msize` assertion must
    fail on its own, proving the test discriminates per option rather than passing on one
    aggregate.
17. New `test/test_server_facet_options.py::test_the_facet_branch_has_no_glyph_calls_of_its_own`
    — parse the emitted source with `ast`, walk the facet loop, and assert no `ptype ==`
    branch body calls a Bokeh glyph method on `_fac_fig` directly. This states 15-03's
    `<verify>` clause for the facet half behaviourally.
    *Mutation:* re-inline any one facet branch — the test must fail.

**Unit tests (rule 4):**

18. `test/test_mode_parity.py` — add a `by()`-bearing entry to `CORPUS` so the standing
    standalone/server property comparison covers the faceted path at all; `REMAINING.md`
    records that it covers *"no `by()`/KPI/filter/`link()`/`tabs()`"* today. Widening the
    corpus in general is Phase 08's deliverable; this is the one row item 3 needs.
    *Mutation:* revert item 3 — the new corpus row must fail.
19. `test/test_glyphs.py` — assert `GlyphMapper.map_*` is call-compatible with the argument
    shape the facet loop will use (`fig, source, yvar, xvar, opts, view=, color_idx=`),
    the same shape the unfaceted branch already uses at `dash_render.py:14090-14092`.

**Integration / cscript:**

20. `test/test_e2e_serve.cscript` — a served, faceted dashboard with marker options;
    assert rc 0 and that the document reports the expected number of figures and
    renderers.

### Suite-level obligations (project rule 5)

Before any commit: pull local `main`, run the full pytest suite and the full certification
suite from `test/` with `arch -arm64`, and set `$dash_nobrowser` for every Stata run that
builds a dashboard. At HEAD the suite stands at **3,498 passed / 37 skipped; 25/25
cscripts** — a skip is not a pass, and the new tests must appear as passes. Fix and re-run
until green.

---

## Definition of done

A reviewer can tick every line below.

**E17.A — the declaring half**

- [ ] All 69 options appear in `scripts/regen_option_surface.py`'s `GRAPH` or `PLOT` list,
      each with an owning section tag (`S07` / `S09` / `S10`, or `IGNORE` if route (b) was
      chosen), and the allocation matches TR-17.2.
- [ ] The 13 argument-less options are in `FLAGS`; the numlist/label-bearing ones are in
      `ASIS`.
- [ ] `dash.ado`'s two `syntax` blocks declare all 69; the four propagation loops
      (`:1125`, `:1395`, `:1411`, `:1465`) and `_dash_plot_opts_to_json` (`:854`) carry the
      new names.
- [ ] Every one of the 69 round-trips: the probe command from
      `test/fixtures/rejected_options.json` puts the option's value in the spec JSON under
      its canonical name.
- [ ] Every one of the 69 is on a `_dash_pending` list and named in the ignoring note.
- [ ] `PLOT_VALUES` in `test/test_unsupported_report_is_true.py` covers all of them, and
      both directions of that file pass.
- [ ] `T(string) B(string) L(string) R(string)` are declared in `_dash_parse_plot_opts`
      and the fold at `dash.ado:534-537` demonstrably fires.

**E17.B — nothing silently dropped**

- [ ] `saving()` is either honoured or on the graph `_dash_pending` list *and* tagged in
      `scripts/regen_option_surface.py:GRAPH`.
- [ ] The `colorvar` family behaves in server mode as in standalone, or is reported as
      pending for server mode; either way the identifier check from
      `dash_render.py:3021-3022` runs on the server path.
- [ ] `xsize()`/`ysize()` shape the served figure with standalone's precedence and its
      `<= 0` rejection, or are on the graph pending list for server mode.

**E17.C — the faceted branch**

- [ ] The facet loop draws through the copied `GlyphMapper`; no `ptype` branch in it calls
      a Bokeh glyph method directly.
- [ ] `msymbol`, `msize`, `malpha`, `jitter`, `mlabel`, `mlcolor`, `mlwidth` produce the
      same glyph properties with and without `by()` in server mode.
- [ ] `size=6`, `width=0.8` and the bare `line_width=_SCHEME_LINE_WIDTH` no longer appear
      as hardcoded constants in the facet branch.

**Cross-cutting**

- [ ] Rule 8 satisfied: for each of the six items there is a named test that was observed
      failing before the fix and passing after, and each has a recorded mutation that kills
      it.
- [ ] Rule 4 satisfied: every function added or changed has a unit test.
- [ ] `test/test_option_surface.cscript` O2-01 still passes; the 115-option probe still
      shows **0 rejections**.
- [ ] `dash.ado` still contains `sreturn local _pending` and `sreturn local _unknown` at
      both levels; `level(150)` still exits 198 from Stata.
- [ ] No new JSON is assembled by hand; every new key flows through `_dash_json_str`.
- [ ] Full pytest suite and all cscripts pass with honest skips; the 12 examples run.
- [ ] `REMAINING.md` is unmodified.
- [ ] Committed on a feature branch with the merge command supplied, never straight to
      `main`, and with no mention of the assistant in the message.

---

## Risks and sequencing notes

**1. The generator is a loaded gun, and item 1's instruction is to fire it.** Item 1 says
"regenerate". `REMAINING.md` says a regeneration at HEAD deletes the `level()` validation
block, both `_dash_pending` accumulations, both `sreturn local _pending`/`_unknown` lines,
`hover` from all four propagation loops, and every alias fold including the `t/b/l/r`
ladder this phase depends on — and that the committed `dash.ado` already carries a
double-applied splice (four copies of the generator banner, the alias ladder twice in
`_dash_parse_graph_opts`). Two ways to sequence around it:

- **Preferred:** pull Phase 18's generator items forward — de-duplicate the splice markers,
  make the splice idempotent, un-hardcode `REPO`, move the `json.dump` before the
  overwrite — then do item 1 as designed. The index orders 18 after 17 by dependency of
  *content*, not of tooling.
- **Fallback:** extend the two `syntax` blocks, the JSON key list and the four propagation
  loops by hand, with a line-by-line diff review against what the generator *would*
  produce, and land the generator fix in Phase 18 immediately after. This keeps the phases
  in index order at the cost of one careful diff.

Either way: snapshot `dash.ado` before touching it and diff afterwards for the six
constructs named above. A regeneration that silently disables 05-03's reporter would make
every accept-and-report test in the suite vacuously... still pass, because they test the
*note*, not the channel — which is exactly why the grep assertion in test 7 exists.

**2. The abbreviation half is Phase 18's and this phase will feel it.** With no
`abbrev_truth.json` entry, `base_min()` falls back to the full name, so the 69 land as
all-caps declarations. That is not a regression (an abbreviated use still falls through the
catch-all and is reported), but it reproduces the `fxsiz`/`fysiz` defect on 69 more
options, and `REMAINING.md` explicitly rescopes the probe to **71** options. Plan for the
probe to run in Phase 18 and for a second, mechanical regeneration to shorten the minimums
then. Also expect `resolve_minimums()`'s ambiguity assert to fire: `REMAINING.md` warns
that "adding these names with real measured minimums may trip that assert and force longer
minimums than existing dash do-files use" — collisions to watch are
`mlab*` (`mlabangle` `mlabformat` `mlabstyle` `mlabtextstyle` `mlabvposition` against the
existing `mlabel` `mlabcolor` `mlabsize` `mlabposition` `mlabgap` `mlabwidth`),
`color*` (11 new names against the existing `colorvar` family) and `d*`
(`dcolor` `dfcolor` `dlalign` `dlcolor` `dlstyle` `dlwidth` `dotextend` `dsize` `dstyle`
`dsymbol` against `degree` `density`).

**3. Items 3, 4 and 5 sit on Phase 05/06's lever.** Item 3's fix *is* the facet half of
15-03's collapse, which Phase 06 owns for plot-type coverage. Doing item 3 by delegating to
`GlyphMapper` discharges both halves at once; doing it by teaching the inline ladder seven
more option keys discharges neither and will be undone by Phase 06. Coordinate: if Phase 06
is running, item 3 belongs to whoever touches the facet loop first, and the other reviews.
Item 4 is in the same position — TR-17.8 records that `GlyphMapper` is copied into the app
whole, so the colorvar port may be a call site rather than a port. Measure with test 10
before writing code.

**4. The (a)/(b) decision changes the owning-section tags, not the work.** `REMAINING.md`
§2 leaves the choice to the user and warns it "sizes everything after it". This phase is
written to be correct under both: declare, serialize, report. Under (b) the tag for a
re-dispositioned option becomes `IGNORE` and it stays on the pending list permanently —
which the test in item 4 of the E17.A unit block checks against the fixture's disposition,
so if the decision is taken mid-phase, the fixture and the inventory must be updated
together or that test will correctly fail.

**5. Serializing 69 options makes the spec JSON wider on every build.** All of them are
short scalars and all flow through `_dash_json_str`, so the cost is bounded, but the spec
is the transport between Stata and Python: watch `test/test_filter_payload_size.py` and
`test/test_dataset_size_warning.py` for any size assertion that tightens unexpectedly.

**6. Do not extend the fifth, dead serializer.** `_dash_graph_opts_to_json`
(`dash.ado:891`) looks like the obvious place to add graph keys and is not maintained by
the generator; `REMAINING.md` calls it "a loaded gun for the next developer who reaches for
the obvious-looking serializer". Deleting it or wiring it into the generator is Phase 18's
item, not this one's — but if a graph option added here appears to need it, that is the
signal that the propagation loops were missed instead.
