# Phase 14 — Axis grammar I: numlist rules and sub-options

**Purpose.** Task 09-02 built the `axis_label`/`axis_scale` grammar and, for the forms it
recognises, it works: `2000(500)4000`, `#5`, `minmax`, `none`, quoted value-label pairs,
`format()`, `labsize()`, `angle()` and `grid`/`nogrid` were all measured producing the right
Bokeh models. This phase fixes the four places where that grammar is wrong *about the tick
marks themselves*, in the standalone renderer and in `dash.ado`. (1) `xtick()`/`ytick()` are
treated as a second spelling of `xlabel()` — they draw **labelled** ticks, and they are
discarded outright whenever `xlabel()` is also present, where Stata draws **unlabelled** marks
*in addition to* the labelled ones. (2) `xmtick()`, `ymtick()`, `xmlabel()` and `ymlabel()` are
parsed by `dash.ado`, carried into the spec JSON, and read by nobody — `grep -c xmtick
dash_render.py` returns **0**. (3) The task's clause "when no `format()` is given, the
variable's Stata display format from S08" can never fire on a default axis, because the axis
loop `continue`s before reaching it, and would still not fire if it did, because
`_stata_numeric_pattern` rejects the `g` family and `%8.0gc` is `auto.dta`'s own format for
`weight` and `price`. (4) The `grid` sub-option paints a hardcoded `#e5e5e5` instead of the
scheme's gridline colour. The phase closes with the Stata-side certification script that
section 09-01 named and that has never existed — the reason a broken axis form can reach a
shipped dashboard while pytest is green. The server port of all of this is **Phase 16**; the
scale/minmax/date half of 09-02 is **Phase 15**.

---

## At a glance

| | |
|---|---|
| **Items** | 6 (numbered 1–6 below, exactly as handed over) |
| **Functional vs deliverable** | 5 functional · 1 deliverable |
| **Effort mix** | 2 × small · 4 × medium · 0 × large |
| **Renderers touched** | `both` on items 1–4 (the standalone fix plus the `dash.ado` half; the *server* copy of each is Phase 16), `standalone` on item 5, `stata` on item 6. Files: `dash_render.py`, `dash.ado`, `dash.sthlp`, `test/` |
| **Ultraplan tasks discharged** | `09-02` — the tick-semantics, minor-tick, default-display-format and `grid`-colour clauses, plus 09-01's missing `<files>` entry `test/test_axis_options.cscript`. Section **S09**. |
| **Not discharged here** | 09-02's numlist rules (`a/b`, `a b to c`, `##N`), `minmax` source frame, ticker-class preservation, scale sub-options and the date axis → **Phase 15**. The whole `ServerAppBuilder` port, the secondary axes and the parity-corpus axis cases → **Phase 16**. The four help sentences → **Phase 30** (but see Risks: item 2's help edit **cannot** wait). |
| **Depends on** | Nothing at HEAD. `self.numeric_formats` is already populated (`dash_render.py:8194-8205`), `self.scheme.grid_color` is already computed (`dash_render.py:1960-1963`) and applied (`:2180`), and `dash.ado` already transports all six option keys into `graph_options` (`dash.ado:1129`, `:1399`, `:1415`, `:1469`). |
| **Unblocks** | **Phase 15** (every item there edits `_parse_axis_spec`/`_apply_axis_spec`, the same two functions) and **Phase 16**, which ports `_apply_axis_spec` into the emitted app via `inspect.getsource` — porting before this phase copies all four defects into `dash serve`. |
| **Source of items** | Items 1, 2, 3: REMAINING.md **Appendix B**, `09-02`. Items 4, 5, 6: REMAINING.md **Appendix C**, `09-02` (19 further items). Items 3 and 4 are the same gap stated twice — B's summary and C's two-cause decomposition; they are implemented once, together. |

---

## Why this phase exists

### What the plan asked for

09-02's `<done>` condition, as quoted by REMAINING.md Appendix C:

> "Axis labelling accepts what twoway accepts and produces what twoway produces"

and the format clause, as quoted by Appendix A:

> *"Numeric tick labels must honour `format()` and, when none is given, the
> variable's Stata display format from S08."*

### What the audit measured — REMAINING.md, Appendix A, `09-02 · PARTIAL`

Copied verbatim:

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
>
> **Remaining:**
> 1. **Tick labels ignore the variable's Stata display format.** The task:
>    *"Numeric tick labels must honour `format()` and, when none is given, the
>    variable's Stata display format from S08."* Measured with
>    `formats={'weight': '%9.0fc'}` and no `format()` sub-option: the formatter
>    stays `BasicTickFormatter`. Only an explicit `format()` works.
> 2. **`xmtick()` `ymtick()` `xmlabel()` `ymlabel()` are not implemented** — all
>    four leave a default `BasicTicker` and are reported as unsupported options.
>    (They are also in 05-04's undeclared list, so that work comes first.)
> 3. **Server mode has no axis-label grammar at all**: `_parse_axis_label` occurs
>    4× in the renderer and **0×** in the emitted app.

Note the line "`xtick()`/`ytick()` work" in the measured table: they *run*, they do not
*mean what Stata means*. Appendix C's adversarial pass is what caught that, and the row
`, grid` → `#e5e5e5` in the same table is the literal item 5 is about. The third remaining
item is Phase 16's, not this phase's.

### The option surface counts these four — REMAINING.md, main body §2

> | plan disposition | total | honoured | accepted + reported ignored |
> |---|---:|---:|---:|
> | accept-and-report | 4 | 0 | 4 ✅ *as intended* |
> | implement-S06 | 3 | 0 | **3** |
> | implement-S07 | 25 | 12 | **13** |
> | implement-S09-axes-text | 28 | 2 | **26** |
> | implement-S09-style | 50 | 3 | **47** |
> | implement-S10 | 5 | 2 | **3** |
> | **total** | **115** | **19** | **96** |
>
> **0 rejections.** […] **92 options the plan said to implement are only accepted
> and reported**, so their values never reach the spec.
>
> Not implemented, by family:
>
> - **S09 axes/text (26):** `b1title` `b2title` `droplines` `l1title` `l2title`
>   `r1title` `r2title` `t1title` `t2title` `text` `tlabel` `tline` `tmlabel`
>   `tmtick` `tscale` `ttext` `ttick` `ttitle` **`xmlabel` `xmtick`** `xvarformat`
>   `xvarlabel` **`ymlabel` `ymtick`** `yvarformat` `yvarlabel`

Four of those 26 are item 2. Implementing them moves the `implement-S09-axes-text` row from
2 honoured to 6, and it moves those four option keys out of dash's own
"unsupported option(s) ignored" note — which is a *reporting contract* change with tests
attached (see TR-14.12).

The status table records the same thing per section:

> | 09 | Axes, legend, titles | 7 | 1 done, 6 partial ②, **73 options open** ① | see §2 — largest single family; none of S09 reached `ServerAppBuilder` |

### Stata's own measurements are already in the repo

`test/fixtures/axis_truth.json` — 233 probes, `generated_by: scripts/extract_axis_truth.do`,
measured from Stata's SVG export on `sysuse auto` (viewBox `0 0 5400 3240`, 14.4 SVG units =
1 point). Four of its probes are the ground truth for this phase, and no test currently reads
any of them (that debt is Phase 15 item 9; this phase is the first consumer):

| probe | Stata command | `n_ticks` on x | `tick_values` (recovered from the label text) | tick label text drawn |
|---|---|---:|---|---|
| `a_default` | `twoway scatter mpg weight` | 4 | `[2000, 3000, 4000, 5000]` | `2,000` `3,000` `4,000` `5,000` |
| `a_ticks_only` | `twoway scatter mpg weight, xtick(2500 3500)` | **6** | `[2000, None, 3000, None, 4000, 5000]` | unchanged — still only the four |
| `a_mticks` | `twoway scatter mpg weight, xmtick(2250 2750 3250)` | **7** | `[2000, None, None, 3000, None, 4000, 5000]` | unchanged — still only the four |
| `a_mlabel` | `twoway scatter mpg weight, xmlabel(2500 3500)` | **6** | `[None, 2500, None, 3500, None, None]` | the four **plus** `2,500` and `3,500` |
| `a_ydefault_price` | `twoway scatter price weight` | (y) | — | y: `0` `5,000` `10,000` `15,000` |

`_meta.caveats` states the rule that makes the `None`s meaningful:

> "Tick VALUES are recovered by parsing the rendered tick LABEL back to a number. Where a
> label is not numeric […] the value is null and only the exact pixel position is reported."

So a `None` in `tick_values` at a recorded `tick_px` **is** an unlabelled tick mark. That is
the whole of item 1 and half of item 2, measured by Stata:

- `xtick(2500 3500)` → **two extra marks, no extra text**. Tick pixels
  `[936.39, 1649.53, 2362.67, 3075.81, 3788.94, 5215.39]`; the two new ones (1649.53,
  3075.81) carry no label.
- `xmtick(2250 2750 3250)` → **three extra marks, no extra text**.
- `xmlabel(2500 3500)` → two extra marks **with** text, and the four major labels stay.
- The minor labels are drawn smaller: `2,500` and `3,500` at `font_size` **67.5**, the
  majors at **112.56** — a ratio of **0.5996**, i.e. 0.6× — and closer to the axis
  (`y = 2858.71` vs `2912.86`, a 54.15-unit / ≈3.76pt shorter standoff).
- `a_default` and `a_ydefault_price` are the format clause: with **no** `xlabel()` and **no**
  `format()` at all, Stata draws `2,000 3,000 4,000 5,000` and `0 5,000 10,000 15,000`.
  Those commas come from `auto.dta`'s own `%8.0gc` display format on `weight` and `price`.
  dash draws `2000`, `3000`, `4000`, `5000`.

### The code, at HEAD

**The axis loop** — `dash_render.py:9900-9913`, inside `_make_figure_body` (which starts at
`:9495`), verbatim:

```python
        # Custom axis tick values (xlabel / ylabel) and label rotation
        from bokeh.models.tickers import FixedTicker
        from bokeh.models.formatters import CustomJSTickFormatter
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

Three defects are visible in those fourteen lines:

1. `raw_ax or raw_tick` — `xtick` is only consulted when `xlabel` is **absent**, and when it
   *is* consulted its positions go through the same `_apply_axis_spec` path that installs a
   `FixedTicker` **with labels**. `xlabel(2000(1000)5000) xtick(2500 3500)` silently loses the
   two marks; `xtick(2500 3500)` alone silently *replaces* Stata's four labelled ticks with two
   labelled ticks at 2500 and 3500.
2. `if not raw_ax and not raw_tick: continue` — the default axis never reaches
   `_apply_axis_spec`, so the S08 display-format fallback inside it is dead code for
   `dash scatter mpg weight`.
3. There is no `xmtick`/`ymtick`/`xmlabel`/`ymlabel` in the tuple, and none anywhere else:

```
$ grep -c 'xtick' dash_render.py      → 1     (line 9908, the ternary above)
$ grep -c 'xmtick' dash_render.py     → 0
$ grep -c 'ymtick' dash_render.py     → 0
$ grep -c 'xmlabel' dash_render.py    → 0
$ grep -c 'ymlabel' dash_render.py    → 0
```

The single `xtick` hit is also the proof for the parenthetical in item 1's *Where* — "server
side has no xtick read at all": the only occurrence in the 16,000-line file is at `:9908`,
which is `DashRenderer`, above `class ServerAppBuilder` at `:12265`.

**The format fallback and the grid literal** — `dash_render.py:9159-9190`, inside
`_apply_axis_spec` (which starts at `:9112`), verbatim:

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
        ...
        if spec["grid"] is not None:
            for g in grid_obj:
                if spec["grid"]:
                    if g.grid_line_color is None:
                        g.grid_line_color = "#e5e5e5"
                else:
                    g.grid_line_color = None
```

**The format parser** — `dash_render.py:374-415`, the two gates C's item names:

```python
    m = re.fullmatch(r"%(-)?(\d+)\.(\d+)(f|e)(c)?", fmt.strip())     # :389
    ...
    if kind != "f":                                                   # :411
        return None
    head = "0,0" if comma else "0"                                    # :413
```

`%8.0gc` does not even match the regex at `:389` — the alternation is `f|e`, so the `g`
family returns `None` from `_parse_stata_numeric_fmt` before the `kind != "f"` check at `:411`
is reached. That matters twice over, because the **loader** gates on the same helper
(`dash_render.py:8194-8205`):

```python
        for col in self.df.columns:
            if col in self.string_vars:
                continue
            kind = _stata_date_kind(self.formats.get(col))
            if kind is None:
                self.df[col] = pd.to_numeric(self.df[col], errors="coerce")
                pattern = _stata_numeric_pattern(self.formats.get(col))
                if pattern is not None:
                    self.numeric_formats[col] = self.formats[col]
                continue
```

So for `auto.dta`, `self.formats["weight"] == "%8.0gc"` but `self.numeric_formats` has **no**
`weight` key at all. Deleting the `continue` guard alone (cause 1) therefore changes nothing
visible: the fallback would look up an empty dict. Both causes must be fixed together, which
is why items 3 and 4 are one piece of work.

**The scheme already knows the right grid colour** — `dash_render.py:1960-1963` and the
chrome pass at `:2180-2185`, which runs at `:9606` (`self.scheme.apply_to_figure(fig)`), long
before the axis loop at `:9903`:

```python
        self.grid_color: str = self._color(
            "color major_grid",
            self._color("color grid", "#d9e8f0"),
        )
        self.minor_grid_color: str = self._color("color minor_grid", "#cccccc")
```

```python
        for grids, draw in ((fig.xgrid, self.draw_major_hgrid),
                            (fig.ygrid, self.draw_major_vgrid)):
            for grid in grids:
                grid.grid_line_color = self.grid_color if draw else None
```

The translated schemes in `schemes/` give, measured:

| scheme | `color major_grid` | what `xlabel(…, grid)` paints today |
|---|---|---|
| `s2color` | `#eaf2f3` (`color grid` also `#eaf2f3`) | `#e5e5e5` |
| `s1color` | `#e0e0e0` | `#e5e5e5` |
| `economist` | `#ffffff` | `#e5e5e5` |

The built-in fallback when a scheme names neither key is `#d9e8f0` — so `#e5e5e5` is not the
scheme's colour, not the package default, and on `economist` it is a visible grey grid where
Stata draws white. REMAINING.md's own framing:

> A style literal of exactly the kind the branch's recent commits claim to have removed from
> both renderers.

(The branch's last four commits are `Put the renderer's own glyph layer into the generated
app`, `Take the last style literals out of both renderers`, `Prove the drop-in claim by
rendering, not by parsing`, `Record which of the six remaining items are done`.)

**`dash.ado` already carries the keys, and still calls them unsupported.** The promotion loop
at `dash.ado:1125-1132` (and the identical lists at `:1395-1401`, `:1415-1421`, `:1465-1471`)
names them:

```
    foreach gkey in title subtitle note caption name saving xtitle ytitle xlabel ///
            ylabel xline yline legend by xscale yscale aspectratio scheme ///
            plotregion graphregion bgcolor plotbgcolor link filter ytitle2 ///
            xtitle2 ylabel2 xlabel2 yscale2 xscale2 xsize ysize fxsize fysize ///
            scale text hover xtick ytick xmtick ymtick xmlabel ymlabel t1title ///
```

while `dash.ado:381-384` (and `:629-632` in the other parser) still declare them pending:

```
    if `"`xmlabel'"' != "" local _dash_pending `"`_dash_pending' xmlabel"'
    if `"`xmtick'"' != ""  local _dash_pending `"`_dash_pending' xmtick"'
    if `"`ymlabel'"' != "" local _dash_pending `"`_dash_pending' ymlabel"'
    if `"`ymtick'"' != ""  local _dash_pending `"`_dash_pending' ymtick"'
```

REMAINING.md calls that "the honest state today" — the value is transported and then dropped,
and the user is told so. The dishonest part is the help, which is Phase 30's items 4 and 5 but
is *mechanically coupled* to this phase (Risks).

`test/fixtures/rejected_options.json` records the measured starting point for all six keys —
e.g. for `xmtick`:

```json
{"option": "xmtick", "takes_argument": true, "twoway_rc": 0, "dash_rc": 198,
 "dash_message": "option xmtick() not allowed",
 "disposition": "implement-S09-axes-text",
 "reason": "axis tick/minor-tick/minor-label placement. dash implements only xlabel()/ylabel() major ticks.",
 "probes": [{"id": "xmtick", "command": "twoway scatter mpg weight, xmtick(2000(250)5000) nodraw", ...}]}
```

and gives ready-made probe commands for every one of them: `xtick(2500 3500)`,
`ytick(10 20 30 40)`, `xmtick(2000(250)5000)`, `ymtick(10(5)40)`, `xmlabel(2000(250)5000)`,
`ymlabel(10(5)40)`.

### Why the suite is green

- `test/test_axis_options.py:213` pins the **wrong** semantics:

  ```python
      def test_xtick_is_honoured(self):
          fig, _ = _fig_with_gopts(_SCATTER, {"xtick": "2000 3000 4000"})
          from bokeh.models import FixedTicker
          assert isinstance(_ticker_of(fig), FixedTicker)
  ```

  A `FixedTicker` is exactly what a *labelled* tick list installs. The test passes on the
  defect and will fail on the fix — it must be rewritten as part of item 1, not deleted.
- No test asserts tick **label text**, which is why the missing default display format went
  unnoticed. Ten tests take the `truth` fixture and none indexes it (Appendix C, Phase 15
  item 9).
- `test/test_axis_options.py` builds `DashRenderer` figures only, via `_fig_with_gopts`
  (`:67`) — there is no Stata in the loop anywhere.
- **There is no cscript.** `grep -l "xlabel" test/*.cscript` does not reach the axis grammar;
  section 09-01 named `test/test_axis_options.cscript` in its `<files>` and the file does not
  exist. REMAINING.md, Appendix C:

  > nothing checks that dash.ado's `syntax` accepts and transports each axis_label form end to
  > end — which is how `ylabel(10 15 to 40)` reaches a shipped dashboard with a tick labelled
  > "to" while pytest is green.

  The repo has **25** cscripts at HEAD and REMAINING.md's gate line records "25/25 cscripts"
  passing; this phase makes it 26.

---

## Epics

| Epic | Goal | Items |
|---|---|---|
| **E14.1 — Tick marks, Stata's way** | Unlabelled ticks stop being labelled ticks, stop cancelling `xlabel()`, and the four minor-tick options stop being reported as unsupported and start drawing. | 1, 2 |
| **E14.2 — The default axis inherits the variable's format** | `dash scatter mpg weight` labels its x axis `2,000 3,000 4,000 5,000`, because `weight`'s own `%8.0gc` reaches the axis with no `xlabel()` written. | 3, 4 |
| **E14.3 — Scheme-true gridlines, proven from Stata** | The `grid` sub-option paints the scheme's colour, and a certification script proves every axis form survives `dash.ado`'s `syntax` and reaches the HTML. | 5, 6 |

---

## User stories

### E14.1 — Tick marks, Stata's way

**US-14.1.1** — *As a Stata user pasting a `twoway` command, I want `xtick()` to add
unlabelled tick marks to the axis my `xlabel()` already labels, so that the dashboard shows
the same tick structure as the graph I copied the command from.*

- **Given** `dash scatter mpg weight, xlabel(2000(1000)5000) xtick(2500 3500) name(g1)`
- **When** the dashboard is built
- **Then** the x axis carries **six** tick marks at 2000, 2500, 3000, 3500, 4000, 5000
- **And** exactly **four** of them carry text: `2,000`, `3,000`, `4,000`, `5,000`
- **And** no tick label reads `2500` or `3500`.

**US-14.1.2** — *As a Stata user, I want `xtick()` on its own to leave my labels alone, so
that adding tick marks does not silently delete the axis labelling.*

- **Given** `dash scatter mpg weight, xtick(2500 3500) name(g1)` (no `xlabel()`)
- **When** the dashboard is built
- **Then** the labelled ticks are the ones dash would have drawn without the option
- **And** two further, unlabelled marks appear at 2500 and 3500
- **And** the probe `a_ticks_only` in `test/fixtures/axis_truth.json` — 6 tick positions, 4
  numeric `tick_values` — is the acceptance oracle.

**US-14.1.3** — *As a Stata user, I want `xmtick()`/`ymtick()` to draw minor tick marks, so
that a command dash currently accepts-and-ignores produces the graph I asked for.*

- **Given** `dash scatter mpg weight, xmtick(2250 2750 3250) name(g1)`
- **When** the dashboard is built
- **Then** three unlabelled marks are drawn at 2250, 2750 and 3250 alongside the four default
  labelled ticks (probe `a_mticks`: `n_ticks == 7`)
- **And** dash prints **no** "unsupported option(s) ignored" note naming `xmtick`.

**US-14.1.4** — *As a Stata user, I want `xmlabel()`/`ymlabel()` to draw labelled minor ticks,
so that intermediate values are readable without overriding my major labels.*

- **Given** `dash scatter mpg weight, xmlabel(2500 3500) name(g1)`
- **When** the dashboard is built
- **Then** the four major labels remain (`2,000 3,000 4,000 5,000`)
- **And** two further labels `2,500` and `3,500` appear at the minor positions
- **And** their text size is 0.6× the major tick label size (measured: 67.5 / 112.56 = 0.5996)
- **And** the minor labels are formatted through the same display format as the majors
  (`2,500`, not `2500`).

**US-14.1.5** — *As a package maintainer, I want dash's unsupported-option note to stop naming
options dash now honours, so that the honesty contract in `test_option_surface.cscript` stays
true in both directions.*

- **Given** a command using `xmtick()`
- **When** dash runs it
- **Then** no line containing "unsupported option" names `xmtick`
- **And** `test/test_help_conformance.py::TestTheUnsupportedSectionIsTrue` passes — which
  requires `dash.sthlp`'s Unsupported section and `dash.ado`'s `_dash_pending` lists to be
  changed in the same commit.

### E14.2 — The default axis inherits the variable's format

**US-14.2.1** — *As a Stata user, I want the axis of a plain `dash scatter mpg weight` to be
labelled the way Stata labels it, so that a dashboard and a `twoway` graph of the same data
read the same.*

- **Given** `sysuse auto` (where `weight` and `price` both carry `%8.0gc`)
- **When** `dash scatter mpg weight, name(g1)` is built with no axis option at all
- **Then** the x axis ticks are formatted with thousands separators (`2,000`, not `2000`)
- **And** `dash scatter price weight` gives `0 5,000 10,000 15,000` on y (probe
  `a_ydefault_price`).

**US-14.2.2** — *As a Stata user, I want an explicit `format()` to keep winning over the
variable's display format, so that the sub-option I wrote is never overridden by a default.*

- **Given** `dash scatter mpg weight, xlabel(, format(%9.2f)) name(g1)`
- **When** the dashboard is built
- **Then** the x tick formatter is `NumeralTickFormatter(format='0.00')`
- **And** `weight`'s own `%8.0gc` is not consulted.

**US-14.2.3** — *As a dashboard viewer, I do not want a spurious warning in the log when dash
falls back to a format it cannot reproduce, so that warnings stay meaningful.*

- **Given** a variable whose display format dash cannot turn into a pattern, and **no**
  `format()` sub-option
- **When** the figure is built
- **Then** the ticks are unformatted and **no** `UserWarning` is emitted
- **And** the warning still fires when the user *did* write `format()`.

**US-14.2.4** — *As a package maintainer, I want the fallback to keep its hands off date and
string axes, so that fixing the numeric default does not regress S08's date work.*

- **Given** a `%td` variable on the x axis
- **When** the figure is built with no axis option
- **Then** no `NumeralTickFormatter` is installed on that axis
- **And** the date-axis behaviour is exactly what it is at HEAD (the date grammar itself is
  Phase 15 item 4).

### E14.3 — Scheme-true gridlines, proven from Stata

**US-14.3.1** — *As a dashboard viewer, I want `xlabel(…, grid)` to draw the scheme's
gridline, so that turning a grid on does not introduce a colour that belongs to no scheme.*

- **Given** `dash scatter mpg weight, scheme(economist) xlabel(2000 4000, grid) name(g1)`
- **When** the dashboard is built
- **Then** the x gridlines are `#ffffff` (economist's `color major_grid`)
- **And** with `scheme(s1color)` they are `#e0e0e0`, and with `s2color` `#eaf2f3`
- **And** the string `#e5e5e5` does not appear in `_apply_axis_spec`.

**US-14.3.2** — *As a package maintainer, I want a certification script that drives the axis
grammar from Stata, so that a form that `dash.ado`'s `syntax` mangles fails in CI rather than
in a user's dashboard.*

- **Given** `test/test_axis_options.cscript` registered in `test/run_all_cscripts.do`
- **When** the suite runs (`arch -arm64 … do test/run_all_cscripts.do` from `test/`)
- **Then** every axis form in the script returns `_rc == 0` from `dash`
- **And** each form's effect is asserted **in the built HTML**, not in the Stata locals
- **And** a form that does not reach the HTML fails the script with a named message.

---

## Business requirements

| ID | Requirement | How it is tested |
|---|---|---|
| **BR-14.1** | `xtick()`/`ytick()` add tick marks **without** labels and never remove or replace the labelled ticks produced by `xlabel()`/`ylabel()` or by the default ticker. | `a_ticks_only`: 6 marks, 4 labels. Unit + cscript. |
| **BR-14.2** | `xlabel()` and `xtick()` given together are both honoured; neither is discarded. | Unit test on the combined command. |
| **BR-14.3** | `xmtick()`/`ymtick()` draw unlabelled minor tick marks at the requested positions and are no longer reported as unsupported. | `a_mticks`: 7 marks, 4 labels; report assertion in the cscript. |
| **BR-14.4** | `xmlabel()`/`ymlabel()` draw **labelled** minor ticks at the requested positions, keeping the major labels, at 0.6× the major label size, formatted through the same display format. | `a_mlabel`: 6 marks, 6 labels, sizes 112.56/67.5. |
| **BR-14.5** | All four minor-tick options accept the whole `axis_label` numlist grammar this phase and Phase 15 support (`a(b)c`, bare lists, and the sub-options `labsize()`/`angle()` where they apply). | Unit tests per form; cscript probes from `rejected_options.json`. |
| **BR-14.6** | dash's "unsupported option(s) ignored" note never names an option dash honours, and always names one it drops. `dash.sthlp` agrees with `dash.ado` on which is which. | `test/test_help_conformance.py:352` and its sibling; `test_option_surface.cscript`. |
| **BR-14.7** | With no `format()` sub-option and no `xlabel()` at all, a numeric axis is labelled through the variable's Stata display format. | `a_default`, `a_ydefault_price`; unit + cscript. |
| **BR-14.8** | An explicit `format()` always takes precedence over the variable's display format; a fallback format that dash cannot reproduce is silent, and an explicit one still warns. | Unit tests, both directions. |
| **BR-14.9** | The display-format fallback never touches a date axis or a string/categorical axis. | Unit test on a `%td` frame. |
| **BR-14.10** | Every gridline dash draws takes its colour from the scheme; no axis code path contains a colour literal. | Scheme-parametrized unit test + a grep guard. |
| **BR-14.11** | Each axis option in this phase is proven to survive `dash.ado`'s `syntax`, the spec JSON and the renderer, end to end from Stata, by `test/test_axis_options.cscript`. | The cscript itself, registered in the runner. |
| **BR-14.12** | Nothing in this phase changes standalone behaviour for the forms Appendix A measured as working (`2000(500)4000`, `#5`, `minmax`, `none`, value-label pairs, `format()`, `labsize()`, `angle()`, `nogrid`). | The existing `TestAxisLabelGrammar` class must pass unchanged, except `test_xtick_is_honoured`, which is rewritten by item 1. |

---

## Technical requirements

### TR-14.1 — Separate the two tick channels in the axis loop  *(item 1)*

`dash_render.py:9903-9913`. Replace `spec = self._parse_axis_spec(raw_ax or raw_tick)` with two
independent reads, and remove the `or`:

- `raw_ax = graph_opts.get(ax_key, "")` → the **labelled** spec, parsed as today.
- `raw_tick = graph_opts.get(tick_key, "")` → a **tick-only** spec: parsed by the same
  `_parse_axis_spec` (so `xtick(2000(500)5000)` works), but applied through the new tick-only
  path in TR-14.2, never through the labelled path.
- Both may be present; each is applied. When only `raw_tick` is present the labelled ticker is
  left exactly as the scheme and Bokeh left it.
- The loop tuple grows to carry the minor keys (TR-14.3/TR-14.4). Suggested shape, one entry
  per axis: `(ax_key, tick_key, mtick_key, mlabel_key, axis_obj, grid_obj, var)`.

### TR-14.2 — A tick-only path in `_apply_axis_spec`  *(item 1)*

`_apply_axis_spec` is at `dash_render.py:9112`; its signature today is
`(self, fig, axis_obj, grid_obj, spec, varname="")`. Add a sibling
`_apply_tick_spec(self, fig, axis_obj, spec, varname="", labelled=False)` (or a `labelled`
keyword on the existing method — the constraint is that the tick-only path must **not** run
the `major_label_overrides`/`CustomJSTickFormatter` block at `:9149-9158`).

Confirmed against the installed Bokeh (**3.9.0**) — the two available mechanisms:

| mechanism | model support (verified) | use when |
|---|---|---|
| **A — `FixedTicker.minor_ticks`** | `FixedTicker.properties()` contains `ticks`, `minor_ticks`, `num_minor_ticks`. Minor marks render through the axis's `minor_tick_line_color` / `minor_tick_in` / `minor_tick_out`, and Bokeh draws **no labels** on minor ticks. | The axis already ends up with a `FixedTicker` — i.e. `xlabel()` supplied an explicit/increment/`minmax` list. Put the `xtick`/`xmtick` positions in `minor_ticks`. |
| **B — a second, label-less axis** | `fig.add_layout(LinearAxis(ticker=FixedTicker(ticks=[…]), axis_line_color=None, major_label_text_font_size="0pt", major_label_standoff=0), side)` | `xlabel()` is absent or is `#N`, so the major ticker must stay dynamic (`BasicTicker` has **no** fixed-minor-position property — its only minor control is the count `num_minor_ticks`). Also the only mechanism for `xmlabel()` (TR-14.4). |

Requirements on whichever is used:

1. The labelled tick set must be **unchanged** by the presence of `xtick()`.
2. No tick label text may appear at an `xtick()` position — assert on
   `major_label_overrides`, on the formatter, and on the second axis's
   `major_label_text_font_size` where mechanism B is used.
3. `xlabel(none) xtick(2500 3500)` must still draw the two marks (`xlabel(none)` sets
   `FixedTicker(ticks=[])` at `:9133`; mechanism A then carries `minor_ticks` on it).
4. Mechanism B must match the axis type: a `LogAxis`/`DatetimeAxis` figure needs the matching
   axis class. Log and date axes are Phase 15's subject; this phase must not crash on them —
   if the axis type is not `LinearAxis`, fall back to mechanism A or skip with the existing
   warning style, and record the choice in a comment.
5. Tick marks must be visible: on the primary axis set `minor_tick_line_color` only if it is
   `None`, and take the colour from `self.scheme.axis_line_color` (`dash_render.py:1965`,
   applied at `:2188`) rather than a literal.

### TR-14.3 — `xmtick()`/`ymtick()`: unlabelled minor marks  *(item 2)*

- Spec keys: `graph_options["xmtick"]`, `["ymtick"]` — already transported (`dash.ado:1129`).
- Parse with `_parse_axis_spec` so the numlist grammar (`2000(250)5000`, bare lists) is shared.
- Apply through the tick-only path of TR-14.2. Semantically identical to `xtick()` — Stata
  draws both as unlabelled marks; the difference is only which tick level they belong to, and
  Bokeh's minor level is the natural home for both.
- Acceptance: `a_mticks`, `xmtick(2250 2750 3250)` → 7 marks on x, 4 labels, the 3 extra marks
  at 2250/2750/3250.

### TR-14.4 — `xmlabel()`/`ymlabel()`: labelled minor ticks  *(item 2)*

Bokeh draws no labels on minor ticks, so this requires **mechanism B**:

```
LinearAxis(ticker=FixedTicker(ticks=positions),
           axis_line_color=None,
           major_label_text_font_size=<0.6 × the primary axis size>,
           major_label_standoff=<shorter than the primary>,
           formatter=<the same formatter the primary axis ends up with>)
```

added on the same side as the primary axis (`"below"` for x, `"left"` for y).

- **0.6×** is measured, not chosen: `a_mlabel` draws the minor labels at `font_size` 67.5
  against 112.56 for the majors (0.5996). Compute from the primary axis's resolved
  `major_label_text_font_size` (the scheme sets it at `dash_render.py:2190` from
  `tick_label_font_size`; `labsize()` may have overridden it at `:9172-9180`), so a scheme
  change or a `labsize()` moves both together.
- The minor labels must carry the **same formatter** as the majors, including the TR-14.8
  display-format fallback — Stata drew `2,500`, not `2500`.
- The major labels must survive: `a_mlabel` keeps all four.
- `xmlabel()` and `xmtick()` may both appear; they are two sets of positions, not one.

### TR-14.5 — Retire the four `_dash_pending` entries, in lockstep with the help  *(item 2)*

- Delete the four lines at `dash.ado:381-384` and the four at `dash.ado:629-632` (the same
  four keys in `_dash_parse_graph_opts` and `_dash_parse_plot_opts`).
- `test/test_help_conformance.py` reads those lines by regex — `_pending(prog)` at `:180-184`
  extracts `_dash_pending' (\w+)"` from each program body — and asserts **both** directions:
  - `:352` `test_nothing_listed_there_is_honoured` fails if `dash.sthlp`'s Unsupported section
    lists an option that is **not** in `_dash_pending`;
  - its sibling `test_everything_dash_ignores_is_listed_there` fails if `_dash_pending`
    contains an option the help does not list.
- Therefore the help edit is **not optional and not deferrable**: `dash.sthlp:1116-1119` —

  ```
  {phang2}{ul:Minor ticks and minor labels.}
      {opt xmtick(numlist)}, {opt ymtick(numlist)},
      {opt xmlabel(numlist)}, {opt ymlabel(numlist)} — Bokeh draws one tick
      level per axis.  {cmd:xtick()} and {cmd:xlabel()} are honoured.
  ```

  must be removed in the same commit as the `dash.ado` deletion. REMAINING.md records that its
  stated rationale is false as well as its status: "Bokeh 3.9 supports minor ticks directly"
  (confirmed here — `FixedTicker.minor_ticks` exists in the installed 3.9.0), and that it
  "tells the reader that xtick() and xlabel() are honoured, when xtick() is exactly the option
  that is wrong".
- `dash.sthlp:866-869` documents `xtick()`/`ytick()` as "x-axis tick positions **without
  labels**" — today's help is right and today's code is wrong, so item 1 makes the help true
  without editing it. Do not "fix" that sentence.

### TR-14.6 — No new transport work in `dash.ado`  *(item 2)*

Verified at HEAD: `xtick ytick xmtick ymtick xmlabel ymlabel` are already in the graph-option
key lists at `dash.ado:1129`, `:1399`, `:1415` and `:1469`, so the values already arrive in
`graph_options` in the master spec JSON. Item 2 needs **no** `syntax` change and **no** new
`sreturn`; the only `dash.ado` edit is the eight deleted `_dash_pending` lines of TR-14.5.
(The comment at `dash.ado:633-636` already explains why `xtick()`/`ytick()` are deliberately
absent from the pending list.)

### TR-14.7 — Remove the guard that makes the S08 fallback unreachable  *(items 3, 4)*

`dash_render.py:9910-9911`:

```python
            if not raw_ax and not raw_tick:
                continue
```

Delete it, and call `_apply_axis_spec` unconditionally with the parsed spec. This is safe by
construction: `_parse_axis_spec("")` returns

```python
        out: dict = {"mode": "default", "ticks": [], "count": None,
                     "labels": {}, "format": None, "labsize": None,
                     "angle": None, "grid": None}
```

and `_apply_axis_spec` has no `"default"` branch, so every tick/label/grid branch is skipped
and only the `fmt` block at `:9159` runs. Guard the cost explicitly: the function must do no
data work in the default case (the `minmax` branch, which reads `self.df`, is not reached).

### TR-14.8 — Teach the format helpers the `g` family  *(items 3, 4)*

The single-point fix is `_parse_stata_numeric_fmt` at `dash_render.py:374-392`, because both
the axis fallback and the loader gate go through it:

1. Widen the regex at `:389` from `%(-)?(\d+)\.(\d+)(f|e)(c)?` to accept `g`:
   `%(-)?(\d+)\.(\d+)(f|e|g)(c)?`.
2. In `_stata_numeric_pattern` (`:395`), replace `if kind != "f": return None` (`:411`) with a
   branch per kind:
   - `f` — unchanged: `"0,0"`/`"0"` plus `"." + "0"*dec`. **Byte-identical output required.**
   - `e` — unchanged: return `None` (dash does not reproduce scientific tick text).
   - `g` — a comma-aware, optional-decimal numbro pattern: `"0,0.[0000]"` when the `c` flag is
     present, `"0.[0000]"` otherwise. Integral ticks then render `2,000`; a non-integral tick
     keeps up to four decimals. Validate the choice against `a_default`
     (`2,000 3,000 4,000 5,000`) and `a_ydefault_price` (`0 5,000 10,000 15,000`) before
     freezing it.
3. Consequence, and it is the point: with `%8.0gc` now parseable, the loader at `:8194-8205`
   starts putting `weight` and `price` into `self.numeric_formats`, so the fallback at `:9159`
   finds them. Both causes REMAINING.md names are closed by one change plus TR-14.7.
4. **`_format_stata_numeric` (`:417`) shares the same parser** and is used for hover rows, KPI
   values and facet labels. Adding `g` changes its behaviour for `%8.0gc` from `f"{val:g}"`
   ("2000") to whatever the new path returns. That is the S08-correct answer ("2,000"), but it
   is a *visible change outside this phase's axes*, so it must be deliberate:
   - add an explicit `g` branch (Python `f"{val:g}"` for the digits, comma grouping applied
     when the `c` flag is set, and the existing width fallbacks — drop commas if the grouped
     string exceeds `width`, then `f"{val:.2e}"` — reused unchanged);
   - leave the `f` and `e` branches untouched;
   - add characterization tests for hover/KPI text on a `%8.0gc` variable so the change shows
     up as an asserted string, not as a surprise in Phase 11/13.

### TR-14.9 — Precedence, silence and the date guard  *(items 3, 4)*

- Precedence is already right and must stay right: `spec["format"] or numeric_formats.get(...)`
  at `:9159-9160`.
- The warning at `:9163-9170` is already gated on `spec["format"]`, so a *fallback* format that
  yields no pattern stays silent. Keep that gate; it becomes load-bearing once the fallback
  runs on every axis.
- Add a date guard before installing a `NumeralTickFormatter`: if the variable is in
  `self.date_vars` (populated in the same loader block, `:8196-8210`) or
  `_stata_date_kind(self.formats.get(varname))` is not `None`, skip the numeric fallback
  entirely. `_apply_axis_spec` has no date awareness at all today — that is Phase 15 item 4,
  a `large` — and this phase must not make the date axis worse by newly formatting it as a
  number.
- Add a string guard: `varname in self.string_vars` → skip.

### TR-14.10 — The `grid` sub-option takes the scheme's colour  *(item 5)*

`dash_render.py:9184-9190`. Replace the literal:

```python
        if spec["grid"] is not None:
            for g in grid_obj:
                if spec["grid"]:
                    if g.grid_line_color is None:
                        g.grid_line_color = "#e5e5e5"      # → self.scheme.grid_color
                else:
                    g.grid_line_color = None
```

- Inside `DashRenderer` the value is reachable as `self.scheme.grid_color` (the attribute
  REMAINING.md names as `self.grid_color` is `SchemeParser`'s own, defined at
  `dash_render.py:1960-1963` and used at `:2180`). Use `self.scheme.minor_grid_color` if a
  minor grid is ever painted from here.
- Also set `grid_line_width` from `self.scheme.grid_line_width` (`:2035`, applied at `:2181`)
  so a grid turned on by the sub-option matches one turned on by the scheme.
- Keep the `is None` test: the branch exists precisely for the case where the scheme left the
  grid off (`draw_major_hgrid`/`draw_major_vgrid` false at `:2172-2180`), which is when the
  user writes `grid`.
- Ordering is already correct: `self.scheme.apply_to_figure(fig)` runs at `:9606`, the axis
  loop at `:9903`.
- No literal may remain. A guard test greps the body of `_apply_axis_spec` for `#` followed by
  six hex digits (see the test plan).

### TR-14.11 — `test/test_axis_options.cscript`  *(item 6)*

New file, modelled on `test/test_option_surface.cscript` and the e2e scripts:

- Header block in the `*!` style used across the suite, naming the plan task (09-01 `<files>`,
  09-02 `<done>`) and stating what is certified.
- `cscript "dash axis grammar" adodir ".."`.
- Skip discipline, copied from `test/test_e2e_single.cscript:16-32`: `capture which jsonio` →
  `exit 222`; probe Python with `if "\`c(python_exec)'" == ""` → `exit 222`. **Never**
  `capture python: pass` — the file records that it made 9 of 14 scripts skip while the suite
  reported all tests passed. A skip is not a pass.
- `qui sysuse auto, clear`; `do "../dash_parse.mata"`; `do "../dash.ado"`; `do "cert_helpers.do"`
  for `cert_file_has` (`test/cert_helpers.do:61`, rclass, returns `r(found)`).
- Set `$dash_nobrowser` before any `dash build` so the script never launches a browser
  (`test/test_server_build.cscript` and `test/test_examples_run.cscript` set it the same way).
- One block per assertion, each: `dash <plot> …, <option> name(gN)` → `assert _rc == 0` →
  `dash build, saving("<tmp>.html")` → `cert_file_has` on the built HTML → clear the registry
  between blocks.
- Probe commands come from `test/fixtures/rejected_options.json` so the script tests what was
  measured: `xtick(2500 3500)`, `ytick(10 20 30 40)`, `xmtick(2000(250)5000)`,
  `ymtick(10(5)40)`, `xmlabel(2000(250)5000)`, `ymlabel(10(5)40)`, plus the forms Appendix A
  measured as working (`xlabel(2000(500)4000)`, `#5`, `minmax`, `none`, `2000 "low" 4000
  "high"`, `, format(%9.0fc)`, `, labsize(large)`, `, angle(45)`, `, grid`, `, nogrid`).
- Assertions in the HTML, not in Stata locals: the tick values appear in the serialized Bokeh
  document, `NumeralTickFormatter` appears when `format()` is used, and for E14.2 the pattern
  emitted for `%8.0gc` appears with **no** axis option written at all.
- Register it in `test/run_all_cscripts.do` following the existing numbered block pattern
  (`// N. test_x.cscript` / `[ RUN ]` / `[ PASS ]` / `[ SKIP]` / `[ FAIL]`), taking the suite
  from 25 scripts to 26.
- **Scope discipline:** this phase's script covers items 1–5 and the working forms. The
  `ylabel(10 15 to 40)` case REMAINING.md uses to motivate the file belongs to **Phase 15**
  (numlist rules `a/b`, `to`, `##N`) and its assertion is added there; server-mode assertions
  are added by **Phase 16**. Adding them here would leave the suite red, which rule 5 forbids
  at commit time.

### TR-14.12 — Reporting and fixture bookkeeping  *(item 2)*

- `test/test_option_surface.cscript`'s contract (quoted in its own header) is that the note
  "names EVERY unsupported option the command used" and "names NOTHING the command did not
  drop". Once the four minor-tick options are honoured, a command using them must produce no
  note; a command using them *and* a genuinely unsupported option must produce a note naming
  only the latter. Add exactly that case.
- `test/fixtures/rejected_options.json` is a measured artefact of task 05-01 with
  `schema_version: 1` — do **not** rewrite its measurements. If a derived disposition or count
  is asserted anywhere against the live report, update the assertion, not the measurement, and
  say so in the commit message.
- REMAINING.md §2 asks the user to choose between implementing all 92 options (a) or a
  high-value subset (b). These four are settled either way: they are already parsed and
  transported, and the plan task 09-02 names them explicitly.

---

## Work items

Every item is listed with the number it was handed over with. Nothing is merged or dropped.

### Item 1 — `[func · both · S]` · origin `09-02` · REMAINING.md **Appendix B**

> Fix xtick()/ytick() semantics. Stata's xtick() adds UNLABELLED tick marks alongside the
> labelled ticks xlabel() (or the default) produces; dash treats xtick as a fallback spelling
> of xlabel — it draws LABELLED ticks at those positions, and discards xtick entirely whenever
> xlabel is also present.

**Where** (verbatim): `dash_render.py:9906-9913` (`tick_key = "xtick" if ax_key == "xlabel"
else "ytick"` then `spec = self._parse_axis_spec(raw_ax or raw_tick)`); `dash_render.py:9112`
`_apply_axis_spec` needs a tick-only path (e.g. FixedTicker.minor_ticks or a second ticker);
server side has no xtick read at all (see item 1).

**Evidence.** The `or` at `:9913` and the single `xtick` occurrence in the whole file
(`grep -c` → 1). Stata's answer is `a_ticks_only`: `xtick(2500 3500)` → `n_ticks` 6,
`tick_values` `[2000, None, 3000, None, 4000, 5000]`, tick label text unchanged. Appendix A's
"`xtick()`/`ytick()` work" means "run", not "match Stata". `test_axis_options.py:213`
currently asserts the defect. Covered by TR-14.1, TR-14.2.

### Item 2 — `[func · both · M]` · origin `09-02` · REMAINING.md **Appendix B**

> Implement xmtick(), ymtick(), xmlabel(), ymlabel() (minor ticks and minor labels). They are
> accepted by dash.ado, promoted into graph_options JSON, and then read by nobody — and
> dash.ado still names them in its 'ignoring unsupported option(s)' list, which is the honest
> state today.

**Where** (verbatim): `dash.ado:381-384` and `dash.ado:629-632` (the `_dash_pending` entries to
remove once implemented); `dash.ado:1129/1399/1415/1469` already carry the keys through to
graph_options JSON; `dash_render.py:9906` loop (add the four keys) and `dash_render.py:9112`
`_apply_axis_spec` (needs a minor-tick path); server: `dash_render.py:14012` emitted loop.

**Evidence.** `grep -c` in `dash_render.py`: `xmtick` 0, `ymtick` 0, `xmlabel` 0, `ymlabel` 0.
The four `_dash_pending` lines are present at both cited locations, and the promotion lists at
`:1129`/`:1399`/`:1415`/`:1469` all name the keys. Appendix A: "all four leave a default
`BasicTicker` and are reported as unsupported options". Stata's answer: `a_mticks`
(`n_ticks` 7, no new labels) and `a_mlabel` (`n_ticks` 6, two new labels `2,500`/`3,500` at
font 67.5 vs 112.56). The help note at `dash.sthlp:1116-1119` must go with the `_dash_pending`
deletion — `test/test_help_conformance.py:352` binds them. The emitted-loop half of the
*Where* (`dash_render.py:14012`) is **Phase 16**'s; this phase does the standalone and
`dash.ado` halves. Covered by TR-14.3 – TR-14.6, TR-14.12.

### Item 3 — `[func · both · M]` · origin `09-02` · REMAINING.md **Appendix B**

> Make the S08 display-format fallback reach a default axis. The fallback lives inside
> `_apply_axis_spec`, but that method is only reached when an xlabel/ylabel/xtick/ytick option
> is actually present (`if not raw_ax and not raw_tick: continue`), so a plain
> `dash scatter mpg weight` gets no tick formatting at all. Separately,
> `_stata_numeric_pattern` returns None for g-kind formats, and `%8.0gc` is auto.dta's own
> format for weight and price — so even with the guard removed the commonest Stata comma
> format would still not format.

**Where** (verbatim): `dash_render.py:9910` (`if not raw_ax and not raw_tick: continue` — the
guard that skips the fallback); `dash_render.py:9159-9171` (the fallback itself, inside
`_apply_axis_spec`); `dash_render.py:395` `_stata_numeric_pattern` (`if kind != "f": return
None` — no g-kind support); populated correctly at `dash_render.py:8194-8205`
`self.numeric_formats`.

**Evidence.** Appendix A measured it: "with `formats={'weight': '%9.0fc'}` and no `format()`
sub-option: the formatter stays `BasicTickFormatter`. Only an explicit `format()` works." The
regex at `:389` admits only `f|e`, so `%8.0gc` fails to parse *before* the `kind != "f"` check
at `:411`; the loader at `:8201-8203` only records a variable in `numeric_formats` when the
same helper returns a pattern, so `self.numeric_formats` has no `weight` key. Stata draws
`2,000 3,000 4,000 5,000` (`a_default`). Covered by TR-14.7 – TR-14.9.

### Item 4 — `[func · both · M]` · origin `09-02` · REMAINING.md **Appendix C**

> The clause "when no format() is given, the variable's Stata display format from S08" does not
> work on a default axis, for two independent reasons. (1) The axis loop `continue`s when
> neither xlabel nor xtick is present (dash_render.py:9908-9911), so `_apply_axis_spec`'s
> `numeric_formats` fallback at dash_render.py:9160 is unreachable unless the user also writes
> xlabel(). (2) `_stata_numeric_pattern` (dash_render.py:395) returns None for every non-`f`
> format, so Stata's DEFAULT numeric format family — auto.dta's own `%8.0gc` on weight and
> price — never yields a pattern even when the fallback does run. Stata labels those axes with
> thousands separators; dash does not.

**Where** (verbatim): `dash_render.py:9903-9913` (the `if not raw_ax and not raw_tick: continue`
guard); `dash_render.py:9160-9170` in `_apply_axis_spec`; `dash_render.py:395`
`_stata_numeric_pattern` (the `if kind != "f": return None`); ServerAppBuilder emitted axis
block `dash_render.py:14012-14021`.

**Evidence.** This is Appendix C's two-cause decomposition of item 3, and it names the second
axis (`price`, `%8.0gc`) and the user-visible difference ("Stata labels those axes with
thousands separators; dash does not"), confirmed by `a_ydefault_price`: `0 5,000 10,000
15,000`. Items 3 and 4 are implemented as one change; both are listed because both were handed
over. The emitted-block half of the *Where* is **Phase 16**'s. Covered by TR-14.7 – TR-14.9.

### Item 5 — `[func · standalone · S]` · origin `09-02` · REMAINING.md **Appendix C**

> The `grid` sub-option paints a hardcoded `#e5e5e5` instead of the scheme's gridline colour,
> which the renderer already computes as `self.grid_color` and applies everywhere else
> (dash_render.py:2180). A style literal of exactly the kind the branch's recent commits claim
> to have removed from both renderers.

**Where** (verbatim): `dash_render.py:9184-9190` in `_apply_axis_spec`
(`g.grid_line_color = "#e5e5e5"`); reuse `self.grid_color` / `self.minor_grid_color` as at
`dash_render.py:2180-2185`.

**Evidence.** The literal is at `:9188`; the scheme value is computed at `:1960-1963`
(`color major_grid`, falling back to `color grid`, then `#d9e8f0`) and applied at `:2180`.
Measured scheme values: `s2color` `#eaf2f3`, `s1color` `#e0e0e0`, `economist` `#ffffff` — none
of them `#e5e5e5`. Appendix A's own table records the defect in passing:
"`, grid` / `, nogrid` | grid `#e5e5e5` / `None`". Covered by TR-14.10.

### Item 6 — `[deli · stata · M]` · origin `09-02` · REMAINING.md **Appendix C**

> There is no Stata-side certification script for the axis grammar. Section 09-01 names
> `test/test_axis_options.cscript` in its <files> and it does not exist, so nothing checks that
> dash.ado's `syntax` accepts and transports each axis_label form end to end — which is how
> `ylabel(10 15 to 40)` reaches a shipped dashboard with a tick labelled "to" while pytest is
> green.

**Where** (verbatim): `test/` (new `test_axis_options.cscript`); pattern to copy:
`test/test_option_surface.cscript`, `test/run_all_cscripts.do`.

**Evidence.** The file does not exist; `test/*.cscript` numbers 25 at HEAD and REMAINING.md's
gate line records "25/25 cscripts" passing, so the axis grammar contributes none of them.
`test/test_axis_options.py` only ever builds `DashRenderer` figures through `_fig_with_gopts`
(`:67`), never Stata. Covered by TR-14.11.

---

## Test plan

Rule 8 governs the order: for each defect, write the check that **fails at HEAD**, watch it
fail, then fix. Rule 4 governs the coverage: every function this phase adds or changes gets a
unit test. Every test below names the file it lands in and the mutation that must kill it.

### Shared harness work (do this first)

`test/test_axis_options.py` already has `_fig_with_gopts` (`:67`), `_ticker_of` (`:101`) and
`_fixed_ticks` (`:106`). Add, in the same style:

- `_labelled_ticks(fig, axis="x")` → the tick positions that carry text (from the
  `FixedTicker.ticks` plus `major_label_overrides` and any extra label-bearing axis).
- `_unlabelled_ticks(fig, axis="x")` → positions drawn with no text (`FixedTicker.minor_ticks`
  plus any axis whose `major_label_text_font_size` is `"0pt"`).
- `_truth(truth, probe, axis="x_axis")` → index `test/fixtures/axis_truth.json`'s `probes`, so
  assertions cite Stata rather than dash. This is the first real use of the `truth` fixture
  (its ten current consumers ignore it — Phase 15 item 9 finishes that job).

### E14.1 — Tick marks, Stata's way (items 1, 2)

**Failing tests first** — `test/test_axis_options.py`:

| test | asserts | fails at HEAD because |
|---|---|---|
| `test_xtick_adds_unlabelled_ticks_beside_xlabel` | `xlabel("2000(1000)5000")` + `xtick("2500 3500")` → labelled `{2000,3000,4000,5000}`, unlabelled `{2500,3500}` | `raw_ax or raw_tick` discards `xtick` entirely |
| `test_xtick_alone_does_not_relabel_the_axis` | `xtick("2500 3500")` alone → no tick label text at 2500/3500 | today it installs a labelled `FixedTicker[2500,3500]` |
| `test_xtick_matches_stata_tick_count` | against `a_ticks_only`: 6 marks, 4 of them labelled | 2 marks, 2 labelled |
| `test_ytick_behaves_like_xtick` | the y mirror | same `or` |
| `test_xmtick_draws_minor_marks` | against `a_mticks`: 7 marks, 4 labelled, extras at 2250/2750/3250 | `xmtick` is read by nobody |
| `test_xmlabel_draws_labelled_minor_ticks` | against `a_mlabel`: majors intact, `2,500`/`3,500` added | `xmlabel` is read by nobody |
| `test_minor_label_size_is_six_tenths_of_major` | minor px size ÷ major px size ∈ [0.58, 0.62] (Stata: 67.5/112.56 = 0.5996) | no minor labels exist |
| `test_minor_options_take_the_increment_form` | `xmtick("2000(250)5000")` → 13 marks | ditto |
| `test_xlabel_none_with_xtick_still_draws_marks` | `xlabel("none") xtick("2500 3500")` → 0 labelled, 2 unlabelled | `raw_ax` wins, `xtick` dropped |

**Rewrite, do not delete:** `test_xtick_is_honoured` (`:213`) asserts a `FixedTicker`, which is
what the *labelled* path installs. Replace its body with the labelled/unlabelled split and keep
the name's intent. Deleting it would remove the only existing `xtick` coverage.

**Unit tests (rule 4)** for every new function: `_apply_tick_spec` (or the `labelled=` branch),
the minor-axis constructor, and the label-size computation — each called directly with a
synthetic figure, not only through `_fig_with_gopts`.

**Stata-side (item 6):** `test/test_axis_options.cscript` blocks for `xtick`, `ytick`,
`xmtick`, `ymtick`, `xmlabel`, `ymlabel` using the `rejected_options.json` probe commands, each
asserting `_rc == 0` and the positions present in the built HTML.

**Reporting contract:** add to `test/test_option_surface.cscript` a command using `xmtick()`
that must emit **no** "unsupported option" line, and one using `xmtick()` plus a genuinely
unsupported option that must name only the latter. `test/test_help_conformance.py` needs no new
test — its two existing assertions at `:352` and below already enforce the lockstep; run them.

**Mutation proof (non-vacuity):**

| break this | this test must die |
|---|---|
| restore `spec = self._parse_axis_spec(raw_ax or raw_tick)` | `test_xtick_adds_unlabelled_ticks_beside_xlabel` |
| route the tick spec through the labelled path | `test_xtick_alone_does_not_relabel_the_axis` |
| drop `xmtick` from the loop tuple | `test_xmtick_draws_minor_marks` |
| set the minor label size equal to the major | `test_minor_label_size_is_six_tenths_of_major` |
| re-add one `_dash_pending' xmtick` line to `dash.ado` | `test_everything_dash_ignores_is_listed_there` stays green but `test_nothing_listed_there_is_honoured` — with the help entry removed — must fail; the new `test_option_surface.cscript` case must fail too |

### E14.2 — The default axis inherits the variable's format (items 3, 4)

**Failing tests first** — `test/test_axis_options.py` and `test/test_dates.py` (there is no
`test_formats.py`; `test/test_dates.py` is the only file that imports `_stata_numeric_pattern`
and `_format_stata_numeric` today, so the helper-level tests below land there), as noted:

| test | asserts | fails at HEAD because |
|---|---|---|
| `test_default_axis_uses_the_variables_display_format` | `_SCATTER` on a frame with `formats={"weight": "%8.0gc"}` and **no** graph options → x formatter is `NumeralTickFormatter` with a comma pattern | the `continue` guard skips `_apply_axis_spec` |
| `test_g_format_yields_a_pattern` | `_stata_numeric_pattern("%8.0gc") is not None` and contains `","` | regex rejects `g` |
| `test_g_format_variables_enter_numeric_formats` | `DashRenderer(...).numeric_formats["weight"] == "%8.0gc"` | loader gates on the same helper |
| `test_default_axis_matches_stata_tick_text` | render the pattern against `a_default`'s four label strings via `_format_stata_numeric(v, "%8.0gc")` → `2,000` … `5,000` | `_format_stata_numeric` takes the `parsed is None` path and returns `2000` |
| `test_price_axis_matches_stata` | `a_ydefault_price` → `0 5,000 10,000 15,000` | same |
| `test_explicit_format_beats_the_variable_format` | `xlabel(", format(%9.2f)")` on the same frame → `'0.00'` | (passes at HEAD — a **regression guard** for the new precedence) |
| `test_fallback_format_is_silent` | an unreproducible display format, no `format()` → no `UserWarning` | (passes at HEAD only because the fallback never runs; must still pass after) |
| `test_explicit_unreproducible_format_still_warns` | `format(%tc)`-style explicit → warning | regression guard |
| `test_default_date_axis_gets_no_numeral_formatter` | a `%td` frame, no options → no `NumeralTickFormatter` on that axis | would newly regress without TR-14.9's guard |
| `test_f_format_patterns_are_unchanged` | `%9.0fc` → `'0,0'`, `%9.2f` → `'0.00'`, `%9.0f` → `'0'` | characterization guard on TR-14.8 step 2 |
| `test_hover_and_kpi_text_for_a_g_format` | the string `_format_stata_numeric(2000, "%8.0gc")` now used by hover/KPI is `'2,000'` | characterization of the deliberate change in TR-14.8 step 4 |

**Stata-side (item 6):** a cscript block that builds `dash scatter mpg weight, name(g1)` with
**no** axis option and asserts the comma pattern reaches the HTML — the end-to-end form of
BR-14.7.

**Mutation proof:**

| break this | this test must die |
|---|---|
| restore the `if not raw_ax and not raw_tick: continue` guard | `test_default_axis_uses_the_variables_display_format` |
| revert the regex to `(f|e)` | `test_g_format_yields_a_pattern`, `test_g_format_variables_enter_numeric_formats` |
| return `"0.0000"` (no comma) for `g` | `test_default_axis_matches_stata_tick_text` |
| swap the precedence to `numeric_formats.get(...) or spec["format"]` | `test_explicit_format_beats_the_variable_format` |
| delete the date guard | `test_default_date_axis_gets_no_numeral_formatter` |
| drop the `spec["format"]` condition from the warning | `test_fallback_format_is_silent` |

### E14.3 — Scheme-true gridlines, proven from Stata (items 5, 6)

**Failing tests first:**

| test | file | asserts | fails at HEAD because |
|---|---|---|---|
| `test_grid_suboption_uses_the_scheme_colour` | `test/test_axis_options.py` | parametrized over `s2color` (`#eaf2f3`), `s1color` (`#e0e0e0`), `economist` (`#ffffff`): `xlabel("2000 4000, grid")` → `fig.xgrid[0].grid_line_color` equals the scheme's value | it is `#e5e5e5` in all three |
| `test_grid_suboption_uses_the_scheme_width` | same | `grid_line_width == scheme.grid_line_width` | never set on this path |
| `test_no_colour_literal_in_the_axis_code` | `test/test_color_fidelity.py` (or a new guard beside it) | `re.search(r"#[0-9a-fA-F]{6}", inspect.getsource(DashRenderer._apply_axis_spec))` is `None` | `#e5e5e5` |
| `test_nogrid_still_removes_the_grid` | `test/test_axis_options.py` | regression guard for the `else` branch | passes; must keep passing |

**The cscript itself (item 6)** is the deliverable; its own non-vacuity is proven by mutation
against the *renderer*, not against the script:

| break this | the cscript must fail |
|---|---|
| revert the `xtick` fix | the `xtick` block's HTML assertion |
| revert the `g`-format fix | the no-option default-axis block |
| revert the grid colour | the `grid` block (assert the scheme colour string in the HTML) |
| remove `xmtick` from the renderer loop | the `xmtick` block |
| re-add `_dash_pending' xmtick` | the "no unsupported note" assertion |

Also assert the script is **registered**: `test/test_cscript_hygiene.py` already exists — extend
it (or add a one-line check) so a cscript present in `test/` but absent from
`test/run_all_cscripts.do` fails pytest. A script that never runs is not a test.

### Suite-level obligations (rule 5, before any commit)

- Full pytest: 3,498 passed / 37 skipped at HEAD is the floor; the count only rises.
- Full certification suite from `test/`, `arch -arm64`, 25 → **26** scripts, with honest skips
  (a skip is not a pass).
- `test/test_help_conformance.py` in particular, because of TR-14.5's lockstep.
- `test/test_mode_parity.py` must still pass; it carries no axis cases today (Phase 16 adds
  them), so this phase cannot break it, and must not be taken as evidence that the server is
  fine.

---

## Definition of done

A reviewer can tick every line:

**E14.1 — ticks**

- [ ] `dash_render.py:9903-9913` reads `xlabel`/`ylabel` and `xtick`/`ytick` independently; the
      `raw_ax or raw_tick` expression is gone.
- [ ] A tick-only path exists in/beside `_apply_axis_spec` and never sets
      `major_label_overrides` or a `CustomJSTickFormatter`.
- [ ] `xlabel(2000(1000)5000) xtick(2500 3500)` → 6 marks, 4 labels (matches `a_ticks_only`'s
      structure).
- [ ] `xtick()` alone leaves the labelled ticks alone.
- [ ] `xlabel(none) xtick(2500 3500)` draws the two marks.
- [ ] `xmtick()`/`ymtick()` draw unlabelled minor marks (`a_mticks`: 7 marks, 4 labels).
- [ ] `xmlabel()`/`ymlabel()` draw labelled minor ticks, majors intact, size 0.6× major,
      formatted with the same display format (`a_mlabel`: `2,500`, `3,500`).
- [ ] `grep -c` in `dash_render.py`: `xmtick`, `ymtick`, `xmlabel`, `ymlabel` are all > 0.
- [ ] The eight `_dash_pending` lines at `dash.ado:381-384` and `:629-632` are deleted.
- [ ] `dash.sthlp:1116-1119` (the minor-tick deferral note) is removed **in the same commit**.
- [ ] `dash.sthlp:866-869` ("tick positions without labels") is left as written and is now true.
- [ ] No "unsupported option(s) ignored" note names any of the four.

**E14.2 — formats**

- [ ] The `if not raw_ax and not raw_tick: continue` guard is gone and the default axis reaches
      `_apply_axis_spec`.
- [ ] `_parse_stata_numeric_fmt` accepts `g`/`gc`; `_stata_numeric_pattern` returns a
      comma-aware optional-decimal pattern for `g` and is **byte-identical** for `f` and `e`.
- [ ] `self.numeric_formats` contains `weight` and `price` for `auto.dta`.
- [ ] `dash scatter mpg weight` with no options labels x `2,000 3,000 4,000 5,000`;
      `dash scatter price weight` labels y `0 5,000 10,000 15,000`.
- [ ] Explicit `format()` still wins; a fallback format dash cannot reproduce is silent; an
      explicit one still warns.
- [ ] Date and string axes are untouched by the fallback.
- [ ] `_format_stata_numeric`'s `g` branch is explicit, `f`/`e` unchanged, and the hover/KPI
      text change is covered by a characterization test.

**E14.3 — grid and proof**

- [ ] `_apply_axis_spec` contains no colour literal (grep guard green).
- [ ] `grid` paints `self.scheme.grid_color` at `self.scheme.grid_line_width`; `nogrid`
      unchanged.
- [ ] `test/test_axis_options.cscript` exists, is registered in `test/run_all_cscripts.do`, and
      passes; the suite reports 26 scripts.
- [ ] The cscript skips honestly (`jsonio`, `c(python_exec)`) and sets `$dash_nobrowser`.
- [ ] Every test above was seen to fail before its fix and pass after (rule 8), and each
      mutation in the test plan kills its named test.

**Both**

- [ ] Full pytest and the full certification suite pass locally from a clean pull of `main`
      merged into `feature/batch4-interactive-layer` (rule 5).
- [ ] The commit message describes the code changes only (rule 7).
- [ ] REMAINING.md is untouched.

---

## Risks and sequencing notes

1. **The help edit cannot wait for Phase 30.** `test/test_help_conformance.py:352`
   (`test_nothing_listed_there_is_honoured`) reads `_dash_pending` out of `dash.ado` by regex
   and compares it with `dash.sthlp`'s Unsupported section. Deleting the four pending entries
   without removing `dash.sthlp:1116-1119` turns the suite red; removing the help sentence
   without deleting the pending entries turns the *other* assertion red. Land both in one
   commit. Phase 30's items 4 and 5 then become verification rather than work — tell Phase 30.
2. **Widening `_parse_stata_numeric_fmt` reaches beyond the axes.** It is shared with
   `_format_stata_numeric` (`:417`), which feeds hover rows, KPI values and facet labels
   (Phases 11, 12, 13). A `%8.0gc` variable's hover text changes from `2000` to `2,000`. That is
   the S08-correct direction, but it must arrive with a characterization test, not as a
   surprise. If Phase 11 or 13 is in flight simultaneously, coordinate: they own those call
   sites.
3. **Phase 16 must port `_apply_axis_spec` *after* this phase.** Its item 1 proposes copying the
   standalone parser/applier into the emitted app via `inspect.getsource`, the way
   `_glyph_layer_lines` (`dash_render.py:12315`) already copies `GlyphMapper`. Porting first
   would copy the `#e5e5e5` literal, the `or` and the dead fallback into `dash serve`. Note for
   Phase 16: `self.scheme.grid_color` does not exist inside the emitted app — the emitted chrome
   reads `_c['grid_color']` (`dash_render.py:12613`, `:12681`), so the port needs a small
   substitution at that line.
4. **Phase 15 edits the same two functions.** Items there change the `minmax` branch, the
   `count` branch's ticker class, the sub-option strip regex and the date path — all inside
   `_parse_axis_spec`/`_apply_axis_spec`. Run 14 before 15 (the index already orders them that
   way) and expect textual conflicts otherwise, not logical ones.
5. **Mechanism B adds layout.** A second `LinearAxis` occupies space below/left of the plot even
   with `axis_line_color=None` and a `0pt` label font. Check a KPI/facet-dense layout
   (`layout(auto)` and a `by()` grid) before settling on it, and prefer mechanism A wherever a
   `FixedTicker` is already installed.
6. **Log and datetime axes.** `_apply_axis_spec` has no date awareness at all (Phase 15 item 4,
   `large`), and `#N` already overwrites a log axis's ticker (Phase 15 item 5). Mechanism B must
   pick the matching axis class or decline; this phase's obligation is *do no new harm* on those
   figures, proven by the date guard test.
7. **`a_mlabel`'s `tick_values` looks odd and is not.** `[None, 2500, None, 3500, None, None]`
   reflects the fixture's stated rule that values are recovered by parsing the rendered label
   back to a number; use `tick_px` (six positions) together with the drawn text for assertions,
   not `tick_values` alone.
8. **Do not chase the `to` rule here.** `ylabel(10 15 to 40)` is the motivating example in item
   6's text, but the rule that fixes it is Phase 15 item 3. Assert it in the cscript in Phase 15,
   so this phase can be committed with a green suite (rule 5).
9. **`test/fixtures/rejected_options.json` is a measurement, not a config.** Change assertions
   against it, never its recorded `dash_rc`/`dash_message` values; they document HEAD before
   05-01's work and are cited throughout REMAINING.md §2.
