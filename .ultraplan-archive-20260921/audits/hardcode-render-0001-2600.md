# Hardcoded-value audit — `dash_render.py` lines 1–2600

Scope: module constants, `OptionTranslator`, `SchemeParser`, `_apply_jitter`,
`_compute_secondary_range`, `GlyphMapper` helpers (`_build_jitter_source`,
`_hover_tool`, `_check_vars`, `_render_ci_band`, `_bootstrap_ci`,
`_apply_line_opts`, `_apply_marker_opts`, `_apply_fill_opts`, `_apply_colorvar`,
`_apply_mlabel_opts`), and mappers `map_scatter`, `map_line`, `map_connected`,
`map_area`, `map_bar`, `map_spike`, `map_lfit`, `map_qfit`, `map_lfitci`,
`map_qfitci`, `map_lowess`, `_compute_lpoly_fit`.

Cross-checked against `dash.ado:230-247` (graph-level `syntax`) and
`dash.ado:293-326` (plot-level `syntax`), plus `dash.ado:476-482` (the loop that
copies parsed plot options into the JSON) and `dash_parse.mata:179-253`
(abbreviation expansion).

---

## 0. Structural findings that drive many of the individual rows

These three facts explain most of the HIGH severity entries below.

**(A) `SchemeParser.apply_to_figure()` (`dash_render.py:1004-1021`) and
`SchemeParser.css_block()` (`dash_render.py:1023-1037`) are never called.**
Verified by grep over the whole 10,455-line file: the only occurrences of both
names are their `def` lines. Consequence: every scheme property the parser
extracts other than the p-color cycle is dead. `background_color`,
`plotregion_color`, `grid_color`, `minor_grid_color`, `axis_line_color`,
`title_color`, `legend_bg_color`, `legend_border_color`, `axis_title_font_size`,
`tick_label_font_size`, `text_font_size`, `heading_font_size`, `note_font_size`,
`grid_line_width` never reach a figure. `scheme()` is a real, reachable
graph-level option (`dash.ado:239`, `dash.ado:319`), so the user *can* set it and
it silently only changes glyph colors.

**(B) Four scheme properties are parsed and then referenced by nothing at all.**
Grep for `scheme.fill_alpha|scheme.bar_alpha|scheme.area_alpha|
scheme.default_line_width|scheme.default_line_pattern|scheme.default_symbol`
returns zero hits. Defined at `dash_render.py:951-967` and
`dash_render.py:996-1002`. Every alpha, line width, line dash and marker symbol
default in the mappers is therefore a literal instead of a scheme lookup.

**(C) Six plot-level options are accepted by `dash.ado`, written into the spec
JSON, and never read by `dash_render.py`.** Grep for `"falpha"`, `"mlcolor"`,
`"pstyle"`, `"cmissing"`, `"recast"`, `"connect"` in `dash_render.py` returns
zero hits. They are declared at `dash.ado:295,301,310,311`, `sreturn`ed at
`dash.ado:333,348,366-369`, and serialized at `dash.ado:476-482`. The user types
a valid Stata option, gets no error, and the hardcoded literal wins.

**(D) `level()` does not exist anywhere in `dash.ado`.** Grep confirms no
`level(` in the `syntax` blocks nor in `dash.sthlp`. Every CI in this range is
permanently 95%. This is the canonical **UNREACHABLE DEFAULT**.

**(E) No `xsize()`, `ysize()` or `scale()` option exists.** Grep over `dash.ado`
finds only `xscale`/`yscale`. So every pixel-valued size map (`_SIZE_MAP`,
`_LWIDTH_MAP`, `_GSIZE_PT`, `_LPATTERN_MAP`) is fixed in absolute px and cannot
track graph size the way Stata's relative sizing does.

---

## 1. HIGH severity

| # | file:line | Hardcoded literal | What it currently does | Should derive from | twoway option? | Sev |
|---|---|---|---|---|---|---|
| H1 | `dash_render.py:2441` | `0.975` (and `df=n-2`) | t critical value for the `lfitci` CI band — pins the band at exactly 95% | `level()`, falling back to Stata's `c(level)` | **yes — `level(#)` on `lfitci`/`qfitci`/`lpolyci`/`fpfitci`** — **UNREACHABLE DEFAULT** (`level` absent from `dash.ado:293-326`) | HIGH |
| H2 | `dash_render.py:1343-1344` | `2.5`, `97.5` | bootstrap percentiles in `_bootstrap_ci` — pins every bootstrap CI at 95% | `level()` → `(100-level)/2`, `100-(100-level)/2` | **yes — `level(#)`** — **UNREACHABLE DEFAULT** | HIGH |
| H3 | `dash_render.py:1971` | `size=8` | default scatter marker size | scheme marker size (`symbolsize p#`) or the translator's own `medium`. `OptionTranslator._SIZE_MAP["medium"] == 11` (`dash_render.py:437`), and `dash_render.py:3586` already uses `options.get("msize","medium")` → 11. So `map_scatter` disagrees with the rest of the file by 3px | yes — `msize()` overrides it (`dash.ado:294`), but the *default* ignores both scheme and the module's own "medium" | HIGH |
| H4 | `dash_render.py:1974` | `alpha=0.7` | default scatter fill+line opacity | `scheme.fill_alpha` (parsed at `dash_render.py:965` from `intensity p`, = 0.8 for s2color) — never read (finding B) | Stata has no marker-alpha default other than the scheme's `intensity p`; `malpha()`/`mcolor(c%n)` override, but the default should be the scheme's | HIGH |
| H5 | `dash_render.py:2199` | `fill_alpha=0.8` | bar fill opacity | `scheme.bar_alpha` (`dash_render.py:966`, from `intensity bar`) — never read | scheme-driven; `fintensity()` overrides via `_apply_fill_opts` | HIGH |
| H6 | `dash_render.py:2106` | `fill_alpha=0.5` | area fill opacity | `scheme.area_alpha` (`dash_render.py:967`, from `intensity area`, = 0.8) — never read. The literal 0.5 contradicts the scheme by 0.3 | scheme-driven; `fintensity()` overrides | HIGH |
| H7 | `dash_render.py:1591` | `or "grey"` | fallback color for NaN in `colorvar` mappings; also the value is passed straight to Bokeh at `:1735` / `:1783` **without** `OptionTranslator.translate_mcolor()`, so `colormissing(eltblue)` (a legal Stata color) emits an invalid CSS color | scheme `color background`/`gs*`; and the user value must go through `translate_mcolor` | yes — `colormissing()` (`dash.ado:308`) is reachable but its value is not translated | HIGH |
| H8 | `dash_render.py:1727-1730` | `"category10"` → `Category10_10` | default palette for **discrete** `colorvar` mappings | `scheme.p_colors` (`dash_render.py:934-936`) — the active scheme's p1–p15 cycle, which is what Stata 18 uses for a discrete colorvar | yes — `colpalette()` overrides, but the *default* ignores `scheme()` entirely | HIGH |
| H9 | `dash_render.py:1780-1781` | `"viridis"` → `Viridis256` | default palette for **continuous** `colorvar` | the scheme's `colorvar` palette; Stata 18's default is scheme-dependent | yes — `colpalette()` overrides; default ignores `scheme()` | HIGH |
| H10 | `dash_render.py:1769` and `1797` | `"right"` | placement slot for the colorvar `Legend` / `ColorBar` — always docked right | `legend(position(#) ring(#))` sub-options; `legend()` **is** a reachable graph-level option (`dash.ado:236`, `dash.ado:317`) | yes — `legend(position())` / `legend(ring())` exist in twoway and are ignored here | HIGH |
| H11 | `dash_render.py:1860` | `text_font_size="10px"` | default marker-label font size | `scheme.text_font_size` (`dash_render.py:970`, `gsize text` → "10pt") — never read; also 10**px** ≠ 10**pt** | yes — `mlabsize()` overrides (`dash.ado:296`), but the default ignores the scheme | HIGH |
| H12 | `dash_render.py:1893-1899` | `int(float(options["mlabgap"]))` | `mlabgap()` is parsed as a **number of pixels only**. Stata's `mlabgap()` takes a *size keyword* (`tiny`, `vsmall`, `small`, …). `int(float("small"))` raises `ValueError` and the whole gap is silently dropped, leaving the hardcoded `4`/`4` offsets | `OptionTranslator.translate_msize()` (which already handles keyword→px), scaled by the label font size | yes — `mlabgap()` (`dash.ado:297`) reaches the renderer; keyword forms are silently discarded | HIGH |
| H13 | `dash_render.py:1441-1449` (in `_apply_marker_opts`) | uses `options["lcolor"]` for the **marker border** | Stata's marker-outline option is `mlcolor()`, not `lcolor()`. `mlcolor` is parsed (`dash.ado:295,333`), serialized (`dash.ado:476-482`) and **never read** anywhere in `dash_render.py`. Meanwhile `lcolor()` — which on `connected`/`line` should color the *connecting line* — is hijacked to repaint marker borders | `options["mlcolor"]` for the border; `lcolor` should stay on the line glyph | yes — `mlcolor()` is a documented twoway marker option and dash ignores it entirely | HIGH |
| H14 | `dash_render.py:1488-1521` (`_apply_fill_opts`) | only `fcolor` + `fintensity` are read | `falpha()` is parsed (`dash.ado:301,348`), serialized, and never read (finding C). Every fill opacity therefore falls back to the hardcoded `0.5`/`0.8`/`0.2` literals | `options["falpha"]` → `fill_alpha = falpha/100` | yes — `falpha()` is a documented twoway fill option and dash ignores it | HIGH |
| H15 | `dash_render.py:1004-1021`, `1023-1037` | the entire `apply_to_figure` / `css_block` bodies | dead code (finding A). Figures get Bokeh's stock white background, stock grid color, stock 13px axis fonts — *not* the scheme's `color background`, `color plotregion`, `color major_grid`, `gsize axis_title`, `gsize tick_label` | the already-parsed `SchemeParser` attributes | yes — `scheme()` (`dash.ado:239`, `dash.ado:319`) is reachable and effectively half-honored | HIGH |
| H16 | `dash_render.py:2109-2113` (`map_area`), `2204-2210` (`map_bar`) | `if "color" in options:` | dead branch: `color()` is **not** in the plot-level `syntax` (`dash.ado:293-326`) and is not an abbreviation target (`dash_parse.mata:179-253`). `twoway area y x, color(navy)` is a legal Stata command that dash rejects with a Stata syntax error; the fallback is the hardcoded `scheme.default_color(...)` | add `color(string)` to `dash.ado:293-326`, map to fill+line | **yes — `color()`** — **UNREACHABLE DEFAULT** (the branch exists but no path reaches it) | HIGH |
| H17 | `dash_render.py:2176` | `for key in ("barwidth", "width")` | `"width"` half of the loop is dead: `width()` is not in `dash.ado:293-326`. Only `barwidth()` reaches it, so the auto `0.8 * min(gaps)` stands for anyone who writes `twoway bar ..., width(.5)` | add `width(string)` to the plot syntax | **yes — twoway `bar` accepts neither, but `twoway histogram`/`rbar` use `barwidth()`; `width()` here is dead** — **UNREACHABLE DEFAULT** | HIGH |
| H18 | `dash_render.py:2330` | `line_dash="solid"` | `map_lfit` pins the fit line to solid | `scheme.default_line_pattern(color_idx)` (`dash_render.py:1000-1002`, from `linepattern p#line`) — defined and never called | yes — `lpattern()` overrides via `_apply_line_opts`, but the default ignores the scheme's pattern cycle | HIGH |
| H19 | `dash_render.py:2023`, `2125`, `2272`, `2330`, `2377`, `2424`, `2497`, `2569`, `1291` | `line_width=1.5` / `line_width=2.0` | default line widths, split arbitrarily: data lines get 1.5, fit lines get 2.0, CI center lines get 2.0 | `scheme.default_line_width` (`dash_render.py:961`, from `linewidth p` → `medium` → 1.5) — never read | yes — `lwidth()` overrides; the default should be the scheme's single value, not two different literals | HIGH |
| H20 | `dash_render.py:386-387` | `"none": "#ffffff"`, `"": "#000000"` | Stata's `none` means *fully transparent*. Mapping it to opaque white paints a white blob over any non-white plot region (and the scheme's own `color background` for s2color is `#d9e8f0`) | `None` / `fill_alpha=0` / Bokeh's `None` color | yes — `fcolor(none)`, `lcolor(none)`, `mfcolor(none)` are common twoway idioms and are rendered wrongly | HIGH |

---

## 2. MEDIUM severity

| # | file:line | Hardcoded literal | What it currently does | Should derive from | twoway option? | Sev |
|---|---|---|---|---|---|---|
| M1 | `dash_render.py:2324`, `2371`, `2432`, `2505` | `0.1 *` range extension, and `200` grid points | fit lines are evaluated on a fixed 200-point grid spanning ±10% of the data range. The 10% hardcodes an assumption about Bokeh's `DataRange1d.range_padding` default; if the user sets `xscale(range(...))` the fit no longer spans the axis. 200 points is overkill for a straight line and possibly coarse for a sharply curved `qfit` | actual figure x-range (`fig.x_range.start/end`) once resolved; grid density from the rendered plot width in px | partly — `xscale(range())` is reachable (`dash.ado:238/318`) and is not consulted | MEDIUM |
| M2 | `dash_render.py:1303`, `2513` | `n_boot: int = 200` vs. `n_boot=500` | bootstrap resample count. The two disagree, and `map_qfitci`'s docstring (`dash_render.py:2468`) says "500 resamples" while `_bootstrap_ci`'s says 200 (`dash_render.py:1319`). Neither tracks N | should scale with sample size / be a documented option (`reps()`) | no twoway analogue | MEDIUM |
| M3 | `dash_render.py:1304` | `seed: int = 42` | fixed bootstrap RNG seed; every `qfitci`/`lpolyci` CI is byte-identical across runs but cannot be varied | `jseed()` is already a reachable option (`dash.ado:304`) and is used for jitter only — it should also seed the bootstrap, or a `bseed()` should exist | no direct twoway analogue, but `jseed()` exists and is ignored here | MEDIUM |
| M4 | `dash_render.py:2582` | `bwidth: float = 0.5` | `_compute_lpoly_fit` default bandwidth. Stata's `lpoly` computes a **rule-of-thumb plug-in bandwidth from the data** (`ROT`), it is not a constant | data-derived ROT estimator: `h = 0.9 * min(sd, IQR/1.34) * n^(-1/5)` scaled to the kernel | yes — `bwidth()` is reachable (`dash.ado:309`), but the *default* should be data-derived, not 0.5 | MEDIUM |
| M5 | `dash_render.py:2560` | `float(options.get("bwidth", "0.8"))` | lowess default bandwidth 0.8 matches Stata's `lowess` default — correct — but the conversion is **unguarded**: a non-numeric `bwidth(foo)` raises `ValueError` and crashes the render instead of falling back (contrast with the `try/except` everywhere else) | wrap in `try/except`, default 0.8 | yes — `bwidth()` reachable; the crash is a robustness bug | MEDIUM |
| M6 | `dash_render.py:2584`, `2606` | `n_grid: int = 200` | fixed evaluation grid for the local-polynomial smoother | plot width in px, or `len(x)` capped | no | MEDIUM |
| M7 | `dash_render.py:2613` | `1e-12` | kernel weight-sum floor below which the fit point becomes NaN | should be relative to the data scale (`np.finfo(float).eps * w.size * scale`), not an absolute constant — for y values of order 1e-9 this silently blanks the curve | no | MEDIUM |
| M8 | `dash_render.py:1083`, `1111` | `padding_pct: float = 0.05` | 5% padding added to the computed secondary-axis range | `yscale2(range())` / `ylabel2()` (both reachable: `dash.ado:244-245`, `dash.ado:324-325`) | yes — `yscale2(range())` is reachable and not consulted | MEDIUM |
| M9 | `dash_render.py:1108` | `return 0.0, 1.0` | fallback secondary-axis range when no layer has data | should let Bokeh auto-range rather than pin to [0,1] | no | MEDIUM |
| M10 | `dash_render.py:1068-1069` | `or 1.0` | zero-variance fallback for the jitter denominator: a constant-x column gets ±(pct/2)·1.0 of absolute noise regardless of the variable's magnitude | the other axis's range, or the variable's own magnitude | no | MEDIUM |
| M11 | `dash_render.py:1070-1071` | `/ 2.0` | jitter half-width = pct·range/2. Stata's `jitter(#)` is defined relative to the **plot region size**, not the data range, and adds *spherical* noise | plot-region px size, converted to data units | yes — `jitter()` is reachable (`dash.ado:304`); the interpretation of the number is a hardcoded approximation | MEDIUM |
| M12 | `dash_render.py:1683`, `1779` | `hi_v = lo_v + 1.0`, `hi = lo + 1.0` | degenerate (constant) colorvar column sentinel — a `+1.0` bump in raw data units | should be `lo * eps` or a relative bump, otherwise a column of constant 1e6 gets a mapper span of 1 part in a million | no | MEDIUM |
| M13 | `dash_render.py:1731-1733` | `while len(pal_list) < len(non_missing_factors): pal_list += pal_list` | when a discrete colorvar has more categories than the palette has colors, colors are **repeated verbatim** — two categories get the identical hex, making the legend ambiguous | generate an interpolated N-color palette (`bokeh.palettes.linear_palette` / `viridis(n)`), or cycle the scheme's 15 p-colors with varied intensity | no direct analogue, but Stata cycles scheme p-styles | MEDIUM |
| M14 | `dash_render.py:1794-1795` | `label_standoff=8`, `width=12`, `location=(0, 0)` | ColorBar geometry, fixed px | scheme `gsize` / figure size | no | MEDIUM |
| M15 | `dash_render.py:1861-1862`, `1883-1887`, `1896-1897` | `x_offset=4`, `y_offset=4`, and the `offset_map` px table `{1:(3,3), 3:(4,0), 6:(0,-4), …}` | marker-label clock-position offsets in absolute px; they do not scale with `msize()` or `mlabsize()`, so a `msize(huge)` marker overlaps its own label | offset should be `≈ msize/2 + mlabgap`, derived from the resolved marker size | yes — `mlabposition()` selects the entry but the magnitudes ignore `msize()` | MEDIUM |
| M16 | `dash_render.py:1871-1875` | `translate_msize()` result reused as a **font px** size | `mlabsize(medium)` → 11 (a *marker diameter* from `_SIZE_MAP`) → `"11px"` font. Marker-size and text-size are different Stata domains; `_GSIZE_PT` (`dash_render.py:709-724`) is the correct table and maps `medium` → `"11pt"` | `SchemeParser._GSIZE_PT` | yes — `mlabsize()` reachable; the translation table is the wrong one | MEDIUM |
| M17 | `dash_render.py:2122` | `or "#aec7e8"` | fallback area border color when `fill_color` is falsy | `scheme.default_color(color_idx, "area")` — the value is already in scope at `dash_render.py:2105` | no (it's a fallback), but it ignores the scheme | MEDIUM |
| M18 | `dash_render.py:2171`, `2173`, `2158`, `2168` | `0.8` (×3) | bar width = 80% of the minimum x gap; `0.8` again as the single-bar and string-x and empty-source fallback | Stata's `twoway bar` default barwidth is likewise derived from the x spacing, so the *method* is right; the 0.8 factor and the fallback should come from the scheme (`barwidth` style) | yes — `barwidth()` overrides (`dash.ado:302`); the factor itself is fixed | MEDIUM |
| M19 | `dash_render.py:2271` | `default_color(color_idx, "scatter")` for spikes | `map_spike` colors spikes with the **marker** color cycle (`p#`) although a spike is a line glyph and Stata styles it from `p#line` | `default_color(color_idx, "line")` | yes indirectly — `scheme()` reachable; wrong cycle selected | MEDIUM |
| M20 | `dash_render.py:1287`, `2421`, `2494` | `fill_alpha=0.2` | CI band opacity. `_render_ci_band` at least calls `_apply_fill_opts` afterwards (`dash_render.py:1294`) so `fintensity()` can override — but the two **empty-data** fallback paths (`2419-2426`, `2492-2499`) never call it, so those are unconditional | `scheme.area_alpha`, or Stata's `ciplot()`/`fintensity()` | yes — `fintensity()` reaches the non-empty path only | MEDIUM |
| M21 | `dash_render.py:310-388` (`_COLOR_MAP`) | the whole 78-entry hex table | Stata's named colors live in `style/color-*.style` files and are scheme-overridable; several entries here are visibly approximations rather than Stata's values (e.g. `teal` `#1b8a7a` vs Stata's `0 128 128`; `forest_green` `#538d22` vs Stata's `85 107 47`; `gs10`–`gs16` all collapse toward `#ffffff` with `gs14`/`gs15`/`gs16` identical) | Stata's `.style` color definitions, or at minimum let the active scheme override a named color | partly — `scheme()` is reachable and cannot redefine a named color here | MEDIUM |
| M22 | `dash_render.py:432-442` (`_SIZE_MAP`), `447-457` (`_LWIDTH_MAP`), `709-724` (`_GSIZE_PT`) | absolute px / pt values for every Stata size keyword | Stata sizes are **relative** to graph size and `scale()`. With no `xsize()`/`ysize()`/`scale()` option anywhere in `dash.ado` (finding E), a `medium` marker is 11px whether the figure is 300px or 1200px wide | figure width/height; `scale()` multiplier | **no — `xsize()`/`ysize()`/`scale()` absent from `dash.ado`** — **UNREACHABLE DEFAULT** | MEDIUM |
| M23 | `dash_render.py:463-479` (`_LPATTERN_MAP`) | `[8,4]`, `[2,4]`, `[16,4]`, `[0,100]` … | dash on/off lengths in absolute px. In Stata a pattern's dash length scales with the line width, so a `vvthick dash` line looks like a `vvthin dash` line here | multiply by the resolved `line_width` | no | MEDIUM |
| M24 | `dash_render.py:182-195` (`_DASH_GRID_CSS`) | `#dee2e6`, `#6c757d`, `1.5rem`, `.9rem`, `.8rem`, `.05em`, `16px`/`12px`/`8px`/`4px` gutters | dashboard chrome (title, subtitle, filter bar, sidebar) is styled with Bootstrap's stock grays and sizes, ignoring the scheme entirely. `css_block()` (`dash_render.py:1023-1037`) exists to fix exactly this and is never called (finding A) | `scheme.title_color`, `scheme.text_font_size`, `scheme.heading_font_size`, `scheme.background_color`, `scheme.legend_bg_color` | yes — `scheme()` reachable and ignored for chrome | MEDIUM |
| M25 | `dash_render.py:1213-1216` (`_hover_tool`) | tooltip label = raw variable name, value spec = `@{var}` with no format | hover shows `mpg` / `21.0000000001` rather than the Stata **variable label** and the variable's **display format**. `self.variable_labels` is populated (`dash_render.py:1148`) and already used by `_apply_colorvar` (`dash_render.py:1596`) — just not here | `self.variable_labels[var]` for the label; the Stata `%fmt` for the value (`@{var}{custom}`) | no twoway analogue (hover is dash-specific), but the data carries both | MEDIUM |
| M26 | `dash_render.py:1766` | `"(missing)"` | English literal for the missing swatch in a discrete colorvar legend; `"__missing__"` (`1672`, `1691`, `1706`, `1712`) is a magic sentinel that would collide with a real string category literally named `__missing__` | Stata's `.` representation / the value label; use a non-collidable sentinel (`None` key) | no | MEDIUM |
| M27 | `dash_render.py:1901-1905` | `options.get("mlabwidth")` — consumed, no-op | `mlabwidth()` is accepted (`dash.ado:297`) and documented as silently ignored. Stata wraps labels at that width | text wrapping via manual `\n` insertion at N chars | yes — reachable option, deliberately unimplemented; should be documented in `dash.sthlp` rather than silently dropped | MEDIUM |
| M28 | `dash.ado:310-311` → `dash_render.py` (nowhere) | `pstyle()`, `cmissing()`, `recast()`, `connect()` | all four are parsed, `sreturn`ed and serialized into the spec JSON (`dash.ado:476-482`) and then **read by nothing**. `cmissing(n)` in particular changes whether a line breaks at missing values — `map_line` (`dash_render.py:2013-2016`) unconditionally `dropna()`s, which is the `cmissing(n)` behavior, so `cmissing(y)` (Stata's default!) is silently unavailable | `options["cmissing"]` should choose between `dropna()` and leaving NaN in place | yes — all four are documented twoway options that dash ignores | MEDIUM |
| M29 | `dash_render.py:2014` | `pd.DataFrame({xvar: ..., yvar: ...})` | `map_line` builds its sorted source from **only** the x and y columns, discarding every other column. `_apply_mlabel_opts` is then called with the *original* unsorted `source` (`dash_render.py:2030`), so `mlabel` positions on a `line` plot come from a different row ordering than the line itself | preserve all columns as `map_scatter` does (`dash_render.py:1954`) | yes — `mlabel()` reachable and mis-positioned | MEDIUM |

---

## 3. LOW severity — deliberately-fixed internals (record, do not change)

| # | file:line | Literal | Note |
|---|---|---|---|
| L1 | `dash_render.py:106` | `_WEBGL_THRESHOLD = 10_000` | perf switch to WebGL. No twoway analogue. Fine as a constant; could be an env override. |
| L2 | `dash_render.py:109` | `_NONSELECTION_ALPHA = 0.15` | dimming for linked brushing. Dash-specific interaction, no twoway analogue. Arguably should be `scheme.fill_alpha * 0.2`, but LOW. |
| L3 | `dash_render.py:115-118` | `_CSP_META` `'unsafe-inline' 'unsafe-eval'` | required by Bokeh's `new Function()` CustomJS compilation; correctly commented. Security-relevant but not a "hardcoded user value". |
| L4 | `dash_render.py:122-196` | the 12-column grid percentages (`8.3333%` … `100%`) and `576/768/992px` breakpoints | standard Bootstrap grid math; correctly fixed. (The *colors* in the same block are M24.) |
| L5 | `dash_render.py:238` | `_math.pi / 2` for `angle(vertical)` | exact by definition. |
| L6 | `dash_render.py:570` | `len(v) in (4, 7)` | CSS hex length check (`#rgb` / `#rrggbb`). Correct; note 8-char `#rrggbbaa` is rejected. |
| L7 | `dash_render.py:623`, `653` | `max(1, ...)`, `max(0.1, ...)` | positive-value floors on user-supplied numeric sizes/widths. Sensible guards. |
| L8 | `dash_render.py:704-706` | `_BUILTIN_NAMES = {s2color, s1color, s1mono, economist, sj}` | matches the five files actually in `schemes/`. Verified. |
| L9 | `dash_render.py:727-732` | `_INTENSITY` `inten0`–`inten100` | exact 1:1 transcription of Stata's intensity keywords. |
| L10 | `dash_render.py:880` | `max(6, int(val * 1.2))` | Stata-points → CSS-pt fudge factor with a 6pt floor. A hardcoded 1.2 conversion; borderline MEDIUM but only fires for numeric `gsize` values in a custom scheme. |
| L11 | `dash_render.py:934-958` | `range(1, 16)` / `% 15` | Stata defines exactly 15 p-styles. Correct. |
| L12 | `dash_render.py:1190` | `jitter_pct = min(100.0, jitter_pct)` | upper clamp only; the comment says "Clamp to [1, 100]" but there is no lower clamp (the `<= 0` early-return at `1186` covers it). Comment/code mismatch, cosmetic. |
| L13 | `dash_render.py:1238` | `stacklevel=3` | warning frame depth. Internal. |
| L14 | `dash_render.py:1575` | `re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", varname)` | Stata identifier allowlist before the name reaches a CDS field — correct hardening, keep. |
| L15 | `dash_render.py:1623` | `nlevels = max(2, nlevels)` | minimum 2 bins. Sensible. |
| L16 | `dash_render.py:1654` | `f"_cvar_{varname}_bin"` | internal derived-column name prefix. Could collide with a real variable named `_cvar_x_bin`; negligible. |
| L17 | `dash_render.py:1756`, `1763` | `size=0`, `visible=False`, `x=[nan]` | invisible proxy renderers that carry legend swatch colors. Internal Bokeh idiom. |
| L18 | `dash_render.py:1879` | `pos = options.get("mlabposition", "3")` | 3 o'clock is Stata's documented default marker-label position. Correct. |
| L19 | `dash_render.py:2093`, `2185`, `2257` | `base_val = 0.0` | Stata's `base()` default for `area`/`bar`/`spike` is 0. Correct, and `base()` is reachable (`dash.ado:302`). |
| L20 | `dash_render.py:2316`, `2363`, `2418`, `2488`, `2555` | `len(x) < 2` / `< 3`, `np.std(x) == 0.0` | minimum-N guards dictated by the math (df = n−2, degree-2 polyfit). Correct. `np.std(x) == 0.0` is an exact float compare — a near-degenerate x would still divide by a tiny `x_ss` at `2437-2439`; borderline. |
| L21 | `dash_render.py:1936` | `marker = "circle"` | scatter default symbol. Stata's p1 symbol **is** `circle` for s2color (`schemes/s2color.scheme:97`), so the literal happens to be right — but it bypasses `scheme.default_symbol(color_idx)` (`dash_render.py:996`, never called), so plot 2 gets a circle where Stata would give it p2's symbol. Promote to MEDIUM if the scheme symbol cycle is wired up. |

---

## 4. Counts

- **HIGH: 20** (H1–H20)
- **MEDIUM: 29** (M1–M29)
- **LOW: 21** (L1–L21)
- **Total: 70**

Of the HIGH findings, **4 are UNREACHABLE DEFAULTS** — the option that should
control the value is rejected by `dash.ado`'s `syntax`, so the literal can never
be overridden: H1/H2 (`level()`), H16 (`color()`), H17 (`width()`). A fifth
category, **accepted-but-never-read**, covers H13 (`mlcolor`), H14 (`falpha`)
and M28 (`pstyle`, `cmissing`, `recast`, `connect`).
