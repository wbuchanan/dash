# Section 05: Marker labels and colour range

## Overview

A per-plot `if`/`in` currently reaches the glyph and nothing else. `mlabel(make)` on
`(scatter mpg weight if foreign==1, mlabel(make))` draws 74 labels over 22 points, and
`colorvar(price)` colours those 22 points against the price range of all 74. This section
makes both marks obey the same row set as the glyph, discharging work item 8 (TR-01.5,
BR-01.5) and US-A3.

Two mechanisms, both forced by measurement rather than chosen. `LabelSet` is a
`DataAnnotation`; it declares exactly one property (`source`) and has no `view`, so it can
never be filtered. It is replaced by `figure.text(...)`, a real `GlyphRenderer` that accepts
`view=`, is not a `ConnectedXYGlyph`, and carries identical visual defaults. And a
`LinearColorMapper` that auto-ranges ignores the view, while `linear_cmap` cannot auto-range
at all; `domain=[(renderer, column)]` is the only measured mechanism that follows a `CDSView`,
which forces the mapper to be built after the renderer exists.

Changing which Bokeh model carries labels moves them out of `fig.center` and into
`fig.renderers`, where three pieces of existing logic will pick them up. That, plus 21 existing
`mlabel` assertions written against `LabelSet`, is where a real regression can hide.

**Ordering:** this section uses a **section-leading failing-test task**. Task 05-01 writes
every new assertion and confirms each fails for the right reason; 05-02 re-baselines the
existing assertions onto a model-agnostic accessor *before* the model changes, so the tree is
never red for a mechanical reason; 05-03 through 05-05 turn 05-01's tests green in order.

## Risk: [yellow] — swapping the Bokeh model that carries marker labels re-baselines 21 existing assertions and exposes labels to three `fig.renderers` consumers that never saw them before

## Dependencies
- Depends on: section-01, section-02
- Blocks: section-06
- Parallel batch: 3

## Evidence

### E1 — `LabelSet` cannot be filtered at all (RESEARCH §2.6, supersedes the original item-8 decision)

The phase document (TR-01.5) and DISCOVERY Q15 both say *mask the `LabelSet`*. RESEARCH §4.2
supersedes that. **Plan the new decision, not the superseded one.** The measurement:

```
LabelSet has a 'view' property:  False
DataAnnotation's own properties: ['source']
LabelSet(view=...) -> AttributeError: unexpected attribute 'view' to LabelSet
```

No annotation inherits a view. A `LabelSet` over a 10-row source drew all ten strings.

> **`figure.text(...)` is a real `GlyphRenderer`, accepts `view=`, is not a `ConnectedXYGlyph`,
> and was measured to filter correctly** — it drew exactly `P0, P2, P4, P6, P8` for a view
> keeping `[0,2,4,6,8]`, while keeping the shared source and linked selection. And **if the
> layer already has a NaN column, a `text` glyph plotted against it subsets itself for free.**
> — RESEARCH §2.6

Re-confirmed read-only against the installed bokeh 3.9.0 for this section:

```
type: GlyphRenderer | in fig.renderers: True | in fig.center: False
glyph: Text | ConnectedXYGlyph: False
view filter booleans: [True, False, True, False, True] | name: _dash_mlabel
validation issues: ValidationIssues(error=[], warning=[])
```

So the swap satisfies BR-01.7 by construction: a `Text` glyph is not a `ConnectedXYGlyph`,
so no E-1024 `CDSVIEW_FILTERS_WITH_CONNECTED` can arise from the label renderer.

**Visual defaults are identical**, measured property by property on bokeh 3.9.0 — this is why
the swap is not a cosmetic change:

| property | `LabelSet` default | `Text` default |
|---|---|---|
| `text_align` | `'left'` | `'left'` |
| `text_baseline` | `'bottom'` | `'bottom'` |
| `text_font_size` | `value('16px')` | `value('16px')` |
| `text_font` | `value('helvetica')` | `value('helvetica')` |
| `text_color` | `'#444444'` | `'#444444'` |
| `text_alpha` | `1.0` | `1.0` |
| `x_offset` / `y_offset` | `0` / `0` | `0` / `0` |
| `angle` | `0` | `0` |

Every keyword `_apply_mlabel_opts` builds today (`dash_render.py:3345-3353`: `x`, `y`, `text`,
`source`, `text_font_size`, `x_offset`, `y_offset`, plus optional `text_color`) exists on
`Text`. Nothing dash sets is `LabelSet`-only.

### E2 — Stata's own answer (RESEARCH §3.5, decision Q15 confirmed)

> `(scatter mpg weight if foreign==1, mlabel(make))`: serset N 74 → **22**, non-blank `make`
> 74 → **22**. The label column is carried into the serset already subset; there is no separate
> filtering step.

That is the acceptance number for BR-01.5: **22 labels, not 74.**

### E3 — the call sites: the phase document says nine, HEAD has thirteen

`_apply_mlabel_opts` is defined at `dash_render.py:3301` and is a method of `GlyphMapper`
(class at `:2474`). TR-01.5 lists nine call sites. `grep -n "_apply_mlabel_opts" dash_render.py`
at HEAD returns **thirteen**, each in a distinct mapper:

| line | owning mapper (`def` line) | source handed to `_apply_mlabel_opts` | positionally valid against the shared source? |
|---|---|---|---|
| 3482 | `map_scatter` (3407) | `plot_source` (jitter copy) | yes — `_build_jitter_source` copies all columns, same rows, same order (RESEARCH §1.4); and when `view is not None`, `clean_source = source` (`:3441-3443`) |
| 3556 | `map_line` (3486) | `sorted_source` | **no** — `dropna(...).sort_values(xvar)` at `:3526` |
| 3589 | `map_connected` (3560) | `source` | yes |
| 3657 | `map_area` (3592) | `source` | yes — **and this is the site the brief names**: the area glyph draws from `area_source` (`:3630`) while the labels come from the unmasked shared source |
| 3762 | `map_bar` (3660) | `source` | yes |
| 3814 | `map_spike` (3765) | `source` | yes |
| 4955 | `map_rarea` (4920) | `source` | yes |
| 5000 | `map_rbar` (4958) | `source` | yes |
| 5038 | `map_rspike` (5003) | `source` | yes |
| 5103 | `map_rcap` (5041) | `source` | yes |
| 5144 | `map_rline` (5106) | `source` | yes |
| 5288 | `map_dropline` (5211) | `dl_source` | **no** — built from `x_arr[mask]` etc. at `:5239-5259` |
| 5367 | `map_rcapsym` (5291) | `source` | yes |

The four sites TR-01.5 omits — 5103 `map_rcap`, 5144 `map_rline`, 5288 `map_dropline`,
5367 `map_rcapsym` — exist at HEAD and are in scope here. All thirteen mappers already accept
`view=None` in their signatures, so the restriction is in scope at every call site with no
signature change.

There is a **fourteenth** `LabelSet` in `GlyphMapper`, at `dash_render.py:5456-5464`, inside
`map_scatteri`. It is **out of scope for the mask**: RESEARCH §3.4 measured that Stata
validates a qualifier on `scatteri`/`pci`/`function` and then discards it byte-identically, and
section 07 owns the validate-then-warn treatment. It is **in scope for the test accessor** —
after the swap the suite must still find it, and it will still be a `LabelSet`.

The eight emitted-app `LabelSet` sites (`dash_render.py:14454, 14484, 14502, 14532, 14552,
14585, 14655, 14925`, plus the import at `:12881`) are **TR-01.13 and out of scope** — they are
string literals inside `ServerAppBuilder` (class at `:12265`), and the server implementation is
deferred (PRD §7). Section 09 owns the failing parity test for server divergence; this section
must not leave `test_mode_parity.py` silently passing on two empty lists (see E5).

### E4 — colour range (RESEARCH §2.7, refined by §4.3)

| mapper | measured metrics | verdict |
|---|---|---|
| `LinearColorMapper()` auto | `0 → 9` | **ignores the view — full column** |
| **`domain=[(renderer,"c")]`** | **`0 → 4`** | **respects the view ✓** |
| explicit `low`/`high` | `0 → 4` | hand-computed |

> **`linear_cmap` can never auto-range** — `low` and `high` are *required positional*
> arguments. Only `LinearColorMapper(palette=...)` auto-ranges, and only `domain` follows a
> view. `ColorBar` has no range of its own, so fixing the mapper fixes the bar.

Confirmed read-only on bokeh 3.9.0:

```
LinearColorMapper has domain: True
domain descriptor: List(Tuple(Instance(GlyphRenderer), Either(String, List(String))))
domain.__doc__: "A collection of glyph renderers to pool data from for establishing
                 data metrics. If empty, mapped data will be used instead."
low.__doc__:    "... If ``None``, the value is inferred from data."
```

The current code is *not* auto-ranging — `dash_render.py:3249-3256` hand-computes over the
**whole** column and passes both bounds:

```python
 3249            lo = float(np.nanmin(col_vals))
 3250            hi = float(np.nanmax(col_vals))
 3251            if lo == hi:
 3252                hi = lo + 1.0
 3253            pal_name = self._PALETTE_MAP.get(palette_key or "viridis", "Viridis256")
 3254            palette  = getattr(_bk_palettes, pal_name, _bk_palettes.Viridis256)
 3255            mapper   = LinearColorMapper(palette=palette, low=lo, high=hi,
 3256                                         nan_color=missing_color)
```

`col_vals` comes from `source.data[varname]` (`:3031`, `:3097-3102`) — the unmasked source.
Because `low`/`high` are set, `domain` would be ignored: **both bounds must be left unset for
`domain` to take effect.** `_apply_colorvar` has exactly one call site,
`dash_render.py:3480` in `map_scatter`, and it is already passed the renderer `r`, so the
"mapper after renderer" ordering requirement costs nothing.

`ColorBar(color_mapper=mapper, ...)` is built at `:3266-3270` from the same mapper object, so
fixing the mapper fixes the bar with no second change.

### E5 — what the model swap touches that nothing else in this phase touches

`fig.add_layout(LabelSet(...))` puts the annotation in `fig.center`. `fig.text(...)` appends a
`GlyphRenderer` to `fig.renderers`. Three pieces of live logic read `fig.renderers` and will
see the label renderer for the first time:

1. **`dash_render.py:10066-10091`.** `_layer_renderers = list(fig.renderers[_r_before:])` feeds
   `self._layer_drew_anything(_layer_renderers)` (`:10084`, helper at `:10308-10331`). The
   helper returns `True` as soon as any renderer's source carries a value — so a layer that
   drew no glyph but did draw labels would stop emitting the
   `"drew nothing from N observations"` warning. That warning is section 07's surface; silently
   suppressing it here would be a cross-section regression.
2. **`dash_render.py:10117-10126`.** `_primary_renderers = [r for r in fig.renderers if ...
   r.data_source is source]` is assigned to `fig.x_range.renderers` / `fig.y_range.renderers`
   when they are `DataRange1d`. Ten of the thirteen call sites hand `_apply_mlabel_opts` the
   shared `source`, so their label renderers would join the auto-range pool. For `map_area`
   this is not a no-op: the area glyph draws from its own `area_source` (`:3630`), so on an
   area-only figure the label renderer would become the *only* primary renderer and would
   dictate the axis ranges.
3. **`dash_render.py:9000-9028`** (`_rebuild_legend`). The item loop bundles every renderer of
   a layer into one `LegendItem`, filtering only names starting with `_clegend_` (`:9002-9006`).
   An unexcluded label renderer would join its series' legend key, so a legend click would hide
   the labels — behaviour `LabelSet` never had.

`_rebuild_legend`'s `_clegend_` filter and the constant `_COLORVAR_LEGEND_NAME = "_dash_clegend"`
(`dash_render.py:595`) are the existing precedent for a name-tag exclusion. Follow it.

Finally, `test/test_mode_parity.py:159-176` (`_annotations`) classifies `LabelSet`, `Label` and
`Span` and compares standalone against served. Its own docstring records that it exists because
"the served marker labels could use a second size table, a different default font and different
offsets (measured: 14px at (5, 5) against the renderer's 15px at (4, 0))". After the swap the
standalone side has no `LabelSet` and the served side still does, so without work this
comparison either fails for the wrong reason or degenerates. It must normalise a
`Text`-glyph marker label into the same dict shape.

### E6 — the trap that governs every assertion here

> Existing coverage is scatter-only and **structurally cannot catch this class of bug**:
> `test/test_varlist_expansion.py:101`'s `_visible_count` helper reads
> `renderer.view.filter.booleans`, which reports a *computed* layer as fully visible no matter
> what it drew. **Assertions on computed layers must compare the layer's own source values
> against an independently computed subsample**, never a view's booleans.

For this section the trap has a specific edge: the label renderer's `view` **is** the
mechanism, so asserting on `renderer.view.filter.booleans` would be asserting that the code did
what the code did. Every assertion in this section must therefore **materialise the strings the
renderer would draw** — resolve the renderer's view against its own `data_source`, index the
text column, and compare the resulting list of strings to a list computed independently from
the DataFrame. Never assert a count of `True` values.

### E7 — data available to the Python tests

`test/fixtures/data/auto.csv` is 74 rows but carries **only `mpg` and `weight`** — no `foreign`,
no `make`. `conftest.py`'s `auto_df` fixture (`:106-122`) is **synthetic**: `foreign` is
`np.random.choice([0, 1], 74)` under seed 42, so its foreign count is not 22. **No Python test
in this section may claim to read Stata's `auto.dta`.** Build the 74/22 split explicitly in the
test module — 74 rows, exactly 22 with `foreign == 1`, labels `m0..m73` — so the shape is
Stata-grounded (E2) without fabricating values dash never had. The regression doubles live in
section 01's `test/fixtures/stat_truth_qualifier.json` and are not needed here; this section
asserts row membership, not coefficients.

## TDD test stubs

All new assertions live in **`test/test_per_plot_qualifier_marks.py`** (new module) unless
stated otherwise.

- **Test:** a `scatter` with `mlabel(make)` and a per-plot `if foreign==1` over a 74-row frame
  with 22 foreign rows draws **22** label strings, and the 22 strings equal the `make` values of
  the 22 foreign rows in frame order. *Fails before:* the `LabelSet` carries all 74.
  *Mutation that must kill it:* pass `view=None` at `dash_render.py:3482` — the test must go red
  on the values, not just the count.
- **Test:** the same layer's scatter glyph still draws all 74 rows when the qualifier is on a
  *sibling* layer and not on the scatter (BR-01.3). *Fails before:* n/a — this is the
  control that stops the fix over-restricting. *Mutation:* apply the mask unconditionally in
  `_apply_mlabel_opts`; the control must go red.
- **Test:** `map_area` with `mlabel` and a qualifier draws labels for the kept rows only.
  *Fails before:* `dash_render.py:3657` hands the unmasked shared `source`.
  *Mutation:* revert `:3657` to `view=None`.
- **Test:** `map_line` with `mlabel` and a qualifier draws labels for the kept rows only, in the
  sorted order the line uses, and no label sits on a row the line does not draw.
  *Fails before:* `sorted_source` is built by `dropna().sort_values()` at `:3526`, so any mask
  indexed against the shared source is positionally wrong. *Mutation:* drop the
  keep-column from `_cols` at `:3521-3524`; the ordering assertion must go red, not just the
  count — a count-only assertion survives a wrong-rows bug here.
- **Test:** `map_dropline` with `mlabel` and a qualifier draws labels for the kept rows only.
  *Fails before:* `dl_source` (`:5250-5260`) is NaN-masked and positionally reindexed.
- **Test:** the marker-label renderer is a `GlyphRenderer` whose `glyph` is a `Text`, it is in
  `fig.renderers` and not in `fig.center`, and `bokeh.core.validation.check_integrity([fig])`
  reports **zero** errors — no E-1024 (BR-01.7).
- **Test:** the label renderer is excluded from `fig.x_range.renderers` / `fig.y_range.renderers`
  on an `area`-with-`mlabel` figure, and the figure's `y_range.renderers` is unchanged from the
  same figure built without `mlabel`. *Fails before:* n/a on the pre-swap tree — this test is
  written in 05-01 and is expected to be **green before 05-03 and to catch 05-03's regression if
  the exclusion is forgotten**; state that in the module docstring so a reader does not mistake
  it for a no-op.
- **Test:** a layer that draws no glyph but does carry `mlabel` still emits the
  `"drew nothing from N observations"` warning (`dash_render.py:10084-10092`).
  *Mutation:* remove the name-tag filter from `_layer_drew_anything`'s input; the warning
  disappears and the test must go red.
- **Test:** a `mlabel` label renderer does not appear in any `LegendItem.renderers`
  (`_rebuild_legend`, `dash_render.py:9000-9028`).
- **Test:** `colorvar(price)` on a qualified scatter produces a `LinearColorMapper` whose `low`
  and `high` are both `None` and whose `domain` is `[(renderer, "price")]` with `renderer` being
  the scatter renderer the figure actually holds. *Fails before:* `:3255` passes
  `low=lo, high=hi` computed over the whole column.
  *Mutation:* set `domain=[]`; the test must go red.
- **Test:** the degenerate branch — when the qualified subset has a single distinct colorvar
  value, the mapper falls back to explicit bounds and those bounds are the **subset's**
  min/max (+1.0 spread), not the full column's. *Fails before:* the `lo == hi` guard at
  `:3251-3252` is computed over the full column. *Mutation:* compute the fallback from
  `col_vals` instead of the masked values; the test must go red.
- **Test:** the `ColorBar` added at `:3266-3270` references the same mapper object, so no second
  range exists to fix. *Mutation:* construct a second `LinearColorMapper` for the bar.
- **Test (existing file, `test/test_mode_parity.py`):** `_annotations` returns a record of
  `kind == "LabelSet"` for a standalone marker label after the swap, with the same `font`,
  `color`, `x_offset` and `y_offset` keys it returns today, so the standalone-vs-served
  comparison stays a real comparison. *Mutation that must kill it:* make `_annotations` return
  `[]` for both sides; the parity assertion must not pass.
- **Test (existing file, `test/test_varlist_expansion.py`):** `test_scatteri_labels_attach_to_
  their_own_points` (`:383`) still passes — `map_scatteri`'s `LabelSet` at `:5456-5464` is
  deliberately not swapped, and the accessor must still find it.

## Tasks

<task type="auto" id="05-01">
  <name>Write the failing tests for masked marker labels and a view-following colour range</name>
  <files>test/test_per_plot_qualifier_marks.py (new)</files>
  <action>
    Create `test/test_per_plot_qualifier_marks.py`. It is the only new file in this task; do not
    touch any other test module or any product file.

    1. Module docstring: state that this module pins work item 8 / TR-01.5 / BR-01.5 and
       US-A3, that the acceptance number comes from Stata (RESEARCH §3.5: `(scatter mpg weight
       if foreign==1, mlabel(make))` takes the serset from 74 to 22 non-blank `make` values),
       and that **no assertion in this file may read `renderer.view.filter.booleans`** — every
       assertion materialises the strings the renderer would draw and compares them to a list
       computed independently from the DataFrame.
    2. Add a module-level fixture `qualified_df()` building a 74-row `pandas.DataFrame` with
       columns `mpg`, `weight`, `price`, `foreign`, `make`, where exactly 22 rows have
       `foreign == 1.0` and `make` is `[f"m{i}" for i in range(74)]`. Do **not** read
       `test/fixtures/data/auto.csv` (it has only `mpg` and `weight`) and do **not** use the
       `auto_df` conftest fixture (`test/conftest.py:106-122`, synthetic `foreign`). Put a
       comment saying exactly that, citing both line ranges.
    3. Add a helper `drawn_label_texts(fig)` that: finds every marker-label carrier on `fig`
       (a `bokeh.models.LabelSet` in any of `fig.center/above/below/left/right`, **and** any
       `GlyphRenderer` in `fig.renderers` whose `glyph` is a `bokeh.models.Text`); resolves the
       text column name (`ls.text` for a `LabelSet`; for a `Text` glyph, `r.glyph.text` which is
       a field spec — take `["field"]` when it is a dict, else the string); resolves the view by
       calling `r.view.filter.compute_indices(r.data_source)` when a view with a non-`AllIndices`
       filter is present, else `range(len(column))`; and returns the **list of strings** at those
       positions. It returns values, never counts.
    4. Write the tests listed in the "TDD test stubs" section above, one test function each,
       each with a docstring naming the BR/TR id it pins and the mutation that must kill it.
       Build figures through `GlyphMapper` directly (`from dash_render import GlyphMapper`,
       mirroring `test/test_glyphs.py:823-830`) for the per-mapper tests, and through the
       `make_dr` helper in `test/conftest.py:246` for the `_make_figure_body`-level tests
       (per-plot qualifier, range-renderer exclusion, legend exclusion, `drew nothing` warning).
    5. For each per-mapper test, compute the expected mask in the test as
       `df["foreign"] == 1.0`, derive `expected = [m for m, k in zip(df["make"], mask) if k]`,
       and assert `drawn_label_texts(fig) == expected` — an equality on the list of strings, in
       order. A `len(...) == 22` assertion alone is forbidden: it survives a wrong-rows bug,
       which is exactly the `map_line` sorted-source failure mode.
    6. For the colour tests, locate the scatter `GlyphRenderer` on the figure, find the
       `LinearColorMapper` through `renderer.glyph.fill_color["transform"]`, and assert
       `mapper.low is None`, `mapper.high is None`, and
       `[(r, c) for r, c in mapper.domain] == [(scatter_renderer, "price")]`. For the degenerate
       test, use a frame whose 22 qualified rows all share one `price` value and assert the
       fallback bounds are that value and that value + 1.0.
    7. Do not mark anything `xfail`. These tests are expected to be red until 05-05.
  </action>
  <verify>
    `python3 -m pytest test/test_per_plot_qualifier_marks.py -q` — red. Then read the failure
    text and confirm each failure is the *right* failure: the label tests must fail on a
    **74-vs-22 list inequality** (or on the `map_line` ordering), not on an import error, a
    missing fixture, or an `AttributeError`. The colour test must fail on
    `mapper.low is None` being `False` with `mapper.low` equal to the full column's min, not on
    `domain` being missing. Record the exact failure line of each test in the commit message.
    `grep -c "view.filter.booleans" test/test_per_plot_qualifier_marks.py` prints `0`.
  </verify>
  <done>
    A new test module exists whose every assertion compares drawn label strings or mapper bounds
    against independently computed values. Every test in it fails, and each failure has been read
    and confirmed to be the defect this section fixes rather than a test-construction error. No
    product file has changed.
  </done>
</task>

<task type="auto" id="05-02">
  <name>Re-baseline every existing marker-label assertion onto a model-agnostic accessor</name>
  <files>test/conftest.py, test/test_glyphs.py, test/test_varlist_expansion.py, test/test_dates.py, test/test_axis_options.py, test/test_dropline_marker_options.py, test/test_mode_parity.py</files>
  <action>
    This task deliberately touches seven files instead of the usual one to three. It is still one
    commit: every edit is the same mechanical substitution, it runs **before** the model changes
    so the tree is green at every point inside it, and splitting it across the 05-03 boundary
    would leave the suite red for a purely mechanical reason, which project rule 5 forbids. Do
    not change any product file in this task.

    1. In `test/conftest.py`, add a module-level function (not a fixture, so it can be imported
       from any test module):

       ```python
       def marker_label_specs(fig):
           """Every marker-label carrier on *fig*, normalised across Bokeh models.

           dash drew marker labels as a LabelSet annotation and now draws them as a
           `figure.text(...)` GlyphRenderer, because LabelSet has no `view` property in
           Bokeh 3.9 and therefore cannot honour a per-plot qualifier.  Both models are
           recognised here: map_scatteri still uses a LabelSet, and so does the emitted
           server app.
           """
       ```

       It returns a list of dicts with the keys `kind` (always `"LabelSet"`, so the parity
       harness's existing shape is preserved), `model` (`"LabelSet"` or `"Text"`), `obj`,
       `source`, `text` (the *column name*, normalised out of a `Text` glyph's field spec),
       `font` (`text_font_size`), `color` (`text_color`), `x_offset`, `y_offset`, and `texts`
       (the list of strings the carrier would draw, resolved through its view exactly as
       `drawn_label_texts` in 05-01 does). Scan `fig.center`, `fig.above`, `fig.below`,
       `fig.left`, `fig.right` for `LabelSet` instances and `fig.renderers` for
       `GlyphRenderer`s whose `glyph` is a `Text`.
    2. `test/test_glyphs.py`: rewrite `_get_labelsets(fig)` (`:814-817`) to
       `return marker_label_specs(fig)` and re-point all 21 tests in `TestMlabelOption`
       (`:820-895`), `TestMlabelOnNonScatter` (`:898-1015`) and `test_mlabwidth_label_still_
       created` (`:1796-1803`) at the returned dicts: `label_sets[0].text_color` becomes
       `specs[0]["color"]`, `.text_font_size` becomes `["font"]`, `.x_offset`/`.y_offset` become
       `["x_offset"]`/`["y_offset"]`, and `.text` becomes `["text"]`. Delete the now-unused
       local `from bokeh.models import LabelSet` imports inside those test bodies. Keep every
       assertion's *meaning* byte-for-byte; this task changes how the object is found, never
       what is asserted about it.
    3. `test/test_varlist_expansion.py`: rewrite `_all_label_sets(fig)` (`:121-126`) to delegate
       to `marker_label_specs` and return the dicts, and update its one consumer,
       `test_scatteri_labels_attach_to_their_own_points` (`:383-396`). Leave `_visible_count`
       (`:101-118`) alone — it is not a marker-label helper, and E6 forbids using it here.
    4. `test/test_dates.py:732-762`, `test/test_axis_options.py:678-682` and `:892-901`,
       `test/test_dropline_marker_options.py:95-105`: replace each inline
       `[r for r in fig.center if isinstance(r, LabelSet)]` with `marker_label_specs(fig)` and
       adjust the attribute reads the same way. In `test_dropline_marker_options.py`,
       `labels[0].text == "make"` becomes `specs[0]["text"] == "make"`, and the negative control
       at `:103-105` becomes `assert not marker_label_specs(fig)`. Remove the now-unused
       `LabelSet` import at `:29`.
    5. `test/test_mode_parity.py`: in `_annotations` (`:150-176`), replace the `isinstance(r,
       LabelSet)` branch with a call to `marker_label_specs(fig)` that emits the same
       `{"kind": "LabelSet", "text", "font", "color", "x_offset", "y_offset"}` dicts for both
       models, then keep the existing `Label` and `Span` branches as they are. Add a comment
       recording that the served side still emits a real `LabelSet` (`dash_render.py:14454`
       and seven siblings, TR-01.13, deferred) while the standalone side will emit a `Text`
       glyph after 05-03, and that normalising here is what keeps this a comparison of fonts,
       colours and offsets rather than a comparison of two empty lists.
  </action>
  <verify>
    `python3 -m pytest test/test_glyphs.py test/test_varlist_expansion.py test/test_dates.py
    test/test_axis_options.py test/test_dropline_marker_options.py test/test_mode_parity.py -q`
    — all pass, on the **unswapped** tree, with the same number of passed tests as before this
    task. Then prove the accessor is not vacuous: temporarily comment out
    `fig.add_layout(ls)` at `dash_render.py:3401`, re-run the same command, and confirm at least
    one test in **each** of the six files goes red. Restore `:3401` and confirm green again.
    `grep -rn "isinstance(r, LabelSet)" test/*.py` returns only `test/conftest.py`'s own
    accessor.
  </verify>
  <done>
    One function in `test/conftest.py` is the single place the suite knows how marker labels are
    carried. Every pre-existing `mlabel` assertion goes through it, asserts exactly what it
    asserted before, and has been shown by mutation to still be able to fail. The product tree is
    untouched and the suite is green.
  </done>
</task>

<task type="auto" id="05-03">
  <name>Replace the mlabel LabelSet with a filterable text glyph and exclude it from the three renderer consumers</name>
  <files>dash_render.py</files>
  <action>
    1. Next to `_COLORVAR_LEGEND_NAME` at `dash_render.py:595`, add:

       ```python
       # Marks the GlyphRenderer that carries mlabel() text.  Labels moved off
       # LabelSet because a DataAnnotation declares exactly one property --
       # `source` -- and has no `view`, so a per-plot qualifier could never
       # reach them.  A `text` glyph is a real GlyphRenderer, takes view=, and
       # is not a ConnectedXYGlyph, so no E-1024 arises from it.  The name is
       # what keeps it out of the legend, the auto-range pool and the
       # "drew nothing" check, exactly as _clegend_ does for colour swatches.
       _MLABEL_GLYPH_NAME = "_dash_mlabel"
       ```
    2. In `_apply_mlabel_opts` (`:3301-3401`): change the signature to
       `(self, fig, source, options, xvar, yvar, view=None, keep=None)` and the return
       annotation to `"GlyphRenderer | None"`. Document `keep` precisely: *a list of booleans
       positional in the space of the `source` argument*, used when `source` is a private,
       positionally reindexed copy for which the shared-source `view` is invalid. It is not
       section 02's `row_mask`, which is positional in the shared source's space; the two
       coincide only when `source` is the shared source. Update the docstring's own summary
       lines at `:3309` and `:3312` in the same edit — both say the method *adds a Bokeh
       ``LabelSet``*, which stops being true in step 5 and is what would otherwise leave a
       stale `LabelSet` mention behind for this task's verification grep to trip over.
    3. Replace `:3321`'s `from bokeh.models import LabelSet` with
       `from bokeh.models import BooleanFilter, CDSView`.
    4. Leave `:3323-3398` — the `mlabel`/`mlabcolor`/`mlabsize`/`mlabposition`/`mlabgap`/
       `mlabwidth` handling and the derived `__mlabel__` text column — **unchanged**. Every
       keyword it builds exists on `Text` with the same default (see Evidence E1), so nothing in
       that block needs adjusting.
    5. Replace `:3400-3401`:

       ```python
       ls = LabelSet(**kwargs)
       fig.add_layout(ls)
       ```

       with: resolve an effective view — if `keep` is not None, build
       `CDSView(filter=BooleanFilter(booleans=[bool(k) for k in keep]))` after asserting
       `len(keep)` equals the source's row count; else use `view` when it is not None **and**
       its filter's `booleans` length matches the source's row count; else no view. On a length
       mismatch, `warnings.warn` naming `mlabel`, the source length and the mask length, and
       draw the labels unrestricted — the "never lose the mark" contract of BR-01.12. Then:

       ```python
       kwargs["name"] = _MLABEL_GLYPH_NAME
       if _eff_view is not None:
           kwargs["view"] = _eff_view
       r = fig.text(**kwargs)
       return r
       ```

       `fig.text` was confirmed on bokeh 3.9.0 to return a `GlyphRenderer` whose glyph is a
       `Text`, to land in `fig.renderers` (not `fig.center`), to accept `view=`, and to leave
       `bokeh.core.validation.check_integrity([fig])` with zero errors.
    6. Do **not** change any of the thirteen call sites yet — they keep calling with no `view`
       and no `keep`, so this task changes the model and nothing else. Threading is 05-04.
    7. Exclude the new renderer from the three consumers identified in Evidence E5:
       - `:10066` — filter the slice:
         `_layer_renderers = [r for r in fig.renderers[_r_before:] if str(getattr(r, "name", "") or "") != _MLABEL_GLYPH_NAME]`,
         so `_layer_drew_anything` at `:10084` keeps its meaning and section 07's
         "drew nothing" warning is not suppressed by a label.
       - `:10117-10120` — add `and str(getattr(r, "name", "") or "") != _MLABEL_GLYPH_NAME` to
         the `_primary_renderers` comprehension, so a label renderer never enters
         `fig.x_range.renderers` / `fig.y_range.renderers`. This is not cosmetic: on an
         `area`-with-`mlabel` figure the area glyph draws from `area_source` (`:3630`), so
         without this the label renderer would become the only primary renderer.
       - `:9002-9006` — extend `_rebuild_legend`'s existing `_clegend_` filter to also drop
         `name == _MLABEL_GLYPH_NAME`, preserving today's behaviour that labels do not hide with
         their series' legend key.
    8. Leave `map_scatteri`'s `LabelSet` at `:5456-5464` alone. RESEARCH §3.4 measured that
       Stata evaluates and then discards a qualifier on `scatteri`; section 07 owns that
       treatment.
  </action>
  <verify>
    `python3 -m pytest test/test_glyphs.py test/test_varlist_expansion.py test/test_dates.py
    test/test_axis_options.py test/test_dropline_marker_options.py test/test_mode_parity.py -q`
    — all pass, unchanged from 05-02, because the accessor already handles both models.
    `python3 -m pytest test/test_per_plot_qualifier_marks.py -q -k "text_glyph or validation or
    range_renderers or legend or drew_nothing"` — the model/validation/exclusion tests now pass;
    the masking tests are still red (05-04 turns them green).
    `grep -n "ls = LabelSet" dash_render.py` returns nothing — no `LabelSet` is constructed
    in `_apply_mlabel_opts` any more. `grep -n "LabelSet" dash_render.py | grep -v '"'` then
    prints exactly two lines, both inside `map_scatteri` (`from bokeh.models import LabelSet`
    and `fig.add_layout(LabelSet(` — `:5456` and `:5460` at HEAD, shifted down by however many
    lines step 1 adds at `:595`). Any third line means a docstring or comment still advertises
    the old model; fix the prose rather than the grep.
    `python3 -c "import dash_render, bokeh.core.validation as V; ..."` rendering one
    `scatter ... mlabel` figure prints `ValidationIssues(error=[], warning=[])`.
  </verify>
  <done>
    Marker labels are carried by a named `Text` `GlyphRenderer` that accepts a view, the emitted
    document has no new validation error, and the three pieces of logic that read `fig.renderers`
    ignore the label renderer by name. No mask is applied yet; the suite is green except for
    05-01's masking assertions.
  </done>
</task>

<task type="auto" id="05-04">
  <name>Thread the layer's restriction to all thirteen mlabel call sites, including the three private sources and map_area</name>
  <files>dash_render.py</files>
  <action>
    1. Ten call sites hand `_apply_mlabel_opts` the shared `source`, for which the layer's own
       `view` is positionally valid. Add `view=view` to each:
       `:3589` (`map_connected`), **`:3657` (`map_area`)**, `:3762` (`map_bar`),
       `:3814` (`map_spike`), `:4955` (`map_rarea`), `:5000` (`map_rbar`), `:5038`
       (`map_rspike`), `:5103` (`map_rcap`), `:5144` (`map_rline`), `:5367` (`map_rcapsym`).
       `:3657` is the site the section brief names explicitly: `map_area` draws its glyph from
       `area_source` (`:3630`) and its labels from the unmasked shared `source`.
    2. `:3482` (`map_scatter`) hands `plot_source`. `_build_jitter_source` (`:2521`, copying all
       columns at `:2559-2562`) preserves row count and order, and when `view is not None`
       `clean_source = source` (`:3441-3443`), so the shared view is positionally valid. Add
       `view=view`. `_apply_mlabel_opts`'s own length check (05-03 step 5) is the guard if that
       ever stops holding; do not add a second one.
    3. `:3556` (`map_line`) hands `sorted_source`, built at `:3521-3527` by
       `dropna(subset=[xvar, yvar]).sort_values(xvar)`. A mask indexed against the shared source
       selects the **wrong rows** there (RESEARCH §1.3, D1). Carry the keep flag through the
       reshape instead of trying to re-index afterwards: immediately before
       `df = pd.DataFrame(_cols)` at `:3525`, add the layer's keep flags as a column of `_cols`
       (booleans, one per shared-source row, taken from `view.filter.booleans` when a view is
       present, else all `True`); then after `:3527` pass
       `keep=list(sorted_source.data["<keepcol>"])` — not `view=` — to `:3556`. The flag travels
       with its row through both the `dropna` and the `sort_values`, so it is correct by
       construction. Name the column with a leading `__dash_` prefix and drop it from
       `sorted_source` only if a test proves a column-count assertion depends on it; a spare
       boolean column is cheaper than a re-indexing bug.
    4. `:5288` (`map_dropline`) hands `dl_source`, built at `:5250-5260` from arrays already
       subset by the NaN `mask` at `:5239-5240`. Apply the same treatment: add
       `_dl_cols["<keepcol>"] = np.asarray(keep_flags)[mask]` beside the existing label-column
       line at `:5259`, then pass `keep=list(dl_source.data["<keepcol>"])` at `:5288`. Note in a
       comment that `dl_source` omits `__dash_row__` entirely (`:5250-5253`, RESEARCH §1.4) —
       this is why the flag is carried positionally rather than by row identity, and section 06
       owns the `__dash_row__` gap itself.
    5. For `map_line` and `map_connected` after section 04's NaN column lands: if the layer
       already carries a per-layer NaN y-column, plotting the label glyph against that column
       subsets the labels for free (RESEARCH §2.6/§4.2) and the keep column is redundant. Do
       **not** remove the keep column here — keep both, confirm with the 05-01 `map_line`
       ordering test that they agree, and record any disagreement as a section 06 input rather
       than silently preferring one.
    6. Every mapper that gains `view=view` or `keep=` already has `view` in its signature
       (all thirteen declare `view=None`), so no signature changes are needed at any call site.
  </action>
  <verify>
    `python3 -m pytest test/test_per_plot_qualifier_marks.py -q -k "not color and not colorvar"`
    — all label tests pass, including the `map_line` ordering assertion and the `map_dropline`
    assertion. `python3 -m pytest test/ -q` — green except 05-01's two colour tests.
    `grep -n "_apply_mlabel_opts" dash_render.py | grep -vc "view=\|keep=\|def "` prints `0`:
    every one of the thirteen call sites now passes a restriction.
    Mutation proof: change `view=view` to `view=None` at `:3657` and re-run
    `python3 -m pytest test/test_per_plot_qualifier_marks.py -q -k area` — it must go red on a
    list inequality; restore it.
  </verify>
  <done>
    All thirteen marker-label call sites pass the layer's own restriction, the two positionally
    reindexed sources carry their keep flag through the reshape rather than re-indexing after
    it, and `map_area` no longer labels rows its glyph did not draw. Stata's 22-of-74 answer
    (RESEARCH §3.5) is reproduced by an assertion on the drawn strings, not on a count.
  </done>
</task>

<task type="auto" id="05-05">
  <name>Make the colorvar colour range follow the layer's view via LinearColorMapper.domain</name>
  <files>dash_render.py</files>
  <action>
    1. In `_apply_colorvar` (`:2995-3299`), the continuous branch at `:3246-3270` currently
       hand-computes `lo`/`hi` from `col_vals` — the **whole** column (`:3031`, `:3097-3102`) —
       and passes both to `LinearColorMapper`. Because `low`/`high` are set, `domain` is ignored:
       bokeh 3.9's `low` docstring is explicit that the value is inferred from data only "If
       ``None``". Rewrite `:3249-3256` to build the mapper **without** `low`/`high`:

       ```python
       mapper = LinearColorMapper(palette=palette, nan_color=missing_color,
                                  domain=[(renderer, varname)])
       ```

       `domain` is typed `List(Tuple(Instance(GlyphRenderer), Either(String, List(String))))` on
       bokeh 3.9.0 and documented as "A collection of glyph renderers to pool data from for
       establishing data metrics. If empty, mapped data will be used instead." RESEARCH §2.7
       measured it as the **only** mechanism that follows a `CDSView` (`0 → 4` on a subset where
       an auto-ranging mapper reported `0 → 9`). `linear_cmap` is not an option: `low` and
       `high` are required positional arguments, so it can never auto-range.
    2. Ordering: the mapper must be built **after** the renderer exists. It already is —
       `_apply_colorvar` has exactly one call site, `dash_render.py:3480` in `map_scatter`, and
       it is passed the renderer `r` as its second argument. Add a comment at `:3246` saying so,
       so a future refactor that hoists the mapper does not silently break the range.
    3. Preserve the degenerate guard, but over the rows the layer draws. Before building the
       mapper, resolve the renderer's view to the values it actually maps — index
       `source.data[varname]` by `renderer.view.filter.compute_indices(renderer.data_source)`
       when a non-`AllIndices` filter is present, else use the whole column. If that subset is
       empty, or if its `nanmin` equals its `nanmax`, fall back to explicit
       `low=sub_lo, high=sub_lo + 1.0` (the subset's value, mirroring the existing `lo == hi`
       rule at `:3251-3252`) and omit `domain`, because a one-value domain gives Bokeh nothing
       to range over. Never fall back to the full column's bounds — that is the defect being
       fixed.
    4. Leave `:3266-3270` alone. `ColorBar(color_mapper=mapper, ...)` takes the same mapper
       object and `ColorBar` has no range of its own (RESEARCH §2.7), so fixing the mapper fixes
       the bar. Add a one-line comment recording that, so nobody adds a second mapper for the
       bar.
    5. Leave the discrete branch (`:3108-3245`, `CategoricalColorMapper`) alone. The brief and
       RESEARCH §2.7/§4.3 scope this item to the **colour range**; the discrete branch's factor
       list is a separate question with no measurement behind it, and inventing one here would
       contradict the "do not invent facts" rule. Record it instead as a one-line note in the
       task's commit message so a later phase can pick it up.
    6. Run rule 5's pre-merge gate at the end of this task: pull `main` into the branch, run the
       full pytest suite and the Stata cert suite, fix anything red, and re-run until green.
       Then report — do not run — the merge command for `feature/batch4-interactive-layer`.
  </action>
  <verify>
    `python3 -m pytest test/test_per_plot_qualifier_marks.py -q` — fully green, colour tests
    included. `python3 -m pytest test/ -q` — green.
    `python3 -c "..."` building one qualified `colorvar(price)` scatter and printing
    `(mapper.low, mapper.high, [(type(r).__name__, c) for r, c in mapper.domain])` prints
    `(None, None, [('GlyphRenderer', 'price')])`.
    Mutation proof: set `domain=[]` and re-run
    `python3 -m pytest test/test_per_plot_qualifier_marks.py -q -k colorvar` — it must go red;
    restore. Second mutation: compute the degenerate fallback from `col_vals` instead of the
    view-resolved subset and confirm the degenerate test goes red; restore.
    `grep -n "low=lo, high=hi" dash_render.py` returns nothing.
  </verify>
  <done>
    A qualified `colorvar()` scatter maps its colours, and draws its colour bar, against the
    range of the rows the layer drew. The mapper is built after its renderer, carries
    `domain=[(renderer, varname)]` with both bounds unset, and falls back to the **subset's**
    bounds only in the degenerate one-value case. Work item 8 is discharged: BR-01.5 holds for
    both the marker label and the colour mapping, and US-A3's two acceptance criteria are pinned
    by tests that have been shown to die under mutation.
  </done>
</task>
