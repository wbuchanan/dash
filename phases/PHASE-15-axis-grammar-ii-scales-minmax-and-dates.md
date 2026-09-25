# Phase 15 — Axis grammar II: scales, minmax and dates

**Purpose.** Task 09-02 built the `axis_label` and `axis_scale` grammars and they work for
the forms the auditor measured — `a(b)c`, a bare numlist, `#N`, `none`, `format()`,
`labsize()`, `angle()`, `grid`/`nogrid`, and `xscale(range())`. Phase 14 finished the
sub-option and numlist clauses that sit *inside* a tick list. This phase takes the other
half: the parts of the grammar that interact with the axis itself. `minmax` is computed
from the whole dataset and from the first series only, so a graph with an `if` qualifier or
two series draws ticks where it has no data. `xscale()`/`yscale()` recognise five
sub-options and silently swallow every other one, including `off`, which in Stata removes
the axis; the secondary scales warn about nothing at all; and `xlabel(..., axis(2))` is
actively misrouted onto the *primary* axis. `#N` and an explicit tick list overwrite the
axis's own ticker, so `xscale(log) xlabel(#5)` gets linear tick placement on a log axis.
Three numlist rules `twoway` accepts — `a/b`, `a b to c`, `##N` — are not implemented.
And `_apply_axis_spec` has no date awareness whatsoever, so on a `%t*` axis *every* form is
wrong: `minmax` emits microseconds where Bokeh wants milliseconds, explicit ticks are raw
Stata day numbers, `#N` throws away the `DatetimeTicker`, and `format(%tdDD/NN/CCYY)` is
discarded without even a warning. Underneath all of it, ten tests request the Stata
ground-truth fixture and not one reads it, and the only date-axis test asserts `fig is not
None` on a frame with no date column — which is why none of this was caught.

---

## At a glance

| | |
|---|---|
| **Items** | 9 (numbered 1–9 below, exactly as handed over) |
| **Functional vs deliverable** | 8 functional · 1 deliverable |
| **Effort mix** | 6 × small · 2 × medium · 1 × large |
| **Renderers touched** | `both` on items 1, 3, 4, 7, 8 · `standalone` (`DashRenderer`) on items 2, 5, 6 · item 9 is test-only. The "both" half is the emitted parser `_parse_axlabel` (`dash_render.py:13989`) and the emitted `xscale`/`yscale` block — see **Risks** for how this phase and Phase 16 divide it. |
| **Ultraplan tasks discharged** | `09-02` — "Implement the axis_label and axis_scale grammars", section **S09**. This phase closes its scale, `minmax`, ticker-class and date clauses. |
| **Not discharged here** | 09-02's `xtick()`/`ytick()` semantics, `xmtick()`/`ymtick()`/`xmlabel()`/`ymlabel()`, the S08 display-format fallback on a default axis, the hardcoded `#e5e5e5` grid colour and the Stata cscript (all **Phase 14**); the server port of the whole grammar, the secondary axes through the new grammar, the bare-token `to` leak, the `str(float)` tick-label key and the parity guard (all **Phase 16**). |
| **Depends on** | **Phase 14.** Items 3 and 8 edit the same two regions of `_parse_axis_spec` (`dash_render.py:9305`) that Phase 14 item 4 edits, and item 5 edits the `count` branch Phase 14 item 3 reaches through. Landing 14 first avoids two developers rewriting the same twenty lines. Nothing else here is blocked at HEAD. |
| **Unblocks** | **Phase 16** (the server port copies a *finished* parser rather than porting one and then re-porting each fix) and, for item 4, the date-axis work that Phase 9 and Phase 10 leave on the table. |
| **Source of items** | Item 1: REMAINING.md **Appendix B**, `09-02`. Items 2–9: REMAINING.md **Appendix C**, `09-02` (19 further items). |

---

## Why this phase exists

### What the audit measured (REMAINING.md, Appendix A — `09-02 · PARTIAL`)

Copied verbatim; this is the baseline everything below is a defect *against*:

> The grammar is in, and I checked each form separately rather than trusting the
> suite. `xlabel(...)` produces:
>
> | form | result |
> |---|---|
> | `2000(500)4000` | `FixedTicker[2000, 2500, 3000, 3500, 4000]` |
> | `2000 3000 4000` | `FixedTicker[2000, 3000, 4000]` |
> | `#5` | `BasicTicker(desired_num_ticks=5)` |
> | `minmax` | `FixedTicker[1800, 4080]` (the data bounds) |
> | `none` | `FixedTicker[]` |
> | `2000 "low" 4000 "high"` | ticks + `major_label_overrides` |
> | `, format(%9.0fc)` | `NumeralTickFormatter(format='0,0')` |
> | `, labsize(large)` | `major_label_text_font_size='15px'` |
> | `, angle(45)` | `major_label_orientation=0.7854` rad |
> | `, grid` / `, nogrid` | grid `#e5e5e5` / `None` |
>
> `_parse_scale_opt` honours `range()`: `xscale(range(1500 5000))` gives
> `Range1d(1500, 5000)`, and `range(...) log` keeps the range. The dead
> `xrange`/`yrange` keys are gone — the task's "do not leave both" is satisfied.
> `xtick()`/`ytick()` work.

The task's own `<done>` condition, quoted in REMAINING.md item 3, is stricter than that
table: *"Axis labelling accepts what twoway accepts and produces what twoway produces"*.

### 1. `minmax` is computed from the wrong rows **and** the wrong variable (items 1, 6)

REMAINING.md, Appendix B, `09-02` — item 1's statement:

> **[func · both · S]** Compute xlabel(minmax) from the graph's active view
> rather than the whole frame — the same defect 09-07 fixed for
> `_compute_secondary_range`, still present here.     *Where:*
> `dash_render.py:9134-9143 (the `mode == "minmax"` branch reads
> `self.df[varname]`); the fix pattern already in the file is
> `_source_frame(source, self.df)` as used at dash_render.py:9678 and :9713;
> `_apply_axis_spec` (das`

REMAINING.md, Appendix C, `09-02` — the same defect, stated twice with more of the damage
enumerated (these are items 6 and 1's Appendix C form):

> **[func · standalone · S]** DashRenderer's xlabel(minmax)/ylabel(minmax)
> computes the min and max from the UNFILTERED frame (self.df), not from the
> graph's active, qualifier-narrowed source, so a tick is drawn where no data
> exists. _apply_axis_spec's minmax branch (dash_render.py:9136-9142) reads
> `col = self.df[varname]`; two other places in the same function body already
> do the right thing with `_source_frame(source, self.df)`
> (dash_render.py:9676 and :9713, _compute_secondary_range), and `source` is
> in scope at the tick loop (dash_render.py:9903-9913, inside
> _make_figure_body which starts at :9495). Fix: pass `_source_frame(source,
> self.df)` into _apply_axis_spec and have the minmax branch read that frame
> instead of self.df. Note this is in addition to server mode, which has no
> minmax at all (auditor's remaining item 1). A guard test belongs in
> test/test_axis_options.py: minmax + graph-level if_expr must give the
> subset's min/max. **Do NOT 'fix' the by() facet case the same way — Stata's
> by() shares a common axis by default, and dash's global minmax across facets
> matches that.**

> **[func · standalone · S]** `minmax` is computed from the wrong rows and the
> wrong variable: `_apply_axis_spec` reads `self.df[varname]` — the WHOLE
> dataset — so a graph-level `if`/`in` qualifier is ignored, and `varname` is
> `plots[0]`'s x/y variable (dash_render.py:9506-9507), so a two-series graph
> labels the axis at the FIRST series' bounds. Nothing recomputes it when a
> filter widget moves either, because the ticks are baked into a FixedTicker
> at build time. The one-bound fallback for `xscale(range(0))` at
> dash_render.py:9765-9770 reads the same unfiltered frame.

Confirmed at HEAD (`ca5fe35`). `_apply_axis_spec`, `dash_render.py:9112`, the `minmax`
branch at `:9136-9142`:

```python
        elif mode == "minmax":
            col = self.df[varname] if varname in getattr(
                self.df, "columns", []) else None
            if col is not None:
                vals = pd.to_numeric(col, errors="coerce").dropna()
                if len(vals):
                    axis_obj.ticker = FixedTicker(
                        ticks=[float(vals.min()), float(vals.max())])
```

The call site, `dash_render.py:9900-9913`, passes only the variable — not the source:

```python
        for ax_key, axis_obj, grid_obj, var in (
            ("xlabel", fig.xaxis, fig.xgrid, xvar),
            ("ylabel", fig.yaxis, fig.ygrid, yvar),
        ):
            raw_ax = graph_opts.get(ax_key, "")
            tick_key = "xtick" if ax_key == "xlabel" else "ytick"
            raw_tick = graph_opts.get(tick_key, "")
            if not raw_ax and not raw_tick:
                continue
            spec = self._parse_axis_spec(raw_ax or raw_tick)
            self._apply_axis_spec(fig, axis_obj, grid_obj, spec, var)
```

and `xvar`/`yvar` are the first layer's variables (`dash_render.py:9506-9507`):

```python
        # Determine axis variables from the first plot layer
        xvar = plots[0].get("xvar", "") if plots else ""
        yvar = plots[0].get("yvar", "") if plots else ""
```

The correct pattern is already in the same method body, at `dash_render.py:9678` — the
09-07 fix, with its own comment explaining exactly this bug:

```python
            # From the ACTIVE view, not self.df: a graph-level if/in
            # qualifier already narrowed the source, so computing the
            # right-hand axis from the full frame left it spanning data the
            # graph does not show.
            _y2_lo, _y2_hi = _compute_secondary_range(
                _source_frame(source, self.df), plots, "yaxis", "yvar", 2
            )
```

The one-bound `range()` fallback at `dash_render.py:9765-9770` repeats the same mistake a
third time, on the same frame *and* the same `plots[0]` variable:

```python
            if _lo is None or _hi is None:
                # One bound given: keep the data's own value for the other.
                _col = xvar if _axis_attr == "x_range" else yvar
                if _col in getattr(self.df, "columns", []):
                    _v = pd.to_numeric(self.df[_col], errors="coerce").dropna()
                    if len(_v):
                        _cur_lo = float(_v.min())
                        _cur_hi = float(_v.max())
```

**Ground truth exists.** `test/fixtures/axis_truth.json`, probe `a_minmax`:
`twoway scatter mpg weight, xlabel(minmax)` → `tick_values [1760.0, 4840.0]`,
`tick_labels ["1,760", "4,840"]`. Probe `a_ymm`: `ylabel(minmax)` →
`tick_values [41.0, 12.0]`, `tick_labels ["41", "12"]`.

### 2. Five scale sub-options are recognised; the rest vanish (items 2, 7, 8)

REMAINING.md, Appendix C, `09-02`:

> **[func · both · S]** Only five xscale()/yscale() sub-options are
> recognised; the rest are dropped with no warning, including `off`, which in
> Stata removes the axis entirely. `_report_unhandled_scale_opts` lists
> exactly noextend/extend/alt/fextend/nofextend, so `yscale(off)`, `noline`,
> `titlegap()`, `lcolor()/lwidth()/lpattern()` and `axis(#)` pass through in
> silence — the opposite of the honesty rule the same function was added to
> satisfy. `off` is a two-line implementation (`axis_obj.visible = False`).

> **[func · standalone · S]** xscale2()/yscale2() never pass through
> _report_unhandled_scale_opts, so noextend/extend/alt/fextend on a secondary
> axis is dropped in total silence while the same token on the primary axis
> warns.

> **[func · both · S]** axis_label sub-options outside the implemented five
> are silently dropped, and `axis(#)` is actively misrouted: `xlabel(1000
> 2000, axis(2))` applies the ticks to the PRIMARY x axis instead of the
> second one. `_parse_axis_spec` strips
> `labcolor/labgap/tlength/labstyle/tstyle/tposition` into the bin and
> truncates at the first sub-option comma, so `valuelabel`, `alternate`,
> `notick`, `add`, `custom` and `angle(stacked)` vanish with no report.

Confirmed at HEAD. The whole of `_report_unhandled_scale_opts` (`dash_render.py:805`):

```python
def _report_unhandled_scale_opts(raw: str, which: str) -> None:
    """Report xscale()/yscale() sub-options dash does not implement."""
    for tok in ("noextend", "extend", "alt", "fextend", "nofextend"):
        if re.search(r"\b" + tok + r"\b", raw or "", re.I):
            warnings.warn(
                f"dash: {which}({tok}) is not implemented and is being "
                f"ignored.", UserWarning, stacklevel=3,
            )
```

It has exactly one caller, `dash_render.py:9756`, inside the primary `xscale`/`yscale`
loop. The secondary scales at `dash_render.py:9683` and `:9718` call `_parse_scale_opt`
and nothing else:

```python
9683:            _y2_log, _y2_rev = _parse_scale_opt(_y2_scale_raw)
9718:            _x2_log, _x2_rev = _parse_scale_opt(_x2_scale_raw)
```

And the sub-option strip in `_parse_axis_spec` (`dash_render.py:9344-9350`) is the truncation
the item describes — note that `axis` is not in the strip list, so `axis(2)` survives into
`head` and is then cut off by the comma rule, taking no effect anywhere:

```python
        # Strip every recognised sub-option so only the numlist remains.
        head = re.sub(r"\b(?:format|labsize|angle|labcolor|labgap|tlength|"
                      r"labstyle|tstyle|tposition)\s*\([^)]*\)", " ",
                      text, flags=re.I)
        head = re.sub(r"\b(?:no)?grid\b", " ", head, flags=re.I)
        # Only a comma that INTRODUCES SUB-OPTIONS separates; Stata also
        # accepts a comma-separated numlist, so xlabel(1,3,5) must survive.
        m_sub = re.search(r",\s*(?=[A-Za-z_])", head)
        if m_sub:
            head = head[:m_sub.start()]
```

**Ground truth for `off` exists and is more precise than "removes the axis entirely".**
`test/fixtures/axis_truth.json`, probe `b_off` — `twoway scatter mpg weight, yscale(off)`:

| what the probe records | value |
|---|---|
| every `<text>` element on the canvas | `['2,000', '3,000', '4,000', '5,000', 'Weight (lbs.)']` |
| `y_axis.tick_labels` | `[null, null, null, null]` |
| `y_axis.tick_px` | `[265.61, 1075.61, 1885.44, 2695.28]` |
| `y_axis.n_gridlines` | `4` (gridlines **survive**) |
| `axis_line_px.v_y_from` → `v_y_to` | `2766.66` → `2811.54` (the vertical axis line is a 45-unit stub) |

So `yscale(off)` removes the y tick labels *and the y axis title*, keeps the gridlines, and
collapses the axis line. Bokeh's `axis_obj.visible = False` hides the axis line, ticks,
tick labels and axis label while leaving `fig.ygrid` untouched — which matches the probe.
The fixture's own `unverified` note for this probe explains the nulls: *"fewer than two tick
labels parse as numbers, so the pixel<->data map could not be inverted; the tick pixel
positions above are still exact"*.

### 3. `#N` and explicit ticks overwrite the axis's own ticker class (item 5)

REMAINING.md, Appendix C, `09-02`:

> **[func · standalone · S]** `#N` and explicit ticks overwrite the axis's own
> ticker class, so `xscale(log) xlabel(#5)` puts LINEAR tick placement on a
> log axis. `_apply_axis_spec`'s count branch assigns a bare
> `BasicTicker(desired_num_ticks=N)` with no regard for the
> LogAxis/DatetimeAxis already built.     *Where:* `dash_render.py:9145-9148
> in `_apply_axis_spec` (`axis_obj.ticker =
> BasicTicker(desired_num_ticks=spec["count"])`) — choose
> LogTicker/DatetimeTicker by `type(axis_obj)``

Confirmed at HEAD, `dash_render.py:9145-9148`:

```python
        elif mode == "count":
            # Stata's #N is a SUGGESTION -- measured, xlabel(#10) on weight
            # yields eight ticks.  Bokeh's desired_num_ticks means the same
            # thing, so the option maps onto it rather than onto a fixed list.
            axis_obj.ticker = BasicTicker(desired_num_ticks=spec["count"])
```

The axis type is decided much earlier, at `dash_render.py:9577-9586`, and the comment there
warns that it is decided once and must not be re-created:

```python
        if _x_date:
            fig_kwargs["x_axis_type"] = "datetime"
        elif _xs_log:
            fig_kwargs["x_axis_type"] = "log"
```

Stata's own answer, measured: probe `b_xlog` (`xscale(log)`) records the x axis with
`mapping.space == "log10"` and ticks `[2000, 3000, 4000, 5000]`; probe `a_hash5`
(`xlabel(#5)`) records four ticks `[2000, 3000, 4000, 5000]`; probe `a_hash10` records
eight, `[1500 … 5000]` — the "`#N` is a suggestion" fact the code comment already relies on.

### 4. Three numlist rules Stata accepts are not implemented (item 3)

REMAINING.md, Appendix C, `09-02`:

> **[func · both · M]** Three numlist rules Stata accepts are unimplemented
> and silently produce the wrong ticks or none: `a/b` (10/15), `a b to c` (10
> 15 to 40) and `##N` (##5). `_parse_axis_spec` (dash_render.py:9305) handles
> only `a(b)c`, `#N`, `minmax`, `none` and bare values, so `/` and `##` fall
> through to the default ticker and `to` degrades as described in the leak
> item. The task's <done> is "Axis labelling accepts what twoway accepts and
> produces what twoway produces".

"the leak item" is the companion Appendix C entry assigned to **Phase 16 item 7**:

> A bare (unquoted) non-numeric token in xlabel()/ylabel() is silently turned
> into a TICK LABEL, so Stata's `to` rule paints the word "to" on the axis.

Confirmed at HEAD: `_parse_axis_spec` (`dash_render.py:9305`) contains exactly four
recognisers — `none`, `minmax`, `#\s*(\d+)`, and the `a(b)c` regex
`(-?[\d.eE+]+)\s*\(\s*(-?[\d.eE+]+)\s*\)\s*(-?[\d.eE+]+)` — and then hands whatever is left
to `_parse_axis_label_opt`. There is no `/`, no `to` and no `##` anywhere in the method.

**No ground truth exists for these three forms.** Measured over
`test/fixtures/axis_truth.json`: 233 probes, none of whose `command` strings contain `to`,
`/` or `##` inside an `xlabel()`/`ylabel()`. The probe groups present are
`axis_label`, `axis_scale`, `legend`, `refline`, `titles`. Probes must be added to
`scripts/extract_axis_truth.do` before the tick counts for these forms can be asserted
against anything but an assumption — see the test plan.

### 5. `_apply_axis_spec` has no date awareness (item 4 — the large one)

REMAINING.md, Appendix C, `09-02`, in full:

> **[func · both · L]** `_apply_axis_spec` has no date awareness, so every
> axis_label and axis_scale form is wrong on a %t* axis. The renderer converts
> date columns to datetime64 (dash_render.py:8196-8210) and Bokeh's
> DatetimeAxis works in epoch MILLISECONDS, but: explicit ticks are passed
> through as raw Stata date numbers; `minmax` emits `float(vals.min())` of a
> datetime column, i.e. MICROseconds (1000x too large); `#N` replaces the
> DatetimeTicker with a BasicTicker; `format(%td...)` is silently ignored (the
> `elif spec["format"] and _stata_date_kind(fmt) is None` guard at :9166
> suppresses even the warning); and `xscale(range())` builds a Range1d in date
> units. The helper that knows the answer, `_figure_date_kind`
> (dash_render.py:9268), is never consulted here.

Confirmed at HEAD, all five clauses:

| clause | evidence at `ca5fe35` |
|---|---|
| explicit ticks passed through raw | `axis_obj.ticker = FixedTicker(ticks=spec["ticks"])` at `:9149`, with `spec["ticks"]` straight off the parser |
| `minmax` in microseconds | the loader produces `datetime64[us]` (`_stata_dates_to_datetime`, `dash_render.py:290`); `pd.to_numeric` of `%td` day 15000 gives **980380800000000.0**, exactly 1000× the **980380800000** ms Bokeh wants |
| `#N` throws away the `DatetimeTicker` | same `BasicTicker` assignment as item 5, `:9148` |
| `format(%td…)` discarded in silence | the `elif` at `:9164-9166`: `elif spec["format"] and _stata_date_kind(fmt) is None:` — a date picture makes `_stata_date_kind` non-`None`, so neither the formatter branch nor the warning branch runs |
| `xscale(range())` in date units | `setattr(fig, _axis_attr, _Rng(float(_new_lo), float(_new_hi)))` at `:9773`, on values parsed by `_parse_scale_range` with no conversion |
| `_figure_date_kind` never consulted | it is called twice, at `dash_render.py:9559-9560`, both inside the figure-construction block; `_apply_axis_spec` does not call it and does not receive its result |

The suppressed-warning block, verbatim (`dash_render.py:9159-9170`):

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

`_stata_numeric_pattern` returns `None` for anything whose kind is not `f`
(`dash_render.py:395-415`), so a date picture reaches the `elif`, which then excludes it.
Nothing is applied and nothing is said. The figure meanwhile *has* a per-kind formatter,
attached at `dash_render.py:9598-9603` — which `_apply_axis_spec` then overwrites whenever a
numeric picture is present, including one merely inherited from `self.numeric_formats`:

```python
        for _axis, _kind in ((fig.xaxis, _x_date), (fig.yaxis, _y_date)):
            if _kind:
                _axis.formatter = _datetime_formatter_for(_kind)
```

### 6. The tests cannot fail (item 9)

REMAINING.md, Appendix C, `09-02`:

> **[deli · docs · M]** The Stata ground-truth fixture is requested by the
> axis tests and never read: ten tests take the `truth` fixture and not one
> indexes it, so every assertion is hardcoded to dash's own numbers rather
> than to what Stata measured. In particular no test asserts tick LABEL text,
> which is why the missing default display format (item 3) and the `to` leak
> (item 1) went unnoticed. And
> `test_a_date_axis_ignores_a_numeric_format_gracefully`
> (test/test_axis_options.py:218) asserts only `fig is not None`, on
> `_SCATTER` — a frame with no date column at all — so the date path has no
> coverage whatsoever.

Confirmed at HEAD. The fixture-taking tests in `test/test_axis_options.py` are at lines
136, 152, 157, 171, 311, 316, 329, 430, 473 and 587; `grep -n "truth\[" ` over the file
returns nothing. Two examples, verbatim:

```python
    def test_minmax_is_two_ticks_at_the_data_bounds(self, truth):
        """Measured: xlabel(minmax) on weight gives exactly 1760 and 4840."""
        fig, _ = _fig_with_gopts(_SCATTER, {"xlabel": "minmax"})
        assert _fixed_ticks(fig) == [1760.0, 4840.0]

    def test_a_date_axis_ignores_a_numeric_format_gracefully(self):
        """Regression guard for the S08 work: no exception, no silent mangle."""
        fig, _ = _fig_with_gopts(_SCATTER, {"xlabel": ", format(%td)"})
        assert fig is not None
```

The docstring of the first names Stata's measurement but the fixture that holds it is not
read; `truth["probes"]["a_minmax"]["x_axis"]["tick_values"]` is `[1760.0, 4840.0]` and
`…["tick_labels"]` is `["1,760", "4,840"]`, which the assertion never touches. The second
builds `_SCATTER` — the `_auto()` frame of `mpg`/`weight`/`price`/`rep78`/`foreign`, no
date column — so no date branch is exercised at all.

---

## Epics

| epic | goal | items |
|---|---|---|
| **15-A — `minmax` tells the truth** | The two ticks `minmax` draws are the bounds of the data the graph is actually drawing, over every variable on that axis. | 1, 6 |
| **15-B — Scales and sub-options: honest, routed, non-destructive** | Nothing in `xscale()`/`yscale()`/`xscale2()`/`yscale2()`/`xlabel()` is dropped without a report, `off` works, `axis(2)` never lands on axis 1, and labelling never destroys the axis's own ticker class. | 2, 5, 7, 8 |
| **15-C — The numlist rules and the date axis** | `xlabel()` accepts what `twoway` accepts, every form is correct on a `%t*` axis, and the tests assert against what Stata measured. | 3, 4, 9 |

---

## User stories

### Epic 15-A — `minmax` tells the truth

**US-15.1** — *As a Stata user pasting a `twoway` command, I want `xlabel(minmax)` on a
graph with an `if` qualifier to label the axis at the bounds of the rows I kept, so that the
axis does not claim data I excluded.*

- **Given** `dash scatter mpg weight if foreign==1, xlabel(minmax)` where the full frame
  spans `weight` 1760–4840 and the foreign subset spans 1760–3420,
  **when** the dashboard is built,
  **then** the x axis carries a `FixedTicker` with ticks `[1760.0, 3420.0]`,
  **and** no tick is drawn at 4840.

**US-15.2** — *As a Stata user overlaying two series, I want `ylabel(minmax)` to span both,
so that the second series is not left outside the labelled range.*

- **Given** `(scatter mpg weight) (scatter price weight), ylabel(minmax)` where `mpg` spans
  12–41 and `price` spans 3291–15906 on the same y axis,
  **when** the dashboard is built,
  **then** the y ticks are the union bounds `[12.0, 15906.0]`, not `[12.0, 41.0]`.

**US-15.3** — *As a Stata user, I want `xscale(range(0))` to take its missing bound from the
same rows `minmax` uses, so that one option does not contradict the other.*

- **Given** a graph with a graph-level `if` qualifier and `xscale(range(0))`,
  **when** the figure's `x_range` is built,
  **then** the upper bound is the filtered maximum, not `self.df`'s.

### Epic 15-B — Scales and sub-options: honest, routed, non-destructive

**US-15.4** — *As a `dash serve` operator and as a package maintainer, I want every
unimplemented `xscale()`/`yscale()` sub-option to produce a warning, so that dash's promise
"accept, never abort, report together" is not a promise it keeps for five tokens only.*

- **Given** `dash scatter mpg weight, yscale(noline)`,
  **when** the build runs,
  **then** a `UserWarning` names `yscale(noline)` as not implemented,
  **and** the build still returns rc 0 with a rendered dashboard.
- **Given** `yscale2(noextend)` on a two-axis graph,
  **when** the build runs,
  **then** the same warning fires as for `yscale(noextend)` on the primary axis.

**US-15.5** — *As a Stata user, I want `yscale(off)` to remove the axis, so that a pasted
`twoway` command that hides an axis hides it in dash too.*

- **Given** `dash scatter mpg weight, yscale(off)`,
  **when** the dashboard is built,
  **then** the y axis is not drawn (no axis line, no ticks, no tick labels, no axis title),
  **and** the y gridlines remain, matching probe `b_off`.

**US-15.6** — *As a Stata user with a right-hand axis, I want `xlabel(1000 2000, axis(2))`
to reach the second axis or tell me it cannot, so that my ticks never silently land on the
wrong axis.*

- **Given** `xlabel(1000 2000, axis(2))`,
  **when** the figure is built,
  **then** either the second x axis carries the `FixedTicker[1000, 2000]` and the primary is
  untouched, **or** a warning names `axis(2)` as unsupported and the primary axis is
  untouched — never the primary carrying the ticks in silence.

**US-15.7** — *As a dashboard viewer, I want `xscale(log) xlabel(#5)` to place ticks
logarithmically, so that the graph I am reading is not linearly ticked on a log axis.*

- **Given** `dash scatter price weight, xscale(log) xlabel(#5)`,
  **when** the figure is built,
  **then** the x axis ticker is a `LogTicker` (not a bare `BasicTicker`) carrying
  `desired_num_ticks == 5`,
  **and** the axis is still a `LogAxis`.
- **Given** a `%td` x variable and `xlabel(#5)`,
  **then** the ticker is a `DatetimeTicker` and the axis is still a `DatetimeAxis`.

### Epic 15-C — The numlist rules and the date axis

**US-15.8** — *As a Stata user pasting a `twoway` command, I want `xlabel(10/15)`,
`xlabel(10 15 to 40)` and `xlabel(##5)` to work, so that "drop-in" means the whole numlist
grammar and not a subset of it.*

- **Given** `xlabel(10/15)`, **when** the figure is built, **then** the ticks are
  `[10, 11, 12, 13, 14, 15]`.
- **Given** `ylabel(10 15 to 40)`, **then** the ticks are `[10, 15, 20, 25, 30, 35, 40]` and
  **no tick label anywhere on the figure is the string `to`**.
- **Given** `xlabel(##5)`, **then** the result matches the measured Stata probe added for it;
  it is never silently the default ticker.

**US-15.9** — *As a Stata user plotting a time series, I want every axis option to behave on
a date axis, so that `xlabel(td(01jan2001) td(01jan2002))` puts ticks on those two days.*

- **Given** a `%td` x variable and `xlabel(15006 15371)`,
  **when** the figure is built,
  **then** the `FixedTicker` ticks are the epoch-millisecond values of those two days,
  **and** the axis is still a `DatetimeAxis` with its per-kind `DatetimeTickFormatter`.
- **Given** the same variable and `xlabel(minmax)`,
  **then** the two ticks are in milliseconds — never 1000× larger.
- **Given** `xlabel(, format(%tdDD/NN/CCYY))`,
  **then** a `DatetimeTickFormatter` reflecting that picture is applied, **or** a warning
  names the format as unreproduced; never silence.
- **Given** `xlabel(, format(%9.0fc))` on a date axis,
  **then** the `DatetimeTickFormatter` is **not** replaced by a `NumeralTickFormatter`.
- **Given** `xscale(range(15006 15371))` on a date axis,
  **then** the `Range1d` bounds are in milliseconds.

**US-15.10** — *As a package maintainer, I want the axis tests to assert against the Stata
measurements in `axis_truth.json`, including tick label text, so that a regression in the
label text cannot pass a green suite.*

- **Given** the `truth` fixture,
  **when** the axis tests run,
  **then** each test that takes `truth` indexes it (`truth["probes"][…]["x_axis"]["tick_values"]`
  / `["tick_labels"]`) and compares dash's output to the probe,
  **and** at least one test asserts rendered tick **label text**.
- **Given** the date-axis tests,
  **then** they build a frame that actually carries a `%t*` column.

---

## Business requirements

Each is testable as written; the test plan names the test that proves it.

| ID | Requirement |
|---|---|
| **BR-15.1** | `xlabel(minmax)`/`ylabel(minmax)` must be computed from the rows the graph draws — after any graph-level `if`/`in` qualifier — not from the whole dataset. |
| **BR-15.2** | When more than one plot layer shares an axis, `minmax` must cover every variable on that axis, not `plots[0]`'s. |
| **BR-15.3** | The one-bound `xscale(range(a))` / `yscale(range(a))` fallback must derive its missing bound from the same rows and the same variable set as BR-15.1 and BR-15.2. |
| **BR-15.4** | `minmax` on a facetted (`by()`) graph must keep its current whole-frame behaviour: Stata's `by()` shares a common axis by default. BR-15.1 must not change it. |
| **BR-15.5** | Any `xscale()`/`yscale()` sub-option dash does not implement must produce a `UserWarning` naming the option and the axis; the build must still succeed. |
| **BR-15.6** | `xscale2()`/`yscale2()` must report unimplemented sub-options identically to `xscale()`/`yscale()`. |
| **BR-15.7** | `xscale(off)`/`yscale(off)` must remove the axis from the figure. |
| **BR-15.8** | Any `axis_label` sub-option dash does not implement must be reported rather than dropped, and `axis(#)` must never apply ticks to the wrong axis. |
| **BR-15.9** | Applying a tick specification must never change the axis's scale type: a log axis keeps logarithmic tick placement, a date axis keeps datetime tick placement. |
| **BR-15.10** | `xlabel()`/`ylabel()` must accept the numlist forms `a/b`, `a b to c` and `##N` in addition to the forms already supported, and produce the ticks Stata produces for them. |
| **BR-15.11** | On a `%t*` axis, every `axis_label` and `axis_scale` form — explicit ticks, `minmax`, `#N`, `format()`, `range()` — must operate in the datetime axis's epoch-millisecond space. |
| **BR-15.12** | A Stata **date** picture in `format()` must either be honoured or reported; silence is not permitted. A **numeric** picture must never replace a date axis's `DatetimeTickFormatter`. |
| **BR-15.13** | Every axis test that takes the `truth` fixture must index it, and the suite must assert rendered tick **label text**, not only tick values. |
| **BR-15.14** | The date-axis tests must exercise a frame carrying a `%t*` column. |
| **BR-15.15** | Per CLAUDE.md rule 8, each defect above ships with a regression test that fails at `ca5fe35` and passes after the fix; per rule 4, each new or changed function carries a unit test. |

---

## Technical requirements

All line numbers are `ca5fe35` on `feature/batch4-interactive-layer`, confirmed at HEAD.
`.ultraplan/sections/09-*.md` line numbers are stale (the file grew from ~10,455 to ~16,000
lines) — use these.

### Epic 15-A — `minmax`

**TR-15.1 — Give `_apply_axis_spec` the frame it should be reading.**
`DashRenderer._apply_axis_spec` is defined at `dash_render.py:9112` with signature
`(self, fig, axis_obj, grid_obj, spec: dict, varname: str = "")`. Add a frame parameter
(e.g. `frame: "pd.DataFrame | None" = None`, defaulting to `self.df` so no other caller
breaks) and pass `_source_frame(source, self.df)` from the single call site at
`dash_render.py:9913`. `_source_frame` is defined at `dash_render.py:2411` and returns a
DataFrame view of a `ColumnDataSource`, falling back to the second argument. `source` is in
scope at the call site — it is `_make_figure_body`'s second parameter
(`dash_render.py:9495-9499`). This is the identical pattern used by the 09-07 fix at
`dash_render.py:9678` and `:9713`.

**TR-15.2 — Read that frame in the `minmax` branch.**
`dash_render.py:9136-9142`: replace `col = self.df[varname] …` with the passed frame. Keep
the `pd.to_numeric(col, errors="coerce").dropna()` guard and the `if len(vals)` guard; a
figure whose source is empty must leave the ticker alone rather than raise.

**TR-15.3 — Use every variable on the axis, not `plots[0]`'s.**
`xvar`/`yvar` at `dash_render.py:9506-9507` are `plots[0].get("xvar")`/`plots[0].get("yvar")`.
For the tick loop at `:9900-9913`, compute the union of the axis's variables across
`graph_spec["plots"]` — for the y axis that is each plot's `yvar`, falling back to `var` for
the univariate types, the same fallback `_figure_date_kind` (`dash_render.py:9268-9297`)
already uses: `plot.get(key, "") or (plot.get("var", "") if key == "yvar" else "") or fallback`.
Exclude layers bound to the secondary axis (`options.yaxis`/`options.xaxis` == 2), which
`_compute_secondary_range` already partitions on. Take `min` over each column's min and
`max` over each column's max. A single-layer graph must produce exactly today's answer.

**TR-15.4 — Fix the `range()` one-bound fallback the same way.**
`dash_render.py:9765-9770` reads `pd.to_numeric(self.df[_col], …)` where `_col` is `xvar` or
`yvar`. Point it at the same filtered frame and the same variable union as TR-15.1–TR-15.3.

**TR-15.5 — Do not touch the facet path.** REMAINING.md is explicit: *"Do NOT 'fix' the
by() facet case the same way — Stata's by() shares a common axis by default, and dash's
global minmax across facets matches that."* `_make_figure_body` receives `facet_view` as its
third parameter (`dash_render.py:9498`); when a facet view is in play, `minmax` must keep
using the graph's whole (filtered) frame rather than the facet's subset. A test pins this
(see the test plan) so a later developer cannot "improve" it.

### Epic 15-B — Scales and sub-options

**TR-15.6 — Extend `_report_unhandled_scale_opts` (`dash_render.py:805`).**
Its token tuple is today `("noextend", "extend", "alt", "fextend", "nofextend")`. Add at
minimum the tokens REMAINING.md names: `noline`, `titlegap`, `lcolor`, `lwidth`, `lpattern`,
`axis`. Bare-word tokens keep the existing `\b<tok>\b` search; parenthesised ones
(`titlegap()`, `lcolor()`, `axis()`) need `\b<tok>\s*\(` so `lcolor(red)` is reported with
its argument. `off` must be **implemented**, not reported (TR-15.7). Keep
`stacklevel=3` so the warning points at the user's call.

**TR-15.7 — Implement `off`.** In the primary scale loop at `dash_render.py:9747-9773`,
after `_report_unhandled_scale_opts`, detect `\boff\b` in the raw `xscale`/`yscale` string
and set `axis_obj.visible = False` on the matching `fig.xaxis`/`fig.yaxis` members. Do
**not** touch `fig.xgrid`/`fig.ygrid`: probe `b_off` records 4 surviving gridlines with the
tick labels and axis title gone.

**TR-15.8 — Route the secondary scales through the reporter.**
Add `_report_unhandled_scale_opts(_y2_scale_raw, "yscale2")` immediately before
`dash_render.py:9683` and `_report_unhandled_scale_opts(_x2_scale_raw, "xscale2")` before
`dash_render.py:9718`. The `which` string must be `yscale2`/`xscale2` so the warning text
names the option the user typed.

**TR-15.9 — Report unimplemented `axis_label` sub-options.**
`_parse_axis_spec` (`dash_render.py:9305`) implements `format()`, `labsize()`, `angle()`,
`grid`, `nogrid`. Its strip regex at `:9344-9347` discards
`labcolor|labgap|tlength|labstyle|tstyle|tposition`, and the comma rule at `:9349-9350`
truncates everything else. Collect the dropped sub-options and report them: the ones named
by REMAINING.md are `labcolor`, `labgap`, `tlength`, `labstyle`, `tstyle`, `tposition`,
`valuelabel`, `alternate`, `notick`, `add`, `custom`, `axis(#)` and `angle(stacked)`.
`_parse_axis_spec` is a `@staticmethod` and warnings from it must carry the option key
(`xlabel`/`ylabel`/`xtick`/`ytick`), so either thread the key in as an argument or return
the dropped list in the spec dict and warn at the call site (`:9913`) — the second keeps the
parser pure and testable, and is preferred. `angle(stacked)` is currently swallowed by
`_parse_axis_angle` (`dash_render.py:904`), which returns `None` for anything that is not
`horizontal`, `vertical` or a float.

**TR-15.10 — Route or report `axis(#)`.** `xlabel(1000 2000, axis(2))` must not apply to the
primary axis. The secondary-axis tick code is at `dash_render.py:9699` (`ylabel2`) and
`:9734` (`xlabel2`). Two acceptable implementations, in REMAINING.md's own words —
*"route `axis(2)` to the secondary-axis code … or report it"*:
(a) when `axis(2)` is present, feed the spec to the `_x2_ax`/`_y2_ax` path instead;
(b) when it is present, skip the primary application and warn. (a) is only worth doing once
**Phase 16 item 3** has routed the secondary axes through the full grammar; until then (b) is
the honest interim and is what BR-15.8's acceptance criterion allows. `axis(1)` is a no-op
and must apply to the primary axis as today. `axis(#)` for `# > 2` must warn.

**TR-15.11 — Preserve the ticker class.** `dash_render.py:9145-9148` assigns
`BasicTicker(desired_num_ticks=spec["count"])` unconditionally. Choose the ticker by the
axis object's own type: `bokeh.models.LogAxis` → `LogTicker`,
`bokeh.models.DatetimeAxis` → `DatetimeTicker`, otherwise `BasicTicker`. `axis_obj` at the
call site is `fig.xaxis`/`fig.yaxis`, a *splattable list* — take `type(axis_obj[0])` (or
`axis_obj._property_values`-free equivalent) rather than `type(axis_obj)`, which is Bokeh's
proxy. All three tickers accept `desired_num_ticks`. The axis type is fixed earlier at
`dash_render.py:9577-9586` and the comment there — *"Axis type is decided ONCE, before the
single bokeh_figure() call. Commit c3941de fixed a bug caused by re-creating a figure to
change its axis type; do not reintroduce it"* — means the ticker must adapt to the axis,
never the reverse. The `explicit` branch at `:9149` keeps `FixedTicker`, which is correct for
all three axis types.

### Epic 15-C — Numlist rules and the date axis

**TR-15.12 — `a/b`.** In `_parse_axis_spec`, next to the `a(b)c` `re.finditer` at
`dash_render.py:9369-9382`, add a rule for `(-?[\d.eE+]+)\s*/\s*(-?[\d.eE+]+)` producing the
unit-increment sequence `a, a+1, …, b`. It must run **before** the bare-token pass so `10/15`
is not seen as two values, and must not fire inside a `format()` argument (the strip at
`:9344-9347` already removes those). Mirror into the emitted copy,
`dash_render.py:13989 _parse_axlabel`, unless Phase 16 has already replaced that copy.

**TR-15.13 — `a b to c`.** Stata's `to` rule takes the increment from the first two values:
`10 15 to 40` → `10, 15, 20, …, 40`. Implement it in `_parse_axis_spec` as a pre-pass over
`head` that recognises `<v1> <v2> to <v3>` and expands it, and — critically — **consumes the
token `to`**, which today reaches `_parse_axis_label_opt` (`dash_render.py:9393`, bare-token
branch ~`:9425-9432`) and is painted on the axis as a tick label. That leak is
**Phase 16 item 7**; this item must not re-introduce it, and the test named in the test plan
asserts on the label text so the two cannot drift apart.

**TR-15.14 — `##N`.** Add a `##\s*(\d+)` recogniser beside the `#\s*(\d+)` branch at
`dash_render.py:9364-9368`. The tick count it produces must come from a **measured probe**
added to `scripts/extract_axis_truth.do` (see TR-15.21), not from an assumption about
Stata's semantics, and it must interact correctly with the minor-tick options
`xmtick()`/`ymtick()`/`xmlabel()`/`ymlabel()` that **Phase 14 item 2** implements — the two
must agree on what `##N` means before either ships.

**TR-15.15 — Tell `_apply_axis_spec` the axis's date kind.**
`_figure_date_kind` (`dash_render.py:9268`) already computes it and is called at
`dash_render.py:9559-9560`; its results (`_x_date`, `_y_date`) are in scope at the tick loop
(`:9900-9913`). Pass the matching kind into `_apply_axis_spec` alongside the frame from
TR-15.1. `self.date_vars.get(varname)` is an acceptable equivalent for the single-variable
case, but the figure-level answer is the correct one because it is the value that decided
`fig_kwargs["x_axis_type"] = "datetime"`.

**TR-15.16 — Convert explicit ticks.** In the `explicit` branch (`dash_render.py:9149-9158`),
when a date kind is in force, map `spec["ticks"]` through
`_stata_dates_to_datetime(pd.Series(ticks), kind).astype("datetime64[ms]").astype("int64")`
before building the `FixedTicker`. `_stata_dates_to_datetime` is at `dash_render.py:290`;
`_stata_date_kind` at `:271`. The explicit `astype("datetime64[ms]")` is required —
`pd.to_numeric` on the loader's output gives **microseconds**: the loader produces
`datetime64[us]` and `%td` day 15000 measures as `980380800000000.0` against Bokeh's
`980380800000`.

**TR-15.17 — Convert `minmax`.** Same conversion in the `minmax` branch
(`dash_render.py:9136-9142`), replacing `float(vals.min())`/`float(vals.max())` with the
millisecond integers. This is the clause REMAINING.md measures as *"MICROseconds (1000x too
large)"*, and it composes with TR-15.2's filtered frame: the frame is chosen first, the
scale conversion second.

**TR-15.18 — Do not destroy the date formatter.** At `dash_render.py:9159-9170`: when the
axis has a date kind and `fmt` is a **numeric** picture — including one merely inherited from
`self.numeric_formats` — leave the axis's `DatetimeTickFormatter` alone. When `fmt` is a
**date** picture (`_stata_date_kind(fmt)` is not `None`), apply a `DatetimeTickFormatter`
derived from it, or warn that dash does not reproduce that picture. Either way the
`elif spec["format"] and _stata_date_kind(fmt) is None` guard at `:9164-9166` must stop
suppressing the warning for date formats. The per-kind default is built by
`_datetime_formatter_for` (`dash_render.py:247`) and attached at `:9598-9603`; its tables are
the reference for what each kind should look like (`%ty` → `years="%Y", months="%Y",
days="%Y"`; `%tm`/`%tq`/`%th` → `days="%b %Y"`; `%tc`/`%tC` → `hours="%d %b %H:%M"`).

**TR-15.19 — Convert `range()` bounds.** `dash_render.py:9747-9773`: when the axis is a date
axis, convert `_lo`/`_hi` from `_parse_scale_range` (`dash_render.py:776`) through the same
millisecond path before constructing `Range1d`, and convert the data-derived fallback bound
at `:9765-9770` instead of `pd.to_numeric`.

**TR-15.20 — `#N` on a date axis.** Covered by TR-15.11: the count branch must produce a
`DatetimeTicker(desired_num_ticks=N)` when the axis is a `DatetimeAxis`.

### Test infrastructure

**TR-15.21 — Ground truth.** `test/fixtures/axis_truth.json` holds 233 probes
(`_meta.counts.measured == 233`) in groups `axis_label`, `axis_scale`, `legend`, `refline`,
`titles`, over `sysuse auto` and `sysuse nlsw88`. It has **no probe** whose command contains
`to`, `/` or `##` in a label option, and **no date probe at all** (neither dataset carries a
`%t*` variable). `scripts/extract_axis_truth.do` must gain: `xlabel(10/15)`,
`ylabel(10 15 to 40)`, `xlabel(##5)`, `xscale(log) xlabel(#5)`, `xlabel(1000 2000, axis(2))`,
and a date group built on a generated `%td`/`%tm`/`%ty` variable covering explicit ticks,
`minmax`, `#N`, `format(%tdDD/NN/CCYY)` and `xscale(range())`. Probe records carry
`command`, `x_axis.tick_values`, `x_axis.tick_labels`, `x_axis.mapping.space`,
`n_gridlines`, `axis_line_px` and `all_text_elements`, which is everything the assertions
below need. `test/fixtures/date_truth.json` already holds per-kind epochs and
value→ISO tables (`date_formats["%td"]["values"][*]["value"]` / `["iso"]`) and can pin the
millisecond conversion without any new Stata run.

**TR-15.22 — The fixture must be read.** `test/test_axis_options.py` defines the `truth`
fixture at `:41` and ten tests take it (`:136, 152, 157, 171, 311, 316, 329, 430, 473, 587`);
none indexes it. Each must compare against
`truth["probes"][<probe>]["x_axis"]["tick_values"]` (or `y_axis`) and, where the probe has
them, `["tick_labels"]`. `_meta.caveats` records that tick values are recovered by parsing
the rendered label back to a number and are `null` for non-numeric labels — assertions must
handle `null` rather than assume every probe has values (`a_none`, `a_pairs`, `b_off` are the
cases, listed in the fixture's `unverified` block).

---

## Work items

The nine items handed to this phase, numbered exactly as given. Nothing merged, nothing
summarised.

---

**Item 1 — `minmax` from the active view.** `[func · both · S]` · origin `09-02` · Appendix B

> Compute `xlabel(minmax)` from the graph's active view rather than the whole frame — the
> same defect 09-07 fixed for `_compute_secondary_range`, still present here.

*Where:* `dash_render.py:9134-9143` (the `mode == "minmax"` branch reads `self.df[varname]`);
the fix pattern already in the file is `_source_frame(source, self.df)` as used at
`dash_render.py:9678` and `:9713`; `_apply_axis_spec` (`dash_render.py:9112`) would need the
source or frame passed in from the call site at `dash_render.py:9913`.

*Evidence:* the `minmax` branch and the 09-07 precedent are quoted in full under
**Why this phase exists §1**. Requirements: BR-15.1, TR-15.1, TR-15.2.

---

**Item 2 — the secondary scales report nothing.** `[func · standalone · S]` · origin `09-02` · Appendix C

> `xscale2()`/`yscale2()` never pass through `_report_unhandled_scale_opts`, so
> `noextend`/`extend`/`alt`/`fextend` on a secondary axis is dropped in total silence while
> the same token on the primary axis warns. Auditor item 5 names only the missing `range()`
> support on the secondary scales.

*Where:* `dash_render.py:9683` and `dash_render.py:9718` (add the
`_report_unhandled_scale_opts(raw, 'yscale2'/'xscale2')` call, helper at
`dash_render.py:805`).

*Evidence:* the helper's full body and its single call site are quoted under **§2**; the two
secondary call sites confirmed at HEAD:
`9683: _y2_log, _y2_rev = _parse_scale_opt(_y2_scale_raw)` and
`9718: _x2_log, _x2_rev = _parse_scale_opt(_x2_scale_raw)`. Requirements: BR-15.6, TR-15.8.

---

**Item 3 — three numlist rules Stata accepts.** `[func · both · M]` · origin `09-02` · Appendix C

> Three numlist rules Stata accepts are unimplemented and silently produce the wrong ticks or
> none: `a/b` (10/15), `a b to c` (10 15 to 40) and `##N` (##5). `_parse_axis_spec`
> (`dash_render.py:9305`) handles only `a(b)c`, `#N`, `minmax`, `none` and bare values, so
> `/` and `##` fall through to the default ticker and `to` degrades as described in the leak
> item. The task's `<done>` is "Axis labelling accepts what twoway accepts and produces what
> twoway produces".

*Where:* `dash_render.py:9305 DashRenderer._parse_axis_spec` (add `/` and `to` rules next to
the existing `a(b)c` regex, and `##N` beside the `#N` branch); mirror into
`dash_render.py:13989 _parse_axlabel`.

*Evidence:* **§4** — the four recognisers present in the method at HEAD, and the measured
absence of any `to` / `/` / `##` probe in the 233-probe fixture. Requirements: BR-15.10,
TR-15.12, TR-15.13, TR-15.14, TR-15.21.

---

**Item 4 — `_apply_axis_spec` has no date awareness.** `[func · both · L]` · origin `09-02` · Appendix C

> `_apply_axis_spec` has no date awareness, so every `axis_label` and `axis_scale` form is
> wrong on a `%t*` axis. The renderer converts date columns to datetime64
> (`dash_render.py:8196-8210`) and Bokeh's DatetimeAxis works in epoch MILLISECONDS, but:
> explicit ticks are passed through as raw Stata date numbers; `minmax` emits
> `float(vals.min())` of a datetime column, i.e. MICROseconds (1000x too large); `#N`
> replaces the DatetimeTicker with a BasicTicker; `format(%td...)` is silently ignored (the
> `elif spec["format"] and _stata_date_kind(fmt) is None` guard at `:9166` suppresses even
> the warning); and `xscale(range())` builds a Range1d in date units. The helper that knows
> the answer, `_figure_date_kind` (`dash_render.py:9268`), is never consulted here.

*Where:* `dash_render.py:9112 _apply_axis_spec` (minmax `:9137-9144`, count `:9145-9148`,
explicit `:9149-9158`, fmt `:9160-9170`); `dash_render.py:9268 _figure_date_kind`;
`dash_render.py:9747-9773` (the xscale/yscale range block); helpers
`dash_render.py:271 _stata_date_kind`, `:290 _stata_dates_to_datetime`.

*Evidence:* the five-clause confirmation table and the suppressed-warning block under **§5**,
including the measured `980380800000000.0` µs vs `980380800000` ms for `%td` day 15000.
Requirements: BR-15.11, BR-15.12, TR-15.15–TR-15.20.

---

**Item 5 — `#N` overwrites the axis's ticker class.** `[func · standalone · S]` · origin `09-02` · Appendix C

> `#N` and explicit ticks overwrite the axis's own ticker class, so `xscale(log) xlabel(#5)`
> puts LINEAR tick placement on a log axis. `_apply_axis_spec`'s count branch assigns a bare
> `BasicTicker(desired_num_ticks=N)` with no regard for the LogAxis/DatetimeAxis already
> built.

*Where:* `dash_render.py:9145-9148` in `_apply_axis_spec`
(`axis_obj.ticker = BasicTicker(desired_num_ticks=spec["count"])`) — choose
`LogTicker`/`DatetimeTicker` by `type(axis_obj)`.

*Evidence:* the count branch and the "axis type is decided ONCE" comment at
`dash_render.py:9577-9586`, both quoted under **§3**; probes `b_xlog` (`mapping.space ==
"log10"`), `a_hash5` (4 ticks) and `a_hash10` (8 ticks). Requirements: BR-15.9, TR-15.11.

---

**Item 6 — `minmax` reads the wrong rows and the wrong variable.** `[func · standalone · S]` · origin `09-02` · Appendix C

> `minmax` is computed from the wrong rows and the wrong variable: `_apply_axis_spec` reads
> `self.df[varname]` — the WHOLE dataset — so a graph-level `if`/`in` qualifier is ignored,
> and `varname` is `plots[0]`'s x/y variable (`dash_render.py:9506-9507`), so a two-series
> graph labels the axis at the FIRST series' bounds. Nothing recomputes it when a filter
> widget moves either, because the ticks are baked into a FixedTicker at build time. The
> one-bound fallback for `xscale(range(0))` at `dash_render.py:9765-9770` reads the same
> unfiltered frame.

*Where:* `dash_render.py:9137-9144` in `_apply_axis_spec`; the `varname` passed at
`dash_render.py:9913`; `dash_render.py:9506-9507` (`xvar`/`yvar` = `plots[0]`); the range
fallback at `dash_render.py:9765-9770` — use the graph's filtered frame
(`self._apply_graph_filter(g)`) and the union of the axis's variables.

*Evidence:* **§1**, including the `xvar`/`yvar` assignment and the `range()` fallback, both
quoted at HEAD. `_apply_graph_filter` is defined at `dash_render.py:8603` and returns a
filtered copy of `self.df` from the graph's `if`/`in` qualifiers.
Requirements: BR-15.1, BR-15.2, BR-15.3, BR-15.4, TR-15.1–TR-15.5.
*Note:* the "filter widget moves" clause is a statement of scope, not a task — ticks stay
baked at build time; recomputing on widget movement is not in this phase.

---

**Item 7 — only five scale sub-options are recognised; `off` is one of the casualties.** `[func · both · S]` · origin `09-02` · Appendix C

> Only five `xscale()`/`yscale()` sub-options are recognised; the rest are dropped with no
> warning, including `off`, which in Stata removes the axis entirely.
> `_report_unhandled_scale_opts` lists exactly `noextend`/`extend`/`alt`/`fextend`/`nofextend`,
> so `yscale(off)`, `noline`, `titlegap()`, `lcolor()/lwidth()/lpattern()` and `axis(#)` pass
> through in silence — the opposite of the honesty rule the same function was added to
> satisfy. `off` is a two-line implementation (`axis_obj.visible = False`).

*Where:* `dash_render.py:805 _report_unhandled_scale_opts` (extend the token list);
`dash_render.py:9747-9773` (apply `off`); server side has neither (see the auditor's server
range item).

*Evidence:* the helper's body under **§2**, plus probe `b_off`'s measurement table — canvas
texts `['2,000','3,000','4,000','5,000','Weight (lbs.)']`, four surviving gridlines, a 45-unit
axis-line stub. Requirements: BR-15.5, BR-15.7, TR-15.6, TR-15.7.

---

**Item 8 — `axis_label` sub-options dropped; `axis(#)` misrouted.** `[func · both · S]` · origin `09-02` · Appendix C

> `axis_label` sub-options outside the implemented five are silently dropped, and `axis(#)`
> is actively misrouted: `xlabel(1000 2000, axis(2))` applies the ticks to the PRIMARY x axis
> instead of the second one. `_parse_axis_spec` strips
> `labcolor/labgap/tlength/labstyle/tstyle/tposition` into the bin and truncates at the first
> sub-option comma, so `valuelabel`, `alternate`, `notick`, `add`, `custom` and
> `angle(stacked)` vanish with no report.

*Where:* `dash_render.py:9305 _parse_axis_spec` (the sub-option strip regex, ~`:9344-9350`);
`dash_render.py:904 _parse_axis_angle`; route `axis(2)` to the secondary-axis code at
`dash_render.py:9699`/`:9734` or report it.

*Evidence:* the strip regex and comma-truncation rule, quoted at HEAD under **§2**.
Requirements: BR-15.8, TR-15.9, TR-15.10.

---

**Item 9 — the ground-truth fixture is never read; the date test is vacuous.** `[deli · n/a · M]` · origin `09-02` · Appendix C

> The Stata ground-truth fixture is requested by the axis tests and never read: ten tests take
> the `truth` fixture and not one indexes it, so every assertion is hardcoded to dash's own
> numbers rather than to what Stata measured. In particular no test asserts tick LABEL text,
> which is why the missing default display format (item 3) and the `to` leak (item 1) went
> unnoticed. And `test_a_date_axis_ignores_a_numeric_format_gracefully`
> (`test/test_axis_options.py:218`) asserts only `fig is not None`, on `_SCATTER` — a frame
> with no date column at all — so the date path has no coverage whatsoever.

*Where:* `test/test_axis_options.py:136,152,157,171,218` (and the other truth-taking tests);
`test/fixtures/axis_truth.json`.

*Evidence:* the two tests quoted verbatim under **§6**; the fixture-taking test lines
confirmed at `:136, 152, 157, 171, 311, 316, 329, 430, 473, 587` with zero `truth[...]`
subscripts in the file. Requirements: BR-15.13, BR-15.14, TR-15.21, TR-15.22.
*Note on the item's cross-references:* its "item 3" and "item 1" are the *Appendix C*
numbering for the default-display-format gap (this repo's **Phase 14 item 4**) and the
bare-token `to` leak (**Phase 16 item 7**). The fixture work here is what makes both of
those provable, which is why it sits in this phase rather than with either of them.

---

## Test plan

Rule 8 governs the order: **the regression test is written first and must fail at
`ca5fe35`.** Rule 4 governs the breadth: every function this phase adds or changes gets a
unit test. Every test below names the file it goes in and the mutation that must kill it —
a test that survives its mutation is vacuous and does not count as done.

Harness in place today: `test/test_axis_options.py` builds figures through
`_fig_with_gopts(plots, gopts, df=None)` (`:67`) over the deterministic `_auto()` frame
(`:48`, `weight` 1760–4840, `mpg` 12–41, `price` 3291–15906), with `_ticker_of(fig, axis)`
(`:101`) and `_fixed_ticks(fig, axis)` (`:106`) as accessors, and `make_dr` / `make_spec` /
`make_data_json` from `test/conftest.py` (`:246`, `:152`, `:205`) for full-spec builds.

### Epic 15-A — `minmax` (items 1, 6)

| # | test | file | kind |
|---|---|---|---|
| A1 | **Failing test first.** `test_minmax_uses_the_filtered_rows` — build a spec whose graph carries `if_expr` restricting to `foreign==1`, with `xlabel(minmax)`; assert `_fixed_ticks(fig) == [<subset min>, <subset max>]`. | `test/test_axis_options.py` | regression (rule 8) |
| A2 | **Failing test first.** `test_minmax_spans_every_series_on_the_axis` — two `scatter` layers sharing the y axis (`mpg`, `price`); assert `_fixed_ticks(fig, "y") == [12.0, 15906.0]`. | `test/test_axis_options.py` | regression (rule 8) |
| A3 | **Failing test first.** `test_one_bound_range_uses_the_filtered_rows` — `if_expr` + `xscale(range(0))`; assert `fig.x_range.end` is the subset maximum. | `test/test_axis_options.py` | regression (rule 8) |
| A4 | `test_minmax_matches_the_stata_probe` — rewrite `test_minmax_is_two_ticks_at_the_data_bounds` (`:136`) to read `truth["probes"]["a_minmax"]["x_axis"]["tick_values"]`, and add the `a_ymm` and `a_nl_minmax` probes as parametrized cases. | `test/test_axis_options.py` | ground truth (item 9) |
| A5 | `test_minmax_on_a_facet_keeps_the_common_axis` — a `by()` graph; assert every facet's `minmax` ticks are the graph-wide bounds. Pins BR-15.4 so TR-15.5 is not "improved" away later. | `test/test_axis_options.py` | guard |
| A6 | Unit: `_source_frame` round-trip for the new call path — a `ColumnDataSource` built from a filtered frame returns the filtered rows; an empty source falls back to `self.df` without raising. | `test/test_axis_options.py` | rule 4 |

**Non-vacuity (mutations).** A1: revert `_apply_axis_spec`'s frame argument to `self.df` —
A1 must fail. A2: pass `plots[0]`'s variable instead of the union — A2 must fail while A1
still passes (they are independent defects). A3: point the fallback back at `self.df` — A3
must fail. A4: change the asserted value to dash's old `[1800, 4080]`-style hardcode — the
test must fail against the probe, proving it is reading the fixture and not itself. A5:
apply the facet subset to `minmax` — A5 must fail.

### Epic 15-B — scales and sub-options (items 2, 5, 7, 8)

| # | test | file | kind |
|---|---|---|---|
| B1 | **Failing test first.** `test_unsupported_scale_suboptions_are_reported` already exists at `test/test_axis_options.py:258` for `noextend`; extend it, parametrized, over `noline`, `titlegap(2)`, `lcolor(red)`, `lwidth(thick)`, `lpattern(dash)` — each must raise a `UserWarning` naming the option. | `test/test_axis_options.py` | regression |
| B2 | **Failing test first.** `test_secondary_scale_suboptions_are_reported` — `yscale2(noextend)` and `xscale2(alt)` on a two-axis spec must warn with `yscale2`/`xscale2` in the message. | `test/test_axis_options.py` | regression |
| B3 | **Failing test first.** `test_scale_off_removes_the_axis` — `yscale(off)`; assert `fig.yaxis[0].visible is False` **and** `fig.ygrid[0].grid_line_color is not None`, the second half taken from probe `b_off` (4 surviving gridlines). | `test/test_axis_options.py` | regression |
| B4 | **Failing test first.** `test_axis_2_never_lands_on_axis_1` — `xlabel(1000 2000, axis(2))`; assert the primary x ticker is **not** a `FixedTicker[1000, 2000]`, and that either the secondary axis carries it or a warning names `axis(2)`. | `test/test_axis_options.py` | regression |
| B5 | **Failing test first.** `test_unsupported_label_suboptions_are_reported` — parametrized over `labcolor(red)`, `labgap(2)`, `tlength(1)`, `valuelabel`, `alternate`, `notick`, `add`, `custom`, `angle(stacked)`; each warns. | `test/test_axis_options.py` | regression |
| B6 | **Failing test first.** `test_hash_n_keeps_a_log_axis_logarithmic` — `xscale(log) xlabel(#5)`; assert `isinstance(_ticker_of(fig), LogTicker)` and `desired_num_ticks == 5`, and that `fig.xaxis[0]` is still a `LogAxis`. | `test/test_axis_options.py` | regression |
| B7 | `test_hash_n_keeps_a_date_axis_datetime` — `%td` frame + `xlabel(#5)`; assert `DatetimeTicker` and `DatetimeAxis`. | `test/test_dates.py` | regression |
| B8 | Unit: `_report_unhandled_scale_opts` — one case per token in the extended list, plus a negative case proving `off` does **not** warn (it is implemented) and that a variable *named* e.g. `alt` in an unrelated option does not trigger a false positive. | `test/test_axis_options.py` | rule 4 |
| B9 | Unit: `_parse_axis_spec` returns the dropped-sub-option list (TR-15.9) for each of B5's inputs, and an empty list for `format()`/`labsize()`/`angle()`/`grid`/`nogrid`. | `test/test_axis_options.py` | rule 4 |

**Non-vacuity (mutations).** B1/B2/B5: delete one token from the reporter's list (or remove
one `_report_unhandled_scale_opts` call) — the parametrized case for it must fail while the
others pass. B3: change `visible = False` to a no-op — B3 fails; additionally set
`grid_line_color = None` alongside it — the gridline half of B3 fails, which is what stops a
developer implementing `off` as "hide everything". B4: route `axis(2)` to the primary axis —
B4 fails. B6/B7: restore the bare `BasicTicker` — both fail; restore it only for the log case
and B7 still passes, so the two axis types are pinned independently.

### Epic 15-C — numlist rules, dates and the fixture (items 3, 4, 9)

| # | test | file | kind |
|---|---|---|---|
| C1 | **Fixture first (blocks C2–C4).** Add probes to `scripts/extract_axis_truth.do` for `xlabel(10/15)`, `ylabel(10 15 to 40)`, `xlabel(##5)`, `xscale(log) xlabel(#5)`, `xlabel(1000 2000, axis(2))` and a date group (`%td`/`%tm`/`%ty` × explicit ticks / `minmax` / `#N` / `format(%tdDD/NN/CCYY)` / `xscale(range())`); regenerate `test/fixtures/axis_truth.json` and bump `_meta.counts`. | `scripts/extract_axis_truth.do`, `test/fixtures/axis_truth.json` | ground truth |
| C2 | **Failing test first.** `test_slash_numlist` — `xlabel(10/15)` → ticks `[10,11,12,13,14,15]`, asserted against the new probe. | `test/test_axis_options.py` | regression |
| C3 | **Failing test first.** `test_to_numlist_and_no_stray_label` — `ylabel(10 15 to 40)` → ticks `[10,15,20,25,30,35,40]` **and** `"to" not in` the figure's `major_label_overrides` values nor in any `CustomJSTickFormatter` code on that axis. The second assertion is the BR-09.2 leak guard shared with Phase 16 item 7. | `test/test_axis_options.py` | regression |
| C4 | **Failing test first.** `test_double_hash_numlist` — `xlabel(##5)` against the measured probe; must not silently fall through to the default ticker. | `test/test_axis_options.py` | regression |
| C5 | **Failing test first.** `test_explicit_date_ticks_are_milliseconds` — a `%td` frame (`formats={"d": "%td"}`) with `xlabel(15006 15371)`; assert the `FixedTicker` ticks equal the epoch-millisecond values, cross-checked against `date_truth.json`'s `date_formats["%td"]` value→ISO table. | `test/test_dates.py` | regression |
| C6 | **Failing test first.** `test_date_minmax_is_milliseconds_not_microseconds` — `%td` frame + `xlabel(minmax)`; assert the ticks are the ms bounds and **specifically** that neither is 1000× the expected value. | `test/test_dates.py` | regression |
| C7 | **Failing test first.** `test_a_numeric_format_does_not_replace_the_date_formatter` — `%td` frame + `xlabel(, format(%9.0fc))`; assert the axis formatter is still a `DatetimeTickFormatter`. | `test/test_dates.py` | regression |
| C8 | **Failing test first.** `test_a_date_picture_is_honoured_or_reported` — `xlabel(, format(%tdDD/NN/CCYY))`; assert either a `DatetimeTickFormatter` reflecting it, or a `UserWarning` naming the format. Silence fails. | `test/test_dates.py` | regression |
| C9 | **Failing test first.** `test_scale_range_on_a_date_axis_is_milliseconds` — `%td` frame + `xscale(range(15006 15371))`; assert `fig.x_range.start`/`.end` are the ms values. | `test/test_dates.py` | regression |
| C10 | **Replace the vacuous test.** Rewrite `test_a_date_axis_ignores_a_numeric_format_gracefully` (`test/test_axis_options.py:218`) so it builds a frame that carries a `%t*` column and asserts a property, not `fig is not None`. | `test/test_axis_options.py` | item 9 |
| C11 | **Read the fixture.** Rewrite each of the ten truth-taking tests (`:136, 152, 157, 171, 311, 316, 329, 430, 473, 587`) to index `truth["probes"][…]`, handling the `null` tick values the fixture's `unverified` block documents for `a_none`, `a_pairs` and `b_off`. | `test/test_axis_options.py` | item 9 |
| C12 | **Assert label text.** At least one test per label form must compare dash's rendered tick label strings to the probe's `tick_labels` — e.g. `a_minmax` → `["1,760","4,840"]`, `a_yfmt_price_c` → `["15,000","10,000","5,000","0"]`. Where dash cannot yet reproduce the text (the default display format is **Phase 14 item 4**), the test is written with an explicit `xfail(strict=True)` naming that phase, so it converts to a pass the moment 14 lands and fails loudly if it silently regresses. | `test/test_axis_options.py` | item 9 |
| C13 | Unit: the three new numlist recognisers in `_parse_axis_spec` — `a/b`, `a b to c`, `##N` — tested directly on the static method, including interaction cases (`10/15 20(10)50`, `10 15 to 40, format(%9.0f)`, a `/` inside a `format()` argument, a negative `-5/-1`). | `test/test_axis_options.py` | rule 4 |
| C14 | Unit: the date conversion path — `_stata_dates_to_datetime(…).astype("datetime64[ms]").astype("int64")` for each of the eight kinds against `date_truth.json`'s tables, plus the `%tm`/`%tq`/`%tw` out-of-range value that raises today (recorded as 08-04's second remaining item) so this phase does not widen that crash surface. | `test/test_dates.py` | rule 4 |
| C15 | Stata-side certification: add axis cases to `test/test_axis_options.cscript` — the file **Phase 14 item 6** creates (section 09-01 names it in `<files>` and it does not exist). Cover `xlabel(10/15)`, `ylabel(10 15 to 40)`, `yscale(off)`, `xlabel(minmax)` with an `if` qualifier, and a `%td` `xlabel()` end to end, asserting rc 0 and that the built HTML carries the expected ticks. Register it in `test/run_all_cscripts.do`; follow the preamble and `c(python_exec)` skip rule used by `test/test_option_surface.cscript`. **A skip is not a pass.** | `test/test_axis_options.cscript`, `test/run_all_cscripts.do` | integration |

**Non-vacuity (mutations).** C2/C3/C4: remove the corresponding recogniser from
`_parse_axis_spec` — that one case must fail and the others pass. C3 second half: re-enable
the bare-token label path — the "no stray `to` label" assertion must fail even though the
tick values are right, which is exactly the class of defect that slipped through before. C5:
drop the `.astype("datetime64[ms]")` step, leaving `pd.to_numeric` — C5 and C6 must fail with
a 1000× discrepancy. C7: restore the unconditional `NumeralTickFormatter` assignment — C7
fails. C8: restore the `_stata_date_kind(fmt) is None` suppression — C8 fails. C11/C12:
corrupt one value in the regenerated `axis_truth.json` — the tests reading it must fail,
proving they consult the fixture rather than their own literals.

### Suite-level

- `test/test_mode_parity.py` is **not** extended here: its axis cases are **Phase 16 item 6**.
  Anything this phase adds to `DashRenderer` that Phase 16 then ports must be re-asserted
  there, and the definition of done below records the handoff.
- Before committing, per CLAUDE.md rule 5: pull `main`, run the full pytest suite plus the
  cscript suite from `test/` with `arch -arm64`, and set `$dash_nobrowser` for any Stata run
  that builds a dashboard.

---

## Definition of done

A reviewer can tick these in order.

- [ ] `_apply_axis_spec` (`dash_render.py:9112`) receives the graph's active frame and the
      axis's date kind; the single call site at `:9913` supplies both.
- [ ] `minmax` reads the filtered frame (TR-15.2) and the union of the axis's variables
      (TR-15.3); the `range()` one-bound fallback at `:9765-9770` reads the same (TR-15.4).
- [ ] The `by()` facet case is unchanged and a test pins it (BR-15.4 / A5).
- [ ] `_report_unhandled_scale_opts` (`:805`) reports `noline`, `titlegap()`, `lcolor()`,
      `lwidth()`, `lpattern()` and `axis(#)` in addition to the original five.
- [ ] `xscale2()`/`yscale2()` call the reporter (`:9683`, `:9718`) with `xscale2`/`yscale2`.
- [ ] `xscale(off)`/`yscale(off)` hide the axis and leave the gridlines, matching probe `b_off`.
- [ ] Unimplemented `axis_label` sub-options are reported; `axis(2)` is routed or reported and
      never applied to the primary axis.
- [ ] The `count` branch chooses `LogTicker`/`DatetimeTicker`/`BasicTicker` by axis type; a
      log axis stays log and a date axis stays datetime under `#N`.
- [ ] `_parse_axis_spec` accepts `a/b`, `a b to c` and `##N`; `to` is consumed, never drawn.
- [ ] On a `%t*` axis: explicit ticks, `minmax` and `range()` are in epoch **milliseconds**;
      a numeric picture does not replace the `DatetimeTickFormatter`; a date picture is
      honoured or warned about.
- [ ] `scripts/extract_axis_truth.do` gained the `/`, `to`, `##N`, `log × #N`, `axis(2)` and
      date probes; `test/fixtures/axis_truth.json` regenerated with `_meta.counts` updated.
- [ ] All ten truth-taking tests in `test/test_axis_options.py` index the fixture; at least
      one asserts tick **label text**.
- [ ] `test_a_date_axis_ignores_a_numeric_format_gracefully` no longer asserts `fig is not None`
      and no longer runs on a date-free frame.
- [ ] Every fix has a regression test that was written first and fails at `ca5fe35` (rule 8);
      every new or changed function has a unit test (rule 4).
- [ ] Each test survives review against its named mutation.
- [ ] `test/test_axis_options.cscript` carries this phase's five Stata-side cases and is
      registered in `test/run_all_cscripts.do`; the run is a pass, not a skip.
- [ ] Full pytest + cscript suite green after a pull from local `main` (rule 5); committed to
      the feature branch with the merge command supplied, never to `main` (rule 6); commit
      message describes the code changes only (rule 7).
- [ ] Handoff recorded for **Phase 16**: the emitted parser `_parse_axlabel`
      (`dash_render.py:13989`) and the emitted `xscale`/`yscale` block still lack every fix in
      this phase unless Phase 16's port has already replaced them.

---

## Risks and sequencing notes

**1. Items 1 and 6 are one code change with two statements.** REMAINING.md records the
`minmax` defect in Appendix B (item 1, the `_source_frame` clause) and again in Appendix C
(item 6, which adds the wrong-variable and `range()`-fallback clauses). A developer who
implements only item 1 will pass a filtered-frame test and still label a two-series graph at
the first series' bounds. Implement TR-15.1 through TR-15.4 as a unit and keep tests A1, A2
and A3 separate so partial work is visible.

**2. Item 4 overlaps two items in Phase 10 — coordinate before writing code.** Phase 10
(`Dates II`) carries, from the 08-04 backlog, *"Convert user-supplied Stata date values to
the datetime axis's millisecond scale in `xlabel()`/`ylabel()` explicit tick lists and in
`minmax`, and in `xscale(range())`/`yscale(range())`"* and *"Give `_apply_axis_spec` a date
branch"*. Item 4 here is the superset: it adds the `#N` ticker-class clause and the
`_figure_date_kind` wiring. They touch the same eight lines of `_apply_axis_spec`. Land them
together, or let whichever phase runs first implement the whole of TR-15.15–TR-15.20 and the
other verify rather than re-implement. Shipping both independently will produce a merge
conflict in `:9137-9170` and, worse, two different millisecond conversions.

**3. The `both` tag does not mean "do it twice in this phase".** Items 3, 4, 7 and 8 are
tagged `both`, but the emitted server app has no `_apply_axis_spec` at all — Appendix B
measures `_parse_axis_label` as occurring "4× in the renderer and **0×** in the emitted app",
and Appendix B's comparison table records the server answer for `minmax`, `none`,
`format()`, `angle()` and `2000(500)4000` as a bare `BasicTicker` in every row. Phase 16 ports
the grammar wholesale, by emitting `_parse_axis_spec`/`_apply_axis_spec` the way
`_glyph_layer_lines` (`dash_render.py:12315`) already copies `GlyphMapper` in. The efficient
order is **15 then 16**: fix the standalone parser once and let the port carry it. If Phase 16
runs first for any reason, every fix here must also be mirrored into
`dash_render.py:13989 _parse_axlabel` by hand.

**4. `##N` needs a decision before it needs code.** No probe measures it, and its natural
home is the minor-tick option family that **Phase 14 item 2** implements
(`xmtick()`/`ymtick()`/`xmlabel()`/`ymlabel()`). Measure it (TR-15.21) and agree the
semantics with Phase 14 before implementing TR-15.14; a guessed tick count that passes a
self-referential test is exactly the failure mode item 9 exists to close.

**5. `axis(2)` routing depends on Phase 16.** The secondary-axis tick path
(`dash_render.py:9699`, `:9734`) still uses the *old* `_parse_axis_label_opt` — Phase 16 item 3
routes it through the new grammar. Routing `axis(2)` there before that lands would deliver
`xlabel(1000 2000, axis(2))` into a parser that drops `#N`, `minmax`, `format()` and
`labsize()`. Take the reporting branch (TR-15.10(b)) now and convert to routing in Phase 16.

**6. `off` must not take the gridlines with it.** Probe `b_off` is unambiguous: four
gridlines survive, the tick labels and axis title do not. Bokeh's `axis.visible = False` gets
this right; a "cleaner" implementation that also nulls `grid_line_color` silently contradicts
measured Stata. Test B3 asserts both halves for this reason.

**7. The date conversion is dtype-sensitive.** The loader emits `datetime64[us]`
(`_stata_dates_to_datetime`, `dash_render.py:290`), so `pd.to_numeric` gives microseconds —
measured, `%td` day 15000 → `980380800000000.0` against Bokeh's `980380800000`. Any fix that
relies on pandas' inferred resolution rather than an explicit
`.astype("datetime64[ms]").astype("int64")` will silently re-break when a column's resolution
differs. Pin it in C14.

**8. `_parse_axis_spec` is a `@staticmethod` and warnings need context.** Adding reporting
inside it (TR-15.9) tempts a developer to reach for `self`. Return the dropped list in the
spec dict and warn at the call site instead; this keeps the parser unit-testable in isolation
(test B9) and keeps the warning text able to name the actual option key.

**9. Item 9's cross-references use Appendix C's numbering, not this phase's.** Its "item 3"
is the default-display-format gap (**Phase 14 item 4**) and its "item 1" is the bare-token
`to` leak (**Phase 16 item 7**). Test C12's `xfail(strict=True)` is the mechanism that keeps
the label-text assertion honest across that phase boundary rather than silently deferring it.
