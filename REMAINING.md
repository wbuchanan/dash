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
  that is a no-op it should say so, not imply the plot is wrong.
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
| 06 | Varlist / plot-spec | 7 | 2 done, 5 partial ② | `horizontal` `sort` `vertical` ①; positional plot-options across an expanded varlist; **no S06 entry in CHANGELOG** ② |
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
