# Phase 21 — S09 style options

**Purpose.** This is the largest single family of unimplemented `twoway` options in the
whole audit. The plan dispositioned **50** style options "implement-S09-style"; at HEAD
**3** are honoured, **4** are declared and serialized but deliberately reported as ignored,
and **43** are not declared anywhere — they reach `dash.ado` only through the trailing `*`
catch-all, so no value ever arrives in the spec JSON and the renderer has nothing to read.
Measured directly against `dash_render.py`, **all 43 appear zero times in the file** as a
quoted option key, in either renderer. This phase implements the whole family: the marker
and marker-label look (`mlabangle` … `dfcolor`), the line/area/bar/CI/dot/arrow look
(`acolor` … `mangle`), the `colorvar()` colour-mapping and colour-legend controls
(`clegend` … `plegend`), and the four style shorthands whose values already arrive
(`colorlist` `lstyle` `mlstyle` `mstyle`). It also finishes task **05-05** on the server
side: `falpha` and `mlcolor` were made honest in `DashRenderer` and never routed into the
source `ServerAppBuilder` emits, so a `dash serve` dashboard silently drops both. The
phase's non-negotiable discipline is the one `dash.ado` already writes down at `:590-592`
— implement an option and remove it from `_dash_pending` in the same commit, or the
existing honesty test fails.

---

## At a glance

| | |
|---|---|
| **Items** | 5 (numbered 1–5 below, exactly as handed over) |
| **Functional vs deliverable** | 5 functional · 0 deliverable |
| **Effort mix** | 0 small · 2 medium (items 1, 5) · 3 large (items 2, 3, 4) |
| **Option names in scope** | **47** — the 43 undeclared (items 2 + 3 + 4, a verified exact partition) plus the 4 declared-but-pending (item 5). This is precisely the "accepted + reported ignored" cell of the `implement-S09-style` row in REMAINING.md §2. |
| **Renderers touched** | `server` only on item 1 (`ServerAppBuilder`, everything after `dash_render.py:12265`). `both` on items 2–5 — `GlyphMapper`/`OptionTranslator` in `DashRenderer` **and** the emitted server app, which today contains none of these names. |
| **Ultraplan tasks discharged** | `OPT-S09S` (the S09-style option group, section **S09**) and the server half of `05-05` (section **S05**). |
| **Not discharged here** | S09's axis/title/text options (Phase 20), S09's legend *chrome* and scheme colour keys (Phase 25), the declaration and serialization of the 43 in `dash.ado` (Phase 17), their abbreviations and the generator (Phase 18). |
| **Depends on** | **Phase 17** — hard. Items 2, 3 and 4 cannot read a value that `dash.ado` never writes; Phase 17 is the item "Declare and serialize the 69 implement-dispositioned options". **Phase 18** — hard for the reporting and abbreviation contract (`_dash_pending`, `abbrev_truth.json`, the idempotent generator). Item 5 alone is unblocked at HEAD, because its four names are already serialized. |
| **Soft dependency** | **Phases 05–08** (server unification). Item 1 edits five hand-written `ptype ==` branches and two facet copies that Phase 06 intends to delete. See Risks. |
| **Unblocks** | **Phase 30** (help and documentation — `dash.sthlp` currently describes a smaller option surface), **Phase 31** (release gates: the conformance corpus and the "nothing silently dropped" claim). |
| **Source of items** | All five from REMAINING.md's **main body**: item 1 from §"17 DONE claims the adversarial pass overturned" (row `05-05`); items 2–5 from §2 "Blocker — the option surface", cross-read against Appendix A `05-04`. |

---

## Why this phase exists

### 1. The measurement, from REMAINING.md §2 "Blocker — the option surface  [S05-04, S07, S09, S10]"

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

The `implement-S09-style` row — **50 total, 3 honoured, 47 open** — is this phase. It is
the largest single row in the table, larger than S06, S07, S10 and the accept-and-report
group combined.

The 47, named verbatim by REMAINING.md §2:

> - **S09 style (47):** `acolor` `alalign` `alpattern` `alstyle` `alwidth`
>   `astyle` `barbsize` `baroffset` `bstyle` `clegend` `colorend`
>   `colorfillonly` `colorformissing` `colorkeysrange` `colorlevels`
>   `colorlist` `colorrule` `colorstart` `colorvarminmax` `dcolor` `dfcolor`
>   `dlalign` `dlcolor` `dlstyle` `dlwidth` `dotextend` `dsize` `dstyle`
>   `dsymbol` `gap` `headlabel` `lalign` `lstyle` `mangle` `mlabangle`
>   `mlabformat` `mlabstyle` `mlabtextstyle` `mlabvposition` `mlalign`
>   `mlstyle` `mstyle` `mwidth` `ndots` `nodropbase` `pcycle` `plegend`

And the choice REMAINING.md puts to the user, which governs whether this phase is built at
all — quoted verbatim, because a developer must not discover it late:

> **Two defensible ways to close this**, and the choice is the user's:
> **(a)** implement all 92 — the plan as written; **(b)** implement the high-value
> subset (`text` `ttitle`/`tlabel` family, the `b1/l1/r1/t1title` set,
> `mlabformat` `mstyle` `lstyle` `acolor` `gap` `fxsize` `fysize` `scale`) and
> formally re-disposition the rest to accept-and-report in the plan and help.

**This document is written for (a).** If the user picks (b), five of this phase's names
survive (`mlabformat` `mstyle` `lstyle` `acolor` `gap`), item 1 survives unchanged (it is
not an option-surface item — it is a server parity defect), and the remaining 42 become a
documentation change owned by Phase 30 rather than a code change. The Definition of done
below has a row for that fork.

### 2. Where the 47 split — from REMAINING.md Appendix A, `05-04 · PARTIAL`

Appendix A re-measured the same family from the declaration side and reports a different,
finer number:

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
> - **S09 style (43):** `acolor` `alalign` `alpattern` `alstyle` `alwidth`
>   `astyle` `barbsize` `baroffset` `bstyle` `clegend` `colorend`
>   `colorfillonly` `colorformissing` `colorkeysrange` `colorlevels` `colorrule`
>   `colorstart` `colorvarminmax` `dcolor` `dfcolor` `dlalign` `dlcolor`
>   `dlstyle` `dlwidth` `dotextend` `dsize` `dstyle` `dsymbol` `gap`
>   `headlabel` `lalign` `mangle` `mlabangle` `mlabformat` `mlabstyle`
>   `mlabtextstyle` `mlabvposition` `mlalign` `mwidth` `ndots` `nodropbase`
>   `pcycle` `plegend`

Appendix A also states, in its own words, why the §2 figure and this one differ:

> Corrects §2 of this file, which put the figure at 92 by treating every
> reported option as undeclared. 27 of those are declared and serialized
> already, and are reported because `_dash_pending` correctly says they are
> awaiting their section.

And Appendix B names the S09-style members of that overlap explicitly, in the item
"Correct REMAINING.md section 2":

> Measured, that is wrong for 23 of them:
> b1title b2title **colorlist** fxsize fysize horizontal l1title l2title **lstyle**
> **mlstyle** **mstyle** r1title r2title scale sort t1title t2title text vertical
> xmlabel xmtick ymlabel ymtick are reported as ignored AND already serialized
> with their value. The 05-04 gap is 69 options, not 92; the other 23 are
> waiting on S06/S09/S10 renderer work, not on dash.ado.

So the arithmetic closes exactly, and it is the arithmetic that produces this phase's five
items:

| state at HEAD | count | names | item |
|---|---:|---|---:|
| honoured | 3 | `color` `jitterseed` `mlwidth` | — |
| declared + serialized, on `_dash_pending`, renderer-side work outstanding | 4 | `colorlist` `lstyle` `mlstyle` `mstyle` | **5** |
| not declared anywhere — value never reaches the spec | 43 | the 43 above | **2, 3, 4** |
| **total dispositioned `implement-S09-style`** | **50** | | |

**Verified as an exact partition.** The three item lists handed to this phase (12 names in
item 2, 20 in item 3, 11 in item 4) were checked against Appendix A's 43: the union is 43,
with no name missing, no name duplicated, and no overlap with item 5's four.

### 3. Confirmatory measurement taken while writing this document

Read-only, against `dash_render.py` at HEAD on `feature/batch4-interactive-layer`. This
confirms Appendix A rather than replacing it: none of the 43 has a consumer to fix, so
every one is new code, not a repair.

```
$ python3 - <<'EOF'
names = """acolor alalign alpattern alstyle alwidth astyle barbsize baroffset bstyle
clegend colorend colorfillonly colorformissing colorkeysrange colorlevels colorrule
colorstart colorvarminmax dcolor dfcolor dlalign dlcolor dlstyle dlwidth dotextend
dsize dstyle dsymbol gap headlabel lalign mangle mlabangle mlabformat mlabstyle
mlabtextstyle mlabvposition mlalign mwidth ndots nodropbase pcycle plegend""".split()
lines = open('dash_render.py').read().split('\n')
zero = [n for n in names
        if sum(1 for l in lines if ("'"+n+"'") in l or ('"'+n+'"') in l) == 0]
print(len(names), "names;", len(zero), "with zero occurrences as a quoted key")
EOF
43 names; 43 with zero occurrences as a quoted key
```

Two near-misses were checked by hand and are **not** consumers: `mstyle` matches only
`self.legend_cols = self._int("numstyle legend_cols", None)` at `dash_render.py:2088` (a
scheme key), and `clegend` matches only the colorvar legend's internal *name*,
`_COLORVAR_LEGEND_NAME = "_dash_clegend"` at `dash_render.py:595` and the per-factor
`name=f"_clegend_{factor}"` at `:3225` — not the `clegend()` option.

The same probe run against the emitted server app (everything after
`dash_render.py:12265`, `class ServerAppBuilder`) returns zero for every name in this
phase and, additionally, zero for the symbols item 1 is about:

| symbol | occurrences in `dash_render.py` | occurrences after `:12265` (the emitted app) |
|---|---:|---:|
| `falpha` | 3 | **0** |
| `mlcolor` | 6 | **0** |
| `mlwidth` | 4 | **0** |
| `colorvar` | 18 | **0** |
| `ColorBar` | 4 | **0** |
| each of the 43 | 0 | **0** |

### 4. Item 1's evidence — the `05-05` refutation

REMAINING.md's table of the 17 DONE claims the adversarial pass overturned carries this row
verbatim:

> | 05-05 | `falpha` and `mlcolor` never routed through the server builder's fill-bearing branches |

The task it refutes, from `.ultraplan/sections/section-05-option-surface.md:178`, is
`05-05 "Make the existing silent no-ops honest"`:

> Nine options are accepted today and never read: `falpha`/`fa`, `pstyle`, `recast`,
> `cmissing`, `connect`, `mlcolor`, `mlabwidth`, `coloruseplegend`, and graph-level
> `scheme`. Each currently fails silently. … `falpha` goes to S09, `mlcolor` to S09 …
>
> **&lt;verify&gt;** Each of the nine produces a note naming it; none is silently dropped.
> **&lt;done&gt;** Every accepted option either works or says it does not.

Both were implemented — in `DashRenderer` only. At HEAD, `GlyphMapper._apply_marker_opts`
handles `mlcolor` with a deliberate comment about the bug it fixed
(`dash_render.py:2841-2861`):

```python
        # mlcolor()/mlwidth() are the marker's OWN border options.  The
        # border used to be taken from lcolor(), the CONNECTING LINE colour,
        # which is wrong in both directions: mlcolor() did nothing and
        # lcolor() restyled the marker.  Applied after lcolor so they win.
        if "mlcolor" in options:
            raw_mlc = str(options["mlcolor"]).strip().lower()
            if raw_mlc == "none":
                if hasattr(glyph, "line_alpha"):
                    glyph.line_alpha = 0.0
            else:
                try:
                    color, alpha = self.tr.parse_color_alpha(options["mlcolor"])
```

and `GlyphMapper._apply_fill_opts` handles `falpha`/`fa` (`dash_render.py:2947-2955`):

```python
        # falpha()/fa() -- used nine times in examples/comprehensive_demo.do
        # and never read.
        for _ak in ("falpha", "fa"):
            if _ak in options:
                _fa = _stat_option_float(options, _ak, None, "fill",
                                         lo=0.0, hi=100.0)
                if _fa is not None and hasattr(glyph, "fill_alpha"):
                    glyph.fill_alpha = _fa / 100.0
                break
```

`ServerAppBuilder` emits its own fill-bearing branches, and every one of them reads
`fcolor` and `fintensity` and stops there. The `area` branch, `dash_render.py:14265-14286`
verbatim (emitted-source string literals):

```python
            "            elif ptype in ('area',):",
            "                clean = g_df[[xvar, yvar]].dropna().sort_values(xvar) if xvar and yvar else g_df",
            "                asrc = ColumnDataSource(clean)",
            "                _ar_base = 0.0",
            "                try: _ar_base = float(opts.get('base', '0') or '0')",
            "                except (ValueError, TypeError): pass",
            "                asrc.data['_zero'] = [_ar_base] * len(clean)",
            "                _ar_fill = color",
            "                _afc = opts.get('fcolor', '')",
            "                if _afc:",
            "                    _afc_r = _resolve_color(_afc)",
            "                    if _afc_r: _ar_fill = _afc_r",
            "                _ar_alpha = _SCHEME_AREA_ALPHA",
            "                _afi = opts.get('fintensity', '')",
            "                if _afi:",
            "                    try:",
            "                        _av = _afi.strip()",
            "                        _ar_alpha = min(1.0, max(0.0, float(_av[5:])/100.0 if _av.startswith('inten') else float(_av)/100.0))",
            "                    except (ValueError, AttributeError): pass",
            "                fig.varea(x=xvar, y1='_zero', y2=yvar, source=asrc,",
            "                          fill_color=_ar_fill, alpha=_ar_alpha)",
            "                graph_sources[gname].append(asrc)",
```

`fintensity` is read. `falpha` is not. The same three-line `fcolor`/`fintensity` shape
repeats at `bar` (`:14288`), `histogram` (`:14133`, using `_SCHEME_BAR_ALPHA`), `rarea`
(`:14429`), `rbar` (`:14457`, which additionally prefers `bfcolor`), and the two CI bands
`lfitci` (`:14375`, hardcoded `_lfci_alpha = 0.2`) and `qfitci` (`:14402`).

The two facet copies are worse: they read nothing at all. `dash_render.py:15150-15153` —
the `by()` facet loop:

```python
            "                elif ptype == 'area':",
            "                    _fac_fig.varea(x=xvar_f, y1=0, y2=yvar_f, source=_fac_src, fill_color=color, fill_alpha=_SCHEME_AREA_ALPHA, legend_label=yvar_f, **_glyph_kw)",
            "                elif ptype in ('histogram', 'hist'):",
```

and `dash_render.py:15251-15253` — the `by(total)` copy, character-for-character the same
call with `_tot_fig`/`_tot_src`. REMAINING.md Appendix C describes this branch in full, and
its description is the reason item 1 names the facet copies as well as the main loop:

> The faceted (`by()`) branch of the emitted server app is a SECOND hand-written glyph
> dispatch that ignores the plot `options` dict entirely except for `lcolor`/`mcolor`.
> Every other serialized plot option is silently discarded on that path — `msymbol`,
> `msize`, `malpha`, `jitter`, `mlabel`, `mlcolor`, `mlwidth` all work in standalone AND in
> non-faceted server mode, then vanish the moment `by()` is added. The branch hardcodes
> `size=6`, `width=0.8`, `line_width=_SCHEME_LINE_WIDTH`.

`falpha` and `mlcolor` **do** reach the spec — `dash.ado:_dash_plot_opts_to_json` serializes
both in its `foreach key` list at `dash.ado:862-870`:

```
    foreach key in mcolor msymbol msize msangle mfcolor mlcolor mlabel mlabcolor ///
                   mlabsize mlabposition mlabgap mlabwidth malpha marker lcolor ///
                   lwidth lpattern lalpha fcolor fintensity falpha barwidth base ///
```

so the key is written on every build and read only by one of the two renderers. That is the
accepted-but-silently-dropped defect class 05-04's action text forbids creating, reopened
on the server path.

### 5. The per-option ground truth already in the repository

`test/fixtures/rejected_options.json` (produced by task 05-01, schema version 1, generated
2026-09-18) carries, for every one of the 50, a `reason`, a `takes_argument` flag and at
least one runnable probe pair. It is the authoritative statement of what each option is
*for* and which plot type exercises it, and it is what the new tests should be
parametrised from so they cannot go stale. Grouped by the `reason` string the fixture
records:

| fixture `reason` | options | representative probe (`dash_command`) |
|---|---|---|
| marker-label look beyond the five keys dash implements | `mlabangle` `mlabformat` `mlabstyle` `mlabtextstyle` `mlabvposition` | `dash scatter mpg weight, mlabformat(%9.0fc) name(g1)` |
| marker outline look — dash implements mcolor/mfcolor/mlcolor but not the outline width/alignment/style | `mlalign` `mlstyle` (`mlwidth`, already honoured) | `dash scatter mpg weight, mlalign(inside) name(g1)` |
| overall style shorthand — dash has `pstyle()` only | `alstyle` `astyle` `bstyle` `dstyle` `lstyle` `mstyle` | `dash line mpg weight, lstyle(p1) name(g1)` |
| CI/fit area look (`fitarea_options`) | `acolor` `alpattern` `alwidth` | `dash lfitci mpg weight, acolor(gs10) name(g1)` |
| line alignment for a filled outline | `alalign` `dlalign` `lalign` | `dash area mpg weight, lalign(inside) name(g1)` |
| dot-plot look — dash renders dot plots but accepts none of the `d*` look options | `dcolor` `dfcolor` `dlcolor` `dlstyle` `dlwidth` `dotextend` `dsize` `dsymbol` `ndots` | `dash dot mpg weight, dsymbol(Oh) name(g1)` |
| bar geometry beyond `barwidth()` | `baroffset` `gap` `mwidth` | `dash histogram mpg, gap(10) name(g1)` |
| area baseline suppression | `nodropbase` | `dash area mpg weight, nodropbase name(g1)` |
| paired-coordinate arrow look (`twoway pcarrow`) | `barbsize` `headlabel` `mangle` | `dash pcarrow y1 x1 y2 x2, mangle(30) name(g1)` |
| colour legend for a `colorvar` plot | `clegend` `plegend` | `dash scatter mpg weight, clegend(off) name(g1)` |
| colorvar colour-mapping control — dash implements a colorvar family under partly non-Stata spellings (`colpalette`/`colornlevels`/`colormissing`); every real Stata spelling here aborts | `colorend` `colorfillonly` `colorformissing` `colorkeysrange` `colorlevels` `colorlist` `colorrule` `colorstart` `colorvarminmax` | `dash scatter mpg weight, colorlevels(4) name(g1)` |
| plot-style cycling across layers | `pcycle` | `dash scatter mpg weight, pcycle(3) name(g1)` |

The `dash_rc: 198` values recorded in that fixture are the **05-01-era** measurement, before
05-04 landed the accept-and-report layer. REMAINING.md §2 supersedes them: at HEAD all 115
are accepted with **rc 0** and **0 rejections**. Use the fixture for *what each option
means and how to exercise it*, not for the current return code.

### 6. The honesty contract this phase must not break

`dash.ado:590-592`, verbatim, immediately above the plot-level `_dash_pending` block:

```
    // every option it names with two different values, asserting the
    // output does not change.  Implement one and forget to remove it
    // here, and that test fails.
    local _dash_pending ""
```

The test it names is `test/test_unsupported_report_is_true.py`. Its parametrised body reads
the `_dash_pending` block straight out of `dash.ado` with a regex
(`_pending()` at `:132-138`), renders the same spec twice with two different values of the
option, and asserts the two SHA-256 hashes are **equal** — i.e. that the option really does
nothing:

```python
@pytest.mark.parametrize("opt", sorted(set(_plot_pending())))
def test_a_plot_option_reported_unsupported_really_is(tmp_path, opt):
    a, b, ptype = PLOT_VALUES[opt]
```

A companion test, `test_every_pending_option_is_covered_here`, asserts that every name on
either `_dash_pending` block has an entry in the module's `PLOT_VALUES` dict, so adding a
name to the list without test values fails the suite too. REMAINING.md records the test's
two known weaknesses, which bear directly on this phase:

> And `test/test_unsupported_report_is_true.py` only tests ONE direction — for each option
> ON the pending list, that rendering twice does not change the output. Nothing asserts the
> converse: every option dash DECLARES must either change the rendered output or be named
> on `_dash_pending`. … The existing test also instantiates `dr.DashRenderer` only
> (test_unsupported_report_is_true.py:178) and never `ServerAppBuilder`, so it is blind to
> every server-mode gap by construction.

That blindness is exactly why item 1's defect survived a DONE claim.

---

## Epics

| epic | name | goal | items |
|---|---|---|---:|
| **21-A** | Server fill and marker-border parity | Finish `05-05` on the path it never reached: `falpha` and `mlcolor` honoured in the emitted `bokeh serve` app, including under `by()` and `by(total)`. | 1 |
| **21-B** | The per-glyph look surface | Implement the 32 style options that describe how a marker, a marker label, a line, an area, a bar, a CI band, a dot plot or an arrow is drawn, in both renderers. | 2, 3 |
| **21-C** | Colour mapping, colour legends and the style shorthands | Implement the 11 `colorvar()` colour-mapping and legend controls, plus the 4 style options whose values already arrive in the spec and are reported as ignored. | 4, 5 |

---

## User stories

### Epic 21-A — Server fill and marker-border parity

**US-21-A1.** *As a `dash serve` operator, I want `falpha()` and `mlcolor()` to change what
the served dashboard draws, so that a command I have already validated in
`dash build` produces the same picture when I serve it.*

- **Given** a spec containing `(area mpg weight, falpha(30))`
  **When** I render it with `DashRenderer` and with the app `ServerAppBuilder` emits
  **Then** both figures' `VArea` glyphs carry `fill_alpha == 0.30`, and neither falls back
  to `_SCHEME_AREA_ALPHA`.
- **Given** a spec containing `(scatter mpg weight, mlcolor(red))`
  **When** I render it in both modes
  **Then** both scatter glyphs carry the same resolved `line_color`, and `mlcolor(none)`
  sets `line_alpha == 0.0` in both.
- **Given** the same two specs with `by(foreign)` added
  **When** I build the emitted app
  **Then** every facet panel — and the `by(total)` panel when `total` is requested —
  carries the same `fill_alpha` / `line_color` as the unfaceted figure.
- **Given** an unparseable value such as `falpha(abc)` or `mlcolor(notacolour)`
  **When** I build in server mode
  **Then** the build returns rc 0 and the layer still draws, matching the standalone
  renderer's behaviour of warning and keeping the default.

**US-21-A2.** *As a package maintainer, I want the honesty contract checked against the
server renderer as well as the standalone one, so that an option can never again be
declared DONE on the strength of one renderer.*

- **Given** any option name serialized by `_dash_plot_opts_to_json`
  **When** the honesty test suite runs
  **Then** the option either changes the output of **both** renderers or is named on
  `_dash_pending`, and a failure message says which renderer dropped it.

### Epic 21-B — The per-glyph look surface

**US-21-B1.** *As a Stata user pasting a `twoway` command, I want the marker-label options I
already use — `mlabangle()`, `mlabformat()`, `mlabvposition()` — to be honoured, so that the
dashboard's point labels read the way my paper's figure does.*

- **Given** `dash scatter mpg weight, mlabel(make) mlabangle(45)`
  **When** the dashboard renders
  **Then** the `LabelSet` carries `angle == 0.7854` rad (45°) and `angle_units` consistent
  with it.
- **Given** `dash scatter mpg weight, mlabel(price) mlabformat(%9.0fc)`
  **When** the dashboard renders
  **Then** the label text reads `5,079` rather than `5079`, formatted through the same
  Stata-format machinery `_apply_mlabel_opts` already uses for `date_vars` and
  `numeric_formats`, and `mlabformat()` overrides the variable's own display format.
- **Given** `dash scatter mpg weight, mlabel(make) mlabvposition(pos)` where `pos` names a
  variable of clock positions
  **When** the dashboard renders
  **Then** each label's offset is taken per-row from that variable, not from the single
  `mlabposition()` default of `3`.

**US-21-B2.** *As a Stata user, I want `twoway dot`'s own look options to work, so that a
dot plot I copy in is not silently reduced to dash's defaults.*

- **Given** `dash dot mpg weight, dsymbol(Oh) dsize(large) dcolor(red) dfcolor(none)`
  **When** the dashboard renders
  **Then** the dot glyph is a hollow circle at the `large` size, stroked red with no fill.
- **Given** `dash dot mpg weight, ndots(50) dotextend(no) nodropbase`
  **When** the dashboard renders
  **Then** the dot density, the extension of the dotted guide line and the baseline drop
  each change observably from the default.

**US-21-B3.** *As a dashboard viewer, I want confidence bands and range plots to carry the
colour and outline the author asked for, so that two overlaid fits are distinguishable.*

- **Given** `dash lfitci mpg weight, acolor(gs10) alwidth(thin) alpattern(dash)`
  **When** the dashboard renders
  **Then** the band's `fill_color` resolves `gs10`, and its outline carries the translated
  width and dash pattern rather than no outline at all.
- **Given** `dash rbar lo hi weight, baroffset(0.2) mwidth`
  **When** the dashboard renders
  **Then** the bars are offset by 0.2 on the x scale and the `mwidth` flag changes the drawn
  bar width.

**US-21-B4.** *As a Stata user, I want `pcarrow`'s arrowhead options to be honoured, so that
a flow diagram copied from a `twoway` script keeps its arrowheads.*

- **Given** `dash pcarrow y1 x1 y2 x2, mangle(30) barbsize(3) headlabel`
  **When** the dashboard renders
  **Then** the arrowhead angle and barb size follow the given values and the head-end label
  is drawn instead of the tail-end one.

### Epic 21-C — Colour mapping, colour legends and the style shorthands

**US-21-C1.** *As a Stata user, I want the real Stata spellings of the `colorvar()` mapping
controls to work, so that I do not have to learn dash's invented `colpalette()` /
`colornlevels()` / `colormissing()` names.*

- **Given** `dash scatter mpg weight, colorvar(price) colorstart(yellow) colorend(red)`
  **When** the dashboard renders
  **Then** the `LinearColorMapper`'s palette runs from yellow to red, not the viridis
  default.
- **Given** `dash scatter mpg weight, colorvar(price) colorlevels(4)`
  **When** the dashboard renders
  **Then** the mapping is quantized into 4 levels, identically to today's
  `colornlevels(4)`, and both spellings are accepted.
- **Given** `dash scatter rep78 weight, colorvar(rep78) colorformissing(gs8)`
  **When** the dashboard renders
  **Then** missing `rep78` rows are drawn `gs8`, and the existing `colormissing()` spelling
  still works.
- **Given** `dash scatter mpg weight, colorvar(price) colorrule(linear)` and
  `… colorrule(intensity)`
  **When** both render
  **Then** the two produce observably different mappings, and an unrecognised rule warns
  once and falls back without aborting.

**US-21-C2.** *As a dashboard viewer, I want the colour key to be suppressible and
placeable, so that a small panel is not dominated by a colour bar.*

- **Given** `dash scatter mpg weight, colorvar(price) clegend(off)`
  **When** the dashboard renders
  **Then** no `ColorBar` and no `_dash_clegend` `Legend` is attached to the figure.
- **Given** `dash scatter mpg weight, colorvar(rep78) colordiscrete plegend(off)`
  **When** the dashboard renders
  **Then** the plot legend is suppressed while the colour key survives, and vice versa for
  `clegend(off)` alone.
- **Given** `dash scatter mpg weight, colorvar(price) colorkeysrange colorvarminmax`
  **When** the dashboard renders
  **Then** the key's range follows the requested rule rather than the data's observed
  min/max.

**US-21-C3.** *As a Stata user, I want `mstyle()`, `lstyle()`, `mlstyle()` and `colorlist()`
to stop appearing in dash's "ignoring unsupported option(s)" note, so that the note is a
trustworthy inventory of what is genuinely missing.*

- **Given** `dash scatter mpg weight, mstyle(p1)` and the same command with `mstyle(p3)`
  **When** both render
  **Then** the two outputs differ, and `mstyle` no longer appears in the note.
- **Given** `dash scatter mpg weight, colorvar(rep78) colorlist(red blue green orange)`
  **When** the dashboard renders
  **Then** the four categories take those four colours in order, and `colorlist` no longer
  appears in the note.
- **Given** any of the four is implemented
  **When** `test/test_unsupported_report_is_true.py` runs
  **Then** it passes because the name has been removed from `dash.ado`'s `_dash_pending`
  block in the same commit — not because the test was weakened.

---

## Business requirements

| id | requirement | how it is testable |
|---|---|---|
| **BR-21.1** | A `twoway` command using any of the 47 S09-style options must run under `dash` with **rc 0** and produce a dashboard whose appearance reflects every one of those options. | Re-run the `implement-S09-style` slice of `test/fixtures/rejected_options.json` and assert rc 0 **and** an output change for each option. |
| **BR-21.2** | After this phase, the `implement-S09-style` row of REMAINING.md §2's table must read **50 total / 50 honoured / 0 accepted-and-reported**, or — under fork (b) — **50 / 8 / 42 re-dispositioned to accept-and-report in the plan and the help**. | Re-run the §2 classification harness over the fixture. |
| **BR-21.3** | No option implemented by this phase may remain on a `_dash_pending` list, and no option this phase does not implement may be removed from one. The "ignoring unsupported option(s)" note must stay a true inventory. | `test/test_unsupported_report_is_true.py` passes unmodified in spirit; the new converse test (BR-21.6) covers the other direction. |
| **BR-21.4** | Every option this phase implements must behave identically in `dash build` (standalone) and `dash serve` / `dash build, server` (emitted app), or be explicitly and visibly declared server-pending. Silent per-mode divergence is prohibited — it is the defect that reopened `05-05`. | Parity assertions in `test/test_mode_parity.py`, extended to carry style options. |
| **BR-21.5** | `falpha()` and `mlcolor()` must be honoured in server mode on the main plot loop, the `by()` facet loop and the `by(total)` loop. | US-21-A1 acceptance criteria, asserted against the emitted app's built figures. |
| **BR-21.6** | The honesty contract must become bidirectional: every option `dash.ado` declares and serializes must either change rendered output in both renderers or be named on `_dash_pending`. | New converse test; it must fail at HEAD against `mlwidth` (standalone-only) and pass after Epic 21-A. |
| **BR-21.7** | An invalid value for any option in scope must never abort the build. It warns once, naming the option and the value, and the layer still draws — matching the established `mlcolor`/`mlwidth` precedent in `_apply_marker_opts`. | Adversarial values fed through the cscript corpus; assert rc 0 and a warning, per CLAUDE.md rules 16 and 18. |
| **BR-21.8** | Where dash already ships an invented spelling for a Stata concept (`colpalette` ↔ `colorlist`/`colorstart`/`colorend`, `colornlevels` ↔ `colorlevels`, `colormissing` ↔ `colorformissing`, `jseed` ↔ `jitterseed`), the Stata spelling must work and the dash spelling must keep working. Neither may be silently dropped. | Paired probes asserting the two spellings produce byte-identical output. |
| **BR-21.9** | Under fork (b), every name not implemented must be re-dispositioned in `.ultraplan/sections/section-09-axes-legend-titles.md`, added to the graph- or plot-level `_dash_pending` block with a `PLOT_VALUES` entry, and documented in `dash.sthlp` as permanently accept-and-report. No name may simply disappear. | Phase 30 gate; cross-check the fixture's `disposition` field against `_dash_pending`. |
| **BR-21.10** | Each of the 47 must have a minimum-abbreviation entry measured against Stata (Phase 18's `abbrev_truth.json` work), so that a user's abbreviated spelling resolves to the same canonical option `twoway` resolves it to. | `test/test_abbreviations.cscript` A7 collision guard over the extended truth file. |

---

## Technical requirements

### TR-21.1 — Preconditions from Phase 17 (hard)

The 43 names in items 2, 3 and 4 do not exist as keys in the spec JSON. Before any renderer
work, Phase 17 must have added each to `scripts/regen_option_surface.py`'s `PLOT`
inventory, regenerated the plot-level `syntax` block at `dash.ado:_dash_parse_plot_opts`
(`:475`), added each to the `foreach key` list in `_dash_plot_opts_to_json`
(`dash.ado:854`, list body at `:862-870`), and added each to the plot-level
`_dash_pending` block at `dash.ado:593-625` so it stays reported until this phase lands.
Two of the 43 are graph-level, not plot-level: `pcycle` and `clegend`/`plegend` behave as
graph-level look controls in `twoway`, and Appendix B records the rule — "The `t*`/`pc*`
family are graph-level (graph syntax block + the four `foreach gk`/`foreach gkey`
propagation lists); the style family is plot-level (plot syntax block +
`_dash_plot_opts_to_json`)". Confirm each of the three against `twoway`'s own help before
placing it, and record the decision in the generator's inventory rather than by hand —
Appendix B warns the generator is not idempotent and "silently deletes hand-added
declarations that are not in its inventory", including `sreturn local _pending` and
`sreturn local _unknown`, "which are the only channel feeding `_dash_report_ignored`".

Item 5 has no such precondition. `colorlist`, `lstyle`, `mlstyle` and `mstyle` are already
declared, already `sreturn local`-ed (`dash.ado:703-705`, `:712`), already in the
`_dash_plot_opts_to_json` `foreach key` list (`dash.ado:869-870`) and already on
`_dash_pending` (`dash.ado:600`, `:610`, `:613`, `:614`). Their values reach
`plot["options"]` today; only the renderer half is missing.

### TR-21.2 — Item 1: the seven server sites

All line numbers are `dash_render.py` at HEAD. Everything after `:12265`
(`class ServerAppBuilder`) is emitted-app source held as Python string literals, so an edit
there is an edit to a string, and the emitted program must still be syntactically valid.

| # | site | line | what it reads today | what item 1 adds |
|---:|---|---:|---|---|
| 1 | main loop, `elif ptype in ('area',)` | 14265–14286 | `fcolor` → `_ar_fill`; `fintensity` → `_ar_alpha`, default `_SCHEME_AREA_ALPHA` | `falpha`/`fa` → `_ar_alpha` (value/100, clamped 0–1), winning over `fintensity` in the same precedence `_apply_fill_opts` uses |
| 2 | main loop, `elif ptype == 'bar'` | 14288 | `fcolor`, `fintensity`, `barwidth`/`width`, `base` | same `falpha` branch |
| 3 | main loop, `elif ptype == 'histogram'` | 14133 | `fcolor` → `_hist_fill`; `fintensity` → `_hist_alpha`, default `_SCHEME_BAR_ALPHA`; `_hist_line = 'white'` | same `falpha` branch |
| 4 | main loop, `elif ptype == 'rarea'` | 14429 | `fcolor` → `_ra_fill`; `fintensity` → `_ra_alpha`, default `_SCHEME_AREA_ALPHA` | same `falpha` branch |
| 5 | main loop, `elif ptype == 'rbar'` | 14457 | `bfcolor` then `fcolor` → `_rb_fill`; `_rb_line = 'white'` | same `falpha` branch |
| 6 | `by()` facet loop | 15150–15151 | nothing — `fill_alpha=_SCHEME_AREA_ALPHA` hardcoded; `size=6`, `width=0.8`, `line_width=_SCHEME_LINE_WIDTH` likewise | `falpha` and `mlcolor` from `opts` |
| 7 | `by(total)` loop | 15251–15252 | identical hardcoded copy on `_tot_fig`/`_tot_src` | same |

The two CI bands at `:14375` (`lfitci`, hardcoded `_lfci_alpha = 0.2`) and `:14402`
(`qfitci`) carry the same `fcolor`/`fintensity` shape and are the natural extension of the
same change; REMAINING.md §4 records that `fpfitci`'s band is missing from server mode
entirely, which is Phase 07's item, not this one.

`mlcolor` has **no** site in the emitted app at all — the scatter branch sets only `color`.
The change is to resolve `opts.get('mlcolor')` through the emitted `_resolve_color` helper
into `line_color` on the scatter glyph, with `mlcolor(none)` → `line_alpha=0.0`, mirroring
`dash_render.py:2845-2861` exactly.

The strongly preferred implementation is **not** to hand-copy the logic seven times. Emit a
single helper into the app — e.g. `_fill_alpha_for(opts, default)` and
`_marker_border_for(opts)` — beside the existing emitted `_resolve_color`, and call it from
each site. Seven hand-written copies is the defect shape Phase 05–08 exists to remove.

### TR-21.3 — Item 2: marker and marker-label options

Twelve names: `mlabangle` `mlabformat` `mlabstyle` `mlabtextstyle` `mlabvposition` `mlalign`
`mwidth` `dsymbol` `dsize` `dstyle` `dcolor` `dfcolor`.

`GlyphMapper._apply_mlabel_opts` is at `dash_render.py:3301`. Its docstring records exactly
what it reads today:

> Reads ``mlabel``, ``mlabcolor``, ``mlabsize``, ``mlabposition``, and ``mlabgap`` from
> *options* and adds a Bokeh ``LabelSet`` to *fig*.

and it has thirteen call sites (`:3482`, `:3556`, `:3589`, `:3657`, `:3762`, `:3814`,
`:4955`, `:5000`, `:5038`, `:5103`, `:5144`, `:5288`, `:5367`), so a change there reaches
scatter, line, connected, area, bar, the range family, dropline and `rcapsym` at once.

- `mlabangle(#)` → `LabelSet.angle` in radians (`math.radians(value)`), matching the
  precedent set by the axis grammar, where `angle(45)` becomes `0.7854` rad
  (REMAINING.md Appendix B, "Three findings worth pulling out first", table row
  `, angle(45)` → `0.7854` rad).
- `mlabformat(fmt)` → route the label text through the same Stata-format path
  `_apply_mlabel_opts` already owns. At `:3330-3350` it builds a derived text column
  `f"__mlabel__{mlabel_var}"` when `self.date_vars` or `self.numeric_formats` has an entry
  for the variable; `mlabformat()` supplies that format explicitly and must take
  precedence over the variable's own. The mapper already carries `date_vars` and
  `numeric_formats`, assigned at `dash_render.py:8141-8142`.
- `mlabvposition(varname)` → a per-row clock position, replacing the scalar
  `pos = options.get("mlabposition", "3")` at `:3369` with a vectorised `x_offset` /
  `y_offset` pair derived from a column. Validate `varname` with the same
  `re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", …)` guard `_apply_colorvar` uses at `:3022`
  (CLAUDE.md rule 16) and ignore the option if the column is absent, exactly as
  `_apply_mlabel_opts` already does for a missing `mlabel` column at `:3324`.
- `mlabstyle(p1)` / `mlabtextstyle(body)` → resolve through the scheme rather than
  hardcoding. `mlabtextstyle(body)` maps onto the scheme's body text size/colour, which
  Phase 23/24 is making available; until then, resolve to the existing
  `_TEXTBOX_DEFAULTS` values and note the dependency.
- `mlalign(inside|outside|center)` → Bokeh has no per-glyph line alignment, so this is a
  half-pixel `line_width` adjustment or a documented no-op. If it is a genuine no-op it
  must **say so**, not be silently accepted — REMAINING.md's note on `sort` is the
  precedent: "note `sort` is reported 'unsupported' although dash sorts by default; if that
  is a no-op it should say so, not imply the plot is wrong."
- `mwidth` is a flag (`takes_argument: false`) and the fixture's probe is
  `dash rbar lo hi weight, mwidth name(g1)` with reason "bar geometry beyond
  `barwidth()`". Although this phase groups it with the marker family, its implementation
  lands in `map_rbar` (`dash_render.py:4958`), not in the marker path. Follow the fixture.
- The dot-plot five — `dsymbol` `dsize` `dstyle` `dcolor` `dfcolor` — land in
  `GlyphMapper.map_dot` (`dash_render.py:5178`). `dsymbol` reuses
  `OptionTranslator.translate_msymbol` (`:1402`), `dsize` reuses `translate_msize`
  (`:1428`), `dcolor`/`dfcolor` reuse `parse_color_alpha` (`:1275`) and
  `translate_mcolor` (`:1331`). Note that `map_dot` already builds its own sub-source
  (`_dl_cols`, `:5254-5259`) so that `mlabel()` can find its column; the new options must
  be applied to the glyph that source feeds, at `:5288`.

### TR-21.4 — Item 3: line, area, bar, CI, dot and arrow options

Twenty names: `acolor` `alalign` `alpattern` `alstyle` `alwidth` `astyle` `bstyle` `lalign`
`dlalign` `dlcolor` `dlstyle` `dlwidth` `barbsize` `baroffset` `gap` `nodropbase`
`dotextend` `ndots` `headlabel` `mangle`.

Target symbols, all `GlyphMapper` methods in `dash_render.py`:

| method | line | options it must learn |
|---|---:|---|
| `map_area` | 3592 | `astyle` `lalign` `nodropbase` |
| `map_bar` | 3660 | `bstyle` `gap` |
| `map_histogram` | 4636 | `gap` (the fixture's probe for `gap` is a histogram) |
| `map_rarea` | 4920 | `astyle` `lalign` |
| `map_rbar` | 4958 | `bstyle` `baroffset` `gap` |
| `map_rspike` / `map_rcap` / `map_rcapsym` | 5003 / 5041 / 5291 | `lalign` where a filled outline exists |
| `map_dot` | 5178 | `dlalign` `dlcolor` `dlstyle` `dlwidth` `dotextend` `ndots` |
| `map_pcarrow` | 5660 | `barbsize` `headlabel` `mangle` |
| `map_lfitci` / `map_qfitci` / `map_lpolyci` / `map_fpfitci` | 3918 / 3998 / 4344 / 4569 | `acolor` `alalign` `alpattern` `alstyle` `alwidth` — the `fitarea_options` family |

Translators to reuse rather than reinvent: `OptionTranslator.translate_lwidth` (`:1459`)
for `alwidth`/`dlwidth`, `translate_lpattern` (`:1484`) for `alpattern`,
`parse_color_alpha` (`:1275`) for `acolor`/`dlcolor`. The CI band's fill is written today
by the same `_apply_fill_opts` path as any other fill (`dash_render.py:2920`), so `acolor`
is a colour source that must lose to an explicit `fcolor()` in the same precedence order
`_apply_fill_opts` already establishes.

`nodropbase` and `dotextend(no)` are suppressions: they remove the baseline drop and the
dotted guide extension respectively. Implement them as the absence of a glyph, and make the
test assert glyph *count*, because an alpha-zero glyph would pass a colour assertion.

### TR-21.5 — Item 4: colour mapping and colour legends

Eleven names: `clegend` `colorend` `colorfillonly` `colorformissing` `colorkeysrange`
`colorlevels` `colorrule` `colorstart` `colorvarminmax` `pcycle` `plegend`.

The whole family lands in `GlyphMapper._apply_colorvar`, `dash_render.py:2995-3300`. That
method's own docstring lists the five dash spellings that exist today
(`dash_render.py:3005-3011`):

```
    colorvar(varname)   — variable whose values drive the color mapping
    colordiscrete       — treat a numeric variable as discrete categories
    coloruseplegend     — add a plot legend instead of a ColorBar
    colornlevels(#)     — quantize continuous data into # equal-width levels
    colorcuts(numlist)  — custom cut-point boundaries for continuous data
    colormissing(color) — Bokeh color for missing/NaN values (default: grey)
    colpalette(name)    — palette name; see _PALETTE_MAP for supported keys
```

and the fixture's reason for the whole group is the precise statement of the gap: "dash
implements a colorvar family under partly non-Stata spellings (`colpalette`/
`colornlevels`/`colormissing`); every real Stata spelling here aborts."

Mapping, spelling by spelling — BR-21.8 requires both sides keep working:

| Stata spelling | existing dash spelling | mechanism |
|---|---|---|
| `colorlevels(#)` | `colornlevels(#)` | alias into the same quantization branch |
| `colorformissing(c)` | `colormissing(c)` | alias into the same missing-colour branch |
| `colorstart(c)` / `colorend(c)` / `colorlist(…)` (item 5) | `colpalette(name)` only | build a palette from the given endpoints or explicit list, in place of a `_PALETTE_MAP` lookup (the `colpalette` value is read at `dash_render.py:3032`; the `_PALETTE_MAP.get` lookups are at `:3195` and `:3253`) |
| `colorrule(linear\|intensity\|hue)` | — | selects how values map onto the ramp; an unrecognised rule warns once and falls back |
| `colorkeysrange` / `colorvarminmax` | — | flags (`takes_argument: false`) that override the key's range derivation |
| `colorfillonly` | — | flag: colour the fill only, leaving the marker outline at the layer colour |
| `clegend(off\|…)` | — | suppress or configure the colour key. The two objects it governs are built at `dash_render.py:3240-3243` (the categorical `Legend`, `name=_COLORVAR_LEGEND_NAME`) and `:3266-3272` (the continuous `ColorBar`) |
| `plegend(off\|…)` | `coloruseplegend` | governs the *plot* legend, not the colour key; `coloruseplegend` is already on `_dash_pending` and honest |
| `pcycle(#)` | — | graph-level: how many layers before the plot-style cycle repeats. Touches the per-plot colour assignment, not `_apply_colorvar` |

The two key-bearing constructions, verbatim at HEAD:

```python
            fig.add_layout(
                Legend(items=legend_items, title=html.escape(var_display),
                       name=_COLORVAR_LEGEND_NAME),
                "right",
            )
```

```python
                fig.add_layout(
                    ColorBar(color_mapper=mapper, label_standoff=8,
                             width=12, location=(0, 0),
                             title=html.escape(var_display)),
                    "right",
                )
```

`_COLORVAR_LEGEND_NAME` is `"_dash_clegend"` (`dash_render.py:595`), with the per-factor
placeholder legends named `f"_clegend_{factor}"` (`:3225`) and `"_clegend___missing__"`
(`:3232`); `DashRenderer` filters on that prefix at `:9006`. `clegend(off)` must remove or
suppress **both** objects and leave that filter working.

Three constraints carried from REMAINING.md that this item must not break:

1. **The colour key's placement is owned by another phase.** "Honour legend(position()
   ring()) for the colorvar colour key and the continuous ColorBar; both are hardcoded to
   the 'right' panel. `GlyphMapper._apply_colorvar` does not receive graph_options, so this
   needs either a plumbing change or a post-pass in `_rebuild_legend` (which today
   deliberately filters `_dash_clegend` legends out of the clock-position move)." That
   plumbing change is Phase 25's, and `clegend()` needs the same `graph_options` it does —
   coordinate, do not duplicate.
2. **The ColorBar has no scheme chrome.** "The continuous colorvar() ColorBar takes no
   scheme chrome at all. Only its palette was considered; its background, border,
   tick-label size/colour and title size/colour are Bokeh defaults, so an economist or
   s2color dashboard draws a white colour bar with #444444 13px text over a themed plot
   region." Also Phase 25. `clegend()` should configure, not fight, whatever that phase
   sets.
3. **`colorvar()` does not exist in server mode at all.** "colorvar() has no implementation
   whatsoever in ServerAppBuilder … a served dashboard silently drops the option entirely
   (no mapper, no colour key, no colour bar). dash.ado parses and serializes it
   (`dash.ado:564-565`, `:673`, `:865`), so the key is written and never read on this
   path." That port is tagged `[func · server · L]` in REMAINING.md and belongs to the
   server-unification phases. **Item 4 must therefore either (i) land after that port, or
   (ii) implement the eleven in `DashRenderer` and add each to a server-pending
   declaration** so BR-21.4's no-silent-divergence rule holds. Option (ii) is the smaller
   change and is the recommended sequencing; record the choice in the commit message.

### TR-21.6 — Item 5: the four whose values already arrive

`colorlist` `lstyle` `mlstyle` `mstyle`. Confirmed at HEAD:

```
dash.ado:600:    if `"`colorlist'"' != "" local _dash_pending `"`_dash_pending' colorlist"'
dash.ado:610:    if `"`lstyle'"'    != "" local _dash_pending `"`_dash_pending' lstyle"'
dash.ado:613:    if `"`mlstyle'"'   != "" local _dash_pending `"`_dash_pending' mlstyle"'
dash.ado:614:    if `"`mstyle'"'    != "" local _dash_pending `"`_dash_pending' mstyle"'
dash.ado:703:    sreturn local mstyle           `"`mstyle'"'
dash.ado:704:    sreturn local lstyle           `"`lstyle'"'
dash.ado:705:    sreturn local mlstyle          `"`mlstyle'"'
dash.ado:712:    sreturn local colorlist        `"`colorlist'"'
```

and in `_dash_plot_opts_to_json`'s `foreach key` list at `dash.ado:869-870`
(`… mstyle lstyle mlstyle mlpattern … colorlist jitterseed`). So `plot["options"]["mstyle"]`
is present in every spec that sets it, and no renderer reads it. The work is:

1. Add a resolver — the natural home is `OptionTranslator` (`dash_render.py:1002`) — that
   turns a Stata plot style name (`p1` … `p15`, and the `pN<glyphclass>` variants) into the
   concrete colour / symbol / width / pattern quadruple the scheme already parses.
   `SchemeParser` is the source (`dash_render.py:1509` onward) and the existing per-plot
   colour cycle is the consumer.
2. Apply it in the per-plot style paths: `mstyle` before the marker options in
   `_apply_marker_opts` (`:2749`) so explicit `mcolor()`/`msymbol()` still win; `lstyle`
   before `_apply_line_opts` (`:2703`); `mlstyle` for the marker border (the `mlcolor`/
   `mlwidth` block at `:2845-2866`).
3. `colorlist(c1 c2 …)` builds an explicit categorical palette in `_apply_colorvar`,
   short-circuiting the `_PALETTE_MAP` lookups at `:3195` and `:3253` (the `colpalette`
   value itself is read at `:3032`). Split on whitespace, resolve
   each through `parse_color_alpha`, and if the list is shorter than the factor count,
   cycle it — matching Stata.
4. **Delete the four `_dash_pending` lines** at `dash.ado:600`, `:610`, `:613`, `:614`, in
   the same commit. Leaving them makes
   `test/test_unsupported_report_is_true.py::test_a_plot_option_reported_unsupported_really_is`
   fail, by design.

**A decision this item forces.** The plan currently disposes `pstyle` to *permanent*
accept-and-report (task 05-05: "`pstyle`, `recast`, `cmissing` and `connect` are
accept-and-report permanently") while dispositioning `mstyle`, `lstyle` and `mlstyle` —
and, in item 3, `astyle`, `bstyle`, `dstyle` and `alstyle` — to implement. Those seven are
the same mechanism as `pstyle` applied to different glyph classes; the fixture's reason
for all of them is one string, "overall style shorthand (mstyle/lstyle/astyle/bstyle/
dstyle/alstyle). dash has pstyle() only." Implementing the seven while `pstyle()` stays a
no-op is defensible only if `pstyle()` is implemented on the same resolver. Decide once,
record the decision in `.ultraplan/sections/section-05-option-surface.md` and
`section-09-axes-legend-titles.md`, and apply it to all eight names.

### TR-21.7 — Cross-cutting requirements

- **Input hardening (CLAUDE.md rule 16).** Every option in scope takes a user string
  straight from a Stata command line into a Bokeh property. Any option whose value names a
  *variable* (`mlabvposition`) must be validated with
  `re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", …)` before use, as `_apply_colorvar` does at
  `dash_render.py:3022`. Any option whose value becomes rendered text must pass through
  `html.escape`, as the colour key's title does. Colour values go through
  `parse_color_alpha` / `_resolve_color` and never into a CSS or JS string directly.
- **Failure mode (BR-21.7).** Warn once with `warnings.warn(..., UserWarning)`, name the
  option and the value, keep the default, keep drawing. The established phrasing is
  `f"dash: mlcolor({options['mlcolor']}) is not a recognised colour; ignoring it."`
  (`dash_render.py:2858-2860`).
- **Server carry.** For each option implemented in `GlyphMapper`, either the emitted app
  reads it too (because `GlyphMapper` is copied into the emitted source — see Risks) or the
  option is declared server-pending. No third option.
- **Dead-list hygiene.** `_dash_graph_opts_to_json` at `dash.ado:891` is, per REMAINING.md,
  "a fifth, DEAD, stale copy of the graph-option list that the generator does not
  maintain". Do not add any graph-level name from this phase to it; Phase 18 owns deleting
  it.

---

## Work items

Every item is reproduced with the tags, location and evidence it was handed over with.

---

### Item 1 — Route `falpha` and `mlcolor` through the server builder's fill-bearing branches

> Route `falpha` and `mlcolor` through the server builder's fill-bearing branches (area,
> bar, histogram, rarea, rbar) and the two facet copies. 05-05 left them standalone-only.

| | |
|---|---|
| **Kind** | functional |
| **Renderer** | server |
| **Effort** | medium |
| **Where** | `dash_render.py:14265-14286` and sibling branches; facet copies at `:15151` and `:15252` |
| **Origin** | `S05` (task 05-05), REMAINING.md main body — "17 DONE claims the adversarial pass overturned" |
| **Epic** | 21-A |

**Evidence.** The refutation row verbatim: "| 05-05 | `falpha` and `mlcolor` never routed
through the server builder's fill-bearing branches |". Confirmed by count: `falpha` occurs
3× in `dash_render.py` and **0×** after `:12265`; `mlcolor` 6× and **0×**. Both keys are
serialized by `dash.ado:_dash_plot_opts_to_json` on every build (`dash.ado:862-870`), so
the value is written and read by one renderer only. The seven sites, what each reads today
and what each must add, are tabulated in TR-21.2; the `area` branch is quoted verbatim in
"Why this phase exists" §4. The facet copies read nothing — REMAINING.md: "Every other
serialized plot option is silently discarded on that path … The branch hardcodes `size=6`,
`width=0.8`, `line_width=_SCHEME_LINE_WIDTH`."

---

### Item 2 — Implement the marker- and label-style options from the 43

> Implement the marker- and label-style options from the 43: `mlabangle` `mlabformat`
> `mlabstyle` `mlabtextstyle` `mlabvposition` `mlalign` `mwidth` `dsymbol` `dsize` `dstyle`
> `dcolor` `dfcolor`.

| | |
|---|---|
| **Kind** | functional |
| **Renderer** | both |
| **Effort** | large |
| **Where** | `dash_render.py:GlyphMapper._apply_mlabel_opts` (`:3301`), marker option translation (`_apply_marker_opts`, `:2749`), `map_dot` (`:5178`), `map_rbar` (`:4958`) |
| **Origin** | `OPT-S09S`, REMAINING.md §2 |
| **Epic** | 21-B |

**Evidence.** All twelve are in REMAINING.md §2's list of 47 and Appendix A's list of 43
("not declared" — the value never reaches the spec). All twelve return **zero** occurrences
as a quoted key in `dash_render.py`. `_apply_mlabel_opts`'s docstring states the five keys
it does read — `mlabel`, `mlabcolor`, `mlabsize`, `mlabposition`, `mlabgap` — and the
fixture's reason for the `mlab*` five is exactly "marker-label look beyond the five keys
dash implements". A sixth marker-label key, `mlabwidth`, is read and discarded at
`dash_render.py:3398` (`options.get("mlabwidth")  # consumed; no-op`) and is correctly on
`_dash_pending` at `dash.ado:611`; it is *not* in this phase's scope. The dot-plot five
carry the fixture reason "dash renders dot plots but accepts none of the `d*` look
options". `mwidth` is a flag whose fixture probe is `dash rbar lo hi weight, mwidth
name(g1)` with reason "bar geometry beyond `barwidth()`" — see TR-21.3.

---

### Item 3 — Implement the line-, area-, bar- and CI-style options from the 43

> Implement the line-, area-, bar- and CI-style options from the 43: `acolor` `alalign`
> `alpattern` `alstyle` `alwidth` `astyle` `bstyle` `lalign` `dlalign` `dlcolor` `dlstyle`
> `dlwidth` `barbsize` `baroffset` `gap` `nodropbase` `dotextend` `ndots` `headlabel`
> `mangle`.

| | |
|---|---|
| **Kind** | functional |
| **Renderer** | both |
| **Effort** | large |
| **Where** | `dash_render.py:map_area` (`:3592`) / `map_bar` (`:3660`) / `map_rarea` (`:4920`) / `map_rbar` (`:4958`) / `map_dot` (`:5178`) / `map_pcarrow` (`:5660`) and the CI band builders `map_lfitci` (`:3918`), `map_qfitci` (`:3998`), `map_lpolyci` (`:4344`), `map_fpfitci` (`:4569`) |
| **Origin** | `OPT-S09S`, REMAINING.md §2 |
| **Epic** | 21-B |

**Evidence.** All twenty are in the 43; all return zero occurrences as a quoted key. The
fixture groups them by purpose and supplies a runnable probe for each — `fitarea_options`
(`acolor` `alpattern` `alwidth`), filled-outline alignment (`alalign` `dlalign` `lalign`),
the style shorthands (`alstyle` `astyle` `bstyle` `dstyle`), dot-plot look (`dlcolor`
`dlstyle` `dlwidth` `dotextend` `ndots`), bar geometry beyond `barwidth()` (`baroffset`
`gap`), area baseline suppression (`nodropbase`) and the `pcarrow` arrowhead
(`barbsize` `headlabel` `mangle`). The per-method allocation is in TR-21.4.

---

### Item 4 — Implement the colour-mapping and legend options from the 43

> Implement the colour-mapping and legend options from the 43: `clegend` `colorend`
> `colorfillonly` `colorformissing` `colorkeysrange` `colorlevels` `colorrule` `colorstart`
> `colorvarminmax` `pcycle` `plegend`. These drive the `colorvar()` colour key and the
> continuous ColorBar.

| | |
|---|---|
| **Kind** | functional |
| **Renderer** | both |
| **Effort** | large |
| **Where** | `dash_render.py:GlyphMapper._apply_colorvar` (`:2995-3300`), the ColorBar builder (`:3266-3272`) and the colour-key legend builder (`:3240-3243`) |
| **Origin** | `OPT-S09S`, REMAINING.md §2 |
| **Epic** | 21-C |

**Evidence.** All eleven are in the 43; all return zero occurrences as a quoted key —
`clegend`'s six matches in the file are the internal legend *name* `"_dash_clegend"`
(`:595`), the per-factor placeholders `"_clegend_{factor}"` and `"_clegend___missing__"`
(`:3225`, `:3232`), the prefix filter that reads them (`:9006`), and two prose comments
that mention the `clegend()` option without implementing it (`:594`, `:9103`). None is a
consumer of the option. The fixture's reason for nine of them is "colorvar colour-mapping control. dash
implements a colorvar family under partly non-Stata spellings (`colpalette`/
`colornlevels`/`colormissing`); every real Stata spelling here aborts", for `clegend` and
`plegend` it is "colour legend for a colorvar plot", and for `pcycle` it is "plot-style
cycling across layers". Three constraints from REMAINING.md bind this item and are stated
in full in TR-21.5: the colour key's placement is hardcoded to `"right"` and its plumbing is
Phase 25's; the ColorBar has no scheme chrome at all; and `colorvar()` "has no
implementation whatsoever in ServerAppBuilder", confirmed here by a count of **0**
occurrences of `colorvar` and of `ColorBar` after `:12265`.

---

### Item 5 — Implement the declared-but-pending style options

> Implement the declared-but-pending style options: `colorlist` `lstyle` `mlstyle`
> `mstyle`. They reach the spec today and are reported as ignored.

| | |
|---|---|
| **Kind** | functional |
| **Renderer** | both |
| **Effort** | medium |
| **Where** | `dash_render.py:OptionTranslator` (`:1002`), the per-plot style paths (`_apply_marker_opts` `:2749`, `_apply_line_opts` `:2703`, the marker-border block `:2845-2866`, `_apply_colorvar` `:2995-3300`, palette selection at `:3032`/`:3195`/`:3253`) |
| **Origin** | `OPT-S09S`, REMAINING.md §2 |
| **Epic** | 21-C |

**Evidence.** REMAINING.md Appendix B names these four among the 23 that "are reported as
ignored AND already serialized with their value … waiting on S06/S09/S10 renderer work, not
on `dash.ado`". Confirmed at HEAD: each has an `sreturn local` (`dash.ado:703-705`,
`:712`), each is in `_dash_plot_opts_to_json`'s `foreach key` list (`:869-870`), and each is
on the plot-level `_dash_pending` block (`:600`, `:610`, `:613`, `:614`). None occurs as a
quoted key in `dash_render.py`. The four `_dash_pending` lines must be deleted in the same
commit that implements them — `dash.ado:590-592` says so in the source: "Implement one and
forget to remove it here, and that test fails." The `pstyle` disposition conflict this item
forces is set out in TR-21.6.

---

## Test plan

Project rules 4 and 8 both bind here. **Rule 8:** every one of these is a reported defect,
so each gets a regression test written *first*, failing against HEAD. **Rule 4:** every new
function — each resolver, each translator, each emitted helper — gets a unit test.

### Epic 21-A — Server fill and marker-border parity

**The failing test to write first.** New file `test/test_server_fill_options.py`:

```
test_server_area_honours_falpha            # build the emitted app from a spec with
                                           # falpha(30); assert VArea.fill_alpha == 0.30
test_server_scatter_honours_mlcolor        # assert Scatter.line_color == resolved red
test_server_facet_area_honours_falpha      # same spec + by(foreign); assert per panel
test_server_total_panel_honours_falpha     # same spec + by(foreign, total)
```

At HEAD all four fail: `falpha` and `mlcolor` occur zero times in the emitted source, so the
`area` branch returns `_SCHEME_AREA_ALPHA` and the scatter branch leaves `line_color` at its
Bokeh default. Build the app the way `test/test_server.py` and
`test/test_server_build_options.py` already do, rather than inventing a new harness.

**Unit tests (rule 4).** Each helper emitted by TR-21.2 — `_fill_alpha_for(opts, default)`
and `_marker_border_for(opts)` — gets a table-driven test over: absent key → default;
`falpha(0)` → 0.0; `falpha(100)` → 1.0; `falpha(150)` → clamped, warns; `falpha(abc)` →
default, warns; `fa(30)` alias → 0.30; `falpha` beating `fintensity` when both are set;
`mlcolor(none)` → `line_alpha == 0.0`; `mlcolor(notacolour)` → default, warns once.

**Integration / cscript.** Extend `test/test_serve_options.cscript` and
`test/test_server_build.cscript` with a `dash build, server` over a spec carrying
`falpha()` and `mlcolor()` under `by()`, asserting rc 0 and that the emitted `.py` compiles
(`python3 -m py_compile`). The emitted app is generated source, so a syntax error there is a
build break invisible to pytest.

**The converse honesty test (BR-21.6).** Extend
`test/test_unsupported_report_is_true.py` with a third parametrised test: for every option
name in `dash.ado`'s `_dash_plot_opts_to_json` `foreach key` list, assert it either (a)
changes the rendered output of **both** `DashRenderer` and the emitted app, or (b) appears
on a `_dash_pending` block. The module today instantiates `dr.DashRenderer` only at
`:162-178`; parametrise `_render` over the two renderers. **This test must fail at HEAD
against `falpha`, `mlcolor` and `mlwidth`** — that failure is its proof of life.

**Mutation checks (prove non-vacuity).**

| break this | this test must die |
|---|---|
| Revert the `falpha` branch in the emitted `area` site (`:14265-14286`) | `test_server_area_honours_falpha` |
| Revert only the `by()` facet copy (`:15151`), leaving the main loop fixed | `test_server_facet_area_honours_falpha` |
| Revert only the `by(total)` copy (`:15252`) | `test_server_total_panel_honours_falpha` |
| Change the clamp from `min(1.0, …)` to no clamp | the `falpha(150)` unit row |
| Re-add `falpha` to a `_dash_pending` block | the converse test, from the other side |

### Epic 21-B — The per-glyph look surface

**The failing test to write first.** New file `test/test_style_options.py`, parametrised
**directly from `test/fixtures/rejected_options.json`** — filter
`disposition == "implement-S09-style"` and take each entry's `probes[0].dash_command`, so
the corpus cannot drift from the fixture:

```
test_style_option_changes_output[<option>]   # render the probe spec with value A and
                                             # value B; assert the two SHA-256 hashes differ
```

Reuse the `_norm` / `_render` helpers from `test/test_unsupported_report_is_true.py`
(`:158-178`) rather than writing a second hashing harness; the difference is that this test
asserts **inequality** where that one asserts equality. At HEAD every row for items 2 and 3
fails: the option is not declared, so it never reaches `plot["options"]` and the two renders
are identical.

**Unit tests (rule 4), by target symbol.**

| test file | covers |
|---|---|
| `test/test_options.py` | `OptionTranslator` additions: angle conversion for `mlabangle`, `translate_lwidth` on `alwidth`/`dlwidth`, `translate_lpattern` on `alpattern`, `translate_msymbol`/`translate_msize` on `dsymbol`/`dsize` |
| `test/test_dropline_marker_options.py` | `map_dot` — `dsymbol` `dsize` `dstyle` `dcolor` `dfcolor` `dlalign` `dlcolor` `dlstyle` `dlwidth` `dotextend` `ndots`, each asserted on the built glyph |
| `test/test_glyphs.py` | `map_area` / `map_bar` / `map_histogram` — `astyle` `bstyle` `lalign` `gap` `nodropbase` |
| `test/test_range_plots.py` | `map_rarea` / `map_rbar` / `map_rspike` / `map_rcap` — `baroffset` `mwidth` `lalign` |
| `test/test_paired_coordinate_plots.py` | `map_pcarrow` — `mangle` `barbsize` `headlabel` |
| `test/test_lpolyci_options.py` and `test/test_fit_grid_parity.py` | the CI band family — `acolor` `alalign` `alpattern` `alstyle` `alwidth` across `map_lfitci` / `map_qfitci` / `map_lpolyci` / `map_fpfitci` |
| `test/test_html_output.py` | `_apply_mlabel_opts` — `mlabangle` angle in radians, `mlabformat` text content, `mlabvposition` per-row offsets, and the rejection of a non-identifier `mlabvposition()` value |

**Integration / cscript.** Add a `test/test_style_options.cscript` that runs each fixture
probe command in Stata, asserting rc 0, and that dash's "ignoring unsupported option(s)"
note no longer names the option. `test/test_option_surface.cscript` is the model for the
reporting assertions (its existing checks are O2-01 … O2-07). Add the same probes to
`test/test_conformance.cscript`'s corpus so the release gate's "zero `r(198)`, zero dropped
series" assertion covers them.

**Mutation checks.**

| break this | this test must die |
|---|---|
| Make `mlabangle` set degrees instead of radians | the `mlabangle` unit row (`0.7854` assertion) |
| Make `mlabformat` fall back to the variable's own format when both are present | the `mlabformat` precedence row |
| Implement `nodropbase` as `alpha=0` rather than as a removed glyph | the glyph-**count** assertion in `test_glyphs.py` |
| Accept a non-identifier `mlabvposition(1;drop)` | the injection row in `test_html_output.py` |
| Re-add any of the twelve/twenty names to `_dash_pending` | `test_style_option_changes_output[<name>]` and the converse test |
| Delete one name from the generator inventory and regenerate | `test_style_option_changes_output` for that name, plus `test_every_pending_option_is_covered_here` |

### Epic 21-C — Colour mapping, colour legends and the style shorthands

**The failing test to write first.** Extend `test/test_colorvar_legend.py`:

```
test_clegend_off_removes_the_colour_key    # no ColorBar and no Legend named
                                           # _dash_clegend on the figure
test_colorstart_colorend_build_the_ramp    # LinearColorMapper.palette endpoints
test_colorlevels_matches_colornlevels      # the two spellings render identically
test_colorformissing_matches_colormissing  # ditto
test_colorlist_sets_categorical_palette    # item 5
test_plegend_off_keeps_the_colour_key      # the two legends are independent
```

At HEAD every one fails — none of the eleven names exists in `dash_render.py`, so the
option is inert.

**Unit tests (rule 4).** `_apply_colorvar`'s new branches, each in isolation against a
constructed `ColumnDataSource`: palette construction from `colorstart`/`colorend`, from
`colorlist` (including a list shorter than the factor count, which must cycle), the
`colorrule` selector including an unrecognised value (warn once, fall back, do not raise),
the two range flags (`colorkeysrange`, `colorvarminmax`), `colorfillonly`, and the
`varname` identifier guard. Put the style-shorthand resolver's own tests in
`test/test_options.py` and its scheme lookups in `test/test_scheme_consumption.py`, which
already owns the "every parsed key has a consumer" assertions.

**Integration / cscript.** Add the eleven fixture probes plus item 5's four to
`test/test_style_options.cscript`. Because `colorvar()` is absent from the server app
entirely, add an explicit assertion for whichever branch of TR-21.5's fork is taken: either
a server parity assertion in `test/test_mode_parity.py`, or a server-pending report
assertion proving the note names the option in server mode.

**Mutation checks.**

| break this | this test must die |
|---|---|
| Make `clegend(off)` remove the ColorBar but leave the `_dash_clegend` Legend | `test_clegend_off_removes_the_colour_key` |
| Make `colorlevels` a silent alias that ignores its argument | `test_colorlevels_matches_colornlevels` (render with 4 and with 8) |
| Break the `colorlist` cycle so a short list raises `IndexError` | the short-list unit row |
| Make an unrecognised `colorrule` raise instead of warning | the fallback unit row, and BR-21.7's rc-0 cscript assertion |
| Leave `mstyle` on `_dash_pending` after implementing it | `test_a_plot_option_reported_unsupported_really_is[mstyle]` |
| Let `mstyle(p1)` override an explicit `mcolor(red)` | the precedence row in `test_options.py` |

### Suite-level gates

Per CLAUDE.md rule 5, before any commit: pull `main`, run the full pytest suite and the full
certification suite (from `test/`, under `arch -arm64`; a skip is not a pass), and fix
forward until green. The baseline to beat is REMAINING.md's recorded HEAD state:

> At HEAD the first four pass (3,498 passed / 37 skipped; 25/25 cscripts);
> the fifth fails on §1.

Per rule 18, generate three adversarial cases per option family: an auth/identifier-bypass
case (`mlabvposition(1); DROP`), an injection case (a colour or format value carrying
`</script>` and a UTF-8 homoglyph), and a resource-exhaustion case (`colorlevels(1e9)`,
`ndots(1e9)`, a `colorlist()` with 10,000 entries). Each must be rejected or clamped, never
executed and never allowed to allocate unboundedly. `test/test_security_surface.py` and
`test/test_resource_limits.py` are the existing homes.

---

## Definition of done

A reviewer can tick these in order.

**Scope and fork**

- [ ] The §2 fork is recorded: (a) implement all, or (b) implement the subset. If (b), the
      names dropped are listed in `.ultraplan/sections/section-09-axes-legend-titles.md`,
      remain on `_dash_pending` with `PLOT_VALUES` entries, and are documented in
      `dash.sthlp` (BR-21.9).
- [ ] The `pstyle` / `mstyle` / `lstyle` / `mlstyle` / `astyle` / `bstyle` / `dstyle` /
      `alstyle` disposition conflict (TR-21.6) is decided once and applied to all eight.

**Item 1 (Epic 21-A)**

- [ ] `falpha`/`fa` is read at all five main-loop fill sites: `area` (`:14265`), `bar`
      (`:14288`), `histogram` (`:14133`), `rarea` (`:14429`), `rbar` (`:14457`).
- [ ] `falpha` and `mlcolor` are read in the `by()` facet loop (`:15151`) and the
      `by(total)` loop (`:15252`).
- [ ] `mlcolor` is read in the emitted scatter branch, including `mlcolor(none)` →
      `line_alpha = 0.0`.
- [ ] The logic is emitted once as a shared helper, not copied seven times.
- [ ] `grep` for `falpha` and `mlcolor` after `dash_render.py:12265` returns non-zero.
- [ ] The emitted app still compiles (`python3 -m py_compile` on a generated `.py`).

**Items 2–5 (Epics 21-B, 21-C)**

- [ ] All 43 previously-undeclared names appear as consumed keys in `dash_render.py` —
      re-running the §3 probe returns `0` names with zero occurrences.
- [ ] `colorlist`, `lstyle`, `mlstyle`, `mstyle` are consumed **and** their four
      `_dash_pending` lines (`dash.ado:600`, `:610`, `:613`, `:614`) are deleted.
- [ ] Both spellings work for every aliased pair (BR-21.8): `colorlevels`/`colornlevels`,
      `colorformissing`/`colormissing`, `colorlist`+`colorstart`+`colorend`/`colpalette`.
- [ ] No option in scope remains on any `_dash_pending` block, and no out-of-scope option
      was removed from one.
- [ ] Every implemented option either works in both renderers or is explicitly declared
      server-pending (BR-21.4); no silent per-mode divergence remains.

**Tests**

- [ ] Every test named in the test plan exists, and each was demonstrated to fail against
      HEAD before its fix (rule 8) — record the failing run in the commit message.
- [ ] Every new function has a unit test (rule 4).
- [ ] Every mutation row in the test plan was performed and killed its named test.
- [ ] The converse honesty test (BR-21.6) exists, runs against both renderers, and fails
      when any declared-and-serialized option is dropped by either.
- [ ] `test/test_style_options.py` and `test/test_style_options.cscript` are parametrised
      from `test/fixtures/rejected_options.json`, not from a hand-written list.
- [ ] Three adversarial cases per option family pass (rule 18).

**Gates and paperwork**

- [ ] Full pytest suite green; full certification suite green with honest skips (25/25
      cscripts), run from `test/` under `arch -arm64`.
- [ ] Conformance corpus: zero `r(198)`, zero dropped series, zero dropped graphs.
- [ ] `CHANGELOG` entry naming the option families implemented.
- [ ] `dash.sthlp` updated (or Phase 30 ticket filed) — it currently describes a smaller
      option surface.
- [ ] Committed to `feature/batch4-interactive-layer` (or a branch off it), never directly
      to `main`, with the merge command supplied (rule 6) and no vendor names in the
      message (rule 7).

---

## Risks and sequencing notes

**R1 — Item 1 edits code Phase 06 intends to delete.** The five main-loop branches and the
two facet copies are precisely the hand-written dispatch that REMAINING.md §4 calls
"15-03's unfinished collapse showing through": "`ServerAppBuilder` holds **51 `ptype ==`
comparisons** across ~4,000 emitted lines; exactly **one** (`scatter`) delegates to
`_DASH_MAPPER`." If Phase 06 lands first and routes the facet branch through the copied
`GlyphMapper` — which is what REMAINING.md recommends, "route the facet branch through the
copied `GlyphMapper` (the `_glyph_layer_lines()` machinery S15-03 already added for the
unfaceted branch)" — then item 1's sites 6 and 7 vanish and `falpha`/`mlcolor` arrive for
free. *Mitigation:* write item 1's four failing tests first regardless of ordering. They are
behaviour assertions, not implementation assertions, so they survive the collapse and become
Phase 06's regression guard. If Phase 06 is imminent, implement only sites 1–5 and let the
tests for 6 and 7 stay red under an explicit `xfail` tied to Phase 06.

**R2 — `GlyphMapper` is copied into the emitted app, so items 2–5 may reach the server for
free — or may not.** Phase 11's analysis records that `GlyphMapper` is copied into the
emitted server app verbatim at `dash_render.py:12344` and `:12408`. Where an option is
implemented inside a `GlyphMapper` method that the emitted app actually calls, the server
gets it automatically; where the emitted app has its own hand-written branch for that
`ptype` (which, per §4, is 35 of 36 types), it does not. *Mitigation:* do not assume either
way. BR-21.4 is satisfied by a test, not by inspection — every option in scope gets a
parity row in `test/test_mode_parity.py`, and the ones that turn out not to carry are
declared server-pending with a note.

**R3 — Item 4 collides with Phase 25.** `clegend()` needs `graph_options` inside
`_apply_colorvar`, which does not receive it; Phase 25 is making the same plumbing change
for `legend(position() ring())` and for the ColorBar's scheme chrome. Two phases editing
`dash_render.py:3240-3272` independently will conflict. *Mitigation:* sequence item 4 after
Phase 25, or agree that Phase 25 owns the `graph_options` plumbing and item 4 consumes it.
Do not do the plumbing twice.

**R4 — `colorvar()` does not exist in server mode, so item 4 can only reach one renderer.**
Stated in REMAINING.md as a `[func · server · L]` item of its own. The recommended path is
TR-21.5 option (ii): implement the eleven in `DashRenderer`, declare them server-pending,
and let the server port land with the colorvar port. The risk of option (i) — waiting — is
that item 4 blocks on a large unrelated piece of work.

**R5 — The style shorthands straddle two epics.** `mstyle`, `lstyle` and `mlstyle` are in
item 5 (Epic 21-C) while `astyle`, `bstyle`, `dstyle` and `alstyle` are in item 3 (Epic
21-B), and `pstyle` is in neither. All eight are one mechanism. *Mitigation:* build the
resolver once, in `OptionTranslator`, as the first commit of whichever epic starts first,
and have the other epic consume it. Sequencing items 3 and 5 adjacently costs nothing and
removes the duplication risk entirely.

**R6 — The dot-plot family straddles items 2 and 3.** `dsymbol` `dsize` `dstyle` `dcolor`
`dfcolor` are item 2; `dlalign` `dlcolor` `dlstyle` `dlwidth` `dotextend` `ndots` are item
3. Both land in `GlyphMapper.map_dot` (`dash_render.py:5178`). *Mitigation:* do them in one
sitting; `map_dot` also has a subtlety recorded in the source at `:5254-5259` — it builds a
narrowed `_dl_cols` source so `mlabel()` can find its column — and the new options must be
applied to the glyph that source feeds at `:5288`.

**R7 — The generator is not idempotent, and its splice has already double-applied.**
REMAINING.md: "The generator's splice has ALREADY double-applied in the committed dash.ado
— the generated blocks are duplicated at HEAD … the banner appears 4 times (twice per
syntax block)". Any regeneration triggered by this phase will produce an unreadable diff and
can delete `sreturn local _pending` / `sreturn local _unknown`, "which are the only channel
feeding `_dash_report_ignored`". *Mitigation:* Phase 18 owns both fixes and is a hard
dependency. Do not regenerate `dash.ado` from this phase.

**R8 — Abbreviation collisions.** Adding 43 names to the declared set will shorten nothing
and may lengthen existing minimums. REMAINING.md: "dash currently accepts shorter prefixes
than twoway precisely because it declares fewer options (measured:
`dash scatter mpg weight, mlabel(make) mlabs(3)` → `"mlabsize":"3"`, while twoway also has
mlabstyle/mlabtextstyle). `resolve_minimums()` in the generator asserts on ambiguity, so
adding these names with real measured minimums may trip that assert and force longer
minimums than existing dash do-files use." This phase adds `mlabstyle` and `mlabtextstyle`
— the exact two named in that example. *Mitigation:* Phase 18's `abbrev_truth.json`
extension must land first, and `test/test_abbreviations.cscript`'s A7 collision guard must
be green before any of item 2 is written. Expect `mlabs` to stop resolving to `mlabsize`;
that is a user-visible change and belongs in the CHANGELOG.

**R9 — Adjacent observation, not an item.** The count in §3 shows `mlwidth` occurs 4× in
`dash_render.py` and **0×** after `:12265`, so it is honoured in standalone and dropped in
server mode, exactly like `mlcolor`. It is one of the three options REMAINING.md §2 counts
as "honoured", and it is not in this phase's item list. It is recorded here because item
1's change touches the same marker-border code path and the converse honesty test (BR-21.6)
will fail against it. Either fix it alongside `mlcolor` — it is two lines on the same helper
— or file it, but do not let the converse test be weakened to hide it.

**Recommended order within the phase:** item 1 → item 5 (unblocked at HEAD, and it builds
the style resolver) → item 3 → item 2 → item 4 (last, for R3 and R4).
