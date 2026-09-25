# Phase 06 — Server unification II: facet expansion and loop unification

**Purpose.** `ServerAppBuilder` emits a `bokeh serve` application whose `by()` and
`by(total)` handling is a hand-written re-implementation of work `DashRenderer` already
does. Task 15-03 asked for the third and fourth copies of the dispatch to be deleted;
they are both still there. The consequence is not cosmetic: under `by()` the served
dashboard silently drops graph options, statistical options, Stata value labels and
display formats, freezes a median band at its first-render values, breaks brush-driven
KPIs, and draws confidence-band plot types as bare lines. Every one of those defects is
invisible at the Stata prompt — the build returns rc 0 and writes a file. This phase
replaces the facet loops' bespoke spine (group splitting, suboption parsing, labelling,
figure construction, source construction) with the shared `_expand_by_groups` /
`_facet_label` path, brings the facet glyph and refresh wiring up to what the
non-faceted server loop already honours, and closes the two guard holes that let the
whole class through: a parity corpus with zero `by()` entries and a certification suite
with no server-mode `by()` case at all.

---

## At a glance

| | |
|---|---|
| **Ultraplan task** | 15-03 — *Collapse the glyph dispatch tables to one* (S15; shared with Phases 05, 07, 08) |
| **Items** | 12 |
| **Functional / deliverable** | 10 functional · 2 deliverable |
| **Effort mix** | 8 small · 4 medium · 0 large |
| **Renderers touched** | server ×10 · both ×1 (parity corpus) · Stata/cscript ×1 |
| **Primary files** | `dash_render.py` (emitted facet regions 15016-15110, 15137-15230, 15218-15240, 15237-15330), `test/test_mode_parity.py`, `test/test_server_build.cscript` (or new `test/test_server_by.cscript`) |
| **Sections discharged** | S15 (partial — 15-03 is split across Phases 05-08) |
| **Depends on** | **Phase 05** (main-loop delegation to `_DASH_MAPPER`; the `_compute_*` collapse). Phase 06 reuses the delegation pattern Phase 05 establishes. |
| **Unblocks** | **Phase 07** (the 20 plot types that draw nothing under `by()` — the routing this phase builds is the mechanism), **Phase 08** (the parity guard, which needs `by()` cases to guard), **Phase 13** (Formats II — facet titles and marker labels) |
| **Runs in parallel with** | Phases 17-22 (the option surface, `dash.ado` work) — disjoint files |

---

## Why this phase exists

### The collapse is 1/46 done, and the facet loops are two of the four copies

From `REMAINING.md` §4 and Appendix A (measured at HEAD, not read off the CHANGELOG):

> **The collapse is 1/46 done.** `ServerAppBuilder` holds **51 `ptype ==`
> comparisons** across ~4,000 emitted lines; exactly **one** (`scatter`) delegates to
> `_DASH_MAPPER`. 39 `map_*` methods exist.

And, specifically for this phase (Appendix A, 15-03, *Remaining* item 2):

> **The `by()` and `by(total)` facet loops were never unified.** The task requires them
> to become the same facet-expansion code the standalone path uses. `_expand_by_groups`
> occurs 3× in `DashRenderer` and **0×** in the emitted app, which still carries its own
> `by_total` handling. The third and fourth copies the task set out to delete are both
> still there.

Appendix B states the item this phase leads with:

> **[func · server · M]** Unify the by() and by(total) facet loops with
> `_expand_by_groups` instead of leaving a third and fourth copy. The emitted app
> re-implements group splitting, suboption parsing (`total`/`missing` by ad-hoc regex),
> qualifier application and facet labelling inline; `_expand_by_groups` is not copied
> into the app at all. *Where:* `dash_render.py:DashRenderer._expand_by_groups (8776)
> and _facet_label (8872) are the targets; the duplicates are emitted at
> dash_render.py:15016-15110 (by) and 15218-15240 (by total)`

### What the duplication costs, measured

`REMAINING.md` Appendix B, *Three findings worth pulling out first*, finding 1:

> **1. 20 plot types are broken in server mode.** Measured by building the emitted app
> from a spec and counting glyph renderers, with spec shapes taken from `dash.ado`'s own
> emission:
>
> - **Draw nothing at all:** `function`, `pci`, `tsrline`.
> - **Draw nothing under `by()`** (they work without it): `lfitci` `qfitci` `mspline`
>   `tsline` `rarea` `rbar` `rcap` `rline` `rscatter` `rspike` `rconnected` `rcapsym`
>   `pcspike` `pcarrow` `pcbarrow` `pcscatter` `scatteri` — 17 of them.
>
> This is 15-03's unfinished collapse showing through: the `by()` and `by(total)` facet
> loops are hand-written copies that only ever learned a subset of the plot types.

(The 17-type blank-panel class is **Phase 07**'s work item. It is quoted here because it
is the same two emitted regions and the same root cause: Phase 06 builds the spine that
Phase 07 routes the glyph chain through.)

Beyond the types that draw nothing, the facet loops diverge on what they *do* draw:

| defect | emitted code | what the non-faceted path does |
|---|---|---|
| marker size / alpha | `size=6`, alpha left at Bokeh's 1.0 (`:15144`, twin `:15245`) | scheme marker size; `msize()`/`msymbol()` honoured |
| graph options | `_fac_kw` = title + var_labels + tools + sizing_mode only (`:15121-15131`) | `xtitle()`/`ytitle()` (`:13832-13836`), `xscale(log)`/`yscale(log)` (`:13977-13980`), `note()`/`caption()`/`subtitle()` (`:13920+`) |
| `by(total)` figure | `bokeh_figure(title='Total', ...)`, **no axis labels at all** (`:15228-15235`) | full construction at `:13826-13990` |
| `kdensity` / `lowess` options | `_compute_kdensity(_fac_gdf, _kdvar)` (`:15170`), `_compute_lowess(_fac_gdf, yvar_f, xvar_f)` (`:15175`) — options argument omitted | non-faceted branches pass `opts`; both helpers take `options=None` (`:13354`, `:13396`) |
| `lpolyci` / `fpfitci` | aliased to the band-less sibling: `elif ptype in ('lpoly','lpolyci')` (`:15179`), `elif ptype in ('fpfit','fpfitci')` (`:15186`) | `GlyphMapper.map_lpolyci` / `map_fpfitci` draw band + line |
| `mband` | fourth inline binner, anonymous `ColumnDataSource({'x_mb': _xm, 'y_mb': _ym})` (`:15205-15213`) | shared `_compute_mband` (`:13524`), source registered for refresh |
| facet titles | value-label lookup only, and that lookup misses (`:15085-15097`) | `_facet_label` (`:8872`): `%t*` dates, numeric `%fmt`, value labels **with a by-variable-name fallback** |
| brush → KPI | facet sources carry no `index` column (`:15111-15113`, `:15221-15223`); wiring skips them (`:15727-15729`) | non-faceted shared source carries `index`, so `update(brush)` fires |

### The two guard holes that let all of this through

`REMAINING.md` §4:

> **The guard is narrower than it reads.** The parity corpus is 32 cases over
> **17 distinct plot types**, against **36 server `ptype` branches** — so **19 types are
> unguarded** (`fpfit` `fpfitci` `function` `lfitci` `lowess` `pcbarrow` `pci` `pcspike`
> `qfit` `qfitci` `rarea` `rbar` `rcap` `rconnected` `rline` `rscatter` `rspike`
> `tsline` `tsrline`). It also never constructs a spec with `by()`, KPIs, `filter()`,
> `link()` or `tabs()` — grep for each of those keys in the corpus returns 0.

and, at the Stata layer (Appendix C):

> **[deli · dash.ado · M]** No .cscript exercises `by()` in server mode, so the whole
> blank-panel class of defect is unguarded at the Stata level. The auditor's corpus item
> correctly says test_mode_parity.py has zero by() entries, but stops at pytest; the
> same hole exists in the certification suite, which is the layer that would have caught
> `dash ... by(foreign)` + `dash build, server` producing an rc-0 blank dashboard.

At HEAD the suite is green — **3,498 passed / 37 skipped; 25/25 cscripts**
(`REMAINING.md`, *Gates still to pass*). Every defect in the table above is inside that
green.

### The value-label defect, in full

This is the commonest case of all — `by(foreign)` on `auto.dta` — and the auditor's own
item under-stated it. From Appendix C:

> **[func · server · S]** Server facet titles drop Stata VALUE LABELS, not merely
> `%fmt`/`%t*` formats. The auditor's facet-label item says the emitted builder
> 'consults value labels only', which implies value labels work; they do not, on the
> commonest case of all (`by(foreign)` on auto.dta). Root cause is a key-space mismatch
> the emitted copy inherited without the standalone's fallback: the emitted code does
> `_lset = val_label_names.get(_bv)` then `_vl = val_labels.get(_lset)`, but jsonio keys
> `valueLabels` by VARIABLE name, so the lookup is `val_labels['origin']` against a dict
> keyed `{'foreign': {...}}` and misses. `DashRenderer._facet_label` has the fallback
> (`candidate = self.value_labels.get(var, {})`) and the emitted copy does not.

Confirmed at source. The emitted builder (`dash_render.py:15085-15097`):

```python
"            _fac_parts = []",
"            for _bv, _bval in zip(by_vars, _fac_vals):",
"                if pd.isna(_bval):",
"                    _fac_parts.append('Missing')",
"                    continue",
"                _lset = val_label_names.get(_bv, '')",
"                _vl = val_labels.get(_lset, {})",
"                _sv = str(_bval)",
"                _iv = str(int(_bval)) if isinstance(_bval, float) and _bval == int(_bval) else _sv",
"                _fac_parts.append(html.escape(_vl.get(_sv) or _vl.get(_iv) or _sv))",
```

`DashRenderer._facet_label` (`dash_render.py:8872`), which the emitted copy was derived
from and then fell behind:

```python
            _kind = getattr(self, "date_vars", {}).get(var)
            if _kind:
                parts.append(self._format_date_value(val, _kind))
                continue
            _numfmt = getattr(self, "numeric_formats", {}).get(var, "")
            if _numfmt:
                parts.append(_format_stata_numeric(val, _numfmt).strip())
                continue
            labelset = self.value_label_names.get(var, "")
            vlabels = self.value_labels.get(labelset, {}) if labelset else {}
            # Fallback: some callers key valueLabels by variable name rather
            # than label-set name (e.g. regen scripts that pre-date the
            # standard Stata jsonio format).
            if not vlabels:
                candidate = self.value_labels.get(var, {})
                if isinstance(candidate, dict):
                    vlabels = candidate
```

Three behaviours — date formatting, numeric `%fmt`, and the by-variable-name fallback —
exist in one copy and not the other. That is the entire argument for this phase: the
copies do not stay equal, and nothing notices when they stop.

### The brush defect, in full

The brush wiring, confirmed at `dash_render.py:15718-15733`:

```python
"    if any(k.get('update', 'filter') in ('brush', 'both')",
"           for k in kpi_defs):",
"        _brush_wired = set()",
"        for _bsrcs in graph_sources.values():",
"            for _bsrc in (_bsrcs if isinstance(_bsrcs, list) else [_bsrcs]):",
"                if id(_bsrc) in _brush_wired:",
"                    continue",
"                if 'index' not in getattr(_bsrc, 'data', {}):",
"                    continue",
```

The `index` guard is deliberate and correct — the comment immediately above it says a
selection on binned or fitted points "ha[s] no row identity, and mapping a selection on
them back to observations would produce a confident, wrong number". The bug is that the
*raw-data* facet source is built without `index` (`:15111-15113`, and the `by(total)`
twin at `:15221-15223`), so a source that **does** have row identity is skipped along
with the ones that do not.

### The fourth median band

From Appendix C, confirmed verbatim at `dash_render.py:15205-15213`:

```python
"                elif ptype == 'mband':",
"                    if xvar_f and yvar_f:",
"                        _mb_d = _fac_gdf[[xvar_f, yvar_f]].dropna() if xvar_f in _fac_gdf.columns and yvar_f in _fac_gdf.columns else None",
"                        if _mb_d is not None and len(_mb_d) >= 4:",
"                            _mb_x = _mb_d[xvar_f].values; _mb_y = _mb_d[yvar_f].values",
"                            _n_b = int(np.clip(int(np.ceil(len(_mb_x)/5)), 2, 20))",
"                            _x_e = np.linspace(_mb_x.min(), _mb_x.max(), _n_b+1)",
"                            _xm, _ym = [], []",
"                            for _bi in range(_n_b):",
"                                _s = (_mb_x >= _x_e[_bi]) & ((_mb_x < _x_e[_bi+1]) if _bi < _n_b-1 else (_mb_x <= _x_e[_bi+1]))",
"                                if _s.sum(): _xm.append(float(0.5*(_x_e[_bi]+_x_e[_bi+1]))); _ym.append(float(np.median(_mb_y[_s])))",
"                            if _xm:",
"                                _fac_fig.line('x_mb', 'y_mb', source=ColumnDataSource({'x_mb': _xm, 'y_mb': _ym}), line_width=_SCHEME_LINE_WIDTH, color=color, legend_label=yvar_f)",
```

The source is anonymous: it is registered in neither `graph_sources` nor `agg_sources`,
so `_on_filter_change` (`:15609-15630`) cannot find it. **A faceted mband is frozen at
its first-render values for the life of the session.** `TR-15.3` asked for one binner;
this is the copy that was left.

### One detail the audit did not have to state, confirmed while writing this

The emitted facet chain already has scheme constants in scope and uses them
inconsistently: the `dot` branch draws at `size=_SCHEME_MARKER_SIZE` while `scatter`
(`:15144`), `connected` and `dropline` in the same `elif` chain hardcode `size=6`, and
every line branch uses `_SCHEME_LINE_WIDTH` while the facet `dropline` stem hardcodes
`line_width=1.0`. So the fix for item 2 is not blocked on plumbing — the value is
already there, three branches simply do not read it.

---

## Epics

| epic | goal | items |
|---|---|---|
| **6.A — One facet expander** | The emitted app splits groups, parses `by()` suboptions and builds facet labels with the same code `DashRenderer` uses; the third and fourth copies are deleted. | 1, 3, 4, 11 |
| **6.B — A facet panel is the main panel, restricted** | Everything the non-faceted server loop honours — figure options, glyph styling, statistical options, live refresh, brush identity — survives `by()`. | 2, 6, 7, 8, 9, 10 |
| **6.C — Guard the facet paths** | `by()` and `by(total)` are covered at both layers: the pytest parity corpus and the Stata certification suite. | 5, 12 |

---

## User stories

### Epic 6.A — One facet expander

**US-6.A.1** — *As a Stata user pasting a `twoway` command*, I want `dash scatter mpg
weight, by(foreign)` served with the panels titled **Domestic** and **Foreign**, so that
the dashboard reads the way my `twoway` graph does instead of showing the raw codes 0
and 1.

> **Given** `auto.dta` with a value label attached to `foreign`
> **When** I run `dash scatter mpg weight, name(g1) by(foreign)` then `dash build,
> server saving(app.py)` and open the served app
> **Then** the two panel titles read `<graph title> — Domestic` and `<graph title> —
> Foreign`
> **And** the same command built with `dash build, saving(x.html)` produces the same two
> titles.

**US-6.A.2** — *As a Stata user*, I want `by(dateqtr)` and `by(income)` panel titles
formatted through the variable's Stata display format, so that a quarterly facet reads
`2022q3` and not `251`.

> **Given** a by-variable carrying a `%tq` date format, and another carrying `%9.0fc`
> **When** the dashboard is built in server mode
> **Then** each facet title is rendered through the same date/numeric formatting branch
> `DashRenderer._facet_label` uses (`dash_render.py:8896` and the numeric branch below
> it).

**US-6.A.3** — *As a dashboard viewer*, I want the `by(, total)` panel to carry the
graph's title like every other panel, so that I can tell which graph the totals belong
to when several faceted graphs share a page.

> **Given** a graph with `title("Mileage by origin")` and `by(foreign, total)`
> **When** the served page renders
> **Then** the total panel is titled `Mileage by origin — Total`, composed by the same
> code that composes `Mileage by origin — Domestic`
> **And** when the graph has no title, the panel is titled `Total`.

**US-6.A.4** — *As a package maintainer*, I want exactly one implementation of `by()`
group splitting and suboption parsing in the codebase, so that the next fix to `by()`
lands once and reaches both renderers.

> **Given** the emitted app source
> **When** I search it for a second implementation of group splitting or `total`/
> `missing` suboption parsing
> **Then** there is none: the emitted app calls the copied `_expand_by_groups`
> **And** `by(foreign, missing)` and `by(foreign, total)` behave identically in both
> renderers because they are parsed by the same function.

### Epic 6.B — A facet panel is the main panel, restricted

**US-6.B.1** — *As a Stata user*, I want `xtitle()`, `ytitle()`, `note()`, `caption()`,
`subtitle()`, `xscale(log)`, `legend(off)`, `bgcolor()` and `aspectratio()` to apply to
my faceted panels, so that adding `by()` to a working command does not silently strip
every option but the title.

> **Given** `dash scatter mpg weight, name(g1) by(foreign) xtitle("Weight (lbs)")
> ytitle("MPG") note("Source: auto.dta") yscale(log)`
> **When** built in server mode
> **Then** each facet figure carries the axis titles, the note and the log y-scale
> **And** the `by(, total)` panel carries them too — it currently passes no axis labels
> at all (`dash_render.py:15228-15235`).

**US-6.B.2** — *As a Stata user*, I want `msize()`, `msymbol()` and the scheme's own
marker size and alpha to apply under `by()`, so that a faceted scatter is the same
scatter, split.

> **Given** `dash scatter mpg weight, by(foreign) msize(large) msymbol(T)` under
> `scheme(economist)`
> **When** built in server mode
> **Then** the facet markers carry the requested symbol and the resolved size/alpha
> **And** with no marker options, the size is the scheme's marker size — not the literal
> `6` at `dash_render.py:15144`.

**US-6.B.3** — *As a Stata user*, I want `kdensity ..., bwidth() kernel() n()` and
`lowess ..., bwidth()` to be honoured under `by()`, so that the faceted curve is the
curve I asked for.

> **Given** `dash (kdensity mpg, bwidth(2) kernel(epan2)), by(foreign)`
> **When** built in server mode
> **Then** `_compute_kdensity` is called with the plot's `options` dict
> **And** the served facet curve equals the standalone facet curve for the same spec.

**US-6.B.4** — *As a dashboard viewer*, I want `lpolyci` and `fpfitci` panels to show
their confidence bands, so that a panel that looks like a complete CI plot is one.

> **Given** `dash (fpfitci mpg weight), by(foreign)` and the same with `lpolyci`
> **When** built in server mode
> **Then** each facet contains a band renderer (`VArea`) **and** a line renderer, as
> `GlyphMapper.map_fpfitci` / `map_lpolyci` produce
> **And** the same holds for the `by(, total)` panel (`dash_render.py:15280`, `:15287`).

**US-6.B.5** — *As a `dash serve` operator*, I want a faceted median band to move when a
filter widget moves, so that the served page does not keep showing a stale line beside
freshly filtered points.

> **Given** a faceted graph containing `mband` and a `filter()` widget
> **When** the widget changes
> **Then** the mband source is recomputed by `_on_filter_change`
> **And** the mband source is registered in `agg_sources` with its `'opts'` key, so the
> recompute uses the same binning as the first render.

**US-6.B.6** — *As a `dash serve` operator*, I want a KPI declared `update(brush)` to
respond to a box-select inside a faceted panel, so that the number on the card matches
the selection a viewer just made.

> **Given** a dashboard with `by(foreign)` and a KPI declared `update(brush)`
> **When** a viewer box-selects points in either facet, or in the total panel
> **Then** the KPI recomputes from the selected rows
> **And** selecting on an aggregate (binned or fitted) source still does **not** drive
> the KPI — the row-identity rule at `dash_render.py:15720-15733` is preserved, not
> weakened.

### Epic 6.C — Guard the facet paths

**US-6.C.1** — *As a package maintainer*, I want the parity corpus to cover every plot
type and the four structural paths it never builds, so that a divergence between the two
renderers fails a test instead of reaching a user.

> **Given** `test/test_mode_parity.py`
> **When** the suite runs
> **Then** the corpus contains at least one case for each of the 21 currently missing
> types and at least one `by()`, one `by(total)`, one `tabs()`, one `link()`, one
> `filter()` and one KPI case
> **And** each new case asserts on glyph profile, annotations and chrome for both
> renderers.

**US-6.C.2** — *As a package maintainer*, I want a certification script that runs
`by()` through `dash build, server` in real Stata, so that an rc-0 blank dashboard fails
the cert suite instead of passing it.

> **Given** a clean Stata session with `dash` on the adopath
> **When** `test/test_server_by.cscript` runs `sysuse auto`, `dash scatter mpg weight,
> name(g1) by(foreign)`, `dash build, server saving(app.py)`
> **Then** rc is 0 **and** the written app is asserted non-blank: it contains one figure
> per group plus the total panel when requested, and at least one glyph call per panel
> **And** the script fails loudly if any panel is empty.

---

## Business requirements

| id | requirement | testable as |
|---|---|---|
| **BR-06.1** | Adding `by()` to a working `dash` command must not silently remove behaviour that command already had. Any option honoured by the non-faceted server path is honoured by the faceted one. | Option-by-option comparison of a faceted and non-faceted figure built from the same spec. |
| **BR-06.2** | A facet panel title must display what Stata would display for that group: the value label if one exists, else the display-formatted value, else the raw value. | Title string equality against `DashRenderer._facet_label` output for the same key. |
| **BR-06.3** | The `by(, total)` panel must be a first-class panel — same title composition, same figure construction, same glyph styling as the per-group panels. | Property diff between a total panel and a per-group panel from the same spec. |
| **BR-06.4** | The standalone and server renderers must produce equivalent output for a faceted spec, to the same standard the parity corpus applies to unfaceted specs. | `test/test_mode_parity.py` with `by()` / `by(total)` corpus entries. |
| **BR-06.5** | Statistical options (`bwidth()`, `kernel()`, `n()`, `range()`, `degree()`, `bin()`) must reach the computation under `by()`, and must survive the first filter interaction. | Numeric comparison of the facet source data before and after a widget change. |
| **BR-06.6** | A confidence-band plot type must draw its band or not be drawn at all — never a bare line that reads as a complete CI plot. | Renderer-count assertion per facet: band + line for `fpfitci`, `lpolyci`. |
| **BR-06.7** | Interactive features declared at the dashboard level (`update(brush)`, `filter()`) must work on faceted panels, without extending brush-driven KPIs to sources that lack row identity. | Brush callback attachment test on facet sources; negative test on aggregate sources. |
| **BR-06.8** | `by()` in server mode must be covered by the Stata certification suite, not only by pytest, because that is the layer a user's command actually travels. | A cscript that builds and asserts on the emitted app. |
| **BR-06.9** | The codebase must contain exactly one implementation of `by()` group expansion, suboption parsing and facet labelling. | Source-level structural test, in the shape of `test/test_layout_facets.py:TestFacetResolutionIsSharedNotDuplicated`. |
| **BR-06.10** | No change in this phase may weaken the emitted app's self-containment: it must not import `dash_render` at runtime. | Existing/forthcoming self-containment assertion (Phase 08 item 2). |

---

## Technical requirements

Line numbers below are `REMAINING.md`'s, which are current for a ~16,264-line
`dash_render.py`; the plan's own section files are stale (the file grew from ~10,455
lines). Where a symbol is named, prefer the symbol.

### Epic 6.A

**TR-06.1 — Extract the facet spine to shared, copyable helpers.**
`DashRenderer._expand_by_groups` (`dash_render.py:8776`) has the signature

```python
    def _expand_by_groups(
        self,
        graph_spec: dict,
        base_df: "pd.DataFrame | None" = None,
    ) -> "list[tuple[str, pd.DataFrame]]":
```

and returns `[("", df)]` when no `by()` is present, so callers iterate uniformly. It is
called at `dash_render.py:11403` (the `link()` path) and `:11436`. `_facet_label`
(`:8872`) is the labelling half. Both are **methods**, and the emitted app is required to
be self-contained (it may not `import dash_render`), so they must be reachable by the
same copy mechanism `ServerAppBuilder` already uses for `OptionTranslator`,
`SchemeParser` and `GlyphMapper` — `inspect.getsource` over a class/helper list at
`dash_render.py:12386-12410`.

Required shape: extract the bodies to module-level functions that take their state
explicitly —

- `_dash_expand_by_groups(df, graph_spec, *, value_labels, value_label_names, date_vars, numeric_formats)`
- `_dash_facet_label(by_vars, key, *, value_labels, value_label_names, date_vars, numeric_formats)`

— leave `DashRenderer._expand_by_groups` / `._facet_label` as thin wrappers so the three
existing standalone call sites and `test/test_layout_facets.py` keep working unchanged,
and add both new functions to the copied-helper list at `:12386-12410`. The emitted facet
regions then call the copied functions instead of re-implementing them.

*Note the inherited fragility:* `_glyph_layer_lines` calls `inspect.getsource` on three
classes and 15 helpers with no `try`/`except` (`dash_render.py:12386-12410`), so any
deployment where the source text is not on disk fails the **build** with a bare
traceback. Adding two helpers extends that surface; hardening it is Phase 08's item, and
this phase must not make it worse (no new import-time source reads outside that block).

**TR-06.2 — Delete the duplicated group-splitting and suboption parsing.** The emitted
copies to remove are `dash_render.py:15016-15110` (the `by()` spine: `work_df.groupby(
groupby_key, sort=True, dropna=False)`, the `by_missing` skip, the `_fac_parts` label
loop, `_fac_gvars` collection, the linked/unlinked source branch) and
`dash_render.py:15218-15240` (the `by(total)` spine). `total`/`missing` are currently
parsed by ad-hoc regex in the emitted app; after TR-06.1 they are parsed once, inside
`_expand_by_groups` (which does `import re as _re` and reads
`graph_opts.get("by")`).

**TR-06.3 — Facet titles must go through the full label path.** The emitted
`_fac_parts` loop at `:15085-15097` must be replaced by a call to the copied
`_dash_facet_label`, which supplies, in order:

1. `Missing` for `pd.isna(val)`;
2. the `%t*` date branch — `date_vars[var]` → `_format_date_value(val, kind)`
   (`dash_render.py:8896`);
3. the numeric branch — `numeric_formats[var]` → `_format_stata_numeric(val, fmt).strip()`;
4. the value-label branch with **both** key spaces: `value_labels[value_label_names[var]]`
   first, then the fallback `value_labels[var]` (`dash_render.py:8905-8913`), which is the
   key space jsonio actually writes;
5. `html.escape` on the resulting label;
6. `' / '.join(parts)` for multi-variable `by()`.

**TR-06.4 — `by(total)` title composition.** Replace the hardcoded
`bokeh_figure(title='Total', ...)` at `dash_render.py:15232` with the same composition
the per-group branch uses: `f'{_fac_title} — Total'` when the graph has a title,
`'Total'` when it does not — the em dash (`—`) is what the per-group branch emits
at `:15117-15120`.

**TR-06.5 — Facet names and registration are unchanged.** `_fac_name =
f'{gname}__by__{_fac_idx}'` and the total panel's `f'{gname}__by__{len(facet_entries)}'`
are consumed by the layout resolver — `test/test_layout_facets.py` asserts
`dr._resolve_layout_names("faceted") == ["faceted__by__0", "faceted__by__1"]`. The
naming scheme, `figures[_fac_name]`, `facet_entries.append((_fac_name, _fac_label))` and
`_facet_group_vals[_fac_name] = (by_vars, _fac_key)` must survive the refactor
untouched.

### Epic 6.B

**TR-06.6 — Build the facet figure the way the main loop does.** `_fac_kw`
(`dash_render.py:15121-15131`) currently passes `title`, `x_axis_label`, `y_axis_label`
(from `var_labels` of `plots[0]` only), `tools=[PanTool(), WheelZoomTool(),
BoxSelectTool(), LassoSelectTool(), ResetTool()]`, `sizing_mode='stretch_width'` and
`output_backend='webgl' if len(df) > _WEBGL_THRESHOLD else 'canvas'`. It must instead be
produced by the same construction the non-faceted server loop uses at
`dash_render.py:13826-13990`, which already honours:

| option | main-loop site |
|---|---|
| `xtitle()` / `ytitle()` | `dash_render.py:13832-13836` |
| `xscale(log)` / `yscale(log)` | `dash_render.py:13977-13980` |
| `note()` / `caption()` / `subtitle()` | `dash_render.py:13920+` |
| `xline()` / `yline()`, `legend(off)`, `aspectratio()`, `bgcolor()` | same block, `:13826-13990` |

The `by(total)` twin (`dash_render.py:15228-15235`) takes the same construction; today it
passes no axis labels whatsoever. Extract the main loop's figure construction into one
emitted helper (e.g. `_dash_build_graph_figure(g, go, …)`) and call it from all three
sites — main loop, per-group facet, total facet.

*Scope note, stated honestly:* `xlabel()`/`ylabel()` appear in the auditor's dropped
list, but the axis-label grammar is absent from the emitted app wholesale —
`_parse_axis_label` appears 4× in the renderer and **0×** in the emitted app
(`REMAINING.md` §4), which is **Phase 16**'s work. TR-06.6's obligation is therefore
*parity with the non-faceted server loop*: build facets through the shared helper, so
that when Phase 16 ports the grammar into that helper, facets inherit it with no further
change.

**TR-06.7 — Facet glyph styling.** `dash_render.py:15144` draws
`_fac_fig.scatter(xvar_f, yvar_f, source=_fac_src, size=6, color=color,
legend_label=yvar_f, **_glyph_kw)`; the `by(total)` twin at `:15245` is identical. The
literal `6` must become the resolved size — the scheme's marker size, overridden by
`msize()`, with `msymbol()` selecting the marker and alpha resolved rather than left at
Bokeh's 1.0. The correct source of those values is `GlyphMapper.map_scatter` via
`_DASH_MAPPER`, the same delegation the main loop's single delegated branch uses at
`dash_render.py:14090`. `_SCHEME_MARKER_SIZE` and `_SCHEME_LINE_WIDTH` are already in
scope in the emitted facet chain (the facet `dot` branch reads `_SCHEME_MARKER_SIZE`
today), so no new plumbing is required for the interim fix if full delegation lands with
Phase 07.

**TR-06.8 — Pass `opts` to the facet compute helpers.** Four call sites:

```
dash_render.py:15170   _compute_kdensity(_fac_gdf, _kdvar)            -> add opts
dash_render.py:15175   _compute_lowess(_fac_gdf, yvar_f, xvar_f)      -> add opts
dash_render.py:15271   (by(total) kdensity twin)
dash_render.py:15276   (by(total) lowess twin)
```

Both helpers accept it: `def _compute_kdensity(df, varname, options=None)` at
`dash_render.py:13354` and `def _compute_lowess(df, yvar, xvar, options=None)` at
`:13396`. Without it, `bwidth()`, `kernel()`, `n()` and `range()` are dropped the moment
`by()` is used.

**TR-06.9 — `lpolyci` and `fpfitci` under `by()`.** The facet chain aliases them to
their band-less siblings:

```
dash_render.py:15179   elif ptype in ('lpoly', 'lpolyci'):   -> _compute_lpoly + one .line('x_lp','y_lp',…)
dash_render.py:15186   elif ptype in ('fpfit', 'fpfitci'):   -> _compute_fpfit + one .line('x_fp','y_fp',…)
dash_render.py:15280 / 15287                                 -> the by(total) twins
```

Give `lpolyci` and `fpfitci` their own branches routed to `GlyphMapper.map_lpolyci` /
`map_fpfitci`, which draw band **and** line. `REMAINING.md` records this defect twice —
once in the Appendix C list this phase carries as item 6, once as the "Four CI plot types
lose their confidence band under `by()`" item Phase 07 carries. It is one defect; fixing
it here closes both entries, and the Phase 07 entry should be ticked by reference rather
than fixed twice.

**TR-06.10 — One median-band binner.** Replace the inline implementation at
`dash_render.py:15205-15213` and its twin at `:15306-15314` with a call to the shared
`_compute_mband` the main loop uses (`dash_render.py:13524`), and register the resulting
source in `agg_sources` keyed `(_fac_name, pi)` in the same shape the neighbouring facet
aggregate registrations use:

```python
agg_sources[(_fac_name, pi)] = {'source': _mbsrc, 'type': 'mband',
                                'yvar': yvar_f, 'xvar': xvar_f, 'opts': opts}
```

The `'opts'` key is required: `_on_filter_change` recomputes with `agg.get('opts') or
{}` (`dash_render.py:15609-15630`). (The *missing* `'opts'` key on the other seven facet
aggregate registrations — `:15156`, `:15161`, `:15166`, `:15172`, `:15177`, `:15184`,
`:15189` and the by(total) twins `:15257`-`:15290` — is Phase 07's item 4; land TR-06.10
in the same shape so the two fixes agree.)

**TR-06.11 — Row identity on facet sources.** The unlinked per-group source
(`dash_render.py:15111-15113`)

```python
"                graph_sources[_fac_name] = [ColumnDataSource(",
"                    {v: _fac_gdf[v].tolist() for v in _fac_gvars}",
"                ) if _fac_gvars else ColumnDataSource({})]",
```

and the `by(total)` source (`:15221-15223`, `{v: work_df[v].tolist() for v in
_tot_gvars}`) must carry an `index` column holding the original DataFrame index of each
retained row (`_fac_gdf.index.tolist()`, `work_df.index.tolist()`), because the brush
wiring at `:15720-15733` skips any source without one. The linked branch already uses
`shared_source` plus a `CDSView(filter=BooleanFilter(...))`, which inherits `index` and
needs no change. The `if 'index' not in …: continue` guard itself stays — it is what
keeps binned and fitted sources out of brush-driven KPIs, and the comment above it
(`:15714-15719`) explains why.

### Epic 6.C

**TR-06.12 — Parity corpus.** `test/test_mode_parity.py` holds `CORPUS` at `:187`
(the auditor cites `~186`), normalised at `:284` by
`CORPUS = [(c + ({},))[:4] for c in CORPUS]`, and consumed by `TestTheTwoModesAgree`
(`:289`). It compares 32 cases over 17 distinct plot types against 36 server `ptype`
branches. Add cases for the 21 user-facing types it never builds —

> `fpfit`, `fpfitci`, `function`, `lfitci`, `lowess`, `pcarrow`, `pcbarrow`, `pci`,
> `pcscatter`, `pcspike`, `qfit`, `qfitci`, `rarea`, `rbar`, `rcap`, `rconnected`,
> `rline`, `rscatter`, `rspike`, `tsline`, `tsrline`

— and at least one case for each structural path the corpus has zero of: `by()`,
`by(total)`, `tabs()`, `link()`, `filter()` and a KPI. Spec shapes must be taken from
`dash.ado`'s own emission (`yvar1`/`yvar2` for range plots, `expr` for `function`,
`points` for `pci`), as `REMAINING.md` §4 did when measuring the five live drifts.
Comparison helpers to reuse: `_glyph_profile` (`:131`; the auditor cites `:129`),
`_annotations` (`:150`), `_chrome` (`:178`), and the two builders `_standalone_figures`
(`:83`) / `_server_figures` (`:94`).

*Known limitation, not this phase's to fix:* `_glyph_profile` compares no **data**, and
`_chrome` omits figure title, axis labels, axis scale type and legend visibility — so
new `by()` corpus entries alone would not catch TR-06.6's figure-option losses. That
widening is Phase 08's item. Sequencing note in §Risks.

**TR-06.13 — Certification script.** No cscript exercises `by()` in server mode; 25
cscripts exist and `test/test_server_build.cscript` is the nearest neighbour (it asserts
that `dash build, saving(app.py) server` *returns* — its header documents the hang it was
written against). Add `test/test_server_by.cscript` (or extend `test_server_build`):

1. `sysuse auto, clear`;
2. `dash scatter mpg weight, name(g1) by(foreign)`;
3. `dash build, server saving("`app'")` — assert `_rc == 0`;
4. read the written app back and assert it is **not blank**: one figure per group, plus
   the total panel for the `by(foreign, total)` case, and at least one glyph call per
   panel;
5. assert the panel titles carry the value labels `Domestic` / `Foreign`, which is the
   defect in item 11;
6. repeat for a CI type (`fpfitci`) and assert both a band and a line are present, which
   is item 6.

Follow the project's cert conventions: `cscript "…" adodir ".."`, `capture which
jsonio`, `$dash_nobrowser` set, and register the script in
`test/run_all_cscripts.do`. A skip is not a pass — if Python or bokeh is unavailable the
script must report a skip that the runner's accounting sees.

---

## Work items

Each item is reproduced with the tag, *Where* and evidence from `REMAINING.md`.
`func` = user-visible behaviour gap; `deli` = a test, cscript or artefact the task asked
for. `B` = Appendix B (deep audit), `C` = Appendix C (adversarial pass).

---

**1. [func · server · M · B] Unify the `by()` and `by(total)` facet loops with
`_expand_by_groups` instead of leaving a third and fourth copy.**
The emitted app re-implements group splitting, suboption parsing (`total`/`missing` by
ad-hoc regex), qualifier application and facet labelling inline; `_expand_by_groups` is
not copied into the app at all.
*Where:* `dash_render.py:DashRenderer._expand_by_groups (8776)` and `_facet_label (8872)`
are the targets; the duplicates are emitted at `dash_render.py:15016-15110` (by) and
`15218-15240` (by total).
*Evidence:* `_expand_by_groups` occurs 3× in `DashRenderer` and **0×** in the emitted
app. → **TR-06.1, TR-06.2**

**2. [func · server · S · B] Facet glyphs ignore the scheme's marker size/alpha and
ignore `msize()`/`msymbol()` entirely** — the emitted facet loops hardcode `size=6` and
leave alpha at Bokeh's 1.0.
*Where:* `dash_render.py:15144` (`_fac_fig.scatter(..., size=6, color=color, ...)`) and
`dash_render.py:15245` (the `by(total)` twin).
*Evidence (confirmed at source):* the neighbouring `dot` branch in the same chain already
draws at `size=_SCHEME_MARKER_SIZE`, so the scheme value is in scope and unread.
→ **TR-06.7**

**3. [func · server · S · B] Facet titles ignore Stata display formats and date
formats.** The emitted label builder consults value labels only; `DashRenderer._facet_label`
also formats `%t*` date kinds and numeric `%fmt`.
*Where:* `dash_render.py:15085-15097` (emitted `_fac_parts` loop) vs
`dash_render.py:8872` `DashRenderer._facet_label` (its date branch at `8896`, numeric
branch just below). → **TR-06.3**

**4. [func · server · S · B] The `by(total)` panel drops the graph title.** The emitted
total branch hardcodes `title='Total'` where the per-group branch composes
`'<title> — <label>'`.
*Where:* `dash_render.py:15232` (`_tot_fig = bokeh_figure(title='Total', ...)`).
→ **TR-06.4**

**5. [deli · both · M · B] Extend the parity corpus to the paths 15-03 is about.**
It covers 17 of the 38 user-facing plot types and has zero `by()`, `by(total)`, `tabs()`,
`link()`, filter or KPI entries — i.e. it reaches one of the four duplicated code paths.
Missing types: `fpfit`, `fpfitci`, `function`, `lfitci`, `lowess`, `pcarrow`, `pcbarrow`,
`pci`, `pcscatter`, `pcspike`, `qfit`, `qfitci`, `rarea`, `rbar`, `rcap`, `rconnected`,
`rline`, `rscatter`, `rspike`, `tsline`, `tsrline`.
*Where:* `test/test_mode_parity.py:CORPUS` (line ~186; `:187` at time of writing) and
`TestTheTwoModesAgree` (`:289`). → **TR-06.12**

**6. [func · server · S · C] Under `by()` / `by(total)`, `lpolyci` and `fpfitci` draw
only the central line — the confidence band is dropped entirely.** The emitted facet
chains alias them to the plain fits: `dash_render.py:15179` `elif ptype in ('lpoly',
'lpolyci'):` calls only `_compute_lpoly` + `_fac_fig.line('x_lp','y_lp',...)`, and
`dash_render.py:15186` `elif ptype in ('fpfit', 'fpfitci'):` calls only `_compute_fpfit`
+ one `.line('x_fp','y_fp',...)`. The `by(total)` twins at `dash_render.py:15280` and
`15287` do the same. This is NOT covered by the auditor's blank-under-`by()` item
(`lpolyci` is not on that list — it draws, just half of it) nor by the main-loop
`fpfitci` item.
*Where:* `dash_render.py:15179` and `15186` (per-group facet chain),
`dash_render.py:15280` and `15287` (`by(total)` twin); targets are
`GlyphMapper.map_lpolyci` / `map_fpfitci`. → **TR-06.9**

**7. [func · server · M · C] Faceted server figures drop EVERY graph option except the
title.** `_fac_kw` (`dash_render.py:15121-15131`) builds the facet figure from title +
var_labels + tools + sizing_mode only, so `xtitle()`/`ytitle()`, `xscale(log)`/
`yscale(log)`, `note()`, `caption()`, `subtitle()`, `xline()`/`yline()`, `legend(off)`,
`aspectratio()`, `bgcolor()` and `xlabel()`/`ylabel()` are all silently ignored under
`by()`. The non-faceted server loop honours all of them (`dash_render.py:13832-13836`
for xtitle/ytitle, `13977-13980` for the log scales, `13920+` for note/caption/subtitle),
so this is facet-only. The `by(total)` twin at `dash_render.py:15228` is worse still — it
passes no axis labels at all.
*Where:* `dash_render.py:15115-15133` (`_fac_kw`/`_fac_fig`), `dash_render.py:15228-15235`
(`by(total)` twin); the correct construction to reuse is the main loop at
`dash_render.py:13826-13990`. → **TR-06.6**

**8. [func · server · S · C] Faceted `kdensity` and `lowess` ignore their options
entirely.** The facet branches call the compute helpers with the options argument
omitted — `_compute_kdensity(_fac_gdf, _kdvar)` (`dash_render.py:15170`, twin `15271`)
and `_compute_lowess(_fac_gdf, yvar_f, xvar_f)` (`dash_render.py:15175`, twin `15276`) —
although both helpers take `options=None` (`dash_render.py:13354`, `13396`) and the
non-faceted branches pass `opts`. So `bwidth()`, `kernel()`, `n()` and `range()` are
dropped the moment `by()` is used.
*Where:* `dash_render.py:15170, 15175, 15271, 15276`. → **TR-06.8**

**9. [func · server · S · C] A KPI declared `update(brush)` never fires on a faceted
panel in server mode.** The brush wiring skips any source without an `index` column
(`dash_render.py:15727-15729`, `if 'index' not in getattr(_bsrc, 'data', {}): continue`),
and the unlinked facet source is built as `ColumnDataSource({v: _fac_gdf[v].tolist() for
v in _fac_gvars})` (`dash_render.py:15111-15113`) and the `by(total)` source as
`{v: work_df[v].tolist() for v in _tot_gvars}` (`dash_render.py:15221-15223`) — neither
adds `index`. Brushing any panel of a `by()` dashboard therefore leaves the KPI frozen,
with no warning.
*Where:* `dash_render.py:15111-15113, 15221-15223` (facet sources);
`dash_render.py:15720-15733` (brush wiring). → **TR-06.11**

**10. [func · server · S · C] The facet loops contain a FOURTH inline median-band
implementation that also never refreshes.** `elif ptype == 'mband'` at
`dash_render.py:15205-15213` (twin at `15306-15314`) recomputes bin edges and medians
inline instead of calling the shared `_compute_mband` the main loop uses
(`dash_render.py:13524`), and draws from an anonymous `ColumnDataSource({'x_mb': _xm,
'y_mb': _ym})` that is registered in neither `graph_sources` nor `agg_sources` — so a
faceted mband is frozen at its first-render values for the life of the session. TR-15.3
asked for one binner; this is the copy that was left.
*Where:* `dash_render.py:15205-15213` and `15306-15314`; shared helper at
`dash_render.py:13524` `_compute_mband`. → **TR-06.10**

**11. [func · server · S · C] Server facet titles drop Stata VALUE LABELS, not merely
`%fmt`/`%t*` formats.** The auditor's facet-label item says the emitted builder
"consults value labels only", which implies value labels work; they do not, on the
commonest case of all (`by(foreign)` on `auto.dta`). Root cause is a key-space mismatch
the emitted copy inherited without the standalone's fallback: the emitted code does
`_lset = val_label_names.get(_bv)` then `_vl = val_labels.get(_lset)`, but jsonio keys
`valueLabels` by VARIABLE name, so the lookup is `val_labels['origin']` against a dict
keyed `{'foreign': {...}}` and misses. `DashRenderer._facet_label` has the fallback
(`candidate = self.value_labels.get(var, {})`) and the emitted copy does not.
*Where:* `dash_render.py:15092-15093` (emitted `_lset`/`_vl` lookup) vs
`dash_render.py:8905-8913` (`DashRenderer._facet_label`'s by-variable-name fallback).
→ **TR-06.3**

**12. [deli · stata · M · C] No `.cscript` exercises `by()` in server mode, so the whole
blank-panel class of defect is unguarded at the Stata level.** The auditor's corpus item
correctly says `test_mode_parity.py` has zero `by()` entries, but stops at pytest; the
same hole exists in the certification suite, which is the layer that would have caught
`dash ... by(foreign)` + `dash build, server` producing an rc-0 blank dashboard.
*Where:* `test/test_server_build.cscript` (or a new `test/test_server_by.cscript`); pair
it with the `by()`/`by(total)` entries the auditor asks for in
`test/test_mode_parity.py:CORPUS`. → **TR-06.13**

---

## Test plan

Project rule 8 governs the order: **for each defect, the regression test is written
first and must fail against HEAD**, then the fix makes it pass. Project rule 4 governs
coverage: every new or extracted function gets a unit test. Every test below names the
file it lives in and the mutation that must kill it — a test that survives its mutation
is vacuous and does not count.

### Epic 6.A — One facet expander

**Failing-first regression tests (write before any code moves):**

| test | file | asserts | fails at HEAD because |
|---|---|---|---|
| `test_server_facet_title_uses_the_value_label` | `test/test_mode_parity.py` (new `TestFacetsAgree`) | server facet titles for `by(foreign)` are `Domestic` / `Foreign` | emitted lookup uses the label-set key space (`:15092-15093`) and misses |
| `test_server_facet_title_formats_a_date_by_variable` | same | `by(dateqtr)` panel titles are `2022q3`-shaped, equal to standalone | emitted builder has no date branch |
| `test_server_facet_title_formats_a_numeric_by_variable` | same | `%9.0fc` by-variable titles carry the separator | emitted builder has no numeric branch |
| `test_the_total_panel_carries_the_graph_title` | same | total panel title is `'<title> — Total'` | `title='Total'` hardcoded at `:15232` |

**Unit tests (rule 4), for the extracted module-level helpers:**

- `test/test_layout_facets.py` — extend with direct tests of
  `_dash_expand_by_groups`: no-`by()` returns `[("", df)]`; single by-variable splits in
  sorted order; `by(a b)` produces tuple keys; `missing` suboption includes the NaN
  group and its absence excludes it; `total` suboption is parsed once and reported to
  the caller.
- `test/test_layout_facets.py` — direct tests of `_dash_facet_label` covering all five
  branches: `Missing`, date, numeric `%fmt`, value label via label set, value label via
  the variable-name fallback, and `' / '` joining for two by-variables.
- Structural test in the shape of the existing
  `TestFacetResolutionIsSharedNotDuplicated` (`test/test_layout_facets.py:254`): assert
  the emitted app source contains **no** second `groupby(` over the by-key and no second
  `total`/`missing` regex — i.e. the third and fourth copies are gone.

**Integration / cscript:** `test/test_server_by.cscript` step 5 (value-label titles).

**Mutation proofs:**

| break this | test that must die |
|---|---|
| delete the `candidate = self.value_labels.get(var, {})` fallback in the shared label helper | `test_server_facet_title_uses_the_value_label` (and the standalone twin) |
| return `'Total'` instead of the composed title | `test_the_total_panel_carries_the_graph_title` |
| make `_dash_expand_by_groups` drop the `missing` suboption | the missing-group unit test |
| re-inline a second `groupby` in the emitted facet region | the structural "no second copy" test |

### Epic 6.B — A facet panel is the main panel, restricted

**Failing-first regression tests:**

| test | file | asserts | fails at HEAD because |
|---|---|---|---|
| `test_faceted_figure_keeps_every_graph_option` | `test/test_graph_options.py` (server section) | faceted server figure carries `xtitle`, `ytitle`, note/caption/subtitle, log scale, `legend(off)` | `_fac_kw` passes four keys (`:15121-15131`) |
| `test_the_total_panel_has_axis_labels` | same | `by(, total)` figure's `xaxis.axis_label` / `yaxis.axis_label` are non-empty | `:15228-15235` passes none |
| `test_faceted_scatter_uses_the_scheme_marker_size` | `test/test_mode_parity.py` `TestFacetsAgree` | facet marker size equals standalone's under `economist`, and `msize(large)` changes it | literal `size=6` at `:15144`, twin `:15245` |
| `test_faceted_kdensity_honours_bwidth` | `test/test_server_statistics.py` (`TestKernelDensity`) | facet kdensity x/y differ between `bwidth(1)` and `bwidth(4)` | `opts` not passed at `:15170` |
| `test_faceted_lowess_honours_bwidth` | `test/test_server_statistics.py` (`TestLowess`) | same, for lowess | `opts` not passed at `:15175` |
| `test_faceted_fpfitci_draws_a_band` | `test/test_server_statistics.py` (`TestTheConfidenceBandIsTheRightWidth`) | facet figure has a band renderer **and** a line renderer | `:15186` aliases to `fpfit` |
| `test_faceted_lpolyci_draws_a_band` | `test/test_server_statistics.py` (`TestLocalPolynomial`) | same, for lpolyci | `:15179` aliases to `lpoly` |
| `test_faceted_mband_refreshes_on_filter_change` | `test/test_server_statistics.py` (`TestMedianBands`) | after a simulated widget change the mband source data changes | anonymous CDS at `:15213` is in no registry |
| `test_faceted_mband_uses_the_shared_binner` | same | facet mband x/y equal `_compute_mband` output for the same frame | fourth inline binner at `:15205-15213` |
| `test_brush_reaches_a_facet_source` | `test/test_server_brush.py` (`TestBrushReachesTheSourceThatIsDrawn`) | every facet raw-data source has a selection callback | facet sources lack `index` (`:15111-15113`) |
| `test_brush_still_skips_aggregate_sources` | same | binned/fitted sources have **no** selection callback | *passes at HEAD* — this is the guard that the fix must not break |

Note the last row: it is the one test in this phase that must be **green before and
after**. It encodes the row-identity rule the `index` guard exists for. Write it with the
others so the fix cannot quietly widen brushing to sources without row identity.

**Unit tests (rule 4):** the extracted `_dash_build_graph_figure` helper from TR-06.6
gets its own tests — one per option family (axis titles, scales, note/caption/subtitle,
legend, background, aspect ratio) — asserting the same figure comes back whether the
caller is the main loop, the per-group facet or the total facet.

**Integration:** `test/test_server_build_options.py` gains a `by()` build case; the
faceted end-to-end path is exercised by the cscript in Epic 6.C.

**Mutation proofs:**

| break this | test that must die |
|---|---|
| drop `note` from the shared figure helper | `test_faceted_figure_keeps_every_graph_option` |
| hardcode `size=6` again in the facet scatter branch | `test_faceted_scatter_uses_the_scheme_marker_size` |
| drop the `options` argument from the facet `_compute_kdensity` call | `test_faceted_kdensity_honours_bwidth` |
| map `fpfitci` back to `map_fpfit` | `test_faceted_fpfitci_draws_a_band` |
| omit the `'opts'` key from the facet mband registration | `test_faceted_mband_refreshes_on_filter_change` |
| stop writing `index` into the facet source | `test_brush_reaches_a_facet_source` |
| remove the `if 'index' not in …: continue` guard | `test_brush_still_skips_aggregate_sources` |

### Epic 6.C — Guard the facet paths

**Corpus extension (`test/test_mode_parity.py`):**

1. Add one `CORPUS` entry per missing type (21 of them), with spec shapes taken from
   `dash.ado`'s emission — `yvar1`/`yvar2` for range plots, `expr` for `function`,
   `points` for `pci`.
2. Add six structural entries: `by()`, `by(, total)`, `tabs()`, `link()`, `filter()`,
   and one KPI.
3. Each entry runs through the existing `_standalone_figures` (`:83`) /
   `_server_figures` (`:94`) pair and is compared with `_glyph_profile` (`:131`),
   `_annotations` (`:150`) and `_chrome` (`:178`).
4. Any deliberate difference goes in `ALLOWED` (`:55`) with a reason over 40 characters,
   which is what `TestTheAllowanceListIsExplicit` (`:388`) checks.

*Expected result at HEAD:* the new `by()` entries fail on facet glyph size, missing
bands, and dropped statistical options; the `function` and `pci` entries fail because
those types draw nothing in server mode (Phase 05/07's items). Failing entries that
belong to another phase are marked `xfail(strict=True)` with the owning phase named, so
the corpus lands green and flips to a hard failure the moment that phase's fix is wrong.

**Certification script (`test/test_server_by.cscript`), per TR-06.13:** six assertions
(rc, one figure per group, total panel present, at least one glyph per panel, value-label
titles, band + line for `fpfitci`), registered in `test/run_all_cscripts.do`, honest skip
when Python or bokeh is absent, `$dash_nobrowser` set before any build.

**Mutation proofs:**

| break this | test that must die |
|---|---|
| delete a plot type's facet branch so the panel is empty | the cscript's "at least one glyph per panel" assertion |
| revert the value-label fallback | the cscript's title assertion, and the corpus `by()` entry |
| revert any Epic 6.B fix | the corresponding corpus entry |
| remove a corpus entry | `TestTheTwoModesAgree`'s count assertion (add one if absent: the corpus must cover every server `ptype` branch) |

**Suite-level gate.** Per project rule 5, before any commit: pull local `main`, run the
full pytest suite and the full certification suite (`arch -arm64` from `test/`; a skip is
not a pass), and fix forward until green. The HEAD baseline to beat is **3,498 passed /
37 skipped; 25/25 cscripts**, plus the new tests.

---

## Definition of done

**Code**

- [ ] `_expand_by_groups` and `_facet_label` exist as module-level helpers, are copied
      into the emitted app by the `inspect.getsource` list at `dash_render.py:12386-12410`,
      and `DashRenderer` delegates to them (its three existing call sites unchanged).
- [ ] The emitted `by()` spine (`:15016-15110`) and `by(total)` spine (`:15218-15240`)
      no longer contain their own group splitting, suboption regex or label builder.
- [ ] Facet titles carry value labels (both key spaces), `%t*` dates and numeric `%fmt`.
- [ ] The `by(, total)` panel title is composed, not hardcoded.
- [ ] Facet and total figures are built by the same helper as the main server loop, and
      honour `xtitle`/`ytitle`, `xscale`/`yscale`, `note`/`caption`/`subtitle`,
      `xline`/`yline`, `legend(off)`, `aspectratio`, `bgcolor`.
- [ ] Facet scatter/connected/dropline marker size and alpha come from the scheme and
      from `msize()`/`msymbol()`; no literal `size=6` remains in the facet chains.
- [ ] `_compute_kdensity` and `_compute_lowess` receive `opts` at all four facet call
      sites.
- [ ] `lpolyci` and `fpfitci` have their own facet branches routed to
      `GlyphMapper.map_lpolyci` / `map_fpfitci`; band **and** line present in both the
      per-group and total panels.
- [ ] The facet `mband` calls the shared `_compute_mband` and registers its source in
      `agg_sources` with an `'opts'` key; the inline binner at `:15205-15213` and its
      twin are gone.
- [ ] Facet and total sources carry `index`; the `index` guard in the brush wiring is
      unchanged.

**Tests**

- [ ] Every defect above has a regression test that was demonstrated to fail at HEAD
      before the fix (rule 8), recorded in the commit message.
- [ ] Every extracted/new function has a unit test (rule 4).
- [ ] `test/test_mode_parity.py:CORPUS` covers all 36 server `ptype` branches and
      contains `by()`, `by(total)`, `tabs()`, `link()`, `filter()` and KPI entries.
- [ ] `test/test_server_by.cscript` exists, is registered in `test/run_all_cscripts.do`,
      and fails if any faceted panel is blank.
- [ ] Every new test proved non-vacuous by the mutation named in the test plan.
- [ ] Full pytest suite and full cert suite green; skips accounted for honestly.

**Records**

- [ ] `BUGS.md` gains an entry per defect fixed (items 2, 3, 4, 6, 7, 8, 9, 10, 11) —
      rule 8 and S16-07's reconciliation both want them recorded.
- [ ] CHANGELOG entry describing the facet unification, without naming the tool that
      wrote it (rule 7).
- [ ] Committed to `feature/batch4-interactive-layer` (or a phase branch off it), with
      the merge command reported rather than run (rule 6).

---

## Risks and sequencing notes

**1. Phase 05 first, or the delegation target keeps moving.** Items 2, 6 and 7 all end
in "route this through `_DASH_MAPPER` / the shared figure helper". Phase 05 delegates the
37 main-loop branches and establishes that pattern. Starting Phase 06 before Phase 05
means inventing the pattern twice.

**2. Phase 06 and Phase 07 edit the same two regions.** Phase 07 (the 20 types that draw
nothing under `by()`, the faceted histogram/dropline divergences, the missing `'opts'`
keys on seven facet aggregate registrations) rewrites the facet **glyph chain**;
Phase 06 rewrites the facet **spine** around it. Land Phase 06 first — the spine is what
Phase 07's chain plugs into — and expect to rebase Phase 07's work items on the new
structure. Running them in parallel will conflict on `dash_render.py:15016-15330`.

**3. One defect is recorded twice.** Item 6 here and Phase 07's "Four CI plot types lose
their confidence band under `by()`" are the same `fpfitci`/`lpolyci` aliasing, found by
two adversarial lenses. Fix once, here, and tick Phase 07's entry by reference. Do not
write two fixes or two tests for it.

**4. The parity corpus will go red before it goes green.** Adding `by()` entries in
Epic 6.C surfaces Phase 05's and Phase 07's defects as well as this phase's. Use
`xfail(strict=True)` with the owning phase named, so the corpus lands green, no failure
is hidden, and the `xfail` becomes a hard error the moment the other phase's fix is
wrong.

**5. New corpus entries alone will not catch the figure-option losses.** `_chrome`
(`test/test_mode_parity.py:178`) omits figure title, axis labels, axis scale type and
legend visibility, and `_glyph_profile` compares no data at all — the corpus reports
165 passed while `kdensity` (300 vs 200 points) and `fpfit`/`fpfitci` (10 vs 200)
diverge inside it. That widening is Phase 08's item. Until it lands, item 7's coverage
comes from the dedicated `test_faceted_figure_keeps_every_graph_option` test in
`test/test_graph_options.py`, not from the corpus. Do not mark item 7 done on a green
corpus.

**6. `xlabel()`/`ylabel()` will still be missing under `by()` after this phase, by
design.** The axis-label grammar is absent from the emitted app entirely
(`_parse_axis_label`: 4× in the renderer, 0× in the app) — Phase 16's work. TR-06.6's
contract is parity with the non-faceted server loop, so facets inherit the grammar
automatically when Phase 16 ports it into the shared figure helper. Say so in the
CHANGELOG rather than implying `by()` is fully fixed.

**7. `by()` still has no group cap.** `REMAINING.md` §6: "`by(id)` has no group cap —
`by(id)` builds one figure per value. (`_MAX_BY_GROUPS`/`_MAX_FACETS`/`_MAX_TABS`: not
defined.)" That cap is Phase 04's item. Unifying on `_expand_by_groups` is what makes the
cap land in one place and reach both renderers — so implement the cap *inside* the shared
expander when Phase 04 runs, and note the dependency in both directions.

**8. Copying two more helpers widens the `inspect.getsource` surface.**
`_glyph_layer_lines` reads source for three classes and 15 helpers with no `try`/`except`
(`dash_render.py:12386-12410`), so a byte-compiled-only or zipimported deployment fails
the **build** with a bare traceback. This phase adds two entries to that list; hardening
the mechanism is Phase 08's item. Do not add a second, separate source-reading path.

**9. The emitted app must stay self-contained.** `dash.sthlp` and the CHANGELOG both
promise the generated app imports nothing from `dash_render`. The fix for item 1 is a
**copy**, never an import — the temptation to `from dash_render import _expand_by_groups`
would be a regression against a documented property that Phase 08 is adding an assertion
for.
