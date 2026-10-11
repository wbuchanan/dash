# UltraPlan Research: dash -- close the GAPS3 drop-in gaps

> Generated: 2026-10-10
> Phase: 2/6 - RESEARCH
> Research topics extracted: 10
> Subagents deployed: 3 (Codebase, Bokeh/web, Stata sources). Their full reports are
> `research/codebase-mechanics.md` (49 KB), `research/bokeh-web.md` (33 KB) and
> `research/stata-ground-truth.md` (39 KB); every section brief cites them by
> heading. This file is the synthesis and the conflict record.

---

## Research Topics

| # | Topic | Source | Priority |
|---|-------|--------|----------|
| 1 | Bokeh contour API and a JavaScript refit | DISCOVERY Q4 | high |
| 2 | twoway contour's interpolation, grid and options | Q4, GAPS3 B4 | high |
| 3 | rpcap/rpspike roles and drawing; sunflower/matamatrix advice | Q5, GAPS3 B1-B3 | high |
| 4 | Per-type option applicability from twoway's parse classes | Q15, GAPS3 C3 | high |
| 5 | Porting the eleven estimators to JavaScript | Q27, GAPS3 F1 | high |
| 6 | Bokeh DataTable, MultiChoice, Switch, Arrow, Legend, axes | Q35-Q40, GAPS3 C1, D1-D6 | medium |
| 7 | Accessibility in Bokeh pages and automated checking | Q34 | medium |
| 8 | WP-30 section/brief/truth-block conventions | Q23-Q26 | high |
| 9 | Declaring a Python dependency end to end | Q11 | low |
| 10 | Bokeh 3.8 vs 3.9 differences | tests must stay on 3.8's API | low |

---

## Key findings

### 1. Contour and contourline are feasible in Bokeh; the live refit is bounded

- Bokeh 3.0+ has `figure.contour(x, y, z, levels, fill_color=, line_color=)` returning a
  `ContourRenderer` (fill = MultiPolygons, line = MultiLine), with NaN masking and
  `construct_color_bar()`. Lines-only is contourline. Python recomputes with
  `contour_data()` + `ContourRenderer.set_data()`. Both installed Bokehs (3.8, 3.9)
  carry it; contourpy is already a Bokeh dependency. **The served app can refit
  contours with existing Bokeh machinery.**
- BokehJS has **no** contouring code: the saved page's JS twin must compute the
  polylines (marching squares, ~60 lines) and, for filled contours, isobands with
  holes (harder). d3-contour 4.0.2 (ISC) produces MultiPolygons with holes; the
  AGPL `marchingsquares` library is out.
- Stata's interpolation ([G-2] manual): "thin-plate spline" is the polyharmonic
  kernel **f = sqrt(x²+y²)** with a degree-1 polynomial (NOT r² log r), solved
  from an (n+3) system; Shepard is global inverse-distance-squared. numpy-only
  implementations (verified exact at the data, equal to scipy's
  `RBFInterpolator(kernel="linear", degree=1)` to 2e-14) are in
  research/bokeh-web.md §2 and transcribe to JavaScript. **No scipy is needed**
  (scipy's `thin_plate_spline` kernel is the wrong one).
- Measured on StataNow 19.5: twoway's grid is `unique(x) × unique(y)` of the data
  (n×n for scattered data, nodes filled by the interpolation); duplicates take the
  smallest z; twoway does not subsample and n=3000 had not finished after ten
  minutes. The TPS solve is O(n³), memory (n+3)² doubles. Practical bound for an
  exact match: about n ≤ 1,000-2,000 unique points (0.01-0.06 s solve, 0.04-0.08 s
  evaluation on a 100×100 grid in Python). The compiled polygon-cutting rule is
  unknown; truth = `twoway__contour_gen ..., gen()` output.
- rpcap/rpspike: a segment from (x, y1) to (x, y2), caps of total width = marker size
  at both ends (rpcap), the marker at (x, y3); y range over the three y variables;
  legend key = cap/spike line plus the marker. **Feasible with existing glyphs.**

### 2. Everything else the discovery asked for is feasible in Bokeh, with these caveats

- Arrows: `Arrow` + `OpenHead/NormalHead/VeeHead` with `size` as a column (screen
  px), `fill_color`; one Arrow over a ColumnDataSource is vectorised. `mangle()` has
  no Arrow equivalent: draw the head as a rotated marker or patch.
- Legend: `glyph_width/height, label_standoff, spacing, padding, margin, ncols/nrows,
  location (named or (x,y)), border_*, background_*, title, title_location,
  click_policy`; empty `LegendItem` as a hole. **Text-before-symbol is not
  expressible** (document, per Q30).
- Minor-tick labels: `LabelSet` with `x_units="data", y_units="screen"` at the
  frame edge stays aligned on resize (Q37's route). Off-frame reference lines:
  Span clips; Segment in canvas units does not but needs a frame-change callback.
- Widgets: `DataTable` with `TableColumn` formatters follows a `CDSView` of the same
  source, so a per-graph table bound to the drawn source follows every move with
  no extra code; SlickGrid virtualises rows and sorts in JS; collapse via a
  `Toggle` driving `visible`. `MultiChoice` (Choices.js, listbox roles),
  `Slider(direction="rtl")`, `Button` for reset.
- Accessibility: every UIElement has `html_attributes` (role, aria-label) on its
  host element; axe-core 4.12.1 (MPL-2.0) on cdnjs can be injected through the
  existing DevTools harness (test_csp_browser.py); Tabs headers have no keydown
  handler (needs a nonce'd script); WCAG contrast formula verified.
- JS errors: `window.onerror`/`unhandledrejection` from a nonce'd script, or a
  try/catch per `_FILTER_JS` body writing a `role="status"` Div.
- Export: `PlotView.export("png"|"svg")` per figure; `LayoutDOMView.export`
  composites child canvases but not DOM widgets, so KPI cards/filters/tabs must be
  hand-composited (`ctx.fillText`); html2canvas does not pierce shadow roots.
- Bokeh 3.8 vs 3.9: no model removed; 3.9 adds `Markdown`, `Tabs.link_layouts`,
  `*_text_outline_width`. Tests stay on 3.8's property set.

### 3. The codebase mechanics every brief cites (research/codebase-mechanics.md)

- An option travels: `syntax` in `_dash_parse_plot_opts` (dash.ado:1167-1239) /
  `_dash_parse_graph_opts` (:933-966) → `sreturn` → `_dash_option_rules`
  (:2987-3079, kinds `num int pos colour style istyle enum numlist axislist
  keyformat var varlist byvarlist scheme format`, `flags`, `values`, `onevalue`)
  → `_dash_plot_opts_to_json` key list (:4441-4458) or the seven graph key lists
  (:5776, 6714, 6748, 6849, 6924, 6956, 7339) → `GlyphMapper._apply_*` /
  `_dash_reference_lines` etc. → the served app by source copy (`_glyph_layer_lines`
  :46530-47393; module helpers need a copy-list entry at :46822-47270).
- The pending blocks (:1010-1042, :1320-1387) feed the "ignoring unsupported
  option(s)" note; `_dash_rep_und_tab` (dash_parse.mata:6250-6324) lists undeclared
  options twoway takes once (delete the row when declaring one).
- There is **no per-type applicability column**; the natural seat is beside
  `flags` and the check sits in `_dash_validate_opts` before the rule loop (:3923).
- A new plot type touches: families (:4516-4529) and the renderer categories
  (dash_render.py:25958-25975), the Mata abbreviation table (:1688-1780),
  `_dash_undrawn_plottype`, the var-count branch, JSON vfields, the "Supported:"
  list, `_dash_glyph_dispatch`/`_dash_pc_dispatch`/`_dash_add_glyph`, var-key
  lists (`_dash_extract_vars`, `_DASH_PLOT_VAR_KEYS`), horizontal tables, help
  table and refusal sentence, and seven test files (listed in §2 of the report).
- JS recompute: a mapper tags `r._dash_agg_source/_dash_agg_config/_dash_agg_rows`;
  `DashRenderer.render()` step 3b registers them; `_FILTER_JS` (:24612) reads one
  variable per config today, so a fit branch must read `ac.xvar`/`ac.yvar`
  itself; new helpers go between `dash_kernel` and the "agg_sources" comment so
  `js_runner.run_filter_js_block` slices carry them; a type that gains a refit must
  make `_dash_stale_kind` return None. Parity pattern: test_statistical_helpers.py
  :810-848.
- Served moves: `_dash_redraw_for` re-draws any layer whose mapper built its own
  source, so new computed types refit when served with no extra code; neither
  `_dash_refinish_axes` nor `_DASH_AXIS_FINISH_JS` touches y2/x2 after a move.
- Test conventions: one truth cscript per WP with `* ==== S<NN> ... ====` blocks and
  a `WP<NN>_ONLY` gate; extractors `scripts/extract_*_truth.do` writing `_meta`;
  CORPUS/MOVE_CORPUS entry shapes; `function_test_map.py` and
  `program_coverage_map.py`; the GAPS2 Tracked reader regexes; the BUGS.md
  four-field entry with one WP-30 example verbatim.
- Dependencies: eight places (dash_setup.ado, dash_setup_lib.py, dash.ado
  `_dash_require_deps`, dash_render.py guards and served header, dash.pkg,
  both help files, requirements files) plus six tests that assert scipy is absent.

### 4. Stata ground truth (research/stata-ground-truth.md)

- The parse-class inheritance table and the per-type option table (which options
  every yxview type accepts, which are bar-family only, which belong to one type)
  give the applicability column directly; inapplicable options fall to Stata's
  compiled `syntax` with "option X() not allowed" r(198) (exact spelling needs
  measurement).
- dot: 75 dots per row, base from the axis range (0 if spanned, else the nearer
  edge), dot style `symbol dots circle`, `symbolsize dots vtiny`, `color dots black`.
- Arrow heads: angle 28.64 (anglestyle stdarrow), `barbsize` 0 (open strokes) or
  filled polygon, `msize` from `symbolsize parrow medium`.
- Legend geometry stubs (symxsize 13, keygap vsmall, rowgap tiny, colgap large,
  cols 2, position 6 ring 3), `ring(0)` → inside at the clock's compass position,
  `pos(0)` → centre; rows/cols rule.
- Minor ticks: `numticks_g *_minor 0`, `gsize minortick half_tiny`,
  `minortick_label vsmall`; `##N` = N-1 between majors, needs even majors.
- Edge titles: ring 1/2 by digit, l/r vertical, textbox styles subheading/body.
- Textbox semantics, mlabel default clock (bar family 12, else 3), histogram
  `gap()`, kdensity `area()/boundary`, function `droplines()/base()`, rbar
  `mwidth`/`msize`, and the 40-odd `scheme-s2color.scheme` stubs absent from
  `dash-s2color.scheme`.

---

## Conflicts between research and discovery

| # | Discovery answer | Research finding | Resolution |
|---|---|---|---|
| C1 | Q4: reimplement the interpolation in Python and JavaScript so contour refits after a move | twoway's own grid is n×n unique values, O(n³) solve; twoway takes >10 min at n=3000; a JS refit of filled contours needs an isoband algorithm | **Decided:** exact match up to a cap of about 1,000 unique points, refit live in both modes within the cap; above it, a bounded grid in Python, the stale cue on the saved page and a note. JS gets marching squares for lines and an isoband routine for fills. |
| C2 | Q20: new computed layers under 2 s for 100,000 rows | an exact contour match cannot meet that at any n above ~2,000 unique points | **Decided:** contour and contourline are exempt from any timing test; every other new computed layer keeps the 2 s / 100,000-row bound. |
| C3 | Q11: any dependency that helps | nothing in scope needs one: numpy reproduces Stata's kernel exactly, contourpy ships with Bokeh | **Decided:** no new dependency; dash_setup unchanged. |
| C4 | Q35(d): legend `textfirst`/`stack` | Bokeh's legend cannot put text before the symbol | documented difference (Q30) |
