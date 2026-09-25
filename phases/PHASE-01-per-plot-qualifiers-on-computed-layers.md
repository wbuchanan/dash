# Phase 01 — Per-plot qualifiers on computed layers

**Purpose.** Today `dash (scatter mpg weight) (lfit mpg weight if foreign==1)`
draws the linear fit for all 74 cars instead of the 22 foreign ones, returns
rc 0, and says nothing. Every statistical layer in the package — `lfit`,
`qfit`, `lfitci`, `qfitci`, `fpfit`, `fpfitci`, `lpoly`, `lpolyci`, `mband`,
`mspline`, `histogram`, `kdensity` — behaves the same way, in both renderers.
When this phase ships, a qualifier written inside a plot's parentheses
re-estimates that layer on the qualified subsample and nothing else; the
restriction survives the viewer's first filter move, a brush, a `link()`, a
`by()` panel and `jitter()`; marker labels stop being drawn for rows the layer
excluded; the layer types that structurally cannot carry a qualifier say so out
loud instead of failing silently; and the `bokeh serve` app the package
generates does the same thing the standalone HTML does. This is the audit's
own item 0 — *"Wrong numbers outrank everything else"* — and it is the reason
this is Phase 1.

---

## At a glance

| | |
|---|---|
| **Work items** | 10 |
| **Functional / deliverable split** | 10 functional · 0 deliverable-only |
| **Effort mix** | 8 medium · 2 small |
| **Renderers touched** | standalone only: items 3, 4, 7, 9, 10 · server only: items 2, 5, 6 · both: items 1, 8 |
| **Files touched** | `dash_render.py` only (both the renderer and the source `ServerAppBuilder` emits). No `dash.ado` / `dash_parse.mata` change belongs to this phase. |
| **Ultraplan coverage** | Task **06-06** "Carry and apply per-plot if/in qualifiers" (section 06, *Varlist / plot-spec*). This phase discharges the **functional Python half**. 06-06 carries 19 backlog items in total (7 from Appendix B + 12 from Appendix C); 10 of them are here. |
| **Depends on** | Nothing. This phase is first in the audit's suggested order and has no upstream. |
| **Unblocks** | **Phase 2** (qualifier edge cases in `dash.ado`/Mata, the rule-8 regression battery, KPI percentiles under brushing) — its parser fixes only matter once the renderer honours what the parser hands it. **Phase 30** items 3, 7 and 8 (the help text can only describe per-plot semantics once they exist). **Phase 8** (parity corpus widening) inherits the server-mode cases this phase creates. |
| **Coordinates with** | **Phases 5–8** (server unification, task 15-03). Items 2, 5 and 6 edit emitted source that 15-03 intends to delete and replace with `_DASH_MAPPER` delegation — see *Risks and sequencing notes*. |

---

## Why this phase exists

Everything in this section is copied from `REMAINING.md`, which states that
every number in it was produced by running the code, not read off a changelog.

### It is one of the five things standing between the branch and "finished"

From the audit's headline list:

> 5. **A per-plot `if` qualifier is silently ignored by every computed layer.**
>    `(lfit mpg weight if foreign==1)` draws the *all-rows* fit. Wrong numbers,
>    no warning.

And from the suggested order:

> 0. **Per-plot `if` on computed layers (§5).** Wrong numbers outrank everything
>    else. Compute the layer from the qualified frame, then view it.

### §5 of the audit — the blocker, in full

> `dash (scatter mpg weight) (lfit mpg weight if foreign==1)` draws the fit for
> **all 74 cars**, not the 22 foreign ones. Measured, with the key `dash.ado`
> actually emits (`if_expr`, written at `dash.ado:1240` and `:1244`, read at
> `dash_render.py:9951`):
>
> | layer | per-plot `if_expr` |
> |---|---|
> | `lfit` | **ignored** — identical y to the unqualified fit |
> | `qfit` | **ignored** |
> | `kdensity` | **ignored** |
>
> Ground truth for that command, from Stata:
>
> ```
> regress mpg weight if foreign==1   ->  slope -.01042596, intercept 48.918297
> regress mpg weight                 ->  slope -.00600869, intercept 39.440284
> ```
>
> dash draws the second.
>
> **Why.** The qualifier is implemented as a `CDSView`/`BooleanFilter` over the
> graph's shared `ColumnDataSource` (`dash_render.py:9957-9990`). That correctly
> restricts which *rows of that source* a glyph draws — but a computed layer
> builds its **own** source from `self.df`, unfiltered, and the view never
> touches it. The comment there explains at length why a CDSView was chosen over
> a private source (`link()` and the filter callback only reach shared sources);
> the reasoning is sound for raw-data layers and simply does not carry to
> computed ones.
>
> A single-plot command is unaffected: `dash.ado:1483` promotes a lone segment's
> qualifier to the graph level, where `_apply_graph_filter` does filter the data.
> The defect is specific to per-plot qualifiers in multi-layer commands — which
> is ordinary `twoway` usage.
>
> This is the worst-shaped defect in the list: a statistical command that
> returns a confidently wrong number, silently. Under project rule 8 it needs a
> failing regression test before the fix.

### Appendix A, task 06-06 — the per-layer measurement

> **The Stata half is done.** `dash.ado:1496` promotes a qualifier to graph level
> only `if n_segs == 1`, with a comment naming the exact bug the task described.
> Per-plot qualifiers survive on their plots.
>
> **The Python half applies to raw-data layers only, and not to all of those.**
> Measured by rendering `scatter/line/... mpg weight` with and without
> `if_expr: "foreign==1"` and inspecting each renderer's `view.filter.booleans`
> and its source data:
>
> | layer | behaviour |
> |---|---|
> | `scatter` `bar` `spike` | correct — `CDSView` + `BooleanFilter` |
> | `line` `connected` | view attached, but Bokeh raises **E-1024 `CDSVIEW_FILTERS_WITH_CONNECTED`** — filters do not apply to connected-topology glyphs, so the qualifier is **inert at runtime** and the document carries a validation error |
> | `area` | **no view attached at all** — qualifier silently dropped |
> | 12 computed layers | **ignored entirely** |
>
> The 12: `lfit` `qfit` `lfitci` `qfitci` `fpfit` `fpfitci` `lpoly` `lpolyci`
> `mband` `mspline` `histogram` `kdensity`. Each builds its own
> `ColumnDataSource` from unfiltered `self.df`, and a view over the *graph's*
> source never reaches it. Ground truth for the simplest case:
>
> ```
> regress mpg weight if foreign==1   ->  slope -.01042596
> regress mpg weight                 ->  slope -.00600869   <- what dash draws
> ```
>
> `in_expr` has the identical shape (`scatter` viewed, `lfit`/`histogram`
> ignored).
>
> **Remaining:**
> 1. Compute every computed layer from the qualified frame, then view it — the
>    fit must be re-estimated on the subset, not filtered after the fact.
> 2. Give `area` the view it never gets.
> 3. Replace the view with a per-layer source for `line`/`connected`, or accept
>    the E-1024 and pre-filter those two — either way the validation error must
>    go and the qualifier must bite.
> 4. Server: `_apply_graph_filter` has **0** occurrences in the emitted app, so
>    none of this exists there.
> 5. The task's explicit test — "`(scatter y x) (scatter y x if foreign)` filters
>    only the second plot; linking still propagates through a qualified plot" —
>    needs to cover a computed layer, which is where it fails.

### What the adversarial pass added

06-06 is one of the 17 DONE claims the adversarial pass overturned, and the
only one it graded **large**:

> | 06-06 | **large** — per-plot `if`/`in` is not applied where a CDSView cannot carry it: every computed glyph (`lfit`, `qfit`, `lowess`, `mband`, `histogram`, `kdensity`) computes from unqualified rows |

> Two of these are functional, not paperwork, and belong beside the four
> blockers: **06-06** (computed layers ignore `if`/`in`) and **13-04**
> (percentile KPIs wrong under brushing).

The backlog arithmetic for the task:

> | task | Appendix B | Appendix C | total |
> |---|---:|---:|---:|
> | 06-06 Per-plot `if`/`in` | 7 | 12 | **19** |

Nothing in the 06-06 backlog was refuted. The audit records that the only
three refutations in the whole adversarial pass were against 11-04 and 09-07.

### The code as it stands today

`DashRenderer._make_figure_body`, `dash_render.py:9951-9998`, confirmed at HEAD.
This is the whole of the per-plot qualifier implementation:

```python
            _p_if = (plot.get("if_expr") or "").strip()
            _p_in = (plot.get("in_expr") or "").strip()
            _g_if = (graph_spec.get("if_expr") or "").strip()
            _g_in = (graph_spec.get("in_expr") or "").strip()
            source_for_plot = source
            _plot_view = facet_view
            if (_p_if and _p_if != _g_if) or (_p_in and _p_in != _g_in):
                try:
                    # _apply_graph_filter filters self.df, so restrict to the
                    # rows this source actually carries afterwards -- a faceted
                    # or already-qualified source is a subset of self.df.
                    _pdf = self._apply_graph_filter(
                        {"if_expr": _p_if, "in_expr": _p_in}
                    )
                    # A CDSView over the source the graph already draws from,
                    # NOT a ColumnDataSource of its own. ...
                    _ids = list(source.data.get(_ROW_ID_COLUMN, []))
                    if not _ids:
                        raise ValueError("source carries no row identity")
                    _pos = {idx: i for i, idx in enumerate(self.df.index)}
                    _wanted = {_pos.get(i, -1) for i in _pdf.index}
                    _mask = [bool(r in _wanted) for r in _ids]
                    # Intersect with a view already on this layer -- a facet
                    # panel, or a linked graph's own qualifier -- rather than
                    # replacing it and losing that restriction.
                    _prev = (getattr(facet_view, "filter", None)
                             if facet_view is not None else None)
                    _prev_bools = getattr(_prev, "booleans", None)
                    if _prev_bools is not None and len(_prev_bools) == len(_mask):
                        _mask = [bool(a and b)
                                 for a, b in zip(_prev_bools, _mask)]
                    _pf = BooleanFilter(booleans=_mask)
                    _plot_view = CDSView(filter=_pf)
                    self._register_view_filter(
                        source, _pf, self._row_ids_for(_pdf))
                except Exception as _pexc:          # never lose the layer
                    warnings.warn(
                        f"dash: per-plot qualifier on layer {pi + 1} could not "
                        f"be applied ({_pexc}); the layer is drawn unfiltered.",
                        stacklevel=2,
                    )
```

Three things follow from this block, and they are the shape of the whole phase:

1. The **only** artefact the qualifier produces is `_plot_view`, a `CDSView`.
   Anything that does not read a `CDSView` — a computed layer that builds its
   own `ColumnDataSource`, a `LabelSet` (which has no `view` property at all), a
   connected-topology glyph (which Bokeh refuses to filter), a browser-side
   aggregate recompute, the entire generated server app — never sees the
   restriction. Epics A and C.
2. The mask `_mask` is *intersected* with a prior facet/linked view, but the
   ids registered on the next line are `self._row_ids_for(_pdf)` — the
   qualifier's own rows, not the intersection. The filter callback rebuilds the
   `BooleanFilter` from those ids, so the intersection is thrown away on the
   first widget move. Epic B, item 7.
3. The failure path is a `warnings.warn` that draws the layer unfiltered. That
   contract — *never lose the layer* — must be preserved by every change in this
   phase, but "drawn unfiltered" must become a **visible warning about a real
   impossibility**, not the silent default it effectively is today.

And for the server renderer, from §4 of the audit — the reason item 5 exists:

> **The collapse is 1/46 done.** `ServerAppBuilder` holds **51 `ptype ==`
> comparisons** across ~4,000 emitted lines; exactly **one** (`scatter`)
> delegates to `_DASH_MAPPER`. 39 `map_*` methods exist.

So a fix threaded through `GlyphMapper` reaches exactly one server-mode plot
type. Every computed layer in the emitted app goes through a module-level
`_compute_*` helper on the graph-level dataframe instead.

---

## Epics

| Epic | Goal | Items |
|---|---|---|
| **A — Make the qualifier reach the glyph** | A qualified layer is computed from the qualified rows, and every mark that layer draws (line, band, bins, density, marker labels) respects it, in both renderers on first paint. | 1, 3, 4, 8 |
| **B — Make the restriction survive interaction** | Once drawn correctly, the layer stays correct after a filter widget moves, a brush is dragged, a link fires, or the layer keeps a private source. | 7, 9, 10 |
| **C — Teach the generated server app about per-plot qualifiers** | `dash serve` / `dash build, server` applies per-plot `if`/`in` at first paint, inside `by()` panels, and after every filter callback — at all fifteen-plus emitted `_compute_*` call sites. | 2, 5, 6 |

Epic A is the correctness floor. Epic B is what keeps it true in an interactive
document. Epic C is the same guarantee in the other renderer, and it is the
largest of the three because the emitted app duplicates the work instead of
delegating it.

---

## User stories

### Epic A — Make the qualifier reach the glyph

**US-A1.** *As a Stata user pasting a `twoway` command, I want
`dash (scatter mpg weight) (lfit mpg weight if foreign==1)` to draw the fit
estimated on foreign cars only, so that the number on the screen is the number
`regress mpg weight if foreign==1` would give me.*

- **Given** `auto.dta` and the command above,
  **when** I run `dash build`,
  **then** the rendered `lfit` layer's endpoints imply slope `-.01042596` and
  intercept `48.918297` (to rendering tolerance), **not** slope `-.00600869`
  and intercept `39.440284`.
- **Given** the same command,
  **when** I inspect the unqualified `scatter` layer,
  **then** it still draws all 74 observations — the qualifier binds to the plot
  it was written on and to no other.
- **Given** any of the 14 affected layer types (`lfit` `qfit` `lfitci` `qfitci`
  `lowess` `lpoly` `lpolyci` `fpfit` `fpfitci` `histogram` `kdensity` `mspline`
  `mband` `area`) with a per-plot `if`,
  **when** I render,
  **then** the layer's data matches the same computation run on the qualified
  subsample, and `area` has a view where today it has none.
- **Given** a per-plot `in 1/20` instead of an `if`,
  **when** I render,
  **then** the behaviour is identical — `in_expr` has the same shape as
  `if_expr` and is fixed by the same code path.

**US-A2.** *As a Stata user, I want a qualifier I write on a layer that
structurally cannot carry one to tell me so, so that I do not ship a dashboard
with a confidently wrong number in it.*

- **Given** `(scatteri 20 3000 "label")`, `(pci 20 2000 30 4000)` or
  `(function y = x^2)` carrying a per-plot `if`,
  **when** I render,
  **then** dash emits a named warning identifying the layer number and type and
  stating that inline-coordinate / analytic layers cannot be qualified, and the
  layer still draws (the "never lose the layer" contract holds).
- **Given** a per-plot `if` on `line`, `connected`, `tsline`, `rline` or
  `rconnected`,
  **when** I render,
  **then** the browser draws the restricted line — and the document contains
  **no** Bokeh E-1024 `CDSVIEW_FILTERS_WITH_CONNECTED` validation error.

**US-A3.** *As a dashboard viewer, I want marker labels to appear only on the
observations the layer actually drew, so that a filtered scatter does not carry
74 labels over 22 points.*

- **Given** `(scatter mpg weight if foreign==1, mlabel(make))`,
  **when** I open the dashboard,
  **then** the `LabelSet` carries exactly the qualified rows' labels.
- **Given** the same layer with `colorvar()`,
  **when** I open the dashboard,
  **then** the colour range is computed from the qualified rows, not from the
  whole source.

### Epic B — Make the restriction survive interaction

**US-B1.** *As a dashboard viewer, I want moving a filter widget to narrow what
I see without silently widening a qualified layer, so that the first interaction
does not undo the command's meaning.*

- **Given** a linked `by()` dashboard where one panel's layer carries a
  per-plot qualifier,
  **when** I move any filter widget,
  **then** the layer still shows only the intersection of (widget selection ∩
  panel rows ∩ qualifier rows) — the panel restriction is not dropped.
- **Given** a `histogram` or `kdensity` layer with a per-plot qualifier,
  **when** I move a filter widget,
  **then** the bins/density are recomputed from rows that satisfy both the
  widget and the qualifier.

**US-B2.** *As a Stata user, I want `jitter()` and a per-plot qualifier to
compose, so that a common cosmetic option does not corrupt which rows are
masked.*

- **Given** `(scatter mpg weight if foreign==1, jitter(5))` in a dashboard that
  also has a filter widget,
  **when** I move that widget,
  **then** the mask still lands on the intended rows — no length mismatch
  between the jittered source and the rebuilt `BooleanFilter`, and no
  off-by-rows shift in which points are hidden.

### Epic C — Teach the generated server app about per-plot qualifiers

**US-C1.** *As a `dash serve` operator, I want the served dashboard to draw the
same layers as the standalone HTML built from the same spec, so that "server
mode" is a delivery choice and not a different product.*

- **Given** a spec with a per-plot `if` on any computed layer,
  **when** the app is built by `ServerAppBuilder` and first painted,
  **then** each `_compute_*` helper receives a dataframe restricted by that
  layer's mask, and the resulting glyph data equals the standalone renderer's
  for the same spec.
- **Given** the same spec under `by()`,
  **when** the served app builds its facets,
  **then** every panel applies the per-plot qualifier as well as the facet
  restriction.
- **Given** the same served dashboard,
  **when** the viewer moves a filter widget and the callback re-renders,
  **then** the per-plot qualifier is reapplied — it is not correct-on-first-paint
  and gone thereafter.
- **Given** a brushed selection on a served dashboard with a qualified
  aggregate layer,
  **when** the brush recompute runs,
  **then** the brushed subset is **intersected** with the per-plot mask, not
  replaced by it.

**US-C2.** *As a package maintainer, I want the two renderers' per-plot
qualifier behaviour pinned by a parity case, so that the next edit to the
emitted app cannot silently re-introduce the divergence.*

- **Given** the parity corpus,
  **when** it runs,
  **then** it contains at least one per-plot-qualified computed layer, and it
  fails if either renderer drops the restriction.

---

## Business requirements

Each is stated so that a single test can decide it.

| ID | Requirement |
|---|---|
| **BR-01.1** | A per-plot `if`/`in` qualifier restricts the rows used to **compute** a statistical layer, not merely the rows drawn from a shared source. The fit/band/bins/density must equal the same computation performed on the qualified subsample. |
| **BR-01.2** | The reference case is decided by Stata's own numbers: for `(lfit mpg weight if foreign==1)` the drawn line must imply slope `-.01042596` / intercept `48.918297`, and must not imply slope `-.00600869` / intercept `39.440284`. |
| **BR-01.3** | A qualifier binds to the plot it was written on and to no other plot in the same command. An unqualified sibling layer keeps all rows. |
| **BR-01.4** | `in_expr` is honoured identically to `if_expr` everywhere `if_expr` is honoured. |
| **BR-01.5** | Every mark a qualified layer draws — glyph, confidence band, marker label, colour mapping — reflects the same row set. No mark may be drawn for a row the layer excluded. |
| **BR-01.6** | A layer type that cannot honour a qualifier (`scatteri`, `pci`, `function`) must say so with a warning naming the layer, and must still be drawn. Silence is not an acceptable outcome. |
| **BR-01.7** | A rendered document must contain no Bokeh validation error caused by dash's own qualifier mechanism; specifically, E-1024 `CDSVIEW_FILTERS_WITH_CONNECTED` must not appear for `line`, `connected`, `tsline`, `rline` or `rconnected`. |
| **BR-01.8** | A qualifier must compose with, and never replace, a restriction already on the layer: a `by()` panel, a `link()`ed graph's graph-level qualifier, and a filter widget's selection. The result is the intersection. |
| **BR-01.9** | Correctness must survive interaction: after any filter-widget move or brush, every qualified layer shows the intersection of widget selection and qualifier rows. |
| **BR-01.10** | Server mode (`dash serve`, `dash build, server`) must produce the same qualified layers as standalone mode for the same spec — at first paint, inside `by()` panels, and after every callback re-render. |
| **BR-01.11** | `link()` must keep working through a qualified layer. The existing shared-source/`CDSView` design was chosen precisely so that a qualified layer stays inside `link()` and inside the filter callback; no fix in this phase may move a qualifiable raw-data layer onto a private source that `link()` cannot reach. |
| **BR-01.12** | No qualifier failure may drop a layer. The existing contract at `dash_render.py:9993-9998` — warn and draw unfiltered — is preserved, and the warning text must remain specific enough to identify the layer (`layer {pi + 1}`). |
| **BR-01.13** | Under project rule 8, each defect above is pinned by a regression test written **before** its fix, which fails on the pre-fix tree and passes after. |

---

## Technical requirements

Line numbers are `REMAINING.md`'s, which the audit states are current for the
~16,000-line `dash_render.py` (the plan's own section files are stale). Symbols
named below were re-confirmed to exist at HEAD.

### Epic A

**TR-01.1 — Thread the row mask into the mapper API.**
`DashRenderer._make_figure_body` already computes the layer's mask at
`dash_render.py:9987` as `_mask`, a `list[bool]` aligned positionally to the
source's `_ROW_ID_COLUMN` (`__dash_row__`) column, then wraps it in
`BooleanFilter(booleans=_mask)` at `:9988`. That list is the mask to thread.
Add an explicit `mask=None` keyword to `DashRenderer._add_glyph`
(`dash_render.py:10334`, whose signature today is
`(self, fig, source, plot_type, yvar, xvar, options, y2var="", view=None, color_idx=0)`)
and to each mapper below, and pass `_mask` from the per-plot block. Deriving
the mask from `view.filter.booleans` inside the mapper is acceptable as long as
the layer also works when a facet/linked view is present, because in that case
`_mask` is already the intersection (`:9981-9989`).

**TR-01.2 — Subset before computing, in all 14 mappers.** Each method listed
must subset `source.data[xvar]` and `source.data[yvar]` (and any weight,
`y2var` or CI-bearing column it reads) by the mask **before** fitting, smoothing
or binning. The fit must be re-estimated on the subset, not filtered after the
fact.

| mapper | line | what must be recomputed on the subset |
|---|---:|---|
| `map_lfit` | 3821 | OLS coefficients (`numpy.polyfit`) and the fit grid |
| `map_qfit` | 3873 | quadratic coefficients and grid |
| `map_lfitci` | 3918 | coefficients **and** the CI band |
| `map_qfitci` | 3998 | coefficients **and** the CI band |
| `map_lowess` | 4091 | the smoother input |
| `map_lpoly` | 4272 | the local-polynomial input and bandwidth |
| `map_lpolyci` | 4344 | as `map_lpoly`, plus the band |
| `map_fpfit` | 4517 | fractional-polynomial fit |
| `map_fpfitci` | 4569 | fit **and** band |
| `map_histogram` | 4636 | bin counts (and bin edges, if data-derived) |
| `map_kdensity` | 4806 | density and its evaluation grid |
| `map_mspline` | 5912 | spline knots/values |
| `map_mband` | 5983 | band medians |
| `map_area` | 3592 | *and* attach the view it never gets today (Appendix A remaining item 2) |

**TR-01.3 — Make the non-qualifiable layers explicit.** `map_scatteri` (5370),
`map_pci_literal` (5548) and `map_function` (6065) take no `view` parameter at
all. Decide — and document in code and in the warning — that
inline-coordinate and analytic layers cannot be qualified, rather than leaving
it silent. Mechanism: in the per-plot block, before building the view, check
the plot type against a module-level frozenset of non-qualifiable types and
`warnings.warn` naming the layer index and type, in the same style as the
existing `:9994-9998` warning.

**TR-01.4 — Resolve the connected-topology case.** A `BooleanFilter` `CDSView`
on a Bokeh `Line` is rejected with **E-1024 `CDSVIEW_FILTERS_WITH_CONNECTED`**
and is not honoured by BokehJS, so the browser draws the unfiltered line.
Affected mappers: `map_line` (3486), `map_connected` (3560), `map_tsline`
(5805), `map_rline` (5106), `map_rconnected` (5147); construction site
`dash_render.py:9956-9997`. Three admissible resolutions, in preference order:

1. **NaN-break a masked copy of the columns** on the shared source — keeps the
   layer inside `link()` and inside the filter callback (BR-01.11) and removes
   the view entirely, so E-1024 cannot arise. Preferred.
2. **A pre-filtered private source when the graph is not linked**, falling back
   to (1) when it is. Acceptable, but doubles the code paths.
3. **Report the limitation** with a named warning, as in TR-01.3. Acceptable
   only if (1) and (2) are shown not to work; it leaves BR-01.7 satisfied
   (no E-1024, because no view is attached) but not BR-01.5.

Whichever is chosen, the E-1024 must be gone from the emitted document.

**TR-01.5 — Mask the `mlabel` `LabelSet`.** `_apply_mlabel_opts`
(`dash_render.py:3301-3400`) attaches a Bokeh `LabelSet`, which has **no `view`
property**, so a per-plot qualifier can never reach it. Nine mappers call it
with an unmasked source: `dash_render.py:3482` (`map_scatter`, note it passes
`plot_source`, the possibly-jittered copy), 3556, 3589, 3657, 3762, 3814, 4955,
5000, 5038 — scatter/line/connected/area/bar/spike plus the rbar/rspike/rcap
family. Fix by constructing the `LabelSet` over a masked **copy** of the label
columns. While here, re-check `_apply_colorvar`, whose colour range is computed
from the unmasked source and therefore maps colours against rows the layer does
not draw. The emitted server app has its own LabelSet sites — `dash_render.py:
14454, 14484, 14502, 14532, 14552, 14585, 14655, 14925` — which need the same
treatment once Epic C lands.

**TR-01.6 — Linked graphs and linked `by()` panels.** Because the mappers
ignore `view`, any restriction carried as a `CDSView` rather than as a shortened
source is invisible to a computed layer. That set now includes two restrictions
the user never wrote on the plot: a LINKED graph's **graph-level** qualifier
(`_linked_graph_views`, `dash_render.py:11500-11505`) and every panel of a
LINKED `by()` graph (`dash_render.py:11465-11476`, `panel_view_r`), both inside
`DashRenderer._build_figures` (~11458-11510). TR-01.1/TR-01.2 fix the
mechanism; this case needs its own test because it is a **silent behaviour
change caused by an unrelated option** — adding `link()` to a working dashboard
changes the numbers in a computed layer.

### Epic B

**TR-01.7 — Register the intersected row set.** The per-plot block intersects
with a prior view at `dash_render.py:9981-9989` but registers the view with
`self._row_ids_for(_pdf)` at `:9991-9992` — the qualifier's own rows only.
`_register_view_filter` (`dash_render.py:8509-8524`) stores
`(source, bool_filter, member_ids)`, and `_FILTER_JS` rebuilds every registered
view from those ids:

```js
vf.filter.booleans = kept.map(id => member.has(id));   // dash_render.py:7164-7170
```

so the first move of any filter widget discards the intersection. The wiring
runs through `_cb.args["view_filters"]` at `dash_render.py:11892`. Fix by
passing the **intersected** ids to `_register_view_filter`, or by registering
the prior view's ids alongside and intersecting in JS. This only bites when the
source is SHARED — a linked `by()` panel and a linked graph's own graph-level
qualifier — because in the unlinked case the panel source is itself the subset;
the test must therefore be written on a linked dashboard.

**TR-01.8 — Reconcile the view's source with the glyph's source under
`jitter()`.** `map_scatter` draws from the copy returned by
`_build_jitter_source` (`dash_render.py:2521-2570`, called at `:3459`) while
`_register_view_filter` was handed the GRAPH source at `:9991`. The copy is not
in `self.sources`, so it is never passed as `all_graph_sources`
(`dash_render.py:11880-11893`) and never shortened by the filter callback.
After any widget move the rebuilt `BooleanFilter` has the **kept-row** length
while the glyph's source still has the **original** length, and the mask lands
on the wrong rows. Two admissible fixes: register the view against the source
the glyph really uses **and** add that source to the callback's list, or jitter
in place on the shared source. The second keeps one source per graph and is
cheaper to reason about; the first is closer to the current structure.

**TR-01.9 — Give the browser-side aggregate recompute a row restriction.**
`_dash_agg_config` is built at `dash_render.py:4695` (histogram) and `:4905`
(kdensity) and carries only `type` / `varname` / `bin_edges` / `ymode`. The
filter callback recomputes bins and densities from `new_data`
(`dash_render.py:7389-7430`), and `new_data` is built from `orig_source` masked
**only** by the widget values (`dash_render.py:7097-7102`). So a per-plot
qualifier on a `histogram`/`kdensity` layer would be correct on first paint and
regress on the first filter move even after TR-01.1/TR-01.2 land. Add the
layer's member row ids to the agg config — the same shape as `view_filters` —
and intersect in JS. Collection point: `dash_render.py:12203-12209`
(`agg_source_registry`, which gathers `(_r._dash_agg_source,
dict(_r._dash_agg_config))`); argument wiring:
`dash_render.py:11905-11914` (`agg_sources` / `agg_configs_json`). **The
graph-level qualifier shares this defect today, so one fix covers both.**

### Epic C

**TR-01.10 — Read per-plot keys in the emitted plot loop.**
`ServerAppBuilder._generate_app_source` (`dash_render.py:12740`; the class
begins at `:12265`, and everything after it is emitted-app source) emits a plot
loop — `for pi, plot in enumerate(plots):` at `dash_render.py:14030` — that
never consults `plot['if_expr']` / `plot['in_expr']`. Only the graph-level keys
are read, emitted at `dash_render.py:13812` / `:13819` as
`go.get('if_expr') or g.get('if_expr')` inside the per-graph filter block
(~13808-13824). Emit the same per-plot mask + `CDSView` the standalone path
builds, reusing the app's already-emitted `_stata_if_to_pandas`
(`dash_render.py:6852`, forwarded into the generated module) and its `_safe_g`
validator. Note the emitted app expands `~=` to `!=` before translating
(`_stata_if_to_pandas(_g_if.replace('~=', '!='))`, `dash_render.py:13821`) —
the per-plot path must do the same.

**TR-01.11 — Apply the mask at every emitted `_compute_*` call site.** This is
the requirement the auditor's own renderer note got wrong, and the audit says
so explicitly: threading the mask through `GlyphMapper` does **not** reach
server mode for computed layers, because the generated app never calls
`GlyphMapper` for them. Only `scatter` routes through `_DASH_MAPPER.map_scatter`
(emitted at `dash_render.py:14090`). Everything else calls a module-level
helper on the **graph-level** dataframe: `_compute_lfit(g_df, ...)`,
`_compute_qfit`, `_compute_lfitci`, `_compute_qfitci`, `_compute_lowess`,
`_compute_lpoly`, `_compute_lpolyci`, `_compute_fpfit`, `_compute_histogram`,
`_compute_kdensity`, `_compute_mspline`, `_compute_mband`, `_compute_rscatter`,
`_compute_pcscatter`. The helper definitions run from `_compute_lfit`
(`dash_render.py:13212`) through `_compute_lpolyci` (`:13605`). The mask must
be applied to the frame at **three** groups of sites:

| site group | emitted lines | frame |
|---|---|---|
| main plot loop | 14108, 14121, 14145, 14180, 14193, 14212, 14227, 14242, 14254, 14376, 14403, 14745, 14757, 14773, 14799 | `g_df` |
| the two facet/`by()` paths | 15154-15187 and 15255-15288 | `_fac_gdf`, `work_df` |
| brush/filter recompute rebuilding `agg['source'].data` | 15605-15633 | `agg_fdf` |

The third must **intersect** the brushed subset with the per-plot mask, not
replace it.

**TR-01.12 — Thread the qualifier into the three further emitted state
sites.** Beyond the per-graph filter block and the plot loop, the generated app
reads qualifiers at three more places, all graph-level only:

- **(a)** `_graph_qualifiers` is built from `go.get('if_expr') or
  g.get('if_expr')` at ~`15007-15014` (the emitted line at `dash_render.py:15007`
  is `_graph_qualifiers = {}  # gname → {'if_expr': ..., 'in_expr': ...}`) and
  is the **only** qualifier state the filter callback can see. Re-key it by
  `gname` **plus plot index**.
- **(b)** the `by()`-facet frame `_by_q_df` is restricted by `_by_in` / `_by_if`
  at ~`15040-15058` with no per-plot consultation.
- **(c)** the filter-callback re-render reapplies `_qual_cb.get('if_expr')` from
  `_gquals` at ~`15523-15560`.

A per-plot mask added only at the plot loop would be **correct on first paint
and then silently dropped on the first filter move**, and would never reach any
`by()` panel of a served dashboard.

**TR-01.13 — Server-side marker labels.** Once the emitted app reads per-plot
qualifiers at all, its own `LabelSet` sites (`dash_render.py:14454, 14484,
14502, 14532, 14552, 14585, 14655, 14925`) need TR-01.5's treatment.

### Cross-cutting

**TR-01.14 — Preserve the failure contract.** Every new code path in the
per-plot block stays inside the existing `try/except` at `dash_render.py:9993`,
which warns (`"dash: per-plot qualifier on layer {pi + 1} could not be applied
({_pexc}); the layer is drawn unfiltered."`) rather than losing the layer. New
warnings added under TR-01.3/TR-01.4 follow the same format so that a user can
always identify the layer by index.

**TR-01.15 — Do not regress `link()`.** The design comment at
`dash_render.py:9964-9973` records the measurement behind the CDSView choice:
on `link(_all)` with two graphs, a layer on a private source had its own source
while the other two shared one, putting it outside both `link()` and the filter
callback. Any private-source resolution chosen under TR-01.4 or TR-01.8 must be
guarded by a test that `link()` still propagates through the qualified layer.

---

## Work items

All ten items, numbered exactly as the phase's item list gives them. Tags are
`[kind · renderer · effort]`.

---

**Item 1 — [functional · both · medium] — Make every computed glyph honour the
per-plot view.**

Thread the layer's row mask (the `BooleanFilter.booleans` built at
`dash_render.py:9987`, or an explicit `mask=` kwarg from
`DashRenderer._add_glyph`) into the 14 `GlyphMapper.map_*` methods that
currently accept `view=` and never reference it, and subset
`source.data[xvar]` / `[yvar]` by that mask before fitting/binning. Affected:
`map_lfit` (3821), `map_qfit` (3873), `map_lfitci` (3918), `map_qfitci` (3998),
`map_lowess` (4091), `map_lpoly` (4272), `map_lpolyci` (4344), `map_fpfit`
(4517), `map_fpfitci` (4569), `map_histogram` (4636), `map_kdensity` (4806),
`map_mspline` (5912), `map_mband` (5983), and `map_area` (3592).
`map_scatteri` (5370), `map_pci_literal` (5548) and `map_function` (6065) take
no `view` parameter at all — decide and document that inline-coordinate /
analytic layers cannot be qualified rather than leaving it silent.

*Where:* `dash_render.py:GlyphMapper.map_lfit/map_qfit/map_lfitci/map_qfitci/map_lowess/map_lpoly/map_lpolyci/map_fpfit/map_fpfitci/map_histogram/map_kdensity/map_mspline/map_mband/map_area`;
`dash_render.py:DashRenderer._add_glyph (10334)`;
`dash_render.py:DashRenderer._make_figure_body (9926-10010)`

*Evidence:* Appendix A's per-layer table — "12 computed layers · **ignored
entirely**", `area` · "**no view attached at all** — qualifier silently
dropped". Ground truth: `regress mpg weight if foreign==1` → slope
`-.01042596`; `regress mpg weight` → slope `-.00600869` ← what dash draws.
Confirmed at HEAD: `map_lfit`'s signature is
`(self, fig, source, yvar, xvar, options, view=None, color_idx=0)` — `view` is
accepted and never referenced.

*Requirements:* TR-01.1, TR-01.2, TR-01.3 · BR-01.1, BR-01.2, BR-01.4, BR-01.6

---

**Item 2 — [functional · server · medium] — Teach the generated `bokeh serve`
app to read per-plot qualifiers.**

`ServerAppBuilder._generate_app_source` emits a plot loop
(`for pi, plot in enumerate(plots):`, `dash_render.py:14030`) that never
consults `plot['if_expr']` / `plot['in_expr']`; only the graph-level keys are
read (emitted at `dash_render.py:13812`/`13819` as
`go.get('if_expr') or g.get('if_expr')`). Emit the same per-plot mask + CDSView
the standalone path builds, using the app's already-emitted
`_stata_if_to_pandas` and `_safe_g` validator.

*Where:* `dash_render.py:ServerAppBuilder._generate_app_source (12740)`,
emitted per-graph filter block ~`13808-13824`, emitted plot loop ~`14030`

*Evidence:* Appendix A remaining item 4 — "Server: `_apply_graph_filter` has
**0** occurrences in the emitted app, so none of this exists there."

*Requirements:* TR-01.10 · BR-01.10

---

**Item 3 — [functional · standalone · small] — Fix computed layers under
`link()` and under linked `by()`.**

Because the mappers ignore `view`, any restriction carried as a CDSView rather
than as a shortened source is invisible to them — which now includes the
graph-level qualifier of a LINKED graph (`_linked_graph_views`,
`dash_render.py:11500-11505`) and every panel of a LINKED `by()` graph
(`dash_render.py:11465-11476`). The mask-threading fix above is the same fix,
but this case needs its own test because it is a silent behaviour change caused
by an unrelated option.

*Where:* `dash_render.py:DashRenderer._build_figures ~11458-11510` (linked
`by()` `panel_view_r`, `_linked_graph_views`); same `GlyphMapper` methods as
item 1

*Evidence:* the restriction reaches the layer only as a `CDSView`; the mapper
never reads it. Adding `link()` to a working dashboard therefore changes a
computed layer's numbers with no diagnostic.

*Requirements:* TR-01.6 · BR-01.8, BR-01.11

---

**Item 4 — [functional · standalone · medium] — Decide what a per-plot
qualifier means for connected-topology glyphs.**

A per-plot `if` on `line`, `connected`, `tsline`, `rline` or `rconnected`
attaches a BooleanFilter CDSView to a Bokeh Line glyph, which Bokeh rejects
(E-1024 `CDSVIEW_FILTERS_WITH_CONNECTED`) and BokehJS does not honour, so the
browser draws the unfiltered line. Either give those types a pre-filtered
private source when the graph is not linked, or insert NaN breaks in a masked
copy of the columns, or report the limitation.

*Where:* `dash_render.py:DashRenderer._make_figure_body (9956-9997)`;
`dash_render.py:GlyphMapper.map_line (3486), map_connected (3560), map_tsline
(5805), map_rline (5106), map_rconnected (5147)`

*Evidence:* Appendix A — "`line` `connected`: view attached, but Bokeh raises
**E-1024 `CDSVIEW_FILTERS_WITH_CONNECTED`** — filters do not apply to
connected-topology glyphs, so the qualifier is **inert at runtime** and the
document carries a validation error."

*Requirements:* TR-01.4 · BR-01.7, BR-01.11

---

**Item 5 — [functional · server · medium] — Correct the scope of the
server-mode fix.**

Threading the mask through GlyphMapper does NOT reach server mode for computed
layers, because the generated app never calls GlyphMapper for them. The emitted
plot loop calls standalone module-level helpers `_compute_lfit(g_df, ...)`,
`_compute_qfit`, `_compute_lfitci`, `_compute_qfitci`, `_compute_lowess`,
`_compute_lpoly`, `_compute_lpolyci`, `_compute_fpfit`, `_compute_histogram`,
`_compute_kdensity`, `_compute_mspline`, `_compute_mband`, `_compute_rscatter`,
`_compute_pcscatter` on the GRAPH-level dataframe. Only `scatter` routes
through `_DASH_MAPPER.map_scatter` (emitted at `dash_render.py:14090`). So the
per-plot row mask must be applied to `g_df` at EVERY `_compute_*` call site in
the emitted source, in three separate places: the main plot loop (emitted at
`dash_render.py:14108, 14121, 14145, 14180, 14193, 14212, 14227, 14242, 14254,
14376, 14403, 14745, 14757, 14773, 14799`), the two facet/`by()` paths
(`_fac_gdf` at `15154-15187` and `work_df` at `15255-15288`), and the
brush/filter recompute path that rebuilds `agg['source'].data` from `agg_fdf`
(`15605-15633`) — which must intersect the brushed subset with the per-plot
mask, not replace it. **The auditor's item-2 renderer_note says this comes "for
free" from the mapper fix; it does not, and planning the work on that
assumption will leave server mode wrong for every computed layer.**

*Where:* `dash_render.py:ServerAppBuilder` emitted plot loop (call sites
`14108-14254, 14376, 14403, 14745-14799`), emitted facet paths (`15154-15187,
15255-15288`), emitted brush recompute (`15605-15633`); emitted helper
definitions `_compute_lfit` (`13212`) through `_compute_lpolyci` (`13605`)

*Evidence:* confirmed at HEAD — `dash_render.py:14108` emits
`"                fit_data = _compute_lfit(g_df, yvar, xvar, opts)"`, `:15159`
emits the `_fac_gdf` form, `:15260` the `work_df` form and `:15607` the
`agg_fdf` form. §4 of the audit: 51 `ptype ==` comparisons in
`ServerAppBuilder`, exactly one delegating to `_DASH_MAPPER`.

*Requirements:* TR-01.11 · BR-01.10, BR-01.9

---

**Item 6 — [functional · server · medium] — The server-mode fix has three more
emitted code sites than the auditor's file list names.**

Beyond the per-graph filter block (~`13808-13824`) and the plot loop (`14030`),
the generated app reads qualifiers at three further places, all graph-level
only: **(a)** `_graph_qualifiers` is built from
`go.get('if_expr') or g.get('if_expr')` at ~`15007-15014` and is the ONLY
qualifier state the filter callback can see, **(b)** the `by()`-facet frame
`_by_q_df` is restricted by `_by_in`/`_by_if` at ~`15045-15058` with no
per-plot consultation, and **(c)** the filter-callback re-render reapplies
`_qual_cb.get('if_expr')` from `_gquals` at ~`15523-15560`. A per-plot mask
added only at the plot loop would be correct on first paint and then silently
dropped on the first filter move, and would never reach any `by()` panel of a
served dashboard. Thread the per-plot qualifier into `_graph_qualifiers` (keyed
by gname + plot index) and into both the facet and callback paths.

*Where:* `dash_render.py:ServerAppBuilder._generate_app_source (12740)`;
emitted `_graph_qualifiers` block ~`15003-15014`; emitted `by()`-facet block
~`15040-15058`; emitted filter-callback requalify block ~`15523-15560`

*Evidence:* confirmed at HEAD — `dash_render.py:15007` emits
`"    _graph_qualifiers = {}  # gname → {'if_expr': ..., 'in_expr': ...}"`,
`:15014` emits `_graph_qualifiers[_gnq] = {'if_expr': _qi, 'in_expr': _qn}`,
`:15054` emits the `_by_px` translation and `:15556` the callback's `_px_cb`.

*Requirements:* TR-01.12 · BR-01.9, BR-01.10

---

**Item 7 — [functional · standalone · small] — Register the INTERSECTED row set
for a per-plot view, not the qualifier's own rows.**

`_make_figure_body` intersects the per-plot mask with an existing facet/linked
view (`dash_render.py:9981-9989`) but then registers the view with
`self._row_ids_for(_pdf)` — the per-plot rows only (`dash_render.py:9991-9992`).
The filter callback rebuilds every registered view from those member ids
(`vf.filter.booleans = kept.map(id => member.has(id))`,
`dash_render.py:7164-7170`), so the first move of any filter widget throws the
intersection away. It only bites when the source is SHARED — a linked `by()`
panel and a linked graph's own graph-level qualifier — because in the unlinked
case the panel source is itself the subset. Pass the intersected ids (or
register the prior view's ids alongside and intersect in JS).

*Where:* `dash_render.py:9981-9992` (`DashRenderer._make_figure_body` per-plot
block), `dash_render.py:8509-8524` (`_register_view_filter`),
`dash_render.py:7163-7170` (`_FILTER_JS` view rebuild), `dash_render.py:11892`
(`_cb.args["view_filters"]`)

*Evidence:* confirmed at HEAD — the block intersects `_prev_bools` with `_mask`
and then calls `self._register_view_filter(source, _pf, self._row_ids_for(_pdf))`.
`_register_view_filter`'s own docstring records the defect class it was written
for: "The filter callback replaces that source's data with fewer rows and never
touched the booleans, so after any filter move each panel masked the wrong
rows."

*Requirements:* TR-01.7 · BR-01.8, BR-01.9

---

**Item 8 — [functional · both · medium] — Mask the `mlabel` `LabelSet` for a
qualified layer.**

`_apply_mlabel_opts` (`dash_render.py:3301`) attaches a Bokeh `LabelSet`, which
has NO `view` property, so a per-plot `if`/`in` never reaches it and every
observation's marker label is drawn over a filtered layer. Nine mappers call it
with an unmasked source (`dash_render.py:3482, 3556, 3589, 3657, 3762, 3814,
4955, 5000, 5038`), i.e. scatter/line/connected/area/bar/spike and the
rbar/rspike/rcap family. Fix by building the LabelSet over a masked copy of the
label columns (and by the same token re-check `_apply_colorvar`, whose colour
range is computed from the unmasked source). The emitted server app has its own
LabelSet sites (`dash_render.py:14454, 14484, 14502, 14532, 14552, 14585,
14655, 14925`) that will need the same treatment once server mode reads
per-plot qualifiers at all.

*Where:* `dash_render.py:3301-3400` (`_apply_mlabel_opts`),
`dash_render.py:3482` (`map_scatter` call),
`dash_render.py:3556/3589/3657/3762/3814/4955/5000/5038`,
`dash_render.py:14454+` (emitted-app LabelSet lines)

*Evidence:* confirmed at HEAD — all nine call sites exist, and `:3482` passes
`plot_source` (the jitter copy), which ties this item to item 9.

*Requirements:* TR-01.5, TR-01.13 · BR-01.5

---

**Item 9 — [functional · standalone · medium] — Make the per-plot view and the
glyph's actual source agree when a layer builds a private source.**

With `jitter()`, `map_scatter` draws from the copy returned by
`_build_jitter_source` (`dash_render.py:2521`, called at `dash_render.py:3459`)
while `_register_view_filter` was handed the GRAPH source
(`dash_render.py:9991`). The copy is not in `self.sources`, so it is never
passed as `all_graph_sources` and never shortened by the filter callback; after
any widget move the rebuilt BooleanFilter has the kept-row length while the
glyph's source still has the original length, and the mask lands on the wrong
rows. Either register the view against the source the glyph really uses (and
add that source to the callback's list), or jitter in place on the shared
source.

*Where:* `dash_render.py:2521-2570` (`_build_jitter_source`),
`dash_render.py:3459-3482` (`map_scatter`), `dash_render.py:9987-9992` (view
construction + registration), `dash_render.py:11880-11893`
(`all_graph_sources` / `view_filters` wiring)

*Evidence:* confirmed at HEAD — `dash_render.py:3459` reads
`plot_source, eff_x, eff_y = self._build_jitter_source(...)`, and the view
registered at `:9991` is over `source`, not `plot_source`.

*Requirements:* TR-01.8, TR-01.15 · BR-01.9, BR-01.11

---

**Item 10 — [functional · standalone · medium] — Give the browser-side
aggregate recompute somewhere to put a row restriction.**

Otherwise `histogram`/`kdensity` per-plot qualifiers will regress on the first
filter move even after the GlyphMapper mask-threading fix lands.
`_dash_agg_config` (`dash_render.py:4695` for histogram, `4905` for kdensity)
carries only type/varname/bin_edges/ymode; the filter callback recomputes bins
and densities from `new_data` (`dash_render.py:7389-7430`), and `new_data` is
built from `orig_source` masked ONLY by the widget values
(`dash_render.py:7097-7102`). Add the layer's member row ids to the agg config
and intersect in JS (the same shape as `view_filters`). Note the graph-level
qualifier shares this defect today, so one fix covers both.

*Where:* `dash_render.py:4695` and `4905` (`_dash_agg_config`),
`dash_render.py:12203-12209` (`agg_source_registry` collection),
`dash_render.py:11905-11914` (`agg_sources` / `agg_configs_json` args),
`dash_render.py:7387-7430` (`_FILTER_JS` aggregate loop),
`dash_render.py:7097-7102` (`new_data`)

*Evidence:* confirmed at HEAD — `r._dash_agg_config = {` at `:4695` and `:4905`;
the registry comprehension at `:12205-12207` collects
`(_r._dash_agg_source, dict(_r._dash_agg_config))`.

*Requirements:* TR-01.9 · BR-01.9

---

## Test plan

Project rule 8 governs the order: **for every item below, the regression test
is written first, is run against the unmodified tree, and must fail there.** A
test that passes before the fix is not evidence. Rule 4 requires a unit test
for every function touched. Each epic's block therefore has four parts: the
failing test, the unit tests, the integration/cscript coverage, and the
mutation that proves the test is not vacuous.

Existing files this phase extends, all present in `test/`:
`test_per_plot_qualifier_linking.py` (classes
`TestALinkedLayerStaysOnTheSharedSource`,
`TestTheUnlinkedCaseIsUnchanged`, `TestItComposesWithAGraphLevelQualifier`,
helper `_render(tmp_path, link, plots, second_graph=True, graph_if="")`),
`test_varlist_expansion.py` (`test_second_plot_if_expr_filters_only_the_second_plot`
at :334, `test_first_plot_if_expr_does_not_leak_onto_later_plots` at :354),
`test_varlist_expansion.cscript` (case V2-11, which checks only the spec JSON,
never a rendered figure), `test_mode_parity.py` (the standalone/server parity
corpus, helpers `_standalone_figures` / `_server_figures` / `_glyph_profile`),
`test_statistical_truth.py`, `test_glyphs.py`, `test_jitter.py`,
`test_filters.py`, `test_linking_filters.py`, `test_kpi_brush.py`,
`test_server_brush.py`, `test_server_statistics.py`, `test_layout_facets.py`,
`test_conformance.cscript`.

One new file is created: **`test/test_per_plot_qualifier_computed.py`**. Put
Epic A's and Epic B's assertions there; Epic C's parity case goes in
`test_mode_parity.py`, beside the corpus it widens.

### Epic A — Make the qualifier reach the glyph

**The failing test, first (rule 8).**
`test/test_per_plot_qualifier_computed.py::test_lfit_with_per_plot_if_is_estimated_on_the_subset`.
Render the spec `(scatter mpg weight) (lfit mpg weight if foreign==1)` against
the `auto` fixture, read the `lfit` renderer's data, and assert the implied
slope is `-.01042596` and intercept `48.918297` within a stated tolerance, and
explicitly assert it is **not** `-.00600869` / `39.440284`. On the unmodified
tree this fails with the unqualified numbers — that failure is the record of
the defect.

**Unit tests (rule 4).** One parametrised test over all 14 mappers named in
TR-01.2, calling each mapper directly with a source and a mask and asserting
the emitted data equals the same computation over the masked subsample. The
parametrisation list *is* the coverage claim: `map_lfit`, `map_qfit`,
`map_lfitci`, `map_qfitci`, `map_lowess`, `map_lpoly`, `map_lpolyci`,
`map_fpfit`, `map_fpfitci`, `map_histogram`, `map_kdensity`, `map_mspline`,
`map_mband`, `map_area`. Add for the band-bearing four (`lfitci`, `qfitci`,
`lpolyci`, `fpfitci`) an assertion that the **band** moved too, not just the
line. Add a mirror test per mapper using `in_expr` instead of `if_expr`
(BR-01.4) — the audit records `in_expr` as measured-working-but-untested for
`scatter` and ignored for `lfit`/`histogram`.

**Non-qualifiable layers.** `test_scatteri_pci_function_warn_when_qualified`:
assert `warnings.warn` fires, names the layer index and type, and that the layer
is still drawn (BR-01.6, BR-01.12).

**Connected topology.** `test_qualified_line_has_no_e1024`: build the document
and assert Bokeh's validation output contains no
`CDSVIEW_FILTERS_WITH_CONNECTED` / E-1024 for `line`, `connected`, `tsline`,
`rline`, `rconnected`, and that the drawn vertex set equals the qualified rows
(or, if resolution 3 of TR-01.4 is chosen, that the documented warning fires and
the help records the limitation — in which case the Phase 30 doc item becomes a
blocking dependency).

**Marker labels.** `test_mlabel_labelset_only_carries_qualified_rows` in
`test_per_plot_qualifier_computed.py`: `(scatter mpg weight if foreign==1,
mlabel(make))` → the `LabelSet` source has 22 rows, not 74. Plus
`test_colorvar_range_uses_qualified_rows` for the `_apply_colorvar` half.

**Integration / cscript.** Extend `test_varlist_expansion.cscript` beside V2-11
with a case that *renders* rather than only inspecting the spec: build the
two-layer command, then assert on the produced HTML/document that the fit
endpoints match the qualified regression. Add the equivalent overlay to
`test_conformance.cscript`'s "every layer drew something" corpus so a qualified
computed layer is part of the standing conformance run.

**Mutation — proof the tests are not vacuous.** For each of the following,
apply the mutation, confirm the named test fails, then revert:

| break this | test that must die |
|---|---|
| drop the `mask` argument in `map_lfit` (compute on the full source again) | `test_lfit_with_per_plot_if_is_estimated_on_the_subset` |
| invert the mask (`[not b for b in mask]`) in the shared subsetting helper | every mapper unit test |
| skip the `LabelSet` masking in `_apply_mlabel_opts` | `test_mlabel_labelset_only_carries_qualified_rows` |
| re-attach the plain `CDSView` on `map_line` | `test_qualified_line_has_no_e1024` |
| silence the non-qualifiable warning | `test_scatteri_pci_function_warn_when_qualified` |

### Epic B — Make the restriction survive interaction

**The failing test, first (rule 8).**
`test/test_per_plot_qualifier_computed.py::test_intersection_survives_a_filter_move`.
Build a **linked** `by()` dashboard whose panel layer carries a per-plot
qualifier, then drive the filter callback's rebuild the way
`test_linking_filters.py` and `test_filters.py` already drive it, and assert the
rebuilt `BooleanFilter.booleans` still equals (panel rows ∩ qualifier rows). On
the unmodified tree this fails, because `_register_view_filter` was handed
`self._row_ids_for(_pdf)` — the qualifier's rows only.

**Unit tests (rule 4).**
- `_register_view_filter` (`:8509`): given a prior view's ids and the
  qualifier's ids, the registered member set is the intersection.
- `_build_jitter_source` (`:2521`): the returned source either *is* the shared
  source (in-place resolution) or is registered in `self.sources` and appears in
  `all_graph_sources` (private-source resolution). Assert whichever invariant
  the implementation picks — this is the test that makes the TR-01.8 decision
  reviewable. Extend `test_jitter.py` with the qualifier composition case.
- `_dash_agg_config` (`:4695`, `:4905`): the emitted dict now carries the
  layer's member row ids, with the same key shape as `view_filters`.

**Integration.** `test_histogram_qualified_still_correct_after_filter_move` and
its `kdensity` twin: drive the aggregate branch of `_FILTER_JS`
(`:7389-7430`) and assert bins/densities come from widget ∩ qualifier rows.
Because the audit records that the graph-level qualifier shares this defect,
add the graph-level variant in the same test module — one fix, two guards.

**Mutation.**

| break this | test that must die |
|---|---|
| register `self._row_ids_for(_pdf)` again instead of the intersection | `test_intersection_survives_a_filter_move` |
| drop the member-id key from `_dash_agg_config` | the histogram/kdensity post-filter tests |
| point `_register_view_filter` back at `source` while `map_scatter` draws from `plot_source` | the `jitter()` composition test |

### Epic C — Teach the generated server app about per-plot qualifiers

**The failing test, first (rule 8).**
`test_mode_parity.py::TestTheTwoModesAgree` gains a corpus case: a spec with
`(scatter mpg weight) (lfit mpg weight if foreign==1)`. The corpus already
renders each case through both `_standalone_figures` and `_server_figures` and
diffs `_glyph_profile`, so the case fails on the unmodified tree the moment
Epic A lands and standalone starts drawing the correct fit — which is exactly
the guard US-C2 asks for. Add matching cases for `histogram`/`kdensity` (the
aggregate path) and for the same spec wrapped in `by(foreign)`.

**Unit tests (rule 4).** Source-level assertions on the **emitted** app text,
in `test_server.py` / `test_server_statistics.py` style:
- every `_compute_*` call site named in TR-01.11 passes a masked frame rather
  than the bare `g_df` / `_fac_gdf` / `work_df` / `agg_fdf`. Assert by counting:
  the number of `_compute_` call sites in the emitted source equals the number
  of masked-frame call sites. A count-based assertion is what catches the *next*
  helper someone adds without a mask.
- `_graph_qualifiers` is keyed by gname **and** plot index (TR-01.12a).
- the `by()`-facet block consults the per-plot keys (TR-01.12b).
- the filter-callback requalify block reapplies the per-plot mask (TR-01.12c).

**Integration.** Extend `test_server_brush.py` with the intersection assertion
for the brush recompute at emitted `15605-15633` — brushed ∩ per-plot, never
replaced. Extend `test_server_statistics.py` with the served-app equivalent of
Epic A's ground-truth `lfit` assertion. `test_e2e_serve.cscript` gains a case
that serves a dashboard containing a qualified computed layer.

**Mutation.**

| break this | test that must die |
|---|---|
| revert one `_compute_lfit(g_df, ...)` call site to the unmasked frame | the emitted-source count assertion **and** the parity case |
| key `_graph_qualifiers` by gname only | the callback re-render test |
| make the brush recompute assign the per-plot mask instead of intersecting | `test_server_brush.py`'s intersection assertion |

### Suite-level gates for this phase

- Full pytest suite green. The audit's HEAD baseline is **3,498 passed / 37
  skipped**; this phase adds tests and must not subtract passes.
- Full certification suite: **25/25 cscripts**, run with `arch -arm64` from
  `test/` — and a skip is not a pass.
- Conformance corpus: zero `r(198)`, zero dropped series, zero dropped graphs.
- Parity corpus green, now including the per-plot qualifier cases.

---

## Definition of done

A reviewer can tick these in order.

**Behaviour**

- [ ] `dash (scatter mpg weight) (lfit mpg weight if foreign==1)` draws a fit
      whose slope/intercept match `regress mpg weight if foreign==1`
      (`-.01042596` / `48.918297`) in standalone mode.
- [ ] The same command draws the same fit in server mode.
- [ ] All 14 mappers in TR-01.2 honour the mask; `area` has a view.
- [ ] `in_expr` behaves identically to `if_expr` for every one of them.
- [ ] `scatteri`, `pci` and `function` warn by name when qualified and still
      draw.
- [ ] No E-1024 `CDSVIEW_FILTERS_WITH_CONNECTED` in any emitted document.
- [ ] `mlabel` labels and `colorvar` colour ranges reflect the qualified rows,
      in both renderers.
- [ ] A linked graph's graph-level qualifier and a linked `by()` panel both
      reach computed layers.
- [ ] After a filter-widget move: the intersection holds (views), the
      aggregates recompute from widget ∩ qualifier rows, and `jitter()` does
      not shift the mask.
- [ ] Served dashboards apply the qualifier at first paint, inside `by()`
      panels, after every callback, and intersect it with a brush rather than
      replacing it.
- [ ] `link()` still propagates through a qualified layer (the measurement the
      original design comment records is re-run and still holds).

**Process**

- [ ] Every item has a regression test that was demonstrated to fail on the
      pre-fix tree (rule 8) — with the failing output recorded in the commit
      message or PR body.
- [ ] Every function touched has a unit test (rule 4).
- [ ] Every test in the phase has a recorded mutation that kills it.
- [ ] Full pytest suite and the 25 cscripts pass, with honest skips.
- [ ] Parity corpus includes at least one qualified computed layer and passes.
- [ ] All ten items are individually addressed; none was merged away or
      declared out of scope without the item number being named.
- [ ] Commits are single-issue, on `feature/batch4-interactive-layer`, with the
      merge command reported rather than run (rule 6), and no Claude/Anthropic
      references in the messages (rule 7).

**Explicitly out of scope for this phase** (so a reviewer does not block on
them): the `dash.ado` / `dash_parse.mata` qualifier-capture and injection items,
and the rule-8 test battery for those, belong to **Phase 2**; the `dash.sthlp`
and CHANGELOG text belongs to **Phase 30**.

---

## Risks and sequencing notes

**The server work overlaps 15-03, and that overlap is the main scheduling
hazard.** Items 2, 5 and 6 edit emitted source that Phases 5–8 intend to delete
in favour of `_DASH_MAPPER` delegation — §4 of the audit records that
`ServerAppBuilder` holds 51 `ptype ==` comparisons and exactly one of them
delegates. Doing Epic C first means writing a mask into ~20 emitted call sites
that a later phase removes; doing it after means shipping a known-wrong server
renderer for longer. The recommended resolution: land Epic A and Epic B
immediately (they are the wrong-numbers fix and they are independent of 15-03),
then land Epic C's **parity case** from the test plan — which makes the server
divergence a failing test rather than an invisible defect — and implement Epic C
either against the current emitted code or as part of the delegation work,
whichever phase reaches it first. Whoever lands it must satisfy TR-01.11 and
TR-01.12 in full; a delegation that covers only the plot loop leaves the
by()-facet and callback paths wrong.

**The auditor's own "for free" note is a documented trap.** Item 5 exists
because a previous pass recorded that server mode would inherit the mapper fix.
It will not. Anyone planning from the Appendix B entry alone will under-scope
this phase by roughly twenty call sites.

**Do not fix this by pre-filtering raw-data layers.** The comment at
`dash_render.py:9964-9973` records a measurement: on `link(_all)` with two
graphs, a layer given its own source fell outside both `link()` and the filter
callback. The correct shape is *compute the layer from the qualified frame,
then view it* — computed layers get a masked computation, raw-data layers keep
the shared-source `CDSView`. TR-01.4's and TR-01.8's private-source options are
the only sanctioned exceptions and each carries its own `link()` guard test.

**Item 7 and item 10 are latent until item 1 lands.** Both are "correct on
first paint, wrong after the first interaction" defects. If they are deferred,
the phase will look done in a screenshot and fail the moment a user touches a
widget — which is the failure mode the audit calls out as the worst-shaped one.
They are small and medium respectively; do them inside this phase.

**Item 9 changes a shared invariant.** Whichever resolution is chosen for
`jitter()`, it alters which `ColumnDataSource` objects exist per graph. Run
`test_jitter.py`, `test_linking.py`, `test_linking_filters.py` and
`test_filters.py` before and after, and treat any change in source counts as a
result to explain rather than a detail.

**Tolerance choice on the ground-truth assertion.** The `lfit` test compares
rendered endpoints against Stata's regression coefficients. Pick the tolerance
once, state it in the test, and make it tight enough that the unqualified fit
(slope `-.00600869` against `-.01042596`, a factor of 1.7) can never pass — the
two numbers are far apart, so there is no excuse for a loose bound.

**Ordering inside the phase:** item 1 → items 3, 4, 8 → items 7, 9, 10 →
items 2, 6, 5. Item 1 is the mechanism everything in Epic A reuses; item 5 is
last because it is the largest and because it benefits from the parity case that
item 2's work makes writable.
