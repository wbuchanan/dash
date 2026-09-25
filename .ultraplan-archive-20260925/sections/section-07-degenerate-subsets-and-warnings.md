# Section 07: Degenerate subsets, inline layers, and the warning surface

## Overview

Section 02 makes a per-plot qualifier reach the twelve computed mappers. This section handles
the two cases where the qualifier cannot produce a number, and makes both of them audible.

The first is a **degenerate subset**: `if make=="Honda Civic"` leaves one row and `map_lfit`
needs two. All eleven guarded mappers already return an empty renderer there, silently. dash
adopts a **uniform graceful policy** — warn, naming the layer, its type, the minimum and the
shortfall; draw nothing; never abort the build; and never fall back to the unqualified
computation, because a wrong number on screen is the defect this phase exists to remove.
Stata's own behaviour here is inconsistent and is deliberately not reproduced (RESEARCH §3.3,
§4.4).

The second is an **inline or analytic layer**: `scatteri`, `pci` and `function` have no rows to
qualify. Stata accepts the qualifier, *evaluates* it, then silently discards it. dash validates
it the same way — a bad variable name and an out-of-range `in` stay errors — and then **says**
it was discarded (RESEARCH §3.4, §4.5).

The third is the qualifier failure path at `dash_render.py:9993-9998`. Its "never lose the
layer" contract (BR-01.12) is preserved, but the two silent defaults inside it — the unwarned
length-mismatch skip at `:9986`, and a message saying "drawn unfiltered" where a *computed*
layer means "computed from all rows" — are removed.

**Ordering: the first task writes every failing test for this section.** Tasks 07-02 through
07-04 are implementation only; 07-05 proves each test dies under mutation.

## Risk: [yellow] — three new warning paths in the hottest block in the renderer

The code is small and local, but it sits inside `_make_figure_body`'s per-plot loop, which every
graph in every test runs. A message that fires once too often turns 82 pytest modules and 25
cscripts noisy, and `test/test_empty_layer_report.py` plus `test_conformance.cscript` assert on
the wording of the warning that already lives four lines below the new one. The mitigation is
that the new warning is computed from a *row count*, never from "the layer drew nothing", so a
missing optional package (`statsmodels` for `lowess`, `scipy` for `mspline`/`lfitci`) can never
be reported as a degenerate subset.

## Dependencies

- Depends on: section-01, section-02
- Blocks: section-10
- Parallel batch: 3

## Evidence

### E1 — Stata is not uniform at one observation, and the asymmetry is arbitrary

RESEARCH §3.3. `twoway (<type> … if _n==1)`, one observation:

| types | message | rc | effect |
|---|---|---|---|
| `lfit` `lfitci` `lpoly` `lpolyci` `kdensity` | `insufficient observations` | **2001** | **whole graph aborts — no graph at all** |
| `qfit` `qfitci` `fpfit` `fpfitci` | `could not fit model` | **0** | all-missing serset, nothing drawn |
| `lowess` `mband` `mspline` `histogram` and every raw type | *(none)* | **0** | 1-obs serset, drawn |

Zero observations (`if foreign==99`):

| types | rc | effect |
|---|---|---|
| `lfit` `lfitci` `qfit` `qfitci` `lowess` `scatter` `line` | **0** | empty serset; other layers draw normally |
| `histogram` | 0 | 1-obs serset |
| `kdensity` | 0 | **75-obs serset** (degenerate) |
| `lpoly` `lpolyci` | **2000** | whole graph aborts |
| `fpfit` | **198** | whole graph aborts |
| `mband` `mspline` | **198** | whole graph aborts |

`twoway (scatter mpg weight) (lfit mpg weight if make=="Honda Civic")` → **rc 2001, and the
scatter is not drawn either** — `graph describe` reports *graph not found*.

Root cause, read from `/Applications/StataNow/ado/base/t/twoway__lfit_serset.ado`: both `lfit`
and `qfit` wrap the internal `regress` in `capture`, but `lfit`/`lfitci` **re-raise any rc other
than 2000** while `qfit`/`qfitci` re-raise nothing. Deliberate in the code, undocumented, and
arbitrary rather than principled.

**Boundaries that must keep working:** exactly 2 observations is rc 0 for every fitted type, and
constant x is rc 0.

### E2 — Q8 was UPHELD after that measurement, not superseded

RESEARCH §4.4: *"keep the uniform graceful policy and document the divergence. Every layer type
warns and draws nothing. Losing an entire dashboard because one layer's qualifier matched one
row is a worse outcome than a missing layer."* DISCOVERY Q8 gives the message shape:

```
dash: lfit on layer 2 needs at least 2 observations; the qualifier left 1
```

and states the prohibition outright: *"Explicitly NOT a fallback to the unqualified computation
— that would put a wrong number on screen, which is the exact failure this phase exists to
remove. Never aborts the build."* RESEARCH §4.7 adds the `by()` corollary: Stata deletes the
whole panel; **do not reproduce it** — keep the panel, warn, draw the failing layer empty.

### E3 — the eleven guards, transcribed from the source at HEAD

Read read-only from `dash_render.py`. These are the thresholds the table in task 07-02 must
agree with, and the twelfth mapper is the interesting one:

| mapper | guard line | condition as written | minimum |
|---|---|---|---|
| `map_lfit` | 3852 | `if len(x) < 2:` | 2 |
| `map_qfit` | 3901 | `if len(x) < 3:` | 3 |
| `map_lfitci` | 3954 | `if scipy_stats is None or n < 3 or np.std(x) == 0.0:` | 3 |
| `map_qfitci` | 4030 | `if len(x) < 3:` | 3 |
| `map_lowess` | 4133 | `if lowess is None or len(x) < 2 or np.std(x) == 0.0:` | 2 |
| `map_lpoly` | 4305 | `if len(x) < 2:` | 2 |
| `map_lpolyci` | 4375 | `if len(x) < 3:` | 3 |
| `map_fpfit` | 4548 | `if len(x) < 4:` | 4 |
| `map_fpfitci` | 4600 | `if len(x) < 4:` | 4 |
| `map_mspline` | 5966 | `if PchipInterpolator is None or len(x_clean) < 2:` | 2 |
| `map_mband` | 6019 | `if len(x_clean) < 4:` | 4 |
| **`map_area`** | **— none —** | reads at 3614-3615, masks NaN at 3617, builds its CDS at 3630 with no count test | **0** |

Three of these conditions are **compound**: `lfitci`, `lowess` and `mspline` bail for a missing
optional package or a zero-variance x as well as for too few rows. `map_mband` has a second bail
at 6031 (`if x_max == x_min:`). Every guard's body builds an empty `ColumnDataSource` and returns
a renderer over it, e.g. `map_lfit:3853-3854`:

```python
 3853            empty = ColumnDataSource({"x": [], "y": []})
 3854            return fig.line(x="x", y="y", source=empty)
```

So the *behaviour* Q8 asks for is already there; what is missing is the warning. `map_area`
needs no entry and must not be given one — Stata draws an `area` at one observation with rc 0.

`map_histogram` (guard at 4662-4665, `self._is_empty(source, yvar)`) and `map_kdensity` (guards
at 4835-4837 and 4859-4861) are **section 03's** — they read through `_extract_finite`
(`dash_render.py:964-995`), which returns a shorter array with no positional correspondence. The
table and helper built here are shared; section 03 wires the two exceptions into them.

### E4 — `scatteri` / `pci` / `function`: validated, then discarded

RESEARCH §3.4, called there *"the sharpest finding for implementers"*:

| probe | `scatteri` | `pci` | `function` | `scatter` (contrast) |
|---|---|---|---|---|
| `if nosuchvar==1` | rc **111** | rc **111** | rc **111** | rc 111 |
| `in 900/901` | rc **198** | rc **198** | rc **198** | rc 198 |
| valid `if foreign==1` | rc 0, **output byte-identical** | rc 0, **identical** | rc 0, **identical** | rc 0, restricted |

RESEARCH §4.5 records the refinement of DISCOVERY Q6: *"validate like Stata, then warn instead of
staying silent. A typo is still an error; a valid-but-inapplicable qualifier gets the named
warning rather than Stata's silence. A deliberate, documented divergence, on the grounds that
silently dropping a user's `if` is the exact pattern this project exists to remove."*

Also from §3.4: **`function` defaults to range 0-1 and does not inherit companion plots'
x-range.** `dash_render.py:10044` already hard-codes `x_lo, x_hi = 0.0, 1.0`, with the
`twoway_function.sthlp` citation in the comment at 10040-10043; a qualifier must not disturb it.

Today the three dispatch arms take no view at all — `map_scatteri` (`:5370`, signature
`fig, values, options, color_idx`), `map_pci_literal` (`:5548`, same shape) and `map_function`
(`:6065`, `fig, expr, x_range, n_points, options`) have no `view=` parameter — and they are
called at `:10013`, `:10019` and `:10060` without one. The qualifier is computed at `:9957-9992`
and thrown away.

### E5 — the failure path, and its two silent defaults

`dash_render.py:9951-9998`. The gate is `:9957`:

```python
 9957            if (_p_if and _p_if != _g_if) or (_p_in and _p_in != _g_in):
```

and the handler is `:9993-9998`:

```python
 9993                except Exception as _pexc:          # never lose the layer
 9994                    warnings.warn(
 9995                        f"dash: per-plot qualifier on layer {pi + 1} could not "
 9996                        f"be applied ({_pexc}); the layer is drawn unfiltered.",
 9997                        stacklevel=2,
 9998                    )
```

BR-01.12 and TR-01.14 require that contract be preserved and that every new warning carry
`layer {pi + 1}` in the same style. Two silent defaults sit inside it:

- **RESEARCH §1.5 / D3.** The length guard at `:9986`
  (`if _prev_bools is not None and len(_prev_bools) == len(_mask):`) **silently skips the
  intersection** when the lengths disagree — no warning, and `except Exception` does not catch
  it because nothing raises. Lengths coincide today only because `linked_source` (`:11379`) is
  built without `df=`; any shortened source loses the facet restriction at initial render too.
- **The message is wrong for a computed layer.** "Drawn unfiltered" is accurate for a scatter.
  For an `lfit` it means *computed from all rows* — i.e. the -.00600869 slope this phase exists
  to delete. RESEARCH §1.8 notes the surrounding translator fails open the same way: a rejected
  qualifier warns and returns the **unfiltered** frame at `:8646-8651` and `:8661-8664`, so it
  draws *more* data, not less.

The neighbouring report at `:10084-10092` is the one that must not change:

```python
10084                if _rows_here and not self._layer_drew_anything(_layer_renderers):
10085                    warnings.warn(
10086                        f"dash: graph "
...
10089                        f"({ptype}) drew nothing from {_rows_here:,} "
10090                        f"observations.",
```

`_rows_here` counts the **shared** source (`:10080-10081`), so for a qualified `lfit` left with
one row it reads 74 — misleading, and duplicative of the new message. `test/test_empty_layer_report.py`
and `test_conformance.cscript` assert on its wording; it stays byte-identical and is suppressed
for the one layer that already got the precise message.

### E6 — the trap that governs every assertion here

RESEARCH §1.9 F-B. Existing coverage is scatter-only and **structurally cannot catch this class
of bug**: `test/test_varlist_expansion.py:101`'s `_visible_count` helper reads
`renderer.view.filter.booleans`, which reports a *computed* layer as fully visible no matter what
it drew. **Assertions on computed layers must compare the layer's own source values against an
independently computed subsample**, never a view's booleans. In this section that has a specific
form: proving "it did not fall back" means asserting that the fit source is **empty**, and —
because an empty source is also what a crash produces — that a sibling unqualified layer of the
same type on the same figure is **non-empty**.

## TDD test stubs

All of these live in two new modules. Every one must FAIL on the pre-fix tree.

**`test/test_qualifier_warning_surface.py`** (new):

- Test: an `lfit` whose per-plot qualifier leaves 1 row emits a warning containing `lfit`,
  `layer 2`, `2 observations` and `left 1`. *Pre-fix: no warning mentioning `lfit` is emitted at
  all.* Mutation that must kill it: drop the `left {n}` clause from the message.
- Test: the same render produces **no** `graph 'g1' plot 2 (lfit) drew nothing from 8
  observations` message — one precise message, not two. *Pre-fix: only the misleading one exists.*
- Test: **no fallback.** The `lfit` layer's own `data_source.data["x"]` is empty, while a second,
  unqualified `lfit` on the same figure is non-empty. Explicitly does **not** call
  `_visible_count` or read `renderer.view.filter.booleans` (E6). Mutation: make the guard at
  `map_lfit:3852` fall through to `np.polyfit` on the unmasked array — the empty assertion dies.
- Test: **boundary.** A qualifier leaving exactly 2 rows draws a real `lfit` (non-empty source)
  and emits no degenerate warning; likewise 3 rows for `qfit`/`lfitci`/`qfitci`/`lpolyci` and 4
  for `fpfit`/`fpfitci`/`mband` (E1: exactly 2 obs is rc 0 in Stata for every fitted type).
- Test: **the build is never aborted.** In `(scatter) (lfit if <1 row>)` the scatter still draws
  all rows and `render()` returns normally — dash does not reproduce Stata's rc 2001
  (E1, RESEARCH §4.4).
- Test: a missing optional package is **not** reported as a degenerate subset. With
  `dash_render.lowess` monkeypatched to `None` and a 50-row unqualified `lowess`, no message
  containing `needs at least` is emitted. Mutation: compute the warning from
  `_layer_drew_anything` instead of the row count — this test dies immediately.
- Test: `(scatteri 20 3000 "a")` with `if_expr: "foreign==1"` warns, naming `layer` and
  `scatteri`, and the scatteri glyph still draws both coordinates (BR-01.6, BR-01.12, US-A2).
- Test: the same for `pci` with `if_expr` and for `function` with `in_expr`.
- Test: `scatteri` with `if_expr: "nosuchvar==1"` emits a warning that names the **unknown
  variable** as well as the layer — the rc 111 analogue (E4). *Pre-fix: the generic
  `dash: if_expr filter skipped — invalid syntax` fires, which names no layer;* assert on
  `layer` + the variable name so the pre-fix message cannot satisfy it.
- Test: `function` with `in_expr: "900/901"` on an 8-row frame warns about the out-of-range
  observation numbers — the rc 198 analogue (E4).
- Test: `function` with a qualifier still evaluates over `[0, 1]` with 300 points —
  `min(x) == 0.0`, `max(x) == 1.0`, `len(x) == 300` — and does not inherit a companion scatter's
  x-range (E4, `:10044`).
- Test: a per-plot qualifier on a raw `scatter` whose intersection is skipped by the `:9986`
  length guard emits a warning naming the layer. Built by rendering a linked `by()` graph where
  `facet_view.filter.booleans` and `_mask` differ in length. *Pre-fix: complete silence* (D3).
- Test: the `:9993` handler's message for a **computed** type says the layer was computed from
  all rows, not merely "drawn unfiltered"; for a **raw** type the existing wording survives
  (BR-01.12). Forced by patching `_apply_graph_filter` to raise.
- Test: every warning this module provokes matches `^dash: ` and contains `layer <n>` (TR-01.14).

**`test/test_degenerate_layer_guards.py`** (new):

- Test: parametrised over the eleven entries of E3 — calling the mapper directly with exactly
  `minimum - 1` finite rows returns a renderer whose source is empty, and with exactly `minimum`
  rows returns a non-empty one. This is the guard-parity pin: it makes the table in 07-02 a claim
  about the code rather than a comment. Mutation: change one table entry by 1 — the test names the
  mapper that disagrees.
- Test: `map_area` is **absent** from the table (`"area" not in dr._MIN_OBS_FOR_COMPUTED`) and
  draws a 1-row area with a non-empty source (E1: every raw type is rc 0 at one observation).
- Test: `map_mband`'s second bail (`x_max == x_min`, `:6031`) and `map_lfitci`/`map_lowess`'s
  `np.std(x) == 0.0` terms return empty **without** a `needs at least` warning — constant x is
  rc 0 in Stata and is not a degenerate *subset* (E1).

## Tasks

<task type="auto" id="07-01">
  <name>Write the failing tests for the degenerate, inline and warning-path behaviours</name>
  <files>test/test_qualifier_warning_surface.py (new), test/test_degenerate_layer_guards.py (new)</files>
  <action>
    Create both modules listed under "TDD test stubs", one test per stub, and nothing else.

    1. Copy the harness shape from `test/test_empty_layer_report.py:48-63`: a `_render(plots,
       graph_options=None)` helper that writes a spec JSON and a data JSON to a `tempfile.mkdtemp()`,
       runs `dr.DashRenderer(sp, dp).render()` inside
       `warnings.catch_warnings(record=True)` with `warnings.simplefilter("always")`, and returns
       `[str(w.message) for w in caught]`. Extend it to also return the `DashRenderer` instance so
       assertions can reach `renderer.figures`/`fig.renderers` for the source-value checks. Use
       `conftest.make_data_json` for the data file.
    2. Use an 8-row frame in the style of `test/test_per_plot_qualifier_linking.py:41-46`
       (`mpg`, `weight`, `foreign`) and add an integer `grp` column so a qualifier can be dialled
       to leave exactly 0, 1, 2, 3 or 4 rows. State the row counts in the module docstring.
    3. Per-plot qualifiers go in the plot dict as `{"type": "lfit", "yvar": "mpg", "xvar":
       "weight", "if_expr": "grp==1", "options": {}}` — that is the key `_make_figure_body:9951`
       reads.
    4. For the "no fallback" test, assert on the fit renderer's OWN source:
       `[r for r in fig.renderers if r.data_source is not shared][k].data_source.data["x"]`.
       Write a comment in the test body naming the trap: `_visible_count`
       (`test/test_varlist_expansion.py:101`) reads `renderer.view.filter.booleans` and reports a
       computed layer as fully visible whatever it drew, so this assertion compares the layer's
       own source values against an independently computed subsample and never a view's booleans.
    5. In `test_degenerate_layer_guards.py`, parametrise over an inline copy of the E3 table and
       call each mapper directly through `dr.GlyphMapper` the way `TR-01.2`'s unit tests do —
       build a `ColumnDataSource` with exactly N finite rows, call `map_<type>(fig, src, "y", "x",
       {})`, and assert on the returned renderer's source. Import `_MIN_OBS_FOR_COMPUTED` from
       `dash_render` so the module fails at import time until 07-02 lands; that is the intended
       first failure for those tests.
    6. Mark nothing `xfail` or `skip`. Every test must fail now.
  </action>
  <verify>`python -m pytest test/test_qualifier_warning_surface.py test/test_degenerate_layer_guards.py -x -q 2>&1 | tail -30` — every test fails or errors. Then run without `-x` and read each failure: the warning tests must fail on a missing/unmatched message (not on a `KeyError` in the harness), the guard-parity module must fail with `ImportError: cannot import name '_MIN_OBS_FOR_COMPUTED'`, and the `function` range test must fail on the assertion, not on a spec-shape error. Record the failure reason for each test in a comment above it.</verify>
  <done>Two new test modules exist, every test in them fails, and each failure has been read and confirmed to be the failure the stub describes rather than a harness defect. No product code has changed.</done>
</task>

<task type="auto" id="07-02">
  <name>Uniform graceful policy for degenerate subsets</name>
  <files>dash_render.py</files>
  <action>
    Implements DISCOVERY Q8 as upheld by RESEARCH §4.4. BR-01.12, TR-01.14.

    1. Add a module-level table next to the other type frozensets (after `_ROW_ID_COLUMN` at
       `:591` is the natural home; `_UNIVARIATE_TYPES` and friends at `:9916-9924` are
       function-local and cannot be imported by a test):

       ```python
       # Minimum observations each computed layer needs before it can produce a
       # number, transcribed from the mappers' own guards.  Keep in step with:
       #   lfit 3852 · qfit 3901 · lfitci 3954 · qfitci 4030 · lowess 4133
       #   lpoly 4305 · lpolyci 4375 · fpfit 4548 · fpfitci 4600
       #   mspline 5966 · mband 6019
       # `area' is deliberately absent: it has no count guard (3614-3630), and
       # Stata draws an area at one observation with rc 0.
       # `histogram'/`kdensity' are added by section 03, which owns the
       # _extract_finite path (964-995) their guards sit behind.
       _MIN_OBS_FOR_COMPUTED: "dict[str, int]" = {
           "lfit": 2, "qfit": 3, "lfitci": 3, "qfitci": 3,
           "lowess": 2, "lpoly": 2, "lpolyci": 3,
           "fpfit": 4, "fpfitci": 4,
           "mspline": 2, "mband": 4,
       }
       ```

       Do not change any guard's threshold or body. The guards already draw nothing, which is the
       behaviour Q8 asks for; only the warning is missing.
    2. Add a module-level formatter beside it so every warning this section adds has one shape
       (TR-01.14):

       ```python
       def _layer_warning(pi: int, ptype: str, detail: str) -> str:
           """Format a per-layer warning: `dash: <ptype> on layer <n>: <detail>'."""
           return f"dash: {ptype} on layer {pi + 1}; {detail}"
       ```
    3. In `_make_figure_body`, inside the per-plot qualifier block, record how many rows the
       qualifier left. Immediately after `_mask` reaches its final value (after the intersection
       at `:9986-9988`, before `BooleanFilter(booleans=_mask)` at `:9989`), set
       `_kept_here = sum(1 for b in _mask if b)`. Initialise `_kept_here = None` alongside
       `source_for_plot = source` at `:9955` so the unqualified path leaves it `None`.
    4. After the layer is dispatched and `_layer_renderers` is collected at `:10066`, and BEFORE
       the existing "drew nothing" report at `:10084`, insert the degenerate report:

       ```python
       _min_obs = _MIN_OBS_FOR_COMPUTED.get(ptype.lower())
       _degenerate = (_min_obs is not None and _kept_here is not None
                      and _kept_here < _min_obs)
       if _degenerate:
           warnings.warn(
               _layer_warning(
                   pi, ptype,
                   f"needs at least {_min_obs} observations; the qualifier "
                   f"left {_kept_here}. The layer is drawn empty -- dash does "
                   f"not fall back to the unqualified computation."),
               UserWarning, stacklevel=2,
           )
       ```

       The condition is computed from the **row count**, never from
       `self._layer_drew_anything(...)`. That is what keeps a missing `statsmodels` (`lowess`,
       guard `:4133`), a missing `scipy` (`lfitci` `:3954`, `mspline` `:5966`) and a constant-x
       bail (`mband` `:6031`) out of this message — they are not degenerate subsets and they warn
       for themselves already, as the comment at `:10075-10078` records.

       On TR-01.14: this one warning sits **outside** the `try/except` that spans `:9958-9998`,
       and must. It needs `_layer_renderers` (`:10066`) to exist so step 5 can suppress the
       duplicate at `:10084`, and the try block closes before dispatch. TR-01.14's substance is
       met — nothing here can lose the layer (the guards already returned an empty renderer, and
       the statement is a `warnings.warn` over an `int` and a `dict.get`), and the message carries
       `layer {pi + 1}` in the required format via `_layer_warning`. Only the step-3 assignment of
       `_kept_here` goes inside the `try`.
    5. Suppress the duplicate: change the existing condition at `:10084` to
       `if _rows_here and not _degenerate and not self._layer_drew_anything(_layer_renderers):`.
       Do not touch the message body at `:10085-10092` — `test/test_empty_layer_report.py` and
       `test_conformance.cscript` assert on its exact wording, and `_rows_here` counts the shared
       source (`:10080-10081`), which reads 74 for a layer the qualifier cut to 1.
    6. Never raise. Stata aborts the whole graph at rc 2001 for `lfit` at one observation, taking
       the companion scatter with it (RESEARCH §3.3); dash does not (RESEARCH §4.4), and under
       `by()` dash keeps the panel rather than deleting it (RESEARCH §4.7).
  </action>
  <verify>`python -m pytest test/test_degenerate_layer_guards.py -q` passes all of it, including the `map_area`-is-absent case. `python -m pytest test/test_qualifier_warning_surface.py -q -k "degenerate or boundary or fallback or abort or optional"` passes. `python -m pytest test/test_empty_layer_report.py -q` still passes with no change to its expected strings. `python -m pytest test/ -q 2>&1 | tail -3` shows no new failures against the section-01 baseline.</verify>
  <done>A qualifier that leaves too few rows produces exactly one message, naming the layer, its type, the minimum and the shortfall; the layer draws nothing; the build completes; and a missing optional package or a constant x is never mislabelled as a degenerate subset.</done>
</task>

<task type="auto" id="07-03">
  <name>Validate-then-warn for scatteri, pci and function</name>
  <files>dash_render.py</files>
  <action>
    Implements DISCOVERY Q6 as refined by RESEARCH §3.4/§4.5. BR-01.6, BR-01.12, TR-01.3, US-A2.

    1. Add a module-level frozenset beside `_MIN_OBS_FOR_COMPUTED`:

       ```python
       # Inline-coordinate and analytic layers: there are no data rows to
       # qualify.  Stata accepts the qualifier, EVALUATES it (rc 111 for a bad
       # variable name, rc 198 for an out-of-range `in') and then silently
       # discards it -- output is byte-identical with and without.  dash
       # validates the same way and then says so.
       _NON_QUALIFIABLE_TYPES: frozenset = frozenset({"scatteri", "pci", "function"})
       ```
    2. In `_make_figure_body`, split the gate at `:9957`. When
       `ptype.lower() in _NON_QUALIFIABLE_TYPES` and `(_p_if or _p_in)`, take a new branch that
       does NOT call `_apply_graph_filter` (it copies the whole frame at `:8623` for a result
       nothing can use) and does NOT build a view. In that branch, in order:

       a. **Validate `_p_if` — the rc 111 analogue.** Run
          `_pandas_expr = _stata_if_to_pandas(_p_if)` then
          `_validate_if_expr(_pandas_expr, self.df.columns)` (`:6932-6967`). On `False`, warn:
          `_layer_warning(pi, ptype, f"the qualifier `if {_p_if}' is not valid against this "
          f"data -- check the variable names")`. Include the offending expression verbatim so a
          typo is identifiable, matching Stata's rc 111.
       b. **Validate `_p_in` — the rc 198 analogue.** Apply the same
          `^(\d+)/(\d+)$` match `_apply_graph_filter` uses at `:8628`. Warn when the pattern does
          not match, when `lo < 1`, when `hi < lo`, or when `hi > len(self.df)`:
          `_layer_warning(pi, ptype, f"`in {_p_in}' is out of range for {len(self.df)} "
          f"observations")`. Note in a comment that D6 (RESEARCH §4.8) — `in 1/l`, `in f/20`,
          `in -10/-1`, `in 10` being silently discarded by `:8628` — is a translator defect out of
          scope for this phase; here the non-matching case is reported rather than discarded, for
          these three types only.
       c. **Report the discard, always**, valid or not:
          `_layer_warning(pi, ptype, "takes inline coordinates and has no data rows, so the "
          "qualifier cannot restrict it; the layer is drawn in full")`. For `function`, say
          "is evaluated analytically" in place of "takes inline coordinates". This is the
          divergence from Stata's silence that RESEARCH §4.5 sanctions.

       Leave `source_for_plot = source` and `_plot_view = facet_view` untouched in this branch, so
       the three dispatch arms at `:10011-10020` and `:10038-10060` are unchanged and the layer
       still draws — the "never lose the layer" contract (BR-01.12).
    3. Do not add a `view=` parameter to `map_scatteri` (`:5370`), `map_pci_literal` (`:5548`) or
       `map_function` (`:6065`), and do not pass one. Instead add three sentences to their
       docstrings recording why they will never take one: the layer's coordinates come from the
       command, not from a row of the frame, so there is no row to include or exclude; Stata
       evaluates a qualifier on them and discards it; dash validates it and warns. Cite
       RESEARCH §3.4.
    4. Do not touch the `function` range block at `:10044-10052`. `x_lo, x_hi = 0.0, 1.0` is
       Stata's documented default (the comment at `:10040-10043` cites `twoway_function.sthlp`)
       and RESEARCH §3.4 confirms `function` does not inherit companion plots' x-range; the test
       from 07-01 pins it.
  </action>
  <verify>`python -m pytest test/test_qualifier_warning_surface.py -q -k "scatteri or pci or function or inline or range"` passes. `python -m pytest test/test_paired_coordinate_plots.py test/test_every_plot_type_draws.py test/test_server_function_security.py -q` still passes — the three layers still draw. `grep -n "_NON_QUALIFIABLE_TYPES" dash_render.py` prints the definition and exactly one use site inside `_make_figure_body`.</verify>
  <done>A per-plot `if`/`in` on `scatteri`, `pci` or `function` is validated exactly as Stata validates it, reported in a warning naming the layer number and type, and then discarded; the layer still draws; `function` still evaluates over `[0, 1]`; and no whole-frame copy is made for a qualifier that cannot be used.</done>
</task>

<task type="auto" id="07-04">
  <name>Remove the two silent defaults in the qualifier failure path</name>
  <files>dash_render.py</files>
  <action>
    BR-01.12, TR-01.14, RESEARCH §1.5 (D3). The contract at `:9993-9998` — warn and never lose the
    layer — is preserved; what changes is that "drawn unfiltered" stops being reachable silently
    and stops understating what it means for a computed layer.

    1. **The unwarned skip (D3).** At `:9986` the intersection is applied only when
       `len(_prev_bools) == len(_mask)`; when they differ the facet or linked-graph restriction is
       dropped with no warning, and `except Exception` at `:9993` never sees it because nothing
       raises. Add the `else` branch:

       ```python
       elif _prev_bools is not None:
           warnings.warn(
               _layer_warning(
                   pi, ptype,
                   f"the restriction already on this layer covers "
                   f"{len(_prev_bools)} rows but the qualifier produced "
                   f"{len(_mask)}; the two could not be intersected and only "
                   f"the qualifier is applied."),
               UserWarning, stacklevel=2,
           )
       ```

       Record in a comment that this is reachable whenever a shortened source reaches the block —
       RESEARCH §1.5 notes the lengths coincide today only because `linked_source` (`:11379`) is
       built without `df=`.
    2. **The message that understates.** Make the handler at `:9993-9998` say what "unfiltered"
       means for the type it is describing, while keeping `layer {pi + 1}` and the exception text:

       ```python
       except Exception as _pexc:          # never lose the layer
           _unqual = ("the layer is COMPUTED FROM ALL ROWS"
                      if ptype.lower() in _MIN_OBS_FOR_COMPUTED
                      else "the layer is drawn unfiltered")
           warnings.warn(
               f"dash: per-plot qualifier on layer {pi + 1} could not "
               f"be applied ({_pexc}); {_unqual}.",
               stacklevel=2,
           )
       ```

       Keep the prefix `dash: per-plot qualifier on layer {pi + 1} could not be applied` byte for
       byte — it is the substring any existing assertion would match on — and keep the layer
       drawn. For a computed type this warning now says out loud that the number on screen is the
       unqualified one, which is the defect RESEARCH §1.8 describes as failing *open*: a rejected
       qualifier draws **more** data, not less.
    3. Leave `_apply_graph_filter`'s own warnings at `:8646-8651` and `:8661-8664` alone. They are
       graph-scoped, they already warn, and widening them is section 10's documentation item, not
       a code change here.
  </action>
  <verify>`python -m pytest test/test_qualifier_warning_surface.py -q -k "length_mismatch or computed_from_all_rows or raw_wording"` passes. `python -m pytest test/test_per_plot_qualifier_linking.py test/test_linking.py test/test_linking_filters.py test/test_layout_facets.py -q` still passes. `grep -c "could not be applied" dash_render.py` prints the same count as before the change.</verify>
  <done>No path through the per-plot qualifier block drops a restriction without saying so, and when the qualifier cannot be applied at all the warning distinguishes a raw layer drawn unfiltered from a computed layer whose number was produced from every row.</done>
</task>

<task type="auto" id="07-05">
  <name>Prove each test dies under mutation and close the section</name>
  <files>test/test_qualifier_warning_surface.py, test/test_degenerate_layer_guards.py</files>
  <action>
    Project rule 8 and PRD §8: a test that certifies nothing is worse than no test. Every stub in
    this section asserts on a *warning string* or on an *empty source*, and both are easy to
    satisfy accidentally.

    1. For each mutation below, apply it to a scratch copy of `dash_render.py` under the
       scratchpad directory (never to the repository file), run the named test, confirm it FAILS,
       then discard the copy:
       - Delete the `left {_kept_here}` clause from 07-02 step 4 → the degenerate-message test
         must fail.
       - Change `_MIN_OBS_FOR_COMPUTED["fpfit"]` from 4 to 3 → `test_degenerate_layer_guards.py`
         must name `map_fpfit`.
       - Replace 07-02's row-count condition with
         `not self._layer_drew_anything(_layer_renderers)` → the missing-`statsmodels` test must
         fail (this is the mutation the section's whole warning design exists to survive).
       - Make `map_lfit:3852`'s guard fall through to `np.polyfit(x, y, 1)` on the unmasked array
         → the no-fallback test must fail on the non-empty source, NOT merely on a warning.
       - Delete 07-03's step 2a validation → the `nosuchvar` test must fail.
       - Restore the unconditional `if _prev_bools is not None and len(...) == len(...)` of
         `:9986` → the D3 length-mismatch test must fail.
    2. Record the result as a `MUTATIONS` block in each module's docstring: one line per mutation,
       naming the test it kills. This is what makes the suite auditable in VALIDATE.
    3. Any mutation that does NOT kill its test means the test certifies nothing — strengthen the
       assertion (usually: assert on the layer's own source values, not on the presence of a
       warning) and re-run before moving on. Restate the trap in the block: `_visible_count`
       (`test/test_varlist_expansion.py:101`) reads `renderer.view.filter.booleans` and reports a
       computed layer as fully visible whatever it drew, so no assertion in either module may read
       a view's booleans.
    4. Run the whole Python suite and compare to the counts section 01 recorded. Report the delta
       in the commit message. Do not run the Stata cert suite here; section 10 owns the
       end-to-end `.cscript`.
  </action>
  <verify>`python -m pytest test/ -q 2>&1 | tail -3` — passed/failed/skipped equal the section-01 baseline plus exactly the new tests, with zero new failures and zero new skips. `grep -c "^  - " test/test_qualifier_warning_surface.py` and the same for the guards module show a MUTATIONS line for every mutation in step 1. Each mutation in step 1 was run and its named test was observed to fail.</verify>
  <done>Every test this section added has been shown to fail under a specific mutation of the code it guards, the mutations are documented in the test modules themselves, no assertion in either module reads `renderer.view.filter.booleans`, and the full Python suite is green against the section-01 baseline.</done>
</task>
