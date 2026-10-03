# Remaining work to finish the ultraplan

Audit of all 89 tasks across 16 sections against `ca5fe35`
(`feature/batch4-interactive-layer`, 61 commits ahead of `main`, tree clean).

Everything below was **measured**, not read off the CHANGELOG. Where a claim
came from a source other than a direct measurement, the source is named.

---

## Headline

The plan's *structural* work landed. Its *coverage* work did not.

Fourteen schemes are translated and faithful; the parser, the statistical
rules, the transport layer and the server root fix are all real and tested.
But five things stand between this branch and "finished":

1. **A real `net install` produces a package whose schemes are all unreachable.**
   Every scheme in the package — the whole of S03 and the first binding
   decision — is inert as installed. No test catches this.
2. **92 of the 111 options the plan dispositioned "implement" are still
   accepted-and-reported rather than implemented.**
3. **`scheme()` warns and falls back where the binding decision says it must
   error.** The path-traversal surface the plan said to retire is still open.
4. **The standalone/server parity guard covers 17 of 36 plot types, and five
   of the unguarded ones have already drifted** — including `function` and
   `pci`, which draw *nothing* in server mode, and `fpfitci`, which loses its
   confidence band there.
5. **A per-plot `if` qualifier is silently ignored by every computed layer.**
   `(lfit mpg weight if foreign==1)` draws the *all-rows* fit. Wrong numbers,
   no warning.

Nothing here is speculative: every number was produced by running the code.

---

## 1. Blocker — `net install` breaks every scheme  [S02, S03, S11]

Reproduced end to end with Stata, not modelled:

```
net set ado "<clean dir>"
net install dash, from("<repo>")     -> rc 0, "installation complete."
```

Stata routes the manifest into **letter subdirectories**:

| manifest line | where Stata actually puts it |
|---|---|
| `f dash.ado` | `<dir>/d/dash.ado` |
| `f dash_render.py` | `<dir>/py/dash_render.py` |
| `f schemes/s1color.scheme` | `<dir>/s/s1color.scheme` |
| `f schemes/economist.scheme` | `<dir>/e/economist.scheme` |

`SchemeParser` searches exactly two places, both relative to
`dash_render.py` (`dash_render.py:1524-1532`):

```python
_SCHEMES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schemes")
_SCHEME_SEARCH_DIRS = (_SCHEMES_DIR, os.path.dirname(os.path.abspath(__file__)))
```

From `<dir>/py/` that is `<dir>/py/schemes` and `<dir>/py` — neither exists.
The comment above those lines anticipates *one* flattening
(`<install dir>/x.scheme`); Stata uses a third layout it does not cover.

Measured from the installed copy:

```
. dash scatter mpg weight, name(g1) scheme(s1color)
. dash build, saving(...)
UserWarning: dash: scheme 's1color' was not found ... using s2color
UserWarning: dash: no scheme file could be resolved for the dashboard
  (searched <dir>/py/schemes, <dir>/py). Falling back to built-in defaults.
  The package's schemes/ directory appears to be missing
```

The build returns rc 0 and writes a file, so nothing fails loudly. Every
installed user silently gets built-in defaults instead of the translated
StataCorp schemes.

**Why no test caught it.** `test/test_packaging.py:89-123` is a
`shutil` model of `net install` — "no network, no Stata" — and models only
two layouts, `flat` (basename in dest) and `as-declared` (keeps `schemes/`).
Stata's real layout is neither. S02-04 asked for an "end-to-end
packaged-install certification script" and S16-06 for "`net install` into a
clean directory ... and run every example"; **no cscript performs a
`net install`** (`grep -rn "net install" test/*.cscript` → nothing).

**Scope, measured.** The package otherwise works: all **12 example do-files
run from the packaged install with rc 0**. But **all 12 also emit the
scheme-fallback warning** — so the breakage is exactly and only the scheme
layer, and it is silent at the Stata prompt.

**Work:** widen the scheme search to the sibling letter directories (and the
install root), *and* replace the shutil model with a cscript that does a real
`net install` and asserts a named scheme survives it.

---

## 2. Blocker — the option surface  [S05-04, S07, S09, S10]

Every one of the 115 options in `test/fixtures/rejected_options.json` was
re-run through `dash` in Stata at HEAD and classified by dash's own report.

| plan disposition | total | honoured | accepted + reported ignored |
|---|---:|---:|---:|
| accept-and-report | 4 | 0 | 4 ✅ *as intended* |
| implement-S06 | 3 | 0 | **3** |
| implement-S07 | 25 | 12 | **13** |
| implement-S09-axes-text | 28 | 2 | **26** |
| implement-S09-style | 50 | 3 | **47** |
| implement-S10 | 5 | 2 | **3** |
| **total** | **115** | **19** | **96** |

**0 rejections.** The drop-in claim holds at the syntax layer and decision 4
(accept, never abort, report together) is satisfied — but **92 options the
plan said to implement are only accepted and reported**, so their values
never reach the spec.

Not implemented, by family:

- **S06 (3):** `horizontal` `sort` `vertical`
  — note `sort` is reported "unsupported" although dash sorts by default; if
  that is a no-op it should say so, not imply the plot is wrong. [WP-29 P0.1, commit b0d170d: partly closed; open: `horizontal`, `vertical`]
- **S07 (13):** `adjust` `area` `atobs` `ciplot` `discrete` `estcmd` `estopts`
  `fitplot` `logit` `mean` `nofit` `noweight` `predopts`
- **S09 axes/text (26):** `b1title` `b2title` `droplines` `l1title` `l2title`
  `r1title` `r2title` `t1title` `t2title` `text` `tlabel` `tline` `tmlabel`
  `tmtick` `tscale` `ttext` `ttick` `ttitle` `xmlabel` `xmtick` `xvarformat`
  `xvarlabel` `ymlabel` `ymtick` `yvarformat` `yvarlabel`
- **S09 style (47):** `acolor` `alalign` `alpattern` `alstyle` `alwidth`
  `astyle` `barbsize` `baroffset` `bstyle` `clegend` `colorend`
  `colorfillonly` `colorformissing` `colorkeysrange` `colorlevels`
  `colorlist` `colorrule` `colorstart` `colorvarminmax` `dcolor` `dfcolor`
  `dlalign` `dlcolor` `dlstyle` `dlwidth` `dotextend` `dsize` `dstyle`
  `dsymbol` `gap` `headlabel` `lalign` `lstyle` `mangle` `mlabangle`
  `mlabformat` `mlabstyle` `mlabtextstyle` `mlabvposition` `mlalign`
  `mlstyle` `mstyle` `mwidth` `ndots` `nodropbase` `pcycle` `plegend`
- **S10 (3):** `fxsize` `fysize` `scale`

The 11 `t*`/`pcarrow` options were re-probed on `tsset` monthly data and
`pcarrow` variables to rule out a harness artefact; all 11 are ignored.

**Two defensible ways to close this**, and the choice is the user's:
**(a)** implement all 92 — the plan as written; **(b)** implement the high-value
subset (`text` `ttitle`/`tlabel` family, the `b1/l1/r1/t1title` set,
`mlabformat` `mstyle` `lstyle` `acolor` `gap` `fxsize` `fysize` `scale`) and
formally re-disposition the rest to accept-and-report in the plan and help.

---

## 3. Binding decision 1 is violated  [S11-05]

`PLAN.md:36-37` — `scheme()` is "**restricted** to the translated set with a
clear error naming the supported names — never a silent fallback to black or
to `s2color`." S11-05 adds: validate "in **Stata**, where the user sees the
error", and retire the arbitrary-`.scheme`-file path, "which also removes the
path-traversal surface".

Measured at HEAD:

| required | actual |
|---|---|
| error naming the set | `warnings.warn(...)` then `_raw_name = ""` → **`s2color`** (`dash_render.py:7970-7982`) |
| validated in Stata | `dash.ado` has **no** scheme-name validation |
| `.scheme` file path retired | `SchemeParser._resolve_path` still resolves `name.endswith(".scheme")` from the CWD (`:1691-1714`); `_resolve_scheme_name` explicitly exempts it (`not _raw_name.endswith(".scheme")`) |
| help matches code | `dash.sthlp:1084` still tells users to "put its Stata-format `.scheme` file in the working directory" |

So a typo in `scheme()` silently produces the wrong aesthetic, and the
path-traversal surface the plan wanted closed is still reachable.

---

## 4. S15 — the parity guard covers less than half the surface, and five layers have already drifted

**The collapse is 1/46 done.** `ServerAppBuilder` holds **51 `ptype ==`
comparisons** across ~4,000 emitted lines; exactly **one** (`scatter`)
delegates to `_DASH_MAPPER`. 39 `map_*` methods exist.

**The guard is narrower than it reads.** The parity corpus is 32 cases over
**17 distinct plot types**, against **36 server `ptype` branches** — so
**19 types are unguarded** (`fpfit` `fpfitci` `function` `lfitci` `lowess`
`pcbarrow` `pci` `pcspike` `qfit` `qfitci` `rarea` `rbar` `rcap` `rconnected`
`rline` `rscatter` `rspike` `tsline` `tsrline`). It also never constructs a
spec with `by()`, KPIs, `filter()`, `link()` or `tabs()` — grep for each of
those keys in the corpus returns 0.

**Five of the 19 have already drifted.** Measured at HEAD by building both
renderers' figures from the same spec and diffing every glyph property. Spec
shapes were taken from `dash.ado`'s own emission (`yvar1`/`yvar2` for range
plots, `expr` for `function`, `points` for `pci`) and columns that exist:

| type | standalone | server | consequence |
|---|---|---|---|
| **`fpfitci`** | `VArea`(α .2) + `Line` | `Line` only | **the confidence band is missing in server mode** |
| **`function`** | `Line` | *nothing* | **server-mode `function` draws no layer** |
| **`pci`** | `Segment` | *nothing* | **server-mode `pci` draws no layer** |
| `lowess` | `#1f77b4`, width 1 | `#1a476f`, width 1.5 | **standalone `lowess` ignores the scheme** (matplotlib's default blue) |
| `rscatter` | marker size 8.0 | marker size 6 | two default size tables |

`test_conformance.cscript`'s "every layer drew something" assertion runs in
**standalone mode only**, which is precisely why the two server-mode layers
that draw nothing are invisible to it.

These five are new defects, not plan items. Under project rule 8 each needs a
regression test that fails first — the natural home is widening the parity
corpus to all 36 types, which closes the class rather than the instances.

**Also unification-shaped:** none of S09's axis/title/legend work reached
`ServerAppBuilder`. `_parse_axis_label` appears 4× in the renderer and **0×**
in the emitted app, so the whole `xlabel()` grammar is absent from
`dash serve` / `dash build, server`. (Agent-reported, path confirmed here.)

## 5. Blocker — per-plot `if` is ignored by every computed layer  [S06-06]

`dash (scatter mpg weight) (lfit mpg weight if foreign==1)` draws the fit for
**all 74 cars**, not the 22 foreign ones. Measured, with the key `dash.ado`
actually emits (`if_expr`, written at `dash.ado:1240` and `:1244`, read at
`dash_render.py:9951`):

| layer | per-plot `if_expr` |
|---|---|
| `lfit` | **ignored** — identical y to the unqualified fit |
| `qfit` | **ignored** |
| `kdensity` | **ignored** |

Ground truth for that command, from Stata:

```
regress mpg weight if foreign==1   ->  slope -.01042596, intercept 48.918297
regress mpg weight                 ->  slope -.00600869, intercept 39.440284
```

dash draws the second.

**Why.** The qualifier is implemented as a `CDSView`/`BooleanFilter` over the
graph's shared `ColumnDataSource` (`dash_render.py:9957-9990`). That correctly
restricts which *rows of that source* a glyph draws — but a computed layer
builds its **own** source from `self.df`, unfiltered, and the view never
touches it. The comment there explains at length why a CDSView was chosen over
a private source (`link()` and the filter callback only reach shared sources);
the reasoning is sound for raw-data layers and simply does not carry to
computed ones.

A single-plot command is unaffected: `dash.ado:1483` promotes a lone segment's
qualifier to the graph level, where `_apply_graph_filter` does filter the data.
The defect is specific to per-plot qualifiers in multi-layer commands — which
is ordinary `twoway` usage.

This is the worst-shaped defect in the list: a statistical command that
returns a confidently wrong number, silently. Under project rule 8 it needs a
failing regression test before the fix.

## 6. Resource limits still open  [S13, S14, S16-04]

Confirmed absent at HEAD — no constant, no clamp:

- **`_MAX_IPS` is an eviction primitive, not a limiter.** One machine cycling
  10,000 forwarded keys took 300 sessions inside a 60-second window against a
  nominal 60. Needs a different structure, not a larger cap. (Project rule 3.)
- **Dropdown filter on a continuous variable** emits one `<option>` per
  distinct value, uncapped — 200,001 options on 200,000 observations.
  (`_MAX_FILTER_OPTIONS`/`_MAX_DROPDOWN`: not defined.)
- **`by()` has no group cap** — `by(id)` builds one figure per value.
  (`_MAX_BY_GROUPS`/`_MAX_FACETS`/`_MAX_TABS`: not defined.)

---

## 7. Release closeout  [S16-06, S16-07]

- **`net install` + run every example** — the gate S16-06 names. Item 1 above
  means it does not pass today.
- **Responsive verification at 375/768/1440px** — S10's procedure, re-run
  against the current build.
- **`BUGS.md`** holds 73 entries, all `[x]`. S16-07 asks for every defect this
  plan fixed to be recorded; the count needs reconciling against the
  CHANGELOG's defect list.
- **`TODO.md` / `PLAN.md`** last touched at `5f857fc`; S16-07 asks that they no
  longer describe an overtaken roadmap.
- **Merge command** to be reported, not run (project rule 6).

### Advisory, outside the plan

`dash.pkg` carries its version only as prose (`d Version: 1.0.0 25mar2026`).
There is no `v` line and no `d Distribution-Date:` line, so `adoupdate` can
never detect an update, and the stated date is six months stale. The manifest
itself is complete — all 20 declared files exist and nothing shippable is
missing.

---

## Status by section

Sources: ① measured this session; ② deep-audit agent; ③ CHANGELOG (self-reported).

| # | Section | Tasks | Status | What is left |
|---|---|---:|---|---|
| 01 | Baseline, env, test integrity | 6 | 4 done, 2 partial ② | runner skip-accounting regression test; BASELINE.md coverage note |
| 02 | Packaging (`net install`) | 4 | **partial** ① | real `net install` cscript; scheme search paths |
| 03 | Scheme translation | 5 | 3 done, 2 partial ② | `color foreground`; all 14 inert once installed ① |
| 04 | Abbreviations | 5 | 4 done, 1 partial ② | narrow |
| 05 | Option surface | 6 | **05-04 not done** ① | 92 options declared nowhere |
| 06 | Varlist / plot-spec | 7 | 2 done, 5 partial ② | `horizontal` `sort` `vertical` ①; positional plot-options across an expanded varlist; **no S06 entry in CHANGELOG** ② [WP-29 P0.1, commit b0d170d: partly closed; open: `horizontal`, `vertical`, positional plot-options across an expanded varlist, no S06 entry in CHANGELOG] |
| 07 | Statistical defaults | 6 | done ③, 13 options open ① | see §2 |
| 08 | Formats, dates, labels | 6 | 2 done, 4 partial ② | `xvarformat` `yvarformat` `xvarlabel` `yvarlabel` ①; `test_formats.cscript` absent ② |
| 09 | Axes, legend, titles | 7 | 1 done, 6 partial ②, **73 options open** ① | see §2 — largest single family; none of S09 reached `ServerAppBuilder` |
| 10 | Geometry | 4 | 2 done, 2 partial ② | `fxsize` `fysize` `scale` ① |
| 11 | Scheme consumption | 6 | **11-05 not done** ①, 6 partial ② | error not warning; Stata-side validation; retire `.scheme` path; help; scheme-driven **text sizing** (title, note, subtitle, mlabel) still ignored ② |
| 12 | Layout, tabs, facets | 5 | 5 partial ② | `by()` group cap ①; `layout(s1:1,1 s2:1,1)` still drops a graph silently outside Bootstrap ② |
| 13 | Linking, filters, KPI | 6 | 3 done, 3 partial ② | dropdown option cap ① |
| 14 | Server root fix | 5 | 2 done, 3 partial ② | `_MAX_IPS` structure ①; no `_rc` check after the six shell browser launches ② |
| 15 | Unification | 4 | **15-03 1/46; 5 live drifts** ① | 45 undelegated branches; corpus covers 17/36 types, no `by()`/KPI/filter/`link()`/`tabs()` |
| 16 | Help, conformance, release | 7 | 16-01..05 done ③ | 16-06, 16-07 gated on §1 |

---

## Suggested order

0. **Per-plot `if` on computed layers (§5).** Wrong numbers outrank everything
   else. Compute the layer from the qualified frame, then view it.
1. **Scheme search paths + a real `net install` cscript.** Smallest change,
   largest correctness gain, and it unblocks the S16-06 release gate.
2. **S11-05.** Turn the warning into a Stata-side error, retire the CWD
   `.scheme` path, fix `dash.sthlp:1084`. Closes a binding decision and a
   security surface together.
3. **The three resource caps.** Each is a constant plus a clamp plus a test.
4. **S05-04 + S07/S09/S10 options.** The bulk. Decide (a) or (b) from §2
   first — that decision sizes everything after it.
5. **S15-03.** Mechanical, guarded by the parity corpus; can proceed in
   parallel with 4 since it touches the emitted app rather than `dash.ado`.
6. **S16-06 / S16-07.** The six gates, then the merge command.

## Gates still to pass (S16-07)

full pytest · full certification suite with honest skips · conformance corpus
(zero `r(198)`, zero dropped series, zero dropped graphs) · parity corpus ·
clean `net install` runs every example · adversarial suite.

At HEAD the first four pass (3,498 passed / 37 skipped; 25/25 cscripts);
the fifth fails on §1.



---

## Final tally, after the adversarial pass

All 16 section audits and all 12 applicable refute passes returned (28 agents,
2,068 tool calls). S11, S12, S15 and S16 had no DONE claim left to refute.

| | DONE | PARTIAL | NOT DONE |
|---|---:|---:|---:|
| **89 tasks** | **19** | **68** | **2** |

Per section — DONE / PARTIAL / NOT DONE:

| S01 | S02 | S03 | S04 | S05 | S06 | S07 | S08 |
|---|---|---|---|---|---|---|---|
| 3/3/0 | 1/2/**1** | 1/4/0 | 3/2/0 | 3/3/0 | 2/5/0 | 2/4/0 | 1/5/0 |

| S09 | S10 | S11 | S12 | S13 | S14 | S15 | S16 |
|---|---|---|---|---|---|---|---|
| 0/7/0 | 0/4/0 | 0/6/0 | 0/5/0 | 2/4/0 | 1/4/0 | 0/4/0 | 0/6/**1** |

**Read PARTIAL carefully — it is not "half-built".** In most cases the audit
found the defect the task was written against genuinely fixed and proven
load-bearing by mutation, with a *secondary* deliverable missing: a cscript
the TDD stubs named, a CHANGELOG entry, a help sentence, a no-caller test.
S12 is the clearest example — "every one of the five named defects is
genuinely fixed at HEAD and I proved each fix load-bearing by mutation"; all
five are PARTIAL on paperwork. The two NOT_DONE are 02-04 (the packaged-install
cscript) and 16-07 (close-out, which is gated on everything else).

### 17 DONE claims the adversarial pass overturned

All to PARTIAL; 10 small, 5 medium, 1 large, 1 cosmetic.

| task | what the refutation found |
|---|---|
| 01-03 | guards hold under attack, but `kdensity` is declared scipy-dependent in five places and provably is not; `dash_render.py:43-49` still lists scipy/statsmodels as hard dependencies |
| 02-01 | the manifest test is strong, but the regression net TR-02.4 names is absent |
| 03-03 | 14 translations independently re-derived exact (1,610 properties, 0 disagreements); `color foreground`/`text`/`tick_label` still absent from the fixture |
| 03-04 | cosmetic — two marker slots moved *toward* Stata; record-keeping only |
| 04-03 | `T() B() L() R()` never added to `_dash_parse_plot_opts`, so the folding code at `dash.ado:534-537` is dead |
| 05-01 | corpus missing probes for `at()`, `ciopts()`, `fitopts()`, `lineopts()`, `mlpattern()` |
| 05-05 | `falpha` and `mlcolor` never routed through the server builder's fill-bearing branches |
| 06-05 | `scatteri` marker labels missing from the server app |
| 06-06 | **large** — per-plot `if`/`in` is not applied where a CDSView cannot carry it: every computed glyph (`lfit`, `qfit`, `lowess`, `mband`, `histogram`, `kdensity`) computes from unqualified rows |
| 07-02 | no value-asserting test for the `c(level)` row |
| 07-04 | the session level never reaches the server plot loop |
| 08-03 | out-of-range period values raise instead of coercing to `NaT` |
| 09-06 | `missing()` misses Stata's *string* missing; a missing bound in a range is mishandled |
| 10-01 | the KPI-span test the section's own stub named is absent |
| 10-03 | facet ratios never thread into `_auto_bs_layout` |
| 13-04 | the brush callback does not carry `dash_pctl`, so percentile KPIs are wrong under brushing |
| 14-01 | both server-fixture `__enter__` paths can leak a process on failure |

Two of these are functional, not paperwork, and belong beside the four
blockers: **06-06** (computed layers ignore `if`/`in`) and **13-04**
(percentile KPIs wrong under brushing).

---

# Appendix A — eight tasks reviewed in detail

Reviewed at `187a786` on `feature/batch4-interactive-layer` (the only branch
consulted). Every line below was measured by running code at HEAD; where an
earlier pass in this file said something different, the measurement here
supersedes it and says so.

Throughout, **"server"** means the Python source `ServerAppBuilder` emits for
`bokeh serve` (everything after `dash_render.py:12265`), and **"standalone"**
means `DashRenderer`. Line numbers quoted in the plan itself are stale — the
file grew from ~10,455 to ~16,000 lines — so everything here is located by
symbol.

## 05-04 — Declare the options destined for later sections · PARTIAL

The reporting half is sound: all 115 options in
`test/fixtures/rejected_options.json` are accepted with rc 0, and 96 are named
in a `dash: ignoring unsupported option(s):` note. Nothing is silently dropped.

The declaring half is not. `dash.ado` declares 158 option tokens across its
`syntax` blocks and tracks 39 more in `_dash_pending`. Cross-referencing
against the 111 options the plan dispositioned "implement":

| disposition | total | declared | **not declared** |
|---|---:|---:|---:|
| implement-S06 | 3 | 3 | 0 |
| implement-S07 | 25 | 12 | **13** |
| implement-S09-axes-text | 28 | 15 | **13** |
| implement-S09-style | 50 | 7 | **43** |
| implement-S10 | 5 | 5 | 0 |
| **total** | **111** | **42** | **69** |

**Remaining: declare and serialize these 69.** They reach `dash.ado` only
through the trailing `*` catch-all, so no value ever arrives in the spec JSON
and the sections that own them have nothing to read — which is exactly the
state 05-04 exists to end.

- **S07 (13):** `adjust` `area` `atobs` `ciplot` `discrete` `estcmd` `estopts`
  `fitplot` `logit` `mean` `nofit` `noweight` `predopts`
- **S09 axes/text (13):** `droplines` `tlabel` `tline` `tmlabel` `tmtick`
  `tscale` `ttext` `ttick` `ttitle` `xvarformat` `xvarlabel` `yvarformat`
  `yvarlabel`
- **S09 style (43):** `acolor` `alalign` `alpattern` `alstyle` `alwidth`
  `astyle` `barbsize` `baroffset` `bstyle` `clegend` `colorend`
  `colorfillonly` `colorformissing` `colorkeysrange` `colorlevels` `colorrule`
  `colorstart` `colorvarminmax` `dcolor` `dfcolor` `dlalign` `dlcolor`
  `dlstyle` `dlwidth` `dotextend` `dsize` `dstyle` `dsymbol` `gap`
  `headlabel` `lalign` `mangle` `mlabangle` `mlabformat` `mlabstyle`
  `mlabtextstyle` `mlabvposition` `mlalign` `mwidth` `ndots` `nodropbase`
  `pcycle` `plegend`

Each needs its S04 minimum abbreviation, a serializer entry, and a
`_dash_pending` line so it stays reported until its section lands.

> Corrects §2 of this file, which put the figure at 92 by treating every
> reported option as undeclared. 27 of those are declared and serialized
> already, and are reported because `_dash_pending` correctly says they are
> awaiting their section.

## 06-06 — Carry and apply per-plot if/in qualifiers · PARTIAL

**The Stata half is done.** `dash.ado:1496` promotes a qualifier to graph level
only `if n_segs == 1`, with a comment naming the exact bug the task described.
Per-plot qualifiers survive on their plots.

**The Python half applies to raw-data layers only, and not to all of those.**
Measured by rendering `scatter/line/... mpg weight` with and without
`if_expr: "foreign==1"` and inspecting each renderer's `view.filter.booleans`
and its source data:

| layer | behaviour |
|---|---|
| `scatter` `bar` `spike` | correct — `CDSView` + `BooleanFilter` |
| `line` `connected` | view attached, but Bokeh raises **E-1024 `CDSVIEW_FILTERS_WITH_CONNECTED`** — filters do not apply to connected-topology glyphs, so the qualifier is **inert at runtime** and the document carries a validation error |
| `area` | **no view attached at all** — qualifier silently dropped |
| 12 computed layers | **ignored entirely** |

The 12: `lfit` `qfit` `lfitci` `qfitci` `fpfit` `fpfitci` `lpoly` `lpolyci`
`mband` `mspline` `histogram` `kdensity`. Each builds its own
`ColumnDataSource` from unfiltered `self.df`, and a view over the *graph's*
source never reaches it. Ground truth for the simplest case:

```
regress mpg weight if foreign==1   ->  slope -.01042596
regress mpg weight                 ->  slope -.00600869   <- what dash draws
```

`in_expr` has the identical shape (`scatter` viewed, `lfit`/`histogram`
ignored).

**Remaining:**
1. Compute every computed layer from the qualified frame, then view it — the
   fit must be re-estimated on the subset, not filtered after the fact.
2. Give `area` the view it never gets.
3. Replace the view with a per-layer source for `line`/`connected`, or accept
   the E-1024 and pre-filter those two — either way the validation error must
   go and the qualifier must bite.
4. Server: `_apply_graph_filter` has **0** occurrences in the emitted app, so
   none of this exists there.
5. The task's explicit test — "`(scatter y x) (scatter y x if foreign)` filters
   only the second plot; linking still propagates through a qualified plot" —
   needs to cover a computed layer, which is where it fails.

## 08-04 — Convert in the loader, give date figures a datetime axis · PARTIAL

**Standalone is done**, and more completely than the task asked. All seven
Stata date kinds produce a `DatetimeAxis` with a `DatetimeTickFormatter` tuned
per kind (`%ty` → `%Y` at every scale; `%tm`/`%tq`/`%th` → `%b %Y` at day
scale; `%tc` → `%d %b %H:%M`):

```
%td %tm %tq %tw %th %ty %tc  ->  DatetimeAxis + DatetimeTickFormatter
no "formats" key             ->  LinearAxis + BasicTickFormatter (unchanged)
y-axis date                  ->  DatetimeAxis
xscale(log) on a date        ->  DatetimeAxis + "dash: xscale(log) is
                                 meaningless for the date variable 'd'"
```

**Remaining:**
1. **Server mode has no date handling whatsoever.** In the emitted app:
   `DatetimeAxis` 0, `DatetimeTickFormatter` 0, `date_vars` 0,
   `numeric_formats` 0. Built both renderers from one spec carrying
   `formats:{"d":"%td"}` — standalone gave `DatetimeAxis`/`DatetimeTickFormatter`,
   the served app gave `LinearAxis`/`BasicTickFormatter`, i.e. raw day numbers
   on screen. This is the whole of 08-04 missing from `dash serve`.
   WP-12's parity guard now names this gap (`TestDatesAreAKnownServerGap`
   asserts the axis, glyph, tool and KPI comparisons still fail) and scoped
   the port: the loader conversion, the axis kind/type/formatter, the KPI
   column, the widget construction and the facet label are the saved
   consumers to lift into shared `_dash_*` helpers. One trap measured on the
   way: the saved renderer converts before it qualifies, so a qualifier
   comparing a date variable to a Stata day number (`if when > 15345`)
   selects Stata's rows when served and every row when saved; the shared
   qualifier has to translate the literal before the port lands.
2. Out-of-range period values still raise. `%tm`/`%tq`/`%tw` with a value past
   pandas' Timestamp range abort the render with a bare
   `AssertionError: Something has gone wrong, please report a bug at pandas`,
   rather than coercing to `NaT` with the existing warning.

## 08-05 — Format dates and numbers everywhere they are displayed · PARTIAL

Five of the six touchpoints work in standalone, verified individually:

- **Hover** — `[('Trade date','@{d}{%F}'), ('Value','@{v}{0.00}')]` with
  `formatters={'@{d}': 'datetime'}`. Variable labels, not raw names; one
  derived precision, not the three hardcoded ones.
- **Filter widgets** — `type(range)` → `DateRangeSlider`, `type(slider)` →
  `DateSlider`, `type(dropdown)` → `Select`.
- **Facet labels** — `by(d)` titles render `21 Dec 2022`, `22 Dec 2022`, …
- **KPI values** — `max`/`min`/`mean`/`p50` on a `%td` variable render
  `19 Jan 2023` etc.; `sum` warns *"dash: sum(d) adds up dates, which has no
  meaning."*
- **JS recompute** — `_kpi_callback_config` carries `datekind: "td"` plus
  `decimals` and `commas`, so the filtered value formats too.

**Remaining:**
1. **Every figure carries two `HoverTool`s.** One is correct; the other is
   `[('d','@{d}'), ('v','@{v}')]` — raw variable names, no formatter, no date
   handling. Present with and without a `formats` key, so it is not the date
   path that adds it. `tools=` at `dash_render.py:9552` is
   `"pan,wheel_zoom,box_select,lasso_select,reset"` and does not include
   `hover`, so both tools are added deliberately somewhere and one is stale.
   The user sees two tooltips, one of them wrong.
2. **No dropdown cardinality warning.** The task requires a warning above a
   reasonable cardinality suggesting `type(range)`. Measured on 5,000 distinct
   dates: **5,001 options, zero warnings**. (Same defect as the uncapped
   dropdown already recorded in §6 of this file; this is the date-specific
   clause of it.)
3. **Server mode has none of it**: in the emitted app `variable_labels` 0,
   `DateRangeSlider` 0, `_facet_label` 0, `_format_kpi_value` 0.
4. Minor: `count` on a date column renders `30.0` rather than `30`.

## 09-02 — Implement the axis_label and axis_scale grammars · PARTIAL

The grammar is in, and I checked each form separately rather than trusting the
suite. `xlabel(...)` produces:

| form | result |
|---|---|
| `2000(500)4000` | `FixedTicker[2000, 2500, 3000, 3500, 4000]` |
| `2000 3000 4000` | `FixedTicker[2000, 3000, 4000]` |
| `#5` | `BasicTicker(desired_num_ticks=5)` |
| `minmax` | `FixedTicker[1800, 4080]` (the data bounds) |
| `none` | `FixedTicker[]` |
| `2000 "low" 4000 "high"` | ticks + `major_label_overrides` |
| `, format(%9.0fc)` | `NumeralTickFormatter(format='0,0')` |
| `, labsize(large)` | `major_label_text_font_size='15px'` |
| `, angle(45)` | `major_label_orientation=0.7854` rad |
| `, grid` / `, nogrid` | grid `#e5e5e5` / `None` |

`_parse_scale_opt` honours `range()`: `xscale(range(1500 5000))` gives
`Range1d(1500, 5000)`, and `range(...) log` keeps the range. The dead
`xrange`/`yrange` keys are gone — the task's "do not leave both" is satisfied.
`xtick()`/`ytick()` work.

**Remaining:**
1. **Tick labels ignore the variable's Stata display format.** The task:
   *"Numeric tick labels must honour `format()` and, when none is given, the
   variable's Stata display format from S08."* Measured with
   `formats={'weight': '%9.0fc'}` and no `format()` sub-option: the formatter
   stays `BasicTickFormatter`. Only an explicit `format()` works.
2. **`xmtick()` `ymtick()` `xmlabel()` `ymlabel()` are not implemented** — all
   four leave a default `BasicTicker` and are reported as unsupported options.
   (They are also in 05-04's undeclared list, so that work comes first.)
3. **Server mode has no axis-label grammar at all**: `_parse_axis_label` occurs
   4× in the renderer and **0×** in the emitted app.

## 09-07 — HTML escaping, hover, secondary-axis range, mlabel on lines · PARTIAL

Three of the five defects are fixed outright; `hover()` was decided but left
inert, and the secondary-axis work is half done:

- **Double escaping — fixed in both layouts.** Worth recording how this was
  checked, because the naive check reads the wrong way round: in `layout(auto)`
  the title lives in a Bokeh `Div` inside `docs_json`, which the embedding
  escapes a second time, so the raw HTML shows `Price &amp;amp; Weight` and
  looks doubly escaped. Decoding the embedding layer gives the Div's real text,
  `Price &amp; Weight&#x27;s end`, which a browser renders as
  `Price & Weight's end`. `layout(bs)` writes it directly, escaped once.
  Both are correct.
- **Canvas text — fixed in `DashRenderer`.** `title("R&D spend")` → figure
  title `'R&D spend'`; `xtitle("W&L")` → axis label `'W&L'`. No escaping on
  canvas glyphs. (Not fixed in the server renderer — see below.)
- **`mlabel()` on line plots — fixed.** `map_line` passes `sorted_source` to
  both the glyph and `_apply_mlabel_opts` (`dash_render.py:3556`).

**Remaining:**
1. **`hover()` is accepted and does nothing.** The decision the task demanded
   was taken in the direction of *implement* — `dash.ado:423`/`:750` `sreturn`
   it, it is in the option lists at `:1129`/`:1399`/`:1415`, and the renderer
   reads it at `dash_render.py:8036` and `:10197`. But the variables it names
   are never extracted, so they never reach the data JSON. Measured end to end
   through Stata:

   ```
   dash scatter mpg weight, hover(price foreign) name(h1)
   dash build, saving(hv.html) replace
   ```

   No "ignoring unsupported option(s)" note, rc 0 — and the strings `price`
   and `foreign` occur **zero times** in the 1.2 MB of output. Add `hover` to
   the key scan in `_dash_extract_vars` so the columns are loaded, then the
   read at `:10197` has something to bind to. As it stands this is an
   accepted-but-silently-dropped option, the defect class the plan exists to
   remove. The help does not document it either, which the task's `<verify>`
   requires.
2. **Canvas text is still escaped in the server renderer.** The 09-07 fix was
   applied to `DashRenderer` only; `ServerAppBuilder` still `html.escape()`s
   the figure title, both axis labels, the subtitle `Label` and the facet
   title, so `title("R&D spend")` draws `R&amp;D spend` under `dash serve`.
3. **Legend text is still escaped in both renderers** — the same defect class
   as the titles, left behind: `legend(label(N "..."))` overrides and the
   colour-key labels reach a canvas but are HTML-escaped on the way.
4. **The filtered secondary axis still does not move.** Half the fix landed:
   the initial range is now computed from the active view
   (`_compute_secondary_range(_source_frame(source, self.df), ...)` at
   `dash_render.py:9678`/`:9713`), with a comment explaining why. But the task
   also requires *"make the filter callback update it"* — and
   `extra_y_ranges` appears in the entire file only at `:9681` and `:9691`,
   both at initial render. No callback, JS or Python, touches it. Move a range
   filter on a dual-axis graph and the right-hand axis stays where it was.
5. **The secondary axis does not exist in server mode.** In the emitted app:
   `extra_y_ranges` 0, `ytitle2` 0, `yscale2` 0, `_compute_secondary_range` 0.
   `dash serve` silently draws a one-axis graph for a two-axis specification.
6. `test_labels_land_on_the_sorted_points` does not detect the regression it is
   named for — it guards the mlabel column carry but passes unchanged when the
   sorted source is swapped back. (The task's adversarial canvas-text test,
   which I first listed as missing here, **does** exist — see Appendix C.)

## 11-04 — Consume the remaining discarded keys and fix the dead CSS · PARTIAL

**The dead CSS is fixed and mechanically guarded.** `css_block()` now emits
`.db-title`, `.db-subtitle` and `.db-kpi-card`, and each matches a class the
HTML actually uses. The guard the task demanded exists:
`test/test_scheme_consumption.py:265`
`test_every_selector_matches_a_class_the_html_emits`, parameterised by layout.

**Most keys are consumed, but through accessors, not attributes** — worth
stating because an attribute-level grep makes them look dead. `default_color`
has 38 external call sites and reads `p_colors`/`p_line_colors`/
`p_bar_colors`/`p_lineplot_colors`; `default_marker_size` 6 and reads
`marker_size`; `default_symbol` 2 (`p_symbols`); `default_line_pattern` 2
(`p_lineplot_patterns`); `default_connect_pattern` 2 (`p_line_patterns`).
Alphas, grid colours, legend chrome, axis and tick styling all resolve in both
renderers.

**Remaining:**
1. **`title_color` and `heading_font_size` never reach the figure title.** They
   are read only by `css_block()`. Measured on `s2color`, which declares
   `title_color='#1e2d53'` and `heading_font_size='14pt'`, while the rendered
   figure title carries Bokeh's defaults `text_color='#444444'`,
   `text_font_size='13px'`. The task names this explicitly: *"`title_color` and
   `heading_font_size` reach the figure title, which today gets no colour, size
   or alignment."* Still true of the canvas title.
2. **`note_font_size` has zero consumers.** Parsed at `dash_render.py:2047`
   (`self.note_font_size = self._gsize("gsize note", "9pt")`), but the note
   annotation at `:9867` hardcodes `{"size": 11.0, "color": "#555555"}`. The
   colour is a hardcoded literal too, and belongs in the same fix.
3. `graphsize_x` / `graphsize_y` are consumed in the standalone renderer and
   absent from the emitted app (S10 territory, but the key is a scheme key).

## 15-03 — Collapse the glyph dispatch tables to one · PARTIAL

Judged against the binding decision that **superseded** this task's wording —
emit `GlyphMapper` into the app rather than importing `dash_render` — so the
"the app must import GlyphMapper" clause is not counted against it.

**What landed:** the emitted app carries `GlyphMapper`, `OptionTranslator` and
`SchemeParser` copied verbatim, and **the scheme is wired through**. The task's
stated symptom is gone: `grep "scheme"` over the emitted region returned zero
hits when the task was written and returns **44** now, and `#1f77b4` — the
uniform colour the task complained of — occurs **0** times.

**Remaining:**
1. **38 of the 39 plot types the emitted app dispatches still carry their own
   drawing code.** Exactly one delegates: `_DASH_MAPPER.map_scatter` at
   `dash_render.py:14090`. The 38: `area` `bar` `connected` `dot` `dropline`
   `fpfit` `fpfitci` `function` `hist` `histogram` `kdensity` `lfit` `lfitci`
   `line` `lowess` `lpoly` `lpolyci` `mband` `mspline` `pcarrow` `pcbarrow`
   `pci` `pcscatter` `pcspike` `qfit` `qfitci` `rarea` `rbar` `rcap` `rcapsym`
   `rconnected` `rline` `rscatter` `rspike` `scatteri` `spike` `tsline`
   `tsrline`.
2. **The `by()` and `by(total)` facet loops were never unified.** The task
   requires them to become the same facet-expansion code the standalone path
   uses. `_expand_by_groups` occurs 3× in `DashRenderer` and **0×** in the
   emitted app, which still carries its own `by_total` handling. The third and
   fourth copies the task set out to delete are both still there.
3. Every server-side gap in 06-06, 08-04, 08-05, 09-02 and 09-07 above is
   downstream of this task. Finishing it is what makes those five stop being
   two problems each.

## What these eight have in common

Six of the eight are **done in `DashRenderer` and absent from
`ServerAppBuilder`**: dates (08-04, 08-05), the axis grammar (09-02), the
secondary axis (09-07), per-plot qualifiers (06-06), and the dispatch itself
(15-03). Sequencing 15-03 first would collapse most of the rest, because a
delegated branch inherits the standalone behaviour instead of needing its own
copy of each fix.

The exceptions are 05-04, which is `dash.ado` work that gates S07/S09/S10, and
11-04, which is three small standalone fixes.

---

# Appendix B — the full task-by-task backlog

Appendix A above records what I measured directly. This appendix is the
complete itemised backlog for the same eight tasks, produced by a deep audit
(one agent per task, each required to take the `<action>` apart clause by
clause and measure rather than read), then put through an adversarial pass
that tried to prove each item was already done.

**77 items.** Tags are `[kind · where · effort]`:
`func` = a user-visible behaviour gap, `deli` = a test, cscript, help sentence
or changelog entry the task asked for; `standalone` / `server` / `both` /
`dash.ado` / `docs`; `S`/`M`/`L`.

Several of these I verified independently — those are flagged inline in
Appendix A and in the notes below. Where Appendix A and this list describe the
same gap, this list is the more detailed statement of it.

## Three findings worth pulling out first

**1. 20 plot types are broken in server mode.** Measured by building the
emitted app from a spec and counting glyph renderers, with spec shapes taken
from `dash.ado`'s own emission:

- **Draw nothing at all:** `function`, `pci`, `tsrline`.
- **Draw nothing under `by()`** (they work without it): `lfitci` `qfitci`
  `mspline` `tsline` `rarea` `rbar` `rcap` `rline` `rscatter` `rspike`
  `rconnected` `rcapsym` `pcspike` `pcarrow` `pcbarrow` `pcscatter`
  `scatteri` — 17 of them.

This is 15-03's unfinished collapse showing through: the `by()` and
`by(total)` facet loops are hand-written copies that only ever learned a
subset of the plot types.

**2. The axis grammar is standalone-only, and the server silently keeps the
positions while dropping the labels.** Same spec through both renderers:

| `xlabel(...)` | standalone | server |
|---|---|---|
| `2000(500)4000` | `FixedTicker[2000, 2500, 3000, 3500, 4000]` | `BasicTicker` |
| `minmax` | `FixedTicker[1800, 4080]` | `BasicTicker` |
| `none` | `FixedTicker[]` | `BasicTicker` |
| `, format(%9.0fc)` | `NumeralTickFormatter` | `BasicTicker` |
| `, angle(45)` | `0.7854` rad | `BasicTicker` |
| `2000 "low" 4000 "high"` | ticks **+ overrides** | ticks, **overrides dropped** |

The last row is the dangerous one: the served graph draws tick marks in the
right places carrying the wrong text, which looks correct.

**3. A date dropdown filters every row away.** `build_dropdown` writes option
values as `str(Timestamp)` — `'2022-12-21 00:00:00'` — while the column holds
`Timestamp`s that Bokeh transports as epoch milliseconds, so `_FILTER_JS`
compares `1671580800000` against a date string and never matches. The display
half is wrong too: the task requires the label formatted through the
variable's Stata format with the raw value kept as the option value, and both
halves of the tuple are the same raw string.

### 05-04 — Declare the options destined for later sections

- **[func · dash.ado · L]** Declare and serialize the 69
  implement-dispositioned options that are declared nowhere. They are accepted
  only by the trailing `*` catch-all, so their values are thrown away and
  never reach the spec. Add each to `GRAPH`/`PLOT` in
  scripts/regen_option_surface.py with its owning section, regenerate, and
  confirm the value round-trips. The 69, by owner — S07 (13): adjust area
  atobs ciplot discrete estcmd estopts fitplot logit mean nofit noweight
  predopts. S09-axes-text (13): droplines tlabel tline tmlabel tmtick tscale
  ttext ttick ttitle xvarformat xvarlabel yvarformat yvarlabel. S09-style
  (43): acolor alalign alpattern alstyle alwidth astyle barbsize baroffset
  bstyle clegend colorend colorfillonly colorformissing colorkeysrange
  colorlevels colorrule colorstart colorvarminmax dcolor dfcolor dlalign
  dlcolor dlstyle dlwidth dotextend dsize dstyle dsymbol gap headlabel lalign
  mangle mlabangle mlabformat mlabstyle mlabtextstyle mlabvposition mlalign
  mwidth ndots nodropbase pcycle plegend. The t*/pc* family are graph-level
  (graph syntax block + the four `foreach gk`/`foreach gkey` propagation
  lists); the style family is plot-level (plot syntax block +
  `_dash_plot_opts_to_json`).     *Where:* `dash.ado:_dash_parse_graph_opts
  (syntax block, :281), dash.ado:_dash_parse_plot_opts (syntax block, :475),
  dash.ado:_dash_plot_opts_to_json (:854), dash.ado:_dash_plot (gopts_json
  loop, :1462), dash.ado:_dash_process_seg`
- **[deli · dash.ado · M]** Measure the minimum abbreviation for the 69
  undeclared options and add them to test/fixtures/abbrev_truth.json. None of
  the 69 has an entry today, so there is no S04 truth to declare them against
  — 05-04's abbreviation clause cannot be satisfied for any of them without
  first extending the S04 probe. Watch for collisions this will force: dash
  currently accepts shorter prefixes than twoway precisely because it declares
  fewer options (measured: `dash scatter mpg weight, mlabel(make) mlabs(3)` ->
  `"mlabsize":"3"`, while twoway also has mlabstyle/mlabtextstyle).
  `resolve_minimums()` in the generator asserts on ambiguity, so adding these
  names with real measured minimums may trip that assert and force longer
  minimums than existing dash do-files use.     *Where:*
  `scripts/extract_abbrev_truth.do, test/fixtures/abbrev_truth.json,
  scripts/regen_option_surface.py:base_min,
  scripts/regen_option_surface.py:resolve_minimums`
- **[func · dash.ado · M]** Fix the generator so it is idempotent before
  extending it. Re-running scripts/regen_option_surface.py against HEAD's
  dash.ado silently deletes hand-added declarations that are not in its
  inventory: `HOVer(string)`, the `T()/B()/L()/R()` title aliases,
  `PBGC/XLA2/XSC2/XTI2/YLA2/YSC2/YTI2`, `BINS(string)`, `sreturn local hover`,
  and — critically — `sreturn local _pending` and `sreturn local _unknown`,
  which are the only channel feeding `_dash_report_ignored`. Deleting those
  two lines disables 05-03's reporter entirely. Since the block comment in
  dash.ado says "Do not hand-edit … run the generator", this is the procedure
  a developer will follow to do the item above.     *Where:*
  `scripts/regen_option_surface.py:GRAPH,
  scripts/regen_option_surface.py:PLOT, scripts/regen_option_surface.py
  (splice steps 1-6), dash.ado:_dash_parse_graph_opts,
  dash.ado:_dash_parse_plot_opts`
- **[deli · dash.ado · S]** Emit the owning-section grouping comments the task
  asks for. The generator computes them (`pending_lines`, step 7) but never
  splices them into dash.ado, so the variable is dead and the source has no
  marker saying which declared option belongs to S06/S07/S09/S10/S11 or is
  permanently accept-and-report. Splice the section tags into the two syntax
  blocks as grouping comments.     *Where:*
  `scripts/regen_option_surface.py:291 (pending_lines),
  scripts/regen_option_surface.py:syntax_block,
  dash.ado:_dash_parse_graph_opts, dash.ado:_dash_parse_plot_opts`
- **[func · dash.ado · S]** Make the reporter name the canonical option rather
  than the prefix the user typed. Because the 69 are undeclared, an
  abbreviated use falls straight through the `*` catch-all and
  `_dash_report_ignored` echoes the raw token, so the note names options that
  do not exist in twoway's vocabulary and cannot be looked up in the help.
  This resolves itself for each option as it is declared, but until then it is
  a live wart, and it is the reason the note cannot be trusted as an
  inventory.     *Where:* `dash.ado:_dash_report_ignored (:1338),
  dash_parse.mata:_dash_option_names (:945), dash_parse.mata:_dash_optname_of
  (:932)`
- **[deli · dash.ado · M]** Add the test 05-04's <verify> names: "every
  'implement' option is accepted, serialized with its value, and reported as
  ignored pending its section". No test asserts the serialization half.
  test/test_option_surface.cscript checks only rc 0 (O2-01/02) and the
  accept-and-report reporting contract (O2-03..O2-07);
  test/test_unsupported_report_is_true.py only walks options already on the
  `_dash_pending` list and asserts the renderer output does NOT change, which
  says nothing about whether the value reached the spec. Drive the new test
  from test/fixtures/rejected_options.json so it cannot go stale.     *Where:*
  `test/test_option_surface.cscript (new O2-08 check),
  test/test_unsupported_report_is_true.py:PLOT_VALUES,
  test/fixtures/rejected_options.json`
- **[deli · dash.ado · S]** Correct REMAINING.md section 2. It states "92
  options the plan said to implement are only accepted and reported, so their
  values never reach the spec". Measured, that is wrong for 23 of them:
  b1title b2title colorlist fxsize fysize horizontal l1title l2title lstyle
  mlstyle mstyle r1title r2title scale sort t1title t2title text vertical
  xmlabel xmtick ymlabel ymtick are reported as ignored AND already serialized
  with their value. The 05-04 gap is 69 options, not 92; the other 23 are
  waiting on S06/S09/S10 renderer work, not on dash.ado.     *Where:*
  `REMAINING.md:102-145 (section 2 "Blocker — the option surface"),
  REMAINING.md:304 ("92 options declared nowhere")`

### 06-06 — Carry and apply per-plot if/in qualifiers

- **[func · both · M]** Make every computed glyph honour the per-plot view.
  Thread the layer's row mask (the `BooleanFilter.booleans` built at
  dash_render.py:9987, or an explicit `mask=` kwarg from
  `DashRenderer._add_glyph`) into the 14 `GlyphMapper.map_*` methods that
  currently accept `view=` and never reference it, and subset
  `source.data[xvar]`/`[yvar]` by that mask before fitting/binning. Affected:
  map_lfit (3821), map_qfit (3873), map_lfitci (3918), map_qfitci (3998),
  map_lowess (4091), map_lpoly (4272), map_lpolyci (4344), map_fpfit (4517),
  map_fpfitci (4569), map_histogram (4636), map_kdensity (4806), map_mspline
  (5912), map_mband (5983), and map_area (3592). map_scatteri (5370),
  map_pci_literal (5548) and map_function (6065) take no `view` parameter at
  all — decide and document that inline-coordinate/analytic layers cannot be
  qualified rather than leaving it silent.     *Where:*
  `dash_render.py:GlyphMapper.map_lfit/map_qfit/map_lfitci/map_qfitci/map_lowess/map_lpoly/map_lpolyci/map_fpfit/map_fpfitci/map_histogram/map_kdensity/map_mspline/map_mband/map_area;
  dash_render.py:DashRenderer._add_glyph `
- **[func · server · M]** Teach the generated `bokeh serve` app to read
  per-plot qualifiers. `ServerAppBuilder._generate_app_source` emits a plot
  loop (`for pi, plot in enumerate(plots):`, dash_render.py:14030) that never
  consults `plot['if_expr']`/`plot['in_expr']`; only the graph-level keys are
  read (emitted at dash_render.py:13812/13819 as `go.get('if_expr') or
  g.get('if_expr')`). Emit the same per-plot mask + CDSView the standalone
  path builds, using the app's already-emitted `_stata_if_to_pandas` and
  `_safe_g` validator.     *Where:*
  `dash_render.py:ServerAppBuilder._generate_app_source (12740), emitted
  per-graph filter block ~13808-13824, emitted plot loop ~14030`
- **[func · dash.ado · M]** Stop discarding a command-level qualifier in paren
  mode. `_dash_split_segs`'s PAREN branch acts only on `(`, `)` and a depth-0
  `,` (dash_parse.mata:388-441); any other depth-0 text — the `if`/`in` clause
  twoway allows after the last group — falls through `i++` and is lost.
  Capture the depth-0 text between the last `)` and the graph-options comma,
  hand it back as a new `_cmd_qualifier` local, and have `_dash_plot`
  (dash.ado:1377) write it to the graph-level `if_expr`/`in_expr` so it
  applies to every plot. Until then dash should at minimum error rather than
  accept silently.     *Where:* `dash_parse.mata:_dash_split_segs (355; paren
  branch 386-441); dash.ado:_dash_plot (1377), graph-JSON assembly at
  1488-1503`
- **[func · standalone · S]** Fix computed layers under link() and under
  linked by(). Because the mappers ignore `view`, any restriction carried as a
  CDSView rather than as a shortened source is invisible to them — which now
  includes the graph-level qualifier of a LINKED graph (`_linked_graph_views`,
  dash_render.py:11500-11505) and every panel of a LINKED by() graph
  (dash_render.py:11465-11476). The mask-threading fix above is the same fix,
  but this case needs its own test because it is a silent behaviour change
  caused by an unrelated option.     *Where:*
  `dash_render.py:DashRenderer._build_figures ~11458-11510 (linked by()
  panel_view_r, _linked_graph_views); same GlyphMapper methods as above`
- **[func · standalone · M]** Decide what a per-plot qualifier means for
  connected-topology glyphs. A per-plot `if` on `line`, `connected`, `tsline`,
  `rline` or `rconnected` attaches a BooleanFilter CDSView to a Bokeh Line
  glyph, which Bokeh rejects (E-1024 CDSVIEW_FILTERS_WITH_CONNECTED) and
  BokehJS does not honour, so the browser draws the unfiltered line. Either
  give those types a pre-filtered private source when the graph is not linked,
  or insert NaN breaks in a masked copy of the columns, or report the
  limitation.     *Where:* `dash_render.py:DashRenderer._make_figure_body
  (9956-9997); dash_render.py:GlyphMapper.map_line (3486), map_connected
  (3560), map_tsline (5805), map_rline (5106), map_rconnected (5147)`
- **[deli · both · M]** Add the regression tests project rule 8 requires for
  each gap above: (a) a per-plot qualifier on each computed type asserting the
  fit/band/bin/density matches the qualified subsample —
  test/test_per_plot_qualifier_linking.py and test/test_varlist_expansion.py
  currently exercise `scatter` only; (b) per-plot `in_expr` (measured working,
  untested); (c) a server-mode parity test that the generated app applies a
  per-plot qualifier; (d) a linked-by() / linked-graph-level computed-layer
  test; (e) a cscript case for `dash (plot) (plot) if <expr>` and `... in
  1/10` in paren mode. V2-11 in test/test_varlist_expansion.cscript checks
  only the spec JSON, never a rendered figure.     *Where:*
  `test/test_per_plot_qualifier_linking.py,
  test/test_varlist_expansion.py:test_second_plot_if_expr_filters_only_the_second_plot
  (334) and :test_first_plot_if_expr_does_not_leak_onto_later_plots (354),
  test/test_varlist_exp`
- **[deli · docs · S]** Document the per-plot qualifier in dash.sthlp: that
  `if`/`in` written inside a plot's parentheses binds to that plot, what
  happens under `link()` and `by()`, and which layer types cannot be qualified
  (scatteri, pci, function). The help's only qualifier example is the
  single-plot form.     *Where:* `dash.sthlp:641-643 ('If qualifier' example
  block), dash.sthlp:129`

### 08-04 — Convert in the loader and give date figures a datetime axis

- **[func · server · M]** Give ServerAppBuilder date support: have the emitted
  app read `build_options["formats"]`, convert `%t*` columns with
  `_stata_dates_to_datetime`, and set `_fig_kw['x_axis_type']/['y_axis_type']
  = 'datetime'` plus the per-kind `DatetimeTickFormatter`, mirroring
  dash_render.py:9556-9603. `_stata_date_kind`, `_stata_dates_to_datetime` and
  `_datetime_formatter_for` must be added to the helper-forwarding tuple so
  they exist in the generated module.     *Where:* `dash_render.py:13161-13165
  (emitted `for col in df.columns: df[col] = pd.to_numeric(...)` — the only
  coercion in the emitted loader); dash_render.py:13851-13855 (emitted
  `_fig_kw` — only `'log'` is handled); dash_render.`
- **[func · standalone · M]** Apply the datetime treatment to the
  secondary-axis path: build the y2/x2 axis as a DatetimeAxis with
  `_datetime_formatter_for(kind)` when the layer's variable is a date, and
  compute `extra_y_ranges['y2']`/`extra_x_ranges['x2']` on Bokeh's millisecond
  scale (`astype('datetime64[ms]').astype('int64')`) instead of
  `pd.to_numeric`, which yields microseconds or nanoseconds depending on the
  inferred resolution.     *Where:* `dash_render.py:9684 (`_y2_ax = (LogAxis
  if _y2_log else LinearAxis)(...)`); dash_render.py:9719 (`_x2_ax = (LogAxis
  if _x2_log else LinearAxis)(...)`); dash_render.py:9678-9681 and :9713-9716
  (the `_compute_secondary_ran`
- **[func · standalone · M]** Convert user-supplied Stata date values to the
  datetime axis's millisecond scale in `xlabel()`/`ylabel()` explicit tick
  lists and in `minmax`, and in `xscale(range())`/`yscale(range())`. Pass the
  axis's date kind into `_apply_axis_spec` (it already receives `varname`, so
  `self.date_vars.get(varname)` suffices) and map the tick list through
  `_stata_dates_to_datetime(...).astype('datetime64[ms]').astype('int64')`; do
  the same for the range block's user bounds and replace its `pd.to_numeric`
  data-derived bound.     *Where:* `dash_render.py:9149-9150
  (`_apply_axis_spec`, `mode == "explicit"` FixedTicker);
  dash_render.py:9137-9143 (same method, `mode == "minmax"`,
  `pd.to_numeric(col)`); dash_render.py:9750-9773 (the
  `xscale(range())`/`yscale(r`
- **[func · standalone · S]** Warn when `_figure_date_kind` declines a
  datetime axis because the figure's layers disagree, naming the date variable
  that will be drawn on a linear axis. Today the method returns None with no
  diagnostic.     *Where:* `dash_render.py:9268-9298 (`_figure_date_kind`, the
  `if len(kinds) > 1 or None in kinds: return None` branch at :9296-9297)`
- **[deli · docs · S]** Document the date-axis precedence in dash.sthlp: that
  `%t*` display formats produce a datetime axis on either axis, that
  `xscale(log)`/`yscale(log)` on a date variable is overridden by the date
  axis and warns, and (per the section) that `%tC` is converted with the `%tc`
  epoch without leap-second correction.     *Where:* `dash.sthlp (the
  xscale()/yscale() and xlabel()/ylabel() option entries, and a new paragraph
  in the options or remarks section)`
- **[deli · standalone · S]** Add a test pinning the per-kind
  `DatetimeTickFormatter` attached to the figure axes — assert
  `fig.xaxis[0].formatter` is a `DatetimeTickFormatter` and that its
  `years`/`months`/`days`/`hours` strings match the kind (%ty -> "%Y" at all
  three grains; %tc -> an hours pattern carrying the time; %tm/%tq/%th ->
  month-grain days pattern).     *Where:* `test/test_dates.py (class
  `TestDatetimeAxis`, currently at test/test_dates.py:334-404); covers
  dash_render.py:9598-9603 and `_datetime_formatter_for` at
  dash_render.py:247-268`
- **[deli · both · S]** Add the two missing coverage cases the task's scope
  implies: (a) a secondary-axis date case in test/test_dual_axis.py asserting
  a DatetimeAxis on the right/top and a y2/x2 range on the same millisecond
  scale as the serialized column; (b) a date case in the ServerAppBuilder
  parity corpus asserting the served figure's axis type and the served
  column's dtype match the standalone renderer.     *Where:*
  `test/test_dual_axis.py (261 lines, no date case);
  test/test_mode_parity.py:74 (`CORPUS` helper `_spec` hardcodes `"formats":
  {}`) and its `CORPUS` list at test/test_mode_parity.py:187-284`

### 08-05 — Format dates and numbers everywhere they are displayed

- **[func · standalone · S]** Make the date dropdown filter.
  `FilterBuilder.build_dropdown` writes option VALUES as `str(Timestamp)`
  ("2001-01-01 00:00:00") while the data column and its snapshot hold epoch
  milliseconds, and `_FILTER_JS` matches with `String(orig[fvar][i]) !== val`,
  which can never be equal. Give the date branch the same treatment the
  range/slider branches got: emit the epoch-millisecond number as the option
  value (and the formatted date as the label).     *Where:*
  `dash_render.py:7571 `FilterBuilder.build_dropdown` (the
  `_int_normalized`/`raw_values` block at 7629-7638 and the `options` build at
  7657-7659); dash_render.py:7077 inside `_FILTER_JS` (`if (active[i] &&
  String(orig[fvar`
- **[func · standalone · S]** Format the date dropdown's DISPLAY text through
  the variable's Stata format while keeping the raw value as the option value
  — the value/label split the task names. Today both halves of the tuple are
  the same `str(Timestamp)`.     *Where:* `dash_render.py:7641
  `_resolve_label` and 7657-7659 `options.append((rv,
  FilterBuilder._safe(_resolve_label(rv))))` in `build_dropdown`; reuse
  `_format_date_value_standalone` (dash_render.py:203)`
- **[func · standalone · S]** Add the date-cardinality warning for dropdowns:
  above a reasonable number of distinct values, warn and suggest
  `type(range)`.     *Where:* `dash_render.py:7629-7638 in
  `FilterBuilder.build_dropdown`, after `raw_values` is built`
- **[func · standalone · S]** Remove or stop activating the raw-variable-name
  HoverTool that `GlyphMapper` adds, so the labelled/formatted tooltip is the
  only one shown. The existing removal at 10199-10202 fires ONLY when
  `hover()` extras are requested; otherwise both tools stay and Bokeh's
  `active_inspect="auto"` leaves both active, so two tooltip boxes appear.
  *Where:* `dash_render.py:2564 `GlyphMapper._hover_tool`; its callers at 3483
  (`map_scatter`) and 3557 (`map_line`); the conditional strip at
  dash_render.py:10199-10202 in `DashRenderer._make_figure``
- **[func · standalone · S]** Make the hover date picture depend on the date
  KIND, as every other touchpoint does. `_hover_row` uses `{%F}` for every
  kind except `tc`, so `%ty` hovers as '1998-01-01' instead of '1998',
  `%tm`/`%tq`/`%th` as '2001-06-01' instead of 'Jun 2001', and `%tC` silently
  loses the time that `%tc` keeps.     *Where:* `dash_render.py:10222-10225 in
  `DashRenderer._make_figure._hover_row`; mirror the kind table already in
  `_format_date_value_standalone` (dash_render.py:203) and
  `_datetime_formatter_for` (dash_render.py:247)`
- **[func · server · L]** Carry the whole of 08-05 into the generated server
  app. `build_options["formats"]` reaches the app but nothing reads it, so no
  column is converted to datetime64 and none of the six touchpoints formats
  anything. Concretely: (a) convert date columns and record
  `date_vars`/`numeric_formats` in the emitted `_load_spec_and_data`; (b)
  assign them onto `_DASH_MAPPER` so the inlined `_apply_mlabel_opts` date
  branch can fire; (c) format facet labels; (d) build
  DateRangeSlider/DateSlider and widen the `is_numeric_dtype` guards; (e)
  format dropdown options; (f) give the emitted `_format_kpi` the date branch,
  the variable's own Stata format fallback, and the sum-on-a-date warning; (g)
  add the labelled/formatted hover the standalone `_hover_row` builds.
  *Where:* `dash_render.py:13123 (emitted `_load_spec_and_data`); 12432
  (`_DASH_MAPPER = GlyphMapper(scheme=_DASH_SCHEME)`); 15364-15460 (emitted
  filter-widget loop: dropdown at 15378, range at 15403 with `if not
  pd.api.types.is_num`
- **[deli · standalone · S]** Fix the vacuous per-source-snapshot test: it
  iterates `cb.args.get("all_graph_sources_orig_json", [])`, a key that does
  not exist, so its loop body never runs and it asserts nothing. The real arg
  is `all_graph_sources_orig`, a list of ColumnDataSource models.     *Where:*
  `test/test_dates.py:672-685
  `TestDateFilterActuallyFilters::test_every_per_source_snapshot_agrees_too`;
  the producing code is dash_render.py:11901
  `_cb.args["all_graph_sources_orig"] = [...]``
- **[deli · standalone · S]** Add a test that the date dropdown actually
  FILTERS, not merely that its labels contain a year. The current test would
  pass against the broken implementation (and does).     *Where:*
  `test/test_dates.py:569
  `TestDateFilterWidgets::test_a_date_dropdown_shows_dates_not_epoch_numbers`
  — assert the option value parses as the same epoch-ms number the snapshot
  column holds, alongside the existing label asse`
- **[deli · server · M]** Add server-mode coverage for dates and display
  formats. No test in the repo exercises ServerAppBuilder with a `formats`
  map, and no .cscript touches sp500 or any %t format at all.     *Where:*
  `test/test_dates.py (no server cases) or a new test/test_dates_server.py;
  follow the pattern in test/test_filter_widget_parity.py and
  test/test_mode_parity.py, which already build and exec the generated app`
- **[func · standalone · S]** Reconcile the two renderings of a `%9.0g`
  (general) KPI between first render and JS recompute for large magnitudes.
  Python emits `f"{v:g}"` while the JS emits
  `String(Number(result.toPrecision(6)))`, so the same card changes shape on
  the first filter move — which the code comment at dash_render.py:7621
  explicitly promises it will not.     *Where:* `dash_render.py:7312-7314 (the
  `k.general` branch of `_FILTER_JS`) vs `DashRenderer._format_kpi_value`
  (dash_render.py:8418) / `_effective_kpi_fmt``

### 09-02 — Implement the axis_label and axis_scale grammars

- **[func · server · M]** Port the axis_label grammar into ServerAppBuilder's
  emitted app. The app's own parser recognises only a bare numlist and quoted
  value-label pairs — #N, minmax, none, the a(b)c increment form, format(),
  labsize() and grid/nogrid are all dropped — and worse, because it tokenises
  the raw string without stripping sub-options first, sub-option text is
  rendered AS A TICK LABEL. The cleanest fix is to emit
  `_parse_axis_spec`/`_apply_axis_spec` into the app the way
  `_glyph_layer_lines` (dash_render.py:12315) already copies GlyphMapper in
  via inspect.getsource, rather than maintaining a second parser.     *Where:*
  `dash_render.py:13989 `_parse_axlabel` (emitted string literal inside
  ServerAppBuilder); dash_render.py:14012-14021 the emitted `for _axk, _axobj
  in (('xlabel', fig.xaxis), ('ylabel', fig.yaxis))` loop; port targets are d`
- **[func · server · S]** Honour xscale(range())/yscale(range()) in the
  emitted server app, and delete the dead `xrange`/`yrange` reads there. The
  task said explicitly: wire range() to the dead code OR delete the dead keys,
  'do not leave both'. Both still exist in the file — DashRenderer took the
  first option, ServerAppBuilder kept the dead keys and got neither.
  *Where:* `dash_render.py:13907-13920 (emitted `# xrange / yrange axis
  limits` block reading `go.get('xrange','')` / `go.get('yrange','')`);
  dash_render.py:13851-13866 (emitted xscale/yscale handling — only `log` and
  `reverse`); re`
- **[func · both · S]** Fix xtick()/ytick() semantics. Stata's xtick() adds
  UNLABELLED tick marks alongside the labelled ticks xlabel() (or the default)
  produces; dash treats xtick as a fallback spelling of xlabel — it draws
  LABELLED ticks at those positions, and discards xtick entirely whenever
  xlabel is also present.     *Where:* `dash_render.py:9906-9913 (`tick_key =
  "xtick" if ax_key == "xlabel" else "ytick"` then `spec =
  self._parse_axis_spec(raw_ax or raw_tick)`); dash_render.py:9112
  `_apply_axis_spec` needs a tick-only path (e.g. FixedTicker.`
- **[func · both · M]** Implement xmtick(), ymtick(), xmlabel(), ymlabel()
  (minor ticks and minor labels). They are accepted by dash.ado, promoted into
  graph_options JSON, and then read by nobody — and dash.ado still names them
  in its 'ignoring unsupported option(s)' list, which is the honest state
  today.     *Where:* `dash.ado:381-384 and dash.ado:629-632 (the
  `_dash_pending` entries to remove once implemented);
  dash.ado:1129/1399/1415/1469 already carry the keys through to graph_options
  JSON; dash_render.py:9906 loop (add the four ke`
- **[func · standalone · S]** Route the secondary axes (xlabel2/ylabel2)
  through the new grammar. They still call the OLD `_parse_axis_label_opt`
  plus `_parse_axis_angle`, so #N, minmax, the a(b)c form, format(), labsize()
  and grid/nogrid are dropped there exactly as they were on the primary axes
  before 09-02 — and sub-option text leaks into the tick label the same way
  the server parser does. xscale2()/yscale2() also ignore range().
  *Where:* `dash_render.py:9699 (`_ticks2, _labels2 =
  self._parse_axis_label_opt(_raw_yla2)`) and dash_render.py:9734 (same for
  `_raw_xla2`); dash_render.py:9683 and :9718 (`_parse_scale_opt` on
  yscale2/xscale2, no `_parse_scale_ran`
- **[func · both · M]** Make the S08 display-format fallback reach a default
  axis. The fallback lives inside `_apply_axis_spec`, but that method is only
  reached when an xlabel/ylabel/xtick/ytick option is actually present (`if
  not raw_ax and not raw_tick: continue`), so a plain `dash scatter mpg
  weight` gets no tick formatting at all. Separately, `_stata_numeric_pattern`
  returns None for g-kind formats, and `%8.0gc` is auto.dta's own format for
  weight and price — so even with the guard removed the commonest Stata comma
  format would still not format.     *Where:* `dash_render.py:9910 (`if not
  raw_ax and not raw_tick: continue` — the guard that skips the fallback);
  dash_render.py:9159-9171 (the fallback itself, inside `_apply_axis_spec`);
  dash_render.py:395 `_stata_numeric_pattern``
- **[func · both · S]** Compute xlabel(minmax) from the graph's active view
  rather than the whole frame — the same defect 09-07 fixed for
  `_compute_secondary_range`, still present here.     *Where:*
  `dash_render.py:9134-9143 (the `mode == "minmax"` branch reads
  `self.df[varname]`); the fix pattern already in the file is
  `_source_frame(source, self.df)` as used at dash_render.py:9678 and :9713;
  `_apply_axis_spec` (das`
- **[deli · both · M]** Add the missing tests for the clauses above: a
  server-side axis-grammar test (there is none — test/test_axis_options.py
  only ever builds DashRenderer figures via `_fig_with_gopts`), a test that
  sub-option text never becomes a tick label in either renderer, a
  display-format-fallback test with no xlabel present,
  xtick-adds-unlabelled-ticks and xmtick/ymtick/xmlabel/ymlabel tests against
  the axis_truth probes, an xlabel2/ylabel2 grammar test, and a dead-key guard
  that actually covers the emitted app.     *Where:*
  `test/test_axis_options.py (add a server-mode variant of `_fig_with_gopts`
  following the `_figs(...)` harness in test/test_server_legend.py:48-76);
  test/test_axis_options.py:248 `test_the_dead_xrange_keys_are_gone` must a`

### 09-07 — HTML escaping, hover, secondary-axis range, mlabel on lines

- **[func · server · S]** Remove html.escape() from the canvas text emitted by
  ServerAppBuilder: the figure title, both axis labels, the subtitle Label and
  the facet title. The 09-07 fix was applied to DashRenderer only.
  *Where:* `dash_render.py:13834, :13835 (x_label/y_label), :13840 (_fig_kw
  title=), :13953 (subtitle _Label text=), :15116 (_fac_title) — all inside
  ServerAppBuilder._generate_app_source (dash_render.py:12740). Note :13944
  (note/ca`
- **[func · dash.ado · S]** hover() variables are never serialized, so the
  option is accepted and does nothing through the real Stata path. Add "hover"
  to the key scan in _dash_extract_vars (or extract it in _dash_prepare_spec
  the way filter() variables are extracted at dash.ado:2177-2235) so the named
  variables reach jsonio's varlist.     *Where:* `dash_parse.mata:537
  _dash_extract_vars (keys vector at :545-551 lists
  yvar/xvar/var/yvar1/yvar2/y1var/x1var/y2var/x2var/mlabel/colorvar — no
  "hover"); consumer dash.ado:2159 `mata: _dash_extract_vars(...)`; downstream
  re` [WP-29 P0.10, commit 735c534: closed]
- **[func · server · M]** ServerAppBuilder ignores graph_options["hover"]
  entirely — add the extra-tooltip handling that DashRenderer has at
  dash_render.py:10197-10261 to the emitted app source.     *Where:*
  `dash_render.py ServerAppBuilder._generate_app_source (:12740) — the emitted
  hover tool is built inside the per-plot dispatch around :14088-14093; the
  only occurrence of the string "hover" after `class ServerAppBuilder` (`
- **[deli · docs · S]** Document the hover() decision in the help file. The
  task's <verify> requires the decision to be "implemented and documented";
  hover() is not in dash.sthlp's option table.     *Where:* `dash.sthlp — the
  only occurrence of the word is prose at :143 ("and hover tooltips
  automatically"); no `hover(varlist)` entry in the graph-option syntax table
  or option descriptions.`
- **[func · standalone · M]** Make the filter callback update the
  secondary-axis range. extra_y_ranges["y2"] / extra_x_ranges["x2"] are static
  Range1d models that no callback ever touches, so an interactive filter
  leaves the right-hand axis spanning the unfiltered data — the exact defect
  09-07 names, for the interactive case.     *Where:* `dash_render.py:9681 and
  :9716 create `fig.extra_y_ranges["y2"]` / `extra_x_ranges["x2"]` in
  _make_figure_body (:9495); _FILTER_JS (dash_render.py:7046-7509) has no
  reference to them; the CustomJS args blocks at :7674, :7`
- **[func · server · L]** ServerAppBuilder has no secondary-axis support at
  all, so neither the active-view range nor the filter update exists there.
  Either implement yaxis(2)/xaxis(2) in the emitted app or report the option
  as unsupported under `dash serve`.     *Where:* `dash_render.py
  ServerAppBuilder._generate_app_source (:12740) — no emitted line contains
  `extra_y_ranges`, `y_range_name` or `LinearAxis`; compare
  DashRenderer._make_figure_body :9664-9745.`
- ~~**[deli · both · S]** Add the adversarial test the task explicitly demands
  for CANVAS text.~~ **REFUTED — it already exists**, and is non-vacuous under
  mutation: `test/test_html_output.py:486`, `:633`, `:939`. See Appendix C.
- **[deli · standalone · S]** Strengthen
  test_labels_land_on_the_sorted_points: it does not detect the regression it
  is named for. It guards the mlabel column carry but passes unchanged when
  the sorted source is swapped back for the unsorted one.     *Where:*
  `test/test_axis_options.py::TestMlabelOnLines::test_labels_land_on_the_sorted_points
  (:889-910). The fixture df has no NaN rows, which is the only thing that
  distinguishes the two sources (per .ultraplan/CHANGELOG.md:300-`
- **[func · both · S]** Canvas text is still HTML-escaped in the legend in
  BOTH renderers — the same class of defect 09-07 fixed for titles, left
  behind. legend(label(N "...")) overrides, the colorvar Legend title and the
  ColorBar title are Bokeh canvas glyphs.     *Where:* `dash_render.py:10165
  (`text = html.escape(m.group(2))` for label(N "text") overrides, in
  _make_figure_body :9495); :3240 and :3269 (`Legend(...
  title=html.escape(var_display))` and `ColorBar(...
  title=html.escape(var_dis`
- **[func · standalone · S]** Latent: the CustomJSTickFormatter map built for
  explicit axis tick labels escapes the label text while the parallel
  major_label_overrides does not — the two disagree, and only the overrides
  path is currently user-visible.     *Where:* `dash_render.py:9152-9158 in
  _apply_axis_spec (:9112) — `safe = {str(k): html.escape(str(v)) ...}`
  feeding CustomJSTickFormatter, immediately followed by
  `major_label_overrides = {float(k): v ...}` with the unescaped valu`
- **[deli · dash.ado · S]** Delete or fix the dead second copy of the
  graph_options JSON writer in dash.ado. It has no caller and its key list is
  missing hover plus ~20 other keys that the live writer emits — exactly the
  drift shape that produced the phantom hover() read in the first place.
  *Where:* `dash.ado:891 `program define _dash_graph_opts_to_json` (key list
  at :898-901 stops at xscale2); the live writer is the inline loop at
  dash.ado:1464-1471, whose list includes hover, xsize, ysize, scale, text,
  xtick, ytick`

### 11-04 — Consume the remaining discarded keys and fix the dead CSS

- **[func · both · S]** Make scheme.text_font_size the default size for
  mlabel() point labels. GlyphMapper._apply_mlabel_opts builds its LabelSet
  with a hardcoded "10px"; an explicit mlabsize() must still win (that branch
  already exists 6 lines below). The server's own mlabel branches use a
  different literal, 9px, so fixing only one side also leaves a
  standalone/server parity split.     *Where:* `dash_render.py:3350
  (GlyphMapper._apply_mlabel_opts, `text_font_size="10px"`); server literals
  at dash_render.py:14452, 14482, 14500, 14530, 14550, 14583, 14653
  (`_r_mlab_kw`, `text_font_size='9px'`) and 14906 (`_mlab_kw`
- **[func · both · S]** Route scheme.title_color and scheme.heading_font_size
  onto the figure Title (and the alignment the task names). Today the Title
  model is only touched when the user passes title() sub-options; with no
  sub-options it keeps Bokeh's defaults. The server never touches fig.title at
  all.     *Where:* `dash_render.py:9588-9596 (DashRenderer figure build, the
  `_t_text, _t_opts = _parse_textbox_opt(...)` block — apply the scheme before
  it so explicit sub-options still win); server: no `fig.title.*` assignment
  exists afte`
- **[func · both · S]** Make scheme.note_font_size the default size for the
  note() annotation. It currently has ZERO consumers anywhere in the file —
  the note Label uses a hardcoded 11.0px default in both renderers.
  *Where:* `dash_render.py:9867 (`_TEXTBOX_DEFAULTS = {"note": {"size": 11.0,
  ...}}` in DashRenderer) and dash_render.py:13932 (the same dict emitted into
  the server app)`
- **[func · both · S]** Give the per-figure subtitle annotation a real scheme
  value instead of the hardcoded 13.0px / #444444 default. (The DASHBOARD
  subtitle is already scheme-driven through .db-subtitle in css_block; this is
  the graph-level subtitle() Label.)     *Where:* `dash_render.py:9893-9896
  (`text_font_size=f"{_textbox_size(subtitle_opts, 13.0):g}px"`,
  `text_color=_textbox_color(subtitle_opts, "#444444")`); server at
  dash_render.py:13953 (`text_font_size='13px', text_color='#444444'`
- **[func · standalone · M]** Honour legend(position() ring()) for the
  colorvar colour key and the continuous ColorBar; both are hardcoded to the
  "right" panel. GlyphMapper._apply_colorvar does not receive graph_options,
  so this needs either a plumbing change or a post-pass in _rebuild_legend
  (which today deliberately filters _dash_clegend legends out of the
  clock-position move).     *Where:* `dash_render.py:3240-3243
  (`fig.add_layout(Legend(items=legend_items, ...,
  name=_COLORVAR_LEGEND_NAME), "right")`), dash_render.py:3267-3271
  (`fig.add_layout(ColorBar(...), "right")`), dash_render.py:2995-3001
  (`GlyphMapp`
- **[func · both · M]** Close the task's <done> condition: 6 of the 34 keys
  SchemeParser parses still have zero consumers (**4**, not 6 — `graphsize_x`/`graphsize_y` were refuted, see Appendix C) — p_mark_colors,
  note_font_size, graphsize_x, graphsize_y, legend_position, legend_cols.
  (p_mark_colors is 11-03's "wire it or remove it"; graphsize_x/y are marked
  in-code as S10's; note_font_size and the two legend keys are 11-04's.)
  Decide and land each, including the removals.     *Where:*
  `dash_render.py:1980 (p_mark_colors), 2047 (note_font_size), 2054-2056
  (graphsize_x/graphsize_y), 2086-2088 (legend_position, legend_cols) — all in
  SchemeParser._init_properties`
- **[deli · docs · S]** Replace the hand-written attribute list in
  test_the_key_is_read_somewhere with a real enumeration of everything
  _init_properties assigns, so the check is mechanical as the <done> demands.
  The current list covers 7 of 34 names and omits every key that is actually
  dead.     *Where:* `test/test_scheme_consumption.py:462-476
  (`@pytest.mark.parametrize("attr", [...]); def
  test_the_key_is_read_somewhere`)`
- **[func · server · M]** Make css_block() reach the served dashboard. The
  generated `bokeh serve` app carries the whole SchemeParser class source (so
  css_block is DEFINED there) but never calls it, and its dashboard
  title/subtitle are unclassed inline-styled markup, so title_color,
  heading_font_size, text_font_size, legend_bg_color and legend_border_color
  are all inert in server mode.     *Where:* `dash_render.py:15929-15936 (the
  emitted `_head += f'<h2
  style="font-family:sans-serif;margin-bottom:2px;">...'` / `<div
  style="font-family:sans-serif;font-size:14px;color:#666;...">` block in
  ServerAppBuilder) — needs th`
- **[deli · server · S]** Extend the CSS selector test to the server-emitted
  document. `_render()` in the test only drives DashRenderer, so the
  mechanical guard the task installed cannot see the server's markup at all.
  *Where:* `test/test_scheme_consumption.py:60-90 (`_render` helper) and
  :242-296 (`TestSchemeCssActuallyApplies`) — add a ServerAppBuilder arm`
- **[func · server · S]** Fix the swallowed exception in the server's
  _dash_style_legend: it assigns Stata's clock integer to Bokeh's
  Legend.location enum, which raises inside the try, so legend_cols is never
  applied either. Map the clockdir through the same _CLOCK_SIDE/_CLOCK_INSIDE
  tables the standalone renderer uses (or drop the assignment), and narrow the
  except so a real failure is not hidden. Also align the label size:
  standalone uses text_font_size, the server uses tick_label_font_size.
  *Where:* `dash_render.py:12657-12666 (emitted `_dash_style_legend`:
  `lg.location = _c['legend_position']` at 12662, `lg.ncols =
  int(_c['legend_cols'])` at 12664, `except (AttributeError, KeyError,
  TypeError, ValueError): pass` at `
- **[func · both · S]** Make the .db-kpi-card rule actually apply. The
  class-name fix landed, but the KPI div carries inline
  `style="background:...; border:1px solid #dee2e6"`, and an inline
  declaration beats a stylesheet rule, so legend_bg_color /
  legend_border_color still have no visible effect on KPI cards. Either drop
  the unconditional inline background/border defaults (emit them only when the
  user passed bgcolor()) or move the scheme values into the inline style.
  *Where:* `dash_render.py:10487-10490 (`_build_kpi_html`, `<div
  class="db-kpi-card" style="background:{bgcolor}; ... border:1px solid
  #dee2e6;">`), dash_render.py:7328-7331 (the CustomJS rebuild),
  dash_render.py:12976-12980 (the se`
- **[func · both · S]** Fix SchemeParser._gsize's numeric branch before
  heading_font_size is wired to anything else. Stata's gsize values are
  relative sizes (style/gsize-medium.style: val 3.8194 = 11pt;
  gsize-large.style: val 4.8611 = 14pt, i.e. pt = val x 2.880), but _gsize
  returns max(6, int(val*1.2))pt. economist declares `gsize heading 6.0`,
  which is ~17pt in Stata and 7pt in dash — and that wrong value is ALREADY
  live in the .db-title rule this task made apply.     *Where:*
  `dash_render.py:1844-1853 (`SchemeParser._gsize`, the `float(raw)` branch at
  1849-1851)`
- **[func · both · S]** Residual alpha literals the task's sweep missed:
  map_rarea still fills at a hardcoded 0.5, and the server's by()-facet and
  total histogram paths fill at a hardcoded 0.6 instead of _SCHEME_BAR_ALPHA.
  *Where:* `dash_render.py:4947-4950 (`GlyphMapper.map_rarea`,
  `fill_alpha=0.5`); dash_render.py:15157 and 15258 (emitted
  `_fac_fig.quad(... fill_alpha=0.6 ...)` and `_tot_fig.quad(...
  fill_alpha=0.6 ...)`)`
- **[deli · standalone · S]** Decide and record what the continuous colorvar()
  ramp should be. The task names Viridis256 as ignoring the scheme but
  prescribes a replacement only for the discrete case, and no Stata scheme
  declares a continuous ramp — so this needs a written disposition (keep
  Viridis as the documented default, or synthesise a ramp from p_colors)
  rather than a silent leave-as-is.     *Where:* `dash_render.py:3253-3254
  (`pal_name = self._PALETTE_MAP.get(palette_key or "viridis",
  "Viridis256")`), .ultraplan/CHANGELOG.md (S11 section at :396-500, whose
  "Consumed now" table lists only the discrete palette)`
- **[deli · both · S]** Add behavioural tests for the clauses that only the
  source-count test covers: the three alphas reaching real glyphs,
  minor_grid_color reaching fig.xgrid/ygrid, and the server-side legend
  chrome. Today nothing asserts any of these against a rendered model.
  *Where:* `test/test_scheme_consumption.py (TestNoParsedKeyIsDiscarded,
  :427-476) — add glyph-level and ServerAppBuilder assertions`

### 15-03 — Collapse the glyph dispatch tables to one

- **[func · server · L]** Delegate the remaining 37 main-loop ptype branches
  to `_DASH_MAPPER`. The chain at dash_render.py:14031 (`ptype =
  plot.get('type','')`) through ~14850 still hand-writes drawing code for:
  area, bar, connected, dot, dropline, fpfit, fpfitci, function, histogram,
  kdensity, lfit, lfitci, line, lowess, lpoly, lpolyci, mband, mspline,
  pcarrow, pcbarrow, pci, pcscatter, pcspike, qfit, qfitci, rarea, rbar, rcap,
  rcapsym, rconnected, rline, rscatter, rspike, scatteri, spike, tsline,
  tsrline. Each has a `GlyphMapper.map_<type>` already emitted into the app
  and unused.     *Where:*
  `dash_render.py:ServerAppBuilder._generate_app_source (starts 12740);
  emitted chain at dash_render.py:14031-14850; targets are GlyphMapper.map_*
  at dash_render.py:3407-6065`
- **[func · server · L]** 20 plot types draw NOTHING under `by()` /
  `by(total)` in server mode: function, lfitci, mspline, pcarrow, pcbarrow,
  pci, pcscatter, pcspike, qfitci, rarea, rbar, rcap, rcapsym, rconnected,
  rline, rscatter, rspike, scatteri, tsline, tsrline. The two facet chains
  handle only 18 types (scatter, line, bar, area, histogram/hist, lfit, qfit,
  kdensity, lowess, lpoly, lpolyci, fpfit, fpfitci, connected, dot, spike,
  dropline, mband); anything else falls off the end of the elif chain
  silently.     *Where:* `dash_render.py emitted facet chain at 15137-15230
  (by) and 15237-15330 (by total); fix by routing both through GlyphMapper
  like the main loop`
- **[func · server · M]** Unify the by() and by(total) facet loops with
  `_expand_by_groups` instead of leaving a third and fourth copy. The emitted
  app re-implements group splitting, suboption parsing (`total`/`missing` by
  ad-hoc regex), qualifier application and facet labelling inline;
  `_expand_by_groups` is not copied into the app at all.     *Where:*
  `dash_render.py:DashRenderer._expand_by_groups (8776) and _facet_label
  (8872) are the targets; the duplicates are emitted at
  dash_render.py:15016-15110 (by) and 15218-15240 (by total)`
- **[func · server · S]** Facet glyphs ignore the scheme's marker size/alpha
  and ignore msize()/msymbol() entirely — the emitted facet loops hardcode
  `size=6` and leave alpha at Bokeh's 1.0.     *Where:* `dash_render.py:15144
  (`_fac_fig.scatter(..., size=6, color=color, ...)`) and dash_render.py:15245
  (the by(total) twin)`
- **[func · server · S]** Facet titles ignore Stata display formats and date
  formats. The emitted label builder consults value labels only;
  `DashRenderer._facet_label` also formats %t* date kinds and numeric %fmt.
  *Where:* `dash_render.py:15085-15097 (emitted `_fac_parts` loop) vs
  dash_render.py:8872 `DashRenderer._facet_label` (its date branch at 8896,
  numeric branch just below)`
- **[func · server · S]** The by(total) panel drops the graph title. The
  emitted total branch hardcodes `title='Total'` where the per-group branch
  composes `'<title> — <label>'`.     *Where:* `dash_render.py:15232
  (`_tot_fig = bokeh_figure(title='Total', ...)`)`
- **[func · server · S]** `pci` with literal coordinates draws nothing in
  server mode — a dead read. dash.ado writes literal pci as
  `"values":[[y,x],...]` (dash.ado:1212, guarded at dash.ado:1655-1667), but
  the emitted branch reads y1var/x1var/y2var/x2var and bails when they are
  absent. `GlyphMapper.map_pci` / `map_pci_literal` (dash_render.py:5516,
  5548) already handle the literal shape.     *Where:*
  `dash_render.py:14781-14796 (emitted `elif ptype in ('pci','pcscatter')`)`
- **[func · server · M]** 13 more main-loop plot types diverge on glyph
  properties under a non-default scheme: fpfitci loses its CI band entirely
  (emitted branch is a verbatim copy of fpfit); rarea fill_alpha 1.0 vs 0.5;
  rbar drawn with a white 1.2px outline vs line_alpha 0; rcapsym caps at
  line_width 1.2 vs 1.5; rline/rconnected/tsrline draw the second series in
  colour index 0 with a dash instead of the scheme's colour index 1 (#3e647d
  vs #7b92a8); rscatter/pcscatter markers at size 6 vs scheme 10.18;
  pcspike/pcarrow/pcbarrow at line_width 1.2 vs 1.5; lowess runs a second
  implementation (`_compute_lowess`) where standalone uses statsmodels via
  map_lowess.     *Where:* `dash_render.py:14253 (fpfitci), 14192 (lowess ->
  _compute_lowess emitted at 13396), 14429 (rarea), 14457 (rbar), 14613
  (rcapsym), 14535 (rline), 14555 (rconnected), 14728 (tsrline), 14768
  (rscatter), 14676 (pcspike/pcarr`
- **[deli · both · M]** Extend the parity corpus to the paths 15-03 is about:
  it covers 17 of the 38 user-facing plot types and has zero by(), by(total),
  tabs(), link(), filter or KPI entries — i.e. it reaches one of the four
  duplicated code paths. Missing types: fpfit, fpfitci, function, lfitci,
  lowess, pcarrow, pcbarrow, pci, pcscatter, pcspike, qfit, qfitci, rarea,
  rbar, rcap, rconnected, rline, rscatter, rspike, tsline, tsrline.
  *Where:* `test/test_mode_parity.py:CORPUS (line ~186) and
  TestTheTwoModesAgree`
- **[deli · server · S]** Add the assertion the task's <verify> names: that
  the generated app contains no glyph dispatch table of its own. Nothing in
  test/ counts or forbids ptype chains in the emitted source, so the collapse
  has no acceptance test.     *Where:* `test/test_mode_parity.py (or a new
  test/test_server_dispatch.py); the check is an ast walk of ServerAppBuilder
  output counting if/elif chains on `ptype``
- **[deli · server · S]** Add a test that the generated app is self-contained
  — imports nothing from dash_render and executes with the package absent from
  sys.path. This property replaced the task's 'the app must import
  dash_render' clause and is asserted nowhere, while dash.sthlp and the
  CHANGELOG both promise it.     *Where:* `test/test_server_build_options.py
  or test/test_packaging.py; assert no `dash_render` import in the emitted
  text and exec the app with sys.path stripped of the repo`
- **[deli · server · S]** The task's packaged-install clause is still open in
  its superseded form: `ServerAppBuilder.__init__` resolves the scheme at
  BUILD time through `SchemeParser.resolve_or_fallback`, so the S02/S03
  net-install layout defect (dash_render.py lands in <dir>/py/, schemes in
  <dir>/s/) silently degrades server mode to built-in defaults too. No cscript
  builds a server app with a scheme from a net-installed copy.     *Where:*
  `dash_render.py:12311 (ServerAppBuilder.__init__ scheme resolution);
  SchemeParser search dirs at dash_render.py:1524-1532;
  test/test_server_build.cscript is the place to add the packaged-install
  case`
---

# Appendix C — what the adversarial pass added

Every item in Appendix B was then put to three independent agents per task:
one trying to **prove it was already done**, one hunting for what the auditor
**missed**, and one **re-running the auditor's own commands** to check the
evidence held. All 24 returned.

**3 items were refuted** — they are already done, and are struck from the
backlog:

- **11-04 · `graphsize_x` / `graphsize_y` are not dead** (refuted twice,
  independently). They are read by *string*, not by attribute —
  `getattr(self.scheme, "graphsize_x", None)` at `dash_render.py:9244-9245`
  inside `_resolve_aspect_ratio`, whose result becomes
  `fig_kwargs["aspect_ratio"]`. Measured on rendered figures: `stcolor`
  → 1.6667 (scheme 7.5/4.5), `economist` → 1.0 (2.2/2.2), `s2color` → 1.375
  (5.5/4.0). An attribute-level count cannot see this, which is the
  methodological trap — and the one Appendix A's own enumeration fell into
  before being redone. The standalone half of Appendix A's item 3 stands:
  re-checked by string, `graphsize_x`, `graphsize_y` and
  `_resolve_aspect_ratio` all occur **0** times in the emitted app, so the
  scheme's graph size still does not reach `dash serve`.
- **09-07 · the adversarial canvas-text test already exists.** Three live
  tests drive `graph_options` (canvas) rather than `build_options` (HTML
  header): `test_html_output.py` `TestXssInHtmlOutput::test_script_tag_in_title_is_escaped`
  (:486), `TestGraphOptionsInHtml::test_title_xss_not_in_html_unescaped`
  (:633) and `TestAdversarialPlotOptions::test_xss_in_note_option_escaped`
  (:939). Proven non-vacuous by mutation — appending the raw graph title to
  the assembled HTML makes them fail.

**Nothing else was refuted.** Every other item in Appendix B survived an agent
whose explicit job was to knock it down, and the evidence lens found no
fabricated or mis-transcribed measurements.

**121 further items were found**, listed below. They are additional to
Appendix B, not restatements of it — each was checked against the Appendix B
list and against the other lenses' findings before being kept.

**Backlog total for the eight tasks: 197 items** (77 + 121, less the one whole
item struck above; the `graphsize` refutation was raised by two agents against
the same sub-claim inside a surviving item, which has been corrected in place
rather than removed).

| task | Appendix B | Appendix C | total |
|---|---:|---:|---:|
| 05-04 Declare the pending options | 7 | 12 | **19** |
| 06-06 Per-plot `if`/`in` | 7 | 12 | **19** |
| 08-04 Datetime axes | 7 | 14 | **21** |
| 08-05 Formats everywhere | 10 | 15 | **25** |
| 09-02 Axis grammars | 8 | 19 | **27** |
| 09-07 Escaping, hover, 2nd axis, mlabel | 11 − 1 | 14 | **24** |
| 11-04 Scheme keys and dead CSS | 15 | 17 | **32** |
| 15-03 Collapse the dispatch tables | 12 | 18 | **30** |
| | **76** | **121** | **197** |

Weighting by where the work lands rather than by task: the server renderer
accounts for the largest share, and almost all of it is downstream of 15-03.

### 05-04 — Declare the options destined for later sections (12 further items)

- **[func · dash.ado · S]** fxsize()/fysize() are declared at a LONGER minimum
  than twoway's, so the abbreviated forms twoway accepts are silently thrown
  away. dash.ado declares `FXSIZE(string)` / `FYSIZE(string)` (all-caps = full
  name required); twoway's measured minimum is `fxsiz` / `fysiz`. A pasted
  `twoway ..., fxsiz(50)` therefore falls through the `*` catch-all in dash:
  rc 0, a note naming a non-existent option `fxsiz()`, and the value gone.
  This breaks 05-04's abbreviation clause for two of the 42 options the
  auditor certified as DONE, and it is outside the auditor's remaining-item-2
  scope, which is written against "the 69 undeclared" options only —
  fxsize/fysize are declared but have NO abbrev_truth entry, so their declared
  minimum was guessed by `base_min()`'s fallback, not measured. Fix: probe
  fxsize/fysize in scripts/extract_abbrev_truth.do, add them to
  test/fixtures/abbrev_truth.json, and let the generator emit
  `FXSIZe`/`FYSIZe`. `scale` is the third declared option with no truth entry
  but needs no change — twoway rejects `sca()`/`scal()` too, so the full name
  is correct there. The abbreviation-probe item should be scoped to 71
  options, not 69.     *Where:*
  `/Users/billy/Desktop/Programs/StataPrograms/d/dash/dash.ado:294
  (FXSIZE/FYSIZE in the graph syntax block at :281),
  /Users/billy/Desktop/Programs/StataPrograms/d/dash/dash.ado:511 (same two in
  the plot`
- **[func · server · M]** xtick(), ytick(), xsize() and ysize() are
  serialized, emit NO note, and are never read by the generated `bokeh serve`
  app — a silent drop in server mode, which is precisely the defect class
  05-04's <done> forbids ("nothing is silently dropped in the interim"). The
  auditor's done_items[3] concludes "No declared implement-option is both
  unimplemented and silent"; that holds for DashRenderer only. All four were
  deliberately taken OFF the `_dash_pending` lists (see the comment block at
  dash.ado:594-604, "scheme(), xsize(), ysize(), xtick() and ytick() are NOT
  listed"), so nothing tells the user. Either teach ServerAppBuilder to read
  them (the emitted axis loop currently iterates only ('xlabel', fig.xaxis),
  ('ylabel', fig.yaxis); `_fig_kw` honours only aspectratio) or, as an
  interim, make the note fire in server mode.     *Where:*
  `/Users/billy/Desktop/Programs/StataPrograms/d/dash/dash_render.py:12265
  (class ServerAppBuilder — emitted axis-tick block and `_fig_kw`
  construction), /Users/billy/Desktop/Programs/StataPrograms/d/das`
- **[func · dash.ado · M]** The generator's destructiveness is larger than the
  auditor's remaining-item-3 lists, and a developer who restores only the
  items named there will still lose working code. Beyond
  HOVer/T/B/L/R/PBGC/XLA2.../BINS/`sreturn local hover`/`sreturn local
  _pending`/`sreturn local _unknown`, re-running
  scripts/regen_option_surface.py also deletes: (a) the whole level()
  validation block in _dash_parse_plot_opts (dash.ado:549-561), which is the
  only thing stopping `level(150)` becoming a Python exception inside the
  renderer; (b) the ENTIRE plot-level `local _dash_pending` accumulation
  (dash.ado:593-641) and `local _dash_unknown` (:642) plus its `sreturn local
  _pending`/`_unknown` (:770-771) — after a regen the whole file contains zero
  `sreturn local _pending`, so 05-03's reporter is dead at BOTH levels, not
  just graph level; (c) `sreturn local g_hover` (:750) and `hover` from all
  four graph propagation loops (:1129, :1399, :1415, :1469); (d) every
  alias-folding `if` (bins->bin, bw->barwidth, mlg->mlabgap,
  cv/colv->colorvar, pbgc->plotbgcolor, xla2/xsc2/xti2/yla2/ysc2/yti2,
  t/b/l/r->*1title). Separately, the script is not runnable as documented on
  any other checkout: REPO is a hardcoded absolute path
  (scripts/regen_option_surface.py:17) and the final `json.dump(...,
  open("/tmp/dash-wf/b2/option_inventory.json", "w"))` runs AFTER dash.ado has
  already been overwritten, so a missing directory leaves the repo mutated and
  the script traceback-ing.     *Where:*
  `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/regen_option_surface.py:17
  (REPO), :299 (json.dump path), splice steps 2 and 4,
  /Users/billy/Desktop/Programs/StataPrograms/d/dash/dash.ado:5`
- **[func · both · S]** `bw()` is hijacked: a legal twoway abbreviation of
  `bwidth()` is routed to `barwidth` and silently discarded, so
  kdensity/lowess/lpoly draw at the DEFAULT bandwidth with no note.
  `scripts/regen_option_surface.py:HISTORICAL_MIN` (lines 104-107) hands `bw`
  to `barwidth` and forces `bwidth` to the longer `bwid`;
  `dash.ado:_dash_parse_plot_opts` declares `BARWidth(string)` +
  `BWIDth(string)` and folds `if "`bw'" != "" & "`barwidth'" == "" local
  barwidth "`bw'"`. Fix: drop the `barwidth: bw` entry from HISTORICAL_MIN,
  give `bwidth` the measured minimum `bw`, regenerate, and add the collision
  to test_abbreviations.cscript's A7 guard. This is the one 05-04 abbreviation
  decision that is not a superset of twoway — it changes the meaning of a
  working command.     *Where:*
  `scripts/regen_option_surface.py:HISTORICAL_MIN (104-107),
  scripts/regen_option_surface.py:base_min, dash.ado:_dash_parse_plot_opts
  (BARWidth/BWIDth declarations and the `local barwidth `"`bw'"'` fold)`
- **[func · dash.ado · S]** `saving()` is declared in BOTH syntax blocks,
  serialized into `graph_options`, read by neither renderer, and is NOT on
  either `_dash_pending` list — an accepted-but-silently-dropped option, the
  exact defect class 05-04's action text forbids creating. Either implement it
  (write the HTML/py for that one graph) or add `saving` to the graph-level
  `_dash_pending` block and to `scripts/regen_option_surface.py:GRAPH` with an
  owning section so the note names it.     *Where:*
  `dash.ado:_dash_parse_graph_opts (SAVing declaration + `local _dash_pending`
  block), dash.ado:_dash_parse_plot_opts (same),
  scripts/regen_option_surface.py:GRAPH`
- **[func · server · M]** The faceted (`by()`) branch of the emitted server
  app is a SECOND hand-written glyph dispatch that ignores the plot `options`
  dict entirely except for `lcolor`/`mcolor`. Every other serialized plot
  option is silently discarded on that path — `msymbol`, `msize`, `malpha`,
  `jitter`, `mlabel`, `mlcolor`, `mlwidth` all work in standalone AND in
  non-faceted server mode, then vanish the moment `by()` is added. The branch
  hardcodes `size=6`, `width=0.8`, `line_width=_SCHEME_LINE_WIDTH`. Fix: route
  the facet branch through the copied `GlyphMapper` (the
  `_glyph_layer_lines()` machinery S15-03 already added for the unfaceted
  branch) instead of the inline `_fac_fig.scatter(...)` ladder.     *Where:*
  `dash_render.py:ServerAppBuilder facet branch (emitted lines at
  dash_render.py:15133-15205),
  dash_render.py:ServerAppBuilder._glyph_layer_lines`
- **[func · server · M]** The whole `colorvar()` colour-mapping family is
  absent from the emitted server app — `colorvar`, `colordiscrete`,
  `colornlevels`, `colorcuts`, `colormissing` are honoured by DashRenderer and
  ignored in server mode, and none of them is on `_dash_pending`, so server
  users get a plain single-colour plot with no note. (`colpalette` rides on
  `colorvar`, so it goes too; `coloruseplegend` is already on the pending list
  and is honest.) Fix: port `_apply_colorvar`/`_PALETTE_MAP`
  (dash_render.py:3011-3032) into ServerAppBuilder's emitted source, or make
  the note mode-aware.     *Where:* `dash_render.py:3011-3032
  (colpalette/_PALETTE_MAP, the DashRenderer implementation),
  dash_render.py:ServerAppBuilder (no colorvar handling),
  dash.ado:_dash_parse_plot_opts `_dash_pending` block`
- **[func · server · S]** `xsize()` and `ysize()` are honoured by DashRenderer
  and silently ignored in server mode, and neither is on the graph
  `_dash_pending` list. S10 is marked done for them on the strength of the
  standalone path only. Fix: carry xsize/ysize into the emitted app's
  `figure(width=, height=)` computation, or list them as pending-for-server.
  *Where:* `dash_render.py:ServerAppBuilder (figure sizing in the emitted
  source), dash.ado:_dash_parse_graph_opts `_dash_pending` block`
- **[deli · both · M]** The reporting contract is mode-blind and has no
  converse test. `_dash_pending` is computed in dash.ado before the renderer
  is chosen, so an option honoured in standalone and dropped in server mode is
  silently dropped with no note (measured instances: colorvar family, xsize,
  ysize, every plot option under by(), plus the already-recorded
  secondary-axis family). And `test/test_unsupported_report_is_true.py` only
  tests ONE direction — for each option ON the pending list, that rendering
  twice does not change the output. Nothing asserts the converse: every option
  dash DECLARES must either change the rendered output or be named on
  `_dash_pending`. That converse test is what would have caught `saving()`,
  `xsize()`, `ysize()` and the colorvar family. The existing test also
  instantiates `dr.DashRenderer` only (test_unsupported_report_is_true.py:178)
  and never `ServerAppBuilder`, so it is blind to every server-mode gap by
  construction. Add: (a) a converse parametrised test driven by the two syntax
  blocks; (b) run both existing directions against ServerAppBuilder as well;
  (c) make the note mode-aware, or record a per-mode pending list.
  *Where:* `test/test_unsupported_report_is_true.py (_render at :162-178,
  _pending at :132, both parametrised tests), dash.ado:_dash_parse_graph_opts
  / _dash_parse_plot_opts `_dash_pending` blocks, dash.ado:_dash`
- **[deli · dash.ado · S]** `_dash_graph_opts_to_json` (dash.ado:891) is a
  fifth, DEAD, stale copy of the graph-option list that the generator does not
  maintain. It carries 30 keys and is missing 25 of the options 05-04 added —
  b1title b2title fxsize fysize hover l1title l2title nodraw play r1title
  r2title scale subtitle2 t1title t2title text title2 xmlabel xmtick xsize
  xtick ymlabel ymtick ysize ytick. Nothing calls it today, so it is not a
  live bug, but it is a loaded gun for the next developer who reaches for the
  obvious-looking serializer. Delete it, or add it to the generator's splice
  targets.     *Where:* `dash.ado:_dash_graph_opts_to_json (:891),
  scripts/regen_option_surface.py`
- **[deli · dash.ado · S]** The generator's splice has ALREADY double-applied
  in the committed dash.ado — the generated blocks are duplicated at HEAD, not
  merely at risk of it. The "this block is generated by
  scripts/regen_option_surface.py" banner appears 4 times (twice per syntax
  block), and `_dash_parse_graph_opts` contains the t()/b()/l()/r() alias-fold
  `if`-ladder twice in a row with two different comment headers. Both copies
  run, so behaviour is unchanged, but the file no longer matches what the
  generator would produce and the next regeneration diff will be unreadable.
  De-duplicate the splice markers before extending the inventory.     *Where:*
  `dash.ado:_dash_parse_graph_opts (:264-346), dash.ado:_dash_parse_plot_opts
  (:460-540), scripts/regen_option_surface.py (splice steps 1-6)`
- **[deli · dash.ado · M]** Three options that 05-04 declared have NO entry in
  test/fixtures/abbrev_truth.json, so their minimum abbreviations were guessed
  from `HISTORICAL_MIN`/`DASH_ONLY_MIN` rather than measured — `bwidth`, `at`
  and `jseed`. `bwidth` is the one that bit (see the bw() item). The S04 probe
  only covered names it found in twoway's help under their canonical spelling,
  so the alias/short-form surface the generator invents is unprobed by
  construction. Extend scripts/extract_abbrev_truth.do to probe every name in
  the generator's GRAPH/PLOT inventory including the alias forms, and add a
  test that, for each token dash accepts, twoway either rejects it (superset,
  fine) or resolves it to the SAME canonical option (parity) — the missing
  test is what let `bw` through, because test_abbreviations.cscript's A7
  collision guard only iterates abbrev_truth.json.     *Where:*
  `scripts/extract_abbrev_truth.do, test/fixtures/abbrev_truth.json,
  scripts/regen_option_surface.py:HISTORICAL_MIN / DASH_ONLY_MIN /
  resolve_minimums, test/test_abbreviations.cscript (A7)`

### 06-06 — Carry and apply per-plot if/in qualifiers (12 further items)

- **[func · server · M]** Correct the scope of the server-mode fix: threading
  the mask through GlyphMapper does NOT reach server mode for computed layers,
  because the generated app never calls GlyphMapper for them. The emitted plot
  loop calls standalone module-level helpers `_compute_lfit(g_df, ...)`,
  `_compute_qfit`, `_compute_lfitci`, `_compute_qfitci`, `_compute_lowess`,
  `_compute_lpoly`, `_compute_lpolyci`, `_compute_fpfit`,
  `_compute_histogram`, `_compute_kdensity`, `_compute_mspline`,
  `_compute_mband`, `_compute_rscatter`, `_compute_pcscatter` on the
  GRAPH-level dataframe. Only `scatter` routes through
  `_DASH_MAPPER.map_scatter` (emitted at dash_render.py:14090). So the
  per-plot row mask must be applied to `g_df` at EVERY `_compute_*` call site
  in the emitted source, in three separate places: the main plot loop (emitted
  at dash_render.py:14108, 14121, 14145, 14180, 14193, 14212, 14227, 14242,
  14254, 14376, 14403, 14745, 14757, 14773, 14799), the two facet/by() paths
  (`_fac_gdf` at 15154-15187 and `work_df` at 15255-15288), and the
  brush/filter recompute path that rebuilds `agg['source'].data` from
  `agg_fdf` (15605-15633) — which must intersect the brushed subset with the
  per-plot mask, not replace it. The auditor's item-2 renderer_note says this
  comes 'for free' from the mapper fix; it does not, and planning the work on
  that assumption will leave server mode wrong for every computed layer.
  *Where:* `dash_render.py:ServerAppBuilder emitted plot loop (call sites
  14108-14254, 14376, 14403, 14745-14799), emitted facet paths (15154-15187,
  15255-15288), emitted brush recompute (15605-15633); emitted he`
- **[func · dash.ado · S]** Paren mode loses a trailing qualifier even on a
  SINGLE plot, which the auditor's done_item #2 ("A single-segment
  (command-level) qualifier is still promoted to graph level") claims works.
  It is true only for the un-parenthesised form. Measured: `dash scatter mpg
  weight if foreign==1, name(g4)` -> plots[0].if_expr="foreign==1" and
  graph-level if_expr="foreign==1" (promoted, correct), but `dash (scatter mpg
  weight) if foreign==1, name(g8)` -> rc=0 and the spec is
  {"plots":[{..."if_expr":"","in_expr":""}],"graph_options":{"name":"g8"},"if_expr":"","in_expr":""}
  — the restriction is gone before _dash_plot ever sees it, because
  _dash_split_segs's PAREN branch never captures depth-0 text. Fix belongs
  with the `_cmd_qualifier` work the auditor scoped, but it needs its own
  case: wrapping one plot in parentheses must not change what the command
  means. Add the case to test/test_varlist_expansion.cscript beside V2-11.
  *Where:* `dash_parse.mata:_dash_split_segs (355; paren branch 386-441);
  dash.ado:1496 (`if `n_segs' == 1` promotion gate);
  test/test_varlist_expansion.cscript:V2-11`
- **[func · dash.ado · S]** `_dash_split_segs`'s paren branch silently
  swallows ANY depth-0 text, not just an if/in clause — a typo'd option
  outside the parentheses is accepted with rc=0 and no message. `dash (scatter
  mpg weight) garbagetoken, name(g9)` returns rc=0 and produces a spec
  identical to the un-garbaged command. The auditor's item 3 asks for a
  `_cmd_qualifier` capture and says dash "should at minimum error rather than
  accept silently", but only for a qualifier; the general case is an
  input-validation hole (CLAUDE.md rule 16) and needs an explicit
  reject-unknown-text path plus an adversarial test, otherwise the qualifier
  capture will simply widen the set of strings that are swallowed.
  *Where:* `dash_parse.mata:_dash_split_segs (355; paren branch 386-441);
  test/test_varlist_expansion.cscript`
- **[func · server · M]** The server-mode fix has three more emitted code
  sites than the auditor's file list names. Beyond the per-graph filter block
  (~13808-13824) and the plot loop (14030), the generated app reads qualifiers
  at three further places, all graph-level only: (a) `_graph_qualifiers` is
  built from `go.get('if_expr') or g.get('if_expr')` at ~15007-15014 and is
  the ONLY qualifier state the filter callback can see, (b) the by()-facet
  frame `_by_q_df` is restricted by `_by_in`/`_by_if` at ~15045-15058 with no
  per-plot consultation, and (c) the filter-callback re-render reapplies
  `_qual_cb.get('if_expr')` from `_gquals` at ~15523-15560. A per-plot mask
  added only at the plot loop would be correct on first paint and then
  silently dropped on the first filter move, and would never reach any by()
  panel of a served dashboard. Thread the per-plot qualifier into
  `_graph_qualifiers` (keyed by gname+plot index) and into both the facet and
  callback paths.     *Where:*
  `dash_render.py:ServerAppBuilder._generate_app_source (12740); emitted
  `_graph_qualifiers` block ~15003-15014; emitted by()-facet block
  ~15040-15058; emitted filter-callback requalify block ~15523-1556`
- **[deli · docs · S]** dash.sthlp states a twoway-parity claim for if/in that
  the code does not honour, and never documents per-plot qualifier semantics.
  Line 128-130: "For plot types, marker/line/axis options, and {it:if}/{in}
  qualifiers, {cmd:dash} accepts the same syntax as {helpb twoway}." Measured:
  twoway accepts `twoway (scatter mpg weight) (scatter mpg price) if
  foreign==1` with rc=0, dash accepts the same text with rc=0 and drops the
  restriction. The only `if` example in the help (line 641-643) is the single
  un-parenthesised plot form. Either implement the command-level capture and
  keep the sentence, or qualify the sentence and add an overlay example
  showing that a qualifier written inside a paren group binds to that layer
  only — and state which layer types cannot honour one.     *Where:*
  `dash.sthlp:128-130 (twoway-parity sentence), dash.sthlp:641-643 ("If
  qualifier" example block)`
- **[func · dash.ado · S]** Fix the silent loss of ANY if/in qualifier that
  contains a double-quoted string, and close the macro-name injection it rests
  on. `dash.ado:1224-1225` call the escaper as `_dash_json_str "`if_expr'"
  _jif` with PLAIN double quotes, contrary to the helper's own documented
  usage at `dash.ado:221` (``Usage: _dash_json_str `"`raw'"' "_escaped"``).
  `_dash_json_str` is `args raw_val out_macro` (dash.ado:224-234), so when the
  expanded value contains a `"` Stata re-tokenizes it: the escaped text is
  truncated at the quote and the macro NAME written by `c_local `out_macro'`
  is taken from the user's own string. Result: `"if_expr":""` for every
  string-valued qualifier, plus a write to an attacker-chosen local in
  `_dash_process_segment`'s frame. Fix both lines to the compound-quote form,
  add the same guard to the helper (reject/ignore an out_macro that did not
  come from the caller), and re-check the other 50 call sites (the remaining
  12 plain-quote sites, dash.ado:1143-1237, all pass variable names, which
  cannot contain a quote).     *Where:* `dash.ado:1224, dash.ado:1225 (call
  sites), dash.ado:219-234 (_dash_json_str), dash.ado:1093-1106 (if_cl/if_expr
  capture), dash.ado:1240/1244 (segment JSON assembly)`
- **[func · standalone · S]** Register the INTERSECTED row set for a per-plot
  view, not the qualifier's own rows. `_make_figure_body` intersects the
  per-plot mask with an existing facet/linked view (dash_render.py:9981-9989)
  but then registers the view with `self._row_ids_for(_pdf)` — the per-plot
  rows only (dash_render.py:9991-9992). The filter callback rebuilds every
  registered view from those member ids (`vf.filter.booleans = kept.map(id =>
  member.has(id))`, dash_render.py:7164-7170), so the first move of any filter
  widget throws the intersection away. It only bites when the source is SHARED
  — a linked `by()` panel and a linked graph's own graph-level qualifier —
  because in the unlinked case the panel source is itself the subset. Pass the
  intersected ids (or register the prior view's ids alongside and intersect in
  JS).     *Where:* `dash_render.py:9981-9992 (DashRenderer._make_figure_body
  per-plot block), dash_render.py:8509-8524 (_register_view_filter),
  dash_render.py:7163-7170 (_FILTER_JS view rebuild), dash_render.py:11892
  (_c` [WP-29 P0.15, commit 3cff164: closed]
- **[func · both · M]** Mask the mlabel LabelSet for a qualified layer.
  `_apply_mlabel_opts` (dash_render.py:3301) attaches a Bokeh `LabelSet`,
  which has NO `view` property, so a per-plot `if`/`in` never reaches it and
  every observation's marker label is drawn over a filtered layer. Nine
  mappers call it with an unmasked source (dash_render.py:3482, 3556, 3589,
  3657, 3762, 3814, 4955, 5000, 5038), i.e.
  scatter/line/connected/area/bar/spike and the rbar/rspike/rcap family. Fix
  by building the LabelSet over a masked copy of the label columns (and by the
  same token re-check `_apply_colorvar`, whose colour range is computed from
  the unmasked source). The emitted server app has its own LabelSet sites
  (dash_render.py:14454, 14484, 14502, 14532, 14552, 14585, 14655, 14925) that
  will need the same treatment once server mode reads per-plot qualifiers at
  all.     *Where:* `dash_render.py:3301-3400 (_apply_mlabel_opts),
  dash_render.py:3482 (map_scatter call),
  dash_render.py:3556/3589/3657/3762/3814/4955/5000/5038,
  dash_render.py:14454+ (emitted-app LabelSet lines)` [WP-29 P0.16, commit 85dc7d2: partly closed; open: the mlabel LabelSet is still not masked for a qualified layer]
- **[func · standalone · M]** Make the per-plot view and the glyph's actual
  source agree when a layer builds a private source. With `jitter()`,
  `map_scatter` draws from the copy returned by `_build_jitter_source`
  (dash_render.py:2521, called at dash_render.py:3459) while
  `_register_view_filter` was handed the GRAPH source (dash_render.py:9991).
  The copy is not in `self.sources`, so it is never passed as
  `all_graph_sources` and never shortened by the filter callback; after any
  widget move the rebuilt BooleanFilter has the kept-row length while the
  glyph's source still has the original length, and the mask lands on the
  wrong rows. Either register the view against the source the glyph really
  uses (and add that source to the callback's list), or jitter in place on the
  shared source.     *Where:* `dash_render.py:2521-2570
  (_build_jitter_source), dash_render.py:3459-3482 (map_scatter),
  dash_render.py:9987-9992 (view construction + registration),
  dash_render.py:11880-11893 (all_graph_sources / vi`
- **[func · standalone · M]** Give the browser-side aggregate recompute
  somewhere to put a row restriction, or histogram/kdensity per-plot
  qualifiers will regress on the first filter move even after the GlyphMapper
  mask-threading fix lands. `_dash_agg_config` (dash_render.py:4695 for
  histogram, 4905 for kdensity) carries only type/varname/bin_edges/ymode; the
  filter callback recomputes bins and densities from `new_data`
  (dash_render.py:7389-7430), and `new_data` is built from `orig_source`
  masked ONLY by the widget values (dash_render.py:7097-7102). Add the layer's
  member row ids to the agg config and intersect in JS (the same shape as
  `view_filters`). Note the graph-level qualifier shares this defect today, so
  one fix covers both.     *Where:* `dash_render.py:4695 and 4905
  (_dash_agg_config), dash_render.py:12203-12209 (agg_source_registry
  collection), dash_render.py:11905-11914 (agg_sources/agg_configs_json args),
  dash_render.py:7387-7430 (`
- **[deli · docs · S]** Correct the help text, which currently asserts a
  parity this task has not achieved, and record the section in the changelog.
  `dash.sthlp:129-131` says "For plot types, marker/line/axis options, and
  if/in qualifiers, dash accepts the same syntax as twoway", and Differences
  item 5 (dash.sthlp:~162-177) says "Nothing is ever dropped without being
  named" — both are false today for (a) a quoted-string qualifier, (b) a
  command-level qualifier written outside the parens, (c) a qualifier on any
  computed layer, (d) any qualifier in server mode. The only qualifier
  documentation is a one-line example at dash.sthlp:641-643. Add a
  Differences-from-twoway entry stating what a per-plot qualifier does
  (shared-source CDSView so link() still propagates) and what it does not
  reach, and add the 06-06 entry to the changelog.     *Where:*
  `dash.sthlp:129-131, dash.sthlp:162-177 (Differences item 5),
  dash.sthlp:641-643 (If qualifier example), .ultraplan/CHANGELOG.md`
- **[deli · both · M]** Add the two adversarial/regression tests that the
  injection above requires under project rules 8 and 18: (a) a cscript
  asserting that `dash scatter y x if svar=="text"` (and the `||` and paren
  forms) puts `"if_expr":"svar==\"text\""` in the registered spec and that
  `dash build` then renders only the matching rows; (b) an adversarial case
  asserting that a crafted qualifier cannot change any other spec field — e.g.
  `if make=="xvar zz"` must not alter `"xvar"`, and `if make=="_opts_json zz"`
  must not produce unparseable JSON. Neither exists: no test in the tree uses
  a quoted-string qualifier, and the security suites never touch `if_expr`.
  *Where:* `test/test_security_surface.py, test/test_adversarial.cscript,
  test/test_varlist_expansion.cscript,
  test/test_per_plot_qualifier_linking.py`

### 08-04 — Convert in the loader and give date figures a datetime axis (14 further items)

- **[func · server · S]** The emitted server loader must ALSO recover the
  display-string date transport before `pd.to_numeric` destroys it, mirroring
  `_load_data`'s `else:` branch (dash_render.py:8208-8226). Today a `%td`
  column that arrives as text ("02jan2001") is coerced to NaN in the generated
  app and the served figure gets ZERO rows, not a wrong-scale axis. Related
  and worth knowing before starting: the generated app ALREADY carries the
  date machinery it needs — `_format_date_value_standalone` is forwarded
  (dash_render.py:12395, lands at app.py:1410 and is called at app.py:3672
  from the forwarded GlyphMapper mlabel path) and the slider helper's
  `allow_datetime` branch (app.py:1221-1248, which does the correct
  `.astype('datetime64[ms]').astype('int64')`) is present. Both are
  unreachable solely because the emitted loader never creates a datetime64
  column, so fixing the loader lights up existing code rather than requiring
  new copies.     *Where:* `dash_render.py:13162-13165 (emitted loader's only
  coercion); dash_render.py:8208-8226 (the standalone branch to mirror);
  generated app lines 1221-1248 and 3672 (already-forwarded date machinery
  that i`
- **[func · standalone · L]** Teach the 21 glyph mappers that coerce their
  source columns with `np.array(source.data[xvar], dtype=float)` /
  `_extract_finite(source, var)` to accept a datetime64 column (convert to
  epoch ms with the existing `_extract_finite(..., allow_datetime=True)` path,
  compute, then convert the fitted/binned x values back to datetime64 before
  handing them to the glyph). 08-04's own `_load_data` clause created this:
  the loader now puts `Timestamp` objects in the DataFrame, and 20 of 31 plot
  types abort the ENTIRE dashboard build the moment a date variable is on an
  axis.     *Where:* `dash_render.py:964-995 (`_extract_finite`, which already
  has the `allow_datetime=True` branch that only `build_slider:7731` and
  `build_range:7809` pass); the 21 mappers that do not: `map_area:3614`, `` [WP-29 P0.8, commit cd210ea: closed]
- **[func · standalone · M]** Make `_figure_date_kind` read every variable-key
  shape `dash.ado` actually emits. It reads only `xvar`, `yvar` and `var`, so
  three whole plot families are invisible to the date decision, and for one
  family it puts the date on the WRONG axis: (a) `histogram`/`kdensity` emit
  `{"var":...}` and `_figure_date_kind` counts `var` under the `"yvar"` key,
  but `map_histogram` draws that variable as `left`/`right` i.e. on X — so
  once the crash above is fixed, `dash histogram datevar` will give a
  DatetimeAxis on the FREQUENCY axis and a LinearAxis on the date axis; (b)
  `rarea`/`rbar`/`rspike`/`rcap`/`rline`/`rconnected`/`rcapsym`/`rscatter`/`tsrline`
  emit `yvar1`/`yvar2` and are never consulted, so a date range band gets no
  datetime y-axis; (c) `pcspike`/`pcarrow`/`pcbarrow`/`pcscatter` emit
  `y1var`/`x1var`/`y2var`/`x2var` and get no datetime axis on either axis.
  *Where:* `dash_render.py:9268-9298 (`DashRenderer._figure_date_kind`); its
  two call sites dash_render.py:9559-9560 in `_make_figure_body`;
  dash_render.py:10415-10421 (`_add_glyph`, where the histogram/kdensity ` [WP-29 P0.8, commit cd210ea: partly closed; open: (b) the range types' yvar1/yvar2 and (c) the pc types' coordinates get no date axis (REM-08-04-C3b, C3c; DROPIN P1.23)]
- **[func · standalone · S]** Partition plots by their `options.yaxis` /
  `options.xaxis` before `_figure_date_kind` demands agreement. Today a single
  secondary-axis layer POISONS the primary axis: a graph whose primary y is a
  date loses its DatetimeAxis entirely as soon as any `yaxis(2)` layer carries
  a numeric variable, because both layers land in the same `kinds` set and the
  `None in kinds` branch bails. This is distinct from the secondary-axis item
  already reported — the damage here is to the PRIMARY axis, which was working
  before the second layer was added.     *Where:* `dash_render.py:9286-9297
  (`_figure_date_kind`'s loop and its `if len(kinds) > 1 or None in kinds:
  return None` bail); dash_render.py:9559-9560 (the two calls, which pass the
  unpartitioned `plots` list`
- **[func · standalone · S]** Convert `xline()` / `yline()` reference-line
  values to the datetime axis's millisecond scale. `_make_figure_body` drops
  each user value straight into `Span(location=float(v))`, so
  `xline(td(01jan2001))` — a Stata SIF day number — lands 14.977 seconds after
  1970-01-01 and is drawn off the figure, silently. Same class as the
  xlabel/xscale(range()) conversion already reported, but a separate code
  block that that fix will not touch.     *Where:* `dash_render.py:9843-9858
  (the `_parse_refline("xline", ...)` / `_parse_refline("yline", ...)` blocks
  and their `Span(location=float(...))` calls, inside `_make_figure_body`)`
- **[func · standalone · S]** Give `_apply_axis_spec` a date branch. Two
  defects on a date axis: (1) `xlabel(, format(%9.0fc))` — or any numeric
  picture, including one inherited from `self.numeric_formats` — OVERWRITES
  the DatetimeTickFormatter with a `NumeralTickFormatter`, so the ticks read
  as epoch milliseconds with thousands separators; (2) `xlabel(,
  format(%tdDD/NN/CCYY))` — a Stata DATE picture, the natural way to ask for a
  tick style — is silently discarded: `_stata_numeric_pattern` returns None
  and the warning branch explicitly excludes date formats (`elif
  spec["format"] and _stata_date_kind(fmt) is None`), so nothing is applied
  and nothing is said. 08-04's action clause promises a formatter "matched to
  the date kind"; a user-supplied kind is never honoured.     *Where:*
  `dash_render.py:9159-9170 (`_apply_axis_spec`, the
  `fmt`/`NumeralTickFormatter` block and its suppressed warning branch);
  dash_render.py:9598-9603 (`_make_figure_body`, where
  `_datetime_formatter_for` `
- **[func · standalone · S]** Convert `scatteri` / `pci` literal coordinates
  to the datetime axis's millisecond scale when the figure they are overlaid
  on has a date axis. The values arrive from `dash.ado` as a JSON array of raw
  Stata numbers and are placed on the figure unchanged, so an annotation point
  written with a date coordinate lands at 1970-01-01.     *Where:*
  `dash_render.py `map_scatteri` / `_add_pc_glyph` (dash_render.py:10423
  onward) and the `values` consumption path; the date kind is available on the
  figure via `_figure_date_kind` at dash_render.py:9559`
- **[func · standalone · S]** Stop `_stata_dates_to_datetime` raising on
  out-of-range period values. `_from_parts` calls `pd.to_datetime` on a
  year/month frame; for `%tm`/`%tq`/`%tw` values past pandas' Timestamp range
  that raises a bare `AssertionError`, which is not in the `except
  (OverflowError, ValueError, pd.errors.OutOfBoundsDatetime)` tuple, so it
  escapes `_load_data` and aborts the whole render instead of coercing to NaT
  with the warning 08-03 specified. (Recorded in REMAINING.md item 2 under
  08-04; not in the auditor's list. Reaching it is 08-04's loader clause.)
  *Where:* `dash_render.py:290-355 (`_stata_dates_to_datetime`), specifically
  `_from_parts` (dash_render.py:317-327) and the `except (OverflowError,
  ValueError, pd.errors.OutOfBoundsDatetime)` tuple at dash_rende`
- **[deli · standalone · S]** Add the task's own `<verify>` clause as a test:
  "an auto scatter is byte-identical ids aside". The section's TDD stub list
  asks for "a scatter of two non-date variables is byte-identical to before,
  ids aside" and no such test exists — the identity was only ever measured by
  hand in an audit scratch script, so nothing in the suite would catch a
  future change to `_load_data`/`_make_figure_body` that perturbs non-date
  figures. This is the guard the section's [red] risk note exists for.
  *Where:* `test/test_dates.py (add to `class TestDatetimeAxis`,
  dash_render.py:9495 `_make_figure_body` is the code under test); pattern to
  copy: test/test_layout_tabs.py:447`
- **[deli · dash.ado · S]** Add a Stata certification script for the date
  axis. Not one of the 25 `.cscript` files touches `sysuse sp500`, a `%t*`
  display format or a datetime axis, so the only Stata-side proof that 08-04
  works end to end is an ad-hoc audit run. Per the repo's own testing
  convention (cscripts, not .do files) a `test/test_dates.cscript` should
  build sp500 with a date x-axis and assert the emitted HTML carries
  `DatetimeAxis`/`DatetimeTickFormatter`, and — once the crash above is fixed
  — that `dash (scatter close date) (lfit close date)` and `dash histogram
  date` return rc 0.     *Where:* `test/ (new `test_dates.cscript`, alongside
  test/test_e2e_single.cscript for the house pattern);
  test/run_all_cscripts.do (registration)`
- **[func · standalone · L]** Fix the hard crash the 08-04 loader conversion
  introduced: 24 of 35 plot types abort the entire `dash build` when their x
  (or binned) variable is a Stata date. `_load_data` now hands `GlyphMapper` a
  datetime64 column, and 37 sites of the form `np.array(source.data[xvar],
  dtype=float)` raise `TypeError: float() argument must be a string or a real
  number, not 'Timestamp'`, which `_build_sources_and_figures`
  (dash_render.py:11510) re-raises as RuntimeError and Stata surfaces as rc
  7102. The machinery for the fix already exists — `_extract_finite`
  (dash_render.py:964-995) takes `allow_datetime=True` and casts via
  `astype('datetime64[ms]').astype('int64')`, and is called that way at
  dash_render.py:7731 and :7809 — but the glyph call sites at :4666
  (`map_histogram`) and :4830 (`map_kdensity`) omit the flag, and the 35
  remaining `np.array(source.data[...], dtype=float)` sites have no equivalent
  at all. Note the CDS column arrives object-dtype (a list of `Timestamp`),
  not datetime64, so an `np.issubdtype(...)` guard is not sufficient — route
  through `pd.Series(col)` / `pd.api.types.is_datetime64_any_dtype` as
  `_extract_finite` already does.     *Where:* `dash_render.py:3614-3615
  (`map_area`), :3787-3788, :3845-3846 (`map_lfit`), :3895-3896 (`map_qfit`),
  :3942-3943 (`map_lfitci`), :4023-4024, :4127-4128 (`map_lowess`),
  :4300-4301, :4366-4367, :4543-454`
- **[func · standalone · S]** Correct `_figure_date_kind`'s axis mapping for
  the single-variable plot types. `dash.ado:1142-1144` emits `"var"` (not
  `xvar`/`yvar`) for `histogram` and `kdensity`, and Stata draws that variable
  on the X axis. `_figure_date_kind` folds `var` into the **y** lookup only
  (`name = plot.get(key, "") or (plot.get("var", "") if key == "yvar" else "")
  or fallback`), so a `%td` histogram variable is classified as a date on Y
  (the density axis) and not on X. Once the crash above is fixed this yields
  an exactly inverted figure: a DatetimeAxis on the frequency axis and raw SIF
  integers on the date axis. `var` should feed the `xvar` branch for
  `histogram`/`kdensity`, and `_make_figure_body`'s `xvar =
  plots[0].get("xvar", "")` (dash_render.py:9506) should fall back to `var`
  for those types so the axis label is right too.     *Where:*
  `dash_render.py:9268-9298 (`_figure_date_kind`), specifically the `name =
  ...` expression at :9288-9290; dash_render.py:9506-9507 (`xvar`/`yvar`
  derivation in `_make_figure_body`); dash.ado:1142-1144 (` [WP-29 P0.8, commit cd210ea: closed]
- **[deli · dash.ado · S]** Add a Stata certification script covering the
  section's own `<verify>` clause end to end. Task 08-04's verify is "sp500
  renders calendar dates on the x-axis", and nothing in `test/` exercises it
  from Stata: no cscript mentions sp500, `%td` or DatetimeAxis. A cscript that
  runs `sysuse sp500; dash line close date; dash build` and greps the produced
  HTML for `"DatetimeAxis"` — plus the computed-layer cases `dash (scatter
  close date) (lfit close date)` and `dash histogram date` asserting rc 0 — is
  what would have caught the crash above before it shipped.     *Where:*
  `test/ (new cscript, e.g. test/test_dates.cscript, registered in
  test/run_all_cscripts.do alongside the existing 25)`
- **[deli · standalone · M]** Add pytest coverage for non-`line` glyphs on a
  date variable. `test/test_dates.py::TestDatetimeAxis._fig` builds only
  `{"type": "line", ...}` (test/test_dates.py:334-404), so the whole
  computed-layer and area/spike/r-family surface is untested against a date
  column — which is why a total build failure on 24 of 35 plot types passes
  CI. Parametrise a date case over at least `area`, `spike`, `lfit`, `qfit`,
  `lowess`, `histogram`, `kdensity`, `rbar`, `rcap` and assert the build
  completes and the date reaches the glyph on the millisecond scale.
  *Where:* `test/test_dates.py:334-404 (`TestDatetimeAxis`, helper `_fig` at
  :335-343)`

### 08-05 — Format dates and numbers everywhere they are displayed (15 further items)

- **[func · standalone · S]** `_stata_dates_to_datetime`
  (/Users/billy/Desktop/Programs/StataPrograms/d/dash/dash_render.py:290)
  crashes `dash` outright on an out-of-range value for the five period-based
  kinds (%tm, %tq, %th, %tw, %ty). Its `except (OverflowError, ValueError,
  pd.errors.OutOfBoundsDatetime)` at dash_render.py:357 does not catch what
  pandas 3.0.1 actually raises. `_from_parts` (dash_render.py:318-328) assigns
  into a `pd.Series(pd.NaT, dtype='datetime64[ns]')` via `out.loc[ok] =
  pd.to_datetime(...)`; when the resulting year exceeds 2262 pandas raises
  `AssertionError` from `blocks.coerce_to_target_dtype(...,
  raise_on_upcast=True)`, which propagates through `DashRenderer._load_data`
  (dash_render.py:8210) and out of `render()`. Section 08-03's action text
  explicitly requires the opposite: 'Do not raise on out-of-range values ...
  Clamp or coerce and emit a `UserWarning` naming the variable.' The %tc and
  %td branches do honour that (they warn and yield NaT); the period branches
  do not. Fix: catch `Exception` (or `AssertionError`) in the try at
  dash_render.py:330-358, or build the period series with `errors='coerce'`
  into an object/`datetime64[us]` Series instead of assigning into a
  `datetime64[ns]` block.     *Where:*
  `/Users/billy/Desktop/Programs/StataPrograms/d/dash/dash_render.py:290
  `_stata_dates_to_datetime`, its `_from_parts` closure at :318-328 and the
  `except` at :357; reached from `DashRenderer._load_data``
- **[deli · standalone · S]** No test anywhere in test/ exercises the
  out-of-range date path that section 08-03 asked for ('Clamp or coerce and
  emit a UserWarning naming the variable'). Add a test per date kind that an
  out-of-range SIF value produces NaT plus a `UserWarning`, and never an
  exception — the existing suite only covers in-range values, which is why the
  %tm/%tq/%th/%tw/%ty crash above has never been seen.     *Where:*
  `/Users/billy/Desktop/Programs/StataPrograms/d/dash/test/test_dates.py (add
  to `TestFormatClassification`'s neighbours, near the conversion tests)`
- **[func · standalone · S]** Hover rows are labelled with the EMPTY STRING
  for any variable that carries no Stata variable label. `_axis_label`
  (dash_render.py:9300) is `return self.variable_labels.get(varname, varname)`
  — jsonio supplies `""` for an unlabelled variable, so the key EXISTS with an
  empty value and the `varname` default never fires. 08-05's own change at
  dash_render.py:10233 (`_hover_fields.append((self._axis_label(col), spec))`,
  introduced by commit 783043e "Carry Stata display formats through to the
  browser, and fix dates entirely") swapped the raw name for this, so the fix
  made unlabelled variables WORSE than the raw names it replaced. The same
  helper feeds the fallback histogram/KDE tooltips at dash_render.py:10282 and
  10295. Fix: `self._axis_label(col) or col`, or give `_axis_label` an
  empty-string fallback (which also fixes the blank axis title it produces on
  the same build).     *Where:* `dash_render.py:9300
  `DashRenderer._axis_label`; dash_render.py:10233 in
  `_make_figure._hover_row`; dash_render.py:10282, 10295 (fallback tooltips)` [WP-29 P0.3, commit 8d3593e: closed]
- **[deli · standalone · S]** Strengthen
  `test_a_date_dropdown_shows_dates_not_epoch_numbers` — it passes against the
  broken dropdown and so certifies nothing. It reads only the LABEL half of
  each option tuple (`labels = [o[1] ... for o in w[0].options]`) and asserts
  `"2001" in joined` and `"14977" not in joined`.
  `str(Timestamp('2001-01-02'))` = '2001-01-02 00:00:00' satisfies both, so
  the test is green while (a) the option VALUE is an ISO string that can never
  equal `String(<epoch ms>)` and (b) the label ignores the variable's Stata
  picture. Add assertions on `o[0]` (the value must be the epoch-millisecond
  number that `_FILTER_JS` compares against) and on the label matching the
  %tm/%td picture, and add a JS-level or DOM-level assertion that selecting an
  option leaves a non-zero row count.     *Where:* `test/test_dates.py:569
  `TestDateFilterWidgets::test_a_date_dropdown_shows_dates_not_epoch_numbers``
- **[deli · both · M]** No test anywhere exercises server-mode display
  formats, and the two parity suites that exist to catch exactly this
  divergence are blind to it because they hardcode an empty formats map. Add a
  date/format case to `test/test_mode_parity.py` and
  `test/test_filter_widget_parity.py` (a %td x-variable, a %tm dropdown, a
  %12.0fc KPI) so that the standalone/server split the auditor found —
  DateRangeSlider vs RangeSlider, 'Jan 2001' vs '492.0', '31 Dec 2001' vs
  '15340.0' — fails a test instead of needing a manual probe.     *Where:*
  `test/test_mode_parity.py:74; test/test_filter_widget_parity.py:61;
  test/test_server_*.py`
- **[func · standalone · L]** Give every computed/sorted mapper a
  datetime-aware x/y extraction. 19 mappers cast the shared source column with
  `np.array(source.data[xvar], dtype=float)` (or call `_extract_finite`
  without `allow_datetime=True`), which raises on a Timestamp;
  `_build_sources_and_figures` re-raises it as a RuntimeError, so the WHOLE
  dashboard aborts with rc 7102 and no HTML file whenever a date variable is
  on the axis of a fit, smoother, univariate, range or area layer.
  `allow_datetime=True` was added for the two filter builders only. Each
  mapper must read the column as epoch ms (the `_extract_finite(...,
  allow_datetime=True)` path already does this correctly) and map the computed
  x back to datetime64 before it reaches the glyph source, or the fitted line
  lands at 1970.     *Where:* `dash_render.py:964 `_extract_finite` (the
  `allow_datetime` switch) and its two format-blind callers at :4666
  `map_histogram`, :4830 `map_kdensity`; the float-cast pairs at :3614
  `map_area`, :3787 `map` [WP-29 P0.8, commit cd210ea: closed]
- **[func · standalone · M]** Stop `colorvar(datevar)` from destroying the
  shared date column. `_apply_colorvar` decides numeric-ness with
  `np.array(raw_col, dtype=float)` inside a try/except; a datetime64 column
  raises, so `is_numeric` is False, `use_discrete` is forced True, and the
  categorical branch writes `source.data[varname] = [str(v) for v in raw_col]`
  back into the SHARED source. Every later consumer of that column then sees
  strings. Route the date case through `date_vars` (the mapper already carries
  `date_vars`/`numeric_formats`, assigned at dash_render.py:8141-8142 and used
  by `_apply_mlabel_opts`): bin on epoch ms, label the key with
  `_format_date_value_standalone`, and never overwrite the transported column.
  The same branch shows raw floats for a `%12.0fc` colorvar key.     *Where:*
  `dash_render.py:2995 `GlyphMapper._apply_colorvar`; the numeric probe at
  :3095-3100; the stringifying write at :3180 `source.data[varname] = [str(v)
  for v in raw_col]`; the value-label branch at :3160-`
- **[func · standalone · S]** Carry the Stata numeric display format onto
  filter slider/range ENDPOINTS. `build_slider` and `build_range` already take
  `date_kind` and set `format=DatetimeTickFormatter()` for clock series, but a
  plain numeric widget is built with no `format=` at all, so Bokeh's default
  `0[.]00` shows `3000000.00` for a `%12.0fc` variable.
  `_stata_numeric_pattern` already returns `'0,0'` for that format; pass it
  through the same way `date_kind` is passed. The section Overview names
  "slider endpoints" as one of the six places the format is lost.     *Where:*
  `dash_render.py:7707 `FilterBuilder.build_slider` (numeric branch at
  :7766-7768), :7788 `FilterBuilder.build_range` (numeric branch at
  :7841-7844); the two call sites that would pass it, dash_render.py`
- **[func · standalone · S]** Format dropdown option LABELS through the
  variable's Stata numeric format. `_resolve_label` resolves value labels only
  and returns the raw string otherwise, so a `%12.0fc` filter dropdown lists
  `3000000`, `3010000`, ... instead of `3,000,000`. This is the non-date half
  of the value/label split the task asks for, and the section Overview names
  "dropdown options" explicitly. Distinct from the auditor's two date-dropdown
  items: fixing the date branch alone leaves formatted numerics unformatted.
  *Where:* `dash_render.py:7571 `FilterBuilder.build_dropdown`,
  `_resolve_label` at :7640-7648, the options build at :7657-7659; caller
  dash_render.py:11760-11775 (where a `numeric_fmt`/`date_kind` argument
  would`
- **[func · standalone · S]** Apply formats in the FALLBACK hover path. When
  no renderer carries the original variable columns (a
  histogram/kdensity/fit-only figure), `_make_figure` builds `_fb_fields` from
  the derived CDS with `_tooltip_precision` alone — it never consults
  `date_vars` or `numeric_formats` and never sets a `formatters` dict, so a
  binned date hovers as raw epoch milliseconds and a `%9.0fc` variable loses
  its commas. This path is currently masked by the crash in item 1; it becomes
  user-visible the moment that is fixed.     *Where:*
  `dash_render.py:10262-10305 (the `_fb_fields` fallback inside
  `DashRenderer._make_figure`), to mirror `_hover_row` at :10215-10234;
  `_tooltip_precision` at :174`
- **[func · both · M]** Render the calendar-period formats with Stata's own
  period picture. `_format_date_value_standalone` collapses `%tm`/`%tq`/`%th`
  to `"%b %Y"` and sends `%tw` to the day branch, so a quarterly variable
  reads "Jan 1960" where Stata writes "1960q1", a half-yearly one "Jan 1960"
  vs "1960h1", and a weekly one "29 Jan 1958" vs "1958w5". Hover is worse —
  `{%F}` for every kind but `tc` — but that half is already on the auditor's
  list; the value formatter, its JS twin and `_datetime_formatter_for` share
  the same collapse, so KPI cards, facet titles, marker labels and (once
  fixed) dropdown labels all mis-state the period. The Stata truth is already
  in the repo and unused: `test/fixtures/date_truth.json` records a `display`
  string for every value, and only the `iso` field is ever asserted.
  *Where:* `dash_render.py:203 `_format_date_value_standalone` (kind table at
  :215-220), dash_render.py:8860 `DashRenderer._format_date_value`, the JS
  twin inside `_FILTER_JS` at dash_render.py:7285-7307 (which m`
- **[deli · standalone · S]** Add a test that a figure carries exactly ONE
  HoverTool and that it is the labelled/formatted one. Both existing hover
  tests use `any(...)` over all tools, so they pass unchanged while
  GlyphMapper's raw-variable-name HoverTool is still attached and active — the
  defect the auditor found in the browser. Without this the fix to that defect
  has no regression guard.     *Where:* `test/test_dates.py:591-623
  `TestHoverShowsDates`; the code under test at dash_render.py:2564
  `GlyphMapper._hover_tool` and dash_render.py:10199-10202`
- **[deli · standalone · M]** Execute the shipped `_FILTER_JS` against a date
  column under node, as the task's "verify rather than assume ... assert it in
  the test" clause asks. Today every date-filter assertion is structural
  (snapshot dtype, slider bounds, the substring 'datekind' appearing in the JS
  source); nothing runs the callback, which is why the dropdown's value/label
  mismatch survived the test suite. The harness already exists and can be
  reused verbatim.     *Where:* `test/test_dates.py:626-714
  `TestDateFilterActuallyFilters` (add the node-executed cases here); pattern
  source test/test_kpi_values.py:263-300; code under test
  dash_render.py:7070-7090 (`_FILTER_JS` ro`
- **[deli · standalone · S]** Add tests for the NUMERIC half of "format ...
  everywhere they are displayed". The section's stub list asks that `%9.0fc`
  render with thousands separators in hover, KPI and tick labels; only the
  pure helpers are tested. Missing: (a) a hover spec test that a `%9.0fc`
  column produces `@{v}{0,0}`; (b) a KPI test with NO `fmt()` proving the
  variable's own format is the fallback (the only numeric KPI test passes
  `fmt="%9.2f"` explicitly); (c) slider/range endpoint and dropdown label
  tests (items 3 and 4 above); (d) a non-date/non-formatted negative twin for
  `_facet_label` — `test_mlabel_on_a_plain_variable_is_unchanged`,
  `test_a_numeric_filter_is_unchanged` and `test_a_numeric_kpi_is_unchanged`
  exist, the facet one does not.     *Where:* `test/test_dates.py:406-486,
  :490-527 (`TestKpiValuesFormatAsDates`), :528-590 (`TestDateFilterWidgets`),
  :716-760 (`TestFacetAndMarkerLabels`); test/test_axis_options.py:175-220`
- **[deli · dash.ado · M]** Give section 08 Stata-side end-to-end coverage
  that would catch a build failure on a date variable.
  `test/test_formats.cscript` — named in 08-01's `<files>` — does not exist,
  and no .cscript in the repo builds any dashboard on a %t variable, so the rc
  7102 abort in item 1 is invisible to the certification suite. The only date
  exemplar, examples/sp500_dates.do, uses `line` twice and nothing else, so
  `test_examples_run.cscript` cannot reach a fit, histogram or area layer
  either. Minimum: a cscript asserting rc 0 and a non-empty file for `dash
  (scatter close date) (lfit close date)`, `dash histogram date` and `dash
  area close date` on sysuse sp500, plus the master JSON carrying a populated
  `formats` map; and extend the exemplar with one computed layer so the corpus
  exercises it.     *Where:* `new test/test_formats.cscript (follow
  test/test_e2e_single.cscript:1-60 for the cscript preamble and the
  `c(python_exec)` skip rule); examples/sp500_dates.do;
  test/test_examples_run.cscript:56-84 (the`

### 09-02 — Implement the axis_label and axis_scale grammars (19 further items)

- **[func · standalone · S]** DashRenderer's xlabel(minmax)/ylabel(minmax)
  computes the min and max from the UNFILTERED frame (self.df), not from the
  graph's active, qualifier-narrowed source, so a tick is drawn where no data
  exists. _apply_axis_spec's minmax branch (dash_render.py:9136-9142) reads
  `col = self.df[varname]`; two other places in the same function body already
  do the right thing with `_source_frame(source, self.df)`
  (dash_render.py:9676 and :9713, _compute_secondary_range), and `source` is
  in scope at the tick loop (dash_render.py:9903-9913, inside
  _make_figure_body which starts at :9495). Fix: pass `_source_frame(source,
  self.df)` into _apply_axis_spec and have the minmax branch read that frame
  instead of self.df. Note this is in addition to server mode, which has no
  minmax at all (auditor's remaining item 1). A guard test belongs in
  test/test_axis_options.py: minmax + graph-level if_expr must give the
  subset's min/max. Do NOT 'fix' the by() facet case the same way — Stata's
  by() shares a common axis by default, and dash's global minmax across facets
  matches that.     *Where:* `dash_render.py:9136-9142 (_apply_axis_spec
  minmax branch, `col = self.df[varname]`); call site
  dash_render.py:9903-9913; the correct pattern is at dash_render.py:9676 and
  :9713 (`_source_frame(source,`
- **[deli · docs · S]** dash.sthlp documents xtick()/ytick() as "x-axis tick
  positions without labels" — the opposite of what the code does. The xtick
  semantics item (auditor item 3) names only dash_render.py; the help sentence
  is a second, independently shipped false claim and must be corrected now or
  fixed together with the code.     *Where:* `dash.sthlp:866-869 (the
  xtick()/ytick() synopt entries); code side dash_render.py:9906-9913`
- **[deli · docs · S]** dash.sthlp's minor-tick deferral note gives a false
  technical rationale and redirects users to a broken option. It says Bokeh
  draws one tick level per axis — Bokeh 3.9 supports minor ticks directly —
  and tells the reader that xtick() and xlabel() are honoured, when xtick() is
  exactly the option that is wrong. This note must also be removed in lockstep
  with dash.ado's _dash_pending entries when
  xmtick()/ymtick()/xmlabel()/ymlabel() are implemented, or
  test/test_help_conformance.py::test_nothing_listed_there_is_honoured fails.
  *Where:* `dash.sthlp:1116-1119; dash.ado:381-384 and dash.ado:629-632
  (_dash_pending); test/test_help_conformance.py:184 and :352`
- **[deli · docs · S]** dash.sthlp advertises the whole new axis_label grammar
  and xscale(range()) with no server-mode caveat, while none of it reaches
  `dash serve`. The help's Server Mode difference table (dash.sthlp:512-525)
  lists what differs between the two modes and does not mention axes, so a
  served user is told the grammar works. Either port it (auditor items 1 and
  2) or state the limitation in the table until then.     *Where:*
  `dash.sthlp:873-895 (axis-label grammar block), dash.sthlp:512-525 (Server
  Mode difference table)`
- **[deli · both · S]** Extend the standing standalone/server parity guard so
  the next axis drift fails there. test/test_mode_parity.py is the file whose
  docstring promises "the next divergence fails here rather than being found
  by a user", yet its figure-chrome comparison checks only background/border
  colour and grid presence — never ticker type, tick positions, formatter or
  major_label_text_font_size — and its CORPUS carries no axis graph_options at
  all. That is structurally why every 09-02 server gap went unnoticed. The
  auditor's deliverable item only asks for server cases inside
  test/test_axis_options.py.     *Where:* `test/test_mode_parity.py (CORPUS
  near :287 and _chrome/test_same_figure_chrome at :337-349)`
- **[func · standalone · S]** xscale2()/yscale2() never pass through
  _report_unhandled_scale_opts, so noextend/extend/alt/fextend on a secondary
  axis is dropped in total silence while the same token on the primary axis
  warns. Auditor item 5 names only the missing range() support on the
  secondary scales.     *Where:* `dash_render.py:9683 and dash_render.py:9718
  (add the _report_unhandled_scale_opts(raw, 'yscale2'/'xscale2') call, helper
  at dash_render.py:805)`
- **[func · both · M]** A bare (unquoted) non-numeric token in
  xlabel()/ylabel() is silently turned into a TICK LABEL, so Stata's `to` rule
  paints the word "to" on the axis. `DashRenderer._parse_axis_label_opt`
  (dash_render.py:9393) pairs every number with the next token whatever it is
  — it never requires quotes — and `_parse_axis_spec` (dash_render.py:9305)
  feeds it the leftover head text. This is the BR-09.2 leak the section was
  written to eliminate, surviving inside the helper 09-02 kept. Fix: only
  accept a QUOTED token as a label in `_parse_axis_label_opt`, and report (or
  expand) an unrecognised bare word; the emitted server app carries its own
  copy of the same tokenizer at dash_render.py:13989 `_parse_axlabel`.
  *Where:* `dash_render.py:9393 `DashRenderer._parse_axis_label_opt`
  (bare-token branch, ~:9425-9432); dash_render.py:9305 `_parse_axis_spec`;
  emitted copy dash_render.py:13989 `_parse_axlabel``
- **[func · both · M]** Three numlist rules Stata accepts are unimplemented
  and silently produce the wrong ticks or none: `a/b` (10/15), `a b to c` (10
  15 to 40) and `##N` (##5). `_parse_axis_spec` (dash_render.py:9305) handles
  only `a(b)c`, `#N`, `minmax`, `none` and bare values, so `/` and `##` fall
  through to the default ticker and `to` degrades as described in the leak
  item. The task's <done> is "Axis labelling accepts what twoway accepts and
  produces what twoway produces".     *Where:* `dash_render.py:9305
  `DashRenderer._parse_axis_spec` (add `/` and `to` rules next to the existing
  `a(b)c` regex, and `##N` beside the `#N` branch); mirror into
  dash_render.py:13989 `_parse_axlabel``
- **[func · both · M]** The clause "when no format() is given, the variable's
  Stata display format from S08" does not work on a default axis, for two
  independent reasons. (1) The axis loop `continue`s when neither xlabel nor
  xtick is present (dash_render.py:9908-9911), so `_apply_axis_spec`'s
  `numeric_formats` fallback at dash_render.py:9160 is unreachable unless the
  user also writes xlabel(). (2) `_stata_numeric_pattern` (dash_render.py:395)
  returns None for every non-`f` format, so Stata's DEFAULT numeric format
  family — auto.dta's own `%8.0gc` on weight and price — never yields a
  pattern even when the fallback does run. Stata labels those axes with
  thousands separators; dash does not.     *Where:* `dash_render.py:9903-9913
  (the `if not raw_ax and not raw_tick: continue` guard);
  dash_render.py:9160-9170 in `_apply_axis_spec`; dash_render.py:395
  `_stata_numeric_pattern` (the `if kind != "f": retur`
- **[func · both · L]** `_apply_axis_spec` has no date awareness, so every
  axis_label and axis_scale form is wrong on a %t* axis. The renderer converts
  date columns to datetime64 (dash_render.py:8196-8210) and Bokeh's
  DatetimeAxis works in epoch MILLISECONDS, but: explicit ticks are passed
  through as raw Stata date numbers; `minmax` emits `float(vals.min())` of a
  datetime column, i.e. MICROseconds (1000x too large); `#N` replaces the
  DatetimeTicker with a BasicTicker; `format(%td...)` is silently ignored (the
  `elif spec["format"] and _stata_date_kind(fmt) is None` guard at :9166
  suppresses even the warning); and `xscale(range())` builds a Range1d in date
  units. The helper that knows the answer, `_figure_date_kind`
  (dash_render.py:9268), is never consulted here.     *Where:*
  `dash_render.py:9112 `_apply_axis_spec` (minmax :9137-9144, count
  :9145-9148, explicit :9149-9158, fmt :9160-9170); dash_render.py:9268
  `_figure_date_kind`; dash_render.py:9747-9773 (the xscale/yscale `
- **[func · standalone · S]** `#N` and explicit ticks overwrite the axis's own
  ticker class, so `xscale(log) xlabel(#5)` puts LINEAR tick placement on a
  log axis. `_apply_axis_spec`'s count branch assigns a bare
  `BasicTicker(desired_num_ticks=N)` with no regard for the
  LogAxis/DatetimeAxis already built.     *Where:* `dash_render.py:9145-9148
  in `_apply_axis_spec` (`axis_obj.ticker =
  BasicTicker(desired_num_ticks=spec["count"])`) — choose
  LogTicker/DatetimeTicker by `type(axis_obj)``
- **[func · standalone · S]** `minmax` is computed from the wrong rows and the
  wrong variable: `_apply_axis_spec` reads `self.df[varname]` — the WHOLE
  dataset — so a graph-level `if`/`in` qualifier is ignored, and `varname` is
  `plots[0]`'s x/y variable (dash_render.py:9506-9507), so a two-series graph
  labels the axis at the FIRST series' bounds. Nothing recomputes it when a
  filter widget moves either, because the ticks are baked into a FixedTicker
  at build time. The one-bound fallback for `xscale(range(0))` at
  dash_render.py:9765-9770 reads the same unfiltered frame.     *Where:*
  `dash_render.py:9137-9144 in `_apply_axis_spec`; the `varname` passed at
  dash_render.py:9913; dash_render.py:9506-9507 (`xvar`/`yvar` = plots[0]);
  the range fallback at dash_render.py:9765-9770 — use t`
- **[func · both · S]** The value-`label` tick form is broken at runtime in
  the served app, and the standalone's copy of it is HTML-escaped canvas text.
  The CustomJSTickFormatter map is keyed with Python's `str(float)` ("2000.0")
  while the JS in it looks up `String(tick)`, which is "2000" for an integral
  tick — so the lookup always misses. Standalone survives only because
  `_apply_axis_spec` also sets `major_label_overrides`, which Bokeh applies
  ahead of the formatter; the emitted server app sets no overrides, so a
  served `xlabel(2000 "low" 4000 "high")` draws 2000/4000. Separately, the
  standalone escapes the label text into the JS map (`R&amp;D`), which is the
  same "canvas text must not be html.escaped" defect the section registers at
  `:5638`.     *Where:* `dash_render.py:9149-9158 in `_apply_axis_spec` (key
  the map with the same string JS produces, drop the `html.escape`); emitted
  app dash_render.py:14015-14021 (needs `major_label_overrides`, not just t`
- **[func · both · S]** Only five xscale()/yscale() sub-options are
  recognised; the rest are dropped with no warning, including `off`, which in
  Stata removes the axis entirely. `_report_unhandled_scale_opts` lists
  exactly noextend/extend/alt/fextend/nofextend, so `yscale(off)`, `noline`,
  `titlegap()`, `lcolor()/lwidth()/lpattern()` and `axis(#)` pass through in
  silence — the opposite of the honesty rule the same function was added to
  satisfy. `off` is a two-line implementation (`axis_obj.visible = False`).
  *Where:* `dash_render.py:805 `_report_unhandled_scale_opts` (extend the
  token list); dash_render.py:9747-9773 (apply `off`); server side has neither
  (see the auditor's server range item)` [WP-29 P0.5, commit 3208b2b: partly closed; open: `off`, `noline`, `titlegap()`, `lcolor()`/`lwidth()`/`lpattern()` still pass through (DROPIN P1.18)]
- **[func · both · S]** axis_label sub-options outside the implemented five
  are silently dropped, and `axis(#)` is actively misrouted: `xlabel(1000
  2000, axis(2))` applies the ticks to the PRIMARY x axis instead of the
  second one. `_parse_axis_spec` strips
  `labcolor/labgap/tlength/labstyle/tstyle/tposition` into the bin and
  truncates at the first sub-option comma, so `valuelabel`, `alternate`,
  `notick`, `add`, `custom` and `angle(stacked)` vanish with no report.
  *Where:* `dash_render.py:9305 `_parse_axis_spec` (the sub-option strip
  regex, ~:9344-9350); dash_render.py:904 `_parse_axis_angle`; route `axis(2)`
  to the secondary-axis code at dash_render.py:9699/:9734 or rep` [WP-29 P0.5, commit 3208b2b: partly closed; open: `valuelabel`, `alternate`, `notick`, `add`, `custom` and `angle(stacked)` (DROPIN P1.18, P2.20)]
- **[func · standalone · S]** The `grid` sub-option paints a hardcoded
  `#e5e5e5` instead of the scheme's gridline colour, which the renderer
  already computes as `self.grid_color` and applies everywhere else
  (dash_render.py:2180). A style literal of exactly the kind the branch's
  recent commits claim to have removed from both renderers.     *Where:*
  `dash_render.py:9184-9190 in `_apply_axis_spec` (`g.grid_line_color =
  "#e5e5e5"`); reuse `self.grid_color` / `self.minor_grid_color` as at
  dash_render.py:2180-2185`
- **[deli · docs · M]** The Stata ground-truth fixture is requested by the
  axis tests and never read: ten tests take the `truth` fixture and not one
  indexes it, so every assertion is hardcoded to dash's own numbers rather
  than to what Stata measured. In particular no test asserts tick LABEL text,
  which is why the missing default display format (item 3) and the `to` leak
  (item 1) went unnoticed. And
  `test_a_date_axis_ignores_a_numeric_format_gracefully`
  (test/test_axis_options.py:218) asserts only `fig is not None`, on
  `_SCATTER` — a frame with no date column at all — so the date path has no
  coverage whatsoever.     *Where:*
  `test/test_axis_options.py:136,152,157,171,218 (and the other truth-taking
  tests); test/fixtures/axis_truth.json`
- **[deli · dash.ado · M]** There is no Stata-side certification script for
  the axis grammar. Section 09-01 names `test/test_axis_options.cscript` in
  its <files> and it does not exist, so nothing checks that dash.ado's
  `syntax` accepts and transports each axis_label form end to end — which is
  how `ylabel(10 15 to 40)` reaches a shipped dashboard with a tick labelled
  "to" while pytest is green.     *Where:* `test/ (new
  test_axis_options.cscript); pattern to copy:
  test/test_option_surface.cscript, test/run_all_cscripts.do`
- **[deli · both · M]** Server-mode axis behaviour is covered only by source
  greps, so no test can fail on the server gaps. test/test_server.py:999-1006
  asserts `"xlabel" in source and "FixedTicker" in source` — true of the
  pre-09-02 parser as well — and test/test_mode_parity.py compares only
  background/border colours and whether a grid exists, with no axis cases in
  its parametrization and no ticker/formatter comparison.     *Where:*
  `test/test_mode_parity.py (add xlabel/ylabel/xscale cases comparing ticker
  type, tick values, formatter and major_label_overrides);
  test/test_server.py:988-1010`

### 09-07 — HTML escaping, hover, secondary-axis range, mlabel on lines (14 further items)

- **[func · both · S]** Canvas text is STILL html.escape()d at six more sites
  that the 09-07 fix never touched — the fix only removed the escape from the
  figure title and the two primary axis titles. `legend(label(1 "R&D"))`,
  by()-facet panel titles, the colorvar legend/colorbar title, and
  secondary-axis tick labels all still draw HTML entities on the canvas.
  *Where:* `dash_render.py:10165 (DashRenderer._make_figure_body, legend
  label(N "...") overrides) and its server twin dash_render.py:14987 (`_lt =
  html.escape(_lm.group(2))`); dash_render.py:8917 (DashRenderer._`
- **[func · standalone · S]** Facet/`by()` titles are still HTML-escaped in
  the STANDALONE renderer. `DashRenderer._facet_label` escapes the Stata value
  label it returns, and that string becomes the facet figure's canvas title —
  the identical defect 09-07 fixed for `title()`/`xtitle()`/`ytitle()`. The
  auditor (and REMAINING.md) reported the facet-title escape only for
  `ServerAppBuilder` (:15096/:15116) and declared canvas text "fixed in
  DashRenderer". Fix: drop `html.escape` at dash_render.py:8917 the same way
  :9518-9519 were fixed.     *Where:* `dash_render.py:8917
  (`DashRenderer._facet_label`); compare the in-file precedent at :9517-9519
  and :9541`
- **[func · standalone · S]** `ylabel2()`/`xlabel2()` custom tick labels are
  HTML-escaped into the `CustomJSTickFormatter` and, unlike the primary axis,
  get NO `major_label_overrides` to mask it — so `ylabel2(1 "R&D")` draws
  `R&amp;D` on the secondary axis. Fix: either stop escaping at
  dash_render.py:9703/:9738, or set `major_label_overrides` with the raw text
  the way the primary-axis path at :9152-9161 does.     *Where:*
  `dash_render.py:9703 (`_safe2` for `_y2_ax.formatter`), :9738 (same for
  `_x2_ax`); correct precedent at :9152-9161 (`safe` +
  `axis_obj.major_label_overrides`)`
- **[func · server · S]** The emitted server app double-escapes the
  browser-tab title: `title_text` is built with `html.escape()` once and then
  used BOTH for the header `<h2>` Div (correct) and for `doc.title` (wrong) —
  Bokeh's page template escapes `doc.title` again. Under `dash serve` the tab
  reads `Price &amp; Weight` where `dash build` reads `Price & Weight`. This
  is the same 09-07 "escape once, in one place" clause, still open in server
  mode. Fix: keep the raw title in a separate local, escape only at the
  `<h2>`/`<div>` interpolation sites, and assign the raw string to `doc.title`
  (mirroring the standalone, which passes the RAW `title_text` to
  `file_html`).     *Where:* `dash_render.py:13717 and :15940 (emitted lines
  inside `ServerAppBuilder._generate_app_source`, :12740); header consumers at
  :15932/:15935; standalone precedent at :12130 + :12174`
- **[deli · dash.ado · S]** No regression test exists for the hover()
  serialization gap, on either side. The auditor's deliverable list names only
  the missing dash.sthlp entry. Per CLAUDE.md #8 the test comes before the
  fix: add a Stata cscript (no .cscript mentions hover at all) asserting that
  `hover(price)` puts `price` into the serialized data, and a pytest that
  fails when "hover" is absent from the `keys` vector in `_dash_extract_vars`.
  *Where:* `test/ (new cscript, e.g. test_hover.cscript, following
  test/test_e2e_single.cscript's shape) and a pytest beside
  test/test_axis_options.py; target symbol dash_parse.mata:537
  `_dash_extract_vars` keys ` [WP-29 P0.10, commit 735c534: closed]
- **[func · standalone · M]** The secondary-axis range still ignores every
  CDSView-based restriction, so the very defect 09-07 names survives on first
  render in three shapes: (a) a LINKED dashboard's graph-level `if` qualifier,
  (b) a linked `by()` facet, (c) a per-plot `if` qualifier on the yaxis(2)
  layer. `_make_figure_body` computes the range from `_source_frame(source,
  self.df)`; when the graph is linked or faceted the source IS the full shared
  CDS and the restriction lives in a CDSView/BooleanFilter that
  `_source_frame` never sees. Fix: intersect `facet_view`/`_plot_view` (and
  any registered view filter) with the frame before calling
  `_compute_secondary_range`, for both the y2 and x2 blocks.     *Where:*
  `dash_render.py: `_compute_secondary_range(_source_frame(source, self.df),
  plots, "yaxis", "yvar", 2)` in `DashRenderer._make_figure_body` (y2 block
  ~:9679, x2 block ~:9714); `_source_frame` (:2411); t`
- **[func · standalone · M]** This task's own mlabel fix silently disconnected
  line-plot labels from the interactive filter. `map_line` builds a private
  `sorted_source` that is never added to `self.sources`, so it is not in the
  callback's `all_graph_sources`; binding the LabelSet to it means marker
  labels on a line plot no longer move when a filter widget moves (before the
  fix they were on the registered graph source and did move). The line glyph
  itself has the same defect — a `line` layer does not respond to filters at
  all in the standalone renderer, while the server registers its per-plot
  source (`graph_sources[gname].append(csrc)`) and does update it. Fix:
  register the sorted source (and its row identities, so `view_filters` can be
  rebuilt) or rebuild it inside `_FILTER_JS`.     *Where:* `dash_render.py:
  `GlyphMapper.map_line` (:3494) — `sorted_source = ColumnDataSource(df)`
  (:3527) and `self._apply_mlabel_opts(fig, sorted_source, ...)` (:3556); the
  registry the callback uses is `self.`
- **[func · standalone · M]** `hover()` does not merely fail to add a variable
  on a line plot — it DELETES every tooltip on the figure. `_make_figure_body`
  drops the existing HoverTools whenever extra hover vars are requested, then
  rebuilds one only for renderers whose own CDS carries every hover column;
  map_line's sorted source carries only x, y and the mlabel column, so the
  line renderer is excluded, and the fallback branch only knows histogram
  (`top`/`left`) and fit (`x`/`y`) sources. A line-only graph therefore ends
  up with zero hover tools. Fix alongside the serialization work the auditor
  already listed, otherwise `hover()` makes line plots strictly worse than not
  using it.     *Where:* `dash_render.py: `DashRenderer._make_figure_body`
  hover block :10197-10290 — `fig.tools = [t for t in fig.tools if not
  isinstance(t, HoverTool)]` (:10202), the `_data_renderers` all-columns test
  (:1025`
- **[func · standalone · S]** The canvas-escaping fix was applied to the
  figure title and the two axis titles only; DashRenderer still html.escape()s
  five more pieces of canvas text. Every one is a Bokeh glyph, not HTML: (1)
  `by()` panel titles via `_facet_label`; (2) the categorical colorvar Legend
  title; (3) the continuous colorvar ColorBar title; (4) `legend(label(N
  "..."))` overrides; (5) the secondary-axis explicit tick labels. A sixth
  site is inconsistent rather than visibly wrong: the primary axis sets an
  ESCAPED CustomJSTickFormatter map and an UNESCAPED `major_label_overrides`
  for the same ticks — BokehJS's `compute_labels` lets the override win, so
  the escaped copy is dead code that will bite whoever removes the overrides.
  *Where:* `dash_render.py:8917 (`_facet_label`, consumed at :11463
  `fig.title.text = f"{orig_title} — {label}"`); :3240 (`Legend(...,
  title=html.escape(var_display))`); :3269 (`ColorBar(...,
  title=html.escape(va`
- **[func · server · S]** ServerAppBuilder's canvas escaping is broader than
  the five lines the auditor enumerated — a developer who fixes only the
  figure title, the two axis labels, the subtitle Label and `_fac_title` will
  leave three more mangled sites: the facet VALUE label (the part that
  actually carries user text), the LegendItem labels built from the emitted
  legend rebuild, and the emitted `legend(label(N "..."))` override.
  *Where:* `dash_render.py, inside `ServerAppBuilder._generate_app_source`
  (:12740): :15096 `_fac_parts.append(html.escape(_vl.get(...)))`; :14951
  `LegendItem(label={'value': html.escape(_lbl)}, ...)`; :14987 `_l`
- **[func · both · S]** Filter dropdown option labels are double-escaped in
  BOTH renderers, so a value label containing `&`, `<` or an apostrophe reads
  as `R&amp;D cars` in the filter widget. Bokeh builds widget DOM with
  `createTextNode`, which is exactly the reasoning the file already records
  for the widget TITLE at :7662 — the same reasoning was never applied to the
  option labels two lines above it.     *Where:* `dash_render.py:
  `FilterBuilder._safe` (:7566-7568) applied to option labels at :7660
  (`options.append((rv, FilterBuilder._safe(_resolve_label(rv))))`); the
  in-file precedent explaining why this is wro`
- **[func · server · M]** The server's faceted dispatch is a cut-down copy of
  the plot loop: it drops `mlabel()` entirely and does not sort a line by x.
  `dash (line y x, mlabel(v)) , by(g)` served live shows no labels and a
  zig-zag line, while the same command in `dash build` shows labels and a
  sorted line. Both the per-group branch and the `by(, total)` branch need the
  real mapper call (or the mlabel + sort logic ported into them).     *Where:*
  `dash_render.py, emitted source inside
  `ServerAppBuilder._generate_app_source`: the per-facet dispatch
  (`_fac_fig.line(xvar_f, yvar_f, source=_fac_src, ...)`) and the `by(,
  total)` dispatch — in the ge`
- **[deli · both · S]** Test-suite gap for the canvas-text clause: the only
  fidelity tests are `test_canvas_text_is_not_html_escaped`,
  `test_axis_titles_are_not_html_escaped` and
  `test_an_apostrophe_survives_on_the_canvas`, all of which read
  `fig.title.text` / `fig.xaxis[0].axis_label` of a single unfaceted figure.
  Nothing asserts fidelity for a `by()` panel title, a colorvar
  legend/colorbar title, a `legend(label())` override, primary or secondary
  explicit tick labels, a filter widget's option labels, or ANY canvas string
  produced by ServerAppBuilder. Add a parametrised test over those model
  properties, plus a mode-parity case (`test/test_mode_parity.py`) asserting
  standalone and server agree on the same `&`-bearing strings.     *Where:*
  `test/test_axis_options.py::TestTitleTextFidelity (:420-459) — the natural
  home; test/test_mode_parity.py for the standalone-vs-server parity case.`
- **[deli · standalone · S]** Test-suite gap for the secondary-range clause:
  `test_the_secondary_range_follows_the_graph_qualifier` asserts only `rng.end
  < full_max` on an UNLINKED graph, so it cannot fail for the linked, faceted
  or per-plot-qualifier cases, and would pass on a range computed from any
  arbitrary subset. Replace the inequality with the exact expected bounds (`lo
  - 0.05*span`, `hi + 0.05*span`) and add three cases:
  `build_options["link"]="g1"`, `graph_options["by"]` with link, and a
  per-plot `if_expr` on the yaxis(2) layer.     *Where:*
  `test/test_axis_options.py::TestSecondaryAxisRange::test_the_secondary_range_follows_the_graph_qualifier
  (:851-885).`

### 11-04 — Consume the remaining discarded keys and fix the dead CSS (17 further items)

- **[func · server · S]** The emitted `_dash_style_legend` aborts halfway on
  every shipped scheme: it assigns the scheme's clock-position INT straight to
  `Legend.location`, Bokeh raises ValueError, and the bare `except` swallows
  it — so `lg.ncols` on the next line never executes. This sharpens the
  auditor's "legend_position/legend_cols have zero consumers": a consumer
  exists, it is reached, and it is silently self-destructing. Fix = map the
  clock int through a side/anchor table (the standalone
  `_CLOCK_SIDE`/`_CLOCK_INSIDE` maps at dash_render.py:9044-9056) before
  assigning, and split the try so one bad assignment cannot kill the rest. Any
  future scheme chrome appended to this block is equally unreachable.
  *Where:* `dash_render.py:12653-12667 (the `_dash_style_legend` string block
  inside ServerAppBuilder; location assignment at :12662, ncols at :12664,
  swallowing `except (AttributeError, KeyError, TypeError, Valu`
- **[func · both · S]** legend_position and legend_cols are NOT unconsumed —
  the generated server app reads both and the read is broken. Fix the server's
  `_dash_style_legend`: map the scheme's integer clock position through the
  same `_CLOCK_SIDE`/`_CLOCK_INSIDE` tables `_rebuild_legend` uses
  (dash_render.py:9044-9056) instead of assigning the raw int to
  `lg.location`, and put the `ncols` assignment in its own try so a bad
  location no longer discards it. Then give the standalone `_rebuild_legend`
  the same scheme defaults, which it has never read at all.     *Where:*
  `dash_render.py:12622-12623 and 12661-12665 (ServerAppBuilder, emitted
  `_dash_style_legend`); dash_render.py:9062-9068
  (DashRenderer._rebuild_legend chrome loop — add the two keys here); clock
  tables t`
- **[func · both · S]** Standalone/server parity split introduced by the
  legend-chrome clause the auditor marked DONE: the two renderers size the
  legend label from DIFFERENT scheme keys. `_rebuild_legend` uses
  `scheme.text_font_size`; the emitted `_dash_style_legend` uses
  `_c['tick_label_font_size']`. Pick one (Stata's key_label gsize is the
  honest source) and make both renderers use it.     *Where:*
  `dash_render.py:9068 (DashRenderer._rebuild_legend); dash_render.py:12660
  (ServerAppBuilder, emitted _dash_style_legend)`
- **[func · both · S]** The `.db-kpi-card` rule css_block() emits is
  overridden by the KPI div's inline style, so the selector test passes while
  the scheme value still does nothing. Either drop the inline
  `background:`/`border:` shorthands from the KPI markup (keeping the per-KPI
  bgcolor() override as a narrower inline property or a CSS custom property),
  or have css_block() stop pretending to style the card. The auditor named
  this in the report headline but it is absent from the itemised backlog, so
  it is not in REMAINING.md.     *Where:* `dash_render.py:2218-2219 (css_block
  .db-kpi-card rule), dash_render.py:10487-10496 (KPI Div markup),
  dash_render.py:7328-7334 (JS rebuild), dash_render.py:12976 (server copy)`
- **[func · server · M]** css_block() is never called in `dash serve`: the
  generated app carries a verbatim copy of SchemeParser (css_block included)
  but no call site, and emits no `.db-title`/`.db-subtitle` markup, so the
  served dashboard chrome ignores the scheme entirely. Wire the scheme CSS
  into the server app's template (Bokeh `curdoc().template` / the Div that
  builds the header) the way DashRenderer does at 10899-10900 and 12136-12140.
  Headline-only in the auditor's report; not in REMAINING.md.     *Where:*
  `dash_render.py:12265+ (ServerAppBuilder — no css_block call), compare
  dash_render.py:10892-10902 and 12132-12141`
- **[deli · server · M]** No test anywhere exercises the server half of 11-04.
  The alphas, minor_grid_color and legend chrome were landed in the emitted
  app with zero coverage, which is exactly how the 11pt/10pt legend split
  above survived. Add server-mode assertions (build an app with
  ServerAppBuilder, exec it, assert `_SCHEME_FILL_ALPHA`/`_SCHEME_CHROME`
  values and call `_dash_style_legend` on a real Legend) alongside the
  standalone ones in test/test_scheme_consumption.py.     *Where:*
  `test/test_scheme_consumption.py (classes TestNoParsedKeyIsDiscarded at
  :427, TestSchemeCssActuallyApplies at :242)`
- **[deli · docs · S]** Correction to remaining item 7 as written: the
  enumerated replacement for `test_the_key_is_read_somewhere` must NOT keep
  the current `code.count(f".{attr}") >= 2` heuristic. Enumerating
  _init_properties while keeping that heuristic produces four false failures
  (graphsize_x, graphsize_y, legend_position, legend_cols are all read, via
  `getattr(self.scheme, "name")` and via `_SCHEME_CHROME[...]` dict keys). The
  mechanical check the `<done>` asks for has to count string-literal reads too
  — or, better, assert behaviour (render/emit and read the value back off the
  model).     *Where:* `test/test_scheme_consumption.py:463-478`
- **[func · standalone · M]** The bs/Bootstrap layout emits a MALFORMED head
  whenever the dashboard contains any widget, and the entire <style> block
  carrying _DASH_GRID_CSS + the scheme's css_block() (plus the CSP and
  viewport metas) is swallowed as script text and never applied. Root cause:
  the head is lifted from bokeh's file_html() with a non-greedy regex, and
  bokeh-widgets.min.js contains a literal '</head>' inside a JS string, so the
  match cuts the head in the middle of that inline <script>. Fix the
  extraction (match to the LAST </head>, or use bokeh's own template/json_item
  instead of string surgery) and assert <script>/</script> balance in the
  emitted document. This is the task's central deliverable — 'align them so
  the block applies' — still not true in a browser, and the .db-kpi-card rule
  the task added can ONLY appear in a document that has a KPI card, i.e.
  exactly the document where the whole block is destroyed.     *Where:*
  `dash_render.py:10784-10786 (`_dummy_html = file_html(...)`, `_head_m =
  re.search(...)`, `_extracted_head`) in DashRenderer._assemble_layout;
  consumed at dash_render.py:10896-10900 (`f"{_extracted_head`
- **[func · standalone · M]** In the auto layout the .db-title / .db-subtitle
  / .db-kpi-card markup is emitted INSIDE Bokeh Div models, which Bokeh 3
  renders in a shadow root, so the document-level scheme rules cannot match
  them. The class-name fix the task landed therefore still has no effect on
  the auto-layout header or on KPI cards in EITHER layout — only `body {
  background-color }` (light DOM) works. Fix by attaching the scheme CSS to
  those Divs (`stylesheets=[InlineStyleSheet(css=self.scheme.css_block())]`)
  or by folding the scheme values into the inline style the Div already
  carries.     *Where:* `dash_render.py:12105-12122 (the two `Div(text='<h2
  class="db-title" ...>')` / `Div(text='<p class="db-subtitle" ...>')` header
  items in DashRenderer._assemble_layout's auto branch); dash_render.py:104`
- **[deli · standalone · M]** The mechanical CSS guard the task installed
  cannot see either failure above, because it only compares selector strings
  against class strings in the HTML source. Give it a rendered-DOM arm (or at
  minimum: assert the emitted document has balanced <script>/</script>, assert
  the <style> element containing the scheme block survives the head splice for
  a spec that has a KPI and a filter, and assert the header/KPI Divs carry a
  stylesheets= entry). Without this the task's own stated purpose — 'that test
  is what stops this recurring' — is unmet.     *Where:*
  `test/test_scheme_consumption.py:242-296 (TestSchemeCssActuallyApplies,
  `_render` helper at :60-90)`
- **[func · standalone · S]** The continuous colorvar() ColorBar takes no
  scheme chrome at all. Only its palette was considered; its background,
  border, tick-label size/colour and title size/colour are Bokeh defaults, so
  an economist or s2color dashboard draws a white colour bar with #444444 13px
  text over a themed plot region. Stata styles this through
  clegendstyle-default.style / textboxstyle-clegend. Set background_fill_color
  from plotregion_color (or background_color), major_label_text_font_size from
  tick_label_font_size, and title_text_font_size/title_text_color from
  text_font_size/title_color, in the same place the ColorBar is built.
  *Where:* `dash_render.py:3266-3272 (`GlyphMapper._apply_colorvar`,
  `fig.add_layout(ColorBar(color_mapper=mapper, label_standoff=8, width=12,
  location=(0,0), title=html.escape(var_display)), "right")`)`
- **[func · server · S]** In server mode a by()-faceted figure's legend never
  receives the scheme chrome: `_dash_style_legend` is called only from the
  main (unfaceted) plot loop, while the facet loop builds its figure and its
  auto-legend and moves on. So one dashboard serves faceted panels with
  Bokeh-default legends and unfaceted panels with the scheme's — the clause
  'style the legend from the scheme unconditionally' is unmet on the faceted
  path.     *Where:* `dash_render.py:14955-14961 (the emitted
  `fig.add_layout(_lg)` / `_dash_style_legend(_lg)` pair in ServerAppBuilder's
  main plot loop) and dash_render.py:15131-15214 (the emitted facet loop:
  `_fac_fig =`
- **[func · both · S]** `gsize note` is a DEAD key at Stata scheme level —
  exactly the trap this file already documented for `draw_major_grid`. No
  style file reads `scheme note`; the note textbox is textboxstyle-body, which
  reads `gsize body` / `color body`. Wiring SchemeParser.note_font_size (from
  `gsize note`) to the note Label, as the remaining item prescribes, would
  draw economist's note at 14pt where Stata draws ~8.6pt. Parse `gsize body`
  (and `color body`) instead, and add those keys back to the 14 translated
  .scheme files, which dropped them on purpose.     *Where:*
  `dash_render.py:2047 (`self.note_font_size = self._gsize("gsize note",
  "9pt")`); schemes/*.scheme (all 14 carry `gsize note`, none carries `gsize
  body`); dash_render.py:9867 and :13932 (the `_TEXTBOX_D`
- **[func · both · S]** The graph-level subtitle clause cannot be closed
  inside dash_render.py at all: Stata's subtitle is textboxstyle-subheading,
  which reads `gsize subheading` and `color subheading`, and SchemeParser
  parses NEITHER — and the 14 translated .scheme files deliberately dropped
  both. So the remaining item 'give the subtitle a real scheme value' needs
  S03-shaped work first (add the keys to schemes/*.scheme, add
  `subheading_font_size` / `subheading_color` to _init_properties) before any
  renderer edit can be correct rather than invented.     *Where:*
  `dash_render.py:2040-2048 (SchemeParser._init_properties font-size block —
  no subheading attribute); schemes/*.scheme (all 14);
  dash_render.py:9893-9896 and :13952-13953 (the subtitle Label in each ren`
- **[func · both · S]** The section's TDD stub names CAPTION explicitly
  ('title, subtitle, axis-title, tick-label, note and caption sizes come from
  the scheme') and the caption is untouched: both renderers draw it at a
  hardcoded 12.0px / #555555 with no scheme key parsed. Like the note, its
  Stata source is `gsize body` / `color body` via textboxstyle-body.
  *Where:* `dash_render.py:9866-9869 (`_TEXTBOX_DEFAULTS` in
  DashRenderer._make_figure_body) and dash_render.py:13931-13934 (the emitted
  copy in ServerAppBuilder)`
- **[func · server · L]** colorvar() has no implementation whatsoever in
  ServerAppBuilder, so the task's whole 'colour mapping' clause — discrete
  palette from scheme.p_colors, continuous ramp, colour-key placement — is
  unmet in `dash serve`, and a served dashboard silently drops the option
  entirely (no mapper, no colour key, no colour bar). dash.ado parses and
  serializes it (dash.ado:564-565, :673, :865), so the key is written and
  never read on this path.     *Where:* `dash_render.py:12265 (class
  ServerAppBuilder) / :12740 (_generate_app_source) — no colorvar branch;
  compare `GlyphMapper._apply_colorvar` at dash_render.py:2995-3300`
- **[deli · both · S]** The section's TDD stub for text sizes is only
  one-third delivered and only on one renderer: axis-title and tick-label
  sizes are asserted once, against DashRenderer, and nothing asserts them
  against the server's emitted `_dash_apply_scheme`; nothing at all asserts
  title, subtitle, note or caption sizes. Add a rendered-model test per
  renderer covering all six names, so the clause has a guard rather than a
  source-count proxy.     *Where:* `test/test_scheme_consumption.py
  (TestNoParsedKeyIsDiscarded, :427-481 — natural home),
  test/test_server_scheme.py (needs an axis/tick font-size arm),
  test/test_scheme.py:290-300`

### 15-03 — Collapse the glyph dispatch tables to one (18 further items)

- **[func · server · S]** Under by() / by(total), `lpolyci` and `fpfitci` draw
  only the central line — the confidence band is dropped entirely. The emitted
  facet chains alias them to the plain fits: dash_render.py:15179 `elif ptype
  in ('lpoly', 'lpolyci'):` calls only `_compute_lpoly` +
  `_fac_fig.line('x_lp','y_lp',...)`, and dash_render.py:15186 `elif ptype in
  ('fpfit', 'fpfitci'):` calls only `_compute_fpfit` + one
  `.line('x_fp','y_fp',...)`. The by(total) twins at dash_render.py:15280 and
  15287 do the same. This is NOT covered by the auditor's blank-under-by()
  item (lpolyci is not on that list — it draws, just half of it) nor by the
  main-loop fpfitci item.     *Where:* `dash_render.py:15179 and 15186
  (per-group facet chain), dash_render.py:15280 and 15287 (by(total) twin);
  targets are GlyphMapper.map_lpolyci / map_fpfitci`
- **[func · server · S]** Faceted glyph divergences beyond marker size/alpha:
  (a) a faceted `histogram` bar is drawn with Bokeh's unstyled default outline
  `#1f77b4` at fill_alpha 0.6, where standalone draws a white outline at
  fill_alpha 1.0 — the emitted `_fac_fig.quad(top='top', bottom=0,
  left='left', right='right', source=_hsrc, fill_color=color, fill_alpha=0.6,
  legend_label=_hvar)` passes no line_color at all; (b) a faceted `dropline`
  stem is drawn at `line_width=1.0` where standalone uses the scheme's 1.2. So
  8 of the 18 plot types the facet chain does handle diverge, not just the
  marker ones.     *Where:* `dash_render.py:15156 (emitted facet `quad`),
  dash_render.py:15199 (emitted facet dropline `segment`), and the by(total)
  twins at dash_render.py:15257 and 15300`
- **[func · server · M]** Faceted server figures drop EVERY graph option
  except the title. `_fac_kw` (dash_render.py:15121-15131) builds the facet
  figure from title + var_labels + tools + sizing_mode only, so
  `xtitle()`/`ytitle()`, `xscale(log)`/`yscale(log)`, `note()`, `caption()`,
  `subtitle()`, `xline()`/`yline()`, `legend(off)`, `aspectratio()`,
  `bgcolor()` and `xlabel()`/`ylabel()` are all silently ignored under `by()`.
  The non-faceted server loop honours all of them (dash_render.py:13832-13836
  for xtitle/ytitle, 13977-13980 for the log scales, 13920+ for
  note/caption/subtitle), so this is facet-only. The by(total) twin at
  dash_render.py:15228 is worse still — it passes no axis labels at all.
  *Where:* `dash_render.py:15115-15133 (`_fac_kw`/`_fac_fig`),
  dash_render.py:15228-15235 (by(total) twin); the correct construction to
  reuse is the main loop at dash_render.py:13826-13990`
- **[func · server · M]** `mlabel()` diverges for every plot type except
  scatter in server mode. The emitted app carries a SECOND marker-label
  builder at dash_render.py:14894-14930 with its own font-size map
  (`_mls_map2`, large=14px), its own offset map (`_mlabpos_map2`, position 9 =
  x_offset -10) and its own defaults (9px / #333333 / (5,5)), while
  `GlyphMapper._apply_mlabel_opts` (dash_render.py:3301) — which IS copied
  into the app and is what the delegated scatter branch uses — says 10px /
  #444444 / (4,0), large=15px, position 9 = x_offset -4. Worse, the block is
  gated on `_mlab_var in _cur_src.data` (dash_render.py:14904), which is false
  for `bar` and `spike`, so those draw no labels at all. `mlabgap()` is not
  read by the second copy either. This is precisely the duplicated size/offset
  table TR-15.3 asked to collapse and that `test_mode_parity._annotations`'
  own docstring warns about — closed for scatter only.     *Where:*
  `dash_render.py:14894-14930 (the emitted second builder); target
  dash_render.py:3301 `GlyphMapper._apply_mlabel_opts`; corpus gap at
  test/test_mode_parity.py:244,271`
- **[func · server · S]** Faceted `lpolyci` and `fpfitci` lose their
  confidence band in server mode. The facet chains collapse them into their
  band-less siblings: `elif ptype in ('lpoly','lpolyci')`
  (dash_render.py:15179, twin at 15280) draws only the lpoly line from
  `_compute_lpoly`, and `elif ptype in ('fpfit','fpfitci')`
  (dash_render.py:15186, twin at 15287) only the fpfit line. Neither is in the
  auditor's '20 types draw NOTHING under by()' list, because they draw a line
  — just the wrong one. The grids differ too.     *Where:*
  `dash_render.py:15179-15192 and dash_render.py:15280-15293; targets are
  GlyphMapper.map_lpolyci / map_fpfitci`
- **[func · server · S]** Faceted `kdensity` and `lowess` ignore their options
  entirely. The facet branches call the compute helpers with the options
  argument omitted — `_compute_kdensity(_fac_gdf, _kdvar)`
  (dash_render.py:15170, twin 15271) and `_compute_lowess(_fac_gdf, yvar_f,
  xvar_f)` (dash_render.py:15175, twin 15276) — although both helpers take
  `options=None` (dash_render.py:13354, 13396) and the non-faceted branches
  pass `opts`. So `bwidth()`, `kernel()`, `n()` and `range()` are dropped the
  moment `by()` is used.     *Where:* `dash_render.py:15170, 15175, 15271,
  15276`
- **[func · server · S]** Faceted aggregate layers lose their plot options
  after the FIRST filter interaction. The facet agg registrations
  (dash_render.py:15156, 15161, 15166, 15172, 15177, 15184, 15189 and the
  by(total) twins at 15257-15290) omit the `'opts'` key, while
  `_on_filter_change` recomputes with `agg.get('opts') or {}`
  (dash_render.py:15609-15630). So a faceted `histogram ..., bin(4)` renders 4
  bars and then silently re-bins to the data-driven default as soon as any
  widget moves; the same applies to faceted lfit `n()`, qfit, and lpoly
  `bwidth()`/`degree()`. The `'bins': 20`, `'bwidth'` and `'degree'` keys
  those registrations DO write are dead reads — nothing in the callback chain
  consults them.     *Where:*
  `dash_render.py:15156/15161/15166/15172/15177/15184/15189 and
  15257/15262/15267/15273/15278/15285/15290; consumer at
  dash_render.py:15609-15630`
- **[func · server · S]** Server-mode `fpfit`/`fpfitci` still evaluate on the
  200-point 1st-99th-percentile linspace that `_fp_grid` was written to
  remove. `_fp_grid`'s own docstring (dash_render.py:6441-6460) states Stata
  uses the distinct observed x values and that 'dash used a 200-point linspace
  for fpfit and a 150-point one for fpfitci, both truncated to the 1st-99th
  percentile ... so the band and the line it belonged to did not lie on top of
  each other, and both ends of the fit were cut off'. `_fp_grid` IS copied
  into the app (dash_render.py:12395) but nothing calls it: the emitted
  `_compute_fpfit` at dash_render.py:13492 still does
  `np.linspace(float(np.percentile(x, 1)), float(np.percentile(x, 99)), 200)`
  at dash_render.py:13502. The served fit is therefore truncated at both ends
  and cannot overlay the observations.     *Where:*
  `dash_render.py:13492-13510 (emitted `_compute_fpfit`), dash_render.py:6441
  `_fp_grid`, dash_render.py:4554/4612 (the standalone call sites)`
- **[func · server · S]** `kdensity` evaluates on a different grid in each
  mode: 300 points standalone, 200 served. `GlyphMapper.map_kdensity` defaults
  `n` to 300.0 (dash_render.py:4806+, `n_pts = _stat_option_float(options,
  "n", 300.0, ...)`); the emitted `_compute_kdensity` hardcodes `n_pts = 200`
  (dash_render.py:13380). kdensity IS in the parity corpus and the guard is
  green, because the guard never compares data (see the parity-corpus item
  below).     *Where:* `dash_render.py:13380 (emitted default) vs
  dash_render.py:~4863 in `GlyphMapper.map_kdensity``
- **[func · server · S]** A KPI declared `update(brush)` never fires on a
  faceted panel in server mode. The brush wiring skips any source without an
  `index` column (dash_render.py:15727-15729, `if 'index' not in
  getattr(_bsrc, 'data', {}): continue`), and the unlinked facet source is
  built as `ColumnDataSource({v: _fac_gdf[v].tolist() for v in _fac_gvars})`
  (dash_render.py:15111-15113) and the by(total) source as `{v:
  work_df[v].tolist() for v in _tot_gvars}` (dash_render.py:15221-15223) —
  neither adds `index`. Brushing any panel of a by() dashboard therefore
  leaves the KPI frozen, with no warning.     *Where:*
  `dash_render.py:15111-15113, 15221-15223 (facet sources);
  dash_render.py:15720-15733 (brush wiring)`
- **[func · server · S]** The facet loops contain a FOURTH inline median-band
  implementation that also never refreshes. `elif ptype == 'mband'` at
  dash_render.py:15205-15213 (twin at 15306-15314) recomputes bin edges and
  medians inline instead of calling the shared `_compute_mband` the main loop
  uses (dash_render.py:13524), and draws from an anonymous
  `ColumnDataSource({'x_mb': _xm, 'y_mb': _ym})` that is registered in neither
  `graph_sources` nor `agg_sources` — so a faceted mband is frozen at its
  first-render values for the life of the session. TR-15.3 asked for one
  binner; this is the copy that was left.     *Where:*
  `dash_render.py:15205-15213 and 15306-15314; shared helper at
  dash_render.py:13524 `_compute_mband``
- **[deli · both · M]** The parity guard compares no DATA. `_glyph_profile`
  (test/test_mode_parity.py:129) reads only
  type/marker/size/fill_color/line_color/line_width/line_dash/fill_alpha;
  `_annotations` and `_chrome` add labels and background/grid colours.
  `data_source.data` is touched in exactly two places, both histogram bar
  counts (test/test_mode_parity.py:365, 382). The section's TDD stub says
  'equivalent glyph types, DATA and visual properties' and 15-01's action says
  'compare ... glyph types, DATA VALUES, and the visual properties'.
  Consequence measured: kdensity (300 vs 200 points) and fpfit/fpfitci (10 vs
  200) diverge inside the existing corpus and the file still reports 165
  passed. Separately, `ALLOWED` (test/test_mode_parity.py:55) gates no
  comparison — its only assertions are that it is non-empty and that each
  reason is over 40 characters (test/test_mode_parity.py:388-392), so the
  'explicit allowance' design is decorative. `_chrome` also omits figure
  title, axis labels, axis scale type and legend visibility, which is why the
  facet graph-option losses above would survive even after the corpus gains
  by() cases.     *Where:* `test/test_mode_parity.py:129 `_glyph_profile`,
  :163 `_chrome`, :55 `ALLOWED`, :388-392`
- **[deli · server · S]** The copied-callee guard does not cover the classes
  15-03 copied.
  `TestTheCopiedHelpersBringTheirCallees.test_every_global_a_copied_helper_calls_is_defined`
  (test/test_mode_parity.py:436) filters `vars(mod)` with `isinstance(_obj,
  types.FunctionType)`, which matches module-level functions only — the 97
  methods of the copied `OptionTranslator`, `SchemeParser` and `GlyphMapper`
  are class attributes and are never scanned. Its companion
  `test_the_scan_found_the_copied_helpers` (:464) greps `_shared_stat_lines`
  for four names and never mentions `_glyph_layer_lines`. This is the exact
  failure mode the test exists for (`_stata_if_to_pandas` gaining
  `_mask_string_literals`, per its own docstring), now applying to a
  5,000-line copied block that it does not look at.     *Where:*
  `test/test_mode_parity.py:436-462 and :464-470; the unscanned block is
  emitted by dash_render.py:12406-12410 (`for _cls in (OptionTranslator,
  SchemeParser, GlyphMapper)`)`
- **[deli · server · S]** The task's explicit clause 'test the
  packaged-install case against S02's cscript' is unmet, and the substitution
  introduced a new hard dependency with no guard. test/test_packaging.py
  exercises `DashRenderer` (:208) and `GlyphMapper` (:238) from a staged
  install but never `ServerAppBuilder`, and there is no
  test_netinstall.cscript in test/ at all. `_glyph_layer_lines` now calls
  `inspect.getsource` on three classes and 15 helpers
  (dash_render.py:12386-12410) with no try/except, so any deployment where
  dash_render.py's source text is not on disk — byte-compiled-only install,
  zipimport, a stripped copy — fails the BUILD with a bare traceback rather
  than a dash-level message.     *Where:* `test/test_packaging.py (add a
  staged-install ServerAppBuilder.build + exec case alongside :208/:238);
  dash_render.py:12386-12410 (`inspect.getsource` calls, no fallback)`
- **[func · server · L]** Collapse the FIFTH dispatch table the auditor never
  counted: the live-recompute `atype` chain in the emitted app (14 branches)
  plus the 15 hand-written `_compute_*` functions it dispatches to, which are
  a second statistical implementation of GlyphMapper's math emitted as string
  literals rather than copied with `inspect.getsource`. The task's <done> is
  'a plot type is implemented once'; with this chain the count of hand-written
  server dispatch chains is 4 (36 + 16 + 16 + 14 = 82 branches), not 3. The
  chain also covers only 14 of 38 plot types, so every other type is frozen at
  its initial values when a filter widget moves.     *Where:* `dash_render.py:
  emitted chain at 15604-15640; emitted _compute_* string literals at
  13192-13700; the collapse targets are GlyphMapper.map_* (3407-6065) and its
  grid helpers (_histogram_grid, _fit_grid` [WP-29 P0.18, commit 2d52fbe: partly closed; open: the emitted atype chain and its hand-written _compute_* functions remain a second implementation covering 14 of 38 plot types; only the bar/rbar redraw widths and an emptied layer's style were fixed]
- **[func · server · S]** Server facet titles drop Stata VALUE LABELS, not
  merely %fmt/%t* formats. The auditor's facet-label item says the emitted
  builder 'consults value labels only', which implies value labels work; they
  do not, on the commonest case of all (`by(foreign)` on auto.dta). Root cause
  is a key-space mismatch the emitted copy inherited without the standalone's
  fallback: the emitted code does `_lset = val_label_names.get(_bv)` then `_vl
  = val_labels.get(_lset)`, but jsonio keys `valueLabels` by VARIABLE name, so
  the lookup is `val_labels['origin']` against a dict keyed `{'foreign':
  {...}}` and misses. `DashRenderer._facet_label` has the fallback (`candidate
  = self.value_labels.get(var, {})`) and the emitted copy does not.
  *Where:* `dash_render.py:15092-15093 (emitted `_lset`/`_vl` lookup) vs
  dash_render.py:8905-8913 (DashRenderer._facet_label's by-variable-name
  fallback)`
- **[func · server · S]** Four CI plot types lose their confidence band under
  `by()`, which neither of the auditor's two facet items covers: their '20
  types draw NOTHING' list omits fpfitci and lpolyci (those draw a partial
  figure, band missing), and their main-loop divergence item is explicitly
  about the main loop. lfitci/qfitci draw nothing at all under by() (they ARE
  in the 20), but fpfitci and lpolyci silently drop the VArea while still
  drawing the Line, so the panel looks plausible and is wrong.     *Where:*
  `dash_render.py: emitted by() facet chain at 15137-15230 and by(total) twin
  at 15237-15330 — the fpfitci and lpolyci facet branches draw only the line;
  fix by routing both chains through GlyphMapper.ma`
- **[deli · dash.ado · M]** No .cscript exercises `by()` in server mode, so
  the whole blank-panel class of defect is unguarded at the Stata level. The
  auditor's corpus item correctly says test_mode_parity.py has zero by()
  entries, but stops at pytest; the same hole exists in the certification
  suite, which is the layer that would have caught `dash ... by(foreign)` +
  `dash build, server` producing an rc-0 blank dashboard.     *Where:*
  `test/test_server_build.cscript (or a new test/test_server_by.cscript); pair
  it with the by()/by(total) entries the auditor asks for in
  test/test_mode_parity.py:CORPUS`