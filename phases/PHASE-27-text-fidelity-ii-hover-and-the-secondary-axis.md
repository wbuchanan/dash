# Phase 27 — Text fidelity II: hover() and the secondary axis

**Purpose.** Task 09-07 bundled four defects — double escaping, canvas text, the
secondary-axis range under a qualifier, and `mlabel()` on line plots. Phase 26 takes the
escaping half. This phase takes the other three, and they share one shape: *the option is
accepted, the render succeeds, and the thing the user asked for is quietly not there.*
`hover(price foreign)` returns `rc 0`, prints no "ignoring unsupported option(s)" note, and
puts the strings `price` and `foreign` **zero times** into the 1.2 MB of HTML it produces —
because `_dash_extract_vars` never collects the variables, so they never leave Stata. On a
line plot the same option is worse than inert: it *deletes every tooltip on the figure*. The
secondary axis is computed once, from the right rows, and then never moves again: no
callback, JS or Python, touches `extra_y_ranges`, and the emitted `bokeh serve` app does not
implement a secondary axis at all — `extra_y_ranges` 0, `ytitle2` 0, `yscale2` 0,
`_compute_secondary_range` 0. And 09-07's own `mlabel()` fix, which is correct on first
render, silently disconnected line-plot labels from the interactive filter by binding them to
a `ColumnDataSource` that is not in the callback's registry. This phase makes all three real,
in both renderers, and leaves regression guards behind each one — including for the two tests
that are named after these defects and cannot currently fail.

---

## At a glance

| | |
|---|---|
| **Items** | 12 (numbered 1–12 below, exactly as handed over) |
| **Functional vs deliverable** | 8 functional · 4 deliverable (items 5, 6, 7, 12) |
| **Effort mix** | 5 small · 6 medium · 1 large (item 4) |
| **Renderers touched** | `standalone` — items 3, 5, 8, 9, 10, 12 · `server` — items 2, 4, 11 · Stata side (`dash.ado`, `dash_parse.mata`) — items 1, 6, 7 |
| **Ultraplan tasks discharged** | `09-07` — its `hover()`, secondary-axis-range and mlabel-on-lines clauses. Section **S09** (0 done / 7 partial in the audit's per-section tally). |
| **Not discharged here** | 09-07's escaping clause → **Phase 26**; the `hover(varlist)` entry in `dash.sthlp` that the task's `<verify>` requires → **Phase 30**. |
| **Depends on** | **Phase 26** (same task, same emitted-app regions — sequence them to avoid conflicting edits in `ServerAppBuilder._generate_app_source`) · **Phases 05–08** (server unification: items 2, 4 and 11 are a port into hand-written emitted strings today, and a one-line inheritance once the branch delegates to `GlyphMapper`) · **Phase 11** (it rewrites the same `_make_figure_body` hover block that items 2 and 10 edit) |
| **Unblocks** | **Phase 30** (the help entry cannot be written honestly until `hover()` works) · **Phase 31** (release gates: the conformance and parity corpora must be clean) |
| **Source of items** | Items 1–6: `REMAINING.md` Appendix B, `09-07`. Items 7–12: `REMAINING.md` Appendix C, `09-07` (14 further items). |

---

## Why this phase exists

Everything in this section is copied from `REMAINING.md`. Where a measurement was
re-confirmed against `HEAD` while writing this document, that is marked **[confirmed at
HEAD]**; nothing here contradicts the audit.

### The audit's verdict on 09-07 (Appendix A — `09-07 · PARTIAL`)

> Three of the five defects are fixed outright; `hover()` was decided but left
> inert, and the secondary-axis work is half done:
>
> - **Double escaping — fixed in both layouts.** […]
> - **Canvas text — fixed in `DashRenderer`.** […] (Not fixed in the server renderer — see below.)
> - **`mlabel()` on line plots — fixed.** `map_line` passes `sorted_source` to
>   both the glyph and `_apply_mlabel_opts` (`dash_render.py:3556`).

The three surviving clauses are this phase:

> **Remaining:**
> 1. **`hover()` is accepted and does nothing.** The decision the task demanded
>    was taken in the direction of *implement* — `dash.ado:423`/`:750` `sreturn`
>    it, it is in the option lists at `:1129`/`:1399`/`:1415`, and the renderer
>    reads it at `dash_render.py:8036` and `:10197`. But the variables it names
>    are never extracted, so they never reach the data JSON. Measured end to end
>    through Stata:
>
>    ```
>    dash scatter mpg weight, hover(price foreign) name(h1)
>    dash build, saving(hv.html) replace
>    ```
>
>    No "ignoring unsupported option(s)" note, rc 0 — and the strings `price`
>    and `foreign` occur **zero times** in the 1.2 MB of output. Add `hover` to
>    the key scan in `_dash_extract_vars` so the columns are loaded, then the
>    read at `:10197` has something to bind to. As it stands this is an
>    accepted-but-silently-dropped option, the defect class the plan exists to
>    remove. The help does not document it either, which the task's `<verify>`
>    requires.

> 4. **The filtered secondary axis still does not move.** Half the fix landed:
>    the initial range is now computed from the active view
>    (`_compute_secondary_range(_source_frame(source, self.df), ...)` at
>    `dash_render.py:9678`/`:9713`), with a comment explaining why. But the task
>    also requires *"make the filter callback update it"* — and
>    `extra_y_ranges` appears in the entire file only at `:9681` and `:9691`,
>    both at initial render. No callback, JS or Python, touches it. Move a range
>    filter on a dual-axis graph and the right-hand axis stays where it was.
> 5. **The secondary axis does not exist in server mode.** In the emitted app:
>    `extra_y_ranges` 0, `ytitle2` 0, `yscale2` 0, `_compute_secondary_range` 0.
>    `dash serve` silently draws a one-axis graph for a two-axis specification.
> 6. `test_labels_land_on_the_sorted_points` does not detect the regression it is
>    named for — it guards the mlabel column carry but passes unchanged when the
>    sorted source is swapped back. (The task's adversarial canvas-text test,
>    which I first listed as missing here, **does** exist — see Appendix C.)

**[confirmed at HEAD]** `extra_y_ranges` occurs at `dash_render.py:9681` and `:9691` and
nowhere else; `extra_x_ranges` at `:9716` and `:9726` and nowhere else. `_FILTER_JS`
(`dash_render.py:7046-7509`) contains no reference to either. Counting the region after
`class ServerAppBuilder` (`dash_render.py:12265`):

| symbol | occurrences after `:12265` |
|---|---:|
| `extra_y_ranges` / `extra_x_ranges` | 0 / 0 |
| `y_range_name` | 0 |
| `LinearAxis` | 0 |
| `_compute_secondary_range` | 0 |
| `ytitle2` / `yscale2` / `ylabel2` | 0 / 0 / 0 |
| `hover` | **1** — the comment at `:14088` |

### The extractor that drops the variables

`REMAINING.md`, Appendix B, `09-07`:

> **[func · dash.ado · S]** hover() variables are never serialized, so the
> option is accepted and does nothing through the real Stata path. Add "hover"
> to the key scan in _dash_extract_vars (or extract it in _dash_prepare_spec
> the way filter() variables are extracted at dash.ado:2177-2235) so the named
> variables reach jsonio's varlist. *Where:* `dash_parse.mata:537
> _dash_extract_vars (keys vector at :545-551 lists
> yvar/xvar/var/yvar1/yvar2/y1var/x1var/y2var/x2var/mlabel/colorvar — no
> "hover"); consumer dash.ado:2159 `mata: _dash_extract_vars(...)`; downstream […]`

**[confirmed at HEAD]** — `dash_parse.mata`, the keys vector, verbatim:

```stata
    keys    = (char(34)+"yvar"+char(34)+":",   char(34)+"xvar"+char(34)+":",  char(34)+"var"+char(34)+":",
               char(34)+"yvar1"+char(34)+":", char(34)+"yvar2"+char(34)+":",
               char(34)+"y1var"+char(34)+":", char(34)+"x1var"+char(34)+":", char(34)+"y2var"+char(34)+":", char(34)+"x2var"+char(34)+":",
               char(34)+"mlabel"+char(34)+":",
               char(34)+"colorvar"+char(34)+":")
```

Eleven keys. No `"hover"`. The renderer's end of the same pipe, `dash_render.py:8032`
`DashRenderer._collect_graph_vars`, is written *as if* the column had arrived and drops it
without a word when it has not:

```python
    @staticmethod
    def _collect_graph_vars(df: "pd.DataFrame", g_spec: dict) -> list:
        """Return deduplicated list of variable columns for a graph,
        including hover tooltip variables from graph_options.hover."""
        seen = DashRenderer._collect_plot_vars(g_spec.get("plots", []))
        hover_str = g_spec.get("graph_options", {}).get("hover", "").strip()
        for hv in hover_str.split():
            if hv and hv not in seen and hv in df.columns:
                seen.append(hv)
        return seen
```

### `hover()` on a line plot deletes the tooltips

`REMAINING.md`, Appendix C, `09-07`:

> **[func · standalone · M]** `hover()` does not merely fail to add a variable
> on a line plot — it DELETES every tooltip on the figure. `_make_figure_body`
> drops the existing HoverTools whenever extra hover vars are requested, then
> rebuilds one only for renderers whose own CDS carries every hover column;
> map_line's sorted source carries only x, y and the mlabel column, so the
> line renderer is excluded, and the fallback branch only knows histogram
> (`top`/`left`) and fit (`x`/`y`) sources. A line-only graph therefore ends
> up with zero hover tools. Fix alongside the serialization work the auditor
> already listed, otherwise `hover()` makes line plots strictly worse than not
> using it.

**[confirmed at HEAD]**, the three mechanisms in that sentence, in order:

```python
        _hover_extra_str = graph_opts.get("hover", "").strip()
        _hover_extra = _hover_extra_str.split() if _hover_extra_str else []
        _has_hover = any(isinstance(t, HoverTool) for t in fig.tools)
        if _has_hover and _hover_extra:
            # Remove existing hover tools before adding comprehensive one with extras
            fig.tools = [t for t in fig.tools if not isinstance(t, HoverTool)]
```

```python
            _hover_col_set = set(_hover_seen)
            _data_renderers = [
                _rend for _rend in fig.renderers
                if hasattr(_rend, "data_source") and
                all(c in _rend.data_source.data for c in _hover_col_set)
            ]
```

and, in `GlyphMapper.map_line` (`dash_render.py:3494`), the source that cannot satisfy that
`all(...)` test:

```python
        _cols = {xvar: source.data[xvar], yvar: source.data[yvar]}
        _mlab = (options or {}).get("mlabel", "")
        if _mlab and _mlab in source.data and _mlab not in _cols:
            _cols[_mlab] = source.data[_mlab]
        df = pd.DataFrame(_cols)
        df = df.dropna(subset=[xvar, yvar]).sort_values(xvar)
        sorted_source = ColumnDataSource(df)
```

The fallback that runs when `_data_renderers` is empty knows two source shapes —
`top`/`left` (histogram) and `x`/`y` (fit/KDE) — and a line source is neither, so
`_fb_fields` stays empty and no tool is added at all.

### The secondary range ignores every view-based restriction

`REMAINING.md`, Appendix C, `09-07`:

> **[func · standalone · M]** The secondary-axis range still ignores every
> CDSView-based restriction, so the very defect 09-07 names survives on first
> render in three shapes: (a) a LINKED dashboard's graph-level `if` qualifier,
> (b) a linked `by()` facet, (c) a per-plot `if` qualifier on the yaxis(2)
> layer. `_make_figure_body` computes the range from `_source_frame(source,
> self.df)`; when the graph is linked or faceted the source IS the full shared
> CDS and the restriction lives in a CDSView/BooleanFilter that
> `_source_frame` never sees.

**[confirmed at HEAD]** `_source_frame` (`dash_render.py:2411`) is a pure `source.data` →
`DataFrame` conversion; it takes no view and therefore cannot know about one:

```python
def _source_frame(source, fallback: "pd.DataFrame") -> "pd.DataFrame":
    """Return the rows a figure is actually drawing, as a DataFrame."""
    try:
        data = dict(source.data)
    …
```

and `_compute_secondary_range` (`dash_render.py:2433`) pads by exactly 5 % on each side, or
returns `(0.0, 1.0)` when nothing qualifies — the two facts item 12's exact-bounds assertion
rests on:

```python
    lo, hi = float(np.min(vals)), float(np.max(vals))
    span = hi - lo if hi != lo else 1.0
    return lo - padding_pct * span, hi + padding_pct * span
```

### 09-07's own mlabel fix broke the filter

`REMAINING.md`, Appendix C, `09-07`:

> **[func · standalone · M]** This task's own mlabel fix silently disconnected
> line-plot labels from the interactive filter. `map_line` builds a private
> `sorted_source` that is never added to `self.sources`, so it is not in the
> callback's `all_graph_sources`; binding the LabelSet to it means marker
> labels on a line plot no longer move when a filter widget moves (before the
> fix they were on the registered graph source and did move). The line glyph
> itself has the same defect — a `line` layer does not respond to filters at
> all in the standalone renderer, while the server registers its per-plot
> source (`graph_sources[gname].append(csrc)`) and does update it.

**[confirmed at HEAD]** the registry the callback is built from
(`dash_render.py:11881-11887`):

```python
            _graph_srcs_for_cb: list = []
            for _gsrc_name, _gsrc in self.sources.items():
                if _gsrc_name in _fc_excludes:
                    continue
                if _gsrc not in _graph_srcs_for_cb:
                    _graph_srcs_for_cb.append(_gsrc)
            _cb.args["all_graph_sources"] = _graph_srcs_for_cb
```

`sorted_source` is created inside `GlyphMapper`, never returned to `DashRenderer`, and
never inserted into `self.sources`. The server's non-faceted line branch does the
registration the standalone omits (emitted source at `dash_render.py:14096-14105`):

```python
            "            elif ptype == 'line':",
            …
            "                clean = g_df[_line_cols].dropna().sort_values(xvar) if xvar and yvar else g_df",
            "                csrc = ColumnDataSource(clean)",
            …
            "                graph_sources[gname].append(csrc)",
```

### The server's facet loop is a cut-down copy

`REMAINING.md`, Appendix C, `09-07`:

> **[func · server · M]** The server's faceted dispatch is a cut-down copy of
> the plot loop: it drops `mlabel()` entirely and does not sort a line by x.
> `dash (line y x, mlabel(v)) , by(g)` served live shows no labels and a
> zig-zag line, while the same command in `dash build` shows labels and a
> sorted line.

**[confirmed at HEAD]** the facet CDS is built from nine plot-variable keys only —
no `mlabel`, no `hover` (`dash_render.py:15101-15105`):

```python
            "            _fac_gvars = []",
            "            for p in g.get('plots', []):",
            "                for k in ('yvar', 'xvar', 'var', 'yvar1', 'yvar2', 'y1var', 'x1var', 'y2var', 'x2var'):",
```

and the non-facet plot loop's *common* mlabel block (emitted at `dash_render.py:14892-14894`,
`"            # ---- Common mlabel block (applies to all point/line plot types) ----"`) has
no facet counterpart: the string `mlabel` does not occur anywhere in `dash_render.py` after
`:14894`, while the facet dispatch begins at `:15040` and its line glyphs are emitted at
`:15147` (per-group, `_fac_fig.line(xvar_f, yvar_f, source=_fac_src, …)`) and `:15248`
(`by(, total)`, `_tot_fig.line(…)`) — with no `.sort_values(xvar)` on the facet frame.

### Two tests named after these defects that cannot fail

`REMAINING.md`, Appendix B and Appendix C:

> **[deli · standalone · S]** Strengthen
> test_labels_land_on_the_sorted_points: it does not detect the regression it
> is named for. It guards the mlabel column carry but passes unchanged when
> the sorted source is swapped back for the unsorted one. […] The fixture df
> has no NaN rows, which is the only thing that distinguishes the two sources
> (per .ultraplan/CHANGELOG.md:300-307).

> **[deli · standalone · S]** Test-suite gap for the secondary-range clause:
> `test_the_secondary_range_follows_the_graph_qualifier` asserts only `rng.end
> < full_max` on an UNLINKED graph, so it cannot fail for the linked, faceted
> or per-plot-qualifier cases, and would pass on a range computed from any
> arbitrary subset.

**[confirmed at HEAD]** the whole of the assertion in
`test/test_axis_options.py::TestSecondaryAxisRange` is:

```python
        assert rng.end < full_max, (
            f"the secondary axis spans the unfiltered data: "
            f"end={rng.end}, filtered max={sub_max}, full max={full_max}"
        )
```

and the fixture in `TestMlabelOnLines` is four complete rows:

```python
        df = pd.DataFrame({
            "y": [1.0, 2.0, 3.0, 4.0],
            "x": [40.0, 10.0, 30.0, 20.0],
            "lab": [100.0, 200.0, 300.0, 400.0],
        })
```

`.ultraplan/CHANGELOG.md:300-307` states exactly why that makes the test blind:

> The real defect was narrower — the sorted source dropped the label column, and the
> unsorted one still holds the NaN rows `map_line` discarded, so labels appeared on points
> the line does not draw.

No NaN row, no difference between the two sources, no possible failure.

### The drift that produced the phantom option

`REMAINING.md`, Appendix B, `09-07`:

> **[deli · dash.ado · S]** Delete or fix the dead second copy of the
> graph_options JSON writer in dash.ado. It has no caller and its key list is
> missing hover plus ~20 other keys that the live writer emits — exactly the
> drift shape that produced the phantom hover() read in the first place.

**[confirmed at HEAD]** `_dash_graph_opts_to_json` appears in `dash.ado` twice: the comment
at `:885` and the `program define` at `:891`. There is no call site anywhere in the package.
Its key list (`:898-901`) holds 30 keys and stops at `xscale2`; the live inline writer
(`dash.ado:1464-1471`) emits those 30 **plus 26 more** — `xsize ysize fxsize fysize scale
text hover xtick ytick xmtick ymtick xmlabel ymlabel t1title t2title b1title b2title l1title
l2title r1title r2title title2 subtitle2 nodraw play`.

---

## Epics

| epic | goal | items |
|---|---|---|
| **A — `hover()` becomes a real option** | The variables named in `hover()` leave Stata, reach both renderers, add tooltip rows, and never remove tooltips that were already there. | 1, 2, 6, 7, 10 |
| **B — The secondary axis tells the truth, always** | The right-hand/top axis matches the rows actually drawn — on first render under every view, after a filter moves, and under `dash serve`. | 3, 4, 8, 12 |
| **C — Lines and their labels stay attached to the filter** | A line layer and its marker labels respond to filter widgets in the standalone renderer and carry `mlabel()`/x-sorting in the server's facet loop. | 5, 9, 11 |

---

## User stories

### Epic A — `hover()` becomes a real option

**A-1 — As a Stata user pasting a `twoway` command, I want `hover(price foreign)` to add
those variables to the tooltip, so that I can inspect a point without re-plotting.**

- *Given* `sysuse auto` and `dash scatter mpg weight, hover(price foreign) name(h1)`,
  *when* I run `dash build, saving(hv.html) replace`, *then* the strings `price` and
  `foreign` appear in the output HTML (today: zero occurrences in 1.2 MB).
- *Given* the same dashboard open in a browser, *when* I hover a marker, *then* the tooltip
  shows rows for the x variable, the y variable, `price` and `foreign`, each labelled and
  formatted the way the other tooltip rows are.
- *Given* `hover(nosuchvar)`, *when* I run the command, *then* `dash` reports the name as
  unusable rather than silently dropping it or failing inside jsonio.

**A-2 — As a Stata user, I want `hover()` on a line plot to add a row, not to remove the
tooltip, so that the option never makes a figure worse than not using it.**

- *Given* `dash line y x, hover(v)`, *when* the figure is built, *then* the figure carries at
  least one `HoverTool` (today: zero) and its tooltips include x, y and `v`.
- *Given* `dash line y x` with no `hover()`, *when* the figure is built, *then* the tooltip
  behaviour is unchanged from HEAD.

**A-3 — As a `dash serve` operator, I want the served dashboard to show the same tooltips as
the saved one, so that "build it, then serve it" is not a behaviour change.**

- *Given* a spec whose `graph_options` carry `hover`, *when* the emitted app is built and
  executed, *then* its figures carry hover tooltips with the same fields as
  `DashRenderer`'s, in the same order.

**A-4 — As a package maintainer, I want exactly one graph-option JSON writer in `dash.ado`,
so that a reader cannot mistake a stale key list for the live one.**

- *Given* a grep for `_dash_graph_opts_to_json`, *when* the phase is done, *then* either it
  returns no `program define` at all, or the program's key list is identical to the live
  writer's and a test proves it.

### Epic B — The secondary axis tells the truth, always

**B-1 — As a dashboard viewer, I want the right-hand axis to rescale when I move a filter,
so that the two series stay comparable.**

- *Given* a dual-axis graph (`yaxis(2)` on one layer) and a range filter, *when* I move the
  slider, *then* the `y2` range end changes to match the filtered rows, padded 5 % as on
  first render.
- *Given* the filter is reset, *when* the callback runs, *then* the `y2` range returns to the
  unfiltered bounds rather than drifting.

**B-2 — As a Stata user, I want the secondary range to respect `if`, `by()` and per-plot
qualifiers on the very first render, whether or not the dashboard is linked.**

- *Given* `dash (scatter mpg weight) (scatter price weight, yaxis(2)), link(g1)` with a
  graph-level `if weight < 2500`, *when* the figure is built, *then* `fig.extra_y_ranges["y2"]`
  equals `(lo - 0.05*span, hi + 0.05*span)` over the **qualified** `price` values.
- *Given* the same with `by(foreign)` under `link()`, *when* each facet figure is built,
  *then* each facet's `y2` range reflects only that facet's rows.
- *Given* a per-plot qualifier on the `yaxis(2)` layer, *when* the figure is built, *then*
  the `y2` range reflects only the rows that layer draws.

**B-3 — As a `dash serve` operator, I want `yaxis(2)` either to work or to be reported as
unsupported, so that I am never shown a one-axis graph for a two-axis specification.**

- *Given* a two-axis spec, *when* it is served, *then* either the served figure carries
  `extra_y_ranges["y2"]` and a right-hand axis, *or* `dash serve` reports
  `yaxis(2)`/`xaxis(2)`/`ytitle2`/`yscale2`/`ylabel2`/`xtitle2`/`xscale2`/`xlabel2` as
  unsupported in that mode, through the existing unsupported-option report.
- *Given* the mode-parity corpus, *when* it runs, *then* the difference is either absent or
  listed explicitly in `ALLOWED` with the reason.

**B-4 — As a package maintainer, I want the secondary-range test to pin exact bounds, so that
a range computed from the wrong subset cannot pass.**

- *Given* the current implementation, *when* the strengthened test runs, *then* it passes.
- *Given* the pre-09-07 implementation (range from `self.df`), *when* it runs, *then* it
  fails — in the unlinked, linked, faceted and per-plot-qualifier cases alike.

### Epic C — Lines and their labels stay attached to the filter

**C-1 — As a dashboard viewer, I want a line layer and its marker labels to respond to filter
widgets, so that filtering a line chart does something.**

- *Given* `dash line y x, mlabel(v)` with a filter widget, *when* I filter, *then* the drawn
  line covers only the surviving rows and the labels move with it.
- *Given* the filtered rows, *when* the line is redrawn, *then* it is still sorted by x
  (filtering must not reintroduce the zig-zag).

**C-2 — As a `dash serve` operator, I want a faceted line to look the same served as built,
so that `by()` is not a second renderer.**

- *Given* `dash (line y x, mlabel(v)) , by(g)`, *when* it is served, *then* each facet shows
  marker labels and an x-sorted line, as `dash build` does.
- *Given* `by(, total)`, *when* it is served, *then* the total panel behaves the same way.

**C-3 — As a package maintainer, I want the mlabel test to fail when the sorted source is
swapped back, so that the guard is real.**

- *Given* a fixture with a NaN row, *when* labels are built from the unsorted source,
  *then* the test fails because a label exists for a point the line does not draw.

---

## Business requirements

| id | requirement | testable as |
|---|---|---|
| **BR-27.1** | `hover(varlist)` must change what the user sees. The named variables reach the browser through the real Stata path and appear as tooltip rows. | cscript asserts `price`/`foreign` present in the built HTML; pytest asserts tooltip fields |
| **BR-27.2** | `hover()` must never reduce the information on a figure. A figure that had tooltips before `hover()` still has them after. | pytest on a line-only figure: `HoverTool` count ≥ 1 with and without `hover()` |
| **BR-27.3** | A variable name in `hover()` that is not a usable variable must be reported, not silently dropped and not passed into jsonio. | cscript asserting a clear message and a non-crashing return |
| **BR-27.4** | The saved dashboard and the served dashboard must show the same tooltips for the same command. | `test/test_mode_parity.py` case |
| **BR-27.5** | `dash.ado` must contain exactly one live graph-option key list; no dead copy may disagree with it. | static test over `dash.ado` |
| **BR-27.6** | On first render, a secondary axis must span exactly the rows the figure draws, under a graph-level `if`, a linked dashboard, a `by()` facet and a per-plot qualifier. | four exact-bounds pytest cases |
| **BR-27.7** | Moving a filter must update the secondary axis in the same direction and by the same rule as first render. | callback-wiring test + JS recompute test |
| **BR-27.8** | `dash serve` must not silently render a two-axis specification as a one-axis figure. Either it supports it, or it reports it. | server pytest, or unsupported-report test |
| **BR-27.9** | A `line` layer and its `mlabel()` labels must respond to filter widgets in both renderers. | pytest that the line's source is in the callback registry |
| **BR-27.10** | A faceted line under `dash serve` must carry `mlabel()` and x-sorting. | server facet pytest + parity case |
| **BR-27.11** | Every test this phase touches or adds must be proven able to fail (rule 4, rule 8). | the mutation column of the test plan |
| **BR-27.12** | No change here may enlarge the data payload without bound: hover columns are added to the serialized varlist only when named and only once. | dedup assertion + payload-size test |

---

## Technical requirements

### Epic A

**TR-27.1 — Serialize `hover()` variables (item 1).**
Add `char(34)+"hover"+char(34)+":"` to the `keys` vector in `_dash_extract_vars`
(`dash_parse.mata:537`, vector at `:545-551`, eleven keys today:
`yvar xvar var yvar1 yvar2 y1var x1var y2var x2var mlabel colorvar`). Unlike every existing
key, `hover`'s value is a **space-separated varlist**, not one name; the extractor appends
the raw value to a space-separated `varlist`, and the consumer at `dash.ado:2159`
(`mata: _dash_extract_vars(...)`, then `foreach v of local gvars`) iterates words, so a
multi-word value degrades correctly into individual names. The alternative the audit names
is to extract it in `_dash_prepare_spec` the way `filter()` variables are extracted at
`dash.ado:2177-2235`; either is acceptable, but only one, and the chosen one must be the
only one.

**TR-27.2 — Validate the names before they reach jsonio (item 1, BR-27.3).**
The `gvars` loop at `dash.ado:2159-2163` adds names to `all_vars` with no
`capture confirm variable`, while the sibling `qvars` loop immediately below it does confirm.
Since `hover()` is free-text user input, its tokens must be confirmed the same way before
they enter the jsonio varlist (CLAUDE.md rule 16: harden all data inputs). A token that is
not a variable is reported through the existing unsupported/ignored-option channel, never
silently dropped.

**TR-27.3 — Keep the renderer-side guard, but make it audible (item 1).**
`DashRenderer._collect_graph_vars` (`dash_render.py:8032`) drops a hover name when
`hv not in df.columns`. Retain the guard — it is the last line of defence against a bad name
reaching a Bokeh field spec — but log at debug/info level when it fires (CLAUDE.md rule 14),
so the next silent drop is visible in the render log rather than invisible in the HTML.
`test/test_render_log_clean.cscript` constrains what may appear on a clean run; the message
must be below that threshold for valid input.

**TR-27.4 — Port the extra-tooltip handling into the emitted app (item 2).**
`ServerAppBuilder._generate_app_source` (`dash_render.py:12740`) emits a hover tool inside the
per-plot dispatch around `:14088-14093`; the string `hover` occurs exactly once after
`class ServerAppBuilder` (`:12265`) and it is that comment. Port
`DashRenderer._make_figure_body`'s hover block (`:10197-10261`), including
`_hover_extra_str = graph_opts.get("hover", "")`, the per-column `_hover_row` construction,
the `formatters` dict and the renderer restriction. If Phases 05–08 have already made the
branch delegate to `_DASH_MAPPER`, the port reduces to passing `graph_opts` through; if not,
the emitted strings carry the logic. Do not fork the field-spec rules — the tooltip label
comes from `_axis_label`, the date/format spec from the same helpers Phase 11 fixes.

**TR-27.5 — Stop `hover()` deleting tooltips (item 10).**
Three coordinated changes in `dash_render.py`:
1. `GlyphMapper.map_line` `_cols` (`:3520-3527`) must carry the graph's hover columns in
   addition to `xvar`, `yvar` and the `mlabel` column, so the sorted source satisfies the
   `all(c in _rend.data_source.data …)` test at `:10255-10259`. The hover varlist must be
   passed into the mapper (it lives in `graph_opts`, not in the per-plot `options`).
2. The unconditional strip at `:10202`
   (`fig.tools = [t for t in fig.tools if not isinstance(t, HoverTool)]`) must not run until
   a replacement tool has been constructed — build first, swap second, so no path can end
   with zero `HoverTool`s where there was one.
3. The fallback branch (`:10262-10298`) knows only `top`/`left` and `x`/`y` sources; extend
   it to the general case — build the tooltip from the intersection of the requested columns
   and the renderer's own CDS columns — so a source shape nobody anticipated degrades to a
   partial tooltip rather than to none.
   *Note:* Phase 11 rewrites the neighbouring lines of this same block (the duplicate
   `GlyphMapper._hover_tool`, the date-kind picture, empty row labels). Sequence Phase 11
   first and rebase.

**TR-27.6 — Remove the dead writer (item 6).**
`dash.ado:891 program define _dash_graph_opts_to_json` has zero call sites (the only other
occurrence is its comment at `:885`). Its key list (`:898-901`) holds 30 keys and stops at
`xscale2`. The live writer is the inline loop at `dash.ado:1464-1471`, whose list adds
`xsize ysize fxsize fysize scale text hover xtick ytick xmtick ymtick xmlabel ymlabel
t1title t2title b1title b2title l1title l2title r1title r2title title2 subtitle2 nodraw play`
— 25 more keys, `hover` among them. Preferred resolution: delete the program. If it is kept
for a future caller, its list must be generated from, or asserted equal to, the live list.

### Epic B

**TR-27.7 — Thread the secondary ranges into the filter callback (item 3).**
`fig.extra_y_ranges["y2"]` and `fig.extra_x_ranges["x2"]` are created at
`dash_render.py:9681` / `:9716` inside `_make_figure_body` (`:9495`) and are the only two
occurrences of each symbol in the file. Register them per graph as the sources are
registered, and add them to the three `CustomJS` args blocks at `:7674`, `:7769` and `:7851`
(the callbacks whose `code=_FILTER_JS` is at `:7701`, `:7782`, `:7864`) alongside
`all_graph_sources` (built at `:11881-11887`). Pass, as a JSON string in the same style the
file already uses for `filter_specs_json` / `kpi_config_json`, a per-graph map of which
columns are assigned to axis 2:
`{gname: {"y2": [yvar…], "x2": [xvar…]}}`, derived from
`str(p["options"].get("yaxis","1")).strip() == "2"`.

**TR-27.8 — Recompute the range in `_FILTER_JS` (item 3).**
`_FILTER_JS` (`dash_render.py:7046-7509`) today references neither range. Add a recompute
that mirrors `_compute_secondary_range` (`:2433`) exactly: take the numeric, non-missing
values of each axis-2 column over the **filtered** rows; `lo = min`, `hi = max`;
`span = hi - lo` or `1.0` when `hi == lo`; write `range.start = lo - 0.05*span`,
`range.end = hi + 0.05*span`; when no value qualifies, write `(0.0, 1.0)`. The 5 % padding
and the `(0.0, 1.0)` empty case are not free choices — they are what the Python helper does,
and first render and post-filter render must agree.

**TR-27.9 — Intersect the views before computing the range (item 8).**
Both secondary blocks call
`_compute_secondary_range(_source_frame(source, self.df), plots, …)` — the y2 block at
`~:9679`, the x2 block at `~:9714`. `_source_frame` (`:2411`) sees only `source.data`.
Introduce a view-aware frame helper that applies, in order, any `facet_view`
(the `_make_figure_body` parameter at `:9499`; the linked-facet `BooleanFilter` is registered
at `:11475`) and any `_plot_view` (`~:9956`, its `BooleanFilter` at `:9991`), reading the
filter's `booleans`/`indices` and selecting those rows from the frame, then pass the result
to `_compute_secondary_range` for **both** blocks. Unknown filter types must degrade to the
unrestricted frame rather than raising — a dashboard must still render.

**TR-27.10 — Secondary axis under `dash serve` (item 4).**
The emitted app contains none of `extra_y_ranges`, `extra_x_ranges`, `y_range_name`,
`LinearAxis`, `_compute_secondary_range`, `ytitle2`, `yscale2`, `ylabel2` (all 0 after
`:12265`). Two acceptable outcomes, chosen explicitly and recorded:
- **(a) Implement.** Mirror `DashRenderer._make_figure_body:9664-9745`: `Range1d` from the
  active rows; `LinearAxis`/`LogAxis` chosen by `_parse_scale_opt(graph_opts["yscale2"])`
  with `y_range_name="y2"` and `axis_label=graph_opts["ytitle2"]`; `fig.add_layout(_y2_ax,
  "right")` (x2: `"above"`); `flipped = True` for a reversed scale; `FixedTicker` +
  `CustomJSTickFormatter` for `ylabel2()`/`xlabel2()`; `major_label_orientation` from
  `_parse_axis_angle`. Each axis-2 glyph must be drawn with `y_range_name='y2'`. This is
  materially cheaper after Phases 05–08, and it overlaps Phase 16 (the axis grammar's server
  port) — coordinate the two.
- **(b) Declare.** Report `yaxis(2)`, `xaxis(2)`, `ytitle2`, `xtitle2`, `ylabel2`, `xlabel2`,
  `yscale2`, `xscale2` as unsupported under `dash serve` through the existing
  unsupported-option channel, and list the difference in `test/test_mode_parity.py`'s
  `ALLOWED` with that reason. Silence is not an outcome.

**TR-27.11 — Make the secondary-range test exact (item 12).**
`test/test_axis_options.py::TestSecondaryAxisRange::test_the_secondary_range_follows_the_graph_qualifier`
(`:851-885`) asserts only `rng.end < full_max`. Replace with equality on both ends —
`lo - 0.05*span` and `hi + 0.05*span` computed from the expected subset — and parametrise
over four cases: unlinked (today's), `build_options["link"]="g1"`, `graph_options["by"]`
with `link`, and a per-plot `if_expr` on the `yaxis(2)` layer. Use `pytest.approx`; do not
loosen to an inequality.

### Epic C

**TR-27.12 — Register the line's sorted source (item 9).**
`GlyphMapper.map_line` (`:3494`) creates `sorted_source` at `:3527` and binds the `LabelSet`
to it at `:3556` (`self._apply_mlabel_opts(fig, sorted_source, options, xvar, yvar)`); the
callback registry is `self.sources`, consumed at `:11881-11887`; `_FILTER_JS` updates only
`all_graph_sources` and `source` (`:7113`, `:7170-7175`). Register the sorted source in the
renderer's per-graph source list **together with its row identities**, so
`_view_filter_args` (`:11890`) can rebuild the matching `BooleanFilter` after the source is
shortened. The server precedent is `graph_sources[gname].append(csrc)` at the emitted line
branch (`:14096-14105`). Because a line's row **order** is load-bearing, the JS rebuild must
re-sort the surviving rows by x after filtering — subsetting alone reintroduces the zig-zag
the sort exists to prevent. The alternative the audit allows — rebuilding the sorted frame
inside `_FILTER_JS` — carries the same ordering obligation.

**TR-27.13 — mlabel and x-sorting in the server's facet loop (item 11).**
In the emitted source inside `ServerAppBuilder._generate_app_source`, the per-facet line is
drawn at `dash_render.py:15147`
(`_fac_fig.line(xvar_f, yvar_f, source=_fac_src, …)`) and the `by(, total)` line at `:15248`
(`_tot_fig.line(…)`); in the generated file these are the `elif ptype == 'line'` branches at
lines 8713 and 8814. Neither sorts the facet frame; neither draws labels. The facet CDS is
built from `_fac_gvars` (`:15101-15105`), which collects only
`yvar xvar var yvar1 yvar2 y1var x1var y2var x2var` — never `mlabel`, never `hover`.
Required: (a) add the mlabel and hover columns to `_fac_gvars`; (b) sort the facet frame by x
for line types, as the non-facet branch does
(`clean = g_df[_line_cols].dropna().sort_values(xvar)`); (c) apply the mlabel block the
non-facet loop has at emitted `:14892-14894`. The preferred form — after Phases 05–08 — is a
single `_DASH_MAPPER` call per facet, which makes (a)–(c) inherited rather than copied.

**TR-27.14 — Make the mlabel test able to fail (item 5).**
`test/test_axis_options.py::TestMlabelOnLines::test_labels_land_on_the_sorted_points`
(`:889-910`) uses a four-row fixture with no NaN. Per `.ultraplan/CHANGELOG.md:300-307`, the
NaN rows are the *only* thing that distinguishes the sorted source from the unsorted one. Add
a row whose `x` or `y` is NaN and whose `lab` is distinctive, and assert that label is
**absent** from the `LabelSet` source, in addition to the existing pairing assertion.

---

## Work items

Twelve items, numbered exactly as handed over. Tags are `[kind · renderer · effort]`.

---

**1. [functional · stata · small] — `hover()` variables are never serialized.**

> hover() variables are never serialized, so the option is accepted and does nothing through
> the real Stata path. Add "hover" to the key scan in `_dash_extract_vars` (or extract it in
> `_dash_prepare_spec` the way filter() variables are extracted at dash.ado:2177-2235) so the
> named variables reach jsonio's varlist.

*Where:* `dash_parse.mata:537` `_dash_extract_vars` (keys vector at `:545-551` lists
`yvar`/`xvar`/`var`/`yvar1`/`yvar2`/`y1var`/`x1var`/`y2var`/`x2var`/`mlabel`/`colorvar` — no
`"hover"`); consumer `dash.ado:2159` `mata: _dash_extract_vars(...)`; downstream reader
`dash_render.py:8032` `DashRenderer._collect_graph_vars`, whose `hv in df.columns` test
silently drops them.
*Evidence:* Appendix A item 1 — `dash scatter mpg weight, hover(price foreign)` +
`dash build` → rc 0, no note, `price` and `foreign` occur **zero times** in 1.2 MB of output.
*Source:* Appendix B. *Requirements:* TR-27.1, TR-27.2, TR-27.3.

---

**2. [functional · server · medium] — `ServerAppBuilder` ignores `graph_options["hover"]`.**

> ServerAppBuilder ignores graph_options["hover"] entirely — add the extra-tooltip handling
> that DashRenderer has at dash_render.py:10197-10261 to the emitted app source.

*Where:* `dash_render.py` `ServerAppBuilder._generate_app_source` (`:12740`) — the emitted
hover tool is built inside the per-plot dispatch around `:14088-14093`; the only occurrence
of the string `"hover"` after `class ServerAppBuilder` (`:12265`) is a comment at `:14088`.
Port the logic from `DashRenderer._make_figure_body` `:10197-10261`
(`_hover_extra_str = graph_opts.get("hover", "")`).
*Evidence:* occurrence count after `:12265` = 1, and it is a comment.
*Source:* Appendix B. *Requirements:* TR-27.4.

---

**3. [functional · standalone · medium] — The filter callback never updates the secondary range.**

> Make the filter callback update the secondary-axis range. extra_y_ranges["y2"] /
> extra_x_ranges["x2"] are static Range1d models that no callback ever touches, so an
> interactive filter leaves the right-hand axis spanning the unfiltered data — the exact
> defect 09-07 names, for the interactive case.

*Where:* `dash_render.py:9681` and `:9716` create `fig.extra_y_ranges["y2"]` /
`extra_x_ranges["x2"]` in `_make_figure_body` (`:9495`); `_FILTER_JS`
(`dash_render.py:7046-7509`) has no reference to them; the `CustomJS` args blocks at `:7674`,
`:7769`, `:7851` do not pass them. Needs the `Range1d` models threaded into the callback args
(alongside `all_graph_sources`) and a recompute in `_FILTER_JS` mirroring
`_compute_secondary_range` (`:2433`).
*Evidence:* Appendix A item 4 — "`extra_y_ranges` appears in the entire file only at `:9681`
and `:9691`, both at initial render. No callback, JS or Python, touches it."
*Source:* Appendix B. *Requirements:* TR-27.7, TR-27.8.

---

**4. [functional · server · large] — No secondary axis exists in server mode.**

> ServerAppBuilder has no secondary-axis support at all, so neither the active-view range nor
> the filter update exists there. Either implement yaxis(2)/xaxis(2) in the emitted app or
> report the option as unsupported under `dash serve`.

*Where:* `dash_render.py` `ServerAppBuilder._generate_app_source` (`:12740`) — no emitted line
contains `extra_y_ranges`, `y_range_name` or `LinearAxis`; compare
`DashRenderer._make_figure_body` `:9664-9745`.
*Evidence:* Appendix A item 5 — in the emitted app, `extra_y_ranges` 0, `ytitle2` 0,
`yscale2` 0, `_compute_secondary_range` 0; "`dash serve` silently draws a one-axis graph for a
two-axis specification."
*Source:* Appendix B. *Requirements:* TR-27.10.

---

**5. [deliverable · standalone · small] — Strengthen `test_labels_land_on_the_sorted_points`.**

> Strengthen test_labels_land_on_the_sorted_points: it does not detect the regression it is
> named for. It guards the mlabel column carry but passes unchanged when the sorted source is
> swapped back for the unsorted one.

*Where:* `test/test_axis_options.py::TestMlabelOnLines::test_labels_land_on_the_sorted_points`
(`:889-910`). The fixture df has no NaN rows, which is the only thing that distinguishes the
two sources (per `.ultraplan/CHANGELOG.md:300-307`). Add a NaN row and assert its label is
absent.
*Evidence:* Appendix A item 6; the CHANGELOG's own statement of the narrowed defect.
*Source:* Appendix B. *Requirements:* TR-27.14.

---

**6. [deliverable · stata · small] — Delete or fix the dead `graph_options` JSON writer.**

> Delete or fix the dead second copy of the graph_options JSON writer in dash.ado. It has no
> caller and its key list is missing hover plus ~20 other keys that the live writer emits —
> exactly the drift shape that produced the phantom hover() read in the first place.

*Where:* `dash.ado:891` `program define _dash_graph_opts_to_json` (key list at `:898-901`
stops at `xscale2`); the live writer is the inline loop at `dash.ado:1464-1471`, whose list
includes `hover`, `xsize`, `ysize`, `scale`, `text`, `xtick`, `ytick`, the `t1title` family,
`title2` and `subtitle2`.
*Evidence:* zero call sites at HEAD; 30 keys in the dead copy against 55 in the live loop.
*Source:* Appendix B. *Requirements:* TR-27.6.

---

**7. [deliverable · stata · small] — No regression test exists for the `hover()` gap.**

> No regression test exists for the hover() serialization gap, on either side. The auditor's
> deliverable list names only the missing dash.sthlp entry. Per CLAUDE.md #8 the test comes
> before the fix: add a Stata cscript (no .cscript mentions hover at all) asserting that
> `hover(price)` puts `price` into the serialized data, and a pytest that fails when "hover"
> is absent from the `keys` vector in `_dash_extract_vars`.

*Where:* `test/` (new cscript, e.g. `test_hover.cscript`, following
`test/test_e2e_single.cscript`'s shape) and a pytest beside `test/test_axis_options.py`;
target symbol `dash_parse.mata:537` `_dash_extract_vars` keys vector at `:545-551`; consumer
`dash.ado:2159`.
*Evidence:* confirmed at HEAD — `grep -l hover test/*.cscript` matches **0** of the 25
cscripts.
*Source:* Appendix C. *Requirements:* TR-27.1, and the Epic A test plan.

---

**8. [functional · standalone · medium] — The secondary range ignores every CDSView restriction.**

> The secondary-axis range still ignores every CDSView-based restriction, so the very defect
> 09-07 names survives on first render in three shapes: (a) a LINKED dashboard's graph-level
> `if` qualifier, (b) a linked `by()` facet, (c) a per-plot `if` qualifier on the yaxis(2)
> layer. `_make_figure_body` computes the range from `_source_frame(source, self.df)`; when
> the graph is linked or faceted the source IS the full shared CDS and the restriction lives
> in a CDSView/BooleanFilter that `_source_frame` never sees. Fix: intersect
> `facet_view`/`_plot_view` (and any registered view filter) with the frame before calling
> `_compute_secondary_range`, for both the y2 and x2 blocks.

*Where:* `dash_render.py`:
`_compute_secondary_range(_source_frame(source, self.df), plots, "yaxis", "yvar", 2)` in
`DashRenderer._make_figure_body` (y2 block `~:9679`, x2 block `~:9714`); `_source_frame`
(`:2411`); the views that are ignored are the `facet_view` parameter of `_make_figure_body`
(`:9499`) and `_plot_view` (`~:9956`); the linked-facet `BooleanFilter` is registered at
`:11475` and the per-plot one at `:9991`.
*Source:* Appendix C. *Requirements:* TR-27.9.

---

**9. [functional · standalone · medium] — The mlabel fix disconnected line labels from the filter.**

> This task's own mlabel fix silently disconnected line-plot labels from the interactive
> filter. `map_line` builds a private `sorted_source` that is never added to `self.sources`,
> so it is not in the callback's `all_graph_sources`; binding the LabelSet to it means marker
> labels on a line plot no longer move when a filter widget moves (before the fix they were on
> the registered graph source and did move). The line glyph itself has the same defect — a
> `line` layer does not respond to filters at all in the standalone renderer, while the server
> registers its per-plot source (`graph_sources[gname].append(csrc)`) and does update it. Fix:
> register the sorted source (and its row identities, so `view_filters` can be rebuilt) or
> rebuild it inside `_FILTER_JS`.

*Where:* `dash_render.py`: `GlyphMapper.map_line` (`:3494`) — `sorted_source =
ColumnDataSource(df)` (`:3527`) and `self._apply_mlabel_opts(fig, sorted_source, ...)`
(`:3556`); the registry the callback uses is `self.sources` consumed at `:11881-11887`
(`_cb.args["all_graph_sources"]`); `_FILTER_JS` updates only `all_graph_sources` and `source`
(`:7113`, `:7170-7175`). Server precedent that does it right: emitted line branch at
`:14096-14105`.
*Source:* Appendix C. *Requirements:* TR-27.12.

---

**10. [functional · standalone · medium] — `hover()` deletes every tooltip on a line plot.**

> `hover()` does not merely fail to add a variable on a line plot — it DELETES every tooltip
> on the figure. `_make_figure_body` drops the existing HoverTools whenever extra hover vars
> are requested, then rebuilds one only for renderers whose own CDS carries every hover
> column; map_line's sorted source carries only x, y and the mlabel column, so the line
> renderer is excluded, and the fallback branch only knows histogram (`top`/`left`) and fit
> (`x`/`y`) sources. A line-only graph therefore ends up with zero hover tools. Fix alongside
> the serialization work the auditor already listed, otherwise `hover()` makes line plots
> strictly worse than not using it.

*Where:* `dash_render.py`: `DashRenderer._make_figure_body` hover block `:10197-10290` —
`fig.tools = [t for t in fig.tools if not isinstance(t, HoverTool)]` (`:10202`), the
`_data_renderers` all-columns test (`:10255-10259`), and the fallback that handles only
`top`/`left` and `x`/`y` sources (`:10262-10298`). Source of the missing columns:
`map_line`'s `_cols` (`:3520-3527`).
*Source:* Appendix C. *Requirements:* TR-27.5.

---

**11. [functional · server · medium] — The server's faceted dispatch drops mlabel and the x-sort.**

> The server's faceted dispatch is a cut-down copy of the plot loop: it drops `mlabel()`
> entirely and does not sort a line by x. `dash (line y x, mlabel(v)) , by(g)` served live
> shows no labels and a zig-zag line, while the same command in `dash build` shows labels and
> a sorted line. Both the per-group branch and the `by(, total)` branch need the real mapper
> call (or the mlabel + sort logic ported into them).

*Where:* `dash_render.py`, emitted source inside `ServerAppBuilder._generate_app_source`: the
per-facet dispatch (`_fac_fig.line(xvar_f, yvar_f, source=_fac_src, ...)`) and the
`by(, total)` dispatch — in the generated file these are the `elif ptype == 'line'` branches
that use `_fac_fig`/`_tot_fig` (generated app lines 8713 and 8814; in `dash_render.py` they
are the emitted string block that follows `_fac_parts`/`_fac_title` at `:15096-15130`). The
non-faceted branch that does it correctly is `:14096-14105`. Related: the facet CDS is built
from `_fac_gvars`, which collects only
`yvar`/`xvar`/`var`/`yvar1`/`yvar2`/`y1var`/`x1var`/`y2var`/`x2var` — never `mlabel` or
`hover` columns (`:15101-15105`).
*Evidence, confirmed at HEAD:* the emitted facet line is at `:15147` and the `by(, total)`
line at `:15248`; the string `mlabel` does not occur in `dash_render.py` after `:14894`, the
last line of the non-facet loop's common mlabel block.
*Source:* Appendix C. *Requirements:* TR-27.13.

---

**12. [deliverable · standalone · small] — The secondary-range test cannot fail for the cases that matter.**

> Test-suite gap for the secondary-range clause:
> `test_the_secondary_range_follows_the_graph_qualifier` asserts only `rng.end < full_max` on
> an UNLINKED graph, so it cannot fail for the linked, faceted or per-plot-qualifier cases,
> and would pass on a range computed from any arbitrary subset. Replace the inequality with
> the exact expected bounds (`lo - 0.05*span`, `hi + 0.05*span`) and add three cases:
> `build_options["link"]="g1"`, `graph_options["by"]` with link, and a per-plot `if_expr` on
> the yaxis(2) layer.

*Where:*
`test/test_axis_options.py::TestSecondaryAxisRange::test_the_secondary_range_follows_the_graph_qualifier`
(`:851-885`).
*Source:* Appendix C. *Requirements:* TR-27.11.

---

## Test plan

Rule 8 governs the order: **the failing test is written and shown to fail before the fix.**
Rule 4 governs the coverage: every function this phase adds or changes gets a unit test. The
mutation column is not optional — this repository has a documented history of tests that
passed against broken implementations, and two of them are items in this very phase
(items 5 and 12).

### Epic A — `hover()`

| # | test | file | kind | must fail before the fix because | mutation that must kill it afterwards |
|---|---|---|---|---|---|
| A-T1 | `test_hover_is_in_the_extract_keys` — read `dash_parse.mata`, assert `"hover"` appears in the `_dash_extract_vars` keys vector | `test/test_axis_options.py` (beside the existing `TestHoverOptionIsRealOrGone`) | unit, static | the vector lists 11 keys and `hover` is not among them | delete the key from the vector |
| A-T2 | `hover(price)` puts `price` into the serialized data | **new** `test/test_hover.cscript` (shape of `test/test_e2e_single.cscript`) | cscript / e2e | `price` occurs zero times in the built HTML | remove the key again; the cscript must report a non-zero rc |
| A-T3 | `test_hover_columns_become_tooltip_rows` — spec with `graph_options["hover"]`, assert the figure's `HoverTool.tooltips` contain a row per hover var, labelled via `_axis_label` | `test/test_axis_options.py` | unit | the column is absent from `df`, so `_collect_graph_vars` drops it | drop the hover loop in `_collect_graph_vars` |
| A-T4 | `test_hover_on_a_line_plot_keeps_a_tooltip` — line-only figure + `hover(v)`; assert ≥ 1 `HoverTool` and that its fields include x, y and `v` | `test/test_axis_options.py` | unit, regression for item 10 | the figure ends with **zero** hover tools | restore the unconditional `fig.tools = [...]` strip at `:10202` |
| A-T5 | `test_hover_survives_a_source_shape_the_fallback_does_not_know` — a source that is neither `top`/`left` nor `x`/`y` | `test/test_axis_options.py` | unit | the fallback produces no fields | narrow the fallback back to the two known shapes |
| A-T6 | `test_server_hover_matches_standalone` — build via `ServerAppBuilder`, exec the emitted module, compare tooltip fields | `test/test_mode_parity.py` (harness `_server_figures`, `:94-127`) | integration / parity | the emitted app has no hover handling at all | delete the ported block from the emitted source |
| A-T7 | `test_a_bad_hover_name_is_reported` — `hover(nosuchvar)` | `test/test_hover.cscript` | cscript, security (rule 16) | today the name is dropped in silence | remove the `capture confirm variable` guard |
| A-T8 | `test_dash_ado_has_one_graph_option_writer` — parse both key lists from `dash.ado`; assert the dead program is gone, or the lists are equal | `test/test_options.py` or `test/test_cscript_hygiene.py` | unit, static | the dead list is 25 keys short | re-add the stale program with its truncated list |

`test/test_axis_options.py::TestHoverOptionIsRealOrGone::test_dash_ado_declares_it_or_the_renderer_does_not_read_it`
already exists and asserts declare/read symmetry; it stays, and A-T1 extends the same class to
the *serialize* half of the pipe, which is the half that is broken.

### Epic B — the secondary axis

| # | test | file | kind | must fail before the fix because | mutation that must kill it afterwards |
|---|---|---|---|---|---|
| B-T1 | `test_the_secondary_range_follows_the_graph_qualifier`, rewritten to exact bounds `(lo - 0.05*span, hi + 0.05*span)` via `pytest.approx` | `test/test_axis_options.py:851-885` | unit, item 12 | it asserts only `rng.end < full_max` — true of almost any subset | compute the range from `self.df`; the exact-bounds form dies, the inequality form does not |
| B-T2 | three added cases: `build_options["link"]="g1"`; `graph_options["by"]` with `link`; a per-plot `if_expr` on the `yaxis(2)` layer | same class | unit, items 8 + 12 | the shared CDS carries every row, so the range spans the unfiltered data | remove the view intersection from either the y2 or the x2 block |
| B-T3 | `test_the_x2_range_follows_the_same_rule` — the x2 block is a separate code path and must be covered separately | `test/test_dual_axis.py` | unit, item 8 | `:9714` has the same defect as `:9679` | fix only the y2 block |
| B-T4 | `test_the_filter_callback_carries_the_secondary_ranges` — assert the `Range1d` models and the axis-2 column map are in `_cb.args` for all three callback shapes | `test/test_filters.py` | unit, item 3 | the args blocks at `:7674`/`:7769`/`:7851` carry no such key | drop the arg from any one of the three blocks |
| B-T5 | `test_filter_js_recomputes_the_secondary_range` — assert `_FILTER_JS` computes and assigns `start`/`end` on the passed range, with the 5 % pad and the `(0,1)` empty case | `test/test_filters.py` | unit, item 3 | `_FILTER_JS` contains no reference to either range | change the JS pad from `0.05` to `0.10`; the assertion on exact bounds must die |
| B-T6 | `test_served_dual_axis_is_implemented_or_declared` — build + exec the emitted app; either `fig.extra_y_ranges["y2"]` exists, or the unsupported report names the eight secondary keys | `test/test_dual_axis.py` + `test/test_unsupported_report_is_true.py` | integration, item 4 | the served figure has neither the axis nor a report | remove the axis (or the report entry) |
| B-T7 | parity case for a dual-axis spec | `test/test_mode_parity.py` | parity | the two modes disagree and nothing says so | remove the `ALLOWED` entry without implementing |

### Epic C — lines, labels and the filter

| # | test | file | kind | must fail before the fix because | mutation that must kill it afterwards |
|---|---|---|---|---|---|
| C-T1 | `test_labels_land_on_the_sorted_points`, with a NaN row added and an assertion that its label is **absent** | `test/test_axis_options.py:889-910` | unit, item 5 | the four-row fixture has no NaN, so both sources look identical | bind `_apply_mlabel_opts` back to the unsorted `source`; the strengthened test dies, today's does not |
| C-T2 | `test_a_line_source_is_in_the_callback_registry` — assert `map_line`'s sorted source appears in `_cb.args["all_graph_sources"]` | `test/test_linking_filters.py` or `test/test_filters.py` | unit, item 9 | `sorted_source` is never added to `self.sources` | revert the registration |
| C-T3 | `test_a_filtered_line_stays_sorted` — apply the filter transform to a line source and assert x is non-decreasing afterwards | `test/test_filters.py` | unit, item 9 | filtering does not touch the line source at all | drop the re-sort from the JS rebuild |
| C-T4 | `test_view_filters_cover_the_line_source` — assert `_view_filter_args` (`:11890`) produces an entry for the registered sorted source | `test/test_linking_filters.py` | unit, item 9 | there is no such source to cover | register the source without its row identities |
| C-T5 | `test_served_facet_line_is_sorted_and_labelled` — build + exec, then assert each facet figure has a `LabelSet` and an x-sorted source | `test/test_layout_facets.py` (or a new `test/test_server_facets.py`) | integration, item 11 | the facet branch neither sorts nor labels | remove `.sort_values(xvar)` from the facet branch; remove the facet mlabel block |
| C-T6 | `test_by_total_facet_line_matches` — the `by(, total)` branch specifically | same file | integration, item 11 | `:15248` is a second copy with the same omissions | fix only the per-group branch |
| C-T7 | parity case: `(line y x, mlabel(v)) , by(g)` | `test/test_mode_parity.py` | parity | the two modes draw different figures | revert either side |

### Suite-level obligations

- Run the **full** pytest suite (82 test modules) and the full cscript suite (25 scripts,
  `arch -arm64` from `test/`) before committing; a skip is not a pass.
- `test/test_filter_payload_size.py` must still pass after item 1 (extra serialized columns)
  and item 9 (an extra registered source) — both enlarge what the callback carries.
- `test/test_render_log_clean.cscript` must still pass with TR-27.3's new log line on valid
  input.
- Set `$dash_nobrowser` before any Stata run that builds a dashboard.

---

## Definition of done

- [ ] `dash scatter mpg weight, hover(price foreign)` → `dash build` produces HTML containing
      `price` and `foreign`, and the tooltip shows a labelled row for each (item 1).
- [ ] `hover(nosuchvar)` is reported, not silently dropped, and never reaches jsonio
      (TR-27.2).
- [ ] A line-only figure with `hover()` carries at least one `HoverTool`; a line-only figure
      without `hover()` is unchanged from HEAD (item 10).
- [ ] The emitted `bokeh serve` app builds the same tooltips from `graph_options["hover"]`,
      and the parity corpus agrees (item 2).
- [ ] `_dash_graph_opts_to_json` is deleted, or its key list provably equals the live writer's
      (item 6).
- [ ] `fig.extra_y_ranges["y2"]` and `extra_x_ranges["x2"]` equal
      `(lo - 0.05*span, hi + 0.05*span)` over the rows actually drawn, in all four cases:
      unlinked qualifier, linked qualifier, linked `by()` facet, per-plot qualifier (item 8).
- [ ] Moving a filter updates both secondary ranges by the same rule, including the
      `(0.0, 1.0)` empty case, in all three callback shapes (item 3).
- [ ] `dash serve` either renders the secondary axis or reports the eight secondary keys as
      unsupported; the choice is recorded in the CHANGELOG and, if (b), in
      `test_mode_parity.ALLOWED` with its reason (item 4).
- [ ] A `line` layer and its `mlabel()` labels move when a filter moves, and the line remains
      x-sorted after filtering (item 9).
- [ ] A served `by()` facet of a line plot shows labels and an x-sorted line, for both the
      per-group and the `by(, total)` branches (item 11).
- [ ] `test_labels_land_on_the_sorted_points` fails when `_apply_mlabel_opts` is rebound to
      the unsorted source (item 5).
- [ ] `test_the_secondary_range_follows_the_graph_qualifier` asserts exact bounds and covers
      four cases (item 12).
- [ ] `test/test_hover.cscript` exists, is listed by the cert runner, and fails when the
      `hover` key is removed from `_dash_extract_vars` (item 7).
- [ ] Every test in the plan above has been shown to fail before its fix and to die under its
      named mutation (rule 8, BR-27.11).
- [ ] Full pytest suite and full cscript suite green, with honest skip accounting.
- [ ] Work committed on `feature/batch4-interactive-layer` (never directly on `main`), with
      the merge command supplied.

---

## Risks and sequencing notes

**Sequence inside the phase.** Item 1 first — it is the smallest change and everything in
Epic A is invisible without it (the renderer-side hover work cannot be exercised end to end
while the columns never leave Stata). Then item 10, then item 2; item 6 and item 7 can run in
parallel with any of them. In Epic B, item 8 before item 3: the JS recompute should mirror a
Python helper that is already correct, or the two will disagree in the faceted case. Item 4
last, and only after its implement-or-declare decision is taken.

**Phase 11 collides with items 2 and 10.** The index records that Phase 11 unblocks exactly
these two, and both edit `DashRenderer._make_figure_body`'s hover block (`:10197-10298`).
Phase 11 removes the duplicate `GlyphMapper._hover_tool`, fixes the date-kind picture and the
empty row labels in the same lines. Run Phase 11 first and rebase; running them concurrently
guarantees a conflict in the block, and — worse — a resolution that silently keeps one
version's field-spec rules.

**Phase 26 collides with items 2, 4 and 11.** Same task, same emitted regions
(`ServerAppBuilder._generate_app_source`, the facet block around `:15096-15130`). Sequence
26 → 27.

**Phases 05–08 change the cost of items 2, 4 and 11 by an order of magnitude.** The audit's
own conclusion: *"Sequencing 15-03 first would collapse most of the rest, because a delegated
branch inherits the standalone behaviour instead of needing its own copy of each fix."* If
the server branches still carry hand-written drawing code when this phase starts, items 2, 4
and 11 are three ports into generated string literals — each a new copy that will drift
again. If they delegate, item 2 is passing `graph_opts` through and item 11 is a single
mapper call per facet. **Item 4 is the one large item in this phase and is where this matters
most.**

**Item 4 interacts with Phase 16.** Phase 16 ports the axis grammar (`_parse_axis_label`,
scales, `ylabel2`/`xlabel2` tick lists) to the server. Implementing the secondary axis there
means implementing the secondary *tick* grammar too. Agree the boundary with Phase 16 before
starting, or option (b) — declare unsupported — becomes the honest short-term answer and
Phase 16 implements both together later.

**Ordering is load-bearing for item 9.** A line's rows are drawn in source order. Filtering
in JS by subsetting preserves the original order, which happens to be sorted — but only if
the rebuild preserves the sort key. A rebuild that filters the *unsorted* frame and forgets
to sort reintroduces the zig-zag this task fixed. C-T3 exists specifically to catch that.

**Payload and performance.** Item 1 adds columns to the serialized varlist; item 9 adds a
source to the callback args and a row-identity vector to `view_filters`. Both enlarge the
document. `test/test_filter_payload_size.py` and the dataset-size warning
(`test/test_dataset_size_warning.py`) are the guards; keep the hover columns deduplicated
against the plot variables (`_collect_graph_vars` already does this) so a variable named in
both `hover()` and a plot is serialized once.

**Security surface (CLAUDE.md rules 1, 16).** `hover()` is free-text user input that ends up
in (a) a Stata varlist passed to jsonio, (b) a Bokeh field spec `@{name}`, and (c) JavaScript
in the emitted document. Confirm each token is a real variable on the Stata side (TR-27.2),
keep the `hv in df.columns` check on the Python side (TR-27.3), and reject names containing
brace or quote characters before they are interpolated into a field spec. The axis-2 column
map added to the callback args (TR-27.7) must be serialized with `json.dumps`, as the
file's existing `filter_specs_json` / `kpi_config_json` args are, not string-concatenated.

**One honest-reporting risk.** Option (b) for item 4 is legitimate only if the report is
*true* — `test/test_unsupported_report_is_true.py` exists precisely because a report that
lists an option as unsupported while the renderer half-draws it is worse than either
extreme. If (b) is chosen, the emitted app must draw a single-axis figure **and** the report
must name every one of the eight secondary keys.
