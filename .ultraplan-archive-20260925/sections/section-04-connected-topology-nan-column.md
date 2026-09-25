# Section 04: Connected-topology layers — the NaN column

## Overview

A per-plot `if`/`in` on `line`, `tsline`, `connected`, `rline`, `rconnected` or `tsrline`
is inert today. The renderer builds a correct `BooleanFilter` mask, wraps it in a `CDSView`
and hands it to `fig.line(...)` — and Bokeh, whose `ConnectedXYGlyph` has exactly two
subclasses in 3.9 (`Line` and `Patch`), flags E-1024 `CDSVIEW_FILTERS_WITH_CONNECTED` and
BokehJS draws something that depends on the *shape* of the mask rather than on its content.
The browser silently under-draws, draws nothing, or draws everything. The user sees a line
over rows their qualifier excluded, with rc 0 and no warning.

This section replaces the view on those glyphs with a **per-layer NaN column written onto
the source the layer draws from**. A NaN in a `y` column breaks the line exactly there, so
the drawn topology is *gapped* — two runs of kept rows draw as two subpaths, not as one
line cutting across the excluded middle. No `CDSView` is attached, so E-1024 cannot arise.
The mask is attached to the row, not to a position, so it survives the sort inside
`map_line` and survives a callback that shortens the source.

If this section does not land, items 1-3's correct numbers are drawn on a shape that lies
about which rows produced them, and BR-01.7 fails outright.

**Test policy: task 04-01 writes every failing test for this section first.** Tasks 04-02
through 04-06 make them pass one behaviour at a time.

## Risk: [red] — the mechanism was chosen by browser measurement over a decision the plan originally shipped; it rewrites the glyph binding of six plot types and touches a shared `ColumnDataSource`

## Dependencies
- Depends on: section-01
- Blocks: section-06
- Parallel batch: 2

## Evidence

### E-1024 is real, narrow, and not a refusal

Bokeh 3.9.0, confirmed read-only in this repository's own interpreter:

```
bokeh 3.9.0
code  Error(code=1024, name='CDSVIEW_FILTERS_WITH_CONNECTED',
            description='CDSView filters are not compatible with glyphs with
                         connected topology such as Line or Patch')
ConnectedXYGlyph.__subclasses__()  ->  ['Line', 'Patch']
```

RESEARCH.md §2.1 gives the validator:

```python
@error(CDSVIEW_FILTERS_WITH_CONNECTED)
def _check_cdsview_filters_with_connected(self):
    if isinstance(self.glyph, ConnectedXYGlyph) and not isinstance(self.view.filter, AllIndices):
```

Two consequences the plan depends on:

1. **`VArea`, `HArea`, `Step`, `MultiLine` and `Patches` are not affected.** `map_area`
   draws `fig.varea` (`dash_render.py:3631`) and therefore **keeps its `CDSView`** and stays
   in section 02. It is not this section's work.
2. It is an *error-level validation issue*, not a refusal — `file_html()` succeeds, the
   `BooleanFilter` serialises unchanged, nothing raises. The defect is invisible from Python.

### What BokehJS actually draws — measured on a canvas, not inferred

RESEARCH.md §2.2. `GlyphRendererView.set_data` subsets the glyph arrays to the view, but
`_paint` then passes `all_indices.ones()` — **full-source-space** positions — into those
**subset-space** arrays. `sx[6]` is `undefined`, and `LineView`'s `gap(i) = i - iprev != 1`
test fires on every non-adjacent pair, turning `lineTo` into `moveTo`. 10 rows, 5 kept:

| kept positions | Line result | Patch result |
|---|---|---|
| `[0,1,2,3,4]` contiguous prefix | **all 5 — correct, by accident** | correct |
| `[3,4,5,6,7]` middle run | **2 of 5** | 2 of 5 |
| `[0,2,4,6,8]` alternating | **nothing drawn** | 3 of 5 |
| `[5,6,7,8,9]` suffix | **nothing drawn** | **nothing drawn** |

> **A `CDSView` filter on a `Line` is correct only when the kept rows are a contiguous
> prefix `0..k-1`.** Every other shape silently under-draws or draws nothing.

Corroborated by [bokeh#7070](https://github.com/bokeh/bokeh/issues/7070) (open since 2017)
and maintainer bryevdv in
[bokeh#9388](https://github.com/bokeh/bokeh/issues/9388#issuecomment-552147658): *"I'm not
actually sure that CDSView together with lines can be considered supported."* The user-guide
page on filtering never mentions the restriction, and the correct warning in the
`GlyphRenderer.view` docstring uses `.. note:` with one colon — malformed reST that has
never rendered. Trust the measurement.

### SUPERSEDED — do not build a private pre-filtered source

DISCOVERY Q3 answered *"private pre-filtered `ColumnDataSource`, with an explicit `link()`
guard test."* **RESEARCH.md §2.3 and §4.1 supersede that.** The head-to-head was run with
12 rows where the layer must draw `g=="A"` = rows `[0,1,2]` and `[6,7,8]` — two contiguous
runs, which is what a real group filter looks like. The correct answer is 2 subpaths,
6 points.

| approach | drawn | linked selection | `source.data` swap reaches it | hover |
|---|---|---|---|---|
| `CDSView` + `BooleanFilter` | **1 subpath, 3 pts — rows 6,7,8 silently lost** | yes | yes (filter goes stale) | correct |
| **(b) NaN in a per-layer column** | **2 subpaths, 6 pts ✓** | **yes, automatic** | **yes** | NaN rows unhittable |
| (a) private pre-filtered source | 1 subpath, 6 pts — **connects straight across the gap** | **no** | **no** | private-space |
| (c) `multi_line` per run | 2 subpaths, 6 pts ✓ | **no** — row identity gone | **no** | no row identity |

Confirmed by screenshot and by canvas trace. Rewriting `shared.data` changed the NaN line
correctly and left the private-source line and the `multi_line` **byte-for-byte unchanged** —
the callback never reached them. §2.5 adds the selection measurement: setting
`shared.selected.indices = [2,4,6]` faded the shared-source scatter to `rgba(31,119,180,0.1)`
while the private-source scatter stayed `#1f77b4`, **completely unaffected**.

The private source honours the qualifier in the data and **lies about it in the picture**,
and it costs `link()` and callback reach as well. The NaN column draws the correct gapped
topology, keeps both, and sidesteps E-1024 because no `CDSView` is set.

This also **dissolves D1** (RESEARCH §1.3): `map_line:3526` does
`dropna(...).sort_values(xvar)` and `:3527` wraps the result in a new CDS, while `:3547-3548`
attach a `BooleanFilter` indexed against the *original, unsorted* source — so even if Bokeh
honoured Line filters the mask would select the **wrong rows**. Under this decision no view
is attached, so the positional invalidity stops mattering. **But only if the NaN column is
written BEFORE the sort at :3526**, so the mask travels with the row.

### NaN semantics — reliable, and excluded from auto-ranging

RESEARCH.md §2.4. `y = [1, 2, NaN, 4, 5]` drew two subpaths breaking exactly at the NaN.
`LineView._paint` tests `!isFinite(sx_i + sy_i)` — **screen** coordinates, so anything
mapping to non-finite (for example ≤ 0 on a log axis) also breaks the line.

| y column | measured `y_range` |
|---|---|
| `[100,101,102,103,104]` | 99.8 → 104.2 |
| `[100,101,102,103,` **NaN** `]` | 99.85 → **103.15** — NaN ignored entirely |
| `[100,101,102,103,` **0.0** `]` | **-5.15** → 108.15 — the 0 stretches the range |

A NaN row neither draws nor stretches the range, and is unselectable and unhoverable. That
is the desired semantics, and it preserves RESEARCH §3.2 point 5 — the axes span the union
across layers, because an unqualified sibling still contributes all its rows.

The third row of that table is a **live hazard in this codebase**, and it is confirmed:

```python
11258        try:
11259            f = float(v)
11260            if math.isnan(f) or math.isinf(f):
11261                return None
```

`DashRenderer._to_serialisable` (`dash_render.py:11238-11264`) turns NaN into Python `None`,
and it is applied to every column of every callback snapshot at `dash_render.py:11829` and
`:11839`. The Bokeh docs quoted in §2.4 warn about exactly that value: *"Do not use the
native Python `None` object, because this will be evaluated as 0"*. Left alone, the first
filter-widget move would turn a qualified `rline`'s gap into a spike to zero **and** stretch
its y-range to -5.15. Task 04-06 fixes it.

### Two design constraints the measurement imposes

1. **One NaN column per layer.** NaN-ing a shared `y` would break every other glyph reading
   it. Two `line` layers over one source using `yA`/`yB` each drew their own correct subset
   (§2.4). Column names must therefore be unique per layer *and* per panel — a faceted
   linked graph gives every panel the same source (`dash_render.py:11465-11470`).
2. **NaN cannot draw an isolated point.** A run of length 1 has nothing to connect to, so it
   draws nothing at all. §2.4: pair the line with a `scatter` on the same NaN column.

### What this section does NOT buy back

`map_line` builds its own sorted `ColumnDataSource` (`dash_render.py:3521-3527`) and that
source is not in `self.sources`, so `all_graph_sources` (`:11882`) never reaches it. That is
**D2** (RESEARCH §1.3, §4.8) — *"private sources are invisible to the filter callback
generally"* — and the suite already pins it with a **strict xfail**:

```
test/test_filters.py:1360
    @pytest.mark.xfail(strict=True,
        reason="S13: map_line builds a derived sorted ColumnDataSource, but
                render() passes self.sources to the filter callback, so
                dragging a filter on a line chart changes nothing on screen.")
    def test_line_filter_updates_the_rendered_source(self):
```

The NaN column is written on the **shared** source and carried into `sorted_source` through
the `_cols` dict at `:3521-3524`, so the topology is correct and identity is preserved — but
`line`/`tsline`/`connected` gain no callback reach they did not have. `rline`, `rconnected`
and `tsrline` draw from `source` **directly** (`dash_render.py:5130-5141`) and therefore do
get full callback reach and linked selection. Say this in the section-10 changelog rather
than implying the line types gained something they did not. Because `xfail` is `strict=True`,
any change that accidentally moved `map_line` onto the shared source would turn that test
XPASS and fail the suite — treat it as a guard rail, not an obstacle.

### The existing coverage cannot see any of this

RESEARCH §1.9 F-B. `test/test_per_plot_qualifier_linking.py` is **entirely scatter-based** —
`_QUALIFIED` at `:94` is `{"type": "scatter", ...}` and every one of its 7 tests counts
`filt.booleans` through the `_visible` helper at `:83-91`. On a `Line` that helper reports a
layer as correctly masked while the browser draws the unfiltered line. The same trap lives in
`test/test_varlist_expansion.py:101`.

> **Every assertion this section adds compares the layer's own source values against an
> independently computed subsample. Never a view's booleans.** A `line` test that reads
> `renderer.view.filter.booleans` certifies nothing — after this section there is no view to
> read.

### Requirements discharged

Phase work item **4**, requirement **TR-01.4** (resolution 1, "NaN-break a masked copy of
the columns on the shared source — Preferred"), satisfying **BR-01.7** (no E-1024 for
`line`, `connected`, `tsline`, `rline`, `rconnected`), **BR-01.11** and **TR-01.15**
(`link()` is not regressed — nothing moves onto a private source that was not already there),
**BR-01.5** (no mark drawn for a row the layer excluded), **BR-01.12** / **TR-01.14** (no
qualifier failure may drop a layer), and **BR-01.13** (test first).

## TDD test stubs

All of these live in a new file, `test/test_per_plot_qualifier_connected.py`, written whole
in task 04-01. Each must FAIL on the pre-fix tree.

- **Test: `test_no_e1024_for_any_connected_type`** — for each of `line`, `tsline`,
  `connected`, `rline`, `rconnected`, `tsrline`, render a graph whose layer carries
  `if_expr="foreign==1"`, then run `bokeh.core.validation.check_integrity` over the rendered
  models and assert no issue with `code == 1024` / `name == "CDSVIEW_FILTERS_WITH_CONNECTED"`.
  Pre-fix: fails on every one of the six. (BR-01.7)
  *Mutation that must kill it:* re-add `_line_kwargs["view"] = view` in `map_line`.
- **Test: `test_line_values_equal_independent_subsample`** — read the line renderer's own
  `data_source.data[renderer.glyph.y.field]`, and compare the finite entries against a
  subsample computed in the test body from the input DataFrame (`df.loc[df.foreign == 1, "mpg"]`
  sorted by `weight`). Assert equality element-wise, and assert the non-finite entries sit at
  exactly the excluded rows. **Do not read `renderer.view`.** Pre-fix: fails, because the
  column is the unmasked `yvar`.
  *Mutation:* drop the `np.where` and return `yvar`; or invert the mask.
- **Test: `test_gap_topology_has_the_expected_number_of_subpaths`** — build a frame whose
  qualifier keeps two separated runs (the §2.3 shape: rows `[0,1,2]` and `[6,7,8]` of 12),
  count maximal runs of finite values in the drawn column, assert exactly 2 runs totalling
  6 points. Pre-fix: the column has 12 finite values and 1 run.
- **Test: `test_gap_follows_the_row_not_the_position`** — supply x values in *descending*
  order so `map_line:3526`'s `sort_values(xvar)` genuinely reorders, then assert the NaN
  positions in the drawn column line up with the excluded rows *after* sorting. This is the
  D1 test.
  *Mutation:* write the NaN column after the sort instead of before — the test must die.
- **Test: `test_two_qualified_line_layers_do_not_corrupt_each_other`** — two `line` layers on
  one graph with different qualifiers. Assert the two renderers reference two **different**
  y-column names, that each column matches its own subsample, and that `source.data[yvar]`
  (the original) still holds all rows with no NaN introduced.
  *Mutation:* use a single fixed column name for every layer.
- **Test: `test_unqualified_connected_layers_are_byte_identical`** — render the same six plot
  types with no qualifier and assert: no column whose name starts with the mask prefix exists
  on any source, each line renderer's `glyph.y.field` is still the plain `yvar`, and the
  renderer count per figure is unchanged from a baseline list recorded in the test body. This
  is the no-visual-regression guard for the isolated-point scatter.
- **Test: `test_isolated_kept_row_is_still_drawn`** — a qualifier that keeps exactly one row
  with excluded neighbours on both sides. Assert a second renderer exists whose y column has
  exactly one finite value, at that row, and that its marker colour equals the line's
  `line_color`. Pre-fix: no such renderer, and the line draws nothing at all for that row.
  *Mutation:* delete the pairing scatter.
- **Test: `test_connected_does_not_double_up_the_isolated_scatter`** — `connected` and
  `rconnected` already draw a scatter on every kept row, so assert the renderer count for a
  qualified `connected` layer is exactly 2 (line + scatter), not 3.
- **Test: `test_rline_keeps_the_shared_source`** — for `rline`, assert
  `renderer.data_source is dr.sources["g1"]` for both boundary renderers, and that
  `renderer.view.filter` is `AllIndices` or the view is absent. This is the BR-01.11 /
  TR-01.15 guard in its post-supersession form: it asserts the layer stayed *inside* `link()`,
  which is what the old "private-source guard test" was for.
- **Test: `test_snapshot_preserves_nan_not_none`** — build a dashboard with a filter widget
  and a qualified `rline`, then read `dr.filter_callbacks[0].args["all_graph_sources_orig"]`
  and assert the mask column's excluded entries are `float('nan')` (`math.isnan`), **not**
  `None`. Pre-fix: they are `None`, which BokehJS evaluates as 0.
  *Mutation:* restore the `_to_serialisable` call for mask columns.
- **Test: `test_qualified_line_does_not_stretch_the_range`** — put the dataset's extreme y
  value on an excluded row and assert it is absent from the finite entries of the drawn
  column, so it cannot reach `DataRange1d`. (§2.4's 99.85→103.15 measurement, in unit form.)
- **Test: `test_area_still_uses_a_cdsview`** — a scope guard against over-reach: a qualified
  `area` layer must still carry a `CDSView` with a `BooleanFilter`, because `VArea` is not a
  `ConnectedXYGlyph`. Owned by section 02; asserted here so this section cannot quietly take
  it over.

## Tasks

<task type="auto" id="04-01">
  <name>Write the failing connected-topology test module</name>
  <files>test/test_per_plot_qualifier_connected.py</files>
  <action>
    Create `test/test_per_plot_qualifier_connected.py`. Follow the import and helper shape of
    `test/test_per_plot_qualifier_linking.py:24-40` — `sys.path.insert` for both the repo root
    and `test/`, then `import dash_render as dr` and `from conftest import make_data_json`.
    Use `conftest.make_dr` (`test/conftest.py:246`) where a rendered `DashRenderer` is enough
    and the local `_render`-style tmp_path builder where a link spec or filter widget is
    needed.

    Define one module-level frame with a deliberately non-prefix mask shape, so the test
    cannot pass by the `[0..k-1]` accident recorded in RESEARCH §2.2:

        _DF = pd.DataFrame({
            "mpg":    [22., 18., 25., 30., 21., 19., 27., 16., 24., 20., 31., 17.],
            "weight": [2930., 3350., 2200., 1800., 3000., 3100.,
                       2050., 3800., 2400., 3500., 1900., 4100.],
            "grp":    [1., 1., 1., 0., 0., 0., 1., 1., 1., 0., 0., 0.],
        })

    `grp==1` keeps rows `[0,1,2]` and `[6,7,8]` — the two-run shape of §2.3, for which a
    CDSView draws 1 subpath of 3 points.

    Write a helper `_drawn_y(renderer)` that returns
    `np.asarray(renderer.data_source.data[renderer.glyph.y.field], dtype=float)`, and a helper
    `_runs(arr)` that returns the list of maximal runs of finite values. Put a module docstring
    on the file stating, in one paragraph, that **no assertion in this file may read
    `renderer.view.filter.booleans`**, because after this section there is no view on a
    connected glyph and because that helper reports a computed layer as fully visible whatever
    it drew (RESEARCH §1.9 F-B, `test/test_varlist_expansion.py:101`).

    Write every test named in the "TDD test stubs" section above. Mark none of them xfail —
    they are meant to be red.

    Do not modify `test/test_per_plot_qualifier_linking.py`, `test/test_filters.py`,
    `test/test_glyphs.py` or any other existing file.
  </action>
  <verify>`python3 -m pytest test/test_per_plot_qualifier_connected.py -q` runs and reports 12 failed, 0 passed. Then `python3 -m pytest test/test_per_plot_qualifier_connected.py -q -k e1024 -x` and read the failure text: it must name `CDSVIEW_FILTERS_WITH_CONNECTED` / code 1024, not an import error, a fixture error or a `KeyError`. A test that errors rather than fails is not yet a failing test.</verify>
  <done>A new red test module exists that pins the gapped topology, the E-1024 absence, the per-layer column isolation, the isolated-point case, the snapshot NaN, and the `area` scope guard. Nothing in the product code has changed.</done>
</task>

<task type="auto" id="04-02">
  <name>The NaN-column mechanism and the row_mask channel</name>
  <files>dash_render.py</files>
  <action>
    **(a) Module constants.** Next to `_ROW_ID_COLUMN = "__dash_row__"` at `dash_render.py:591`,
    add:

        _NAN_MASK_PREFIX = "__dash_qmask_"
        # ConnectedXYGlyph has exactly two subclasses in Bokeh 3.9 -- Line and
        # Patch -- so a CDSView filter on these types raises E-1024 and BokehJS
        # draws a shape that depends on the mask's shape, not its content.
        # These types take a per-layer NaN column instead of a view.
        # VArea is NOT a ConnectedXYGlyph: `area` keeps its CDSView.
        _CONNECTED_TOPOLOGY_TYPES = frozenset({
            "line", "li", "tsline", "connected", "rline", "rconnected", "tsrline",
        })

    `tsline` delegates to `map_line` (`:5830`) and `tsrline` delegates to `map_rline`
    (`:5859`), so both are covered by the delegation and both are listed for the benefit of
    callers that test membership.

    **(b) Two helpers on `GlyphMapper`,** placed immediately before `map_scatter` (`:3407`).

        def _resolve_row_mask(self, row_mask, view, n):
            """Return a list[bool] of length *n*, or None for no restriction."""

    Rules, in order: if `row_mask` is not None and `len(row_mask) == n`, return
    `[bool(b) for b in row_mask]`. Otherwise, if `view` is not None, read
    `getattr(view, "filter", None)`: a `BooleanFilter` whose `booleans` has length `n` becomes
    that list; an `IndexFilter` becomes a length-`n` list true at its `indices`; `AllIndices`,
    `None`, or any length mismatch returns `None`. Never raise — a connected mapper is called
    from `_add_glyph` (`:10412`, `:10421`), **outside** the `try/except` at `:9993`, so a raise
    here would lose the layer and violate BR-01.12 / TR-01.14. On a length mismatch,
    `warnings.warn` in the existing format (`"dash: per-plot qualifier on layer ... could not
    be applied ..."` at `:9994-9997`) and return `None`.

        def _nan_masked_column(self, source, yvar, mask, label=""):
            """Write a per-layer NaN copy of *yvar* onto *source*; return its name."""

    Behaviour: `if mask is None: return yvar`. Otherwise allocate a name from a per-instance
    counter — initialise `self._nan_mask_seq = 0` in `GlyphMapper.__init__` — as
    `f"{_NAN_MASK_PREFIX}{self._nan_mask_seq:03d}_{label or yvar}"`, then increment. A counter,
    not `(graph name, layer index)`: under `link()` a faceted graph gives **every panel the
    same source** (`:11465-11470`), so a name keyed by layer index would have one panel's mask
    overwrite another's. Write
    `source.data[col] = np.where(np.asarray(mask, dtype=bool),
                                 np.asarray(source.data[yvar], dtype=float), np.nan)`
    and return `col`. Assign a **float64 ndarray**, not a list — task 04-06 depends on the
    dtype surviving into the snapshot. Sanitise `label` to `[A-Za-z0-9_]` before use.

    **(c) The `row_mask` channel.** Add `row_mask=None` to the signature of `_add_glyph`
    (`:10334-10345`) and forward `row_mask=row_mask` on the range dispatch at `:10412` and on
    both standard dispatch calls at `:10419` and `:10421`. In `_make_figure_body`, add
    `row_mask=_plot_row_mask` to the `_add_glyph` calls at `:10031`, `:10036` and `:10063`,
    where `_plot_row_mask` is computed immediately after the per-plot block closes at `:9998`:

        _plot_row_mask = None
        if _plot_view is not None:
            _pvf = getattr(_plot_view, "filter", None)
            _pvb = getattr(_pvf, "booleans", None)
            if _pvb is not None:
                _plot_row_mask = [bool(b) for b in _pvb]

    Reading `_plot_view` rather than the per-plot branch's `_mask` is deliberate: it also
    carries a **facet** panel's mask, so a `line` layer inside a `by()` panel gets the same
    treatment. That is finding F-A (RESEARCH §1.9) as it applies to connected glyphs.

    **Merge note.** Section 02 specifies the *identical* `row_mask=` addition to `_add_glyph`
    and the same three dispatch-site edits, and runs in the same parallel batch. Use exactly
    the parameter name `row_mask`, exactly the source `_plot_view.filter.booleans`, and exactly
    these three call sites. If section 02 landed first, grep before editing and leave its
    version in place; if a textual conflict appears at `:10412`/`:10419`/`:10421`, keep one
    copy.

    Do not change any mapper body in this task.
  </action>
  <verify>`python3 -c "import dash_render as d, inspect; print(d._NAN_MASK_PREFIX); print(sorted(d._CONNECTED_TOPOLOGY_TYPES)); print(inspect.signature(d.DashRenderer._add_glyph)); print(hasattr(d.GlyphMapper, '_nan_masked_column'), hasattr(d.GlyphMapper, '_resolve_row_mask'))"` prints `__dash_qmask_`, the seven type names, a signature containing `row_mask=None`, and `True True`. `python3 -m pytest test/test_per_plot_qualifier_connected.py -q` still reports 12 failed (no mapper consumes the channel yet). `python3 -m pytest test/test_glyphs.py test/test_filters.py -q` is unchanged from the section-01 baseline.</verify>
  <done>The renderer can compute a per-layer NaN column and hand any layer's mask to its mapper. No glyph binding has changed yet, so rendered output is byte-identical.</done>
</task>

<task type="auto" id="04-03">
  <name>map_line: NaN column before the sort, no view on the Line</name>
  <files>dash_render.py</files>
  <action>
    **`map_line` (`:3486`).** Add `row_mask=None` to the signature after `view=None` (`:3493`).
    At the top of the body, before the `_cols` dict at `:3521`:

        _n = len(source.data.get(xvar, []))
        _mask = self._resolve_row_mask(row_mask, view, _n)
        _ycol = self._nan_masked_column(source, yvar, _mask, label=yvar)

    Then extend the `_cols` dict at `:3521-3524` so the mask column travels into the sorted
    frame: after the `_mlab` block, add `if _ycol != yvar: _cols[_ycol] = source.data[_ycol]`.
    **This is the whole of D1's resolution** — the column is built in source order and carried
    through `df.dropna(...).sort_values(xvar)` at `:3526`, so the mask stays attached to the row
    rather than to a position. Leave `dropna(subset=[xvar, yvar])` exactly as it is: it must
    keep dropping on the *unmasked* `yvar`, or every excluded row would be deleted from the
    sorted frame and the gap would close.

    In `_line_kwargs` at `:3529-3537`, change `y=yvar` to `y=_ycol`, and **delete the
    `if view is not None: _line_kwargs["view"] = view` block at `:3547-3548` outright.** A view
    is never attached to a `fig.line` again; the restriction now travels in the column. Replace
    those two lines with a comment recording why, citing E-1024 and RESEARCH §2.2's table.

    After `r = fig.line(**_line_kwargs)` at `:3549`, stash the handle other sections need:

        r._dash_nan_column = _ycol if _ycol != yvar else ""

    (Same plain-attribute pattern as `_dash_agg_config` at `:4695`.) Section 05 reads it to
    plot its `text` glyph against a column that subsets itself for free (RESEARCH §2.6);
    section 06 reads it to know which columns a callback must carry.

    Change the `_apply_mlabel_opts` call at `:3556` to pass `_ycol` in place of `yvar` as the
    y argument. Leave `self._hover_tool(yvar, xvar, renderers=[r])` at `:3557` on `yvar`: the
    tooltip should name the user's variable, and NaN rows are unhittable anyway (§2.3).

    **`map_connected` (`:3560`).** Add `row_mask=None` to the signature and forward
    `row_mask=row_mask` to both sub-calls at `:3585` and `:3587`. Keep `view=view` on both:
    `map_line` now converts it to a mask and ignores it as a view, while `map_scatter`'s
    `Scatter` is not a `ConnectedXYGlyph` and filters correctly (§2.2 applies only to
    `Line`/`Patch`).

    **`map_tsline` (`:5805`).** Add `row_mask=None` to the signature and forward it on the
    delegation at `:5830`.
  </action>
  <verify>`python3 -m pytest test/test_per_plot_qualifier_connected.py -q -k "e1024 or subsample or subpaths or follows_the_row or corrupt_each_other or does_not_stretch"` — all pass for `line`, `tsline` and `connected`; the `rline`/`rconnected` parameter cases of `test_no_e1024_for_any_connected_type` still fail. `python3 -m pytest test/test_glyphs.py test/test_axis_options.py test/test_color_alias.py test/test_jitter.py test/test_phase4_plots.py -q` matches the section-01 baseline. `python3 -m pytest test/test_filters.py -q` still reports `test_line_filter_updates_the_rendered_source` as xfailed, never xpassed — an XPASS there means `map_line` was accidentally moved onto the shared source.</verify>
  <done>`line`, `tsline` and the line half of `connected` draw a gapped, correctly-masked line from a column built before the sort; no `CDSView` reaches a `Line`; each renderer advertises its mask column as `_dash_nan_column`.</done>
</task>

<task type="auto" id="04-04">
  <name>map_rline and map_rconnected: two NaN columns on the shared source</name>
  <files>dash_render.py</files>
  <action>
    **`map_rline` (`:5106`).** Add `row_mask=None` after `view=None` (`:5114`). Before
    `_rl1_kwargs` at `:5130`:

        _n = len(source.data.get(xvar, []))
        _mask = self._resolve_row_mask(row_mask, view, _n)
        _y1col = self._nan_masked_column(source, y1var, _mask, label=y1var)
        _y2col = self._nan_masked_column(source, y2var, _mask, label=y2var)

    Two calls, two columns — one per drawn series, per the one-column-per-layer constraint in
    §2.4. Set `y=_y1col` in `_rl1_kwargs` (`:5130`) and `y=_y2col` in `_rl2_kwargs` (`:5134`),
    and **delete the whole `if view is not None:` block at `:5137-5139`**, which today sets
    `view` on both range lines — two E-1024s from a single layer. Replace it with the same
    explanatory comment as in 04-03.

    After `r2 = fig.line(**_rl2_kwargs)` at `:5141`, set `r1._dash_nan_column = _y1col if
    _y1col != y1var else ""` and the matching line for `r2`. Change the `_apply_mlabel_opts`
    call at `:5144` to pass `_y2col` in place of `y2var`.

    Unlike `map_line`, these two renderers draw from `source` **directly** — the graph's shared
    `ColumnDataSource`. So for `rline` the NaN column delivers the full §2.3 result: correct
    gapped topology, linked selection automatically, and the filter callback reaches the column
    because the callback rewrites that very source. This is the one place in the section where
    "callback reach: yes" is literally true, and task 04-06 is what makes it survive.

    **`map_rconnected` (`:5147`).** Add `row_mask=None` to the signature and forward
    `row_mask=row_mask` to all four delegations at `:5172-5175` — the two `map_line` calls take
    it as the mask, the two `map_scatter` calls keep using `view=view`.

    **`map_tsrline` (`:5832`).** Add `row_mask=None` to the signature and forward it on the
    delegation at `:5859`.
  </action>
  <verify>`python3 -m pytest test/test_per_plot_qualifier_connected.py -q -k "e1024 or rline_keeps_the_shared_source"` passes for all six types. `python3 -c "
import sys; sys.path.insert(0,'test'); sys.path.insert(0,'.')
import pandas as pd
from bokeh.core.validation import check_integrity
from conftest import make_dr
df = pd.DataFrame({'lo':[1.,2,3,4,5,6],'hi':[2.,3,4,5,6,7],'x':[1.,2,3,4,5,6],'g':[1.,1,0,0,1,1]})
d = make_dr([{'type':'rline','yvar1':'lo','yvar2':'hi','xvar':'x','options':{},'if_expr':'g==1'}], df)
iss = check_integrity(list(d.figures.values()))
print([e.code for e in iss.error])"` prints `[]`. `python3 -m pytest test/test_phase4_plots.py test/test_every_plot_type_draws.py -q` matches the section-01 baseline.</verify>
  <done>All six connected-topology types honour a qualifier. `rline`, `rconnected` and `tsrline` do it on the shared source, so they keep `link()` and linked selection; no rendered document carries E-1024 from dash's own qualifier mechanism (BR-01.7).</done>
</task>

<task type="auto" id="04-05">
  <name>Pair the line with a scatter so isolated kept rows are visible</name>
  <files>dash_render.py</files>
  <action>
    A run of length 1 has nothing to connect to, so a NaN-masked line draws **nothing** for an
    isolated kept row (RESEARCH §2.4). Fix it without changing what an unqualified plot looks
    like.

    Add a third `GlyphMapper` helper beside the two from 04-02:

        def _isolated_points_column(self, source, ycol):
            """Column holding only the finite values with no finite neighbour."""

    Read `np.asarray(source.data[ycol], dtype=float)` **in that source's own row order** — for
    `map_line` that is the post-sort order of `sorted_source`, which is the order BokehJS
    connects in. A position is isolated when its value is finite and both neighbours are
    non-finite or out of bounds. Return `None` when there are none; otherwise write a column
    named `f"{ycol}__pts"` holding the value at isolated positions and NaN elsewhere, and
    return its name.

    Add `pair_isolated: bool = True` to `map_line`'s signature. In `map_line`, after
    `sorted_source` is built at `:3527` and after `r = fig.line(...)` at `:3549`:

        if pair_isolated and _ycol != yvar:
            _pts = self._isolated_points_column(sorted_source, _ycol)
            if _pts:
                fig.scatter(x=xvar, y=_pts, source=sorted_source,
                            marker="circle",
                            size=max(3.0, float(_line_kwargs["line_width"]) * 2.0),
                            fill_color=_line_kwargs["line_color"],
                            line_color=_line_kwargs["line_color"])

    Three guards, all load-bearing:
    - `_ycol != yvar` — an **unqualified** line never gains a renderer. This is what
      `test_unqualified_connected_layers_are_byte_identical` pins.
    - `if _pts` — a qualified line whose kept rows form runs of length ≥ 2 never gains one
      either. The scatter appears only where the line physically cannot draw.
    - `pair_isolated` — `map_connected` (`:3585`) and `map_rconnected` (`:5172`, `:5174`) pass
      `pair_isolated=False`, because they already draw a scatter over every kept row through
      `map_scatter`'s `view`. Without this, a qualified `connected` layer would carry three
      renderers and a doubled marker.

    Apply the same block to `map_rline` for `_y1col` and `_y2col`, using each line's own
    `line_color` and `line_width` from `_rl1_kwargs` / `_rl2_kwargs`; `map_rline` gets no
    `pair_isolated` parameter of its own, since `map_rconnected` delegates to `map_line`, not
    to `map_rline`.

    Do not touch `self.scheme` for the marker: reuse the colour and width already resolved into
    the line kwargs, so a scheme change cannot make the paired marker disagree with its line.
  </action>
  <verify>`python3 -m pytest test/test_per_plot_qualifier_connected.py -q -k "isolated or byte_identical"` passes. Then mutate: comment out the `fig.scatter(...)` call, re-run `-k isolated`, and confirm `test_isolated_kept_row_is_still_drawn` FAILS; revert. `python3 -m pytest test/test_glyphs.py test/test_every_plot_type_draws.py test/test_html_verification.py -q` matches the section-01 baseline — an unqualified plot must gain zero renderers.</verify>
  <done>A qualifier that isolates a single row still puts that row on screen, and a plot with no qualifier renders exactly the glyphs it did before this section.</done>
</task>

<task type="auto" id="04-06">
  <name>Keep NaN as NaN through the callback snapshot, and sweep the document for E-1024</name>
  <files>dash_render.py</files>
  <action>
    **(a) The `None`-is-zero defect.** `DashRenderer._to_serialisable` (`:11238-11264`) returns
    `None` for NaN at `:11260-11261`, and it is applied per value to every snapshot column at
    `:11829` and `:11839`. Bokeh's own documentation, quoted in RESEARCH §2.4, warns: *"Do not
    use the native Python `None` object, because this will be evaluated as 0"*, and §2.4's
    third measured row shows a `0.0` in place of a NaN stretching `y_range` from
    `99.85 → 103.15` to `-5.15 → 108.15`. So after the first filter move a qualified `rline`
    would draw a spike to zero instead of a gap.

    At `:11826-11830`, change the `_orig_data` loop to:

        for _col, _arr in fsource.data.items():
            if str(_col).startswith(_NAN_MASK_PREFIX):
                _orig_data[_col] = np.asarray(_arr, dtype=float)
            else:
                _orig_data[_col] = [DashRenderer._to_serialisable(v) for v in _arr]

    Apply the identical branch inside the `_snapshot_of` comprehension at `:11838-11841`,
    rewriting it as an explicit loop. A float64 ndarray is the only representation measured to
    carry NaN intact; a Python list of floats is not, because `_to_serialisable` is what
    flattens it.

    **(b) Prove the round trip, do not assume it.** The verify step below serialises a real
    document and reads the value back, because the claim "Bokeh transports a float64 ndarray
    without flattening NaN" is a property of the serializer, not something this plan asserts
    from memory. If the round trip shows `null`, stop and report it rather than proceeding —
    the fallback is to emit a parallel boolean keep-column and have `_FILTER_JS` rebuild the
    NaN column client side, which is a larger change and belongs to section 06.

    **(c) Document-level sweep.** Add a `DashRenderer` helper `_assert_no_connected_view()`
    called at the end of `render()`, iterating `fig.renderers` for every figure and warning —
    in the `:9994-9997` format — if any renderer whose `glyph` is a Bokeh `Line` or `Patch`
    carries a `view` whose `filter` is not `AllIndices`. This is a cheap standing guard against
    a future mapper re-introducing the defect the section just removed; it warns, it never
    raises, so BR-01.12 holds.

    **(d) Re-run the affected suites** and reconcile every delta against the section-01
    baseline. Nothing in this section may change a passing count except by turning
    `test_per_plot_qualifier_connected.py` green.
  </action>
  <verify>`python3 -m pytest test/test_per_plot_qualifier_connected.py -q` reports 12 passed, 0 failed. Round-trip proof: `python3 -c "
import sys, json; sys.path.insert(0,'test'); sys.path.insert(0,'.')
import numpy as np, pandas as pd
from bokeh.embed import file_html
from bokeh.resources import CDN
from conftest import make_dr
df = pd.DataFrame({'lo':[1.,2,3,4,5,6],'hi':[2.,3,4,5,6,7],'x':[1.,2,3,4,5,6],'g':[1.,1,0,0,1,1]})
d = make_dr([{'type':'rline','yvar1':'lo','yvar2':'hi','xvar':'x','options':{},'if_expr':'g==1'}], df,
            filters=[{'varname':'x','type':'range','exclude':[],'label':''}])
snap = d.filter_callbacks[0].args['all_graph_sources_orig'][0]
col = [c for c in snap.data if c.startswith('__dash_qmask_')][0]
vals = list(snap.data[col])
print('has None:', any(v is None for v in vals))
print('has NaN :', any(isinstance(v,float) and np.isnan(v) for v in vals))"` prints `has None: False` and `has NaN : True`. Then `python3 -m pytest test/ -q -m 'not serve'` and diff the pass/fail/skip counts against `.ultraplan/BASELINE.md`: the only change is +12 passed. `test/test_filters.py::test_line_filter_updates_the_rendered_source` is still xfailed, not xpassed.</verify>
  <done>A qualified connected layer's gap survives a filter-widget move as a gap, not as a spike to zero; the renderer warns if any `Line` or `Patch` ever carries a non-trivial `CDSView` again; the full pytest suite is green against the section-01 baseline with 12 new passes. Section 06 can now build on `_dash_nan_column` and on a snapshot that carries the mask column intact.</done>
</task>
