# Section 53: Composite PNG/SVG export and a print stylesheet

> Part of: WP-31 · GAPS3 rows: H2x (H2 export/print part; E10, J7 notes) · Risk: yellow · Batch: 18 · Depends on: 48, 52 · Blocks: -- · Tasks: 4, 1 commit · Case-id prefix: U53

## Overview

**What is wrong today.** GAPS3 H2 (GAPS3.md:239): "no print stylesheet; PNG/SVG omit KPI cards, title, filters and tab strip". The save button on a grid's toolbar writes `dashboard.png` of the grid alone (`_dash_name_save`, dash_render.py:35329-35367), and the Save as SVG action (`_DASH_SVG_SAVE_JS`, :35281-35303) calls `Bokeh.index.find_one(grid).export("svg")`: BokehJS `LayoutDOMView.export` composites child canvases but not DOM widgets (research/bokeh-web.md §9: "KPI cards/filters/tabs would be missing"). Printing the page relies on the browser's default rendering of a `stretch_width` layout, which may re-layout to the paper width during print (research §9: "`beforeprint` ... to fix widths").

**After this section** every top-level grid's toolbar carries THREE export controls (DECISIONS A30, REVIEW-4 R4-22b): the save button (the grid alone as PNG, unchanged), the existing "Save as SVG" action -- which on a top-level grid now writes the whole dashboard (the composite) and on a by() sub-grid keeps writing that grid alone -- and one new `CustomAction`, "Save dashboard" (PNG composite). Both composite writers draw -- the title and subtitle, the filter widgets' titles and current values, the tab strip (titles, active tab marked), the KPI cards and the grid image -- from Bokeh model values with `ctx.fillText`, never from the DOM, in both modes (the action is a `CustomJS` run by BokehJS). A `GlobalInlineStyleSheet` with `@media print` rules and a `document_ready` `CustomJS` registering `beforeprint`/`afterprint` handlers fix the layout width for printing in both modes; the hook is appended to the `_hooks` list S52 created at the three `document_ready` sites (DECISIONS A28, REVIEW-4 R4-12).

**Why one section.** One JS string pair, one action builder, one stylesheet, one hook; all shared and copied by name. S53 is batch 18's "export/print JS + composite" owner; it depends on S48 (D-53d: a table is never drawn, open or folded, and an open one adds a caption) and on S52 (the `_hooks` list).

**Test order and commit rule.** One cycle, one commit `(WP-31 H2x)`: 53-01 tests red; 53-02 the composite action in both modes; 53-03 the print stylesheet and hook; 53-04 Chrome verification, help, close, commit.

### Section decisions (binding on the executor)

- **D-53a. The composite is drawn from model values, not the DOM.** The action's `CustomJS` receives models: `grid` (the layout root to export), `header` (the title and subtitle Divs, `_dash_header_models`), `widgets` (the filter widgets, S49's reset button excluded), `tabs` (the `Tabs` model or null), `kpis` (the KPI Divs, in layout order) and `name`. Text is read from `Div.text` with tags stripped (`div.text.replace(/<[^>]*>/g, "")` then entity-decoded through a `DOMParser`-free table for `&amp; &lt; &gt; &quot; &#x27;`), widget titles from `w.title`, values from `w.value` through the widget's own option labels (`Select`: the option whose value equals `w.value`; `MultiChoice`: the joined labels; sliders: `w.value` formatted by `dash_fmt_text` when the spec carries a format, else `String`), tab titles from `tabs.tabs[i].title` and `tabs.active`, KPI title/value/subtitle from the card's three inner divs (the markup `_dash_kpi_card_html` writes, :22900-22957: title div, `#kpi_val_<name>`, subtitle div, in that order).
- **D-53b. Layout arithmetic (CSS pixels, hidpi applied by `export`).** Let `W = max(gridCanvas.width / dpr, 960)`, `dpr = window.devicePixelRatio || 1`; margins `M = 16`; `y = M`. Header: title `bold 20px sans-serif` at `(M, y + 20)`, `y += 28`; subtitle `14px` at `(M, y + 14)`, `y += 22` (each only when present). Filters: `13px`; each `"<title>: <value>"` drawn at `(x, y + 13)` with `x` starting at `M` and advancing by `ctx.measureText(text).width + 24`, wrapping to a new line (`y += 20`, `x = M`) when `x + width > W - M`; `y += 24` after the last. Tabs: `14px`; each title at `(x, y + 14)`, the active one `bold` and underlined with a 2px line at `y + 18`; `x` advances by width + 24; `y += 28`. KPI cards: `cw = 220, ch = 110, gap = 16`; per row `n = max(1, floor((W - 2M + gap) / (cw + gap)))`; card i at `(M + (i % n) * (cw + gap), y + floor(i / n) * (ch + gap))`; a rounded rectangle (radius 8) stroked `#999`, filled with the card's background (the inline `background:` if present else `#ffffff`); title `13px` centred at `+20`, value `bold 36px` centred at `+62` in the value div's `color:`, subtitle `11px` centred at `+92`; `y += ceil(k / n) * (ch + gap)`. Grid: the exported canvas drawn at `(0, y)` at its CSS size; total height `H = y + gridCanvas.height / dpr + M`. Background white. Fonts: the generic `sans-serif` (the page's fonts are Bokeh's defaults; no web font is embedded).
- **D-53c. PNG and SVG share one layout.** `_DASH_COMPOSITE_JS` defines `dash_composite_layout(models) -> [{kind, x, y, text|font|color|w|h}]` (the arithmetic above, measuring text with a scratch 2D context) and two writers: `dash_composite_png(layout, gridCanvas)` paints onto a new canvas and `toBlob`s it; `dash_composite_svg(layout, gridSvgText, w, h)` wraps `<svg xmlns=... width height>` holding `<rect>` for the page and cards, `<text>` elements and the grid's serialised SVG inside `<g transform="translate(0,y)">`. EVERY text body AND every attribute value goes through `dash_html_escape` (REVIEW-4 R4-20): a card's `fill` and a value's `fill` colour (read from the KPI's inline `background:`/`color:` styles, i.e. the user's `color()`/`bgcolor()` options) is accepted only when it matches `/^#[0-9a-fA-F]{6,8}$|^[a-zA-Z]+$/`, else `#ffffff` (fill) or `#000000` (text); numbers are written through `String(Number(v))`; a font string is one of the fixed D-53b fonts, never read from the page (research §9: `layer.ctx.get_serialized_svg(true)`; use `view.export("svg").to_blob()` → text via `blob.text()`). File names `<name>-dashboard.png` / `.svg` with `name` from `_dash_save_filename`. **Three controls (A30):** `_DASH_SVG_SAVE_JS` gains a branch at its top -- `if (typeof header !== "undefined" && header !== null) { <the composite SVG path> return; }` -- so the SVG action on a top-level grid (which receives the composite args, TR-53.2) writes the composite and the same action on a by() sub-grid (no composite args) keeps writing the grid alone; `_DASH_COMPOSITE_SAVE_JS` is the body of the new PNG action only. The toolbar therefore holds the save button, "Save as SVG" and "Save dashboard" -- three controls, not four.
- **D-53d. Tables (S48).** An open table (`toggle.active`) is drawn as up to 10 text rows (`12px`) under its figure's cell? No -- the grid image already shows the DataTable? It does not (DOM widget). Decision: a table is NOT drawn in the composite; the composite's caption line reads `"Data tables are not included"` (11px, grey) when any `fig._dash_table` toggle is active. Residual, documented in help.
- **D-53e. Print.** `GlobalInlineStyleSheet(css=_DASH_PRINT_CSS)` added to the document (saved: `doc.add_root`-free -- attached as a `stylesheets` entry of the layout root; served: the same on the root), with `_DASH_PRINT_CSS = "@media print { :root { --dash-print-width: 1000px; } .db-dashboard, .db-bs-container { width: 1000px !important; max-width: 1000px !important; } .db-filter-bar, .bk-Toolbar { display: none !important; } }"` -- host-element rules only (shadow roots are reached by the `beforeprint` handler, not CSS); `.bk-root` is Bokeh 2 markup and does not exist on a Bokeh 3 page (REVIEW-4 R4-21; `.db-dashboard` and `.db-filter-bar` exist, 3 hits each; `.db-bs-container` stands for the layout(bs) container's class -- read `_render_bootstrap_html` for its name and use that), so the root width is fixed by the `beforeprint` hook, not by CSS. The hook: `doc.js_on_event("document_ready", CustomJS(args={"roots": [...]}, code=_DASH_PRINT_HOOK_JS))` with `window.addEventListener('beforeprint', () => { for (const r of roots) { r._dash_sm = r.sizing_mode; r.sizing_mode = 'fixed'; r.width = 1000; } }); window.addEventListener('afterprint', () => { for (const r of roots) { r.sizing_mode = r._dash_sm; r.width = null; } });`. Both strings are copy-list constants. The hook is APPENDED to S52's `_hooks` list: one line `_hooks += [_print_hook]` directly after `_hooks = [*_by_hooks, *_err_hooks]` at each of the three sites (saved :44454ff and :46118ff as S52 left them; the served `make_document` template line) -- never a second `js_on_event("document_ready", ...)` call (R4-12; S54 adds its own `_hooks += [_tabs_hook]` line after S53's).

## Risk: [yellow] -- a new toolbar action on every grid, canvas text in two formats, and print behaviour that only a browser shows

**Why.** `export()` is a BokehJS internal (`_DASH_BOKEH_INTERNALS` already lists the SVG action's three calls); `toBlob`, `measureText` and `DOMParser`-free decoding are browser APIs no Python test runs.

**Risk factors.** (1) `LayoutDOMView.export("png")` of the grid returns a CanvasLayer whose `.canvas` has device pixels (hidpi); the composite must scale; (2) the SVG composite must escape every text and every attribute value; (3) print layout is unverifiable without Chrome (research §9 "Not verified in a browser"); (4) a `Tabs` model exists only under `tabs()`; the composite must tolerate `null`.

**Mitigation.** (1) `dpr` division (D-53b) and `drawImage(gridCanvas, 0, y, cssW, cssH)`; the Chrome test reads the blob's dimensions; (2) `dash_html_escape` (already in `_DASH_FMT_JS`) on every `<text>` body and attribute value, the colour whitelist of D-53c; `TestTheSvgWriter::test_escapes_every_text` and `::test_attribute_values_are_escaped` under node; (3) the Chrome test uses `Emulation.setEmulatedMedia({media: "print"})` through `_CspProbe._send` and reads the root's width; (4) `tabs: null` arm in the node test.

## Dependencies

- **Depends on: 48** (`fig._dash_table`, D-53d), **52** (the `_hooks` list at the three `document_ready` sites). **Blocks: none.**
- **Parallel batch: 18** with S54 (`html_attributes`/ARIA, Tabs keyboard hook) and S55 (served template env/health/bundle). S53 edits `_dash_name_save`, `_DASH_SVG_SAVE_JS`'s top branch, the new JS constants, `_DASH_BOKEH_INTERNALS`, and ONE added line `_hooks += [_print_hook]` after S52's `_hooks = [...]` line at each of the three sites; S54 edits `_dash_header_models`, `_dash_filter_widget`, `_make_kpi_div`/`_dash_kpi_card`, `_dash_tab_panels` and adds its own one line `_hooks += [_tabs_hook]` after S53's at the same three sites; S55 edits `_dash_served_template`'s env/health/bundle lines. The merger applies 53 then 54 and places S54's line after S53's at each site (index batch-18 row; DECISIONS A28).

## Evidence

### The actions today

```python
35281 _DASH_SVG_SAVE_JS = r"""
35282 const stem = (typeof name === "string"
35283               && /^[A-Za-z_][A-Za-z0-9_]{0,31}$/.test(name)) ? name : "dashboard";
...
35288   const view = Bokeh.index.find_one(grid);
35290   view.export("svg").to_blob().then((blob) => {
```

`_dash_name_save(model, name=None)` (:35329-35367) sets the SaveTool's `filename` and appends one `CustomAction(description="Save as SVG", icon=_DASH_SVG_SAVE_ICON, tags=["dash_svg_save"], callback=CustomJS(args={"grid": model, "name": filename}, code=_DASH_SVG_SAVE_JS))`. It is called from `_dash_layout_cell` (by() sub-grids), `_dash_tab_panels` (:36034) and the top-level grid builders. test/test_export_svg.py pins: `TestTheAction::test_a_grid_and_a_figure_each_gain_one_action` (:94), `::test_a_second_call_adds_nothing` (:113), `TestEveryToolbar::test_one_action_beside_each_save` (:205), `TestTheBundle::test_the_calls_exist_in_the_shipped_bokehjs` (:253), `TestInChrome` (:341-429, release).

### Where the models live

Header: `_dash_header_models` (:36433); filter widgets: `self.filter_widgets` (saved) / the template's widget list; tabs: `_dash_tab_panels` returns the `Tabs`; KPI Divs: `self.kpi_divs` / the template's `kpi_divs`. The top-level grid is built in `_assemble_layout` (:45939) for the saved page and in `make_document` for the served app; the layout(bs) saved page has no Bokeh layout root (ALLOWED "layout(bs) is standalone markup") -- there each embedded item has its own toolbar; D-53f: under `layout(bs)` the composite action is added to each item's toolbar and draws the header, filters and tabs text plus THAT item only (KPI cards are items of their own there and get no action).

### Hooks

`_dash_by_stack_hooks` (:38391) and its `document_ready` registration (:44448-44464) are the pattern for a page-level `CustomJS` under the CSP seal (`_dash_seal_saved_page`, :4843: "New behaviour must be a Bokeh CustomJS ... or an InlineStyleSheet").

## User stories

- **US-53.1** As an author I want one click to save the whole dashboard as a PNG, cards and filters included, so that a report shows what the reader saw.
- **US-53.2** As an author I want the same as a vector SVG.
- **US-53.3** As a reader I want the page to print at a fixed width with no toolbars so that nothing reflows on paper.

## Business requirements

- **BR-53.1** Every grid toolbar offers "Save dashboard" (PNG) and "Save dashboard as SVG"; the file shows title, subtitle, filter titles and current values, the tab strip with the active tab marked, every KPI card (title, value, subtitle, colours) and the grid image, in that order from the top.
- **BR-53.2** The text in the file is the text on the page at that moment (after moves).
- **BR-53.3** Printing uses a 1000 px layout with toolbars and the filter bar hidden; the screen layout is restored afterwards.
- **BR-53.4** Both modes behave alike; no page data reaches the code except through model properties.

## Technical requirements

- **TR-53.1 Constants.** `_DASH_COMPOSITE_JS` (D-53c: `dash_composite_layout`, `dash_composite_png`, `dash_composite_svg`, `dash_svg_attr` (the escape plus colour whitelist), `dash_text_of_div`, `dash_widget_value_text`, the entity table) and `_DASH_COMPOSITE_SAVE_JS` (the PNG action body: `Bokeh.index.find_one(grid).export("png")` then `dash_composite_png`); `_DASH_SVG_SAVE_JS` gains the composite branch of D-53c at its top and is prefixed by `_DASH_COMPOSITE_JS` when the composite args are passed; `_DASH_PRINT_CSS`, `_DASH_PRINT_HOOK_JS`, `_DASH_COMPOSITE_PNG_ICON`/`_SVG_ICON` (18×18 data URIs like `_DASH_SVG_SAVE_ICON`). Placed after `_DASH_SVG_SAVE_ICON`; copy list after `_DASH_STALE_STATUS_HTML`'s entry (after batch 16/17 additions).
- **TR-53.2 `_dash_name_save(model, name=None, composite=None)`.** New keyword `composite`: a dict `{"header": [...], "widgets": [...], "tabs": Tabs|None, "kpis": [...], "tables_open": bool}` or None. When given: the existing SVG action (tag `dash_svg_save`) is built with `args={"grid": model, "name": filename, **composite}` and `code=_DASH_COMPOSITE_JS + _DASH_SVG_SAVE_JS` (so it writes the composite); and ONE `CustomAction(description="Save dashboard", icon=_DASH_COMPOSITE_PNG_ICON, tags=["dash_composite_png"], callback=CustomJS(args={"grid": model, "name": filename, **composite}, code=_DASH_COMPOSITE_JS + _DASH_COMPOSITE_SAVE_JS))` is appended (idempotent like the SVG action: a second call updates args). Without `composite` the function behaves as today (grid-alone SVG, no PNG composite action). Three controls per top-level toolbar (A30). Callers: the top-level saved grid (in `_assemble_layout` after the grid is built), each tab's grid (`_dash_tab_panels` gets a `composite` parameter), the served `make_document`'s root grid; by() sub-grids and layout(bs) items per D-53f.
- **TR-53.3 `_DASH_BOKEH_INTERNALS`.** Append `("LayoutDOMView.export('png').canvas, CanvasLayer.to_blob", "_DASH_COMPOSITE_JS", "test/test_export_composite.py::TestTheBundle::test_the_calls_exist_in_the_shipped_bokehjs")`.
- **TR-53.4 Print.** `_dash_print_models(roots) -> (GlobalInlineStyleSheet, CustomJS)` (shared): both modes attach the stylesheet to the root layout's `stylesheets` and append the hook to S52's list: `_print_css, _print_hook = _dash_print_models(<roots>)` then `_hooks += [_print_hook]` directly after `_hooks = [*_by_hooks, *_err_hooks]` -- at :44454ff (`_render_bootstrap_html`, layout(bs): the stylesheet goes on every embedded item), at :46118ff (`_assemble_layout`) and at the template's `_hooks = [...]` line in `make_document` (as S52 left them; re-read the numbers). No new `js_on_event` call.
- **TR-53.5 Maps.** function_test_map: `_dash_print_models`; `_dash_name_save` keeps its entry. test/test_export_svg.py's `TestEveryToolbar` counts ONE action beside each save -- flip to "one SVG action everywhere and, on a top-level grid, one PNG composite action" (three controls) with a `Flipped:` line; its `TestInChrome` node that reads the SVG action's output on a top-level grid is flipped to expect the composite (the grid-alone expectation holds on a by() sub-grid: add that arm) with a `Flipped:` line.
- **TR-53.6 Help.** dash.sthlp `{title:Exporting}` (:1354ff): the three controls (the save button: the graphs alone; Save as SVG: the whole dashboard on a top-level grid; Save dashboard: the whole dashboard as PNG), what the composite holds, the D-53d table note, printing; the Standalone-vs-server table rows.

## Boundaries

- No change to the PNG `SaveTool` (it keeps writing the grid alone); `_DASH_SVG_SAVE_JS` changes only by the composite branch at its top (its grid-alone path is byte-identical).
- No ARIA (S54), no served template env work (S55).
- No html2canvas or any third-party script (M22, CSP).
- No `output_backend="svg"` on figures (test_export_svg.py::TestNoSvgBackend stays).

## Stata truth

None. Truth block `* ==== S53 H2x: export and print ====`: `U53-1` a built page holds the `dash_composite_png` tag once per top-level grid and `dash_svg_save` once per toolbar (python: block reading the saved HTML's JSON); `U53-2` the page holds `@media print` once and `beforeprint` once; `U53-3` a served app source (`_dash_serve_spec` → `dash serve, dryrun`-style build through the existing serve-spec helper) defines the same constants (`cert_file_has`).

## TDD test stubs

Regression (red at 6370ca4), file `test/test_export_composite.py`:
- `TestTheActions::test_three_controls_on_the_top_grid_both_modes` (save tool, `dash_svg_save` with the composite args, `dash_composite_png`), `::test_a_second_call_updates_not_adds`, `::test_tab_grids_and_bs_items_get_them`, `::test_by_sub_grids_keep_the_grid_alone_svg` (no composite args, no PNG action), `::test_only_models_reach_the_args`.
- `TestTheLayoutArithmetic` (node, `dash_composite_layout` with a fake `measureText` of 7 px per character): `::test_header_then_filters_then_tabs_then_cards_then_grid`, `::test_filters_wrap_at_the_width`, `::test_card_rows_fill_then_wrap`, `::test_no_tabs_no_header_collapses`, `::test_values_are_the_current_ones` (a Select whose value changed), `::test_table_caption_when_a_table_is_open`.
- `TestTheSvgWriter::test_escapes_every_text` (node; `<`, `&`, `"` in a title and a value), `::test_attribute_values_are_escaped` (node; a card background `" onload="x` and a value colour `url(javascript:1)` come out as `#ffffff`/`#000000` and no raw `"` or `<` reaches an attribute; `#1a2b3c`, `#1a2b3c80` and `steelblue` pass), `::test_translate_of_the_grid`.
- `TestTheBundle::test_the_calls_exist_in_the_shipped_bokehjs` (greps `to_blob`, `export(` in the installed bokeh.js, like test_export_svg.py:253).
- `TestPrint::test_stylesheet_and_hook_present_both_modes` (the hook is one entry of the single `document_ready` callback list, beside S52's error hook), `::test_the_css_is_fixed_text` (no `.bk-root`), `::test_the_hook_restores`.
- Release (Chrome): `TestInChrome::test_saved_composite_png_dimensions_and_text` (download to a temp dir through `_CspProbe(downloads=...)`, open the PNG with Pillow if present else assert the file size > 10 kB and the SVG holds the title text), `::test_served_composite`, `::test_print_media_fixes_the_width` (`Emulation.setEmulatedMedia`).
- Flips: test_export_svg.py::TestEveryToolbar::test_one_action_beside_each_save; test_export_svg.py::TestInChrome's top-level SVG output node (TR-53.5).

cscript: U53-1..U53-3. Parity: `_case("tabs with kpis composite", [...], kpis=[...], bo={"tabs": "A: g1 k1 / B: g2"})` (the layout tree records the action tags per toolbar in both modes -- extend `_tools(fig)`/the grid toolbar reader in `_layout_tree` to list `CustomAction` tags).

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| three controls, args, idempotence | pytest | none | yes |
| layout arithmetic, text, escaping | node | none | saved JS (shared) |
| bundle calls | pytest | none | -- |
| print stylesheet/hook | pytest | none | yes |
| files written, print width | Chrome (release) | none | yes |
| spec/page markers | cscript U53-1..3 | none | yes |

**AC-53.1** every stub green; **AC-53.2** U53-1..3 pass; **AC-53.3** test_export_svg.py (flipped), test_csp.py, test_bokeh_internals.py, test_saved_page_errors.py (S52's hook tests still see their hook) green.

## Tasks

**Commit boundary.** 53-01..53-04 form the one commit `Save the whole dashboard as PNG or SVG and fix the print layout (WP-31 H2x)`.

<task type="auto" id="53-01">
  <name>Write the failing export and print tests</name>
  <files>test/test_export_composite.py, test/test_mode_parity.py, test/test_wp31_truth.cscript</files>
  <action><![CDATA[Create test/test_export_composite.py with the classes above (node tests run _DASH_COMPOSITE_JS through test/js_runner.py with a stub canvas context exposing measureText/fillText/fillRect/drawImage recording calls). Append the parity entry and the S53 truth block (U53-1..U53-3). Run `python3 -m pytest test/test_export_composite.py -q -m "not release"` on the unmodified tree; save to <scratch>/53-01-failure.txt. Do not commit.]]></action>
  <verify><![CDATA[The pytest tail prints failures only (AttributeError: module has no attribute _DASH_COMPOSITE_JS); test -s <scratch>/53-01-failure.txt]]></verify>
  <done>The regression tests exist and fail at 6370ca4.</done>
</task>

<task type="auto" id="53-02">
  <name>Add the composite actions in both modes</name>
  <files>dash_render.py, test/test_export_svg.py, test/function_test_map.py</files>
  <action><![CDATA[Apply TR-53.1 (the JS constants and icon after _DASH_SVG_SAVE_ICON, with the D-53b arithmetic, the D-53c writers, dash_svg_attr's escape and colour whitelist, and the composite branch at the top of _DASH_SVG_SAVE_JS), TR-53.2 (_dash_name_save's composite keyword: the SVG action takes the composite args and one PNG composite action is appended -- three controls, A30; the callers in _assemble_layout, _dash_tab_panels, the served make_document, layout(bs) items per D-53f), TR-53.3 and the copy-list entries. Flip test_export_svg.py::TestEveryToolbar and its TestInChrome top-level SVG node with Flipped lines (TR-53.5). Run test/test_export_composite.py -k "Actions or Arithmetic or SvgWriter or Bundle", test/test_export_svg.py -m "not release", test/test_bokeh_internals.py, test/test_statistical_helpers.py -k CarriesEveryName.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_export_composite.py test/test_export_svg.py test/test_bokeh_internals.py -q -m "not release" prints all passed]]></verify>
  <done>Every top-level grid in both modes offers the two composite actions drawn from model values.</done>
</task>

<task type="auto" id="53-03">
  <name>Add the print stylesheet and hook</name>
  <files>dash_render.py, test/test_csp.py</files>
  <action><![CDATA[Apply TR-53.4: _dash_print_models after _dash_by_stack_hooks (copy-list entry after S52's `_dash_error_hooks` entry); at each of the three sites add the stylesheet to the root's `stylesheets` and ONE line `_hooks += [_print_hook]` directly after S52's `_hooks = [*_by_hooks, *_err_hooks]` (saved :44454ff and :46118ff, the template's make_document line; re-read the numbers after batch 17) -- no new js_on_event call. Run test/test_export_composite.py -k Print, test/test_csp.py, test/test_saved_page_errors.py -k WindowHooks, and the S53 truth block driver through scripts/stata_slot.sh.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_export_composite.py -k Print test/test_csp.py test/test_saved_page_errors.py -k WindowHooks -q passes; `grep -c "_hooks += \[_print_hook\]" dash_render.py` prints 3; `grep -c 'js_on_event("document_ready"' dash_render.py` is unchanged from the batch-18 base; the cscript log shows U53-1..U53-3 PASS]]></verify>
  <done>Both modes carry one print stylesheet and one beforeprint/afterprint hook under the sealed policy.</done>
</task>

<task type="auto" id="53-04">
  <name>Verify in Chrome, document and commit H2x</name>
  <files>dash.sthlp</files>
  <action><![CDATA[Run DASH_TEST_TIER=release python3 -m pytest test/test_export_composite.py -m release -q (skip without Chrome, say so) and DASH_TEST_TIER=batch python3 -m pytest test/test_mode_parity.py -k composite. Edit the Exporting help paragraphs (TR-53.6). Replace the <!-- WP-31 H2x --> marker under "### Fixed in WP-31" with "Every top-level grid toolbar saves the whole dashboard -- title, filters, tabs, KPI cards and graphs -- as SVG (Save as SVG) or PNG (Save dashboard), and pages print at a fixed width without toolbars, in both modes (WP-31, H2x)". Close BUGS.md "Dashboard extensions: export and print" (Residual: data tables not in the composite, D-53d), rewrite the GAPS3 H2x Tracked line to the Closed form with `commit pending` (DECISIONS A11; no amend). Commit on wp31-s53 with the body forms.]]></action>
  <verify><![CDATA[git log -1 --format=%s ends "(WP-31 H2x)"; git log -1 --format=%B | grep -ci "claude\|anthropic" prints 0; python3 -m pytest test/test_tracking_documents.py test/test_help_conformance.py -q passes]]></verify>
  <done>H2x is committed with help, CHANGELOG, BUGS.md and GAPS3 updated.</done>
</task>

## Section completion criteria

- Three export controls per top-level grid in both modes (save button, composite SVG, composite PNG), drawn from model values with the D-53b arithmetic; SVG text and attribute values escaped; print stylesheet present and the hook appended to the `_hooks` list at the three sites; Chrome test green or documented skip; one commit `(WP-31 H2x)`.

## Notes

- **CSP (M11).** Everything is `CustomJS` or `GlobalInlineStyleSheet`; `_dash_seal_saved_page` sees no new inline script. `style-src 'unsafe-inline'` admits the stylesheet.
- **Security.** Text reaches the canvas through `fillText` (inert) and the SVG through `dash_html_escape` for bodies AND attribute values, with colours whitelisted by `dash_svg_attr` (R4-20); the file stem is `_dash_save_filename` (a Stata name); no DOM reads.
- **Bokeh internals (A109).** Register the `export('png').canvas`/`to_blob` dependence in `_DASH_BOKEH_INTERNALS`; `test_bokeh_internals.py` pins it.
- **Copy lists (R2):** constants after `_DASH_STALE_STATUS_HTML`'s entry; `_dash_print_models` after `_dash_reference_lines`.
- **Commit body forms:** `Regression: test/test_export_composite.py::TestTheActions::test_three_controls_on_the_top_grid_both_modes -- failed at 6370ca4 with AssertionError: no CustomAction tagged dash_composite_png`; `Flipped: test/test_export_svg.py::TestEveryToolbar::test_one_action_beside_each_save -- one action was wrong because a top-level grid now carries the PNG composite action too`; `Flipped: test/test_export_svg.py::TestInChrome::<node> -- the grid-alone SVG was wrong on a top-level grid because Save as SVG now writes the whole dashboard there (A30)`; `BUGS.md: "Dashboard extensions: export and print" (closed)`; `GAPS3: H2x Tracked`.
- **Decisions for ratification:** the layout arithmetic constants (D-53b); tables excluded from the composite (D-53d); the 1000 px print width and hidden filter bar (D-53e). **Decided:** three controls (A30, R4-22b); the `_hooks` list (A28, R4-12); attribute escaping (R4-20); no `.bk-root` (R4-21).
- **Tracked line (A11):** `commit pending`; no amend. **A14:** 53-01 appends the one H2x block.
- **Files (A13):** `<files>` lists primary files; the tracking documents and flipped tests are implied.
