# Section 03: `histogram` and `kdensity` — the two exceptions

## Overview

Section 02 gives twelve of the fourteen computed mappers a `row_mask=` keyword that is ANDed
into the NaN mask they already build, two inserted lines each. `map_histogram` (:4636) and
`map_kdensity` (:4806) cannot take that treatment. Both read their data through
`_extract_finite` (:964-995), which drops `None` and `NaN` *inside* the function and returns a
**shorter array with no positional correspondence to the source column**. A mask applied after
that call would land on the wrong observations. The mask has to land **at** the call — at
:4666 for the histogram and :4830 for the density — so this section adds an optional `mask=`
parameter to `_extract_finite` itself and threads `row_mask=` through both mappers.

Everything downstream then becomes subset-relative for free and matches Stata: the bin rule
`_stata_bin_count` reads `len(arr)`, `_histogram_grid` (:4668) rebuilds the edges from the
subset's own min and max, `_histogram_heights` (:4670) renormalises a density against the
subset's total, `_stata_kde_bandwidth` (:4848) re-derives the bandwidth, and the evaluation
span at :4870 re-centres on the subset. Both mappers also put `options` **before** `xvar` in
their signatures and `_add_glyph` already special-cases them at :10418-10419, so the plumbing
is its own task. If this section does not land, `dash (scatter mpg weight) (histogram mpg if
foreign==1)` draws Stata's 8-bin full-sample histogram where Stata draws 4 bins.

**Convention (project rule 8): task 03-01 writes every failing test for this section.** Tasks
03-02 through 03-05 each name which of those tests must turn green, and none of them may add a
new assertion of its own.

## Risk: [yellow] — the mask must be applied inside a shared helper with four call sites that the emitted server app also copies

`_extract_finite` is called from exactly four places — `map_histogram` (:4666),
`map_kdensity` (:4830) and two filter-bound builders (:7731, :7809, both with
`allow_datetime=True`) — and it is **copied verbatim into the generated `bokeh serve` app**
by the `inspect.getsource` loop at :12392-12407 (the name is in the tuple at :12393). A new keyword with a `None` default changes no existing caller and no emitted
call site, but the emitted app's source text changes, so the server suite is part of this
section's verification even though this section writes no server code.

## Dependencies

- Depends on: section-01, section-02
- Blocks: section-06
- Parallel batch: 3

## Evidence

### E1 — `_extract_finite` destroys positional correspondence (RESEARCH §1.2)

`dash_render.py:964-995`, verbatim tail:

```python
  994    arr = np.array([v for v in col if v is not None], dtype=float)
  995    return arr[~np.isnan(arr)]
```

Two length-changing steps, in sequence. RESEARCH §1.2 states the consequence directly:

> **`map_histogram` and `map_kdensity` are the two exceptions.** `_extract_finite`
> (:964-995) drops `None`/NaN internally and returns a **shorter array with no positional
> correspondence**, so a mask cannot be applied after the call. […] The mask must be applied
> **at** :4666 / :4830 — either by adding an optional `mask=` to `_extract_finite` or by
> zipping `source.data[yvar]` against the mask inline. Both also need the agg-config change
> in §1.5, or the bars jump back to the full sample on the first widget move. Note both put
> `options` **before** `xvar` in their signatures, and `_add_glyph` already special-cases
> them at :10418-10419.

Confirmed read-only at HEAD. `map_histogram`'s signature is
`(self, fig, source, yvar, options=None, xvar=None, view=None, color_idx=0)` — `options` at
position 4, `xvar` at position 5, `view` accepted and never referenced. `map_kdensity`
(:4806-4815) is identical in shape. The new keyword therefore goes **after `view=`**, as
`row_mask=None`, matching section 02's name so one helper name covers all fourteen mappers.

The dispatch special case, `dash_render.py:10415-10421`:

```python
10415        fn = dispatch.get(pt)
10416        if fn is not None:
10417            # histogram and kdensity are univariate — no xvar positional arg
10418            if pt in ("histogram", "hist", "kdensity"):
10419                fn(fig, source, yvar, options, view=view, color_idx=color_idx)
10420            else:
10421                fn(fig, source, yvar, xvar, options, view=view, color_idx=color_idx)
```

`_UNIVARIATE_TYPES = frozenset({"histogram", "hist", "kdensity"})` is defined at
`dash_render.py:9920` and routes these two layers to `_add_glyph` at :10036-10037.

### E2 — the mask that has to be threaded is already computed (RESEARCH §1.1)

`DashRenderer._make_figure_body:9951-9998`. `source_for_plot = source` (:9955) is never
reassigned; the layer always draws from the graph's shared `ColumnDataSource`. `_mask` at
:9979-9988 is one bool per row of that source, already intersected with any facet view, and it
is in scope at the dispatch call at :10036 as `_plot_view.filter.booleans`. Identity is
`_ROW_ID_COLUMN = "__dash_row__"` (:591).

### E3 — Stata's own numbers, reproduced exactly from the committed fixture

Ground truth for this section (`sysuse auto`, N=74; `foreign==1`: 22 observations, which
RESEARCH §3.1 records as occupying observations 53-74 because auto.dta ships domestic-first):

| quantity | full sample | `if foreign==1` |
|---|---|---|
| histogram bins | **8** | **4** |
| histogram first/last bin centre | **13.8125 / 39.1875** | **17.375 / 37.625** |
| kdensity grid span | **12 → 41** | **14 → 41** |
| kdensity mean density over that grid | **.0331** | **.0346** |

These reproduce **exactly** from `test/fixtures/data/auto.csv` (74 rows, `mpg` and `weight`,
already committed and already the real auto data — row 1 is `22,2930`) using the package's own
`_stata_bin_count`, `_stata_kde_bandwidth` and `_kde_curve`, with
`foreign = [0]*52 + [1]*22`:

```
full n=74  bins=8  width=3.625  centres 13.8125 … 39.1875
           edges [12.0, 15.625, 19.25, 22.875, 26.5, 30.125, 33.75, 37.375, 41.0]
           counts [10, 25, 13, 15, 6, 1, 3, 1]
sub  n=22  bins=4  width=6.75   centres 17.375  … 37.625
           edges [14.0, 20.75, 27.5, 34.25, 41.0]
           counts [5, 11, 3, 3]
           density tops [0.03367003, 0.07407407, 0.02020202, 0.02020202]

kdensity   full  bw = 1.9746142001   sub  bw = 2.516773101
           mean density on the DATA-RANGE grid: full .033121   sub .034627
```

`_stata_kde_bandwidth`'s own docstring records that `kdensity mpg` on `sysuse auto` returns
`r(bwidth) = 1.9746142001` and that this function returns the same to ten decimal places, so
the full-sample column is a re-derivation of a number Stata already agreed with. The
subsample column (.034627) matches the brief's Stata measurement **.0346** to three
significant figures. `_stata_bin_count(74) = 8` and `_stata_bin_count(22) = 4` follow from the
rule the function documents, `k = min(sqrt(n), 10*ln(n)/ln(10))` truncated.

**One honest caveat the tests must respect.** dash's `map_kdensity` does not evaluate on
Stata's grid. Line :4870 reads

```python
4870        _lo, _hi = arr.min() - 3 * bw, arr.max() + 3 * bw
```

so dash extends three bandwidths past the data on each side, while Stata's grid is the data
range. Measured on this fixture, dash's own grid goes `6.076157 → 46.923843` on the full
sample and `6.449681 → 48.550319` on the subsample — the **upper** end moves *outward* under
the qualifier because the bandwidth grew from 1.9746 to 2.5168 faster than the data max fell
(it did not fall: 41 is a foreign car). So "the grid shrinks" is a **false** assertion for
dash and must not be written. The correct assertions are (a) the endpoints equal
`arr_sub.min() - 3*bw_sub` / `arr_sub.max() + 3*bw_sub`, (b) `bw_sub == _stata_kde_bandwidth`
of the 22-row subsample, and (c) dash's density re-evaluated on **Stata's** data-range grid
has mean .0346, which is the Stata-anchored check.

### E4 — the early-outs return untagged renderers

Three of them, all returning a renderer with no `_dash_agg_source` and no `_dash_agg_config`:

```
4662        if self._is_empty(source, yvar):          # map_histogram
4663            empty_src = ColumnDataSource({"top": [], "left": [], "right": []})
4664            return fig.quad(top="top", bottom=0, left="left", right="right",
4665                            source=empty_src)

4835        if len(arr) < 2 or np.std(arr) == 0.0:    # map_kdensity
4836            empty = ColumnDataSource({"x": [], "y": []})
4837            return fig.line(x="x", y="y", source=empty)

4859        if bw <= 0.0:                             # map_kdensity
4860            empty = ColumnDataSource({"x": [], "y": []})
4861            return fig.line(x="x", y="y", source=empty)
```

RESEARCH §1.6: *"Only two producers of `_dash_agg_config` exist: :4695 (histogram) and :4905
(kdensity). […] Both mappers' early-outs (:4662-4665, :4835-4837, :4859-4861) return
**untagged** renderers."* The registry that consumes them, :12202-12210, is `hasattr`-guarded
on both attributes, so an untagged renderer is silently skipped. That is the behaviour
section 06 will build item 10 on top of, so this section pins it as a contract rather than
changing it.

### E5 — a qualifier that empties the sample currently draws a bin over [0, 1]

Read from the code, not measured in a browser. When a mask leaves zero rows, `_is_empty`
still returns `False` (the *source* has rows), `arr` is empty, and `_histogram_grid` (:4707)
falls through its `n == 0` branch — `a_min = float(arr.min()) if n else 0.0` at :4727 and
`a_max = float(arr.max()) if n else 1.0` at :4728. The result is `n_bins = _stata_bin_count(0) = 1`,
`edges = [0.0, 1.0]`, `counts = [0]`, and `_histogram_heights` returns the counts unchanged
because `total <= 0`. A zero-height quad is drawn from x=0 to x=1 — which **stretches the
figure's x range down to 0** on a variable whose real range is 12 to 41. RESEARCH §2.4
measured the analogous effect for a literal `0.0` in a y column: the range went from
`99.85 → 103.15` to `-5.15 → 108.15`.

### E6 — the policy for a degenerate subset (DISCOVERY Q8, UPHELD by RESEARCH §4.4)

RESEARCH §3.3 measured Stata and found it **not uniform**: at one observation `kdensity`
returns rc 2001 and **aborts the whole graph**, taking the companion scatter with it, while
`histogram` returns rc 0 and draws a 1-observation serset; at zero observations `histogram`
draws a 1-observation serset and `kdensity` draws a **75-observation** degenerate one. RESEARCH
§4.4 resolves this:

> **Resolution: keep the uniform graceful policy and document the divergence.** Every layer
> type warns and draws nothing. Losing an entire dashboard because one layer's qualifier
> matched one row is a worse outcome than a missing layer.

This section implements that policy for these two mappers only. Section 07 owns the same
policy for the twelve and for `scatteri`/`pci`/`function`; its `files` list does not include
`map_histogram` or `map_kdensity`, so the two sections do not collide in parallel batch 3.
**The warning fires only when `row_mask is not None`** — a genuinely degenerate *unqualified*
dataset keeps today's silent behaviour, so no existing assertion in
`test_statistical_defaults.py` or `test_statistical_truth.py` changes.

The layer index is available inside the mapper: `_make_figure_body` passes `color_idx=pi` at
every dispatch site (:10013, :10020, :10027, :10032, :10037, :10064), so `color_idx + 1` is
the user-visible layer number in the same one-based form the existing warning at :9995 uses
(`layer {pi + 1}`).

### E7 — RESEARCH §1.7 / D5: what this section does NOT touch

`GlyphMapper` is copied whole into the emitted `bokeh serve` app by the class loop at
:12410-12412 (`for _cls in (OptionTranslator, SchemeParser, GlyphMapper):` at :12410,
`_inspect.getsource(_cls)` at :12411), so `row_mask=` travels into the server app's text automatically — but no emitted
code calls it. The server app computes distributions through its own emitted
`_compute_histogram` (:13192) and `_compute_kdensity` (:13354), whose only restriction channel
is the first positional `df`, at call sites :14145, :14180, :15154, :15170, :15255, :15271,
:15605, :15611. Per DISCOVERY Q2 those are **section 09's failing parity test** and Phases
5-8's implementation. Nothing in this section may edit emitted string literals.

### The trap that governs every test below

Existing coverage is scatter-only and **structurally cannot catch this class of bug**.
`test/test_varlist_expansion.py:101`'s `_visible_count` helper reads
`renderer.view.filter.booleans`; for a histogram the renderer's `data_source` is
`hist_source` — four bins, or eight — and `view` is `None`, so the helper returns the bin
count and calls the layer fully visible no matter which observations produced those bins.
**Every assertion in this section compares the layer's own source values (`top`, `left`,
`right`, `x`, `y`) against an independently computed subsample**, never against a view's
booleans. This restriction is repeated in each task where it applies.

## TDD test stubs

All of these live in the new module **`test/test_per_plot_qualifier_distributions.py`** unless
stated otherwise. All must FAIL on the pre-fix tree.

- **Test:** `_extract_finite(source, "mpg", mask=[...])` returns only the masked, finite
  values, in source order. *Fails before the fix with `TypeError: _extract_finite() got an
  unexpected keyword argument 'mask'` — the right failure.*
- **Test:** `_extract_finite` with a mask whose length differs from the column raises
  `ValueError` and does not silently truncate. Guards against the D3-shaped silent-skip
  failure RESEARCH §1.5 found at :9986.
- **Test:** `_extract_finite` with `mask=None` returns exactly what it returns today, for a
  column containing `None`, `NaN` and real values, and for the `allow_datetime=True` path.
  This is the no-regression anchor for the four existing callers (:4666, :4830, :7731, :7809).
- **Test:** `map_histogram` called directly with `row_mask` for the 22 foreign rows emits
  **4** bins, `left[0] == 14.0`, `right[-1] == 41.0`, and bin centres 17.375 and 37.625 —
  and explicitly **not** 8 bins / 13.8125 / 39.1875. *Mutation that must kill it: drop
  `mask=row_mask` at :4666.*
- **Test:** `map_histogram`'s `top` column equals `_histogram_heights` of
  `np.histogram(arr_sub, bins=edges_sub)` computed independently in the test body — the
  density renormalises to the subsample, values `[0.03367003, 0.07407407, 0.02020202,
  0.02020202]`. Compares **source values**, never a view.
- **Test:** `map_histogram`'s `_dash_agg_config["bin_edges"]` equals the subset edges
  `[14.0, 20.75, 27.5, 34.25, 41.0]`, not the full-sample edges. Without this the bars jump
  back to the full sample on the first widget move (RESEARCH §1.2).
- **Test:** `map_kdensity` with the same mask uses bandwidth `_stata_kde_bandwidth(arr_sub)`
  = 2.516773101 and not the full-sample 1.9746142001, to a relative tolerance of 1e-9.
  *Mutation: compute the bandwidth from the unmasked `arr`.*
- **Test:** `map_kdensity`'s grid endpoints equal `arr_sub.min() - 3*bw_sub` and
  `arr_sub.max() + 3*bw_sub` (6.449681, 48.550319). The test must assert these values, **not**
  that the grid shrank — see the caveat in E3.
- **Test:** `map_kdensity`'s `y` column equals `_kde_curve(arr_sub, grid, bw_sub,
  "epanechnikov")` recomputed in the test body, and dash's density re-evaluated on Stata's
  own data-range grid `linspace(14, 41, 300)` has mean 0.0346 ± 5e-5 while the unqualified
  curve has mean 0.0331. This is the Stata-anchored assertion.
- **Test:** `map_kdensity`'s `_dash_agg_config["x_grid"]` is the subset grid.
- **Test:** a mask selecting **zero** rows makes `map_histogram` draw nothing —
  `len(r.data_source.data["top"]) == 0` — and emits a `UserWarning` naming the layer and the
  type. *Mutation: delete the `arr.size == 0` guard; the layer then draws one zero-height
  quad from x=0 to x=1 (E5) and the test dies.*
- **Test:** a mask selecting one row, and a mask selecting rows whose `mpg` values are all
  identical, each make `map_kdensity` draw nothing and warn. Stata aborts the graph here
  (RESEARCH §3.3); the test also asserts that the **companion scatter in the same figure still
  has 74 points**, which is the divergence DISCOVERY Q8 chose.
- **Test:** with `row_mask=None` and degenerate data, **no warning is emitted** — today's
  behaviour is preserved for unqualified layers.
- **Test:** an early-out renderer carries neither `_dash_agg_source` nor `_dash_agg_config`,
  so the registry comprehension at :12204-12208 skips it. This is the contract section 06
  builds on. *Mutation: remove the `arr.size == 0` guard so the renderer is tagged; the test
  dies.*
- **Test:** end to end through `make_dr`, the spec
  `[(scatter mpg weight), (histogram mpg, if_expr="foreign==1")]` produces a 4-bin histogram
  **and** a 74-point scatter in the same figure (BR-01.3: the qualifier binds to its own
  layer only).
- **Test:** the `in_expr` mirror (BR-01.4) — `in 53/74` gives byte-identical bins to
  `if foreign==1` on this fixture, and `in 1/52` gives 7 bins over `[12, 34]`.
- **Test:** the graph-level qualifier still reaches these layers. `graph_if="foreign==1"` with
  no per-plot qualifier must also give 4 bins, and a graph-level `foreign==1` combined with a
  per-plot `mpg>20` must give the **intersection** (BR-01.8).
- **Test (in `test/test_per_plot_qualifier_computed.py`, section 02's module):**
  `map_histogram` and `map_kdensity` appear in the parametrised fourteen-mapper list. The
  phase document states *"the parametrisation list **is** the coverage claim"*; until these
  two ids are in it, the claim is false. The same test walks `dash_render._ROW_MASK_TYPES`
  and asserts every member's `inspect.signature` carries `row_mask`, so it also fails until
  `"histogram"`, `"hist"` and `"kdensity"` are members — section 02 seeds that set with its
  twelve and leaves these three to task 03-05.
- **Test:** the generated server app still parses. Build an app with
  `dr.ServerAppBuilder(spec, data).build(path)` and `ast.parse` the result — the new
  `_extract_finite` keyword and the new `GlyphMapper` source are copied verbatim into it
  (the function loop at :12392-12407, the class loop at :12410-12412).

## Tasks

<task type="auto" id="03-01">
  <name>Write the failing distribution tests</name>
  <files>test/test_per_plot_qualifier_distributions.py (new)</files>
  <action>
    Create `test/test_per_plot_qualifier_distributions.py`. It is a new module rather than an
    addition to section 02's `test/test_per_plot_qualifier_computed.py` because sections 03,
    05 and 07 all run in parallel batch 3 and would otherwise edit the same file; the one
    two-line edit this section makes to that shared module is deferred to task 03-05.

    1. Module docstring. State the defect in one paragraph — `_extract_finite` (:964-995)
       returns a shorter array with no positional correspondence, so the mask must land at the
       call — and then state **the trap** verbatim: `test/test_varlist_expansion.py:101`'s
       `_visible_count` reads `renderer.view.filter.booleans`, which for a histogram reports
       the bin count and calls a computed layer fully visible whatever rows produced it.
       Every assertion in this file compares the layer's own source values against an
       independently computed subsample. Do not import `_visible_count`.
    2. Imports and path setup in the house style of `test/test_histogram_spurious_bin.py:28-40`
       (`_HERE`, two `sys.path.insert` lines, `import dash_render as dr`). Also
       `from conftest import make_dr, make_spec` where the end-to-end cases need them.
    3. Fixture helpers:
       - `_auto()` reads `test/fixtures/data/auto.csv` with `pandas.read_csv` and adds
         `foreign = np.array([0.0]*52 + [1.0]*22)`. Document in a comment that RESEARCH §3.1
         records auto.dta as shipping domestic-first with foreign cars at observations 53-74,
         N=74 / 22 / 52, and that this reproduces the Stata bin counts exactly.
       - `_mask_foreign(df)` returns `[bool(v == 1.0) for v in df["foreign"]]`.
       - `_cds(df)` returns a `ColumnDataSource` carrying `dash_render._ROW_ID_COLUMN`
         (`"__dash_row__"`, :591) set to `range(len(df))`, matching `_make_source` (:8506).
    4. Module constants, each with the exact Stata command in a trailing comment:
       `_STATA_BINS_FULL = 8`, `_STATA_BINS_SUB = 4`,
       `_STATA_CENTRES_FULL = (13.8125, 39.1875)`, `_STATA_CENTRES_SUB = (17.375, 37.625)`,
       `_STATA_KDE_RANGE_FULL = (12.0, 41.0)`, `_STATA_KDE_RANGE_SUB = (14.0, 41.0)`,
       `_STATA_KDE_MEAN_FULL = 0.0331`, `_STATA_KDE_MEAN_SUB = 0.0346`,
       `_STATA_BW_FULL = 1.9746142001`. Add the E3 caveat as a comment above
       `_STATA_KDE_RANGE_*`: dash extends the grid by 3*bw on each side, so these two are the
       grid for the *Stata-grid* mean-density check only and are never compared to
       `kd_source.data["x"]` endpoints.
    5. Write every test named in the "TDD test stubs" section above, one per stub, in these
       classes: `TestExtractFiniteTakesAMask`, `TestHistogramHonoursTheMask`,
       `TestKdensityHonoursTheMask`, `TestDegenerateSubsetsWarnAndDrawNothing`,
       `TestEarlyOutsStayOutOfTheAggRegistry`, `TestEndToEndThroughMakeDr`. Recompute every
       expected value **inside the test body** from `arr_sub` using `dr._stata_bin_count`,
       `dr.GlyphMapper._histogram_grid`, `dr._histogram_heights`, `dr._stata_kde_bandwidth`
       and `dr._kde_curve`, then additionally assert the literal Stata constants above. The
       literals are the anti-tautology guard: a recompute-only test would pass against a
       broken implementation that is self-consistently wrong.
    6. Every histogram assertion also asserts the negative: `len(left) != 8`,
       `left[0] != 12.0`. Every kdensity assertion also asserts `bw != _STATA_BW_FULL`.
    7. Do not add `xfail` or `skip` to anything in this file. These tests are meant to be red.
  </action>
  <verify>`python3 -m pytest test/test_per_plot_qualifier_distributions.py -q` — every test in
  the file fails. Then `python3 -m pytest test/test_per_plot_qualifier_distributions.py -q 2>&1 | grep -c "unexpected keyword argument 'row_mask'\|unexpected keyword argument 'mask'"`
  returns a non-zero count, confirming the failures are the *right* failures (the API does not
  exist yet) and not an import error or a bad fixture path.</verify>
  <done>A new red test module exists that pins Stata's 4-bin / 17.375-37.625 histogram and the
  2.516773101 subsample bandwidth, and every failure is attributable to the missing `mask=` /
  `row_mask=` API rather than to the test's own setup.</done>
</task>

<task type="auto" id="03-02">
  <name>Give `_extract_finite` an optional positional mask</name>
  <files>dash_render.py</files>
  <action>
    Edit `_extract_finite` at `dash_render.py:964-995`.

    1. Change the signature at :964-966 to
       `def _extract_finite(source, varname, allow_datetime=False, mask=None):`
       keeping the existing type comments. `mask` goes **last** so the two positional callers
       at :7731 and :7809 (`_extract_finite(source, varname, allow_datetime=True)`) are
       untouched.
    2. Extend the docstring's `Args:` block with:
       `mask: Optional sequence of bool, one per row of the column as it sits in the source.
       Applied BEFORE None/NaN are dropped, because dropping them destroys positional
       correspondence and a mask applied afterwards would select the wrong observations.`
    3. Immediately after `col = source.data.get(varname, [])` (:983) and **before** the
       `if allow_datetime:` branch, insert:
       ```python
       if mask is not None:
           if len(mask) != len(col):
               raise ValueError(
                   "dash: _extract_finite mask has %d entries for a %d-row "
                   "column (%s); the mask must be positional over the source "
                   "as given." % (len(mask), len(col), varname)
               )
           col = [v for v, keep in zip(col, mask) if keep]
       ```
       Raising rather than truncating is deliberate: RESEARCH §1.5 (D3) records that the
       length guard at :9986 silently skips the intersection when the lengths disagree, with
       no warning and nothing raised, and that is the failure mode to not repeat. The caller
       in `_make_figure_body` is already wrapped in `except Exception` at :9993-9998, which
       warns and draws the layer unfiltered — the BR-01.12 "never lose the layer" contract.
    4. Masking before the `allow_datetime` branch means the datetime path is masked too. Add
       a one-line comment saying so and naming :7731/:7809 as the callers that pass no mask.
    5. Change nothing else in the function. `arr = np.array([v for v in col if v is not None],
       dtype=float)` at :994 and the NaN filter at :995 stay exactly as they are.
  </action>
  <verify>`python3 -m pytest test/test_per_plot_qualifier_distributions.py -k ExtractFinite -q`
  — the three `TestExtractFiniteTakesAMask` tests pass. `python3 -m pytest test/test_filters.py test/test_filter_slider_step.py test/test_dates.py -q`
  — unchanged and green, proving the :7731/:7809 callers were not disturbed.</verify>
  <done>`_extract_finite` accepts `mask=`, applies it before any length-changing step, and
  raises a named `ValueError` on a length mismatch. No existing caller changed behaviour.</done>
</task>

<task type="auto" id="03-03">
  <name>Thread `row_mask` through `map_histogram`</name>
  <files>dash_render.py</files>
  <action>
    Edit `map_histogram`, `dash_render.py:4636-4704`. Implements TR-01.1 and TR-01.2 for this
    mapper; satisfies BR-01.1, BR-01.4.

    1. Signature (:4636-4645): add `row_mask=None` **after** `view=None` and before
       `color_idx: int = 0`. Name it `row_mask`, not `mask` — section 02 uses `row_mask`
       across the twelve because those mappers already have a local named `mask` for the NaN
       filter, and one name across all fourteen is what makes the parametrised test in task
       03-05 possible.
    2. Docstring `Args:` — add
       `row_mask: Optional per-source-row bool list from the layer's per-plot qualifier. The
       bins, their edges and their heights are all computed on the masked rows, which is what
       twoway histogram ... if does.`
    3. Line :4666 becomes `arr = _extract_finite(source, yvar, mask=row_mask)`.
    4. Insert the degenerate guard immediately after that line, before the
       `edges, ymode = self._histogram_grid(arr, options)` call at :4668:
       ```python
       if arr.size == 0:
           # A per-plot qualifier can empty the sample while the source is
           # still full, and _is_empty above only sees the source.  Falling
           # through gives _histogram_grid n=0, a_min=0.0, a_max=1.0 -- one
           # zero-height bar from x=0 to x=1, which drags the figure's x
           # range down to zero on a variable that lives in [12, 41].
           if row_mask is not None:
               warnings.warn(
                   f"dash: histogram on layer {color_idx + 1} ({yvar}) has no "
                   f"observations left after the per-plot qualifier; the layer "
                   f"is drawn empty.",
                   UserWarning, stacklevel=2,
               )
           empty_src = ColumnDataSource({"top": [], "left": [], "right": []})
           return fig.quad(top="top", bottom=0, left="left", right="right",
                           source=empty_src)
       ```
       The guard is conditioned on `row_mask is not None` for the warning only — the empty
       draw happens either way. `color_idx` is the zero-based layer index: every dispatch site
       in `_make_figure_body` passes `color_idx=pi` (:10013, :10020, :10027, :10032, :10037,
       :10064), so `color_idx + 1` matches the one-based `layer {pi + 1}` wording the existing
       warning at :9995 already uses. This is the uniform graceful policy of DISCOVERY Q8,
       upheld by RESEARCH §4.4; Stata instead draws a 1-observation serset here (RESEARCH §3.3).
    5. Change nothing below :4668. `_histogram_grid` (:4668), `np.histogram` (:4669) and
       `_histogram_heights` (:4670) all read `arr` and become subset-relative for free, as does
       `_stata_bin_count(n)` inside `_histogram_grid`. `_dash_agg_config["bin_edges"]` at :4698
       is `edges.tolist()` and therefore also becomes the subset's edges with no edit.
    6. Leave the `_is_empty` early-out at :4662-4665 exactly where it is, returning an
       untagged renderer. That is the contract section 06 relies on (E4) and the registry
       comprehension at :12204-12208 is `hasattr`-guarded for it.
  </action>
  <verify>`python3 -m pytest test/test_per_plot_qualifier_distributions.py -k "Histogram or EarlyOuts" -q`
  — the histogram and early-out classes pass; the kdensity classes still fail.
  `python3 -m pytest test/test_histogram_spurious_bin.py test/test_statistical_truth.py test/test_statistical_defaults.py -q`
  — green, unchanged.</verify>
  <done>`map_histogram` bins the qualified rows. `(histogram mpg if foreign==1)` on the auto
  fixture emits 4 bins with edges `[14.0, 20.75, 27.5, 34.25, 41.0]` and density heights
  `[0.03367003, 0.07407407, 0.02020202, 0.02020202]`, and its `_dash_agg_config` carries the
  subset edges. An emptying qualifier draws nothing and says so.</done>
</task>

<task type="auto" id="03-04">
  <name>Thread `row_mask` through `map_kdensity`</name>
  <files>dash_render.py</files>
  <action>
    Edit `map_kdensity`, `dash_render.py:4806-4914`. Same TR/BR coverage as 03-03.

    1. Signature (:4806-4815): add `row_mask=None` after `view=None`. Docstring `Args:` gains
       the same sentence as 03-03, worded for the density: the bandwidth, the evaluation span
       and the density are all derived from the masked rows.
    2. Line :4830 becomes `arr = _extract_finite(source, yvar, mask=row_mask)`.
    3. Attach the warning to the guard already at :4835-4837, keeping the guard's condition
       and its return exactly as they are:
       ```python
       if len(arr) < 2 or np.std(arr) == 0.0:
           if row_mask is not None:
               warnings.warn(
                   f"dash: kdensity on layer {color_idx + 1} ({yvar}) needs at "
                   f"least two distinct observations; the per-plot qualifier "
                   f"left {len(arr)}. The layer is drawn empty.",
                   UserWarning, stacklevel=2,
               )
           empty = ColumnDataSource({"x": [], "y": []})
           return fig.line(x="x", y="y", source=empty)
       ```
       Do the same at the second early-out, :4859-4861, with
       `"...could not derive a positive bandwidth from the {len(arr)} observations the
       per-plot qualifier left..."`. Both warnings fire only under a mask, so an unqualified
       degenerate dataset keeps today's silence and no existing assertion moves.
       RESEARCH §3.3: Stata returns rc 2001 here and aborts the whole graph, taking the
       companion scatter with it; RESEARCH §4.4 chose not to reproduce that.
    4. Change nothing between :4839 and :4914. `_stata_kde_bandwidth(arr)` at :4848 re-derives
       the bandwidth from the subset (2.516773101 for the 22 foreign cars, against
       1.9746142001 for all 74); `_lo, _hi = arr.min() - 3 * bw, arr.max() + 3 * bw` at :4870
       re-centres the evaluation span; `_kde_curve(arr, x_range, bw, kernel)` at :4890 uses
       `n = len(arr)` as its divisor, so the density normalises to the subsample. The
       `_dash_agg_config` at :4905-4913 picks up the subset `x_grid` with no edit.
    5. Do not "fix" the grid to match Stata's data-range grid. dash's ±3*bw extension is
       existing, intentional behaviour (the comment at :4865-4869 explains it) and changing it
       is not in this phase's scope. Record in a comment beside :4870 that the span is now
       subset-relative and that the Stata-grid comparison lives in the test.
  </action>
  <verify>`python3 -m pytest test/test_per_plot_qualifier_distributions.py -q` — the whole
  module passes except the two end-to-end classes, which still need task 03-05. Confirm the
  bandwidth assertion specifically:
  `python3 -m pytest test/test_per_plot_qualifier_distributions.py -k bandwidth -q` passes.
  `python3 -m pytest test/test_statistical_truth.py test/test_statistical_defaults.py test/test_glyphs.py -q`
  — green, unchanged.</verify>
  <done>`map_kdensity` estimates on the qualified rows: bandwidth 2.516773101, grid
  `6.449681 → 48.550319`, and a density whose mean over Stata's own `[14, 41]` grid is 0.0346
  against 0.0331 unqualified. Degenerate subsets warn by name and draw nothing.</done>
</task>

<task type="auto" id="03-05">
  <name>Plumb the mask through the univariate dispatch and close the fourteen-mapper claim</name>
  <files>dash_render.py, test/test_per_plot_qualifier_computed.py</files>
  <action>
    1. In `DashRenderer._add_glyph` (`dash_render.py:10334-10421`), confirm section 02 added
       the `row_mask=None` keyword to the signature at :10334-10345 and forwards it on the
       generic call at :10421. If it did not, add it now in the same position (after
       `view=None`, before `color_idx`).
    2. **Open the gate these two types are still outside of.** Section 02 forwards the mask
       only for names in the module-level `_ROW_MASK_TYPES` frozenset it added immediately
       after `_ROW_ID_COLUMN` at :591 — it seeds that set with its own twelve and states in
       its task 02-06 that *"Section 03 adds `"histogram"`, `"hist"` and `"kdensity"` to this
       set"*. Add those three names now, keeping the comment section 02 left there, so the
       frozenset stays a truthful registry of which mappers accept `row_mask=`: section 02's
       `test_row_mask_types_matches_the_mappers_that_accept_the_kwarg` walks it and asserts
       every member's `inspect.signature` has the parameter, and section 06 reads the same
       set. With the three names added, section 02's existing
       `_extra = {"row_mask": row_mask} if pt in _ROW_MASK_TYPES else {}` line inside
       `_add_glyph` forwards the mask down the univariate branch at :10418-10419 with **no
       further edit** — do not hard-code `row_mask=row_mask` into that branch and do not
       remove the `**_extra` gate, or the two shapes diverge and the raw mappers start
       receiving a kwarg they do not accept. Verify by reading the branch: it must still be
       `fn(fig, source, yvar, options, view=view, color_idx=color_idx, **_extra)`, the
       `options`-before-`xvar` call shape that `_UNIVARIATE_TYPES` (:9920) exists to select.
       If section 02 landed the frozenset but left the univariate branch un-gated, restore
       the `**_extra` form here rather than inventing a third shape.
    3. In `DashRenderer._make_figure_body`, confirm the `_UNIVARIATE_TYPES` dispatch at
       :10036-10037 passes `row_mask=`. If section 02 threaded the mask only through the
       final `else` branch at :10063-10064, add the same argument here. The value is the mask
       section 02 derives from `_plot_view` — `_plot_view.filter.booleans` when `_plot_view`
       carries a `BooleanFilter`, `None` otherwise (RESEARCH §1.1: the mask at :9979-9988 is
       already the intersection of the facet view and the per-plot qualifier, so passing it
       straight through is what satisfies BR-01.8). Reuse section 02's local, do not
       recompute it.
    4. In `test/test_per_plot_qualifier_computed.py` (section 02's module), add
       `"map_histogram"` and `"map_kdensity"` to the parametrised mapper list so it names all
       fourteen of TR-01.2. Give each the univariate call shape — `options` before `xvar`,
       `xvar` omitted — and assert against an independently computed subsample, never against
       `renderer.view`. Keep the edit to those two entries plus whatever dispatch shim the
       parametrisation needs; this module is also being edited by sections 05 and 07 in the
       same parallel batch.
    5. Do not touch any emitted string literal. `GlyphMapper` is copied whole into the server
       app by the class loop at :12410-12412 and `_extract_finite` by the function-name loop
       at :12392-12407, so both new keywords travel into the emitted app automatically with no
       emitted caller passing them. The emitted `_compute_histogram` (:13192) and
       `_compute_kdensity` (:13354) stay exactly as they are — section 09's parity test and
       Phases 5-8 own them (DISCOVERY Q2).
  </action>
  <verify>`python3 -c "import dash_render as dr; s=dr._ROW_MASK_TYPES; print(len(s), sorted(s))"`
  prints `15` and a list containing `hist`, `histogram` and `kdensity` alongside section 02's
  twelve. Then `python3 -m pytest test/test_per_plot_qualifier_distributions.py test/test_per_plot_qualifier_computed.py -q`
  — all pass, and the parametrised list reports 14 mapper ids
  (`python3 -m pytest test/test_per_plot_qualifier_computed.py --collect-only -q | grep -c "map_histogram\|map_kdensity"` is 2 or more).
  Then the server surface: `python3 -m pytest test/test_server_statistics.py test/test_server_histogram_bins.py test/test_mode_parity.py test/test_fit_grid_parity.py -q`
  — green, proving the emitted app still parses and behaves as before. Finally
  `python3 -m pytest test/ -q -m "not serve"` against the counts task 01-01 recorded in
  `.ultraplan/BASELINE.md` — no new failures, and the only new passes are this section's.</verify>
  <done>`dash (scatter mpg weight) (histogram mpg if foreign==1)` draws a 74-point scatter and
  a 4-bin histogram over `[14, 41]`; `(kdensity mpg if foreign==1)` uses bandwidth
  2.516773101. `_ROW_MASK_TYPES` holds all fifteen names, so `_add_glyph`'s existing gate
  forwards the mask to these two with no second dispatch shape, and the fourteen-mapper
  parametrisation names all fourteen, so the phase document's coverage claim is literally
  true. The generated server app is untouched and still parses,
  and its divergence remains section 09's red test.</done>
</task>
