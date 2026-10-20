# Bokeh / browser research for WP-33..WP-49 (20 Oct 2026)

Inputs: `.ultraplan/DISCOVERY.md` (binding), `review/DROPIN-AUDIT-19oct2026.md` lines 1-915.
Versions measured: Bokeh **3.8.0** (`/opt/anaconda3/bin/python3`, Python 3.13) and **3.9.0** (`python3`, Python 3.14); Chrome 155.0.8059.85, Firefox 157.0, Safari 26.5, macOS 26.5 (M2 Max).
Citations: `B8` = `/opt/anaconda3/lib/python3.13/site-packages/bokeh`, `B9` = `/opt/homebrew/lib/python3.14/site-packages/bokeh`; `js8`/`js9` = `<B>/server/static/js/bokeh.js`.
Experiments (scratch, not in the repo): `$SCRATCH/r3/` = `/private/tmp/claude-501/-Users-billy-Desktop-Programs-StataPrograms-d-dash/38f9d591-4f54-40a5-b82e-132f3af8ec53/scratchpad/r3/`. Every one reuses `test/range_probe.RangeProbe` (Chrome over DevTools, tornado websocket) and was run under both Pythons. Nothing was installed; no Stata was run.

## 0. Verdicts in one place

| Question | Verdict |
|---|---|
| Static SVG without selenium | **Yes, today, both versions.** `Bokeh.index.find_one(model).export("svg").ctx.get_serialized_svg(true)` evaluated over DevTools on the saved page. No `output_backend="svg"` is needed: `PlotView.export("svg")` repaints any canvas or webgl figure into a fresh SVG layer. dash already ships this call (Save as SVG, `dash_render.py:50184`, `:50560`). |
| What the SVG loses against the canvas | Raster `<image>` for: legend key glyphs (20x20 PNG each), the ColorBar strip, image glyphs, TeX text (SVG data URIs), and GL glyphs when WebGL is active. The rest is vector. Each text is written twice (fill, then a zero-opacity stroke). clipPath ids are random. The rasterised SVG matches the canvas export to SSIM 0.998. |
| Fixed 5.5x4 in size | A lone figure: set `sizing_mode="fixed"`, `width`/`height`, and clear `min_height`, `max_height` and `aspect_ratio` in-page, then export. This gives exactly 528x384 in both versions. A by() GridPlot forced the same way collapses (empty SVG), so by() needs dash itself to honour a fixed size (the P1-5 fix below). Note that twoway's default under stcolor is **7.5 x 4.5 in**, not 5.5 x 4 (`scheme-stcolor.scheme:9-11`); 5.5 x 4 is s2color. |
| Verdict machinery | Geometry: the existing stdlib readers (`scripts/svg_truth.py`, `svg_layer.py`, `svg_text_runs.py`, `svg_scheme_visual.py`, `svg_chrome.py`) on the twoway side, and one BokehJS view dump on the dash side. Image score: Chrome rasterises both SVGs at one size, then SSIM in numpy+scipy (matches scikit-image to 4 dp). **No new dependency.** |
| Firefox + WebKit release tier | Firefox: **WebDriver BiDi over the tornado client dash already uses**, against the installed Firefox. Measured working; no geckodriver or selenium. WebKit: **Playwright for Python** (dev-only). It is the only headless WebKit on macOS, since Safari/safaridriver has no headless mode. Alternative: Playwright for both. |
| P1-5 aspectratio + xsize/ysize | Cause measured. Fix: give the fixed figure `width`/`height` = the xsize/ysize box and clear `min_height`, `max_height` and `aspect_ratio`. That gives the exact frame and no E-1023 in both versions. |
| P2 WebGL | No per-renderer backend exists, so dashed lines must keep the whole figure on canvas. Thick dashed and dotted lines drawn by WebGL diverge on the **real GPU** too (dotted IoU 0.44 against solid 0.92 at 20,000 vertices). Today's browser tests pass `--disable-gpu`, which turns WebGL off completely in Chrome 155, so no existing test has drawn a WebGL figure. |
| P6-P10 under the maintainer's definition | 97 bullets: 0 judged **no**. 70 are yes, of which many are parse, rc or computation work with no drawing limit. 27 are yes-as-composite (several Bokeh glyphs, labels and boxes making one twoway element). Three of the composites have residuals worth a sentence under Differences anyway (section 4.8). |

---

## 1. Static SVG of a dash graph without selenium

### 1.1 What Bokeh's own exporter does

- `bokeh.io.export_svg/get_svgs` need selenium (`B9/io/export.py:285-317`). They are not usable: selenium is in neither Python.
- The JS they run is what matters:
  - 3.9 `_SVGS_SCRIPT` (`B9/io/export.py:469-484`) calls `view.export("svg")` and `ctx.get_serialized_svg(true)` for each `PlotView` whose `output_backend == "svg"`.
  - 3.8 (`B8/io/export.py:469-484`) instead calls `view.canvas_view.compose()`. That only yields SVG for an svg-backend figure.
  - `_SVG_SCRIPT` (both versions) calls `view.export("svg")` on the root views found by id.
- The BokehJS export methods are identical in 3.8 and 3.9:
  - `PlotView.export(type)` (js9:45559-45585, js8:45438-45464) builds a new `CanvasLayer("svg")`, force-paints primary + overlays into it, and draws every exportable renderer view (Legend, ColorBar) into it. **The figure's own backend is irrelevant.**
  - `LayoutDOMView.export` (js9:21868-21887, js8:21819-21838) composites child exports. A Div, widget or Tabs header has no canvas paint and is absent.
  - `UIElementView.export` (js9:11560-11566) returns an empty layer of its bbox.
- dash already relies on this: `_DASH_SVG_SAVE_JS` (`dash_render.py:50184`), the composite save (`:50560`), the internals list (`:309-321`) and `test/test_export_svg.py::TestInChrome`.
- Do **not** set `output_backend="svg"` in shipped pages. It breaks the grid's PNG save: `drawImage` TypeError, measured in both versions again here (`f_svg` row below).

### 1.2 Experiment (`$SCRATCH/r3/exp_svg.py`, both versions; outputs `out38/`, `out39/`)

Eight 528x384 figures on one page, exported in-page:
- Each SVG was drawn onto a same-size canvas and compared with `export("png")`, counting pixels whose channel difference is above 48.
- Each figure has: title, subtitle, note Titles, markers, a 4 px dashed line, an inside Legend with a title, a bold Label, a BoxAnnotation and a dotted Span.

| Figure | 3.9 SVG (3.8 within 1%) | `<image>` | Pixel diff vs canvas |
|---|---|---|---|
| canvas backend | 48.7 KB, 105 paths, 40 texts (= 20 x2) | 3 (legend keys, PNG 20x20) | 0.018% |
| svg backend | 47.9 KB, 108 paths | 0 (keys vector) | `export("png")` throws `TypeError ... drawImage` (both) |
| webgl backend + 20,000 points, Chrome `--disable-gpu` | 7.3 MB, 20,106 paths | 3 (keys) | 0.023% |
| image glyph + stepped ColorBar | 20.4 KB | 2 (the image glyph, the colour strip, PNG) | 0.63% |
| outside legend + TeX axis label + TeX Label | 43.5 KB | 4 (2 keys PNG, 2 TeX `data:image/svg+xml`) | 0 |
| inactive tab (fixed-size child) | identical to the active one | 3 | 0.018% |
| `frame_width=400, frame_height=300` | 425x347 (3.8: 425x349) | 0 | 0 |

Findings:
1. **Vector except**:
   - legend key glyphs. The Legend is DOM; each entry's glyph is its own small canvas (`_paint_glyphs`, js9:39793-39807), so export embeds PNG.
   - ColorBar strip: a PNG even under the svg backend (`$SCRATCH/r3/cbsvg`: canvas 2 PNG, svg backend 1 PNG).
   - image glyphs.
   - TeX: MathJax SVG as a data URI.
   - With an svg-backend figure the legend keys become vector paths.
2. **WebGL**: with WebGL unavailable (Chrome `--disable-gpu`), GL glyphs fall back to canvas painting and export as paths. In **Firefox** (WebGL2 on) the same figure exported 290 KB with 7 `<image>`: the GL scatter became a raster. So a vector export of a WebGL figure needs WebGL off in the exporting browser, or the figure rebuilt as canvas in the harness copy.
3. **Text**: `font-family="helvetica"`, px sizes. Every text appears twice: `fill=...` and then `fill="none" stroke-opacity="0"`. Readers keep only `fill` not `none`.
4. **Determinism**: clipPath ids are random per export (`id="ngWPXGKbisGz"`). Committed gallery SVGs need an id normaliser (renumber in document order) so re-runs do not churn git.
5. **Tabs**: a fixed-size figure in an inactive tab exports normally. A stretch-sized one may have a 0 bbox (not measured). The harness exports single-graph pages, so tabs do not arise there.
6. **Size**: about 350 bytes per marker path. 20k points makes 7.3 MB. Q53 sets no cap, but the README pairs should avoid examples above about 5k points.

### 1.3 On real dash pages (`$SCRATCH/r3/exp_fixed.py`, `fix38/`, `fix39/`)

Pages were built with `DashRenderer` and exported at 528x384 after this in-page fix-up:

```js
for (const r of doc.roots()) { r.sizing_mode='fixed'; r.width=W; r.height=H; }
f.min_height=null; f.max_height=null; f.aspect_ratio=null;
f.sizing_mode='fixed'; f.width=W; f.height=H;          // then wait ~1.5 s, then export
```

| Case | Result (3.8 and 3.9 equal) |
|---|---|
| lone scatter | 528x384, 0 `<image>` |
| scatter + line on yaxis(2) (legend) | 528x384, 2 PNG keys |
| colorvar | 528x384, 1 PNG (colour strip) |
| **by(foreign)** GridPlot fixed the same way | 528x384 shell with **no content**: 8 paths, 0 texts. The panels laid out 0 px wide. |

Conclusion:
- The in-page fix-up works for a lone figure.
- For by() and other multi-cell graphs, the harness should let dash size the graph. Once P1-5 / P10 VF-4 land (fixed `width`/`height` when `xsize()`/`ysize()` are given), the harness appends `xsize(W) ysize(H)` (W x H = the twoway SVG's own `width`/`height`, `7.500in`x`4.500in` under stcolor) to both the twoway and the dash runs, and shows the original command in the caption.
- Until then, by() can be exported at its natural size with the viewport width set so the grid is W px wide (`Emulation.setDeviceMetricsOverride`, then `export("svg")` of the grid), and the SVG wrapped in an outer `<svg viewBox>` scaled into W x H (letterboxed).

### 1.4 Recommended export procedure for the harness (WP-33)

1. Build the example's page with dash, as now.
2. Copy it for the harness. Optionally rewrite every figure's `output_backend` to `"svg"` in the copy's doc JSON, which makes legend keys vector (measured). Do not touch shipped text.
3. Open it with `RangeProbe` (`--disable-gpu`, so WebGL is off and GL glyphs export as vector).
4. Apply the size step from 1.3. Wait for `Bokeh.documents[0].is_idle`, and allow about 2.5 s when TeX is present (MathJax is async).
5. Evaluate `Bokeh.index.find_one(m).export('svg').ctx.get_serialized_svg(true)` with `awaitPromise`.
6. Post-process: drop the duplicate `fill="none"` texts, renumber ids, and strip nothing else.
7. Measured cost: about 1.5 s per example after Chrome start. One Chrome per batch of examples.

---

## 2. Verdict machinery (Q18: geometry first, image score second)

### 2.1 Geometry

- **twoway side: already built, stdlib only.**
  - `scripts/svg_truth.py` (686 lines; the plot region, ticks and labels, each axis's pixel-to-value calibration, the U+00A0 rule), `svg_layer.py` (every drawn element and marker shape), `svg_text_runs.py` (styled runs: weight, style, family, size, level), `svg_scheme_visual.py` and `svg_chrome.py`.
  - Each has a pytest module. Stata's SVG is flat (`<rect>`, `<line>`, `<circle>`, `<text>`, `<polyline>`/`<path>`, inline `style=`, `viewBox 0 0 5400 3240` at 720 units per inch, e.g. `test/fixtures/svg_truth_smoke.svg`), so `xml.etree` is enough.
  - svgelements (MIT, pure Python, 138 kB, last release 1.9.6, Aug 2023; text is a stub with no font engine) and svgpathtools (MIT, needs numpy/scipy) add nothing Stata's dialect needs.
- **dash side: read the live BokehJS views, not the exported SVG.** Bokeh's SVG writes markers as anonymous paths in a clipped matrix soup, while the views hold the data. One JS dump per example, in the same session as the export, collects:
  - each axis view's `tick_coords` and labels (see `test/test_default_axes_chrome.py:49-50`);
  - title, subtitle, note and caption texts and bboxes;
  - `Legend.items` labels and their renderers' glyph types and colours;
  - per renderer, the glyph type, row count (`data_size` after the view filter) and data extents;
  - fill and line colours and widths from the glyph models;
  - `frame.bbox` and the figure bbox.
- Compare in data space, mapping the twoway side through `svg_truth`'s axis calibration:
  - ticks: values and labels;
  - titles: text plus relative position;
  - keys: order and text;
  - glyph counts and extents;
  - colours: to the nearest named Stata colour.
- Known differences go to the ledger the corpus already plans.

### 2.2 Image similarity

`$SCRATCH/r3/exp_ssim.py`. The smoke command from `svg_truth_smoke.json`, auto.dta read with pandas, was drawn by dash. Both SVGs were rasterised by **Chrome** onto a 720x432 white canvas (`img` → `drawImage` → `toDataURL`). Measured:

| Pair | SSIM (Gaussian sigma 1.5, as Wang 2004) |
|---|---|
| twoway vs dash (different scheme/legend/ticks in this ad-hoc spec) | 0.7785 (numpy) = 0.7785 (scikit-image 0.25.2) |
| dash SVG raster vs dash canvas export | 0.9977 |
| twoway SVG: Chrome raster vs rsvg-convert 2.56.3 raster | 0.9946 |

The numpy implementation (about 15 lines with `scipy.ndimage.gaussian_filter`, in the experiment file) equals scikit-image's to 4 dp. scipy is already in both Pythons. SSIM is a weak, global signal: a picture with the legend in the wrong place still scores about 0.78. Keep it secondary, as Q18 says, and report it with its two components (the luminance and structure maps) only for triage.

| Rasteriser / scorer | Licence | Install friction | Note |
|---|---|---|---|
| **Chrome (existing harness)** | n/a | none | Same engine for both SVGs, which removes engine noise. Fonts are the system's. |
| resvg-py 0.5.0 (Aug 2026) | page states none (resvg itself is Apache-2.0/MIT) | wheels about 1.2-1.7 MB, abi3 cp310+, mac arm64 | Fast; its own text engine, so fonts differ from Chrome. |
| cairosvg | LGPL-3.0 | needs the native cairo library (Homebrew/conda), not bundled | Avoid. |
| rsvg-convert (librsvg, LGPL-2.1) | system/conda binary | present only in conda here | Useful as a cross-check only. |
| scikit-image 0.25 | BSD-3 | only in anaconda; about 13 MB plus networkx, tifffile, imageio, lazy_loader | Not needed. |
| **numpy+scipy SSIM** | BSD | already installed | **Recommended.** |

**Recommendation:**
- geometry from `scripts/svg_*.py` and a BokehJS view dump;
- image score from Chrome rasters and numpy/scipy SSIM;
- **zero new dependencies**;
- verdicts: Same = no geometry difference outside the ledger; Close = only ledger or tolerance differences (e.g. text width within 2 px); Differs = otherwise;
- SSIM printed as information and never decides a verdict alone.

---

## 3. Firefox and WebKit headless runs (Q32)

What the DevTools tests use today (13 modules through `RangeProbe` and `_CspProbe`, `test/test_csp_browser.py:183-280`):
- `Runtime.evaluate` (with `awaitPromise`), `Page.navigate`, `Page.addScriptToEvaluateOnNewDocument` (the CSP violation listener), `Browser.setDownloadBehavior`;
- the events `Runtime.exceptionThrown` and `Runtime.consoleAPICalled`;
- `Page.captureScreenshot`.

### 3.1 Firefox: WebDriver BiDi, measured

- Firefox removed CDP in 141 ([Mozilla](https://fxdx.dev/cdp-retirement-in-firefox/), [Selenium](https://www.selenium.dev/blog/2025/remove-cdp-firefox/)).
- `$SCRATCH/r3/exp_firefox_bidi.py` starts `firefox --headless --no-remote --profile <tmp> --remote-debugging-port N` and connects tornado's `websocket_connect("ws://127.0.0.1:N/session")`. It then runs `session.new`, `session.subscribe(log.entryAdded)`, `browsingContext.create(tab)`, `setViewport`, `navigate(wait=complete)`, `script.evaluate(awaitPromise)`, `captureScreenshot` and `browser.close`.
- Result: connected in 0.8 s; the whole run took 5.8 s. It ran the same `export("svg")` JS (results in 1.2) with no console errors. WebGL2 is on.
- Gotcha: Firefox 157's initial `about:home` context refuses `setViewport` ("System access is required ... -remote-allow-system-access"). Create a new tab context instead.
- `/usr/local/bin/geckodriver` is a 2017 x86_64 build that prints nothing on `--version`. It is not usable and is not needed.
- The CDP to BiDi mapping is 1:1 for what the tests use:

| CDP | BiDi |
|---|---|
| `Runtime.evaluate` | `script.evaluate` / `script.callFunction` (results come back as BiDi remote values; return `JSON.stringify` strings as now) |
| `Page.addScriptToEvaluateOnNewDocument` | `script.addPreloadScript` |
| `exceptionThrown` / `consoleAPICalled` | `log.entryAdded` (`type: "javascript"` / `"console"`) |
| `Page.captureScreenshot` | `browsingContext.captureScreenshot` |
| `Browser.setDownloadBehavior` | `browser.setDownloadBehavior` (in the spec; **not verified on Firefox**). The SVG tests already capture blobs in-page (`_CAPTURE_JS`) rather than download, so they do not need it. |

### 3.2 WebKit

- Safari 26.5 has **no headless mode**. `safaridriver` needs a one-time `safaridriver --enable` (admin; a system setting, so the maintainer does it) and drives a visible Safari window, one session at a time. It is not suitable for an unattended tier.
- **Playwright** ships a patched WebKit build that runs headless on macOS 14+ ([system requirements](https://playwright.dev/python/docs/intro)). Its WebKit is "derived from the latest WebKit main branch", so it is not Safari ([browsers](https://playwright.dev/python/docs/browsers)).
- Facts:
  - playwright 1.64.0: uploaded 13 Oct 2026; Apache-2.0; Python 3.10+; macOS arm64 wheel 43.0 MB (bundles its Node driver).
  - `playwright install firefox webkit` downloads about 187 MB + 180 MB into `~/Library/Caches/ms-playwright`; `PLAYWRIGHT_BROWSERS_PATH` relocates it.
  - The browsers must be re-downloaded on each Playwright upgrade. There is no documented offline installer beyond `PLAYWRIGHT_DOWNLOAD_HOST` or a pre-filled cache directory, so a release run is offline only after a first online install.
  - Pin a version at least two weeks old (1.63.x today).
- Playwright's CDP session works on Chromium only. It drives Firefox through its own patched-Firefox protocol, not the user's branded Firefox.

### 3.3 Route (recommended)

- Generalise the probe into one small interface, `BrowserPage`: `eval(js)`, `eval_async(js)`, `add_init_script(js)`, `screenshot()`, `errors()`, `console()`, `close()`. Implement it three times:
  1. **ChromeCdp**: today's `RangeProbe`/`_CspProbe`, unchanged.
  2. **FirefoxBidi**: the 3.1 client, about 150 lines, tornado only. It drives the Firefox users actually run.
  3. **WebKitPlaywright**: `playwright.sync_api` with `page.evaluate`, `page.add_init_script`, `page.on("pageerror")`, `page.on("console")` and `page.screenshot`. Imported lazily, so the module skips cleanly when Playwright is absent, and that skip is red under `DASH_STRICT=1`, as the Chrome tier does now.
- Parametrise the CSP, browser and accessibility test classes over the available engines with `@pytest.mark.release`. axe-core injects the same way into all three.
- Dependencies:
  - only `playwright` in the dev/test lock (Q19), plus its WebKit download;
  - Firefox and Chrome are the installed browsers.
- Alternative (one dependency path, simpler to explain): Playwright for both Firefox and WebKit. The cost is that the tested Firefox is Playwright's patched build, not the release Firefox.

---

## 4. Bokeh capability check, packages 6-10 (plus P1-5 and P2 WebGL)

### 4.0 Conventions and measured facts used below

- **3.8 vs 3.9**: none of the models or properties named below differs between the versions. The exceptions are `*_text_outline_width` on Axis, Legend, Title and Label, plus `Markdown`, `Tabs.link_layouts` and `Step.pad_*` (3.9 only); none is needed. So "3.8 = 3.9" unless a row says otherwise. Measured with `props.py`; `p38.json`, `p39.json`.
- Available in both versions:
  - `Scatter.defs` custom markers (`B8/models/glyphs.py:1487`, `B9:1488`). In SVG export, use the paint-directly form: the `Path2D`-return form throws "not implemented" in Bokeh's SVG context (js9:15091-15613 region).
  - `HTMLLabel`, `HTMLLabelSet`, `HTMLTitle`. These print markup literally: measured, `<b>` shows as text.
  - `TeX`, `MathML`, `PlainText`.
  - `Node` coordinates for `BoxAnnotation`/`Label`. `Label.anchor`, `.padding` and `.border_radius`.
  - `Slope`, `ScaleBar`, `CustomJSTicker`, `CustomJSTransform`, `CustomJSExpr`.
  - `Title.padding` and `text_line_height`.
- Multi-line text: TextBox splits on `"\n"` (js9:28690-28784) for titles, axis labels and Labels.
- `line_dash` is `DashPattern` = integers only (`B9/core/property/visual.py:65`). Sub-pixel dash lengths cannot be expressed. This is a residual, not a listed item.
- Legend keys: each LegendItem's renderers draw overlaid in one `glyph_width` x `glyph_height` box (default 20; `_paint_glyphs` js9:39793 / js8:39741).
  - markers at `0.4 x min(box)`, angle ignored (`_get_legend_args` js9:54240-54250 / js8:54107);
  - line glyphs: a full-width horizontal line (`generic_line_*_legend` js9:33642 / js8:33613);
  - area glyphs: a rect inset 10% with fill + line (js9:33673 / js8:33644);
  - a renderer with **0 rows draws no key** (`draw_legend` js9:32124 / js8:32092). Legend-only renderers need a 1-row source with NaN coordinates.
- "Composite" = several shipped glyphs, labels and boxes making one twoway element. That includes a **key cell**: a small bare `Plot` holding Quad/Scatter/Segment glyphs, Labels and an Axis. dash already builds such cells for by() (`dash_by_*`).
- Verdict "yes" covers rows that are parsing, rc or computation work with no Bokeh drawing limit. Their sketch says so.

### 4.1 Package 6: by() fidelity (20)

| Item | Verdict | Bokeh means | Sketch |
|---|---|---|---|
| BY-28 contour cuts shared across panels | yes | one `LinearColorMapper`/palette and one level list for every panel's `contour()` | compute the cuts over all panels (and Total) once in Python and in the JS refit; pass the same levels to each panel |
| BY-1 note/caption/subtitle ring(0) dropped | yes-as-composite | `Title`/`Label` in by() chrome cells, or `Label(x_units/y_units="screen")` in the panel array's cell | draw them inside the panel array at their clock position |
| BY-2/29/11 outer scale() vs by(,scale()) | yes | font/size multipliers on every model | ignore the outer scale() under by(); apply by(scale()) through `_dash_apply_scale` to all cells |
| BY-27 function range(varname) per panel | yes (computation) | per-panel CDS | min/max per panel inside the panel loop, both modes |
| BY-3 at() hole not reserved | yes | GridBox/gridplot cell (`None` or a Spacer) | return the at() cell whenever at() is given |
| BY-4 compact vs style(); compact outlines | yes | `Plot.outline_line_*`; panel-label `Title.border_line_*`, `background_fill_*` | apply compact only without style(); expand its special options into outlines |
| BY-5 aspectratio + shrink accepted | yes (rc) | none | refuse in twoway's words |
| BY-6 by(,total) without varlist rc | yes (rc) | none | r(100) "varlist required in by()" |
| BY-12 by(l1title() b1title() ...) | yes | `Title` (left/below/right/above) on the by() grid's side cells | draw the eight edge titles; l1/b1 replace the shared axis titles |
| BY-13 legloc/clegloc/plegend/plegloc | yes | Legend / ColorBar placed in a grid cell | merge into the existing cell placement; plegend = a plot Legend cell |
| BY-14 coloruseplegend under by() | yes-as-composite | stepped `ColorBar` (see CV-8), or a key cell | draw twoway's colour-bar key instead of a discrete Legend; drop "(missing)" |
| BY-10 panel-label sub-options (justification, nobexpand, lwidth/lpattern, span, alignment, linegap, bmargin, placement, orientation) | yes-as-composite | panel label as its own bare `Plot` cell: `background_fill`, `outline_line_width/dash`, a `Label` with `text_align`, `text_baseline`, `text_line_height`, `angle`; the cell width (span/nobexpand) | the label cell's box draws the expanded or unexpanded box; the Label positions the text |
| BY-16/17 date panel labels raw; quoted value labels split | yes | Title text | write the raw value (14610); split quoted parts into "\n" lines |
| BY-18/19/20/21 documented layout (combine grid, clock 3/9 beside, per-region aspect, margin inset) | yes-as-composite | GridBox rows/cols; Title in left/right cells (horizontal Label for beside); `frame_width`/`frame_height` per panel (the P1-5 V1 sizing); `min_border_*` | port combine's regions; beside-panel placement through side cells; aspect on each frame |
| VF-6 first-column panels narrower | yes | equal `min_border_left` on every panel, y labels in an outer Axis-only cell | fix the left border to the widest label width (measured once in JS) for all panels |
| GW-5 overhangs under by() | yes (computation) | `min_border_*` | skip under by(); measure only the end labels |
| sil:SD-7 all-zero weights per panel | yes (rc) | none | apply the check per panel |
| PIC-13 hole legend not scaled 0.85 | yes | `Legend.label_text_font_size`, `glyph_*` | multiply by by()'s size factor |
| BY-7/15 legend(pos(abc)) note; bgcolor | yes | none / `background_fill_color` | twoway's clockdir note with its fallback; bgcolor silent or drawn |
| TR-19 unfiled residuals | yes (tracking) | none | open BUGS entries |

### 4.2 Package 7: colorvar (17)

| Item | Verdict | Bokeh means | Sketch |
|---|---|---|---|
| CV-8 gradient instead of binned at z ticks | yes-as-composite | glyph colour from a precomputed **bin-index column** through `LinearColorMapper(palette=k colours, low=-0.5, high=k-0.5)` (or a `CategoricalColorMapper`); key = `ColorBar` on that mapper with `FixedTicker` at the bin edges and `major_label_overrides` = cut values. Fully vector alternative: a key cell of Quads + LinearAxis. | route every type through the stepped mapper lines already use. Note that the ColorBar strip is a PNG in SVG export and may smooth between steps when scaled; the key cell avoids that. |
| CV-1 colorfillonly strips line colour | yes | keep `line_color` mapped on line glyphs | map `line_color` with the transform on line, connected, spike and pc shafts/heads |
| CV-3 discrete/binned clegend form | yes-as-composite | key cell: Quad swatches (the type's key swatch), `LinearAxis` with `FixedTicker`, highest level at top | twoway's axis-style key; no "(missing)" entry, no frame |
| CV-4 coloruseplegend key order and labels | yes | `Legend.items` order and labels, `title=None` | descending levels + "Other", display-format numbers; legend() not applied |
| CV-2 colordiscrete colorlevels(k) cuts | yes (computation) | none | k cuts at range/(k+1), with minmax |
| CV-5 legend(size/rows/cols) restyle the key | yes | separate Legend/ColorBar objects | exclude colour keys from legend()'s grid and size steps |
| CV-6 two colorvar layers | yes | one ColorBar + a plot Legend | key from the last colorvar layer; keep plot-legend items |
| CV-7 plot-legend swatch takes row 0's colour | yes-as-composite | a legend-only `GlyphRenderer` (1 NaN row) in the pstyle colour as the LegendItem's renderer | proxy swatch |
| CV-11/12 colorkeysreverse; single-value levels | yes | palette order; mapper low/high | reverse colours only; zero-width cuts |
| CV-9 refusal rc/words | yes (rc) | none | twoway's rc and line; refuse wildcards |
| CV-10 malformed clegend/plegend/zlabel/zscale | yes (rc) | none | route through the refusal checks |
| CV-14 documented acceptances | yes (policy) | none | keep or refuse, per P11 |
| CV-15 zlabel/zscale on a discrete key; clegend altaxis, region(), bplacement(), bmargin(), subtitle/note/caption | yes-as-composite | key cell: `LinearAxis` on the left or right (altaxis), cell `background_fill`/`outline_line_*` (region), Titles above/below (subtitle/note/caption), `min_border` (bmargin), cell position (bplacement) | draw on the key cell once CV-3 exists |
| LT-12 clegend(title()) textbox | yes | `ColorBar.title` + `title_text_*`, or a `Title` on the key cell | parse as a textbox; draw above the key, keeping ztitle |
| AX-12 z tick family (zticks, zmlabels, zmticks) | yes-as-composite | `ColorBar` has **no minor ticker** (`ColorBar.minor_ticker` absent in both); key-cell `LinearAxis` has `FixedTicker(ticks, minor_ticks)` and `major_label_overrides` | accept the plurals; draw on the key cell |
| sil:SD-4/14 colour-bar width; scheme contour keys | yes | `ColorBar.width`/`height`, `bar_line_*`, palette order, levels | read clegend_width/height and the four contour keys |
| LT-22 contourline colorlines legend; key title/axis line | yes-as-composite | Legend items per level (Line renderers); key-cell axis line (`axis_line_*`) | build the level legend under colorlines; drop the note |

### 4.3 Package 8: legend, titles and added text (25)

| Item | Verdict | Bokeh means | Sketch |
|---|---|---|---|
| LT-1 legend title/subtitle styles | yes | `Legend.title_text_font_size/color/style`; a subtitle as a second line or a Title in the legend cell | style from textbox_style('leg_title'/'leg_subtitle') |
| LT-4 ring(0) bplacement | yes | `Legend.location` (compass or `(x, y)` screen px from the frame's bottom-left) | map bplacement and its compass abbreviations to location |
| LT-2 nobox is the key-text textbox | yes | keep `border_line_*`/`background_fill_*` | treat box/nobox as the key-text box; flip the test |
| LT-3 key-text textbox options (box, bcolor, fcolor, justification, alignment, margin, linegap, tstyle) | yes-as-composite | Legend labels have no box: key cell with one `Label` per entry (`background_fill_*`, `border_line_*`, `padding`, `text_align`, `text_baseline`, `text_line_height`) | draw keys in a key cell when any textbox option is given |
| LT-5 legend(all), draw/nodraw | yes (logic) | Legend `visible`, items | honour all (skip the merge), draw and nodraw |
| LT-6 style(), width(), height(), xoffset/yoffset, showindex, region(style/lstyle/lalign) | yes-as-composite | `Legend.margin`, `padding`, `location` tuple, `label_width`, `border_line_*`; fixed width/height and inside stroke alignment = key cell + BoxAnnotation inset by w/2 | implement on Legend; key cell for width/height/lalign |
| LT-7 bexpand on legend and titles | yes-as-composite | `BoxAnnotation` with `Node` canvas or frame coordinates spanning the width, behind a Title/Label | draw the expanded box |
| LT-8 title box fill under stcolor | yes | `Title.background_fill_color`, `border_line_*` | take fill and line from the textbox style |
| LT-9 fractional ring() | yes (logic) | order of `above`/`below` panels | parse ring as real 0-100; order by value |
| LT-10 numeric marginstyles | yes | `Title.padding`/`Legend.padding`/`margin` accept per-side tuples | route through `_dash_margin_sides` |
| LT-11 text(alignment()) | yes | `Label.text_baseline` | pass alignment through `_dash_at_canon` |
| LT-13 legend(t1title()...) accepted | yes (rc) | none | drop them from both legend tables |
| LT-14 title(ring(x)) accepted | yes (rc) | none | twoway's notes, then r(198) |
| LT-15 legend title/subtitle sub-options | yes-as-composite | `title_location`, `title_standoff`, `title_text_*`; a boxed legend title = Label/Title in the key cell | apply or name |
| LT-16 title placement() at ring(0) | yes | `Label(x_units/y_units="screen")` with `anchor` (both versions) at the frame's inside compass point | place the box at twoway's point; fixture |
| LT-17 legend(holes()) with cols(1) | yes-as-composite | `LegendItem(label="", renderers=[NaN-row renderer])` as a hole | mirror legend_g's hole placement |
| LT-18/ST-18 title box orientation/width/height/angle/lstyle/bl*/lalign/style; clocks 2-4/8-10 | yes-as-composite | rotated or fixed-box titles = `Label(angle, x_units="screen")` in the border plus a BoxAnnotation (Node coords) for width/height; `Title` on the left/right sides for beside placement | draw them, or name the rest |
| LT-19 edge titles: box, justification, margin, tstyle | yes | `Title` props (`align`, `padding`, `background_fill_*`, `border_line_*`) | reuse `_dash_textbox_style` |
| LT-20/GW-21 text() width/height/linegap/bexpand/bmargin/lstyle/lpattern/lalign; `=exp` | yes-as-composite | Label + BoxAnnotation (fixed box; `line_dash`); `text_line_height`. `=exp` is Stata-side | draw a fixed-size multi-line box with a dashed frame; evaluate `=exp` in Stata |
| LT-21/VF-8/PIC-14 key marker size; textfirst, stacked, symplacement; legend note/caption; 384 px clipping | yes-as-composite | Bokeh Legend: key size is fixed at 0.4 of the box, glyph always before label. So use a **key cell** (Scatter at the true marker size, Labels left or right or below, Titles for note/caption); clipping: `ncols` and `label_width` | custom legend in a key cell when these options are given or a marker key is involved; a TapTool + CustomJS can restore click-to-hide |
| PIC-11 key shapes (rcap, rcapsym, pccapsym, dropline, pcarrow, pcbarrow, rarea) | yes-as-composite | see section 6 | legend-only renderers in twoway's shapes |
| MS-10 keys merged across look-alike pstyles | yes (logic) | separate LegendItems | merge only by the same resolved p# |
| ST-14 partial SMCL markup | yes-as-composite | see section 5 | positioned runs |
| LT-24 title("'90s") accepted | yes (rc) | none | by design, or emulate r(100) |
| RH-13 horizontal kdensity keyed by name | yes (logic) | LegendItem label | key by the grid name under yxswitch |

### 4.4 Package 9: axes (21)

| Item | Verdict | Bokeh means | Sketch |
|---|---|---|---|
| AX-13 axis-title orientation/justification/placement/box/margin | yes-as-composite | `Axis.axis_label_orientation` ('horizontal'/'vertical'/'parallel'/'normal'/radians), `axis_label_align`, `axis_label_standoff`; a boxed title = hide `axis_label` and draw a Label + BoxAnnotation in the border | draw orientation, margin and justification on the Axis; box through the composite |
| AX-5 xlabel(custom) styles; empty custom | yes-as-composite | a second styled tick set: `LabelSet` (x data, y `screen`) + a `Segment`-free tick via a second `LinearAxis` with `FixedTicker`, or `major_label_overrides` per value; own `Grid(ticker=FixedTicker)` | custom ticks as their own styled overlay; refuse the empty form (rc) |
| AX-6 xtick/xmtick gridlines in the major style | yes | `Grid(ticker=FixedTicker(ticks=...))` with `grid_line_*` of the tickset's gridstyle | use the tickset's gridstyle |
| AX-7 yscale(off fill) | yes | Axis kept with `axis_line_alpha=0`, `major_label_text_alpha=0`, tick lines alpha 0 | keep the border space |
| AX-8 labelminlen, show/noshowlabels, pgmgrid, style() | yes | `major_label_text_alpha`, `Grid.visible`, `CustomJSTickFormatter` (padding) | map them; pad for labelminlen |
| AX-9/sil:SD-5 atanh, logit, log1m, style() drawn linear | yes-as-composite | no such Bokeh scale. Draw on transformed coordinates (`transform(field, CustomJSTransform)` so filter moves still work), `FixedTicker` at transformed tick positions, `major_label_overrides`/`CustomJSTickFormatter` for the original values | transformed-space axis |
| AX-10 contradictory transforms accepted | yes (rc) | none | opts_exclusive within one copy |
| AX-11 log axis over non-positive data | yes (policy) | `LogScale` | natscale over finite values then drop <= 0, or document twoway's degenerate picture |
| AX-14 tstyle/labstyle/gstyle/tlstyle/glstyle; nogextend | yes | Axis/Grid style props; **`Grid.bounds`** for nogextend | read the style files; Grid bounds = the tick range |
| AX-15/17/19 one tick length for xtick+xmtick; out-of-range reflines clipped; string/hex formats; dates past the browser range; margin fixed at build | yes-as-composite | `major_tick_out`/`minor_tick_out` (separate), an extra Axis for a third length; reflines past the frame = `Segment`/`Arrow` annotations in canvas units recomputed by CustomJS on frame change (Span and glyphs clip); formats via `CustomJSTickFormatter`; **dates past ~275760** need a `LinearAxis` + own calendar arithmetic in `CustomJSTickFormatter` (DatetimeAxis uses JS Date); margin = CustomJS updating `min_border_*` | case by case; the date one is the heaviest |
| AX-18/stat:PT-20/VF-12 number labels where twoway does; log date axis | yes | `LinearAxis` (numbers) instead of DatetimeAxis; `LogAxis` + `CustomJSTickFormatter` for dates | follow twoway's rule; log date axes |
| MS-14 log axis range end adds a tick | yes (computation) | `FixedTicker` | do not add range ends to log default ticks |
| MS-12 only plot on yaxis(2) gets y gridlines | yes | `Grid.visible` per axis | keep axis k's grid default when renumbering |
| MS-11/RH-17 '<first title>...' x title | yes (logic) | `axis_label` text | measure and apply the rule in both modes |
| MS-13 ytitle suffix copies on separate lines | yes | `axis_label` with "\n" (TextBox splits lines, js9:28690) | join copies with newlines |
| PIC-12 right y title reads downward | yes | `Axis.axis_label_orientation` = the radian angle that reads upward on a right axis | set it on right axes; pin with a pixel or bbox test (sign convention measured in the pin) |
| DG-6 %tC leap seconds | yes (computation) | `FixedTicker` + `CustomJSTickFormatter` | shift Stata's tick values; label with %tC |
| DG-4 parenthesised dates with blanks | yes (parse) | none | tokenise datelists binding parentheses |
| DG-9/TR-8 non-numbers in label lists | yes (rc) | none | refuse in twoway's words |
| DG-13/11 ylabel(minmax) on an empty scale; ±8e307 overflow | yes | `FixedTicker(ticks=[])` | no ticks on an empty minmax axis; guard `10**z` |
| natscale after a move (open entry) | yes (computation) | `FixedTicker` updated in the CustomJS refit; served refit in Python | refit the model, or ask Stata where it is available |

### 4.5 Package 10: schemes, styles, figure geometry (14)

| Item | Verdict | Bokeh means | Sketch |
|---|---|---|---|
| PIC-4 economist note never painted | yes | `Title(text, ...)` in `below`/`above`, or a `Label` in `screen`/`canvas` units (not a Title node target) | place it in a painted row; pixel test |
| PIC-7/8 economist widths; rarea outline | yes | `line_width` per renderer; inner alignment = inset (see P15) | route widths through p#other and rarea through p#area |
| ST-1..6/11 style-word abbreviations and names | yes (parse) | none | one reader per class following `_unabbrev` |
| ST-7 leaf style files on the ado-path | yes (parse) | none | extend the style-file walk |
| ST-15/GW-18 color-*.style, textboxstyle-*.style | yes (parse) | colour strings | read them with the other classes |
| ST-17 scheme directives not drawn (clockdir p, title textboxstyle, legend_col_gap, title clocks 2-4/8-10) | yes-as-composite | `Legend.spacing` is one gap for rows and columns, so a separate column gap = `label_width` padding or a key cell; side-clock titles via Label in the border | draw the directives |
| ST-10 shipped-name scheme before BASE | yes (Python) | none | rank shipped translations at BASE's position |
| ST-16/GW-17 unknown scheme() | yes (policy) | none | note and draw s2color |
| GW-6/VF-7 graph-region outline; 3.5-unit margin | yes-as-composite | no Plot property strokes the outer border: `BoxAnnotation(left=Node(canvas.left)...)` (Node in both) inset by w/2, `fill_alpha=0`; margin via `min_border_*` | stroke from the scheme's graphregion line; add the margin |
| ST-21/GW-19 graphregion inner box, lalign, ifcolor, plot margin share | yes-as-composite | `border_fill_color` (outer), a BoxAnnotation with Node coordinates (inner box and fill), frame-based `min_border` | inner BoxAnnotation; compute the margin on the frame |
| VF-4/GW-20/sil:SD-21/VF-5/VF-11 figure proportions; unit 2.88 pt; fxsize/fysize | yes | `sizing_mode="fixed"` + `width`/`height` (measured, P1-5 V1), or `sizing_mode="scale_width"` + `aspect_ratio` to keep the shape while filling the width | let the requested ratio win; scale the unit to the scheme's graphsize; state the band values |
| GW-1 xsize/ysize with units | yes (parse) | none | parse in/pt/cm |
| ST-22 navy*52 intensity rule; blank stylelist element | yes (computation, rc) | colour string | match the clamp; reword the refusal |
| GW-10 graph set fontface | yes | `*_text_font` (CSS family, needs the font on the viewer's machine) | measure, then apply the default face |

### 4.6 P1 item 5: aspectratio() with xsize()/ysize()

Measured with `$SCRATCH/r3/exp_aspect.py` on real `DashRenderer` pages; 3.8 and 3.9 gave identical numbers.

| Case | V0 today (model: `sizing_mode="fixed"`, width/height = defaults 600/600, `frame_*` set, `min_height`/`max_height` = 160/560, `aspect_ratio` = 2) | V1: `width,height` = box, `min_height`/`max_height`/`aspect_ratio` = None | V2: width/height None, sizing_mode None |
|---|---|---|---|
| aspectratio(2) xsize(8) ysize(4) | host 600x560, canvas 767x384, **frame 0x510**, **E-1023** | host 768x384, frame 168x334 (ratio 1.99), no message | re-stretched to 1200 wide; frame 600x334 (frame_width ignored) |
| aspectratio(1) xsize(8) | host 600x560, frame 166x510, E-1023 | 768x384, frame 334x334 | frame 766x334 |
| aspectratio(.5) xsize(6) ysize(3) | host 600x560, frame 500x510, E-1023 | 576x288, frame 476x238 | frame 1100x238 |

Why each symptom appears:

- **E-1023** is Python-side validation at serialisation, `_check_min_preferred_max_height` (`B9/models/layouts.py:321-328`, `B8:323-331`). With `sizing_mode == "fixed"` the preferred height is `self.height` (the figure default, 600), which exceeds `max_height` 560, so the error is logged as "Expected min_height <= height <= max_height".
- **0 px plot**:
  - BokehJS sizes the host from width/height. Fixed policy gives 600, and `max_height` clamps it to 560.
  - The plot's inner CSS grid is laid out as `left px | frame_width px | right px` and `top | frame_height | bottom` (`PlotView._measure_layout` js9:45007-45023 / js8:44880-44896; `center_panel.set_sizing` js9:44917-44921).
  - The canvas follows the grid (767x384), while the frame's measured bbox follows a host that disagrees with it.
  - The leftover `aspect_ratio=2` also acts on the fixed box (`box_sizing` js9:44736-44744 / js8:44609-44617).
  - For ar 2 the frame column collapses to 0.
- **Fix** (V1), in `_dash_frame_sizes` (`dash_render.py:27650-27677`):
  - set `fig.width, fig.height = round(width), round(height)`;
  - set `fig.min_height = fig.max_height = None` and `fig.aspect_ratio = None`.
  - The page height bound is already applied to the box in `_dash_apply_frame_aspect` (`:27693-27697`).
  - Pin it with a headless frame-size and ratio test, and assert that the render's bokeh log has no `E-10`/`W-10` line. The experiment captures it with a handler on the `bokeh` logger.
  - A fixed figure does not shrink on a phone. D41 forbids only a 0 px plot; say in the help that such a graph scrolls sideways in a narrow cell.

### 4.7 P2 WebGL

- **Which glyphs have WebGL** (a `load_glglyph` exists): Line, Step, MultiLine, Scatter, Circle, Rect, the LRTB family (Quad, VBar, HBar, Block), HexTile, Ngon, Annulus, AnnularWedge, Wedge, HStrip, VStrip, Image, ImageRGBA and ImageStack. Source: js9 lines 32247-55449 and the `bokeh-gl.js` module list, identical in 3.8.
- **Everything else always paints on canvas, even on a webgl figure**: Patch, Patches, VArea/HArea (and Step variants), Segment, Ray, Bezier, Quadratic, Arc, Ellipse, MultiPolygons, Text and MathText glyphs, and all annotations (Band, Whisker, Arrow, Span, BoxAnnotation, Label, Legend, ColorBar). `GlyphView.paint` uses GL only when `has_webgl()` (js9:32500-32509 / js8:32470).
- **Per-renderer backend: no.** `output_backend` and `hidpi` are on `Plot` only; `GlyphRenderer` has no backend property (checked, both versions).
  - The only implicit per-renderer canvas route: a glyph type without GL, or a Scatter whose marker is a custom `defs` marker (`ScatterView._compute_can_use_webgl` js9:54044 / js8:53911).
  - No shipped non-GL glyph strokes an open polyline as one path: Segment and Bezier restart the dash per segment; Patch closes. `Spline` exists in BokehJS only (js9:54792) and has no Python model.
  - **So Q34's "dashed lines stay on canvas" means the whole figure stays on canvas when any Line, MultiLine or Step renderer has a non-solid `line_dash`.**
- The row count for the switch is dash's own computation (rows drawn, not `len(self.df)` at `dash_render.py:63396`).
- **Dashed lines under WebGL, measured** (`$SCRATCH/r3/exp_webgl_dash.py`; ink IoU of the webgl rendering against the canvas rendering of the same line, 500x200 px):

| 20,000 vertices | 1px dashed | 4px dashed | 8px dashed | 4px dotted | 4px dashdot | 4px solid |
|---|---|---|---|---|---|---|
| GPU (ANGLE Metal, M2 Max) | 0.615 | 0.758 | 0.801 | **0.435** | 0.685 | 0.917 |
| SwiftShader | 0.565 | 0.844 | 0.859 | 0.553 | 0.767 | 0.961 |

- At 400 vertices the GPU IoUs were 0.66-0.90 and solid was 0.92. So the break-up grows with vertex density and is real on GPU WebGL, not only SwiftShader (DG-14's "unverified on GPU" is settled).
- 3.8 gave identical GPU numbers.
- **Browser flags matter:**
  - Every existing probe passes `--disable-gpu`; under Chrome 155 that means **no WebGL at all**: `getContext('webgl2')` returns null and Bokeh's `canvas_view.webgl` is null.
  - So `test_export_svg.py::test_a_webgl_figure_exports_as_vector` passes only because WebGL is off. With WebGL on (Firefox), GL glyphs export as raster `<image>`.
  - The WebGL-vs-canvas pin must launch Chrome **without** `--disable-gpu` (GPU) or with `--disable-gpu --enable-unsafe-swiftshader` (SwiftShader, CI-stable). Both were measured working.
  - Pin assertion: a dashed figure above the threshold is emitted with `output_backend` absent or `"canvas"`, and its drawn ink matches a canvas reference with IoU >= 0.95.

### 4.8 Items judged not supported, and residuals worth a sentence under Differences anyway

- **None of the 97 bullets is "no"** under the maintainer's definition.
- The composites that leave a visible or behavioural residual, which planning may still want documented:
  1. **ST-14**: mixed runs in the plain-font route are exact but heavy (section 5). The light TeX route draws in MathJax's TeX fonts, not Helvetica.
  2. **AX-15 dates past the JS Date range**: needs dash's own calendar arithmetic in a formatter (not a Bokeh limit, but new JS to maintain).
  3. **LT-21 / LT-3 / PIC-11 key cells**: replacing Bokeh's Legend loses its built-in click-to-hide unless rebuilt with TapTool + CustomJS.
- Outside the packages: `line_dash` takes integers only, so sub-pixel pattern lengths cannot be drawn; this sits with P15's dot-pattern items.

---

## 5. Partial SMCL markup ({bf:}, {it:}, {sup:}, font tags) in titles, labels and keys

Measured with `$SCRATCH/r3/exp_text.py` (both versions, screenshot `txt39/screen.png`).

| Route | Titles | Axis titles | Tick labels | Legend entries | Added text | In SVG export |
|---|---|---|---|---|---|---|
| `TeX(...)` | yes (`Title(text=TeX(...))`; `figure(title=TeX)` is refused by the figure's validator, so build the Title) | yes (`axis_label`) | yes (`major_label_overrides` values are TextLike) | **no**: `LegendItem.label` is a string spec; `Legend.title` is a String | yes (`Label.text`); `LabelSet` no | as `<image href="data:image/svg+xml">` (vector inside an image) |
| `HTMLLabel`/`HTMLTitle`/`HTMLLabelSet` | no: markup is printed literally (`<b>bold</b>` on screen) | n/a | n/a | n/a | no | not exported (DOM) |
| `Div` (innerHTML) | outside the plot only (layout cell) | no | no | no | no | not exported |
| **Positioned runs** (composite) | yes | yes (hide `axis_label`, Labels in the border) | yes (hide major labels; `LabelSet` runs at tick positions, `x` data/`y` screen; the existing CustomJS refit rewrites the source) | yes (key cell) | yes | plain `<text>`, Helvetica, exact |

- **TeX caveats.** Math mode collapses spaces ("Bold title it x^2" drew as "Boldtitleitx²"): wrap words in `\text{}`. The face is MathJax's TeX font family, not twoway's Helvetica; `\textsf` is sans but still not Helvetica. Bokeh's MathJax configuration is fixed in `bokeh-mathjax.js`. It needs MathJax in the page, as dash already includes for TeX titles (`test_csp_browser._specs()["rich"]`).
- **Positioned-runs sketch.** Split the SMCL into runs `(text, weight, style, size, baseline_shift, family)`, the shape `svg_text_runs.py` already reads from twoway. Emit one `Label` per run, all with the same `x`/`y`, `text_align="left"`, and `x_offset` set by a CustomJS on document ready. That CustomJS measures each run with an offscreen canvas `ctx.font = "<style> <weight> <size> <family>"` / `measureText`, the same metric Bokeh's TextBox uses.
  - `{sup:}`: a smaller size and a negative `y_offset`.
  - `{stSerif}`/`{stMono}`: `text_font`.
  - Centred or right alignment: total width first, then shift.
  - The served app runs the same JS (twin).
- **Recommendation:**
  - titles, axis titles and added text: positioned runs (exact font), with TeX as a fallback only where the user wrote TeX;
  - legend entries: the key cell of section 6;
  - tick labels: runs only when a label actually holds markup, which is rare.

---

## 6. Legend key shapes and key marker size

**What LegendItem allows** (section 4.0 citations):
- a list of renderers whose glyphs each draw their own fixed legend picture into one shared box: markers centred at 0.4 of the box, lines across the middle, areas as an inset rect;
- `index` selects a row for vector visuals;
- there is no per-item box size or angle.

Measured (`txt39/screen.png`):
- An item whose renderers have **empty** sources draws **nothing**: `data_size == 0` returns early.
- A **custom `defs` marker** in the paint-directly form (`ctx.moveTo/lineTo`; `visuals.line.apply(ctx, i)`) draws a capped "I" both in the plot and in the key, and exports to SVG.

Composite recipes (all with legend-only renderers: a 1-row CDS with NaN x/y, excluded from HoverTool and DataRange1d `renderers`):

| twoway key | Build |
|---|---|
| rcap / rcapsym (capped spike, symbols at the ends) | custom `defs` marker drawing shaft + caps (+ an end symbol for rcapsym), or Line + two `defs` cap markers overlaid in one item |
| pccapsym | `defs` marker: a segment with end symbols |
| dropline | `defs` marker: a vertical drop with a marker at the top; or Scatter + a `defs` "drop" stroke |
| pcarrow / pcbarrow | `defs` marker drawing the shaft + one or two heads (`ctx` paths, filled heads via `visuals.fill.apply`) |
| rarea | Patch/VArea area legend (inset rect) with `line_*` set to twoway's outline (P1-6) |
| marker key at the true marker size | Bokeh draws markers at 0.4 x the box. Either set `Legend.glyph_width/height = size / 0.4`, which is per Legend and enlarges every row, or use a key cell |

Caveats:
- Custom-marker renderers are canvas or SVG only. That matters only for the in-plot glyph; a legend-only renderer draws nothing in the frame.
- On a webgl figure such a renderer silently paints on canvas, which is harmless.
- In SVG export, keys of a canvas-backend figure are 20x20 PNGs (section 1.2). For README fidelity, export from an svg-backend copy (vector keys) or use the key cell.
- The **key cell** (a bare Plot with Scatter, Segment and Quad glyphs plus Labels) is the general fallback. It covers textfirst, stacked, symplacement, per-entry textboxes and exact marker size. It is fully vector in export, and dash already lays such cells out for by().

## Not verified here

- `browser.setDownloadBehavior` on Firefox BiDi.
- Playwright's WebKit run itself (nothing installed).
- Whether a hidpi `deviceScaleFactor` sharpens the PNG parts of `export("svg")`.
- A stretch-sized figure in an inactive tab.
- The exact radian sign for an upward right-axis title (pin it).
- Multi-line axis titles rendered (the code path is confirmed, js9:28690-28784; the picture is not).
