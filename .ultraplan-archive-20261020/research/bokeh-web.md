# Bokeh / web research for the dash GAPS3 plan (10 Oct 2026)

Environment verified: `python3` = Python 3.14.5 + bokeh 3.9.0 + scipy 1.17.1 + contourpy 1.3.3; `/opt/anaconda3/bin/python3` = Python 3.13.9 + bokeh 3.8.0 + scipy 1.16.3. Both bokeh wheels declare `Requires-Python >=3.10`; 3.9 dropped `pandas` from its hard requirements (3.8 requires `pandas>=1.2`); both require `contourpy>=1.2`. Local Chrome 154 at `/Applications/Google Chrome.app`, node 24.13.1. Snippets were run under BOTH pythons unless noted; scratch files are in the session scratchpad (`snip1.py`, `snip2.py`, `snip3.py`, `interp.py`, `stata/probe*.do`). No repository file was edited. The one Stata run used the console binary only.

---

## 1. Contours

**API (identical in 3.8 and 3.9; added in Bokeh 3.0)**
- `bokeh.plotting.figure.contour(self, x=None, y=None, z=None, levels=None, **visuals) -> ContourRenderer`
- `bokeh.plotting.contour.contour_data(x=None, y=None, z=None, levels=None, *, want_fill=True, want_line=True) -> ContourData` (fields `fill_data` with `xs, ys, lower_levels, upper_levels`; `line_data` with `xs, ys, levels`; `.asdict()` on each).
- `bokeh.models.ContourRenderer(DataRenderer)`: props `fill_renderer: Instance(GlyphRenderer)`, `line_renderer: Instance(GlyphRenderer)`, `levels: Seq(Float)`; Python-only methods `set_data(ContourData)` and `construct_color_bar(**kwargs) -> ContourColorBar` (builds `ContourColorBar(fill_renderer, line_renderer, levels, ticker=FixedTicker(ticks=levels))`).
- Inputs: `x`, `y` 1-D (len nx, len ny) or 2-D meshgrid; `z` 2-D shape (ny, nx); masked array or `np.nan` excludes grid points (verified: NaN block rendered as a hole). `levels` sequence; vector line props length `len(levels)`, vector fill props length `len(levels)-1`; palettes resampled with `interp_palette`; hatch via `hatch_pattern/hatch_color/hatch_alpha` (vectors allowed). Fill glyph is `MultiPolygons` (line_width 0), line glyph is `MultiLine`.
- fill source columns: `xs, ys, lower_levels, upper_levels, fill_color, hatch_pattern`; `xs[i]` is a list of polygons, each a list of rings (exterior + holes). Line source columns: `xs, ys, levels`. Lines-only (`line_color` without `fill_color`) leaves the fill source empty = contourline.

**Verified snippet (both versions)**
```python
import numpy as np
from bokeh.plotting import figure
from bokeh.plotting.contour import contour_data
from bokeh.palettes import Cividis
x = np.linspace(0, 4, 25); y = np.linspace(0, 3, 20)
X, Y = np.meshgrid(x, y); Z = np.sin(X) * np.cos(Y); Z[0:3, 0:3] = np.nan   # masked corner
levels = np.linspace(-1, 1, 9)
p = figure(width=400, height=300)
cr = p.contour(x, y, Z, levels, fill_color=Cividis, line_color="black",
               hatch_pattern=["x", " "] * 4, hatch_color="white")
p.add_layout(cr.construct_color_bar(title="z"), "right")
cr.set_data(contour_data(x, y, -Z, levels))          # Python-side refit (served app)
cl = figure().contour(x, y, Z, levels, line_color="navy")   # lines only = contourline
```

**BokehJS side**: the JS `ContourRenderer` (bokeh.js, `ContourRendererView`) only holds `fill_renderer`, `line_renderer`, `levels` and paints the two child glyph views; it has NO `set_data` and the bundle contains no contouring code (`contour` appears 4 times in bokeh.min.js, all the renderer class; `marching` 0). Contouring is done by ContourPy in Python only (user guide "Updating contours" says run under `bokeh serve`). So the saved page's JS twin must compute the polygons/polylines itself and write `fill_renderer.data_source.data = {xs, ys, lower_levels, upper_levels, fill_color: <copied>, hatch_pattern: <copied>}` and `line_renderer.data_source.data = {xs, ys, levels}` (mirror of Python `set_data`, which copies the non-geometry columns from the old source). `xs/ys` for MultiPolygons must be the 3-level nesting `[polygon][ring][points]`.
- JS options: write marching squares (lines are ~60 lines; filled *bands with holes* are much harder: need isobands + ring assembly), or embed a library: `d3-contour` 4.0.2 (ISC, GeoJSON MultiPolygon with holes for `z >= threshold`; bands can be faked by painting `z >= level_i` regions in ascending order with opaque fills -- breaks with fill alpha < 1), `marchingsquares` 1.3.3 has true `isoBands` but is **AGPL-3.0** (avoid). contourpy itself has no JS build.
- Gotcha: ContourPy's NaN masking omits any cell touching a masked node; a hand-written JS version must apply the same rule for parity.

**Verdict**: contour (filled) -- *feasible with caveat* (Python side trivial; JS refit needs an isoband implementation, or accept the painter's-order trick/frozen cue). contourline -- *feasible* (JS marching-squares lines are short to write; parity against contourpy's segment order is not needed if tests compare the rasterised/level sets).

---

## 2. Scattered (x,y,z) -> grid interpolation

Stata's [G-2] manual (verified from the shipped PDF) defines:
- "thin-plate-spline": `z = w1 f(y-y1, x-x1) + ... + wn f(y-yn, x-xn) + w(n+1) + w(n+2) x + w(n+3) y` with **`f(y,x) = sqrt(y^2 + x^2)`** (i.e. the *linear/polyharmonic* kernel r, NOT r^2 log r) solved from an (n+3) system, n = unique (y,x) pairs with nonmissing z. Rule of thumb n <= 1000.
- Shepard: `z = sum(z_i f_i)/sum(f_i)`, `f(y,x) = 1/(x^2+y^2)` over all n points (global inverse-distance-squared).
- Reference: Press et al. 2007, 140-144.

**numpy-only reference implementations (verified: exact at data points to 1e-14; agrees with `scipy.interpolate.RBFInterpolator(kernel="linear", degree=1)` to 2e-14)**
```python
import numpy as np
def tps_fit(x, y, z):                      # Stata's "thinplatespline": kernel r, degree-1 polynomial
    x, y, z = (np.asarray(a, float) for a in (x, y, z)); n = x.size
    r = np.hypot(x[:, None] - x[None, :], y[:, None] - y[None, :])
    P = np.column_stack([np.ones(n), x, y])
    A = np.zeros((n + 3, n + 3)); A[:n, :n] = r; A[:n, n:] = P; A[n:, :n] = P.T
    return np.linalg.solve(A, np.concatenate([z, np.zeros(3)]))   # O(n^3); singular for duplicate (x,y) or collinear data
def tps_eval(w, x, y, gx, gy):
    x, y = np.asarray(x, float), np.asarray(y, float); n = x.size
    gx, gy = np.asarray(gx, float).ravel(), np.asarray(gy, float).ravel(); out = np.empty(gx.size)
    for s in range(0, gx.size, 4096):                                  # chunked: memory = chunk x n
        r = np.hypot(gx[s:s+4096, None] - x[None, :], gy[s:s+4096, None] - y[None, :])
        out[s:s+4096] = r @ w[:n] + w[n] + w[n+1] * gx[s:s+4096] + w[n+2] * gy[s:s+4096]
    return out
def shepard(x, y, z, gx, gy):              # Stata's "shepard": 1/d^2 weights; exact hit returns z_i
    x, y, z = (np.asarray(a, float) for a in (x, y, z))
    gx, gy = np.asarray(gx, float).ravel(), np.asarray(gy, float).ravel(); out = np.empty(gx.size)
    for s in range(0, gx.size, 4096):
        d2 = (gx[s:s+4096, None] - x[None, :])**2 + (gy[s:s+4096, None] - y[None, :])**2
        hit = d2 == 0
        wgt = np.where(hit, 0.0, 1.0 / np.where(hit, 1.0, d2))
        val = (wgt @ z) / wgt.sum(axis=1)
        anyhit = hit.any(axis=1); val[anyhit] = z[hit.argmax(axis=1)[anyhit]]
        out[s:s+4096] = val
    return out
```
Both transcribe to JS directly (the solve needs a small Gaussian-elimination with partial pivoting, ~25 lines; everything else is loops).

**Measured cost (python3, M-series Mac, 100x100 target grid)**: n=500 solve 0.00 s; n=1000 solve 0.01 s / eval 0.04 s; n=2000 0.06 s / 0.08 s; n=4000 0.34 s / 0.12 s; Shepard n=1e5 -> 100x100: 4.05 s (over the 2 s bound; needs a KD-tree/neighbour cutoff or a smaller grid). Dense solve memory is (n+3)^2 doubles: n=1e4 = 800 MB -> impractical; n=1e5 impossible.
**scipy**: `scipy.interpolate.RBFInterpolator(y, d, neighbors=None, smoothing=0.0, kernel='thin_plate_spline', epsilon=None, degree=None)` (scipy >= 1.7). `kernel="linear", degree=1` reproduces Stata's formula; `kernel="thin_plate_spline"` is r^2 log r (does NOT match Stata). n=2000 linear 0.12 s; n=1e5 with `neighbors=50` 0.37 s (local, so differs from Stata's global fit). Note `scipy` is NOT a bokeh dependency and is not in Stata's bundled Python by default -- it would be a new dash_setup dependency (both local pythons happen to have it).

**What Stata actually does (measured with `twoway__contour_gen`, StataNow 19.5; the work is in compiled Mata built-ins `_contour_filled/_contour_line/_contour_heatmap`, so undocumented beyond the manual)**:
- The grid is NOT a uniform raster: nodes are `unique(x) x unique(y)` of the data. 200 scattered points -> 200x200 = 40,000 nodes (heatmap output 40,000 rects; 201 distinct rect edges = data midpoints plus min/max); 50 points -> 50x50. Rect edges are at midpoints of consecutive unique x (and y) values, extremes at min/max.
- Duplicate (y,x) -> smallest z (verified on the manual's 5-row example).
- Missing nodes are filled by the chosen `interp()`; `interp(none)` draws only observed cells.
- Cost: n=3000 scattered -> 3000x3000 = 9e6 nodes x 3000 kernels; Stata's own run had not finished after 10 minutes (killed). twoway does NOT subsample. So the plan's 1e5-row/2 s bound cannot apply to "match Stata exactly"; either cap n (refuse/subsample with a cue) or evaluate on a bounded grid and accept a documented difference.
- Not verified: the exact marching rule Stata uses to cut polygons on its rectilinear grid (only polygon vertex dumps are available; use `twoway__contour_gen ..., gen() [line] [heatmap]` output as truth as DISCOVERY Q4 says).

**Verdict**: TPS/Shepard in numpy and JS -- *feasible* for n <= ~2000 (matches Stata's formula exactly); *feasible with caveat* beyond that (cost/memory, divergence from Stata's n x n grid).

---

## 3. Arrows

- `bokeh.models.Arrow(DataAnnotation)`: `x_start, y_start, x_end, y_end` (NumberSpec: field/value), `start_units/end_units: Enum('canvas','screen','data')` (default data), `start`/`end: Instance(ArrowHead) | None`, `source: ColumnDataSource`, `line_*` props.
- Heads: `OpenHead` (line props), `NormalHead` and `VeeHead` (line + fill + hatch props), `TeeHead` (line). All have `size: NumberSpec` (default 25) -- **screen pixels only**, can be a column (`size="sz"`) but there is no data-unit option.
- Head angle: computed in `ArrowView.map_data` as `PI/2 + atan2(start, end)` per arrow -- no independent rotation; Stata `mangle()` cannot be expressed with Arrow. Alternative: draw the head with `scatter(marker="triangle", angle=..., size=...)` (screen size, radians angle) or a `patches` glyph in data units at the tip; shaft with `segment`.
- `barbsize` equivalent: `ArrowHead.size` (px), one value or a column. `barbangle` -> none (head shapes are fixed: Vee ~ Stata's default, Normal = filled triangle, Open = chevron).
- Performance: one `Arrow` with a `ColumnDataSource` draws all rows vectorised (verified construct); one Arrow per row is N annotations and N views -- avoid.

```python
src = ColumnDataSource(dict(x0=[0,1,2], y0=[0,1,0], x1=[1,2,3], y1=[1,0,1], sz=[8,12,16]))
arr = Arrow(end=VeeHead(size="sz", fill_color="red", line_color="black"), start=OpenHead(size=6),
            x_start="x0", y_start="y0", x_end="x1", y_end="y1", source=src, line_width=2, line_color="navy")
p.add_layout(arr)
```
JS update: `arr.source.data = {...}` (same CDS as the glyphs) -- the annotation re-maps on source change.
**Verdict**: pcarrow/pcbarrow -- *feasible*; `mangle()`/`barbangle()` -- *feasible with caveat* (custom head glyph, not Arrow).

---

## 4. Legend geometry (3.8 = 3.9 except `label_text_outline_width`/`title_text_outline_width` added in 3.9)

Props verified: `glyph_width: Int`, `glyph_height: Int`, `label_standoff: Int`, `spacing: Int`, `padding: Int | (x,y) | (l,r,t,b)`, `margin: Int`, `ncols/nrows: Positive Int | 'auto'`, `orientation: 'horizontal'|'vertical'`, `location: Enum(top_left … center … bottom_right, top/left/center/right/bottom) | (Float, Float)` (tuple = screen px from the frame's bottom-left), `border_line_*`, `border_radius`, `background_fill_*`, `background_hatch_*`, `item_background_*`, `item_background_policy: none|even|odd|every`, `title`, `title_standoff`, `title_location: above|below|left|right`, `title_text_align`, `label_text_align`, `label_width/label_height`, `click_policy: none|hide|mute`, `inactive_fill_*`, `items: [LegendItem(label, renderers, index, visible)]`. Outside the frame: `p.add_layout(Legend(items=[...]), "right")` (verified). ncols/nrows resolution (JS): both set -> used as is; only one set -> the other is `ceil(n/that)`.
- Rendering: in both 3.8 and 3.9 `LegendView` is a "dual renderer": a DOM CSS-grid (`legend_css`) on screen and canvas painting when exporting, so `view.export()` includes the legend.
- Text-first stacking: the item element is `glyph_el, label_el` in that order with no property to swap; the legend has its own shadow root and no `stylesheets` prop -> **not feasible** natively (only `label_text_align` and `title_location`).
- Holes: `LegendItem(label="", renderers=[])` constructs and is added as an entry with a blank glyph (verified at the Python level; not verified visually) -> *feasible with caveat*.
**Verdict**: legend options -- *feasible* (except text-before-symbol).

---

## 5. Axes

- Minor ticks: `Axis.minor_tick_in/out`, `minor_tick_line_*`; `BasicTicker(num_minor_ticks=k)`; `FixedTicker(ticks=[...], minor_ticks=[...])` (verified both versions). Other verified props: `axis_label_standoff`, `major_label_standoff`, `major_tick_in/out`, `major_label_orientation: 'horizontal'|'vertical'|'parallel'|'normal'|Float(radians)`, `fixed_location: Float|Factor|None` (axis drawn at a data value), `major_label_overrides`, `bounds`, `axis_label_orientation`.
- Labelled minor ticks: no native support (ticker minor ticks never get labels). Options: (a) `LabelSet(x="x", y="y", source=..., x_units="data", y_units="screen", y_offset=-18, text_align="center", text_baseline="top", level="overlay")` with y=0 (frame bottom) -- screen units are frame-relative so it stays aligned on resize/pan without JS (verified construct); (b) a second `LinearAxis` with `FixedTicker(ticks=minor)` at the same side, `major_tick_in/out=0`, small `major_label_text_font_size` and a `major_label_overrides` dict -- pure model, also resize-safe, but Bokeh stacks the second axis outside the first (needs negative `axis_label_standoff`/`major_label_standoff` tuning). (a) matches DISCOVERY Q37.
- Reference lines beyond the frame: `Span` (`location`, `location_units: data|screen|canvas`, `dimension`, `level`) clips to the frame; glyphs clip to the frame; `Arrow`/`Segment` with `start_units="canvas"` are not clipped but need canvas px (a CustomJS on `frame` change would have to recompute). A cheaper route for "line into the margin" is the padding of the range (`DataRange1d.range_padding`) or `Axis.fixed_location`. Not verified in a browser.
- Extra ranges: `Plot.extra_y_ranges: Dict(String, Instance(Range))`, `LinearAxis(y_range_name="r")`, glyphs with `y_range_name`. `Range1d(start, end, bounds, min_interval, max_interval, reset_start, reset_end)`; `DataRange1d(renderers=[...], only_visible, range_padding, follow, …)` auto-fits from the listed renderers (JS recomputes on source change, so a filter move updates it with no code); explicit `Range1d` must be set from the callback: `CustomJS(args=dict(rng=p.extra_y_ranges["r"]), code="rng.start = lo; rng.end = hi;")` (verified construct).
**Verdict**: *feasible* (minor-tick labels via LabelSet; margin-crossing lines *feasible with caveat*).

---

## 6. Widgets (all present and identical in 3.8/3.9 except `Tabs.link_layouts` (3.9, default False) and the new `Markdown` widget (3.9))

- `MultiChoice(options, value, title, placeholder, max_items, option_limit, search_option_limit, delete_button, solid, description)` (Choices.js; emits `role=listbox/combobox`, `aria-multiselectable`, `aria-haspopup`, `role=option` -- seen in the bundle). `MultiSelect(options, value, size, title)` = native `<select multiple>`. `Select(options, value, title)` = native `<select>`. `Slider/RangeSlider(start, end, value, step, title, format, direction: 'ltr'|'rtl', orientation, show_value, bar_color, tooltips, value_throttled)` (noUiSlider; `value_throttled` fires on release). `Button(label, button_type, icon)` = native `<button>`; `Toggle(active, …)`; `Switch(active, label, on_icon, off_icon)` (3.9 added `role` support to Switch per release notes; its knob has `tabIndex=0`, icon `role=img aria-hidden`).
- `DataTable(source, view: CDSView, columns, sortable, autosize_mode: fit_columns|fit_viewport|force_fit|none, fit_columns, frozen_columns, frozen_rows, index_position (None hides the index), index_header, index_width, header_row, row_height, selectable, multi_selectable, editable, auto_edit, reorderable, scroll_to_selection, height, width)` + `TableColumn(field, title, formatter, sortable, default_sort, sorter, editor)`; formatters `NumberFormatter(format, language, rounding, nan_format, null_format, text_align, text_color, font_style, background_color)` (numbro format strings), `DateFormatter(format)`, `StringFormatter`, `HTMLTemplateFormatter(template)` (underscore template; `<%- value %>` escapes). SlickGrid virtualises rows (only visible rows rendered), so "virtual scrolling through all rows" is native; sorting is in-JS via `TableDataProvider.sort`.
- **CDSView**: `DataTable.view` is honoured -- `TableDataProvider.init(source, view)` reads `view.indices`, and `DataTableView.connect_signals` re-inits on `view.change`, so a table bound to the same source and a `CDSView` with the same filter follows every filter move with no extra code (verified construct `DataTable(source=src, view=CDSView(filter=BooleanFilter([...])))` in both versions). A separate CDS is unnecessary unless the rows must be formatted (Stata display formats/value labels) -> formatters, or a per-table row cap -> an `IndexFilter` view.
- Collapse/expand: no accordion; `Toggle.js_on_change("active", CustomJS(args=dict(dt=dt), code="dt.visible = cb_obj.active;"))` (verified construct; `visible` on a hidden DataTable: SlickGrid may need `dt.visible=true` then a resize -- not verified in a browser) or `Tabs`. Bokeh 3.x also has `Dialog`/`OpenDialog`/`CloseDialog` models.
- Standalone pages: all of the above are pure BokehJS; `--allow-websocket-origin` is irrelevant to the saved page.
**Verdict**: data table, multi-select, reset button, slider direction -- *feasible*.

---

## 7. Accessibility

Bundle inspection (bokeh 3.9 `bokeh.js`, `bokeh-widgets.js`, `bokeh-tables.js`; 3.8 is the same except Switch):
- Bokeh's own ARIA is minimal: `aria-label="close"` on the notification close button, `role` only via a static `aria_role` hook on UI elements (unset for Plot/Canvas) and on Switch (3.9). Native widgets (`<select>`, `<button>`, `<input>`) are keyboard-reachable; sliders are noUiSlider handles (keyboard arrows supported by the library); MultiChoice comes from Choices.js with listbox/option roles; Tabs headers are `div tabIndex=0` with a click handler only (no keydown handler -> Enter/Space do nothing; keyboard activation needs a small nonce'd script or a `js_on_event` on keydown); the DataTable is SlickGrid (panes `tabIndex=0`, no ARIA grid roles); the plot's events layer is a `div tabIndex=0` with no role or name; `<canvas>` carries no `role`/`aria-label`.
- Every `UIElement` (Plot/figure, all widgets, layouts) has `html_attributes: Dict(String, String)`, `html_id`, `css_classes`, `styles`, `stylesheets` (verified 3.8 and 3.9; JS `_apply_html_attributes` sets them on the host element). `figure(html_attributes={"role": "img", "aria-label": "…"})` and `Slider(html_attributes={"aria-label": "…"})` serialise (18 occurrences in the test page). Caveat: this labels the *host* element (light DOM), not the inner `<canvas>`/`<select>` inside the shadow root; axe treats a `role=img` host with a name as accessible. Inner-element ARIA would need a nonce'd script walking `shadowRoot`s (Bokeh shadow roots are open), or `stylesheets`/`css_variables` cannot add attributes.
- Browser verification: my `--dump-dom` probe did not complete (Bokeh render timing under `--virtual-time-budget`/`--timeout`); dash already has a DevTools-protocol harness (`test/test_csp_browser.py`, `test/range_probe.py`, `--headless=new --remote-debugging-port`) that the accessibility test should reuse.
- Tools: axe-core 4.14.0 on npm (MPL-2.0); cdnjs latest 4.12.1 at `https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.12.1/axe.min.js` (HTTP 200 verified). Run: inject the script via DevTools `Runtime.evaluate` (or `Page.addScriptToEvaluateOnNewDocument`), then `await axe.run(document, {runOnly: ['wcag2a','wcag2aa','wcag21aa']})` -> `{violations:[{id, impact, nodes:[{target, html}]}]}`; axe does pierce open shadow DOM. Fetching the file into the repo is a download (not done here). `@axe-core/puppeteer` 4.13.0 and `@axe-core/cli` 4.13.0 (MPL-2.0, need puppeteer 25.x Apache-2.0), `pa11y` 10.0.0 (LGPL-3.0, wraps HTML_CodeSniffer/axe), `lighthouse` 13.5.0 (Apache-2.0, needs node >= 22.19; its accessibility audit is axe). Keep axe-core vendored or CDN-fetched by the test only, never into the shipped page (CSP).
- Contrast (WCAG 2.1, verified: black/white = 21.0, #777 on white = 4.478, #1a476f on white = 9.656):
```python
def rel_lum(hexcol):
    h = hexcol.lstrip('#'); r, g, b = (int(h[i:i+2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)
def contrast(a, b):
    la, lb = sorted((rel_lum(a), rel_lum(b)), reverse=True); return (la + 0.05) / (lb + 0.05)   # AA text >= 4.5, large/UI >= 3
```
**Verdict**: *feasible with caveat* (host-level ARIA via `html_attributes`; Tabs keyboard activation and inner-element names need a small nonce'd script; automated check via existing DevTools harness + axe-core).

---

## 8. JavaScript error surfacing

- A standalone page can register `window.onerror = (msg, src, line, col, err) => …` and `window.addEventListener('unhandledrejection', e => …)` from an inline `<script nonce=…>` placed before the Bokeh bootstrap; BokehJS does not swallow exceptions thrown inside `CustomJS` -- they propagate from the property-change signal to the caller (a widget event handler), so `window.onerror` sees them (not verified in a browser this session; `test_csp_browser.py`'s `Runtime.exceptionThrown` listener is the existing way dash observes them).
- Safer: wrap each `_FILTER_JS` body in `try { … } catch (e) { const d = Bokeh.documents[0].get_model_by_id(ERR_DIV_ID); d.text = escape(e.message); throw e; }` and give the `Div` `html_attributes={"role": "status", "aria-live": "polite"}`. `Div.text` is innerHTML -> escape the message (or `render_as_text=True`).
- CSP: dash's pages already carry a `<meta http-equiv="Content-Security-Policy">` with a per-page nonce (`dash_render.py` lines ~39-44, 4590-4711): the handler script must carry that nonce; `CustomJS` code runs via `new Function` inside BokehJS, which the existing policy already permits (`'unsafe-eval'` or equivalent as measured in WP-30 P1.29) -- no new directive needed. Avoid `javascript:` URLs and inline handlers (`onclick=`), which nonces do not cover.
**Verdict**: *feasible*.

---

## 9. Printing / export

- `@media print`: Bokeh draws to `<canvas>` inside shadow roots; browsers print canvases as rasters at the on-screen size, and `sizing_mode="stretch_*"` layouts can re-layout to the paper width during print (ResizeObserver). Register `window.addEventListener('beforeprint', …)` to fix widths (or set `@media print { .bk-root … }` to a fixed width) and `afterprint` to restore. Not verified in a browser.
- In-page export (verified in bokeh.js 3.9 source): `PlotView.export(type="auto"|"png"|"svg", hidpi=true) -> CanvasLayer` with `.canvas` and `.to_blob()` (PNG Blob or SVG Blob), composes glyph levels + overlays + exportable renderer views (legend included via its canvas paint path). `LayoutDOMView.export(type, hidpi)` composites every *child view's* `export()` onto one canvas filled with the layout background: plots and color bars yes, DOM widgets (Div, DataTable, sliders, Tabs headers) are drawn only if their view implements `export` -- they do not, so KPI cards/filters/tabs would be missing. Access from the page: `for (const v of Bokeh.index) …` (root views), `v.owner.get_one(model)` for a child. SVG of several figures: call `export("svg")` per figure and wrap the serialised strings (`layer.ctx.get_serialized_svg(true)`) in an outer `<svg>` with `<g transform="translate(x,y)">` using each view's `bbox`.
- Composite with HTML widgets: `html2canvas` 1.4.1 (MIT; last release 2022; walks the light DOM, does not descend into shadow roots -- Bokeh's widgets and canvases live in shadow roots, so it would miss them) and `html-to-image` 1.11.13 (MIT; SVG `foreignObject` serialisation; shadow-DOM support unconfirmed -- web search gave no authoritative answer). Both need to be inlined into the page (CSP: no CDN) and `foreignObject` rendering taints or blocks fonts. Pragmatic route: Bokeh `export()` per figure + draw the KPI/title/filter text onto the composite canvas with `ctx.fillText` from model values, or render those as Bokeh `Label`/`Div`-free elements.
- `output_backend="svg"`: per-figure property, text and lines become DOM paths; cost is proportional to glyph count (large scatters become slow and the SVG huge); hover/selection work but WebGL is unavailable. Use only for export, i.e. `export("svg")` on a canvas-backend figure already switches the backend for the export layer -- no need to set `output_backend` globally.
**Verdict**: PNG/SVG of figures -- *feasible*; composite with widgets -- *feasible with caveat* (hand-composited, not html2canvas); print stylesheet -- *feasible with caveat* (needs browser verification).

---

## 10. Bokeh 3.8 vs 3.9

Programmatic diff of every `bokeh.models` class's property set between the two installed versions:
- New model: `Markdown` (3.9). No removed models, no removed properties.
- Added in 3.9: `Tabs.link_layouts` (Bool, default False -- 3.8 always linked tab layouts); `Step.pad_before/pad_after`; `*_text_outline_width` on every text-bearing model (Axis, Legend, Label/LabelSet, Title, ColorBar, ContourColorBar, Text glyph …).
- DataTable, MultiChoice, MultiSelect, Select, Slider, Button, Toggle, Switch, ContourRenderer, Legend (apart from outline width), Arrow/ArrowHead: identical property sets.
- Release notes (fetched from GitHub `docs/bokeh/source/docs/releases/3.9.0.rst`, 3.8.0.rst): 3.9 adds Python 3.14 and pandas 3 support, removes pandas as a required dependency, ARIA `role` on `Switch`, CSS-variable colour system (initial), Preact virtual DOM (initial), large-dataset perf; no deprecations listed. 3.8 adds HoverTool filters/sorters/limits, session reconnect events, `Plot` side panels + `SizeBar`, `Document.config`, `legend_name` glyph kwarg, buffer compression, CSS-variable theming (preliminary). Neither release note mentions DataTable/MultiChoice/contour/Arrow changes.
- Resources: dash inlines BokehJS (`file_html(..., INLINE)`; page ~1.2-1.9 MB in the probes). CDN resources would need `script-src https://cdn.bokeh.org` in the CSP and break offline use -- keep INLINE. `bokeh-tables` and `bokeh-widgets` bundles are added automatically when DataTable/widgets are in the document.
**Verdict**: no 3.8/3.9 divergence affects the plan; keep tests to the 3.8 property set (no `link_layouts`, no `*_outline_width`, no `Markdown`).

---

## 11. Stata twoway contour / contourline (from the shipped [G-2] PDF and ado files)

- Syntax: `twoway contour z y x [if] [in] [, ccuts(numlist) levels(#) minmax crule(hue|chue|intensity|linear) scolor() ecolor() ccolors() heatmap interp(thinplatespline|shepard|none) twoway_options]`; `contourline` adds `format(%fmt) colorlines clwidths(linewidthstylelist) reversekey` and has no `heatmap`/`ccolors` for areas. `clegend()` is a [G-3] option (`clegend(off)`, `width()`, `altaxis`, `title()`, merged-implicit) controlling the contour legend; `zlabel()` controls that legend's axis and, when neither `ccuts()` nor `levels()` is given, the cuts themselves.
- `levels(#)` -> `# - 1` cuts equally spaced between min(z) and max(z); `minmax` adds min and max; `ccuts()` and `levels()` may not be combined. `crule(hue)` equally spaced hues from scolor to ecolor; `chue` adds 360 to ecolor's hue when it is below scolor's; `intensity` spaces intensities with ecolor as base (scolor ignored); `linear` interpolates RGB. Default scheme colours come from `shadestyle-contour_begin.style`/`contour_end.style` and `zyx2type-contour.style`.
- Interpolation formulas: see §2 (kernel is `sqrt(x^2+y^2)`, not r^2 log r). "Regular grid" = every nonmissing (y,x) combination has a z; duplicate pairs use the smallest z.
- Undocumented (measured only): the grid is `unique(x) x unique(y)` of the data (n x n for scattered data); heatmap rectangles have edges at midpoints between consecutive unique values and at min/max; the polygon-cutting algorithm lives in compiled Mata (`_contour_filled`, `_contour_line`, `_contour_heatmap` called from `/Applications/StataNow/ado/base/t/twoway__contour_gen.ado`, which exposes `gen(z y x levels)` output = the truth fixture source); the run time for n=3000 exceeded 10 minutes (so twoway itself does not subsample).
- Video/ref: Press et al. 2007 pp. 140-144 (RBF interpolation).

---

## Not verified / open
- Browser-side behaviour (ARIA host attributes in the live DOM, `window.onerror` catching CustomJS throws, DataTable `visible` toggle, print layout, legend hole rendering): the headless `--dump-dom` probe did not reach Bokeh's render; use dash's DevTools harness (`test/test_csp_browser.py`) for these.
- html-to-image shadow DOM support.
- Stata's exact contour polygon construction (compiled Mata); match by comparing `twoway__contour_gen` output.
- axe-core was not downloaded (file download needs explicit permission).