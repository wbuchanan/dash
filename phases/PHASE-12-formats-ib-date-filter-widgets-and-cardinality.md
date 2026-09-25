# Phase 12 — Formats I(b) — date filter widgets and cardinality

**Purpose.** A `dash` dashboard built on a `%td` variable ships a date dropdown
that filters *every row away*: `FilterBuilder.build_dropdown` writes the option
value as `str(Timestamp)` — `'2001-01-01 00:00:00'` — while the transported
column and its filter snapshot hold epoch milliseconds, and `_FILTER_JS`
compares the two with `String(orig[fvar][i]) !== val`, which can never be
equal. The label half is wrong too: task 08-05 asks for the *value/label split*
— raw value kept as the option value, Stata's own picture used for the display
text — and today both halves of the tuple are the same raw string. The test
that exists to guard this reads only the label half, so it is green against the
broken code. This phase closes that dropdown, extends the same "format it where
it is displayed" rule to slider endpoints, range endpoints and numeric dropdown
labels, reconciles the one KPI format that renders differently on first paint
than after the first filter move, teaches the calendar-period formats Stata's
own period picture (`1960q1`, not `Jan 1960`), stops a date variable on a
computed layer's axis from aborting the whole build with rc 7102, carries the
whole of 08-05 into the generated `bokeh serve` app, and — rule 8 — replaces
every vacuous assertion in this area with one that executes the shipped
`_FILTER_JS` under node and dies when the implementation is broken.

---

## At a glance

| | |
|---|---|
| **Work items** | 14 |
| **Functional / deliverable split** | 9 functional (items 1, 2, 3, 4, 6, 9, 10, 11, 12) · 5 deliverable (items 5, 7, 8, 13, 14) |
| **Effort mix** | 9 small · 3 medium · 2 large |
| **Renderers touched** | standalone only: items 1, 2, 3, 5, 6, 7, 9, 10, 11, 13, 14 · server only: item 4 · both: items 8, 12 |
| **Files touched** | `dash_render.py` (both `DashRenderer` and the source `ServerAppBuilder` emits); `test/test_dates.py`, `test/test_mode_parity.py`, `test/test_filter_widget_parity.py`, `test/test_axis_options.py`. Read-only: `test/fixtures/date_truth.json`. No `dash.ado` change belongs to this phase. |
| **Ultraplan coverage** | Task **08-05** — *"Format dates and numbers everywhere they are displayed"* (section 08, *Formats, dates, labels*). 08-05 carries **25** backlog items in total (10 from Appendix B + 15 from Appendix C); **14 of them are here**. The remaining 11 are split between Phase 11 (hover and tooltips) and Phase 13 (KPIs, facets, marker labels, the server-side cscript). |
| **Depends on** | **Phase 09 — Dates I (the standalone loader and primary axes).** Every item below assumes `date_vars` / `numeric_formats` are populated on the renderer and that `%t*` columns arrive as `datetime64`; that is Phase 09's loader work. |
| **Unblocks** | **Phase 13 — Formats II.** The KPI, facet and marker-label touchpoints there share `_format_date_value_standalone` and its JS twin with item 12, and its server-side date cscript exercises the code item 4 adds. |
| **Coordinates with** | **Phases 05–08** (server unification, task 15-03). Item 4 edits emitted source that 15-03 intends to delete and replace with `_DASH_MAPPER` delegation — see *Risks and sequencing notes*. **Phase 04** (resource limits) owns the hard dropdown option **cap**; item 3 here is 08-05's date-specific **warning** clause of the same defect. |

Where this phase sits in the audit's own accounting:

| | measured | source |
|---|---|---|
| Section 08 status | 6 tasks — **2 done, 4 partial** | *Status by section* |
| Section 08 final tally (DONE/PARTIAL/NOT DONE) | **1 / 5 / 0** | *Final tally, after the adversarial pass* |
| 08-05 backlog | Appendix B **10** + Appendix C **15** = **25** | *Backlog total table* |

---

## Why this phase exists

Everything in this section is copied from `REMAINING.md`, which states that
every number in it was produced by running the code, not read off a CHANGELOG.
A developer should not need to open `REMAINING.md` to know what is broken.

### The headline finding — a date dropdown filters every row away

From Appendix B, *"Three findings worth pulling out first"*, finding 3:

> **3. A date dropdown filters every row away.** `build_dropdown` writes option
> values as `str(Timestamp)` — `'2022-12-21 00:00:00'` — while the column holds
> `Timestamp`s that Bokeh transports as epoch milliseconds, so `_FILTER_JS`
> compares `1671580800000` against a date string and never matches. The display
> half is wrong too: the task requires the label formatted through the
> variable's Stata format with the raw value kept as the option value, and both
> halves of the tuple are the same raw string.

The two halves of that mismatch, in the shipped source. The option build, at
`dash_render.py:7657-7659` inside `FilterBuilder.build_dropdown`:

```python
options = [(_sentinel, "All")]
for rv in raw_values:
    options.append((rv, FilterBuilder._safe(_resolve_label(rv))))
```

`rv` comes from `_int_normalized(v) for v in source.data[varname]`
(`dash_render.py:7629-7638`), and `_resolve_label` (`:7640-7648`) resolves a
*value label* or returns `rv` unchanged — so both members of the tuple are the
same string, and for a datetime column that string is `str(Timestamp)`.

The consumer, at `dash_render.py:7070-7077` inside `_FILTER_JS`:

```javascript
if (ftype === 'dropdown') {
    const val = w.value;
    const sentinel = spec.sentinel || '__all__';
    if (val === sentinel) continue;
    for (let i = 0; i < n_rows; i++) {
        if (active[i] && String(orig[fvar][i]) !== val) active[i] = false;
    }
}
```

`orig[fvar][i]` is epoch milliseconds — the repo's own tests prove it:
`test/test_dates.py::TestDateFilterActuallyFilters::test_the_snapshot_values_are_epoch_milliseconds`
asserts `pd.Timestamp(first, unit="ms").date().isoformat() == "2001-01-02"`.
So the comparison is `String(978393600000) !== '2001-01-02 00:00:00'` for every
row, every row is deactivated, and the dashboard goes blank on selection with
no error.

### Appendix A, task 08-05 — what works, and what is left

The five touchpoints that *do* work in standalone, verified individually by the
audit (quoted in full, because the phase must not break any of them):

> - **Hover** — `[('Trade date','@{d}{%F}'), ('Value','@{v}{0.00}')]` with
>   `formatters={'@{d}': 'datetime'}`. Variable labels, not raw names; one
>   derived precision, not the three hardcoded ones.
> - **Filter widgets** — `type(range)` → `DateRangeSlider`, `type(slider)` →
>   `DateSlider`, `type(dropdown)` → `Select`.
> - **Facet labels** — `by(d)` titles render `21 Dec 2022`, `22 Dec 2022`, …
> - **KPI values** — `max`/`min`/`mean`/`p50` on a `%td` variable render
>   `19 Jan 2023` etc.; `sum` warns *"dash: sum(d) adds up dates, which has no
>   meaning."*
> - **JS recompute** — `_kpi_callback_config` carries `datekind: "td"` plus
>   `decimals` and `commas`, so the filtered value formats too.

And the *Remaining* list for 08-05, verbatim:

> 1. **Every figure carries two `HoverTool`s.** One is correct; the other is
>    `[('d','@{d}'), ('v','@{v}')]` — raw variable names, no formatter, no date
>    handling. Present with and without a `formats` key, so it is not the date
>    path that adds it. `tools=` at `dash_render.py:9552` is
>    `"pan,wheel_zoom,box_select,lasso_select,reset"` and does not include
>    `hover`, so both tools are added deliberately somewhere and one is stale.
>    The user sees two tooltips, one of them wrong.
> 2. **No dropdown cardinality warning.** The task requires a warning above a
>    reasonable cardinality suggesting `type(range)`. Measured on 5,000 distinct
>    dates: **5,001 options, zero warnings**. (Same defect as the uncapped
>    dropdown already recorded in §6 of this file; this is the date-specific
>    clause of it.)
> 3. **Server mode has none of it**: in the emitted app `variable_labels` 0,
>    `DateRangeSlider` 0, `_facet_label` 0, `_format_kpi_value` 0.
> 4. Minor: `count` on a date column renders `30.0` rather than `30`.

Remaining item 2 is **item 3** of this phase. Remaining item 3 is **item 4** of
this phase. Remaining item 1 (the double `HoverTool`) belongs to Phase 11 and
remaining item 4 (`count` on a date) to Phase 13; they are named here only so
the Appendix A evidence stands complete.

### The uncapped dropdown, from §6 of the main body

> - **Dropdown filter on a continuous variable** emits one `<option>` per
>   distinct value, uncapped — 200,001 options on 200,000 observations.
>   (`_MAX_FILTER_OPTIONS`/`_MAX_DROPDOWN`: not defined.)

Confirmed absent at HEAD — no constant, no clamp. A date column is the worst
case of this: every observation of a `%tc` variable is distinct.

### The test that certifies nothing

From Appendix C, 08-05:

> **[deli · standalone · S]** Strengthen
> `test_a_date_dropdown_shows_dates_not_epoch_numbers` — it passes against the
> broken dropdown and so certifies nothing. It reads only the LABEL half of
> each option tuple (`labels = [o[1] ... for o in w[0].options]`) and asserts
> `"2001" in joined` and `"14977" not in joined`.
> `str(Timestamp('2001-01-02'))` = '2001-01-02 00:00:00' satisfies both, so
> the test is green while (a) the option VALUE is an ISO string that can never
> equal `String(<epoch ms>)` and (b) the label ignores the variable's Stata
> picture.

The test as shipped, `test/test_dates.py:569-577`:

```python
def test_a_date_dropdown_shows_dates_not_epoch_numbers(self, tmp_path):
    from bokeh.models import Select
    w = [x for x in self._widgets(tmp_path, "dropdown")
         if isinstance(x, Select)]
    assert w, "no dropdown was built"
    labels = [o[1] if isinstance(o, tuple) else o for o in w[0].options]
    joined = " ".join(str(x) for x in labels)
    assert "2001" in joined, f"dropdown showed {labels[:4]}"
    assert "14977" not in joined
```

`o[0]` is never read. This is why the defect survived a 3,498-test suite.

And the reason no structural test would have caught it either, from Appendix C:

> **[deli · standalone · M]** Execute the shipped `_FILTER_JS` against a date
> column under node … Today every date-filter assertion is structural
> (snapshot dtype, slider bounds, the substring 'datekind' appearing in the JS
> source); nothing runs the callback, which is why the dropdown's value/label
> mismatch survived the test suite. The harness already exists and can be
> reused verbatim.

The harness is `test/test_kpi_values.py:263-300` (`_js_kpi`): it slices
`dash_render._FILTER_JS`, wraps the slice with a JSON-encoded input, writes an
`.mjs` file and runs it under `node`, skipping when `shutil.which("node")` is
`None`. It executes *the code users receive*, which is exactly what this phase
needs for the dropdown branch.

### A date on a computed layer's axis aborts the whole dashboard

From Appendix C, 08-05 (item 9 below):

> **[func · standalone · L]** Give every computed/sorted mapper a
> datetime-aware x/y extraction. 19 mappers cast the shared source column with
> `np.array(source.data[xvar], dtype=float)` (or call `_extract_finite`
> without `allow_datetime=True`), which raises on a Timestamp;
> `_build_sources_and_figures` re-raises it as a RuntimeError, so the WHOLE
> dashboard aborts with rc 7102 and no HTML file whenever a date variable is
> on the axis of a fit, smoother, univariate, range or area layer.
> `allow_datetime=True` was added for the two filter builders only. Each
> mapper must read the column as epoch ms (the `_extract_finite(...,
> allow_datetime=True)` path already does this correctly) and map the computed
> x back to datetime64 before it reaches the glyph source, or the fitted line
> lands at 1970.

The correct path already exists — `_extract_finite`, `dash_render.py:964-995`:

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

The re-raise that turns a mapper's `ValueError` into a whole-dashboard abort,
`dash_render.py:11508-11512`:

```python
except Exception as exc:
    raise RuntimeError(
        f"dash_render: failed to build figure '{name}': {exc}"
    ) from exc
```

This is the largest single item in the phase, and it is a hard crash with no
output file — worse in user-visible terms than any formatting defect beside it.

### Stata's period pictures are collapsed to `%b %Y`

From Appendix C, 08-05 (item 12 below):

> **[func · both · M]** Render the calendar-period formats with Stata's own
> period picture. `_format_date_value_standalone` collapses `%tm`/`%tq`/`%th`
> to `"%b %Y"` and sends `%tw` to the day branch, so a quarterly variable
> reads "Jan 1960" where Stata writes "1960q1", a half-yearly one "Jan 1960"
> vs "1960h1", and a weekly one "29 Jan 1958" vs "1958w5". … the value
> formatter, its JS twin and `_datetime_formatter_for` share the same
> collapse, so KPI cards, facet titles, marker labels and (once fixed)
> dropdown labels all mis-state the period. The Stata truth is already in the
> repo and unused: `test/fixtures/date_truth.json` records a `display` string
> for every value, and only the `iso` field is ever asserted.

The collapse, `dash_render.py:213-220`:

```python
if kind == "ty":
    return f"{ts.year}"
if kind in ("tc", "tC"):
    return ts.strftime("%d %b %Y %H:%M:%S")
if kind in ("tm", "tq", "th"):
    return ts.strftime("%b %Y")
return ts.strftime("%d %b %Y")
```

The unused truth, read from `test/fixtures/date_truth.json` while writing this
phase (confirming Appendix C's claim, not replacing it):

| kind | SIF value | fixture `display` (Stata) | fixture `iso` | what dash renders today |
|---|---:|---|---|---|
| `%tq` | `-40` | `1950q1` | `1950-01-01` | `Jan 1950` |
| `%tq` | `0` | `1960q1` | `1960-01-01` | `Jan 1960` |
| `%th` | `-20` | `1950h1` | `1950-01-01` | `Jan 1950` |
| `%tw` | `-100` | `1958w5` | `1958-01-29` | `29 Jan 1958` |
| `%tm` | `-120` | `1950m1` | `1950-01-01` | `Jan 1950` |

Only `iso` is asserted: the fixture's date records are read at
`test/test_dates.py:104` and `:138`, both of which compare
`str(got.iloc[i].date())` against `v["iso"]`. (`display` *is* asserted, but for
`truth["numeric_formats"]` at `test/test_dates.py:431` — a different fixture
branch.)

### The numeric half of "everywhere they are displayed"

Three separate places lose a Stata numeric picture. First, slider and range
**endpoints** — the date branches pass a formatter, the numeric branches pass
none. `dash_render.py:7766-7767`:

```python
widget = Slider(title=_slider_title, start=vmin, end=vmax,
                value=vmin, step=vstep)
```

and `dash_render.py:7847-7849`:

```python
widget = RangeSlider(title=_raw_range_lbl,
                     start=vmin, end=vmax,
                     value=(vmin, vmax), step=vstep)
```

No `format=`, so Bokeh's default `0[.]00` renders a `%12.0fc` variable as
`3000000.00`. The helper that would fix it already exists and is already
tested: `_stata_numeric_pattern` (`dash_render.py:395`) returns `'0,0'` for
`%9.0fc`, `'0,0.00'` for `%9.2fc`, `'0.00'` for `%9.2f`
(`test/test_dates.py::TestNumericDisplayFormats::test_a_bokeh_tick_pattern_is_produced`).

Second, dropdown **labels** for formatted numerics — `_resolve_label` resolves
value labels only, so a `%12.0fc` filter lists `3000000`, `3010000`, … instead
of `3,000,000`.

Third, the `%9.0g` KPI **changes shape on the first filter move**, which two
comments in the shipped source promise it will not. The JS,
`dash_render.py:7310-7313`:

```javascript
if (k.general) {
    // Stata's %9.0g: six significant digits, the same as Python's
    // f"{value:g}" on the initial render.
    fmt = String(Number(result.toPrecision(6)));
}
```

The Python, `DashRenderer._format_kpi_value` at `dash_render.py:8448-8452`:

```python
if fmt_str.strip() in ("", "%9.0g"):
    # Stata's default display: six significant digits.  The callback
    # does the same via toPrecision(6), so the card does not change
    # shape when a filter moves.
    return f"{float(value):g}"
```

They are not the same function. Measured at HEAD while writing this phase:

| value | first render, Python `f"{v:g}"` | after a filter move, JS `String(Number(v.toPrecision(6)))` |
|---:|---|---|
| `1234567` | `1.23457e+06` | `1234570` |
| `3000000` | `3e+06` | `3000000` |
| `123456` | `123456` | `123456` |
| `0.000012345` | `1.2345e-05` | `0.000012345` |

(`REMAINING.md` locates the promise at `dash_render.py:7621`; at HEAD that line
is inside `_int_normalized`, and the promise is written in the two places
quoted above. Prefer the symbols — the defect and the measurement are
unchanged.)

### Nothing anywhere tests server-mode formats

From Appendix C, 08-05:

> **[deli · both · M]** No test anywhere exercises server-mode display
> formats, and the two parity suites that exist to catch exactly this
> divergence are blind to it because they hardcode an empty formats map. Add a
> date/format case to `test/test_mode_parity.py` and
> `test/test_filter_widget_parity.py` (a %td x-variable, a %tm dropdown, a
> %12.0fc KPI) so that the standalone/server split the auditor found —
> DateRangeSlider vs RangeSlider, 'Jan 2001' vs '492.0', '31 Dec 2001' vs
> '15340.0' — fails a test instead of needing a manual probe.

Both suites really do hardcode it. `test/test_mode_parity.py:70-73`:

```python
bo = {"layout": "auto", "link": "", "filter": "", "theme": "",
      "scheme": "", "session_scheme": "", "title": "", "subtitle": "",
      "registry": "g1", "tabs": "", "filter_position": "top",
      "level": "95", "formats": {}}
```

`test/test_filter_widget_parity.py:57-61` carries the same `"formats": {}`.
The one guard designed to catch a standalone/server divergence is switched off
for exactly the feature this phase ships.

### And the server app never reads `formats` at all

`build_options["formats"]` reaches the generated app and nothing consumes it.
The emitted loader's only coercion, `dash_render.py:13162-13165`:

```python
"    # Convert to numeric where possible",
"    for col in df.columns:",
"        if not type_is_str.get(col, False):",
"            df[col] = pd.to_numeric(df[col], errors='coerce')",
```

The emitted filter loop guards range and slider on `is_numeric_dtype`
(`dash_render.py:15405`), which a `datetime64` column fails; the emitted
dropdown (`:15378-15395`) stringifies with `str(v)`; the emitted `_format_kpi`
(`dash_render.py:13665`) has a `%w.df`/`%w.dg`/`%w.de` regex and no date branch
and no variable-format fallback; and `_format_date_value_standalone` is already
in the helper-forwarding tuple at `dash_render.py:12394-12396` — copied into the
generated module and never called. Appendix A's count of the emitted app is
the summary: `variable_labels` 0, `DateRangeSlider` 0, `_facet_label` 0,
`_format_kpi_value` 0.

---

## Epics

| epic | goal | items |
|---|---|---|
| **A — The dropdown that filters nothing** | Make a date dropdown select rows instead of erasing them, label it in Stata's picture, warn before it grows to one option per observation, and replace the assertions that let this ship. | 1, 2, 3, 5, 7, 13 |
| **B — Numbers and periods, everywhere a value is displayed** | Carry the Stata numeric picture onto slider endpoints, range endpoints and dropdown labels; make `%9.0g` render identically before and after a filter move; render `%tm`/`%tq`/`%th`/`%tw` with Stata's own period picture in Python and in its JS twin; test the numeric half that only the pure helpers cover today. | 6, 10, 11, 12, 14 |
| **C — Dates on computed axes, and in `dash serve`** | Stop a date axis on a computed layer from aborting the build, port the whole of 08-05 into the generated server app, and turn the two blind parity suites into the guard that keeps both renderers together. | 4, 8, 9 |

---

## User stories

### Epic A — the dropdown that filters nothing

**A-1.** *As a Stata user pasting a `twoway` command, I want
`dash line close date, filter(date, type(dropdown))` to produce a dropdown that
narrows the dashboard when I pick a date, so that the filter I asked for does
what a filter does.*

- **Given** a dashboard built from a `%td` variable with a `type(dropdown)`
  filter, **when** the viewer selects any option other than "All", **then** the
  visible row count is greater than zero and equals the number of observations
  carrying that date.
- **Given** the same dashboard, **when** the shipped `_FILTER_JS` dropdown
  branch is executed under node against the snapshot column, **then** the
  active mask has exactly the rows of the selected date set to `true`.
- **Given** the option list, **when** its value half is read, **then** every
  value is the decimal string of the epoch-millisecond integer that
  `orig[fvar][i]` holds for that row.

**A-2.** *As a dashboard viewer, I want the dropdown to list dates the way
Stata prints them, so that I can find the date I want without reading
`2001-01-02 00:00:00`.*

- **Given** a `%td` filter variable, **when** the dropdown renders, **then**
  each label reads `02 Jan 2001` (the variable's Stata picture), while the
  option value stays the epoch-millisecond string.
- **Given** a `%tm` filter variable, **when** the dropdown renders, **then**
  each label reads Stata's month picture for that value and never the raw SIF
  number.

**A-3.** *As a Stata user, I want to be told when a dropdown filter on a date
would produce thousands of options, so that I switch to `type(range)` before I
ship the dashboard rather than after.*

- **Given** a filter variable with more distinct values than the cardinality
  threshold, **when** `build_dropdown` runs, **then** a `UserWarning` is
  emitted naming the variable, the distinct-value count and
  `type(range)` as the suggested alternative.
- **Given** a filter variable below the threshold, **when** `build_dropdown`
  runs, **then** no warning is emitted.

**A-4.** *As a package maintainer, I want the date-filter tests to execute the
JavaScript we actually ship, so that a value/label mismatch can never again
pass a 3,498-test suite.*

- **Given** `test_a_date_dropdown_shows_dates_not_epoch_numbers`, **when** the
  option value half is reverted to `str(Timestamp)`, **then** the test fails.
- **Given** the new node-executed case, **when** `node` is absent, **then** the
  test skips with a reason — and a skip is not counted as a pass.

### Epic B — numbers and periods, everywhere a value is displayed

**B-1.** *As a Stata user whose variable carries `%12.0fc`, I want the filter
widget's endpoints and the dropdown's labels to show `3,000,000`, so that the
dashboard reads the way my `list` output does.*

- **Given** a `%12.0fc` variable with a `type(range)` filter, **when** the
  widget renders, **then** its `format` is a `NumeralTickFormatter`-compatible
  pattern derived from `_stata_numeric_pattern('%12.0fc')` = `'0,0'`, and the
  endpoints read `3,000,000`, not `3000000.00`.
- **Given** the same variable with `type(slider)`, **then** the same holds.
- **Given** the same variable with `type(dropdown)`, **when** the options
  render, **then** each label is `_format_stata_numeric(value, '%12.0fc')` and
  the option value is unchanged.
- **Given** a variable with no Stata display format, **when** any of the three
  widgets renders, **then** its appearance is byte-identical to today's.

**B-2.** *As a dashboard viewer, I want a KPI card to keep its shape when I move
a filter, so that I do not read `1.23457e+06` before the move and `1234570`
after it and think the number changed.*

- **Given** a `%9.0g` (or empty-`fmt()`) KPI whose value is `1234567`,
  **when** the dashboard first renders and again after any filter move,
  **then** both renderings are the same string.
- **Given** the same KPI, **when** the JS branch is executed under node with
  the value `3000000`, **then** its output equals `DashRenderer._format_kpi_value`'s
  output for the same value and format.

**B-3.** *As a Stata user with a quarterly variable, I want dash to print
`1960q1` where Stata prints `1960q1`, so that the dashboard does not invent a
month my data does not have.*

- **Given** `%tq` value `0`, **when** it is formatted for a KPI card, a facet
  title, a marker label or a dropdown label, **then** the text is `1960q1`, the
  `display` string `test/fixtures/date_truth.json` records for that value.
- **Given** `%th` value `-20`, **then** `1950h1`. **Given** `%tw` value `-100`,
  **then** `1958w5`. **Given** `%tm` value `-120`, **then** `1950m1`.
- **Given** the JS twin inside `_FILTER_JS`, **when** it formats the same epoch
  millisecond for the same kind, **then** it produces the identical string.

### Epic C — dates on computed axes, and in `dash serve`

**C-1.** *As a Stata user, I want `dash (scatter close date) (lfit close date)`
on `sysuse sp500` to build, so that a date on a fitted layer's axis is ordinary
usage rather than a crash.*

- **Given** any spec placing a `%t*` variable on the x or y of a fit, smoother,
  univariate, range or area layer, **when** `dash build` runs, **then** it
  returns rc 0 and writes a non-empty HTML file.
- **Given** the same spec, **when** the fitted line is inspected, **then** its x
  values are datetime64 within the data's own date range, and not 1970.
- **Given** a spec with no `formats` key, **when** the same mappers run,
  **then** their output is unchanged from today's.

**C-2.** *As a `dash serve` operator, I want the served app to format dates and
numbers the way the standalone HTML does, so that a dashboard does not change
meaning when it is served instead of saved.*

- **Given** one spec carrying `formats: {"date": "%td"}` built through both
  renderers, **when** the filter widgets are compared, **then** both produce a
  `DateRangeSlider` (not `RangeSlider` on one side).
- **Given** a `%tm` KPI, **when** both renderers format it, **then** both
  produce the same string — not `'Jan 2001'` against `'492.0'`, and not
  `'31 Dec 2001'` against `'15340.0'`.
- **Given** a `%tm` dropdown and a `%12.0fc` KPI in the parity corpus, **when**
  the suite runs, **then** a divergence fails a test rather than needing a
  manual probe.

**C-3.** *As a package maintainer, I want the two parity suites to stop
hardcoding an empty `formats` map, so that the guard that exists to catch this
class of divergence is actually switched on.*

- **Given** `test/test_mode_parity.py` and `test/test_filter_widget_parity.py`,
  **when** their spec builders are called with a formats map, **then** that map
  reaches both renderers.
- **Given** the server date support from item 4 reverted, **when** the parity
  suites run, **then** they fail.

---

## Business requirements

| id | requirement | testable as |
|---|---|---|
| **BR-12.1** | A date dropdown filter must select rows. Choosing any non-sentinel option leaves a non-zero, correct row count. | Epic A test 1 (node-executed `_FILTER_JS`) |
| **BR-12.2** | Every filter widget must display values through the variable's Stata display format — dates in their period picture, numerics with their decimals and comma grouping — while keeping the raw transported value as the machine-readable half. | Epic A tests 2–3; Epic B tests 1–3 |
| **BR-12.3** | `dash` must warn, not silently comply, when a dropdown filter would list more distinct values than a viewer can use, and must name `type(range)` as the alternative. | Epic A test 4 |
| **BR-12.4** | A displayed value must not change shape between first render and any later recompute. | Epic B test 4 |
| **BR-12.5** | A calendar-period variable must be printed with Stata's own period picture, and dash's Python and JavaScript renderings of it must agree exactly. | Epic B tests 5–6 |
| **BR-12.6** | A date variable on any layer's axis must never abort the build. `dash` returns rc 0 and writes a file, or reports a named, actionable diagnostic. | Epic C test 1 |
| **BR-12.7** | The `bokeh serve` app must display dates and numbers identically to the standalone HTML built from the same spec. | Epic C tests 2–3 |
| **BR-12.8** | No behaviour change for a variable that carries no Stata display format: unformatted dashboards render exactly as they do at HEAD. | negative twins in every epic |
| **BR-12.9** | Every defect fixed in this phase gains a regression test that fails before the fix and passes after (project rule 8), and every new or changed function gains a unit test (project rule 4). | the *Test plan* mutation column |

---

## Technical requirements

### Epic A — the dropdown

**TR-12.1 — the option value must be the epoch-millisecond string.**
In `FilterBuilder.build_dropdown` (`dash_render.py:7571`), the `raw_values`
build at `:7629-7638` currently runs every column value through
`_int_normalized`, which calls `float(s)` and falls back to `str(v)` — on a
`Timestamp` that fallback yields `'2001-01-02 00:00:00'`. The date branch must
instead convert the column the way `_extract_finite(..., allow_datetime=True)`
does (`dash_render.py:986-993`): `pd.Series(col).astype('datetime64[ms]').astype('int64')`,
then use the decimal string of that integer as the option value. Bokeh's
`Select` carries option values as strings and `_FILTER_JS` compares
`String(orig[fvar][i])` against `w.value` (`dash_render.py:7077`), so the value
half must be exactly `str(int(epoch_ms))`. The existing `_int_normalized`
normalisation (`"0.0"` → `"0"`) must continue to apply to non-date columns
unchanged.

**TR-12.2 — `build_dropdown` must learn the date kind.**
`build_slider` (`:7707`) and `build_range` (`:7788`) already take a `date_kind`
argument, and the call sites at `dash_render.py:11780-11783` and `:11800-11803`
already pass `date_kind=getattr(self, 'date_vars', {}).get(fvar, '')`. Give
`build_dropdown` the same parameter with the same default and pass it from the
call site at `dash_render.py:11760-11775`. Absent or empty, the method's
behaviour is unchanged.

**TR-12.3 — the label half goes through the Stata picture.**
`_resolve_label` (`dash_render.py:7640-7648`) resolves a value label or returns
the raw string. Extend it so that, for a date column, the fallback is
`_format_date_value_standalone(epoch_ms, kind)` (`dash_render.py:203`) rather
than `rv`; a value label, where one exists, still wins. The tuple built at
`:7657-7659` therefore becomes `(str(int(epoch_ms)), _safe(<formatted date>))`
— the value/label split task 08-05 names.

**TR-12.4 — the cardinality warning.**
After `raw_values` is built (`dash_render.py:7629-7638`) and before the options
are assembled, compare `len(raw_values)` against a module-level threshold
constant and `warnings.warn(..., UserWarning, stacklevel=2)` when it is
exceeded. The message must name the variable, the distinct-value count and
`type(range)`. The measured worst cases this guards: **5,001 options on 5,000
distinct dates, zero warnings** (Appendix A) and **200,001 options on 200,000
observations** (§6). The hard *cap* (`_MAX_FILTER_OPTIONS`/`_MAX_DROPDOWN`,
neither of which is defined at HEAD) is Phase 04's item; this phase supplies the
warning 08-05 asks for and must read the cap constant if Phase 04 has already
defined one rather than introducing a second name for it.

### Epic B — numbers and periods

**TR-12.5 — numeric widget endpoints.**
`build_slider`'s numeric branch (`dash_render.py:7766-7767`) builds
`Slider(title=..., start=..., end=..., value=..., step=...)` and
`build_range`'s (`:7847-7849`) builds `RangeSlider(...)`, neither passing
`format=`. Thread a `numeric_fmt` argument from the two call sites
(`dash_render.py:11780-11783`, `:11800-11803`) exactly as `date_kind` is
threaded, resolve it with `_stata_numeric_pattern` (`dash_render.py:395`), and
pass the result as `format=` when it is not `None`. Measured helper outputs to
rely on: `%9.0fc` → `'0,0'`, `%9.2fc` → `'0,0.00'`, `%9.2f` → `'0.00'`,
`%9.0f` → `'0'`, `%12.4f` → `'0.0000'`; and `%td`, `%9s`, `%9.0g`, `%12.0gc`,
`''`, `None` → `None` (the helper's own parametrised test,
`test/test_dates.py:458-476`). A `None` pattern must leave the widget exactly
as it is today.

**TR-12.6 — numeric dropdown labels.**
The same `_resolve_label` change as TR-12.3, on the non-date side: when the
variable carries a Stata numeric format and no value label applies, the label
is `_format_stata_numeric(value, fmt)` (`dash_render.py:~415`). A `%12.0fc`
dropdown then lists `3,000,000` instead of `3000000`. This is explicitly
*distinct* from the date items: fixing the date branch alone leaves formatted
numerics unformatted.

**TR-12.7 — one `%9.0g` rendering, not two.**
`DashRenderer._format_kpi_value` (`dash_render.py:8418`) returns
`f"{float(value):g}"` for `fmt_str.strip() in ("", "%9.0g")`
(`:8448-8452`); the `k.general` branch of `_FILTER_JS` (`:7310-7313`) returns
`String(Number(result.toPrecision(6)))`. Measured divergence: `1234567` →
`1.23457e+06` / `1234570`; `3000000` → `3e+06` / `3000000`. Pick one rendering
and make both sides implement it — the comments at `:7311-7312` and
`:8449-8451` both assert the shapes already agree, so whichever is chosen, both
comments must end up true. Whichever way it goes, the small-magnitude cases
that already agree (`123456`, `1.2345e-05`) must not move.

**TR-12.8 — Stata's period pictures.**
Three implementations share one kind table and must stay byte-compatible:
`_format_date_value_standalone` (`dash_render.py:203`, table at `:213-220`),
`DashRenderer._format_date_value` (`:8860`), and the JS twin inside
`_FILTER_JS` (`:7285-7307`). `_datetime_formatter_for` (`:247`) carries the
same collapse for axis ticks. Replace the `%b %Y` collapse for `tm`/`tq`/`th`
and the day-branch fallthrough for `tw` with Stata's pictures, derived from the
period the timestamp falls in:

| kind | Stata picture | example (fixture value → `display`) |
|---|---|---|
| `tm` | `<year>m<month>` | `-120` → `1950m1` |
| `tq` | `<year>q<quarter>` | `-40` → `1950q1`, `0` → `1960q1` |
| `th` | `<year>h<half>` | `-20` → `1950h1` |
| `tw` | `<year>w<week>` | `-100` → `1958w5` |

The fixture is the oracle: `test/fixtures/date_truth.json`,
`date_formats["%tq"]["values"][i]["display"]`, and it is already in the repo.
`ty`, `td`, `tc` and `tC` are unchanged.

### Epic C — computed axes and the server

**TR-12.9 — datetime-aware extraction in 19 mappers.**
Two mappers call `_extract_finite` without `allow_datetime=True`
(`dash_render.py:4666` `map_histogram`, `:4830` `map_kdensity`); seventeen cast
the shared column directly with `np.array(source.data[xvar], dtype=float)`:
`:3614` `map_area`, `:3787` `map_spike`, `:3845` `map_lfit`, `:3895`
`map_qfit`, `:3942` `map_lfitci`, `:4023` `map_qfitci`, `:4127` `map_lowess`,
`:4300` `map_lpoly`, `:4366` `map_lpolyci`, `:4543` `map_fpfit`, `:4591`
`map_fpfitci`, `:5065` `map_rcap`, `:5237` `map_dropline`, `:5320`
`map_rcapsym`, `:5889` `map_rscatter`, `:5942` `map_mspline`, `:6011`
`map_mband`. Each must (a) read the column as epoch milliseconds through the
`allow_datetime=True` path, (b) compute in that space, and (c) map the computed
x back to `datetime64` before it reaches the glyph source — otherwise the
fitted line lands at 1970. The failure mode today is not a wrong line but no
dashboard at all: the mapper's exception is re-raised as a `RuntimeError` at
`dash_render.py:11510` and surfaces in Stata as **rc 7102 with no HTML file**.

**TR-12.10 — the server port of 08-05, in seven parts.**
`build_options["formats"]` already reaches the generated app; nothing reads it.

| part | what | where in the emitted source |
|---|---|---|
| (a) | convert `%t*` columns and record `date_vars` / `numeric_formats` | `dash_render.py:13123` (emitted `_load_spec_and_data`); the only coercion today is `pd.to_numeric(df[col], errors='coerce')` at `:13162-13165` |
| (b) | assign both onto the mapper so the inlined `_apply_mlabel_opts` date branch can fire | `dash_render.py:12432` (`_DASH_MAPPER = GlyphMapper(scheme=_DASH_SCHEME)`) |
| (c) | format `by()` facet labels | `dash_render.py:8630-8663` (emitted facet-label build using `str(_bval)`) |
| (d) | build `DateRangeSlider` / `DateSlider` and widen the numeric guards | emitted filter loop `dash_render.py:15364-15460`; range at `:15403` guarded by `if not pd.api.types.is_numeric_dtype(df[fvar])`, slider at `:15433` |
| (e) | format dropdown options (value/label split, as TR-12.1/TR-12.3) | emitted dropdown at `dash_render.py:15378-15395`, which builds `(str(v), html.escape(str(vlabels.get(...))))` |
| (f) | give the emitted `_format_kpi` the date branch, the variable's own Stata format fallback, and the sum-on-a-date warning | `dash_render.py:13665` (emitted `_format_kpi`, today a `%[0-9]*\.([0-9]+)([fge])` regex only); its three call sites `_format_kpi(val, kpi.get('fmt',''))` at `:15332` (first render), `:15645` (filter change), `:15697` (brush) |
| (g) | add the labelled/formatted hover the standalone `_hover_row` builds | mirror `DashRenderer._make_figure._hover_row` |

`_format_date_value_standalone` is already forwarded into the generated module
by the helper-copy list at `dash_render.py:12394-12396` and is never called;
the remaining date helpers (`_stata_date_kind`, `_stata_dates_to_datetime`,
`_datetime_formatter_for`) must join that tuple so they exist in the emitted
app. Note the call-site signature change in (f): three sites pass
`(val, fmt)` today and will need the variable name and statistic to reach the
date branch, the same two arguments `DashRenderer._format_kpi_value` takes
(`varname`, `stat`, `dash_render.py:8418-8419`).

**TR-12.11 — un-blind the parity suites.**
`test/test_mode_parity.py:70-73` (`_spec`'s `bo` dict) and
`test/test_filter_widget_parity.py:57-61` (`_spec`) both hardcode
`"formats": {}`. Give each an optional formats argument that reaches both
renderers, and add the three cases Appendix C names: a `%td` x-variable, a
`%tm` dropdown, a `%12.0fc` KPI. The divergences these must catch, as measured
by the audit: `DateRangeSlider` vs `RangeSlider`; `'Jan 2001'` vs `'492.0'`;
`'31 Dec 2001'` vs `'15340.0'`.

**TR-12.12 — nothing regresses for unformatted data.**
Every change above is gated on a non-empty `formats` entry for the variable in
question. The suite's existing negative twins —
`test_a_numeric_filter_is_unchanged` (`test/test_dates.py:578-587`),
`test_a_numeric_kpi_is_unchanged` (`:522-524`),
`test_mlabel_on_a_plain_variable_is_unchanged` (`:751-760`) — must pass
unchanged, and the facet twin item 14 adds joins them.

---

## Work items

Every item below is reproduced with the number it carries in the phase
assignment; none is dropped, merged or summarised. Tags are
`[kind · renderer · effort]`, as `REMAINING.md` uses them.

### Item 1 — the date dropdown's option VALUE  `[func · standalone · S]`

Make the date dropdown filter. `FilterBuilder.build_dropdown` writes option
VALUES as `str(Timestamp)` ("2001-01-01 00:00:00") while the data column and its
snapshot hold epoch milliseconds, and `_FILTER_JS` matches with
`String(orig[fvar][i]) !== val`, which can never be equal. Give the date branch
the same treatment the range/slider branches got: emit the epoch-millisecond
number as the option value (and the formatted date as the label).

**Where.** `dash_render.py:7571` `FilterBuilder.build_dropdown` (the
`_int_normalized`/`raw_values` block at 7629-7638 and the `options` build at
7657-7659); `dash_render.py:7077` inside `_FILTER_JS`
(`if (active[i] && String(orig[fvar][i]) !== val)`).

**Evidence.** Appendix B, 08-05 — and Appendix B's *"Three findings worth
pulling out first"*, finding 3, quoted in full above.

### Item 2 — the date dropdown's DISPLAY text  `[func · standalone · S]`

Format the date dropdown's DISPLAY text through the variable's Stata format
while keeping the raw value as the option value — the value/label split the task
names. Today both halves of the tuple are the same `str(Timestamp)`.

**Where.** `dash_render.py:7641` `_resolve_label` and 7657-7659
`options.append((rv, FilterBuilder._safe(_resolve_label(rv))))` in
`build_dropdown`; reuse `_format_date_value_standalone` (`dash_render.py:203`).

**Evidence.** Appendix B, 08-05.

### Item 3 — the date-cardinality warning  `[func · standalone · S]`

Add the date-cardinality warning for dropdowns: above a reasonable number of
distinct values, warn and suggest `type(range)`.

**Where.** `dash_render.py:7629-7638` in `FilterBuilder.build_dropdown`, after
`raw_values` is built.

**Evidence.** Appendix A, 08-05, remaining item 2: *"Measured on 5,000 distinct
dates: 5,001 options, zero warnings."* Main body §6: *"200,001 options on
200,000 observations. (`_MAX_FILTER_OPTIONS`/`_MAX_DROPDOWN`: not defined.)"*

### Item 4 — carry the whole of 08-05 into the generated server app  `[func · server · L]`

Carry the whole of 08-05 into the generated server app. `build_options["formats"]`
reaches the app but nothing reads it, so no column is converted to datetime64 and
none of the six touchpoints formats anything. Concretely: (a) convert date columns
and record `date_vars`/`numeric_formats` in the emitted `_load_spec_and_data`;
(b) assign them onto `_DASH_MAPPER` so the inlined `_apply_mlabel_opts` date
branch can fire; (c) format facet labels; (d) build DateRangeSlider/DateSlider and
widen the `is_numeric_dtype` guards; (e) format dropdown options; (f) give the
emitted `_format_kpi` the date branch, the variable's own Stata format fallback,
and the sum-on-a-date warning; (g) add the labelled/formatted hover the standalone
`_hover_row` builds.

**Where.** `dash_render.py:13123` (emitted `_load_spec_and_data`); 12432
(`_DASH_MAPPER = GlyphMapper(scheme=_DASH_SCHEME)`); 15364-15460 (emitted
filter-widget loop: dropdown at 15378, range at 15403 with
`if not pd.api.types.is_numeric_dtype(df[fvar])`, slider at 15433); 13665
(emitted `_format_kpi`); 15332 / 15645 / 15697
(`_format_kpi(val, kpi.get('fmt',''))` at first render, on filter change, on
brush); 8630-8663 (emitted by()-facet label build using `str(_bval)`);
12394-12396 (the helper-copy list, which already carries
`_format_date_value_standalone` but nothing calls it).

**Evidence.** Appendix A, 08-05, remaining item 3: *"Server mode has none of
it: in the emitted app `variable_labels` 0, `DateRangeSlider` 0, `_facet_label`
0, `_format_kpi_value` 0."* Appendix B, 08-05.

### Item 5 — a test that the date dropdown actually FILTERS  `[deli · standalone · S]`

Add a test that the date dropdown actually FILTERS, not merely that its labels
contain a year. The current test would pass against the broken implementation
(and does).

**Where.** `test/test_dates.py:569`
`TestDateFilterWidgets::test_a_date_dropdown_shows_dates_not_epoch_numbers` —
assert the option value parses as the same epoch-ms number the snapshot column
holds, alongside the existing label assertion.

**Evidence.** Appendix B, 08-05.

### Item 6 — one rendering of a `%9.0g` KPI  `[func · standalone · S]`

Reconcile the two renderings of a `%9.0g` (general) KPI between first render and
JS recompute for large magnitudes. Python emits `f"{v:g}"` while the JS emits
`String(Number(result.toPrecision(6)))`, so the same card changes shape on the
first filter move — which the code comment at `dash_render.py:7621` explicitly
promises it will not.

**Where.** `dash_render.py:7312-7314` (the `k.general` branch of `_FILTER_JS`)
vs `DashRenderer._format_kpi_value` (`dash_render.py:8418`) /
`_effective_kpi_fmt`.

**Evidence.** Appendix B, 08-05; the two promise comments and the measured
divergence table under *Why this phase exists*.

### Item 7 — strengthen the vacuous dropdown test  `[deli · standalone · S]`

Strengthen `test_a_date_dropdown_shows_dates_not_epoch_numbers` — it passes
against the broken dropdown and so certifies nothing. It reads only the LABEL
half of each option tuple (`labels = [o[1] ... for o in w[0].options]`) and
asserts `"2001" in joined` and `"14977" not in joined`.
`str(Timestamp('2001-01-02'))` = '2001-01-02 00:00:00' satisfies both, so the
test is green while (a) the option VALUE is an ISO string that can never equal
`String(<epoch ms>)` and (b) the label ignores the variable's Stata picture. Add
assertions on `o[0]` (the value must be the epoch-millisecond number that
`_FILTER_JS` compares against) and on the label matching the %tm/%td picture, and
add a JS-level or DOM-level assertion that selecting an option leaves a non-zero
row count.

**Where.** `test/test_dates.py:569`
`TestDateFilterWidgets::test_a_date_dropdown_shows_dates_not_epoch_numbers`.

**Evidence.** Appendix C, 08-05. Items 5 and 7 are the Appendix B and Appendix C
statements of the same deliverable, kept separate because item 7 adds the label
picture and the row-count assertion; satisfy both in one strengthened test.

### Item 8 — a date/format case in the two parity suites  `[deli · both · M]`

No test anywhere exercises server-mode display formats, and the two parity suites
that exist to catch exactly this divergence are blind to it because they hardcode
an empty formats map. Add a date/format case to `test/test_mode_parity.py` and
`test/test_filter_widget_parity.py` (a %td x-variable, a %tm dropdown, a %12.0fc
KPI) so that the standalone/server split the auditor found — DateRangeSlider vs
RangeSlider, 'Jan 2001' vs '492.0', '31 Dec 2001' vs '15340.0' — fails a test
instead of needing a manual probe.

**Where.** `test/test_mode_parity.py:74`; `test/test_filter_widget_parity.py:61`;
`test/test_server_*.py`.

**Evidence.** Appendix C, 08-05; the two hardcoded `"formats": {}` blocks quoted
above.

### Item 9 — datetime-aware x/y extraction in every computed mapper  `[func · standalone · L]`

Give every computed/sorted mapper a datetime-aware x/y extraction. 19 mappers cast
the shared source column with `np.array(source.data[xvar], dtype=float)` (or call
`_extract_finite` without `allow_datetime=True`), which raises on a Timestamp;
`_build_sources_and_figures` re-raises it as a RuntimeError, so the WHOLE dashboard
aborts with rc 7102 and no HTML file whenever a date variable is on the axis of a
fit, smoother, univariate, range or area layer. `allow_datetime=True` was added for
the two filter builders only. Each mapper must read the column as epoch ms (the
`_extract_finite(..., allow_datetime=True)` path already does this correctly) and
map the computed x back to datetime64 before it reaches the glyph source, or the
fitted line lands at 1970.

**Where.** `dash_render.py:964` `_extract_finite` (the `allow_datetime` switch)
and its two format-blind callers at `:4666` `map_histogram`, `:4830`
`map_kdensity`; the float-cast pairs at `:3614` `map_area`, `:3787` `map_spike`,
`:3845` `map_lfit`, `:3895` `map_qfit`, `:3942` `map_lfitci`, `:4023`
`map_qfitci`, `:4127` `map_lowess`, `:4300` `map_lpoly`, `:4366` `map_lpolyci`,
`:4543` `map_fpfit`, `:4591` `map_fpfitci`, `:5065` `map_rcap`, `:5237`
`map_dropline`, `:5320` `map_rcapsym`, `:5889` `map_rscatter`, `:5942`
`map_mspline`, `:6011` `map_mband`; the re-raise at `dash_render.py:11510`.

**Evidence.** Appendix C, 08-05.

### Item 10 — Stata numeric format on slider/range ENDPOINTS  `[func · standalone · S]`

Carry the Stata numeric display format onto filter slider/range ENDPOINTS.
`build_slider` and `build_range` already take `date_kind` and set
`format=DatetimeTickFormatter()` for clock series, but a plain numeric widget is
built with no `format=` at all, so Bokeh's default `0[.]00` shows `3000000.00` for
a `%12.0fc` variable. `_stata_numeric_pattern` already returns `'0,0'` for that
format; pass it through the same way `date_kind` is passed. The section Overview
names "slider endpoints" as one of the six places the format is lost.

**Where.** `dash_render.py:7707` `FilterBuilder.build_slider` (numeric branch at
`:7766-7768`), `:7788` `FilterBuilder.build_range` (numeric branch at
`:7841-7844`); the two call sites that would pass it, `dash_render.py:11780-11783`
and `:11800-11803` (they already pass
`date_kind=getattr(self,'date_vars',{}).get(fvar,'')`); helper
`_stata_numeric_pattern` at `dash_render.py:395`.

**Evidence.** Appendix C, 08-05; the two format-less widget constructors quoted
above.

### Item 11 — Stata numeric format on dropdown LABELS  `[func · standalone · S]`

Format dropdown option LABELS through the variable's Stata numeric format.
`_resolve_label` resolves value labels only and returns the raw string otherwise,
so a `%12.0fc` filter dropdown lists `3000000`, `3010000`, ... instead of
`3,000,000`. This is the non-date half of the value/label split the task asks for,
and the section Overview names "dropdown options" explicitly. Distinct from the
auditor's two date-dropdown items: fixing the date branch alone leaves formatted
numerics unformatted.

**Where.** `dash_render.py:7571` `FilterBuilder.build_dropdown`, `_resolve_label`
at `:7640-7648`, the options build at `:7657-7659`; caller
`dash_render.py:11760-11775` (where a `numeric_fmt`/`date_kind` argument would be
passed); `_format_stata_numeric` at `dash_render.py:~415`.

**Evidence.** Appendix C, 08-05.

### Item 12 — Stata's own calendar-period pictures  `[func · both · M]`

Render the calendar-period formats with Stata's own period picture.
`_format_date_value_standalone` collapses `%tm`/`%tq`/`%th` to `"%b %Y"` and sends
`%tw` to the day branch, so a quarterly variable reads "Jan 1960" where Stata
writes "1960q1", a half-yearly one "Jan 1960" vs "1960h1", and a weekly one
"29 Jan 1958" vs "1958w5". Hover is worse — `{%F}` for every kind but `tc` — but
that half is already on the auditor's list; the value formatter, its JS twin and
`_datetime_formatter_for` share the same collapse, so KPI cards, facet titles,
marker labels and (once fixed) dropdown labels all mis-state the period. The Stata
truth is already in the repo and unused: `test/fixtures/date_truth.json` records a
`display` string for every value, and only the `iso` field is ever asserted.

**Where.** `dash_render.py:203` `_format_date_value_standalone` (kind table at
`:215-220`), `dash_render.py:8860` `DashRenderer._format_date_value`, the JS twin
inside `_FILTER_JS` at `dash_render.py:7285-7307` (which must stay byte-compatible
with the Python side), `_datetime_formatter_for` at `:247`; fixture
`test/fixtures/date_truth.json` (`date_formats.*.values[].display`); tests
`test/test_dates.py:490-527` and `:716-731`.

**Evidence.** Appendix C, 08-05; the collapse and the fixture table quoted above.

### Item 13 — execute the shipped `_FILTER_JS` under node  `[deli · standalone · M]`

Execute the shipped `_FILTER_JS` against a date column under node, as the task's
"verify rather than assume ... assert it in the test" clause asks. Today every
date-filter assertion is structural (snapshot dtype, slider bounds, the substring
'datekind' appearing in the JS source); nothing runs the callback, which is why the
dropdown's value/label mismatch survived the test suite. The harness already exists
and can be reused verbatim.

**Where.** `test/test_dates.py:626-714` `TestDateFilterActuallyFilters` (add the
node-executed cases here); pattern source `test/test_kpi_values.py:263-300`; code
under test `dash_render.py:7070-7090` (`_FILTER_JS` row match) and `:7285-7307`
(KPI date branch).

**Evidence.** Appendix C, 08-05.

### Item 14 — tests for the NUMERIC half  `[deli · standalone · S]`

Add tests for the NUMERIC half of "format ... everywhere they are displayed". The
section's stub list asks that `%9.0fc` render with thousands separators in hover,
KPI and tick labels; only the pure helpers are tested. Missing: (a) a hover spec
test that a `%9.0fc` column produces `@{v}{0,0}`; (b) a KPI test with NO `fmt()`
proving the variable's own format is the fallback (the only numeric KPI test passes
`fmt="%9.2f"` explicitly); (c) slider/range endpoint and dropdown label tests
(items 3 and 4 above); (d) a non-date/non-formatted negative twin for `_facet_label`
— `test_mlabel_on_a_plain_variable_is_unchanged`, `test_a_numeric_filter_is_unchanged`
and `test_a_numeric_kpi_is_unchanged` exist, the facet one does not.

**Where.** `test/test_dates.py:406-486`, `:490-527` (`TestKpiValuesFormatAsDates`),
`:528-590` (`TestDateFilterWidgets`), `:716-760` (`TestFacetAndMarkerLabels`);
`test/test_axis_options.py:175-220`.

**Evidence.** Appendix C, 08-05. Note: the "items 3 and 4 above" in clause (c)
are the auditor's own numbering within the 08-05 Appendix C list; in this phase
they are **items 10 and 11**.

---

## Test plan

Project rule 8 governs the order: **for every defect below, write the failing
test first, watch it fail against HEAD, then fix.** Project rule 4 governs the
breadth: every function added or changed gets a unit test. Every test is listed
with the mutation that must kill it — a test that survives its mutation is
vacuous and does not count, which is the exact failure mode this phase is
cleaning up (`test_a_date_dropdown_shows_dates_not_epoch_numbers` is green
against a dropdown that filters every row away).

A skip is not a pass. The node-executed cases skip when `shutil.which("node")`
is `None`, exactly as `test/test_kpi_values.py:271-273` does; the suite's
skip-accounting must show them.

### Epic A — the dropdown

**Write first (the failing test).**
`test/test_dates.py::TestDateFilterActuallyFilters::test_selecting_a_date_option_leaves_that_date_s_rows`
— build the `%td` dropdown dashboard (`_widgets(tmp_path, "dropdown")` already
does the build), take `w.options[1][0]` as the selected value, slice the
dropdown branch out of `dash_render._FILTER_JS` (`dash_render.py:7070-7078`),
run it under node against the `orig_source` snapshot with that `val`, and assert
the resulting active mask has exactly the rows of that date `true`. At HEAD this
fails with zero active rows — the whole defect, in one assertion.

| test | file / name | asserts | mutation that must kill it |
|---|---|---|---|
| A-U1 | `test/test_dates.py::TestDateFilterWidgets::test_a_date_dropdown_shows_dates_not_epoch_numbers` (strengthened — items 5, 7) | for every non-sentinel option, `float(o[0])` equals an epoch-ms value present in the snapshot column; `o[1]` matches the `%td` picture (`02 Jan 2001`) | revert the value half to `str(Timestamp)` → the `float(o[0])` parse or comparison fails |
| A-U2 | same class, `test_a_date_dropdown_label_uses_the_stata_picture` (`%tm` variant) | label equals `_format_date_value_standalone(ms, "tm")` and is not the ISO string | make `_resolve_label` return `rv` for dates → fails |
| A-U3 | `test/test_dates.py::TestDateFilterActuallyFilters::test_selecting_a_date_option_leaves_that_date_s_rows` (node) | active-row count > 0 and equals the count for that date | revert item 1 → zero active rows |
| A-U4 | same class, `test_selecting_all_leaves_every_row` (node) | the sentinel leaves every row active | break the sentinel comparison → fails |
| A-U5 | `test/test_dates.py::TestDateFilterWidgets::test_a_high_cardinality_dropdown_warns_and_suggests_range` | `pytest.warns(UserWarning, match=r"type\(range\)")` on a payload above the threshold; the message names the variable and the count | remove the `warnings.warn` → `pytest.warns` fails |
| A-U6 | same class, `test_a_small_dropdown_does_not_warn` (negative twin) | `warnings.catch_warnings(record=True)` is empty below the threshold | warn unconditionally → fails |
| A-U7 | `test/test_dates.py::TestDateFilterWidgets::test_a_string_dropdown_is_unchanged` (negative twin) | a non-date, non-formatted column's options are identical to HEAD's | route all columns through the date branch → fails |

**Integration.** `test/test_filter_widget_parity.py` gains the `%tm` dropdown
case from item 8, so the standalone and server dropdowns are compared on the
same spec. No new `.cscript` belongs to this epic — the Stata-side end-to-end
coverage for section 08 (`test/test_formats.cscript`, named in 08-01's `<files>`
and absent from the repo) is the sibling Formats phase's deliverable.

### Epic B — numbers and periods

**Write first (the failing test).**
`test/test_dates.py::TestNumericDisplayFormats::test_the_python_and_js_general_kpi_agree`
— parametrise over `[1234567, 3000000, 123456, 0.000012345]`, compute
`DashRenderer._format_kpi_value(v, "%9.0g")` and run the `k.general` branch of
`_FILTER_JS` (`dash_render.py:7310-7313`) under node with the same value, assert
the two strings are equal. At HEAD `1234567` gives `1.23457e+06` against
`1234570` and `3000000` gives `3e+06` against `3000000`, so it fails on two of
four cases immediately.

| test | file / name | asserts | mutation that must kill it |
|---|---|---|---|
| B-U1 | `test/test_dates.py::TestDateFilterWidgets::test_a_formatted_numeric_range_shows_thousands_separators` (item 14c) | the `RangeSlider`'s `format` is the pattern `_stata_numeric_pattern('%12.0fc')` returns (`'0,0'`) | drop the `format=` argument → fails |
| B-U2 | same class, `test_a_formatted_numeric_slider_shows_thousands_separators` | same for `Slider` | same |
| B-U3 | same class, `test_an_unformatted_numeric_widget_has_no_format` (negative twin) | a variable with no Stata format produces a widget whose `format` is unchanged from HEAD | pass a pattern unconditionally → fails |
| B-U4 | same class, `test_a_formatted_numeric_dropdown_labels_with_commas` (item 11) | options list `3,000,000`, and `o[0]` is still the raw value | revert `_resolve_label` → fails |
| B-U5 | `test/test_dates.py::TestNumericDisplayFormats::test_the_python_and_js_general_kpi_agree` (node) | Python and JS strings equal for all four magnitudes | revert either side → fails |
| B-U6 | `test/test_dates.py::TestEpochConversion::test_period_kinds_match_statas_display_string` | for `%tm`, `%tq`, `%th`, `%tw`, every fixture value's `display` equals `_format_date_value_standalone(ms, kind)` (stripped — the fixture pads, e.g. `' 1958w5'`) | restore the `%b %Y` collapse → fails on `1960q1`, `1950h1`, `1958w5`, `1950m1` |
| B-U7 | same class, `test_the_js_twin_renders_the_same_period_string` (node) | the JS branch at `dash_render.py:7285-7307` produces the same strings for the same epoch ms | change one side only → fails (this is the byte-compatibility guard TR-12.8 requires) |
| B-U8 | `test/test_dates.py::TestKpiValuesFormatAsDates::test_a_numeric_kpi_with_no_fmt_uses_the_variables_own_format` (item 14b) | `%12.0fc` KPI with `fmt=""` renders `3,000,000` | remove the `numeric_formats` fallback at `dash_render.py:8443-8446` → fails |
| B-U9 | `test/test_dates.py::TestHoverShowsDates::test_a_formatted_numeric_column_hovers_with_commas` (item 14a) | the hover spec for a `%9.0fc` column is `@{v}{0,0}` | drop the numeric pattern from the hover row → fails |
| B-U10 | `test/test_dates.py::TestFacetAndMarkerLabels::test_a_facet_on_a_plain_variable_is_unchanged` (item 14d, the missing negative twin) | `_facet_label` on an unformatted variable returns the raw value's plain string | format unconditionally → fails |
| B-U11 | `test/test_axis_options.py` (lines 175-220 neighbourhood) | a `%9.0fc` variable's tick labels carry the Stata pattern where the section's stub list requires it | drop the pattern → fails |

**Integration.** `test/test_mode_parity.py` gains the `%12.0fc` KPI case from
item 8; `test/test_kpi_values.py`'s node harness is the pattern B-U5 and B-U7
reuse.

### Epic C — computed axes and the server

**Write first (the failing test).**
`test/test_dates.py::TestDatesOnComputedLayers::test_a_date_x_on_an_lfit_builds`
— a spec with `formats={"date": "%td"}` and plots
`[{"type": "scatter", ...}, {"type": "lfit", "yvar": "close", "xvar": "date"}]`,
rendered to `tmp_path`. At HEAD this raises `RuntimeError: dash_render: failed
to build figure 'g1': ...` from `dash_render.py:11510` — the rc 7102 abort — and
writes no file.

| test | file / name | asserts | mutation that must kill it |
|---|---|---|---|
| C-U1 | `test/test_dates.py::TestDatesOnComputedLayers::test_a_date_x_on_an_lfit_builds` | `render()` returns, the output file exists and is non-empty | revert one float cast (e.g. `dash_render.py:3845` `map_lfit`) → `RuntimeError` |
| C-U2 | same class, parametrised over the 19 mappers by plot type (`area`, `spike`, `lfit`, `qfit`, `lfitci`, `qfitci`, `lowess`, `lpoly`, `lpolyci`, `fpfit`, `fpfitci`, `rcap`, `dropline`, `rcapsym`, `rscatter`, `mspline`, `mband`, `histogram`, `kdensity`) | each builds with a `%td` x (or y, where the mapper is y-driven) | revert any single mapper → that parameter fails, and the parametrisation names it |
| C-U3 | same class, `test_the_fitted_line_lands_in_the_datas_own_date_range` | the computed x values are datetime64 between the min and max of the source date column — not 1970 | map back with `pd.to_datetime(x, unit="s")` instead of `unit="ms"`, or skip the map-back → fails |
| C-U4 | same class, `test_a_plain_numeric_lfit_is_unchanged` (negative twin) | with no `formats` key, the fitted y values equal HEAD's | route unformatted columns through the datetime path → fails |
| C-I1 | `test/test_mode_parity.py` (item 8) | a `%td` x-variable gives the same axis type and the same serialized column dtype in both renderers; a `%tm` KPI gives the same string | revert item 4 part (a) → `'Jan 2001'` vs `'492.0'` fails |
| C-I2 | `test/test_filter_widget_parity.py` (item 8) | both renderers produce `DateRangeSlider` for a `%td` `type(range)` filter, and equal dropdown option values for `%tm` | revert item 4 part (d) → `RangeSlider` on the server side fails |
| C-I3 | `test/test_mode_parity.py` | with `formats={}` the corpus behaves exactly as it does at HEAD | make the formats argument non-optional → the existing corpus fails |
| C-U5 | a server case exercising the emitted `_format_kpi` (in `test/test_dates.py` or the parity suite, following the build-and-exec pattern at `test/test_filter_widget_parity.py:64-75`) | the emitted app's `_format_kpi` renders a `%td` `max()` as a date and warns on `sum()` of a date | revert item 4 part (f) → renders `15340.0`, no warning |

**Non-vacuity discipline for the whole phase.** Each mutation above is applied
to a scratch copy of `dash_render.py`, the named test is run, and the test must
fail. Any test that still passes is rewritten before the fix is committed. This
is the check that `test_a_date_dropdown_shows_dates_not_epoch_numbers` never
had.

---

## Definition of done

A reviewer can tick each line without opening `REMAINING.md`.

**Behaviour**

- [ ] Selecting a non-sentinel option in a date dropdown leaves a non-zero,
      correct row count, proved by the shipped `_FILTER_JS` executed under node.
- [ ] Every date dropdown option is a `(epoch-ms string, Stata-formatted label)`
      pair; neither half is `str(Timestamp)`.
- [ ] A dropdown above the cardinality threshold emits a `UserWarning` naming
      the variable, the count and `type(range)`; below it, none.
- [ ] A `%12.0fc` slider and range show `3,000,000` at their endpoints; a
      `%12.0fc` dropdown lists `3,000,000`.
- [ ] A `%9.0g` KPI renders the same string on first paint and after a filter
      move, for `1234567`, `3000000`, `123456` and `0.000012345`.
- [ ] `%tm`, `%tq`, `%th`, `%tw` render Stata's period pictures (`1950m1`,
      `1960q1`, `1950h1`, `1958w5`), in Python and in the JS twin, for every
      value in `test/fixtures/date_truth.json`.
- [ ] `dash (scatter close date) (lfit close date)`-shaped specs build: rc 0, a
      non-empty file, and a fitted line inside the data's own date range — for
      all 19 mappers listed in TR-12.9.
- [ ] The generated `bokeh serve` app reads `build_options["formats"]` and
      applies it at all seven touchpoints (a)–(g) of TR-12.10.
- [ ] A dashboard with no `formats` entry renders exactly as it does at HEAD.

**Tests (rules 4 and 8)**

- [ ] Every defect above has a test that was written first, observed failing at
      HEAD, and passes after the fix.
- [ ] Every mutation in the *Test plan* mutation column kills its named test.
- [ ] `test_a_date_dropdown_shows_dates_not_epoch_numbers` asserts `o[0]`, not
      only `o[1]`, and fails when the value half is reverted.
- [ ] `test_every_per_source_snapshot_agrees_too`'s sibling assertions are not
      relied upon by anything this phase adds (its own vacuity — the
      non-existent `all_graph_sources_orig_json` key — is Phase 11's item).
- [ ] `test/test_mode_parity.py` and `test/test_filter_widget_parity.py` no
      longer hardcode `"formats": {}` and carry the `%td` / `%tm` / `%12.0fc`
      cases.
- [ ] The node-executed cases skip explicitly when `node` is absent, and the
      skip is visible in the run summary rather than counted as a pass.

**Hygiene**

- [ ] `REMAINING.md` is unchanged.
- [ ] Full `pytest` run is green; no test was deleted to make it so.
- [ ] Full certification suite run from `test/` is green with honest skips.
- [ ] Committed on `feature/batch4-interactive-layer` (or a branch off it), never
      directly on `main`, with the merge command reported rather than run
      (project rule 6), and no Claude/Anthropic reference in the commit message
      (project rule 7).

---

## Risks and sequencing notes

**1. Item 4 edits source that Phases 05–08 intend to delete.**
The whole of `ServerAppBuilder` after `dash_render.py:12265` is emitted app
source, and task 15-03's collapse replaces the hand-written emitted branches
with `_DASH_MAPPER` delegation. Item 4 touches the emitted loader, the emitted
filter loop, the emitted `_format_kpi` and the emitted facet-label build — four
places 15-03 has an opinion about. Sequence item 4 **after** Phases 05–08 land
where possible; where it cannot wait, write the date logic into helpers that are
forwarded through the helper-copy tuple (`dash_render.py:12394-12396`) rather
than inlined into emitted strings, so the collapse inherits it instead of having
to redo it.

**2. Item 9 is the largest and the riskiest.**
Nineteen mappers, each with its own x/y shape (single x, x plus two y bounds,
derived grids). The compute-in-epoch-ms / map-back-to-datetime64 round trip must
not change a single number for unformatted data — `map_lowess`, `map_lpoly` and
the `fp*` family are numerically sensitive. Do it mapper by mapper behind the
parametrised C-U2 test, and keep C-U4 (the unformatted negative twin) green at
every step. `_extract_finite`'s own comment (`dash_render.py:986-992`) records
why the explicit `datetime64[ms]` cast matters: pandas 3 preserves the inferred
resolution, so a raw `astype("int64")` divided by a constant silently yields
seconds for one column and milliseconds for another.

**3. Item 12 changes strings other phases assert on.**
`_format_date_value_standalone` feeds KPI cards, facet titles, marker labels and
(after item 2) dropdown labels. Existing tests pin the *current* collapse —
`test/test_dates.py:490-527` (`TestKpiValuesFormatAsDates`) and `:716-731`
(the facet case) assert `"2001" in text`, which survives the change, but any
test that pins `Jan 2001` exactly will not. Phase 13 owns the KPI/facet/marker
touchpoints; land item 12 before Phase 13 starts, or agree the picture with it,
so the two do not assert different strings for the same value.

**4. The byte-compatibility constraint between Python and JS is easy to lose.**
Item 12 and item 6 both require a Python function and a JavaScript branch to
produce identical output. The only reliable guard is executing the shipped JS
(B-U5, B-U7), not eyeballing the two implementations; a substring assertion over
`_FILTER_JS` source will pass while the two diverge, which is precisely how the
dropdown defect survived.

**5. The cardinality threshold must not collide with Phase 04.**
Phase 04 owns the hard cap from §6 (`_MAX_FILTER_OPTIONS` / `_MAX_DROPDOWN`,
neither defined at HEAD). If Phase 04 lands first, item 3 reads its constant; if
this phase lands first, item 3 defines one name and Phase 04 extends it. Two
constants with different names for the same limit is the failure to avoid.

**6. `node` availability.**
Items 13, B-U5, B-U7 and A-U3/A-U4 all depend on `node` being installed.
`test/test_kpi_values.py:271-273` skips when it is not; the same skip is correct
here, but a skipped date-filter test is not evidence that the date filter works
— it is the absence of evidence, and the phase's Definition of Done requires the
skip to be visible in the run summary.

**7. Dependency on Phase 09.**
Every item here assumes `self.date_vars` and `self.numeric_formats` are
populated (they are assigned at `dash_render.py:8141-8142`) and that `%t*`
columns arrive as `datetime64`. If Phase 09 has not landed, items 1, 2, 10, 11
and 12 have nothing to read and item 9 has no crash to fix.
