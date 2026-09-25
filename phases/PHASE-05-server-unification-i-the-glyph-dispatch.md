# Phase 05 — Server unification I — the glyph dispatch

**Purpose.** `dash` has two renderers. `DashRenderer` writes a standalone HTML file and
draws every plot type through one shared `GlyphMapper`. `ServerAppBuilder` emits the
source of a `bokeh serve` app, and that emitted app carries its *own* hand-written
drawing code for 38 of the 39 plot types dash advertises — plus a second, string-literal
implementation of the statistical math, plus a fifth dispatch table that recomputes
layers when a filter widget moves. The result is measurable divergence: layers that draw
nothing, a confidence band that disappears, fits evaluated on a truncated grid, markers
and line widths that ignore the scheme. This phase collapses the **main loop** and the
**live-recompute chain** onto the shared mapper, which is the lever the whole audit turns
on: once a plot type delegates, it inherits every standalone fix instead of needing its
own copy. The `by()` / `by(total)` facet chains are the sibling work in Phase 06, and the
parity-guard deliverables that lock the collapse in are Phase 08.

---

## At a glance

| | |
|---|---|
| **Work items** | 5 (numbered 1–5 below) |
| **Functional / deliverable** | 5 functional / 0 deliverable |
| **Effort mix** | 2 large (items 1, 5) · 1 medium (item 3) · 2 small (items 2, 4) |
| **Renderers touched** | `server` — all 5 items land in the emitted `bokeh serve` app; every *target* is shared code (`GlyphMapper.map_*`, `_fp_grid`) already copied into that app |
| **Ultraplan tasks discharged** | **15-03** — "Collapse the four glyph dispatch tables to one" (the main-loop half and the live-recompute half; the two facet halves are Phase 06) |
| **Section at entry** | S15 — 0 DONE / 4 PARTIAL / 0 NOT DONE. Status line: *"15-03 1/46; 5 live drifts — 45 undelegated branches; corpus covers 17/36 types, no `by()`/KPI/filter/`link()`/`tabs()`"* |
| **Depends on** | — (nothing hard). `REMAINING.md` §Suggested order, step 5: *"S15-03. Mechanical, guarded by the parity corpus; can proceed in parallel with 4 since it touches the emitted app rather than `dash.ado`."* |
| **Unblocks** | Phases **06**, **07**, **08** (the rest of S15); the server halves of **06-06, 08-04, 08-05, 09-02, 09-07** — carried by Phases **10**, **13**, **16**, **27**. Appendix A: *"Every server-side gap in 06-06, 08-04, 08-05, 09-02 and 09-07 above is downstream of this task. Finishing it is what makes those five stop being two problems each."* |

---

## Why this phase exists

Everything in this section is copied from `REMAINING.md`. A developer should not need to
open that file to know what is broken.

### The collapse is 1/46 done

> **The collapse is 1/46 done.** `ServerAppBuilder` holds **51 `ptype ==`
> comparisons** across ~4,000 emitted lines; exactly **one** (`scatter`)
> delegates to `_DASH_MAPPER`. 39 `map_*` methods exist.
>
> — `REMAINING.md` §4

Confirmed against the tree at `187a786`: `_DASH_MAPPER` is constructed at
`dash_render.py:12432` (`_DASH_MAPPER = GlyphMapper(scheme=_DASH_SCHEME)`) and is
referenced by exactly one emitted branch, `dash_render.py:14090`
(`_r = _DASH_MAPPER.map_scatter(`). `GlyphMapper` defines 39 `map_*` methods between
`dash_render.py:3407` (`map_scatter`) and `dash_render.py:6065` (`map_function`).

### What 15-03 already landed, and what it did not

> **What landed:** the emitted app carries `GlyphMapper`, `OptionTranslator` and
> `SchemeParser` copied verbatim, and **the scheme is wired through**. The task's
> stated symptom is gone: `grep "scheme"` over the emitted region returned zero
> hits when the task was written and returns **44** now, and `#1f77b4` — the
> uniform colour the task complained of — occurs **0** times.
>
> **Remaining:**
> 1. **38 of the 39 plot types the emitted app dispatches still carry their own
>    drawing code.** Exactly one delegates: `_DASH_MAPPER.map_scatter` at
>    `dash_render.py:14090`. The 38: `area` `bar` `connected` `dot` `dropline`
>    `fpfit` `fpfitci` `function` `hist` `histogram` `kdensity` `lfit` `lfitci`
>    `line` `lowess` `lpoly` `lpolyci` `mband` `mspline` `pcarrow` `pcbarrow`
>    `pci` `pcscatter` `pcspike` `qfit` `qfitci` `rarea` `rbar` `rcap` `rcapsym`
>    `rconnected` `rline` `rscatter` `rspike` `scatteri` `spike` `tsline`
>    `tsrline`.
>
> — `REMAINING.md` Appendix A, 15-03

The machinery for delegation is therefore already in place. The three classes are copied
into the app verbatim by `inspect.getsource` (`dash_render.py:12406-12410`,
`for _cls in (OptionTranslator, SchemeParser, GlyphMapper):`), the scheme is resolved and
handed to the mapper, and `map_scatter` proves the call shape works. What is missing is
the other 37 call sites.

### Layers that draw nothing, and layers that draw the wrong thing

> **Five of the 19 have already drifted.** Measured at HEAD by building both
> renderers' figures from the same spec and diffing every glyph property. Spec
> shapes were taken from `dash.ado`'s own emission (`yvar1`/`yvar2` for range
> plots, `expr` for `function`, `points` for `pci`) and columns that exist:
>
> | type | standalone | server | consequence |
> |---|---|---|---|
> | **`fpfitci`** | `VArea`(α .2) + `Line` | `Line` only | **the confidence band is missing in server mode** |
> | **`function`** | `Line` | *nothing* | **server-mode `function` draws no layer** |
> | **`pci`** | `Segment` | *nothing* | **server-mode `pci` draws no layer** |
> | `lowess` | `#1f77b4`, width 1 | `#1a476f`, width 1.5 | **standalone `lowess` ignores the scheme** (matplotlib's default blue) |
> | `rscatter` | marker size 8.0 | marker size 6 | two default size tables |
>
> `test_conformance.cscript`'s "every layer drew something" assertion runs in
> **standalone mode only**, which is precisely why the two server-mode layers
> that draw nothing are invisible to it.
>
> These five are new defects, not plan items. Under project rule 8 each needs a
> regression test that fails first.
>
> — `REMAINING.md` §4

> **1. 20 plot types are broken in server mode.** Measured by building the
> emitted app from a spec and counting glyph renderers, with spec shapes taken
> from `dash.ado`'s own emission:
>
> - **Draw nothing at all:** `function`, `pci`, `tsrline`.
> - **Draw nothing under `by()`** (they work without it): `lfitci` `qfitci`
>   `mspline` `tsline` `rarea` `rbar` `rcap` `rline` `rscatter` `rspike`
>   `rconnected` `rcapsym` `pcspike` `pcarrow` `pcbarrow` `pcscatter`
>   `scatteri` — 17 of them.
>
> This is 15-03's unfinished collapse showing through.
>
> — `REMAINING.md` Appendix B, "Three findings worth pulling out first"

The `by()` half of that finding is Phase 07. The "draw nothing at all" half is this
phase: `pci` is work item 2, and `function` and `tsrline` are inside the 37 branches of
work item 1.

### The property-level divergences the delegation must close

> **[func · server · M]** 13 more main-loop plot types diverge on glyph
> properties under a non-default scheme: fpfitci loses its CI band entirely
> (emitted branch is a verbatim copy of fpfit); rarea fill_alpha 1.0 vs 0.5;
> rbar drawn with a white 1.2px outline vs line_alpha 0; rcapsym caps at
> line_width 1.2 vs 1.5; rline/rconnected/tsrline draw the second series in
> colour index 0 with a dash instead of the scheme's colour index 1 (#3e647d
> vs #7b92a8); rscatter/pcscatter markers at size 6 vs scheme 10.18;
> pcspike/pcarrow/pcbarrow at line_width 1.2 vs 1.5; lowess runs a second
> implementation (`_compute_lowess`) where standalone uses statsmodels via
> map_lowess.
>
> — `REMAINING.md` Appendix B, 15-03

### The fit that cannot lie on top of its own data

> **[func · server · S]** Server-mode `fpfit`/`fpfitci` still evaluate on the
> 200-point 1st-99th-percentile linspace that `_fp_grid` was written to
> remove. `_fp_grid`'s own docstring (dash_render.py:6441-6460) states Stata
> uses the distinct observed x values and that 'dash used a 200-point linspace
> for fpfit and a 150-point one for fpfitci, both truncated to the 1st-99th
> percentile ... so the band and the line it belonged to did not lie on top of
> each other, and both ends of the fit were cut off'. `_fp_grid` IS copied
> into the app (dash_render.py:12395) but nothing calls it: the emitted
> `_compute_fpfit` at dash_render.py:13492 still does
> `np.linspace(float(np.percentile(x, 1)), float(np.percentile(x, 99)), 200)`
> at dash_render.py:13502.
>
> — `REMAINING.md` Appendix C, 15-03

Confirmed verbatim in the tree. The emitted literal at `dash_render.py:13502` reads:

```python
"    x_grid = np.linspace(float(np.percentile(x, 1)), float(np.percentile(x, 99)), 200)",
```

while both standalone call sites (`dash_render.py:4554` in `map_fpfit`,
`dash_render.py:4612` in `map_fpfitci`) read `x_grid = _fp_grid(x)`. `_fp_grid` is in the
emitted helper list at `dash_render.py:12386-12410` and its resource cap
`_FP_GRID_MAX = 1000` (`dash_render.py:121`) is in the emitted constant list at
`dash_render.py:12367` — the function is present in the app and simply never called.

### The fifth dispatch table nobody counted

> **[func · server · L]** Collapse the FIFTH dispatch table the auditor never
> counted: the live-recompute `atype` chain in the emitted app (14 branches)
> plus the 15 hand-written `_compute_*` functions it dispatches to, which are
> a second statistical implementation of GlyphMapper's math emitted as string
> literals rather than copied with `inspect.getsource`. The task's <done> is
> 'a plot type is implemented once'; with this chain the count of hand-written
> server dispatch chains is 4 (36 + 16 + 16 + 14 = 82 branches), not 3. The
> chain also covers only 14 of 38 plot types, so every other type is frozen at
> its initial values when a filter widget moves.
>
> — `REMAINING.md` Appendix C, 15-03

Confirmed: the 15 string-literal `_compute_*` definitions run from
`dash_render.py:13192` (`_compute_histogram`) to `dash_render.py:13648`
(`_compute_kpi`), and the `atype` chain runs `dash_render.py:15604-15640`.

### What the ultraplan task itself asked for

> This is the core of the section: 38 `map_*` methods, 37 server `ptype` branches, 16 in the
> `by()` facet loop, 16 in `by(total)`. ... The generated file becomes
> a thin document-construction shim over the same rendering code rather than a second
> renderer.
>
> `<verify>` The parity test passes except for documented capability differences; the generated app contains no dispatch table of its own.
> `<done>` A plot type is implemented once, and both modes render it identically.
>
> — `.ultraplan/sections/section-15-unification.md`, task 15-03

One clause of that action was superseded by a binding decision and does **not** apply:
the app must **not** import `dash_render`; it carries `GlyphMapper` copied in. Appendix A
records that explicitly — *"Judged against the binding decision that **superseded** this
task's wording — emit `GlyphMapper` into the app rather than importing `dash_render` — so
the 'the app must import GlyphMapper' clause is not counted against it."*

---

## Epics

| Epic | Name | Goal (one line) | Items |
|---|---|---|---|
| **E05.A** | Delegate the main loop | Every one of the 37 remaining main-loop `ptype` branches calls `_DASH_MAPPER.map_<type>` instead of drawing for itself. | 1, 2 |
| **E05.B** | Make the served figure draw what the saved one draws | Close the measured glyph-property and grid divergences that the delegation must reproduce, so "delegated" and "identical" mean the same thing. | 3, 4 |
| **E05.C** | Collapse the fifth dispatch table | The live-recompute `atype` chain and its 15 string-literal `_compute_*` twins become one implementation, covering every plot type rather than 14. | 5 |

---

## User stories

### E05.A — Delegate the main loop

**US-05.A1** — *As a Stata user pasting a `twoway` command, I want `dash build, server`
to draw every layer my command names, so that the served dashboard is the same graph as
the saved one.*

- **Given** the command `dash pci 20 3000 30 4000, name(g1)` followed by
  `dash build, server saving(app.py)`
- **When** the generated app is served and the document is built
- **Then** the figure contains a `Segment` renderer with two literal endpoints, exactly
  as the standalone HTML does — not an empty, titled, axed plot region at rc 0.

**US-05.A2** — *As a Stata user, I want `function` and `tsrline` to draw in server mode,
so that a layer I asked for is never silently absent.*

- **Given** a spec whose plot list contains `function` (key `expr`) or `tsrline`
  (keys `yvar1`/`yvar2`)
- **When** the emitted app builds its document
- **Then** at least one glyph renderer exists for that layer, and its type matches the
  standalone renderer's (`Line` for `function`).

**US-05.B/A3** — *As a package maintainer, I want one implementation per plot type, so
that a fix I make once cannot be missing from the other mode.*

- **Given** the source emitted by `ServerAppBuilder._generate_app_source`
- **When** the emitted module is parsed and its `if`/`elif` comparisons against `ptype`
  in the main plot loop are counted
- **Then** no branch contains its own Bokeh glyph call (`fig.line`, `fig.scatter`,
  `fig.quad`, `fig.segment`, `fig.varea`, `fig.vbar`, …) for a type `GlyphMapper` maps.

### E05.B — Make the served figure draw what the saved one draws

**US-05.B1** — *As a dashboard viewer, I want a confidence band to be there in both
modes, so that I am not shown a fit whose uncertainty has silently vanished.*

- **Given** a spec with `{"type": "fpfitci", "yvar": "mpg", "xvar": "weight"}` under a
  non-default scheme
- **When** the standalone figure and the served figure are diffed glyph by glyph
- **Then** both contain a `VArea` at `fill_alpha` 0.2 **and** a `Line`, not a `Line`
  alone.

**US-05.B2** — *As a Stata user who set `scheme()`, I want the served glyphs to honour the
scheme, so that the two modes are not two different graphs of the same data.*

- **Given** a non-default scheme and a spec containing `rarea`, `rbar`, `rcapsym`,
  `rline`, `rconnected`, `tsrline`, `rscatter`, `pcscatter`, `pcspike`, `pcarrow` or
  `pcbarrow`
- **When** the two modes' glyph profiles are compared
- **Then** `fill_alpha`, `line_alpha`, `line_width`, `size` and the series colour index
  agree — e.g. `rarea` at 0.5 not 1.0, `rcapsym` caps at 1.5 not 1.2, the second series at
  the scheme's colour index 1 (`#7b92a8`) not index 0 (`#3e647d`).

**US-05.B3** — *As a Stata user comparing `dash` to `twoway fpfit`, I want the served fit
to be evaluated where Stata evaluates it, so that the fit overlays my observations and is
not cut off at both ends.*

- **Given** any dataset whose x has more than two distinct positive values
- **When** an `fpfit` or `fpfitci` layer is built by the emitted app
- **Then** its x array equals `_fp_grid(x)` — the sorted distinct positive observed x
  values, capped at `_FP_GRID_MAX` (1000) — starting at the smallest positive observation
  and ending at the largest, not at the 1st and 99th percentiles.

### E05.C — Collapse the fifth dispatch table

**US-05.C1** — *As a `dash serve` operator, I want every computed layer to follow the
filter widgets, so that a user who narrows the data is not left reading a line fitted to
rows that are no longer on screen.*

- **Given** a served dashboard containing a computed layer whose type is not one of the
  14 in the `atype` chain (for example `rscatter`'s siblings, `lpolyci`'s band, `mspline`,
  `function`)
- **When** a filter widget moves
- **Then** the layer's source is recomputed from the filtered frame, or the layer is
  explicitly and documentedly static — never silently frozen.

**US-05.C2** — *As a package maintainer, I want the recompute path and the draw path to
share one statistical implementation, so that a change to `GlyphMapper`'s math reaches the
served app without being retyped into a string literal.*

- **Given** a change to the shared grid or fitting code (`_fit_grid`, `_fp_grid`,
  `_kde_curve`, `GlyphMapper._histogram_grid`)
- **When** a server app is regenerated
- **Then** the recompute path in the generated app uses that changed code, because it was
  copied with `inspect.getsource` rather than written out as a literal.

---

## Business requirements

| ID | Requirement | How it is testable |
|---|---|---|
| **BR-05.1** | Every plot type `dash.ado` advertises draws at least one glyph in server mode, with no warning-free empty figure. | Server mirror of `test/test_every_plot_type_draws.py`, which reads the advertised list out of `dash.ado` rather than restating it. |
| **BR-05.2** | For a given spec, a served figure and a saved figure contain the same glyph types with the same visual properties, except where an entry in `test/test_mode_parity.ALLOWED` states a reason. | `test/test_mode_parity.py::TestTheTwoModesAgree` over a corpus that includes the 13 divergent types under a non-default scheme. |
| **BR-05.3** | A plot type is implemented once. No plot type is drawn by hand-written code in the generated app when `GlyphMapper` maps it. | AST walk of `ServerAppBuilder` output: no Bokeh glyph call inside a `ptype` branch of the main plot loop. |
| **BR-05.4** | `pci` and `pcscatter` work with **both** spec shapes `dash.ado` emits — four variable names, and the literal `values` array. | Unit test per shape plus a cscript that runs the literal form end to end. |
| **BR-05.5** | Statistical layers are evaluated on the same grid in both modes, including endpoints and point count. | `test/test_fit_grid_parity.py::TestTheServedFitUsesTheSameGrid`, extended to `fpfit`/`fpfitci`. |
| **BR-05.6** | A computed layer in a served dashboard is either recomputed when a filter moves or documented as static; it is never silently frozen at its first-render values. | Filter-move test that asserts the layer's source data changed, for every computed type. |
| **BR-05.7** | The generated app remains self-contained: it imports nothing from `dash_render` and runs with the package absent from `sys.path`. | Existing binding decision; asserted by the self-containment test owned by Phase 08 and re-run here as a guard. |
| **BR-05.8** | Server-mode output changes are recorded, because the served graph becomes correct rather than a drifted copy (bin counts, smoother parameters, colours). | CHANGELOG entry required by task 15-04; drafted in this phase, landed in Phase 30. |

---

## Technical requirements

Line numbers are as `REMAINING.md` gives them (current for `187a786`), confirmed against
the tree where noted. The plan's own section files carry stale numbers — the file grew
from ~10,455 to 16,264 lines — so these, not those, are authoritative.

### TR-05.1 — The delegation call shape (work item 1)

- **File / region.** `dash_render.py:ServerAppBuilder._generate_app_source`, which starts
  at `dash_render.py:12740`. Everything after `class ServerAppBuilder`
  (`dash_render.py:12265`) is *emitted-app source*, written as Python string literals; an
  edit there changes the generated app, not this module's behaviour.
- **The chain to replace.** The main plot loop begins at `dash_render.py:14031`
  (`"            ptype = plot.get('type', '')",`) and runs to roughly
  `dash_render.py:14850`. The loop variable `pi` is the plot index and doubles as the
  colour index; `plot` is the spec dict.
- **The one worked example.** `dash_render.py:14090`:

  ```python
  "                _r = _DASH_MAPPER.map_scatter(",
  "                    fig, csrc, yvar, xvar, opts,",
  "                    view=_sc_view, color_idx=pi)",
  "                graph_sources[gname].append(",
  "                    getattr(_r, 'data_source', None) or csrc)",
  ```

  Every `map_*` follows the same signature family, confirmed in the tree:
  `map_scatter(self, fig, source, yvar, xvar, options, view=None, color_idx=0)`
  (`dash_render.py:3407`); `map_fpfit` identical (`dash_render.py:4517`); the
  paired-coordinate family takes four variable names —
  `map_pci(self, fig, source, y1var, x1var, y2var, x2var, options, view=None, color_idx=0)`
  (`dash_render.py:5516`). Some return a single `GlyphRenderer`, some a `list` (e.g.
  `map_pci`, `map_fpfitci`), so the `graph_sources` registration must handle both.
- **Targets.** `GlyphMapper.map_*`, `dash_render.py:3407-6065`, 39 methods. Already
  copied verbatim into the app by `dash_render.py:12406-12410`; already instantiated as
  `_DASH_MAPPER` at `dash_render.py:12432`.
- **Spec keys the loop already unpacks** (`dash_render.py:14031-14040`): `type`, `yvar`
  (falling back to `var`), `xvar`, `yvar1`, `yvar2`; the paired-coordinate branch reads
  `y1var`, `x1var`, `y2var`, `x2var`; `function` reads `expr`; `pci` literal reads
  `values`.
- **The 37 types to delegate:** `area`, `bar`, `connected`, `dot`, `dropline`, `fpfit`,
  `fpfitci`, `function`, `histogram`, `kdensity`, `lfit`, `lfitci`, `line`, `lowess`,
  `lpoly`, `lpolyci`, `mband`, `mspline`, `pcarrow`, `pcbarrow`, `pci`, `pcscatter`,
  `pcspike`, `qfit`, `qfitci`, `rarea`, `rbar`, `rcap`, `rcapsym`, `rconnected`, `rline`,
  `rscatter`, `rspike`, `scatteri`, `spike`, `tsline`, `tsrline`. (Appendix A's list of
  38 additionally names `hist`, the alias `histogram` already shares a branch with.)
- **Invariant to preserve.** `graph_sources[gname]` must continue to receive the source a
  delegated branch actually draws from, because the filter replacement loop and `link()`
  walk that registry. Where the mapper builds its own source (every computed layer), the
  returned renderer's `data_source` is the one to register — and, for computed layers, it
  is also what TR-05.5 registers into `agg_sources`.

### TR-05.2 — `pci` with literal coordinates (work item 2)

- **The dead read.** `dash_render.py:14781-14796`, emitted as
  `"            elif ptype in ('pci', 'pcscatter'):"`, reads
  `plot.get('y1var','')`, `plot.get('x1var','')`, `plot.get('y2var','')`,
  `plot.get('x2var','')` and is gated on `if y1v and x1v and y2v and x2v:`. For a literal
  command those four keys are absent, the guard is false, and the branch falls through
  drawing nothing.
- **What `dash.ado` actually writes.** The literal form is serialized as
  `"values":[[y,x],...]` at `dash.ado:1212` (the `local vfields "values":`arr'"` path),
  and `dash.ado:1655-1667` is the guard that lets a varlist-free plot through at all:

  ```stata
  // scatteri, pci, pcscatter and function take literal coordinates or an
  // expression rather than variables, so having no varlist is correct for
  // them -- this guard used to reject those plot types outright.
  local _varfree = 0
  foreach _vf in scatteri pci pcscatter function {
      if strpos(`"`json_spec'"', `""type":"`_vf'""') > 0 local _varfree = 1
  }
  ```

- **The targets, both already emitted.** `GlyphMapper.map_pci` (`dash_render.py:5516`),
  which delegates to `map_pcspike`, and `GlyphMapper.map_pci_literal`
  (`dash_render.py:5548`), signature
  `map_pci_literal(self, fig, values, options, color_idx=0)`. Its docstring states the
  order explicitly: *"`pci 20 3000 30 4000` names two points — `(y=20, x=3000)` and
  `(y=30, x=4000)` — and draws a line between them. More points draw more segments, two
  at a time. dash.ado writes the list as `[[20,3000],[30,4000]]`, in `(y, x)` order."*
- **Required dispatch.** Variable form → `map_pci`; `values` present → `map_pci_literal`.
  Neither path may depend on the other's keys.

### TR-05.3 — The 13 divergent types (work item 3)

Each row is a measured divergence under a **non-default scheme**. The delegated branch
must reproduce the standalone column, because the standalone column is what
`GlyphMapper` already produces.

| type | emitted branch | standalone (target) | server (today) |
|---|---|---|---|
| `fpfitci` | `dash_render.py:14253` | `VArea` (α 0.2) + `Line` | `Line` only — a verbatim copy of the `fpfit` branch; **the band is gone** |
| `lowess` | `dash_render.py:14192` → `_compute_lowess` emitted at `dash_render.py:13396` | `map_lowess`, statsmodels | a second smoother implementation |
| `rarea` | `dash_render.py:14429` | `fill_alpha` 0.5 | `fill_alpha` 1.0 |
| `rbar` | `dash_render.py:14457` | `line_alpha` 0 | white outline at 1.2px |
| `rcapsym` | `dash_render.py:14613` | cap `line_width` 1.5 | 1.2 |
| `rline` | `dash_render.py:14535` | second series at scheme colour index 1 (`#7b92a8`) | colour index 0 (`#3e647d`) with a dash |
| `rconnected` | `dash_render.py:14555` | as `rline` | as `rline` |
| `tsrline` | `dash_render.py:14728` | as `rline` | as `rline` |
| `rscatter` | `dash_render.py:14768` | marker size from the scheme (`REMAINING.md` records **10.18** for the non-default-scheme case in Appendix B and **8.0** for the default-scheme diff in §4) | hardcoded `size=6` |
| `pcscatter` | in the `dash_render.py:14781` branch | scheme marker size | hardcoded `size=6` |
| `pcspike` / `pcarrow` / `pcbarrow` | `dash_render.py:14676` | `line_width` 1.5 | 1.2 |

Targets: `GlyphMapper.map_fpfitci` (`dash_render.py:4569`), `map_lowess` (`4091`),
`map_rarea` (`4920`), `map_rbar` (`4958`), `map_rcapsym` (`5291`), `map_rline` (`5106`),
`map_rconnected` (`5147`), `map_tsrline` (`5832`), `map_rscatter` (`5861`),
`map_pcscatter` (`5609`), `map_pcspike` (`5472`), `map_pcarrow` (`5660`),
`map_pcbarrow` (`5732`).

Because the delegation in TR-05.1 replaces the branch body wholesale, these 13 are closed
*by* TR-05.1 rather than alongside it — but they are itemised separately because each is
an independently measured, independently testable behaviour change, and because three of
them (`fpfitci`'s band, the `rline` family's colour index, `lowess`'s second smoother)
change the picture enough to need a CHANGELOG line under BR-05.8.

### TR-05.4 — The fractional-polynomial grid (work item 4)

- **Defect site.** `dash_render.py:13492-13510`, the emitted `_compute_fpfit`. Line
  `dash_render.py:13502` is the linspace quoted above.
- **Target.** `_fp_grid` (`dash_render.py:6441`), whose contract is: *"Sorted distinct
  positive x values, capped at `_FP_GRID_MAX` points."* Its body drops non-positive x
  (`pos = np.unique(x[x > 0])`), returns `np.array([1e-6, 1.0])` for an empty positive
  set, a single-element array for one distinct value, and falls back to
  `np.linspace(float(pos[0]), float(pos[-1]), _FP_GRID_MAX)` above the cap — the resource
  guard the docstring describes as protecting the `O(n_boot * n_points)` bootstrap band.
- **`_FP_GRID_MAX = 1000`** at `dash_render.py:121`, already in the emitted constant list
  at `dash_render.py:12367`.
- **Standalone call sites to match.** `dash_render.py:4554` (`map_fpfit`) and
  `dash_render.py:4612` (`map_fpfitci`), both `x_grid = _fp_grid(x)`.
- **Availability.** `_fp_grid` is already named in the `inspect.getsource` emission list
  at `dash_render.py:12386-12410`, so no new copy is needed — only the call.
- **Consequence to reverse.** With the linspace, the served fit is truncated at the 1st
  and 99th percentiles at both ends and cannot overlay the observations; the `fpfitci`
  band (150 points in the historical code) and its line (200) did not coincide.

### TR-05.5 — The live-recompute chain (work item 5)

- **The chain.** `dash_render.py:15604-15640`, inside the emitted `_on_filter_change`
  handler, dispatching on `atype = agg['type']` across 14 branches: `histogram`, `lfit`,
  `qfit`, `kdensity`, `lowess`, `lpolyci`, `lpoly`, `fpfit`, `lfitci`, `qfitci`,
  `mspline`, `mband`, `rscatter`, `pcscatter`.
- **The registry it reads.** The main loop writes entries such as
  `dash_render.py:14110`:

  ```python
  "                agg_sources[(gname, pi)] = {",
  "                    'opts': opts,",
  "                    'source': fit_src,",
  "                    'type': 'lfit',",
  "                    'yvar': yvar, 'xvar': xvar,",
  "                }",
  ```

  There are 16 such registrations in the main loop (`dash_render.py:14110, 14123, 14147,
  14182, 14195, 14214, 14229, 14244, 14256, 14378, 14405, 14747, 14759, 14775, 14801`,
  plus the paired branch). The recompute handler reads `agg.get('opts') or {}`, so an
  entry that omits `opts` silently loses the user's `bin()`, `n()`, `bwidth()` and
  `degree()` on the first widget move.
- **The 15 string-literal twins.** `dash_render.py:13192-13648`:
  `_compute_histogram` (13192), `_compute_lfit` (13212), `_compute_qfit` (13227),
  `_compute_lfitci` (13237), `_compute_qfitci` (13302), `_compute_kdensity` (13354),
  `_compute_lowess` (13396), `_compute_lpoly` (13428), `_compute_fpfit` (13492),
  `_compute_mspline` (13509), `_compute_mband` (13524), `_compute_rscatter` (13557),
  `_compute_pcscatter` (13570), `_compute_lpolyci` (13605), `_compute_kpi` (13648).
- **Collapse targets.** `GlyphMapper.map_*` (`dash_render.py:3407-6065`) and its grid
  helpers: `GlyphMapper._histogram_grid` (`dash_render.py:4707`), module-level
  `_fit_grid` (`dash_render.py:6419`), `_kde_curve` (`dash_render.py:6681`), `_fp_grid`
  (`dash_render.py:6441`).
- **The mechanism already in the file.** `dash_render.py:12518-12529` copies four
  `GlyphMapper` static methods and one `DashRenderer` method into the app as module-level
  functions, stripping decorators and rewriting the class prefix:

  ```python
  for _sm in (GlyphMapper._histogram_grid,
              GlyphMapper._default_lpoly_bwidth,
              GlyphMapper._compute_lpoly_fit,
              GlyphMapper._bootstrap_ci,
              DashRenderer._kpi_statistic):
      _lines = _textwrap.dedent(
          _inspect.getsource(_sm)).rstrip("\n").split("\n")
      while _lines and _lines[0].strip().startswith("@"):
          _lines = _lines[1:]
      _lines = [_l.replace("GlyphMapper._", "_")
                 .replace("DashRenderer._", "_") for _l in _lines]
  ```

  This is the precedent the collapse should follow: the data half of each layer must come
  from copied source, not from a retyped literal. Three of the emitted `_compute_*`
  already call copied helpers (`_histogram_grid` at `dash_render.py:13204`, `_fit_grid` at
  `13223`, `13233`, `13264`, `13328`, `_kde_curve` at `13393`), which shows the pattern
  works; the remaining math is what still diverges.
- **Coverage requirement.** The chain covers 14 of 38 types. The other 24 are frozen at
  their initial values the moment a widget moves. Either a type recomputes, or the
  generated app must state — in one place, not per branch — that it is static.
- **Counting requirement.** `REMAINING.md` records the branch arithmetic as
  `36 + 16 + 16 + 14 = 82` hand-written server dispatch branches across four chains. This
  phase removes the 36 and the 14; Phase 06 removes the two 16s.

### TR-05.6 — Constraints the collapse must not break

- The emitted app **must not import `dash_render`** (superseding binding decision). All
  shared code arrives by `inspect.getsource` copy.
- The app embeds its data base64-encoded; that transport and S14's cleanup of the file
  carrying it are unchanged.
- `inspect.getsource` at `dash_render.py:12386-12410` has **no `try`/`except`**. Any
  widening of the copied set widens the blast radius on a byte-compiled-only or
  zipimported install. The guard for this is itemised in Phase 08; do not widen the list
  without noting the dependency.
- `ServerAppBuilder.__init__` resolves the scheme at **build** time
  (`dash_render.py:12311`, via `SchemeParser.resolve_or_fallback`), so scheme-sensitive
  work in this phase is only meaningful where the scheme resolves — see Risks.

---

## Work items

Every item below is reproduced from the phase assignment, numbered as given. Nothing is
dropped, merged or summarised.

---

**Item 1 — Delegate the remaining 37 main-loop `ptype` branches to `_DASH_MAPPER`.**
`[functional · server · large]` · origin 15-03 · Appendix B

> The chain at dash_render.py:14031 (`ptype = plot.get('type','')`) through ~14850 still
> hand-writes drawing code for: area, bar, connected, dot, dropline, fpfit, fpfitci,
> function, histogram, kdensity, lfit, lfitci, line, lowess, lpoly, lpolyci, mband,
> mspline, pcarrow, pcbarrow, pci, pcscatter, pcspike, qfit, qfitci, rarea, rbar, rcap,
> rcapsym, rconnected, rline, rscatter, rspike, scatteri, spike, tsline, tsrline. Each has
> a `GlyphMapper.map_<type>` already emitted into the app and unused.

*Where:* `dash_render.py:ServerAppBuilder._generate_app_source` (starts 12740); emitted
chain at `dash_render.py:14031-14850`; targets are `GlyphMapper.map_*` at
`dash_render.py:3407-6065`.

*Evidence:* `REMAINING.md` §4 ("51 `ptype ==` comparisons … exactly one delegates");
Appendix A 15-03 remaining item 1 (the 38-type list); Appendix B 15-03 item 1.

---

**Item 2 — `pci` with literal coordinates draws nothing in server mode — a dead read.**
`[functional · server · small]` · origin 15-03 · Appendix B

> dash.ado writes literal pci as `"values":[[y,x],...]` (dash.ado:1212, guarded at
> dash.ado:1655-1667), but the emitted branch reads y1var/x1var/y2var/x2var and bails when
> they are absent. `GlyphMapper.map_pci` / `map_pci_literal` (dash_render.py:5516, 5548)
> already handle the literal shape.

*Where:* `dash_render.py:14781-14796` (emitted `elif ptype in ('pci','pcscatter')`).

*Evidence:* `REMAINING.md` §4 drift table (`pci`: standalone `Segment`, server *nothing*);
Appendix B "Three findings worth pulling out first", finding 1 ("Draw nothing at all:
`function`, `pci`, `tsrline`"); Appendix B 15-03. Also the docstring of
`test/test_every_plot_type_draws.py`, which records that `pci` and `pcscatter` *"produced
a titled, axed, empty plot region with rc 0 and no warning until this test existed"* — and
that test runs standalone only.

---

**Item 3 — 13 more main-loop plot types diverge on glyph properties under a non-default
scheme.** `[functional · server · medium]` · origin 15-03 · Appendix B

> fpfitci loses its CI band entirely (emitted branch is a verbatim copy of fpfit); rarea
> fill_alpha 1.0 vs 0.5; rbar drawn with a white 1.2px outline vs line_alpha 0; rcapsym
> caps at line_width 1.2 vs 1.5; rline/rconnected/tsrline draw the second series in colour
> index 0 with a dash instead of the scheme's colour index 1 (#3e647d vs #7b92a8);
> rscatter/pcscatter markers at size 6 vs scheme 10.18; pcspike/pcarrow/pcbarrow at
> line_width 1.2 vs 1.5; lowess runs a second implementation (`_compute_lowess`) where
> standalone uses statsmodels via map_lowess.

*Where:* `dash_render.py:14253` (fpfitci), `14192` (lowess → `_compute_lowess` emitted at
`13396`), `14429` (rarea), `14457` (rbar), `14613` (rcapsym), `14535` (rline), `14555`
(rconnected), `14728` (tsrline), `14768` (rscatter), `14676` (pcspike/pcarrow/pcbarrow),
vs `GlyphMapper.map_*` at `dash_render.py:3407-6065`.

*Evidence:* Appendix B 15-03; corroborated by the §4 drift table for `fpfitci`
(`VArea`(α .2) + `Line` vs `Line` only) and `rscatter` (marker size 8.0 vs 6).

---

**Item 4 — Server-mode `fpfit`/`fpfitci` still evaluate on the 200-point
1st-99th-percentile linspace that `_fp_grid` was written to remove.**
`[functional · server · small]` · origin 15-03 · Appendix C

> `_fp_grid`'s own docstring (dash_render.py:6441-6460) states Stata uses the distinct
> observed x values and that 'dash used a 200-point linspace for fpfit and a 150-point one
> for fpfitci, both truncated to the 1st-99th percentile ... so the band and the line it
> belonged to did not lie on top of each other, and both ends of the fit were cut off'.
> `_fp_grid` IS copied into the app (dash_render.py:12395) but nothing calls it: the
> emitted `_compute_fpfit` at dash_render.py:13492 still does
> `np.linspace(float(np.percentile(x, 1)), float(np.percentile(x, 99)), 200)` at
> dash_render.py:13502. The served fit is therefore truncated at both ends and cannot
> overlay the observations.

*Where:* `dash_render.py:13492-13510` (emitted `_compute_fpfit`), `dash_render.py:6441`
`_fp_grid`, `dash_render.py:4554`/`4612` (the standalone call sites).

*Evidence:* Appendix C 15-03; confirmed in the tree — the literal at `13502` and both
standalone `x_grid = _fp_grid(x)` call sites are as described.

---

**Item 5 — Collapse the FIFTH dispatch table the auditor never counted.**
`[functional · server · large]` · origin 15-03 · Appendix C

> The live-recompute `atype` chain in the emitted app (14 branches) plus the 15
> hand-written `_compute_*` functions it dispatches to, which are a second statistical
> implementation of GlyphMapper's math emitted as string literals rather than copied with
> `inspect.getsource`. The task's <done> is 'a plot type is implemented once'; with this
> chain the count of hand-written server dispatch chains is 4 (36 + 16 + 16 + 14 = 82
> branches), not 3. The chain also covers only 14 of 38 plot types, so every other type is
> frozen at its initial values when a filter widget moves.

*Where:* `dash_render.py`: emitted chain at `15604-15640`; emitted `_compute_*` string
literals at `13192-13700`; the collapse targets are `GlyphMapper.map_*` (`3407-6065`) and
its grid helpers (`_histogram_grid`, `_fit_grid`, `_kde_curve`).

*Evidence:* Appendix C 15-03; confirmed in the tree — 14 `atype` branches at
`15604-15640`, 15 `_compute_*` definitions from `13192` to `13648`.

---

## Test plan

Project rule 8 governs the order: **every one of these five items is a reported defect, so
its regression test is written first and must fail before the fix and pass after.** Rule 4
governs the breadth: every function introduced or changed gets a unit test. Each test
below is followed by its **mutation** — the specific edit that must make it die, proving
it is not vacuous.

### Cross-cutting: the two harnesses that already exist

| file | what it gives this phase |
|---|---|
| `test/test_mode_parity.py` | `_spec()` (:70), `CORPUS` (:187, 4-tuples of name/plots/build_options/graph_options, normalised at :284), `_glyph_profile` (:131), `_annotations` (:150), `_chrome` (:178), `ALLOWED` (:55), `TestTheTwoModesAgree` (:289) |
| `test/test_fit_grid_parity.py` | `TestTheServedFitUsesTheSameGrid` (:115) with `_served()`, which builds a one-plot spec, runs `ServerAppBuilder(...).build()`, execs the app, calls `make_document(doc)` and returns the fitted x array; currently parametrized `["lfit", "qfit"]` |
| `test/test_every_plot_type_draws.py` | reads the advertised plot-type list out of `dash.ado` (`_ADO`, :33) rather than restating it; `test_an_advertised_plot_type_draws_a_glyph` (:150) and `test_an_advertised_plot_type_draws_real_data` (:160) — **standalone only, no `ServerAppBuilder` reference in the file** |

Widening `CORPUS` in general, and fixing the parity guard's blind spots (it compares no
data; `ALLOWED` gates no comparison), are itemised deliverables owned by **Phase 08**.
This phase does not wait on them: the tests below assert data directly where the property
profile cannot see it.

### E05.A — Delegate the main loop (items 1, 2)

**Write first (must fail today):**

1. `test/test_every_plot_type_draws.py` — add a server mirror,
   `test_an_advertised_plot_type_draws_a_glyph_in_server_mode(ptype)`, parametrized over
   the same list read from `dash.ado`. It builds the same minimal spec, runs
   `dr.ServerAppBuilder(spec, data).build(app_path)`, execs the generated module, calls
   `make_document(Document())` and asserts at least one `GlyphRenderer`.
   **Fails today on `function`, `pci` and `tsrline`** (Appendix B finding 1).
   *Mutation:* restore the `if y1v and x1v and y2v and x2v:` gate in the `pci` branch —
   the test must fail again.
2. `test/test_paired_coordinate_plots.py` — add
   `test_literal_pci_draws_segments_in_server_mode`: a spec carrying
   `{"type": "pci", "values": [[20, 3000], [30, 4000]]}` and **no** `y1var`/`x1var`/
   `y2var`/`x2var`, asserting a `Segment` renderer whose `x0`/`y0`/`x1`/`y1` data match
   the literal pairs in `(y, x)` order. **Fails today** — the branch reads keys that are
   not there.
   *Mutation:* swap the `(y, x)` order in `map_pci_literal`'s consumption — the coordinate
   assertion must fail.

**Unit tests (rule 4):**

3. New `test/test_server_dispatch.py`:
   - `test_no_ptype_branch_draws_for_itself` — parse the emitted source with `ast`, walk
     the main plot loop, and assert that no `if`/`elif` body comparing `ptype` contains a
     `Call` whose function is an attribute of `fig` in the Bokeh glyph set (`line`,
     `scatter`, `quad`, `segment`, `varea`, `vbar`, `hbar`, `patch`, `multi_line`,
     `ray`, `text`). This is task 15-03's own `<verify>` clause
     ("the generated app contains no dispatch table of its own") expressed behaviourally
     enough to be mutation-provable.
   - `test_every_mapped_type_has_a_delegating_branch` — for each of the 39 `map_*` names,
     assert the emitted source contains a `_DASH_MAPPER.map_<type>` call.
   *Mutation:* re-inline any one branch (e.g. put `fig.line(...)` back in the `lfit`
   branch) — both tests must fail.
4. `test/test_server_data_shape.py` — assert that for each delegated computed layer the
   source registered in `graph_sources[gname]` is the one the returned renderer draws
   from, i.e. `renderer.data_source is registered_source`.
   *Mutation:* register the shared `csrc` instead of the renderer's own source — the test
   must fail, and the filter tests in E05.C must fail with it.

**Integration / cscript:**

5. `test/test_server_build.cscript` — add a literal-`pci` case: `dash pci 20 3000 30 4000,
   name(g1)` then `dash build, server saving(...)`, assert rc 0, assert the emitted file
   contains `map_pci_literal`, and assert it contains no `fig.segment(` inside a `ptype`
   branch.
6. `test/test_e2e_serve.cscript` — extend the served-dashboard walk with a multi-layer
   command that includes `function` and `tsrline`, asserting the served document reports
   the expected layer count.
7. `test/test_conformance.cscript` — its "every layer drew something" assertion runs
   standalone only (`REMAINING.md` §4). Add the server arm so the conformance corpus
   covers both modes.

### E05.B — Make the served figure draw what the saved one draws (items 3, 4)

**Write first (must fail today):**

8. `test/test_mode_parity.py` — add one `CORPUS` entry per divergent type under a
   non-default scheme (`{"scheme": "economist"}` and `{"scheme": "s1mono"}` are both
   already used by existing entries): `fpfitci`, `rarea`, `rbar`, `rcapsym`, `rline`,
   `rconnected`, `tsrline`, `rscatter`, `pcscatter`, `pcspike`, `pcarrow`, `pcbarrow`,
   `lowess`. `TestTheTwoModesAgree::test_same_glyph_properties` must fail on all 13 —
   `fill_alpha` 1.0 vs 0.5, `line_width` 1.2 vs 1.5, `size` 6 vs the scheme's,
   colour `#3e647d` vs `#7b92a8`.
   *Mutation:* after the fix, set `rarea`'s `fill_alpha` back to 1.0 in the delegated path
   — the `rarea` case must fail and no other.
9. `test/test_mode_parity.py` — a dedicated
   `test_fpfitci_keeps_its_band_in_both_modes`: assert the **count of `VArea` renderers**
   is equal in the two modes for an `fpfitci` spec. The property profile alone will not
   catch a missing glyph if the remaining one matches, so assert the type census.
   *Mutation:* drop the `VArea` from the delegated `fpfitci` path — the test must fail.
10. `test/test_fit_grid_parity.py` — extend
    `TestTheServedFitUsesTheSameGrid`'s parametrization from `["lfit", "qfit"]` to
    `["lfit", "qfit", "fpfit", "fpfitci"]`.
    `test_the_two_modes_draw_at_the_same_x` must fail today: 200 linspace points between
    the 1st and 99th percentiles against `_fp_grid`'s distinct positive observed x.
    *Mutation:* restore the linspace at the emitted `_compute_fpfit` — the test must fail.

**Unit tests (rule 4):**

11. `test/test_fit_grid_parity.py` — `test_the_served_fp_grid_is_the_observed_x`: assert
    the served `fpfit` x array equals `np.unique(x[x > 0])` exactly, including that its
    first element is the smallest positive observation and its last the largest.
12. `test/test_fit_grid_parity.py` — `test_the_served_fp_grid_honours_the_cap`: with more
    than `_FP_GRID_MAX` (1000) distinct positive x values, assert the served grid has
    exactly 1000 points and spans `pos[0]` to `pos[-1]`, matching `_fp_grid`'s documented
    resource guard.
    *Mutation:* raise `_FP_GRID_MAX` in the emitted constants only — the length assertion
    must fail, proving the app reads the copied constant rather than a literal.
13. `test/test_statistical_truth.py` — assert the served `lowess` values equal the
    standalone `map_lowess` values on the same data (one implementation, not two).
    *Mutation:* point the delegated branch back at `_compute_lowess` — the test must fail.
14. `test/test_range_plots.py` and `test/test_glyphs.py` — per-type unit assertions for the
    scheme-derived properties the delegation now supplies (`rarea` α 0.5, `rbar`
    `line_alpha` 0, `rcapsym` 1.5, the `rline` family's colour index 1).

**Integration / cscript:**

15. `test/test_server_scheme.cscript` coverage does not exist; add the case to
    `test/test_server_build.cscript`: build the same command with `scheme(economist)` in
    both modes and assert the emitted app's glyph properties come from the scheme.

### E05.C — Collapse the fifth dispatch table (item 5)

**Write first (must fail today):**

16. New `test/test_server_recompute.py` —
    `test_a_computed_layer_follows_the_filter(ptype)`, parametrized over every computed
    plot type. Build a served app with a `filter()` widget, snapshot the layer's source
    data, fire the filter callback with a mask that removes rows, and assert the data
    changed. **Fails today for the 24 types absent from the 14-branch chain**, which are
    frozen at their initial values.
    *Mutation:* make `_on_filter_change` return early — every case must fail.
17. `test/test_server_recompute.py` — `test_plot_options_survive_a_filter_move`: a
    `histogram ..., bin(4)` layer must still have 4 bars after a widget move (the handler
    reads `agg.get('opts') or {}`, so an `agg_sources` entry that omits `opts` regresses
    here).
    *Mutation:* delete `'opts': opts` from one registration — the test must fail for that
    type only.

**Unit tests (rule 4):**

18. `test/test_server_recompute.py` — `test_the_recompute_uses_the_copied_math`: assert
    the generated app contains no retyped statistical literal for a type `GlyphMapper`
    already implements; concretely, assert the recomputed values for `histogram`, `lfit`,
    `qfit`, `kdensity`, `lowess`, `lpoly`, `lpolyci`, `fpfit`, `lfitci`, `qfitci`,
    `mspline`, `mband`, `rscatter`, `pcscatter` equal what the shared code produces on the
    filtered frame.
    *Mutation:* change `_fit_grid`'s default point count in `dash_render.py` only — the
    served values must move with it; if they do not, the app is still carrying a literal.
19. `test/test_server_statistics.py` — keep the existing served-statistic assertions green
    across the collapse; they are the guard that the recompute path did not change its
    numbers for the 14 types that already worked.
20. `test/test_mode_parity.py::TestTheCopiedHelpersBringTheirCallees` (:395) — re-run;
    a widened `inspect.getsource` set must not introduce a `NameError` at import. (Its
    known blind spot — it scans module-level functions only, so the copied classes are
    unscanned — is Phase 08's item, not this phase's; note it rather than rely on it.)

**Integration / cscript:**

21. `test/test_e2e_filters.cscript` — add a served case whose computed layer is one of the
    24 previously frozen types, moving a widget and asserting the layer changed.
22. `test/test_e2e_kpi.cscript` — unchanged expectations; re-run to confirm the KPI half of
    `_on_filter_change` (the `_compute_kpi` path at `dash_render.py:13648`) is unaffected.

### Suite-level obligations (project rule 5)

Before any commit: pull `main`, then run the full pytest suite and the full certification
suite from `test/` under `arch -arm64`, with `$dash_nobrowser` set. A skip is not a pass.
The baseline to beat is `REMAINING.md`'s recorded HEAD state: **3,498 passed / 37 skipped;
25/25 cscripts**.

---

## Definition of done

A reviewer can tick each line.

**Behaviour**

- [ ] Every one of the 37 main-loop `ptype` branches calls `_DASH_MAPPER.map_<type>`; the
      only drawing code left in the emitted main loop is the delegation and the
      `graph_sources` registration.
- [ ] `function`, `pci` and `tsrline` draw a glyph in server mode.
- [ ] Literal `pci` (spec key `values`, `(y, x)` order) draws segments in server mode via
      `map_pci_literal`; variable-form `pci` still draws via `map_pci`.
- [ ] `fpfitci` renders a `VArea` **and** a `Line` in server mode.
- [ ] The 13 measured property divergences are closed: `rarea` α 0.5, `rbar` `line_alpha`
      0, `rcapsym` 1.5, `rline`/`rconnected`/`tsrline` on the scheme's colour index 1
      (`#7b92a8`), `rscatter`/`pcscatter` at the scheme marker size,
      `pcspike`/`pcarrow`/`pcbarrow` at 1.5, `lowess` through `map_lowess`.
- [ ] Served `fpfit`/`fpfitci` are evaluated on `_fp_grid(x)`, capped at `_FP_GRID_MAX`
      (1000), with no percentile truncation.
- [ ] The `atype` chain at `dash_render.py:15604-15640` no longer dispatches by hand; the
      recompute path shares one implementation with the draw path.
- [ ] No computed layer is silently frozen when a filter widget moves; any layer that is
      deliberately static is documented as such in one place.
- [ ] `opts` reaches every recompute (`bin()`, `n()`, `bwidth()`, `degree()` survive a
      widget move).

**Structure**

- [ ] The hand-written server dispatch branch count drops from 82 to 32 (the two facet
      chains, `16 + 16`, which are Phase 06).
- [ ] The generated app imports nothing from `dash_render` and runs with the package off
      `sys.path`.
- [ ] Shared math reaches the app by `inspect.getsource`, not by retyped string literal.

**Tests**

- [ ] Each of the five items has a regression test that was observed to fail before the
      fix and pass after (rule 8), recorded in the commit message.
- [ ] Each new or changed function has a unit test (rule 4).
- [ ] Every test above has a named mutation that kills it, and that mutation was run.
- [ ] `test/test_every_plot_type_draws.py` covers both modes.
- [ ] Full pytest suite and all cscripts green, with honest skips; no regression against
      3,498 passed / 37 skipped and 25/25 cscripts.

**Paperwork**

- [ ] A CHANGELOG line drafted (landing in Phase 30) stating that server-mode output
      changes because it is now correct rather than a drifted copy — different smoother,
      different grid, different colours, a restored confidence band.
- [ ] `BUGS.md` entries added for the five items, per rule 8's diagnose-then-test-then-fix
      order.
- [ ] Committed to `feature/batch4-interactive-layer`, with the merge command reported and
      not run (rule 6).

---

## Risks and sequencing notes

**1. Delegating `lowess` propagates a standalone defect into both modes.**
`REMAINING.md` §4 records that **standalone** `lowess` draws `#1f77b4` at width 1 —
matplotlib's default blue — and *"ignores the scheme"*, while server draws `#1a476f` at
width 1.5. Item 3 requires the server to delegate to `map_lowess`. If `map_lowess`'s
colour handling is not fixed at the same time, the two modes will agree on the *wrong*
colour and the parity test will go green on a defect. Fix the mapper first, then delegate;
assert the served `lowess` colour against the scheme, not against standalone.

**2. The parity guard compares no data, so a green corpus proves less than it looks.**
Appendix C: `_glyph_profile` (`test/test_mode_parity.py:131`) reads only
type/marker/size/fill_color/line_color/line_width/line_dash/fill_alpha, `data_source.data`
is touched in exactly two places (`:365`, `:382`, both histogram bar counts), and `ALLOWED`
(`:55`) gates no comparison — its only assertions are that it is non-empty and each reason
exceeds 40 characters (`:388-392`). Consequence, measured: *"kdensity (300 vs 200 points)
and fpfit/fpfitci (10 vs 200) diverge inside the existing corpus and the file still reports
165 passed."* Therefore item 4's regression **must** live in
`test/test_fit_grid_parity.py`, which compares arrays, and not in the property corpus.
Repairing the guard itself is Phase 08.

**3. The `kdensity` grid divergence is adjacent and is itemised elsewhere.**
Appendix C records that `GlyphMapper.map_kdensity` defaults `n` to 300.0
(`dash_render.py:~4863`) while the emitted `_compute_kdensity` hardcodes `n_pts = 200`
(`dash_render.py:13380`). It is not one of this phase's five items, but the collapse in
item 5 will move it; coordinate with whichever phase carries it so the change is recorded
once.

**4. Scheme-sensitive assertions depend on the scheme resolving at all.**
`ServerAppBuilder.__init__` resolves the scheme at build time
(`dash_render.py:12311`), and `REMAINING.md` §1 shows that under a real `net install`
`SchemeParser` searches `<dir>/py/schemes` and `<dir>/py` — neither of which exists —
so every scheme silently degrades to built-in defaults. Run this phase's scheme-sensitive
tests from the repo checkout. The install-layout fix is **Phase 03**; until it lands, a
packaged-install run of these tests would pass for the wrong reason.

**5. Widening the `inspect.getsource` list has no error path.**
`dash_render.py:12386-12410` calls `inspect.getsource` on three classes and 15 helpers
with no `try`/`except`. Any deployment where the source text is not on disk —
byte-compiled-only install, zipimport, a stripped copy — fails the **build** with a bare
traceback rather than a dash-level message. Item 5's recommended mechanism widens that
set. The guard is itemised in Phase 08; if item 5 lands first, note the exposure in the
commit message.

**6. Order inside the phase.** Item 4 is a two-line change and is the cheapest proof that
the emitted app can be made to call copied code — do it first, as a pathfinder. Then
item 2 (one branch, two spec shapes). Then item 1, type by type, with the parity corpus
entries from item 3 written ahead of each group so the fix is always closing a red test.
Item 5 last: it touches the live path and changes what users see when a widget moves.

**7. This phase is deliberately main-loop only.** The `by()` facet chain
(`dash_render.py:15137-15230`) and its `by(total)` twin (`15237-15330`) are Phase 06, and
the 20 types that draw nothing under `by()` are Phase 07. Appendix A explains why this
order: *"Sequencing 15-03 first would collapse most of the rest, because a delegated branch
inherits the standalone behaviour instead of needing its own copy of each fix."* Doing the
facets first means writing the delegation twice.

**8. The change is user-visible and should be announced.** Task 15-04 already requires the
CHANGELOG to *"record that server-mode output changes substantially — different bin counts,
different smoother parameters, different colours, different KPI cards — because it is now
correct rather than a drifted copy."* That requirement is created by this phase and
discharged in Phase 30.
