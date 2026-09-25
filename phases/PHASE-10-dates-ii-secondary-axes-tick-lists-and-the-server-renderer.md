# Phase 10 — Dates II: secondary axes, tick lists and the server renderer

**Purpose.** Phase 9 makes a Stata date survive the loader and reach a primary
axis in `dash build`. This phase finishes the job in the two places Phase 9
does not reach. First, `dash serve`: the emitted Bokeh app has *no* date
handling at all — its loader coerces every non-string column with
`pd.to_numeric`, which either turns a date into a raw day number or, when the
column arrived as display text, deletes every row of the dataset. Second,
every value on a date figure that is **not the data itself**: the secondary
y2/x2 axis and its range, the explicit tick lists in `xlabel()`/`ylabel()`,
`minmax`, the bounds in `xscale(range())`/`yscale(range())`, the reference
lines in `xline()`/`yline()`, and the `format()` sub-option. Bokeh's
`DatetimeAxis` works in **epoch milliseconds**; Stata hands us **SIF day (or
month, or quarter, or millisecond) numbers**; today six separate code blocks
push the Stata number straight onto the millisecond axis, so `xline(td(01jan2001))`
— SIF day 14977 — is drawn 14.977 *seconds* after 1970-01-01 and vanishes off
the left edge of the figure without a warning. One further defect in the same
family is the inverse: a single `yaxis(2)` layer carrying a numeric variable
strips the DatetimeAxis off the **primary** axis, which was correct until the
second layer was added. Eight items, one ultraplan task (08-04), two renderers.

---

## At a glance

| | |
|---|---|
| **Work items** | 8 (numbered 1–8; every one appears in *Work items* below) |
| **Functional vs deliverable** | 7 functional · 1 deliverable (item 4, the two missing coverage cases) |
| **Effort mix** | 3 medium (items 1, 2, 3) · 5 small (items 4, 5, 6, 7, 8) |
| **Renderers touched** | standalone 5 (items 2, 3, 6, 7, 8) · server 2 (items 1, 5) · both 1 (item 4) |
| **Ultraplan tasks discharged** | **08-04** — "Convert in the loader and give date figures a datetime axis" (section 08, *Formats, dates, labels*). Specifically its clauses *"Apply the same treatment to the secondary-axis path"*, *"An explicit `xlabel()` tick list must still win"* and *"Attach a `DatetimeTickFormatter` matched to the date kind"*, plus the whole of 08-04 in server mode. |
| **Section status this moves** | S08 = 1 DONE / 5 PARTIAL. 08-04 is PARTIAL; it closes only when **Phase 9 + Phase 10 + Phase 30 item 1** (the `dash.sthlp` precedence paragraph) have all landed. |
| **Origin of the items** | REMAINING.md Appendix B, `08-04` (items 1–4) · Appendix C, `08-04` "14 further items" (items 5–8) |
| **Depends on** | **Phase 09** (Dates I) — its glyph-mapper crash fix and its `_figure_date_kind` key-shape fix both land in code this phase edits. |
| **Unblocks** | **Phase 13** (Formats II: served KPI/filter/mlabel date formatting is dead code until the emitted loader produces a datetime64 column) · **Phase 15/16** (axis grammar on date axes, and its server port) · **Phase 27** (server secondary axis, and the filter callback that must update the y2 range) |
| **Files** | `dash_render.py` (both renderers) · `test/test_dual_axis.py` · `test/test_mode_parity.py` · `test/test_dates.py` · `test/test_axis_options.py` · `test/conftest.py` · `test/test_e2e_serve.cscript` |

---

## Why this phase exists

Everything below is copied from `REMAINING.md`, which states that every claim
in it was produced by running the code at `187a786` on
`feature/batch4-interactive-layer`. A developer should not need to open that
file to work this phase.

### 1. What already works — the baseline this phase must not break

> **08-04 — Convert in the loader, give date figures a datetime axis · PARTIAL**
>
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

That machinery is real and is the model every item here copies:

- `_stata_date_kind(fmt)` (`dash_render.py:271`) classifies a Stata display
  format into one of the seven kinds, case-sensitively (`%tc` ≠ `%tC`).
- `_stata_dates_to_datetime(series, kind)` (`dash_render.py:290-355`) converts
  SIF numbers to `datetime64`.
- `_datetime_formatter_for(kind)` (`dash_render.py:247-268`) is the per-kind
  formatter table — the exact measurements this phase must reproduce on the
  secondary axis:

  | kind | `years` | `months` | `days` | `hours` / `minutes` / `seconds` |
  |---|---|---|---|---|
  | `ty` | `%Y` | `%Y` | `%Y` | — |
  | `tc`, `tC` | `%Y` | `%b %Y` | `%d %b %Y` | `%d %b %H:%M` / `%H:%M` / `%H:%M:%S` |
  | `tm`, `tq`, `th` | `%Y` | `%b %Y` | `%b %Y` | — |
  | default (`td`, `tw`) | `%Y` | `%b %Y` | `%d %b %Y` | — |

- The axis type is decided **once**, before the single `bokeh_figure()` call
  (`dash_render.py:9561-9591`), with a comment that says re-creating a figure to
  change its axis type was a real bug fixed in commit `c3941de`. Nothing in this
  phase may reintroduce that pattern.

### 2. `dash serve` has no dates whatsoever

> **Remaining:**
> 1. **Server mode has no date handling whatsoever.** In the emitted app:
>    `DatetimeAxis` 0, `DatetimeTickFormatter` 0, `date_vars` 0,
>    `numeric_formats` 0. Built both renderers from one spec carrying
>    `formats:{"d":"%td"}` — standalone gave `DatetimeAxis`/`DatetimeTickFormatter`,
>    the served app gave `LinearAxis`/`BasicTickFormatter`, i.e. raw day numbers
>    on screen. This is the whole of 08-04 missing from `dash serve`.

The two emitted blocks responsible. The **only** coercion in the generated
app's loader, `dash_render.py:13161-13165` (these are source *strings* that
`ServerAppBuilder` writes into `app.py`):

```python
"    # Convert to numeric where possible",
"    for col in df.columns:",
"        if not type_is_str.get(col, False):",
"            df[col] = pd.to_numeric(df[col], errors='coerce')",
```

and the emitted figure keywords, `dash_render.py:13851-13855`, where only
`'log'` is ever considered:

```python
"        _xs_toks = go.get('xscale', '').lower().split()",
"        _ys_toks = go.get('yscale', '').lower().split()",
"        if 'log' in _xs_toks: _fig_kw['x_axis_type'] = 'log'",
"        if 'log' in _ys_toks: _fig_kw['y_axis_type'] = 'log'",
"        fig = bokeh_figure(**_fig_kw)",
```

The emitted facet and `by(total)` figures repeat the omission at
`dash_render.py:15131` (`_fac_fig = bokeh_figure(**_fac_kw)`) and
`dash_render.py:15228` (`_tot_fig = bokeh_figure(...)`).

The forwarding tuple that decides which module-level helpers exist inside the
generated module, `ServerAppBuilder._shared_module_lines`,
`dash_render.py:12392-12397`:

```python
for _fn_name in ("_parse_textbox_opt",
                 "_optional_import", "_extract_finite", "_apply_jitter",
                 "_with_color_alias", "_jitter_seed", "_floats_only",
                 "_parse_stata_numeric_fmt", "_format_stata_numeric",
                 "_format_date_value_standalone", "_fp_grid",
                 "_fp_report_unsupported", "_betacf", "_betainc",
                 "_t_cdf", "_t_ppf"):
```

`_stata_date_kind`, `_stata_dates_to_datetime` and `_datetime_formatter_for`
are **not** in that tuple, so they do not exist in the generated module at all.

### 3. Worse than a wrong scale: the emitted loader deletes the data

From Appendix C (item 5 of this phase):

> The emitted server loader must ALSO recover the display-string date transport
> before `pd.to_numeric` destroys it, mirroring `_load_data`'s `else:` branch
> (dash_render.py:8208-8226). Today a `%td` column that arrives as text
> ("02jan2001") is coerced to NaN in the generated app and the served figure
> gets **ZERO rows**, not a wrong-scale axis.

The standalone branch to mirror, `dash_render.py:8208-8226`:

```python
            raw = self.df[col]
            numeric = pd.to_numeric(raw, errors="coerce")
            if numeric.notna().any() or raw.isna().all():
                converted = _stata_dates_to_datetime(numeric, kind)
            else:
                # Legacy transport: jsonio renders a %t* variable THROUGH its
                # display format and emits a string ("02jan2001"), so a spec
                # from an older dash.ado carries text here.  Coercing it to
                # NaN drops every row of the dataset, which is how
                # `dash line close date` came to produce an empty dashboard.
                converted = pd.to_datetime(raw.astype(str).str.strip(),
                                            errors="coerce")
                if converted.isna().all() and raw.notna().any():
                    warnings.warn(...)
```

The same appendix entry records the one piece of good news in this phase:

> Related and worth knowing before starting: the generated app **ALREADY**
> carries the date machinery it needs — `_format_date_value_standalone` is
> forwarded (dash_render.py:12395, lands at app.py:1410 and is called at
> app.py:3672 from the forwarded GlyphMapper mlabel path) and the slider
> helper's `allow_datetime` branch (app.py:1221-1248, which does the correct
> `.astype('datetime64[ms]').astype('int64')`) is present. Both are unreachable
> solely because the emitted loader never creates a datetime64 column, so
> fixing the loader **lights up existing code** rather than requiring new copies.

The `allow_datetime` branch referred to is `_extract_finite`
(`dash_render.py:964-995`), whose own comment states the resolution trap this
phase must respect:

```python
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
```

Only two call sites pass the flag: `build_slider` at `dash_render.py:7731` and
`build_range` at `dash_render.py:7809`.

### 4. Six blocks that put a Stata number on a millisecond axis

The arithmetic, once, because every item below is an instance of it. Stata
transports a `%td` date as a SIF **day** number (01jan2001 = 14977 — the value
`test/test_dates.py:337` already uses as its fixture). Bokeh's `DatetimeAxis`
reads **epoch milliseconds**. 14977 milliseconds is 14.977 seconds after
1970-01-01. So an unconverted user value is not merely inaccurate; it is
roughly 31 years away, off the rendered range, invisible, and silent.

| block | file:line | what it does today | consequence on a date axis |
|---|---|---|---|
| secondary range | `dash_render.py:2461` in `_compute_secondary_range` (`:2433-2467`) | `pd.to_numeric(df[varname], errors="coerce")` on a `datetime64` column | microseconds or nanoseconds depending on the resolution pandas inferred — "1000x too large" as measured in the 09-02 appendix |
| secondary axis model | `dash_render.py:9684` (`_y2_ax`), `:9719` (`_x2_ax`) | `(LogAxis if _y2_log else LinearAxis)(...)` | never a `DatetimeAxis`, never a `DatetimeTickFormatter`, whatever the layer's variable is |
| explicit tick list | `dash_render.py:9149-9150` | `axis_obj.ticker = FixedTicker(ticks=spec["ticks"])` with the raw Stata numbers | ticks at 1970-01-01 + a few seconds |
| `minmax` | `dash_render.py:9137-9143` | `vals = pd.to_numeric(col, errors="coerce")`, then `FixedTicker(ticks=[float(vals.min()), float(vals.max())])` | same 1000× resolution bug as the secondary range |
| `xscale(range())` | `dash_render.py:9750-9773` | `_Rng(float(_new_lo), float(_new_hi))`, and a one-bound fallback that reads `pd.to_numeric(self.df[_col])` | the graph is ranged to a few seconds around the epoch |
| `xline()` / `yline()` | `dash_render.py:9843-9858` | `fig.add_layout(Span(location=float(xline_val), dimension="height", **_xl_kw))` | the reference line is drawn off-figure, silently |

`_apply_axis_spec` (`dash_render.py:9112`, one call site at `:9913` which
already passes the variable name) has a seventh defect in the same method —
the `format()` sub-option block at `dash_render.py:9159-9170`:

```python
        fmt = spec["format"] or getattr(self, "numeric_formats", {}).get(
            varname, "")
        if fmt:
            pattern = _stata_numeric_pattern(fmt)
            if pattern is not None:
                axis_obj.formatter = NumeralTickFormatter(format=pattern)
            elif spec["format"] and _stata_date_kind(fmt) is None:
                warnings.warn(
                    f"dash: axis format({spec['format']}) is not a numeric "
                    f"display format dash reproduces; the ticks are "
                    f"unformatted.", UserWarning,
                )
```

Two consequences, both from Appendix C:

1. `xlabel(, format(%9.0fc))` — or any numeric picture **inherited** from
   `self.numeric_formats` — overwrites the `DatetimeTickFormatter` that
   `_make_figure_body` attached at `:9598-9603` with a `NumeralTickFormatter`,
   so the ticks read as epoch milliseconds with thousands separators.
2. `xlabel(, format(%tdDD/NN/CCYY))` — a Stata **date** picture, the natural
   way to ask for a tick style — is silently discarded: `_stata_numeric_pattern`
   returns `None` and the `elif` guard *explicitly excludes date formats*, so
   nothing is applied and nothing is said. Task 08-04's action clause promises a
   formatter "matched to the date kind"; a user-supplied kind is never honoured.

### 5. A secondary layer poisons the primary axis

`_figure_date_kind` (`dash_render.py:9268-9298`) folds every layer of the
figure into one `kinds` set and bails if they disagree:

```python
        kinds = set()
        for plot in plots or []:
            name = plot.get(key, "") or (
                plot.get("var", "") if key == "yvar" else "") or fallback
            if not name:
                continue
            kinds.add(self.date_vars.get(name))
        if not kinds:
            return None
        if len(kinds) > 1 or None in kinds:
            return None
        return kinds.pop()
```

Both call sites (`dash_render.py:9559-9560`) pass the **unpartitioned** `plots`
list:

```python
        _x_date = self._figure_date_kind(plots, "xvar", xvar)
        _y_date = self._figure_date_kind(plots, "yvar", yvar)
```

From Appendix C:

> Today a single secondary-axis layer **POISONS** the primary axis: a graph
> whose primary y is a date loses its DatetimeAxis entirely as soon as any
> `yaxis(2)` layer carries a numeric variable, because both layers land in the
> same `kinds` set and the `None in kinds` branch bails. This is distinct from
> the secondary-axis item already reported — the damage here is to the PRIMARY
> axis, which was working before the second layer was added.

The predicate needed already exists downstream: `dash_render.py:9678-9719`
splits layers by `str(opts.get(axis_key, "1")).strip() != str(axis_number)`.

### 6. Nothing in the suite would catch any of this

- `test/test_dual_axis.py` is **261 lines** and has **no date case**. Its
  helper `_make_spec_and_data` (`:23-57`) builds `build_options` with no
  `formats` key at all, so no test in that file can produce a date column.
- `test/test_mode_parity.py:74` — the corpus helper `_spec` hardcodes
  `"formats": {}`, so the 17-entry `CORPUS` at `test/test_mode_parity.py:187-284`
  can never exercise a served date. The corpus compares glyph properties,
  annotations and figure chrome (`_glyph_profile`, `_annotations`, `_chrome`);
  it does not compare axis **types** at all.
- `test/test_dates.py::TestDatetimeAxis` (`:334-404`) builds only
  `{"type": "line", ...}` figures with a primary date axis.
- `test/test_axis_options.py` has `TestAxisLabelGrammar` (`:112`),
  `TestAxisScale` (`:228`), `TestReferenceLines` (`:565`) and
  `TestSecondaryAxisRange` (`:851`) — none of them with a `formats` map, because
  `conftest.make_spec` (`test/conftest.py:152`) takes no `formats` argument.

---

## Epics

| epic | goal | items |
|---|---|---|
| **E10.1 — Dates reach `dash serve`** | The generated Bokeh app loads, types and formats a `%t*` column exactly as `DashRenderer` does, and stops deleting string-transported dates. | 1, 5 |
| **E10.2 — User-supplied values on a date axis** | Every number the user writes in Stata date units — secondary-axis data, tick lists, `minmax`, `range()` bounds, reference lines, `format()` pictures — lands where Stata would put it. | 2, 3, 7, 8 |
| **E10.3 — The axis-kind decision, and proof in both modes** | The date decision is made per axis rather than per figure, and the two coverage gaps 08-04's scope implies are closed. | 4, 6 |

---

## User stories

### E10.1 — Dates reach `dash serve`

**US-10.1.1** — *As a `dash serve` operator, I want a `%td` variable to draw as
calendar dates in the served dashboard, so that the interactive app I hand to
colleagues says "Jan 2001" where the static HTML says "Jan 2001".*

- **Given** a spec whose `build_options.formats` is `{"d": "%td"}` and a graph
  `line v d`,
  **when** the app is built by `ServerAppBuilder` and `make_document` is run,
  **then** the figure's x axis is a `DatetimeAxis` carrying a
  `DatetimeTickFormatter`, not a `LinearAxis` with a `BasicTickFormatter`.
- **Given** the same spec,
  **when** both renderers are built from it,
  **then** the served column's dtype and the standalone column's dtype are the
  same, and both figures report the same `x_axis_type`.
- **Given** a `%tc` variable,
  **when** the served figure is built,
  **then** its formatter's `hours` pattern is `"%d %b %H:%M"` — the same value
  `_datetime_formatter_for` returns in standalone.

**US-10.1.2** — *As a dashboard viewer, I want the served graph to contain my
data, so that a date variable does not silently produce an empty chart.*

- **Given** a data JSON in which a `%td` column arrives as display text
  (`"02jan2001"`) rather than as a number,
  **when** the generated app loads it,
  **then** the column is recovered as `datetime64` and the figure receives the
  full row count — **not** zero rows.
- **Given** a text column the app genuinely cannot parse as a date,
  **when** the generated app loads it,
  **then** a `UserWarning` naming the variable and its display format is
  emitted, mirroring `dash_render.py:8218-8225`, rather than a silent empty
  frame.
- **Given** a spec with **no** `formats` key (an older `dash.ado`),
  **when** the app is built,
  **then** every column takes exactly the path it takes today.

### E10.2 — User-supplied values on a date axis

**US-10.2.1** — *As a Stata user pasting a `twoway` command, I want
`yaxis(2)` on a date variable to produce a date axis on the right, so that the
two axes of a dual-axis graph are readable in the same units I typed.*

- **Given** `dash (line v d) (line v2 d2, yaxis(2))` where `d2` is `%tm`,
  **when** the figure is built,
  **then** the right-hand axis is a `DatetimeAxis` whose formatter's `days`
  pattern is `"%b %Y"` (the `%tm` row of the table above).
- **Given** the same graph,
  **when** `fig.extra_y_ranges["y2"]` is read,
  **then** its `start`/`end` are on the **millisecond** scale — equal, within
  the 5% padding `_compute_secondary_range` applies, to
  `series.astype('datetime64[ms]').astype('int64')` of the serialized column.

**US-10.2.2** — *As a Stata user, I want `xlabel(td(01jan2001) td(01jan2002))`
to put ticks on those two dates, so that the tick list I write is the tick list
I see.*

- **Given** `xlabel(14977 15342)` on a `%td` x axis,
  **when** the figure is built,
  **then** the `FixedTicker.ticks` are `[1293840000000, 1325376000000]` — the
  same values `_stata_dates_to_datetime(...).astype('datetime64[ms]').astype('int64')`
  produces — not `[14977.0, 15342.0]`.
- **Given** `xlabel(minmax)` on a `%td` axis,
  **when** the figure is built,
  **then** the two ticks equal the millisecond epoch of the column's min and
  max, not their microsecond or nanosecond value.
- **Given** `xscale(range(14977 15342))` on a `%td` axis,
  **when** the figure is built,
  **then** `fig.x_range.start`/`.end` are the millisecond epochs of those dates.
- **Given** `xscale(range(14977 .))` — one bound only — on a `%td` axis,
  **when** the figure is built,
  **then** the supplied bound is converted and the data-derived bound is taken
  on the same millisecond scale.

**US-10.2.3** — *As a Stata user, I want `xline(td(01jan2001))` to draw a line
on 01jan2001, so that an annotation I can see in Stata is visible in the
dashboard.*

- **Given** `xline(14977)` on a `%td` x axis,
  **when** the figure is built,
  **then** a `Span` exists with `location == 1293840000000`, inside the
  figure's rendered x range.
- **Given** `xline(3000)` on a **numeric** x axis,
  **when** the figure is built,
  **then** the `Span` location is `3000.0`, unchanged (the existing
  `TestReferenceLines` assertions must still pass, including the measured
  default of a **black, dashed** line).

**US-10.2.4** — *As a Stata user, I want `xlabel(, format(%tdDD/NN/CCYY))` to
restyle my date ticks, and I never want a numeric picture to turn my dates into
epoch integers.*

- **Given** `xlabel(, format(%9.0fc))` on a date axis,
  **when** the figure is built,
  **then** the axis formatter is still a `DatetimeTickFormatter`, and a
  `UserWarning` names the variable and says the numeric picture was not applied
  to a date axis.
- **Given** `xlabel(, format(%tdDD/NN/CCYY))` on a date axis,
  **when** the figure is built,
  **then** the axis formatter is a `DatetimeTickFormatter` reflecting the
  requested picture, and **no** silent discard occurs.
- **Given** a numeric axis with `format(%9.0fc)`,
  **when** the figure is built,
  **then** a `NumeralTickFormatter` is applied exactly as today.

### E10.3 — The axis-kind decision, and proof in both modes

**US-10.3.1** — *As a Stata user, I want adding a `yaxis(2)` layer to leave my
primary axis alone, so that a graph does not silently degrade when I overlay a
second series.*

- **Given** `dash (line d x) (line v x, yaxis(2))` where `d` is `%td` and `v` is
  numeric,
  **when** the figure is built,
  **then** the **left** axis is still a `DatetimeAxis` — the behaviour before
  the second layer was added.
- **Given** two primary-axis layers whose date kinds genuinely disagree
  (`%td` and `%tm` on the same axis),
  **when** the figure is built,
  **then** `_figure_date_kind` still declines, exactly as today (the warning for
  that case is **Phase 09 item 1**, not this phase).

**US-10.3.2** — *As a package maintainer, I want the dual-axis suite and the
parity corpus to contain a date case, so that the next change to either
renderer cannot re-break this phase without a red test.*

- **Given** `test/test_dual_axis.py`,
  **when** the suite runs,
  **then** at least one test asserts a `DatetimeAxis` on the right/top and a
  y2/x2 range on the millisecond scale.
- **Given** `test/test_mode_parity.py`,
  **when** the suite runs,
  **then** at least one `CORPUS` entry carries a non-empty `formats` map and a
  test compares the served figure's axis type and the served column's dtype
  against standalone.

---

## Business requirements

| id | requirement | how it is judged |
|---|---|---|
| **BR-10.1** | A `%t*` variable renders as calendar dates under `dash serve` exactly as under `dash build`. | Served figure axis class and formatter class/patterns equal standalone's, for all seven kinds. |
| **BR-10.2** | No observation is lost in server mode because of a date. Row count in the served figure equals row count in standalone, including for the display-string transport. | Parity test on data length; explicit zero-rows regression test. |
| **BR-10.3** | A secondary (`yaxis(2)`/`xaxis(2)`) date layer gets the same axis treatment as a primary one: `DatetimeAxis`, kind-matched formatter, millisecond range. | `test/test_dual_axis.py` date case. |
| **BR-10.4** | Any value the user writes in Stata date units — tick list, `minmax`, `range()` bound, `xline()`/`yline()` value — is drawn at the date it names. | Per-block millisecond assertions. |
| **BR-10.5** | A date axis never silently loses its date formatting to a numeric picture, and a user-supplied `%t*` picture is either honoured or warned about — never discarded in silence. | Formatter-class assertions plus warning assertions. |
| **BR-10.6** | Adding a layer on a secondary axis never changes the primary axis's type. | Primary-axis regression test with a mixed pair of layers. |
| **BR-10.7** | Non-date figures are unchanged by every item in this phase. | The existing suite stays green; the byte-identity guard (Phase 09 item 7) stays green. |
| **BR-10.8** | A spec with no `formats` key behaves exactly as before, in both renderers. | Explicit absent-key tests in both modes. |
| **BR-10.9** | Every functional item in this phase ships with a regression test that fails before the fix and passes after (CLAUDE.md rule 8), and every new or changed function has a unit test (rule 4). | Review checklist; mutation proofs recorded in the PR. |

---

## Technical requirements

Line numbers are the current ones from `REMAINING.md`, re-confirmed against
`dash_render.py` at 16,264 lines. The plan's own section files quote stale
numbers (the file grew from ~10,455 lines) — ignore those.

### E10.1 — server

**TR-10.1 — Forward the three date helpers into the generated module.**
Add `_stata_date_kind`, `_stata_dates_to_datetime` and `_datetime_formatter_for`
to the name tuple in `ServerAppBuilder._shared_module_lines`
(`dash_render.py:12392-12397`), which currently ends
`..., "_t_cdf", "_t_ppf")`. The mechanism forwards the *source text* of each
function, so their own dependencies must already be present or also forwarded;
`_stata_dates_to_datetime` calls `_from_parts` internally
(`dash_render.py:317-327`) — verify the emitted module resolves every global
each forwarded helper calls. `test/test_mode_parity.py:437`
(`test_every_global_a_copied_helper_calls_is_defined`) is the existing guard
for exactly this and must stay green.

**TR-10.2 — Give the emitted loader a date branch.**
Replace the unconditional coercion at `dash_render.py:13161-13165`. The emitted
loader must read `spec["build_options"]["formats"]` (the same key
`DashRenderer._load_data` reads at `dash_render.py:8188`, written by
`dash.ado:1723` and `dash.ado:2343` from `_dash_formats_json`,
`dash.ado:1266`), and for each non-string column:

1. `kind = _stata_date_kind(formats.get(col))`; if `None`, keep today's
   `pd.to_numeric(..., errors='coerce')` and record the numeric pattern in an
   emitted `numeric_formats` dict (via `_stata_numeric_pattern`), mirroring
   `dash_render.py:8199-8205`.
2. Otherwise mirror `dash_render.py:8208-8226` exactly, **including the
   `else:` display-string branch and its `UserWarning`** (TR-10.3).
3. Record `date_vars[col] = kind` in the emitted module's module-level state so
   the figure block and the already-forwarded widget/label code can read it.
   `type_is_str` must continue to win: a string column is never converted even
   if it carries a date format.

**TR-10.3 — Mirror the legacy string transport.**
The `else:` branch at `dash_render.py:8212-8226` uses
`pd.to_datetime(raw.astype(str).str.strip(), errors="coerce")` and warns when
`converted.isna().all() and raw.notna().any()`. Both halves are required: the
conversion (BR-10.2) and the warning (BR-10.5).

**TR-10.4 — Set the emitted figure's axis type and formatter.**
At `dash_render.py:13851-13855`, before `bokeh_figure(**_fig_kw)`, decide the
axis type once — never re-create the figure (commit `c3941de`) — mirroring
`dash_render.py:9561-9603`:

- `_fig_kw['x_axis_type'] = 'datetime'` / `['y_axis_type'] = 'datetime'` when
  the axis variable is in `date_vars`;
- date **wins over** `'log'`, with the same `UserWarning` text standalone emits
  (`"dash: xscale(log) is meaningless for the date variable '<v>'; drawing a
  date axis instead."`);
- after construction, `axis.formatter = _datetime_formatter_for(kind)` for each
  dated axis.

**TR-10.5 — Same treatment in the emitted facet and total figures.**
`dash_render.py:15131` (`_fac_fig`) and `dash_render.py:15228` (`_tot_fig`)
construct figures through their own kwargs dicts and must receive the same
axis-type and formatter treatment, or `by()` reverts to raw day numbers.

**TR-10.6 — Prefer lighting up existing code to copying it.**
`_format_date_value_standalone` is already forwarded
(`dash_render.py:12395`; lands at generated `app.py:1410`, called at
`app.py:3672` from the forwarded GlyphMapper mlabel path) and the slider
helper's `allow_datetime` branch is already present at generated
`app.py:1221-1248` doing the correct
`.astype('datetime64[ms]').astype('int64')`. Both become reachable the moment
the emitted loader produces a `datetime64` column. Do not emit second copies of
either; **Phase 13** owns the remaining served-format touchpoints (KPI, filter
widgets, dropdown) and depends on this loader change.

### E10.2 — standalone

**TR-10.7 — Secondary range on the millisecond scale.**
`_compute_secondary_range` (`dash_render.py:2433-2467`) accumulates values at
`:2461` with `pd.to_numeric(df[varname], errors="coerce")`. On a `datetime64`
column that yields microseconds or nanoseconds depending on the resolution
pandas inferred — the 09-02 appendix measured it as *"`float(vals.min())` of a
datetime column, i.e. MICROseconds (1000x too large)"*. Route date columns
through `.astype('datetime64[ms]').astype('int64')`, the same cast
`_extract_finite` uses at `dash_render.py:989`. The function keeps its
`(lo, hi)` float contract and its 5% `padding_pct`; only the scale changes.
Its two call sites are `dash_render.py:9678-9681` (y2) and `:9713-9716` (x2),
both already passing the *active view* frame via `_source_frame(source, self.df)`
— do not regress that (it is 09-07's fix, and Phase 27 builds on it).

**TR-10.8 — Secondary axis model.**
`dash_render.py:9684` builds `_y2_ax = (LogAxis if _y2_log else LinearAxis)(y_range_name="y2", axis_label=...)`
and `:9719` the `_x2_ax` equivalent with `x_range_name="x2"`. Select
`DatetimeAxis` when the *secondary* layers' variable is a date — i.e. when
`self.date_vars.get(varname)` is set for the layers whose
`options["yaxis"]`/`["xaxis"]` is `"2"` — and attach
`_datetime_formatter_for(kind)`. A date must beat `LogAxis` here for the same
reason it beats `'log'` on the primary axis. The explicit
`ylabel2()`/`xlabel2()` tick path immediately below
(`dash_render.py:9695-9711`) sets `FixedTicker(ticks=_ticks2)` from
`self._parse_axis_label_opt` — those ticks are user-supplied Stata numbers and
need the same conversion as TR-10.9.

**TR-10.9 — `_apply_axis_spec` learns the date kind.**
`_apply_axis_spec` (`dash_render.py:9112-9170`) already receives `varname` (sole
call site `dash_render.py:9913` passes `var`), so `kind = self.date_vars.get(varname)`
inside the method is sufficient — no signature change. Then:

- `mode == "explicit"` (`:9149-9150`): map `spec["ticks"]` through
  `_stata_dates_to_datetime(pd.Series(ticks), kind).astype('datetime64[ms]').astype('int64')`
  before building the `FixedTicker`. The `major_label_overrides` dict keyed by
  `float(k)` at `:9156-9157` must be re-keyed to the converted values or the
  user's tick **labels** detach from their ticks.
- `mode == "minmax"` (`:9137-9143`): replace `pd.to_numeric(col, errors="coerce")`
  with the millisecond cast for a date column.
- The task clause *"An explicit `xlabel()` tick list must still win"* means the
  `FixedTicker` replaces the datetime ticker, while the **formatter** attached at
  `dash_render.py:9598-9603` survives unless the user asked otherwise (TR-10.11).

**TR-10.10 — `xscale(range())` / `yscale(range())`.**
The block at `dash_render.py:9750-9773` parses bounds with
`_parse_scale_range(_raw_sc)` and sets `_Rng(float(_new_lo), float(_new_hi))`.
Convert user bounds with the same helper chain, and replace the one-bound
data-derived fallback at `:9766-9769`
(`_v = pd.to_numeric(self.df[_col], errors="coerce").dropna()`) with the
millisecond cast for a date column. `_report_unhandled_scale_opts(_raw_sc, _which)`
at `:9757` and the reversal handling below stay as they are.

**TR-10.11 — `format()` on a date axis.**
At `dash_render.py:9159-9170`, branch on the axis's date kind **before** the
numeric path:

- date axis + numeric picture (explicit or inherited from
  `self.numeric_formats`): do **not** install a `NumeralTickFormatter`; keep the
  `DatetimeTickFormatter`; warn naming the variable and the picture.
- date axis + `%t*` picture: honour it. `_datetime_formatter_for`
  (`dash_render.py:247-268`) is kind-driven, not picture-driven, so this needs a
  picture-aware variant (e.g. `_datetime_formatter_for(kind, picture=None)`)
  that maps a Stata date picture such as `%tdDD/NN/CCYY` onto the equivalent
  strftime patterns for the `years`/`months`/`days`/`hours` slots. Any picture
  element the mapper cannot express must warn rather than be dropped.
- non-date axis: byte-identical to today, including the existing warning at
  `:9165-9170`.

Note the existing guard is what suppresses today's silence:
`elif spec["format"] and _stata_date_kind(fmt) is None`.

**TR-10.12 — Reference lines.**
`dash_render.py:9843-9858` builds each `Span` with `location=float(xline_val)`
inside a `try/except (ValueError, TypeError): pass`. Convert the value through
the axis's date kind before the `float()`. Two hazards: (a) the silent `except`
must not swallow a conversion failure — a value that cannot be converted should
warn; (b) `yline()` on a figure whose **y** axis is the dated one needs the y
kind, not the x kind, so the two blocks take different kinds.

### E10.3 — decision and coverage

**TR-10.13 — Partition before agreeing.**
`_figure_date_kind` (`dash_render.py:9268-9298`) must consider only the layers
belonging to the axis being decided. Either filter the `plots` list at the two
call sites (`dash_render.py:9559-9560`) with the predicate the secondary path
already uses (`str(plot.get("options", {}).get("yaxis", "1")).strip() != "2"`),
or add an `axis_number` parameter with default `1`. Keep the
`if len(kinds) > 1 or None in kinds: return None` bail for genuine
within-axis disagreement — **Phase 09 item 1** adds the warning on that branch,
so coordinate rather than duplicate. Note Phase 09 item 4 also rewrites the
`name = ...` expression at `:9288-9290` to read `yvar1`/`y1var`/`var` shapes;
land Phase 09 first and rebase.

**TR-10.14 — A `formats` hook in the shared test helpers.**
`test/conftest.py:152` (`make_spec`) and `:246` (`make_dr`) take no `formats`
argument, and `test/test_dual_axis.py:44-56` and `test/test_mode_parity.py:70-80`
each build their own `build_options` without one
(`test/test_mode_parity.py:74` hardcodes `"formats": {}`). Add an optional
`formats: dict | None = None` keyword threaded into
`build_options["formats"]` in `make_spec`/`make_dr`, and give
`test_dual_axis._make_spec_and_data` and `test_mode_parity._spec` the same
optional parameter, defaulting to today's behaviour so no existing test
changes.

---

## Work items

Numbered exactly as handed over. Tags are `[kind · renderer · effort]`.

---

**1. [functional · server · M] — Give `ServerAppBuilder` date support.**

Have the emitted app read `build_options["formats"]`, convert `%t*` columns
with `_stata_dates_to_datetime`, and set
`_fig_kw['x_axis_type']/['y_axis_type'] = 'datetime'` plus the per-kind
`DatetimeTickFormatter`, mirroring `dash_render.py:9556-9603`.
`_stata_date_kind`, `_stata_dates_to_datetime` and `_datetime_formatter_for`
must be added to the helper-forwarding tuple so they exist in the generated
module.

*Where:* `dash_render.py:13161-13165` (emitted
`for col in df.columns: df[col] = pd.to_numeric(...)` — the only coercion in the
emitted loader); `dash_render.py:13851-13855` (emitted `_fig_kw` — only `'log'`
is handled); `dash_render.py:12392-12397` (`_emitted_names` forwarding tuple in
`ServerAppBuilder._shared_module_lines`); `dash_render.py:15131` and `:15228`
(emitted facet/total figures, same omission).

*Evidence:* measured in the emitted app — `DatetimeAxis` **0**,
`DatetimeTickFormatter` **0**, `date_vars` **0**, `numeric_formats` **0**. One
spec carrying `formats:{"d":"%td"}` built through both renderers gave
`DatetimeAxis`/`DatetimeTickFormatter` in standalone and
`LinearAxis`/`BasicTickFormatter` in the served app — raw day numbers on screen.
*"This is the whole of 08-04 missing from `dash serve`."* (REMAINING.md,
Appendix A, 08-04; Appendix B, 08-04.) Requirements: TR-10.1, TR-10.2, TR-10.4,
TR-10.5.

---

**2. [functional · standalone · M] — Datetime treatment on the secondary-axis path.**

Build the y2/x2 axis as a `DatetimeAxis` with `_datetime_formatter_for(kind)`
when the layer's variable is a date, and compute `extra_y_ranges['y2']` /
`extra_x_ranges['x2']` on Bokeh's millisecond scale
(`astype('datetime64[ms]').astype('int64')`) instead of `pd.to_numeric`, which
yields microseconds or nanoseconds depending on the inferred resolution.

*Where:* `dash_render.py:9684` (`_y2_ax = (LogAxis if _y2_log else LinearAxis)(...)`);
`dash_render.py:9719` (`_x2_ax = (LogAxis if _x2_log else LinearAxis)(...)`);
`dash_render.py:9678-9681` and `:9713-9716` (the `_compute_secondary_range`
calls); `dash_render.py:2433-2467` (`_compute_secondary_range`, whose
`pd.to_numeric(df[varname])` at `:2461` is the unit bug).

*Evidence:* task 08-04's action clause says in as many words *"Apply the same
treatment to the secondary-axis path"*; no `DatetimeAxis` is ever constructed
there. The 09-02 appendix measured the same `pd.to_numeric`-on-datetime defect
as *"MICROseconds (1000x too large)"*. (REMAINING.md, Appendix B, 08-04.)
Requirements: TR-10.7, TR-10.8.

---

**3. [functional · standalone · M] — Convert user tick lists, `minmax` and `range()` bounds.**

Convert user-supplied Stata date values to the datetime axis's millisecond
scale in `xlabel()`/`ylabel()` explicit tick lists and in `minmax`, and in
`xscale(range())`/`yscale(range())`. Pass the axis's date kind into
`_apply_axis_spec` (it already receives `varname`, so `self.date_vars.get(varname)`
suffices) and map the tick list through
`_stata_dates_to_datetime(...).astype('datetime64[ms]').astype('int64')`; do the
same for the range block's user bounds and replace its `pd.to_numeric`
data-derived bound.

*Where:* `dash_render.py:9149-9150` (`_apply_axis_spec`, `mode == "explicit"`
`FixedTicker`); `dash_render.py:9137-9143` (same method, `mode == "minmax"`,
`pd.to_numeric(col)`); `dash_render.py:9750-9773` (the
`xscale(range())`/`yscale(range())` block in `_make_figure_body`, including its
`pd.to_numeric(self.df[_col])` one-bound fallback).

*Evidence:* 08-04 requires that *"An explicit `xlabel()` tick list must still
win"*, which it cannot do correctly while its values are ~31 years from where
the user put them. (REMAINING.md, Appendix B, 08-04; the same code block is
re-measured in Appendix C under 09-02.) Requirements: TR-10.9, TR-10.10.

---

**4. [deliverable · both · S] — The two missing coverage cases 08-04's scope implies.**

(a) A secondary-axis date case in `test/test_dual_axis.py` asserting a
`DatetimeAxis` on the right/top and a y2/x2 range on the same millisecond scale
as the serialized column; (b) a date case in the `ServerAppBuilder` parity
corpus asserting the served figure's axis type and the served column's dtype
match the standalone renderer.

*Where:* `test/test_dual_axis.py` (261 lines, no date case);
`test/test_mode_parity.py:74` (`CORPUS` helper `_spec` hardcodes `"formats": {}`)
and its `CORPUS` list at `test/test_mode_parity.py:187-284`.

*Evidence:* the two files that would have caught items 1 and 2 are structurally
incapable of producing a date column. (REMAINING.md, Appendix B, 08-04.)
Requirements: TR-10.14; test plan E10.1-T4, E10.2-T1.

---

**5. [functional · server · S] — Recover the display-string date transport in the emitted loader.**

The emitted server loader must ALSO recover the display-string date transport
before `pd.to_numeric` destroys it, mirroring `_load_data`'s `else:` branch
(`dash_render.py:8208-8226`). Today a `%td` column that arrives as text
("02jan2001") is coerced to NaN in the generated app and the served figure gets
**ZERO rows**, not a wrong-scale axis. Related and worth knowing before
starting: the generated app ALREADY carries the date machinery it needs —
`_format_date_value_standalone` is forwarded (`dash_render.py:12395`, lands at
`app.py:1410` and is called at `app.py:3672` from the forwarded `GlyphMapper`
mlabel path) and the slider helper's `allow_datetime` branch
(`app.py:1221-1248`, which does the correct
`.astype('datetime64[ms]').astype('int64')`) is present. Both are unreachable
solely because the emitted loader never creates a `datetime64` column, so
fixing the loader lights up existing code rather than requiring new copies.

*Where:* `dash_render.py:13162-13165` (emitted loader's only coercion);
`dash_render.py:8208-8226` (the standalone branch to mirror); generated app
lines 1221-1248 and 3672 (already-forwarded date machinery that is currently
unreachable).

*Evidence:* REMAINING.md, Appendix C, 08-04. The standalone comment at
`dash_render.py:8214-8218` records that this exact coercion *"is how
`dash line close date` came to produce an empty dashboard"*. Requirements:
TR-10.2, TR-10.3, TR-10.6.

---

**6. [functional · standalone · S] — Partition plots by axis before `_figure_date_kind` demands agreement.**

Partition plots by their `options.yaxis` / `options.xaxis` before
`_figure_date_kind` demands agreement. Today a single secondary-axis layer
POISONS the primary axis: a graph whose primary y is a date loses its
`DatetimeAxis` entirely as soon as any `yaxis(2)` layer carries a numeric
variable, because both layers land in the same `kinds` set and the
`None in kinds` branch bails. This is distinct from the secondary-axis item
already reported — the damage here is to the PRIMARY axis, which was working
before the second layer was added.

*Where:* `dash_render.py:9286-9297` (`_figure_date_kind`'s loop and its
`if len(kinds) > 1 or None in kinds: return None` bail);
`dash_render.py:9559-9560` (the two calls, which pass the unpartitioned `plots`
list); the secondary-axis split already exists downstream at
`dash_render.py:9678-9719` and can supply the same predicate.

*Evidence:* REMAINING.md, Appendix C, 08-04. Requirements: TR-10.13.

---

**7. [functional · standalone · S] — Convert `xline()` / `yline()` values.**

Convert `xline()` / `yline()` reference-line values to the datetime axis's
millisecond scale. `_make_figure_body` drops each user value straight into
`Span(location=float(v))`, so `xline(td(01jan2001))` — a Stata SIF day number —
lands 14.977 seconds after 1970-01-01 and is drawn off the figure, silently.
Same class as the `xlabel`/`xscale(range())` conversion already reported, but a
separate code block that that fix will not touch.

*Where:* `dash_render.py:9843-9858` (the `_parse_refline("xline", ...)` /
`_parse_refline("yline", ...)` blocks and their `Span(location=float(...))`
calls, inside `_make_figure_body`).

*Evidence:* REMAINING.md, Appendix C, 08-04. Requirements: TR-10.12.

---

**8. [functional · standalone · S] — Give `_apply_axis_spec` a date branch.**

Two defects on a date axis: (1) `xlabel(, format(%9.0fc))` — or any numeric
picture, including one inherited from `self.numeric_formats` — OVERWRITES the
`DatetimeTickFormatter` with a `NumeralTickFormatter`, so the ticks read as
epoch milliseconds with thousands separators; (2) `xlabel(, format(%tdDD/NN/CCYY))`
— a Stata DATE picture, the natural way to ask for a tick style — is silently
discarded: `_stata_numeric_pattern` returns `None` and the warning branch
explicitly excludes date formats
(`elif spec["format"] and _stata_date_kind(fmt) is None`), so nothing is applied
and nothing is said. 08-04's action clause promises a formatter *"matched to the
date kind"*; a user-supplied kind is never honoured.

*Where:* `dash_render.py:9159-9170` (`_apply_axis_spec`, the
`fmt`/`NumeralTickFormatter` block and its suppressed warning branch);
`dash_render.py:9598-9603` (`_make_figure_body`, where `_datetime_formatter_for`
is attached); `dash_render.py:247-268` (`_datetime_formatter_for`, which would
need a picture-aware variant).

*Evidence:* REMAINING.md, Appendix C, 08-04. Requirements: TR-10.11.

---

## Test plan

Rule 8 governs the order: **write the failing test first**, prove it red at
`HEAD`, then fix. Rule 4 governs the breadth: every function added or changed
gets a unit test. Every test below names a mutation — the edit that must make it
die — because a green test that cannot fail proves nothing (the corpus file
already carries `test_the_profile_is_not_empty` at
`test/test_mode_parity.py:328` as the house pattern for this).

Shared prerequisite: **TR-10.14** (`formats=` in `test/conftest.py:152`
`make_spec` / `:246` `make_dr`, in `test_dual_axis._make_spec_and_data` and in
`test_mode_parity._spec`). Existing fixture values to reuse:
`test/test_dates.py:337` seeds `date` at `14977.0 + i` (SIF 14977 =
01jan2001, epoch ms 1293840000000) with `close` and `vol`;
`test/test_dates.py` also provides `_jsonio_payload`, `_minimal_spec(plots, formats=...)`
and `_renderer`. `test/test_axis_options.py` provides `_fig_with_gopts(plots, gopts)`
and `_auto()`.

### Epic E10.1 — Dates reach `dash serve` (items 1, 5)

| id | test | file | kind |
|---|---|---|---|
| **E10.1-T1** *(write first)* | `test_a_served_date_axis_is_a_datetime_axis` — build `ServerAppBuilder` from a spec with `formats={"d": "%td"}`, exec the emitted module, run `make_document`, assert the figure's x axis is a `DatetimeAxis` and its formatter a `DatetimeTickFormatter`. **Red at HEAD** (measured: `DatetimeAxis` 0 in the emitted app). | new `test/test_server_dates.py` | regression (rule 8) |
| **E10.1-T2** *(write first)* | `test_a_string_transported_date_keeps_every_row` — data JSON whose `%td` column is text (`"02jan2001"`…), 10 rows; assert the served figure's data source carries 10 points. **Red at HEAD**: zero rows. | `test/test_server_dates.py` | regression (rule 8) |
| **E10.1-T3** | `test_an_unparseable_date_text_column_warns` — assert a `UserWarning` naming the variable and its display format, mirroring `dash_render.py:8218-8225`. | `test/test_server_dates.py` | unit (rule 4) |
| **E10.1-T4** | Parity corpus date entries: add `("line on a %td x axis", [...], {"formats": {"d": "%td"}})` and one `%tc` entry to `CORPUS` (`test/test_mode_parity.py:187-284`), and a new `test_same_axis_types_and_column_dtypes` comparing `type(fig.xaxis[0]).__name__`, `type(fig.xaxis[0].formatter).__name__`, the formatter's `years`/`months`/`days`/`hours` strings, and the served vs standalone column dtype. | `test/test_mode_parity.py` | integration — **item 4(b)** |
| **E10.1-T5** | `test_the_three_date_helpers_are_defined_in_the_generated_module` — assert `_stata_date_kind`, `_stata_dates_to_datetime`, `_datetime_formatter_for` are module attributes of the exec'd app. | `test/test_server_dates.py` | unit (rule 4), guards TR-10.1 |
| **E10.1-T6** | `test_no_formats_key_leaves_the_served_frame_alone` — spec with no `formats`; assert every column's dtype and the figure's axis classes match today's behaviour. | `test/test_server_dates.py` | regression, BR-10.8 |
| **E10.1-T7** | `test_a_faceted_date_axis_is_a_datetime_axis` — the same spec under `by()`; covers the facet/total figures at `dash_render.py:15131`/`:15228`. | `test/test_server_dates.py` | unit (rule 4), guards TR-10.5 |
| **E10.1-T8** | cscript: extend `test/test_e2e_serve.cscript` with a `%td` case (`sysuse sp500`, `dash line close date`, `dash serve`-side build) asserting rc 0 and that the generated app text contains `DatetimeAxis`. If Phase 09's `test/test_dates.cscript` has landed, add the served case there instead and register once in `test/run_all_cscripts.do`. | `test/test_e2e_serve.cscript` | end-to-end, Stata side |

**Mutation proofs.** E10.1-T1 dies if the `_fig_kw['x_axis_type'] = 'datetime'`
line added at `dash_render.py:13851-13855` is reverted. E10.1-T2 dies if the
emitted `else:` branch is replaced by the old unconditional
`pd.to_numeric(df[col], errors='coerce')`. E10.1-T4 dies if the forwarded
`_datetime_formatter_for` is swapped for a bare `DatetimeTickFormatter()` — the
per-kind patterns stop matching standalone. E10.1-T5 dies if any of the three
names is removed from the tuple at `dash_render.py:12392-12397`.

### Epic E10.2 — User-supplied values on a date axis (items 2, 3, 7, 8)

| id | test | file | kind |
|---|---|---|---|
| **E10.2-T1** *(write first)* | `TestSecondaryDateAxis::test_the_right_axis_is_a_datetime_axis` and `::test_the_y2_range_is_on_the_millisecond_scale` — two layers, the `yaxis(2)` one on a `%tm` variable; assert `DatetimeAxis` on the right, the formatter's `days` pattern is `"%b %Y"`, and `fig.extra_y_ranges["y2"].start/.end` equal the column's `astype('datetime64[ms]').astype('int64')` min/max ±5% padding. **Red at HEAD** (`LinearAxis`, microsecond range). | `test/test_dual_axis.py` | regression (rule 8) — **item 4(a)** |
| **E10.2-T2** | `test_x2_gets_the_same_treatment` — the `xaxis(2)` mirror, guarding `dash_render.py:9719`. | `test/test_dual_axis.py` | unit (rule 4) |
| **E10.2-T3** | `test_a_numeric_secondary_axis_is_unchanged` — the existing `TestSecondaryAxisSetup` expectations (`test/test_dual_axis.py:112-170`) still hold with no `formats` key. | `test/test_dual_axis.py` | regression, BR-10.7 |
| **E10.2-T4** *(write first)* | `test_an_explicit_date_tick_list_lands_on_the_dates` — `xlabel(14977 15342)` on a `%td` axis; assert `FixedTicker.ticks == [1293840000000, 1325376000000]`. **Red at HEAD** (raw `[14977.0, 15342.0]`). | `test/test_axis_options.py`, extending `TestAxisLabelGrammar` | regression (rule 8) |
| **E10.2-T5** | `test_date_tick_labels_follow_their_converted_ticks` — `xlabel(14977 "start")`; assert `major_label_overrides` is keyed on the converted millisecond value. | `test/test_axis_options.py` | unit (rule 4) |
| **E10.2-T6** | `test_minmax_on_a_date_axis_is_milliseconds` — assert the two ticks equal the column's ms min/max, not its µs/ns value. | `test/test_axis_options.py` | regression (rule 8) |
| **E10.2-T7** | `test_xscale_range_on_a_date_axis` plus `test_a_single_date_bound_takes_the_other_from_the_data` — guards both halves of `dash_render.py:9750-9773`. | `test/test_axis_options.py`, extending `TestAxisScale` | unit (rule 4) |
| **E10.2-T8** *(write first)* | `test_xline_on_a_date_axis_lands_on_the_date` — `xline(14977)` on a `%td` axis; assert a `Span` at `1293840000000` and that it lies inside `fig.x_range`. **Red at HEAD** (location `14977.0`). Mirror with `yline` on a dated y axis. | `test/test_axis_options.py`, extending `TestReferenceLines` (`:565`) | regression (rule 8) |
| **E10.2-T9** | `test_a_numeric_xline_is_unchanged` — `xline(3000)` still yields `3000.0`, still black and dashed (the measured Stata default asserted at `test/test_axis_options.py:588`). | `test/test_axis_options.py` | regression, BR-10.7 |
| **E10.2-T10** *(write first)* | `test_a_numeric_picture_does_not_replace_the_date_formatter` — `xlabel(, format(%9.0fc))` on a `%td` axis; assert the formatter is still a `DatetimeTickFormatter` and a `UserWarning` names the variable. **Red at HEAD** (`NumeralTickFormatter`). | `test/test_dates.py`, new `TestDateAxisFormatOption` | regression (rule 8) |
| **E10.2-T11** *(write first)* | `test_a_stata_date_picture_is_honoured` — `xlabel(, format(%tdDD/NN/CCYY))`; assert the resulting `DatetimeTickFormatter` reflects the requested picture. **Red at HEAD** (silently discarded, no warning). | `test/test_dates.py` | regression (rule 8) |
| **E10.2-T12** | `test_an_inherited_numeric_format_does_not_reach_a_date_axis` — no explicit `format()`, but `self.numeric_formats` carries one for the variable; guards the `spec["format"] or ... numeric_formats.get(varname, "")` fallback at `dash_render.py:9159-9160`. | `test/test_dates.py` | unit (rule 4) |
| **E10.2-T13** | Unit tests for the picture-aware `_datetime_formatter_for` variant: each supported picture element maps to the expected strftime slot; an unsupported element warns. Parametrised over the seven kinds so the table in *Why this phase exists* stays pinned. | `test/test_dates.py`, alongside `TestDatetimeAxis` (`:334-404`) | unit (rule 4), TR-10.11 |

**Mutation proofs.** E10.2-T1 dies if `_y2_ax` is forced back to `LinearAxis`,
and its range half dies if `_compute_secondary_range`'s cast is reverted to
`pd.to_numeric`. E10.2-T4/T6 die if the conversion in `_apply_axis_spec` is made
the identity. E10.2-T8 dies if `Span(location=float(xline_val))` is restored.
E10.2-T10 dies if the date guard in the `fmt` block is removed; E10.2-T11 dies
if the picture-aware branch falls through to `_datetime_formatter_for(kind)`
with the picture ignored. E10.2-T13 dies if any row of the kind→pattern table is
changed.

### Epic E10.3 — The axis-kind decision (items 4, 6)

| id | test | file | kind |
|---|---|---|---|
| **E10.3-T1** *(write first)* | `test_a_secondary_numeric_layer_does_not_poison_the_primary_date_axis` — `(line d x) (line v x, yaxis(2))`, `d` is `%td`, `v` numeric; assert the **left** axis is a `DatetimeAxis`. **Red at HEAD**: the `None in kinds` bail strips it. | `test/test_dates.py`, in `TestDatetimeAxis` | regression (rule 8) |
| **E10.3-T2** | `test_two_primary_layers_with_different_kinds_still_decline` — `%td` and `%tm` on the same axis; assert no `DatetimeAxis`. Guards that the partition did not weaken the genuine-disagreement bail. | `test/test_dates.py` | unit (rule 4) |
| **E10.3-T3** | `test_the_primary_and_secondary_kinds_are_decided_independently` — primary `%td`, secondary `%tm`; assert the left formatter's `days` is `"%d %b %Y"` and the right's is `"%b %Y"`. | `test/test_dual_axis.py` | unit (rule 4) |
| **E10.3-T4** | Parametrised unit tests for `_figure_date_kind` itself over the axis-number predicate: layers with `options={}`, `{"yaxis": "1"}`, `{"yaxis": "2"}`, `{"yaxis": " 2 "}` (whitespace, as `_compute_secondary_range:2457` strips) and a non-numeric `yaxis` value (which `test/test_dual_axis.py:253` already requires be treated as primary). | `test/test_dates.py` | unit (rule 4) |
| **E10.3-T5** | Coverage bookkeeping for **item 4**: E10.2-T1/T2 satisfy clause (a); E10.1-T4 satisfies clause (b). Both must be present before the phase is closed. | — | — |

**Mutation proofs.** E10.3-T1 dies if the call sites at
`dash_render.py:9559-9560` are reverted to passing the unpartitioned `plots`
list. E10.3-T2 dies if the `len(kinds) > 1 or None in kinds` bail is deleted
instead of scoped. E10.3-T4 dies if the predicate uses `==` on the raw option
value without `str(...).strip()`.

### Suite-level

- Full `pytest` must stay green: **3,498 passed / 37 skipped** at HEAD is the
  baseline recorded in REMAINING.md's gate list; this phase may only add.
- Full certification suite: **25/25 cscripts**, run from `test/` with
  `arch -arm64`. A skip is not a pass.
- The parity corpus and the copied-callee guard
  (`test/test_mode_parity.py:437`) must both stay green after the three helpers
  are forwarded.
- Set `$dash_nobrowser` before any Stata run that builds a dashboard.

---

## Definition of done

- [ ] **Item 1** — the emitted app sets `x_axis_type`/`y_axis_type` to
      `'datetime'` and attaches `_datetime_formatter_for(kind)`, in the main,
      facet (`:15131`) and total (`:15228`) figures; the three helpers appear in
      the tuple at `dash_render.py:12392-12397`.
- [ ] **Item 5** — the emitted loader converts `%t*` columns and mirrors the
      `else:` display-string branch of `dash_render.py:8208-8226`, warning
      included; a text-transported date yields full row count, not zero.
- [ ] **Item 2** — `_y2_ax`/`_x2_ax` are `DatetimeAxis` with the kind-matched
      formatter when the secondary layer is dated; `_compute_secondary_range`
      returns millisecond-scale bounds and still computes from the active view.
- [ ] **Item 3** — explicit tick lists, their label overrides, `minmax`, and
      both `range()` bounds (including the one-bound data fallback) are on the
      millisecond scale on a date axis.
- [ ] **Item 7** — `xline()`/`yline()` values are converted per the axis's own
      kind; an unconvertible value warns rather than being swallowed by the
      `except (ValueError, TypeError): pass`.
- [ ] **Item 8** — a numeric picture never replaces a `DatetimeTickFormatter`
      (it warns); a `%t*` picture is honoured by the picture-aware formatter
      variant.
- [ ] **Item 6** — `_figure_date_kind` is consulted per axis; a `yaxis(2)`
      layer cannot change the primary axis type; genuine within-axis
      disagreement still declines.
- [ ] **Item 4** — `test/test_dual_axis.py` has the secondary-axis date case and
      `test/test_mode_parity.py` has the served date case; `_spec` no longer
      hardcodes `"formats": {}` for every entry.
- [ ] Every functional item has a named regression test that was **observed red**
      before the fix (rule 8), and the red-then-green observation is recorded in
      the PR description.
- [ ] Every new or changed function has a unit test (rule 4), including the
      picture-aware formatter variant and the axis-number predicate.
- [ ] Every mutation listed in the test plan was applied once and killed its
      test.
- [ ] Non-date behaviour unchanged: full pytest green at ≥ 3,498 passed, 25/25
      cscripts, parity corpus green, and Phase 09's byte-identity guard green.
- [ ] No API key, path or secret introduced; the emitted app remains
      self-contained (`test/test_mode_parity.py` self-containment guard green).
- [ ] Commit on `feature/batch4-interactive-layer` (or a branch off it), never
      directly on `main`; the merge command is supplied with the PR. Commit
      messages describe the change only.
- [ ] Open follow-ups handed to their phases: `dash.sthlp` precedence paragraph
      → **Phase 30 item 1**; served KPI/filter/dropdown date formatting →
      **Phase 13**; the remaining `_apply_axis_spec` grammar forms →
      **Phase 15**; the served secondary axis → **Phase 27**.

---

## Risks and sequencing notes

**R1 — Phase 09 lands first, without exception.** Phase 09 item 9 fixes the
hard crash where *"24 of 35 plot types abort the entire `dash build` when their
x (or binned) variable is a Stata date"* (Stata surfaces it as **rc 7102**).
Until that lands, most date figures cannot be built at all, so several tests in
this phase cannot even be written. Phase 09 items 1, 4 and 10 also edit
`_figure_date_kind` (`dash_render.py:9268-9298`) — the same method item 6 edits,
including the same `name = ...` expression at `:9288-9290`. Land Phase 09, then
rebase this phase onto it; do not develop the two in parallel on the same
method.

**R2 — Item 3 and item 8 overlap Phase 15 item 4.** That item, from the 09-02
audit, states the superset: *"`_apply_axis_spec` has no date awareness, so every
axis_label and axis_scale form is wrong on a `%t*` axis"*, listing explicit
ticks, `minmax`, `#N` (which *"replaces the DatetimeTicker with a BasicTicker"*),
`format(%td...)` and `xscale(range())`. This phase owns the date branch,
the tick/minmax/range conversions and the `format()` behaviour; **Phase 15 item
4 then reduces to the `#N` ticker-preservation case and the remaining grammar
forms**, and **Phase 16** ports the result to the server. Agree this split
before either phase starts, or the same method is rewritten twice.

**R3 — Item 2 overlaps Phase 27.** Phase 27 items 3, 4 and 8 rework the
secondary axis: the filter callback that must update `extra_y_ranges["y2"]`,
the CDSView-restricted range, and server-side secondary-axis support. Item 2
changes what that range *means* (milliseconds, not raw numbers). Land item 2
first and tell Phase 27 the scale contract, or Phase 27's callback will write
raw values back into a millisecond range. Do not regress the existing
`_source_frame(source, self.df)` active-view computation at
`dash_render.py:9678-9681` / `:9713-9716` — that is 09-07's fix and
`test/test_axis_options.py:851` (`TestSecondaryAxisRange`) guards it.

**R4 — Items 1 and 5 edit emitted source *strings*.** Everything after
`class ServerAppBuilder` (`dash_render.py:12265`) is Python that writes Python.
Phase 06 ("facet expansion and loop unification") and Phase 07 rewrite the
emitted facet loops that contain `dash_render.py:15131` and `:15228` — the two
figures TR-10.5 touches. Sequence item 1's facet half **after** those phases, or
expect a textual conflict in a block that no type checker will help you merge.
The mitigation for the rest is TR-10.6: forward helpers, do not re-emit bodies.
REMAINING.md is explicit that *"a delegated branch inherits the standalone
behaviour instead of needing its own copy of each fix"*.

**R5 — The resolution trap.** `pd.to_numeric` on a `datetime64` column yields
microseconds **or** nanoseconds depending on the unit pandas inferred; the
09-02 audit measured the microsecond case ("1000x too large"). Always cast
explicitly: `.astype('datetime64[ms]').astype('int64')`. `_extract_finite`'s
comment at `dash_render.py:975-983` is the in-repo statement of this and is the
one correct precedent — copy it rather than inventing a divisor. Any new
`/ 1e6`-style constant in a diff is a defect.

**R6 — Non-date regression is the phase's real hazard.** Seven of the eight
items add a branch to code that runs on **every** figure, dated or not. Task
08-04's own `<verify>` clause is *"an auto scatter is byte-identical ids
aside"*, and the test enforcing it is Phase 09 item 7. Until that guard exists,
treat the full pytest count (3,498 passed / 37 skipped) as the regression net
and re-run it after each item, not once at the end.

**R7 — The `%tC` caveat carries forward.** Section 08 converts `%tC` with the
`%tc` epoch **without leap-second correction**; `_datetime_formatter_for` treats
`tc` and `tC` identically (`dash_render.py:258`). Do not "fix" that here — it is
a documented decision, and documenting it is Phase 30 item 1.

**Suggested order within the phase:** 5 → 1 → (4b) · 6 → 2 → (4a) · 3 → 7 → 8.
Item 5 before item 1 because an axis type on an empty frame proves nothing; item
6 before items 2 and 3 because the axis-kind decision must be right before
anything converts values against it; items 3, 7 and 8 last because they are
three independent blocks that share one helper and can be split across
developers once the date kind is reliably available.
