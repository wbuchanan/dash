# Research — `dash` gap and hardcoding audit

Eight parallel audit agents plus direct empirical probing against live StataNow 19.5.
Every finding below is cited to `file:line` and was verified in code; findings marked
**[measured]** were additionally reproduced by running the software.

---

## 0. Executive summary

| Class | Count | Worst instance |
|---|---|---|
| **Distribution** | 1 | `net install` produces a package that tracebacks on every command **[measured]** |
| **Server mode** | ~20 | `bokeh serve app.py` serves an **empty document**; `/health` 404 **[measured]** |
| **Rejected `twoway` syntax** | 37 of 59 probed | `bin()`, `level()`, `xsize()`, `sort`, `mlab()`, `msym()` all `r(198)` **[measured]** |
| **Accepted then silently discarded** | ~35 | `scatter y1 y2 x` renders one series instead of two **[measured]** |
| **Hardcoded values that should be derived** | 211 total (73 HIGH) | histogram always 10 bins; Stata gives 8 and 33 on two real datasets **[measured]** |
| **Scheme pipeline** | 63 of 108 parsed keys unused | `stcolor` (the Stata 18+ default) renders **every series black** |
| **Doc/code divergence** | see §7 | help says only `play()`/`nodraw` are unsupported |
| **Test-suite integrity** | see §8 | cscript runner prints "ALL TESTS PASSED" having asserted nothing |

Totals for the hardcoding audit across `dash_render.py`, split by the four line ranges
audited: 70 + 81 + 60 findings in lines 1-2600 / 2600-5100 / 5100-7800 respectively, plus
the Stata-side and server-mode registers.

---

## 1. BLOCKER — the package cannot be installed **[measured]**

`dash.pkg` declares six files and omits `schemes/`. `SchemeParser._SCHEMES_DIR`
(`dash_render.py:702`) is a sibling of `dash_render.py`, so after `net install` it does not
exist. The recovery path is:

```python
try:    self.scheme = SchemeParser(_scheme_name)
except (ValueError, OSError):
        self.scheme = SchemeParser("s2color")   # dash_render.py:5004 — outside the try
```

The fallback resolves the same missing directory and raises the same `ValueError`, uncaught.
`GlyphMapper.__init__:1142` fails identically.

Reproduced by staging exactly the six declared files into a clean directory: `DashRenderer`
construction raises `ValueError: dash: scheme 's2color' not found`. In the development tree
it succeeds. **Every `dash` command would traceback for every user who installs the package
the advertised way.** No test can catch it — every test runs from the repo.

---

## 2. BLOCKER — server mode serves nothing **[measured]**

The generated app binds `make_document` to a `Server` and registers `/health` only inside
`if __name__ == '__main__':` (`dash_render.py:10305-10313`), and never calls `curdoc()`
(zero grep hits). Bokeh's `CodeRunner` executes app scripts under a synthetic module name
`bokeh_app_<uuid>`, so that guard is **always false**.

Verified by generating an app and serving it: `docs_json` is literally `{}`, the title is
absent, `/health` returns 404. `python app.py` works; no documented workflow uses it.

This is the path `dash serve` takes (`dash_render.py:10419`), the path `dash.ado:1471` tells
the user to run, and the path `dash.sthlp:438` documents.

### Everything downstream of it

- **`dash serve` can never create a filter widget.** `_dash_serve`'s syntax is
  `[, PORT() NOBROWSER TIMEOUT()]` (`dash.ado:1487`) and its master JSON is hardcoded
  (`dash.ado:1603`) to `layout:"auto"`, `link:""`, `filter:""`, `theme:"default"`,
  `title:""`, `subtitle:""`, with `tabs` and `filter_position` absent entirely. It inherits
  nothing from a prior `dash build`. The help's own example (`dash.sthlp:487-490`) puts
  `filter(foreign,...)` on the `dash build` line and then runs `dash serve` — demonstrating
  the bug. Live filtering is the single feature server mode is sold on (`dash.sthlp:200-206`).
- **`dash build, saving(app.py) server` blocks Stata and opens a browser.**
  `_dash_do_render` (`dash.ado:142`) sets `sys.argv` with no `--no-browser` and no
  `--timeout`, then `runpy.run_path(..., run_name="__main__")` runs the launcher *inside
  Stata*: a browser opens after 1.5 s (`:10436-10441`), timeout defaults to 0 so nothing
  stops, and `_proc.wait()` (`:10452`) blocks forever. `dash.sthlp` denies this in three
  places — `:82`, `:249-251` ("does not block or open a browser"), `:492`.
- **`update(brush)` is dead in BOTH paths.** Standalone has no selection callback at all
  (`_kpi_update_modes` at `:5030` is assigned and never read); the server's callback binds to
  `shared_source` (`:10232`), which no glyph renders from. `dash.sthlp:424` claims
  "Yes / Yes" — false twice.
- `link()` is broken in server mode for the same reason.
- `tabs()`, `layout()`, `filterposition()`, `theme()` are never read by the generated app —
  `layout_opt` and `theme_opt` are computed at `:7832`/`:7835` and never used.

### Architectural cause, quantified

38 `map_*` methods in the standalone renderer; 37 `ptype` branches in the server main loop;
16 more in the `by()` facet loop; 16 more in `by(total)`. **16 plot types are implemented
four times and 21 more twice — 107 implementations for 38 behaviours.** KPI card HTML exists
in 5 places, histogram binning in 4, KPI statistics in 4 (one of them Stata's `summarize`).

The drift is already user-visible for identical commands: histogram bins 10 vs 20; lowess
`frac` 0.8 vs a hardcoded 0.5 with `bwidth()` ignored; lfit grid 200-points-with-padding vs
100-without; default series colour scheme-derived vs the literal `#1f77b4`; KPI card
36px/bordered vs 28px/borderless; and `msize(large)` resolving to 12px *or* 11px within the
same generated file (7 duplicated size maps on 2 incompatible scales).

### Security and hygiene in the generated app

| Finding | Line |
|---|---|
| `args.port` never forwarded to `builder.build()` — every app embeds `_port = 5006` **[measured with `--port 7777`]** | `:10356` |
| `allow_websocket_origin` fixed to `localhost:<port>` — 127.0.0.1 or LAN access gets a blank page, no option | `:10310`, `:10422` |
| `X-Forwarded-For` trusted unconditionally — rate limiter bypassable by header spoofing | `:7975-7979` |
| Temp app written as `` `_serve_app_base'.py `` while Stata cleans up `_serve_app_base` — **a file containing the full dataset base64-encoded leaks into the temp dir permanently** | `dash.ado:1633-1634` |
| `from scipy import stats` unguarded at module scope (lazy in standalone) | `:7882` |
| Missing `statsmodels` silently draws raw points and calls them a lowess curve | `:8147-8148` |
| `/health` uses deprecated `datetime.utcnow()` — `DeprecationWarning` on Python 3.14 **[measured]** | `:7995` |

---

## 3. Rejected `twoway` syntax — 37 of 59 probed commands abort **[measured]**

Method: `dash <spec>, name(gN)` under `capture` against live Stata, `dash clear` between
each. Full transcript in the plan's appendix.

### r(198) — "option not allowed", aborts the user's do-file

| Group | Options rejected |
|---|---|
| Graph geometry | `xsize()` `ysize()` `text()` `xtick()` `xmlabel()` `t1title()` `b1title()` `title2()` |
| Plot behaviour | `sort` `horizontal` `mlwidth()` `mstyle()` `lstyle()` `color()` `blabel()` |
| Histogram | `bin()` `width()` `start()` `percent` `frequency` `density` |
| Density / smoothing | `kernel()` `n()` |
| Inference | `level()` |
| Documented-as-ignored | `nodraw` `play()` — **neither string appears anywhere in the source**; the help promises a warning, the reality is an abort |
| Plot types | `contour` `pccapsym` |
| **Abbreviations** | `mlab()` `msym()` `xlab()` `mcol()` `lcol()` |

`function y=x**2, range(0 10)` and `, n(400)` fail with r(101).

### The abbreviation problem is structural

`dash.ado` declares every option in **lowercase**, which disables Stata's own abbreviation,
and simulates abbreviation with a fixed exact-match table (`dash_parse.mata:179-253`). It
accepts one short form plus the full name and rejects every intermediate prefix. About **25**
standard `twoway` abbreviations hard-fail: `mlab` `msym` `msy` `xlab` `ylab` `xtit` `ytit`
`lcol` `lwid` `lpat` `mcol` `msiz` `lege` `subt` `capt` `xli` `yli` `tit` `aspe` `conn`
`drop` `scat` and more.

**Five are mis-mapped to a different option — silent wrong output, not an error:**
`mlc`→`mlabcolor` (Stata: `mlcolor`, the marker outline), `mlw`→`mlabwidth` (Stata:
`mlwidth`, which `dash` does not even declare), plus `mls`, `mlp`, `mlg`.

And `dash.sthlp` documents five spellings that do not work: `mlac` (537), `mlas` (538),
`mlap` (540), `mlag` (543), and `xlab` (639) — the last contradicting `xla` at line 637.

No test covers any of this.

**Fix direction:** delete the table and capitalise the minimum abbreviation in the `syntax`
declarations, which is what Stata's own commands do. That single change fixes all 25 and
removes the five mis-mappings.

### Accepted by `syntax`, sub-option then discarded (silent) **[measured]**

These pass because they are declared `string asis`, then lose their contents:

| Written by the user | What is dropped |
|---|---|
| `title("T", size(large))` | `size()` |
| `legend(order(1 2))` | `order()`, and also `size()`, `region()`, `position(1..12)` — `loc_map` (`:6006-6014`) knows 6 keywords only |
| `ylabel(, format(%9.0fc))` | `format()` |
| `xlabel(#10)` | the `#N` tick-count form → **zero ticks** |
| `xlabel(minmax)` | → **zero ticks** |
| `xlabel(1990(5)2020)` | numlist increment form → **zero ticks** |
| `yscale(range(0 50))` | `range()` — `_parse_scale_opt` knows only `log` and `reverse`; meanwhile `:5799-5817` reads `xrange`/`yrange`, keys `dash.ado` never emits |
| `graphregion(margin(zero))` | `margin()` |

---

## 4. Accepted then silently discarded

### 4.1 Multi-variable plot specs lose series **[measured]**

`twoway scatter mpg price weight` draws **two** series. `dash` draws **one**:
`_dash_parse_varpart_std` (`dash.ado:665-670`) takes `yvar = word 1`, `xvar = last word`,
and discards everything between. Confirmed by colour census of the generated HTML — one
series colour (`#1a476f`) for the 3-variable form, two (`#1a476f`, `#90353b`) for the
explicitly overlaid form. No error, no warning.

This is the most damaging silent break found: `y1 y2 ... x` is everyday `twoway` syntax.

### 4.2 `layout(bs)` deletes every faceted graph **[measured]**

Two dashboards identical except for `layout()`:

| Marker in the generated HTML | `layout(bs)` | `layout(auto)` |
|---|---|---|
| the by-graph's title | **absent** | present |
| the ordinary graph's title | present | present |
| facet labels `Domestic` / `Foreign` | **absent** | present |

The Bootstrap grid checks `name in self.figures` (`:6546`), but faceted graphs are keyed
`name__by__0`, `name__by__1`, ... so the lookup misses and the graph is dropped. This
combines the abstract's two headline features — Bootstrap responsiveness and `twoway`'s
`by()` — and loses one silently.

### 4.3 Options parsed, serialized, and never read

Confirmed by grep across all 10,455 lines. `dash.ado` parses and serializes each of these
into the spec JSON; `dash_render.py` contains zero reads:

`falpha` / `fa` · `mlcolor` · `pstyle` · `cmissing` · `recast` · `connect` · `mlabwidth` ·
`coloruseplegend` · graph-level `scheme`

`scheme()` is worse than previously understood: it is parsed (`dash.ado:239`, `:319`),
abbreviation-expanded (`dash_parse.mata:243`) and escaped into `graph_options`
(`dash.ado:514`) — then never read in **any** of the three paths. `dash_render.py:4990-5000`
resolves the scheme only from `build_options`, and `dash build`'s syntax has no `scheme()`.
So the option documented as "fully supported" (`dash.sthlp:161-162`) is dead everywhere; the
only working knob is `theme()` on `dash build`.

### 4.4 Reachable options ignored by specific glyphs

| Option | Honoured by | Ignored by |
|---|---|---|
| `base()` | `map_bar:2094`, `map_area:2186` | `map_dropline:3415` (always drops to 0) |
| `barwidth()` | `map_bar:2175` | `map_rbar:3161` |
| `msize()`/`msymbol()`/`msangle()` | scatter, connected, dot, ... | `map_dropline:3440` (never calls `_apply_marker_opts`) |
| `bwidth()` | `map_lowess`, `map_lpoly` | `map_kdensity:3068` (uses scipy's Scott's rule), `map_fpfit:2843`, `map_fpfitci:2898` — the last two contradicting `dash.sthlp:559-560` |
| cap width | — | `map_rcap:3246`, `map_rcapsym:3486` fixed at `0.2` |

### 4.5 Other silent losses

- **`link(_all)` silently produces an unlinked dashboard** in the standalone path.
  Two audits disagreed on this, so it was resolved directly. `_all` IS expanded in three
  places: `_setup_sources:6855`, `_build_figures:6983`, and
  `ServerAppBuilder._generate_app_source:7842`. But `_build_figures:6970` is the only caller
  of `_setup_sources`, and **nothing calls `_build_figures`** outside tests — both are dead
  code. The production standalone path is `render():7488`, which derives `link_names` at
  `:7510-7512` with **no `_all` expansion**, so no graph name matches and every graph falls
  into the unlinked branch. The command returns `rc=0`, which is why it looks implemented.
  Documented at `dash.sthlp:295`.
- `layout(name:row,col ...)` is validated in Stata (`dash.ado:1224-1227`) and documented
  (`dash.sthlp:271-275`) but `_compute_grid` calls `int(parts[0])` on `"s1:1,1"`, throws
  `ValueError` and falls through to auto.
- `tabs()` is parsed and passed to Python but **discarded unless `layout(bs...)`**
  (`:7372`), with no warning. Tab labels are forcibly `.title()`-cased (`:6692`) —
  `tabs(MPG stuff: u1)` renders as "Mpg Stuff", with no way to suppress it.
- `_NONSELECTION_ALPHA` (`:109`) is applied only in `_build_figures`, which `render()` never
  calls — **linked-brush dimming never ships**.
- `filter(x, label("..."))` is read at `:7189` but nothing ever sets it.
- `hover()` is read at `:6063` and `:4940` but does not exist in `dash.ado` at all.
- `if` qualifiers using Stata functions (`!missing()`, `inlist()`, `< .`) fail the AST
  whitelist (`:4318-4353`), warn, and render **unfiltered**.
- `dash kpi ... if ...` computes the conditional value in Stata and then throws it away —
  `_build_kpi_html` recomputes from the full DataFrame (`:7125-7133`).
- `p25` and `p75` KPIs are absent from the JS recompute list (`:4504-4528`); on the first
  filter interaction they fall through to `result = 0` and **display 0**.
- Unicode variable and filter names are rejected by ASCII-only regexes; the `filter()` one
  (`dash.ado:1351`) drops them **silently**.

---

## 5. Hardcoded values that should be derived

211 findings across the four audited ranges of `dash_render.py` plus the Stata side.
73 are HIGH — meaning Stata gives the user a documented way to control the value and `dash`
either ignores the option or does not offer one.

### 5.1 Statistical defaults — the most consequential group

| Line | Hardcoded | Stata's behaviour | Reachable? |
|---|---|---|---|
| `:3001` | `options.get("bin", 10)` — 10 bins at every N | `k = min(sqrt(N), 10*ln(N)/ln(10))`. **[measured]** auto/mpg: Stata **8**, dash 10. nlsw88/wage: Stata **33**, dash 10 | `bin()` **UNREACHABLE** |
| `:3003` | `np.histogram` returns raw **counts** | default y-axis is **density**; `percent`/`fraction`/`frequency` selectable | all four **UNREACHABLE** |
| `:1343-1344`, `:2441`, `:8101`, `:8123` | `2.5`/`97.5` percentiles, `t.ppf(0.975)` — **CI level fixed at 95%** in four places | `c(level)` (=95 here) and `level()` | `level()` **UNREACHABLE**; `c(level)` never read |
| `:3066`, `:2611` | kernel fixed **Gaussian** | Stata's default for `kdensity` and `lpoly` is **epanechnikov** | `kernel()` **UNREACHABLE** |
| `:3068` | `map_kdensity` computes bandwidth from scipy's **Scott's rule** and never reads `bwidth` | `bwidth()` | `bwidth()` IS reachable — silently ignored |
| `:4617` vs `:3068` | filter-callback KDE uses **Silverman**, initial render uses **Scott's** | — | touching any filter makes the curve jump even with no rows removed; the comment at `:3080-3081` admits it |
| `:2667`, `:2604` | `map_lpoly` treats `bwidth` as a **fraction of x-range** clamped to `[0.01,1.0]` | Stata's `lpoly bwidth()` is an **absolute bandwidth in data units** | `bwidth(5)` on `weight` clamps to the whole x-range — the opposite of the request |
| `:5951`, `:4121` | every `twoway function` plotted over **x ∈ [0,1]** | `range()`, default = the x-axis range | `range()` **UNREACHABLE**; the read at `:5953` is dead code |
| `:5952` | `n_pts = 200` | Stata's default is **300** | `n()` **UNREACHABLE**; dead read at `:5960` |
| `:2880-2883`, `:2941-2944` | `fpfit` truncated to the **1st-99th percentile** of x; **200** points in `fpfit` vs **150** in `fpfitci` | full estimation range | the two disagree on the same data |
| `:4085` | `map_mband` invents `clip(ceil(n/5), 2, 20)` equal-**width** bands | `bands()`, cross-medians | `bands()` absent |
| `:1303` vs `:2513` | bootstrap `n_boot` 200 vs 500, docstrings contradict; `seed=42` fixed at `:1304` | — | not reproducible per user |
| `:2582` | `_compute_lpoly_fit` `bwidth=0.5` | Stata computes a rule-of-thumb bandwidth **from the data** | — |
| `:2324`, `:2371`, `:2432`, `:2505` | fit grids of `200` points with a `0.1 *` range extension | — | MEDIUM |

### 5.2 Visual defaults that ignore the scheme

Every one of these has a value sitting in the parsed scheme object that is never read:

| Line | Hardcoded | Scheme key that exists and is ignored |
|---|---|---|
| `:1936` | `marker = "circle"` for every series | `p_symbols` (`:951`) |
| `:1971` | `size = 8` | `gsize` / `medium` = 11 — and `:3586` in the same file already uses `medium` |
| `:1974`, `:2199`, `:2106` | `alpha=0.7`, `fill_alpha=0.8`, `fill_alpha=0.5` | `fill_alpha`, `bar_alpha`, `area_alpha` (all 0.8, all unread) |
| `:2023` + 8 sites | `line_width` 1.5 or 2.0 | `default_line_width` (`:961`) |
| `:2330` | `line_dash="solid"` for every series | `p_line_patterns` (`:956`), `default_line_pattern()` (`:1000`, **zero call sites**) |
| `:1727-1730` | `Category10_10` for discrete `colorvar` | `scheme.p_colors` |
| `:1780-1781` | `Viridis256` for continuous `colorvar` | scheme palette |
| `:1769`, `:1797` | colorbar `"right"` | `legend(position() ring())` — parsed, ignored |
| `:1860` | mlabel `"10px"` | `scheme.text_font_size` |
| `:5643-5644` | figure title has no colour, size or alignment | `title_color`, `heading_font_size` |
| `:5866-5867` | `note()`/`caption()` both 11px `#555555`, both at screen `(0,0)` `"below"` → **they overlap** | `note_font_size` (`gsize note`), 0 consumers |
| `:5878-5879` | subtitle 13px `#444444`, collides with the title | `gsize subheading` — not even parsed |
| `:5846`, `:5853` | `xline`/`yline` forced grey dashed; `_parse_refline` float-casts tokens and discards `lcolor()`/`lpattern()`/`lwidth()` that `dash.ado` passed through intact | — |
| `:386-387` | `"none": "#ffffff"` — `fcolor(none)` paints an **opaque white blob** instead of nothing | should be `fill_alpha=0` |
| `:6289-6290` | KPI colours bypass **both** `translate_mcolor` and `_sanitize_css_color` on the initial render — CSS-property injection, unlike the JS path at `:7292-7297` | SECURITY |

**The dead-CSS finding is the highest-leverage single fix.** `css_block()` (`:1026-1035`)
emits `.dash-title` / `.dash-subtitle` / `.kpi-card`; the HTML emits `db-title` /
`db-subtitle` and inline-styled KPI divs (`:6551`, `:6555`, `:6292-6300`). **All three
selectors match nothing.** Four scheme values are inert for the cost of a class-name change.

### 5.3 Figure geometry — no lever exists at all **[measured]**

`:5643-5650` creates every figure with `sizing_mode="stretch_width"` and no `width`,
`height` or `frame_width`. Neither generated file in the empirical test contains any of the
three. Meanwhile:

- `twoway` has `xsize()` / `ysize()` — both `r(198)` in `dash`.
- Stata schemes carry `graphsize 5`, `graphsize x 5.5`, `graphsize y 4` — `SchemeParser` does
  not parse `graphsize` at all.
- `_compute_grid`'s `ceil(sqrt(n))`, and the Bootstrap auto-layout's "4 KPIs per row",
  `span = 12 // per_row`, and the 1→col-12 / 2-4→col-6 / ≥5→col-4 thresholds are all fixed.
- The Bootstrap grid is responsive at the `md` breakpoint only — every cell is
  `db-col-12 db-col-sm-12 db-col-md-{span}` (`:6567-6571`), so it stacks to full width below
  768 px regardless of content.

There is currently **no way — by option, by scheme, or by data — for a user to influence plot
proportions.** (Confirmed non-finding: there is no Bootstrap CDN URL or version to manage;
the grid is fully inline under a `db-` prefix.)

### 5.4 Data-derived values that are not

| Line | Issue |
|---|---|
| `:5061-5083` | `_load_data` never reads Stata **display formats** — see §5.5 |
| `:6078-6089` | hover labels rows with raw **variable names**; `self.variable_labels` is loaded and used for axes (`_axis_label:5540`) but not for hover |
| `:6078-6089` | tooltip values are bare `@{var}` with no format |
| `:6127-6131` | fallback tooltips hardcode three different precisions (`{0.2f}`, `{0.3f}`, `{0.4f}`) |
| `:7118-7133` vs `:7277` | KPI format default mismatch — initial render `fmt=""` (full float precision), filter callback `"%9.0f"` (0 dp). **The number's precision changes the instant a filter moves.** |
| `:4809`, `:4862` | slider `vstep = (vmax-vmin)/100.0` — a 0/1 dummy gets a step of 0.01 instead of deriving integrality from the data |
| `:5729`, `:5764` | secondary-axis range computed from the **unfiltered** `self.df` |
| `:1068-1069`, `:1683`, `:1779` | `or 1.0` / `+1.0` degenerate-range sentinels |
| `:2171` | bar width `0.8 * min(gaps)` |
| `:1083` | secondary-axis padding fixed at 5% |
| `:1591` | `colormissing` defaults to the literal `"grey"` **and** is never passed through `translate_mcolor`, so `colormissing(eltblue)` emits invalid CSS |
| `:1893-1899` | `mlabgap` uses `int(float(v))`, so `mlabgap(small)` throws and is silently dropped; should go through `translate_msize()` |
| `:2560` | `map_lowess` does an **unguarded** `float(options.get("bwidth","0.8"))` — a non-numeric value crashes the whole render |
| `:2014`/`:2030` | `map_line` drops non-x/y columns, then `_apply_mlabel_opts` is called with the **unsorted** original source — mislabelled points on line plots |

### 5.5 Display formats never leave Stata — and `jsonio` cannot send them

`dash.ado` calls `jsonio out ..., what(all) metaprint(varnames varlabels vallabs labelnames)`
at `:961`, `:1377`, `:1559`.

The audit of the installed `jsonio` found that **`metaprint()` is a no-op here**:
`jsonio.ado:238` gates the metadata branch on
`inlist("`metaprint'`filenm'", "varlabels","varnames","vallabs","labelnames")` — it
concatenates `metaprint` *and* `filenm`. `dash` always passes a non-empty `filenm()` plus
four words, so the branch never fires; only `what(all)` has effect. `what(all)` maps to
`StataAllToJSON`, whose field set — confirmed in source and by `javap` on the shipped jar —
has **no format member**. `jsonio` does hold `Variables.getDisplayFmt()` internally, but
`StataAllToJSON` does not expose it and `StataMetaToJSON`'s switch has no `formats` case.

**Conclusion: there is no `jsonio` option that emits display formats.** A Stata-side side
channel is required — collect `local f : format <var>` in `dash.ado` and carry a `formats`
map in `dash`'s own master JSON. This is exactly the approach specified in the prior
conference plan's section 02.

Consequence today: every `%td`/`%tc` arrives as a raw Stata SIF integer and every `%9.0fc`
or `%9.2f` is lost — on axes, tooltips, dropdown options, slider endpoints, facet labels and
KPI values. There is **no date handling anywhere in the package**: `DatetimeTickFormatter`,
`DatetimeAxis` and `x_axis_type="datetime"` appear nowhere, and `map_tsline:3894` is a
pass-through to `map_line`.

### 5.6 Stata-side hardcoded JSON and validation

- `dash.ado:974` (immediate render): `{"layout":"1 1","theme":"default"}` — the immediate
  path can never use a non-default scheme.
- `dash.ado:1433` (`dash build`): the only user-driven assembly. Defaults `theme="default"`
  (`:1282`), `layout="auto"` (`:1221`), `filterposition="top"` (`:1234`). Never emits a
  `"scheme"` key.
- `dash.ado:1603` (`dash serve`): every option a literal — see §2.
- KPI stat list (`:1080`) omits `var`, `cv`, `iqr`, `skewness`; `_pctile` frozen at
  `p(25 50 75)` (`:1115`).
- `layout()` regexes (`:1225-1227`) require exactly one space, are case-inconsistent, allow
  `0` in the placement form, and are not end-anchored.
- `filterposition()` (`:1234-1238`) is case-sensitive and its error message names a
  non-existent option `filter_position()`.
- The path validator (`:150-178`) rejects `(` and `)` — breaking `C:\Program Files (x86)\...`
  — and any `..` substring; **server-mode `saving()` bypasses it entirely** (`:1198-1207`).
- `c(` appears 11 times in `dash.ado`, in two idioms only: `c(sysdir_plus)` and `c(os)`.
  **`c(scheme)` and `c(level)` are never consulted.**
- Six `shell` lines open a browser (`:1012-1014` immediate, `:1475-1477` build,
  unconditional). `dash build` has **no `nobrowser`** — only `dash serve` does (`:1488`).
  No `_rc` check after any `shell`, and the immediate path never displays the temp file path,
  so a failed `xdg-open` leaves the output unreachable.
- `dash.ado:143` is `python: runpy.run_path(...)`. A single-line `python:` echoes the
  expression value, and `run_path` returns the module globals dict, so **every `dash build`
  dumps ~10 KB of `dash_render.py`'s namespace into the Stata log** **[measured]**.
  Assigning the result suppresses it.

---

## 6. The scheme pipeline

`SchemeParser` requests **108 keys** (`dash_render.py:918-974`). Exactly **three** consumers
exist in 10,455 lines: `default_color()` (38 glyph call sites), `apply_to_figure()` (one call
site, `:5661`), and `css_block()` (`:6595`, `:7476` — and its selectors match nothing, §5.2).

**63 of the 108 parsed keys are discarded.** `default_symbol()` (`:996`) and
`default_line_pattern()` (`:1000`) have **zero call sites** — they exist only to be
unit-tested.

### The approximation gap, measured

`dash` can read **33 of the 2,048 distinct keys** in Stata's real `scheme-s2color.scheme`
(2,588 lines) — **1.6%**, of which it acts on about 1.1%.

**75 of `dash`'s own 108 keys do not exist in real Stata schemes at all.** `dash` invented
`color p1line`, `symbol p1`, `linepattern p1line`; Stata writes `markerstyle p1 p1` and
`linestyle p1 p1`. `graphsize`, `numstyle`, `margin`, `symbolsize`, `yesno`, `clockdir`,
`relsize` and `axisstyle` are unparsed. Of `gsize`'s 76 real keys, `dash` reads 5.

Stata resolves per-series styling through `p#stub → pstub → p# → p`. `dash` implements only
the `p#stub → p#` rung (as a `default=` argument). Bare-`p` entries that real schemes rely on
(`color p gs6`, `symbol p circle`) are ignored.

### Verified at runtime, not inferred

- Feeding a **real** `scheme-s2color.scheme`: colours survive, but `p_symbols` all resolve to
  `circle` and `p_line_patterns` to `[]`. Silent degradation, no error.
- Feeding **`scheme-stcolor.scheme`** — the Stata 18+ default, and the active scheme on this
  machine: **every series renders `#000000`.** `color p1 stc1` fails `translate_mcolor`,
  `_color()` (`:863`) swallows the failure and returns its `"#000000"` default (`:934`).
- `SchemeParser("stcolor")` raises; `:5004-5005` silently substitutes s2color.
- `c(scheme)` is never read, so `set scheme economist` in a user's profile is ignored.

### The series cycle differs by output mode

| Mode | Behaviour |
|---|---|
| Standalone HTML | cycles colour correctly — `for pi, plot in enumerate(plots)` (`:5915`) → `color_idx=pi`. **[measured]** p1 navy `#1a476f`, p2 maroon `#90353b` |
| Server | **hardcodes `color = '#1f77b4'`** (`:8678`, also `:9680`, `:9778`); `pi` is used only as an `agg_sources` dict key. Three scatters render **identically blue**. `grep "scheme"` over lines >7738 returns **zero hits** |

Even in standalone mode only *hue* varies across series — symbol, size, dash pattern and
line width are identical, because the scheme keys carrying them are parsed and dropped.

`dash.sthlp:161-162` claims `scheme()` is "fully supported". That is not defensible.

---

## 7. Documentation divergence

`dash.sthlp:25-26` states: *"The following `twoway` options are not yet supported by `dash`:
`play()`, `nodraw`. Specifying them will produce a warning and the option will be ignored."*

Neither string appears anywhere in `dash.ado`, `dash_parse.mata` or `dash_render.py`. Both
abort with r(198) **[measured]**. The documented exception list is both wrong in its
mechanism and wrong by roughly 35 options in its extent.

Further divergences confirmed in this round (the dedicated reconciliation pass is folded in
below in §7 of the plan's appendix):

| Help says | Reality |
|---|---|
| `scheme()` on `dash build` (`:79`, `:704-713`) | absent from `dash.ado:1174-1185` → `r(198)` |
| `scheme()` "fully supported" (`:161-162`) | dead in all three paths (§4.3) |
| `theme()` values `default, clean, dark` (`:248`) | `dark` is not in `_THEME_SCHEME_MAP`; silent `s2color` fallback |
| `degree()` 0-2 (`:566-568`) | code allows 0-3 |
| Brush/lasso KPI update "Standalone: Yes" (`:424`) | dead in **both** paths (§2) |
| `dash build, server` "does not block or open a browser" (`:82`, `:249-251`, `:492`) | blocks forever and opens a browser |
| `by()` cannot be combined with `link()` (`:653`) | stale — the guards were removed; it works |
| custom scheme by base name in the CWD (`:708-710`) | a bare name is only looked up in `SCHEMES_DIR`; the `.scheme` extension is required |
| `link(_all)` (`:295`) | silently produces an unlinked dashboard |
| `layout(name:row,col)` (`:271-275`) | never implemented |
| five `mlab*` abbreviations (`:537`, `:538`, `:540`, `:543`) and `xlab` (`:639`) | do not work; `:639` contradicts `:637` |
| `timeout()` units | previously corrected to minutes (commit `99b7a1b`) |

Undocumented but working, and worth documenting: `tabs()`, `filterposition()`, `layout(bs)`
and its `bs: spec` grammar, the multi-`filter()` mechanism and its `;` separator, the
`__all__` dropdown sentinel, and the whole `colorvar()` family
(`colorcuts()`/`colornlevels()`/`colormissing()`/`colpalette()`/`colordiscrete`).

Three items a first pass flagged as undocumented are in fact documented, and are recorded
here so the plan does not generate redundant help text: the secondary-axis family
(`dash.sthlp:704-707`), and `jitter()`/`jseed()`/`msangle()` (`dash.sthlp:683-695`) — though
those three sit under the heading *"Unsupported Stata twoway options"*, which is the wrong
section.

Two prior claims were **disproved** and must not be carried into the plan. `by()` combined
with `link()` is **not** forbidden by the code (`dash_render.py:6873-6878`, `:6991-6999`,
`_facet_masks` at `:7536-7620`); only `dash.sthlp:653` and a stale `Raises: ValueError`
docstring at `:6966-6968` say so. And `timeout()`'s units were already corrected to minutes
in commit `99b7a1b`. Separately, `dash.sthlp:422` *understates* the standalone histogram —
the JS does recompute bin counts (`:4566-4630`).

---

## 8. Test-suite integrity

1,494 pytest tests + 11 cscripts. **The suite is currently RED: 14 failed / 1,480 passed**
**[measured]** — all 14 from the unguarded `statsmodels` import at `:2547`. Project rule 5
forbids committing in this state.

### Structural problems

- **The cscript runner cannot fail honestly.** All 15 dependency guards `exit 0`, which the
  runner scores as PASS; `n_skip` (`run_all_cscripts.do:36`) is never incremented, so `:216`
  always prints "0 skipped". **A bare machine prints ALL TESTS PASSED having asserted
  nothing.**
- Only 4 of 11 cscripts reach Python end to end. `test_parser.cscript` is parse-only — its
  single `dash` call passes `name()`, which routes to `_dash_register_graph` and never
  renders.
- **The two richest scripts — `test_adversarial.cscript` and `test_e2e_serve.cscript` — are
  orphans**, not in the runner.

### Coverage

Glyph mappers 38/38 have direct tests; translators 7/7; `ServerAppBuilder` 4/4. But
**`SchemeParser`: 8 of 15 functions untested** — the entire coercion layer (`_color`,
`_gsize`, `_intensity`, `_symbol`, `_lpattern`, `_lwidth`, `_parse_file`,
`_init_properties`), which is exactly where the silent-black `stcolor` failure lives.
28 functions have zero references, including `FilterBuilder._safe` (`:4645`, the XSS
chokepoint) and `_validate_expr_node` (`:4161`). `DashRenderer._make_source` looks covered,
but all 20 hits are same-named test helpers.

### Landmines — tests that assert the wrong thing

| Test | Problem |
|---|---|
| `test_scheme.py:404-415` | feeds a real Stata scheme and asserts only `p_colors[0]` — the one thing that works — concealing the 98.4% gap |
| `test_scheme.py:194-203` | green-lights dead API |
| `test_linking.py:207-214` | **no assertion at all** |
| `test_kpi.py:276`, `:287` | tautologies |
| `test_server.py:6990` (+4) | skips on the exact regression it guards |
| `test_server.py:2225`, `:2238`, `:2250` | accept two opposite security outcomes |

### Zero regression coverage

Date/time axes · figure sizing · scheme consumption · the series colour cycle ·
server-vs-standalone parity · `tabs()` (the string `tabs` appears nowhere in `test/`).

The absence of server-vs-standalone parity tests is why the empty-document bug (§2) survived
448 server tests.

---

## 9. The load-bearing claim, and the defects that break it

### 9.1 The sentence the whole package rests on

`dash.sthlp:668-673`:

> *"No error is produced for unknown options, so existing Stata graph commands copy-pasted
> into `dash` will still run."*

This is false, and it is false by construction. `_dash_parse_graph_opts` (`dash.ado:230-246`)
and `_dash_parse_plot_opts` (`dash.ado:293-326`) are **closed allow-lists** invoked with no
`capture` and no catch-all (`dash.ado:666-669`). Any option not on the list aborts the
do-file. **46 full-name options were confirmed rejected by execution**, plus 9 abbreviations
confirmed and structurally unbounded more.

### 9.2 Additional blockers confirmed by execution (StataNow 19.5, ~150 probe commands)

| # | Defect | Citation | Observed |
|---|---|---|---|
| 1 | `dash function y=x^2` — the canonical documented form | `dash.ado:455` lacks `equalok`, so the `y=` stripper at `:630` is unreachable | **r(101)** `=exp not allowed` |
| 2 | Variable-free plots standalone: `dash scatteri 20 3000 30 4000, saving(x.html)`, `dash pci ...`, `dash function x^2` | `dash.ado:937-940` | **r(198)** "no variables identified" |
| 3 | `dash tsline mpg` with no `tsset` — `dash` never reads `_dta[_TStvar]` | `xvar:""` → `KeyError: ''` | **r(7102)** `failed to build figure ''` |
| 4 | `name(g1, replace)` is impossible — the raw name is validated at `:857` *before* the replace parse at `:864-870`; the error at `:880-883` instructs the user to type the syntax that cannot work | `dash.ado:857-883` | **r(198)**, self-contradicting |
| 5 | `saving(myfig)` (the normal `twoway` form), `saving(myfig.gph)`, `saving(f.html, replace)` | validated at `:921` before the `.html` append at `:929`; `:158-161` | **r(198)** ×3 |
| 6 | `dash.sthlp:54` documents `name(id, replace)`; `:61`/`:66` document KPI `nam()`/`upd()` | `dash.ado:1065` lowercase, `:1070` all-caps | **r(198)** ×3 |
| 7 | ~12 plot-type abbreviations Stata accepts and `dash` rejects | `dash_parse.mata:126-167` | `scat` `conn` `lin` `kdens` ... |
| 8 | Plot types not accepted at all | — | `contour` `contourline` `pccapsym` `rbarm`, and the literal `twoway` prefix word |

### 9.3 Additional silent defects

- **Per-plot `if` is broken in both directions.** Only the *first* layer's `if_expr` is
  promoted to graph level (`dash.ado:828-835`) and then applied to every layer, and the
  renderer never reads a per-plot `if_expr` at all (`dash_render.py:5281`). So
  `(scatter y x) (scatter y x if foreign)` drops the qualifier entirely.
- **`name()` inverts `twoway` semantics.** In `twoway` it names a graph in memory *and draws
  it*; in `dash` it suppresses all output and registers for `dash build`
  (`dash.ado:838-845`). Copying `twoway scatter y x, name(fig1)` produces no graph.
- **Title and note sub-options leak into the rendered text.**
  `title("My Title", size(large) color(red))` renders the literal string
  `My Title , size(large) color(red)`; `note("n=74", span)` renders `"n=74", span` — quotes
  retained, because `note` is `string asis` while `title` is `string`.
- **`scatteri` label text is mis-paired.** `scatteri 20 3000 "A" 30 4000 "B"` serializes as
  `"values":[[20,3000],["A",30],[4000,"B"]]` (`dash.ado:710-727` pairs blindly, checking only
  token-count parity at `:714-717`) — malformed output.
- **`dash kpi ... if ...` shows the wrong number.** Measured: the card displays **21.2973**
  where Stata's own `summarize` under the same qualifier reports **24.7727**
  (`dash.ado:1421` omits `if_expr`; `dash_render.py:7121-7131` recomputes unconditionally).
- **`dcount` is always missing** — `codebook` returns nothing in `r()` (`dash.ado:1110-1113`).
- **`dash clear` drops `_dash_*`, not `dash_*`** — orphan globals survive into the next build.
- **`dash_setup` never actually compares the Python version**, despite
  `dash_setup.sthlp:34`.
- **Hollow markers render filled** (`Oh`, `Sh`, `Dh`), and `msymbol(i)` / `msymbol(none)`
  silently draws visible markers.
- **Every glyph passes `legend_label=yvar`**, so single-series plots get a legend `twoway`
  would not draw.
- **`ciopts()`, `level()`, `fitopts()`, `lineopts()`, `bands()`, `at()` all r(198)** — every
  CI and smoother layer is style-locked.

### 9.4 Reconciliation counts

Documented-but-not-accepted: **17**. Documented-but-not-implemented: **14**.
Implemented-but-undocumented: **16**. Documented-with-wrong-values: **19**.
Silent-failure sites: **180+**, of which exactly **10** emit a warning.

---

## 10. Decisions taken (these bind the plan)

1. **Schemes — translate the most widely used StataCorp schemes and restrict `scheme()` to
   the translated set.** `dash` keeps its own `schemes/` directory rather than parsing
   Stata's 2,588-line scheme grammar. The translated set is widened to cover the schemes
   users actually have set, the translations are deepened so they *faithfully reproduce the
   aesthetics* (which requires consuming the 63 parsed-but-ignored keys and adding the
   properties `SchemeParser` does not model), and a scheme outside the translated set is
   rejected with a clear message naming the supported list rather than silently falling back
   to black or to `s2color`.
2. **Statistical and visual defaults change to match Stata.** Matching `twoway` is the
   definition of correct. Every altered default is documented with a changelog entry and a
   migration note.
3. **Server mode: fix the root bug, then unify.** First make `bokeh serve` actually serve a
   document and wire `dash serve`'s discarded options through; then collapse the 107
   duplicated implementations onto one shared code path so the two modes cannot drift again.
4. **Unsupported options are accepted, never abort, and are reported together.** A single
   note per command lists every unsupported option that command used — not one message per
   option, and never silence.
