# Phase 16 — Axis grammar III: the server port

**Purpose.** Task 09-02 built Stata's `axis_label` and `axis_scale` grammars inside
`DashRenderer`, and built them well: `2000(500)4000`, `#5`, `minmax`, `none`, `format()`,
`labsize()`, `angle()`, `grid`/`nogrid` and `xscale(range())` were each measured correct in
the standalone renderer. **None of it reached `ServerAppBuilder`.** The emitted app carries a
fourteen-line parser of its own that understands a bare numlist and quoted value-label pairs
and nothing else — and because it tokenises the raw option string *without stripping
sub-options first*, `xlabel(2000 4000, format(%9.0fc))` paints the literal text
`format(%9.0fc)` on the axis as the label for the 4000 tick. This phase ports the one grammar
into the emitted app rather than growing a second one, wires `xscale(range())` there and
deletes the dead `xrange`/`yrange` reads that survive only in the app, and then repairs the
three defects inside the helper 09-02 kept: the secondary axes still run the pre-09-02 parser,
a bare unquoted token is still accepted as a tick label (so Stata's `ylabel(10 15 to 40)`
writes the word **to** on the axis), and the value-label formatter is keyed `"2000.0"` while
its own JavaScript looks up `"2000"`. It closes with the test surface whose absence is the
structural reason none of this was caught: server-mode cases in the axis suite, and axis cases
plus ticker/formatter comparison in the standing standalone/server parity guard.

---

## At a glance

| | |
|---|---|
| **Work items** | 9 |
| **Functional / deliverable** | 6 functional (items 1, 2, 3, 5, 7, 8) · 3 deliverable (items 4, 6, 9) |
| **Effort mix** | 4 medium (1, 4, 7, 9) · 5 small (2, 3, 5, 6, 8) — 0 large |
| **Renderers touched** | `ServerAppBuilder` (emitted app) ×2 (items 1, 2) · `DashRenderer` (standalone) ×2 (items 3, 5) · both ×5 (items 4, 6, 7, 8, 9) |
| **Ultraplan tasks discharged** | **09-02** — its server half entirely, plus the two leaks that survived inside the helper it kept. Also closes 09-07's `<done>` clause *"no dead option read remains in the axis code"* for the emitted app, which `DashRenderer` satisfied and `ServerAppBuilder` did not. |
| **Sections** | S09 "Axes, legend, titles" — 7 tasks, currently *1 done, 6 partial*, **73 options open**, and the section REMAINING.md names as "largest single family; none of S09 reached `ServerAppBuilder`". Items 6 and 9 also extend the S15 parity guard. |
| **Depends on** | **14** and **15** — they change `_parse_axis_spec`/`_apply_axis_spec`, and this phase ports those two functions verbatim; porting first means porting twice. **05–08** — the server-unification phases own the emitted app's structure and the parity corpus this phase adds cases to. |
| **Unblocks** | Phase **30** item 6 (the `dash.sthlp` server-mode caveat can be deleted rather than written, once the grammar is actually there). The S16-07 **parity corpus** release gate. |
| **Backlog provenance** | REMAINING.md main body §4 (the "also unification-shaped" note) · Appendix A, *09-02 · PARTIAL* (remaining item 3) · Appendix B, "Three findings worth pulling out first" finding 2 and 4 of the 8 items under 09-02 · Appendix C, 5 of the 19 further items under 09-02 |

---

## Why this phase exists

### The audit's verdict: the grammar stops at the renderer boundary

REMAINING.md §4, closing paragraph:

> **Also unification-shaped:** none of S09's axis/title/legend work reached
> `ServerAppBuilder`. `_parse_axis_label` appears 4× in the renderer and **0×**
> in the emitted app, so the whole `xlabel()` grammar is absent from
> `dash serve` / `dash build, server`. (Agent-reported, path confirmed here.)

Confirmed again at HEAD (`187a786`) for this document, by locating every axis symbol in
`dash_render.py` and comparing against `class ServerAppBuilder`, which begins at **:12265** —
everything below that line is renderer code, everything above it *inside the class body* is
emitted-app source:

| symbol | lines it occurs on | any occurrence ≥ :12265? |
|---|---|---|
| `_parse_axis_label*` (4 occurrences) | 9384, 9393, 9699, 9734 | **no** |
| `_parse_axis_spec` | 9305 (def), 9120, 9912 | **no** |
| `_apply_axis_spec` | 9112 (def), 9913 | **no** |
| `major_label_overrides` | 9157 | **no** |
| `NumeralTickFormatter` | 9126, 9165 | **no** |
| `BasicTicker` | 9124, 9148 | **no** |
| `_parse_scale_range` | 776 (def), 9757 | **no** |
| `_report_unhandled_scale_opts` | 805 (def), 9756 | **no** |

One definition, one call site, both on the standalone side. The grammar is not partially
ported; it is not ported.

### What 09-02 actually delivered — and what it did not

REMAINING.md Appendix A, *"09-02 — Implement the axis_label and axis_scale grammars ·
PARTIAL"*, verbatim:

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
> 1. **Tick labels ignore the variable's Stata display format.** […]
> 2. **`xmtick()` `ymtick()` `xmlabel()` `ymlabel()` are not implemented** […]
> 3. **Server mode has no axis-label grammar at all**: `_parse_axis_label` occurs
>    4× in the renderer and **0×** in the emitted app.

Remaining items 1 and 2 are **Phase 14**. Remaining item 3 is this phase — work items 1 and 2
below. The "dead `xrange`/`yrange` keys are gone" sentence is true of `DashRenderer` and false
of the emitted app, which is work item 2.

### The dangerous half: the server keeps the tick positions and drops the labels

REMAINING.md Appendix B, "Three findings worth pulling out first", finding 2, verbatim:

> **2. The axis grammar is standalone-only, and the server silently keeps the
> positions while dropping the labels.** Same spec through both renderers:
>
> | `xlabel(...)` | standalone | server |
> |---|---|---|
> | `2000(500)4000` | `FixedTicker[2000, 2500, 3000, 3500, 4000]` | `BasicTicker` |
> | `minmax` | `FixedTicker[1800, 4080]` | `BasicTicker` |
> | `none` | `FixedTicker[]` | `BasicTicker` |
> | `, format(%9.0fc)` | `NumeralTickFormatter` | `BasicTicker` |
> | `, angle(45)` | `0.7854` rad | `BasicTicker` |
> | `2000 "low" 4000 "high"` | ticks **+ overrides** | ticks, **overrides dropped** |
>
> The last row is the dangerous one: the served graph draws tick marks in the
> right places carrying the wrong text, which looks correct.

### The parser that is there instead

`dash_render.py:13989`, the emitted string literal inside `ServerAppBuilder` (reproduced by
`ast.literal_eval`-ing the literal lines, so this is the app's text, not a transcription):

```python
def _parse_axlabel(raw):
    tks, labs = [], {}
    toks = _re.findall(r'"([^"]*)"|\'([^\']*)\'|([^\s,"\']+)', raw)
    flat = [d or s or b for d,s,b in toks]
    i = 0
    while i < len(flat):
        try:
            v = float(flat[i]); tks.append(v)
            if i+1 < len(flat):
                try: float(flat[i+1])
                except ValueError: labs[str(v)] = flat[i+1]; i += 1
        except ValueError: pass
        i += 1
    return sorted(tks), labs
```

and the loop that uses it, `dash_render.py:14012-14021`:

```python
for _axk, _axobj in (('xlabel', fig.xaxis), ('ylabel', fig.yaxis)):
    _raw_ax = go.get(_axk, '')
    if not _raw_ax: continue
    _tks, _labs = _parse_axlabel(_raw_ax)
    if _tks:
        _axobj.ticker = _FT(ticks=_tks)
        if _labs:
            _axobj.formatter = _CJSF(code=f'const m={_json.dumps(_labs)};return m[String(tick)]||String(tick);')
    _ang = _parse_axangle(_raw_ax)
    if _ang is not None: _axobj.major_label_orientation = _ang
```

Running that exact function over the grammar's forms (confirmation of REMAINING.md's claims,
executed at HEAD against the literal at :13989):

| option text | `_parse_axlabel` returns | consequence on a served axis |
|---|---|---|
| `2000 4000, format(%9.0fc)` | `([2000.0, 4000.0], {'4000.0': 'format(%9.0fc)'})` | **the string `format(%9.0fc)` is drawn as the 4000 tick's label** |
| `1000 2000, labsize(large) grid` | `([1000.0, 2000.0], {'2000.0': 'labsize(large)'})` | **`labsize(large)` drawn as the 2000 tick's label** |
| `10 15 to 40` | `([10.0, 15.0, 40.0], {'15.0': 'to'})` | **the word `to` drawn as the 15 tick's label** |
| `2000(500)4000` | `([], {})` | increment form silently ignored → `BasicTicker` |
| `minmax` | `([], {})` | ignored → `BasicTicker` |
| `none` | `([], {})` | ignored → `BasicTicker`, i.e. *more* ticks than the user asked for, not fewer |
| `#5` | `([], {})` | ignored → `BasicTicker` |
| `2000 "low" 4000 "high"` | `([2000.0, 4000.0], {'2000.0': 'low', '4000.0': 'high'})` | ticks correct, and see the key defect below |

Note the map keys: `'2000.0'`. The JavaScript in the same expression looks up
`String(tick)`, which for an integral tick is `'2000'`. **The lookup always misses.** The
standalone renderer survives the identical bug only because `_apply_axis_spec` *also* sets
`major_label_overrides` (`dash_render.py:9157`), which Bokeh applies ahead of the formatter;
the emitted app sets no overrides, so a served `xlabel(2000 "low" 4000 "high")` draws
**2000 / 4000**. That is work item 8.

### The dead reads 09-02 was told not to leave

The ultraplan's own text for 09-02 (`.ultraplan/sections/section-09-axes-legend-titles.md`):

> Extend `_parse_scale_opt` (`:203-213`) to honour `range()`. Working range code already
> exists at `:5799-5817` but is keyed on `xrange`/`yrange`, which `dash.ado` never emits —
> either wire `range()` to it or delete the dead keys. **Do not leave both.**

`DashRenderer` took the first option (`dash_render.py:9746-9773`, calling `_parse_scale_range`
at :9757). The emitted app took neither: it still reads keys `dash.ado` never emits, at
`dash_render.py:13907-13920`:

```python
"        # xrange / yrange axis limits",
"        _raw_xr = go.get('xrange', '')",
...
"        _raw_yr = go.get('yrange', '')",
```

and its `xscale`/`yscale` handling at :13851-13866 recognises exactly two tokens, `log` and
`reverse`. So on a served graph `xscale(range(1500 5000))` does nothing at all, while the
in-file guard test that was written to prevent precisely this —
`test/test_axis_options.py:248 test_the_dead_xrange_keys_are_gone` — only greps for
`graph_opts.get("xrange"` and therefore passes over the emitted spelling `go.get('xrange'`.

### The leaks inside the helper 09-02 kept

`_parse_axis_spec` (`dash_render.py:9305`) strips the recognised sub-options and then hands
the leftover head text to the **old** `_parse_axis_label_opt` (`:9393`), which pairs every
number with the next token *whatever it is* — it never requires quotes. Measured at HEAD:

```
DashRenderer._parse_axis_spec('10 15 to 40')
  -> {'mode': 'explicit', 'ticks': [10.0, 15.0, 40.0], 'labels': {'15.0': 'to'}, ...}
DashRenderer._parse_axis_spec('10/15')  -> {'mode': 'default', 'ticks': [], ...}
DashRenderer._parse_axis_spec('##5')    -> {'mode': 'default', 'ticks': [], ...}
```

REMAINING.md calls this "the BR-09.2 leak the section was written to eliminate, surviving
inside the helper 09-02 kept" (work item 7). The `a/b` and `##N` gaps in the same output are
**Phase 15**, item 3 — named here only so the fix is written once, in one function, with both
phases' tests over it.

The same old helper is still the *only* parser the secondary axes use —
`dash_render.py:9699` and `:9734`:

```python
_ticks2, _labels2 = self._parse_axis_label_opt(_raw_yla2)
...
_safe2 = {str(k): html.escape(str(v)) for k, v in _labels2.items()}
_y2_ax.formatter = CustomJSTickFormatter(
    code=f"const m = {json.dumps(_safe2)}; "
         "return m[String(tick)] || String(tick);")
```

— the pre-09-02 grammar, the `str(float)` key mismatch and the `html.escape` of canvas text,
all three, on `xlabel2()`/`ylabel2()`. And `xscale2()`/`yscale2()` are parsed at :9683/:9718
with `_parse_scale_opt` only, so `range()` is dropped there as well (work item 3).

### Why `minmax` labels a tick where there is no data

`_apply_axis_spec`'s minmax branch, `dash_render.py:9136-9142`:

```python
elif mode == "minmax":
    col = self.df[varname] if varname in getattr(
        self.df, "columns", []) else None
```

`self.df` is the whole dataset. Two other places in the same file already do the right thing —
`dash_render.py:9679` and `:9714` pass `_source_frame(source, self.df)` into
`_compute_secondary_range`, with the helper defined at `:2411` — and `source` is in scope at
the tick loop (`:9903-9913`, inside `_make_figure_body`, which starts at `:9495`). So a
graph-level `if`/`in` qualifier narrows the data and the axis still carries a tick at the
unfiltered bound (work item 5). REMAINING.md is explicit about the limit of this fix: **do not
change the `by()` facet case** — Stata's `by()` shares a common axis by default, and dash's
global minmax across facets matches that.

Stata's own answer, from the ground-truth fixture `test/fixtures/axis_truth.json`, probe
`a_minmax` (`twoway scatter mpg weight, xlabel(minmax)`, `sysuse auto`):

```
x tick_values [1760.0, 4840.0]   tick_labels ['1,760', '4,840']
```

### Why nothing failed

REMAINING.md Appendix C, on the test surface (work items 6 and 9):

> Server-mode axis behaviour is covered only by source greps, so no test can fail on the
> server gaps. `test/test_server.py:999-1006` asserts `"xlabel" in source and "FixedTicker"
> in source` — true of the pre-09-02 parser as well — and `test/test_mode_parity.py` compares
> only background/border colours and whether a grid exists, with no axis cases in its
> parametrization and no ticker/formatter comparison.

and:

> `test/test_mode_parity.py` is the file whose docstring promises "the next divergence fails
> here rather than being found by a user", yet its figure-chrome comparison checks only
> background/border colour and grid presence — never ticker type, tick positions, formatter or
> `major_label_text_font_size` — and its CORPUS carries no axis `graph_options` at all. **That
> is structurally why every 09-02 server gap went unnoticed.**

Confirmed at HEAD: `test/test_axis_options.py` (932 lines) contains **zero** occurrences of
`ServerAppBuilder` or `server`; `test/test_mode_parity.py` (471 lines) contains **zero** lines
matching `ticker`, `formatter` or `major_label`. Its entire chrome comparison is:

```python
def _chrome(fig):
    return {
        "background_fill_color": fig.background_fill_color,
        "border_fill_color": fig.border_fill_color,
        "xgrid": [g.grid_line_color for g in fig.xgrid],
        "ygrid": [g.grid_line_color for g in fig.ygrid],
    }
```

---

## Epics

| epic | goal | items |
|---|---|---|
| **16.A — Port the grammar into the emitted app** | `dash serve` and `dash build, server` draw the axes `dash build` draws, from one parser, with no dead option reads left in the app. | 1, 2 |
| **16.B — Close the leaks in the helper 09-02 kept** | No sub-option text, and no bare word, ever reaches an axis as a tick label; value labels survive the JS lookup unescaped; the secondary axes and `minmax` use the same grammar and the same rows as the primary ones. | 3, 5, 7, 8 |
| **16.C — Make the next axis drift fail in CI** | The axis suite exercises both renderers, and the standing parity guard compares tickers, tick values, formatters and overrides — not just background colours. | 4, 6, 9 |

---

## User stories

### Epic 16.A — Port the grammar into the emitted app

**US-16.A.1** — *As a `dash serve` operator, I want the `xlabel()`/`ylabel()` grammar to work
in the served app exactly as it does in a built HTML file, so that the dashboard I serve to my
department is the one I checked before serving it.*

- **Given** a spec whose graph options carry `xlabel: "2000(500)4000"`,
  **when** the app emitted by `ServerAppBuilder` is executed and its document built,
  **then** the x axis ticker is a `FixedTicker` with ticks `[2000, 2500, 3000, 3500, 4000]` —
  the same object the standalone renderer produces from the same spec.
- **Given** `xlabel: "#5"`, **when** the served figure is built, **then** the ticker is a
  `BasicTicker` with `desired_num_ticks == 5`, not the default ticker.
- **Given** `xlabel: "none"`, **when** the served figure is built, **then** the ticker carries
  zero ticks and the x gridlines are off — `none` removes more ticks, never fewer.
- **Given** `ylabel: ", format(%9.0fc)"`, **when** the served figure is built, **then** the
  y-axis formatter is a `NumeralTickFormatter` with `format='0,0'`.
- **Given** `xlabel: ", labsize(large)"`, **then** `major_label_text_font_size == '15px'`.
- **Given** `xlabel: "2000 4000, grid"` / `", nogrid"`, **then** the x grid is drawn / is
  `None`, by the same rule the standalone renderer applies.

**US-16.A.2** — *As a Stata user pasting a `twoway` command into `dash serve`, I want
`xscale(range(1500 5000))` to move the served axis, so that the range I set is the range I
see.*

- **Given** `xscale: "range(1500 5000)"`, **when** the served figure is built, **then**
  `fig.x_range` is a `Range1d(1500, 5000)`.
- **Given** `yscale: "log range(1 100)"`, **then** the axis is logarithmic **and** the range is
  kept — the same behaviour REMAINING.md records for the standalone renderer.
- **Given** `xscale: "range(1500)"` (one bound), **then** the lower bound is 1500 and the upper
  bound is the data's own maximum.
- **Given** `yscale: "noextend"`, **when** the served app is built, **then** the same
  "not implemented and is being ignored" warning the standalone renderer emits is raised.

**US-16.A.3** — *As a package maintainer, I want exactly one axis parser in the codebase, so
that the next axis fix cannot land in one renderer and miss the other.*

- **Given** the emitted app source, **when** it is searched for a second tokeniser,
  **then** `_parse_axlabel` and `_parse_axangle` are absent and `_parse_axis_spec` /
  `_apply_axis_spec` are present, copied by `inspect.getsource` the way
  `_glyph_layer_lines` (`dash_render.py:12315`) already copies `GlyphMapper`.
- **Given** the emitted app source, **when** it is searched for `go.get('xrange'` or
  `go.get('yrange'`, **then** there is no match.

### Epic 16.B — Close the leaks in the helper 09-02 kept

**US-16.B.1** — *As a dashboard viewer, I want every tick label on an axis to be a number or a
label the author wrote in quotes, so that I never read option syntax off a chart and take it
for data.*

- **Given** `xlabel(2000 4000, format(%9.0fc))` in either renderer, **when** the figure is
  built, **then** no tick label anywhere on the figure contains the text `format(`,
  `labsize(`, `angle(` or `grid`.
- **Given** `ylabel(10 15 to 40)`, **when** the figure is built, **then** no tick carries the
  label `to`, and a `UserWarning` names the unrecognised token.
- **Given** `xlabel(2000 "low" 4000 "high")`, **then** the ticks *are* labelled `low` and
  `high` — quoting is what distinguishes the two cases.

**US-16.B.2** — *As a Stata user, I want `xlabel(2000 "R&D" 4000 "Other")` to draw `R&D` on
the axis, in both renderers, so that my labels are not mangled by HTML escaping that a canvas
never undoes.*

- **Given** a quoted label containing `&`, **when** the standalone figure is built, **then**
  `major_label_overrides` and the `CustomJSTickFormatter` map both carry `R&D`, not `R&amp;D`.
- **Given** the same option in server mode, **when** the served figure is built, **then**
  `major_label_overrides` is set (not only the formatter) and carries `R&D`.
- **Given** an integral tick, **when** the `CustomJSTickFormatter` map is inspected, **then**
  its key is the string JavaScript's `String(tick)` produces (`"2000"`), so the lookup hits.

**US-16.B.3** — *As a Stata user with a dual-axis graph, I want `xlabel2()`/`ylabel2()` and
`xscale2()`/`yscale2()` to accept everything `xlabel()`/`xscale()` accept, so that the second
axis is not a second-class axis.*

- **Given** `ylabel2("1000(500)2000")`, **then** the secondary y axis carries a `FixedTicker`
  with `[1000, 1500, 2000]`.
- **Given** `xlabel2(", format(%9.0fc) labsize(large)")`, **then** the secondary x axis gets
  the `NumeralTickFormatter` and the 15px label size, and **no** tick is labelled with
  sub-option text.
- **Given** `yscale2("range(0 100)")`, **then** `fig.extra_y_ranges["y2"]` spans 0–100.

**US-16.B.4** — *As a Stata user who wrote `if foreign==1` on the graph, I want
`xlabel(minmax)` to label the bounds of the rows I am looking at, so that no tick sits where
there is no data.*

- **Given** a graph-level `if_expr` that narrows the frame **and** `xlabel(minmax)`,
  **when** the figure is built, **then** the two ticks are the min and max of the **narrowed**
  rows.
- **Given** a `by()` facet graph with `xlabel(minmax)`, **when** the figures are built,
  **then** every facet still shares the global min/max — Stata's `by()` shares a common axis,
  and this behaviour is deliberately unchanged.

### Epic 16.C — Make the next axis drift fail in CI

**US-16.C.1** — *As a package maintainer, I want the parity guard to fail when an axis drifts
between renderers, so that the promise in its own docstring is true.*

- **Given** the parity corpus, **when** it is inspected, **then** it contains cases whose
  `graph_options` carry `xlabel`, `ylabel`, `xtick`, `xscale(range())` and a value-label pair.
- **Given** any corpus case, **when** both renderers build it, **then** ticker **type**, tick
  **values**, formatter **type and format string**, `major_label_overrides` and
  `major_label_text_font_size` are compared on both axes, and a difference fails the test.

**US-16.C.2** — *As a package maintainer, I want the axis suite to build server figures, not
grep server source, so that "the option name appears in the file" can never again be mistaken
for "the option works".*

- **Given** `test/test_axis_options.py`, **when** it is inspected, **then** it has a
  server-mode figure builder alongside `_fig_with_gopts`, following the `_figs(...)` harness in
  `test/test_server_legend.py:48-76`.
- **Given** `test/test_server.py:988-1010`, **when** the emitted app is built, **then** the
  assertions are made against the **built figure's models**, not against substrings of the
  source.

---

## Business requirements

| id | requirement | how it is tested |
|---|---|---|
| **BR-16.1** | Every `axis_label` form the standalone renderer implements — numlist, `a(b)c`, `#N`, `minmax`, `none`, quoted value-label pairs, `format()`, `labsize()`, `angle()`, `grid`/`nogrid` — produces the same Bokeh models in server mode as in standalone mode, for the same spec. | Row-for-row server assertions mirroring Appendix A's table, plus parity cases. |
| **BR-16.2** | `xscale(range())` / `yscale(range())` move the served axis, with one or two bounds, and combine with `log`. | Server range tests; parity case. |
| **BR-16.3** | No option key that `dash.ado` never emits is read anywhere in the package, in either renderer, including inside emitted string literals. | Dead-key guard extended to the `go.get('xrange'` spelling. |
| **BR-16.4** | Option syntax never appears as a tick label. For any option value containing sub-options, no tick label in the resulting figure contains sub-option text, in either renderer. | Cross-renderer leak test. |
| **BR-16.5** | Only a quoted token may become a tick label. A bare non-numeric token is reported, never drawn. | `ylabel(10 15 to 40)` test asserting labels are empty and a warning is raised. |
| **BR-16.6** | User-supplied tick label text reaches the canvas exactly as written — no HTML escaping — and its value-label lookup succeeds at runtime in both renderers. | `R&D` test plus formatter-key test; served `major_label_overrides` test. |
| **BR-16.7** | The secondary axes accept the same grammar as the primary axes, including `range()` on `xscale2()`/`yscale2()`. | Secondary-axis grammar tests. |
| **BR-16.8** | `minmax` reports the bounds of the rows the graph is actually drawing; `by()` facets keep a common axis. | `minmax` + `if_expr` test; `by()` test asserting the existing shared-axis behaviour. |
| **BR-16.9** | A future divergence in axis models between the two renderers fails in `test/test_mode_parity.py`, not in a user's dashboard. | Widened `_chrome`; axis cases in `CORPUS`. |
| **BR-16.10** | No axis assertion in the suite is satisfied by a source-code substring. | `test/test_server.py:988-1010` rewritten against built models. |

---

## Technical requirements

### The port mechanism (items 1, 2)

- **TR-16.1** — Port by copying, not by rewriting. `ServerAppBuilder._glyph_layer_lines`
  (`dash_render.py:12315`) already emits the renderer's own code into the app with
  `inspect.getsource`; its docstring states the rule this phase follows: *"the app gets ONE
  implementation — this one, copied by `inspect.getsource` as the statistical helpers already
  are — and the branches call into it."* `_parse_axis_spec` and `_apply_axis_spec` join that
  emission. Do **not** extend `_parse_axlabel`.
- **TR-16.2** — `_parse_axis_spec` (`dash_render.py:9305`) is a `@staticmethod` on
  `DashRenderer`. The builder already has the pattern for emitting one as a module-level
  function: the loop at `dash_render.py:12518-12529` takes `GlyphMapper._histogram_grid`,
  `GlyphMapper._default_lpoly_bwidth`, `GlyphMapper._compute_lpoly_fit`,
  `GlyphMapper._bootstrap_ci` and `DashRenderer._kpi_statistic`, strips leading `@` decorator
  lines, and rewrites `GlyphMapper._` / `DashRenderer._` to `_`. Add `_parse_axis_spec` (and
  `_parse_axis_label_opt`, which it calls) to that tuple.
- **TR-16.3** — **Callee closure.** `_apply_axis_spec` calls `_stata_numeric_pattern`
  (`dash_render.py:395`) and `_stata_date_kind` (`:271`). Neither is emitted today — every
  reference to either lives at or below `dash_render.py:10230`, i.e. entirely on the renderer
  side. Both must be added to the emitted module-level helper list (the tuple at
  `dash_render.py:12485-12502`), or the served page raises `NameError` at document-build time.
  This is exactly the failure the builder's own comment at `:12497-12500` warns about: *"a
  copied function whose callees stay behind raises NameError on the served page rather than
  here, where it would be noticed."*
- **TR-16.4** — `_apply_axis_spec` also calls `OptionTranslator.translate_msize` for
  `labsize()`. No new work: `OptionTranslator` is copied whole into the app at
  `dash_render.py:12408-12409` (`for _cls in (OptionTranslator, SchemeParser, GlyphMapper)`).
- **TR-16.5** — **Signature change.** `_apply_axis_spec(self, fig, axis_obj, grid_obj, spec,
  varname="")` reads `self.df` (the minmax branch, `:9136-9142`) and
  `getattr(self, "numeric_formats", {})` (`:9160`). The emitted app is a module, not a
  `DashRenderer` instance, so both must become explicit parameters — e.g.
  `_apply_axis_spec(fig, axis_obj, grid_obj, spec, varname="", frame=None,
  numeric_formats=None)`. This is the same change work item 5 needs for the `minmax` fix;
  make it once. Update the sole standalone call site, `dash_render.py:9913`.
- **TR-16.6** — **Emitted call site.** Replace the body of the loop at
  `dash_render.py:14012-14021` with a call to the emitted `_parse_axis_spec` /
  `_apply_axis_spec`, iterating `(('xlabel', fig.xaxis, fig.xgrid, _xvar), ('ylabel',
  fig.yaxis, fig.ygrid, _yvar))` so that `grid`/`nogrid` and the display-format fallback have
  the objects they need. Mirror the standalone loop's `xtick`/`ytick` fallback semantics from
  `dash_render.py:9906-9913` (`tick_key = "xtick" if ax_key == "xlabel" else "ytick"`), as
  Phase 14 redefines them. Delete the emitted `_parse_axlabel` (`:13989`) and `_parse_axangle`
  (`:14003-14011`) once `angle()` arrives through `spec["angle"]`.
- **TR-16.7** — **Scales.** In the emitted app, delete the `# xrange / yrange axis limits`
  block at `dash_render.py:13907-13920` outright, and extend the emitted xscale/yscale
  handling at `:13851-13866` (today: `log` and `reverse` only) to call the emitted
  `_parse_scale_range` (`dash_render.py:776`) and `_report_unhandled_scale_opts` (`:805`),
  reproducing the standalone logic at `:9746-9773` — including its one-bound rule, *"One bound
  given: keep the data's own value for the other"*, and its ordering note, *"Apply axis
  reversal (after any `Range1d` replacement so flipped sticks)"*. Both helpers are
  module-level functions and go into the same emitted-helper tuple as TR-16.3.
- **TR-16.8** — The figure is constructed before these run (`fig = bokeh_figure(**_fig_kw)` at
  `dash_render.py:13855`), so a `Range1d` assignment replaces `fig.x_range` / `fig.y_range`
  exactly as the standalone path does with `setattr(fig, _axis_attr, _Rng(...))`.

### The tokenizer and the label map (items 7, 8)

- **TR-16.9** — `_parse_axis_label_opt` (`dash_render.py:9393`) must accept a label **only**
  when the token was quoted. Its tokeniser currently discards that information at the
  flattening step (`flat.append(dq or sq or bare)`, ~`:9414-9417`), so it has to carry a
  per-token quoted flag, e.g. `flat.append((dq or sq, True))` vs `(bare, False)`. In the
  bare-token branch (~`:9425-9432`) an unquoted non-numeric token must be **reported**
  (`warnings.warn`, `UserWarning`) and dropped, not attached as a label. Measured behaviour to
  change: `_parse_axis_spec('10 15 to 40')` returns `labels={'15.0': 'to'}` today.
- **TR-16.10** — Keep `xlabel(1,3,5)` working: `_parse_axis_spec`'s comma rule
  (`re.search(r",\s*(?=[A-Za-z_])", head)`, `:9348-9350`) exists because *"Stata also accepts
  a comma-separated numlist, so `xlabel(1,3,5)` must survive"*. The quoting change must not
  disturb it.
- **TR-16.11** — **Formatter key.** `dash_render.py:9149-9158`:
  ```python
  safe = {str(k): html.escape(str(v)) for k, v in spec["labels"].items()}
  axis_obj.formatter = CustomJSTickFormatter(
      code=f"const m = {json.dumps(safe)}; "
           "return m[String(tick)] || String(tick);")
  axis_obj.major_label_overrides = {float(k): v for k, v in spec["labels"].items()}
  ```
  The map keys are `str(float)` — `'2000.0'` — and the JS looks up `String(tick)` — `'2000'`.
  Key the map with the string JavaScript produces: for a float that is integral, the integer
  spelling; otherwise the shortest round-tripping spelling. Drop `html.escape`: this is canvas
  text, the same defect the section registers at `:5638`.
- **TR-16.12** — **Served overrides.** The emitted axis code must set
  `major_label_overrides` as well as the formatter (`dash_render.py:14015-14021` today sets
  only the formatter). Once TR-16.1 lands, this is automatic — `_apply_axis_spec` sets both —
  which is the argument for porting rather than patching.

### The secondary axes (item 3)

- **TR-16.13** — Replace `self._parse_axis_label_opt(_raw_yla2)` at `dash_render.py:9699` and
  `self._parse_axis_label_opt(_raw_xla2)` at `:9734` with
  `spec = self._parse_axis_spec(raw)` followed by `_apply_axis_spec(fig, _y2_ax, [], spec,
  var2, frame, numeric_formats)` (and `_x2_ax`). The secondary axes have no grid of their own,
  so an empty grid sequence is the correct `grid_obj`; `_apply_axis_spec` iterates it
  (`for g in grid_obj`) and an empty sequence is a no-op — `grid`/`nogrid` on a secondary axis
  must therefore be reported as unhandled rather than silently swallowed.
- **TR-16.14** — Delete the duplicated formatter construction at `:9700-9707` and `:9735-9742`
  (`_safe2 = {str(k): html.escape(str(v)) ...}`) — it carries both the `str(float)` key
  mismatch and the `html.escape` defect, and `_apply_axis_spec` replaces it.
- **TR-16.15** — `_parse_axis_angle` calls at `:9708-9710` / `:9743-9745` become redundant:
  `spec["angle"]` already carries it.
- **TR-16.16** — `xscale2()`/`yscale2()` at `dash_render.py:9683` and `:9718` parse with
  `_parse_scale_opt` only. Add `_parse_scale_range` (`:776`) and apply the result to
  `fig.extra_y_ranges["y2"]` / `fig.extra_x_ranges["x2"]`, which are built one line earlier
  from `_compute_secondary_range`. Phase 15's item 2 adds
  `_report_unhandled_scale_opts(raw, 'yscale2'/'xscale2')` at the same two lines — land them
  together.

### `minmax` from the active view (item 5)

- **TR-16.17** — The minmax branch at `dash_render.py:9136-9142` must read the frame passed in
  under TR-16.5, not `self.df`. The call site at `dash_render.py:9903-9913` (inside
  `_make_figure_body`, which starts at `:9495`) has `source` in scope; pass
  `_source_frame(source, self.df)` — the helper at `dash_render.py:2411`, used correctly
  already at `:9679` and `:9714` with the comment *"From the ACTIVE view, not self.df: a
  graph-level if/in qualifier already narrowed the source"*.
- **TR-16.18** — Do **not** change the `by()` facet case. REMAINING.md: *"Stata's `by()` shares
  a common axis by default, and dash's global minmax across facets matches that."*
- **TR-16.19** — Server mode has no `minmax` at all today; TR-16.1 supplies it, and the frame
  passed in the emitted app must be the app's own active source, so that a served `minmax`
  axis obeys the same rule.

### Tests (items 4, 6, 9)

- **TR-16.20** — `test/test_axis_options.py` gets a server-mode figure builder beside
  `_fig_with_gopts` (defined at `test/test_axis_options.py:67`), following the `_figs(...)`
  harness at `test/test_server_legend.py:48-76`: write spec and data JSON to `tmp_path`, call
  `dr.ServerAppBuilder(str(spec), str(data)).build(str(app))`, load the module with
  `importlib.util.spec_from_file_location`, `exec_module` it, call `mod.make_document(doc)` on
  a fresh `bokeh.document.Document`, and select the figures with
  `[m for m in doc.select({"type": object}) if type(m).__name__ == "figure"]`.
- **TR-16.21** — `test/test_axis_options.py:248 test_the_dead_xrange_keys_are_gone` must reject
  the emitted spelling as well. Today it scans for `graph_opts.get("xrange"` /
  `graph_opts.get("yrange"` after stripping comments; add `go.get('xrange'` and
  `go.get('yrange'` (both quote styles) to the `dead` tuple.
- **TR-16.22** — `test/test_mode_parity.py`: add axis cases to `CORPUS` (defined at `:187`,
  normalised to 4-tuples at `:284`, each case `(name, plots, build_options,
  graph_options)`), and widen `_chrome` (`:178-184`) and `test_same_figure_chrome`
  (`:337-349`) to compare, for both axes: `type(axis.ticker).__name__`, `ticker.ticks` when
  present, `ticker.desired_num_ticks` when present, `type(axis.formatter).__name__`,
  `formatter.format` when present, `axis.major_label_overrides` and
  `axis.major_label_text_font_size`. Legitimate differences go in `ALLOWED`, per the file's own
  rule: *"Legitimate differences are listed explicitly, not tolerated by a loose comparison."*
- **TR-16.23** — `test/test_server.py:988-1010`
  (`TestServerGraphOptionsExtended::test_xlabel_code_in_server_source` and its `ylabel`
  sibling) asserts `"xlabel" in source and "FixedTicker" in source` — true of the pre-09-02
  parser too. Rewrite both against the built document's models using the TR-16.20 harness.
- **TR-16.24** — Ground truth for the tick tests is `test/fixtures/axis_truth.json` (233
  probes measured in Stata). The probes this phase's tests index, with their commands:

  | probe | Stata command | measured x-axis truth |
  |---|---|---|
  | `a_ticks_only` | `twoway scatter mpg weight, xtick(2500 3500)` | `n_ticks: 6`, `tick_values [2000, None, 3000, None, 4000, 5000]`, `tick_labels ['2,000', None, '3,000', None, '4,000', '5,000']` |
  | `a_mticks` | `twoway scatter mpg weight, xmtick(2250 2750 3250)` | `n_ticks: 7`, `tick_labels ['2,000', None, None, '3,000', None, '4,000', '5,000']` |
  | `b_ext_ticklist` | `twoway scatter mpg weight, xlabel(2000 3000 4000)` | `n_ticks: 3`, `tick_values [2000, 3000, 4000]`, `tick_labels ['2,000', '3,000', '4,000']` |
  | `a_minmax` | `twoway scatter mpg weight, xlabel(minmax)` | `tick_values [1760, 4840]`, `tick_labels ['1,760', '4,840']` |

  A `None` in `tick_labels` beside a `tick_px` entry is Stata's *unlabelled* tick — the shape
  the `xtick()`/`xmtick()` assertions must reproduce. (The `xtick`/`xmtick` *implementations*
  are Phase 14; the probes are named here because work item 4 asks this phase's tests to assert
  against them.)

---

## Work items

Numbered as handed over. Tags are `[kind · renderer · effort]`.

---

### 1. Port the axis_label grammar into `ServerAppBuilder`'s emitted app · `[functional · server · medium]`

> Port the axis_label grammar into ServerAppBuilder's emitted app. The app's own parser
> recognises only a bare numlist and quoted value-label pairs — #N, minmax, none, the a(b)c
> increment form, format(), labsize() and grid/nogrid are all dropped — and worse, because it
> tokenises the raw string without stripping sub-options first, sub-option text is rendered AS
> A TICK LABEL. The cleanest fix is to emit `_parse_axis_spec`/`_apply_axis_spec` into the app
> the way `_glyph_layer_lines` (dash_render.py:12315) already copies GlyphMapper in via
> inspect.getsource, rather than maintaining a second parser.

**Where:** `dash_render.py:13989` `_parse_axlabel` (emitted string literal inside
`ServerAppBuilder`); `dash_render.py:14012-14021` the emitted `for _axk, _axobj in (('xlabel',
fig.xaxis), ('ylabel', fig.yaxis))` loop; port targets are `dash_render.py:9305`
`DashRenderer._parse_axis_spec` and `dash_render.py:9112` `DashRenderer._apply_axis_spec`; emit
helper pattern at `dash_render.py:12315` `ServerAppBuilder._glyph_layer_lines`.

**Evidence:** Appendix B finding 2's table (every form → `BasicTicker` in server mode); the
emitted parser's own output, reproduced above — `'2000 4000, format(%9.0fc)'` →
`{'4000.0': 'format(%9.0fc)'}`. **Origin:** 09-02, Appendix B. **Requirements:** TR-16.1 –
TR-16.6, TR-16.12, TR-16.19.

---

### 2. Honour `xscale(range())` in the server app and delete the dead keys there · `[functional · server · small]`

> Honour xscale(range())/yscale(range()) in the emitted server app, and delete the dead
> `xrange`/`yrange` reads there. The task said explicitly: wire range() to the dead code OR
> delete the dead keys, 'do not leave both'. Both still exist in the file — DashRenderer took
> the first option, ServerAppBuilder kept the dead keys and got neither.

**Where:** `dash_render.py:13907-13920` (emitted `# xrange / yrange axis limits` block reading
`go.get('xrange','')` / `go.get('yrange','')`); `dash_render.py:13851-13866` (emitted
xscale/yscale handling — only `log` and `reverse`); reuse `dash_render.py:776`
`_parse_scale_range` and `dash_render.py:805` `_report_unhandled_scale_opts`.

**Evidence:** the ultraplan's *"Do not leave both"* clause quoted above; `_parse_scale_range`
occurs at only two lines in the file (776 def, 9757 call), both standalone. **Origin:** 09-02,
Appendix B. **Requirements:** TR-16.7, TR-16.8, TR-16.21.

---

### 3. Route the secondary axes through the new grammar · `[functional · standalone · small]`

> Route the secondary axes (xlabel2/ylabel2) through the new grammar. They still call the OLD
> `_parse_axis_label_opt` plus `_parse_axis_angle`, so #N, minmax, the a(b)c form, format(),
> labsize() and grid/nogrid are dropped there exactly as they were on the primary axes before
> 09-02 — and sub-option text leaks into the tick label the same way the server parser does.
> xscale2()/yscale2() also ignore range().

**Where:** `dash_render.py:9699` (`_ticks2, _labels2 = self._parse_axis_label_opt(_raw_yla2)`)
and `dash_render.py:9734` (same for `_raw_xla2`); `dash_render.py:9683` and `:9718`
(`_parse_scale_opt` on yscale2/xscale2, no `_parse_scale_range` call); switch both to
`dash_render.py:9305` `_parse_axis_spec` + `dash_render.py:9112` `_apply_axis_spec`.

**Evidence:** the secondary-axis code block quoted above — the old parser, the `str(k)` key and
the `html.escape`, all three. **Origin:** 09-02, Appendix B. **Requirements:** TR-16.13 –
TR-16.16.

---

### 4. Add the missing tests for the clauses above · `[deliverable · both · medium]`

> Add the missing tests for the clauses above: a server-side axis-grammar test (there is none —
> test/test_axis_options.py only ever builds DashRenderer figures via `_fig_with_gopts`), a
> test that sub-option text never becomes a tick label in either renderer, a
> display-format-fallback test with no xlabel present, xtick-adds-unlabelled-ticks and
> xmtick/ymtick/xmlabel/ymlabel tests against the axis_truth probes, an xlabel2/ylabel2 grammar
> test, and a dead-key guard that actually covers the emitted app.

**Where:** `test/test_axis_options.py` (add a server-mode variant of `_fig_with_gopts`
following the `_figs(...)` harness in `test/test_server_legend.py:48-76`);
`test/test_axis_options.py:248 test_the_dead_xrange_keys_are_gone` must also reject the
emitted-app spelling `go.get('xrange'`; ground truth already available in
`test/fixtures/axis_truth.json` probes `a_ticks_only`, `a_mticks`, `b_ext_ticklist`.

**Evidence:** `test/test_axis_options.py` contains zero occurrences of `ServerAppBuilder` or
`server` (confirmed at HEAD over all 932 lines). **Note on scope:** the
display-format-fallback and `xtick`/`xmtick` *implementations* belong to Phase 14; this item
owns their **tests**, which must be written against the `axis_truth` probes in TR-16.24 and
will fail until Phase 14 lands. Sequence Phase 14 first, or mark these `xfail(strict=True)`
for exactly as long as it takes. **Origin:** 09-02, Appendix B. **Requirements:** TR-16.20 –
TR-16.24.

---

### 5. `xlabel(minmax)` must use the graph's active, qualifier-narrowed source · `[functional · standalone · small]`

> DashRenderer's xlabel(minmax)/ylabel(minmax) computes the min and max from the UNFILTERED
> frame (self.df), not from the graph's active, qualifier-narrowed source, so a tick is drawn
> where no data exists. _apply_axis_spec's minmax branch (dash_render.py:9136-9142) reads
> `col = self.df[varname]`; two other places in the same function body already do the right
> thing with `_source_frame(source, self.df)` (dash_render.py:9676 and :9713,
> _compute_secondary_range), and `source` is in scope at the tick loop
> (dash_render.py:9903-9913, inside _make_figure_body which starts at :9495). Fix: pass
> `_source_frame(source, self.df)` into _apply_axis_spec and have the minmax branch read that
> frame instead of self.df. Note this is in addition to server mode, which has no minmax at all
> (auditor's remaining item 1). A guard test belongs in test/test_axis_options.py: minmax +
> graph-level if_expr must give the subset's min/max. Do NOT 'fix' the by() facet case the same
> way — Stata's by() shares a common axis by default, and dash's global minmax across facets
> matches that.

**Where:** `dash_render.py:9136-9142` (`_apply_axis_spec` minmax branch, `col =
self.df[varname]`); call site `dash_render.py:9903-9913`; the correct pattern is at
`dash_render.py:9676` and `:9713` (`_source_frame(source, self.df)`, defined at
`dash_render.py:2411`); test target `test/test_axis_options.py`.

**Evidence:** the branch is quoted above; `_source_frame` occurs at exactly three lines in the
file — 2411 (def), 9679, 9714 — and not at the minmax branch. **Coordination:** the same
defect is handed to **Phase 15** as its items 1 and 6 (item 6 narrows it further: `varname` is
`plots[0]`'s variable, `dash_render.py:9506-9507`, so a two-series graph labels at the *first*
series' bounds, and the one-bound `xscale(range(0))` fallback at `:9765-9770` reads the same
unfiltered frame). Implement the frame change **once**, under TR-16.5's signature change, and
let both phases' tests stand over it. **Origin:** 09-02, Appendix C. **Requirements:**
TR-16.5, TR-16.17 – TR-16.19.

---

### 6. Extend the standing parity guard so the next axis drift fails there · `[deliverable · both · small]`

> Extend the standing standalone/server parity guard so the next axis drift fails there.
> test/test_mode_parity.py is the file whose docstring promises "the next divergence fails here
> rather than being found by a user", yet its figure-chrome comparison checks only
> background/border colour and grid presence — never ticker type, tick positions, formatter or
> major_label_text_font_size — and its CORPUS carries no axis graph_options at all. That is
> structurally why every 09-02 server gap went unnoticed. The auditor's deliverable item only
> asks for server cases inside test/test_axis_options.py.

**Where:** `test/test_mode_parity.py` (CORPUS near `:287` and `_chrome`/`test_same_figure_chrome`
at `:337-349`).

**Evidence:** `_chrome` in full, quoted above — four keys, none of them a ticker; zero lines in
the 471-line file match `ticker`, `formatter` or `major_label` (confirmed at HEAD).
**Coordination:** **Phase 08** widens the same `CORPUS` from 17 to 36 plot types; this item
adds axis `graph_options` to it and widens `_chrome`. The two edits touch the same two regions
— land Phase 08 first or expect a merge. **Origin:** 09-02, Appendix C. **Requirements:**
TR-16.22.

---

### 7. A bare unquoted token must never become a tick label · `[functional · both · medium]`

> A bare (unquoted) non-numeric token in xlabel()/ylabel() is silently turned into a TICK
> LABEL, so Stata's `to` rule paints the word "to" on the axis. `DashRenderer._parse_axis_label_opt`
> (dash_render.py:9393) pairs every number with the next token whatever it is — it never
> requires quotes — and `_parse_axis_spec` (dash_render.py:9305) feeds it the leftover head
> text. This is the BR-09.2 leak the section was written to eliminate, surviving inside the
> helper 09-02 kept. Fix: only accept a QUOTED token as a label in `_parse_axis_label_opt`, and
> report (or expand) an unrecognised bare word; the emitted server app carries its own copy of
> the same tokenizer at dash_render.py:13989 `_parse_axlabel`.

**Where:** `dash_render.py:9393` `DashRenderer._parse_axis_label_opt` (bare-token branch,
~`:9425-9432`); `dash_render.py:9305` `_parse_axis_spec`; emitted copy `dash_render.py:13989`
`_parse_axlabel`.

**Evidence:** measured at HEAD — `DashRenderer._parse_axis_spec('10 15 to 40')` returns
`{'mode': 'explicit', 'ticks': [10.0, 15.0, 40.0], 'labels': {'15.0': 'to'}, ...}`.
**Coordination:** *expanding* `a b to c` into the numlist Stata means is **Phase 15** item 3
(together with `a/b` and `##N`); this item guarantees that until it is expanded it is
**reported**, never drawn. Once item 1 lands, the emitted copy disappears with
`_parse_axlabel`. **Origin:** 09-02, Appendix C. **Requirements:** TR-16.9, TR-16.10.

---

### 8. The value-label tick form: fix the JS key and stop escaping canvas text · `[functional · both · small]`

> The value-`label` tick form is broken at runtime in the served app, and the standalone's copy
> of it is HTML-escaped canvas text. The CustomJSTickFormatter map is keyed with Python's
> `str(float)` ("2000.0") while the JS in it looks up `String(tick)`, which is "2000" for an
> integral tick — so the lookup always misses. Standalone survives only because
> `_apply_axis_spec` also sets `major_label_overrides`, which Bokeh applies ahead of the
> formatter; the emitted server app sets no overrides, so a served `xlabel(2000 "low" 4000
> "high")` draws 2000/4000. Separately, the standalone escapes the label text into the JS map
> (`R&amp;D`), which is the same "canvas text must not be html.escaped" defect the section
> registers at `:5638`.

**Where:** `dash_render.py:9149-9158` in `_apply_axis_spec` (key the map with the same string
JS produces, drop the `html.escape`); emitted app `dash_render.py:14015-14021` (needs
`major_label_overrides`, not just the formatter).

**Evidence:** the code is quoted above; `major_label_overrides` occurs at exactly one line in
the file, `:9157` — so the emitted app has none. Both parsers were measured returning
`{'2000.0': 'low'}` for `2000 "low" 4000 "high"`. **Origin:** 09-02, Appendix C.
**Requirements:** TR-16.11, TR-16.12, TR-16.14.

---

### 9. Replace the server-mode source greps with model assertions · `[deliverable · both · medium]`

> Server-mode axis behaviour is covered only by source greps, so no test can fail on the server
> gaps. test/test_server.py:999-1006 asserts `"xlabel" in source and "FixedTicker" in source`
> — true of the pre-09-02 parser as well — and test/test_mode_parity.py compares only
> background/border colours and whether a grid exists, with no axis cases in its
> parametrization and no ticker/formatter comparison.

**Where:** `test/test_mode_parity.py` (add xlabel/ylabel/xscale cases comparing ticker type,
tick values, formatter and `major_label_overrides`); `test/test_server.py:988-1010`.

**Evidence:** the two tests are quoted above. `"xlabel" in source` is satisfied by the emitted
`go.get('xlabel', '')` line alone; `"FixedTicker" in source` is satisfied by the emitted
`from bokeh.models.tickers import FixedTicker as _FT` line alone — neither builds a figure.
**Origin:** 09-02, Appendix C. **Requirements:** TR-16.20, TR-16.22, TR-16.23.

---

## Test plan

Project rule 8: **every bug fix gets a regression test that fails before the fix and passes
after.** Project rule 4: **every function gets a unit test.** Each epic below therefore names a
failing-first test, the unit coverage, the integration coverage, and — because a test that
cannot die proves nothing — the mutation that must make each test fail.

### Shared harness work (prerequisite for everything below)

`test/test_axis_options.py` gains `_server_fig_with_gopts(plots, gopts, df=None)` beside
`_fig_with_gopts` (`:67`), built on the `_figs(...)` pattern from
`test/test_server_legend.py:48-76` (TR-16.20). The two builders take the same arguments and
return the same shape, so every grammar test can be parametrized over `("standalone",
"server")` rather than duplicated.

**Non-vacuity of the harness itself:** a test asserting that the server builder returns at
least one `figure` model, and that a deliberately bad `graph_options` value (e.g.
`{"xlabel": "2000 3000"}` compared against a wrong expectation) fails — if the harness ever
returns an empty list, every axis test in the file would pass vacuously, which is the failure
mode this whole phase exists to end.

### Epic 16.A — Port the grammar into the emitted app (items 1, 2)

**Failing test first** — `test/test_axis_options.py::TestServerAxisGrammar::test_suboption_text_is_never_a_tick_label`:
build the served figure for `{"xlabel": "2000 4000, format(%9.0fc)"}`, collect every tick
label the figure can produce (`major_label_overrides` values plus the JSON map inside
`axis.formatter.code`), and assert that none contains `format(`. **Fails at HEAD** — the map
is `{'4000.0': 'format(%9.0fc)'}`.

**Unit tests** (rule 4), one per grammar form, asserted on the *served* figure and mirroring
Appendix A's table row for row:

| test | option | assertion |
|---|---|---|
| `test_server_increment_form` | `xlabel: 2000(500)4000` | `FixedTicker`, ticks `[2000, 2500, 3000, 3500, 4000]` |
| `test_server_bare_numlist` | `xlabel: 2000 3000 4000` | `FixedTicker`, ticks `[2000, 3000, 4000]`; cross-checked against `axis_truth` probe `b_ext_ticklist` |
| `test_server_count_form` | `xlabel: #5` | `BasicTicker`, `desired_num_ticks == 5` |
| `test_server_minmax` | `xlabel: minmax` | `FixedTicker` with the served source's own min/max |
| `test_server_none` | `xlabel: none` | `FixedTicker(ticks=[])` **and** x gridlines `None` |
| `test_server_value_labels` | `xlabel: 2000 "low" 4000 "high"` | ticks **and** `major_label_overrides == {2000.0: 'low', 4000.0: 'high'}` |
| `test_server_format_suboption` | `ylabel: , format(%9.0fc)` | `NumeralTickFormatter(format='0,0')` |
| `test_server_labsize` | `xlabel: , labsize(large)` | `major_label_text_font_size == '15px'` |
| `test_server_angle` | `xlabel: , angle(45)` | `major_label_orientation` ≈ `0.7854` |
| `test_server_grid_nogrid` | `xlabel: 2000 4000, grid` / `, nogrid` | grid colour set / `None` |
| `test_server_scale_range` | `xscale: range(1500 5000)` | `fig.x_range` is `Range1d(1500, 5000)` |
| `test_server_scale_log_keeps_range` | `yscale: log range(1 100)` | log axis **and** the range |
| `test_server_scale_one_bound` | `xscale: range(1500)` | lower 1500, upper = data max |
| `test_server_unhandled_scale_opt_warns` | `yscale: noextend` | the same `UserWarning` the standalone path raises |

**Integration / cscript.** The Stata-side certification script for the axis grammar,
`test/test_axis_options.cscript`, is **Phase 14** item 6; when it exists, add a served-build
case to it so the end-to-end path `dash.ado` → spec JSON → emitted app is exercised in Stata,
following `test/test_option_surface.cscript` and registered in `test/run_all_cscripts.do`.
Set `$dash_nobrowser` before any Stata run that builds dashboards.

**Dead-key guard** — extend `test_the_dead_xrange_keys_are_gone`
(`test/test_axis_options.py:248`) with `go.get('xrange'` and `go.get('yrange'` (TR-16.21).

**Mutation proofs:**

| break this | this test must die |
|---|---|
| restore the emitted `_parse_axlabel` call in place of `_parse_axis_spec` | every `TestServerAxisGrammar` unit test |
| drop `major_label_overrides` from the emitted path | `test_server_value_labels` |
| re-add the emitted `# xrange / yrange axis limits` block | `test_the_dead_xrange_keys_are_gone` |
| remove the `_parse_scale_range` call from the emitted scale handling | `test_server_scale_range`, `test_server_scale_one_bound` |
| remove `_stata_numeric_pattern` from the emitted helper list | `test_server_format_suboption` (the served document raises `NameError`) |

### Epic 16.B — Close the leaks in the helper 09-02 kept (items 3, 5, 7, 8)

**Failing tests first**, one per defect:

1. `test_a_bare_word_is_never_a_tick_label` — `ylabel(10 15 to 40)`, both renderers: assert
   `spec["labels"] == {}` and that a `UserWarning` names `to`. **Fails at HEAD** (`{'15.0':
   'to'}`).
2. `test_value_label_map_key_matches_the_js_lookup` — `xlabel(2000 "low" 4000 "high")`: parse
   the JSON map out of `axis.formatter.code` and assert `"2000" in map`. **Fails at HEAD**
   (key is `"2000.0"`).
3. `test_tick_labels_are_not_html_escaped` — `xlabel(2000 "R&D")`: assert `R&D` in both the
   formatter map and `major_label_overrides`, and `R&amp;D` in neither. **Fails at HEAD.**
4. `test_secondary_axis_accepts_the_full_grammar` — `ylabel2("1000(500)2000")`: assert a
   `FixedTicker` with `[1000, 1500, 2000]` on the secondary axis. **Fails at HEAD** (the old
   parser returns no ticks for the increment form).
5. `test_minmax_uses_the_qualified_rows` — a graph-level `if_expr` narrowing the frame plus
   `xlabel(minmax)`: assert the two ticks equal the **subset's** min and max. **Fails at HEAD.**

**Unit tests** (rule 4): `_parse_axis_label_opt` directly — quoted label accepted, bare word
rejected **and** warned, `xlabel(1,3,5)` still parsed as three ticks (TR-16.10), quoted numeric
label (`2000 "2001"`) treated as a label not a tick; `_apply_axis_spec` directly with an
explicit `frame=` argument, asserting the minmax branch reads it and never `self.df`;
`_parse_scale_range` on `range(0 100)`, `range(100)`, `range(0,100)` and a malformed
`range(abc)`.

**Integration:** a dual-axis figure built through `_fig_with_gopts` with `ylabel2`, `xlabel2`,
`yscale2(range())` and `xscale2(range())` set together, asserting all four take effect on the
same figure; a `by()` facet figure with `xlabel(minmax)` asserting the facets **still share**
the global bounds (TR-16.18) — a guard against over-fixing item 5.

**Mutation proofs:**

| break this | this test must die |
|---|---|
| drop the quoted-token requirement in `_parse_axis_label_opt` | `test_a_bare_word_is_never_a_tick_label` |
| re-key the formatter map with `str(float(k))` | `test_value_label_map_key_matches_the_js_lookup` |
| re-add `html.escape` around the label text | `test_tick_labels_are_not_html_escaped` |
| point `:9699`/`:9734` back at `_parse_axis_label_opt` | `test_secondary_axis_accepts_the_full_grammar` |
| change `_source_frame(source, self.df)` back to `self.df` at the tick call site | `test_minmax_uses_the_qualified_rows` |
| make the `by()` path use the per-facet frame | the `by()` shared-axis guard |

### Epic 16.C — Make the next axis drift fail in CI (items 4, 6, 9)

**Failing test first** — widen `_chrome` and `test_same_figure_chrome`
(`test/test_mode_parity.py:178-184` and `:337-349`) to compare ticker type, tick values,
formatter type and format, `major_label_overrides` and `major_label_text_font_size`, and add
these `CORPUS` cases (case shape `(name, plots, build_options, graph_options)`):

```
("scatter, xlabel increment form",   _SCATTER, {}, {"xlabel": "2000(500)4000"})
("scatter, xlabel count form",       _SCATTER, {}, {"xlabel": "#5"})
("scatter, xlabel minmax",           _SCATTER, {}, {"xlabel": "minmax"})
("scatter, xlabel none",             _SCATTER, {}, {"xlabel": "none"})
("scatter, xlabel value labels",     _SCATTER, {}, {"xlabel": "2000 \"low\" 4000 \"high\""})
("scatter, ylabel format",           _SCATTER, {}, {"ylabel": ", format(%9.0fc)"})
("scatter, xlabel labsize + angle",  _SCATTER, {}, {"xlabel": ", labsize(large) angle(45)"})
("scatter, xscale range",            _SCATTER, {}, {"xscale": "range(1500 5000)"})
("scatter, xtick alongside xlabel",  _SCATTER, {}, {"xlabel": "2000 4000", "xtick": "2500 3500"})
```

Every one of these **fails at HEAD** on the widened comparison, which is the point: the guard
is what should have caught the whole of this phase.

**Model-based server tests** — rewrite
`test/test_server.py::TestServerGraphOptionsExtended::test_xlabel_code_in_server_source` and
its `ylabel` sibling (`:988-1010`) to build the document and assert on the ticker, replacing
`"xlabel" in source and "FixedTicker" in source`.

**Ground-truth tests** (item 4, against `test/fixtures/axis_truth.json`, TR-16.24):
`test_xtick_adds_unlabelled_ticks` (probe `a_ticks_only`: 6 ticks, 4 labelled),
`test_xmtick_adds_minor_ticks` (probe `a_mticks`: 7 ticks), `test_explicit_ticklist_labels`
(probe `b_ext_ticklist`: labels `'2,000' '3,000' '4,000'` — which also covers the display-format
fallback), `test_minmax_matches_stata` (probe `a_minmax`: `[1760, 4840]`). These index the
fixture rather than hardcoding dash's own numbers — REMAINING.md records that *"ten tests take
the `truth` fixture and not one indexes it"*, which is a separate item owned by **Phase 15**
(its item 9); these four are this phase's contribution to closing it.

**Mutation proofs:**

| break this | this test must die |
|---|---|
| set a different ticker class in one renderer only | `test_same_figure_chrome` on every axis case |
| drop `major_label_overrides` in the server path only | `test_same_figure_chrome` on the value-labels case |
| revert `test_server.py`'s assertions to substring greps | the rewritten tests pass vacuously → assert the *rewrite* by mutating the emitted ticker and watching them fail |
| replace a probe assertion with dash's own output | the `axis_truth` tests must be shown failing when the fixture value is perturbed |

### Suite-level requirement

Per project rule 5, before any commit: pull from local `main`, run the **full** pytest suite
and the **full** certification suite (from `test/`, under `arch -arm64`; a skip is not a pass),
and repeat until green. HEAD's baseline is **3,498 passed / 37 skipped; 25/25 cscripts**.

---

## Definition of done

**Epic 16.A**

- [ ] `_parse_axis_spec` and `_apply_axis_spec` appear in the emitted app, copied by
      `inspect.getsource`, not transcribed.
- [ ] `_parse_axlabel` (`:13989`) and `_parse_axangle` (`:14003-14011`) are deleted; a grep of
      the emitted app finds no second axis tokeniser.
- [ ] `_stata_numeric_pattern` and `_stata_date_kind` are emitted with them; a served figure
      with `ylabel(, format(%9.0fc))` builds without `NameError`.
- [ ] All ten forms in Appendix A's table produce the same models in server mode as in
      standalone mode.
- [ ] `xscale(range())` / `yscale(range())` work in the served app, with one bound and with
      `log`.
- [ ] The emitted `# xrange / yrange axis limits` block is gone; `go.get('xrange'` and
      `go.get('yrange'` appear nowhere in `dash_render.py`.
- [ ] `_report_unhandled_scale_opts` reaches the server path, so `yscale(noextend)` warns in
      both modes.

**Epic 16.B**

- [ ] A bare unquoted token is reported and dropped; `ylabel(10 15 to 40)` draws no tick
      labelled `to` in either renderer.
- [ ] `xlabel(1,3,5)` still yields three ticks.
- [ ] The `CustomJSTickFormatter` map is keyed with the string `String(tick)` produces, and the
      label text is **not** `html.escape`d, in the primary path, the secondary path and the
      emitted app.
- [ ] The emitted app sets `major_label_overrides`.
- [ ] `xlabel2`/`ylabel2` accept the full grammar; `xscale2`/`yscale2` honour `range()`.
- [ ] `minmax` reads the active, qualifier-narrowed frame; `by()` facets still share a common
      axis.
- [ ] `_apply_axis_spec`'s frame and formats arrive as parameters, not through `self`.

**Epic 16.C**

- [ ] `test/test_axis_options.py` builds **server** figures through a `_figs`-style harness.
- [ ] `test/test_mode_parity.py`'s `CORPUS` carries axis `graph_options`, and `_chrome`
      compares ticker type, tick values, formatter, overrides and label font size.
- [ ] `test/test_server.py:988-1010` asserts on models, not on substrings.
- [ ] The four `axis_truth` probes named in TR-16.24 are indexed by tests, not paraphrased.
- [ ] Every new test has a recorded mutation that kills it.

**Cross-cutting**

- [ ] Each of the six functional items has a regression test that was demonstrated failing
      before the fix (rule 8).
- [ ] Full pytest suite and full cscript suite green, from a tree freshly pulled from local
      `main` (rule 5).
- [ ] Commit on the feature branch only, with the merge command supplied, and no mention of any
      AI tool in the message (rules 6 and 7).
- [ ] `CHANGELOG` records the server port and the three tokenizer fixes.
- [ ] **`REMAINING.md` is untouched.**

---

## Risks and sequencing notes

**Sequence inside the phase.** 7 → 8 → 5 → 3 → 1 → 2 → 4/6/9. Every one of those fixes lands in
`_parse_axis_label_opt`, `_parse_axis_spec` or `_apply_axis_spec` — the three functions item 1
then copies into the emitted app. Porting first means porting a parser that still writes `to`
on an axis, and then porting again.

**Phases 14 and 15 are upstream of the port, for the same reason.** Phase 14 changes
`_apply_axis_spec` (the `#e5e5e5` grid literal → `self.grid_color`, the `xtick` semantics, the
display-format fallback) and Phase 15 changes both functions (numlist rules `a/b`, `a b to c`,
`##N`; date awareness; ticker-class preservation on a log axis; the `varname` selection). Each
lands *before* the copy, or the copy is stale on arrival. If schedule pressure forces the port
earlier, the mitigation is cheap and must be written down: because the app receives the
function **by `inspect.getsource`**, a later change to either function propagates on the next
build with no second edit — that is the whole argument for TR-16.1. The risk is only that the
emitted *call site* (TR-16.6) may need a signature update.

**The `self.grid_color` dependency.** Phase 14's item 5 replaces the hardcoded `#e5e5e5` at
`dash_render.py:9184-9190` with `self.grid_color` / `self.minor_grid_color`. That adds a
*second* `self` dependency to a function this phase turns into a module-level one (TR-16.5).
Agree the signature once: pass the resolved grid colours in, alongside `frame` and
`numeric_formats`. The emitted app already resolves the scheme (`_dash_apply_scheme(fig)`,
`dash_render.py:13856`), so the values exist on both sides.

**Overlap with Phase 08 in one file.** Items 6 and 9 edit `test/test_mode_parity.py`'s `CORPUS`
and `_chrome`; Phase 08 widens the same `CORPUS` from 17 to 36 plot types. Land Phase 08 first,
or expect a merge in exactly those two regions.

**Overlap with Phase 15 on `minmax`.** Item 5 here and items 1 and 6 there are the same defect
seen from three angles (wrong rows; wrong rows *and* wrong variable; the `xscale(range(0))`
one-bound fallback reading the same unfiltered frame). One implementation, three tests; do not
write two.

**Item 4 can only go green behind Phase 14.** Its `xtick`/`xmtick`/`ymtick`/`xmlabel`/`ymlabel`
and display-format-fallback tests assert behaviour Phase 14 implements. Either schedule Phase
14 first or land them `xfail(strict=True)` — strict, so they fail loudly the moment Phase 14
makes them pass and are not left as permanent decoration.

**The `none` regression risk in server mode.** Today a served `xlabel(none)` silently draws the
default ticks. After the port it draws none — a visible change to existing served dashboards,
and the correct one (Appendix A records that Stata's `xlabel(none)` also removes the
gridlines). Worth a CHANGELOG line of its own.

**Tokenizer change and quoted numerics.** Requiring quotes for labels changes how
`xlabel(2000 "2001")` parses: `"2001"` becomes a *label* for the 2000 tick rather than a second
tick. That matches Stata, and it is a behaviour change — cover it with an explicit test so it
is a decision on the record rather than a side effect.

**Documentation is Phase 30, not this phase.** `dash.sthlp:873-895` advertises the whole axis
grammar with no server caveat and `dash.sthlp:512-525` is the Server Mode difference table that
does not mention axes. Phase 30's item 6 disposes of both — and once this phase lands, the
disposal is a deletion rather than a new limitation to document. Tell Phase 30 when this lands;
`test/test_help_conformance.py` is the file that notices if the two drift apart.
