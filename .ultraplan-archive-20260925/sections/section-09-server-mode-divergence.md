# Section 09: Server-mode divergence — the failing parity test

## Overview

This section does not fix server mode. It proves server mode is broken, inside the test
suite, with an owner's name attached. By the time it runs, sections 02 and 03 have made
`DashRenderer` compute `lfit`, `histogram`, `kdensity` and the other computed layers on the
qualified rows. The generated `bokeh serve` app has not changed and structurally cannot have:
its fifteen emitted `_compute_*` helpers take a dataframe and nothing else, so the only
restriction channel is the first positional argument, and 43 call sites pass an unrestricted
one. The two renderers now disagree, and BR-01.10 says they must not. Discovery Q2 decided
that Phase 01 lands the disagreement as a **visible red-marked test** rather than an invisible
defect, and that the implementation travels with the `_DASH_MAPPER` delegation work in
Phases 5-8.

Three commits: the runtime parity case on the main plot loop; the runtime cases on the `by()`
facet and `by(total)` twin paths; a census of the **emitted source** that pins all 43
aggregate call sites and the three further qualifier state sites TR-01.12 names. Every
deferred assertion is `xfail(strict=True, raises=AssertionError)` with a reason naming Phases
5-8 and its TR — never `skip` — so when the implementation lands each marker XPASSes, the
suite goes red, and whoever landed it must delete the marker.

**Ordering (rule 8):** this section is tests only, so there is no fix to precede. Each task
writes its own tests and must observe them failing for the right reason under
`pytest --runxfail` before committing.

## Risk: [green] — test-only; the hazard is an xfail that fails for the wrong reason and so certifies nothing

## Dependencies
- Depends on: section-02, section-03
- Blocks: section-10
- Parallel batch: 4

## Evidence

### Why this section exists at all (DISCOVERY Q2, upheld by research)

> **A:** *Parity test now, implement later.* Land Epics A and B (the wrong-numbers fix) plus
> Epic C's failing parity test, so the server divergence is a visible red test rather than an
> invisible defect. The ~20 emitted call sites are implemented with the delegation work.
> → TR-01.11 and TR-01.12 travel with the item so whoever lands it covers the by()-facet and
> callback paths too.

Research corrected the count from ~20 to **43** (RESEARCH §1.7). PRD §7 restates the scope:
"It does not implement the server-mode fix. Items 2, 5 and 6 become a failing parity test."

### RESEARCH §1.7 — 43 call sites, and no row identity

15 `_compute_*` helpers are emitted (plus `_compute_lpoly_fit`, copied by `inspect.getsource`
at `dash_render.py:12520`, so a grep of `dash_render.py` does not find it). **None takes a
mask or row-id list** — the only restriction channel is the first positional `df`.

| path | emitted loop at | frame passed | sites |
|---|---|---|---|
| main plot loop | `dash_render.py:14030` | `g_df` | 15 |
| `by()` facet ladder | `dash_render.py:15136` | `_fac_gdf` | 7 |
| `by(total)` twin | `dash_render.py:15236` | `work_df` | 7 |
| filter callback | `dash_render.py:15583` | `agg_fdf` | 14 |

Verified read-only at `187a786` by building an app into the scratchpad and counting with the
regex `(?<![\w.])_compute_(histogram|lfit|qfit|lfitci|qfitci|kdensity|lowess|lpoly|lpolyci|fpfit|mspline|mband|rscatter|pcscatter)\(`:
**57 tokens − 14 module-level `def` lines = 43 call sites**, splitting 15 / 7 / 7 / 14 exactly
as the table says. Three further `_compute_kpi` sites and the `_compute_lpoly_fit` sites
inside copied helper bodies are **not** part of the 43. The emitted app also embeds a copy of
`GlyphMapper`, which carries its own `self._compute_lpoly_fit` — hence the `(?<![\w.])`
guard, without which a census over-counts.

The 15 `g_df` sites are emitted at `dash_render.py:14108, 14121, 14145, 14180, 14193, 14212,
14227, 14242, 14254, 14376, 14403, 14745, 14757, 14773, 14799`; the facet sites at
`15154, 15159, 15164, 15170, 15175, 15182, 15187`; the twin sites at
`15255, 15260, 15265, 15271, 15276, 15283, 15288`; the callback sites at
`15605, 15607, 15609, 15611, 15613, 15615, 15617, 15621, 15623, 15625, 15627, 15629, 15631,
15633`.

> **D4. Server mode has no row-identity carrier.** `_ROW_ID_COLUMN` is emitted as a bare
> constant — it reaches the app only through the explicit constant tuple `_glyph_layer_lines`
> (`dash_render.py:12315`) writes out at `dash_render.py:12362-12369`, whose own comment says
> these are "constants these classes reference that are not already written out by
> `_shared_stat_lines`". (The separate `_supply_missing_constants` scanner at
> `dash_render.py:16063`, called at `:16059`, is a different mechanism and does not carry it.)
> And **no emitted code ever writes `__dash_row__` into a
> ColumnDataSource**. Verified on a built app: `_ROW_ID_COLUMN` occurs exactly once (its own
> assignment) and the string `__dash_row__` exactly once (the value of that assignment). The
> app uses a plain `'index'` column, and only on `shared_source` (`dash_render.py:13751`:
> `_shared_data['index'] = list(df.index)`). **A row-id-list approach has no carrier in server
> mode; a mask over `df.index` is the only thing available today**, which changes the shape of
> the eventual implementation and is why this section pins the fact rather than asserting a
> carrier into existence.

> **D5. The per-plot data is present in the payload; the emitted code never reads it.**
> `dash.ado:1240` / `:1244` emit `"if_expr":"…","in_expr":"…"` on **every** plot segment and
> those reach `_SPEC_B64`. But `plot.get('if_expr')` occurs **exactly once in the whole of
> `dash_render.py`, at `:9951`** — the standalone `_make_figure_body` — and **zero times in a
> built app**. Every emitted read is graph-scoped: `dash_render.py:13812` / `:13819`
> (`go.get('if_expr') or g.get('if_expr')`, inside the per-graph block that builds `g_df`) and
> `_graph_qualifiers` at `:15007`.

The consequence the test must encode: `dash.ado:1496` promotes a qualifier to graph level
**only when `n_segs == 1`**, and the comment at `dash.ado:1485` states the outcome outright —
*"per-plot qualifiers are not read in build/server flows."* So **single-layer commands work in
server mode today and multi-layer ones silently ignore the qualifier.** A parity test that
does not distinguish the two cannot tell "the server drops per-plot scope" from "the server
cannot see qualifiers at all", and the fix for the second is not the fix for the first.

### The three further state sites (item 6 / TR-01.12), confirmed at HEAD

- **(a)** `dash_render.py:15007` emits `_graph_qualifiers = {}  # gname → {...}` and `:15014`
  emits `_graph_qualifiers[_gnq] = {'if_expr': _qi, 'in_expr': _qn}` — keyed by **gname
  alone**. It is the only qualifier state the filter callback can see.
- **(b)** the `by()`-facet frame is built at `dash_render.py:15044-15058`
  (`_by_q_df = df.copy()`, then `_by_in` / `_by_if`, then `work_df = _by_q_df`) with **no**
  per-plot consultation.
- **(c)** the filter-callback re-render reapplies `_qual_cb = _gquals.get(_orig_gn_cb, {})` at
  `dash_render.py:15527` and translates it at `:15556` — graph-level only.

A per-plot mask added only at the plot loop would be correct on first paint and silently
dropped on the first filter move, and would never reach any `by()` panel of a served
dashboard. That is exactly why TR-01.11 and TR-01.12 must travel with the deferred item.

### The pre-existing `'opts'` omission (RESEARCH §1.7, §4.8)

The main plot loop's aggregate registry entry carries its options —
`dash_render.py:14110-14111` emits `agg_sources[(gname, pi)] = {` / `'opts': opts,`. The
facet and twin entries **omit the key**: `dash_render.py:15156` emits
`agg_sources[(_fac_name, pi)] = {'source': _hsrc, 'type': 'histogram', 'var': _hvar, 'bins': 20}`
and `:15161` the `lfit` form, with the `_tot_name` forms at `:15257` / `:15262`. The callback
then reads `agg.get('opts') or {}` at `dash_render.py:15605ff`, so **a faceted layer's
options silently degrade to `{}` on the first widget move**. Whoever implements TR-01.11 must
add the mask *and* the missing `'opts'` to those entries, or the facet path will recompute
with default bins under a correct mask.

Also note the registry is already keyed by `(gname, pi)` — the plot index is in hand at every
aggregate site, so a per-plot mask has somewhere to live without a new key shape.

### The trap, in this module's own dialect

RESEARCH §1.9 F-B: existing coverage is scatter-only and **structurally cannot catch this
class of bug**. `test/test_varlist_expansion.py:101`'s `_visible_count` helper reads
`renderer.view.filter.booleans`, which reports a *computed* layer as fully visible no matter
what it drew. **Assertions on computed layers must compare the layer's own source values
against an independently computed subsample**, never a view's booleans. In server mode the
trap is sharper still: the emitted app attaches **no view at all** to a computed layer, so
there are no booleans to read even incorrectly.

`test/test_mode_parity.py` has its own version of the same trap. `_glyph_profile`
(`test/test_mode_parity.py:131-148`) collects `type, marker, size, fill_color, line_color,
line_width, line_dash, fill_alpha` — **visual properties only, never `data_source.data`**.
Adding a per-plot-qualified spec to `CORPUS` therefore **passes today and after the fix** and
certifies nothing: both modes draw a `Line` of the same colour and width, one from 10 rows and
one from 5. The new cases need a data-level comparison helper, which this section adds.

### Ground truth for the parity module's own frame

`test/test_mode_parity.py:44-49` defines a 10-row `_DF`; `foreign == 1` selects rows
1, 3, 5, 7, 9. Computed read-only with `numpy.polyfit`:

| quantity | full sample (10 rows) | `foreign==1` (5 rows) |
|---|---|---|
| slope | `-0.0070944099` | `-0.0083342585` |
| intercept | `41.8751452` | `44.9190554` |
| x-range of the drawn segment | `[1800, 4080]` | `[1800, 3350]` |

Two independent signals separate the cases: the slope (17% apart, far outside the 1e-6
relative tolerance Q4 fixed) and the fitted segment's x-max (`4080` vs `3350`), which is the
same second signal Stata gives in RESEARCH §3.1 (`[1760, 4840]` vs `[1760, 3420]`). This
module keeps its own frame; Stata's `auto` coefficients from RESEARCH §3.1 are section 01's
and section 02's reference and are **not** needed here — cross-mode parity is a comparison
between two renderers, and the anchor that stops both from being wrong together is a
`polyfit` on the subsample computed in the test.

### Decisions that do NOT govern this section

RESEARCH §4 superseded three discovery decisions — Q3 (connected glyphs now get a per-layer
NaN column, not a private source), item 8's `LabelSet` (now a `figure.text` glyph, because
`LabelSet` has no `view` property in Bokeh 3.9, §2.6) and the colour range (now
`LinearColorMapper(domain=[(renderer, col)])`). None of the three is planned here: they belong
to sections 04 and 05. In particular **TR-01.13 (server-side marker labels at
`dash_render.py:14454, 14484, 14502, 14532, 14552, 14585, 14655, 14925`) is not planned in
this section** — it is downstream of the emitted app reading per-plot qualifiers at all, so it
travels with TR-01.11 and TR-01.12 into Phases 5-8. Do not add an assertion about server-side
labels here; it would pin a mechanism section 05 is still choosing.

## TDD test stubs

All stubs live in **`test/test_mode_parity.py`**. Every deferred one is
`@pytest.mark.xfail(strict=True, raises=AssertionError, reason=…)`, never `skip`.
`raises=AssertionError` is load-bearing: without it, an `ImportError`, `KeyError` or a typo in
a spec key is reported as a satisfied expectation, and the stub certifies nothing.

**Must fail now, on the pre-implementation tree (deferred to Phases 5-8):**

- Test: a two-plot spec `(scatter mpg weight) (lfit mpg weight if foreign==1)` renders through
  both modes; the fit layer's own `x`/`y` source values must agree between modes to `rtol=1e-6`.
  Fails: standalone draws the 5-row fit, the server the 10-row fit. (item 2/5, TR-01.10,
  TR-01.11 plot-loop group, BR-01.10, US-C1.)
- Test: the same for an aggregate layer, parametrized over `histogram` (compare `left`,
  `right`, `top`) and `kdensity` (compare `x`, `y`). (TR-01.11, BR-01.10.)
- Test: the same spec under `graph_options={"by": "foreign"}` — every panel's fit layer must
  agree between modes. Fails at `_fac_gdf`. (TR-01.11 facet group, TR-01.12b, BR-01.8.)
- Test: the same under `by: "foreign, total"` — the total twin must apply the per-plot
  qualifier. Fails at `work_df`. (TR-01.11 twin group.)
- Test: in the built app's source, no `_compute_*` call site passes a bare `g_df`, `_fac_gdf`,
  `work_df` or `agg_fdf`. Fails 43 times. (TR-01.11.)
- Test: the built app's source contains a per-plot qualifier read (`plot.get('if_expr')`).
  Fails: zero occurrences. (TR-01.10, D5.)
- Test: the emitted `_graph_qualifiers` assignment is keyed by graph **and** plot index.
  Fails: `_graph_qualifiers[_gnq] = …`. (TR-01.12a.)
- Test: the emitted `by()`-facet block between `_by_q_df = df.copy()` and the facet plot loop
  consults a per-plot key. Fails: graph-level only. (TR-01.12b.)
- Test: the emitted callback requalify block reapplies a per-plot mask, and the aggregate
  recompute **intersects** `agg_fdf` with it rather than replacing it. Fails. (TR-01.12c,
  BR-01.9.)
- Test: the emitted facet and twin `agg_sources[...]` entries carry an `'opts'` key. Fails:
  both omit it, so `agg.get('opts') or {}` degrades to `{}` on the first widget move.

**Must pass now — the anchors, without which the deferred stubs certify nothing:**

- Test: a **graph-level** qualifier (`graph_options={"if_expr": "foreign==1"}`, the
  `n_segs == 1` promotion path of `dash.ado:1496`) produces the same fit in both modes. This
  is the positive control for D5: it proves the harness can see a qualifier at all, so a
  failure in the per-plot stub is about scope, not about a broken harness.
- Test: standalone's own fit for the per-plot case equals `numpy.polyfit` on
  `_DF[_DF.foreign == 1]` to `rtol=1e-6`. Without this, the parity stubs would be satisfied by
  both renderers being wrong in the same way. This is the assertion that makes the dependency
  on sections 02 and 03 real.
- Test (guards the guard): the `by()` harness collected more than one panel and each panel
  carries a comparable fit layer; comparing two empty lists proves nothing.
- Test: the built app defines `_ROW_ID_COLUMN` and references it nowhere, and `'index'` is the
  only identity column on `shared_source` — D4, recorded as an executable fact so the
  implementer knows a mask over `df.index` is the only channel available.
- Test: the aggregate call-site census is still 43. A count-based assertion is what catches
  the *next* emitted helper someone adds without a mask.
- Test (attribution): every `xfail` in this module carries a reason naming Phases 5-8 and a
  `TR-01.x`, no test in this module is marked `skip`, and the number of deferred cases equals
  a module constant — so deleting one to quiet the suite fails here.

**Mutations that must kill a stub:**

| break this | test that must die |
|---|---|
| revert `map_lfit`'s `row_mask` (section 02) to the unmasked frame | the standalone anchor, and the per-plot parity stub stops failing for its stated reason |
| add the per-plot spec to `CORPUS` and rely on `_glyph_profile` instead of comparing data | nothing dies — which is why the data helper exists; assert the helper returns non-empty arrays |
| drop `raises=AssertionError` from a marker and typo a spec key | the deferred stub silently "passes" as xfail; the attribution test must assert `raises` is set |
| implement only the plot loop and leave `_fac_gdf` unmasked | the `by()` facet stub and the masked-frame census stub both stay red |
| delete a deferred stub instead of implementing it | the attribution test's count assertion |

## Tasks

<task type="auto" id="09-01">
  <name>The failing parity case: a per-plot qualifier on a computed layer</name>
  <files>test/test_mode_parity.py</files>
  <action>
    Work only in `test/test_mode_parity.py`. Do not touch `dash_render.py`, `dash.ado` or any
    other test file.

    1. Add a module-level helper after `_chrome` (which ends at `test/test_mode_parity.py:185`):

       ```python
       def _computed_layer_data(fig, keys):
           """The layer's OWN source values, for layers that build their own source.

           `_glyph_profile' compares colour and width and never data, so a qualified
           computed layer that draws the wrong numbers has the right colour. Assertions
           on computed layers must compare the layer's own source values against an
           independently computed subsample -- never a view's booleans, which in server
           mode do not even exist because no CDSView is attached.
           """
       ```
       It walks `fig.renderers`, takes each `r.data_source`, and returns a list of
       `{k: [float(v) for v in src.data[k]] for k in keys}` for every source whose column
       set is exactly `set(keys)`. Exactness is what distinguishes a computed layer's private
       source (`{"x", "y"}`) from the shared source a scatter draws from.

    2. Add a second helper `_only(profiles, what)` that asserts `len(profiles) == 1` with the
       message `f"expected exactly one {what} layer, found {len(profiles)}"` and returns it.
       A silently-empty list is the failure mode this section is written to avoid.

    3. Add `class TestPerPlotQualifiersCrossTheModeBoundary:` after
       `TestAggregateLayersStartFromTheSameNumbers` (which ends at
       `test/test_mode_parity.py:386`). Give it a docstring citing DISCOVERY Q2, BR-01.10 and
       US-C1, and stating that the implementation is deferred to Phases 5-8.

    4. Give the class two spec builders as `@staticmethod`s, both using the module's `_spec`:
       - `_per_plot_spec()` → plots
         `[{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}},
           {"type": "lfit", "yvar": "mpg", "xvar": "weight", "options": {},
            "if_expr": "foreign==1", "in_expr": ""}]`
         — the per-plot keys `dash.ado:1240`/`:1244` emit on every segment.
       - `_graph_level_spec()` → the same two plots with **no** per-plot keys, and
         `graph_options={"if_expr": "foreign==1"}`, which is what `dash.ado:1496` promotes when
         `n_segs == 1`. `_spec` copies `graph_options` into both `"graph_options"` and
         `"options"`, and the emitted app reads `go.get('if_expr') or g.get('if_expr')` at
         `dash_render.py:13819`, so this is the path that works in server mode today.

    5. Write `test_a_graph_level_qualifier_agrees_in_both_modes` — **no xfail marker**. Render
       `_graph_level_spec()` through `_standalone_figures` and `_server_figures`, pull the
       single `{"x","y"}` layer from figure `[0]` of each with `_computed_layer_data(fig,
       ("x", "y"))`, and assert `numpy.allclose(std["y"], srv["y"], rtol=1e-6)` and the same
       for `x`. Docstring: this is the positive control for D5 — single-layer commands work in
       server mode today, so a failure here means the harness is broken, not that per-plot
       scope is missing.

    6. Write `test_the_standalone_side_of_the_parity_case_is_itself_correct` — **no xfail
       marker**. Render `_per_plot_spec()` standalone only. Compute the expected slope with
       `numpy.polyfit(_DF.loc[_DF.foreign == 1, "weight"], _DF.loc[_DF.foreign == 1, "mpg"], 1)`
       and recover the drawn slope as `(y[-1] - y[0]) / (x[-1] - x[0])`. Assert the drawn slope
       equals the expected `-0.0083342585` to `rtol=1e-6`, and assert `max(x) == 3350.0` (the
       qualified sample's x-max, not the full sample's `4080.0`). State the tolerance in the
       test body once, per DISCOVERY Q4. Docstring: without this anchor the parity assertion
       below would be satisfied by both renderers being wrong together; this is the assertion
       that makes the dependency on sections 02 and 03 real.

    7. Write `test_a_per_plot_qualifier_on_lfit_agrees_in_both_modes`, decorated with

       ```python
       @pytest.mark.xfail(
           strict=True, raises=AssertionError,
           reason="S09: the emitted app never reads plot['if_expr'] -- there is no "
                  "occurrence of plot.get('if_expr') in a built app -- and all 43 "
                  "_compute_* call sites take an unrestricted frame. TR-01.10 and "
                  "TR-01.11 travel with the _DASH_MAPPER delegation work in Phases 5-8 "
                  "(DISCOVERY Q2). Delete this marker when the emitted app masks them.",
       )
       ```
       Body: render `_per_plot_spec()` through both modes, take the `{"x","y"}` layer from
       each, and assert `numpy.allclose(std["y"], srv["y"], rtol=1e-6)` with a message that
       prints **both recovered slopes and both x-maxima**, so the failure output is itself the
       characterisation of the divergence:
       `f"standalone slope {std_slope!r} over x<={max(std['x'])!r}; server slope {srv_slope!r} over x<={max(srv['x'])!r} -- the server drew the full-sample fit"`.

    Follow the module's existing house style for markers, which `test/test_filters.py:1360`
    established: `strict=True` plus a `reason` that names the section and the observed
    behaviour. There is no `pytest.ini`, `setup.cfg` or `pyproject.toml` in this repository, so
    `xfail_strict` is not set globally — `strict=True` must be written on every marker.
  </action>
  <verify>
    `cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_mode_parity.py::TestPerPlotQualifiersCrossTheModeBoundary -q`
    prints `2 passed, 1 xfailed`.
    Then confirm it fails for the RIGHT reason:
    `python3 -m pytest test/test_mode_parity.py -k per_plot_qualifier_on_lfit --runxfail -q`
    prints `1 failed`, and the assertion message shows the standalone slope near
    `-0.00833` over `x<=3350.0` against the server slope near `-0.00709` over `x<=4080.0`.
    If `--runxfail` reports anything other than an `AssertionError` from that comparison, the
    stub is measuring something else — fix it before committing.
  </verify>
  <done>
    `test/test_mode_parity.py` carries a data-level comparison helper and three tests: a
    graph-level positive control that passes, a standalone ground-truth anchor that passes, and
    one strict xfail that records the per-plot divergence on the main plot loop and names
    Phases 5-8 as its owner. No product file changed.
  </done>
</task>

<task type="auto" id="09-02">
  <name>The facet and twin paths: `by()` and `by(total)` lose the qualifier too</name>
  <files>test/test_mode_parity.py</files>
  <action>
    Still only `test/test_mode_parity.py`. This task discharges the half of item 6 that is
    observable at runtime: TR-01.11's facet and twin groups, and TR-01.12b.

    1. Add `class TestTheQualifierMustReachEveryServerPath:` below
       `TestPerPlotQualifiersCrossTheModeBoundary`. Docstring: the emitted app builds facets
       from `_fac_gdf` (7 call sites, emitted at `dash_render.py:15154-15187`) and the
       `by(total)` twin from `work_df` (7 sites, `:15255-15288`); neither consults a per-plot
       key, so a fix confined to the plot loop would never reach a panel of a served dashboard.

    2. Reuse `TestPerPlotQualifiersCrossTheModeBoundary._per_plot_spec`; add a `_by_spec(by)`
       staticmethod that passes `graph_options={"by": by}`. The emitted facet block reads
       `by_raw = (go.get('by') or '').strip()` and splits varlist from suboptions on the first
       comma (`dash_render.py:15026-15032`), so `"foreign"` and `"foreign, total"` are the two
       strings to pass.

    3. Write `test_the_by_harness_sees_every_panel` — **no xfail marker**. Render
       `_by_spec("foreign")` through both modes; assert both return the same number of figures
       and that it is greater than 1; assert every figure yields exactly one `{"x","y"}` layer
       via `_computed_layer_data`. This guards the guard in the same spirit as
       `test_the_profile_is_not_empty` (`test/test_mode_parity.py:328`): a per-panel comparison
       over zero panels proves nothing.

    4. Write `test_a_per_plot_qualifier_survives_by_faceting`, strict-xfail with
       `raises=AssertionError` and a reason naming **TR-01.11 (facet group,
       `dash_render.py:15154-15187`) and TR-01.12b (`:15044-15058`)** and Phases 5-8. Body:
       render `_by_spec("foreign")` both ways and compare each panel's `{"x","y"}` layer pairwise
       at `rtol=1e-6`, with a message naming the panel index and both slopes.

    5. Write `test_the_by_total_twin_applies_the_per_plot_qualifier`, strict-xfail with
       `raises=AssertionError`, reason naming **TR-01.11 (twin group,
       `dash_render.py:15255-15288`)** and Phases 5-8. Body: render `_by_spec("foreign, total")`
       both ways and compare the **last** figure — the total twin — the same way.

    6. Write `test_a_per_plot_qualifier_on_an_aggregate_layer_agrees`, parametrized
       `@pytest.mark.parametrize("ptype,keys", [("histogram", ("left", "right", "top")),
       ("kdensity", ("x", "y"))])`, strict-xfail with `raises=AssertionError`, reason naming
       **TR-01.11 (plot-loop sites `dash_render.py:14145` and `:14180`)** and Phases 5-8. Build
       a spec of `[scatter, <ptype> with if_expr "foreign==1"]`, using `{"type": ptype,
       "yvar": "mpg", "xvar": "", "options": {}, "if_expr": "foreign==1", "in_expr": ""}` for
       the aggregate plot — the same shape the existing histogram/kdensity corpus entries use
       at `test/test_mode_parity.py:224-227`. Compare the aggregate layer's own source values
       across modes with `_computed_layer_data(fig, keys)` at `rtol=1e-6`. The emitted helpers
       return `dict(top=…, left=…, right=…)` (`dash_render.py:13207-13209`) and
       `dict(x=…, y=…)` (`:13392-13393`), and the standalone mappers build sources with the same
       keys, so the comparison is key-for-key.

    Do **not** add any of these specs to `CORPUS`. The corpus tests compare `_glyph_profile`
    and `_annotations`, neither of which reads `data_source.data`, so a corpus entry would pass
    today and after the fix and certify nothing — and `by()` produces several figures where the
    corpus tests index `[0]`.
  </action>
  <verify>
    `cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_mode_parity.py::TestTheQualifierMustReachEveryServerPath -q`
    prints `1 passed, 4 xfailed`.
    `python3 -m pytest test/test_mode_parity.py::TestTheQualifierMustReachEveryServerPath --runxfail -q`
    prints `1 passed, 4 failed`, and each failure message is an `AssertionError` naming the
    panel or layer and two differing slopes — not a `KeyError`, `IndexError` or `TypeError`.
  </verify>
  <done>
    The facet ladder, the `by(total)` twin and the aggregate path each carry a strict xfail that
    fails for a stated reason and names the TR whoever implements it must satisfy. One passing
    guard proves the panel harness is comparing real layers. No product file changed.
  </done>
</task>

<task type="auto" id="09-03">
  <name>The emitted-source census and the attribution guard</name>
  <files>test/test_mode_parity.py</files>
  <action>
    Still only `test/test_mode_parity.py`. `dash_render.py` is read-only in this phase. This
    task pins the *shape* of the divergence so that whoever implements it cannot cover the plot
    loop and call the item done (PRD §10 risk 1).

    1. Add a module-level constant with a comment, near `ALLOWED`
       (`test/test_mode_parity.py:55`):

       ```python
       # RESEARCH §1.7, re-verified at 187a786 on a built app: 15 call sites take g_df,
       # 7 take _fac_gdf, 7 take work_df, 14 take agg_fdf. _compute_kpi (3 sites) and
       # _compute_lpoly_fit (inside copied helper bodies) are NOT aggregate sites.
       _AGG_HELPERS = ("histogram", "lfit", "qfit", "lfitci", "qfitci", "kdensity",
                       "lowess", "lpoly", "lpolyci", "fpfit", "mspline", "mband",
                       "rscatter", "pcscatter")
       _AGG_CALL_SITES = 43
       _AGG_FRAMES = {"g_df": 15, "_fac_gdf": 7, "work_df": 7, "agg_fdf": 14}
       ```

    2. Add `class TestTheServerDivergenceIsExactlyThisWide:` with a `_app_source(tmp_path)`
       staticmethod modelled on `TestTheCopiedHelpersBringTheirCallees._app_module`
       (`test/test_mode_parity.py:415-435`): build a scatter spec through `ServerAppBuilder`
       under `warnings.catch_warnings()` and return `ap.read_text()` instead of importing it.
       Line numbers in a built app shift with the spec, so every assertion below must anchor on
       a regex or a substring, never on a line number.

    3. `test_the_aggregate_call_sites_are_still_the_forty_three_we_planned_for` — **no xfail**.
       Count with
       `re.findall(r"(?<![\w.])_compute_(?:%s)\(" % "|".join(_AGG_HELPERS), src)` and subtract
       the `def` lines matched by `r"def\s+_compute_(?:%s)\(" % …`; assert the difference equals
       `_AGG_CALL_SITES`. The `(?<![\w.])` guard is required: the app embeds a copy of
       `GlyphMapper` whose `self._compute_lpoly_fit` would otherwise be counted. Failure
       message: "the emitted app gained or lost an aggregate call site; every one of them needs
       a per-plot mask (TR-01.11) — update _AGG_CALL_SITES deliberately, not reflexively."

    4. `test_every_aggregate_call_site_takes_a_per_plot_masked_frame` — strict xfail,
       `raises=AssertionError`, reason naming **TR-01.11** and Phases 5-8. Build
       `{frame: len(re.findall(r"(?<![\w.])_compute_(?:%s)\(\s*%s\b" % (…, frame), src))
       for frame in _AGG_FRAMES}` and assert every value is `0`. The failure message must print
       the dict beside `_AGG_FRAMES` so the reader sees `{'g_df': 15, '_fac_gdf': 7,
       'work_df': 7, 'agg_fdf': 14}` — the four groups, not one.

    5. `test_the_emitted_plot_loop_reads_the_per_plot_qualifier` — strict xfail,
       `raises=AssertionError`, reason naming **TR-01.10 and D5** and Phases 5-8. Assert
       `"plot.get('if_expr')" in src`. Docstring: `dash.ado:1240`/`:1244` put `if_expr` on every
       segment and it reaches `_SPEC_B64`; the data is in the payload and the emitted code never
       looks at it (`dash.ado:1485`).

    6. `test_graph_qualifiers_is_keyed_by_graph_and_plot_index` — strict xfail,
       `raises=AssertionError`, reason naming **TR-01.12a**. Find the assignment with
       `re.search(r"_graph_qualifiers\[([^\]]+)\]\s*=", src)` and assert the captured key
       expression contains a plot index (a comma, i.e. a tuple). Today it captures `_gnq`.

    7. `test_the_by_facet_block_consults_the_per_plot_keys` — strict xfail,
       `raises=AssertionError`, reason naming **TR-01.12b**. Slice the app source between
       `"_by_q_df = df.copy()"` and `"for pi, plot in enumerate(g.get('plots', []))"` and assert
       a per-plot read (`"plot.get('if_expr')"`) occurs inside that slice.

    8. `test_the_filter_callback_reapplies_the_per_plot_mask` — strict xfail,
       `raises=AssertionError`, reason naming **TR-01.12c and BR-01.9**. Slice from
       `"_qual_cb = _gquals.get("` to the end of the aggregate recompute (the last
       `"_compute_pcscatter(agg_fdf"` occurrence) and assert **both**: a per-plot read occurs in
       the slice, and the aggregate recompute intersects rather than replaces — i.e. no
       `_compute_*` call in the slice takes a bare `agg_fdf`. The message must say
       "brushed ∩ per-plot, never replaced".

    9. `test_the_faceted_aggregate_entries_carry_their_options` — strict xfail,
       `raises=AssertionError`, reason: the facet and twin registry entries omit `'opts'`
       (`dash_render.py:15156`, `:15161`, `:15257`, `:15262`) while the plot loop's entry
       carries it (`:14110-14111`), so `agg.get('opts') or {}` at `:15605ff` degrades to `{}` for
       a faceted layer on the first widget move — RESEARCH §1.7 and §4.8. Assert every
       `agg_sources[(` assignment in the app source contains `'opts'`. Say in the reason that
       whoever implements TR-01.11 must add the mask **and** the missing `'opts'`.

    10. `test_server_mode_has_no_row_identity_carrier` — **no xfail**. Assert
        `src.count("_ROW_ID_COLUMN") == 1` and `src.count("__dash_row__") == 1` (the constant's
        own assignment, written out by the explicit constant tuple in `_glyph_layer_lines` at
        `dash_render.py:12362-12369` — not by the `_supply_missing_constants` scanner at
        `:16063`) and that `"_shared_data['index'] = list(df.index)"` is present.
        Docstring: D4 — the emitted app has no row-identity carrier, so the eventual mask must
        be over `df.index`; if this test ever fails because a carrier was added, the
        implementation shape changed and the plan needs updating rather than the test.

    11. `test_every_deferred_case_is_attributed_and_none_is_skipped` — **no xfail**. Walk this
        module's globals for classes, and their attributes for functions whose name starts with
        `test_`; read `getattr(fn, "pytestmark", [])`. Assert: no mark named `skip` or
        `skipif` anywhere in the module; every `xfail` mark has `strict is True`,
        `kwargs.get("raises") is AssertionError`, a `reason` containing `"Phases 5-8"` and a
        `reason` matching `r"TR-01\.\d+"`; and the number of xfail-marked functions equals a
        module constant `_DEFERRED_TO_PHASES_5_8 = 10` defined beside `_AGG_CALL_SITES` with a
        comment that lowering it means an unimplemented case was deleted rather than fixed.
        (One in 09-01, three in 09-02, six here.)

    Finally, extend the module docstring (`test/test_mode_parity.py:1-23`) with one bullet in
    its existing voice: per-plot qualifiers on computed layers reach one renderer and not the
    other; the deferred cases below carry the divergence until Phases 5-8. Do **not** add an
    entry to `ALLOWED` — this is a defect, not a legitimate difference, and `ALLOWED` is what a
    reader consults to learn which differences are intentional.
  </action>
  <verify>
    `cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_mode_parity.py::TestTheServerDivergenceIsExactlyThisWide -q`
    prints `3 passed, 6 xfailed`.
    `python3 -m pytest test/test_mode_parity.py::TestTheServerDivergenceIsExactlyThisWide --runxfail -q`
    prints `3 passed, 6 failed`, and the masked-frame failure prints
    `{'g_df': 15, '_fac_gdf': 7, 'work_df': 7, 'agg_fdf': 14}`.
    Whole module: `python3 -m pytest test/test_mode_parity.py -q` reports `11 xfailed`
    alongside the module's pre-existing passes, with no failures, no errors and no skips.
    Eleven outcomes, ten marked functions — the aggregate case in 09-02 is parametrized over
    `histogram` and `kdensity` — which is why `_DEFERRED_TO_PHASES_5_8 = 10` counts functions
    and not outcomes.
  </verify>
  <done>
    `test/test_mode_parity.py` now states the exact width of the server divergence — 43
    aggregate call sites in four groups, zero per-plot reads, a gname-only qualifier registry, a
    facet block and a callback block that never consult a plot index, facet registry entries
    missing `'opts'`, and no row-identity carrier — with each deferred case attributed to
    Phases 5-8 and its TR, and a guard that fails if one is deleted instead of implemented.
    Items 2, 5 and 6 are discharged as tests; no product code changed in this section.
    Commit on `feature/batch4-interactive-layer` (project rule 6), no AI references in the
    message (rule 7), and report `git checkout main && git merge feature/batch4-interactive-layer`
    rather than running it.
  </done>
</task>
