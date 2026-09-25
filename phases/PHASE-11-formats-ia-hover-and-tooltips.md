# Phase 11 — Formats I(a): hover and tooltips

**Purpose.** Task 08-05 ("Format dates and numbers everywhere they are displayed") has six
touchpoints; five of them work in the standalone renderer and one does not. The hover
tooltip is the one that does not. Today every scatter and line figure carries **two**
`HoverTool`s — the labelled, formatted one that 08-05 built, and a stale raw-variable-name
one that `GlyphMapper` attaches per renderer — and Bokeh leaves both active, so the user
sees two tooltip boxes and one of them is wrong. Even the correct box is not right yet: its
date picture ignores the date *kind* (`%ty` hovers as `1998-01-01`), its row labels collapse
to the **empty string** for any variable without a Stata variable label, and the fallback
tooltip used on histogram/KDE/fit-only figures consults neither `date_vars` nor
`numeric_formats`, so a binned date hovers as raw epoch milliseconds. This phase closes the
hover clause of 08-05 in the standalone renderer and leaves a regression guard behind it —
today's two hover tests both use `any(...)` over all tools and pass against the defect.

---

## At a glance

| | |
|---|---|
| **Items** | 5 (numbered 1–5 below, exactly as handed over) |
| **Functional vs deliverable** | 4 functional · 1 deliverable |
| **Effort mix** | 5 × small (no medium, no large) |
| **Renderers touched** | `standalone` (`DashRenderer`) on all five items. **But** `GlyphMapper` is copied into the emitted server app *verbatim* (`dash_render.py:12344`, `:12408`), so item 1 changes `dash serve` too — see Risks. |
| **Ultraplan tasks discharged** | `08-05`, hover clause only (1 of its 6 touchpoints). Section **S08**. |
| **Not discharged here** | 08-05's filter-widget clause (Phase 12), its KPI/facet/marker-label and server clauses (Phase 13), 09-07's `hover()` option (Phase 27). |
| **Depends on** | Nothing hard at HEAD — `self.date_vars` / `self.numeric_formats` are already populated (`dash_render.py:8193-8228`, propagated to the mapper at `:8141-8142`). Item 4's user-visible effect is masked until the date-axis crashes in **Phase 9** (items 3, 9) / **Phase 12** (item 9) / **Phase 13** (item 3) are fixed; the unit-level defect is testable now. |
| **Unblocks** | **Phase 12** item 4(g) and **Phase 13** (the server carry of 08-05 — it must copy a hover that is correct first), **Phase 27** items 2 and 10, which edit the same `_make_figure` hover block. |
| **Source of items** | Items 1–2: REMAINING.md Appendix B, `08-05`. Items 3–5: REMAINING.md Appendix C, `08-05` (15 further items). |

---

## Why this phase exists

### What the audit measured (REMAINING.md, Appendix A, `08-05 · PARTIAL`)

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
>    handling. Present with and without a `formats` key, so it is not the date
>    path that adds it. `tools=` at `dash_render.py:9552` is
>    `"pan,wheel_zoom,box_select,lasso_select,reset"` and does not include
>    `hover`, so both tools are added deliberately somewhere and one is stale.
>    The user sees two tooltips, one of them wrong.

The "somewhere" is `GlyphMapper._hover_tool`, confirmed at HEAD (`dash_render.py:2564`):

```python
    def _hover_tool(self, yvar: str, xvar: str,
                   renderers: "list | None" = None) -> HoverTool:
        """Return a HoverTool scoped to *renderers* (or all if None)."""
        ht = HoverTool(tooltips=[
            (xvar, f"@{{{xvar}}}"),
            (yvar, f"@{{{yvar}}}"),
        ])
        if renderers is not None:
            ht.renderers = renderers
        return ht
```

It has exactly two callers, both unconditional — `map_scatter` (`:3483`) and `map_line`
(`:3557`), each `fig.add_tools(self._hover_tool(yvar, xvar, renderers=[r]))`. The
comprehensive tool built later in `DashRenderer._make_figure` removes them **only** when
`hover()` extras were requested (`dash_render.py:10199-10202`, verbatim at HEAD):

```python
        _hover_extra_str = graph_opts.get("hover", "").strip()
        _hover_extra = _hover_extra_str.split() if _hover_extra_str else []
        _has_hover = any(isinstance(t, HoverTool) for t in fig.tools)
        if _has_hover and _hover_extra:
            # Remove existing hover tools before adding comprehensive one with extras
            fig.tools = [t for t in fig.tools if not isinstance(t, HoverTool)]
```

`graph_opts["hover"]` is empty on virtually every real build — REMAINING.md Appendix B,
`09-07` records that `hover()` is **never serialized by `dash.ado` at all**, so the strip
above is dead in practice and both tools survive. With Bokeh's `active_inspect="auto"`,
both are active, and the user gets two tooltip boxes.

### The date picture ignores the date kind

`_hover_row` (`dash_render.py:10216`, its date branch measured at `:10223-10227`) is the
only date touchpoint in the file that does not consult the kind table:

```python
            kind = getattr(self, "date_vars", {}).get(col)
            if kind:
                spec = f"@{{{col}}}{{%F}}" if kind != "tc" else \
                       f"@{{{col}}}{{%F %T}}"
                _hover_formatters[f"@{{{col}}}"] = "datetime"
```

Two sibling helpers already carry the kind table and disagree with it —
`_format_date_value_standalone` (`:203`) and `_datetime_formatter_for` (`:247`):

| kind | `_format_date_value_standalone` | axis formatter `_datetime_formatter_for` | hover today | REMAINING.md's example of the defect |
|---|---|---|---|---|
| `%ty` | `f"{ts.year}"` → `1998` | `years="%Y"` | `{%F}` → `1998-01-01` | "`%ty` hovers as '1998-01-01' instead of '1998'" |
| `%tm` `%tq` `%th` | `"%b %Y"` → `Jun 2001` | `%b %Y` | `{%F}` → `2001-06-01` | "`%tm`/`%tq`/`%th` as '2001-06-01' instead of 'Jun 2001'" |
| `%td` `%tw` | `"%d %b %Y"` | day-level | `{%F}` | ISO where the rest of the dashboard writes `21 Dec 2022` |
| `%tc` | `"%d %b %Y %H:%M:%S"` | seconds | `{%F %T}` ✓ | the only kind that is right |
| `%tC` | same as `%tc` | same as `%tc` | `{%F}` | "`%tC` silently loses the time that `%tc` keeps" — the branch tests `kind != "tc"`, so `tC` falls through |

### Row labels are the empty string, and 08-05's own fix caused it

REMAINING.md, Appendix C, `08-05`:

> **[func · standalone · S]** Hover rows are labelled with the EMPTY STRING for any
> variable that carries no Stata variable label. `_axis_label` (dash_render.py:9300) is
> `return self.variable_labels.get(varname, varname)` — jsonio supplies `""` for an
> unlabelled variable, so the key EXISTS with an empty value and the `varname` default
> never fires. 08-05's own change at dash_render.py:10233
> (`_hover_fields.append((self._axis_label(col), spec))`, introduced by commit 783043e
> "Carry Stata display formats through to the browser, and fix dates entirely") swapped the
> raw name for this, so the fix made unlabelled variables WORSE than the raw names it
> replaced. The same helper feeds the fallback histogram/KDE tooltips at
> dash_render.py:10282 and 10295. Fix: `self._axis_label(col) or col`, or give
> `_axis_label` an empty-string fallback (which also fixes the blank axis title it produces
> on the same build).

Confirmed at HEAD: `variable_labels` is loaded straight from the payload
(`self.variable_labels = stata_json.get("variableLabels", {})`, `:8168`) and `_axis_label`
(`:9300`, body at `:9302`) is the one-line `.get(varname, varname)`. The codebase already
contains the correct idiom **twice**, which is why this reads as an oversight rather than a
decision:

| site | code |
|---|---|
| `dash_render.py:3056` (`GlyphMapper._apply_colorvar`) | `var_display = self.variable_labels.get(varname, "") or varname` |
| `dash_render.py:11757` (filter-widget label resolution) | `or self.variable_labels.get(fvar, "").strip() \` … `or fvar` |
| `dash_render.py:9302` (`_axis_label` — the defect) | `return self.variable_labels.get(varname, varname)` |

### The fallback tooltip is format-blind

REMAINING.md, Appendix C, `08-05`:

> **[func · standalone · S]** Apply formats in the FALLBACK hover path. When no renderer
> carries the original variable columns (a histogram/kdensity/fit-only figure),
> `_make_figure` builds `_fb_fields` from the derived CDS with `_tooltip_precision` alone —
> it never consults `date_vars` or `numeric_formats` and never sets a `formatters` dict, so
> a binned date hovers as raw epoch milliseconds and a `%9.0fc` variable loses its commas.

The branch at HEAD (`:10262-10305`) confirms it: `_tooltip_precision` (`:174`) derives one
numeric precision from the spread of the data and that is the entire formatting story —
no `formatters=` argument is ever passed to the fallback `HoverTool`:

```python
                    if "top" in _fb_src.data and "left" in _fb_src.data:
                        _bin_var = self._axis_label(_yvar_eff or "value")
                        _p = _tooltip_precision(_fb_src.data.get("left", []))
                        _fb_fields = [
                            (_bin_var,
                             f"@{{left}}{{{_p}}} to @{{right}}{{{_p}}}"),
                            ("Count",   "@{top}"),
                        ]
                        _fb_mode = "vline"
                    # KDE / fit line: "x" and "y" columns
                    elif "x" in _fb_src.data and "y" in _fb_src.data:
```

### The existing tests cannot see any of this

REMAINING.md, Appendix C, `08-05`:

> **[deli · standalone · S]** Add a test that a figure carries exactly ONE HoverTool and
> that it is the labelled/formatted one. Both existing hover tests use `any(...)` over all
> tools, so they pass unchanged while GlyphMapper's raw-variable-name HoverTool is still
> attached and active — the defect the auditor found in the browser. Without this the fix
> to that defect has no regression guard.

Both tests in `test/test_dates.py:591` (`class TestHoverShowsDates`) are existential:

```python
        hovers = [t for t in fig.tools if isinstance(t, HoverTool)]
        assert hovers, "no hover tool on the figure"
        assert any(
            getattr(h, "formatters", None)
            and any("datetime" in str(v) for v in h.formatters.values())
            for h in hovers
        ), "the date column has no datetime tooltip formatter"
```

and

```python
        text = " ".join(
            str(h.tooltips) for h in fig.tools if isinstance(h, HoverTool))
        assert "Closing price" in text, (...)
```

A second, wrong tool passes both.

### What the plan asked for

`.ultraplan/sections/section-08-formats-dates.md`, task `08-05` `<action>`, hover clause:

> **Hover** (`:6078-6089`, `:6127-6131`). Use a datetime field spec with a `formatters`
> entry for date columns; use the Stata numeric pattern for formatted numerics. While here,
> fix two adjacent defects: tooltips label rows with raw **variable names** although
> `self.variable_labels` is loaded and used for axes (`_axis_label:5540`) — use the label;
> and the fallback tooltips hardcode three different precisions (`{0.2f}`, `{0.3f}`,
> `{0.4f}`) — derive one from the data or the format.

(Those line numbers are the plan's own and are stale — the file grew from ~10,455 to
~16,000 lines. The symbols are `_axis_label` at `:9300` and the `_make_figure` hover block
at `:10192-10305`.)

The same section's requirements that this phase is measured against:

> - BR-08.1 Every Stata date format renders as a date wherever it is displayed.
> - BR-08.2 Every Stata numeric display format is honoured wherever the value is displayed.
> - BR-08.4 A variable with no date format takes exactly the code path it takes today.
> - TR-08.4 Hover, filters, facet labels, marker labels and KPI values format dates as dates
>   and numbers by their Stata format.

and the task's opening constraint: *"Six touchpoints. Each must leave non-date, unformatted
columns exactly as they are."*

---

## Epics

| Epic | Name | Goal | Items |
|---|---|---|---|
| **E11.1** | One tooltip, and it is the right one | A figure carries exactly one `HoverTool`, the labelled/formatted one, and a test says so | 1, 5 |
| **E11.2** | Every hover row says what it means | Row label never blank; date picture follows the Stata date kind | 2, 3 |
| **E11.3** | The fallback tooltip honours formats too | Histogram / KDE / fit-only figures format dates and numerics like every other figure | 4 |

---

## User stories

### E11.1 — One tooltip, and it is the right one

> **As a Stata user pasting a `twoway` command**, I want one tooltip when I hover a point,
> so that I am not shown two boxes with two different answers and left to guess which is
> mine.

- **Given** `dash line close date` on `sysuse sp500` with `formats={"date": "%td"}`,
  **when** the figure is built, **then** `[t for t in fig.tools if isinstance(t, HoverTool)]`
  has length 1.
- **Given** that one tool, **when** its `tooltips` are read, **then** the row labels are the
  variable labels (or names), not the bare `('date','@{date}')` pair `GlyphMapper` emits,
  and `formatters` contains `{'@{date}': 'datetime'}`.
- **Given** a figure with a `scatter` plus an `lfit` layer, **when** the hover tools are
  inspected, **then** the single remaining tool is still renderer-scoped so the fit line
  does not tooltip `???` — the BF-11 guarantee in `test/test_glyphs.py:2612` is unchanged.
- **Given** the same spec built through `ServerAppBuilder`, **when** the emitted app is
  exec'd, **then** the figure still has at least one `HoverTool` (no silent loss of the
  server's only tooltip — see Risks).

> **As a package maintainer**, I want a test that counts hover tools rather than searching
> them, so that the next person who adds a tool somewhere cannot reintroduce the double
> tooltip and stay green.

- **Given** the fix is reverted (restore `fig.add_tools(self._hover_tool(...))` in
  `map_scatter`), **when** the suite runs, **then** the new test fails.

### E11.2 — Every hover row says what it means

> **As a dashboard viewer**, I want a hovered date to read the way the axis, the facet title
> and the KPI card read it, so that `1998` is `1998` and not `1998-01-01`.

- **Given** a `%ty` variable, **when** I hover, **then** the row shows `1998`.
- **Given** a `%tm`, `%tq` or `%th` variable, **when** I hover, **then** the row shows
  `Jun 2001` — the same picture `_format_date_value_standalone` (`:203`) produces.
- **Given** a `%tC` variable, **when** I hover, **then** the time component is shown, as it
  is for `%tc`.
- **Given** a plain, unformatted numeric column, **when** I hover, **then** the spec is
  exactly `@{col}` as it is today (BR-08.4).

> **As a Stata user whose variables have no variable labels**, I want the hover row to name
> the variable, so that the tooltip is not a column of blank labels.

- **Given** a payload whose `variableLabels` maps `"mpg"` to `""` (what `jsonio` supplies
  for an unlabelled variable), **when** the figure is built, **then** the tooltip row label
  is `mpg`.
- **Given** the same payload, **when** the axis title is read, **then** it is `mpg` and not
  the empty string (`_axis_label` is shared).
- **Given** a payload whose `variableLabels` maps `"mpg"` to `"Mileage (mpg)"`, **when** the
  figure is built, **then** the row label is `Mileage (mpg)` — the labelled case is
  unchanged.

### E11.3 — The fallback tooltip honours formats too

> **As a Stata user**, I want `dash histogram date` and `dash (lfit close date)` to hover in
> dates and thousands separators like every other figure, so that the formatting I set in
> Stata does not depend on which glyph happens to be under the cursor.

- **Given** a histogram figure whose binned variable is `%td`, **when** I hover a bar,
  **then** the bin edges read as dates and the tool carries a `datetime` entry in
  `formatters` for the referenced fields.
- **Given** a fit-only figure on a `%9.0fc` variable, **when** I hover the line, **then** the
  value carries thousands separators (`_stata_numeric_pattern('%9.0fc')` → `'0,0'`).
- **Given** a histogram of an unformatted numeric, **when** I hover, **then** the tooltip is
  byte-identical to today's `_tooltip_precision`-derived one, and `mode="vline"` is retained
  (`test/test_glyphs.py:2700`).

---

## Business requirements

| ID | Requirement | How it is judged |
|---|---|---|
| **BR-11.1** | A built figure carries exactly one `HoverTool`, and it is the labelled/formatted one built by `DashRenderer._make_figure`. | Count, not search, over `fig.tools`. |
| **BR-11.2** | No tooltip row is ever labelled with the empty string. | A row label is the Stata variable label when non-blank, otherwise the variable name. |
| **BR-11.3** | A hovered date renders in the picture its Stata date kind implies, matching the picture the axis, facet title and KPI card already use for that kind. | Per-kind assertion against the `_format_date_value_standalone` table. |
| **BR-11.4** | A Stata numeric display format is honoured in the tooltip on **every** figure, including figures whose renderers carry only derived columns. | `%9.0fc` → `0,0` in both the primary and the fallback paths. |
| **BR-11.5** | A variable with no date format and no display format takes exactly the code path it takes today, with the same output. (Section 08's *"Each must leave non-date, unformatted columns exactly as they are"*; BR-08.4.) | Negative twins assert unchanged specs. |
| **BR-11.6** | Every defect fixed in this phase has a test that fails before the fix and passes after (CLAUDE.md rule 8), and every function touched or added has a unit test (rule 4). | Mutation column of the test plan. |
| **BR-11.7** | `dash serve` does not lose its tooltips as a side effect of item 1. | An emitted-app test asserts a `HoverTool` survives on a served scatter/line figure. |

---

## Technical requirements

### TR-11.1 — Stop the duplicate tool at the source (item 1)

- **Symbol:** `GlyphMapper._hover_tool`, `dash_render.py:2564`. Callers, both unconditional,
  both `fig.add_tools(self._hover_tool(yvar, xvar, renderers=[r]))`:
  `map_scatter` at `:3483`, `map_line` at `:3557`. `grep -n "_hover_tool("` returns exactly
  those three lines — there is no third caller.
- **Mechanism:** the figure is created with
  `tools="pan,wheel_zoom,box_select,lasso_select,reset"` (`dash_render.py:9552`) — no
  `hover` — so both tools are added by code, and the conditional strip at `:10199-10202`
  only fires when `graph_opts["hover"]` is non-empty. `hover()` is not serialized by
  `dash.ado` at all (REMAINING.md, Appendix B, `09-07`), so in practice the strip never
  fires and Bokeh's `active_inspect="auto"` leaves both tools active.
- **Required change:** the raw-name tool must not be *active* on a `DashRenderer` figure.
  Preferred shape: remove the two `add_tools` calls so only `_make_figure`'s comprehensive
  tool exists. `_hover_tool` itself must **not** simply be deleted without handling
  TR-11.7 — it is the server app's only tooltip today.
- **Must not regress:** the BF-11 renderer scoping (`renderers=[r]`) that the comprehensive
  tool reproduces at `:10252-10262` via `_data_renderers`; `test/test_glyphs.py:2612`
  `TestHoverToolRendererScope` a/b/c.

### TR-11.2 — One date-kind table, consulted by hover (item 2)

- **Symbol:** `DashRenderer._make_figure._hover_row`, `dash_render.py:10216`; the offending
  branch is `:10223-10227` (REMAINING.md cites `:10222-10225`, the same statement including
  the docstring terminator).
- **Mechanism:** `kind = getattr(self, "date_vars", {}).get(col)` already yields the Stata
  kind (`date_vars` is populated at `:8193-8228` and mirrored onto the mapper at `:8141`).
  The spec string must select a Bokeh datetime picture per kind rather than `{%F}`:

  | kind | required tooltip spec | mirrors |
  |---|---|---|
  | `ty` | `@{col}{%Y}` | `_format_date_value_standalone` `f"{ts.year}"` (`:203`), `_datetime_formatter_for` `years="%Y"` (`:247`) |
  | `tm` `tq` `th` | `@{col}{%b %Y}` | `"%b %Y"` |
  | `td` `tw` | `@{col}{%d %b %Y}` | `"%d %b %Y"` |
  | `tc` `tC` | `@{col}{%d %b %Y %H:%M:%S}` (or the existing `%F %T`, applied to **both**) | `"%d %b %Y %H:%M:%S"` |

- `_hover_formatters[f"@{{{col}}}"] = "datetime"` must continue to be set for every date
  kind — it is what `test/test_dates.py:593` asserts.
- **Structural requirement:** implement as a *shared* kind→picture lookup, not a third
  inline table. Phase 12 item 12 will retune the period kinds to Stata's own pictures
  (`1960q1`, `1960h1`, `1958w5`) across `_format_date_value_standalone`,
  `DashRenderer._format_date_value` (`:8860`) and the `_FILTER_JS` twin (`:7285-7307`); hover
  must move with them, not drift a fourth time.

### TR-11.3 — `_axis_label` must never return the empty string (item 3)

- **Symbol:** `DashRenderer._axis_label`, `dash_render.py:9300`, body at `:9302`:
  `return self.variable_labels.get(varname, varname)`.
- **Cause:** `self.variable_labels = stata_json.get("variableLabels", {})` (`:8168`); `jsonio`
  emits `""` for an unlabelled variable, so the key exists and the `varname` default is
  unreachable.
- **Required change:** `return self.variable_labels.get(varname, "") or varname` (the idiom
  already used at `:3056` and `:11757`), or the call-site form `self._axis_label(col) or col`
  at `:10233`. The helper-level fix is preferred because it also repairs the blank **axis
  title** the same build produces, and because `_axis_label` also feeds the fallback
  tooltips at `:10282` and `:10295`.
- **Blast radius to check before choosing:** every caller of `_axis_label`. A helper-level
  change alters axis titles as well as tooltips; that is the intended repair, but it must be
  asserted rather than assumed.
- **Regression origin:** commit `783043e` ("Carry Stata display formats through to the
  browser, and fix dates entirely") introduced `:10233`
  `_hover_fields.append((self._axis_label(col), spec))`, replacing the raw name.

### TR-11.4 — Formats in the fallback hover path (item 4)

- **Symbol:** the `else:` branch of `if _data_renderers:` inside
  `DashRenderer._make_figure`, `dash_render.py:10262-10305`; `_fb_fields` is initialised at
  `:10272`, the histogram branch at `:10281-10289` (`_bin_var` at `:10282`), the KDE/fit
  branch at `:10290-10300` (`_axis_label(xvar or "x")` at `:10295`).
- **Defect:** `_tooltip_precision` (`:174`) is the only formatting applied, and no
  `formatters=` dict is passed to the `HoverTool` constructed at `:10301-10303`.
- **Required change:** mirror `_hover_row` (`:10215-10234`):
  - resolve the *source* variable behind each derived column — `left`/`right`/`top` come
    from the binned variable (`_yvar_eff or "value"`, already resolved at `:10282`), `x`/`y`
    from `xvar` / `_yvar_eff` (already resolved at `:10295-10298`);
  - if that variable is in `date_vars`, use the TR-11.2 picture and add
    `formatters={"@{left}": "datetime", ...}` for each referenced field;
  - else if it is in `numeric_formats`, use `_stata_numeric_pattern(pattern)` (`:395`);
  - else keep `_tooltip_precision` exactly as today.
- `mode="vline"` for the histogram branch and `renderers=_fb_rends[:1]` must be preserved —
  both are asserted by `test/test_glyphs.py:2700`.
- **Visibility note:** REMAINING.md records this path as "currently masked by the crash in
  item 1" of its Appendix C `08-05` list. That item is **not** in this phase: the first
  Appendix C item for `08-05` is the `_stata_dates_to_datetime` out-of-range crash (Phase 13,
  item 3), and the crash that actually blocks a histogram/kdensity/fit-only figure on a date
  variable is the float-cast mapper abort — "the WHOLE dashboard aborts with rc 7102 and no
  HTML file" (Phase 12 item 9; its 08-04 twins are Phase 9 items 3 and 9). The fallback
  defect is fixable and unit-testable here regardless, on a **non-date formatted numeric**
  and on a date column fed directly to the figure builder.

### TR-11.5 — The counting test (item 5)

- **Symbol under test:** `dash_render.py:2564`, `:3483`, `:3557`, `:10199-10202`.
- **Location:** `test/test_dates.py`, beside `TestHoverShowsDates` (`:591-623`).
- **Shape:** `hovers = [t for t in fig.tools if isinstance(t, HoverTool)]`;
  `assert len(hovers) == 1`; then assert on `hovers[0].tooltips` / `.formatters` directly —
  never `any(...)` over the list, which is precisely why the current pair of tests is blind.

### TR-11.6 — Non-date, unformatted columns unchanged

- For a column in neither `date_vars` nor `numeric_formats`, `_hover_row` must still produce
  exactly `f"@{{{col}}}"` and add nothing to `_hover_formatters`; the fallback must still
  produce the `_tooltip_precision` spec. Assert as explicit negative twins, in the style of
  the existing `test_mlabel_on_a_plain_variable_is_unchanged` /
  `test_a_numeric_filter_is_unchanged` / `test_a_numeric_kpi_is_unchanged`.

### TR-11.7 — Do not strip the server's only tooltip

- `ServerAppBuilder` emits `GlyphMapper`'s source **verbatim**: `dash_render.py:12344`
  (`"# ---- The glyph layer, copied verbatim from dash_render.py ----"`), `:12408`
  (`for _cls in (OptionTranslator, SchemeParser, GlyphMapper):` … `_inspect.getsource(_cls)`),
  and the app instantiates it at `:12432` (`_DASH_MAPPER = GlyphMapper(scheme=_DASH_SCHEME)`).
  The emitted scatter branch calls `_DASH_MAPPER.map_scatter(...)` at `:14090`, under a
  comment that names this exact tool (`:14088`: *"a hover tool showing raw variable names
  where … the saved dashboard shows labels and formats"*).
- The emitted app has **no** comprehensive hover: `grep` for `hover` after
  `class ServerAppBuilder` (`:12265`) returns that one comment line and nothing else, which
  matches REMAINING.md, Appendix B, `09-07`: *"the only occurrence of the string 'hover'
  after `class ServerAppBuilder`"*.
- Therefore removing the two `add_tools` calls silently leaves `dash serve` with **zero**
  tooltips. Required: either (a) keep the raw tool for the server path only, by moving the
  `add_tools` call out of `GlyphMapper` and into `DashRenderer`'s and the emitted app's own
  code, or (b) land the emitted labelled hover from Phase 12 item 4(g) in the same change.
  Whichever is chosen, an emitted-app test (TR-11.7's story in E11.1) must assert a
  `HoverTool` still exists on a served scatter and line figure.

---

## Work items

All five items are reproduced exactly as handed over, with their tags, *Where* clauses and
evidence. Nothing is merged or summarised.

### Item 1 — `[func · standalone · S]` · origin `08-05` · REMAINING.md Appendix B

> Remove or stop activating the raw-variable-name HoverTool that `GlyphMapper` adds, so the
> labelled/formatted tooltip is the only one shown. The existing removal at 10199-10202
> fires ONLY when `hover()` extras are requested; otherwise both tools stay and Bokeh's
> `active_inspect="auto"` leaves both active, so two tooltip boxes appear.

*Where:* `dash_render.py:2564 GlyphMapper._hover_tool`; its callers at 3483 (`map_scatter`)
and 3557 (`map_line`); the conditional strip at `dash_render.py:10199-10202` in
`DashRenderer._make_figure`.

*Evidence:* Appendix A, `08-05`, Remaining §1 — the second tool is
`[('d','@{d}'), ('v','@{v}')]`, present with and without a `formats` key; `tools=` at
`:9552` does not include `hover`. Confirmed at HEAD: three `_hover_tool` occurrences, the
`if _has_hover and _hover_extra:` guard, and `hover()` unserialized by `dash.ado`
(Appendix B, `09-07`).

*Cross-phase:* **Phase 27 item 10** edits the same block (`hover()` on a line plot deletes
every tooltip, `:10197-10290`). **TR-11.7** governs the server side.

### Item 2 — `[func · standalone · S]` · origin `08-05` · REMAINING.md Appendix B

> Make the hover date picture depend on the date KIND, as every other touchpoint does.
> `_hover_row` uses `{%F}` for every kind except `tc`, so `%ty` hovers as '1998-01-01'
> instead of '1998', `%tm`/`%tq`/`%th` as '2001-06-01' instead of 'Jun 2001', and `%tC`
> silently loses the time that `%tc` keeps.

*Where:* `dash_render.py:10222-10225` in `DashRenderer._make_figure._hover_row`; mirror the
kind table already in `_format_date_value_standalone` (`dash_render.py:203`) and
`_datetime_formatter_for` (`dash_render.py:247`).

*Evidence:* the branch at HEAD is `spec = f"@{{{col}}}{{%F}}" if kind != "tc" else
f"@{{{col}}}{{%F %T}}"` (measured at `:10224-10226`); the two sibling tables disagree with
it for `ty`, `tm`, `tq`, `th`, `td`, `tw` and `tC`.

### Item 3 — `[func · standalone · S]` · origin `08-05` · REMAINING.md Appendix C

> Hover rows are labelled with the EMPTY STRING for any variable that carries no Stata
> variable label. `_axis_label` (dash_render.py:9300) is
> `return self.variable_labels.get(varname, varname)` — jsonio supplies `""` for an
> unlabelled variable, so the key EXISTS with an empty value and the `varname` default never
> fires. 08-05's own change at dash_render.py:10233
> (`_hover_fields.append((self._axis_label(col), spec))`, introduced by commit 783043e
> "Carry Stata display formats through to the browser, and fix dates entirely") swapped the
> raw name for this, so the fix made unlabelled variables WORSE than the raw names it
> replaced. The same helper feeds the fallback histogram/KDE tooltips at dash_render.py:10282
> and 10295. Fix: `self._axis_label(col) or col`, or give `_axis_label` an empty-string
> fallback (which also fixes the blank axis title it produces on the same build).

*Where:* `dash_render.py:9300 DashRenderer._axis_label`; `dash_render.py:10233` in
`_make_figure._hover_row`; `dash_render.py:10282`, `10295` (fallback tooltips).

*Evidence:* the one-line body at `:9302`; `variableLabels` read raw at `:8168`; the working
`or` idiom already at `:3056` and `:11757`.

### Item 4 — `[func · standalone · S]` · origin `08-05` · REMAINING.md Appendix C

> Apply formats in the FALLBACK hover path. When no renderer carries the original variable
> columns (a histogram/kdensity/fit-only figure), `_make_figure` builds `_fb_fields` from the
> derived CDS with `_tooltip_precision` alone — it never consults `date_vars` or
> `numeric_formats` and never sets a `formatters` dict, so a binned date hovers as raw epoch
> milliseconds and a `%9.0fc` variable loses its commas. This path is currently masked by the
> crash in item 1; it becomes user-visible the moment that is fixed.

*Where:* `dash_render.py:10262-10305` (the `_fb_fields` fallback inside
`DashRenderer._make_figure`), to mirror `_hover_row` at `:10215-10234`; `_tooltip_precision`
at `:174`.

*Evidence:* the two fallback branches at HEAD carry only `_tooltip_precision`-derived specs
and no `formatters=` argument. On "the crash in item 1" see **TR-11.4** — the referenced
crash lives in Phase 13 (item 3) / Phase 12 (item 9) / Phase 9 (items 3, 9), not here.

### Item 5 — `[deli · standalone · S]` · origin `08-05` · REMAINING.md Appendix C

> Add a test that a figure carries exactly ONE HoverTool and that it is the
> labelled/formatted one. Both existing hover tests use `any(...)` over all tools, so they
> pass unchanged while GlyphMapper's raw-variable-name HoverTool is still attached and
> active — the defect the auditor found in the browser. Without this the fix to that defect
> has no regression guard.

*Where:* `test/test_dates.py:591-623 TestHoverShowsDates`; the code under test at
`dash_render.py:2564 GlyphMapper._hover_tool` and `dash_render.py:10199-10202`.

*Evidence:* both existing tests quoted verbatim in **Why this phase exists**; each is
satisfied by a second, wrong tool.

---

## Test plan

Rule 8 governs the order: **the failing test is written and seen to fail first**, then the
fix. Rule 4 governs the breadth: every function touched or introduced gets a unit test.
Every test below carries a mutation — the specific edit that must make it die. A test whose
mutation leaves it green is vacuous and does not count as done.

Files used: `test/test_dates.py` (all date/format pytest coverage; helpers `_renderer` `:196`,
`_minimal_spec` `:205`, `_dated_payload` `:482`, `_jsonio_payload` `:182`),
`test/test_glyphs.py` (hover scoping, `:2551` `_make_dr_for_hover`, `:2591` `_all_hover_cols`,
`:2612` `TestHoverToolRendererScope`), `test/test_mode_parity.py` and
`test/test_server.py` (emitted-app execution). No new pytest file is needed; hover belongs
with the rest of 08-05's coverage in `test/test_dates.py`.

### E11.1 — One tooltip, and it is the right one (items 1, 5)

| # | Test | File · class | Asserts | Mutation that must kill it |
|---|---|---|---|---|
| **1.a** | `test_a_figure_carries_exactly_one_hover_tool` — **write first, must fail at HEAD** | `test/test_dates.py` · new `TestExactlyOneHoverTool` | `len([t for t in fig.tools if isinstance(t, HoverTool)]) == 1` for a `line` and for a `scatter` figure | restore `fig.add_tools(self._hover_tool(yvar, xvar, renderers=[r]))` at `dash_render.py:3483` |
| **1.b** | `test_the_one_hover_tool_is_the_labelled_one` | same | `hovers[0].tooltips` row labels are the variable labels, and `hovers[0].formatters` contains `"datetime"` for the date column — asserted on `hovers[0]`, never via `any(...)` | change `_hover_fields.append((self._axis_label(col), spec))` (`:10233`) back to `(col, spec)` |
| **1.c** | `test_raw_name_tooltips_are_gone` | same | no tool on the figure has `tooltips == [(xvar, "@{"+xvar+"}"), (yvar, "@{"+yvar+"}")]` | as 1.a |
| **1.d** | unit test for `GlyphMapper._hover_tool` itself (rule 4) — whichever shape survives TR-11.7 | `test/test_glyphs.py` · beside `TestHoverToolRendererScope` | called directly, it still returns a `HoverTool` with `renderers` set when `renderers` is passed | drop the `if renderers is not None:` guard at `:2570` |
| **1.e** | non-regression: BF-11 scoping still holds | `test/test_glyphs.py:2615, 2640, 2672` (existing) | unchanged; run them, do not edit them | make the comprehensive tool unrestricted (delete `renderers=_data_renderers` at `:10262`) |
| **1.f** | `test_served_scatter_still_has_a_hover_tool` (BR-11.7) | `test/test_server.py` or `test/test_mode_parity.py` | the exec'd emitted app's scatter and line figures each have ≥ 1 `HoverTool` | remove the `add_tools` call from the emitted app's dispatch as well as the standalone one |

### E11.2 — Every hover row says what it means (items 2, 3)

| # | Test | File · class | Asserts | Mutation that must kill it |
|---|---|---|---|---|
| **2.a** | `test_hover_date_picture_follows_the_kind` — **write first, must fail at HEAD** | `test/test_dates.py` · `TestHoverShowsDates` | parametrised over `ty`→`{%Y}`, `tm`/`tq`/`th`→`{%b %Y}`, `td`/`tw`→`{%d %b %Y}`, `tc`/`tC`→ a spec containing `%H:%M:%S`; read the spec out of the single tool's `tooltips` | revert the branch to `f"@{{{col}}}{{%F}}" if kind != "tc" else …` |
| **2.b** | `test_tC_keeps_its_time_like_tc` | same | the `%tC` spec equals the `%tc` spec | restore the `kind != "tc"` test |
| **2.c** | `test_hover_kind_table_agrees_with_the_value_formatter` | same | for each kind, the hover picture and `_format_date_value_standalone(value, kind)` describe the same granularity (year / month / day / second) | change one row of the shared kind table in isolation — the test must fail, proving the two tables cannot drift again |
| **2.d** | `test_an_unlabelled_variable_hovers_under_its_name` — **write first, must fail at HEAD** | `test/test_dates.py` · new `TestHoverRowLabels` | build with `variableLabels = {"close": "", "date": ""}`; the tool's row labels are `close` / `date`, and no label is `""` | revert `_axis_label` to `self.variable_labels.get(varname, varname)` |
| **2.e** | `test_a_labelled_variable_still_hovers_under_its_label` (negative twin) | same | `variableLabels = {"close": "Closing price"}` → row label `Closing price`; the existing `test_tooltips_use_variable_labels_not_raw_names` (`:608`) also stays green | make `_axis_label` return `varname` unconditionally |
| **2.f** | `test_an_unlabelled_variable_gets_a_non_blank_axis_title` (rule 4, the helper's other consumer) | `test/test_axis_options.py` or `test/test_dates.py` | `fig.xaxis[0].axis_label` is `date`, not `""` | as 2.d |
| **2.g** | `test_an_unformatted_column_hovers_exactly_as_before` (BR-11.5 negative twin) | `test/test_dates.py` | spec is `@{mpg}` and `formatters` has no entry for it | make the numeric branch emit a pattern unconditionally |

### E11.3 — The fallback tooltip honours formats too (item 4)

| # | Test | File · class | Asserts | Mutation that must kill it |
|---|---|---|---|---|
| **3.a** | `test_fallback_tooltip_formats_a_date` — **write first, must fail at HEAD** | `test/test_dates.py` · new `TestFallbackHoverFormats` | on a histogram-only figure whose binned variable is `%td`, the fallback tool carries a `datetime` formatter entry and a date picture, not `@{left}{0.00}` | delete the `date_vars` lookup added to the fallback branch |
| **3.b** | `test_fallback_tooltip_keeps_thousands_separators` | same | fit-only / KDE-only figure on a `%9.0fc` variable → spec contains `0,0` (`_stata_numeric_pattern('%9.0fc')`) | delete the `numeric_formats` lookup in the fallback branch |
| **3.c** | `test_fallback_tooltip_on_a_plain_numeric_is_unchanged` (BR-11.5 negative twin) | same | spec equals the `_tooltip_precision` value computed for the same data, and no `formatters` dict is attached | make the fallback always attach a `formatters` dict |
| **3.d** | `test_histogram_hover_uses_fallback_tooltip` (existing, `test/test_glyphs.py:2700`) | existing | unchanged: a scoped tool with `mode="vline"` | drop `_fb_mode = "vline"` at `:10289` |
| **3.e** | unit test for `_tooltip_precision` boundaries (rule 4) | `test/test_dates.py` | already-covered pure helper; extend with the empty-column and zero-spread cases at `:190-197` | return a constant `"0.00"` from the spread branch |

### Cross-cutting

- **Suite runs.** Full `pytest` before and after (HEAD baseline is *3,498 passed / 37
  skipped*, per REMAINING.md "Gates still to pass"). No net new skips.
- **Certification suite.** 25/25 cscripts must still pass, run with `arch -arm64` from
  `test/`. A skip is not a pass. This phase adds no cscript of its own: the Stata-side date
  exemplar `test/test_formats.cscript` is named by 08-01, does not exist, and is owned by
  **Phase 9 item 14** / **Phase 13 item 6**. When it lands, it should gain one hover
  assertion; until then the hover coverage is pytest-only, and this document says so rather
  than claiming Stata-side proof it does not have.
- **Browser check.** 08-06's standing instruction applies to anything visual: *"Open it in a
  browser and look at it… Do not report this task complete on the basis of the HTML source."*
  One human look at an `sp500` build confirming a single tooltip box, set
  `$dash_nobrowser` for the automated builds around it.

---

## Definition of done

- [ ] `[t for t in fig.tools if isinstance(t, HoverTool)]` has length 1 on a scatter figure,
      a line figure, a scatter+lfit figure and a faceted figure. (BR-11.1, item 1)
- [ ] That one tool's `tooltips` carry variable labels and format-aware specs; its
      `formatters` carry `"datetime"` for every date column. (item 1)
- [ ] Hover pictures match `_format_date_value_standalone` for `ty`, `tm`, `tq`, `th`, `td`,
      `tw`, `tc` and `tC`, sourced from one shared kind table rather than a new inline one.
      (BR-11.3, item 2)
- [ ] `%tC` shows a time. (item 2)
- [ ] `_axis_label` never returns `""`; hover rows, fallback hover rows (`:10282`, `:10295`)
      and axis titles all fall back to the variable name. (BR-11.2, item 3)
- [ ] The fallback hover path consults `date_vars` and `numeric_formats` and attaches a
      `formatters` dict when it references a date; `mode="vline"` and
      `renderers=_fb_rends[:1]` survive. (BR-11.4, item 4)
- [ ] A column in neither `date_vars` nor `numeric_formats` produces byte-identical tooltips
      to HEAD, asserted by explicit negative twins. (BR-11.5)
- [ ] Every fix above has a test that was **seen to fail** before the fix and passes after,
      and each new test was proven non-vacuous by the mutation named in its row. (BR-11.6,
      rule 8)
- [ ] `test/test_dates.py`'s existing `TestHoverShowsDates` pair still passes, and the new
      count-based test replaces `any(...)` reasoning rather than adding to it. (item 5)
- [ ] An emitted-app test proves `dash serve` still shows a tooltip on scatter and line.
      (BR-11.7, TR-11.7)
- [ ] Full pytest green against the 3,498-passed baseline with no new skips; 25/25 cscripts
      green.
- [ ] One browser look at an `sp500` dashboard: one tooltip box, dates in it.
- [ ] Branch-local commits only, with the merge command supplied; commit messages describe
      the change and mention no assistant. (CLAUDE.md rules 6, 7)

---

## Risks and sequencing notes

1. **`GlyphMapper` is copied verbatim into the emitted server app — item 1 is not
   standalone-only in effect.** `dash_render.py:12344` and `:12408` copy the class with
   `inspect.getsource`, the app builds `_DASH_MAPPER` at `:12432`, and the emitted scatter
   branch calls `map_scatter` at `:14090`. The emitted app has no comprehensive hover of its
   own (one comment at `:14088` is the only `hover` string after `class ServerAppBuilder`
   at `:12265`). Removing the `add_tools` calls therefore leaves `dash serve` with **no**
   tooltip at all. Mitigation in TR-11.7: move the call out of the mapper, or land it with
   Phase 12 item 4(g). Either way, test 1.f is mandatory, not optional.
2. **Phase 27 edits the same block.** Phase 27 item 10 ("`hover()` … DELETES every tooltip on
   the figure", `_make_figure_body` hover block `:10197-10290`, the strip at `:10202`) and
   item 2 (the server's missing `hover()` support) both rewrite the code this phase touches.
   Land Phase 11 **first**: once only one hover tool exists, the strip at `:10199-10202`
   becomes a much simpler thing for Phase 27 to reason about, and the "hover() deletes
   everything" defect reduces to a rebuild-or-not decision. If the two phases run
   concurrently, they must share a branch.
3. **Item 4's user-visible effect is gated elsewhere.** A histogram/KDE/fit-only figure on a
   date variable currently aborts the whole build with rc 7102 (Phase 12 item 9; Phase 9
   items 3 and 9), and out-of-range period values raise a bare pandas `AssertionError`
   (Phase 13 item 3). Do not wait for those: test item 4 at the unit level, on a formatted
   numeric and on a date column driven straight into `_make_figure`, so the fix is proven
   now and simply becomes visible when the crashes are gone.
4. **The period pictures will change under this phase's feet.** Phase 12 item 12 replaces
   `"%b %Y"` with Stata's own period pictures (`1960q1`, `1960h1`, `1958w5`) across
   `_format_date_value_standalone` (`:203`), `DashRenderer._format_date_value` (`:8860`) and
   the `_FILTER_JS` twin (`:7285-7307`). Build item 2 as a lookup that those phases can
   retune once; a fourth inline table is a guaranteed future drift. Note also that a Bokeh
   tooltip picture is a strftime-style string, so a literal `1960q1` may need a computed
   label rather than a format spec — flag it to Phase 12 rather than half-solving it here.
5. **`_axis_label` has consumers beyond hover.** The helper-level fix in TR-11.3 changes axis
   titles as well as tooltips. That is the intended repair (REMAINING.md calls the blank axis
   title out explicitly), but enumerate the callers before committing and assert the axis
   case (test 2.f) so the change is deliberate rather than incidental.
6. **Do not weaken BF-11.** The comprehensive tool's `_data_renderers` filter
   (`:10246-10262`) is what keeps `???` out of tooltips on derived-CDS renderers. Item 1
   removes a *tool*, not a *scope*. Run `test/test_glyphs.py::TestHoverToolRendererScope`
   unchanged as part of the acceptance evidence.
7. **Sequencing within the phase.** E11.1 first (it is the defect a user sees), then E11.2
   (cheap, and its tests are easier to write against a single tool), then E11.3. Item 5 is
   written before item 1's fix, by rule 8, and is the gate on the whole phase.
