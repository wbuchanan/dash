# Section 06: Survival under interaction

## Overview

Sections 02-05 make a qualified layer correct **on first paint**. This section makes it stay
correct after the viewer touches a widget. Three defects share that shape. **Item 7:**
`_make_figure_body` builds the combined `facet AND qualifier` mask at `dash_render.py:9986-9988`
but registers only the qualifier's own rows at `:9991-9992`; the browser rebuild at `:7169` is a
*total* replacement of `booleans`, so the facet term is discarded on the first widget move and a
panel then shows qualifier-passing rows from every facet. **Item 9:** `map_scatter` draws from
the private source `_build_jitter_source` returns (`:2521`, called at `:3459`) while the view was
registered against the graph source; the callback shortens the graph source and rebuilds the
filter to its kept-row length, then that filter is applied to a source that still has every row.
**Item 10:** the browser-side histogram/kdensity recompute (`_FILTER_JS:7390-7399`) reads
`new_data[ac.varname]` — the primary snapshot, every row — so a qualified aggregate opens on the
conditional sample and silently becomes the unconditional one.

Nothing here is visible in a screenshot of the first render. If this section is deferred, the
phase looks finished and fails the moment a user drags a slider.

**TDD convention for this section: each implementation task begins by writing its own failing
test and confirming it fails for the stated reason.** There is no single up-front test task.
One commit per task, on `feature/batch4-interactive-layer`.

## Risk: [red] — Three interaction defects in shared machinery; the jitter fix changes which `ColumnDataSource` objects the filter callback touches, and `:11902` raises `KeyError` the moment a source outside `self.sources` reaches it.

## Dependencies
- Depends on: section-02, section-03, section-04, section-05
- Blocks: section-10
- Parallel batch: 4

## Evidence

### Item 7 — the intersection loss (RESEARCH §1.5, CONFIRMED at `187a786`)

`_make_figure_body`, `dash_render.py:9974-9992`, verbatim at HEAD:

```python
 9974                    _ids = list(source.data.get(_ROW_ID_COLUMN, []))
 9975                    if not _ids:
 9976                        raise ValueError("source carries no row identity")
 9977                    _pos = {idx: i for i, idx in enumerate(self.df.index)}
 9978                    _wanted = {_pos.get(i, -1) for i in _pdf.index}
 9979                    _mask = [bool(r in _wanted) for r in _ids]
 ...
 9985                    _prev_bools = getattr(_prev, "booleans", None)
 9986                    if _prev_bools is not None and len(_prev_bools) == len(_mask):
 9987                        _mask = [bool(a and b)
 9988                                 for a, b in zip(_prev_bools, _mask)]
 9989                    _pf = BooleanFilter(booleans=_mask)
 9990                    _plot_view = CDSView(filter=_pf)
 9991                    self._register_view_filter(
 9992                        source, _pf, self._row_ids_for(_pdf))
 9993                except Exception as _pexc:          # never lose the layer
```

At `:9987` `_mask` becomes `facet_mask AND qualifier_mask`. At `:9992` the registered member set
is `self._row_ids_for(_pdf)` — **the qualifier alone**. `_register_view_filter`
(`:8509-8524`) stores `(source, BooleanFilter, member_ids)`; the `CDSView` itself is not stored
and no copy of the render-time mask is kept anywhere, so `member_ids` is the sole source of
truth. The rebuild in `_FILTER_JS` (`:7164-7171`), verbatim:

```javascript
 7167    const kept = _kept_ids_by_src[_si] || [];
 7168    const member = new Set(vf.member_ids || []);
 7169    vf.filter.booleans = kept.map(id => member.has(id));
 7170    vf.filter.change.emit();
```

`:7169` never reads the prior `booleans`. **Fix shape (RESEARCH §1.5):** register the ids the
*combined* mask selects — `[r for r, keep in zip(_ids, _mask) if keep]`.

> **D3 (RESEARCH §1.5, NEW).** The length guard at `:9986` **silently skips** the intersection
> when `len(_prev_bools) != len(_mask)`, and then `:9989-9990` still replaces `_plot_view` with a
> qualifier-only view — so the facet restriction is lost **at initial render too**. The
> `except Exception` at `:9993` does not catch it because nothing raises. Lengths coincide today
> only because `linked_source` (`:11379`) is built without `df=`.

Three registration sites exist: `:9991` (per-plot), `:11399` (linked-graph qualifier), `:11475`
(linked `by()` panel). `_register_view_filter` is **not initialised in `__init__`** — `:8522-8523`
creates `self._view_filters` lazily and never resets it. Do not copy that pattern for new state.

### Item 9 — jitter: three blockers, not one (RESEARCH §1.4)

`_build_jitter_source` (`:2521`) copies **all** columns at `:2559` —
`new_data = {k: list(v) for k, v in source.data.items()}` — so `__dash_row__` survives and row
count and order are identical. At initial render the view is valid. After the first widget move
it is not: the callback shortens only sources in `all_graph_sources` and rebuilds booleans to the
kept-row count (`:7167-7169`), while the jittered CDS keeps every row.

Appending the jittered source to `all_graph_sources` (`:11881-11887`) is **necessary but not
sufficient**:

1. **`:11902` would raise `KeyError`.** `_snapshot_of` is keyed by `id()` and populated only from
   `self.sources` (`:11835-11841`); the comprehension at `:11901-11903` is unguarded.
2. **The snapshot must be taken from the jittered CDS**, so kept rows retain their own offsets.
   There is no JS port of `_apply_jitter` (`:2231`), so offsets cannot be re-derived client-side.
   The per-source loop at `:7132-7157` already rebuilds each source from *its own* snapshot, reading
   that source's identities at `:7138` (`const _ids_i = _orig_i[ROW_ID];`) and keeping a row when
   `_active_ids.has(_ids_i[i])` (`:7145-7147`), so a correct snapshot is all that is needed.
3. **`_view_filter_args` resolves by object identity** (`ordered_sources.index(source)`, `:8542`)
   and all three registration sites register the *shared* source.

Confirmed at HEAD: `:3459` reads `plot_source, eff_x, eff_y = self._build_jitter_source(...)` and
`:3467` passes `source=plot_source` to `fig.scatter`, while `:9991` registered `source`.

Related private sources in the same code path: `map_scatter`'s NaN-dropped `clean_source`
(`:3452-3454`, which copies every column so `__dash_row__` survives) and `map_dropline`'s
`dl_source` (`:5260`), which jitters inline at `:5244-5248` into a column set (`:5250-5253`) that
**omits `__dash_row__` entirely** — so a `map_scatter` fix does not generalise.

> **D2 (RESEARCH §1.3, carried forward).** Private sources are invisible to the filter callback
> *generally*, not only to the qualifier: `sorted_source`, `clean_source`, `seg_source`,
> `dl_source` and every computed mapper's CDS are never updated when a widget moves. This
> section reduces D2 for the sources a *qualifiable* raw-data layer draws from; it does not close
> it, and must not claim to.

> **B1 (RESEARCH §2.3, measured in a real browser).** After a callback grew a source 10 → 12
> rows, the `BooleanFilter` still held **10** booleans. No error, no warning; the two new rows
> were simply invisible. **Any callback that rewrites a shared source must also rewrite every
> `BooleanFilter.booleans` to the new length.** The jitter defect is the special case where the
> source the filter is applied to is never rewritten at all.

### Item 10 — the KPI path is a working precedent to copy (RESEARCH §1.6)

Only two producers of `_dash_agg_config` exist: `:4695` (histogram) and `:4905` (kdensity). Both
attach plain Python attributes to the `GlyphRenderer`. Both mappers' early-outs (`:4662-4665`,
`:4835-4837`, `:4859-4861`) return **untagged** renderers. Registry at `:12203-12210`
(inside `render()`, not `_assemble_layout`); wiring at `:11905-11914`.

The `_FILTER_JS` agg loop selects rows **by column name only** — no graph id, no source index, no
row-id list — and reads the already-filtered `new_data` (built at `:7097-7104` from `orig`, the
**primary** snapshot):

```javascript
 7390 for (let ai = 0; ai < agg_configs.length; ai++) {
 7391     const ac  = agg_configs[ai];
 7392     const src = agg_sources[ai];
 7393     if (!src) continue;
 7395     // Pull filtered values for this aggregate variable.
 7396     // new_data already contains only the rows that passed every active filter.
 7397     const raw_col = new_data[ac.varname];
 7398     if (!raw_col) continue;
 7399     const vals = raw_col.filter(v => v !== null && v !== undefined && !isNaN(v));
```

`_kpi_callback_config` (`:11613`, `:11620-11621`) and `dash_apply_kpis` (`:7215-7225`) already do
exactly the needed thing:

```python
11613        qual_ids = self._kpi_qualifier_row_ids(kdef)
11620            "has_qual": qual_ids is not None,
11621            "qual_ids": qual_ids if qual_ids is not None else [],
```

```javascript
 7215        let src_col = col;
 7216        if (k.has_qual) {
 7217            const qset = new Set(k.qual_ids || []);
 7218            const rids = data_obj[ROW_ID];
 7219            src_col = [];
 7220            if (rids) {
 7221                for (let qi = 0; qi < col.length; qi++) {
 7222                    if (qset.has(rids[qi])) src_col.push(col[qi]);
 7223                }
 7224            }
 7225        }
```

**Copy that shape.** Three insertion points: **(a)** config build `:4695-4703` and `:4905-4913` —
the ids arrive from `_make_figure_body`, where the combined-mask id list is already being built
for item 7; **(b)** serialization needs **no change** (`dict(...)` shallow-copies at `:12205-12206`,
`_row_ids_for` already returns `int`, `json.dumps` at `:11914`); **(c)** JS between `:7397` and
`:7399`, where `ROW_ID` is already in scope (`:7115`). **Preserve the tri-state:** `None` =
unrestricted, `[]` = blank the layer.

> **Residual gap (out of scope, recorded).** Even with (a)-(c) the recompute still draws from
> `new_data`, the **primary** source. An aggregate on an unlinked graph with a *different frame*
> is already recomputed from the wrong row universe today. Do not widen this section to it.

### The approved addition — Q7, the graph-level qualifier (DISCOVERY Q7, index "Additions")

The graph-level qualifier shares item 10's defect and lives on the same code path. Fixing only
the per-plot half would knowingly ship a defect this change touches. `_layer_row_ids` (task
06-01) answers all three restriction kinds uniformly:

| restriction | where it lives at render time | branch |
|---|---|---|
| unlinked graph-level qualifier | `self.sources[name]` is itself the subset | source shorter than `self.df` |
| linked graph-level qualifier | `_linked_graph_views[name]`, registered at `:11397-11399`, arrives as `facet_view` via `:11505` | `view.filter.booleans` |
| `by()` panel, linked | `panel_view_r`, registered at `:11470-11475` | `view.filter.booleans` |
| `by()` panel, unlinked | `self.sources[fkey]` is itself the subset | source shorter than `self.df` |
| per-plot `if`/`in` | `_pf` built at `:9989` from the combined mask | `view.filter.booleans` |

This means an **unqualified** faceted histogram also stops recomputing from the full frame on a
widget move — the browser-side sibling of F-A (RESEARCH §1.9). That is a behaviour change inside
BR-01.8/BR-01.9 and it needs its own test (task 06-07), not silence.

### The trap that governs every test in this section (RESEARCH §1.9, F-B)

Existing coverage is scatter-only and **structurally cannot catch this class of bug**.
`test/test_varlist_expansion.py:101`'s `_visible_count` helper reads
`renderer.view.filter.booleans`, which reports a *computed* layer as fully visible no matter what
it drew. **Assertions on computed layers must compare the layer's own source values against an
independently computed subsample**, never a view's booleans. For a histogram that means
`r._dash_agg_source.data["top"]` against `np.histogram(subsample, bins=r._dash_agg_config["bin_edges"])`.
Item 7 is the one exception, and only because the `BooleanFilter` *is* the defect: there the
assertion is on the registered `member_ids` and on the booleans the shipped JS rebuilds, never on
a row count.

### The harness to reuse

`test/test_linking_filters.py:340-420` already runs the **shipped** `_FILTER_JS` under `node`:
it slices the block out of `dash_render._FILTER_JS` by string index, stubs
`all_graph_sources_orig` / `_srcs` / `active` / `new_data` / `orig` / `view_filters`, writes an
`.mjs` file and runs it under `subprocess`. Copy that pattern rather than transliterating the JS
into Python. `_NODE = shutil.which("node")` with `@pytest.mark.skipif` is the established guard —
but **a skip is not a pass**, so every node test in this section is paired with a Python-side
assertion on the shipped `_FILTER_JS` text that runs unconditionally.

## TDD test stubs

- **Test:** `DashRenderer._layer_row_ids` returns `None` for a full-length source with no view;
  the kept ids for a full-length source under a `BooleanFilter`; the source's own ids for a
  pre-filtered (shorter) source; `[]` — not `None` — for an all-False mask; and raises
  `ValueError` when the view's boolean count does not match the source's row count.
  → `test/test_layer_row_ids.py` (new). Fails before 06-01 with `AttributeError`.
- **Test:** `test_intersection_survives_a_filter_move` — on a **linked** `by()` dashboard whose
  panel layer carries a per-plot `if`, the registered `member_ids` equal `panel rows ∩ qualifier
  rows`, and after the shipped rebuild the panel's booleans still select only that intersection.
  → `test/test_per_plot_qualifier_computed.py` (created by section 02). Fails before 06-01
  because `:9992` registers the qualifier's rows only.
  *Mutation that must kill it:* restore `self._row_ids_for(_pdf)` at `:9992`.
- **Test:** a `_prev_bools` length mismatch warns naming the layer and leaves the prior view in
  place, instead of silently replacing it. → same file. Fails before 06-01 (D3: nothing raises,
  nothing warns, and the facet view is replaced).
- **Test:** `map_dropline`'s `dl_source` carries `__dash_row__`, with the ids of the rows that
  survived the NaN mask. → `test/test_dropline_marker_options.py`. Fails before 06-02 with a
  `KeyError`.
  *Mutation:* delete the new `_dl_cols[_ROW_ID_COLUMN]` assignment.
- **Test:** `_build_jitter_source` and `map_scatter`'s `clean_source` both keep `__dash_row__`.
  → `test/test_jitter.py`. Passes today; it is a regression pin.
  *Mutation that must kill it:* narrow `:2559` to `{xvar, yvar}`.
- **Test:** a jittered, qualified scatter's renderer has a `CDSView` whose `BooleanFilter` is
  registered **against the renderer's own `data_source`**, with
  `len(booleans) == len(data_source.data["__dash_row__"])`, and whose True positions are the
  qualifier's rows *by id*. → `test/test_qualifier_survives_interaction.py` (new). Fails before
  06-03: the registration is against the graph source and the booleans are sized to it.
  *Mutation:* point `_register_view_filter` back at `source`.
- **Test:** `cb.args["all_graph_sources"]` contains the jittered source; its entry in
  `all_graph_sources_orig` carries `_x_jit`/`_y_jit` holding the **jittered** values; and the
  number of distinct `ColumnDataSource` objects referenced by the figure's renderers is unchanged
  by the fix. → `test/test_qualifier_survives_interaction.py`. Fails before 06-04.
- **Test:** `_dash_agg_config` on a qualified histogram carries `has_qual is True` and `qual_ids`
  equal to the layer's rows; on an unqualified one `has_qual is False` and `qual_ids == []`; and
  `json.loads(cb.args["agg_configs_json"])` round-trips both. → `test/test_per_plot_qualifier_computed.py`.
  Fails before 06-05 with `KeyError`.
  *Mutation:* drop the two keys from `:4695-4703`.
- **Test:** `test_histogram_qualified_still_correct_after_filter_move` and its `kdensity` twin —
  drive the shipped agg branch under node and assert the recomputed `top` / `y` arrays equal the
  same computation on `widget rows ∩ qualifier rows`. Compare **source values**, never a view's
  booleans. → `test/test_per_plot_qualifier_computed.py`. Fails before 06-06.
  *Mutation:* delete the `ac.has_qual` block from `_FILTER_JS`.
- **Test:** the shipped `_FILTER_JS` agg block textually references `ROW_ID` and `qual_ids`
  between `const agg_configs = JSON.parse` and `if (ac.type === 'histogram')`. Runs with no node.
  → `test/test_per_plot_qualifier_computed.py`.
- **Test:** a graph-level qualifier — **linked and unlinked** — and an unqualified `by()` panel
  each produce `has_qual is True` with the right ids, and each recomputes to the intersection.
  → `test/test_qualifier_survives_interaction.py`. Fails before 06-07 for at least the unlinked
  and `by()` cases.
- **Test (B1 invariant):** for every `(source, bool_filter, member_ids)` in `r._view_filters`,
  `len(bool_filter.booleans) == len(source.data["__dash_row__"])` at render time, and after the
  shipped rebuild `len(booleans) == len(kept)` for that source.
  → `test/test_qualifier_survives_interaction.py`.
- **Test (end to end):** `test/test_e2e_filters.cscript` gains a case that builds a dashboard with
  a per-plot-qualified `histogram` plus a filter widget and asserts the emitted `agg_configs_json`
  carries a non-empty `qual_ids`. Run with `arch -arm64` from `test/`, with `$dash_nobrowser` set.

## Tasks

<task type="auto" id="06-01">
  <name>Register the rows the layer actually draws, and stop the silent skip</name>
  <files>dash_render.py, test/test_layer_row_ids.py (new), test/test_per_plot_qualifier_computed.py</files>
  <action>
    Write the tests first and confirm they fail for the stated reason before touching
    `dash_render.py`.

    1. Create `test/test_layer_row_ids.py`. Header follows the house style used by
       `test/test_per_plot_qualifier_linking.py:24-38`: a docstring naming the defect, then
       `sys.path.insert(0, ...)` for the repo root and `test/`, `import dash_render as dr`, and
       `from conftest import make_data_json`. Unit-test `DashRenderer._layer_row_ids(source, view)`
       (rule 4), one test per branch:
         - source with no `__dash_row__` column → `None`;
         - full-length source, `view=None` → `None`;
         - full-length source, `CDSView(filter=BooleanFilter(booleans=[...]))` → the ids at the
           True positions, as `int`;
         - all-False booleans → `[]`, and explicitly `assert ids == [] and ids is not None`
           (the tri-state: `[]` must blank the layer, `None` must not);
         - source shorter than `self.df`, `view=None` → the source's own ids;
         - booleans whose length differs from the source's row count → `pytest.raises(ValueError)`.
       These fail with `AttributeError: 'DashRenderer' object has no attribute '_layer_row_ids'`.

    2. In `test/test_per_plot_qualifier_computed.py` (the module section 02 creates; if you are
       running 06 before 02, create it with the same header) add
       `test_intersection_survives_a_filter_move`. Build a **linked** `by()` dashboard — the test
       must be on a linked dashboard, because in the unlinked case the panel source is itself the
       subset and the defect does not bite. Give one panel layer a per-plot `if`. Then:
         - locate the triple in `r._view_filters` whose `bool_filter` is the per-plot layer's
           `renderer.view.filter`;
         - assert `set(member_ids) == set(panel_ids) & set(qualifier_ids)`, where both operands are
           computed independently in the test from the DataFrame, not read back from dash;
         - simulate the shipped rebuild exactly as `_FILTER_JS:7167-7169` does —
           `[rid in set(member_ids) for rid in kept_ids]` for the ids the source keeps under a
           widget value — and assert the resulting True set is still the intersection.
       Pre-fix this fails: `member_ids` is the qualifier's rows only, so the rebuilt booleans admit
       qualifier-passing rows from every facet.

    3. Add `test_a_prior_view_length_mismatch_warns_and_keeps_it` to the same module: construct the
       case where `len(_prev_bools) != len(_mask)` and assert (a) a `UserWarning` whose text names
       `layer {pi + 1}`, and (b) the layer's view is still the prior (facet) view, not a
       qualifier-only one.

    4. Now implement. Add `_layer_row_ids` to `DashRenderer`, immediately after `_row_ids_for`
       (which ends at `:8592`) and next to `_kpi_qualifier_row_ids` (`:8549`), whose tri-state
       docstring it mirrors:

           def _layer_row_ids(self, source, view) -> "list[int] | None":
               """Row identities a layer actually draws, or None when unrestricted.

               Tri-state, exactly as _kpi_qualifier_row_ids: None means "no
               restriction at all", [] means "a restriction that selects
               nothing" -- the layer must be blanked, not shown whole.

               Answers every restriction kind through one channel: a per-plot
               if/in (a BooleanFilter over the graph source), a linked graph's
               own qualifier and a linked by() panel (the same), and an
               unlinked qualified graph or by() panel (a source that is
               already the subset).

               Raises:
                   ValueError: the view's boolean count does not match the
                       source's row count, so the two cannot be intersected.
               """
               ids = list(source.data.get(_ROW_ID_COLUMN, []))
               if not ids:
                   return None
               booleans = getattr(getattr(view, "filter", None), "booleans", None)
               if booleans is not None:
                   if len(booleans) != len(ids):
                       raise ValueError(
                           f"a view with {len(booleans)} booleans cannot be "
                           f"intersected with a source of {len(ids)} rows")
                   return [int(r) for r, keep in zip(ids, booleans) if keep]
               if len(ids) < len(self.df):
                   return [int(r) for r in ids]
               return None

    5. At `:9986`, replace the silent skip with a raise, so the existing `except Exception` at
       `:9993` turns it into the named warning BR-01.12 requires. Replace

           if _prev_bools is not None and len(_prev_bools) == len(_mask):

       with

           if _prev_bools is not None:
               # D3: a mismatch used to be skipped in silence, and :9989-9990
               # then REPLACED the prior view with a qualifier-only one -- the
               # facet restriction was lost at initial render, not just after a
               # widget move.  Raise so the layer keeps the prior view and says
               # what happened.
               if len(_prev_bools) != len(_mask):
                   raise ValueError(
                       f"a prior view with {len(_prev_bools)} booleans cannot "
                       f"be intersected with a mask of {len(_mask)} rows")

       keeping the existing two-line `_mask = [bool(a and b) ...]` body under it.

    6. At `:9991-9992`, register the combined set. Replace
       `self._register_view_filter(source, _pf, self._row_ids_for(_pdf))` with

           # The COMBINED rows, not the qualifier's own: _FILTER_JS:7169 is a
           # total replacement of `booleans' and never reads the prior value,
           # so a facet AND-term registered as anything less is discarded on
           # the first widget move.
           self._register_view_filter(
               source, _pf, self._layer_row_ids(source, _plot_view))

       `_plot_view` is assigned at `:9990` from `_pf`, so this returns exactly
       `[r for r, keep in zip(_ids, _mask) if keep]`.

    Cite BR-01.8, BR-01.9, BR-01.12, TR-01.7.
  </action>
  <verify>
    `python3 -m pytest test/test_layer_row_ids.py test/test_per_plot_qualifier_computed.py -q`
    prints no failures. Then mutate: put `self._row_ids_for(_pdf)` back at `:9992`, rerun, and
    confirm `test_intersection_survives_a_filter_move` FAILS; restore the fix. Then
    `python3 -m pytest test/test_per_plot_qualifier_linking.py test/test_layout_facets.py test/test_linking.py -q`
    prints no failures.
  </verify>
  <done>
    `DashRenderer._layer_row_ids` exists with a unit test per branch. The per-plot block registers
    the intersected row set, and a prior-view length mismatch raises, warns naming the layer, and
    leaves the prior view attached instead of replacing it.
  </done>
</task>

<task type="auto" id="06-02">
  <name>Give every private source a row identity</name>
  <files>dash_render.py, test/test_dropline_marker_options.py, test/test_jitter.py</files>
  <action>
    Failing test first.

    1. In `test/test_dropline_marker_options.py` add
       `test_dl_source_carries_the_row_identifier`: call `GlyphMapper.map_dropline` with a
       `ColumnDataSource` that carries `dash_render._ROW_ID_COLUMN` and a NaN in one of the two
       plot variables. Assert the returned renderers' `data_source.data` contains
       `dash_render._ROW_ID_COLUMN`, that its length equals the non-NaN row count, and that its
       values are the ids of exactly the surviving rows (not `range(n)`). This fails at HEAD:
       `_dl_cols` (`:5250-5253`) lists only `"x"`, `"y"`, `"y0"`, `xvar`, `yvar` and an optional
       mlabel column, so the key is absent.

    2. In `test/test_jitter.py` add a `TestPrivateSourcesKeepRowIdentity` class with two pins that
       pass at HEAD and must not be allowed to regress:
         - `_build_jitter_source` returns a CDS whose `__dash_row__` column is identical, in value
           and order, to the input's (`:2559` copies every column);
         - `map_scatter` given a source with a NaN in `xvar` returns a renderer whose
           `data_source` still carries `__dash_row__` with the surviving ids (`:3452-3454` builds
           `clean_source` from a full-column DataFrame copy, then drops NaN rows).
       State the mutation in each docstring: narrowing `:2559` to `{xvar, yvar}`, or narrowing the
       `clean_source` comprehension at `:3452`, must make these die.

    3. Implement. In `map_dropline`, between the `_dl_cols` literal ending at `:5253` and
       `dl_source = ColumnDataSource(_dl_cols)` at `:5260`, add:

           # The filter callback masks a source by row identity
           # (_FILTER_JS:7138-7147), so a private source without __dash_row__
           # can never be shortened correctly -- and a CDSView over it cannot
           # be rebuilt at all.  `mask' is the non-NaN mask built at :5239.
           if _ROW_ID_COLUMN in source.data:
               _dl_cols[_ROW_ID_COLUMN] = np.asarray(
                   source.data[_ROW_ID_COLUMN])[mask]

       `_ROW_ID_COLUMN` is a module-level constant (`:591`), so it is in scope inside
       `GlyphMapper`. Place the assignment before the existing mlabel block at `:5254-5259` or
       after it; either is fine, but keep it inside the same `_dl_cols` construction so the
       optional mlabel column is unaffected.

    Do not change `_build_jitter_source` or `map_scatter` in this task — they are already correct
    and this task only pins them.

    Cite TR-01.8, BR-01.9.
  </action>
  <verify>
    `python3 -m pytest test/test_dropline_marker_options.py test/test_jitter.py -q` prints no
    failures. Then `python3 -c "import dash_render as d, inspect; s=inspect.getsource(d.GlyphMapper.map_dropline); print(d._ROW_ID_COLUMN in s)"`
    prints `True`.
  </verify>
  <done>
    Every private `ColumnDataSource` a qualifiable raw-data layer can draw from — the jitter copy,
    `map_scatter`'s NaN-dropped copy, and `map_dropline`'s `dl_source` — carries `__dash_row__`,
    and each is pinned by a test that names the mutation that would kill it.
  </done>
</task>

<task type="auto" id="06-03">
  <name>Reconcile the per-plot view with the source the glyph really draws from</name>
  <files>dash_render.py, test/test_qualifier_survives_interaction.py (new)</files>
  <action>
    Failing test first.

    1. Create `test/test_qualifier_survives_interaction.py`. Docstring: item 9 / TR-01.8 — the
       view was registered against the graph source while the glyph drew from a private one, so
       the callback rebuilt the filter to one length and applied it to a source of another. Add
       `test_a_jittered_qualified_layer_is_masked_on_its_own_source`: render a dashboard with one
       scatter layer carrying `jitter(5) jseed(42)` **and** a per-plot `if`, plus one filter
       widget. Assert, on the scatter renderer:
         - `r.data_source is not` the graph source (the jitter copy);
         - a triple exists in `dr._view_filters` whose source **is** `r.data_source` and whose
           `bool_filter is r.view.filter`;
         - `len(r.view.filter.booleans) == len(r.data_source.data[dash_render._ROW_ID_COLUMN])`;
         - the ids at the True positions equal the qualifier's rows, computed independently in the
           test from the DataFrame.
       At HEAD this fails on the second assertion: `:9991` registered the graph `source`.

    2. Implement. In `DashRenderer.__init__`, immediately after
       `self.agg_source_registry: dict = {}` (`:8123`), add:

           # Private ColumnDataSources a mapper built for itself (a jittered
           # scatter's, a dropline's) that the filter callback must shorten
           # like any other graph source.  graph_name -> [cds, ...].
           # Initialised HERE, not lazily: _view_filters (:8522) is created on
           # first use and never reset, which is a wart, not a pattern.
           self._aux_sources: "dict[str, list]" = {}

       and a registrar next to `_register_view_filter` (`:8509`):

           def _register_aux_source(self, gname: str, source) -> None:
               """Remember a private source the filter callback must shorten."""
               bucket = self._aux_sources.setdefault(gname, [])
               if not any(s is source for s in bucket):
                   bucket.append(source)

    3. In `_make_figure_body`, add `_plot_pf = None` next to `_plot_view = facet_view` at `:9956`,
       and set `_plot_pf = _pf` immediately after `:9989`. (`_plot_pf` is not used by this task's
       final code but records, per layer, whether a per-plot filter was built; keep it only if
       your implementation needs it — otherwise omit both lines rather than leaving dead state.)

    4. In `_make_figure_body`, immediately after
       `_layer_renderers = list(fig.renderers[_r_before:])` at `:10066` and before
       `_plot_renderers.append(...)` at `:10067`, insert:

           # A mapper that builds a source of its own -- _build_jitter_source
           # (:2521), map_scatter's NaN-dropped clean_source (:3454),
           # map_dropline's dl_source (:5260) -- leaves the view registered
           # against the GRAPH source.  The callback then rebuilds those
           # booleans to the graph source's kept-row count and they are applied
           # to a source that has its own length, so the mask lands on the
           # wrong rows (TR-01.8).  Give each such renderer its own filter over
           # its own source, by identity, and record the source so the callback
           # shortens it too.
           _aux_ids = None
           if _plot_view is not None:
               try:
                   _aux_ids = self._layer_row_ids(source, _plot_view)
               except ValueError as _aexc:
                   warnings.warn(
                       f"dash: layer {pi + 1} draws from a source of its own "
                       f"and its restriction could not be carried over "
                       f"({_aexc}); the layer is drawn unfiltered.",
                       stacklevel=2,
                   )
           for _r in _layer_renderers:
               _rsrc = getattr(_r, "data_source", None)
               if _rsrc is None or _rsrc is source:
                   continue
               if _ROW_ID_COLUMN not in _rsrc.data:
                   continue
               self._register_aux_source(graph_opts.get("name", ""), _rsrc)
               if _aux_ids is None:
                   continue
               _aux_member = set(_aux_ids)
               _aux_pf = BooleanFilter(booleans=[
                   bool(int(r) in _aux_member)
                   for r in _rsrc.data[_ROW_ID_COLUMN]])
               _r.view = CDSView(filter=_aux_pf)
               self._register_view_filter(_rsrc, _aux_pf, _aux_ids)

       Four properties this shape must have, and which the tests must assert:
         - it registers the aux source **whether or not** there is a restriction, because a
           jittered layer with no qualifier does not respond to filter widgets today either (D2);
         - it gives each renderer its **own** `BooleanFilter`, so a layer sharing a facet
           `CDSView` with unjittered siblings cannot break them;
         - the original registration at `:9991` stays, because a mapper such as `map_connected`
           returns one renderer over the private source and one over the graph source, and the
           latter still needs it. One extra harmless entry in `_view_filters` is the price;
         - it skips any private source without `__dash_row__` (every computed mapper's CDS,
           `sorted_source`, `seg_source`), because those cannot be masked by identity. D2 is
           reduced here, not closed — do not claim otherwise.

    Note for the test author: this task's assertions are on a **raw-data** scatter, so a row count
    is meaningful. The moment the same file asserts on a computed layer, it must compare that
    layer's own source values against an independently computed subsample, never
    `renderer.view.filter.booleans` — see `test/test_varlist_expansion.py:101`.

    Cite TR-01.8, TR-01.15, BR-01.9, BR-01.11.
  </action>
  <verify>
    `python3 -m pytest test/test_qualifier_survives_interaction.py test/test_jitter.py test/test_dropline_marker_options.py -q`
    prints no failures. Then mutate: change the new block to call
    `self._register_view_filter(source, _aux_pf, _aux_ids)` (the graph source), rerun, and confirm
    `test_a_jittered_qualified_layer_is_masked_on_its_own_source` FAILS; restore.
  </verify>
  <done>
    A layer that draws from a private source carrying `__dash_row__` has a `CDSView` whose
    `BooleanFilter` is sized to and registered against *that* source, and the source is recorded in
    `self._aux_sources`. Nothing reads `_aux_sources` yet — that is 06-04.
  </done>
</task>

<task type="auto" id="06-04">
  <name>Make the filter callback reach the private sources, and measure the cost</name>
  <files>dash_render.py, test/test_qualifier_survives_interaction.py, test/test_filter_payload_size.py</files>
  <action>
    Failing test first.

    1. Add to `test/test_qualifier_survives_interaction.py`:
         - `test_the_jittered_source_is_in_all_graph_sources`: `cb = dr.filter_callbacks[0]`;
           assert the scatter renderer's `data_source` is in `cb.args["all_graph_sources"]` by
           identity, and that `len(cb.args["all_graph_sources_orig"]) == len(cb.args["all_graph_sources"])`.
         - `test_the_snapshot_holds_the_jittered_values`: the snapshot at that source's index
           carries `_x_jit` / `_y_jit` and its values equal the jittered source's, **not** the
           unjittered `xvar`/`yvar`. This is blocker (2): there is no JS port of `_apply_jitter`
           (`:2231`), so offsets that are not in the snapshot cannot be re-derived in the browser.
         - `test_the_fix_adds_no_column_data_source_to_the_figure`: the number of **distinct**
           `ColumnDataSource` objects reachable from `fig.renderers` (by `id()`) is the same as at
           HEAD for the same spec. Record the expected number in the test as a literal with a
           comment saying what it counts. The jitter copy already exists at HEAD (`:2562` returns
           `ColumnDataSource(new_data)` unconditionally when jitter is on); this fix makes it
           *reachable*, it does not create it.
       All three fail before the implementation below.

    2. Implement step (a) **alone** first and run the tests once: add, between `:11886` and the
       `_cb.args["all_graph_sources"] = _graph_srcs_for_cb` assignment at `:11887`:

           # Private sources a mapper built for itself carry __dash_row__ and a
           # CDSView of their own now, so the callback has to shorten them like
           # any other graph source -- otherwise the view is rebuilt against
           # rows the source no longer has (RESEARCH B1).
           for _aux_gname, _aux_list in self._aux_sources.items():
               if _aux_gname in _fc_excludes:
                   continue
               for _aux in _aux_list:
                   if not any(s is _aux for s in _graph_srcs_for_cb):
                       _graph_srcs_for_cb.append(_aux)

       Run the tests. They must now fail with `KeyError` raised from the comprehension at
       `:11901-11903`. That is blocker (1) from RESEARCH §1.4 reproducing exactly as predicted —
       record the traceback line in the commit message and move on.

    3. Implement step (b): make the snapshot lookup build on demand. Keep the eager loop at
       `:11835-11841` as it is (minimal diff, stable model ordering) and add, immediately after it:

           def _snapshot_for(_gsrc) -> ColumnDataSource:
               """One snapshot model per source, built on first use.

               Built lazily because a private source -- a jittered scatter's, a
               dropline's -- is not in self.sources and would KeyError here.
               The snapshot must come from the PRIVATE source so its kept rows
               keep their own jitter offsets: there is no JS port of
               _apply_jitter (:2231).
               """
               _key = id(_gsrc)
               if _key not in _snapshot_of:
                   _snapshot_of[_key] = ColumnDataSource({
                       _col: [DashRenderer._to_serialisable(v) for v in _arr]
                       for _col, _arr in _gsrc.data.items()
                   })
               return _snapshot_of[_key]

       and replace the comprehension at `:11901-11903` with

           _cb.args["all_graph_sources_orig"] = [
               _snapshot_for(_gsrc) for _gsrc in _graph_srcs_for_cb
           ]

       No change is needed in `_FILTER_JS`: the per-source loop at `:7132-7157` already rebuilds
       each source from its own snapshot, masking it by the identities read at `:7138`, and the
       view rebuild at
       `:7167-7169` already sizes `booleans` to that source's kept-row count. That is the B1
       invariant holding by construction — assert it in 06-07, do not assume it.

    4. In `test/test_filter_payload_size.py` add the jittered dashboard to the cases it measures,
       so the extra snapshot per aux source is visible and bounded rather than silent.

    5. Measurement, per the index's `jitter()` risk note. Render the largest example in the repo
       twice — once on the pre-06-03 tree, once on this one — and record, in the commit message:
       distinct CDS per figure (expected: unchanged), `len(cb.args["all_graph_sources"])`
       (expected: `+1` per graph with a jittered or dropline layer), the number of snapshot models
       (expected: the same `+1`), and the emitted HTML size in bytes. Explain any number that does
       not match those expectations rather than waving it through.

    Cite TR-01.8, TR-01.15, BR-01.9.
  </action>
  <verify>
    `python3 -m pytest test/test_qualifier_survives_interaction.py test/test_filters.py test/test_linking_filters.py test/test_filter_payload_size.py test/test_jitter.py -q`
    prints no failures. Then revert step (b) only, rerun, and confirm the failure is
    `KeyError` from `dash_render.py:11902`; restore.
  </verify>
  <done>
    A jittered or dropline layer's private source is in `all_graph_sources` with its own snapshot
    taken from the jittered data, so the callback shortens it and the view over it is rebuilt to
    the matching length. The source-count and payload measurements are in the commit message.
  </done>
</task>

<task type="auto" id="06-05">
  <name>Carry the layer's rows into the aggregate config</name>
  <files>dash_render.py, test/test_per_plot_qualifier_computed.py</files>
  <action>
    Failing test first.

    1. Add to `test/test_per_plot_qualifier_computed.py`:
         - `test_agg_config_carries_the_layer_rows`: render `(histogram mpg if foreign==1)` with a
           filter widget; assert the tagged renderer's `_dash_agg_config["has_qual"] is True` and
           `_dash_agg_config["qual_ids"]` equals the qualifier's row ids computed independently in
           the test. Repeat for `kdensity`.
         - `test_an_unqualified_agg_config_is_unrestricted`: `has_qual is False` and
           `qual_ids == []`.
         - `test_agg_config_round_trips_through_json`:
           `json.loads(cb.args["agg_configs_json"])[i]["qual_ids"]` equals the same list, and every
           element is an `int`. Serialization needs no change — `dict(...)` at `:12205-12206`
           shallow-copies and `_row_ids_for` already returns `int` — but assert it rather than
           assuming it.
         - `test_an_emptied_agg_layer_carries_no_config`: a qualifier selecting no rows takes the
           early-out at `:4662-4665` (histogram) or `:4835-4837` / `:4859-4861` (kdensity), which
           return **untagged** renderers, so no `_dash_agg_config` exists and the browser loop
           never touches that source. Assert `not hasattr(r, "_dash_agg_config")`.
       **The trap applies here.** Every assertion about what the layer drew must compare
       `r._dash_agg_source.data["top"]` (or `["y"]` for kdensity) against
       `np.histogram(subsample, bins=r._dash_agg_config["bin_edges"])` computed in the test —
       never `renderer.view.filter.booleans`, which reports a computed layer as fully visible no
       matter what it drew (`test/test_varlist_expansion.py:101`).

    2. Implement. Add a trailing keyword to both mapper signatures — `map_histogram`
       (`:4636-4645`) and `map_kdensity` (`:4806-4815`) — after `color_idx: int = 0` and after any
       `row_mask=` section 03 has already added:

           qual_row_ids: "list[int] | None" = None,

       Document it in each `Args:` block: "Row identities this layer was computed from, or None
       when unrestricted. Carried into `_dash_agg_config` so the browser recompute can intersect."

    3. Write the two keys into the config dicts. In `map_histogram`, inside the literal at
       `:4695-4703`, and in `map_kdensity`, inside the literal at `:4905-4913`, add:

           # The browser recompute reads the PRIMARY snapshot (_FILTER_JS:7097),
           # which holds every row, so a qualified layer opens on the
           # conditional sample and silently becomes the unconditional one on
           # the first widget move.  Same shape as _kpi_callback_config
           # (:11620-11621).  Tri-state: has_qual False is "unrestricted";
           # has_qual True with an empty list blanks the layer, it does not
           # show every row.
           "has_qual":  qual_row_ids is not None,
           "qual_ids":  ([int(r) for r in qual_row_ids]
                         if qual_row_ids is not None else []),

    4. Thread it. In `_add_glyph` (`:10334-10345`) add `qual_row_ids=None` after `color_idx`, and
       forward it **only** in the univariate branch at `:10418-10419`, which already special-cases
       these two mappers:

           if pt in ("histogram", "hist", "kdensity"):
               fn(fig, source, yvar, options, view=view, color_idx=color_idx,
                  qual_row_ids=qual_row_ids)

       Leave the `else` branch at `:10420-10421` and the range branch at `:10412` untouched — no
       other mapper builds an aggregate config.

    5. In `_make_figure_body`, at the `_UNIVARIATE_TYPES` dispatch (`:10033-10037`), compute the
       ids and pass them:

           _agg_ids = None
           try:
               _agg_ids = self._layer_row_ids(source, _plot_view)
           except ValueError as _gexc:
               warnings.warn(
                   f"dash: layer {pi + 1} could not carry its row restriction "
                   f"into the browser recompute ({_gexc}); the aggregate is "
                   f"recomputed from every row.",
                   stacklevel=2,
               )
           self._add_glyph(fig, source_for_plot, ptype, pyvar, pxvar, popts,
                           view=_plot_view, color_idx=pi,
                           qual_row_ids=_agg_ids)

       `_layer_row_ids` answers all five restriction kinds through one channel — per-plot,
       linked graph-level, unlinked graph-level, linked `by()` panel and unlinked `by()` panel —
       which is what discharges the Q7 addition in one code path rather than two.

    Cite TR-01.9, BR-01.9; and DISCOVERY Q7 for the graph-level half.
  </action>
  <verify>
    `python3 -m pytest test/test_per_plot_qualifier_computed.py test/test_statistical_defaults.py test/test_statistical_truth.py test/test_histogram_spurious_bin.py -q`
    prints no failures. Then mutate: delete the `"has_qual"` and `"qual_ids"` keys from `:4695-4703`,
    rerun, and confirm `test_agg_config_carries_the_layer_rows` FAILS with `KeyError`; restore.
  </verify>
  <done>
    `_dash_agg_config` carries `has_qual` / `qual_ids` for both aggregate mappers, the ids reach it
    from `_make_figure_body` through `_add_glyph`, and they survive `dict()` and `json.dumps`
    unchanged. The browser does not read them yet — that is 06-06.
  </done>
</task>

<task type="auto" id="06-06">
  <name>Intersect in the browser-side aggregate recompute</name>
  <files>dash_render.py, test/test_per_plot_qualifier_computed.py</files>
  <action>
    Failing test first.

    1. Add `test_the_agg_loop_uses_the_row_identifier` to
       `test/test_per_plot_qualifier_computed.py`, modelled on
       `test/test_linking_filters.py:346-354`. Slice the shipped source:
       `js = dash_render._FILTER_JS`, `lo = js.index("const agg_configs = JSON.parse")`,
       `hi = js.index("if (ac.type === 'histogram')", lo)`, and assert both
       `dash_render._ROW_ID_COLUMN` (via the in-scope `ROW_ID` identifier, declared at `:7115`)
       and `"qual_ids"` appear in that block. **This test must not be skippable** — it is the
       guard that keeps the section honest on a machine with no `node`, where the tests below skip
       and a skip is not a pass.

    2. Add `test_histogram_qualified_still_correct_after_filter_move` and
       `test_kdensity_qualified_still_correct_after_filter_move`, guarded by
       `@pytest.mark.skipif(shutil.which("node") is None, ...)`. Drive the **shipped** agg branch
       under node exactly as `test/test_linking_filters.py:355-420` drives the mask loop: slice
       the block from `const agg_configs = JSON.parse` to the end of the aggregate loop, stub
       `agg_configs_json` (from `cb.args`), `agg_sources` (plain objects with `data` and
       `change.emit`), `new_data` (the primary snapshot masked by a chosen widget value) and
       `ROW_ID`, write an `.mjs` file, run it, and read the resulting `src.data`. Assert the
       recomputed `top` array equals `np.histogram` of `widget rows ∩ qualifier rows` on
       `ac.bin_edges`, rescaled by `ac.ymode`; and the kdensity twin against `_kde_curve` on the
       same `x_grid`, `kernel` and bandwidth rule. Compare **values**, never booleans.
       At HEAD both fail: the JS reads `new_data[ac.varname]` whole.

    3. Implement. In `_FILTER_JS`, between `:7397` (`const raw_col = new_data[ac.varname];`) and
       `:7399` (`const vals = raw_col.filter(...)`), and after the existing `if (!raw_col) continue;`
       at `:7398`, insert:

           // A layer carrying its own restriction -- a per-plot if/in, a
           // graph-level qualifier, or a by() panel -- is confined to the rows
           // that restriction selects, intersected with the rows the filters
           // kept.  Without this the bars open on the conditional sample and
           // silently become the unconditional one the first time any widget
           // moves.  Same shape as dash_apply_kpis (:7215-7225): the
           // restriction travels as a set of row identities, never as an
           // expression, so there is no evaluator in the browser and nothing
           // to inject into.
           let _agg_col = raw_col;
           if (ac.has_qual) {
               const _qset = new Set(ac.qual_ids || []);
               const _rids = new_data[ROW_ID];
               _agg_col = [];
               if (_rids) {
                   for (let qi = 0; qi < raw_col.length; qi++) {
                       if (_qset.has(_rids[qi])) _agg_col.push(raw_col[qi]);
                   }
               }
           }

       and change `:7399` to read from `_agg_col`:

           const vals = _agg_col.filter(v => v !== null && v !== undefined && !isNaN(v));

       Three properties to preserve, each with a test:
         - **tri-state.** `ac.has_qual === false` leaves `raw_col` untouched;
           `has_qual === true` with `qual_ids: []` yields `vals.length === 0`, which the existing
           zero-rows branch at `:7422-7432` already handles by clearing the bars to zero rather
           than leaving stale ones. Assert that path, do not assume it.
         - **`new_data[ROW_ID]` is present.** `new_data` is built at `:7097-7099` from
           `Object.keys(orig)`, and `orig` is the primary snapshot, which `_make_source` stamps
           with `__dash_row__` at `:8506`. The `if (_rids)` guard covers a spec old enough to
           predate the column, matching the same positional fallback at `:7145-7147`.
         - **no new evaluator.** `qual_ids` are integers from `_row_ids_for`, serialised by
           `json.dumps` at `:11914` and read into a `Set` (project rule 16).

    4. No change is needed at `:11905-11914` or `:12203-12210`; assert that in the test rather
       than editing them.

    Cite TR-01.9, BR-01.9.
  </action>
  <verify>
    `python3 -m pytest test/test_per_plot_qualifier_computed.py -q` prints no failures (and, if
    `node` is absent, `test_the_agg_loop_uses_the_row_identifier` still runs and passes). Then
    mutate: delete the `if (ac.has_qual) { ... }` block from `_FILTER_JS`, rerun, and confirm both
    `*_still_correct_after_filter_move` tests FAIL and `test_the_agg_loop_uses_the_row_identifier`
    FAILS; restore.
  </verify>
  <done>
    The shipped aggregate recompute intersects the widget-kept rows with the layer's own row
    identities, for histogram and kdensity, honouring the tri-state, with the intersection proven
    by running the real JavaScript rather than a transliteration of it.
  </done>
</task>

<task type="auto" id="06-07">
  <name>The graph-level qualifier, the faceted aggregate, and the length invariant</name>
  <files>test/test_qualifier_survives_interaction.py, test/test_per_plot_qualifier_computed.py, test/test_e2e_filters.cscript</files>
  <action>
    This task is the approved Q7 addition plus the invariant that keeps the whole section honest.
    Write each test, confirm it fails for the stated reason, and only then change product code —
    the expectation is that 06-01 through 06-06 already make items (1)-(3) pass, and if any of them
    does not, the gap is in `_layer_row_ids` and is fixed there, not with a special case.

    1. `test/test_per_plot_qualifier_computed.py` — the graph-level half of Q7, both topologies:
         - `test_an_unlinked_graph_level_qualifier_reaches_the_agg_recompute`: a graph carrying
           `if_expr` with no `link()`. `self.sources[name]` is itself the subset, so
           `_layer_row_ids` takes its "source shorter than `self.df`" branch and `has_qual` must be
           True with the subset's ids. Drive the node harness and assert the recomputed bins equal
           `widget rows ∩ graph rows`.
         - `test_a_linked_graph_level_qualifier_reaches_the_agg_recompute`: the same graph inside
           `link(_all)`. The restriction arrives as `_linked_graph_views[name]` (built and
           registered at `:11393-11399`, passed in as `facet_view` at `:11505`), so
           `_layer_row_ids` takes its booleans branch. Same assertion.
         - `test_a_by_panel_aggregate_recomputes_on_its_own_panel`: a `by()` histogram with **no**
           qualifier at all. Before this section the browser recomputed every panel from the full
           frame, so all panels became identical on the first widget move — the browser-side
           sibling of F-A (RESEARCH §1.9). Assert each panel's recomputed `top` equals
           `np.histogram` of `that panel's rows ∩ widget rows`. Run it for both the linked and the
           unlinked `by()` topologies, because they take different `_layer_row_ids` branches.
       Compare source values against an independently computed subsample throughout; never a
       view's booleans.

    2. `test/test_qualifier_survives_interaction.py` — the B1 invariant (RESEARCH §2.3). Add
       `test_every_registered_filter_matches_its_source_length`: build the busiest dashboard the
       suite can express — linked `by()`, a graph-level qualifier, a per-plot qualifier, a jittered
       scatter, a dropline and a histogram, plus two filter widgets — and assert that for every
       `(source, bool_filter, member_ids)` in `dr._view_filters`,
       `len(bool_filter.booleans) == len(source.data[dash_render._ROW_ID_COLUMN])`. Then add
       `test_the_rebuilt_booleans_match_the_shortened_source`: run the shipped per-source loop
       (`:7132-7157`) and view rebuild (`:7164-7171`) under node against that dashboard's real
       snapshots, and assert that for every rebuilt filter `len(booleans)` equals the new row count
       of the source it is over. Pair it with an unconditional Python-side assertion that the
       shipped rebuild at `:7169` sizes `booleans` from `kept`, so the check is not lost when
       `node` is missing.
       *Mutation that must kill it:* in `_FILTER_JS`, change `:7169` to
       `vf.filter.booleans = vf.filter.booleans` — the stale-length hazard B1 measured.

    3. `test/test_e2e_filters.cscript` — one end-to-end case through real Stata (DISCOVERY Q10):
       build a dashboard with a per-plot-qualified `histogram` and a filter widget, then assert the
       emitted HTML's `agg_configs_json` carries a non-empty `qual_ids`. Set `$dash_nobrowser`
       before the run. Run the cert suite with `arch -arm64` from `test/`; a skipped cscript is
       not a pass.

    4. Close out the section. Run both suites in full against the baseline section 01 recorded.
       Then report — do **not** run — the merge command, per project rule 6:
       `git checkout main && git merge --no-ff feature/batch4-interactive-layer`.
       Commit messages carry no AI references (rule 7).

    Cite BR-01.8, BR-01.9, TR-01.7, TR-01.9; and DISCOVERY Q7 as the approved
    task-beyond-requirement VALIDATE must see.
  </action>
  <verify>
    `python3 -m pytest test/ -q -m 'not serve'` prints no failures and no new skips against the
    baseline in `.ultraplan/BASELINE.md`. Then
    `cd /Users/billy/Desktop/Programs/StataPrograms/d/dash/test && arch -arm64 /usr/local/bin/stata-mp -b do run_all_cscripts.do`
    and `grep -ci "error\|r([0-9]" run_all_cscripts.log` prints `0`; confirm no cscript reported a
    skip. Then apply the `:7169` mutation above, rerun
    `python3 -m pytest test/test_qualifier_survives_interaction.py -q`, and confirm
    `test_the_rebuilt_booleans_match_the_shortened_source` FAILS; restore.
  </verify>
  <done>
    A row restriction of any of the five kinds — per-plot, linked and unlinked graph-level, linked
    and unlinked `by()` panel — reaches the browser-side aggregate recompute through one code path;
    the render-time and rebuilt `BooleanFilter` lengths are pinned against B1; one `.cscript`
    proves the path through real Stata; both suites are green against the section-01 baseline and
    the merge command is reported, not run.
  </done>
</task>
