# Section 02: The mask mechanism — twelve computed mappers

## Overview

This section builds the mechanism the rest of the phase plugs into: a `row_mask=` keyword
that carries a layer's row restriction *into* a computed mapper as data, because a `CDSView`
can never reach one. Twelve of the fourteen computed mappers share one shape — read
`source.data[xvar]`/`[yvar]`, build a NaN mask, subset, then fit — so the fix is one shared
helper ANDed into the NaN mask each already builds, plus one keyword threaded from
`_make_figure_body` through `_add_glyph`. `histogram` and `kdensity` cannot take this
treatment and belong to section 03; connected-topology raw layers belong to section 04.

Two user-visible bugs close here. **Item 1**: `dash (scatter mpg weight) (lfit mpg weight if
foreign==1)` draws the all-74-car fit, slope `-.00600869`, where Stata draws the 22-car fit,
slope `-.01042596` — rc 0, no warning. **Item 3 / finding F-A**: a *linked* `by()` graph gives
every panel the same source and differentiates panels by view alone, so every panel already
draws an identical `lfit` computed from all rows **with no qualifier written at all**. One
derivation closes both, because the view's booleans are exactly the mask.

Without this section, sections 03, 05, 06, 07 and 09 have no mask to consume.

**Test order (project rule 8): task 02-01 writes every failing test for this section**, runs
them against the unmodified tree, and records the failure. Tasks 02-02 through 02-07 turn
them green a group at a time; only 02-07 adds tests, for behaviour unreachable until 02-06.

## Risk: [yellow] — twelve edits to statistical code paths, each one line, but every one changes a number users have already seen

## Dependencies
- Depends on: section-01
- Blocks: section-03, section-05, section-06, section-07, section-09
- Parallel batch: 2

## Evidence

### The single qualifier site, and why it never arrives

`DashRenderer._make_figure_body`, `dash_render.py:9951-9998` (RESEARCH §1.1).
`source_for_plot = source` at `:9955` is **never reassigned** — the layer always draws from
the graph's shared `ColumnDataSource`; only `_plot_view` changes. The mask built at `:9979`
is *exactly* the array a `mask=` kwarg would carry — one bool per row of the source the mapper
receives, already intersected with any facet view at `:9986-9988`. It is in scope at every
dispatch call (`:10027`, `:10031`, `:10036`, `:10063`) as `_plot_view.filter.booleans`.

Identity space: `_ROW_ID_COLUMN = "__dash_row__"` (`:591`), stamped by `_make_source`
(`:8506`). `_row_ids_for` (`:8574-8592`) returns ordinal positions in `self.df`.

### The fourteen computed mappers — a uniform result

RESEARCH §1.2, **machine-verified by AST walk: all 14 accept `view=None`, and the token
`view` never appears in any of their bodies.** All 14 build their own `ColumnDataSource`.

| method | `def` | reads data at | own CDS at | returns | section |
|---|---|---|---|---|---|
| `map_area` | 3592 | 3614, 3615 | 3630, 3652 | VArea renderer | **02** |
| `map_lfit` | 3821 | 3845, 3846 | 3853, 3865 | renderer | **02** |
| `map_qfit` | 3873 | 3895, 3896 | 3902, 3910 | renderer | **02** |
| `map_lfitci` | 3918 | 3942, 3943 | 3950, 3988 | `[line_r, band_r]` | **02** |
| `map_qfitci` | 3998 | 4023, 4024 | 4031, 4082 | `[line_r, band_r]` | **02** |
| `map_lowess` | 4091 | 4127, 4128 | 4134, 4141 | renderer | **02** |
| `map_lpoly` | 4272 | 4300, 4301 | 4306, 4333 | renderer | **02** |
| `map_lpolyci` | 4344 | 4366, 4367 | 4372, 4433 | `[line_r, band_r]` | **02** |
| `map_fpfit` | 4517 | 4543, 4544 | 4549, 4558 | renderer | **02** |
| `map_fpfitci` | 4569 | 4591, 4592 | 4597, 4625 | `[line_r, band_r]` | **02** |
| `map_histogram` | 4636 | `_extract_finite` :4666 | 4663, 4672 | Quad + agg tags | 03 |
| `map_kdensity` | 4806 | `_extract_finite` :4830 | 4836, 4860, 4892 | Line + agg tags | 03 |
| `map_mspline` | 5912 | 5942, 5943 | 5967, 5975 | `[r]` | **02** |
| `map_mband` | 5983 | 6011, 6012 | 6017, 6057 | `[r]` | **02** |

Twelve share one shape, e.g. `map_lfit`:

```python
 3845        x = np.array(source.data[xvar], dtype=float)
 3846        y = np.array(source.data[yvar], dtype=float)
 3847        # Drop NaN pairs
 3848        mask = ~(np.isnan(x) | np.isnan(y))
 3849        x, y = x[mask], y[mask]
```

**Minimal change for those twelve: a `row_mask=` kwarg ANDed into the existing NaN mask —
no other body change.** The local is already named `mask`, so the parameter must be
`row_mask=` (or the local renamed); `row_mask` occurs **0 times** in `dash_render.py` today
(`grep -c row_mask dash_render.py` → 0), so the name is free.

Insertion points, per RESEARCH §1.2: `map_lfit` after `:3846` · `map_qfit` after `:3896` ·
`map_lfitci` after `:3943` (**before `n = len(x)` at `:3946`**, which feeds `df = n-2` and
`se_fit`) · `map_qfitci` after `:4024` · `map_lowess` after `:4128` · `map_lpoly` after
`:4301` · `map_lpolyci` after `:4367` (also fixes the bootstrap at `:4427-4430`) ·
`map_fpfit` after `:4544` · `map_fpfitci` after `:4592` (plus `_bootstrap_ci` at `:4620`) ·
`map_mspline` after `:5943` (**before the `argsort` at `:5949`**) · `map_mband` after
`:6012` · `map_area` after `:3615`.

Most become *correct by construction* once masked: `map_lowess`'s `frac=bw` (`:4139`) is a
fraction of the sample; `_default_lpoly_bwidth` (`:4157`) derives bandwidth from the data;
`map_mband`'s band count `_mband_default_bands(len(x_clean))` (`:6029`) becomes
subset-relative — each matching what `twoway ... if` does.

### Why `histogram` and `kdensity` are excluded from this section

RESEARCH §1.2: `_extract_finite` (`:964-995`) drops `None`/NaN internally and returns a
**shorter array with no positional correspondence**, so a mask cannot be applied after the
call:

```python
  994    arr = np.array([v for v in col if v is not None], dtype=float)
  995    return arr[~np.isnan(arr)]
```

Both also put `options` **before** `xvar` in their signatures and are already special-cased
in `_add_glyph` at `:10418-10419`. They are section 03's five tasks.

### Why `map_area` stays here and not in section 04

RESEARCH §2.1, measured against bokeh 3.9.0: `ConnectedXYGlyph` has **exactly two subclasses
in 3.9 — `Line` and `Patch`.** Not `VArea`. `map_area` draws `fig.varea` (`:3631`), so
E-1024 `CDSVIEW_FILTERS_WITH_CONNECTED` does not apply to it and it is not moved onto section
04's NaN-column mechanism. Its restriction arrives as `row_mask`, like the other eleven.

> **Superseded decision, recorded so no one implements the earlier answer.** Discovery Q3
> mandated a *private pre-filtered `ColumnDataSource`* for the connected-topology case.
> RESEARCH §2.3 measured, in a real browser with an instrumented `CanvasRenderingContext2D`,
> that a private source draws the line **straight across the excluded gap**, loses linked
> selection entirely, and is never reached by the filter callback. **The new decision is a
> per-layer NaN column on the shared source (section 04).** Nothing in this section may
> introduce a pre-filtered private source for a raw-data layer (BR-01.11, TR-01.15).

### Item 3 — finding F-A, a bug with no qualifier in it

RESEARCH §1.9: at `dash_render.py:11465-11476` a **linked** `by()` graph gives every panel
the same `shared_src_render` and differentiates them only by `panel_view_r`:

```python
11465                    if shared_src_render is not None and name in link_names:
11466                        src = shared_src_render
11467                        if panel_idx_r < len(masks_render):
11468                            _, mask_r   = masks_render[panel_idx_r]
11469                            _pf = BooleanFilter(booleans=mask_r)
11470                            panel_view_r = CDSView(filter=_pf)
```

Since computed mappers ignore `view`, **every facet panel draws an identical
`lfit`/`kdensity`/`histogram` computed from all rows.** An **unlinked** `by()` graph
(`:11481`, `src = self.sources.get(fkey)`, `panel_view_r = None`) gets a genuinely pre-subset
source per panel and is correct. So **adding `link()` silently changes a computed layer's
values.** The same applies to a linked graph-level qualifier (`_linked_graph_views`,
`:11499-11505`). This is its own user-visible bug: it needs its own test and its own
changelog line (RESEARCH §4.8, F-A). The `row_mask` fix closes it because in that path
`_plot_view` *is* the panel view and its booleans *are* the restriction.

### Stata ground truth (RESEARCH §3.1, §3.2)

StataNow 19.5 MP (arm64), `sysuse auto`, N=74, foreign==1: 22.

| quantity | `if foreign==1` | full sample |
|---|---|---|
| N | **22** | **74** |
| slope `_b[weight]` | **-.010425957587798849** | **-.0060086868119993289** |
| intercept `_b[_cons]` | **48.918297231743246** | **39.440283530717977** |
| x-range of the drawn segment | **[1760, 3420]** | [1760, 4840] |

| command | layer 1 serset | `lfit` slope | equals `regress` on |
|---|---|---|---|
| `(scatter) (lfit)` | 74 obs | -.0060086866 | full sample |
| **`(scatter) (lfit … if foreign==1)`** | **74 obs** | **-.0104259571** | `if foreign==1` |
| `(scatter … if foreign==0) (lfit … if foreign==1)` | 52 obs | -.0104259571 | each its own |
| `(scatter) (lfit … if weight>2500) if foreign==1` | 22 obs | -.0093656528 | the **intersection**, N=6 |
| `(scatter) (lfit … in 1/60) if foreign==1` | 22 obs | -.0096564116 | intersection, N=8 |

A per-layer qualifier restricts only its own layer (the scatter keeps all 74 rows);
command-level restricts every layer; both together are a logical **AND**, and order does not
matter. **Method caveat:** sersets store `float`, so graph-recovered coefficients agree with
`regress` doubles only to ~1e-8. Assertions must use the `regress` doubles, which section 01
checks in as `test/fixtures/stat_truth_qualifier.json`.

> ⚠️ **Trap.** `auto.dta` ships sorted domestic-first; foreign cars start at observation 53.
> `in 1/20` contains **zero** foreign cars. Use `in 1/60` (N=8) for any intersection test.

### The trap that governs every test in this section

RESEARCH §1.9, F-B. Existing coverage is **scatter-only and structurally cannot catch this
class of bug**. `test/test_varlist_expansion.py:101`'s `_visible_count` helper, and the
identical `_visible` at `test/test_per_plot_qualifier_linking.py:82`, read
`renderer.view.filter.booleans` — which reports a *computed* layer as **fully visible no
matter what it drew**, because a computed layer's renderer has a private source and no view.
**Assertions on computed layers must compare the layer's own source values against an
independently computed subsample**, never a view's booleans. `test_per_plot_qualifier_linking.py`
(163 lines, 7 tests) contains no reference to `lfit`, `kdensity` or `histogram`.

### Environment fact that shapes the test file

`statsmodels` does not import in this environment (`No module named 'packaging'`), so
`_optional_import("statsmodels.nonparametric.smoothers_lowess", "lowess", …)` returns `None`
and `map_lowess` takes its early-out at `:4133-4135`. `scipy` **is** present
(`scipy.stats` and `scipy.interpolate.PchipInterpolator` both import), so `lfitci`, `qfitci`
and `mspline` are exercisable. Per the project's own rule, **a skip is not a pass**: the
parametrised test must assert how many mappers actually ran and name the ones it skipped.

### Boundaries — what this section must NOT touch

- The `len(x) < 2` / `< 3` / `< 4` early-outs in each mapper now fire on the **masked** count.
  Leave them exactly as they are. Replacing their silence with a named warning is
  **section 07** (degenerate subsets, discovery Q8 upheld).
- `self._apply_mlabel_opts(fig, source, options, xvar, yvar)` at `map_area:3657` still reads
  the **unmasked shared source**. That is **section 05** (the `LabelSet` → `figure.text`
  replacement). Do not change it here.
- `self._register_view_filter(source, _pf, self._row_ids_for(_pdf))` at `:9991-9992`
  registers the qualifier's rows alone, losing the facet AND-term on the first widget move
  (RESEARCH §1.5, item 7). That is **section 06**. Do not change it here.
- The `except Exception` / warn-and-draw-unfiltered contract at `:9993-9998` (BR-01.12) is
  preserved unchanged.
- `CHANGELOG.md`, `dash.sthlp` and the end-to-end `.cscript` are **section 10**. This section
  leaves the F-A facts in the new test module's docstring for section 10 to lift.

## TDD test stubs

All of these live in one new file, **`test/test_per_plot_qualifier_computed.py`**, created by
task 02-01. Each stub names the pre-fix failure, because a test that fails for the wrong
reason is not evidence.

- **Test: `test_lfit_with_per_plot_if_is_estimated_on_the_subset`** (the headline, BR-01.1 /
  BR-01.2). Render `(scatter mpg weight) (lfit mpg weight if foreign==1)` over
  `test/fixtures/data/auto.csv`; recover slope and intercept from the `lfit` renderer's own
  `data_source`; assert slope `-.010425957587798849` and intercept `48.918297231743246` at
  `rtol=1e-6` against `test/fixtures/stat_truth_qualifier.json`, and assert explicitly that
  they are **not** `-.0060086868119993289` / `39.440283530717977`. Also assert the fit grid
  spans `[1760, 3420]`, not `[1760, 4840]`, and that the scatter still draws 74 points
  (BR-01.3). **Pre-fix failure: a wrong number, `-0.00600868…`, not an exception.**
- **Test: `test_every_computed_mapper_equals_the_same_mapper_on_a_presubset_source`**
  (rule 4 coverage for TR-01.2). Parametrised over the twelve: `map_lfit`, `map_qfit`,
  `map_lfitci`, `map_qfitci`, `map_lowess`, `map_lpoly`, `map_lpolyci`, `map_fpfit`,
  `map_fpfitci`, `map_mspline`, `map_mband`, `map_area`. Oracle: the **same mapper called on
  a ColumnDataSource built from the qualified rows only**, with no mask. Compare the emitted
  renderer's `data_source.data` arrays elementwise. Never read `renderer.view`. Run each
  case twice — once with a contiguous run (`foreign==1`, rows 52-73) and once with a
  non-contiguous mask (every third row) so a positional misalignment cannot hide behind a
  single run. **Pre-fix failure: `TypeError: map_lfit() got an unexpected keyword argument
  'row_mask'`** — a shape failure, so its non-vacuity rests on the mutation row below.
- **Test: `test_the_ci_band_moved_too_not_just_the_line`** for the four band-bearing mappers
  (`lfitci`, `qfitci`, `lpolyci`, `fpfitci`), BR-01.5. The `y_lower`/`y_upper` arrays must
  equal the pre-subset-source oracle's. The bootstrap is seeded (`_resolve_seed`, `:6522`,
  default 42), so the comparison is exact, not statistical. **Mutation that must kill it:
  mask `x`/`y` but pass the *unmasked* arrays to `GlyphMapper._bootstrap_ci` at `:4427`.**
- **Test: `test_in_expr_is_honoured_exactly_as_if_expr`** (BR-01.4). The headline test again
  with `in 1/60` instead of `if foreign==1`, and the intersection case
  `(lfit … in 1/60) if foreign==1` → N=8, slope `-.0096564106174751828`. RESEARCH §1.2
  records `in_expr` as measured-working-but-untested for `scatter` and ignored for `lfit`.
- **Test: `test_and_row_mask_returns_the_nan_mask_when_row_mask_is_none`** (rule 4, the new
  helper). Pre-fix failure: `AttributeError: module 'dash_render' has no attribute
  '_and_row_mask'`.
- **Test: `test_and_row_mask_warns_and_does_not_apply_a_wrong_length_mask`** (BR-01.12). A
  9-entry mask against a 10-row column must warn, name the layer, and return the NaN mask
  unchanged. **Mutation that must kill it: `return nan_mask & rm[:nan_mask.size]`** — a
  silent truncation must not pass.
- **Test: `test_linked_by_panels_do_not_all_draw_the_same_fit`** (item 3 / F-A, BR-01.8).
  Build a `by(rep78)` graph with `link(_all)` and an unqualified `lfit` layer; assert the
  per-panel fit coefficients are **pairwise distinct** and that each equals the **unlinked**
  `by()` render of the same spec, panel for panel. The unlinked path is the oracle because
  RESEARCH §1.9 measured it correct. **Pre-fix failure: every panel returns the same slope,
  the all-rows one.**
- **Test: `test_a_linked_graph_level_qualifier_reaches_a_computed_layer`** (item 3,
  `_linked_graph_views` at `:11499-11505`). A graph in `link(_all)` carrying
  `if foreign==1` at graph level must draw the 22-row fit. Pre-fix: the 74-row fit.
- **Test: `test_row_mask_types_matches_the_mappers_that_accept_the_kwarg`** (the coverage
  claim, made mechanical). For every name in `dash_render._ROW_MASK_TYPES`, assert the
  dispatch target's `inspect.signature` has a `row_mask` parameter; and assert the twelve
  names of this section are members. Written as a **superset** assertion so section 03 can
  add `histogram`/`hist`/`kdensity` without editing it.

**Mutation table — proof the tests are not vacuous.** Apply, confirm the named test fails,
revert:

| break this | test that must die |
|---|---|
| delete the `_and_row_mask(...)` line in `map_lfit` | `test_lfit_with_per_plot_if_is_estimated_on_the_subset` |
| invert in `_and_row_mask`: `return nan_mask & ~rm` | every case of `test_every_computed_mapper_equals_the_same_mapper_on_a_presubset_source` |
| truncate in `_and_row_mask`: `rm[:nan_mask.size]` | `test_and_row_mask_warns_and_does_not_apply_a_wrong_length_mask` |
| pass unmasked `x, y` to `_bootstrap_ci` at `:4427` | `test_the_ci_band_moved_too_not_just_the_line[lpolyci]` |
| in `_make_figure_body`, derive `_row_mask` only inside the per-plot branch | `test_linked_by_panels_do_not_all_draw_the_same_fit` |
| drop `"area"` from `_ROW_MASK_TYPES` | `test_row_mask_types_matches_the_mappers_that_accept_the_kwarg` and the `map_area` parametrisation |

## Tasks

<task type="auto" id="02-01">
  <name>Write the failing tests for the whole section</name>
  <files>test/test_per_plot_qualifier_computed.py (new)</files>
  <action>
    Create `/Users/billy/Desktop/Programs/StataPrograms/d/dash/test/test_per_plot_qualifier_computed.py`.
    Write **only tests**. Do not touch `dash_render.py` in this task.

    1. Module docstring. State the defect in the terms a reader of section 10's CHANGELOG
       will need: `dash (scatter mpg weight) (lfit mpg weight if foreign==1)` drew slope
       -.00600869 / intercept 39.440284 (all 74 cars) and must draw -.01042596 / 48.918297
       (the 22 foreign cars); and, separately, that a LINKED `by()` graph drew an identical
       computed layer in every panel with no qualifier written at all (finding F-A). Section
       10 lifts both paragraphs; leave them self-contained.
    2. Imports and paths: copy the header block of `test/test_statistical_truth.py:16-34`
       (`_HERE`, the two `sys.path.insert` lines, `import dash_render`,
       `from dash_render import GlyphMapper, OptionTranslator, SchemeParser`) and add
       `from conftest import make_data_json` as `test/test_per_plot_qualifier_linking.py:40`
       does. Load `test/fixtures/data/auto.csv` with pandas for the data fixtures.
    3. Ground-truth fixture: read `test/fixtures/stat_truth_qualifier.json` (section 01's
       deliverable). Do **not** put a module-level `pytest.mark.skipif` on the file. If the
       fixture is missing, `pytest.fail` with the message
       "section 01 must land first: test/fixtures/stat_truth_qualifier.json is missing".
       A skip here would silently certify nothing.
    4. Renderer helper `_render(tmp_path, plots, *, link="", graph_if="", by="")` modelled on
       `test/test_per_plot_qualifier_linking.py:50-75` but backed by the 74-row auto frame.
       It writes a spec JSON + data JSON, constructs `dr.DashRenderer`, calls `.render()`,
       returns the renderer.
    5. Layer-reading helper `_fit_line(renderer)` that returns `(slope, intercept, xmin,
       xmax)` from the renderer's OWN `data_source.data` — `slope = (y[-1]-y[0])/(x[-1]-x[0])`,
       `intercept = y[0] - slope*x[0]`. Add a module comment saying in full:
       "Assertions on computed layers compare the layer's own source VALUES against an
       independently computed subsample. Never read renderer.view.filter.booleans: a
       computed layer has a private source and no view, so _visible_count
       (test_varlist_expansion.py:101) reports it fully visible no matter what it drew."
       Add an assertion inside `_fit_line` that `getattr(renderer, "view", None)` is not
       being consulted — i.e. simply do not reference it.
    6. Oracle helper `_presubset_source(df, mask, cols)` returning a `ColumnDataSource` built
       from `df.loc[mask, cols]`, used as the independent oracle for the parametrised test.
    7. Write every test named in this section's "TDD test stubs" list, with exactly those
       names. For the parametrised mapper test, build the parametrisation from a module-level
       list of the twelve `(type_name, method_name, kind)` tuples so the list is visible as
       the coverage claim. Skip a case only when its optional dependency is absent
       (`map_lowess` needs statsmodels, which does not import in this environment), record
       the skipped names in a module-level list, and end the test session's parametrised run
       with an assertion that at least 11 of the 12 mappers actually executed.
    8. Run the file against the unmodified tree and paste the failure summary into the commit
       message.

    Commit on `feature/batch4-interactive-layer`. No AI references in the message (rule 7).
    Do not commit to `main` (rule 6).
  </action>
  <verify>`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_per_plot_qualifier_computed.py -q 2>&1 | tail -30` reports **0 passed** and no collection error. `python3 -m pytest test/test_per_plot_qualifier_computed.py -q -k lfit_with_per_plot_if 2>&1 | grep -c -- "-0.00600868"` prints a non-zero count — the headline test fails with the unqualified slope, which is the record of the defect, not with an exception.</verify>
  <done>`test/test_per_plot_qualifier_computed.py` exists, collects cleanly, and every test in it fails. The two behavioural tests fail with wrong numbers; the API-shape tests fail with `TypeError`/`AttributeError`. `dash_render.py` is unmodified.</done>
</task>

<task type="auto" id="02-02">
  <name>Add the shared `_and_row_mask` helper</name>
  <files>dash_render.py</files>
  <action>
    In `/Users/billy/Desktop/Programs/StataPrograms/d/dash/dash_render.py`, insert a new
    module-level function immediately after `_extract_finite` ends at `:996` and before the
    `# ===== OptionTranslator =====` banner at `:998`. `warnings` and `np` are already
    imported at module level (`warnings.warn` is used at `:9994`).

    ```python
    def _and_row_mask(
        nan_mask: "np.ndarray",
        row_mask: "list | np.ndarray | None",
        *,
        where: str = "",
    ) -> "np.ndarray":
        """AND a per-plot row restriction into a mapper's own NaN mask.

        A computed layer builds its own ColumnDataSource, so a CDSView over the
        graph's shared source never reaches it.  The restriction has to arrive
        as data.  ``row_mask`` is one bool per row of the source the mapper was
        handed -- the booleans of the layer's view, already intersected with any
        facet or linked-graph view by ``_make_figure_body`` -- and ``nan_mask``
        is the mapper's own finite-pair mask over the same rows, so the two are
        positionally aligned by construction and an elementwise AND is the whole
        operation.

        Args:
            nan_mask: Boolean array the mapper built from its own columns.
            row_mask: The layer's row restriction, or None for no restriction.
            where:    Layer type name, used only in the length-mismatch warning.

        Returns:
            ``nan_mask`` unchanged when ``row_mask`` is None; otherwise the
            elementwise AND.  On a length mismatch the mask is returned
            unchanged and a warning is issued: a mask of the wrong length
            cannot be realigned, and silently dropping the wrong rows is worse
            than drawing all of them (BR-01.12 -- never lose the layer).
        """
        if row_mask is None:
            return nan_mask
        rm = np.asarray(row_mask, dtype=bool)
        if rm.shape != nan_mask.shape:
            warnings.warn(
                f"dash: the row restriction on {where or 'this layer'} has "
                f"{rm.size} entries for {nan_mask.size} rows; it was not "
                f"applied and the layer is computed unrestricted.",
                stacklevel=3,
            )
            return nan_mask
        return nan_mask & rm
    ```

    Use `rm.size` / `nan_mask.size` in the message, not `rm.shape[0]`: a scalar `row_mask`
    has shape `()` and would raise `IndexError` inside the warning path.

    This is the single mutation target the phase's test plan names ("invert the mask in the
    shared subsetting helper", phase document line 981). Every one of the twelve mappers must
    go through it — do not inline `mask & np.asarray(row_mask)` anywhere.

    **Line numbers shift from here on.** This helper adds ~45 lines at `:996`, so every line
    number quoted in tasks 02-03 through 02-06 refers to the *pre-edit* file and will be
    roughly 45 lines low once this task lands (and a further 1-3 lines low per mapper already
    edited). Every anchor in those tasks is also given as a symbol — the
    `mask = ~(np.isnan(...) | np.isnan(...))` line inside a named method — and the symbol is
    authoritative. Locate the method by name, then the `mask = ~(...)` line inside it; never
    trust a bare line number after an insertion.
  </action>
  <verify>`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_per_plot_qualifier_computed.py -q -k and_row_mask 2>&1 | tail -3` prints `2 passed`. `python3 -c "import numpy as np,dash_render as d;print(d._and_row_mask(np.array([1,1,0],bool),None).tolist(), d._and_row_mask(np.array([1,1,0],bool),[1,0,1]).tolist())"` prints `[True, True, False] [True, False, False]`.</verify>
  <done>`dash_render._and_row_mask` exists, is covered by two unit tests (rule 4), warns rather than truncating on a length mismatch, and no mapper calls it yet.</done>
</task>

<task type="auto" id="02-03">
  <name>Thread `row_mask=` into the six single-fit mappers</name>
  <files>dash_render.py</files>
  <action>
    Six mappers, two edits each. Cite TR-01.1 and TR-01.2 in the commit message.

    For each of `map_lfit` (`:3821`), `map_qfit` (`:3873`), `map_lowess` (`:4091`),
    `map_lpoly` (`:4272`), `map_fpfit` (`:4517`) and `map_area` (`:3592`):

    1. **Signature.** Add `row_mask=None` immediately after `view=None` and before
       `color_idx: int = 0`. Keep `view=None` — raw mappers and `_add_glyph` pass it
       positionally-by-keyword everywhere and removing it would break the dispatch.
    2. **Body.** Insert exactly one line immediately AFTER the existing
       `mask = ~(np.isnan(...) | np.isnan(...))` line and BEFORE the line that subsets:
       ```python
            mask = _and_row_mask(mask, row_mask, where="lfit")
       ```
       with `where=` set to the layer type: `"lfit"`, `"qfit"`, `"lowess"`, `"lpoly"`,
       `"fpfit"`, `"area"`. In `map_area`, `map_lowess` and `map_lpoly` the locals are named
       as in the file (`x_arr`/`y_arr` for `area`); the anchor is the `mask = ~(...)` line in
       every case, which is `:3848` (lfit), `:3897` (qfit), `:4129` (lowess), `:4302`
       (lpoly), `:4545` (fpfit), `:3617` (area).
    3. **Docstring.** Add one `row_mask:` line to each `Args:` block:
       "Optional per-row boolean restriction for this layer, one entry per row of *source*;
       the fit is estimated on the kept rows only."

    Do **not** change anything else in these bodies. In particular:
    - Leave the `if len(x) < 2:` / `< 4` early-outs alone. They now fire on the masked count,
      which is the intended behaviour; replacing their silence with a named warning is
      section 07.
    - In `map_area`, do **not** attach `view` to `fig.varea` at `:3631`. TR-01.2's
      parenthetical ("attach the view it never gets today") is satisfied by `row_mask`:
      `area_source` at `:3630` is a private, already-subset CDS, so a `BooleanFilter` sized
      to the shared source would be positionally invalid against it — the exact shape of
      finding D1 (RESEARCH §1.3) and hazard B1 (§2.3). Record that reasoning in a code
      comment above `area_source`.
    - In `map_area`, leave `self._apply_mlabel_opts(fig, source, ...)` at `:3657` untouched;
      it is section 05's.
    - `map_lowess`'s `frac=bw` at `:4139` and `_default_lpoly_bwidth` at `:4157` need no edit:
      both derive from the arrays they are handed, so they become subset-relative for free,
      matching `twoway lowess ... if` (RESEARCH §1.2).
  </action>
  <verify>`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -c "
import inspect, dash_render as d
for n in ['map_lfit','map_qfit','map_lowess','map_lpoly','map_fpfit','map_area']:
    assert 'row_mask' in inspect.signature(getattr(d.GlyphMapper,n)).parameters, n
print('ok 6')"` prints `ok 6`. `python3 -m pytest test/test_per_plot_qualifier_computed.py -q -k "presubset and (lfit or qfit or lpoly or fpfit or area)" 2>&1 | tail -3` shows those parametrised cases passing (the `lowess` cases skip: statsmodels does not import here).</verify>
  <done>Six mappers accept `row_mask=` and AND it into their NaN mask through `_and_row_mask`. Their parametrised subsample-equality cases pass. The renderer does not pass the kwarg yet, so the headline test still fails with the unqualified slope.</done>
</task>

<task type="auto" id="02-04">
  <name>Thread `row_mask=` into the four CI mappers</name>
  <files>dash_render.py</files>
  <action>
    Same two edits as 02-03, applied to `map_lfitci` (`:3918`), `map_qfitci` (`:3998`),
    `map_lpolyci` (`:4344`) and `map_fpfitci` (`:4569`), with `where=` set to `"lfitci"`,
    `"qfitci"`, `"lpolyci"`, `"fpfitci"`. Anchors: the `mask = ~(np.isnan(x) | np.isnan(y))`
    line at `:3944`, `:4025`, `:4368`, `:4593`.

    Three things to get right, all of which the band assertions in 02-01 will catch:

    1. **`map_lfitci`: the insertion must land before `n = len(x)` at `:3946`.** `n` feeds
       `df = n - 2` for the t critical value and the `se_fit` denominator; a band computed
       with the full-sample `n` around a subset-sample line is a worse wrong answer than
       today's, because it looks calibrated. Verify with
       `grep -n -A3 'where="lfitci"' dash_render.py` after the edit — not by line number,
       which 02-02 has already shifted by ~45 — and confirm the order is `_and_row_mask(...)`,
       then `x, y = x[mask], y[mask]`, then `n = len(x)`.
    2. **`map_lpolyci`'s bootstrap at `:4427-4430` is fixed by construction.** It is called
       as `GlyphMapper._bootstrap_ci(x, y, x_grid, _lpoly_fn, fallback=y_fit, ...)` — `x` and
       `y` are the masked arrays by then, so the resamples are drawn from the subset. Make no
       edit there; add a one-line comment saying so, and let
       `test_the_ci_band_moved_too_not_just_the_line[lpolyci]` prove it.
    3. **`map_fpfitci`'s `_bootstrap_ci` at `:4620` is the same case.** Same comment, same
       proof. The bootstrap is seeded via `_resolve_seed(options)` (`:6522`, default 42), so
       the band is reproducible and the oracle comparison is exact.

    Leave the `len(x) < 3` / `len(x) < 4` early-outs and their `empty_ci_src` /
    `empty_src` returns exactly as they are — section 07 owns the degenerate policy.
  </action>
  <verify>`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -c "
import inspect, dash_render as d
for n in ['map_lfitci','map_qfitci','map_lpolyci','map_fpfitci']:
    assert 'row_mask' in inspect.signature(getattr(d.GlyphMapper,n)).parameters, n
print('ok 4')"` prints `ok 4`. `python3 -m pytest test/test_per_plot_qualifier_computed.py -q -k "band_moved" 2>&1 | tail -3` prints `4 passed`. `grep -n -A3 'where="lfitci"' dash_render.py` prints the `_and_row_mask` call, then `x, y = x[mask], y[mask]`, then `n = len(x)`, in that order (line numbers have moved; the order is what is being checked).</verify>
  <done>All four CI mappers estimate the line **and** the band on the qualified rows. The band assertions pass for all four, and the two bootstrap call sites are documented as fixed by construction rather than edited.</done>
</task>

<task type="auto" id="02-05">
  <name>Thread `row_mask=` into `map_mspline` and `map_mband`</name>
  <files>dash_render.py</files>
  <action>
    Same two edits, applied to `map_mspline` (`:5912`, anchor `mask = ~(...)` at `:5944`,
    `where="mspline"`) and `map_mband` (`:5983`, anchor at `:6013`, `where="mband"`).

    Two ordering facts to preserve:

    1. **`map_mspline`: the insertion must land before the `np.argsort(x_clean)` at `:5949`.**
       `row_mask` is positional against the source's rows; once `x_clean` is sorted, position
       no longer means row. Insert on the `mask = ~(...)` line, so `x_clean = x_arr[mask]` at
       `:5945` already carries the restriction and the sort, the `np.unique` dedup at `:5955`
       and the PCHIP fit all operate on the subset.
    2. **`map_mband`: the band count becomes subset-relative and that is correct.**
       `_mband_default_bands(len(x_clean))` at `:6029` is Stata's own rule applied to the
       estimation sample, so a qualified `mband` gets the number of bands Stata gives it
       (RESEARCH §1.2). Do not pin the old count. `x_min`/`x_max` at `:6030` likewise shrink
       to the subset's range, matching the `lfit` x-range finding in RESEARCH §3.1.

    Leave the `len(x_clean) < 4` early-out at `:6019-6021` and the `x_max == x_min` guard at
    `:6031-6033` unchanged — section 07.
  </action>
  <verify>`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -c "
import inspect, dash_render as d
for n in ['map_mspline','map_mband']:
    assert 'row_mask' in inspect.signature(getattr(d.GlyphMapper,n)).parameters, n
print('ok 2')"` prints `ok 2`. `python3 -m pytest test/test_per_plot_qualifier_computed.py -q -k "presubset" 2>&1 | tail -3` shows 22 of the 24 parametrised cases passing and 2 skipped (`lowess`, both mask shapes). `grep -n -A5 'where="mspline"' dash_render.py` shows the `_and_row_mask` call above `x_clean = x_arr[mask]` and above `order = np.argsort(x_clean)` (line numbers have moved since 02-02; the order is what is being checked).</verify>
  <done>All twelve mappers of this section accept `row_mask=` and honour it. `grep -c "_and_row_mask(mask" dash_render.py` returns 12. The headline test still fails: nothing passes the kwarg yet.</done>
</task>

<task type="auto" id="02-06">
  <name>Derive the mask in `_make_figure_body` and pass it through `_add_glyph`</name>
  <files>dash_render.py</files>
  <action>
    This is the task that turns the headline test green. Three edits, all in
    `/Users/billy/Desktop/Programs/StataPrograms/d/dash/dash_render.py`. TR-01.1.

    1. **Module-level type set.** Immediately after `_ROW_ID_COLUMN = "__dash_row__"` at
       `:591`, add:
       ```python
       # Plot types whose mapper recomputes from the data and therefore takes
       # row_mask=.  A CDSView never reaches these layers: each builds its own
       # ColumnDataSource, so the restriction has to arrive as data, not as a
       # view.  Every other mapper honours view= already.
       _ROW_MASK_TYPES = frozenset({
           "lfit", "qfit", "lfitci", "qfitci", "lowess", "lpoly", "lpolyci",
           "fpfit", "fpfitci", "mspline", "mband", "area",
       })
       ```
       Section 03 adds `"histogram"`, `"hist"` and `"kdensity"` to this set; leave a comment
       saying so. Module level, not function level, so the test can import it.

    2. **`_add_glyph` (`:10334`).** Add `row_mask=None` to the signature after `view=None`,
       document it in the `Args:` block, and gate the forwarding on the frozenset so raw and
       range mappers are untouched. Replace the `fn = dispatch.get(pt)` block at
       `:10415-10421` with:
       ```python
               fn = dispatch.get(pt)
               if fn is not None:
                   # Only the computed mappers take row_mask=; the rest honour view=.
                   _extra = {"row_mask": row_mask} if pt in _ROW_MASK_TYPES else {}
                   # histogram and kdensity are univariate — no xvar positional arg
                   if pt in ("histogram", "hist", "kdensity"):
                       fn(fig, source, yvar, options, view=view,
                          color_idx=color_idx, **_extra)
                   else:
                       fn(fig, source, yvar, xvar, options, view=view,
                          color_idx=color_idx, **_extra)
       ```
       Leave the `range_dispatch` branch at `:10410-10413` alone: no range type is in
       `_ROW_MASK_TYPES`. Leave `_add_pc_glyph` alone.

    3. **`_make_figure_body` (`:9495`).** Insert the derivation between the end of the
       per-plot `except` block at `:9998` and the
       `# Determine secondary axis assignments for this plot layer` comment at `:10000`:
       ```python
                   # The mask a computed mapper needs is exactly the booleans the
                   # view already carries.  In the branch above, _mask is already
                   # (facet AND qualifier); where no per-plot qualifier was written,
                   # _plot_view is still the facet or linked-graph view, and its
                   # booleans are the only restriction those layers ever get --
                   # which is why a LINKED by() graph drew an identical lfit in
                   # every panel.  One derivation covers both.
                   _row_mask = None
                   _pv_filter = getattr(_plot_view, "filter", None)
                   _pv_bools = getattr(_pv_filter, "booleans", None)
                   if _pv_bools is not None:
                       _row_mask = [bool(b) for b in _pv_bools]
       ```
       `getattr` chains cover `_plot_view is None` and an `AllIndices` filter, both of which
       must yield `None`.

       Then add `row_mask=_row_mask` to the three `self._add_glyph(...)` calls — the
       `_RANGE_TYPES` branch at `:10031`, the `_UNIVARIATE_TYPES` branch at `:10036`, and the
       default branch at `:10063`. Pass it at all three even though only the default branch
       reaches a type in `_ROW_MASK_TYPES` today: the gate in `_add_glyph` makes the other
       two inert, and it means section 03 changes the frozenset and two mapper signatures and
       nothing else. Do **not** pass it to `self._add_pc_glyph(...)` at `:10027` or to
       `map_scatteri` / `map_pci_literal` / `map_function`: those are section 07's warning
       surface, not maskable layers.

    Do **not** change `self._register_view_filter(source, _pf, self._row_ids_for(_pdf))` at
    `:9991-9992`, and do not change the `len(_prev_bools) == len(_mask)` guard at `:9986`.
    Both are section 06 (item 7 and finding D3). The derivation above inherits whatever
    `_plot_view` carries, so it is exactly as correct as `:9986` is and no less.
  </action>
  <verify>`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_per_plot_qualifier_computed.py -q -k "lfit_with_per_plot_if or in_expr" 2>&1 | tail -3` prints `2 passed`. `python3 -m pytest test/test_per_plot_qualifier_computed.py -q 2>&1 | tail -3` shows everything passing except the two item-3 tests (`linked_by_panels`, `linked_graph_level_qualifier`) and possibly `row_mask_types_matches`, which task 02-07 closes; 2 skipped for statsmodels.</verify>
  <done>`(scatter mpg weight) (lfit mpg weight if foreign==1)` renders slope -.010425957587798849 and intercept 48.918297231743246 to 1e-6, over a grid spanning [1760, 3420], while the scatter still draws 74 points. `in 1/60` behaves identically (BR-01.4), and the command-level/per-plot intersection gives N=8, slope -.0096564106. BR-01.1, BR-01.2, BR-01.3 and BR-01.4 are satisfied for these twelve types.</done>
</task>

<task type="auto" id="02-07">
  <name>Close item 3 — linked `by()` and linked graph-level qualifiers, and re-baseline</name>
  <files>test/test_per_plot_qualifier_computed.py, dash_render.py</files>
  <action>
    Item 3 (finding F-A) is closed by 02-06's derivation, but it is a separate user-visible
    bug and needs its own proof and its own record. TR-01.6, BR-01.8, BR-01.11.

    1. **Confirm the two item-3 tests now pass** and that they failed for the right reason
       before 02-06. Re-run them against the pre-02-06 tree if the failure text was not
       captured in 02-01's commit message: every panel must have returned the same slope.
       If `test_linked_by_panels_do_not_all_draw_the_same_fit` passed before 02-06, it is
       vacuous — the panels were probably not actually linked. Fix the spec it builds until
       it fails pre-fix, then re-verify.

    2. **Add the coverage-reflection test** `test_row_mask_types_matches_the_mappers_that_accept_the_kwarg`
       if 02-01 left it as a stub: import `dash_render._ROW_MASK_TYPES`, walk it against a
       `{type: method}` map read from `GlyphMapper` by name, and assert every member's method
       has a `row_mask` parameter. Assert the twelve names of this section are a **subset**
       of `_ROW_MASK_TYPES`, never an equality, so section 03 can add `histogram`, `hist` and
       `kdensity` without editing this test.

    3. **Re-baseline pass.** Run the full pytest suite. Two classes of existing failure are
       expected and must be handled differently:
       - A test asserting a computed layer's values on a **linked** `by()` graph or a
         **linked** graph-level qualifier was encoding the bug. Update the expectation to the
         correct number and add a comment citing RESEARCH §1.9 finding F-A and the unlinked
         render that is the oracle. Candidates named in the phase test plan:
         `test_layout_facets.py`, `test_linking.py`, `test_linking_filters.py`,
         `test_statistical_truth.py`, `test_glyphs.py`.
         **Never weaken the new code to keep an old assertion green.**
       - Anything else is a real regression from this section. Fix the code, not the test.
       Record every re-baselined assertion in the commit message, one line each: file, test
       name, old number, new number, why the old one was wrong. Section 10 lifts this list
       into the CHANGELOG (discovery Q9); do not edit `CHANGELOG.md` here.

    4. **Leave the hand-off for section 10** in the module docstring of
       `test_per_plot_qualifier_computed.py`: the F-A paragraph, plus the before/after values
       for the headline case and for the linked-`by()` case.

    5. `dash_render.py` is in this task's file list only for regression fixes found in step 3.
       If the suite is clean apart from the re-baselines, do not touch it.

    Commit on `feature/batch4-interactive-layer`; report the merge command into local `main`,
    do not run it (rules 6 and 11).
  </action>
  <verify>`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_per_plot_qualifier_computed.py -q 2>&1 | tail -3` prints all tests passing with 2 skipped (`lowess`, both mask shapes). `python3 -m pytest test/ -q 2>&1 | tail -5` reports no failures and a passed count at or above section 01's recorded baseline in `.ultraplan/BASELINE.md`, plus this section's new tests. `git diff --stat main -- dash_render.py` shows changes confined to `_ROW_ID_COLUMN`'s neighbourhood, `_and_row_mask`, the twelve `map_*` methods, `_add_glyph` and `_make_figure_body`.</verify>
  <done>Item 1 (twelve of fourteen types) and item 3 are both closed and pinned by tests that fail on the pre-fix tree. A linked `by()` graph's panels each draw their own fit, equal panel-for-panel to the unlinked render; a linked graph-level qualifier reaches its computed layers. The full suite is green against section 01's baseline, every re-baselined assertion is explained in the commit message, and sections 03, 05, 06, 07 and 09 have a `row_mask` mechanism and a `_ROW_MASK_TYPES` set to extend.</done>
</task>
