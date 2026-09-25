# Phase 13 — Formats II: KPIs, facets, marker labels and the server renderer

**Purpose.** Task 08-05 asked that a Stata display format reach every place a value is shown —
hover, filter widgets, facet labels, KPI cards, marker labels and the JavaScript recompute.
Five of those six touchpoints work in the standalone renderer, and Phases 11 and 12 take the
hover path and the filter widgets. This phase closes 08-05 on what is left: the two defects
that damage the **shared** date column everything else reads, and the four proof surfaces the
task never got. The first functional item is a hard abort — `_stata_dates_to_datetime` still
raises a bare pandas `AssertionError` for the five period kinds (`%tm %tq %th %tw %ty`) where
section 08-03 required a coerce-and-warn. The second is `colorvar(datevar)`, which writes
`[str(v) for v in raw_col]` back into the shared `ColumnDataSource`, so every later consumer of
that column — the KPI cards, the facet titles, the marker labels, the range filter guard —
sees ISO strings instead of dates. Then the proof: a per-source snapshot test whose loop body
never executes, an out-of-range case that covers `%td` and no other kind, the complete absence
of any server-mode test for dates or display formats, and `test/test_formats.cscript`, which
08-01's `<files>` names and which does not exist — so the certification suite has never once
built a dashboard on a `%t` variable.

---

## At a glance

| | |
|---|---|
| **Work items** | 6 |
| **Functional / deliverable** | 2 functional (items 3, 5) · 4 deliverable (items 1, 2, 4, 6) |
| **Effort mix** | 3 small (1, 3, 4) · 3 medium (2, 5, 6) · 0 large |
| **Renderers touched** | `DashRenderer` (standalone) ×4 (items 1, 3, 4, 5) · `ServerAppBuilder` (emitted app) ×1 (item 2) · `dash.ado` / Stata certification ×1 (item 6) |
| **Ultraplan tasks discharged** | **08-05** — the closing slice (Phases 11 and 12 take the hover and filter-widget slices) · the **08-03** refutation clause (out-of-range values must coerce and warn, not raise) · **08-01**'s named-but-absent `test/test_formats.cscript` |
| **Sections** | S08 "Formats, dates, labels" — 6 tasks, currently *2 done, 4 partial*; REMAINING.md's status row names `test_formats.cscript` as one of the two things outstanding |
| **Depends on** | **09–12** and **05–08**. Item 2 tests behaviour that Phase 12 item 4 implements (*"Carry the whole of 08-05 into the generated server app"*) on top of Phase 10 item 1 (`ServerAppBuilder` date support); item 6's cscript cannot return rc 0 until the float-cast mapper fix lands (Phase 09 item 3 / Phase 12 item 9). |
| **Unblocks** | Phase 30 (documentation) and Phase 31 (release gates): `test_formats.cscript` and the extended date exemplar are part of the certification-suite and conformance-corpus gates S16-06/S16-07 must pass. |
| **Backlog provenance** | REMAINING.md Appendix A (08-05 and 08-04's remaining item 2), Appendix B (2 of 10 items under 08-05), Appendix C (4 of 15 items under 08-05), the 08-03 row of *"17 DONE claims the adversarial pass overturned"*, and the S08 row of *"Status by section"* |

---

## Why this phase exists

### What 08-05 delivered, and what it did not

REMAINING.md, Appendix A, *"08-05 — Format dates and numbers everywhere they are displayed ·
PARTIAL"*, in full:

> Five of the six touchpoints work in standalone, verified individually:
>
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
>
> **Remaining:**
> 1. **Every figure carries two `HoverTool`s.** One is correct; the other is
>    `[('d','@{d}'), ('v','@{v}')]` — raw variable names, no formatter, no date
>    handling. […]
> 2. **No dropdown cardinality warning.** The task requires a warning above a
>    reasonable cardinality suggesting `type(range)`. Measured on 5,000 distinct
>    dates: **5,001 options, zero warnings**. […]
> 3. **Server mode has none of it**: in the emitted app `variable_labels` 0,
>    `DateRangeSlider` 0, `_facet_label` 0, `_format_kpi_value` 0.
> 4. Minor: `count` on a date column renders `30.0` rather than `30`.

Remaining items 1 and 2 are **not** this phase — item 1 is Phase 11 (hover), item 2 is Phase 12
(filter widgets and cardinality). Remaining item 3 is the measurement this phase's title comes
from, and it is what item 2 below makes testable: **the KPI formatter, the facet label, the
date widgets and the variable labels are all absent from `dash serve`, and nothing in `test/`
would notice.**

Two more findings, both from the adversarial pass, sit underneath those five working
touchpoints and can take all of them down at once. They are this phase's functional work.

### Finding 1 — the period converter aborts the render instead of warning

REMAINING.md, Appendix C, 08-05 (reproduced below as work item 3):

> `_stata_dates_to_datetime`
> (/Users/billy/Desktop/Programs/StataPrograms/d/dash/dash_render.py:290)
> crashes `dash` outright on an out-of-range value for the five period-based
> kinds (%tm, %tq, %th, %tw, %ty). Its `except (OverflowError, ValueError,
> pd.errors.OutOfBoundsDatetime)` at dash_render.py:357 does not catch what
> pandas 3.0.1 actually raises. `_from_parts` (dash_render.py:318-328) assigns
> into a `pd.Series(pd.NaT, dtype='datetime64[ns]')` via `out.loc[ok] =
> pd.to_datetime(...)`; when the resulting year exceeds 2262 pandas raises
> `AssertionError` from `blocks.coerce_to_target_dtype(...,
> raise_on_upcast=True)`, which propagates through `DashRenderer._load_data`
> (dash_render.py:8210) and out of `render()`. Section 08-03's action text
> explicitly requires the opposite: 'Do not raise on out-of-range values ...
> Clamp or coerce and emit a `UserWarning` naming the variable.' The %tc and
> %td branches do honour that (they warn and yield NaT); the period branches do
> not.

The auditor measured the same thing from the 08-04 side. REMAINING.md, Appendix A,
*"08-04 — Convert in the loader, give date figures a datetime axis · PARTIAL"*, remaining
item 2:

> Out-of-range period values still raise. `%tm`/`%tq`/`%tw` with a value past
> pandas' Timestamp range abort the render with a bare
> `AssertionError: Something has gone wrong, please report a bug at pandas`,
> rather than coercing to `NaT` with the existing warning.

And the refutation table, *"17 DONE claims the adversarial pass overturned"*:

| task | what the refutation found |
|---|---|
| 08-03 | out-of-range period values raise instead of coercing to `NaT` |

The code, read at HEAD. `_from_parts` (`dash_render.py:318-328`) — note the `datetime64[ns]`
block that the assignment must upcast:

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

The five branches that route through it, and the `except` tuple that does not catch what
pandas raises (`dash_render.py:330-358`):

```python
    try:
        if kind in ("tc", "tC"):
            out = _STATA_EPOCH + pd.to_timedelta(v, unit="ms", errors="coerce")
        elif kind == "td":
            out = _STATA_EPOCH + pd.to_timedelta(v, unit="D", errors="coerce")
        elif kind == "ty":
            out = _from_parts(v, pd.Series(np.ones(len(v))))
        elif kind == "tm":
            idx = np.floor(v)
            out = _from_parts(1960 + np.floor(idx / 12.0), (idx % 12) + 1)
        elif kind == "tq":
            idx = np.floor(v)
            out = _from_parts(1960 + np.floor(idx / 4.0), 3 * (idx % 4) + 1)
        elif kind == "th":
            idx = np.floor(v)
            out = _from_parts(1960 + np.floor(idx / 2.0), 6 * (idx % 2) + 1)
        elif kind == "tw":
            idx = np.floor(v)
            years = 1960 + np.floor(idx / 52.0)
            weeks = idx % 52
            base = _from_parts(years, pd.Series(np.ones(len(v))))
            out = base + pd.to_timedelta(weeks * 7, unit="D", errors="coerce")
        else:
            return pd.Series(pd.NaT, index=v.index, dtype="datetime64[ns]")
    except (OverflowError, ValueError, pd.errors.OutOfBoundsDatetime):
        out = pd.Series(pd.NaT, index=v.index, dtype="datetime64[ns]")
```

The `%td` and `%tc` branches survive because `pd.to_timedelta(..., errors="coerce")` never
raises; the five period branches go through `_from_parts`, and that is where the
`AssertionError` comes from. The coerce-and-warn behaviour 08-03 asked for is already written
and sits immediately after the `try` (`dash_render.py:360-369`, read at HEAD) — it is simply
never reached on the period kinds:

```python
    out = pd.Series(out).reset_index(drop=True)
    lost = int((v.notna() & out.isna()).sum())
    if lost:
        # Stata's date range is wider than pandas' nanosecond datetime64
        # (1677-2262).  Coerce rather than raise, but never silently.
        warnings.warn(
            f"dash: {lost} value(s) of a %{kind} variable fall outside the "
            f"range of dates this renderer can represent (roughly 1677-2262) "
            f"and are shown as missing.",
            UserWarning, stacklevel=3,
        )
```

*Observed at HEAD, not in REMAINING.md:* that warning names the **kind** (`%tm`), not the
variable, while 08-03's action text says *"emit a `UserWarning` naming the variable"*. The
caller — `DashRenderer._load_data`, `dash_render.py:8195-8228` — does know the column name.
Recorded here as a one-line optional improvement under TR-13.4; it is not a work item.

### Finding 2 — `colorvar()` on a date destroys the column every other touchpoint reads

REMAINING.md, Appendix C, 08-05 (reproduced below as work item 5):

> Stop `colorvar(datevar)` from destroying the shared date column.
> `_apply_colorvar` decides numeric-ness with `np.array(raw_col, dtype=float)`
> inside a try/except; a datetime64 column raises, so `is_numeric` is False,
> `use_discrete` is forced True, and the categorical branch writes
> `source.data[varname] = [str(v) for v in raw_col]` back into the SHARED
> source. Every later consumer of that column then sees strings. Route the date
> case through `date_vars` (the mapper already carries
> `date_vars`/`numeric_formats`, assigned at dash_render.py:8141-8142 and used
> by `_apply_mlabel_opts`): bin on epoch ms, label the key with
> `_format_date_value_standalone`, and never overwrite the transported column.
> The same branch shows raw floats for a `%12.0fc` colorvar key.

The probe, `dash_render.py:3095-3100` (read at HEAD):

```python
        # Determine whether the column is numeric
        try:
            col_vals = np.array(raw_col, dtype=float)
            is_numeric = not np.all(np.isnan(col_vals))
        except (ValueError, TypeError):
            is_numeric = False
            col_vals = None
```

A date column reaches this as a list of `Timestamp` objects, `np.array(..., dtype=float)`
raises `TypeError`, and `is_numeric` is `False` — so control reaches the "already categorical"
branch and the shared column is overwritten (`dash_render.py:3174-3181`, read at HEAD):

```python
            else:
                # Already categorical (string / object column)
                factors = sorted(
                    str(v) for v in raw_col
                    if v is not None and str(v) != "nan"
                )
                source.data[varname] = [str(v) for v in raw_col]
                has_missing = False
```

Two consequences, both named by REMAINING.md's *Where* clause for this item:

1. **The legend/colorbar keys are `Timestamp` reprs.** `factors` becomes
   `'2001-01-02 00:00:00'`, `'2001-01-03 00:00:00'`, … where every other touchpoint in
   08-05 renders `02 Jan 2001` through `_format_date_value_standalone`
   (`dash_render.py:203`).
2. **The range filter then drops its own widget.** REMAINING.md points at
   `dash_render.py:11788-11798`; read at HEAD, that guard is:

```python
            elif ftype == "range":
                # Same guard for range slider.
                _rng_col = fsource.data.get(fvar, [])
                # A datetime64 column is not "numeric" by this test, but it is
                # perfectly filterable -- it used to be dropped silently.
                if not (pd.api.types.is_numeric_dtype(pd.Series(_rng_col))
                        or _is_datetime_column(fsource, fvar)):
                    warnings.warn(
                        f"dash: filter '{fvar}' type 'range' requires numeric "
                        f"data; skipping widget (use type(dropdown) for string "
                        f"columns).",
                        stacklevel=2,
                    )
                    continue
```

Glyph mapping runs before the filter widgets are built, so once `_apply_colorvar` has
stringified the column, `is_numeric_dtype` is False, `_is_datetime_column` is False, and the
user's `filter(date, type(range))` silently becomes no widget at all, with a warning that
blames the data.

The machinery for the correct behaviour is already carried on the mapper.
`DashRenderer` assigns it at `dash_render.py:8141-8142`:

```python
        self.mapper.date_vars         = dict(getattr(self, "date_vars", {}))
        self.mapper.numeric_formats   = dict(getattr(self, "numeric_formats", {}))
```

and `_apply_mlabel_opts` (`dash_render.py:3301`, the marker-label half of 08-05) already
consumes it exactly the way `_apply_colorvar` should — deriving a formatted column **beside**
the transported one rather than overwriting it:

```python
        text_col = mlabel_var
        _kind = getattr(self, "date_vars", {}).get(mlabel_var)
        _numfmt = getattr(self, "numeric_formats", {}).get(mlabel_var, "")
        if _kind or _numfmt:
            text_col = f"__mlabel__{mlabel_var}"
```

The numeric half of the same defect: the discrete branch's key labels come from `_vlookup`
(`dash_render.py:3064-3077`), whose fallback is `f"{v:g}"` — so a `%12.0fc` colorvar legends as
`3000000`, not `3,000,000`, even though `_stata_numeric_pattern` already knows the answer.

### Finding 3 — the proof surface: one vacuous test, one kind, no server, no Stata

**(a) A test in `test_dates.py` whose loop body never runs.** REMAINING.md, Appendix B, 08-05:

> Fix the vacuous per-source-snapshot test: it iterates
> `cb.args.get("all_graph_sources_orig_json", [])`, a key that does not exist,
> so its loop body never runs and it asserts nothing. The real arg is
> `all_graph_sources_orig`, a list of ColumnDataSource models.

`test/test_dates.py:672-685`, read at HEAD:

```python
    def test_every_per_source_snapshot_agrees_too(self, tmp_path):
        dr = self._rendered(tmp_path)
        cb = dr.filter_callbacks[0]
        for raw in cb.args.get("all_graph_sources_orig_json", []):
            snap = json.loads(raw)
            if "date" not in snap:
                continue
            vals = [v for v in snap["date"] if v is not None]
            assert all(isinstance(v, (int, float)) for v in vals), (
                f"a per-source snapshot serialised dates as "
                f"{type(vals[0]).__name__}"
            )
```

The producing code, `dash_render.py:11834-11903` (read at HEAD) — the arg is a **list of
`ColumnDataSource`**, not a list of JSON strings, and it is built for a reason the class
docstring spells out (per-source schemas differ, so one shared `new_data` corrupts unlinked
graphs):

```python
        _snapshot_of: "dict[int, ColumnDataSource]" = {}
        ...
            _cb.args["all_graph_sources_orig"] = [
                _snapshot_of[id(_gsrc)] for _gsrc in _graph_srcs_for_cb
            ]
```

This matters beyond tidiness: the sibling test above it,
`test_the_snapshot_and_the_live_column_use_the_same_representation`, exists because the
snapshot *did* serialise dates as strings once (`_to_serialisable` calls `float(v)`, which
raises on a `Timestamp` and falls through to `str(v)`) and the filter callback then compared a
string against the slider's numeric bounds, filtering nothing. The per-source variant of that
same regression is currently unguarded.

**(b) Out-of-range is tested for exactly one kind.** REMAINING.md, Appendix C, 08-05:

> No test anywhere in test/ exercises the out-of-range date path that section
> 08-03 asked for ('Clamp or coerce and emit a UserWarning naming the
> variable'). Add a test per date kind that an out-of-range SIF value produces
> NaT plus a `UserWarning`, and never an exception — the existing suite only
> covers in-range values, which is why the %tm/%tq/%th/%tw/%ty crash above has
> never been seen.

`test/test_dates.py:168-175`, read at HEAD — `"td"`, and only `"td"`, which is one of the two
kinds that cannot fail:

```python
    def test_out_of_range_values_warn_rather_than_raise(self):
        """Stata's date range is wider than pandas' nanosecond datetime64."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            got = dash_render._stata_dates_to_datetime(
                pd.Series([14977.0, 1e9]), "td")
        assert got is not None
        assert any("range" in str(w.message).lower() for w in caught)
```

**(c) No server-mode test touches a `formats` map at all.** REMAINING.md, Appendix B, 08-05:

> Add server-mode coverage for dates and display formats. No test in the repo
> exercises ServerAppBuilder with a `formats` map, and no .cscript touches
> sp500 or any %t format at all.

Confirmed at HEAD: both parity harnesses hardcode an empty map. `test/test_mode_parity.py:70`:

```python
    bo = {"layout": "auto", "link": "", "filter": "", "theme": "",
          "scheme": "", "session_scheme": "", "title": "", "subtitle": "",
          "registry": "g1", "tabs": "", "filter_position": "top",
          "level": "95", "formats": {}}
```

and `test/test_filter_widget_parity.py:61` the same, `"formats": {}`. Appendix A's server
count — `variable_labels` 0, `DateRangeSlider` 0, `_facet_label` 0, `_format_kpi_value` 0 —
was a manual probe precisely because no automated test could produce it.

**(d) The certification suite has never built a dashboard on a `%t` variable.**
REMAINING.md, Appendix C, 08-05:

> Give section 08 Stata-side end-to-end coverage that would catch a build
> failure on a date variable. `test/test_formats.cscript` — named in 08-01's
> `<files>` — does not exist, and no .cscript in the repo builds any dashboard
> on a %t variable, so the rc 7102 abort in item 1 is invisible to the
> certification suite. The only date exemplar, examples/sp500_dates.do, uses
> `line` twice and nothing else, so `test_examples_run.cscript` cannot reach a
> fit, histogram or area layer either.

REMAINING.md's *Status by section* row for S08 records the same absence:

| # | Section | Tasks | Status | What is left |
|---|---|---:|---|---|
| 08 | Formats, dates, labels | 6 | 2 done, 4 partial ② | `xvarformat` `yvarformat` `xvarlabel` `yvarlabel` ①; `test_formats.cscript` absent ② |

Confirmed at HEAD: `ls test/*.cscript` returns 25 scripts and `test_formats.cscript` is not
among them, and `examples/sp500_dates.do` contains four `dash kpi` commands, two
`dash line` commands and a `dash build` — no fit, no histogram, no area. "The rc 7102 abort in
item 1" the item refers to is the float-cast mapper crash carried by Phase 09 item 3 / Phase 12
item 9: **20 of 31 plot types abort the entire dashboard build the moment a date variable is on
an axis**, and nothing in the Stata suite can see it.

### Where this phase sits in the backlog

08-05 is split across three phases. Phase 11 takes the hover touchpoint (the duplicate
`HoverTool`, the kind-blind `{%F}` picture, the empty-string labels, the fallback tooltips).
Phase 12 takes the filter widgets (the dropdown that filters every row away, the missing
cardinality warning, the numeric endpoints and labels, the `%9.0g` KPI reconciliation, the
large server carry). **This phase takes what is left: the shared-column defects that can break
all six touchpoints at once, and the four proof surfaces.** It is the last 08-05 phase, and the
one that makes the section's work visible to `pytest` in server mode and to the certification
suite in Stata.

---

## Epics

| Epic | Goal | Items |
|---|---|---|
| **13.A — The transported date column survives every consumer** | No code path may turn a Stata date column into an exception or into strings: the period converter coerces and warns, and `colorvar()` derives a formatted key beside the column instead of overwriting it | 3, 5 |
| **13.B — The standalone proof surface for dates** | Replace an assertion that never executes and a kind matrix that was never written, so a green `test_dates.py` means something | 1, 4 |
| **13.C — Proof across the wire: `dash serve` and Stata certification** | Give 08-05 the server-mode tests no suite has ever run, and the Stata cscript 08-01 named and nobody wrote | 2, 6 |

---

## User stories

### Epic 13.A — The transported date column survives every consumer

**Story 13.A.1 — one bad observation must not cost the whole dashboard**

> *As a Stata user pasting a `twoway` command*, I want `dash line sales month` to finish even
> when `month` holds a value outside the range the renderer can represent, so that one
> out-of-range observation costs me those points and not the entire dashboard.

- **Given** a dataset whose `%tm` variable contains a value past pandas' `Timestamp` range
  (roughly 1677–2262), **when** I run `dash line sales month, saving("out.html")`, **then** the
  command returns rc 0, writes a non-empty HTML file, and prints
  `dash: 1 value(s) of a %tm variable fall outside the range of dates this renderer can
  represent (roughly 1677-2262) and are shown as missing.`
- **Given** the same dataset, **when** the dashboard renders, **then** the out-of-range
  observation is `NaT`/missing and every in-range observation is drawn at its correct date.
- **Given** an out-of-range value under **any** of `%tc %tC %td %ty %tm %tq %th %tw`, **when**
  `_stata_dates_to_datetime` is called, **then** no exception of any class escapes it.

**Story 13.A.2 — colouring by a date must not break the rest of the page**

> *As a Stata user pasting a `twoway` command*, I want `scatter close date, colorvar(date)` to
> colour my points by date without silently removing my date filter or relabelling my legend
> with `Timestamp` reprs, so that adding a colour option does not change anything else on the
> page.

- **Given** a spec with a `%td` x-variable, a `colorvar(date)` scatter and
  `filter(date, type(range))`, **when** the dashboard is built, **then** the shared source's
  `date` column is still datetime-like (Bokeh transports it as epoch milliseconds), the range
  widget is still a `DateRangeSlider`, and no
  *"filter 'date' type 'range' requires numeric data; skipping widget"* warning is emitted.
- **Given** the same spec, **when** the legend or colorbar is drawn, **then** its keys read
  `02 Jan 2001` (the `_format_date_value_standalone` picture for the variable's kind), not
  `2001-01-02 00:00:00`.
- **Given** a `colorvar(pop)` scatter where `pop` carries `%12.0fc`, **when** the discrete
  legend is drawn, **then** the keys read `3,000,000`, not `3000000`.
- **Given** a `colorvar()` on a plain unformatted numeric variable, **when** the dashboard is
  built, **then** the behaviour is byte-identical to HEAD's (no regression in the working case).

**Story 13.A.3 — one place where the mapper learns about formats**

> *As a package maintainer*, I want `_apply_colorvar` to read the `date_vars` and
> `numeric_formats` dictionaries the mapper already carries, so that format knowledge lives in
> one place and the next touchpoint inherits it instead of re-deriving it.

- **Given** `GlyphMapper.date_vars` and `GlyphMapper.numeric_formats` are assigned by
  `DashRenderer` at `dash_render.py:8141-8142`, **when** `_apply_colorvar` needs to know whether
  a column is a date, **then** it consults `self.date_vars` rather than probing with
  `np.array(raw_col, dtype=float)`.
- **Given** a `GlyphMapper` constructed standalone with empty `date_vars` (the server path
  today), **when** `_apply_colorvar` runs, **then** it degrades to the current behaviour rather
  than raising.

### Epic 13.B — The standalone proof surface for dates

**Story 13.B.1 — every test must execute its assertions**

> *As a package maintainer*, I want each test in `test_dates.py` to be provably non-vacuous, so
> that a green suite is evidence rather than decoration.

- **Given** `test_every_per_source_snapshot_agrees_too`, **when** it runs, **then** it reads
  `cb.args["all_graph_sources_orig"]`, asserts the list is non-empty, and asserts that at least
  one snapshot carried a `date` column — so the test can never again pass by iterating nothing.
- **Given** a mutation that makes a per-source snapshot serialise dates as strings, **when** the
  suite runs, **then** this test fails.

**Story 13.B.2 — every date kind is proven safe at the edges**

> *As a package maintainer*, I want an out-of-range case for each of the eight date kinds, so
> that the crash in 13.A.1 can never be reintroduced for a kind nobody tested.

- **Given** an out-of-range SIF value for kind *k*, for each of `tc tC td ty tm tq th tw`,
  **when** `_stata_dates_to_datetime(values, k)` is called, **then** it returns a Series, the
  out-of-range entry is `NaT`, the in-range entry is preserved, and a `UserWarning` whose text
  contains "range" is emitted.
- **Given** kind `tC`, **when** the test inspects the warnings, **then** it distinguishes the
  leap-second warning from the out-of-range warning rather than accepting any warning.

### Epic 13.C — Proof across the wire

**Story 13.C.1 — the served dashboard shows what the file shows**

> *As a `dash serve` operator*, I want the served dashboard to display dates and formatted
> numbers exactly as the standalone HTML does, so that choosing `serve` over `build` is a
> deployment decision and not a change to what my audience reads.

- **Given** a spec carrying `formats: {"date": "%td"}` and a date x-variable, **when** the
  emitted app is built and executed, **then** the served figure's x-axis is a `DatetimeAxis`
  with a `DatetimeTickFormatter`, as `DashRenderer` produces for the same spec.
- **Given** `filter(date, type(range))`, **when** the app is executed, **then** the document
  contains a `DateRangeSlider`, not a `RangeSlider` over raw day numbers.
- **Given** a `max(date)` KPI, **when** the card renders, **then** it reads as a date
  (e.g. `31 Dec 2001`), not `15340.0`.
- **Given** `by(date)` facets and `mlabel(date)` markers, **when** the app is executed, **then**
  the facet titles and marker labels are formatted through the variable's kind.
- **Given** a `%12.0fc` variable, **when** it appears in a KPI or a tooltip in the served app,
  **then** it carries its thousands separators.

**Story 13.C.2 — the certification suite builds a dashboard on a date**

> *As a package maintainer*, I want a `.cscript` that builds real dashboards on `sysuse sp500`,
> so that a date-specific build failure fails the certification suite instead of waiting for a
> user to report it.

- **Given** `sysuse sp500` and a working Python, **when** `test/test_formats.cscript` runs
  `dash (scatter close date) (lfit close date)`, `dash histogram date` and
  `dash area close date`, **then** each returns `_rc == 0` and writes a non-empty HTML file.
- **Given** the same script, **when** it inspects the master JSON, **then** the document carries
  a populated `formats` map including `"date":"%td"`.
- **Given** no Python or no `jsonio`, **when** the script runs, **then** it skips with
  `exit 222` using the `c(python_exec)` rule, never by executing Python.

**Story 13.C.3 — the shipped example exercises a computed layer**

> *As a Stata user learning `dash` from the shipped examples*, I want the date exemplar to
> include a fitted layer, so that the corpus proves a computed layer works on a date axis and I
> have a pattern to copy.

- **Given** `examples/sp500_dates.do` extended with one computed layer, **when**
  `test_examples_run.cscript` runs the corpus, **then** every example still runs clean
  (`n_bad == 0`, `n_ok == nfiles`).

---

## Business requirements

| # | Requirement | How it is tested |
|---|---|---|
| **BR-13.1** | A dashboard build must never abort because a date value lies outside the range the renderer can represent. For every one of the eight Stata date kinds, an out-of-range value is coerced to missing and reported by a `UserWarning`. | `test/test_dates.py` — parametrised out-of-range case per kind (item 4) |
| **BR-13.2** | The warning that accompanies coercion must state how many values were lost and which date kind they belonged to, so a user can tell a data problem from a rendering problem. | Assertion on the warning text in the same tests |
| **BR-13.3** | Using `colorvar()` on a variable must not change the behaviour of any other feature on the page: filters, KPIs, facet titles, marker labels and hover must all behave exactly as they do without it. | `test/test_colorvar_legend.py` + `test/test_dates.py` (item 5's regression tests) |
| **BR-13.4** | Any user-facing rendering of a date value produced by `colorvar()` — legend entry, colorbar tick, category key — must use the same picture as every other 08-05 touchpoint for that kind. | Legend-factor assertions (item 5) |
| **BR-13.5** | Any user-facing rendering of a numeric value produced by `colorvar()` must honour the variable's Stata display format (`%12.0fc` → `3,000,000`). | Legend-factor assertion with a `%12.0fc` variable |
| **BR-13.6** | No test in the date suite may pass without executing its assertions; each new or repaired test must fail against a deliberate mutation of the code it covers. | Mutation checks listed in the test plan |
| **BR-13.7** | `dash serve` must present dates and Stata display formats to a viewer exactly as `dash build` presents them in the standalone file, and that agreement must be asserted automatically rather than probed by hand. | New server-mode tests (item 2) |
| **BR-13.8** | The certification suite must build at least one dashboard on a `%t` variable for a scatter, a computed (fit) layer, a histogram and an area layer, and must fail if any of them errors or produces an empty file. | `test/test_formats.cscript` (item 6) |
| **BR-13.9** | The master spec JSON that `dash.ado` writes must carry the display formats of every variable in the build, and that must be asserted from Stata, not only from Python. | `cert_file_has` assertion in `test/test_formats.cscript` |
| **BR-13.10** | The shipped example corpus must exercise a computed layer on a date axis, and must continue to run clean end to end. | `examples/sp500_dates.do` + `test/test_examples_run.cscript` |

---

## Technical requirements

### 13.A — The transported date column survives every consumer

**TR-13.1 — Stop the period branches escaping their handler.**
In `_stata_dates_to_datetime` (`dash_render.py:290`), the `try` at `dash_render.py:330-358`
must catch what pandas 3.0.1 actually raises. Two acceptable mechanisms, both named by
REMAINING.md:

1. widen the handler at `dash_render.py:357` from
   `except (OverflowError, ValueError, pd.errors.OutOfBoundsDatetime)` to `except Exception`
   (or add `AssertionError` explicitly); or
2. build the period series with `errors="coerce"` into an object or `datetime64[us]` Series
   instead of assigning into the `datetime64[ns]` block that `_from_parts`
   (`dash_render.py:318-328`) creates — i.e. remove the
   `out.loc[ok] = pd.to_datetime(...)` assignment into
   `pd.Series(pd.NaT, dtype="datetime64[ns]")` that triggers
   `blocks.coerce_to_target_dtype(..., raise_on_upcast=True)`.

Mechanism (2) is preferred where it keeps per-element coercion: option (1) discards the whole
Series on a single bad value, so a dataset with one out-of-range observation loses every date.
If (1) is chosen, the handler must still fall through to the `lost`-count warning at
`dash_render.py:360-369`, and the resulting all-`NaT` Series must be reported honestly.

**TR-13.2 — The five affected kinds are exactly `ty`, `tm`, `tq`, `th`, `tw`.**
They are the branches at `dash_render.py:337-355` that call `_from_parts`. `tc`/`tC`
(`:331-332`) and `td` (`:333-334`) use `pd.to_timedelta(..., errors="coerce")` and already
yield `NaT` plus the warning; their behaviour must not change.

**TR-13.3 — The failure path must be observable.** After the fix, an out-of-range value on a
period kind must (a) produce `NaT` for that element, (b) leave in-range elements untouched, and
(c) emit the existing `UserWarning` from `dash_render.py:363-369` whose text contains
`"fall outside the range of dates this renderer can represent (roughly 1677-2262)"`. Reached
from `DashRenderer._load_data` at `dash_render.py:8210` (`converted =
_stata_dates_to_datetime(numeric, kind)`), which must continue to assign
`self.df[col] = pd.Series(converted).to_numpy()` and record `self.date_vars[col] = kind`.

**TR-13.4 — Optional, one line:** 08-03's action text says the warning should name the
variable. `_stata_dates_to_datetime` has no variable name in scope; `_load_data`
(`dash_render.py:8195-8228`) does. If the warning is to name the column, add the name at the
call site or pass it in as a keyword with a default of `None`, preserving the existing message
when it is absent. *(Observed at HEAD; recorded for completeness, not a work item.)*

**TR-13.5 — `_apply_colorvar` must ask `date_vars`, not `np.array`.**
In `GlyphMapper._apply_colorvar` (`dash_render.py:2995`), before the numeric probe at
`dash_render.py:3095-3100`, resolve

```python
_kind   = getattr(self, "date_vars", {}).get(varname)
_numfmt = getattr(self, "numeric_formats", {}).get(varname, "")
```

using the same `getattr(..., {})` defensive shape `_apply_mlabel_opts` uses at
`dash_render.py:3331-3332`, so a mapper constructed without the metadata (the server path
today, `dash_render.py:12432`) keeps working.

**TR-13.6 — Bin dates on epoch milliseconds.** When `_kind` is truthy, convert the column with
the same cast the rest of the renderer uses —
`pd.Series(raw_col).astype("datetime64[ms]").astype("int64")`, the cast
`_extract_finite(..., allow_datetime=True)` performs at `dash_render.py:964-995` — and feed
those integers to the existing continuous/`colornlevels`/`colorcuts` machinery. Do **not** use
a raw `astype("int64")`: pandas 3 preserves the resolution it inferred, so a column may be
`datetime64[us]` or `[ns]` and a fixed divisor yields seconds for one and milliseconds for the
other. `_extract_finite`'s own comment records this.

**TR-13.7 — Label the key, never overwrite the column.** The assignment at
`dash_render.py:3180`, `source.data[varname] = [str(v) for v in raw_col]`, must not run for a
date column. The formatted text belongs in a derived column or in the factor list only —
mirror `_apply_mlabel_opts`, which writes `__mlabel__<var>` beside the transported column
(`dash_render.py:3334`). Legend/colorbar keys for a date come from
`_format_date_value_standalone(value, kind)` (`dash_render.py:203-220`), whose picture is
`%Y` for `ty`, `%d %b %Y %H:%M:%S` for `tc`/`tC`, `%b %Y` for `tm`/`tq`/`th` and `%d %b %Y`
otherwise.

**TR-13.8 — The numeric key label.** In the discrete branch at `dash_render.py:3158-3166`,
`val_label = {v: _vlookup(v) for v in unique_sorted}` falls back to `f"{v:g}"`
(`_vlookup`, `dash_render.py:3064-3077`), losing the Stata picture. When no value label exists
and `numeric_formats[varname]` is set, format the key with `_format_stata_numeric(v, fmt)` —
the helper `_apply_mlabel_opts` already uses at `dash_render.py:3341` — so `%12.0fc` legends as
`3,000,000`. A defined Stata value label still wins over the numeric picture.

**TR-13.9 — The downstream guard must stay satisfied.** After this change the range-filter
guard at `dash_render.py:11788-11798` must still see a datetime column: either
`pd.api.types.is_numeric_dtype(pd.Series(col))` or `_is_datetime_column(fsource, fvar)`
(`dash_render.py:223-243`) must be true for a `colorvar()`-coloured date column, and the
warning `"dash: filter '<v>' type 'range' requires numeric data; skipping widget"` must not be
emitted.

**TR-13.10 — No behaviour change for the working cases.** A `colorvar()` on a plain numeric
column (continuous colorbar, `colordiscrete`, `colornlevels`, `colorcuts`,
`coloruseplegend`, `colormissing`) and on a genuine string column must be unchanged. The
`"__missing__"` factor handling at `dash_render.py:3170-3172` applies to the date branch too:
`NaT` entries map to `"__missing__"`, coloured by `colormissing()`.

### 13.B — The standalone proof surface for dates

**TR-13.11 — Repair the vacuous test in place.** In `test/test_dates.py:672-685`, replace
`cb.args.get("all_graph_sources_orig_json", [])` with `cb.args["all_graph_sources_orig"]`. The
arg holds `ColumnDataSource` models (`dash_render.py:11834` declares
`_snapshot_of: "dict[int, ColumnDataSource]"`; `:11901-11903` builds the list), so each element
is read as `dict(cds.data)` — not `json.loads(raw)`. Drop the `json` round-trip.

**TR-13.12 — Make the repaired test structurally non-vacuous.** It must assert, before the
loop, that `"all_graph_sources_orig" in cb.args` and that the list is non-empty; and it must
count the snapshots that carried a `date` column and assert that count is at least 1, so the
`if "date" not in snap: continue` guard can never empty the test again.

**TR-13.13 — Parametrise the out-of-range case over all eight kinds.** Extend or replace
`test/test_dates.py:168` (`test_out_of_range_values_warn_rather_than_raise`) with a
`@pytest.mark.parametrize` over `tc tC td ty tm tq th tw`. Each case passes a two-element
Series — one in-range anchor value, one out-of-range value — and asserts: no exception, the
out-of-range element is `NaT`, the in-range element is not, and a `UserWarning` containing
`"range"` was raised. The thresholds follow from the branch arithmetic quoted above
(`dash_render.py:330-356`); pandas' representable window is roughly 1677–2262, i.e. about 302
years after the 1960 Stata epoch:

| kind | branch arithmetic | out-of-range value that clears 2262 |
|---|---|---|
| `tc` / `tC` | `_STATA_EPOCH + to_timedelta(v, unit="ms")` | `1e13` (≈ 317 years of milliseconds) |
| `td` | `_STATA_EPOCH + to_timedelta(v, unit="D")` | `1e9` (the value the existing test uses) |
| `ty` | `_from_parts(v, 1)` — the year itself | `3000` |
| `tm` | `1960 + floor(idx/12)` | `1e5` (≈ year 10,293) |
| `tq` | `1960 + floor(idx/4)` | `1e5` |
| `th` | `1960 + floor(idx/2)` | `1e5` |
| `tw` | `1960 + floor(idx/52)` | `1e6` |

**TR-13.14 — Do not let the `%tC` leap-second warning stand in for the range warning.**
`_stata_dates_to_datetime` emits an unconditional `UserWarning` for `tC`
(`dash_render.py:303-310`, *"%tC is a leap-second-corrected millisecond count…"*). The `tC`
case must therefore assert on a warning whose message contains `"fall outside the range"` (or
`"range"` **and** not `"leap"`), not merely `any(...)` over the caught list.

**TR-13.15 — Negative direction.** Include at least one case below the window (e.g. `%ty` with
`1000`, or `%tm` with `-1e5`) so a fix that clamps only the upper bound is caught.

### 13.C — Proof across the wire

**TR-13.16 — Build and execute the emitted app, do not grep it.** Server-mode tests follow the
harness already in the repo. `test/test_mode_parity.py:94-128`:

```python
def _server_figures(tmp_path, spec):
    tag = next(_SEQ)
    sp = tmp_path / f"srv_s_{tag}.json"
    dp = tmp_path / f"srv_d_{tag}.json"
    ap = tmp_path / f"srv_a_{tag}.py"
    sp.write_text(json.dumps(spec))
    dp.write_text(json.dumps(make_data_json(_DF)))
    dr.ServerAppBuilder(str(sp), str(dp)).build(str(ap))
    ms = importlib.util.spec_from_file_location(f"_parity_{tag}", str(ap))
    mod = importlib.util.module_from_spec(ms)
    ms.loader.exec_module(mod)
    doc = Document()
    mod.make_document(doc)
```

and `test/test_filter_widget_parity.py:64` (`_widgets(tmp_path, filter_raw, server)`) for the
widget walk. The new cases live in `test/test_dates_server.py` (new file) or in a
`TestServerDates` class in `test/test_dates.py`; the spec builder must pass a **populated**
`formats` map rather than the hardcoded `"formats": {}` of
`test/test_mode_parity.py:70` and `test/test_filter_widget_parity.py:61`.

**TR-13.17 — Cover all six 08-05 touchpoints in server mode.** Appendix A's four zero-counts
(`variable_labels` 0, `DateRangeSlider` 0, `_facet_label` 0, `_format_kpi_value` 0) plus
08-04's (`DatetimeAxis` 0, `DatetimeTickFormatter` 0, `date_vars` 0, `numeric_formats` 0) define
the assertion list:

| touchpoint | assertion on the executed app's `Document` |
|---|---|
| axis | the served figure's x (or y) axis is a `DatetimeAxis` carrying a `DatetimeTickFormatter` for the kind |
| data | the served column is transported on the same scale as standalone (epoch ms), so a range filter's bounds and the column agree |
| filter widgets | `type(range)` → `DateRangeSlider`; `type(slider)` → `DateSlider`; `type(dropdown)` → `Select` whose option **values** are epoch-ms numbers |
| KPI | `max(date)` renders as a date; `sum(date)` warns; a `%12.0fc` KPI carries separators |
| facets | `by(date)` panel titles render through the variable's kind |
| marker labels | `mlabel(date)` prints formatted dates, via the forwarded `_format_date_value_standalone` |
| hover | the served tooltip is the labelled/formatted one, with a `datetime` formatter entry |

**TR-13.18 — Compare against the standalone renderer, not against a literal, wherever a
sibling phase may change the picture.** Phase 12 item 12 replaces the `%b %Y` collapse in
`_format_date_value_standalone` with Stata's period pictures (`1960q1`, `1960h1`, `1958w5`).
Server tests for `%tq`/`%th`/`%tw` must therefore assert *agreement with `DashRenderer` for the
same spec* rather than hardcoding `"Jan 1960"`; `%td` and `%ty` literals are safe.

**TR-13.19 — `test/test_formats.cscript`: preamble and skip rule.** Follow
`test/test_e2e_single.cscript:1-60` exactly:

```stata
cscript "dash display formats and dates" adodir ".."

capture which jsonio
if _rc != 0 {
    display as error "SKIP: jsonio not installed. Run dash_setup first."
    exit 222
}

// Do NOT probe with `capture python: pass'.
if "`c(python_exec)'" == "" {
    display as error "SKIP: Python not available."
    exit 222
}

do "../dash_parse.mata"
do "../dash.ado"
do "cert_helpers.do"

global dash_nobrowser 1
```

`global dash_nobrowser 1` is required before any build (the pattern in
`test/test_examples_run.cscript:54`, `test/test_conformance.cscript:44` and five other
scripts); a skip is `exit 222` and is not a pass.

**TR-13.20 — `test/test_formats.cscript`: the four builds.** On `sysuse sp500, clear`
(`date` carries `%td`), each of the following must return `_rc == 0` and produce a non-empty
file, asserted with `capture confirm file` plus `cert_file_has` from
`test/cert_helpers.do:60-80` (which searches the file from Mata, so no character in the
generated HTML can terminate a Stata quote):

| command | why it is in the list |
|---|---|
| `dash (scatter close date) (lfit close date), saving(...)` | a computed layer on a date axis — the shape the float-cast crash aborts |
| `dash histogram date, saving(...)` | the binned-univariate path (`map_histogram`, `_extract_finite` without `allow_datetime=True`) |
| `dash area close date, saving(...)` | the sorted/area path (`map_area`, `np.array(source.data[xvar], dtype=float)`) |
| `dash scatter close date, saving(...)` | the plain control case that must have worked all along |

**TR-13.21 — `test/test_formats.cscript`: assert the `formats` map from Stata.** The spec
document is written by `_dash_prepare_spec` (`dash.ado:2001`) at `dash.ado:2343-2348`, and the
map itself is built by `_dash_formats_json` (`dash.ado:1266-1294`), which records
`"<var>":"<format>"` for every variable in the build and flags `%-?t[cCdhmqwy]` as a date. The
cscript obtains the document the way `test/test_serve_options.cscript:49-59` does — call the
preparer with its own tempfiles and read the path back — then asserts:

```stata
cert_file_has "`mj'", needle(`""formats":'")
assert r(found) == 1
cert_file_has "`mj'", needle(`""date":"%td""')
assert r(found) == 1
```

The immediate single-graph path writes the same key at `dash.ado:1723`
(`… "level": "`_dash_lvl'", "formats": `_dash_fmt_json'}}`), so either entry point is
acceptable as long as the assertion is on a populated map.

**TR-13.22 — Extend the date exemplar with one computed layer.**
`examples/sp500_dates.do` currently issues four `dash kpi` commands, two `dash line` commands
and one `dash build`. Add one computed layer — e.g. a third graph
`dash (scatter close date) (lfit close date), name(g3) title("Close with trend")` — and add
`g3` to the `layout(bs: …)` string so the graph is placed rather than silently dropped. The
corpus runner `test/test_examples_run.cscript:56-84` re-runs every `.do` in `examples/` and
asserts `n_bad == 0` and `n_ok == nfiles`, with `assert nfiles >= 10` guarding against a
corpus that has silently emptied.

---

## Work items

Every item is reproduced with the tag, *Where* and evidence it was handed to this phase with.
Nothing is merged, dropped or summarised.

---

**1. [deli · standalone · S]** — *origin 08-05, Appendix B*

Fix the vacuous per-source-snapshot test: it iterates
`cb.args.get("all_graph_sources_orig_json", [])`, a key that does not exist, so its loop body
never runs and it asserts nothing. The real arg is `all_graph_sources_orig`, a list of
ColumnDataSource models.

*Where:* `test/test_dates.py:672-685`
`TestDateFilterActuallyFilters::test_every_per_source_snapshot_agrees_too`; the producing code
is `dash_render.py:11901` `_cb.args["all_graph_sources_orig"] = [...]`

---

**2. [deli · server · M]** — *origin 08-05, Appendix B*

Add server-mode coverage for dates and display formats. No test in the repo exercises
ServerAppBuilder with a `formats` map, and no .cscript touches sp500 or any %t format at all.

*Where:* `test/test_dates.py` (no server cases) or a new `test/test_dates_server.py`; follow the
pattern in `test/test_filter_widget_parity.py` and `test/test_mode_parity.py`, which already
build and exec the generated app

---

**3. [func · standalone · S]** — *origin 08-05, Appendix C*

`_stata_dates_to_datetime`
(/Users/billy/Desktop/Programs/StataPrograms/d/dash/dash_render.py:290) crashes `dash` outright
on an out-of-range value for the five period-based kinds (%tm, %tq, %th, %tw, %ty). Its
`except (OverflowError, ValueError, pd.errors.OutOfBoundsDatetime)` at dash_render.py:357 does
not catch what pandas 3.0.1 actually raises. `_from_parts` (dash_render.py:318-328) assigns into
a `pd.Series(pd.NaT, dtype='datetime64[ns]')` via `out.loc[ok] = pd.to_datetime(...)`; when the
resulting year exceeds 2262 pandas raises `AssertionError` from
`blocks.coerce_to_target_dtype(..., raise_on_upcast=True)`, which propagates through
`DashRenderer._load_data` (dash_render.py:8210) and out of `render()`. Section 08-03's action
text explicitly requires the opposite: 'Do not raise on out-of-range values ... Clamp or coerce
and emit a `UserWarning` naming the variable.' The %tc and %td branches do honour that (they
warn and yield NaT); the period branches do not. Fix: catch `Exception` (or `AssertionError`)
in the try at dash_render.py:330-358, or build the period series with `errors='coerce'` into an
object/`datetime64[us]` Series instead of assigning into a `datetime64[ns]` block.

*Where:* `/Users/billy/Desktop/Programs/StataPrograms/d/dash/dash_render.py:290`
`_stata_dates_to_datetime`, its `_from_parts` closure at `:318-328` and the `except` at `:357`;
reached from `DashRenderer._load_data` at `:8210`

---

**4. [deli · standalone · S]** — *origin 08-05, Appendix C*

No test anywhere in test/ exercises the out-of-range date path that section 08-03 asked for
('Clamp or coerce and emit a UserWarning naming the variable'). Add a test per date kind that an
out-of-range SIF value produces NaT plus a `UserWarning`, and never an exception — the existing
suite only covers in-range values, which is why the %tm/%tq/%th/%tw/%ty crash above has never
been seen.

*Where:* `/Users/billy/Desktop/Programs/StataPrograms/d/dash/test/test_dates.py` (add to
`TestFormatClassification`'s neighbours, near the conversion tests)

---

**5. [func · standalone · M]** — *origin 08-05, Appendix C*

Stop `colorvar(datevar)` from destroying the shared date column. `_apply_colorvar` decides
numeric-ness with `np.array(raw_col, dtype=float)` inside a try/except; a datetime64 column
raises, so `is_numeric` is False, `use_discrete` is forced True, and the categorical branch
writes `source.data[varname] = [str(v) for v in raw_col]` back into the SHARED source. Every
later consumer of that column then sees strings. Route the date case through `date_vars` (the
mapper already carries `date_vars`/`numeric_formats`, assigned at dash_render.py:8141-8142 and
used by `_apply_mlabel_opts`): bin on epoch ms, label the key with
`_format_date_value_standalone`, and never overwrite the transported column. The same branch
shows raw floats for a `%12.0fc` colorvar key.

*Where:* `dash_render.py:2995` `GlyphMapper._apply_colorvar`; the numeric probe at `:3095-3100`;
the stringifying write at `:3180` `source.data[varname] = [str(v) for v in raw_col]`; the
value-label branch at `:3160-3166` (`val_label`, where a numeric_formats lookup belongs); the
guard that then drops the widget at `dash_render.py:11788-11798`

---

**6. [deli · stata · M]** — *origin 08-05, Appendix C*

Give section 08 Stata-side end-to-end coverage that would catch a build failure on a date
variable. `test/test_formats.cscript` — named in 08-01's `<files>` — does not exist, and no
.cscript in the repo builds any dashboard on a %t variable, so the rc 7102 abort in item 1 is
invisible to the certification suite. The only date exemplar, examples/sp500_dates.do, uses
`line` twice and nothing else, so `test_examples_run.cscript` cannot reach a fit, histogram or
area layer either. Minimum: a cscript asserting rc 0 and a non-empty file for
`dash (scatter close date) (lfit close date)`, `dash histogram date` and `dash area close date`
on sysuse sp500, plus the master JSON carrying a populated `formats` map; and extend the
exemplar with one computed layer so the corpus exercises it.

*Where:* new `test/test_formats.cscript` (follow `test/test_e2e_single.cscript:1-60` for the
cscript preamble and the `c(python_exec)` skip rule); `examples/sp500_dates.do`;
`test/test_examples_run.cscript:56-84` (the loop that runs the corpus)

> *Cross-phase note.* "The rc 7102 abort in item 1" refers to the float-cast mapper crash
> carried by Phase 09 item 3 and Phase 12 item 9, not to an item in this phase. This cscript is
> that crash's Stata-side regression guard: it must be written here and it cannot go green
> until those fixes land. See *Risks and sequencing notes*.

---

## Test plan

Project rule 8 governs the two functional items: **write the regression test first, watch it
fail, then fix the code.** Project rule 4 governs the helpers: every function touched gets a
unit test. Every test below carries a mutation — the specific thing to break so the test dies —
because two of this phase's six items exist precisely because a test passed while the code was
wrong.

### Epic 13.A — The transported date column survives every consumer

#### 13.A / item 3 — the period converter

**The failing test, first** (`test/test_dates.py`, beside
`test_out_of_range_values_warn_rather_than_raise` at `:168`):

```python
@pytest.mark.parametrize("kind,anchor,bad", [
    ("tm", 492.0, 1e5), ("tq", 164.0, 1e5), ("th", 82.0, 1e5),
    ("tw", 2131.0, 1e6), ("ty", 2001.0, 3000.0),
])
def test_period_kinds_coerce_out_of_range_instead_of_raising(kind, anchor, bad):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        got = dash_render._stata_dates_to_datetime(pd.Series([anchor, bad]), kind)
    assert not pd.isna(got.iloc[0])          # the in-range value survives
    assert pd.isna(got.iloc[1])              # the out-of-range value is NaT
    assert any("fall outside the range" in str(w.message) for w in caught)
```

At HEAD this raises `AssertionError` out of pandas rather than failing an assertion — which is
the proof that the defect is real. Record that distinction in the test's docstring.

**Unit tests (rule 4).**

| test | asserts |
|---|---|
| `test_period_kinds_coerce_out_of_range_instead_of_raising` | the case above, parametrised over `tm tq th tw ty` |
| `test_in_range_period_values_are_unchanged` | the existing `date_truth.json` anchors still convert byte-identically (guards mechanism (2) of TR-13.1 against a resolution change) |
| `test_an_all_bad_period_column_is_all_nat_and_warns_once` | every value out of range → all `NaT`, exactly one warning |
| `test_a_single_bad_value_does_not_discard_the_good_ones` | the mechanism-(1) trap: if `except Exception` replaces the whole Series, this fails |

**Integration.** `DashRenderer.render()` on a spec with `formats={"m": "%tm"}` and one
out-of-range row: `render()` returns, the output file is non-empty, the figure's renderer has
the expected number of finite points, and a `UserWarning` was raised.

**Mutation (non-vacuity).** Restore the handler at `dash_render.py:357` to
`except (OverflowError, ValueError, pd.errors.OutOfBoundsDatetime)` (or re-introduce the
`datetime64[ns]` assignment in `_from_parts`): the five parametrised cases must error, and the
integration test must fail. Separately, delete the `warnings.warn` at `dash_render.py:365-370`:
the `"fall outside the range"` assertions must fail.

#### 13.A / item 5 — `colorvar()` on a date

**The failing test, first** (`test/test_dates.py`, in `TestFacetAndMarkerLabels`'s neighbours,
or a new `TestColorvarOnADate`):

```python
def test_colorvar_on_a_date_leaves_the_shared_column_a_date(self, tmp_path):
    spec = _minimal_spec(
        [{"type": "scatter", "yvar": "close", "xvar": "date",
          "options": {"colorvar": "date"}}],
        formats={"date": "%td"})
    spec["build_options"]["filters"] = [
        {"varname": "date", "type": "range", "exclude": [], "label": ""}]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        dr = _renderer(spec, _dated_payload(), tmp_path)
        dr.render()
    # the transported column is still a date
    assert dash_render._is_datetime_column(<the shared source>, "date")
    # and so the range widget is still a DATE widget
    assert any(isinstance(w, DateRangeSlider) for w in dr.filter_widgets)
    assert not any("requires numeric data" in str(w.message) for w in caught)
```

**Unit tests (rule 4)** — `_apply_colorvar` is one function with several branches; each gets a
case in `test/test_colorvar_legend.py` (the existing home for this helper):

| test | asserts |
|---|---|
| `test_a_date_colorvar_does_not_stringify_the_source_column` | `source.data["date"]` is unchanged in dtype and length after `_apply_colorvar` |
| `test_a_date_colorvar_labels_its_keys_with_the_stata_picture` | legend factors / colorbar ticks read `02 Jan 2001`, matching `_format_date_value_standalone(v, "td")` |
| `test_a_date_colorvar_bins_on_epoch_milliseconds` | with `colornlevels(4)`, the cut points are epoch-ms integers and the four bins partition the data |
| `test_a_formatted_numeric_colorvar_key_carries_its_separators` | `%12.0fc` → `3,000,000`, not `3000000` (TR-13.8) |
| `test_a_value_labelled_colorvar_still_prefers_the_value_label` | `_vlookup`'s value-label hit still wins over the numeric picture |
| `test_a_plain_numeric_colorvar_is_unchanged` | the negative twin: continuous colorbar path byte-identical to HEAD |
| `test_a_string_colorvar_is_unchanged` | the genuine categorical branch still stringifies |
| `test_nat_values_map_to_the_missing_factor` | `NaT` → `"__missing__"`, coloured by `colormissing()` |
| `test_a_mapper_without_date_vars_degrades` | `GlyphMapper()` with no `date_vars` assigned behaves as HEAD does (protects the server path at `dash_render.py:12432`) |

**Integration.** One render carrying `colorvar(date)` **and** `filter(date, type(range))`
**and** a `max(date)` KPI **and** `mlabel(date)`: assert the widget is a `DateRangeSlider`, the
KPI card reads as a date, and the marker-label column `__mlabel__date` contains formatted dates
— i.e. that the shared column survived all four consumers.

**Mutation (non-vacuity).** Re-introduce `source.data[varname] = [str(v) for v in raw_col]` for
the date branch: the integration test, the filter-widget assertion and the
`_is_datetime_column` assertion must all fail. Change the key formatter from
`_format_date_value_standalone` to `str`: the legend-factor test must fail. Replace
`astype("datetime64[ms]").astype("int64")` with a bare `astype("int64")`: the epoch-ms binning
test must fail on a `datetime64[ns]`-resolution column.

### Epic 13.B — The standalone proof surface for dates

#### 13.B / item 1 — the vacuous snapshot test

**Prove the vacuity before repairing it.** Add, in the same class, a guard that fails at HEAD:

```python
def test_the_per_source_snapshot_arg_exists_and_is_populated(self, tmp_path):
    dr = self._rendered(tmp_path)
    cb = dr.filter_callbacks[0]
    assert "all_graph_sources_orig" in cb.args
    assert cb.args["all_graph_sources_orig"], "no per-source snapshots were built"
```

Then repair `test_every_per_source_snapshot_agrees_too` per TR-13.11/TR-13.12: iterate the
`ColumnDataSource` list, read `dict(cds.data)`, count the snapshots carrying `"date"`, and
assert that count ≥ 1 before asserting the values are numeric.

**Mutation (non-vacuity).** Two mutations, both must kill it:

1. rename the arg back to `all_graph_sources_orig_json` at `dash_render.py:11901` — the
   repaired test must fail with `KeyError`, not pass silently;
2. make the per-source snapshot serialise dates as strings (mirror the original
   `_to_serialisable` `float(v)` → `str(v)` fall-through) — the value assertion must fail.

A third check, cheap and worth having: run the repaired test with `-p no:randomly` and assert
in review that the loop counter is non-zero, because a test that asserts inside a loop is only
as good as the loop's length.

#### 13.B / item 4 — out-of-range per kind

The parametrised tests are the ones written first for item 3 (above), extended to the two kinds
that already work and to the negative direction:

| test | asserts |
|---|---|
| `test_every_kind_coerces_out_of_range` (`tc tC td ty tm tq th tw`) | no exception; out-of-range → `NaT`; in-range preserved; a `"fall outside the range"` `UserWarning` |
| `test_tC_out_of_range_warning_is_not_the_leap_second_warning` | TR-13.14 — the caught warning list contains both, and the range assertion matches the right one |
| `test_values_below_the_window_also_coerce` | TR-13.15 — `%ty 1000`, `%tm -1e5` |
| `test_no_warning_when_every_value_is_in_range` | the negative twin: a clean column raises no `UserWarning` at all (except `tC`'s unconditional leap-second one) |

**Mutation.** Narrow the handler back, as above; and separately make the coercion silent
(delete the warning): `test_no_warning_when_every_value_is_in_range` must still pass while every
out-of-range case fails, which proves the warning assertions are load-bearing.

### Epic 13.C — Proof across the wire

#### 13.C / item 2 — server-mode dates and formats

**The failing test, first.** A single case that fails at HEAD for a reason Appendix A already
measured:

```python
def test_the_served_app_gives_a_date_column_a_datetime_axis(tmp_path):
    spec = _spec([{"type": "line", "yvar": "close", "xvar": "date", "options": {}}],
                 build_options={"formats": {"date": "%td"}})
    figs = _server_figures(tmp_path, spec)
    assert isinstance(figs[0].xaxis[0], DatetimeAxis)
    assert isinstance(figs[0].xaxis[0].formatter, DatetimeTickFormatter)
```

**Unit / integration tests**, in `test/test_dates_server.py` (new), one per touchpoint of
TR-13.17:

| test | asserts |
|---|---|
| `test_the_served_axis_is_a_datetime_axis` | `DatetimeAxis` + per-kind `DatetimeTickFormatter` |
| `test_the_served_column_is_on_the_same_scale_as_standalone` | the served column and the standalone column agree (epoch ms) for the same spec |
| `test_a_served_range_filter_on_a_date_is_a_daterangeslider` | `DateRangeSlider`, and its bounds equal the column's min/max |
| `test_a_served_slider_filter_on_a_date_is_a_dateslider` | `DateSlider` |
| `test_a_served_date_dropdown_carries_epoch_values_and_formatted_labels` | `Select` options: value is the epoch-ms number, label is the Stata picture |
| `test_a_served_date_kpi_renders_as_a_date` | `max(date)` → a date string, not `15340.0` |
| `test_a_served_sum_of_a_date_warns` | the *"adds up dates, which has no meaning"* warning survives into the app |
| `test_a_served_facet_title_on_a_date_reads_as_a_date` | `by(date)` panel titles |
| `test_a_served_marker_label_on_a_date_reads_as_a_date` | `mlabel(date)` |
| `test_a_served_formatted_numeric_kpi_keeps_its_separators` | `%12.0fc` |
| `test_a_served_tooltip_is_the_labelled_formatted_one` | variable labels + a `datetime` formatter entry |
| `test_a_served_spec_without_formats_is_unchanged` | the negative twin: `"formats": {}` behaves exactly as HEAD |

**Mutation (non-vacuity).** In the emitted loader (`dash_render.py:13123`
`_load_spec_and_data`, whose only coercion today is the `pd.to_numeric` loop at
`dash_render.py:13161-13165`), make the `formats` read a no-op — every positive test above must
fail and `test_a_served_spec_without_formats_is_unchanged` must still pass. Separately, strip
the `DateRangeSlider` branch from the emitted filter loop
(`dash_render.py:15364-15460`, dropdown at `:15378`, range at `:15403`): only the widget tests
must fail. If a test survives its mutation, it is asserting on the generated **source text**
rather than on the executed document — rewrite it against `mod.make_document(doc)`.

#### 13.C / item 6 — Stata certification

**The failing script, first.** `test/test_formats.cscript` is written before the mapper fixes
it guards (Phase 09 item 3 / Phase 12 item 9) land, and at that point it fails: the
`lfit`, `histogram` and `area` builds return rc 7102 with no HTML file. That failure is the
deliverable's evidence — record the observed rc in the commit message, per rule 8.

**Script contents** (TR-13.19 to TR-13.21):

1. preamble + `jsonio`/`c(python_exec)` skip rules + `global dash_nobrowser 1`;
2. `sysuse sp500, clear`;
3. four builds — scatter, scatter+lfit, histogram, area — each with
   `capture confirm file`, `assert _rc == 0`, and a `cert_file_has` needle proving the file
   carries a Bokeh embed rather than being merely non-empty;
4. a `formats`-map assertion on the master JSON via `_dash_prepare_spec` with the script's own
   tempfiles, following `test/test_serve_options.cscript:49-59`;
5. a final `display "test_formats.cscript: ALL CHECKS PASSED"`.

**Corpus extension.** Add the computed layer to `examples/sp500_dates.do` (TR-13.22) and run
`test/test_examples_run.cscript`, which asserts `nfiles >= 10`, `n_bad == 0` and
`n_ok == nfiles`.

**Mutation (non-vacuity).** Revert the datetime-aware extraction in one mapper (e.g. restore
`np.array(source.data[xvar], dtype=float)` in `map_area`, `dash_render.py:3614`): the
`dash area close date` assertion must fail with a non-zero rc. Remove `formats` from the master
JSON at `dash.ado:2343`: the `cert_file_has` assertion must report `r(found) == 0`. Remove the
new layer from the exemplar: no test should fail (it is a corpus extension, not a guard) — which
is why it is paired with the cscript rather than standing alone.

### Suite-level obligations

- Run the full `pytest` suite and the full certification suite before any commit (rule 5).
  At HEAD the audit records **3,498 passed / 37 skipped; 25/25 cscripts**; this phase adds one
  cscript, so the expected figure becomes 26/26.
- The cert suite runs from `test/` under `arch -arm64`; **a skip is not a pass** — if
  `test_formats.cscript` reports `exit 222`, the environment is wrong and the result is not
  evidence.
- `$dash_nobrowser` must be set for every Stata run that builds a dashboard.

---

## Definition of done

A reviewer can tick every line below.

**Functional — Epic 13.A**

- [ ] `_stata_dates_to_datetime` raises no exception for any of `tc tC td ty tm tq th tw` on
      any finite input, including values far outside 1677–2262 in both directions.
- [ ] An out-of-range value yields `NaT` for that element only; in-range elements in the same
      Series are unaffected.
- [ ] The `"fall outside the range of dates this renderer can represent"` `UserWarning` fires
      once per conversion that lost values, naming the count and the kind.
- [ ] `DashRenderer.render()` completes and writes a non-empty file for a `%tm` (and `%tq`,
      `%th`, `%tw`, `%ty`) column containing an out-of-range value.
- [ ] `_apply_colorvar` never writes `[str(v) for v in raw_col]` into a date column of the
      shared `ColumnDataSource`.
- [ ] `_apply_colorvar` resolves date-ness from `self.date_vars`, not from
      `np.array(raw_col, dtype=float)`.
- [ ] Date colour bins are computed on epoch milliseconds via
      `astype("datetime64[ms]").astype("int64")`.
- [ ] Legend/colorbar keys for a date read through `_format_date_value_standalone` for the
      variable's kind; keys for a formatted numeric read through the variable's Stata picture
      (`%12.0fc` → `3,000,000`), with a defined value label still winning.
- [ ] `colorvar(date)` + `filter(date, type(range))` still produces a `DateRangeSlider` and
      emits no *"requires numeric data; skipping widget"* warning.
- [ ] `colorvar()` on plain numeric and on genuine string columns is unchanged.

**Deliverable — Epic 13.B**

- [ ] `test_every_per_source_snapshot_agrees_too` reads `all_graph_sources_orig` as
      `ColumnDataSource` models and no longer references
      `all_graph_sources_orig_json` anywhere in `test/`.
- [ ] That test asserts the arg exists, the list is non-empty, and at least one snapshot
      carried the date column — it cannot become vacuous again.
- [ ] Out-of-range coverage exists for all eight date kinds, in both directions.
- [ ] The `%tC` case distinguishes the leap-second warning from the range warning.
- [ ] Each new or repaired test was run against its stated mutation and observed to fail.

**Deliverable — Epic 13.C**

- [ ] `test/test_dates_server.py` (or `TestServerDates` in `test/test_dates.py`) builds and
      **executes** the emitted app with a populated `formats` map.
- [ ] All seven server touchpoints of TR-13.17 are asserted, plus the unformatted negative
      twin.
- [ ] Period-kind server assertions compare against `DashRenderer` output rather than
      hardcoded pictures (TR-13.18).
- [ ] `test/test_formats.cscript` exists, follows the `test_e2e_single.cscript` preamble and the
      `c(python_exec)` skip rule, sets `$dash_nobrowser`, and asserts rc 0 plus a non-empty,
      Bokeh-bearing file for scatter, scatter+lfit, histogram and area on `sysuse sp500`.
- [ ] The script asserts the master JSON carries a populated `formats` map including
      `"date":"%td"`.
- [ ] `examples/sp500_dates.do` includes one computed layer, placed in the layout.
- [ ] `test_examples_run.cscript` passes with `n_bad == 0` and `n_ok == nfiles`.

**Process**

- [ ] Both functional items were driven by a test that failed first and passes after (rule 8),
      with the pre-fix failure recorded.
- [ ] Every function touched has a unit test (rule 4).
- [ ] Full `pytest` and full certification suite pass, 26/26 cscripts, no new skips (rule 5).
- [ ] Work committed to a feature branch, with the merge command reported and not run
      (rule 6), and no tool or vendor names in the commit message (rule 7).
- [ ] `REMAINING.md` is untouched.

---

## Risks and sequencing notes

**1. Item 3 duplicates Phase 09 items 6 and 13 — deliberately.** The same defect was found
through three lenses: Appendix A's 08-04 remaining item 2, the 08-03 refutation row, and
Appendix C's 08-05 entry (this phase's item 3). Whichever phase lands first, the other closes
its copy as already-done — but **item 4's per-kind test matrix belongs to this phase either
way** and must still be written, because Phase 09's guard is expressed as a parametrisation of
the existing `%td` test and this phase's is the full eight-kind matrix including the negative
direction and the `%tC` warning discrimination. Coordinate before starting: if Phase 09 has
already landed the fix, item 3 becomes a verification, not a change, and the phase's effort
drops from 3 medium + 3 small to 3 medium + 2 small.

**2. Item 6's cscript cannot pass until two other phases land.** The commands it runs —
`lfit`, `histogram`, `area` on a date axis — are exactly the ones that abort with rc 7102 until
Phase 09 item 3 / Phase 12 item 9 teach the mappers a datetime-aware extraction. That is the
point of the script, and it is also a scheduling constraint: the certification suite must be
green before any commit (rule 5), so either the cscript lands in the same merge as those fixes,
or it lands after them. It must **not** be weakened (e.g. by asserting `_rc != 0`) to make the
suite green in the meantime — that would encode the defect as expected behaviour.

**3. Item 2 tests behaviour another phase implements.** Phase 12 item 4 (*"Carry the whole of
08-05 into the generated server app"*, `[func · server · L]`) and Phase 10 item 1
(`ServerAppBuilder` date support) are the implementation; item 2 is the proof. Writing the
tests first is correct and useful — they will fail exactly the way Appendix A's manual probe
did (`DateRangeSlider` 0, `_facet_label` 0, `_format_kpi_value` 0) and give those phases a
target — but they cannot be merged green before that work. Sequence: write with Phase 12,
merge with Phase 12, or merge immediately after.

**4. Do not duplicate Phase 12 item 8.** That item adds a date/format case to the two **parity**
suites (`test/test_mode_parity.py:74`, `test/test_filter_widget_parity.py:61`), which compare
standalone against server. Item 2 here adds **server-mode** coverage of the six touchpoints,
which the parity corpus does not enumerate. Agree the split before writing: parity cases assert
*agreement*, item 2's cases assert *correctness* of the served artefact. Duplicating the same
assertion in both places doubles the maintenance without adding a guard.

**5. Appendix A's minor item 4 is not in scope.** *"`count` on a date column renders `30.0`
rather than `30`"* is a recorded 08-05 minor that no item in this phase carries. The server KPI
tests in item 2 must not pin `30.0` as expected output — assert the count as a number, or
assert agreement with the standalone renderer, so that whichever phase fixes the `.0` does not
have to revisit this file.

**6. The period picture is about to change under item 2's feet.** Phase 12 item 12 replaces
`_format_date_value_standalone`'s `%b %Y` collapse for `%tm`/`%tq`/`%th` (and the `%tw` day
branch) with Stata's own pictures — `1960q1`, `1960h1`, `1958w5` — using
`test/fixtures/date_truth.json`'s `display` field, which the suite currently ignores in favour
of `iso`. TR-13.18 exists for this: assert server/standalone agreement for the period kinds,
literals only for `%td` and `%ty`.

**7. `_apply_colorvar` is shared with the server builder.** The mapper the emitted app
constructs (`dash_render.py:12432`, `_DASH_MAPPER = GlyphMapper(scheme=_DASH_SCHEME)`) carries
no `date_vars` today, so item 5's fix must degrade gracefully rather than assume the attribute
(TR-13.5). Once Phase 12 item 4 assigns `date_vars`/`numeric_formats` onto `_DASH_MAPPER`, the
same fix lights up in server mode with no further work — which is the argument for landing
item 5 before, not after, that server carry.

**8. Mechanism choice in TR-13.1 has a user-visible consequence.** `except Exception` around
the whole dispatch discards the entire column on a single bad value; per-element `errors=
"coerce"` discards only the bad values. The second is what 08-03 asked for ("Clamp or coerce"),
and `test_a_single_bad_value_does_not_discard_the_good_ones` is the test that forces the
choice. Pick the mechanism before writing the fix, not after.

**9. Effort honesty.** Items 3 and 1 are genuinely small (a handler and a dictionary key).
Item 4 is small but broad — eight kinds, two directions, one warning discrimination. Item 5 is
medium and touches a 200-line method with six option branches; the negative twins in the test
table are not optional, because `colorvar()` is the kind of shared helper where a date fix
quietly changes the numeric path. Items 2 and 6 are medium and are mostly **writing tests
against code other phases are writing** — schedule them late in the wave, not first.
