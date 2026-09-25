# Phase 22 — Geometry, sizing and layout

**Purpose.** Section 10 gave `dash` a figure geometry that comes from the user's
option or the user's scheme, and section 12 gave every layout a guarantee that no
graph can vanish from a dashboard without an error. Both landed — and both stop
one step short of the edge of their own surface. The Bootstrap auto-layout decides
how many graphs go on a row from each figure's aspect ratio, but reads that ratio
with `figures.get(name)`, and a faceted graph is not stored under its own name, so
every `by()` panel counts as ratio `0.0` and the one case with the strongest shape
opinion is the one case the layout is blind to. The "no graph vanishes" guard is
called from exactly one place — the Bootstrap HTML path — so `layout(s1:1,1
s2:1,1)` still drops a graph in silence outside `layout(bs)`. The KPI-span test
section 10's own TDD stub named was never written in the contrasting form the stub
asked for, so the height-by-span rule is certified by an assertion that survives
its own removal. And three of the five options the plan dispositioned to this
section — `fxsize`, `fysize`, `scale` — are declared, serialized, reported as
ignored, and read by nothing: `fxsize` and `fysize` occur **0** times in
`dash_render.py`. This phase closes those four gaps: two in the Bootstrap
auto-layout, one in the layout guarantee, and one in the option surface.

---

## At a glance

| | |
|---|---|
| **Work items** | 4 |
| **Functional / deliverable split** | 3 functional (items 2, 3, 4) · 1 deliverable (item 1) |
| **Effort mix** | 1 small (item 1) · 3 medium (items 2, 3, 4) · 0 large |
| **Renderers touched** | standalone only: items 1, 2, 3 · both renderers: item 4 (`DashRenderer._resolve_aspect_ratio` **and** the `_fig_kw` block `ServerAppBuilder` emits at `dash_render.py:13839-13855`) |
| **Files touched** | `dash_render.py` (`_auto_bs_layout`, `_ar_of`, `_resolve_layout_names`, `_assemble_layout`, `_assert_every_graph_was_placed`, `_resolve_aspect_ratio`, `_cell_height_class`, `OptionTranslator._SIZE_MAP`, the emitted `_fig_kw`); `dash.ado` (the two `_dash_pending` blocks only); `test/test_geometry.py`, `test/test_layout_facets.py`, `test/test_layout_placement.py`, `test/test_mode_parity.py`, `test/test_unsupported_report_is_true.py`. Read-only: `test/test_geometry_visual.md`, `examples/geometry_responsive.do` |
| **Ultraplan coverage** | **S10** — section 10, *Figure geometry and layout sizing* (tasks 10-01 and 10-03, the two DONE claims the adversarial pass overturned). **S12** — section 12, *Layout, tabs, facets* (the one live defect left in the status table's row 12). **OPT-S10** — the `implement-S10` row of the option-surface audit: `fxsize` `fysize` `scale` |
| **Depends on** | **Phases 17 and 18** (the option surface), and softly — see *Risks*. The three S10 options are **already declared and serialized**; Appendix A's 05-04 table records `implement-S10 | 5 | 5 | 0` (five dispositioned, five declared, none undeclared). What Phase 18 owns is the abbreviation entry that makes `fxsiz(50)` reach the option rather than the `*` catch-all |
| **Unblocks** | **Phase 30** (help reconciliation — the sizing precedence must be documented once it has a third and fourth term) and **Phase 31** (release closeout — §7's *"Responsive verification at 375/768/1440px — S10's procedure, re-run against the current build"*, which must be re-run **after** this phase, not before) |

Where this phase sits in the audit's own accounting, copied from `REMAINING.md`:

| # | Section | Tasks | Status | What is left |
|---|---|---:|---|---|
| 10 | Geometry | 4 | 2 done, 2 partial ② | `fxsize` `fysize` `scale` ① |
| 12 | Layout, tabs, facets | 5 | 5 partial ② | `by()` group cap ①; `layout(s1:1,1 s2:1,1)` still drops a graph silently outside Bootstrap ② |

> Sources: ① measured this session; ② deep-audit agent; ③ CHANGELOG (self-reported).

And after the adversarial pass, from *Final tally* — DONE / PARTIAL / NOT DONE:

| S09 | **S10** | S11 | **S12** | S13 | S14 | S15 | S16 |
|---|---|---|---|---|---|---|---|
| 0/7/0 | **0/4/0** | 0/6/0 | **0/5/0** | 2/4/0 | 1/4/0 | 0/4/0 | 0/6/**1** |

The status table's "2 done, 2 partial" for section 10 is the earlier figure; the
final tally supersedes it, because the adversarial pass overturned both remaining
DONE claims. `REMAINING.md` names them in its list of *17 DONE claims the
adversarial pass overturned*:

| task | what the refutation found |
|---|---|
| 10-01 | the KPI-span test the section's own stub named is absent |
| 10-03 | facet ratios never thread into `_auto_bs_layout` |

Read PARTIAL the way `REMAINING.md` asks it to be read: *"it is not 'half-built'.
In most cases the audit found the defect the task was written against genuinely
fixed and proven load-bearing by mutation, with a secondary deliverable missing."*
It names section 12 as the clearest example — *"every one of the five named
defects is genuinely fixed at HEAD and I proved each fix load-bearing by
mutation"*; all five are PARTIAL on paperwork. Item 3 below is the one exception
in that section that is not paperwork.

---

## Why this phase exists

Everything in this section is copied from `REMAINING.md`, whose own preface says
every number in it *was measured, not read off the CHANGELOG*. A developer should
not need to open `REMAINING.md` to know what is broken here. Where a fact was
confirmed by reading the source at HEAD rather than quoted from the audit, it is
labelled **(confirmed in source)**.

### 1. The KPI-span test the section's own stub named is absent

Section 10's TDD stub list (`.ultraplan/sections/section-10-geometry.md`) names
nine tests. One of them is:

> - Test: a col-4 Bootstrap cell and a col-12 cell get different heights.

and task 10-03's action says, in the same file:

> Set Bootstrap cell heights from the span so a col-4 cell is not the height of a
> col-12 cell (TR-10.4), and add an `lg` tier to the
> `db-col-12 db-col-sm-12 db-col-md-N` chain.

The implementation exists. `_cell_height_class` at `dash_render.py:2391-2408`
(confirmed in source):

```python
def _cell_height_class(span: int) -> str:
    if span >= 12:
        return "lg"
    if span >= 6:
        return "md"
    return "sm"
```

and the stylesheet it keys into, at `dash_render.py:735-739`:

```css
.db-cell-h-sm{min-height:130px}
.db-cell-h-md{min-height:150px}
.db-cell-h-lg{min-height:170px}
@media(max-width:767px){
.db-cell-h-sm,.db-cell-h-md,.db-cell-h-lg{min-height:120px}
}
```

The class is attached to KPI cells only, at `dash_render.py:10825`:

```python
f'{" db-cell-h-" + _cell_height_class(span) if _is_kpi else ""}">'
```

What is missing is the **contrast**. The only test that reads a `db-cell-h-*`
class is `test/test_geometry.py:345` `test_a_kpi_cell_height_follows_its_span`,
and it renders exactly one arrangement — four KPI cards — then asserts
(`test/test_geometry.py:368-370`):

```python
kpi_cells = [c for c in self._emitted(html_text) if "db-cell-h-" in c]
assert kpi_cells, "KPI cells carry no height class"
assert all("db-cell-h-sm" in c for c in kpi_cells), kpi_cells
```

Four KPIs give `per_row = 4` and `span = 12 // 4 = 3`, so every cell is `sm` and
the assertion is single-sided: **`_cell_height_class` could return the constant
`"sm"` for every span and this test would still pass.** The stub's case — one KPI
at span 12 against four at span 3, two different classes — is the one that makes
the rule load-bearing, and it is absent. That is precisely what the refutation of
10-01 recorded.

The span arithmetic those two cases rest on is in `_auto_bs_layout`
(`dash_render.py:10538-10546`, confirmed in source), with the named constant
10-03 asked for — `_MAX_KPIS_PER_ROW = 4` at `dash_render.py:125`:

```python
per_row = min(n_kpis, _MAX_KPIS_PER_ROW)
span = max(1, 12 // per_row)
```

One KPI → `per_row = 1` → `span = 12` → `db-cell-h-lg`. Four KPIs → `per_row = 4`
→ `span = 3` → `db-cell-h-sm`.

### 2. Facet ratios never thread into `_auto_bs_layout`

This is the refutation of 10-03 in full: *"facet ratios never thread into
`_auto_bs_layout`"*.

The auto-layout's graph rows are explicitly derived from each figure's own
proportions — the comment at `dash_render.py:10550-10553` says so (confirmed in
source):

> Derived from each figure's OWN proportions, not from the count alone and not
> from the widest figure on the dashboard: a panel wide enough to need a full row
> should take one without pushing every other graph onto a row of its own.

```python
def _ar_of(nm):
    _f = (figures or {}).get(nm)
    _a = getattr(_f, "aspect_ratio", None) if _f else None
    return float(_a) if _a else 0.0

_wide = [n for n in graph_names if _ar_of(n) >= 2.5]
_rest = [n for n in graph_names if n not in _wide]
...
elif max((_ar_of(n) for n in _rest), default=0.0) >= 1.8:
    per_row = min(2, n_rest)
```

`_ar_of` looks the **registered graph name** up in `self.figures`. A faceted graph
is not there. `_resolve_layout_names`' own docstring at
`dash_render.py:10959-10966` states the storage rule:

> A faceted graph is stored under generated keys ``name__by__0``,
> ``name__by__1``, ... so a layout that looks the name up directly in
> ``self.figures`` misses it and drops the graph from the dashboard with no
> error. ``_build_tabs_widget`` consulted ``_facet_map`` and got this right; the
> Bootstrap grid did not. Two implementations of one lookup is how they
> diverged, so there is now one.

The keys are written at `dash_render.py:11407` and `:11453` as
`fkey = f"{name}__by__{idx}"`. `_render_bootstrap_html` passes `self.figures` —
figure keys — while `grid_names` are registered names
(`dash_render.py:10718-10721`), so for every faceted graph `_ar_of` resolves
`None` and returns `0.0`. A `by()` graph of ten wide panels and a `by()` graph of
four square ones are indistinguishable to the layout: both are "ratio 0", neither
is ever `_wide`, and neither can raise `per_row` to 2. The item's fix is to make
`_ar_of` resolve through `_facet_map` / `_resolve_layout_names` and take the
panels' common ratio.

The same class of lookup has already been fixed once for placement — that is what
`_resolve_layout_names` is — so this is the second consumer of the same idea, not
a new mechanism.

### 3. `layout(s1:1,1 s2:1,1)` still drops a graph in silence outside Bootstrap

From the status table, row 12, source ②:

> `layout(s1:1,1 s2:1,1)` still drops a graph silently outside Bootstrap

Section 12's task 12-02 called the guard *"the fix that matters"*:

> Then add the general guard this defect should never have survived: at the end of
> layout assembly, assert every registered graph name appears somewhere in the
> output, and raise a clear error naming any that does not. **This is the fix that
> matters** — defect 1 is one instance of a class, and the guard catches the rest.

The guard exists, and it is good (`dash_render.py:10982-11000`, confirmed in
source):

```python
missing = [k for k in self.figures if k not in placed_keys]
...
raise ValueError(
    "dash: the following graph(s) were built but never placed in the "
    "dashboard: " + ", ".join(names) + ". This is a layout defect in "
    "dash, not an error in your command; please report it with the "
    "layout() option you used."
```

It is called **once**, at `dash_render.py:10793`, inside `_render_bootstrap_html`.
The other half of `_assemble_layout` — the standard Bokeh `gridplot` path, which
is what `layout(auto)`, `layout(R C)` and `layout(name:row,col ...)` all take — is
unguarded. And that path has a silent drop in it (`dash_render.py:12046-12060`,
confirmed in source):

```python
if _placed:
    _slots = [[None] * cols_n for _ in range(rows_n)]
    for _nm, (_r, _c) in _placed.items():
        if 0 <= _r < rows_n and 0 <= _c < cols_n:
            _slots[_r][_c] = _by_name.get(_nm)
    # Anything the spec did not place fills the remaining cells in
    # registration order, which is what the Bootstrap path does.
    _free = [(r, c) for r in range(rows_n) for c in range(cols_n)
             if _slots[r][c] is None]
    for _nm in [n for n in _grid_names if n not in _placed]:
        ...
```

Two silent paths, both reachable:

1. **Collision.** Two names resolving to the same cell: the second assignment
   overwrites the first, and because the loser *is* in `_placed` it is not in the
   "fill the free cells" list either. It is simply gone.
2. **Out of range.** The `if 0 <= _r < rows_n and 0 <= _c < cols_n` has no `else`;
   a name outside the computed grid is skipped, and again is not re-queued.

Traced for the exact spec the audit names, `layout(s1:1,1 s2:1,1)` (confirmed in
source): `_placement_map` (`dash_render.py:11092-11128`) finds both pairs, sees no
zero index, treats the spec as 1-based and normalises both to `(0, 0)`.
`_compute_grid` returns `rows = max(r)+1 = 1`, `cols = 1`; `_assemble_layout`
grows `rows_n` to `ceil(2/1) = 2`. Both names write cell `(0,0)`, `s2` last. `s1`
is never drawn, `_free` holds `(1,0)` and is never used, the guard is never
called, and the build returns rc 0.

The existing coverage misses it by construction.
`test/test_layout_facets.py:191` `test_every_registered_graph_reaches_the_document`
is parametrised over `["auto", "bs", "1 2", "bs: plain=6 faceted=6"]` — the
placement form is not among them (confirmed in source), and the four direct guard
tests at `test/test_layout_facets.py:213-247` all call
`dr._assert_every_graph_was_placed(...)` by hand, which only ever exercises the
Bootstrap contract.

### 4. `fxsize` `fysize` `scale` — declared, serialized, reported, read by nothing

From §2 of the main body, *Blocker — the option surface*. Every one of the 115
options in `test/fixtures/rejected_options.json` was re-run through `dash` in Stata
at HEAD and classified by dash's own report:

| plan disposition | total | honoured | accepted + reported ignored |
|---|---:|---:|---:|
| accept-and-report | 4 | 0 | 4 ✅ *as intended* |
| implement-S06 | 3 | 0 | **3** |
| implement-S07 | 25 | 12 | **13** |
| implement-S09-axes-text | 28 | 2 | **26** |
| implement-S09-style | 50 | 3 | **47** |
| **implement-S10** | **5** | **2** | **3** |
| **total** | **115** | **19** | **96** |

> **0 rejections.** The drop-in claim holds at the syntax layer and decision 4
> (accept, never abort, report together) is satisfied — but **92 options the plan
> said to implement are only accepted and reported**, so their values never reach
> the spec.

And the family list:

> - **S10 (3):** `fxsize` `fysize` `scale`

The two honoured members of that row are `xsize` and `ysize` (confirmed in source:
`_resolve_aspect_ratio` reads them at `dash_render.py:9229-9230` via
`_stat_option_float(graph_opts, "xsize", ...)` / `"ysize"`). The three unhonoured
members are this phase's item 4.

The Stata half is **done**, which is why this is renderer work and not `dash.ado`
work. Appendix A's 05-04 cross-reference records it:

| disposition | total | declared | **not declared** |
|---|---:|---:|---:|
| implement-S10 | 5 | 5 | 0 |

Confirmed in source, the four places each option already reaches:

| stage | `fxsize` / `fysize` | `scale` |
|---|---|---|
| declared, graph block | `dash.ado:292-293` — `FXSIZE(string)` `FYSIZE(string)` | `dash.ado:293` — `SCALE(string)` |
| declared, plot block | `dash.ado:511` | `dash.ado:511` |
| reported pending (graph) | `dash.ado:367-368` | `dash.ado:375` |
| reported pending (plot) | `dash.ado:604-605` | `dash.ado:621` |
| serialized | `dash.ado:420-421` (`sreturn local fxsize` / `fysize`), `:747-748` (`g_fxsize` / `g_fysize`) | `dash.ado:422` (`sreturn local scale`) |
| **read by the renderer** | **`grep -c fxsize dash_render.py` → 0**, `fysize` → 0 | no `"scale"` key lookup anywhere |

So the value arrives in the spec JSON and dies there. What the item asks for:

> `fxsize`/`fysize` size a figure as a percentage of the graph region and `scale`
> multiplies every text and marker size.

`REMAINING.md` also records that the user gets to choose *how much* of §2 to close,
and that all three of these options are in the smaller of the two sets:

> **Two defensible ways to close this**, and the choice is the user's: **(a)**
> implement all 92 — the plan as written; **(b)** implement the high-value subset
> (`text` `ttitle`/`tlabel` family, the `b1/l1/r1/t1title` set, `mlabformat`
> `mstyle` `lstyle` `acolor` `gap` `fxsize` `fysize` `scale`) and formally
> re-disposition the rest to accept-and-report in the plan and help.

**This phase is inside subset (b).** It is the part of §2 that survives either
decision, which is why it can be scheduled without waiting on that decision.

### What item 4 has to reach on the server side

Three findings bound the server half.

From Appendix C, the 11-04 **refutation** — which corrected an Appendix A claim in
place rather than striking it:

> **11-04 · `graphsize_x` / `graphsize_y` are not dead** (refuted twice,
> independently). They are read by *string*, not by attribute —
> `getattr(self.scheme, "graphsize_x", None)` at `dash_render.py:9244-9245` inside
> `_resolve_aspect_ratio`, whose result becomes `fig_kwargs["aspect_ratio"]`.
> Measured on rendered figures: `stcolor` → 1.6667 (scheme 7.5/4.5), `economist` →
> 1.0 (2.2/2.2), `s2color` → 1.375 (5.5/4.0). An attribute-level count cannot see
> this, which is the methodological trap — and the one Appendix A's own enumeration
> fell into before being redone. The standalone half of Appendix A's item 3 stands:
> re-checked by string, `graphsize_x`, `graphsize_y` and `_resolve_aspect_ratio`
> all occur **0** times in the emitted app, so the scheme's graph size still does
> not reach `dash serve`.

From Appendix C, under 05-04:

> **[func · server · S]** `xsize()` and `ysize()` are honoured by DashRenderer and
> silently ignored in server mode, and neither is on the graph `_dash_pending`
> list. S10 is marked done for them on the strength of the standalone path only.
> Fix: carry xsize/ysize into the emitted app's `figure(width=, height=)`
> computation, or list them as pending-for-server. *Where:*
> `dash_render.py:ServerAppBuilder (figure sizing in the emitted source),
> dash.ado:_dash_parse_graph_opts` `_dash_pending` block`

> **[func · server · M]** xtick(), ytick(), xsize() and ysize() are serialized,
> emit NO note, and are never read by the generated `bokeh serve` app — a silent
> drop in server mode, which is precisely the defect class 05-04's `<done>`
> forbids ("nothing is silently dropped in the interim"). ... All four were
> deliberately taken OFF the `_dash_pending` lists (see the comment block at
> dash.ado:594-604, "scheme(), xsize(), ysize(), xtick() and ytick() are NOT
> listed"), so nothing tells the user. Either teach ServerAppBuilder to read them
> (the emitted axis loop currently iterates only ('xlabel', fig.xaxis), ('ylabel',
> fig.yaxis); `_fig_kw` honours only aspectratio) or, as an interim, make the note
> fire in server mode.

The emitted `_fig_kw` block those two items describe, at
`dash_render.py:13839-13855` (confirmed in source):

```python
"        _fig_kw = dict(",
"            title=html.escape(go.get('title', '') or ''),",
"            x_axis_label=x_label,",
"            y_axis_label=y_label,",
"            tools=TOOLS,",
"            sizing_mode='stretch_width',",
"            output_backend=backend,",
"        )",
"        _raw_ar = go.get('aspectratio', '')",
"        if _raw_ar:",
"            try: _fig_kw['aspect_ratio'] = float(_raw_ar)",
"            except (ValueError, TypeError): pass",
```

**One further divergence, confirmed in source and not claimed by `REMAINING.md`:**
the emitted app assigns `aspect_ratio = float(_raw_ar)` *directly*, with no
reciprocal, while the standalone renderer returns `1.0 / float(ar)` — the
inversion `_resolve_aspect_ratio`'s docstring was written to fix
(`dash_render.py:9214-9219`):

> Note the inversion: **Stata's aspectratio() is height/width**, and Bokeh's
> `aspect_ratio` is **width/height**. dash passed the value straight through, so
> every request came out upside down — `aspectratio(0.5)` asks for a plot region
> half as tall as it is wide, and dash drew one twice as tall as it is wide.
> Measured on a 600x600 export: `aspectratio(0.25)` yields a plot region 542x152,
> i.e. h/w = 0.28.

`grep -n aspect_ratio dash_render.py` returns the reciprocal only inside
`_resolve_aspect_ratio`; line 13849 is the emitted assignment and has none. Item 4
touches this exact block, so the phase should fix the inversion while it is there
rather than build a percentage on top of an upside-down base — see TR-22.11 and
the *Risks* section, which also records that this is **not** in `REMAINING.md` and
must be re-measured before it is treated as fact.

### What "responsive" means in this section, and who checks it

Section 10 carries the only risk line in the plan that says a structural assertion
is not enough:

> **Risk: [yellow]** — visual rather than logical, which makes it the section most
> likely to be reported "done" on the basis of a structural assertion. It is not
> done until someone has looked at it at three viewport widths.

The procedure exists — `test/test_geometry_visual.md`, driving
`examples/geometry_responsive.do` at 375px, 768px and 1440px (confirmed in
source). The **re-run** is booked in §7 of `REMAINING.md`:

> - **Responsive verification at 375/768/1440px** — S10's procedure, re-run
>   against the current build.

That re-run belongs to **Phase 31**, not here. What belongs here is not
invalidating it: every change in this phase moves cells or figure proportions, so
the procedure must be runnable and its exemplar still representative when Phase 31
picks it up.

---

## Epics

| epic | goal | items |
|---|---|---|
| **A — The Bootstrap auto-layout knows what it is placing** | The grid's own shape decisions see every figure's proportions, including faceted ones, and the span→height rule is proved by contrast rather than asserted in one direction. | 1, 2 |
| **B — No graph vanishes from any layout** | Extend section 12's class-level guarantee past the Bootstrap path, so a placement spec cannot silently lose a graph. | 3 |
| **C — The three geometry options** | `fxsize()`, `fysize()` and `scale()` stop being accepted-and-reported and start changing the picture, in both renderers. | 4 |

---

## User stories

### Epic A — The Bootstrap auto-layout knows what it is placing

> **As a Stata user pasting a `twoway` command,** I want a `by()` graph under
> `layout(bs)` to be laid out from the shape of its panels, so that wide faceted
> panels get the room they need instead of being packed three to a row as if they
> had no shape at all.

**AC-A1** — *Given* a dashboard with one faceted graph whose panels each carry
`aspect_ratio` ≥ 2.5 and two square plain graphs, *when* it is rendered with
`layout(bs)`, *then* the faceted graph occupies a row of its own at span 12 and
the two square graphs share a row, exactly as three unfaceted figures of the same
ratios do today.

**AC-A2** — *Given* the same dashboard, *when* `_auto_bs_layout` is called for it,
*then* the ratio it resolves for the faceted name is the panels' common ratio, not
`0.0`.

**AC-A3** — *Given* a faceted graph whose panels disagree on ratio (a
`_resolve_aspect_ratio` result differing between panels), *when* the ratio is
resolved, *then* a single documented reduction is applied — the panels' common
ratio when they agree, and the documented fallback when they do not — and no
exception escapes into the layout.

**AC-A4** — *Given* a graph registered but absent from `self.figures` and from
`_facet_map`, *when* `_ar_of` is called for it, *then* it still returns `0.0` and
the layout is unchanged from HEAD.

> **As a package maintainer,** I want the cell-height rule tested by contrast, so
> that a future simplification of `_cell_height_class` cannot pass the suite.

**AC-A5** — *Given* a dashboard with exactly one KPI card, *when* it is rendered
under `layout(bs)`, *then* its cell carries `db-cell-h-lg` (span 12).

**AC-A6** — *Given* a dashboard with four KPI cards, *when* it is rendered under
`layout(bs)`, *then* every KPI cell carries `db-cell-h-sm` (span 3), and the class
differs from the one-KPI case.

**AC-A7** — *Given* `_cell_height_class` mutated to return a constant, *when* the
suite runs, *then* the new contrast test fails.

### Epic B — No graph vanishes from any layout

> **As a Stata user pasting a `twoway` command,** I want `dash build,
> layout(s1:1,1 s2:1,1)` to tell me something is wrong, so that I never publish a
> dashboard that is quietly missing a graph I asked for.

**AC-B1** — *Given* two registered graphs and `layout(s1:1,1 s2:1,1)`, *when* the
dashboard is built, *then* the build does not return rc 0 with one graph missing:
either both graphs are placed, or the build raises the existing
`_assert_every_graph_was_placed` error naming the missing graph.

**AC-B2** — *Given* a placement spec with no collision (`layout(s1:0,0 s2:0,1)`),
*when* the dashboard is built, *then* placement is unchanged from HEAD and the
guard is silent.

**AC-B3** — *Given* `layout(auto)`, `layout(2 2)` or `layout(bs)`, *when* the
dashboard is built, *then* behaviour is byte-identical to HEAD for the existing
corpus in `test/test_layout.py` and `test/test_layout_placement.py`.

**AC-B4** — *Given* a KPI card that the layout never places, *when* the dashboard
is built, *then* it is reported by the same guard rather than dropped — the guard
today reads `self.figures` only.

> **As a package maintainer,** I want one guard for the whole of layout assembly,
> so the class of defect is closed rather than its instances.

**AC-B5** — *Given* any layout form dash accepts, *when* assembly finishes, *then*
the guard has run exactly once for that document, on the standalone path.

### Epic C — The three geometry options

> **As a Stata user pasting a `twoway` command,** I want `fxsize()`, `fysize()`
> and `scale()` to do what they do in Stata, so that a command I already have does
> not come back with a note saying three of my options were ignored.

**AC-C1** — *Given* `dash scatter mpg weight, fxsize(50)`, *when* the dashboard is
built, *then* the figure occupies 50% of the width it would otherwise take, and
`dash` emits no "ignoring unsupported option(s)" note naming `fxsize`.

**AC-C2** — *Given* `dash scatter mpg weight, scale(1.5)`, *when* the dashboard is
built, *then* every text size and marker size on that figure is 1.5× its
unscaled value, and the unscaled render differs from the scaled one.

**AC-C3** — *Given* `fxsize(0)`, `fxsize(-3)`, `fxsize(abc)` or `scale(0)`, *when*
the dashboard is built, *then* `dash` warns in the same shape
`_resolve_aspect_ratio` already uses for a bad `xsize()` and ignores the value —
it does not raise.

**AC-C4** — *Given* none of the three options, *when* a dashboard is built,
*then* the output is unchanged from HEAD.

> **As a `dash serve` operator,** I want the served dashboard sized like the
> standalone one, so that the two modes do not disagree about the shape of the
> same graph.

**AC-C5** — *Given* the same spec built with `dash build` and with `dash build,
server`, *when* both figures are constructed, *then* their `aspect_ratio` and
sizing inputs agree, for `aspectratio()`, for `xsize()`/`ysize()`, for
`fxsize()`/`fysize()` and for the scheme's `graphsize`.

**AC-C6** — *Given* any option this phase implements, *when* `dash` reports its
ignored options, *then* that option is no longer named — and
`test/test_unsupported_report_is_true.py` passes, which it cannot unless the
`_dash_pending` entries are removed in the same commit.

---

## Business requirements

Each is testable as written.

| # | Requirement |
|---|---|
| **BR-22.1** | The Bootstrap auto-layout derives its rows from the proportions of every figure it places, including the panels of a `by()` graph. A faceted graph is never treated as having no shape. |
| **BR-22.2** | A Bootstrap cell's height follows its span, and that rule is guarded by a test that compares two different spans. |
| **BR-22.3** | No layout form dash accepts can drop a registered graph or KPI from the dashboard without an error. `layout(bs)` and every non-Bootstrap form are held to the same guarantee. |
| **BR-22.4** | `fxsize()` and `fysize()` size a figure as a percentage of the graph region; `scale()` multiplies every text and marker size. |
| **BR-22.5** | An option this phase implements is removed from the `_dash_pending` report in the same change, so the note never names an option that works (and never omits one that does not). |
| **BR-22.6** | Invalid geometry values are reported and ignored, never raised, matching the existing `xsize()`/`aspectratio()` behaviour. |
| **BR-22.7** | Responsiveness survives: a sized or scaled figure still carries a responsive sizing mode and the dashboard still renders without horizontal scroll at 375px, 768px and 1440px. (BR-10.3 — *"Responsiveness — the abstract's headline feature — is preserved"*.) |
| **BR-22.8** | Geometry agrees between `DashRenderer` and the app `ServerAppBuilder` emits: the same spec produces the same figure proportions in both modes. |
| **BR-22.9** | A dashboard that uses none of this phase's options and no placement spec renders exactly as it does at HEAD. |

---

## Technical requirements

### Epic A — the auto-layout and the span rule

**TR-22.1 — `_ar_of` resolves through the facet map.** In
`DashRenderer._auto_bs_layout` (`dash_render.py:10515`), the nested `_ar_of`
(`:10555-10558`) must stop being `figures.get(nm)`. It resolves a registered name
to its figure keys the way `_resolve_layout_names` (`dash_render.py:10959`) does —
`_facet_map[name]` → `[fkey for fkey, _label in ...]`, else `[name]` — and reduces
the panels' `aspect_ratio` values to one number. Facet keys are
`f"{name}__by__{idx}"` (`dash_render.py:11407`, `:11453`).

**TR-22.2 — the reduction is documented and total.** The item says *"taking the
panels' common ratio"*. Implement exactly that: when every panel's
`aspect_ratio` is equal (within a documented tolerance), that value; otherwise a
single documented fallback (the maximum is the reading consistent with
`_default_grid_cols`, which uses `widest = max(ratios)` at
`dash_render.py:11196-11203`). A panel with no `aspect_ratio` contributes nothing;
a name that resolves to no panels still returns `0.0`, preserving HEAD behaviour
for unknown names.

**TR-22.3 — the signature stays static-callable.** `_auto_bs_layout` and
`_parse_bs_layout` are both `@staticmethod` (`dash_render.py:10514`, `:10583`) and
are called statically with positional arguments from at least six tests —
`test/test_layout.py:382`, `:387`, `:394`, `:403`, `:411`, `:422`,
`test/test_geometry.py:374`. The facet map must therefore arrive as a new optional
trailing parameter (`facet_map=None`, defaulting to `{}`) threaded through
`_parse_bs_layout` (`dash_render.py:10584`) from its single call site at
`dash_render.py:10720`, or the two must become bound methods **and** every one of
those call sites updated. The optional parameter is the smaller change and keeps
the existing tests meaningful.

**TR-22.4 — thresholds unchanged.** The numeric thresholds stay as 10-03 set them:
`_ar_of(n) >= 2.5` → a full row at span 12; `max(_ar_of) >= 1.8` → two per row;
`n_rest <= 4` → two per row; otherwise three (`dash_render.py:10560-10576`). This
item changes *what ratio is seen*, not *what is done with it*.

**TR-22.5 — the KPI-span contrast test.** Add to `test/test_geometry.py`, class
`TestBootstrapLayout`, alongside `test_a_kpi_cell_height_follows_its_span`
(`:345`). Render one KPI under `layout(bs)` and four KPIs under `layout(bs)`,
extract the emitted grid classes with the existing `_emitted` helper
(`test/test_geometry.py:287-298`, which matches `class="db-col-12[^"]*"` so it
reads emitted cells, not stylesheet definitions), and assert: the one-KPI cell
carries `db-cell-h-lg`, the four-KPI cells carry `db-cell-h-sm`, and the two class
sets are disjoint. The arithmetic behind those expectations is
`_MAX_KPIS_PER_ROW = 4` (`dash_render.py:125`), `per_row = min(n_kpis,
_MAX_KPIS_PER_ROW)`, `span = max(1, 12 // per_row)` (`:10542-10543`), and
`_cell_height_class` (`:2391-2408`): span 12 → `lg`, span ≥ 6 → `md`, else `sm`.

**TR-22.6 — the graph-cell invariant is not disturbed.**
`test_a_graph_cell_takes_its_height_from_the_figure`
(`test/test_geometry.py:327-343`) asserts a **graph** cell carries no
`db-cell-h-*` class at all, because with an aspect ratio the figure determines its
own height and a floor leaves dead space — *"measured at 217px under a 10x2in
panel in a full-width cell"*. The new test must assert only over KPI cells.

### Epic B — the layout guarantee

**TR-22.7 — call the guard on the non-Bootstrap path.**
`_assert_every_graph_was_placed` (`dash_render.py:10982`) is called only at
`dash_render.py:10793` in `_render_bootstrap_html`. Call it in `_assemble_layout`
(`dash_render.py:11918`) too, after `grid_rows` is built and before `gridplot(...)`
at `:12066`, passing the figure keys that actually reached a cell. `tabbed_keys`
must be counted as placed, exactly as the Bootstrap path does at
`dash_render.py:10739` (`_placed_figs: set[str] = set(tabbed_keys)`).

**TR-22.8 — do not merely report the collision; place both graphs where the
contract says they go.** The documented behaviour for a name the spec does not
place is *"appended, as the Bootstrap path does"* (`dash_render.py:11164-11165`,
`:10653-10655`). A collision is the same situation one step later: the loser has
no cell. Route the loser through the same `_free` list the unplaced names use
(`dash_render.py:12053-12060`), growing `rows_n` by `math.ceil(len(extra) /
max(1, cols))` the way `_compute_grid` already does at `:11170-11171` when
`_free` is exhausted. The guard then stays silent for this case in normal use and
fires only on a genuine dash defect — which is what its error text claims:
*"This is a layout defect in dash, not an error in your command"*.

**TR-22.9 — close the out-of-range branch too.** `if 0 <= _r < rows_n and 0 <= _c
< cols_n` (`dash_render.py:12049`) has no `else`. Give it one: an out-of-range
name joins the same `_free` queue.

**TR-22.10 — the guard must see KPIs.** `_assert_every_graph_was_placed` computes
`missing = [k for k in self.figures if k not in placed_keys]`
(`dash_render.py:10996`) — `self.kpi_divs` is not consulted, so a dropped KPI card
is invisible to the guarantee in both paths (confirmed in source). Extend the
guard to KPI names, keeping the error's existing registered-name reporting via
`facet_owner` (`dash_render.py:10999-11004`).

### Epic C — the three options

**TR-22.11 — where `fxsize`/`fysize` enter.** `_resolve_aspect_ratio`
(`dash_render.py:9210-9265`) is the single standalone sizing decision; its result
becomes `fig_kwargs["aspect_ratio"]` at `dash_render.py:9530` / `:9554-9555`. Its
current precedence (confirmed in source) is:

1. `xsize()`/`ysize()` — either one alone keeps the scheme's other dimension
   (`sx = getattr(self.scheme, "graphsize_x", None)`, `sy = ... "graphsize_y"`,
   `dash_render.py:9244-9252`);
2. `aspectratio()`, taken as `1.0 / float(ar)` because Stata's is height/width;
3. the scheme's `graphsize_x` / `graphsize_y` — measured `stcolor` → 1.6667,
   `economist` → 1.0, `s2color` → 1.375;
4. `None`, leaving Bokeh's default.

`fxsize()`/`fysize()` are a **percentage of the graph region**, not a ratio, so
they cannot be folded into that return value alone: they scale the cell the figure
is given. Implement as a multiplier applied after the ratio is resolved — the
width percentage adjusts the emitted Bootstrap span / grid share and the height
percentage adjusts the effective ratio — and document the precedence against
`xsize()`/`ysize()` and `aspectratio()` in the same docstring, since Phase 30 has
to publish it.

**TR-22.12 — where `scale` enters.** `scale` multiplies text and marker sizes.
The size vocabulary is `OptionTranslator._SIZE_MAP` (`dash_render.py:1213-1223`):
`tiny 3, vsmall 5, small 7, medsmall 9, medium 11, medlarge 13, large 15, vlarge
19, huge 24`, consumed by `translate_msize` (`:1428-1451`), which also accepts a
raw number (`max(1, int(float(v)))`). Apply `scale` as a post-multiplier at the
resolution points rather than by mutating `_SIZE_MAP` — the map is a module-level
class attribute and is **copied verbatim into the emitted app** at
`dash_render.py:12912` (`"_SIZE_MAP = %r" % (dict(OptionTranslator._SIZE_MAP),)`)
and aliased six times inside it (`:14338`, `:14362`, `:14564`, `:14605`, `:14637`,
`:14664`), so a mutation would leak across graphs and across modes.

**TR-22.13 — the server half.** The emitted figure construction is `_fig_kw` at
`dash_render.py:13839-13855`. It honours `aspectratio` only, applies it without
the `1.0 /` reciprocal that `_resolve_aspect_ratio` applies, and never reads
`xsize`, `ysize` or the scheme's `graphsize` — Appendix C's refutation states
`graphsize_x`, `graphsize_y` and `_resolve_aspect_ratio` occur **0** times in the
emitted app. Item 4 is tagged `both`, so the emitted block gains the same
resolution the standalone path uses. The cheapest correct route is to emit a copy
of `_resolve_aspect_ratio` into the app, as `GlyphMapper`, `OptionTranslator` and
`SchemeParser` are already emitted verbatim, rather than to grow a second sizing
implementation inside `_fig_kw`.

**TR-22.14 — validation shape.** Invalid values follow the existing precedent
verbatim (`dash_render.py:9231-9241`): a `UserWarning` reading
`f"dash: {name}({value}) must be a positive number of inches; ignoring it."` for
`xsize`/`ysize`, and `f"dash: aspectratio({raw_ar}) must be a positive number;
ignoring it."` for `aspectratio`. `fxsize`/`fysize` are percentages, so the
message says so; `scale` is a positive multiplier. Parse through
`_stat_option_float(graph_opts, name, None, "graph", lo=0.0)`, as the existing
code does. Stata returns **r(198)** for `xsize(0)` and `xsize(-3)`; dash's
contract is accept-and-report, never abort.

**TR-22.15 — retire the pending entries in the same commit.** Remove `fxsize`,
`fysize` and `scale` from `dash.ado:367-368`, `:375` (`_dash_parse_graph_opts`,
`dash.ado:263-445`) and `dash.ado:604-605`, `:621` (`_dash_parse_plot_opts`,
`dash.ado:458-772`). This is forced, not optional:
`test/test_unsupported_report_is_true.py` reads those blocks directly
(`_pending()` at `:132-138`, via `re.findall(r"_dash_pending' (\w+)\"", ...)`) and
parametrises a test per name asserting that changing the value does **not** change
the rendered document — with values already on file at `:85`, `:86` and `:110`:

```python
"fxsize": ("50", "80", "scatter"),
"fysize": ("50", "80", "scatter"),
"scale":  ("1.5", "0.5", "scatter"),
```

Implement the option and that test fails with *"dash reports graph-level fxsize()
as unsupported, but changing it from '50' to '80' changes the rendered dashboard —
the note names an option that works"*. The failure is the feature.

**TR-22.16 — do not take them off the list without implementing them.** The
converse error is the one Appendix C records for `xtick`/`ytick`/`xsize`/`ysize`:
taken off `_dash_pending` (the comment block at `dash.ado:594-604`) while still
unread by the server app, which is a silent drop. If the server half of item 4 is
deferred, the option stays on the list with a mode-aware note rather than
disappearing from the report.

**TR-22.17 — the fifth, dead serializer.** `_dash_graph_opts_to_json`
(`dash.ado:891`) is recorded in Appendix C as *"a fifth, DEAD, stale copy of the
graph-option list that the generator does not maintain"*, missing 25 options
including `fxsize fysize scale`. Nothing calls it. It is **Phase 18's** item, not
this phase's — do not edit it here; just do not add to it.

---

## Work items

Every item below is reproduced with the number it carries in the phase assignment;
none is dropped, merged or summarised. Tags are `[kind · renderer · effort]`, as
`REMAINING.md` uses them.

### Item 1 — the KPI-span contrast test `[deli · standalone · S]`

> Add the KPI-span test S10's own stub named: render one KPI (span 12) and four
> KPIs (span 3) and assert the two cells carry different `db-cell-h-*` classes.
> It is absent.

**Where.** `test/test_geometry.py` — class `TestBootstrapLayout`, beside
`test_a_kpi_cell_height_follows_its_span` (`:345-370`) and
`test_a_graph_cell_takes_its_height_from_the_figure` (`:327-343`). The code under
test: `_cell_height_class` (`dash_render.py:2391-2408`), the class attachment at
`dash_render.py:10825`, the spans from `_auto_bs_layout` (`:10538-10546`) with
`_MAX_KPIS_PER_ROW = 4` (`:125`), the CSS at `dash_render.py:735-739`.

**Evidence.** Main body, *17 DONE claims the adversarial pass overturned*: `10-01
| the KPI-span test the section's own stub named is absent`. The stub itself, in
`.ultraplan/sections/section-10-geometry.md`: *"Test: a col-4 Bootstrap cell and a
col-12 cell get different heights."* The existing test asserts only
`all("db-cell-h-sm" in c for c in kpi_cells)` over a single four-KPI render, which
a constant-returning `_cell_height_class` survives.

### Item 2 — facet ratios into the auto-layout `[func · standalone · M]`

> Thread facet aspect ratios into `_auto_bs_layout`: `_ar_of` must resolve a graph
> name through `_facet_map`/`_resolve_layout_names` (taking the panels' common
> ratio) instead of `figures.get(name)`.

**Where.** `dash_render.py:_auto_bs_layout` (`:10515`, the nested `_ar_of` at
`:10555-10558` and its three uses at `:10560`, `:10570`), `_resolve_layout_names`
(`:10959-10981`), `_facet_map` (initialised `:8129`, written `:11411`, `:11456`,
from the keys built at `:11407` and `:11453`),
and the call chain `_render_bootstrap_html:10720` → `_parse_bs_layout:10584` →
`_auto_bs_layout`.

**Evidence.** Main body, *17 DONE claims the adversarial pass overturned*: `10-03
| facet ratios never thread into _auto_bs_layout`. `_resolve_layout_names`'
docstring records the storage rule that makes `figures.get(name)` miss: *"A
faceted graph is stored under generated keys `name__by__0`, `name__by__1`, ... so
a layout that looks the name up directly in `self.figures` misses it"*.

### Item 3 — the guard beyond Bootstrap `[func · standalone · M]`

> Extend the "no graph vanishes" guard beyond the Bootstrap path. `layout(s1:1,1
> s2:1,1)` still drops a graph in silence outside `layout(bs)`.

**Where.** `dash_render.py:_resolve_layout_names` (`:10959`) and the non-Bootstrap
layout paths: `_assemble_layout` (`:11918`, the placement slotting at
`:12040-12064`, the `gridplot` at `:12066`), `_assert_every_graph_was_placed`
(`:10982`, called today only at `:10793`), `_placement_map` (`:11092`),
`_compute_grid` (`:11130`).

**Evidence.** Status by section, row 12: *"`layout(s1:1,1 s2:1,1)` still drops a
graph silently outside Bootstrap ②"*. Section 12's task 12-02 on why the guard is
the point: *"This is the fix that matters — defect 1 is one instance of a class,
and the guard catches the rest."* Confirmed in source: the guard has one call
site, and in the placement branch two names resolving to one cell overwrite each
other with no else-branch and no re-queue.

### Item 4 — `fxsize` `fysize` `scale` `[func · both · M]`

> Implement `fxsize` `fysize` `scale`. All three are declared and serialized and
> still reported as ignored; `fxsize`/`fysize` size a figure as a percentage of
> the graph region and `scale` multiplies every text and marker size.

**Where.** `dash_render.py:_resolve_aspect_ratio` (`:9210-9265`), the figure
sizing path (`:9530`, `:9554-9555`), `OptionTranslator._SIZE_MAP` (`:1213-1223`)
and `translate_msize` (`:1428-1451`), the emitted `_fig_kw`
(`:13839-13855`) and the emitted `_SIZE_MAP` copy (`:12912`); `dash.ado` pending
entries at `:367-368`, `:375`, `:604-605`, `:621`.

**Evidence.** §2, *Blocker — the option surface*: `implement-S10 | 5 | 2 | 3`, and
the family list *"**S10 (3):** `fxsize` `fysize` `scale`"*. Appendix A, 05-04:
`implement-S10 | 5 | 5 | 0` — all five declared, so this is renderer work.
Confirmed in source: `grep -c fxsize dash_render.py` → **0**, `fysize` → **0**, no
`"scale"` key lookup; `dash.ado` serializes all three at `:420-422` and `:747-749`
and reports all three as pending. Server context, Appendix C: *"`xsize()` and
`ysize()` are honoured by DashRenderer and silently ignored in server mode ... S10
is marked done for them on the strength of the standalone path only"*, and the
11-04 refutation: *"`graphsize_x`, `graphsize_y` and `_resolve_aspect_ratio` all
occur 0 times in the emitted app, so the scheme's graph size still does not reach
`dash serve`."*

---

## Test plan

Rule 8 governs the order: **write the failing test first, watch it fail at HEAD,
then fix.** Rule 4 governs the coverage: every function this phase adds or changes
gets a unit test. Every test below names the mutation that must kill it — a test
that survives its own mutation is not evidence.

### Epic A — the auto-layout and the span rule

**The failing test to write first** (item 2):
`test/test_geometry.py::TestBootstrapLayout::test_a_faceted_graph_contributes_its_panels_ratio`.
Build a renderer with `_facet_map = {"faceted": [("faceted__by__0", "Domestic"),
("faceted__by__1", "Foreign")]}` and `figures` holding those two keys at
`aspect_ratio` 5.0, plus two square plain graphs, then call the auto-layout and
assert the faceted name lands on a row of its own at span 12. At HEAD `_ar_of`
returns `0.0` for `"faceted"`, so it is never `_wide` and the assertion fails.
`test/test_geometry.py` already has the `_FakeFig(ratio)` helper this needs
(used at `:374-377`).

**Unit tests (rule 4).**

| test | asserts |
|---|---|
| `test_ar_of_resolves_a_plain_name` | unchanged: a name in `figures` returns its own ratio |
| `test_ar_of_resolves_a_faceted_name` | the facet map is consulted and the panels' common ratio returned |
| `test_ar_of_returns_zero_for_an_unknown_name` | HEAD behaviour preserved (AC-A4) |
| `test_ar_of_reduces_disagreeing_panels_by_the_documented_rule` | TR-22.2's fallback, stated once and tested (AC-A3) |
| `test_auto_bs_layout_is_still_callable_statically` | the two-argument and three-argument static calls in `test/test_layout.py:382-403` still work (TR-22.3) |
| `test_cell_height_class_maps_every_band` | `_cell_height_class(12) == "lg"`, `(6) == "md"`, `(3) == "sm"` — the function's own unit test |

**Integration.** `test/test_layout_facets.py` gains the Bootstrap-row assertion
for a wide faceted graph beside its existing title/label coverage
(`:121-176`). `test/test_geometry.py::TestGrid::test_wide_figures_get_fewer_columns`
(`:395`) is the non-Bootstrap analogue and must stay green —
`_default_grid_cols` (`dash_render.py:11179-11204`) reads `self.figures` directly
and so already sees facet panels; this phase does not change it.

**Non-vacuity (mutation).**

| break this | the test that must die |
|---|---|
| revert `_ar_of` to `(figures or {}).get(nm)` | `test_a_faceted_graph_contributes_its_panels_ratio` |
| make `_cell_height_class` return `"sm"` unconditionally | the new item-1 contrast test (AC-A7) |
| make `_cell_height_class` return `"lg"` unconditionally | the new item-1 contrast test, on the four-KPI half |
| change the reduction from common-ratio to "first panel" on disagreeing panels | `test_ar_of_reduces_disagreeing_panels_by_the_documented_rule` |
| drop the `db-cell-h-` attachment at `dash_render.py:10825` | both the new test and the existing `test_a_kpi_cell_height_follows_its_span` |

### Epic B — the layout guarantee

**The failing test to write first** (item 3):
`test/test_layout_placement.py::TestPlacementIsHonoured::test_a_colliding_placement_does_not_lose_a_graph`.
Render two registered graphs with `layout(s1:1,1 s2:1,1)` and assert **both**
figure ids appear in the document — the assertion style
`test/test_layout_facets.py:191-199` already uses (`assert fig.id in out`). At
HEAD `s1` is overwritten in `_slots[0][0]`, never re-queued, and the document
carries one figure and one empty cell, with rc 0 and no warning.

**Unit tests (rule 4).**

| test | asserts |
|---|---|
| `test_the_guard_runs_on_the_plain_grid_path` | `_assert_every_graph_was_placed` is reached from `_assemble_layout`, not only from `_render_bootstrap_html` (AC-B5) |
| `test_a_colliding_name_is_appended_like_an_unplaced_one` | TR-22.8 — the loser gets the next free cell, growing the grid if needed |
| `test_an_out_of_range_cell_is_appended_not_skipped` | TR-22.9 — the `else` branch exists |
| `test_the_guard_reports_a_dropped_kpi` | TR-22.10 — `self.kpi_divs` is in scope for the guarantee |
| `test_a_tabbed_figure_counts_as_placed` | no false positive when `tabs()` holds a figure (mirrors `dash_render.py:10739`) |

**Integration / cscript.** Extend the layout parametrisation in
`test/test_layout_facets.py:187-199`
(`test_every_registered_graph_reaches_the_document`) from `["auto", "bs", "1 2",
"bs: plain=6 faceted=6"]` to include `"plain:0,0 faceted:0,1"` and the colliding
`"plain:1,1 faceted:1,1"` — that single edit turns the existing guarantee test
into the guard for this class. `test/test_layout_placement.py`'s five existing
cases (`:94-123`) are the regression net for "nothing else moved".
`test/test_e2e_multi.cscript` and `test/test_conformance.cscript` run from Stata
with real `layout()` strings and must stay at zero dropped graphs.

**Non-vacuity (mutation).**

| break this | the test that must die |
|---|---|
| remove the new call to `_assert_every_graph_was_placed` in `_assemble_layout` | `test_the_guard_runs_on_the_plain_grid_path` |
| restore the bare `_slots[_r][_c] = ...` overwrite | `test_a_colliding_placement_does_not_lose_a_graph` |
| delete the `else` on the range check at `dash_render.py:12049` | `test_an_out_of_range_cell_is_appended_not_skipped` |
| narrow the guard back to `self.figures` only | `test_the_guard_reports_a_dropped_kpi` |
| count tabbed keys as unplaced | `test_a_tabbed_figure_counts_as_placed` (it should fail loudly, not silently pass) |

### Epic C — the three options

**The failing tests to write first** (item 4) — three, one per option, in
`test/test_geometry.py`, in a new class `TestFxsizeFysizeScale`:

1. `test_fxsize_narrows_the_figure` — render the same spec with and without
   `fxsize(50)` and assert the two documents differ in the figure's width share.
2. `test_fysize_shortens_the_figure` — the same for height.
3. `test_scale_multiplies_text_and_marker_sizes` — assert a `scale(1.5)` render
   carries text and marker sizes 1.5× the unscaled ones, reading the figure
   models rather than the HTML.

All three fail at HEAD by *identity*: the option reaches the spec and nothing
reads it, so the two renders are byte-identical. That identity is exactly what
`test/test_unsupported_report_is_true.py` asserts today for these three names
(values on file at `:85`, `:86`, `:110`) — so the moment the implementation lands,
`test_a_graph_option_reported_unsupported_really_is[fxsize]`,
`[fysize]` and `[scale]` and their plot-level twins **must** fail until
TR-22.15 removes the `_dash_pending` entries. Both directions are evidence; run
them in that order.

**Unit tests (rule 4).**

| test | asserts |
|---|---|
| `test_resolve_aspect_ratio_precedence_is_documented_and_followed` | `xsize`/`ysize` → `aspectratio` → scheme `graphsize` → `None`, with the new options' position stated (TR-22.11) |
| `test_fxsize_is_a_percentage_not_a_ratio` | 50 means half the region, not ratio 50 |
| `test_a_bad_fxsize_warns_and_is_ignored` | `0`, `-3`, `abc` each produce a `UserWarning` and HEAD output (AC-C3, TR-22.14) |
| `test_scale_does_not_mutate_the_size_map` | `OptionTranslator._SIZE_MAP` is unchanged after a scaled render (TR-22.12) — `{tiny: 3 … huge: 24}` |
| `test_scale_applies_to_a_numeric_msize_too` | `translate_msize`'s numeric passthrough is scaled as well as the keyword path |
| `test_an_unsized_figure_is_unchanged_in_kind` | already exists at `test/test_geometry.py:276`; must stay green (AC-C4, BR-22.9) |
| `test_a_sized_figure_is_still_responsive` | already exists at `test/test_geometry.py:252`; extended to a scaled and an `fxsize`d figure (BR-22.7) |

**Parity / server.** Add the geometry case to `test/test_mode_parity.py`: build the
same spec through `DashRenderer` and through the app `ServerAppBuilder` emits, and
compare the figures' `aspect_ratio` and sizing inputs for (a) `aspectratio(0.5)`,
(b) `xsize(9)` alone under `stcolor`, (c) `fxsize(50) fysize(50)`, (d) no option
at all under `economist`. The measured scheme ratios the audit recorded are the
expected values for (d) and the fallback in (b): `stcolor` → 1.6667 (7.5/4.5),
`economist` → 1.0 (2.2/2.2), `s2color` → 1.375 (5.5/4.0). Case (a) is the one that
exposes the missing reciprocal at `dash_render.py:13849` — see *Risks*.

**Stata-side (cscript).** `test/test_option_surface.cscript` and
`test/test_option_report_paren.cscript` assert the shape of the ignored-option
note; after TR-22.15 neither may name `fxsize()`, `fysize()` or `scale()`.
`test/test_examples_run.cscript` must still run all 12 examples at rc 0.

**Non-vacuity (mutation).**

| break this | the test that must die |
|---|---|
| make `fxsize` a no-op again | `test_fxsize_narrows_the_figure` |
| make `scale` a no-op again | `test_scale_multiplies_text_and_marker_sizes` |
| leave `fxsize` on `_dash_pending` after implementing it | `test_a_graph_option_reported_unsupported_really_is[fxsize]` |
| remove `fxsize` from `_dash_pending` *without* implementing it | `test_fxsize_narrows_the_figure` (and TR-22.16's converse) |
| apply `scale` by mutating `_SIZE_MAP` | `test_scale_does_not_mutate_the_size_map` |
| pin width and height in pixels instead of a ratio | `test_a_sized_figure_is_still_responsive` and `test_proportions_are_carried_as_a_RATIO_not_as_pixels` (`test/test_geometry.py:260`) |
| emit `aspect_ratio` server-side without the reciprocal | the parity case (a) |

### Visual verification

`test/test_geometry_visual.md` is section 10's written procedure and
`examples/geometry_responsive.do` its exemplar — *"four KPI cards, a deliberately
wide panel (`xsize(10) ysize(2)`), a square one (`aspectratio(1)`), one at the
scheme's own proportions, and a faceted graph"*. Every item in this phase changes
what that dashboard looks like. Run the procedure at 375px, 768px and 1440px
before handing over, and extend the exemplar with an `fxsize()`/`scale()` graph so
Phase 31's re-run — §7's *"Responsive verification at 375/768/1440px"* — covers
this phase's work. Section 10's risk line is the reason: *"It is not done until
someone has looked at it at three viewport widths."*

---

## Definition of done

A reviewer can tick each line without opening `REMAINING.md`.

**Behaviour**

- [ ] A faceted graph whose panels are wide (ratio ≥ 2.5) gets its own full-width
      Bootstrap row; one whose panels are square shares a row — identical to the
      unfaceted figures of the same ratios.
- [ ] `_ar_of` returns the panels' common ratio for a faceted name, the figure's
      own ratio for a plain name, and `0.0` for an unknown name.
- [ ] A one-KPI dashboard emits `db-cell-h-lg`; a four-KPI dashboard emits
      `db-cell-h-sm`; graph cells still emit no height class at all.
- [ ] `layout(s1:1,1 s2:1,1)` no longer produces a dashboard missing a graph at
      rc 0: both graphs are placed, or the build raises the named error.
- [ ] `layout(auto)`, `layout(2 2)`, `layout(bs)`, `layout(bs: spec)` and
      non-colliding placement specs are unchanged from HEAD.
- [ ] A KPI card that no layout places is reported by the same guard as a graph.
- [ ] `fxsize(50)` halves the figure's width share; `fysize(50)` its height;
      `scale(1.5)` multiplies every text and marker size by 1.5.
- [ ] `fxsize(0)`, `fxsize(-3)`, `fxsize(abc)`, `scale(0)` each warn and are
      ignored; none raises; rc stays 0.
- [ ] `dash`'s ignored-option note no longer names `fxsize()`, `fysize()` or
      `scale()`, and the corresponding `_dash_pending` lines are gone from
      `dash.ado:367-368`, `:375`, `:604-605`, `:621`.
- [ ] The same spec produces the same figure proportions under `dash build` and
      `dash build, server` for `aspectratio()`, `xsize()`/`ysize()`,
      `fxsize()`/`fysize()` and the scheme's `graphsize`.
- [ ] A dashboard using none of these options and no placement spec renders
      exactly as it does at HEAD.

**Tests (rules 4 and 8)**

- [ ] Every defect above has a test that was written first, observed failing at
      HEAD, and passes after the fix.
- [ ] Every mutation in the *Test plan* mutation tables kills its named test.
- [ ] The KPI-span test compares **two** spans; it fails when
      `_cell_height_class` is made constant.
- [ ] `test_every_registered_graph_reaches_the_document` is parametrised over a
      placement spec, including a colliding one.
- [ ] `test/test_unsupported_report_is_true.py` passes — which it can only do
      once the three names are off the pending lists **and** implemented.
- [ ] `test/test_mode_parity.py` carries the four geometry cases.
- [ ] Every function added or changed has a unit test: `_ar_of`'s resolution,
      the panel-ratio reduction, `_cell_height_class`, the new guard call site,
      the `fxsize`/`fysize`/`scale` resolution and its validation.

**Deliverables and hygiene**

- [ ] `test/test_geometry_visual.md` run at 375px, 768px and 1440px against a
      build from this branch: no horizontal scroll, no overlapping cells, faceted
      panels sized consistently with unfaceted ones.
- [ ] `examples/geometry_responsive.do` extended with an `fxsize()`/`scale()`
      graph so Phase 31's re-run exercises this phase.
- [ ] The sizing precedence — `xsize`/`ysize`, `aspectratio`, `fxsize`/`fysize`,
      `scale`, scheme `graphsize` — is documented in `_resolve_aspect_ratio`'s
      docstring, ready for Phase 30 to publish in `dash.sthlp`.
- [ ] Full pytest suite and full certification suite green against the S01
      baseline, with honest skips (a skip is not a pass).
- [ ] `REMAINING.md` unmodified.

---

## Risks and sequencing notes

**1. The dependency on Phases 17 and 18 is softer than the index implies.** The
three options are already declared and serialized — Appendix A's 05-04 table
records `implement-S10 | 5 | 5 | 0`. Nothing in item 4's renderer work waits on
Phase 17. What does wait is the abbreviation: Appendix C records that
`fxsize()`/`fysize()` *"are declared at a LONGER minimum than twoway's, so the
abbreviated forms twoway accepts are silently thrown away. dash.ado declares
`FXSIZE(string)` / `FYSIZE(string)` (all-caps = full name required); twoway's
measured minimum is `fxsiz` / `fysiz`. A pasted `twoway ..., fxsiz(50)` therefore
falls through the `*` catch-all in dash: rc 0, a note naming a non-existent option
`fxsiz()`, and the value gone."* That fix — probing `fxsize`/`fysize` in
`scripts/extract_abbrev_truth.do`, adding them to
`test/fixtures/abbrev_truth.json`, letting the generator emit `FXSIZe`/`FYSIZe` —
belongs to **Phase 18** and is not an item here. The same note records that
`scale` needs no change: *"twoway rejects `sca()`/`scal()` too, so the full name
is correct there."* Land this phase after Phase 18 if you want `fxsiz(50)` to work
on day one; land it before, and the full spelling works and the abbreviation does
not.

**2. Do not touch `dash.ado`'s generated blocks beyond the four pending lines.**
Appendix C records that `scripts/regen_option_surface.py` *"has ALREADY
double-applied in the committed `dash.ado` — the generated blocks are duplicated
at HEAD"*, and that re-running it deletes hand-written code including the
`level()` validation block and the whole `_dash_pending` accumulation. De-duplicating
the splice markers is Phase 18's work. This phase removes four `if ... local
_dash_pending` lines by hand and does not regenerate.

**3. The missing reciprocal in the emitted app is an enrichment, not an audit
finding.** `REMAINING.md` says the emitted app never reads `graphsize_x`,
`graphsize_y` or `_resolve_aspect_ratio`; it does **not** say the emitted
`aspectratio` handling is inverted. That claim comes from reading
`dash_render.py:13849` (`_fig_kw['aspect_ratio'] = float(_raw_ar)`, no `1.0 /`)
against `dash_render.py:9264` (`return 1.0 / float(ar)`) at HEAD. Re-measure it —
build one spec with `aspectratio(0.25)` in both modes and compare the figures —
before writing it up as a defect. If it holds, it is a rule-8 bug in its own right
and needs its own failing test; the parity case (a) in the test plan is that test.

**4. Item 4's server half collides with the server-unification phases.** The
emitted `_fig_kw` block is inside the region Phases 05–08 (task 15-03) intend to
replace with delegation to the shared mapper. `REMAINING.md` is explicit that
*"Sequencing 15-03 first would collapse most of the rest, because a delegated
branch inherits the standalone behaviour instead of needing its own copy of each
fix."* Figure construction is not glyph dispatch, so `_fig_kw` is not literally
one of the 38 undelegated branches — but the same "emit the standalone helper
rather than write a second implementation" discipline applies, and coordinating
with Phase 05's author costs one message and can save the whole server half of
item 4.

**5. Items 1, 2 and 3 are independent of everything else in the plan.** They touch
`DashRenderer`'s layout assembly only, need no `dash.ado` change and no server
work, and can be done in any order relative to Waves 1–5. If this phase has to be
split, split it there: Epics A and B ship on their own.

**6. Order inside the phase: item 1 before item 2.** The contrast test is the
cheapest thing here and it exercises `_auto_bs_layout`'s span arithmetic, which
item 2 also edits. Having it green first means item 2's change is made against a
suite that can see a regression in the KPI row.

**7. Item 3 changes behaviour a user could be relying on.** Today a colliding
placement spec silently yields a smaller dashboard. After TR-22.8 it yields a
larger one, with the loser appended. That is the documented contract for unplaced
names (`dash_render.py:11164-11165`) and the right reading — but it is a visible
change to output, so record it in the CHANGELOG as a behaviour change, not as a
bug fix.

**8. Watch the aspect-ratio/height interaction.** `test/test_geometry.py:327`
records a measurement worth keeping in mind: a graph cell deliberately carries no
height class, because with an aspect ratio the figure determines its own height
and a `min-height` floor left *"dead space — measured at 217px under a 10x2in
panel in a full-width cell."* `fysize()` is a height percentage, so the temptation
to reach for a height floor will recur. It is the wrong mechanism for the same
measured reason.

**9. Responsiveness is the section's stated risk and this phase's easiest
regression.** BR-10.3 calls it *"the abstract's headline feature"*, and the
structural tests at `test/test_geometry.py:249-283` are the only automatic guard —
`test_a_sized_figure_is_still_responsive` and
`test_proportions_are_carried_as_a_RATIO_not_as_pixels`. Extend both to the new
options rather than adding a parallel check, and then look at it at three widths,
which is what the section says done means.
