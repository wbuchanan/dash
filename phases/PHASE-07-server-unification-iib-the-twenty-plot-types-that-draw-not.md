# Phase 07 — Server unification II(b): the twenty plot types that draw nothing

**Purpose.** In server mode (`dash build, server` / `dash serve`), adding `by()` to an
otherwise working command can silently delete the plot. The emitted app's two facet
chains — the `by()` chain at `dash_render.py:15137-15230` and its `by(total)` twin at
`dash_render.py:15237-15330` — are hand-written `elif ptype ==` ladders that handle only
18 of the 38 plot types dash accepts. The other 20 fall off the end of the chain and
nothing is drawn, nothing is warned, and the build still returns rc 0. Two more types
(`lpolyci`, `fpfitci`) are worse than blank: they are aliased onto their band-less
siblings, so the panel draws a plausible-looking line with the confidence band silently
missing. Of the 18 the chains do handle, 8 diverge from the standalone rendering on glyph
properties, and 7 lose their plot options (`bin()`, `n()`, `bwidth()`, `degree()`) the
moment any filter widget moves. This phase routes both facet chains through the
`GlyphMapper` methods that already exist and are already emitted into the app but never
called there, and it repairs the parity guard so that this class of defect cannot return
undetected — because the guard, as written, compares no data at all and would have passed
through every one of these.

---

## At a glance

| | |
|---|---|
| **Items** | 6 (numbered 1–6 below, exactly as handed over) |
| **Functional vs deliverable** | 5 functional · 1 deliverable |
| **Effort mix** | 1 large · 1 medium · 4 small |
| **Renderers touched** | `ServerAppBuilder` (emitted app) ×5 · both renderers ×1 (the parity guard) |
| **Ultraplan tasks discharged** | `15-03` (jointly with Phases 05, 06, 08 — this phase closes its facet-dispatch half) |
| **Sections** | S15 (Unification); downstream relief for S06, S08, S09, S12, S13 server-side gaps |
| **Depends on** | **Phase 05** (main-loop delegation to `_DASH_MAPPER` — establishes the call convention the facet chains will reuse) · **Phase 06** (facet-loop unification with `_expand_by_groups`, facet graph options, facet marker size/alpha — same two code regions) |
| **Unblocks** | **Phase 08** (parity guard III: corpus widening needs a guard that compares data) · **Phase 31** (release gates — the parity corpus is a named S16-07 gate) |
| **Primary files** | `dash_render.py:15137-15230`, `dash_render.py:15237-15330`, `dash_render.py:15609-15630`, `dash_render.py:3407-6065` (`GlyphMapper.map_*`), `test/test_mode_parity.py` |

---

## Why this phase exists

### The headline finding, copied from `REMAINING.md`

> 4. **The standalone/server parity guard covers 17 of 36 plot types, and five
>    of the unguarded ones have already drifted** — including `function` and
>    `pci`, which draw *nothing* in server mode, and `fpfitci`, which loses its
>    confidence band there.

### The measured state of the collapse (`REMAINING.md` §4)

> **The collapse is 1/46 done.** `ServerAppBuilder` holds **51 `ptype ==`
> comparisons** across ~4,000 emitted lines; exactly **one** (`scatter`)
> delegates to `_DASH_MAPPER`. 39 `map_*` methods exist.
>
> **The guard is narrower than it reads.** The parity corpus is 32 cases over
> **17 distinct plot types**, against **36 server `ptype` branches** — so
> **19 types are unguarded** (`fpfit` `fpfitci` `function` `lfitci` `lowess`
> `pcbarrow` `pci` `pcspike` `qfit` `qfitci` `rarea` `rbar` `rcap` `rconnected`
> `rline` `rscatter` `rspike` `tsline` `tsrline`). It also never constructs a
> spec with `by()`, KPIs, `filter()`, `link()` or `tabs()` — grep for each of
> those keys in the corpus returns 0.

Five of those 19 had already drifted when the audit ran, measured by building both
renderers' figures from the same spec and diffing every glyph property:

| type | standalone | server | consequence |
|---|---|---|---|
| **`fpfitci`** | `VArea`(α .2) + `Line` | `Line` only | **the confidence band is missing in server mode** |
| **`function`** | `Line` | *nothing* | **server-mode `function` draws no layer** |
| **`pci`** | `Segment` | *nothing* | **server-mode `pci` draws no layer** |
| `lowess` | `#1f77b4`, width 1 | `#1a476f`, width 1.5 | **standalone `lowess` ignores the scheme** (matplotlib's default blue) |
| `rscatter` | marker size 8.0 | marker size 6 | two default size tables |

and, on why nothing caught them:

> `test_conformance.cscript`'s "every layer drew something" assertion runs in
> **standalone mode only**, which is precisely why the two server-mode layers
> that draw nothing are invisible to it.

That table is about the **main loop**. This phase is about the **facet chains**, where the
same class of defect is twenty types wide rather than two.

### Appendix A — `15-03` · PARTIAL, remaining items 1 and 2

> 1. **38 of the 39 plot types the emitted app dispatches still carry their own
>    drawing code.** Exactly one delegates: `_DASH_MAPPER.map_scatter` at
>    `dash_render.py:14090`. The 38: `area` `bar` `connected` `dot` `dropline`
>    `fpfit` `fpfitci` `function` `hist` `histogram` `kdensity` `lfit` `lfitci`
>    `line` `lowess` `lpoly` `lpolyci` `mband` `mspline` `pcarrow` `pcbarrow`
>    `pci` `pcscatter` `pcspike` `qfit` `qfitci` `rarea` `rbar` `rcap` `rcapsym`
>    `rconnected` `rline` `rscatter` `rspike` `scatteri` `spike` `tsline`
>    `tsrline`.
> 2. **The `by()` and `by(total)` facet loops were never unified.** The task
>    requires them to become the same facet-expansion code the standalone path
>    uses. `_expand_by_groups` occurs 3× in `DashRenderer` and **0×** in the
>    emitted app, which still carries its own `by_total` handling. The third and
>    fourth copies the task set out to delete are both still there.
> 3. Every server-side gap in 06-06, 08-04, 08-05, 09-02 and 09-07 above is
>    downstream of this task. Finishing it is what makes those five stop being
>    two problems each.

### Appendix B — the twenty blank types (this phase's item 1, verbatim)

> - **[func · server · L]** 20 plot types draw NOTHING under `by()` /
>   `by(total)` in server mode: function, lfitci, mspline, pcarrow, pcbarrow,
>   pci, pcscatter, pcspike, qfitci, rarea, rbar, rcap, rcapsym, rconnected,
>   rline, rscatter, rspike, scatteri, tsline, tsrline. The two facet chains
>   handle only 18 types (scatter, line, bar, area, histogram/hist, lfit, qfit,
>   kdensity, lowess, lpoly, lpolyci, fpfit, fpfitci, connected, dot, spike,
>   dropline, mband); anything else falls off the end of the elif chain
>   silently.     *Where:* `dash_render.py emitted facet chain at 15137-15230
>   (by) and 15237-15330 (by total); fix by routing both through GlyphMapper
>   like the main loop`

**Confirmed at HEAD** (read-only `sed -n '15130,15215p' dash_render.py`): the per-group
chain's last branch is `elif ptype == 'mband':` at `dash_render.py:15201`, whose body ends
at 15213 and is followed at 15214 by

```python
"            figures[_fac_name] = _fac_fig",
"            facet_entries.append((_fac_name, _fac_label))",
```

There is no `else:` and no diagnostic. A `ptype` the ladder does not name produces a
figure with zero renderers and the loop moves on.

### The emitted code, as it stands

The three divergences this phase fixes inside the 18 handled types are visible in the
emitted string literals themselves:

```python
# dash_render.py:15156 — faceted histogram: no line_color at all, fill_alpha 0.6
"                    _fac_fig.quad(top='top', bottom=0, left='left', right='right', source=_hsrc, fill_color=color, fill_alpha=0.6, legend_label=_hvar)",

# dash_render.py:15199 — faceted dropline stem: hardcoded 1.0, not the scheme's 1.2
"                    _fac_fig.segment(x0=xvar_f, y0=0, x1=xvar_f, y1=yvar_f, source=_fac_src, line_width=1.0, color=color, **_glyph_kw)",

# dash_render.py:15179 / 15186 — lpolyci and fpfitci aliased onto their band-less siblings
"                elif ptype in ('lpoly', 'lpolyci'):",
"                elif ptype in ('fpfit', 'fpfitci'):",

# dash_render.py:15156 (and 15161/15166/15172/15177/15184/15189) — registration without 'opts'
"                    agg_sources[(_fac_name, pi)] = {'source': _hsrc, 'type': 'histogram', 'var': _hvar, 'bins': 20}",
```

against the consumer that recomputes those same sources on every widget move:

```python
# dash_render.py:15609-15630 — every branch reads agg.get('opts')
"                if atype == 'histogram':",
"                    agg['source'].data = _compute_histogram(agg_fdf, agg['var'], agg.get('opts') or {})",
"                elif atype == 'lfit':",
"                    agg['source'].data = _compute_lfit(agg_fdf, agg['yvar'], agg['xvar'], agg.get('opts') or {})",
```

The `'bins': 20` key the registration *does* write is read by nothing. So a faceted
`histogram mpg, bin(4)` renders four bars and re-bins itself to the data-driven default
the first time the user touches a filter.

### The guard that should have caught all of this

> **[deli · both · M]** The parity guard compares no DATA. `_glyph_profile`
> (test/test_mode_parity.py:129) reads only
> type/marker/size/fill_color/line_color/line_width/line_dash/fill_alpha;
> `_annotations` and `_chrome` add labels and background/grid colours.
> `data_source.data` is touched in exactly two places, both histogram bar
> counts (test/test_mode_parity.py:365, 382). The section's TDD stub says
> 'equivalent glyph types, DATA and visual properties' and 15-01's action says
> 'compare ... glyph types, DATA VALUES, and the visual properties'.
> Consequence measured: kdensity (300 vs 200 points) and fpfit/fpfitci (10 vs
> 200) diverge inside the existing corpus and the file still reports 165
> passed. Separately, `ALLOWED` (test/test_mode_parity.py:55) gates no
> comparison — its only assertions are that it is non-empty and that each
> reason is over 40 characters (test/test_mode_parity.py:388-392), so the
> 'explicit allowance' design is decorative. `_chrome` also omits figure
> title, axis labels, axis scale type and legend visibility, which is why the
> facet graph-option losses above would survive even after the corpus gains
> by() cases.

**Confirmed at HEAD.** `_chrome` (`test/test_mode_parity.py:178`) returns exactly four
keys:

```python
def _chrome(fig):
    return {
        "background_fill_color": fig.background_fill_color,
        "border_fill_color": fig.border_fill_color,
        "xgrid": [g.grid_line_color for g in fig.xgrid],
        "ygrid": [g.grid_line_color for g in fig.ygrid],
    }
```

and the allowance-list test asserts only non-emptiness and a 40-character reason:

```python
class TestTheAllowanceListIsExplicit:
    def test_every_allowance_states_a_reason(self):
        assert ALLOWED, "an empty allowance list hides nothing, but says nothing"
        for key, why in ALLOWED.items():
            assert len(why) > 40, f"{key}: allowances must say why"
```

The last sentence of the item is the reason this deliverable sits in *this* phase rather
than being deferred to Phase 08: a guard that compares no data and no figure chrome would
pass a faceted panel that draws the right glyph types with the wrong numbers — which is
precisely what items 3, 4 and 6 describe.

### The targets already exist

Every one of the 20 blank types has a `GlyphMapper` method that is already copied into the
emitted app (`dash_render.py:12406-12410` emits `OptionTranslator`, `SchemeParser` and
`GlyphMapper` verbatim) and is never called from the facet chains. Confirmed at HEAD by
`grep -n "    def map_" dash_render.py`:

| blank type | existing target | defined at |
|---|---|---|
| `function` | `GlyphMapper.map_function` | `dash_render.py:6065` |
| `lfitci` | `GlyphMapper.map_lfitci` | `dash_render.py:3918` |
| `mspline` | `GlyphMapper.map_mspline` | `dash_render.py:5912` |
| `pcarrow` | `GlyphMapper.map_pcarrow` | `dash_render.py:5660` |
| `pcbarrow` | `GlyphMapper.map_pcbarrow` | `dash_render.py:5732` |
| `pci` | `GlyphMapper.map_pci` / `map_pci_literal` | `dash_render.py:5516` / `5548` |
| `pcscatter` | `GlyphMapper.map_pcscatter` | `dash_render.py:5609` |
| `pcspike` | `GlyphMapper.map_pcspike` | `dash_render.py:5472` |
| `qfitci` | `GlyphMapper.map_qfitci` | `dash_render.py:3998` |
| `rarea` | `GlyphMapper.map_rarea` | `dash_render.py:4920` |
| `rbar` | `GlyphMapper.map_rbar` | `dash_render.py:4958` |
| `rcap` | `GlyphMapper.map_rcap` | `dash_render.py:5041` |
| `rcapsym` | `GlyphMapper.map_rcapsym` | `dash_render.py:5291` |
| `rconnected` | `GlyphMapper.map_rconnected` | `dash_render.py:5147` |
| `rline` | `GlyphMapper.map_rline` | `dash_render.py:5106` |
| `rscatter` | `GlyphMapper.map_rscatter` | `dash_render.py:5861` |
| `rspike` | `GlyphMapper.map_rspike` | `dash_render.py:5003` |
| `scatteri` | `GlyphMapper.map_scatteri` | `dash_render.py:5370` |
| `tsline` | `GlyphMapper.map_tsline` | `dash_render.py:5805` |
| `tsrline` | `GlyphMapper.map_tsrline` | `dash_render.py:5832` |

and for the two band-losing types: `GlyphMapper.map_lpolyci` at `dash_render.py:4344`,
`GlyphMapper.map_fpfitci` at `dash_render.py:4569` (REMAINING.md gives this as the
"4400-ish region, symbol `map_fpfitci`"; the exact definition line at HEAD is 4569).

**This is the whole shape of the phase: not new drawing code, but twenty-two call sites
that should have been delegations.**

---

## Epics

| epic | goal | items |
|---|---|---|
| **7.A — Every plot type draws under `by()`** | Route both facet chains through `GlyphMapper` so the 20 blank types draw and the CI types keep their bands. | 1, 3, 6 |
| **7.B — Faceted layers keep their scheme and their options** | Close the glyph-property divergences inside the 18 handled types, and make faceted aggregate registrations carry `'opts'` so options survive the first interaction. | 2, 4 |
| **7.C — A guard that compares numbers** | Make `test/test_mode_parity.py` compare data values and figure chrome, and make `ALLOWED` gate a real comparison. | 5 |

Items 3 and 6 describe the same two branches from two directions (3 names the branch lines
and the missing band; 6 frames it as "four CI types lose their band under `by()`", of which
`lfitci`/`qfitci` are also members of item 1's twenty). They are implemented together in
7.A and verified separately — see *Risks and sequencing notes*.

---

## User stories

### Epic 7.A — Every plot type draws under `by()`

**US-7.A.1** — *As a Stata user pasting a `twoway` command, I want `dash (rspike hi lo
date) ..., by(region)` served by `dash serve` to draw the spikes in every panel, so that
adding `by()` does not silently delete my plot.*

- **Given** a spec whose graph has `by: {vars: ["foreign"]}` and one plot of any of the
  20 types (`function`, `lfitci`, `mspline`, `pcarrow`, `pcbarrow`, `pci`, `pcscatter`,
  `pcspike`, `qfitci`, `rarea`, `rbar`, `rcap`, `rcapsym`, `rconnected`, `rline`,
  `rscatter`, `rspike`, `scatteri`, `tsline`, `tsrline`),
- **When** the server app is built and executed,
- **Then** every faceted figure carries at least one renderer whose glyph type matches the
  standalone renderer's glyph type for that plot type, and the emitted facet chain contains
  no `ptype` for which the ladder falls through without drawing.

**US-7.A.2** — *As a dashboard viewer, I want a faceted `fpfitci` or `lpolyci` panel to
show its confidence band, so that I am not shown a narrower claim than the data supports.*

- **Given** a spec with `(fpfitci mpg weight)` and `by(foreign)`,
- **When** the app is executed and the panel figures are inspected,
- **Then** each panel carries both a `VArea` (fill_alpha 0.2) and a `Line`, matching the
  standalone `fpfitci` profile, and the same holds for `lpolyci` and for the `by(total)`
  panel.

**US-7.A.3** — *As a `dash serve` operator, I want a plot type the facet path cannot draw
to be reported at build time, so that an empty panel is never the first I hear of it.*

- **Given** a spec with a plot type that no `GlyphMapper.map_*` handles,
- **When** the app is built,
- **Then** dash emits the same empty-layer diagnostic the standalone path emits, and the
  panel is not silently blank.

### Epic 7.B — Faceted layers keep their scheme and their options

**US-7.B.1** — *As a Stata user, I want a faceted histogram to look like the unfaceted one,
so that `by()` is a data-partitioning option and not a restyling option.*

- **Given** `(histogram mpg)` rendered both with and without `by(foreign)` under the same
  scheme,
- **When** the glyph properties of the `Quad` in each are compared,
- **Then** `line_color` and `fill_alpha` are identical (white outline, fill_alpha 1.0 —
  not Bokeh's unstyled `#1f77b4` at 0.6), and a faceted `dropline` stem is drawn at the
  scheme's 1.2 line width, not a hardcoded 1.0.

**US-7.B.2** — *As a dashboard viewer, I want the bin count I asked for to survive my first
click on a filter, so that the chart I am reading does not re-bin itself underneath me.*

- **Given** a served dashboard built from `(histogram mpg, bin(4))` with `by(foreign)` and
  any `filter()` widget,
- **When** the widget is moved,
- **Then** each panel still draws 4 bars; and equivalently faceted `lfit n()`, `qfit`, and
  `lpoly bwidth()`/`degree()` keep their declared options across the recompute.

### Epic 7.C — A guard that compares numbers

**US-7.C.1** — *As a package maintainer, I want the parity guard to fail when the two
renderers put different numbers on the screen, so that "165 passed" means the modes agree
rather than that they agree about colours.*

- **Given** the existing corpus entry for `kdensity` (standalone evaluates 300 points,
  the emitted `_compute_kdensity` 200) and for `fpfit`/`fpfitci` (10 vs 200),
- **When** the parity suite runs against HEAD *before* Phases 05–08 land the fixes,
- **Then** those entries fail with a message naming the array length or value that differs
  — not pass.

**US-7.C.2** — *As a package maintainer, I want every accepted difference to be an entry in
`ALLOWED` that some comparison actually consults, so that the allowance list documents
behaviour instead of decorating the file.*

- **Given** a difference between the two modes that is listed in `ALLOWED`,
- **When** the comparison runs,
- **Then** the difference is skipped **by key lookup** and the test reports which allowance
  was used; and **when** a difference is not listed, the test fails.

**US-7.C.3** — *As a package maintainer, I want figure chrome — title, axis labels, axis
scale type, legend visibility — compared, so that the faceted graph-option losses cannot
hide behind a green suite once the corpus gains `by()` cases.*

---

## Business requirements

| id | requirement | how it is testable |
|---|---|---|
| **BR-07.1** | In server mode, a plot type draws the same glyph types under `by()` and `by(total)` as it draws without them. | Per-type parity assertion over all 38 types × {no by, by, by total}. |
| **BR-07.2** | No faceted panel silently omits a layer. A plot type the facet path cannot draw must produce a build-time diagnostic. | Assert the emitted facet dispatch has no silent fall-through; assert the diagnostic fires for an unknown type. |
| **BR-07.3** | A faceted glyph is visually identical to its unfaceted counterpart except for the rows it covers. | `_glyph_profile` equality between faceted and unfaceted figures for the same scheme. |
| **BR-07.4** | Confidence-interval plot types (`lfitci`, `qfitci`, `fpfitci`, `lpolyci`) keep their band under `by()` and `by(total)`. | Assert a `VArea` renderer is present in each panel for each of the four. |
| **BR-07.5** | Plot options declared in the command remain in effect after any widget interaction, faceted or not. | Build, move a filter, re-read the aggregate source; bar/point counts unchanged. |
| **BR-07.6** | The parity guard fails when the two modes produce different **data values**, not only different visual properties. | Mutation: change a grid size in one renderer → suite must go red. |
| **BR-07.7** | Every accepted mode difference is an `ALLOWED` entry that a comparison consults; an unlisted difference fails. | Remove an allowance → its case fails. Add a bogus allowance → unused-allowance check fails. |
| **BR-07.8** | Figure chrome (title, axis labels, axis scale type, legend visibility) is compared between modes. | Extend `_chrome`; mutate a server-side title composition → suite goes red. |
| **BR-07.9** | Nothing in this phase changes standalone-mode output. | The standalone half of every corpus case is byte-stable against the pre-phase profile. |

---

## Technical requirements

### 7.A — Facet dispatch

**TR-07.1** — Replace the per-group facet `elif ptype` ladder, emitted at
`dash_render.py:15137-15230`, with a delegation to `_DASH_MAPPER`, following the pattern
the main loop already uses for `scatter` at `dash_render.py:14090`
(`_DASH_MAPPER.map_scatter`). The ladder's branch set today is exactly the sixteen
branch heads measured at HEAD: `scatter` (`if` at 15144), `line` (15146), `bar` (15148),
`area` (15150), `histogram`/`hist` (15152, whose `quad` is at 15157 and whose registration
REMAINING.md cites as 15156), `lfit` (15158), `qfit` (15163), `kdensity` (15168), `lowess`
(15174), `lpoly`/`lpolyci` (15179), `fpfit`/`fpfitci` (15186), `connected` (15191), `dot`
(15194), `spike` (15196), `dropline` (15198, whose `segment` is the 15199 REMAINING.md
cites), and last `mband` (15201, body through 15213). Line 15214 is
`figures[_fac_name] = _fac_fig` — there is no `else:`.

**TR-07.2** — Apply the identical change to the `by(total)` twin at
`dash_render.py:15237-15330`, the `_tot_fig` / `_tot_src` / `work_df` analogue of the
same ladder. Its sixteen branch heads, measured at HEAD, are `scatter` (15245), `line`
(15247), `bar` (15249), `area` (15251), `histogram`/`hist` (15253), `lfit` (15259), `qfit`
(15264), `kdensity` (15269), `lowess` (15275), `lpoly`/`lpolyci` (15280),
`fpfit`/`fpfitci` (15287), `connected` (15292), `dot` (15295), `spike` (15297), `dropline`
(15299) and `mband` (15302, body through 15314, with `figures[_tot_name] = _tot_fig` at
15315). The numbers REMAINING.md quotes for this twin — `15257`, `15262`, `15267`,
`15273`, `15278`, `15285`, `15290` — are the aggregate **registration** lines inside those
branches (see TR-07.9), and `15300` is the dropline `segment` call. Both chains must end up calling the same
mapper entry point; the only difference between them is the frame (`_fac_gdf` vs
`work_df`) and the figure (`_fac_fig` vs `_tot_fig`).

**TR-07.3** — The 20 types that currently fall through must reach their existing
`GlyphMapper` targets, per the table in *Why this phase exists*: `map_function` (6065),
`map_lfitci` (3918), `map_mspline` (5912), `map_pcarrow` (5660), `map_pcbarrow` (5732),
`map_pci` (5516) / `map_pci_literal` (5548), `map_pcscatter` (5609), `map_pcspike` (5472),
`map_qfitci` (3998), `map_rarea` (4920), `map_rbar` (4958), `map_rcap` (5041),
`map_rcapsym` (5291), `map_rconnected` (5147), `map_rline` (5106), `map_rscatter` (5861),
`map_rspike` (5003), `map_scatteri` (5370), `map_tsline` (5805), `map_tsrline` (5832).
These classes are already emitted into the app by the loop at
`dash_render.py:12406-12410` (`for _cls in (OptionTranslator, SchemeParser, GlyphMapper)`),
so no new import or new emitted source block is required — only the call.

**TR-07.4** — `lpolyci` must stop aliasing to `lpoly` and `fpfitci` must stop aliasing to
`fpfit`. The branches to split are `elif ptype in ('lpoly', 'lpolyci'):` at
`dash_render.py:15179` (twin `15280`) and `elif ptype in ('fpfit', 'fpfitci'):` at
`dash_render.py:15186` (twin `15287`). Targets: `GlyphMapper.map_lpolyci`
(`dash_render.py:4344`) and `GlyphMapper.map_fpfitci` (`dash_render.py:4569`). The
standalone profile these must reproduce is the one measured in `REMAINING.md` §4 for
`fpfitci`: **`VArea`(α .2) + `Line`**, where server today draws **`Line` only**. Note
that REMAINING.md records "The grids differ too" for these branches — the faceted
`_compute_lpoly`/`_compute_fpfit` path and the mapper path do not evaluate on the same x
grid; delegating resolves both at once (the `_fp_grid` divergence itself is Phase 05
item 4, `dash_render.py:6441` vs the emitted `_compute_fpfit` at `13492-13510`).

**TR-07.5** — After delegation, the facet chain must have no silent fall-through: an
unrecognised `ptype` must take an explicit `else:` that records an empty layer through the
same reporting path the standalone renderer uses, rather than leaving a renderer-less
figure. This is what makes BR-07.2 assertable.

**TR-07.6** — `by()` facet panels and the `by(total)` panel must both be covered. Per
`REMAINING.md`, `lfitci`/`qfitci` "draw nothing at all under `by()`", while `fpfitci` and
`lpolyci` "silently drop the `VArea` while still drawing the `Line`, so the panel looks
plausible and is wrong" — the acceptance check must therefore assert the **presence of the
band**, not merely that the panel is non-empty.

### 7.B — Faceted glyph fidelity and option survival

**TR-07.7** — The faceted histogram `Quad`, emitted at `dash_render.py:15156` (twin
`15257`), currently reads:

```python
_fac_fig.quad(top='top', bottom=0, left='left', right='right', source=_hsrc,
              fill_color=color, fill_alpha=0.6, legend_label=_hvar)
```

It passes **no `line_color`**, so Bokeh's unstyled default outline `#1f77b4` is used at
`fill_alpha` 0.6, where the standalone renderer draws a **white outline at fill_alpha
1.0**. Delegation to `GlyphMapper.map_histogram` (`dash_render.py:4636`) is the fix;
whatever the route, the post-fix faceted `Quad` must carry the standalone `line_color` and
`fill_alpha`.

**TR-07.8** — The faceted `dropline` stem, emitted at `dash_render.py:15199` (twin
`15300`), is drawn at `line_width=1.0`; the standalone scheme value is **1.2**. Target:
`GlyphMapper.map_dropline` (`dash_render.py:5211`). REMAINING.md's count for this item:
**8 of the 18 plot types the facet chain does handle diverge**, not only the marker ones
(marker size/alpha and `msize()`/`msymbol()` are Phase 06 item 2, at
`dash_render.py:15144` and `15245`).

**TR-07.9** — Every faceted aggregate registration must carry an `'opts'` key. The
registrations are at `dash_render.py:15156, 15161, 15166, 15172, 15177, 15184, 15189` and
the `by(total)` twins at `15257, 15262, 15267, 15273, 15278, 15285, 15290`. The consumer
is the live-recompute chain at `dash_render.py:15609-15630`, whose every branch reads
`agg.get('opts') or {}`:

```python
if atype == 'histogram':
    agg['source'].data = _compute_histogram(agg_fdf, agg['var'], agg.get('opts') or {})
elif atype == 'lfit':
    agg['source'].data = _compute_lfit(agg_fdf, agg['yvar'], agg['xvar'], agg.get('opts') or {})
```

**TR-07.10** — The `'bins': 20`, `'bwidth'` and `'degree'` keys those registrations
currently write are **dead reads** — nothing in the callback chain consults them. Remove
them in the same change, so that the registration's shape matches what
`_on_filter_change` actually consumes and a reader cannot mistake `'bins': 20` for the
effective bin count.

**TR-07.11** — Behavioural acceptance for TR-07.9/10: a faceted `histogram ..., bin(4)`
must render 4 bars **and still render 4 bars after any widget moves**. The same applies to
faceted `lfit n()`, `qfit`, and `lpoly bwidth()`/`degree()`.

### 7.C — The parity guard

**TR-07.12** — Extend `test/test_mode_parity.py:129 _glyph_profile` (or add a sibling
`_data_profile`) to compare `renderer.data_source.data`. Today `data_source.data` is
touched in exactly two places, both histogram bar counts
(`test/test_mode_parity.py:365, 382`). The comparison must cover, at minimum: the length
of each column and the element-wise values within a stated float tolerance. The measured
consequence of its absence: **kdensity (300 vs 200 points) and fpfit/fpfitci (10 vs 200)
diverge inside the existing corpus and the file still reports 165 passed.**

**TR-07.13** — Extend `_chrome` (`test/test_mode_parity.py:163`, whose body at HEAD sits
at `:178` and returns only `background_fill_color`, `border_fill_color`, `xgrid`, `ygrid`)
to include **figure title, axis labels, axis scale type and legend visibility**. Per
REMAINING.md these omissions "[are] why the facet graph-option losses above would survive
even after the corpus gains `by()` cases" — i.e. TR-07.13 is what gives Phase 06's facet
graph-option work (`_fac_kw` at `dash_render.py:15121-15131`, `by(total)` twin at
`15228-15235`) a guard.

**TR-07.14** — Make `ALLOWED` (`test/test_mode_parity.py:55`) gate a comparison. Today its
only assertions are non-emptiness and a >40-character reason
(`test/test_mode_parity.py:388-392`). Required: (a) a comparison consults `ALLOWED` by key
before reporting a difference; (b) an `ALLOWED` entry that no comparison ever used fails
the suite as dead allowance; (c) a difference with no matching key fails.

**TR-07.15** — The corpus entries this phase adds are `by()` and `by(total)` cases for the
types in 7.A. Corpus widening to all 36/38 types and the other structural paths (`KPIs`,
`filter()`, `link()`, `tabs()`) is Phase 08 item 8 and Phase 06 item 5; this phase adds
only what its own epics need and must not conflict with those edits —
`test/test_mode_parity.py:CORPUS` begins at line ~186.

**TR-07.16** — No change in this phase may alter `DashRenderer` output. `_expand_by_groups`
(`dash_render.py:8776`) and `_facet_label` (`dash_render.py:8872`) are read-only references
here; changing them is Phase 06's business.

---

## Work items

Numbered exactly as handed over. Tags: `kind · renderer · effort`.

---

### Item 1 — 20 plot types draw NOTHING under `by()` / `by(total)` in server mode
`functional · server · large` · origin `15-03` (Appendix B)

20 plot types draw NOTHING under `by()` / `by(total)` in server mode: function, lfitci,
mspline, pcarrow, pcbarrow, pci, pcscatter, pcspike, qfitci, rarea, rbar, rcap, rcapsym,
rconnected, rline, rscatter, rspike, scatteri, tsline, tsrline. The two facet chains handle
only 18 types (scatter, line, bar, area, histogram/hist, lfit, qfit, kdensity, lowess,
lpoly, lpolyci, fpfit, fpfitci, connected, dot, spike, dropline, mband); anything else
falls off the end of the elif chain silently.

**Where:** `dash_render.py` emitted facet chain at `15137-15230` (by) and `15237-15330`
(by total); fix by routing both through `GlyphMapper` like the main loop.

**Evidence:** the ladder's last branch is `elif ptype == 'mband'` at `dash_render.py:15201`,
whose body ends at 15213 and is followed at 15214 by `figures[_fac_name] = _fac_fig` — no
`else`, no diagnostic (confirmed at HEAD; the `by(total)` twin ends the same way at
15302 → 15315). All 20 targets exist as `GlyphMapper.map_*` methods already emitted into the app
(table above). `test_conformance.cscript`'s "every layer drew something" assertion runs in
standalone mode only, which is why this is invisible to the certification suite.

---

### Item 2 — Faceted glyph divergences beyond marker size/alpha
`functional · server · small` · origin `15-03` (Appendix C)

Faceted glyph divergences beyond marker size/alpha: (a) a faceted `histogram` bar is drawn
with Bokeh's unstyled default outline `#1f77b4` at fill_alpha 0.6, where standalone draws a
white outline at fill_alpha 1.0 — the emitted `_fac_fig.quad(top='top', bottom=0,
left='left', right='right', source=_hsrc, fill_color=color, fill_alpha=0.6,
legend_label=_hvar)` passes no line_color at all; (b) a faceted `dropline` stem is drawn at
`line_width=1.0` where standalone uses the scheme's 1.2. So 8 of the 18 plot types the
facet chain does handle diverge, not just the marker ones.

**Where:** `dash_render.py:15156` (emitted facet `quad`), `dash_render.py:15199` (emitted
facet dropline `segment`), and the `by(total)` twins at `dash_render.py:15257` and `15300`.

**Evidence:** both emitted literals read exactly as quoted, confirmed at HEAD.

---

### Item 3 — Faceted `lpolyci` and `fpfitci` lose their confidence band
`functional · server · small` · origin `15-03` (Appendix C)

Faceted `lpolyci` and `fpfitci` lose their confidence band in server mode. The facet chains
collapse them into their band-less siblings: `elif ptype in ('lpoly','lpolyci')`
(`dash_render.py:15179`, twin at `15280`) draws only the lpoly line from `_compute_lpoly`,
and `elif ptype in ('fpfit','fpfitci')` (`dash_render.py:15186`, twin at `15287`) only the
fpfit line. Neither is in the auditor's '20 types draw NOTHING under by()' list, because
they draw a line — just the wrong one. The grids differ too.

**Where:** `dash_render.py:15179-15192` and `dash_render.py:15280-15293`; targets are
`GlyphMapper.map_lpolyci` / `map_fpfitci`.

**Evidence:** branch heads confirmed verbatim at HEAD; targets confirmed at
`dash_render.py:4344` (`map_lpolyci`) and `dash_render.py:4569` (`map_fpfitci`).

---

### Item 4 — Faceted aggregate layers lose their plot options after the first interaction
`functional · server · small` · origin `15-03` (Appendix C)

Faceted aggregate layers lose their plot options after the FIRST filter interaction. The
facet agg registrations (`dash_render.py:15156, 15161, 15166, 15172, 15177, 15184, 15189`
and the by(total) twins at `15257-15290`) omit the `'opts'` key, while `_on_filter_change`
recomputes with `agg.get('opts') or {}` (`dash_render.py:15609-15630`). So a faceted
`histogram ..., bin(4)` renders 4 bars and then silently re-bins to the data-driven default
as soon as any widget moves; the same applies to faceted lfit `n()`, qfit, and lpoly
`bwidth()`/`degree()`. The `'bins': 20`, `'bwidth'` and `'degree'` keys those registrations
DO write are dead reads — nothing in the callback chain consults them.

**Where:** `dash_render.py:15156/15161/15166/15172/15177/15184/15189` and
`15257/15262/15267/15273/15278/15285/15290`; consumer at `dash_render.py:15609-15630`.

**Evidence:** the registration literal and the consumer's `agg.get('opts') or {}` reads are
quoted from HEAD above.

---

### Item 5 — The parity guard compares no DATA
`deliverable · both · medium` · origin `15-03` (Appendix C)

The parity guard compares no DATA. `_glyph_profile` (`test/test_mode_parity.py:129`) reads
only type/marker/size/fill_color/line_color/line_width/line_dash/fill_alpha; `_annotations`
and `_chrome` add labels and background/grid colours. `data_source.data` is touched in
exactly two places, both histogram bar counts (`test/test_mode_parity.py:365, 382`). The
section's TDD stub says 'equivalent glyph types, DATA and visual properties' and 15-01's
action says 'compare ... glyph types, DATA VALUES, and the visual properties'. Consequence
measured: kdensity (300 vs 200 points) and fpfit/fpfitci (10 vs 200) diverge inside the
existing corpus and the file still reports 165 passed. Separately, `ALLOWED`
(`test/test_mode_parity.py:55`) gates no comparison — its only assertions are that it is
non-empty and that each reason is over 40 characters (`test/test_mode_parity.py:388-392`),
so the 'explicit allowance' design is decorative. `_chrome` also omits figure title, axis
labels, axis scale type and legend visibility, which is why the facet graph-option losses
above would survive even after the corpus gains `by()` cases.

**Where:** `test/test_mode_parity.py:129 _glyph_profile`, `:163 _chrome`, `:55 ALLOWED`,
`:388-392`.

**Evidence:** `_chrome`'s four-key body and the allowance test's two assertions are quoted
from HEAD above.

---

### Item 6 — Four CI plot types lose their confidence band under `by()`
`functional · server · small` · origin `15-03` (Appendix C)

Four CI plot types lose their confidence band under `by()`, which neither of the auditor's
two facet items covers: their '20 types draw NOTHING' list omits fpfitci and lpolyci (those
draw a partial figure, band missing), and their main-loop divergence item is explicitly
about the main loop. lfitci/qfitci draw nothing at all under `by()` (they ARE in the 20),
but fpfitci and lpolyci silently drop the VArea while still drawing the Line, so the panel
looks plausible and is wrong.

**Where:** `dash_render.py`: emitted `by()` facet chain at `15137-15230` and `by(total)`
twin at `15237-15330` — the fpfitci and lpolyci facet branches draw only the line; fix by
routing both chains through `GlyphMapper.map_fpfitci` (symbol confirmed at
`dash_render.py:4569`) and `map_lpolyci` (`dash_render.py:4344`).

**Evidence:** `REMAINING.md` §4's measured main-loop row for `fpfitci` — standalone
`VArea`(α .2) + `Line`, server `Line` only — is the profile the faceted branches must also
produce. This item is the *acceptance framing* for items 1 and 3 taken together: it names
the four CI types as a class and requires the band, not merely a non-empty panel.

---

## Test plan

All new tests are written **before** the corresponding fix and must be observed failing
against HEAD (project rule 8). Every mapper call site added is covered by a unit test
(rule 4). Non-vacuity is proved by mutation: the named break must turn the test red.

### Epic 7.A — Every plot type draws under `by()`

**Failing test first — `test/test_server_facets.py` (new).**

| test | asserts | fails at HEAD because |
|---|---|---|
| `test_every_plot_type_draws_in_every_facet_panel` — parametrised over all 38 types × {`by(foreign)`, `by(foreign, total)`} | each faceted figure has ≥1 renderer, and its glyph type set equals the standalone figure's for the same plot | the 20 listed types produce a figure with zero renderers |
| `test_the_facet_chain_has_no_silent_fallthrough` | an AST/text walk of `ServerAppBuilder` output finds an explicit `else:` terminating both facet ladders | neither ladder has one (`dash_render.py:15201→15214`, twin `15302→15315`) |
| `test_ci_types_keep_their_band_under_by` — `lfitci`, `qfitci`, `fpfitci`, `lpolyci` | each panel carries a `VArea` renderer; for `fpfitci`, `fill_alpha == 0.2` | `lfitci`/`qfitci` draw nothing; `fpfitci`/`lpolyci` draw `Line` only |
| `test_by_total_panel_matches_the_group_panels_in_glyph_types` | the `by(total)` figure's glyph-type set equals a per-group panel's | the twin ladder has the same 20 holes |

**Unit tests (rule 4).** One test per newly reached mapper call path, in
`test/test_glyphs.py` alongside the existing mapper tests: for each of the 22 types
(20 blank + `lpolyci` + `fpfitci`), assert that the faceted call passes the same
`(figure, frame, plot, options, scheme)` arguments the standalone call site passes, and
that the returned renderer list is non-empty on a frame restricted to one `by` group.

**Integration / cscript.** Add a `by()` server case to `test/test_server_build.cscript`
(and pair it with Phase 06's `test/test_server_by.cscript` if that file has landed; create
it here otherwise): `dash (rspike hi lo date) ..., by(region)` → `dash build, server` →
assert rc 0 **and** assert the built app draws. Per REMAINING.md, "No .cscript exercises
`by()` in server mode, so the whole blank-panel class of defect is unguarded at the Stata
level" — an rc-0 assertion alone reproduces exactly the hole that let this through, so the
cscript must inspect the built app, not just its return code. Extend
`test/test_layout_facets.py` with the faceted-server structural cases.

**Mutation proof.**

- Re-alias one delegation back to its old inline branch (e.g. point `rspike` at nothing) →
  `test_every_plot_type_draws_in_every_facet_panel[rspike]` must fail.
- Change `map_fpfitci`'s faceted call to `map_fpfit` → `test_ci_types_keep_their_band_under_by[fpfitci]` must fail.
- Delete the new `else:` from the per-group ladder →
  `test_the_facet_chain_has_no_silent_fallthrough` must fail.
- Restore the old `elif ptype in ('lpoly','lpolyci')` alias →
  `test_ci_types_keep_their_band_under_by[lpolyci]` must fail.

### Epic 7.B — Faceted layers keep their scheme and their options

**Failing test first — `test/test_server_facet_options.py` (new).**

| test | asserts | fails at HEAD because |
|---|---|---|
| `test_faceted_histogram_outline_matches_standalone` | faceted `Quad.line_color` equals the standalone value (white) and `fill_alpha == 1.0` | emitted `quad` passes no `line_color`; Bokeh defaults to `#1f77b4`, alpha 0.6 |
| `test_faceted_dropline_uses_the_scheme_line_width` | faceted dropline `Segment.line_width == 1.2` | hardcoded `line_width=1.0` at `dash_render.py:15199` |
| `test_faceted_bin_option_survives_a_filter_move` | build `(histogram mpg, bin(4))` + `by(foreign)` + a filter; invoke `_on_filter_change`; each panel's source still has 4 bars | registrations omit `'opts'`, so `agg.get('opts') or {}` re-bins to the default |
| `test_faceted_lfit_n_qfit_and_lpoly_options_survive_a_filter_move` | same for `lfit n()`, `qfit`, `lpoly bwidth()`/`degree()` | same root cause |
| `test_facet_agg_registrations_carry_no_dead_keys` | no registration writes a key `_on_filter_change` never reads (`'bins'`, `'bwidth'`, `'degree'`) | all seven per-group registrations do |

**Unit tests (rule 4).** For each of the seven registration sites and their seven twins,
a test that the emitted dict's key set equals the key set the consumer branch for that
`atype` reads at `dash_render.py:15609-15630`.

**Integration / cscript.** Extend `test/test_server_histogram_bins.py` with a faceted case
(the unfaceted one already exists) and add the faceted bin assertion to the `by()` server
cscript from 7.A.

**Mutation proof.**

- Remove `line_color` from the fixed faceted `quad` → outline test fails.
- Set the faceted dropline width back to `1.0` → line-width test fails.
- Drop the `'opts'` key from the faceted histogram registration → bin-survival test fails.
- Re-add `'bins': 20` to a registration → dead-key test fails.

### Epic 7.C — A guard that compares numbers

**Failing test first — inside `test/test_mode_parity.py`.** Write the data comparison
*before* Phases 05/07 fix the underlying grids, and confirm it goes red on the two
divergences REMAINING.md already measured:

| test | asserts | fails at HEAD because |
|---|---|---|
| `test_the_two_modes_agree_on_data_values` (extends `TestTheTwoModesAgree`) | for every corpus case, each renderer's `data_source.data` matches column-for-column, length-for-length, within tolerance | kdensity is 300 points standalone vs 200 served; fpfit/fpfitci 10 vs 200 |
| `test_chrome_includes_title_axes_scale_and_legend` | `_chrome` returns title, axis labels, axis scale type and legend visibility | `_chrome` returns four keys only |
| `test_an_unused_allowance_is_a_failure` | every `ALLOWED` key was consulted by at least one comparison during the run | `ALLOWED` gates no comparison at all |
| `test_an_unlisted_difference_fails` | an injected difference with no `ALLOWED` key fails the case | nothing compares data, so the injection is invisible |

**Unit tests (rule 4).** `_glyph_profile`, the new `_data_profile`, `_chrome` and the
`ALLOWED` lookup each get a direct unit test over synthetic Bokeh figures — the helper
functions are the ones everything else in the file depends on, and they are currently
untested in isolation.

**Non-vacuity, stated as a standing requirement.** `test/test_mode_parity.py` reported
**165 passed** while kdensity and fpfit/fpfitci disagreed inside its own corpus. After this
phase, the following mutations must each turn the file red:

- change `_compute_kdensity`'s `n_pts` in the emitted app (currently 200,
  `dash_render.py:13380`) or `map_kdensity`'s `n` default (300.0, `dash_render.py:4806+`);
- change the emitted `_compute_fpfit` linspace count (`dash_render.py:13502`);
- change a figure title composition on either side;
- delete any `ALLOWED` entry;
- add an `ALLOWED` entry no comparison uses.

**Interaction with Phases 06 and 08.** This epic changes comparison **helpers**; Phase 06
item 5 and Phase 08 item 8 change the **corpus**. Land the helper changes first so the
widened corpus is measured by the stronger guard; coordinate the edit to
`test/test_mode_parity.py:CORPUS` (~line 186) to avoid a three-way conflict.

---

## Definition of done

A reviewer can tick each of these:

- [ ] Both emitted facet chains (`dash_render.py:15137-15230` and `15237-15330`) delegate
      to `_DASH_MAPPER`; no hand-written drawing code remains in either.
- [ ] All 20 previously blank types (`function`, `lfitci`, `mspline`, `pcarrow`,
      `pcbarrow`, `pci`, `pcscatter`, `pcspike`, `qfitci`, `rarea`, `rbar`, `rcap`,
      `rcapsym`, `rconnected`, `rline`, `rscatter`, `rspike`, `scatteri`, `tsline`,
      `tsrline`) draw in `by()` and in `by(total)` panels.
- [ ] `lpolyci` → `map_lpolyci` and `fpfitci` → `map_fpfitci`; all four CI types
      (`lfitci`, `qfitci`, `fpfitci`, `lpolyci`) carry a `VArea` in every faceted panel;
      `fpfitci`'s band is at fill_alpha 0.2.
- [ ] Both facet ladders end in an explicit `else:` that reports an empty layer; no silent
      fall-through remains.
- [ ] Faceted `Quad` carries the standalone `line_color` and `fill_alpha` 1.0; faceted
      dropline stems are at the scheme's 1.2.
- [ ] All 14 faceted aggregate registrations carry `'opts'`; the dead `'bins'`, `'bwidth'`
      and `'degree'` keys are gone.
- [ ] A faceted `histogram ..., bin(4)` still shows 4 bars after a widget move; likewise
      faceted `lfit n()`, `qfit`, `lpoly bwidth()`/`degree()`.
- [ ] `test/test_mode_parity.py` compares `data_source.data`; the kdensity and
      fpfit/fpfitci divergences it previously passed are now detected (or fixed upstream
      and asserted).
- [ ] `_chrome` compares title, axis labels, axis scale type and legend visibility.
- [ ] `ALLOWED` gates a real comparison; an unused allowance and an unlisted difference
      both fail.
- [ ] Every test above was observed **failing before** its fix and passing after (rule 8),
      and each mutation listed in the test plan was observed turning the relevant test red.
- [ ] A `by()` server-mode case exists in the certification suite and inspects the built
      app, not only its return code.
- [ ] Standalone-mode output is unchanged: the standalone half of every corpus case matches
      its pre-phase profile.
- [ ] Full pytest and the full certification suite pass with honest skips; the parity
      corpus gate is green (project rule 5).
- [ ] `REMAINING.md` is untouched.

---

## Risks and sequencing notes

**Sequencing inside the 15-03 family.** Phases 05, 06, 07 and 08 all edit
`dash_render.py`'s emitted-app region and `test/test_mode_parity.py`. The safe order is
**05 → 06 → 07 → 08**: Phase 05 establishes the delegation convention in the main loop
(so this phase copies a pattern rather than inventing one), Phase 06 unifies the facet
loops onto `_expand_by_groups` and fixes `_fac_kw`'s graph options (so the figures this
phase draws into are already correct), then this phase fills the dispatch, then Phase 08
widens the corpus. Landing 07 before 06 is possible but means writing the delegations
against a facet loop that is about to be replaced — rework, not risk.

**Item overlap is deliberate, not duplication.** Items 3 and 6 target the same two branch
pairs. Implement once; verify twice — item 3's acceptance is "the branch no longer aliases"
(a code-shape assertion), item 6's is "the band is present in all four CI types" (a
rendered-output assertion). Keep both tests; they fail for different reasons.

**Behaviour change is the point, and must be announced.** Twenty plot types go from
drawing nothing to drawing something, and eight more change appearance under `by()`.
`15-04`'s action already requires the CHANGELOG to "[r]ecord ... that server-mode output
changes substantially ... because it is now correct rather than a drifted copy". Any
dashboard a user has built against the blank-panel behaviour will look different after
this phase. That is a fix, not a regression, but it belongs in the release note (Phase 31).

**The guard change can turn the suite red before the fixes land.** TR-07.12 will expose
the kdensity (300 vs 200) and fpfit/fpfitci (10 vs 200) divergences that live in the
*existing* corpus and are owned by Phase 05 item 4 and Phase 08 item 5. Plan for one of
two dispositions, chosen deliberately and not by accident: either land those two fixes
first, or add each as a **temporary, dated `ALLOWED` entry naming the owning phase** — and
note that TR-07.14(b) makes an allowance that outlives its fix fail as dead, which is the
mechanism that stops a temporary entry becoming permanent.

**Scope discipline.** Four things that look adjacent are **not** in this phase: faceted
marker size/alpha and `msize()`/`msymbol()` (Phase 06 item 2); `_fac_kw`'s dropped graph
options (Phase 06 item 7); faceted `kdensity`/`lowess` option passing (Phase 06 item 8);
the faceted `mband` fourth binner and the facet-source `index` column that freezes
brush-updated KPIs (Phase 06 items 10 and 9). Fixing them here would collide with Phase 06
in the same emitted lines.

**`by(total)` is half the work and is easy to forget.** Every line number in this document
has a twin roughly 100 lines below it. A delegation landed in the per-group ladder and not
in the total ladder produces a dashboard where the group panels are right and the Total
panel is blank — a worse failure than the current one, because it looks like a data
problem rather than a code problem. Every test in 7.A is parametrised over both for this
reason.

**Performance.** The facet chains run once per group per plot. Delegating to `GlyphMapper`
replaces inline Bokeh calls with mapper calls that also resolve scheme properties and
translate options. On a high-cardinality `by()` this multiplies the per-panel cost. The
`by()` group cap noted against S12 in the status table is the mitigation; if a measurable
build-time regression appears on a wide `by()`, record it rather than reverting the
delegation.
