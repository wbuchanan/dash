# Section 08: Display formats, dates and labels

## Overview
Stata display formats never leave Stata, so `dash` has **no date handling at all**.
`DatetimeTickFormatter`, `DatetimeAxis` and `x_axis_type="datetime"` appear nowhere in
10,455 lines, and `map_tsline:3894` is a pass-through to `map_line`. A `%td` variable arrives
as a raw Stata SIF integer and gets a linear axis reading `14.0k`. Every `%9.0fc` and `%9.2f`
the user set is lost on axes, tooltips, dropdown options, slider endpoints, facet labels and
KPI values.

The cause is upstream and was verified rather than assumed: **`jsonio` has no option that
emits display formats.** `jsonio.ado:238` gates its metadata branch on
`inlist("`metaprint'`filenm'", ...)` — concatenating `metaprint` and `filenm` — so with a
non-empty `filenm()` the branch never fires and `metaprint()` is a no-op. Only `what(all)`
has effect, and `StataAllToJSON`'s field set (confirmed in source and by `javap` on the
shipped jar) has no format member. `jsonio` holds `Variables.getDisplayFmt()` internally but
never exposes it.

So `dash` carries formats itself, in its own master JSON. `jsonio` is not modified.

## User story
> As a Stata user, `dash line close date` on `sysuse sp500` draws an x-axis of calendar
> dates, the hover shows a date, and my `%9.0fc` price reads `12,345` not `12345.0`.

## Business requirements
- BR-08.1 Every Stata date format renders as a date wherever it is displayed.
- BR-08.2 Every Stata numeric display format is honoured wherever the value is displayed.
- BR-08.3 A master JSON without the new key must still load (an older `dash.ado` against a
  newer `dash_render.py`).
- BR-08.4 A variable with no date format takes exactly the code path it takes today.

## Technical requirements
- TR-08.1 `dash.ado` collects `local f : format <var>` for every serialized variable and
  emits a `"formats"` object in all three master-JSON paths (`:974`, `:1433`, `:1603`).
- TR-08.2 `_load_data` (`:5061-5083`) converts `%t*` columns to datetime64 and records which
  columns are dates and of which kind.
- TR-08.3 `_make_figure` sets `x_axis_type`/`y_axis_type` to `"datetime"` for date variables,
  **before** the single `bokeh_figure()` call — commit `c3941de` fixed a bug caused by
  re-creating a figure to change its axis type; do not reintroduce it.
- TR-08.4 Hover, filters, facet labels, marker labels and KPI values format dates as dates
  and numbers by their Stata format.

## The eight Stata date epochs — get these exactly right

| format | unit | epoch |
|---|---|---|
| `%td` | days | 01jan1960 |
| `%tc` | milliseconds | 01jan1960 00:00:00.000 |
| `%tC` | milliseconds, leap-second corrected | 01jan1960 |
| `%tw` | weeks | 1960w1 |
| `%tm` | months | 1960m1 |
| `%tq` | quarters | 1960q1 |
| `%th` | half-years | 1960h1 |
| `%ty` | **the year itself — not an offset** |

`%tw`, `%tm`, `%tq` and `%th` count calendar periods, not fixed-length intervals, so they
cannot be converted by multiplication. Build the timestamp from the period index. `%ty` must
not be offset from 1960 at all. `%tC` differs from `%tc` by accumulated leap seconds;
treating it as `%tc` is acceptable **if documented**, not if silent.

## Risk: [red] — `_load_data` feeds every code path and `_make_figure` builds every figure. Any behaviour change for non-date data is a bug in this section.

## Dependencies
- Depends on: S07
- Blocks: S09
- Parallel batch: 3

## TDD test stubs
- Test: `%td` 14977 → 2001-01-02; `%tc` → the right timestamp; `%tm` 0 → 1960-01 and 745 →
  2022-02; `%tq`, `%tw`, `%th` → the correct period start; `%ty` 1998 → 1998, **not** offset.
- Test: a `%9.0g` variable is untouched and remains numeric.
- Test: a variable absent from the `formats` map is untouched.
- Test: a master JSON with no `formats` key loads (backward compatibility).
- Test: a date x-variable produces a datetime axis; a numeric one does not.
- Test: a scatter of two non-date variables is byte-identical to before, ids aside.
- Test: `xscale(log)` on a date variable degrades gracefully with a warning.
- Test: hover on a date column shows a formatted date.
- Test: `%9.0fc` renders with thousands separators in hover, KPI and tick labels.
- Test: `filter(date, type(range))` and `type(slider)` produce widgets with date bounds that
  actually filter.
- Test: `filter(date, type(dropdown))` shows dates, not epoch milliseconds.
- Test: `by(datevar)` facet titles read as dates; `mlabel(datevar)` prints dates.
- Test: `dash kpi min(datevar)` / `max(datevar)` display dates, before and after filtering.
- Test: each of the above is unchanged for a non-date variable.

## Tasks

<task type="auto" id="08-01">
  <name>Write the epoch and format-passthrough tests from Stata-derived fixtures</name>
  <files>test/test_dates.py, test/test_formats.cscript, scripts/extract_date_truth.do</files>
  <action>
    Derive every expected value from Stata, not from memory: run `display %td 14977` and the
    equivalents for all eight formats and record the outputs as fixtures, with the commands
    beside them.

    Write the Stata-side test: after a `dash build` against `sysuse sp500`, the master JSON on
    disk contains a `formats` object mapping `date` to `%td`. Confirm sp500's actual format
    with `describe` rather than assuming — it is `%td`, verified, but the test should check.

    Write the backward-compatibility tests: a master JSON **with** a `formats` key loads, and
    one **without** it loads too.

    Write the two negative cases: a `%9.0g` variable and a variable missing from the map both
    pass through untouched.

    Run. Every date test must fail because the converter does not exist, not on a wrong value.
  </action>
  <verify>All date tests fail with "no such function/attribute"; the two negative cases pass.</verify>
  <done>A Stata-derived fixture set exists for all eight formats plus the negative cases.</done>
</task>

<task type="auto" id="08-02">
  <name>Collect display formats in Stata and carry them in the master JSON</name>
  <files>dash.ado</files>
  <action>
    Add a private helper in the style of `_dash_json_str` and `_dash_validate_path` that takes
    a varlist and returns a JSON object mapping each variable to its display format. Use
    `local f : format <var>`, and escape through the existing `_dash_json_str` — do not
    hand-roll escaping.

    Emit `{}` for an empty varlist. Skip a variable that does not exist rather than aborting;
    the varlists passed to `jsonio` are assembled from several sources.

    Wire it into all three master-JSON sites — immediate render (`:974`), `dash build`
    (`:1433`) and `dash serve` (`:1603`) — using the same local each path actually passed to
    `jsonio`, so the map covers exactly the columns that will exist in the DataFrame. Emit it
    as a nested object, not a string, so Python does not double-parse.

    Add a header comment explaining why this exists: `jsonio`'s `metaprint()` cannot emit
    display formats. Cite the gating bug so the next reader does not go looking for a
    `jsonio` option that does not exist.
  </action>
  <verify>All three paths emit a populated `formats` map for sp500 and for auto; the Stata-side tests pass.</verify>
  <done>Display formats reach Python, without modifying `jsonio`.</done>
</task>

<task type="auto" id="08-03">
  <name>Classify formats and convert epochs</name>
  <files>dash_render.py</files>
  <action>
    Add a module-level helper classifying a Stata format string into one of the eight date
    kinds or None. Match the `%t`/`%-t` prefix and the following letter **case-sensitively**
    — `%tc` and `%tC` are different formats.

    Add a converter from a numeric Series plus a date kind to datetime64. Use pandas' period
    machinery for month/quarter/half/week/year rather than hand-rolled calendar arithmetic,
    and a timedelta offset from the 1960-01-01 epoch for days and milliseconds.

    Preserve missing values as NaT. Do not raise on out-of-range values — Stata's date range
    is wider than pandas' nanosecond datetime64 range. Clamp or coerce and emit a
    `UserWarning` naming the variable, in the style of the slider dtype guard at `:7203`.

    Add a second helper for **numeric** formats — `%9.0fc`, `%9.2f`, `%12.0gc` — returning a
    display pattern. This is what BR-08.2 needs and it is easy to forget behind the date work.

    Keep all three pure and side-effect free so the tests can call them directly.
  </action>
  <verify>All 08-01 conversion tests pass.</verify>
  <done>Format classification and conversion are implemented and fully covered.</done>
</task>

<task type="auto" id="08-04">
  <name>Convert in the loader and give date figures a datetime axis</name>
  <files>dash_render.py</files>
  <action>
    In `_load_data` (`:5061-5083`), after the existing `pd.to_numeric(..., errors="coerce")`
    coercion, consult the `formats` map and convert date columns. Record the set of date
    columns and their kinds, and the numeric display patterns, on the renderer instance —
    later tasks and later sections all need them.

    Absent-key path: no `formats` member means no date columns and every existing path
    unchanged. This is what keeps an older `dash.ado` working.

    Do not convert string columns even if they somehow carry a date format.

    In `_make_figure` (`:5629-5660`), extend the axis-type decision that currently handles
    only the log case at `:5654`: a date x-variable gets `x_axis_type="datetime"`, likewise
    `y_axis_type`. **Decide the axis type before the single `bokeh_figure()` call** and never
    re-create the figure — commit `c3941de` fixed exactly that bug.

    Attach a `DatetimeTickFormatter` matched to the date kind: years for `%ty`, dates for
    `%td`, date and time for `%tc`. An explicit `xlabel()` tick list must still win.

    Apply the same treatment to the secondary-axis path (`:5715-5799`).

    `xscale(log)` on a date variable is meaningless: choose datetime, warn naming the
    variable, and document the precedence.
  </action>
  <verify>sp500 renders calendar dates on the x-axis; an auto scatter is byte-identical ids aside.</verify>
  <done>Date variables produce datetime axes on both axes, with no change to non-date figures.</done>
</task>

<task type="auto" id="08-05">
  <name>Format dates and numbers everywhere they are displayed</name>
  <files>dash_render.py</files>
  <action>
    Six touchpoints. Each must leave non-date, unformatted columns exactly as they are.

    **Hover** (`:6078-6089`, `:6127-6131`). Use a datetime field spec with a `formatters`
    entry for date columns; use the Stata numeric pattern for formatted numerics. While here,
    fix two adjacent defects: tooltips label rows with raw **variable names** although
    `self.variable_labels` is loaded and used for axes (`_axis_label:5540`) — use the label;
    and the fallback tooltips hardcode three different precisions (`{0.2f}`, `{0.3f}`,
    `{0.4f}`) — derive one from the data or the format.

    **Filter widgets** (`:4705-4849`, `:7186-7222`). Range and slider guard on
    `is_numeric_dtype` and skip the widget entirely for non-numeric columns (commit
    `b25584c`); a datetime64 column fails that test, so a date range filter would silently
    produce **no widget**. Extend the guard and use `DateRangeSlider`/`DateSlider`. Bokeh
    transports datetimes as epoch milliseconds so the existing `_FILTER_JS` comparison should
    work on the underlying numbers — **verify this rather than assuming**, because a mismatch
    silently filters nothing; assert it in the test. For the dropdown, format dates for
    display while keeping the raw value as the option value — the same split already used for
    value-labelled variables — and preserve the `__all__` sentinel's collision-growing
    behaviour. A date dropdown with thousands of distinct values is useless: warn above a
    reasonable cardinality and suggest `type(range)`.

    **Facet labels** (`_facet_label:5501`), **marker labels** (`_apply_mlabel_opts:1829-1912`)
    and **KPI values** (`_format_kpi_value:7068`, `_compute_kpi_stat:5115`). Format dates as
    dates. For a date column, `min`, `max`, `median`, `p25`, `p50` and `p75` are meaningful;
    `mean` is defensible and formats as a date; `sum` is not — warn. `count` and `dcount` are
    unaffected.

    Update the **JavaScript recompute** path too, so a date or formatted KPI still formats
    correctly after a filter change, not only on first render.
  </action>
  <verify>Dates read as dates and formatted numbers keep their formatting in all six places, before and after filtering; non-date columns are unchanged.</verify>
  <done>Formats are honoured everywhere a value is shown.</done>
</task>

<task type="auto" id="08-06">
  <name>End-to-end sp500 verification and commit</name>
  <files>examples/, .ultraplan/CHANGELOG.md</files>
  <action>
    Build a real sp500 dashboard end to end from Stata: a `line close date` graph, a
    `kpi max(close)` card, and `filter(date, type(range))` under `layout(bs)`.

    **Open it in a browser and look at it.** Confirm the x-axis reads calendar dates, the
    hover shows a date, and the range slider shows dates at both ends and actually filters.
    Do not report this task complete on the basis of the HTML source — the whole point of the
    section is what a person sees.

    Add the dashboard to `examples/` as the date exemplar, since there is currently none.

    Run the full pytest suite, the certification suite and the S05 conformance corpus against
    the S01 baseline. Record in the CHANGELOG that formatted numerics now display differently
    — that is a deliberate visible change.

    Commit as two single-issue commits: the Stata-side format carriage, then the Python-side
    consumption.
  </action>
  <verify>A browser rendering shows dates on the axis, in the tooltip and in the filter; suites green against baseline.</verify>
  <done>Date and format support is complete and verified visually, not only structurally.</done>
</task>
