# Phase 09 — Dates I: the standalone loader and primary axes

**Purpose.** Task 08-04 converted Stata date columns inside `DashRenderer._load_data` and
taught `_make_figure_body` to build a `DatetimeAxis` with a per-kind `DatetimeTickFormatter`.
For a `line` plot on one date variable that works, and works well. For everything else it
broke the build: the loader now puts `Timestamp` objects in the DataFrame, and the 37 glyph
call sites that coerce their columns with `np.array(source.data[xvar], dtype=float)` raise
`TypeError`, which `_build_sources_and_figures` re-raises as `RuntimeError` and Stata surfaces
as **rc 7102** — a total dashboard build failure on 24 of 35 plot types. Where the build does
survive, the axis decision itself is wrong for three whole plot families, and for
`histogram`/`kdensity` it is exactly inverted. This phase repairs the standalone renderer's
date path end to end — the loader, the coercion sites, the axis decision, the literal
coordinates — and then builds the test surface that would have caught all of it: pytest cases
for non-`line` glyphs, a formatter assertion, the byte-identity guard the section's own
`<verify>` clause names, and the two Stata certification scripts the plan named and never
wrote. It deliberately stops at the primary axes of the standalone renderer: `ServerAppBuilder`,
the secondary axis, and the `xlabel()`/`xscale()`/`xline()` date grammars are a later phase.

---

## At a glance

| | |
|---|---|
| **Work items** | 14 |
| **Functional / deliverable** | 8 functional (items 1, 3, 4, 5, 6, 9, 10, 13) · 6 deliverable (items 2, 7, 8, 11, 12, 14) |
| **Effort mix** | 2 large (3, 9) · 4 medium (4, 12, 13, 14) · 8 small (1, 2, 5, 6, 7, 8, 10, 11) |
| **Renderers touched** | `DashRenderer` (standalone) ×10 · Stata cscripts ×3 · both renderers ×1 (item 13, the shared `_stata_dates_to_datetime` helper) |
| **Ultraplan tasks discharged** | **08-04** (the standalone half, completely) · the **08-03** refutation (out-of-range period values) · **08-01**'s named-but-absent `test/test_formats.cscript` |
| **Sections** | S08 "Formats, dates, labels" — 6 tasks, currently *2 done, 4 partial* |
| **Depends on** | Nothing. Every item is inside `dash_render.py`'s standalone path or `test/`; no other phase has to land first. |
| **Unblocks** | The remaining date work — `ServerAppBuilder` date support, the secondary-axis datetime path, and the `xlabel()`/`xscale(range())`/`xline()` millisecond conversions — all of which assume a standalone renderer that does not crash. The plan records S08 as **blocking S09** (`.ultraplan/sections/section-08-formats-dates.md`, "Blocks: S09"). |
| **Backlog provenance** | REMAINING.md Appendix A (08-04), Appendix B (2 of 7 items), Appendix C (10 of 14 items), main body §"Status by section" and the 08-03 refutation row |

---

## Why this phase exists

### The audit's own verdict on 08-04

REMAINING.md, Appendix A, *"08-04 — Convert in the loader, give date figures a datetime axis ·
PARTIAL"*:

> **Standalone is done**, and more completely than the task asked. All seven
> Stata date kinds produce a `DatetimeAxis` with a `DatetimeTickFormatter` tuned
> per kind (`%ty` → `%Y` at every scale; `%tm`/`%tq`/`%th` → `%b %Y` at day
> scale; `%tc` → `%d %b %H:%M`):
>
> ```
> %td %tm %tq %tw %th %ty %tc  ->  DatetimeAxis + DatetimeTickFormatter
> no "formats" key             ->  LinearAxis + BasicTickFormatter (unchanged)
> y-axis date                  ->  DatetimeAxis
> xscale(log) on a date        ->  DatetimeAxis + "dash: xscale(log) is
>                                  meaningless for the date variable 'd'"
> ```
>
> **Remaining:**
> 1. **Server mode has no date handling whatsoever.** In the emitted app:
>    `DatetimeAxis` 0, `DatetimeTickFormatter` 0, `date_vars` 0,
>    `numeric_formats` 0. […] This is the whole of 08-04 missing from `dash serve`.
> 2. Out-of-range period values still raise. `%tm`/`%tq`/`%tw` with a value past
>    pandas' Timestamp range abort the render with a bare
>    `AssertionError: Something has gone wrong, please report a bug at pandas`,
>    rather than coercing to `NaT` with the existing warning.

Remaining item 1 (server mode) is **not** this phase — it is the Dates II work. Remaining
item 2 **is** this phase: it is work items 6 and 13 below.

That headline — "standalone is done" — was written against a `line` plot. The adversarial
pass then measured the other 30 plot types.

### Finding 1 — the loader conversion is a hard crash on 24 of 35 plot types

REMAINING.md Appendix C, 08-04, the large functional item (reproduced here as work item 9):

> Fix the hard crash the 08-04 loader conversion introduced: 24 of 35 plot types abort the
> entire `dash build` when their x (or binned) variable is a Stata date. `_load_data` now
> hands `GlyphMapper` a datetime64 column, and 37 sites of the form
> `np.array(source.data[xvar], dtype=float)` raise
> `TypeError: float() argument must be a string or a real number, not 'Timestamp'`, which
> `_build_sources_and_figures` (dash_render.py:11510) re-raises as RuntimeError and Stata
> surfaces as rc 7102. The machinery for the fix already exists — `_extract_finite`
> (dash_render.py:964-995) takes `allow_datetime=True` and casts via
> `astype('datetime64[ms]').astype('int64')`, and is called that way at dash_render.py:7731
> and :7809 — but the glyph call sites at :4666 (`map_histogram`) and :4830 (`map_kdensity`)
> omit the flag, and the 35 remaining `np.array(source.data[...], dtype=float)` sites have no
> equivalent at all. Note the CDS column arrives object-dtype (a list of `Timestamp`), not
> datetime64, so an `np.issubdtype(...)` guard is not sufficient — route through
> `pd.Series(col)` / `pd.api.types.is_datetime64_any_dtype` as `_extract_finite` already does.

The auditor's independent statement of the same defect (work item 3) counts it from the
mapper side rather than the call-site side:

> the loader now puts `Timestamp` objects in the DataFrame, and 20 of 31 plot types abort the
> ENTIRE dashboard build the moment a date variable is on an axis.

Both measurements are kept verbatim below. They are one body of work seen through two lenses —
37 coercion sites across 21 named mappers — and the difference in the denominators (24/35 vs
20/31) is a difference in what each lens counted as a distinct plot type, not a disagreement
about the defect.

The failing shape, at `map_area` (`dash_render.py:3614-3615`):

```python
x_arr = np.array(source.data[xvar], dtype=float)
y_arr = np.array(source.data[yvar], dtype=float)
```

The working shape already in the file, `_extract_finite` (`dash_render.py:964-995`):

```python
col = source.data.get(varname, [])
if allow_datetime:
    series = pd.Series(col)
    if pd.api.types.is_datetime64_any_dtype(series):
        # Cast to an explicit millisecond unit first.  pandas 3 preserves
        # the resolution it inferred, so this column can be
        # datetime64[us] or [ns]; dividing a raw astype("int64") by a
        # fixed constant silently yields seconds for one and
        # milliseconds for the other.
        ms = series.dropna().astype("datetime64[ms]").astype("int64")
        return ms.to_numpy(dtype=float)
arr = np.array([v for v in col if v is not None], dtype=float)
return arr[~np.isnan(arr)]
```

Only two callers pass the flag: `build_slider` at `dash_render.py:7731` and `build_range` at
`:7809`.

*Confirmed at HEAD while writing this phase:* `grep -c "np.array(source.data\[" dash_render.py`
→ **37**. `_extract_finite` is at `dash_render.py:964`, `_build_sources_and_figures`'s re-raise
is at `dash_render.py:11505-11510` and reads:

```python
except Exception as exc:
    raise RuntimeError(
        f"dash_render: failed to build figure '{name}': {exc}"
    ) from exc
```

### Finding 2 — the axis decision cannot see three plot families, and inverts one

`DashRenderer._figure_date_kind` (`dash_render.py:9268-9298`) reads only `xvar`, `yvar` and
`var`. Its key expression, at `:9288-9290`:

```python
name = plot.get(key, "") or (
    plot.get("var", "") if key == "yvar" else "") or fallback
```

`dash.ado:1142-1158` emits three other variable-key shapes:

| plot family | `vfields` emitted by `dash.ado` | seen by `_figure_date_kind`? |
|---|---|---|
| `histogram` `kdensity` | `"var":"<v>"` | folded into the **`yvar`** lookup — wrong axis |
| `rarea` `rbar` `rspike` `rcap` `rline` `rconnected` `rcapsym` `rscatter` `tsrline` | `"yvar1"`, `"yvar2"`, `"xvar"` | `yvar1`/`yvar2` never consulted |
| `pcspike` `pcarrow` `pcbarrow` `pcscatter` | `"y1var"`, `"x1var"`, `"y2var"`, `"x2var"` | none consulted |

The `histogram`/`kdensity` case is the dangerous one, because the dispatch draws that variable
on **X**. `DashRenderer._add_glyph`, `dash_render.py:10415-10421`:

```python
fn = dispatch.get(pt)
if fn is not None:
    # histogram and kdensity are univariate — no xvar positional arg
    if pt in ("histogram", "hist", "kdensity"):
        fn(fig, source, yvar, options, view=view, color_idx=color_idx)
    else:
        fn(fig, source, yvar, xvar, options, view=view, color_idx=color_idx)
```

and `map_histogram` draws it as `left`/`right`. REMAINING.md states the consequence plainly
(work item 10):

> so a `%td` histogram variable is classified as a date on Y (the density axis) and not on X.
> Once the crash above is fixed this yields an exactly inverted figure: a DatetimeAxis on the
> frequency axis and raw SIF integers on the date axis.

So the crash is currently **hiding** a wrong-axis bug: fixing item 9 without items 4 and 10
turns a loud failure into a silent one.

### Finding 3 — the disagreement branch is silent, and literals are unconverted

`_figure_date_kind` ends:

```python
if not kinds:
    return None
if len(kinds) > 1 or None in kinds:
    return None
return kinds.pop()
```

That `return None` at `:9296-9297` is the only diagnostic a user gets when a date variable is
about to be drawn on a linear axis: none (work item 1).

And `scatteri`/`pci` literal coordinates arrive from `dash.ado:1160-1212` as a JSON array of
raw Stata numbers and are placed on the figure unchanged, so an annotation written at a date
coordinate lands at 1970-01-01 (work item 5).

### Finding 4 — the period-kind converter raises where 08-03 required a warning

`_stata_dates_to_datetime` (`dash_render.py:290-355`) builds the five period kinds through the
`_from_parts` closure at `:317-327`:

```python
def _from_parts(year, month):
    frame = pd.DataFrame({
        "year": year, "month": month,
        "day": np.ones(len(year), dtype="float64"),
    })
    ok = frame["year"].notna()
    out = pd.Series(pd.NaT, index=frame.index, dtype="datetime64[ns]")
    if ok.any():
        out.loc[ok] = pd.to_datetime(frame.loc[ok].astype("int64"),
                                      errors="coerce")
    return out
```

and guards it with `except (OverflowError, ValueError, pd.errors.OutOfBoundsDatetime)` at
`dash_render.py:352`. REMAINING.md's measurement of what pandas actually raises:

> when the resulting year exceeds 2262 pandas raises `AssertionError` from
> `blocks.coerce_to_target_dtype(..., raise_on_upcast=True)`, which propagates through
> `DashRenderer._load_data` (dash_render.py:8210) and out of `render()`. Section 08-03's
> action text explicitly requires the opposite: 'Do not raise on out-of-range values ...
> Clamp or coerce and emit a `UserWarning` naming the variable.' The %tc and %td branches do
> honour that (they warn and yield NaT); the period branches do not. Fix: catch `Exception`
> (or `AssertionError`) in the try at dash_render.py:330-358, or build the period series with
> `errors='coerce'` into an object/`datetime64[us]` Series instead of assigning into a
> `datetime64[ns]` block.

This is the one line in the whole audit that moved a **DONE** claim to PARTIAL for S08:

| task | what the refutation found |
|---|---|
| 08-03 | out-of-range period values raise instead of coercing to `NaT` |

### Finding 5 — none of this is testable today, which is why it shipped

REMAINING.md, on `test/test_dates.py::TestDatetimeAxis` (work item 12):

> `test/test_dates.py::TestDatetimeAxis._fig` builds only `{"type": "line", ...}`
> (test/test_dates.py:334-404), so the whole computed-layer and area/spike/r-family surface is
> untested against a date column — which is why a total build failure on 24 of 35 plot types
> passes CI.

and on the Stata side (work items 8, 11, 14):

> Not one of the 25 `.cscript` files touches `sysuse sp500`, a `%t*` display format or a
> datetime axis, so the only Stata-side proof that 08-04 works end to end is an ad-hoc audit
> run.

> `test/test_formats.cscript` — named in 08-01's `<files>` — does not exist, and no .cscript
> in the repo builds any dashboard on a %t variable, so the rc 7102 abort in item 1 is
> invisible to the certification suite. The only date exemplar, examples/sp500_dates.do, uses
> `line` twice and nothing else, so `test_examples_run.cscript` cannot reach a fit, histogram
> or area layer either.

*Confirmed at HEAD:* `ls test/*.cscript | wc -l` → **25**. `test/test_dates.py` defines
`TestDatetimeAxis` at line 334 with helper `_fig` at 336, and every one of its five tests
passes `{"type": "line", ...}`.

Finally, the section's own `<verify>` clause has a second half nothing tests (work item 7):

> `<verify>sp500 renders calendar dates on the x-axis; an auto scatter is byte-identical ids aside.</verify>`

and its TDD stub list asks for *"a scatter of two non-date variables is byte-identical to
before, ids aside"* — against a section carrying this risk note:

> ## Risk: [red] — `_load_data` feeds every code path and `_make_figure` builds every figure. Any behaviour change for non-date data is a bug in this section.

### Where this phase sits in the backlog

| task | Appendix B | Appendix C | total |
|---|---:|---:|---|
| 08-04 Datetime axes | 7 | 14 | **21** |

Of those 21, this phase takes 12 (2 from B, 10 from C) and adds the two S08 main-body items
(13, 14). The nine it leaves are the server renderer, the secondary axis, the
`xlabel()`/`ylabel()`/`xscale(range())` conversions, the `xline()`/`yline()` Spans, the
`_apply_axis_spec` date branch, the `yaxis(2)` partition, the `dash.sthlp` precedence
paragraph, and the dual-axis/parity test cases.

---

## Epics

| Epic | Goal | Items |
|---|---|---|
| **9.A — The build survives a date** | No plot type aborts `dash build` because a variable carries a `%t*` format, and no date value can raise out of the loader. | 3, 6, 9, 13 |
| **9.B — The date lands on the right axis** | Every variable-key shape `dash.ado` emits participates in the axis decision, single-variable plots put the date on X, literal coordinates are on the axis's scale, and a declined datetime axis says so. | 1, 4, 5, 10 |
| **9.C — Proof, in pytest and in Stata** | The date surface is covered by tests that fail before these fixes and pass after, in both test languages the repo uses. | 2, 7, 8, 11, 12, 14 |

---

## User stories

### Epic 9.A — The build survives a date

**US-9.A.1** — *As a Stata user pasting a `twoway` command, I want `dash (scatter close date)
(lfit close date)` to build a dashboard, so that I am not blocked from plotting anything but a
plain line against a date.*

- **Given** `sysuse sp500` (where `date` has display format `%td`)
  **When** I run `dash (scatter close date) (lfit close date)` then `dash build`
  **Then** the command returns rc 0 and the HTML file is non-empty.
- **Given** any of `area`, `spike`, `lfit`, `qfit`, `lfitci`, `qfitci`, `lowess`, `lpoly`,
  `lpolyci`, `fpfit`, `fpfitci`, `histogram`, `kdensity`, `rcap`, `dropline`, `rcapsym`,
  `rscatter`, `mspline`, `mband` with a date on the x axis
  **When** the dashboard is built
  **Then** no `RuntimeError: dash_render: failed to build figure` is raised and Stata does not
  return rc 7102.
- **Given** a fitted layer (`lfit`, `qfit`, `lowess`, `lpoly`, `fpfit`, `mspline`, `mband`) on
  a date x
  **When** the glyph is drawn
  **Then** the fitted x grid is handed to the glyph as datetime64 — not as epoch milliseconds
  and not as SIF day numbers — so the fit lies on the same axis as the scatter it fits.

**US-9.A.2** — *As a Stata user with a long historical or projected series, I want an
out-of-range `%tm`/`%tq`/`%tw`/`%th`/`%ty` value to be dropped with a warning, so that one bad
observation does not destroy the whole dashboard.*

- **Given** a `%tm` column containing a month index whose year exceeds 2262
  **When** `_load_data` converts it
  **Then** that observation becomes `NaT`, a `UserWarning` naming the variable is emitted, and
  no exception escapes `render()`.
- **Given** the same column
  **When** the conversion completes
  **Then** the in-range observations are converted correctly and the figure is drawn from them.

### Epic 9.B — The date lands on the right axis

**US-9.B.1** — *As a Stata user, I want `dash histogram date` to put the dates along the
bottom, so that the graph reads the way Stata's own `histogram` does.*

- **Given** a `%td` variable and `dash histogram date`
  **When** the figure is built
  **Then** `fig.xaxis` contains a `DatetimeAxis` and `fig.yaxis` (frequency/density) does not.
- **Given** the same command
  **When** the axis label is resolved
  **Then** the x-axis label is the date variable's label or name, not an empty string.
- **Given** `dash kdensity date`
  **Then** the same two assertions hold.

**US-9.B.2** — *As a Stata user drawing a range band over time, I want `rbar`/`rcap`/`rarea`
and the paired-coordinate plots to get a datetime axis, so that a date range band is not
plotted as six-digit integers.*

- **Given** a plot of family `rarea` `rbar` `rspike` `rcap` `rline` `rconnected` `rcapsym`
  `rscatter` `tsrline` whose `yvar1`/`yvar2` carry a `%t*` format
  **When** the figure is built
  **Then** the y axis is a `DatetimeAxis` with the kind's `DatetimeTickFormatter`.
- **Given** a `pcspike`/`pcarrow`/`pcbarrow`/`pcscatter` plot whose `x1var`/`x2var` (or
  `y1var`/`y2var`) carry a `%t*` format
  **Then** the corresponding axis is a `DatetimeAxis`.

**US-9.B.3** — *As a Stata user annotating a time series, I want `scatteri`/`pci` coordinates
written as Stata dates to land on the date they name, so that my annotation is not drawn at
1970-01-01.*

- **Given** a figure whose x axis is a `DatetimeAxis` of kind `%td`
  **When** I overlay `scatteri 1200 14977 "peak"`
  **Then** the marker is placed at 1 262 304 000 000 ms (2001-01-02), i.e. the same scale as
  the data column, not at 14 977 ms.
- **Given** a figure with no date axis
  **Then** the literal is placed unchanged — the conversion must not fire.

**US-9.B.4** — *As a Stata user overlaying a date series and a numeric one, I want to be told
that my date variable is being drawn on a linear axis, so that I can split the graph instead
of publishing SIF integers.*

- **Given** two layers on one figure whose x variables disagree (one `%td`, one numeric)
  **When** `_figure_date_kind` declines the datetime axis
  **Then** exactly one `UserWarning` is emitted, naming the date variable that will be drawn
  on a linear axis.
- **Given** a figure where every layer agrees
  **Then** no such warning is emitted.

### Epic 9.C — Proof, in pytest and in Stata

**US-9.C.1** — *As a package maintainer, I want the date path covered for every plot family, so
that a total build failure cannot pass CI again.*

- **Given** the pytest suite
  **When** `TestDatetimeAxis` runs
  **Then** it exercises at least `area`, `spike`, `lfit`, `qfit`, `lowess`, `histogram`,
  `kdensity`, `rbar`, `rcap` on a date column, asserting the build completes and the date
  reaches the glyph on the millisecond scale.

**US-9.C.2** — *As a package maintainer, I want the per-kind tick formatter pinned, so that a
future refactor of `_datetime_formatter_for` cannot silently change how every date axis reads.*

- **Given** a `%ty` figure
  **Then** `fig.xaxis[0].formatter` is a `DatetimeTickFormatter` with `years`, `months` and
  `days` all `"%Y"`.
- **Given** a `%tc` figure
  **Then** its `hours` pattern carries the time (`"%d %b %H:%M"`).
- **Given** a `%tm`, `%tq` or `%th` figure
  **Then** its `days` pattern is month-grain (`"%b %Y"`).

**US-9.C.3** — *As a package maintainer, I want the section's `[red]` risk pinned by a test,
so that any change to `_load_data`/`_make_figure_body` that perturbs a non-date figure is
caught the moment it is made.*

- **Given** a scatter of two non-date variables
  **When** it is rendered twice, before and after a change to the date path
  **Then** the two documents are byte-identical once Bokeh's per-render ids are normalised.

**US-9.C.4** — *As a `dash serve` operator and as a maintainer shipping a release, I want the
date axis proved from Stata, so that the certification suite — not an ad-hoc audit script — is
what stands behind the claim.*

- **Given** `sysuse sp500`
  **When** `test/test_dates.cscript` runs `dash line close date; dash build`
  **Then** it asserts rc 0 and greps `DatetimeAxis` and `DatetimeTickFormatter` out of the
  produced HTML.
- **Given** the same cscript
  **When** it runs `dash (scatter close date) (lfit close date)` and `dash histogram date`
  **Then** both return rc 0 and produce a non-empty file.
- **Given** `test/test_formats.cscript`
  **When** it builds on sp500
  **Then** it asserts the master JSON carries a populated `formats` map, and that
  `dash area close date` returns rc 0.
- **Given** either new cscript
  **When** `test/run_all_cscripts.do` runs
  **Then** the script is registered and reported `[ PASS]` — and a skipped script is reported
  `[ SKIP]`, which is not a pass.

---

## Business requirements

| id | requirement |
|---|---|
| **BR-09.1** | No plot type may abort a dashboard build because one of its variables carries a Stata `%t*` display format. Measured as: every plot type in the conformance corpus returns rc 0 with a date on its natural axis. |
| **BR-09.2** | No date value, in range or out of range, may raise an exception out of `_load_data`. Out-of-range values become `NaT` and emit one `UserWarning` naming the variable, for all seven date kinds — matching what 08-03's action text required and what the `%tc`/`%td` branches already do. |
| **BR-09.3** | A variable Stata draws on the X axis must produce a datetime **X** axis. Specifically, `histogram` and `kdensity` — which `dash.ado` emits as `{"var": …}` — must not put their date on the frequency axis. |
| **BR-09.4** | Every variable-key shape `dash.ado` emits (`xvar`, `yvar`, `var`, `yvar1`/`yvar2`, `y1var`/`x1var`/`y2var`/`x2var`) participates in the date decision, so no plot family is silently excluded from a datetime axis. |
| **BR-09.5** | User-supplied literal coordinates (`scatteri`, `pci`) are interpreted on the same scale as the axis they are drawn on. |
| **BR-09.6** | When dash declines a datetime axis for a figure that contains a date variable, it says so, naming the variable. Silence is not an acceptable outcome for a wrong-looking axis. |
| **BR-09.7** | A figure containing no date variable renders byte-identically to its pre-phase output, ids aside. This is the S08 `[red]` risk and it is enforced by test, not by inspection. |
| **BR-09.8** | Every defect fixed in this phase has a regression test that fails before the fix and passes after it (CLAUDE.md rule 8), and every function added or materially changed has a unit test (rule 4). |
| **BR-09.9** | The date axis is proved from Stata, in the repo's own certification-script convention, not only from pytest. The two cscripts the plan named (`test_dates.cscript`, `test_formats.cscript`) exist and are registered. |

---

## Technical requirements

### 9.A — The build survives a date

**TR-09.1 — Route every `np.array(source.data[…], dtype=float)` coercion through a
datetime-aware extractor.**
There are **37** such sites (`grep -c "np.array(source.data\[" dash_render.py` → 37, confirmed
at HEAD). The 21 mappers REMAINING.md names, with the line numbers it gives:

`map_area:3614`, `map_spike:3787`, `map_lfit:3845`, `map_qfit:3895`, `map_lfitci:3942`,
`map_qfitci:4023`, `map_lowess:4127`, `map_lpoly:4300`, `map_lpolyci:4366`, `map_fpfit:4543`,
`map_fpfitci:4591`, `map_histogram:4666`, `map_kdensity:4830`, `map_rcap:5065`,
`map_dropline:5237`, `map_rcapsym:5321`, `map_rscatter:5889`, `map_mspline:5942`,
`map_mband:6011`.

Mechanism: `_extract_finite(source, varname, allow_datetime=True)` at `dash_render.py:964-995`
already implements the conversion, casting `astype("datetime64[ms]").astype("int64")`. Two
callers pass the flag today — `build_slider` at `:7731` and `build_range` at `:7809`.
`map_histogram` (`:4666`) and `map_kdensity` (`:4830`) call `_extract_finite` **without** the
flag; the other 35 sites use the raw `np.array(...)` form and need an equivalent.

**TR-09.2 — Detect the date column by pandas dtype on a `pd.Series`, never by
`np.issubdtype`.** The CDS column arrives **object-dtype** — a Python list of `Timestamp` —
not datetime64. REMAINING.md is explicit: *"an `np.issubdtype(...)` guard is not sufficient —
route through `pd.Series(col)` / `pd.api.types.is_datetime64_any_dtype` as `_extract_finite`
already does."*

**TR-09.3 — Convert fitted/binned x values back to datetime64 before they reach the glyph.**
`_fit_grid` (`dash_render.py:6419`) returns `np.linspace(lo, hi, n_pts)` over the observed
range; with TR-09.1 applied, `lo`/`hi` are epoch milliseconds, so the grid comes back in
milliseconds and must be cast to datetime64 before being assigned to a glyph's x field.
The same applies to `map_histogram`'s bin edges and `map_kdensity`'s evaluation grid.

**TR-09.4 — Preserve the millisecond unit explicitly.** Use
`.astype("datetime64[ms]").astype("int64")`, as `_extract_finite` does, and not a raw
`astype("int64")` divided by a constant: pandas 3 preserves the inferred resolution, so the
column can be `datetime64[us]` or `[ns]` and a fixed divisor silently yields seconds for one
and milliseconds for the other. `_extract_finite`'s own comment records this.

**TR-09.5 — Widen the exception guard in `_stata_dates_to_datetime`.** The `try` block opens at
`dash_render.py:330` and is guarded by
`except (OverflowError, ValueError, pd.errors.OutOfBoundsDatetime)`.
pandas 3.0.1 raises a bare `AssertionError` from `blocks.coerce_to_target_dtype(...,
raise_on_upcast=True)` when `_from_parts` assigns a post-2262 timestamp into a
`pd.Series(pd.NaT, dtype="datetime64[ns]")` via `out.loc[ok] = pd.to_datetime(...)`.
Two accepted fixes, per REMAINING.md: catch `Exception` (or `AssertionError`) in that `try`,
**or** build the period series with `errors="coerce"` into an object/`datetime64[us]` Series
instead of assigning into a `datetime64[ns]` block. Either way the result must match the
`%tc`/`%td` branches' behaviour: `NaT` plus a `UserWarning` naming the variable. Affected
kinds: **`%tm`, `%tq`, `%th`, `%tw`, `%ty`**.

*Exact positions, measured at HEAD (`187a786`) while writing this phase — the audit's own
citations differ by a few lines and REMAINING.md is itself inconsistent about `_from_parts`,
so implement against these:* the `except` tuple is at **`dash_render.py:357`** (the audit's
Appendix C item cites `:352`); `_from_parts` is **`dash_render.py:318-328`** (Appendix C item 6
cites `:317-327`, the same appendix's 08-03 refutation cites `:318-328`); the
`_stata_dates_to_datetime` call in `_load_data` is at **`dash_render.py:8210`** (item 6 cites
`:8207`, which is the `raw = self.df[col]` line three lines above). Locate by symbol, not by
line, if the file has moved again.

### 9.B — The date lands on the right axis

**TR-09.6 — Teach `_figure_date_kind` every `vfields` shape.** `DashRenderer._figure_date_kind`
is at `dash_render.py:9268-9298`; its key expression at `:9288-9290` is

```python
name = plot.get(key, "") or (
    plot.get("var", "") if key == "yvar" else "") or fallback
```

`dash.ado:1142-1158` emits (verified in the source at HEAD):

```stata
if inlist("`ptype'", "histogram", "kdensity") {
    _dash_json_str "`yvar'" _jyv
    local vfields `""var":"`_jyv'""'
}
else if inlist("`ptype'", "rarea", "rbar", "rspike", "rcap", "rline", ///
                           "rconnected", "rcapsym", "rscatter", "tsrline") {
    ...
    local vfields `""yvar1":"`_jy1'","yvar2":"`_jy2'","xvar":"`_jxv'""'
}
else if inlist("`ptype'", "pcspike", "pcarrow", "pcbarrow", "pcscatter") {
    ...
    local vfields `""y1var":"`_jy1'","x1var":"`_jx1'","y2var":"`_jy2'","x2var":"`_jx2'""'
}
```

Required mapping: `var` → the **`xvar`** branch for `histogram`/`kdensity`; `yvar1`/`yvar2` →
the `yvar` branch; `y1var`/`y2var` → the `yvar` branch and `x1var`/`x2var` → the `xvar` branch
for the `pc*` family.

**TR-09.7 — Fix the axis label for single-variable plots.** `_make_figure_body`
(`dash_render.py:9495`) derives its axis variables at `:9506-9507`:

```python
xvar = plots[0].get("xvar", "") if plots else ""
yvar = plots[0].get("yvar", "") if plots else ""
```

For `histogram`/`kdensity` this yields `""` for `xvar`, so the x-axis label is empty even once
the axis type is right. `xvar` must fall back to `plot.get("var", "")` for those two types.
The dispatch that proves the variable is drawn on X is `_add_glyph` at
`dash_render.py:10415-10421` (quoted in *Why this phase exists*), where the univariate branch
passes the variable positionally as `yvar` and `map_histogram` then draws it as `left`/`right`.

**TR-09.8 — Convert `scatteri`/`pci` literals to the axis scale.** The values are emitted by
`dash.ado:1160-1212` as a JSON array of raw Stata numbers and consumed by `map_scatteri` /
`_add_pc_glyph` (`dash_render.py:10423` onward). The figure's date kind is already computed in
`_make_figure_body` at `dash_render.py:9559-9560`:

```python
_x_date = self._figure_date_kind(plots, "xvar", xvar)
_y_date = self._figure_date_kind(plots, "yvar", yvar)
```

Pass the kind (or the resolved `x_axis_type`) into the literal path and map the coordinate
through `_stata_dates_to_datetime(…, kind).astype("datetime64[ms]").astype("int64")`. The
conversion must be a no-op when the corresponding axis is not a date axis.

**TR-09.9 — Warn on the declined-datetime-axis branch.** At `dash_render.py:9296-9297`:

```python
if len(kinds) > 1 or None in kinds:
    return None
```

Emit one `UserWarning` naming the date variable(s) that will therefore be drawn on a linear
axis. Match the house style of the sibling warning already in `_make_figure_body` at
`:9562-9568`: `"dash: xscale(log) is meaningless for the date variable '{xvar}'; drawing a
date axis instead."` The warning must not fire when `kinds` is empty (no date variable at all)
and must not fire once per plot — the method has two call sites (`:9559-9560`), so a figure
with a disagreeing x **and** y must not produce duplicate noise for the same variable.

**TR-09.10 — Do not disturb the settled behaviour.** The axis type is decided **once**, before
the single `bokeh_figure()` call — commit `c3941de` fixed a bug caused by re-creating a figure
to change its axis type, and `dash_render.py:9556-9558` carries a comment saying so. The
per-kind formatter attachment at `dash_render.py:9598-9603` stays where it is:

```python
for _axis, _kind in ((fig.xaxis, _x_date), (fig.yaxis, _y_date)):
    if _kind:
        _axis.formatter = _datetime_formatter_for(_kind)
```

and `_datetime_formatter_for` (`dash_render.py:247-268`) keeps its current per-kind patterns —
`ty` → `years/months/days` all `"%Y"`; `tc`/`tC` → `hours="%d %b %H:%M"`, `minutes="%H:%M"`,
`seconds="%H:%M:%S"`; `tm`/`tq`/`th` → `days="%b %Y"`; default → `days="%d %b %Y"`.

### 9.C — Proof

**TR-09.11 — Extend `TestDatetimeAxis` past `line`.** `test/test_dates.py:334-404`, helper
`_fig` at `:335-343`, builds `{"type": "line", …}` only. Parametrise over at least `area`,
`spike`, `lfit`, `qfit`, `lowess`, `histogram`, `kdensity`, `rbar`, `rcap`, asserting both that
the build completes and that the date reaches the glyph on the millisecond scale. The existing
`test_the_data_actually_reaches_the_glyph` is the pattern for the second half.

**TR-09.12 — Pin the formatter.** Assert `fig.xaxis[0].formatter` is a `DatetimeTickFormatter`
and that its `years`/`months`/`days`/`hours` strings match the kind: `%ty` → `"%Y"` at all
three grains; `%tc` → an hours pattern carrying the time; `%tm`/`%tq`/`%th` → the month-grain
days pattern. Covers `dash_render.py:9598-9603` and `_datetime_formatter_for` at
`dash_render.py:247-268`.

**TR-09.13 — Pin the byte-identity guard.** Add the `<verify>` clause's second half — *"an auto
scatter is byte-identical ids aside"* — as a test in `test/test_dates.py`, with
`_make_figure_body` (`dash_render.py:9495`) as the code under test. Copy the id-normalisation
pattern from `test/test_layout_tabs.py:447` (`TestTabsWorkUnderEveryLayout`, whose `_normalise`
helper strips Bokeh's per-render `pNNNN` ids via `re.sub(r"\bp\d{3,6}\b", "P", out)`).

**TR-09.14 — Write `test/test_dates.cscript`.** New file, following
`test/test_e2e_single.cscript:1-60` for the preamble and the `c(python_exec)` skip rule
(probe availability with `c(python_exec)`; never by running Python). Contents:
`sysuse sp500` → `dash line close date` → `dash build` → grep the HTML for `DatetimeAxis` and
`DatetimeTickFormatter`; then `dash (scatter close date) (lfit close date)` and
`dash histogram date`, each asserting rc 0 and a non-empty file. Register it in
`test/run_all_cscripts.do` in the existing numbered-block form (`// N. <name>.cscript`, with
`[ RUN ]` / `[ PASS]` / `[ SKIP]` / `[ FAIL]` reporting) — there are 25 registered today.

**TR-09.15 — Write `test/test_formats.cscript`.** Named in 08-01's `<files>`
(`test/test_dates.py, test/test_formats.cscript, scripts/extract_date_truth.do`) and absent.
Minimum, per REMAINING.md: assert rc 0 and a non-empty file for
`dash (scatter close date) (lfit close date)`, `dash histogram date` and
`dash area close date` on `sysuse sp500`, **plus** the master JSON on disk carrying a populated
`formats` map (08-01's own Stata-side test: the JSON maps `date` to `%td`, confirmed with
`describe` rather than assumed). Extend `examples/sp500_dates.do` — which uses `line` twice and
nothing else — with one computed layer, so `test/test_examples_run.cscript:56-84` reaches a
fit/histogram/area layer too. Register in `test/run_all_cscripts.do`.

**TR-09.16 — Environment.** Per the repo's testing memory: cscripts, not `.do` files; run the
Stata suite with `arch -arm64` from `test/`; set `$dash_nobrowser` before any Stata run that
builds a dashboard; **a skip is not a pass**.

---

## Work items

Every item is reproduced with the tag, *Where* and evidence it was handed to this phase with.
Nothing is merged or summarised — items 3/9, 6/13 and 8/11 are near-duplicates from different
audit lenses and are kept as separate items on purpose (see *Risks and sequencing notes*).

---

**1. [func · standalone · S]** — *origin 08-04, Appendix B*

Warn when `_figure_date_kind` declines a datetime axis because the figure's layers disagree,
naming the date variable that will be drawn on a linear axis. Today the method returns None
with no diagnostic.

*Where:* `dash_render.py:9268-9298` (`_figure_date_kind`, the
`if len(kinds) > 1 or None in kinds: return None` branch at `:9296-9297`)

---

**2. [deli · standalone · S]** — *origin 08-04, Appendix B*

Add a test pinning the per-kind `DatetimeTickFormatter` attached to the figure axes — assert
`fig.xaxis[0].formatter` is a `DatetimeTickFormatter` and that its `years`/`months`/`days`/`hours`
strings match the kind (`%ty` → `"%Y"` at all three grains; `%tc` → an hours pattern carrying
the time; `%tm`/`%tq`/`%th` → month-grain days pattern).

*Where:* `test/test_dates.py` (class `TestDatetimeAxis`, currently at `test/test_dates.py:334-404`);
covers `dash_render.py:9598-9603` and `_datetime_formatter_for` at `dash_render.py:247-268`

---

**3. [func · standalone · L]** — *origin 08-04, Appendix C*

Teach the 21 glyph mappers that coerce their source columns with
`np.array(source.data[xvar], dtype=float)` / `_extract_finite(source, var)` to accept a
datetime64 column (convert to epoch ms with the existing `_extract_finite(..., allow_datetime=True)`
path, compute, then convert the fitted/binned x values back to datetime64 before handing them
to the glyph). 08-04's own `_load_data` clause created this: the loader now puts `Timestamp`
objects in the DataFrame, and **20 of 31 plot types abort the ENTIRE dashboard build** the
moment a date variable is on an axis.

*Where:* `dash_render.py:964-995` (`_extract_finite`, which already has the
`allow_datetime=True` branch that only `build_slider:7731` and `build_range:7809` pass); the 21
mappers that do not: `map_area:3614`, `map_spike:3787`, `map_lfit:3845`, `map_qfit:3895`,
`map_lfitci:3942`, `map_qfitci:4023`, `map_lowess:4127`, `map_lpoly:4300`, `map_lpolyci:4366`,
`map_fpfit:4543`, `map_fpfitci:4591`, `map_histogram:4666`, `map_kdensity:4830`,
`map_rcap:5065`, `map_dropline:5237`, `map_rcapsym:5321`, `map_rscatter:5889`,
`map_mspline:5942`, `map_mband:6011`; dispatch at `DashRenderer._add_glyph`
`dash_render.py:10415-10421`; `_fit_grid` `dash_render.py:6419` (the fitted-x grid that must
come back as datetime64)

---

**4. [func · standalone · M]** — *origin 08-04, Appendix C*

Make `_figure_date_kind` read every variable-key shape `dash.ado` actually emits. It reads only
`xvar`, `yvar` and `var`, so three whole plot families are invisible to the date decision, and
for one family it puts the date on the WRONG axis: (a) `histogram`/`kdensity` emit
`{"var":...}` and `_figure_date_kind` counts `var` under the `"yvar"` key, but `map_histogram`
draws that variable as `left`/`right` i.e. on X — so once the crash above is fixed,
`dash histogram datevar` will give a DatetimeAxis on the FREQUENCY axis and a LinearAxis on the
date axis; (b) `rarea`/`rbar`/`rspike`/`rcap`/`rline`/`rconnected`/`rcapsym`/`rscatter`/`tsrline`
emit `yvar1`/`yvar2` and are never consulted, so a date range band gets no datetime y-axis;
(c) `pcspike`/`pcarrow`/`pcbarrow`/`pcscatter` emit `y1var`/`x1var`/`y2var`/`x2var` and get no
datetime axis on either axis.

*Where:* `dash_render.py:9268-9298` (`DashRenderer._figure_date_kind`); its two call sites
`dash_render.py:9559-9560` in `_make_figure_body`; `dash_render.py:10415-10421` (`_add_glyph`,
where the histogram/kdensity `var` is passed positionally as `yvar`); `dash.ado:1142-1158` (the
three alternative `vfields` shapes)

---

**5. [func · standalone · S]** — *origin 08-04, Appendix C*

Convert `scatteri` / `pci` literal coordinates to the datetime axis's millisecond scale when the
figure they are overlaid on has a date axis. The values arrive from `dash.ado` as a JSON array
of raw Stata numbers and are placed on the figure unchanged, so an annotation point written
with a date coordinate lands at 1970-01-01.

*Where:* `dash_render.py` `map_scatteri` / `_add_pc_glyph` (`dash_render.py:10423` onward) and
the `values` consumption path; the date kind is available on the figure via `_figure_date_kind`
at `dash_render.py:9559-9560`; `dash.ado:1160-1212` (emission)

---

**6. [func · standalone · S]** — *origin 08-04, Appendix C*

Stop `_stata_dates_to_datetime` raising on out-of-range period values. `_from_parts` calls
`pd.to_datetime` on a year/month frame; for `%tm`/`%tq`/`%tw` values past pandas' Timestamp
range that raises a bare `AssertionError`, which is not in the
`except (OverflowError, ValueError, pd.errors.OutOfBoundsDatetime)` tuple, so it escapes
`_load_data` and aborts the whole render instead of coercing to NaT with the warning 08-03
specified. (Recorded in REMAINING.md item 2 under 08-04; not in the auditor's list. Reaching it
is 08-04's loader clause.)

*Where:* `dash_render.py:290-355` (`_stata_dates_to_datetime`), specifically `_from_parts`
(`dash_render.py:317-327`) and the `except (OverflowError, ValueError, pd.errors.OutOfBoundsDatetime)`
tuple at `dash_render.py:352`; caller `dash_render.py:8207` in `_load_data`;
`test/test_dates.py:168` (`test_out_of_range_values_warn_rather_than_raise`, which needs
`%tm`/`%tq`/`%tw` parametrisation)

---

**7. [deli · standalone · S]** — *origin 08-04, Appendix C*

Add the task's own `<verify>` clause as a test: "an auto scatter is byte-identical ids aside".
The section's TDD stub list asks for "a scatter of two non-date variables is byte-identical to
before, ids aside" and no such test exists — the identity was only ever measured by hand in an
audit scratch script, so nothing in the suite would catch a future change to
`_load_data`/`_make_figure_body` that perturbs non-date figures. This is the guard the
section's `[red]` risk note exists for.

*Where:* `test/test_dates.py` (add to `class TestDatetimeAxis`, `dash_render.py:9495`
`_make_figure_body` is the code under test); pattern to copy: `test/test_layout_tabs.py:447`

---

**8. [deli · stata · S]** — *origin 08-04, Appendix C*

Add a Stata certification script for the date axis. Not one of the 25 `.cscript` files touches
`sysuse sp500`, a `%t*` display format or a datetime axis, so the only Stata-side proof that
08-04 works end to end is an ad-hoc audit run. Per the repo's own testing convention (cscripts,
not `.do` files) a `test/test_dates.cscript` should build sp500 with a date x-axis and assert
the emitted HTML carries `DatetimeAxis`/`DatetimeTickFormatter`, and — once the crash above is
fixed — that `dash (scatter close date) (lfit close date)` and `dash histogram date` return
rc 0.

*Where:* `test/` (new `test_dates.cscript`, alongside `test/test_e2e_single.cscript` for the
house pattern); `test/run_all_cscripts.do` (registration)

---

**9. [func · standalone · L]** — *origin 08-04, Appendix C*

Fix the hard crash the 08-04 loader conversion introduced: **24 of 35 plot types abort the
entire `dash build`** when their x (or binned) variable is a Stata date. `_load_data` now hands
`GlyphMapper` a datetime64 column, and 37 sites of the form
`np.array(source.data[xvar], dtype=float)` raise
`TypeError: float() argument must be a string or a real number, not 'Timestamp'`, which
`_build_sources_and_figures` (`dash_render.py:11510`) re-raises as RuntimeError and Stata
surfaces as **rc 7102**. The machinery for the fix already exists — `_extract_finite`
(`dash_render.py:964-995`) takes `allow_datetime=True` and casts via
`astype('datetime64[ms]').astype('int64')`, and is called that way at `dash_render.py:7731` and
`:7809` — but the glyph call sites at `:4666` (`map_histogram`) and `:4830` (`map_kdensity`)
omit the flag, and the 35 remaining `np.array(source.data[...], dtype=float)` sites have no
equivalent at all. Note the CDS column arrives object-dtype (a list of `Timestamp`), not
datetime64, so an `np.issubdtype(...)` guard is not sufficient — route through `pd.Series(col)`
/ `pd.api.types.is_datetime64_any_dtype` as `_extract_finite` already does.

*Where:* `dash_render.py:3614-3615` (`map_area`), `:3787-3788`, `:3845-3846` (`map_lfit`),
`:3895-3896` (`map_qfit`), `:3942-3943` (`map_lfitci`), `:4023-4024`, `:4127-4128`
(`map_lowess`), `:4300-4301`, `:4366-4367`, `:4543-4544`, `:4591-4592`, `:5065-5067`,
`:5237-5238`, `:5320-5322` (37 sites total from `grep -c "np.array(source.data\[" dash_render.py`);
`dash_render.py:4666` and `:4830` (`_extract_finite` called without `allow_datetime=True`);
`dash_render.py:964-995` (`_extract_finite`, which already implements the conversion);
`dash_render.py:11505-11510` (the re-raise)

---

**10. [func · standalone · S]** — *origin 08-04, Appendix C*

Correct `_figure_date_kind`'s axis mapping for the single-variable plot types.
`dash.ado:1142-1144` emits `"var"` (not `xvar`/`yvar`) for `histogram` and `kdensity`, and
Stata draws that variable on the X axis. `_figure_date_kind` folds `var` into the **y** lookup
only (`name = plot.get(key, "") or (plot.get("var", "") if key == "yvar" else "") or fallback`),
so a `%td` histogram variable is classified as a date on Y (the density axis) and not on X.
Once the crash above is fixed this yields an exactly inverted figure: a DatetimeAxis on the
frequency axis and raw SIF integers on the date axis. `var` should feed the `xvar` branch for
`histogram`/`kdensity`, and `_make_figure_body`'s `xvar = plots[0].get("xvar", "")`
(`dash_render.py:9506`) should fall back to `var` for those types so the axis label is right
too.

*Where:* `dash_render.py:9268-9298` (`_figure_date_kind`), specifically the `name = ...`
expression at `:9288-9290`; `dash_render.py:9506-9507` (`xvar`/`yvar` derivation in
`_make_figure_body`); `dash.ado:1142-1144` (the `"var"` emission for histogram/kdensity)

---

**11. [deli · stata · S]** — *origin 08-04, Appendix C*

Add a Stata certification script covering the section's own `<verify>` clause end to end. Task
08-04's verify is "sp500 renders calendar dates on the x-axis", and nothing in `test/`
exercises it from Stata: no cscript mentions sp500, `%td` or DatetimeAxis. A cscript that runs
`sysuse sp500; dash line close date; dash build` and greps the produced HTML for
`"DatetimeAxis"` — plus the computed-layer cases `dash (scatter close date) (lfit close date)`
and `dash histogram date` asserting rc 0 — is what would have caught the crash above before it
shipped.

*Where:* `test/` (new cscript, e.g. `test/test_dates.cscript`, registered in
`test/run_all_cscripts.do` alongside the existing 25)

---

**12. [deli · standalone · M]** — *origin 08-04, Appendix C*

Add pytest coverage for non-`line` glyphs on a date variable.
`test/test_dates.py::TestDatetimeAxis._fig` builds only `{"type": "line", ...}`
(`test/test_dates.py:334-404`), so the whole computed-layer and area/spike/r-family surface is
untested against a date column — which is why a total build failure on 24 of 35 plot types
passes CI. Parametrise a date case over at least `area`, `spike`, `lfit`, `qfit`, `lowess`,
`histogram`, `kdensity`, `rbar`, `rcap` and assert the build completes and the date reaches the
glyph on the millisecond scale.

*Where:* `test/test_dates.py:334-404` (`TestDatetimeAxis`, helper `_fig` at `:335-343`)

---

**13. [func · both · M]** — *origin S08, REMAINING.md main body*

Make the period-kind date path (`%ty %tm %tq %th %tw`) coerce out-of-range values to `NaT` with
the existing UserWarning instead of raising a bare pandas `AssertionError` that aborts the whole
render.

*Where:* `dash_render.py:_stata_dates_to_datetime` / `_from_parts`

---

**14. [deli · stata · M]** — *origin S08, REMAINING.md main body*

Write `test/test_formats.cscript`. 08-01 named it; it does not exist, and no cscript touches
sp500 or any `%t` format.

*Where:* `test/test_formats.cscript` (new)

---

## Test plan

House rules that govern all of it: **rule 8** — each of these defects gets a regression test
written *before* the fix, proven to fail against HEAD; **rule 4** — every function added or
materially changed gets a unit test; **the repo's convention** — Stata tests are `.cscript`
files registered in `test/run_all_cscripts.do`, run with `arch -arm64` from `test/`, with
`$dash_nobrowser` set, and *a skip is not a pass*.

### Epic 9.A — The build survives a date

**Write first (must fail at HEAD).**

| test | file | fails at HEAD with |
|---|---|---|
| `test_every_plot_type_builds_with_a_date_x` — parametrised over `area`, `spike`, `lfit`, `qfit`, `lfitci`, `qfitci`, `lowess`, `lpoly`, `lpolyci`, `fpfit`, `fpfitci`, `histogram`, `kdensity`, `rcap`, `dropline`, `rcapsym`, `rscatter`, `mspline`, `mband` | `test/test_dates.py` (extend `TestDatetimeAxis`) | `RuntimeError: dash_render: failed to build figure 'g1': float() argument must be a string or a real number, not 'Timestamp'` |
| `test_out_of_range_period_values_warn_rather_than_raise[tm/tq/tw/th/ty]` — parametrise the existing `test/test_dates.py:168` case over the five period kinds | `test/test_dates.py` | bare `AssertionError: Something has gone wrong, please report a bug at pandas` |
| `test_date_build_returns_rc_0` — `dash (scatter close date) (lfit close date)`, `dash histogram date`, `dash area close date` on `sysuse sp500` | `test/test_dates.cscript`, `test/test_formats.cscript` | rc 7102 |

**Unit tests (rule 4).**

- The new datetime-aware coercion helper (whether a new function or an extension of
  `_extract_finite`): object-dtype list-of-`Timestamp` input → float ms array; datetime64[us]
  input and datetime64[ns] input → **the same** ms values (guards TR-09.4); plain float input →
  unchanged; `None`/`NaN` dropped; empty column → empty array.
- `_fit_grid` round trip: ms grid in → datetime64 out, endpoints equal to the observed
  min/max of the date column.
- `_stata_dates_to_datetime` per kind, in-range and out-of-range, asserting `NaT` + exactly one
  `UserWarning` naming the variable and **no** exception, for all seven kinds. The existing
  `TestEpochConversion` (`test/test_dates.py:99`) is the in-range half; the out-of-range half is
  new.

**Integration / cscript.**

- `test/test_dates.cscript`: `sysuse sp500`; `dash line close date`; `dash build`; assert rc 0,
  file non-empty, HTML contains `DatetimeAxis` and `DatetimeTickFormatter`; then the two
  computed-layer commands asserting rc 0.
- `test/test_formats.cscript`: the three builds above plus the master-JSON assertion that
  `formats` maps `date` to `%td` (confirm with `describe`, do not assume).
- Both registered in `test/run_all_cscripts.do`; both following
  `test/test_e2e_single.cscript:1-60` for the preamble and the `c(python_exec)` skip rule.

**Non-vacuity (mutation).**

| break this | the test that must die |
|---|---|
| revert one mapper — put `np.array(source.data[xvar], dtype=float)` back in `map_lfit` | `test_every_plot_type_builds_with_a_date_x[lfit]` |
| drop the `.astype("datetime64[ms]")` step and use a bare `astype("int64")` | the dtype-resolution unit test (ns vs us give different numbers) |
| remove `AssertionError` from the widened `except` | `test_out_of_range_period_values_warn_rather_than_raise[tm]` |
| swallow the warning while still returning `NaT` | the same test's warning assertion |
| have `_fit_grid`'s consumer skip the datetime64 cast back | the "fit lies on the same axis as its scatter" assertion in `test_every_plot_type_builds_with_a_date_x[lfit]` |

### Epic 9.B — The date lands on the right axis

**Write first (must fail at HEAD).**

| test | file | fails at HEAD because |
|---|---|---|
| `test_a_histogram_of_a_date_puts_the_date_on_x` — `DatetimeAxis` in `fig.xaxis`, none in `fig.yaxis` | `test/test_dates.py` | `var` is folded into the `yvar` lookup, so the axis is inverted (masked today by the rc 7102 crash — write it against the item-9 fix) |
| `test_a_kdensity_of_a_date_puts_the_date_on_x` | `test/test_dates.py` | same |
| `test_a_histogram_of_a_date_labels_the_x_axis` — label is the variable's label/name, not `""` | `test/test_dates.py` | `plots[0].get("xvar", "")` is `""` for the univariate shape (`dash_render.py:9506`) |
| `test_an_r_family_date_gets_a_datetime_y_axis` — `rbar`/`rcap` with `%td` `yvar1`/`yvar2` | `test/test_dates.py` | `yvar1`/`yvar2` are never consulted |
| `test_a_pc_family_date_gets_a_datetime_axis` — `pcspike` with `%td` `x1var`/`x2var` | `test/test_dates.py` | `x1var`/`x2var` are never consulted |
| `test_scatteri_literal_lands_on_the_date` — literal `14977` on a `%td` axis renders at 2001-01-02, not at 14 977 ms | `test/test_dates.py` | literals pass through unconverted |
| `test_disagreeing_layers_warn_and_name_the_variable` | `test/test_dates.py` | `_figure_date_kind` returns `None` silently |
| `test_agreeing_layers_do_not_warn` (the negative case) | `test/test_dates.py` | — must pass before and after |

**Unit tests (rule 4).** `_figure_date_kind` called directly with each of the four `vfields`
shapes from `dash.ado:1142-1158` — `{"xvar","yvar"}`, `{"var"}`, `{"yvar1","yvar2","xvar"}`,
`{"y1var","x1var","y2var","x2var"}` — asserting the kind is returned on the correct axis key and
`None` on the other; plus the two bail branches (`len(kinds) > 1`, `None in kinds`) and the
empty-`kinds` branch, which must return `None` **without** warning.

**Integration / cscript.** `test/test_dates.cscript` covers `dash histogram date` end to end
from Stata; `test/test_formats.cscript` adds `dash area close date`. Together they are the
Stata-side proof of BR-09.1 and BR-09.3.

**Non-vacuity (mutation).**

| break this | the test that must die |
|---|---|
| put `var` back under the `yvar` branch only | `test_a_histogram_of_a_date_puts_the_date_on_x` |
| remove the `xvar` fallback to `var` at `dash_render.py:9506` | `test_a_histogram_of_a_date_labels_the_x_axis` |
| drop `yvar1`/`yvar2` from the key list | `test_an_r_family_date_gets_a_datetime_y_axis` |
| make the literal conversion unconditional (fire on a non-date axis too) | a negative test asserting a numeric `scatteri` is unchanged |
| downgrade the new warning to a `print`/log line | `test_disagreeing_layers_warn_and_name_the_variable` (assert via `warnings.catch_warnings(record=True)`, as `test_log_scale_on_a_date_variable_warns_and_stays_a_date` already does) |

### Epic 9.C — Proof

**Write first.** Every item in this epic *is* a test, so "fails first" means: each one must be
demonstrated red against HEAD before its fix lands, and the two formatter/identity tests must be
red against a deliberately mutated `_datetime_formatter_for` / `_make_figure_body` — otherwise
they are vacuous by construction.

**Coverage.**

- `test/test_dates.py` — the formatter assertion (item 2), the non-`line` parametrisation
  (item 12), the byte-identity guard (item 7), all inside or alongside `TestDatetimeAxis`
  (`:334-404`).
- `test/test_dates.cscript` (items 8, 11) and `test/test_formats.cscript` (item 14) — new,
  registered in `test/run_all_cscripts.do`, raising the suite from 25 to 27 cscripts.
- `examples/sp500_dates.do` gains one computed layer so
  `test/test_examples_run.cscript:56-84` reaches a fit/histogram/area layer.

**Non-vacuity (mutation).**

| break this | the test that must die |
|---|---|
| change `_datetime_formatter_for`'s `ty` branch from `years/months/days = "%Y"` to the default patterns | the item-2 formatter test |
| drop the `hours="%d %b %H:%M"` pattern from the `tc`/`tC` branch | the item-2 formatter test, `%tc` case |
| add any unconditional change to `_make_figure_body` that touches a non-date figure (e.g. always set `fig.xaxis.formatter`) | the item-7 byte-identity test |
| make `_normalise` in the identity test strip too much (e.g. all digits) | guard with a companion assertion that two *deliberately different* documents still compare unequal — the pattern `test/test_layout_tabs.py` already uses (`assert _normalise(without) != _normalise(with_tabs)`) |
| comment out `dash histogram date` in the cscript | nothing — therefore also assert the cscript's own command count, or keep each command's `rc` assertion explicit so a deletion is visible in the diff |
| let a cscript be reported `[ SKIP]` on a missing `c(python_exec)` and count it as green | the runner accounting: a skip is not a pass; the release gate requires *honest skips* |

---

## Definition of done

**Functional**

- [ ] `grep -c "np.array(source.data\[" dash_render.py` no longer reports any site that can
      receive a date column without a datetime-aware path (all 37 audited, each either routed
      through the extractor or proven unreachable by a date column, with the reason recorded).
- [ ] `map_histogram` (`dash_render.py:4666`) and `map_kdensity` (`:4830`) call `_extract_finite`
      with `allow_datetime=True`.
- [ ] Every plot type in the corpus builds with a date on its natural axis; no `RuntimeError`
      from `dash_render.py:11505-11510`; no rc 7102 from Stata.
- [ ] Fitted and binned x values reach the glyph as datetime64, so a fit overlays its scatter.
- [ ] `_stata_dates_to_datetime` cannot raise for any of the seven kinds: out-of-range →
      `NaT` + one `UserWarning` naming the variable.
- [ ] `_figure_date_kind` consumes `xvar`, `yvar`, `var`, `yvar1`/`yvar2` and
      `y1var`/`x1var`/`y2var`/`x2var`, with `var` mapped to **X**.
- [ ] `_make_figure_body`'s `xvar` falls back to `var` for `histogram`/`kdensity`, so the x-axis
      label is populated.
- [ ] `scatteri`/`pci` literals are converted to the axis's millisecond scale when — and only
      when — that axis is a date axis.
- [ ] The declined-datetime-axis branch emits exactly one `UserWarning` naming the variable,
      and stays silent when no date variable is present.
- [ ] The axis type is still decided once, before the single `bokeh_figure()` call
      (`dash_render.py:9556-9558`); commit `c3941de`'s bug is not reintroduced.

**Tests**

- [ ] Each fix above has a regression test that was demonstrated **red at HEAD** and is green
      after (rule 8), with the red run recorded in the commit message.
- [ ] Each new or materially changed function has a unit test (rule 4).
- [ ] `TestDatetimeAxis` exercises at least `area`, `spike`, `lfit`, `qfit`, `lowess`,
      `histogram`, `kdensity`, `rbar`, `rcap` on a date column.
- [ ] The per-kind `DatetimeTickFormatter` is pinned for `%ty`, `%tc` and `%tm`/`%tq`/`%th`.
- [ ] The `<verify>` byte-identity guard exists and is non-vacuous.
- [ ] `test/test_dates.cscript` and `test/test_formats.cscript` exist, are registered in
      `test/run_all_cscripts.do`, and pass — not skip — on a machine with `c(python_exec)` set.
- [ ] `examples/sp500_dates.do` carries one computed layer.
- [ ] Full pytest suite green (baseline for comparison: 3,498 passed / 37 skipped at HEAD);
      full cscript suite green at 27/27 with honest skip accounting.

**Hygiene**

- [ ] `REMAINING.md` untouched.
- [ ] Work done on `feature/batch4-interactive-layer` (or a branch off it); nothing committed
      directly to `main`; the merge command is provided rather than run.
- [ ] Commit messages describe the change only.

---

## Risks and sequencing notes

**The crash is currently masking the wrong-axis bug.** Fix item 9/3 first and
`dash histogram datevar` stops aborting — and starts drawing a DatetimeAxis on the *frequency*
axis with SIF integers along the bottom. That is a worse failure than rc 7102 because it looks
like a graph. **Land items 4 and 10 in the same change as 9 and 3, or land 4/10 first.**

**Items 3 and 9 are one body of work, and items 6 and 13 are another.** They are listed
separately because two independent audit lenses found them and this document may not drop
anything it was handed. Implement 3+9 as a single change (the mapper-side and call-site-side
views of the same 37 coercion sites) and 6+13 as a single change (the `except` tuple at
`dash_render.py:352` and the `_from_parts` assignment at `:317-327`). Items 8 and 11 both ask
for `test/test_dates.cscript` with overlapping contents; write one file satisfying both, then
tick both. Note item 13's renderer tag is **both** — `_stata_dates_to_datetime` is a
module-level helper, so fixing it also fixes the emitted server app *once* the Dates II phase
teaches that app's loader to call it. Nothing in this phase makes that call site exist.

**The `[red]` risk is real and this phase is the one it was written for.** The section note
says: *"`_load_data` feeds every code path and `_make_figure` builds every figure. Any behaviour
change for non-date data is a bug in this section."* Every change here touches one of those two
methods or the mappers they feed. The item-7 byte-identity test is the cheapest possible guard
and should be written **before** the first functional change, not last — it is the only thing
standing between a coercion refactor and a silent regression across all 36 plot types.

**Do not fix the datetime problem by converting the column back to float in the loader.** The
loader's `Timestamp` column is what makes the hover, filter-widget, facet-label, marker-label
and KPI work of 08-05 possible; reverting it would trade 24 broken plot types for five broken
display surfaces. The fix belongs at the coercion sites.

**`np.issubdtype` will look like it works and will not.** The CDS column is object-dtype — a
Python list of `Timestamp` — because Bokeh's `ColumnDataSource` holds it that way. Any guard
written against the *DataFrame* dtype will pass its author's ad-hoc check and fail in the
renderer. Use `pd.Series(col)` + `pd.api.types.is_datetime64_any_dtype`, exactly as
`_extract_finite` already does.

**Resolution drift is a silent-wrong-numbers risk.** pandas 3 preserves the inferred resolution,
so the same code path yields `datetime64[us]` for one column and `[ns]` for another. Always cast
to `datetime64[ms]` explicitly before `astype("int64")`; a fixed divisor gives seconds for one
and milliseconds for the other, and a plot drawn in seconds looks plausible.

**Scope boundary.** Five date defects in the 08-04 backlog are deliberately **out** of this
phase and must not be half-started here: `ServerAppBuilder` date support (including the emitted
loader's display-string recovery), the secondary-axis datetime path
(`dash_render.py:9684`, `:9719`), the `xlabel()`/`ylabel()`/`xscale(range())` millisecond
conversions (`_apply_axis_spec` `:9137-9150`, `:9750-9773`), the `xline()`/`yline()` `Span`
conversions (`:9843-9858`), and the `yaxis(2)` partition that stops a secondary layer poisoning
the primary axis (`:9286-9297`). Two of those touch `_figure_date_kind` and `_apply_axis_spec`,
which this phase also edits — expect a merge seam there, and keep this phase's changes to
`_figure_date_kind` confined to the key-shape lookup and the warning so the partition work can
land cleanly on top.

**Stata-side cost.** The cscripts need a machine with Stata and `c(python_exec)` set; on a
machine without it they report `[ SKIP]`. Per the project's own rule, a skip is not a pass — the
phase is not done until both new cscripts have been observed `[ PASS]` on a real Stata run with
`arch -arm64` from `test/` and `$dash_nobrowser` set.
