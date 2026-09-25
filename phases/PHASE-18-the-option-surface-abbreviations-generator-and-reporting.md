# Phase 18 — The option surface: abbreviations, generator and reporting

**Purpose.** Phase 17 declares and serializes the 69 options that reach `dash.ado` only
through the trailing `*` catch-all. This phase supplies the three things that work needs in
order to be correct, repeatable and honest — and fixes the defects each of them has today.
**First, the abbreviations are unmeasured:** none of the 69 has an entry in
`test/fixtures/abbrev_truth.json`, so 05-04's "with the correct minimum abbreviation per
S04's truth table" clause cannot be satisfied for any of them, and three options 05-04
*already* declared (`bwidth`, `at`, `jseed`) plus `fxsize`/`fysize`/`scale` had their
minimums guessed rather than measured — one of those guesses, `bw`, silently hijacks a legal
`twoway` abbreviation and throws a user's kernel bandwidth away. **Second, the generator that
owns those declarations cannot safely be run:** `scripts/regen_option_surface.py` is the
procedure `dash.ado`'s own block comment tells a developer to follow, yet re-running it
deletes the `level()` validation, both `_dash_pending` accumulations and both `sreturn local
_pending` lines — which kills 05-03's reporter outright — and its splice has *already*
double-applied in the committed file. **Third, the report those declarations feed is not an
inventory:** it echoes the raw token the user typed rather than the canonical option name, it
is computed before the renderer is chosen so it says nothing about server-mode drops, and no
test asserts the serialization half of 05-04's `<verify>` or its converse. Nothing in this
phase implements an option's *behaviour* — that is Phases 19 through 22. This phase makes the
ground under them measured, regenerable and truthful.

---

## At a glance

| | |
|---|---|
| **Items** | 15 (numbered 1–15 below, exactly as handed over) |
| **Functional vs deliverable** | 6 functional (2, 4, 7, 8, 9, 10) · 9 deliverable (1, 3, 5, 6, 11, 12, 13, 14, 15) |
| **Effort mix** | 8 × small · 7 × medium · 0 × large |
| **Renderers touched** | `stata` (`dash.ado`, `scripts/`, `test/fixtures/`) on 12 items · `server` (`ServerAppBuilder`) on item 8 · `both` on items 10 and 11 |
| **Ultraplan tasks discharged** | **05-04** — its abbreviation clause ("with the correct minimum abbreviation per S04's truth table"), its grouping-comment clause ("Group them in the source with a comment naming the owning section"), and its `<verify>` ("every 'implement' option is accepted, serialized with its value, and reported as ignored pending its section"). **S05** — 05-01's five missing corpus probes (item 15). Also repairs the S04 fixture that 05-04 depends on. |
| **Not discharged here** | Declaring and serializing the 69 themselves (**Phase 17**, item 1 there). Implementing any of them — S07 (**Phase 19**), S09 axes/text (**Phase 20**), S09 style (**Phase 21**), S10 geometry (**Phase 22**). The help rewording 05-06 asks for (**Phase 30**). |
| **Depends on** | **Phase 17.** Items 1, 3 and 5 are written against the 69 that Phase 17 declares; items 2, 9 and 13 must land *before* Phase 17 regenerates, because Phase 17's stated procedure is "add each to `GRAPH`/`PLOT` … regenerate". See *Risks and sequencing notes* — the intra-phase ordering matters more here than the inter-phase ordering. |
| **Unblocks** | **Phases 19, 20, 21 and 22.** Each implements a family of the options this phase makes reachable, measured and reported; each needs the converse test (item 11) to prove an option came off the pending list because it works, not because someone deleted a line. |
| **Source of items** | Items 1–6: `REMAINING.md` Appendix B, `05-04`. Items 7–14: `REMAINING.md` Appendix C, `05-04` (12 further items). Item 15: `REMAINING.md` main body, the *17 DONE claims the adversarial pass overturned* table, row `05-01`. |

---

## Why this phase exists

### 1. What the audit measured — `REMAINING.md` §2, "Blocker — the option surface" [S05-04, S07, S09, S10]

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

Confirmed at HEAD: `test/fixtures/rejected_options.json` carries `"schema_version": 1`,
`"plan_task": "05-01"`, a `rejected_options` list of **115** entries and a `probes` list of
**299**.

### 2. What the audit measured — `REMAINING.md` Appendix A, `05-04 · PARTIAL`

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
> **Remaining: declare and serialize these 69.** […]
>
> Each needs its S04 minimum abbreviation, a serializer entry, and a
> `_dash_pending` line so it stays reported until its section lands.
>
> > Corrects §2 of this file, which put the figure at 92 by treating every
> > reported option as undeclared. 27 of those are declared and serialized
> > already, and are reported because `_dash_pending` correctly says they are
> > awaiting their section.

The two figures in that correction — **27** in Appendix A and **23** in Appendix B (item 6
below) — are both right and describe different denominators. §2's table reports **96**
options accepted-and-reported, of which **4** are the intended accept-and-report set, leaving
**92** implement-dispositioned. Appendix A subtracts the 69 undeclared from all 96 → **27**.
Item 6 subtracts the 69 from the 92 implement-dispositioned → **23**, which is exactly the 27
less the 4 permanent accept-and-report options. Item 6's list of 23 names, counted, is 23.
No measurement is in dispute; only the denominator.

The "Each needs its S04 minimum abbreviation" clause is what makes this phase a prerequisite
rather than a postscript, and it is the first thing that turns out not to be available.

### 3. The abbreviation truth set does not cover what the generator declares

`test/fixtures/abbrev_truth.json` carries **93** entries under `options`. Measured at HEAD —
`fxsize`, `fysize`, `scale`, `bwidth`, `at` and `jseed` all return `None`; none of the 69
Phase 17 declares has an entry either. What fills the hole is guesswork in the generator:

```python
# scripts/regen_option_surface.py:22-30
DASH_ONLY_MIN = {
    "bgcolor": "bgc", "plotbgcolor": "pbgc", "link": "link", "filter": "filt",
    ...
    "bwidth": "bwidth",
}
```

```python
# scripts/regen_option_surface.py:104-107
HISTORICAL_MIN = {
    "aspectratio": "asp", "name": "nam", "jitter": "jit", "colorvar": "cv",
    "mlabgap": "mlg", "barwidth": "bw", "bwidth": "bwid",
}
```

```python
# scripts/regen_option_surface.py:110-117
def base_min(name):
    entry = TRUTH_OPTS.get(name)
    mn = entry.get("min_abbrev") if entry else None
    if not mn:
        mn = DASH_ONLY_MIN.get(name, name)
    if not name.startswith(mn):
        mn = name  # measured minimum is not a prefix -> require the full name
    return mn
```

Two consequences, both measured by the adversarial pass and reproduced here:

- **`bw()` is hijacked** (item 10). `HISTORICAL_MIN` hands `bw` to `barwidth` and pushes
  `bwidth` out to `bwid`. A pasted `twoway kdensity mpg, bw(2)` therefore sets `barwidth` and
  the kernel draws at the default bandwidth, with no note. REMAINING.md calls this "the one
  05-04 abbreviation decision that is not a superset of twoway — it changes the meaning of a
  working command."
- **`fxsize()`/`fysize()` are declared too long** (item 7). `dash.ado:294` and `:511` declare
  `FXSIZE(string)` / `FYSIZE(string)` — all-caps, i.e. the full name is required — while
  twoway's measured minimum is `fxsiz`/`fysiz`. `twoway ..., fxsiz(50)` falls through the `*`
  catch-all: rc 0, a note naming a non-existent option `fxsiz()`, value gone.

`scale` is the third declared option with no truth entry and needs no change — twoway rejects
`sca()`/`scal()` too, so the full name is correct there. REMAINING.md's conclusion: **"The
abbreviation-probe item should be scoped to 71 options, not 69."**

And the guard that should have caught `bw` cannot: `test/test_abbreviations.cscript:217` sets
`RES = D["abbrev_resolution"]` and the A7 collision block iterates only that table
(`:435-443`), so a collision the generator *invents* is invisible to it by construction.

### 4. The generator is the documented procedure and it is not safe to run

`dash.ado`'s own banner tells the developer what to do:

```
    // NOTE: this block is generated by scripts/regen_option_surface.py
    // from test/fixtures/abbrev_truth.json.  Do not hand-edit; the same
    // option list appears in several places and the generator keeps them
    // in step.  Capitalised letters are the minimum abbreviation, measured
    // against real twoway rather than guessed.
```

Confirmed at HEAD, that banner appears **four** times — `dash.ado:266`, `:271`, `:460`,
`:465`, i.e. twice per syntax block — and the `t()/b()/l()/r()` alias-fold `if`-ladder appears
**twice** inside `_dash_parse_graph_opts` (which spans `:263-457`), at `:316` and `:340`, with
two different comment headers. The splice has already double-applied (item 13). Behaviour is
unchanged because both copies run, but the file no longer matches what the generator would
produce.

Re-running it on that file destroys working code. REMAINING.md's two lists, combined:

| what a regen deletes | where, confirmed at HEAD | consequence |
|---|---|---|
| `HOVer(string)`, `T()/B()/L()/R()` title aliases, `PBGC/XLA2/XSC2/XTI2/YLA2/YSC2/YTI2`, `BINS(string)` | both syntax blocks | hand-added declarations vanish |
| `sreturn local hover`, `sreturn local g_hover` | `dash.ado:750` | `hover()` stops reaching the renderer |
| `hover` in all four graph propagation loops | `dash.ado:1129`, `:1399`, `:1415`, `:1469` (loop headers at `:1125`, `:1395`, `:1411`, `:1465`) | same, on every promotion path |
| the whole `level()` validation block | `dash.ado:549-561` | `level(150)` becomes a Python exception inside the renderer |
| the entire plot-level `local _dash_pending` accumulation | `dash.ado:593-641` (`local _dash_pending ""` at `:593`) | — |
| `local _dash_unknown` | `dash.ado:642` | — |
| `sreturn local _pending` / `sreturn local _unknown` | `dash.ado:770-771` | **after a regen the whole file contains zero `sreturn local _pending`, so 05-03's reporter is dead at BOTH levels** |
| every alias-folding `if` — `bins→bin`, `bw→barwidth`, `mlg→mlabgap`, `cv/colv→colorvar`, `pbgc→plotbgcolor`, `xla2/xsc2/xti2/yla2/ysc2/yti2`, `t/b/l/r→*1title` | `dash.ado:316`, `:340`, `:534-537`, `:562` and following | aliases stop resolving |

The `level()` block it deletes, verbatim at HEAD (`dash.ado:549-560`):

```stata
    if `"`level'"' != "" {
        capture confirm number `level'
        if _rc {
            display as error "level() must be a number between 0 and 100"
            exit 198
        }
        if `level' <= 0 | `level' >= 100 {
            display as error "level() must be between 0 and 100 (exclusive)"
            exit 198
        }
    }
```

It is also not runnable anywhere else. `REPO` is a hardcoded absolute path
(`scripts/regen_option_surface.py:17`), and the run order is destructive-before-reporting:

```python
# scripts/regen_option_surface.py:291-299
pending_lines = "\n".join(
    '    local _dash_pending_%s "%s"' % (n, s) for n, s in sorted(PENDING.items()))

open(REPO + "/dash.ado", "w").write(src)
print("\ndash.ado: %d -> %d chars" % (len(orig), len(src)))
print("graph options: %d  plot options: %d  pending: %d"
      % (len(GRAPH_NAMES), len(PLOT_NAMES), len(PENDING)))
json.dump({"graph": GRAPH_NAMES, "plot": PLOT_NAMES, "pending": PENDING},
          open("/tmp/dash-wf/b2/option_inventory.json", "w"), indent=1)
```

Two defects in nine lines: `pending_lines` is computed and **never spliced** — the
owning-section grouping comments 05-04 explicitly asks for are dead code (item 3) — and the
`json.dump` to a hardcoded `/tmp` path runs *after* `dash.ado` has already been overwritten,
so a missing directory leaves the repository mutated and the script traceback-ing (item 9).

### 5. The report is not an inventory

`_dash_report_ignored` (`dash.ado:1338`) receives `raw`, which its own comment describes as
mixing "bare option names (pending, from the declared set) with the verbatim text Stata could
not match (unknown, from the trailing `*`)". It cuts each token at its opening parenthesis and
echoes what is left:

```stata
    mata: _dash_option_names("raw", "_dash_optnames")
    local raw `"`_dash_optnames'"'
    ...
    display as text "dash: ignoring unsupported option(s):" as result `"`out'"'
```

So an abbreviated use of an *undeclared* option is reported under the prefix the user typed —
a name that does not exist in twoway's vocabulary and cannot be looked up in the help
(item 4). That is why the note cannot be trusted as an inventory today, and it is why
`fxsiz(50)` produces the nonsense note described above.

The note is also **mode-blind**. `_dash_pending` is computed in `dash.ado` before the renderer
is chosen. REMAINING.md's measured instances of options honoured in standalone and dropped in
server mode with no note: the `colorvar` family, `xsize`, `ysize`, every plot option under
`by()`, and the secondary-axis family. Four more are silent in *both* directions of the
contract — `xtick()`, `ytick()`, `xsize()`, `ysize()` are serialized, emit no note, and are
never read by the emitted server app (item 8). They were taken off the pending lists
deliberately, and the comment saying so is at `dash.ado:632-640`, verbatim at HEAD:

```stata
    // scheme(), xsize(), ysize(), xtick() and ytick() are NOT listed.  They
    // are twoway GRAPH-level options, and this program promotes them --
    // `sreturn local g_xsize' and friends just above, picked up by the
    // promotion loop in _dash_process_segment -- so however they are
    // written they reach the renderer and are honoured.  Naming them here
    // told a user who typed dash.sthlp's own example,
    //     dash scatter mpg weight, xsize(10) ysize(2)
    // that dash had ignored two options it had just applied.
```

The reasoning is sound for `DashRenderer` — `_resolve_aspect_ratio` reads them at
`dash_render.py:9228-9229` and the tick spec is consumed at `:9904-9912`. It is false for
`ServerAppBuilder` (`dash_render.py:12265`). The emitted app's axis loop, at
`dash_render.py:14012`, iterates two keys only:

```python
            "        for _axk, _axobj in (('xlabel', fig.xaxis), ('ylabel', fig.yaxis)):",
```

and the emitted `_fig_kw` construction (`dash_render.py:13839-13855`) honours only
`aspect_ratio` (`:13849`) plus the log axis types (`:13853-13854`). REMAINING.md's verdict:
"The auditor's `done_items[3]` concludes 'No declared implement-option is both unimplemented
and silent'; that holds for DashRenderer only" — and this is "precisely the defect class
05-04's `<done>` forbids ('nothing is silently dropped in the interim')".

### 6. No test asserts the half of 05-04's `<verify>` that matters

05-04's `<verify>`, from `.ultraplan/sections/section-05-option-surface.md:174`:

> Every "implement" option is accepted, serialized with its value, and reported as ignored
> pending its section.

Three clauses. What exists at HEAD:

| clause | test | verdict |
|---|---|---|
| accepted | `test/test_option_surface.cscript` O2-01/O2-02 (corpus walk at `:379`) | covered — rc 0 |
| **serialized with its value** | — | **nothing** |
| reported as ignored | `test/test_option_surface.cscript` O2-03…O2-07 | covered |

And `test/test_unsupported_report_is_true.py` tests exactly one direction. It reads the
pending names straight out of `dash.ado` (`_pending` at `:132`, via
`re.findall(r"_dash_pending' (\w+)\"", ...)`), then for each asserts that rendering with two
different values produces the same HTML (`:195-196` for plot options, `:212-214` for graph
options). Nothing asserts the converse — that every option dash *declares* either changes the
output or is named on `_dash_pending`. REMAINING.md: "That converse test is what would have
caught `saving()`, `xsize()`, `ysize()` and the colorvar family." The module also builds only
one renderer:

```python
# test/test_unsupported_report_is_true.py:178
        return _norm(dr.DashRenderer(str(sp), str(dp)).render())
```

`ServerAppBuilder` is never instantiated, "so it is blind to every server-mode gap by
construction" (item 11).

Finally, a fifth, dead, stale copy of the graph-option list sits at `dash.ado:891`,
`_dash_graph_opts_to_json`, which the generator does not maintain (item 12), and a fifth
serializer is exactly the drift the generator's own docstring says it exists to prevent:

```python
# scripts/regen_option_surface.py:3-7
dash.ado repeats the option list in five places (two syntax blocks, two sreturn
blocks, the plot-option JSON key list, and the graph-level propagation loops).
Keeping them in sync by hand is how they drifted.  This script is the single
source of truth; run it, don't hand-edit those blocks.
```

### 7. And the corpus the whole edifice rests on is missing five probes

From the main body's *17 DONE claims the adversarial pass overturned* table:

| task | what the refutation found |
|---|---|
| 05-01 | corpus missing probes for `at()`, `ciopts()`, `fitopts()`, `lineopts()`, `mlpattern()` |

Confirmed at HEAD: `grep` for `at(`, `ciopts(`, `fitopts(`, `lineopts(`, `mlpattern(` as
probe arguments in `test/fixtures/twoway_corpus.do` returns nothing. The corpus has the right
sections to hang them on — `// 13. marker_options` at `:329`, `// 17. fit plots: lfit / qfit
/ lfitci / fpfit` at `:383`, `// 18. smoothers: lowess / lpoly / mband / mspline` at `:409`,
`// 20. twoway kdensity` at `:440` — and the `dashprobe` helper at `:67-69` takes
`args id spec opts twextra`. Its output line format, from the fixture's own header:

```
id %|% twoway_rc %|% dash_rc %|% plotspec %|% options %|% twoway_only_extra %|% dash spec JSON
```

Three of the five — `at`, `ciopts`, `fitopts` — are names Phase 17 declares or that already
carry a `_dash_pending` line, so the corpus is silent about options this very phase is
reasoning over (item 15).

### 8. Confirmed at HEAD — the symbol map for this phase

Line numbers in `.ultraplan/sections/*.md` are stale (`dash_render.py` grew from ~10,455 to
~16,000 lines). Everything below was re-checked in the working tree at
`feature/batch4-interactive-layer`.

| symbol | file:line | note |
|---|---|---|
| `_dash_parse_graph_opts` | `dash.ado:263` | spans to `:457` |
| generated-block banner (graph) | `dash.ado:266`, `:271` | **duplicated** |
| `FXSIZE(string) FYSIZE(string)` (graph) | `dash.ado:294` | all-caps = full name required |
| `t/b/l/r → *1title` fold (graph) | `dash.ado:316`, `:340` | **duplicated** |
| `sreturn local t1title` | `dash.ado:431` | |
| `_dash_parse_plot_opts` | `dash.ado:458` | spans to `:778` |
| generated-block banner (plot) | `dash.ado:460`, `:465` | **duplicated** |
| `FXSIZE(string) FYSIZE(string)` (plot) | `dash.ado:511` | |
| `t/b/l/r` fold (plot) | `dash.ado:534` | dead — `T()/B()/L()/R()` undeclared here (Phase 17 item 6) |
| `level()` validation | `dash.ado:549-561` | deleted by a regen |
| `bw → barwidth` fold | `dash.ado:562` | the hijack |
| `local _dash_pending ""` (plot) | `dash.ado:593` | accumulation runs to `:641` |
| "scheme(), xsize(), … are NOT listed" | `dash.ado:632-640` | the deliberate omission |
| `local _dash_unknown` | `dash.ado:642` | |
| `sreturn local g_hover` | `dash.ado:750` | deleted by a regen |
| `sreturn local _pending` / `_unknown` | `dash.ado:770-771` | the reporter's only channel |
| `_dash_plot_opts_to_json` | `dash.ado:854` | maintained by the generator |
| `_dash_graph_opts_to_json` | `dash.ado:891` | **fifth, dead, unmaintained copy** |
| `_dash_report_ignored` | `dash.ado:1338` | |
| graph propagation loops | `dash.ado:1125`, `:1395`, `:1411`, `:1465` | `hover` at `:1129`, `:1399`, `:1415`, `:1469` |
| `_dash_optname_of` | `dash_parse.mata:932` | |
| `_dash_option_names` | `dash_parse.mata:945` | calls `_dash_optname_of` at `:981`, `:987` |
| `REPO = "/Users/billy/…/dash"` | `scripts/regen_option_surface.py:17` | hardcoded |
| `DASH_ONLY_MIN` | `scripts/regen_option_surface.py:22-30` | contains `"bwidth": "bwidth"` |
| `HISTORICAL_MIN` | `scripts/regen_option_surface.py:104-107` | contains `"barwidth": "bw"`, `"bwidth": "bwid"` |
| `base_min` | `scripts/regen_option_surface.py:112` | |
| `resolve_minimums` | `scripts/regen_option_surface.py:121` | asserts on ambiguity |
| `pending_lines` | `scripts/regen_option_surface.py:291` | computed, never spliced |
| `open(REPO + "/dash.ado", "w")` | `scripts/regen_option_surface.py:294` | the destructive write |
| `json.dump(..., "/tmp/dash-wf/b2/…")` | `scripts/regen_option_surface.py:298-299` | runs *after* the write |
| `abbrev_truth.json` `options` | `test/fixtures/abbrev_truth.json` | 93 entries; none for `fxsize`, `fysize`, `scale`, `bwidth`, `at`, `jseed` |
| `RES = D["abbrev_resolution"]` | `test/test_abbreviations.cscript:217` | what A7 iterates |
| A7 collision block | `test/test_abbreviations.cscript:435-443` | |
| O2-01…O2-07 | `test/test_option_surface.cscript:57-76` (header), `:379` (corpus walk) | |
| `PLOT_VALUES` | `test/test_unsupported_report_is_true.py:67` | |
| `_pending` | `test/test_unsupported_report_is_true.py:132` | scrapes `dash.ado` |
| `_render` / `DashRenderer` only | `test/test_unsupported_report_is_true.py:162` / `:178` | |
| `dashprobe` | `test/fixtures/twoway_corpus.do:67-69` | `args id spec opts twextra` |
| `class ServerAppBuilder` | `dash_render.py:12265` | everything after is emitted-app source |
| emitted `_fig_kw` | `dash_render.py:13839-13855` | `aspect_ratio` at `:13849` only |
| emitted axis loop | `dash_render.py:14012` | `(('xlabel', fig.xaxis), ('ylabel', fig.yaxis))` |
| `DashRenderer` xsize/ysize | `dash_render.py:9228-9229` | inside `_resolve_aspect_ratio` |
| `DashRenderer` xtick/ytick | `dash_render.py:9904-9912` | |

---

## Epics

Three epics, in the order they must be executed.

| epic | name | goal | items |
|---|---|---|---:|
| **18.A** | **Measured truth about twoway's option surface** | Every abbreviation and every disposition dash ships rests on a probe against real `twoway`, not on a hand-written guess. | 1, 7, 10, 14, 15 |
| **18.B** | **A generator that can be run twice** | `scripts/regen_option_surface.py` is idempotent, portable, non-destructive and complete, so "run the generator" is a safe instruction for the next developer — including Phase 17's. | 2, 3, 9, 12, 13 |
| **18.C** | **A report that is an inventory** | The `dash: ignoring unsupported option(s):` note names canonical options, tells the truth per render mode, and is guarded in both directions by tests. | 4, 5, 6, 8, 11 |

Epic 18.A produces the input the generator consumes; 18.B makes it safe to feed it; 18.C
proves the result. Running 18.B before 18.A would regenerate from a fixture that is still
wrong; running 18.A before 18.B would require a regen that destroys the reporter.

---

## User stories

### Epic 18.A — Measured truth about twoway's option surface

**US-18.A.1** — *As a Stata user pasting a `twoway` command into `dash`, I want every
abbreviation `twoway` accepts to mean the same thing in `dash`, so that a command I copied
does not quietly change meaning.*

> **Given** `twoway kdensity mpg, bw(2)`, where `bw` is a legal `twoway` abbreviation of
> `bwidth()`,
> **When** I run `dash kdensity mpg, bw(2) name(g1)` and build,
> **Then** the spec JSON carries `"bwidth":"2"` and not `"barwidth":"2"`, and the kernel is
> computed at bandwidth 2.

> **Given** `twoway scatter mpg weight, fxsiz(50)`,
> **When** I run the same command through `dash`,
> **Then** `fxsize` is accepted at the abbreviation `fxsiz`, its value reaches the spec, and
> no note names an option called `fxsiz()`.

**US-18.A.2** — *As a package maintainer, I want every option name the generator can emit to
have a measured minimum in the truth fixture, so that no declaration is ever a guess.*

> **Given** the generator's `GRAPH`/`PLOT` inventory, including the alias forms it invents,
> **When** `scripts/extract_abbrev_truth.do` has run,
> **Then** every name in that inventory has an entry in `test/fixtures/abbrev_truth.json`
> with `min_abbrev`, `probe_cmd` and an oracle — including `bwidth`, `at`, `jseed`, `fxsize`
> and `fysize`, and including the 69 Phase 17 declares.

> **Given** any token `dash` accepts,
> **When** the parity test runs it through both commands,
> **Then** either `twoway` rejects it (dash is a superset — allowed) **or** `twoway` resolves
> it to the **same** canonical option that `dash` does. Nothing else passes.

**US-18.A.3** — *As a package maintainer, I want the conformance corpus to probe every option
family the audit reasons about, so that a disposition is never assigned to an option nobody
measured.*

> **Given** `test/fixtures/twoway_corpus.do`,
> **When** it is run under `arch -arm64` from a scratch directory,
> **Then** `twoway_corpus_results.txt` contains lines for `at()` on `kdensity` and `lpoly`,
> `ciopts()` on `lfitci` and `lpolyci`, `fitopts()` on `lfitci`, `lineopts()` on `kdensity`
> and `mlpattern()` on `scatter`, each with a `twoway_rc`, a `dash_rc` and a disposition
> recorded in `test/fixtures/rejected_options.json`.

### Epic 18.B — A generator that can be run twice

**US-18.B.1** — *As a package maintainer following the instruction in `dash.ado`'s own banner,
I want running the generator to be a no-op when the inventory has not changed, so that I can
trust it with the file.*

> **Given** a clean working tree at HEAD,
> **When** I run `python3 scripts/regen_option_surface.py` and then `git diff --stat`,
> **Then** the diff is empty.

> **Given** a clean working tree,
> **When** I run the generator twice in a row,
> **Then** the second run changes nothing the first did not, the generated-block banner
> appears exactly **twice** in `dash.ado` (once per syntax block, not four times), and the
> `t/b/l/r` alias fold appears exactly once in `_dash_parse_graph_opts`.

**US-18.B.2** — *As a package maintainer, I want the generator to preserve the hand-written
code around its splice points, so that regenerating never silently removes a validation or a
reporting channel.*

> **Given** a regenerated `dash.ado`,
> **When** I grep it,
> **Then** `sreturn local _pending` and `sreturn local _unknown` each appear in **both**
> `_dash_parse_graph_opts` and `_dash_parse_plot_opts`; the `level()` validation block
> survives verbatim; `sreturn local g_hover` survives; `hover` is present in all four graph
> propagation loops; and every alias-folding `if` (`bins→bin`, `bw→barwidth` *as corrected by
> item 10*, `mlg→mlabgap`, `cv/colv→colorvar`, `pbgc→plotbgcolor`, the `*2` family,
> `t/b/l/r→*1title`) survives.

> **Given** `dash kdensity mpg, level(150)` after a regeneration,
> **When** I run it,
> **Then** Stata exits `198` with `level() must be between 0 and 100 (exclusive)`, and no
> Python traceback reaches the user.

**US-18.B.3** — *As a developer on any checkout, I want the generator to run from a fresh
clone without editing it, so that the documented procedure works off this machine.*

> **Given** a clone at an arbitrary path and no `/tmp/dash-wf/b2` directory,
> **When** I run `python3 scripts/regen_option_surface.py`,
> **Then** it locates the repository from its own file location (or an explicit argument),
> writes its inventory report to a path inside the repo or a path it creates, and either
> completes cleanly or fails **before** touching `dash.ado`.

**US-18.B.4** — *As a developer reading `dash.ado`, I want each declared option to carry the
section that owns it, so that I can tell at a glance what is wired up and what is waiting.*

> **Given** the two syntax blocks after a regeneration,
> **When** I read them,
> **Then** the options are grouped under comments naming their owning section — S06, S07,
> S09, S10, S11, or "permanently accept-and-report" — and `pending_lines` is no longer a dead
> variable in the generator.

> **Given** `dash.ado`,
> **When** I search for graph-option serializers,
> **Then** there is one maintained by the generator, not a fifth dead copy at `:891`.

### Epic 18.C — A report that is an inventory

**US-18.C.1** — *As a Stata user, I want the "ignoring unsupported option(s)" note to name
options I can look up in `help twoway_options`, so that the note tells me something I can act
on.*

> **Given** `dash scatter mpg weight, mlabel(make) mlabs(3) fxsiz(50)`,
> **When** the note is displayed,
> **Then** every name in it is a canonical option name (`fxsize()`, not `fxsiz()`), and no
> name in it is absent from twoway's vocabulary.

**US-18.C.2** — *As a `dash serve` operator, I want the note to tell the truth about the mode
I am rendering in, so that I do not ship a served dashboard that silently discards options the
standalone build honours.*

> **Given** a spec carrying `xtick(5(5)40)`, `ytick(...)`, `xsize(10)` and `ysize(2)`,
> **When** I build it through `ServerAppBuilder`,
> **Then** either the emitted app honours them, **or** the note names them as pending for
> server mode. Neither silent case remains.

**US-18.C.3** — *As a package maintainer, I want a test that fails the moment a declared
option becomes a silent no-op, so that the reporting contract cannot decay again.*

> **Given** the two syntax blocks as the source of declared names,
> **When** the converse test runs,
> **Then** for each declared option, either two different values produce different rendered
> output, or the option is named on the matching `_dash_pending` list. An option that is on
> neither side fails the test, naming itself.

> **Given** the same two directions,
> **When** they are run against `ServerAppBuilder` as well as `DashRenderer`,
> **Then** both renderers are covered and a server-only gap fails the suite.

**US-18.C.4** — *As a package maintainer, I want 05-04's `<verify>` asserted in full, so that
"serialized with its value" is a tested claim and not a hope.*

> **Given** `test/fixtures/rejected_options.json`,
> **When** the new O2-08 check runs each implement-dispositioned option through `dash` and
> inspects the emitted spec JSON,
> **Then** the option's key is present with the value supplied, **and** the option is named in
> the note, **and** the command returned rc 0 — all three clauses, for every option, driven
> from the fixture so it cannot go stale.

---

## Business requirements

| id | requirement | how it is tested |
|---|---|---|
| **BR-18.1** | A command that `twoway` accepts and `dash` also accepts must resolve to the same canonical option in both, or `dash` must reject it. `dash` may accept *more* than `twoway` (superset, permitted); it may never map an abbreviation to a *different* option. | `test/test_abbreviations.cscript` new A8 parity group |
| **BR-18.2** | No option's declared minimum abbreviation may be longer than the minimum real `twoway` accepts. | A8 + `abbrev_truth.json` completeness check |
| **BR-18.3** | Every option name the generator can emit — canonical and alias — has a measured entry in `test/fixtures/abbrev_truth.json`, with the probe command that produced it recorded. | `test/test_regen_option_surface.py::test_every_inventory_name_has_truth` |
| **BR-18.4** | Running `scripts/regen_option_surface.py` on an unchanged inventory produces a byte-identical `dash.ado`. | `test/test_regen_option_surface.py::test_generator_is_idempotent` |
| **BR-18.5** | Running the generator never removes hand-written code outside its splice regions: the `level()` validation, both `_dash_pending` blocks, both `sreturn local _pending`/`_unknown` pairs, `sreturn local g_hover`, `hover` in the four propagation loops, and every alias fold. | `test/test_regen_option_surface.py::test_regen_preserves_hand_written_blocks` |
| **BR-18.6** | The generator runs to completion from any checkout path with no pre-existing scratch directory, and fails before mutating the repository if it cannot. | `test/test_regen_option_surface.py::test_generator_is_path_independent` |
| **BR-18.7** | `dash.ado` contains exactly one copy of each generated block and one graph-option serializer. | `test/test_regen_option_surface.py::test_splice_markers_are_unique` |
| **BR-18.8** | Every declared option in `dash.ado` is annotated in the source with the section that owns it. | `test/test_regen_option_surface.py::test_every_declared_option_has_a_section_tag` |
| **BR-18.9** | The "ignoring unsupported option(s)" note names only canonical twoway or dash option names. | `test/test_option_surface.cscript` O2-09 |
| **BR-18.10** | No option `dash` declares may be silently dropped in **either** render mode: it either changes the rendered output or is named in the note for that mode. | `test/test_unsupported_report_is_true.py` converse test, run against both renderers |
| **BR-18.11** | Every implement-dispositioned option is accepted (rc 0), serialized into the spec with the value supplied, and named in the note until its section lands. | `test/test_option_surface.cscript` O2-08 |
| **BR-18.12** | The conformance corpus carries a probe, a `twoway_rc`, a `dash_rc` and a disposition for every option family the audit reasons about, including `at()`, `ciopts()`, `fitopts()`, `lineopts()` and `mlpattern()`. | `test/fixtures/twoway_corpus.do` + `rejected_options.json` regeneration |
| **BR-18.13** | The written record of the option gap states the measured figure (69 undeclared of 92 implement-dispositioned reported) rather than the superseded one. | review checklist, item 6 |
| **BR-18.14** | Nothing in this phase changes which options `dash` *honours*. Behaviour changes are confined to abbreviation resolution (items 7, 10) and to what the note says (items 4, 8, 11). | full `pytest` + 25-cscript certification suite green |

---

## Technical requirements

### 18.A — Measured truth

**TR-18.1 — Extend the S04 probe to the generator's whole inventory.**
`scripts/extract_abbrev_truth.do` today probes only names found in twoway's help under their
canonical spelling, which is why the alias/short-form surface the generator invents is
unprobed by construction. Extend it to iterate every name in
`scripts/regen_option_surface.py`'s `GRAPH` and `PLOT` lists, **plus** the alias forms
(`bins`, `bw`, `mlg`, `cv`, `colv`, `pbgc`, `xla2`, `xsc2`, `xti2`, `yla2`, `ysc2`, `yti2`,
`t`, `b`, `l`, `r`). Each new entry must carry the same shape as an existing one, e.g.
`barwidth` at HEAD:

```json
"barwidth": {
  "dash": {"accepts": false, "key": null,
           "probe_cmd": "dash scatter mpg weight, barw(...) name(zqdash)", "rc": 198},
  "full_name_cmd": "twoway bar mpg weight, barwidth(100) nodraw",
  "min_abbrev": "barw",
  "oracle": "gph-identity",
  "plottype_context": "bar",
  "probe_cmd": "twoway bar mpg weight, barw(100) nodraw",
  "probe_value": "100"
}
```

The `oracle` field must stay `gph-identity` — the resolution oracle the S04 fixture was built
with. Scope: the **71** options REMAINING.md names (the 69 undeclared plus `fxsize` and
`fysize`), plus `bwidth`, `at` and `jseed` which are declared with guessed minimums. `scale`
is explicitly out of scope: "twoway rejects `sca()`/`scal()` too, so the full name is correct
there."

**TR-18.2 — Expect `resolve_minimums()` to force longer minimums, and record which.**
`resolve_minimums()` (`scripts/regen_option_surface.py:120`) asserts on ambiguity at `:137`
(`assert not ambiguous(mins), "measured minimums are already ambiguous"`). REMAINING.md's measured example of
the collision this will force: `dash scatter mpg weight, mlabel(make) mlabs(3)` currently
yields `"mlabsize":"3"`, because dash declares fewer options than twoway — twoway also has
`mlabstyle` and `mlabtextstyle`, both of which appear in the 69. Declaring them makes `mlabs`
ambiguous. Every minimum that lengthens as a result must be listed in the commit message and
checked against `test/fixtures/conformance_corpus.txt` and the twelve example do-files, because
existing dash do-files may use the shorter form.

**TR-18.3 — `fxsize`/`fysize`: emit `FXSIZe`/`FYSIZe`.**
After the probe adds `"min_abbrev": "fxsiz"` / `"fysiz"`, `base_min()` returns the measured
value and `syntax_block` emits mixed case at `dash.ado:294` (graph) and `:511` (plot),
replacing today's `FXSIZE(string)` / `FYSIZE(string)`. No `DASH_ONLY_MIN` entry is needed —
adding one would defeat the measurement.

**TR-18.4 — `bwidth`: undo the `bw` hijack.**
Three coordinated edits. (a) Delete `"barwidth": "bw"` from `HISTORICAL_MIN`
(`scripts/regen_option_surface.py:104-107`); `barwidth` then falls back to its measured
`abbrev_truth` minimum `barw`. (b) Delete `"bwidth": "bwid"` from `HISTORICAL_MIN` and
`"bwidth": "bwidth"` from `DASH_ONLY_MIN` (`:22-30`), and let the new probe supply `bwidth`'s
measured minimum `bw`. (c) Delete the fold at `dash.ado:562`:

```stata
    if `"`bw'"' != "" & `"`barwidth'"' == "" local barwidth `"`bw'"'
```

`_dash_parse_plot_opts` then declares `BARWidth(string)` and `BWidth(string)`, and `bw()`
resolves to `bwidth`. This is a **deliberate behaviour change**: any dash do-file that used
`bw()` meaning bar width must be updated. It is the one abbreviation decision in 05-04 that is
not a superset of twoway, and leaving it is worse — it changes the meaning of a working
`twoway` command.

**TR-18.5 — A7 must see generator-invented collisions.**
`test/test_abbreviations.cscript:435-443` iterates `RES = D["abbrev_resolution"]`
(`:217`) only. Add a second source: the set of tokens the two `dash.ado` syntax blocks accept,
derived the same way `test/test_unsupported_report_is_true.py:132` derives pending names — by
parsing `dash.ado` — so a collision introduced by `HISTORICAL_MIN`/`DASH_ONLY_MIN` is in scope
even when `abbrev_truth.json` has never heard of it.

**TR-18.6 — Corpus probes (item 15).**
Add to `test/fixtures/twoway_corpus.do`, each as a `dashprobe id spec opts [twextra]` line in
the section that owns it:

| id | section | spec | opts |
|---|---|---|---|
| `kd_at` | 20 (`:440`) | `kdensity mpg` | `at(mpg)` |
| `lp_at` | 18 (`:409`) | `lpoly mpg weight` | `at(weight)` |
| `lfitci_ciopts` | 17 (`:383`) | `lfitci mpg weight` | `ciopts(lcolor(red))` |
| `lpolyci_ciopts` | 17/18 | `lpolyci mpg weight` | `ciopts(lcolor(red))` |
| `lfitci_fitopts` | 17 (`:383`) | `lfitci mpg weight` | `fitopts(lwidth(thick))` |
| `kd_lineopts` | 20 (`:440`) | `kdensity mpg` | `lineopts(lcolor(navy))` |
| `sc_mlpattern` | 13 (`:329`) | `scatter mpg weight` | `mlpattern(dash)` with `twextra` of `mlabel(make)` where the option needs a label present |

Each writes one line to `twoway_corpus_results.txt` in the documented format
(`id %|% twoway_rc %|% dash_rc %|% plotspec %|% options %|% twoway_only_extra %|% dash spec
JSON`), and each gets a disposition row in `test/fixtures/rejected_options.json`. A probe whose
`twoway_rc` is non-zero is a **bad probe**, not a dash rejection — the corpus header says so
at `:15-17` — so fix the command rather than record it. Note that `at`, `ciopts` and `fitopts`
already carry `_dash_pending` lines at `dash.ado:594`, `:598` and `:603`, so the corpus is currently
silent about options dash already reports on.

Running the corpus needs Stata: `mkdir -p /tmp/dash-corpus && cd /tmp/dash-corpus` then
`arch -arm64 /usr/local/bin/stata-mp -b do <repo>/test/fixtures/twoway_corpus.do`. The
`arch -arm64` prefix is required (the x86_64 slice dies with `r(7100)` on libpython), Stata
batch mode exits 0 even on error, and the file deliberately carries **no** `version` statement
— a leading `version 17.0` or lower makes every dash graph registration fail.

### 18.B — The generator

**TR-18.7 — Idempotence (item 2).**
The splice steps 1–6 must be anchored on begin/end markers rather than on a prefix match that
can re-fire. Replace the current banner text with a paired sentinel, e.g.

```stata
    // >>> BEGIN generated by scripts/regen_option_surface.py — do not hand-edit
    ...
    // <<< END generated
```

and have each splice step locate the pair, replace between them, and assert exactly one pair
per target program. Hand-written code between the sentinels is by definition the generator's;
everything outside them is not the generator's to touch.

**TR-18.8 — De-duplicate the existing double splice (item 13).**
Before the first regeneration, remove by hand the second banner at `dash.ado:271` and `:465`
and the second `t/b/l/r` fold at `dash.ado:340` (keeping `:316`). `_dash_parse_graph_opts`
spans `:263-445` and `_dash_parse_plot_opts` `:458-772`, so the duplicate at `:534` is a
*different* defect (a live but dead fold in the plot parser, owned by Phase 17 item 6) and must
not be removed here.

**TR-18.9 — Preserve, don't recreate (item 9).**
The regions listed in the table in *Why this phase exists* §4 must all fall outside the
sentinels, or be preserved explicitly. The two that matter most: `sreturn local _pending` and
`sreturn local _unknown` at `dash.ado:770-771` are the **only** channel feeding
`_dash_report_ignored` (`dash.ado:1338`), and the `level()` block at `:549-561` is the only
thing stopping `level(150)` becoming a Python exception inside the renderer. Losing either is a
silent, total regression of an entire feature.

**TR-18.10 — Portability (item 9, second half).**
Replace `REPO = "/Users/billy/Desktop/Programs/StataPrograms/d/dash"`
(`scripts/regen_option_surface.py:17`) with a path derived from `__file__`
(`os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`), overridable by `argv[1]`.
Move the `json.dump` at `:298-299` to a repo-relative path (or `os.makedirs(..., exist_ok=True)`
first) **and** validate every output path *before* the destructive
`open(REPO + "/dash.ado", "w").write(src)` at `:294`. Today the order is write-then-report, so
a missing `/tmp/dash-wf/b2` leaves the repository mutated and the script traceback-ing.

**TR-18.11 — Splice the grouping comments (item 3).**
`pending_lines` at `scripts/regen_option_surface.py:291` is computed from
`PENDING = {n: s for n, s in GRAPH + PLOT if s}` and then discarded. Either splice it, or
replace it with what 05-04 actually asks for: grouping comments inside `syntax_block` that
emit each option under a header naming its owning section. The task text is explicit —
"Group them in the source with a comment naming the owning section, so it is obvious which are
wired up and which are waiting." The section tag for each option is already carried as the
second element of the `GRAPH`/`PLOT` tuples; an empty tag means "not pending", which for a
generated comment reads as *implemented* or *permanently accept-and-report* and should be
distinguished by an explicit marker rather than by absence.

**TR-18.12 — The fifth serializer (item 12).**
`_dash_graph_opts_to_json` at `dash.ado:891` carries 30 keys and is missing 25 of the options
05-04 added: `b1title b2title fxsize fysize hover l1title l2title nodraw play r1title r2title
scale subtitle2 t1title t2title text title2 xmlabel xmtick xsize xtick ymlabel ymtick ysize
ytick`. Nothing calls it, so this is not a live bug — it is a trap for the next developer who
reaches for the obvious-looking serializer. Preferred fix: **delete it**, and note the deletion
in the generator's docstring, which currently says the list is repeated in five places
(`scripts/regen_option_surface.py:3-7`) — after deletion it is four. Alternative fix: add it to
the generator's splice targets. Do not leave it unmaintained.

### 18.C — The report

**TR-18.13 — Canonical names in the note (item 4).**
`_dash_report_ignored` (`dash.ado:1338`) splits `raw` with
`mata: _dash_option_names("raw", "_dash_optnames")` (`dash_parse.mata:945`, which calls
`_dash_optname_of` at `:932`), then truncates each token at `strpos("`tok'", "(")`. Add a
resolution step between those: map each unknown token to the canonical option it is a prefix
of, using the same declared-name inventory the generator owns, and report the canonical name.
Where a token is a prefix of nothing (a genuinely unknown option such as
`notarealoption(3)` — O2-05's case), report it verbatim as today. This wart resolves itself
for each of the 69 as Phase 17 declares it, but it is live until then and it is the reason the
note cannot be trusted as an inventory.

**TR-18.14 — `xtick`/`ytick`/`xsize`/`ysize` in server mode (item 8).**
Two acceptable closures, and the choice sizes the item:

- *Implement.* Teach `ServerAppBuilder` (`dash_render.py:12265`) to read them. The emitted
  axis loop at `dash_render.py:14012` iterates `(('xlabel', fig.xaxis), ('ylabel', fig.yaxis))`
  and must gain the `xtick`/`ytick` keys, mirroring `DashRenderer`'s handling at
  `dash_render.py:9904-9912`, which resolves `tick_key = "xtick" if ax_key == "xlabel" else
  "ytick"` and falls through to `_parse_axis_spec(raw_ax or raw_tick)`. `xsize`/`ysize` must
  reach the emitted `_fig_kw` (`dash_render.py:13839-13855`), which today honours only
  `aspect_ratio` (`:13849`) and the log axis types (`:13853-13854`); `DashRenderer` consumes
  them via `_resolve_aspect_ratio` at `dash_render.py:9228-9229`.
- *Interim.* Make the note fire in server mode for these four. This requires TR-18.15.

Either way the silent case must end. Note the interaction with **Phase 16** (the axis-grammar
server port) and **Phase 22** (geometry): if those land first, this item shrinks to a
verification. Coordinate rather than duplicate.

**TR-18.15 — Mode-aware reporting (item 11c).**
`_dash_pending` is accumulated in `dash.ado` (graph block `:364-384`, plot block `:593-641`,
with `local _dash_unknown` at `:386` and `:642`) *before* the renderer is chosen, so it cannot distinguish
standalone from server. Two designs:

- **Per-mode pending lists.** Emit `_pending_standalone` and `_pending_server` alongside
  `sreturn local _pending` at `:770`, and have `_dash_report_ignored` select on the build mode
  the same way `_dash_do_render` (`dash.ado:120`) already knows it.
- **Defer the note to render time.** Carry the pending list into the spec JSON and let the
  chosen renderer emit it. Larger change, and it moves user-facing text out of Stata, which is
  where the plan wants errors to appear (see the S11-05 binding decision). Prefer the first.

Measured instances the mode-aware note must cover, from REMAINING.md: the `colorvar` family,
`xsize`, `ysize`, every plot option under `by()`, and the secondary-axis family. Those
*implementations* belong to Phases 17 (items 3–5), 21 and 27; what belongs here is the
mechanism and the test that makes their absence loud.

**TR-18.16 — The converse test (item 11a/11b).**
In `test/test_unsupported_report_is_true.py`, add a third parametrised test driven by the two
syntax blocks rather than by the pending lists, asserting for each declared option that
`_render(...)` with value `a` differs from `_render(...)` with value `b`, **or** the option is
named on the matching `_dash_pending` list. Reuse the existing scraping helper shape:

```python
# test/test_unsupported_report_is_true.py:132-138, at HEAD
def _pending(block_start_marker: str) -> "list[str]":
    """The option names one `_dash_pending` block lists."""
    with open(_ADO, encoding="utf-8") as fh:
        src = fh.read()
    i = src.index(block_start_marker)
    j = src.index("local _dash_unknown", i)
    return re.findall(r"_dash_pending' (\w+)\"", src[i:j])
```

A matching `_declared(block_start_marker)` should parse the `syntax [, ... ]` block and
lower-case the mixed-case declarations. The existing `FLAGS` set
(`colordiscrete coloruseplegend density fraction frequency horizontal nodraw percent sort
vertical`) already handles the "a flag has no second value" case and must be honoured by the
converse test too: for a flag, the comparison is present-versus-absent.

Then parametrise `_render` over the renderer. Today `_render` at `:162-178` ends:

```python
        return _norm(dr.DashRenderer(str(sp), str(dp)).render())
```

It must gain a `builder` parameter so the same three tests run against `ServerAppBuilder`
(`dash_render.py:12265`), normalising the emitted Python source the way `_norm` normalises HTML
(`_PID`/`_UUID` substitution then SHA-256). `TestTheListIsCoveredAndHonest::
test_every_pending_option_is_covered_here` (`:182-185`) already forces a new pending entry to
come with values in `PLOT_VALUES` (`:67`); the converse test needs the same guard for newly
declared options.

**TR-18.17 — O2-08, the serialization assertion (item 5).**
`test/test_option_surface.cscript` documents O2-01…O2-07 in its header (`:57-76`) and walks the
corpus fixture at `:379`. Add **O2-08**: for each implement-dispositioned option in
`test/fixtures/rejected_options.json` (`rejected_options`, 115 entries), run
`dash <spec>, <opt>(<value>) name(g1)`, then inspect the spec JSON that `dash build` writes and
assert the option's key is present carrying the value supplied, **and** that the note names the
option, **and** that `_rc == 0`. Driving it from the fixture rather than a hand-kept list is
what stops it going stale — the same discipline `test_unsupported_report_is_true.py` uses by
scraping `dash.ado`. Add **O2-09** for BR-18.9: assert every name the note prints is either in
the declared inventory or was typed verbatim by the test.

**TR-18.18 — The written correction (item 6).**
REMAINING.md §2 (`:102-145`) states "92 options the plan said to implement are only accepted
and reported, so their values never reach the spec", and `:304` records "92 options declared
nowhere". Measured, 23 of the 92 are reported as ignored **and** already serialized with their
value: `b1title b2title colorlist fxsize fysize horizontal l1title l2title lstyle mlstyle
mstyle r1title r2title scale sort t1title t2title text vertical xmlabel xmtick ymlabel ymtick`.
The 05-04 gap is **69**, not 92; the other 23 wait on S06/S09/S10 renderer work, not on
`dash.ado`.

> **Handling note.** This phase document does **not** edit `REMAINING.md` — it is the source of
> record for every phase document in this directory and is deliberately left unchanged.
> REMAINING.md already carries the correction itself, as the blockquote under Appendix A's
> `05-04` section ("Corrects §2 of this file…"). What this item requires of the developer is
> that any *derived* statement of the gap — the CHANGELOG entry, the commit message, the help
> text, and the status line in `.ultraplan/sections/section-05-option-surface.md` — uses 69 and
> not 92. If the maintainer does want §2 amended in place, that is a one-line erratum under §2
> pointing at Appendix A, and it should be a separate, explicitly requested commit.

---

## Work items

All fifteen, numbered exactly as handed over. Tags are `[kind · renderer · effort]`.

---

### 1. Measure the minimum abbreviation for the 69 undeclared options — `[deliverable · stata · medium]` · Epic 18.A · origin `05-04` (Appendix B)

Measure the minimum abbreviation for the 69 undeclared options and add them to
`test/fixtures/abbrev_truth.json`. None of the 69 has an entry today, so there is no S04 truth
to declare them against — 05-04's abbreviation clause cannot be satisfied for any of them
without first extending the S04 probe. Watch for collisions this will force: dash currently
accepts shorter prefixes than twoway precisely because it declares fewer options (measured:
`dash scatter mpg weight, mlabel(make) mlabs(3)` → `"mlabsize":"3"`, while twoway also has
`mlabstyle`/`mlabtextstyle`). `resolve_minimums()` in the generator asserts on ambiguity, so
adding these names with real measured minimums may trip that assert and force longer minimums
than existing dash do-files use.

*Where:* `scripts/extract_abbrev_truth.do`, `test/fixtures/abbrev_truth.json`,
`scripts/regen_option_surface.py:base_min`, `scripts/regen_option_surface.py:resolve_minimums`

*Evidence:* `abbrev_truth.json` carries 93 `options` entries at HEAD; none of the 69 is among
them. `base_min` at `:112` falls back to `DASH_ONLY_MIN.get(name, name)` when the fixture is
silent. Item 7 raises the scope of this item from 69 to **71**.

---

### 2. Fix the generator so it is idempotent before extending it — `[functional · stata · medium]` · Epic 18.B · origin `05-04` (Appendix B)

Re-running `scripts/regen_option_surface.py` against HEAD's `dash.ado` silently deletes
hand-added declarations that are not in its inventory: `HOVer(string)`, the `T()/B()/L()/R()`
title aliases, `PBGC/XLA2/XSC2/XTI2/YLA2/YSC2/YTI2`, `BINS(string)`, `sreturn local hover`,
and — critically — `sreturn local _pending` and `sreturn local _unknown`, which are the only
channel feeding `_dash_report_ignored`. Deleting those two lines disables 05-03's reporter
entirely. Since the block comment in `dash.ado` says "Do not hand-edit … run the generator",
this is the procedure a developer will follow to do item 1.

*Where:* `scripts/regen_option_surface.py:GRAPH`, `scripts/regen_option_surface.py:PLOT`,
`scripts/regen_option_surface.py` (splice steps 1–6), `dash.ado:_dash_parse_graph_opts`,
`dash.ado:_dash_parse_plot_opts`

*Evidence:* the banner instructing the developer to do exactly this is at `dash.ado:266-270`.
`sreturn local _pending`/`_unknown` are at `dash.ado:770-771`; `_dash_report_ignored` is at
`:1338` and reads nothing else.

---

### 3. Emit the owning-section grouping comments the task asks for — `[deliverable · stata · small]` · Epic 18.B · origin `05-04` (Appendix B)

The generator computes them (`pending_lines`, step 7) but never splices them into `dash.ado`,
so the variable is dead and the source has no marker saying which declared option belongs to
S06/S07/S09/S10/S11 or is permanently accept-and-report. Splice the section tags into the two
syntax blocks as grouping comments.

*Where:* `scripts/regen_option_surface.py:291 (pending_lines)`,
`scripts/regen_option_surface.py:syntax_block`, `dash.ado:_dash_parse_graph_opts`,
`dash.ado:_dash_parse_plot_opts`

*Evidence:* `pending_lines` at `scripts/regen_option_surface.py:291-292` is assigned and never
read; the destructive write follows immediately at `:294`. 05-04's `<action>` asks for it in
terms: "Group them in the source with a comment naming the owning section, so it is obvious
which are wired up and which are waiting."

---

### 4. Make the reporter name the canonical option rather than the prefix the user typed — `[functional · stata · small]` · Epic 18.C · origin `05-04` (Appendix B)

Because the 69 are undeclared, an abbreviated use falls straight through the `*` catch-all and
`_dash_report_ignored` echoes the raw token, so the note names options that do not exist in
twoway's vocabulary and cannot be looked up in the help. This resolves itself for each option
as it is declared, but until then it is a live wart, and it is the reason the note cannot be
trusted as an inventory.

*Where:* `dash.ado:_dash_report_ignored (:1338)`, `dash_parse.mata:_dash_option_names (:945)`,
`dash_parse.mata:_dash_optname_of (:932)`

*Evidence:* the reporter's own comment at `dash.ado:1342-1345` — "`raw' mixes bare option names
(pending, from the declared set) with the verbatim text Stata could not match (unknown, from
the trailing `*`)". Item 7 gives the live user-visible instance: `fxsiz(50)` produces a note
naming `fxsiz()`.

---

### 5. Add the test 05-04's `<verify>` names — `[deliverable · stata · medium]` · Epic 18.C · origin `05-04` (Appendix B)

"Every 'implement' option is accepted, serialized with its value, and reported as ignored
pending its section." No test asserts the serialization half.
`test/test_option_surface.cscript` checks only rc 0 (O2-01/02) and the accept-and-report
reporting contract (O2-03..O2-07); `test/test_unsupported_report_is_true.py` only walks options
already on the `_dash_pending` list and asserts the renderer output does NOT change, which says
nothing about whether the value reached the spec. Drive the new test from
`test/fixtures/rejected_options.json` so it cannot go stale.

*Where:* `test/test_option_surface.cscript (new O2-08 check)`,
`test/test_unsupported_report_is_true.py:PLOT_VALUES`, `test/fixtures/rejected_options.json`

*Evidence:* the O2 inventory is documented at `test/test_option_surface.cscript:57-76`;
`PLOT_VALUES` is at `test/test_unsupported_report_is_true.py:67`; the fixture's
`rejected_options` list has 115 entries.

---

### 6. Correct REMAINING.md section 2 — `[deliverable · stata · small]` · Epic 18.C · origin `05-04` (Appendix B)

It states "92 options the plan said to implement are only accepted and reported, so their
values never reach the spec". Measured, that is wrong for 23 of them: `b1title b2title
colorlist fxsize fysize horizontal l1title l2title lstyle mlstyle mstyle r1title r2title scale
sort t1title t2title text vertical xmlabel xmtick ymlabel ymtick` are reported as ignored AND
already serialized with their value. The 05-04 gap is 69 options, not 92; the other 23 are
waiting on S06/S09/S10 renderer work, not on `dash.ado`.

*Where:* `REMAINING.md:102-145 (section 2 "Blocker — the option surface")`,
`REMAINING.md:304 ("92 options declared nowhere")`

*Evidence and handling:* see **TR-18.18**. REMAINING.md already carries the correcting
blockquote under Appendix A's `05-04`; the arithmetic reconciles to 92 − 69 = 23 here and
96 − 69 = 27 there. This phase document does not edit REMAINING.md; the correction is carried
into the derived artefacts (CHANGELOG, help, `.ultraplan` status) instead.

---

### 7. `fxsize()`/`fysize()` are declared at a LONGER minimum than twoway's — `[functional · stata · small]` · Epic 18.A · origin `05-04` (Appendix C)

…so the abbreviated forms twoway accepts are silently thrown away. `dash.ado` declares
`FXSIZE(string)` / `FYSIZE(string)` (all-caps = full name required); twoway's measured minimum
is `fxsiz` / `fysiz`. A pasted `twoway ..., fxsiz(50)` therefore falls through the `*`
catch-all in dash: rc 0, a note naming a non-existent option `fxsiz()`, and the value gone.
This breaks 05-04's abbreviation clause for two of the 42 options the auditor certified as
DONE, and it is outside the auditor's remaining-item-2 scope, which is written against "the 69
undeclared" options only — `fxsize`/`fysize` are declared but have NO `abbrev_truth` entry, so
their declared minimum was guessed by `base_min()`'s fallback, not measured. Fix: probe
`fxsize`/`fysize` in `scripts/extract_abbrev_truth.do`, add them to
`test/fixtures/abbrev_truth.json`, and let the generator emit `FXSIZe`/`FYSIZe`. `scale` is the
third declared option with no truth entry but needs no change — twoway rejects `sca()`/`scal()`
too, so the full name is correct there. **The abbreviation-probe item should be scoped to 71
options, not 69.**

*Where:* `dash.ado:294` (FXSIZE/FYSIZE in the graph syntax block at `:281`), `dash.ado:511`
(same two in the plot syntax block at `:475`),
`scripts/regen_option_surface.py:base_min + DASH_ONLY_MIN`,
`scripts/extract_abbrev_truth.do`, `test/fixtures/abbrev_truth.json`

*Evidence:* confirmed at HEAD — `dash.ado:294` reads
`FXSIZE(string) /// FYSIZE(string) SCALE(string)`; `dash.ado:511` reads
`FXSIZE(string) FYSIZE(string) SCALE(string)`; `abbrev_truth.json` returns `None` for all
three.

---

### 8. `xtick()`, `ytick()`, `xsize()` and `ysize()` are silent in server mode — `[functional · server · medium]` · Epic 18.C · origin `05-04` (Appendix C)

They are serialized, emit NO note, and are never read by the generated `bokeh serve` app — a
silent drop in server mode, which is precisely the defect class 05-04's `<done>` forbids
("nothing is silently dropped in the interim"). The auditor's `done_items[3]` concludes "No
declared implement-option is both unimplemented and silent"; that holds for `DashRenderer`
only. All four were deliberately taken OFF the `_dash_pending` lists (see the comment block at
`dash.ado:594-604`, "scheme(), xsize(), ysize(), xtick() and ytick() are NOT listed"), so
nothing tells the user. Either teach `ServerAppBuilder` to read them (the emitted axis loop
currently iterates only `('xlabel', fig.xaxis)`, `('ylabel', fig.yaxis)`; `_fig_kw` honours
only `aspectratio`) or, as an interim, make the note fire in server mode.

*Where:* `dash_render.py:12265` (`class ServerAppBuilder` — emitted axis-tick block and
`_fig_kw` construction), `dash_render.py:9908` (DashRenderer xtick/ytick),
`dash_render.py:9228` (DashRenderer xsize/ysize), `dash.ado:593-642` (`_dash_pending` block
that deliberately omits them)

*Evidence:* the comment is at `dash.ado:632-640` in the working tree (REMAINING.md cites
`:594-604`; the block moved, the text is verbatim — quoted in full in *Why this phase exists*
§5). The emitted loop is at `dash_render.py:14012`; the emitted `_fig_kw` at `:13839-13855`
sets `aspect_ratio` at `:13849` and nothing else dimensional.

---

### 9. The generator's destructiveness is larger than the auditor's remaining-item-3 lists — `[functional · stata · medium]` · Epic 18.B · origin `05-04` (Appendix C)

A developer who restores only the items named in item 2 will still lose working code. Beyond
`HOVer`/`T`/`B`/`L`/`R`/`PBGC`/`XLA2...`/`BINS`/`sreturn local hover`/`sreturn local
_pending`/`sreturn local _unknown`, re-running `scripts/regen_option_surface.py` also deletes:

(a) the whole `level()` validation block in `_dash_parse_plot_opts` (`dash.ado:549-561`), which
is the only thing stopping `level(150)` becoming a Python exception inside the renderer;

(b) the ENTIRE plot-level `local _dash_pending` accumulation (`dash.ado:593-641`) and
`local _dash_unknown` (`:642`) plus its `sreturn local _pending`/`_unknown` (`:770-771`) —
after a regen the whole file contains zero `sreturn local _pending`, so 05-03's reporter is
dead at BOTH levels, not just graph level;

(c) `sreturn local g_hover` (`:750`) and `hover` from all four graph propagation loops
(`:1129`, `:1399`, `:1415`, `:1469`);

(d) every alias-folding `if` (`bins→bin`, `bw→barwidth`, `mlg→mlabgap`, `cv/colv→colorvar`,
`pbgc→plotbgcolor`, `xla2/xsc2/xti2/yla2/ysc2/yti2`, `t/b/l/r→*1title`).

Separately, the script is not runnable as documented on any other checkout: `REPO` is a
hardcoded absolute path (`scripts/regen_option_surface.py:17`) and the final
`json.dump(..., open("/tmp/dash-wf/b2/option_inventory.json", "w"))` runs AFTER `dash.ado` has
already been overwritten, so a missing directory leaves the repo mutated and the script
traceback-ing.

*Where:* `scripts/regen_option_surface.py:17 (REPO)`, `:299 (json.dump path)`, splice steps 2
and 4, `dash.ado:549-561 (level validation)`, `:593-642 (_dash_pending/_dash_unknown)`,
`:750 (g_hover)`, `:770-771 (sreturn _pending/_unknown)`

*Evidence:* every line number above was re-confirmed in the working tree; the `level()` block
and the run-order defect are quoted verbatim in *Why this phase exists* §4.

---

### 10. `bw()` is hijacked — `[functional · both · small]` · Epic 18.A · origin `05-04` (Appendix C)

A legal twoway abbreviation of `bwidth()` is routed to `barwidth` and silently discarded, so
`kdensity`/`lowess`/`lpoly` draw at the DEFAULT bandwidth with no note.
`scripts/regen_option_surface.py:HISTORICAL_MIN` (lines 104-107) hands `bw` to `barwidth` and
forces `bwidth` to the longer `bwid`; `dash.ado:_dash_parse_plot_opts` declares
`BARWidth(string)` + `BWIDth(string)` and folds
``if "`bw'" != "" & "`barwidth'" == "" local barwidth "`bw'"``. Fix: drop the `barwidth: bw`
entry from `HISTORICAL_MIN`, give `bwidth` the measured minimum `bw`, regenerate, and add the
collision to `test_abbreviations.cscript`'s A7 guard. **This is the one 05-04 abbreviation
decision that is not a superset of twoway — it changes the meaning of a working command.**

*Where:* `scripts/regen_option_surface.py:HISTORICAL_MIN (104-107)`,
`scripts/regen_option_surface.py:base_min`, `dash.ado:_dash_parse_plot_opts` (BARWidth/BWIDth
declarations and the ``local barwidth `"`bw'"'`` fold), `test/fixtures/abbrev_truth.json`,
`test/test_abbreviations.cscript (A7 collision guard)`

*Evidence:* `HISTORICAL_MIN` at `scripts/regen_option_surface.py:104-107` is quoted verbatim in
*Why this phase exists* §3, and `DASH_ONLY_MIN` at `:22-30` independently pins
`"bwidth": "bwidth"`. The fold is at `dash.ado:562`. Tagged `both` because the discarded
bandwidth affects every renderer that recomputes the smooth.

---

### 11. The reporting contract is mode-blind and has no converse test — `[deliverable · both · medium]` · Epic 18.C · origin `05-04` (Appendix C)

`_dash_pending` is computed in `dash.ado` before the renderer is chosen, so an option honoured
in standalone and dropped in server mode is silently dropped with no note (measured instances:
`colorvar` family, `xsize`, `ysize`, every plot option under `by()`, plus the already-recorded
secondary-axis family). And `test/test_unsupported_report_is_true.py` only tests ONE direction
— for each option ON the pending list, that rendering twice does not change the output.
Nothing asserts the converse: every option dash DECLARES must either change the rendered output
or be named on `_dash_pending`. That converse test is what would have caught `saving()`,
`xsize()`, `ysize()` and the colorvar family. The existing test also instantiates
`dr.DashRenderer` only (`test_unsupported_report_is_true.py:178`) and never `ServerAppBuilder`,
so it is blind to every server-mode gap by construction. Add: **(a)** a converse parametrised
test driven by the two syntax blocks; **(b)** run both existing directions against
`ServerAppBuilder` as well; **(c)** make the note mode-aware, or record a per-mode pending
list.

*Where:* `test/test_unsupported_report_is_true.py` (`_render` at `:162-178`, `_pending` at
`:132`, both parametrised tests), `dash.ado:_dash_parse_graph_opts` /
`_dash_parse_plot_opts` `_dash_pending` blocks, `dash.ado:_dash_report_ignored`

*Evidence:* `:178` is `return _norm(dr.DashRenderer(str(sp), str(dp)).render())`, confirmed; the
two existing parametrised tests are at `:195-196` and `:212-214`. Design options for (c) are in
TR-18.15.

---

### 12. `_dash_graph_opts_to_json` is a fifth, DEAD, stale copy — `[deliverable · stata · small]` · Epic 18.B · origin `05-04` (Appendix C)

`_dash_graph_opts_to_json` (`dash.ado:891`) is a fifth, DEAD, stale copy of the graph-option
list that the generator does not maintain. It carries 30 keys and is missing 25 of the options
05-04 added — `b1title b2title fxsize fysize hover l1title l2title nodraw play r1title r2title
scale subtitle2 t1title t2title text title2 xmlabel xmtick xsize xtick ymlabel ymtick ysize
ytick`. Nothing calls it today, so it is not a live bug, but it is a loaded gun for the next
developer who reaches for the obvious-looking serializer. Delete it, or add it to the
generator's splice targets.

*Where:* `dash.ado:_dash_graph_opts_to_json (:891)`, `scripts/regen_option_surface.py`

*Evidence:* `program define _dash_graph_opts_to_json, rclass` confirmed at `dash.ado:891`,
immediately after the generator-maintained `_dash_plot_opts_to_json` at `:854`. The generator's
docstring (`scripts/regen_option_surface.py:3-7`) counts five copies and names four.

---

### 13. The generator's splice has ALREADY double-applied in the committed `dash.ado` — `[deliverable · stata · small]` · Epic 18.B · origin `05-04` (Appendix C)

The generated blocks are duplicated at HEAD, not merely at risk of it. The "this block is
generated by `scripts/regen_option_surface.py`" banner appears 4 times (twice per syntax
block), and `_dash_parse_graph_opts` contains the `t()/b()/l()/r()` alias-fold `if`-ladder
twice in a row with two different comment headers. Both copies run, so behaviour is unchanged,
but the file no longer matches what the generator would produce and the next regeneration diff
will be unreadable. De-duplicate the splice markers before extending the inventory.

*Where:* `dash.ado:_dash_parse_graph_opts (:264-346)`, `dash.ado:_dash_parse_plot_opts
(:460-540)`, `scripts/regen_option_surface.py` (splice steps 1–6)

*Evidence:* confirmed at HEAD — banner at `dash.ado:266`, `:271`, `:460`, `:465`; the
`t→t1title` fold at `:316` and `:340`, both inside `_dash_parse_graph_opts` (`:263-457`). The
third occurrence at `:534` is inside `_dash_parse_plot_opts` and is a *different* defect (dead
code, Phase 17 item 6) — do not remove it here.

---

### 14. Three declared options have NO `abbrev_truth` entry, and the alias surface is unprobed — `[deliverable · stata · medium]` · Epic 18.A · origin `05-04` (Appendix C)

Three options that 05-04 declared have NO entry in `test/fixtures/abbrev_truth.json`, so their
minimum abbreviations were guessed from `HISTORICAL_MIN`/`DASH_ONLY_MIN` rather than measured —
`bwidth`, `at` and `jseed`. `bwidth` is the one that bit (see item 10). The S04 probe only
covered names it found in twoway's help under their canonical spelling, so the alias/short-form
surface the generator invents is unprobed by construction. Extend
`scripts/extract_abbrev_truth.do` to probe every name in the generator's `GRAPH`/`PLOT`
inventory including the alias forms, and add a test that, for each token dash accepts, twoway
either rejects it (superset, fine) or resolves it to the SAME canonical option (parity) — the
missing test is what let `bw` through, because `test_abbreviations.cscript`'s A7 collision guard
only iterates `abbrev_truth.json`.

*Where:* `scripts/extract_abbrev_truth.do`, `test/fixtures/abbrev_truth.json`,
`scripts/regen_option_surface.py:HISTORICAL_MIN / DASH_ONLY_MIN / resolve_minimums`,
`test/test_abbreviations.cscript (A7)`

*Evidence:* confirmed at HEAD — `abbrev_truth.json["options"]` returns `None` for `bwidth`,
`at` and `jseed`; `test/test_abbreviations.cscript:217` reads
`RES = D["abbrev_resolution"]` and the A7 block at `:435-443` iterates nothing else.

---

### 15. Add the probes 05-01 missed to `test/fixtures/twoway_corpus.do` — `[deliverable · stata · small]` · Epic 18.A · origin `S05` (main body)

`at()` on `kdensity` and `lpoly`, `ciopts()` on `lfitci`/`lpolyci`, `fitopts()` on `lfitci`,
`lineopts()` on `kdensity`, `mlpattern()` on `scatter` — each with `twoway_rc`, `dash_rc` and a
disposition.

*Where:* `test/fixtures/twoway_corpus.do`, `test/fixtures/rejected_options.json`

*Evidence:* the *17 DONE claims the adversarial pass overturned* table, row `05-01`: "corpus
missing probes for `at()`, `ciopts()`, `fitopts()`, `lineopts()`, `mlpattern()`". Confirmed at
HEAD: none of the five appears as a probe argument in the corpus. The probe table, sections and
run procedure are in **TR-18.6**.

---

## Test plan

Rule 8 governs every functional item: **write the failing test first, watch it fail for the
stated reason, then fix.** Rule 4 governs every new or changed function. Every test below is
paired with a mutation — the edit that must kill it — because a test that cannot die is not a
test.

### Epic 18.A — Measured truth

**The failing test first.** Two, in `test/test_abbreviations.cscript`:

- **A8-bw (item 10).** `dash kdensity mpg, bw(2) name(g1)` then assert the emitted spec JSON
  carries `"bwidth":"2"`. **Fails today** with `"barwidth":"2"` — the fold at `dash.ado:562`.
- **A8-fxsiz (item 7).** `dash scatter mpg weight, fxsiz(50) name(g1)` then assert the spec
  carries `"fxsize":"50"` and that the note does not name `fxsiz()`. **Fails today**: rc 0, the
  value is discarded by the `*` catch-all, and the note names a non-existent option.

**Unit tests (rule 4).** New module `test/test_regen_option_surface.py` — pure Python, no Stata,
so it runs in the ordinary `pytest` suite:

| test | asserts |
|---|---|
| `test_base_min_prefers_measured_truth` | `base_min("barwidth") == "barw"` from the fixture, not `"bw"` from `HISTORICAL_MIN` |
| `test_base_min_falls_back_only_when_truth_is_silent` | with a stub fixture containing the name, `DASH_ONLY_MIN` is not consulted |
| `test_base_min_rejects_a_non_prefix_minimum` | the `if not name.startswith(mn): mn = name` guard at `:115-116` |
| `test_resolve_minimums_raises_on_ambiguity` | feed it `mlabsize`, `mlabstyle`, `mlabtextstyle`; the assert fires (TR-18.2) |
| `test_every_inventory_name_has_truth` | **BR-18.3** — every `GRAPH`+`PLOT` name and every alias form has an `abbrev_truth` entry. Expected to fail until item 1 and item 14 land; it is the acceptance gate for both |
| `test_no_declared_minimum_is_longer_than_twoway` | **BR-18.2** — for each option, the declared mixed-case prefix length ≤ `min_abbrev` length |
| `test_historical_min_does_not_steal_another_options_prefix` | `bw` is not mapped to `barwidth` (item 10) |

**Integration / cscript coverage.**

- `test/test_abbreviations.cscript` — new **A8 parity group** (TR-18.5, BR-18.1). For every
  token dash accepts, run it through both commands: pass if `twoway` rejects it, pass if
  `twoway` resolves it to the same canonical option, **fail otherwise**. Source the token set
  from the `dash.ado` syntax blocks, not from `abbrev_truth.json`, so a generator-invented
  collision is in scope. Existing groups `A1..A7`, `R1..R4` (iterated at `:534` and `:684`)
  stay green.
- `test/fixtures/twoway_corpus.do` — the seven new probes (item 15, TR-18.6), re-run to produce
  `twoway_corpus_results.txt`, and the dispositions folded into
  `test/fixtures/rejected_options.json`. `test/test_conformance.cscript` must still show **zero
  `r(198)`** across the corpus.

**Mutation proofs.**

| test | break this | it must die |
|---|---|---|
| A8-bw | restore `"barwidth": "bw"` in `HISTORICAL_MIN` | yes |
| A8-fxsiz | revert `FXSIZe` → `FXSIZE` in `dash.ado:294` | yes |
| A8 parity group | add a fake `DASH_ONLY_MIN` entry mapping `msy` to `mlabsize` and regenerate | yes |
| `test_every_inventory_name_has_truth` | delete any one entry from `abbrev_truth.json` | yes |
| the new corpus probes | change `dashprobe kd_at`'s spec to a plottype that does not accept `at()`, making `twoway_rc` non-zero | the bad-probe guard at `twoway_corpus.do:15-17` must flag it |

### Epic 18.B — The generator

**The failing test first.** `test/test_regen_option_surface.py::test_generator_is_idempotent`:
copy the repo to a `tmp_path`, run the generator, `diff` the resulting `dash.ado` against the
input. **Fails today** — the splice re-fires, which is precisely how the double-applied banners
at `dash.ado:266`/`:271`/`:460`/`:465` and the doubled fold at `:316`/`:340` got there (item 13).

**Unit tests (rule 4).**

| test | asserts | item |
|---|---|---|
| `test_generator_is_idempotent` | run twice; the second run is a no-op (BR-18.4) | 2 |
| `test_splice_markers_are_unique` | the generated-block sentinel appears exactly twice in `dash.ado` (once per syntax block) and the `t/b/l/r` fold exactly once in `_dash_parse_graph_opts` (BR-18.7) | 13 |
| `test_regen_preserves_hand_written_blocks` | after a regen: the `level()` block is byte-identical; `sreturn local _pending` and `sreturn local _unknown` each appear in both parsers; `sreturn local g_hover` survives; `hover` appears in all four propagation loops; every alias fold survives (BR-18.5) | 9 |
| `test_generator_is_path_independent` | run from a copy at a different path with `$TMPDIR` unset and no `/tmp/dash-wf/b2`; it completes, and on a deliberately unwritable report path it raises **before** `dash.ado` is modified (BR-18.6) | 9 |
| `test_pending_lines_is_spliced` | every declared option in both syntax blocks sits under a section-tag comment; no computed-and-discarded variable remains (BR-18.8) | 3 |
| `test_there_is_one_graph_option_serializer` | `_dash_graph_opts_to_json` is absent, or present and regenerated in step with `_dash_plot_opts_to_json` (BR-18.7) | 12 |

**Integration / cscript coverage.**

- `test/test_ado_loads.cscript` must stay green after a regeneration — the file still parses.
- `test/test_option_report_paren.cscript` is the canary for item 9(b): it exercises the note,
  which dies the moment `sreturn local _pending` is deleted.
- **Regression cscript for the `level()` deletion (rule 8).** Add to
  `test/test_adversarial.cscript`: `dash lfitci mpg weight, level(150) name(g1)` must exit
  `198` with `level() must be between 0 and 100 (exclusive)` and no Python traceback. It passes
  today; it exists so that a future regeneration that eats `dash.ado:549-561` fails loudly
  rather than turning a Stata error into a renderer exception.
- **Regression pytest for item 12.** Assert no unreferenced option-serializer program remains
  in `dash.ado` — a `grep`-style structural test, cheap and durable.

**Mutation proofs.**

| test | break this | it must die |
|---|---|---|
| `test_generator_is_idempotent` | make a splice step match on a prefix instead of a sentinel pair | yes |
| `test_splice_markers_are_unique` | re-add the second banner at `dash.ado:271` | yes |
| `test_regen_preserves_hand_written_blocks` | delete `sreturn local _pending` from `dash.ado:770` | yes — and so must `test_option_report_paren.cscript` |
| `test_generator_is_path_independent` | restore the hardcoded `REPO` at `:17` | yes |
| `test_pending_lines_is_spliced` | drop the section tag from one option's group | yes |
| the `level(150)` cscript | delete the block at `dash.ado:549-561` | yes |

### Epic 18.C — The report

**The failing test first.** Three:

- **O2-08 (item 5).** In `test/test_option_surface.cscript`, drive
  `test/fixtures/rejected_options.json` and assert *serialized with its value* for every
  implement-dispositioned option. **Fails today** for all 69 undeclared ones — no key reaches
  the spec. This is also Phase 17's acceptance gate; it turns green as Phase 17 lands and stays
  green thereafter.
- **The converse test (item 11a).** In `test/test_unsupported_report_is_true.py`, parametrised
  over the declared names scraped from the two syntax blocks. **Fails today**, naming
  `saving`, `xsize`, `ysize` and the colorvar family — options that neither change the output
  nor appear on a pending list.
- **The server-mode direction (item 11b, item 8).** The same converse test parametrised over
  `ServerAppBuilder`. **Fails today** on `xtick`, `ytick`, `xsize`, `ysize` and the colorvar
  family.

**Unit tests (rule 4).**

| test | asserts | item |
|---|---|---|
| `test_report_resolves_a_prefix_to_its_canonical_option` | `fxsiz` → `fxsize()` in the note (BR-18.9) | 4 |
| `test_report_leaves_a_genuinely_unknown_token_verbatim` | `notarealoption(3)` is still reported as typed — the O2-05 case must not regress | 4 |
| `test_report_does_not_split_a_multiword_argument` | `addplot(line y2 x)` yields one name, not three. Guards the existing `_dash_option_names` behaviour documented at `dash.ado:1346-1352` | 4 |
| `test_declared_block_parser_finds_both_syntax_blocks` | the new `_declared()` helper is non-vacuous — the mirror of today's `test_the_blocks_were_actually_found` at `:190` | 11 |
| `test_flags_compare_presence_not_value` | the `FLAGS` set is honoured by the converse test | 11 |
| `test_pending_is_per_mode` | the standalone and server pending lists are distinct objects and each is non-empty (BR-18.10) | 8, 11 |

**Integration / cscript coverage.**

- `test/test_option_surface.cscript` — **O2-08** (serialization, BR-18.11) and **O2-09** (the
  note names only canonical options, BR-18.9), documented in the header alongside O2-01…O2-07
  at `:57-76`.
- `test/test_server_build.cscript` and `test/test_e2e_serve.cscript` — a served build carrying
  `xtick`/`ytick`/`xsize`/`ysize` either honours them or emits the note. No silent case.
- `test/test_unsupported_report_is_true.py` — the third parametrised test, plus both existing
  directions re-run against `ServerAppBuilder`.

**Mutation proofs.**

| test | break this | it must die |
|---|---|---|
| O2-08 | delete one option from `_dash_plot_opts_to_json` (`dash.ado:854`) | yes |
| O2-09 | make the reporter echo the raw token again | yes |
| converse test (standalone) | remove `colorlist` from the graph `_dash_pending` block without implementing it | yes |
| converse test (server) | revert the emitted axis loop at `dash_render.py:14012` to two keys | yes |
| `test_report_resolves_a_prefix_to_its_canonical_option` | drop the resolution step from `_dash_report_ignored` | yes |
| `test_pending_is_per_mode` | collapse both lists back onto one `sreturn local _pending` | yes |

### Suite-level gates

Per CLAUDE.md rule 5, before committing: pull local `main`, run the **full** suite, fix, repeat
until green. The baselines to beat, from REMAINING.md's *Gates still to pass (S16-07)*: at HEAD
the suite is **3,498 passed / 37 skipped; 25/25 cscripts**. Per the project memory, run the
certification suite with `arch -arm64` from `test/`, set `$dash_nobrowser` before any Stata run
that builds a dashboard, and remember that **a skip is not a pass** — a cscript that skips
because Stata or Python was unavailable has proven nothing.

---

## Definition of done

A reviewer can tick every line below.

**Epic 18.A — Measured truth**

- [ ] `test/fixtures/abbrev_truth.json` has a measured entry — `min_abbrev`, `probe_cmd`,
      `oracle: gph-identity` — for all 71 options in scope (the 69 plus `fxsize`, `fysize`),
      and for `bwidth`, `at` and `jseed`. `scale` is deliberately unchanged and the reason is
      recorded.
- [ ] `scripts/extract_abbrev_truth.do` probes every name in the generator's `GRAPH`/`PLOT`
      inventory **including** the alias forms.
- [ ] `dash.ado` declares `FXSIZe(string)` / `FYSIZe(string)` in both syntax blocks
      (`:294`, `:511`), and `dash scatter mpg weight, fxsiz(50)` puts `"fxsize":"50"` in the
      spec.
- [ ] `barwidth: bw` is gone from `HISTORICAL_MIN`; `bwidth`'s minimum is the measured `bw`;
      the fold at `dash.ado:562` is deleted; `dash kdensity mpg, bw(2)` yields `"bwidth":"2"`.
- [ ] Every minimum that `resolve_minimums()` forced longer is listed in the commit message and
      checked against `test/fixtures/conformance_corpus.txt` and the twelve example do-files.
- [ ] `test/fixtures/twoway_corpus.do` carries the seven new probes; each has a `twoway_rc` of
      0, a `dash_rc`, and a disposition row in `test/fixtures/rejected_options.json`.
- [ ] `test/test_abbreviations.cscript` group **A8** exists, is driven from the `dash.ado`
      syntax blocks, and passes.

**Epic 18.B — The generator**

- [ ] `python3 scripts/regen_option_surface.py && git diff --stat` produces an empty diff on a
      clean tree.
- [ ] The generated-block sentinel appears exactly twice in `dash.ado`; the `t/b/l/r` fold
      appears exactly once in `_dash_parse_graph_opts`.
- [ ] After a regeneration: the `level()` block at `:549-561` is byte-identical;
      `sreturn local _pending` and `sreturn local _unknown` appear in both parsers;
      `sreturn local g_hover` survives; `hover` appears in all four propagation loops; every
      alias fold survives.
- [ ] The generator runs from an arbitrary checkout path with no pre-existing scratch
      directory, and validates its output paths before writing `dash.ado`.
- [ ] Every declared option in both syntax blocks sits under a comment naming its owning
      section; `pending_lines` is either spliced or removed, with no dead variable left.
- [ ] `_dash_graph_opts_to_json` is deleted (or regenerated in step), and the generator's
      docstring count is corrected.
- [ ] `test/test_regen_option_surface.py` exists and passes; each of its tests has been proven
      non-vacuous by the mutation in the table above.
- [ ] `dash lfitci mpg weight, level(150)` exits `198` with the Stata-side message, and a
      cscript asserts it.

**Epic 18.C — The report**

- [ ] The note names canonical option names only; `fxsiz(50)` reports `fxsize()`;
      `notarealoption(3)` still reports verbatim.
- [ ] `test/test_option_surface.cscript` has **O2-08** and **O2-09**, documented in its header,
      driven from `test/fixtures/rejected_options.json`.
- [ ] `test/test_unsupported_report_is_true.py` runs three directions — pending-is-true,
      converse, and both against `ServerAppBuilder` as well as `DashRenderer`.
- [ ] `xtick()`, `ytick()`, `xsize()`, `ysize()` are either honoured by the emitted server app
      or named in a server-mode note. No silent case remains for any of the four.
- [ ] A per-mode pending list exists, or the note is otherwise mode-aware, and a test asserts
      the two modes differ.
- [ ] The figure **69** (not 92) is used in the CHANGELOG entry, the commit message, any help
      text, and the `.ultraplan` section status. `REMAINING.md` is unmodified.

**Phase-level**

- [ ] Full `pytest` green, at or above 3,498 passed; 25/25 cscripts, with **no** skip standing
      in for a pass.
- [ ] `test/test_conformance.cscript` shows zero `r(198)` across the corpus, including the
      seven new probes.
- [ ] No option's *honoured* behaviour changed except the two deliberate abbreviation fixes
      (items 7 and 10), and both are called out in the commit message as breaking changes for
      existing dash do-files.
- [ ] Committed to a feature branch, never directly to `main`, with the merge command supplied
      and no mention of the assistant in the message (CLAUDE.md rules 6 and 7).

---

## Risks and sequencing notes

**The intra-phase order is not negotiable.** 18.B before 18.A before 17's regeneration:

1. **18.B first — de-duplicate and make idempotent (items 13, 2, 9).** Until the splice is
   sentinel-anchored and non-destructive, *any* regeneration destroys 05-03's reporter, the
   `level()` guard and every alias fold. This is also why item 13 must be done by hand: the
   file is already double-spliced, so the first idempotent run has to start from a
   de-duplicated file or it will simply preserve the duplication.
2. **18.A next — measure (items 1, 7, 14, 10, 15).** The generator consumes
   `abbrev_truth.json`; fixing the generator without fixing the fixture produces a faithful
   reproduction of the wrong answer.
3. **Then Phase 17 regenerates**, and **18.C** proves the result (items 5, 11, 4, 8, 6).

**Risk — `resolve_minimums()` will fire, and existing do-files may break.** This is the
largest risk in the phase and it is a *user-visible* one. Declaring `mlabstyle` and
`mlabtextstyle` makes `mlabs` ambiguous, so `mlabs(3)` — which resolves to `mlabsize` today,
measured — will stop resolving. Mitigation: enumerate every lengthened minimum before
regenerating, check each against `test/fixtures/conformance_corpus.txt` and the twelve example
do-files, and document the list in the CHANGELOG. There is no way to have both twoway parity
and today's shorter prefixes; parity wins, because the drop-in claim is the product.

**Risk — item 10 is a deliberate breaking change.** Any dash do-file using `bw()` to mean bar
width changes meaning. It is still right: `bw()` in `twoway` means `bwidth()`, and silently
mapping it elsewhere is worse than an explicit break. Call it out in the CHANGELOG, and
consider a one-release transitional note in the reporter naming the change when `bw()` is used
on a bar plot.

**Risk — item 8 overlaps Phases 16 and 22.** `xtick`/`ytick` in the emitted app is also the
subject of **Phase 16** (the axis-grammar server port), and `xsize`/`ysize` of **Phase 22**
(geometry) and **Phase 17** item 5. If those land first, item 8 collapses to a verification;
if this phase lands first, take the *interim* branch of TR-18.14 (make the note fire in server
mode) rather than writing emitted-app code that Phase 16 will rewrite. Decide once, in whichever
phase runs first, and record the decision in the other.

**Risk — Phase 17 and this phase both regenerate `dash.ado`.** They will conflict at the splice
region if run in parallel. Run them in series on the same branch; the epic order above assumes
it.

**Risk — the Stata-dependent work cannot run in CI.** Items 1, 7, 14 and 15 need real `twoway`
with `arch -arm64`, and the certification suite skips without it. A skip is not a pass. The
Python-only guards — `test/test_regen_option_surface.py` and the converse tests in
`test/test_unsupported_report_is_true.py` — are deliberately designed to run without Stata, so
the generator and the reporting contract stay guarded on every push even when the abbreviation
fixture can only be regenerated on a machine with Stata.

**Note — item 6 and the source of record.** `REMAINING.md` is not modified by this phase, by
this document, or by any phase document in this directory. Item 6's correction travels through
the derived artefacts instead. If the maintainer wants §2 amended in place, that is a separate,
explicitly requested one-line erratum.
