# Section 33-04: dash runner -- saved page, SVG and view dump

> Part of: WP-33 (Verification corpus and README gallery) · Items: none (TR-2 closes in 33-14) · Risk: yellow · Batch: 33.4 · Depends on: 33-03 · Blocks: 33-05, 33-08, 33-09 · Tasks: 4, 1 commit · Case-id prefix: Q3304 (none used)

## Overview

For each corpus example 33-03 records twoway's SVG, rc and message. The dash side needs the same three things plus what the verdict engine compares: a static SVG of dash's drawing at twoway's size and a dump of the drawn geometry. Bokeh's own `export_svg` needs selenium, which is not installed; but "`Bokeh.index.find_one(model).export("svg").ctx.get_serialized_svg(true)` evaluated over DevTools on the saved page" works today in both Bokeh versions, and "A lone figure: set `sizing_mode="fixed"`, `width`/`height`, and clear `min_height`, `max_height` and `aspect_ratio` in-page ... gives exactly 528x384" [B §0, §1.3]. The exported SVG writes every text twice and random clipPath ids [B §1.2], so it must be normalised before it is committed anywhere.

After this section, `python3 scripts/corpus/dash_run.py --run <run>` runs every example's dash command in Stata (chunks through `scripts/stata_slot.sh`, as 33-03 does; an example whose dataset is missing from the offline cache is set aside and named once per dataset, as 33-03 does, D-33-04.g), saving each page; then opens each page in one headless Chrome held over DevTools (`test/range_probe.RangeProbe`, read-only reuse), sizes the figure to twoway's size, exports the SVG, dumps the views, normalises the SVG, and writes `<run>/dash.jsonl` plus `<run>/dash/<id>.svg` and `<id>.view.json`. A by() grid or any page with more than one figure is exported at its natural size with the viewport set to twoway's width and letterboxed into twoway's box, and is marked `size_matched: false` (PD-17).

**Test order and commit rule.** 33-04-01 writes the unit tests red; 33-04-02 writes the Stata half; 33-04-03 the Chrome half and the normaliser; 33-04-04 runs a live sample and commits once: `Add the corpus dash runner: saved page, SVG and view dump (WP-33 33-04)`.

### Section decisions

- **D-33-04.a (saving).** The dash command gets `saving("<run>/dash/<id>.html", replace)`: appended as ` saving(...)` when the command has a comma at parenthesis depth 0 outside quotes, else as `, saving(...)`. 33-02 has already stripped any `name()`, `saving()` and `nodraw` of the example from `dash_cmd` (D-33-02.h), so the added `saving()` is the command's only one (dash refuses a second as twoway does). `global dash_nobrowser 1` and `adopath ++ "<repo>/"` open each do-file (memory: no browser windows).
- **D-33-04.b (pixel size).** W = round(width_in * 96), H = round(height_in * 96) from twoway.jsonl (96 px per inch, the factor dash's `_dash_apply_frame_aspect` uses, [C] §4.3); 7.5 x 4.5 in gives 720 x 432.
- **D-33-04.c (lone figure vs grid).** A page whose document has exactly one root that is a `Plot` (after unwrapping one `column`/`row`/`GridBox` holding only it) is a lone figure: the in-page fix-up of [B] §1.3 applies (`r.sizing_mode='fixed'; r.width=W; r.height=H` for every root; on the figure `min_height=null; max_height=null; aspect_ratio=null; sizing_mode='fixed'; width=W; height=H`), then a 1.5 s settle (2.5 s when the page holds TeX: `document.querySelector('mjx-container')` or a `TeX` model). Anything else: `Emulation.setDeviceMetricsOverride {width: W, height: 2000, deviceScaleFactor: 1, mobile: false}`, settle, export the first root, and wrap the SVG in `<svg xmlns="http://www.w3.org/2000/svg" width="W" height="H" viewBox="0 0 W H"><g transform="translate(dx,dy) scale(s)">...</g></svg>` with s = min(W/w, H/h) and the remainder centred (letterbox). `size_matched` is true only for the first path.
- **D-33-04.d (WebGL off).** RangeProbe starts Chrome with `--disable-gpu`, so GL glyphs export as vector paths [B §1.2 item 2]; the harness never edits a page's `output_backend`.
- **D-33-04.e (normalisation, deterministic).** `normalise_svg(text)`: (1) delete every `<text>` element whose attributes hold `fill="none"` (Bokeh's second, stroke-only copy, [B §1.2 item 3]); (2) rename every `id="..."` in document order to `d1`, `d2`, ... and rewrite each `url(#old)` and `href="#old"` / `xlink:href="#old"` to the new id; (3) nothing else. Applying it twice gives the same text.
- **D-33-04.f (one Chrome, any page).** One `CorpusProbe` (subclass of `RangeProbe`, in dash_run.py) serves every page of a run; it is restarted after 100 pages or after a page error. `RangeProbe.__enter__` waits for `_READY_JS` (`document.readyState === 'complete' && !!window.Bokeh && Bokeh.documents.length > 0`, range_probe.py:118-119, :167-168) and raises after 60 s, so a page with no Bokeh (33-05's blank raster page) would never load: `CorpusProbe(path, chrome=None, timeout=60, ready=None)` keeps `self.ready = ready or _READY_JS` and overrides `__enter__` with RangeProbe's body (range_probe.py:147-173, copied, not edited) waiting for `self.ready`; `navigate(path, ready=None)` first evaluates `window.__dashCorpusOld = true` on the current page, sends `Page.navigate` to `file://<abspath>`, then waits for `!window.__dashCorpusOld && (<ready or _READY_JS>)`, so it never reads the old page while the new one has not committed.
- **D-33-04.g (a dataset missing from the cache; DECISIONS A-26, D-33-03.f).** Before chunking, `run_stata` reads the cache as it is now (it may differ from the twoway run's): it sets aside every example `twoway_run.missing_datasets(examples, datasets.cache_dir())` names -- none of their lines reaches a do-file and no Stata session starts when no example is left -- prints `skip: dataset <name> not cached` once per key of that map, in name order (so a dataset that is only ever an example's second missing one is named too), before its counts line, and gives each of them the dash.jsonl row `{id, rc: None, first_line: None, setup_rc: None, html: None, skip}` with the `skip` of its `twoway_run.skip_rows(examples, datasets.cache_dir())` row (`dataset <name> not cached`, `<name>` the first of its `missing` list). Every other example with no twoway record or a twoway `skip` is skipped with that reason, as before.

## Risk: [yellow] -- browser internals read by a dev tool

**Why.** The view dump reads BokehJS view internals (as test_default_axes_chrome.py does), which can change between 3.8 and 3.9. **Risk factors.** by() grids exporting empty when forced to a fixed size [B §1.3]; TeX settling; huge pages (20k points -> 7.3 MB SVG, [B §1.2 item 6]). **Mitigation.** The grid path never forces a size; the dump JS tolerates missing members (`?.`) and records `null`; the live sample runs under both Pythons (bokeh 3.8 `/opt/anaconda3/bin/python3` and 3.9 `python3`) only for the Chrome half, since the page is the same.

## Dependencies

- **Depends on:** 33-03 (twoway.jsonl sizes; its chunk runner pattern, reused through `twoway_run.chunks` and `twoway_run.parse_log`; its missing-dataset split, `twoway_run.missing_datasets` and `twoway_run.skip_rows`, with 33-02's `datasets.cache_dir`).
- **Blocks:** 33-05 (reads dash.jsonl, the SVGs and view dumps; rasters through `CorpusProbe`), 33-08 (`normalise_svg`, the run commands), 33-09 (`do_text`, `records`, `export_pages`) -- each through the Published interface.
- **Parallel batch 33.4:** 33-12, 33-13 -- disjoint files. `test/range_probe.py` is read only.

## Evidence

- `test/range_probe.py:132-300`: `RangeProbe(path, chrome=None, timeout=60)`; `__enter__` starts Chrome with `--headless=new --disable-gpu --remote-debugging-port --window-size=1200,900`, enables Runtime and Page and navigates to `file://<path>`, then waits for `_READY_JS` (:118-119, `document.readyState === 'complete' && !!window.Bokeh && Bokeh.documents.length > 0`); `_send(method, params)` :238, `_eval(expr)` :241 (returnByValue), `_wait_for` :251, `js_errors` :297.
- `test/test_default_axes_chrome.py:42-67` `_TICKS_JS`: walks `Bokeh.index` views through `child_views`, `renderer_views`, `axis_views`; an axis view has `v.model.ticker`, `v.tick_coords.major[v.dimension]`, `v.dimension`, `v.model.x_range_name`/`y_range_name`; its title from `v.parent.model.title.text`.
- [B §1.2]: export text is `font-family="helvetica"` in px, each text twice (`fill=...` then `fill="none" stroke-opacity="0"`); legend keys, the ColorBar strip and TeX come out as embedded PNG or SVG data URIs; clipPath ids random (`id="ngWPXGKbisGz"`).
- [B §1.3]: the lone-figure fix-up (quoted in D-33-04.c) gives 528x384 in both versions; a by() GridPlot forced the same way exported an empty shell (8 paths, 0 texts).
- `dash_render.py:50171-50198` `_DASH_SVG_SAVE_JS` (Save as SVG) calls the same `export("svg")`; figures are never drawn with `output_backend="svg"` (:50163-50170).
- The saved page's CSP (`_DASH_CSP_STANDALONE`, dash_render.py:5706-5716) does not apply to DevTools `Runtime.evaluate`.

## User stories

- US-33-04.1 As the README reader, I want dash's picture of each example as a vector SVG at twoway's size so that the pair can be compared side by side.
- US-33-04.2 As the maintainer, I want dash's drawn ticks, titles, keys and glyph counts read from the page so that verdicts compare geometry, not pixels alone.

## Business requirements

- BR-33-04.1 Every example with a twoway record gets a dash record: rc and first line, and for rc 0 an SVG and a view dump, or a skip reason.
- BR-33-04.2 A lone figure's SVG is exactly twoway's size in pixels; any other is letterboxed into it and marked not size-matched.
- BR-33-04.3 A committed SVG made from the same page is byte-identical on every run.
- BR-33-04.4 No record or SVG holds a machine path or user name.
- BR-33-04.5 An example whose dataset is not in the offline cache is not run under dash, and each missing dataset is named once in the run's output (A-26).

## Technical requirements

- TR-33-04.1 Create `scripts/corpus/dash_run.py` with these public functions (one unit test each):
  - `with_saving(cmd, path) -> str` (D-33-04.a; the top-level comma scan skips `"..."` and `` `"..."' `` strings and counts `(`/`)`).
  - `do_text(examples, out_dir, cache, repo) -> str`: as `twoway_run.do_text`, with `adopath ++ "<repo>/"` and `global dash_nobrowser 1` after `version 19`, the command `capture noisily <with_saving(dash_cmd, out_dir/<id>.html)>`, no `graph export`, and `display "##RC <id> " _rc` after it.
  - `run_stata(run_dir, jobs=3, timeout=1800, only=None) -> dict`: as `twoway_run.run` (chunks in `<run_dir>/dash/c<k>/`, parsed with `twoway_run.parse_log`), keeping the html files in `<run_dir>/dash/`; an example whose dataset is missing from the cache is set aside by D-33-04.g (its one `skip:` line per dataset, its row, no Stata line); examples with no twoway record or a twoway skip are skipped with the same reason.
  - `class CorpusProbe(RangeProbe)`: `__init__(path, chrome=None, timeout=60, ready=None)`, `__enter__` (D-33-04.f), `navigate(path, ready=None)` (D-33-04.f), `eval_async(expr)` (`Runtime.evaluate` with `awaitPromise: True, returnByValue: True`; raises on `exceptionDetails`), `viewport(w, h)` (`Emulation.setDeviceMetricsOverride {width: w, height: h, deviceScaleFactor: 1, mobile: false}`) and `errors_since(n)` (`self.js_errors()[n:]`, so each page reports only its own errors).
  - `SIZE_JS`, `EXPORT_JS`, `DUMP_JS` (module constants, the JS of D-33-04.c and TR-33-04.2), and `export_page(probe, path, w, h) -> dict` returning `{"svg": text, "view": dump, "size_matched": bool, "js_errors": [...]}` (the SVG already passed through `letterbox` when D-33-04.c's second path was taken; not yet normalised).
  - `export_pages(pages: dict[str, str], sizes: dict[str, tuple[int, int]], out_dir: str, probe=None) -> dict[str, dict]`: for each id of `pages` (id -> saved page path) in sorted order, `export_page` at `sizes[id]` (W, H px) through `probe`, or through one `CorpusProbe` it opens and closes when `probe` is None; writes `<out_dir>/<id>.svg` (`normalise_svg` of the export) and `<out_dir>/<id>.view.json` (sorted keys, 2-space indent); returns `{id: {"svg": "<out_dir>/<id>.svg", "view": "<out_dir>/<id>.view.json", "size_matched": bool, "js_errors": [...], "w": W, "h": H}}`, and `{id: {"error": "<text>"}}` for a page whose export raised (the probe is then restarted for the next page).
  - `records(examples, parsed, html_dir, run_dir, twoway_rows) -> list[dict]`: the dash.jsonl rows of one parsed log without running Stata -- `{id, rc, first_line, setup_rc, html, skip}` per example (`html` = `dash/<id>.html` relative to the run folder when rc is 0 and the file exists; the twoway record's skip carried over; TR-33-04.3's path replacement). `run_stata` calls it per chunk; 33-09 calls it on its own session's log.
  - `letterbox(svg, w, h) -> str` (D-33-04.c; reads the inner root's `width`/`height`).
  - `normalise_svg(text) -> str` (D-33-04.e; regex-based, no XML re-serialisation, so untouched bytes stay untouched).
  - `run_chrome(run_dir, only=None) -> dict`: for every dash record with rc 0 and an html file, calls `export_pages` (one probe) at twoway's W x H (D-33-04.b) into `<run_dir>/dash/`, and rewrites `<run_dir>/dash.jsonl` with `svg` and `view` (relative), `size_matched`, `js_errors`, `w`, `h`, and `export_error` when the export failed.
  - `main(argv)`: `--run <dir>`, `--jobs`, `--timeout`, `--only`, `--stata-only`, `--chrome-only`.
- TR-33-04.2 `DUMP_JS` returns JSON `{"figures": [...]}`, one entry per Plot view found by walking `Bokeh.index` as `_TICKS_JS` does: `id` (model id), `bbox` and `frame` (`[x, y, w, h]` from `view.bbox` and `view.frame.bbox`, rounded to 0.1 px), `axes` (per axis view: `side` = `v.model.side ?? v.panel?.side`, `dim`, `ticks` = `Array.from(v.tick_coords.major[v.dimension])`, `labels` = the drawn label texts when `v.compute_labels` exists, else null, `title` = `v.model.axis_label`), `titles` (each `Title` model on the plot: `text`, `align`, `side`), `legend` (each `LegendItem`: label text and its renderers' glyph type names), `renderers` (per GlyphRenderer view: `glyph` = `v.glyph.model.type`, `n` = `v.model.data_source.get_length()` when present, `x`/`y` = `[min, max]` of the glyph's own `x`/`y` (or `left`/`right`, `top`/`bottom`) columns when they are number arrays, `marker` = for a `Scatter` glyph the marker its model draws (`m = v.glyph.model.marker`: `m.value` when `m` is an object with a value, else the distinct values of the data column `m.field`, else `m` when it is a string), `fill`/`line` colours, `fill_alpha`/`line_alpha` and `line_width` as written on the glyph model (`v.glyph.model.fill_color`, `.line_color`, `.fill_alpha`, `.line_alpha`, `.line_width`), and `visible` = the renderer's own `v.model.visible` (a Bokeh glyph model has no `visible`; the renderer has, in 3.8 and 3.9). "As written" is how BokehJS holds the property, reduced to JSON: a plain value as it is (a string, a number, `null`); a value spec as `{"value": v}` (BokehJS decodes a serialised `{type: "value", value: v}` to `{value, transform, units}`, and `transform`/`units` are left out when undefined); a field spec as `{"field": f}`; an expression as `{"expr": <its model's type name>}` (the model itself is not serialised). Any member it cannot read is `null`; it never throws. 33-05's `marker_shape`, `glyph_extents` and colour check read `marker`, `x`/`y`, the colours, their alphas and `visible` (D-33-05.b: a hidden or fully transparent colour is not drawn: dash keeps real colours on glyphs it hides -- hollow markers' `fill_alpha` 0.0, dash_render.py:12856; the area patch's `line_alpha=0.0`, :18684; the contour extent's invisible scatter, `fill_alpha=0, line_alpha=0`, :24475).
- TR-33-04.3 Records hold relative paths only (`dash/<id>.svg`); `first_line` has the cache and run directories replaced as in TR-33-03.3; `normalise_svg` does not remove anything else, so a data URI an image glyph or legend key produced stays (it holds no path).
- TR-33-04.4 No shipped file changes: no `dash_render.py` export option, no new `dash build` option (a fixed-size dash build is 34-04/45-04's work; until then by() pairs stay letterboxed, PD-17).
- TR-33-04.5 The functions, files and fields of the Published interface below keep these names and shapes; a later section (33-05, 33-08, 33-09, 33-14) calls or reads them and adds nothing to dash_run.py.

### Published interface (for 33-05, 33-08, 33-09, 33-14)

Module `scripts.corpus.dash_run` (import convention D-33-02.g; it imports `from scripts.corpus import twoway_run`).

| Name | Signature / shape | Used by |
|---|---|---|
| `with_saving` | `with_saving(cmd, path) -> str` | 33-09 (its own session's do-file) |
| `do_text` | `do_text(examples, out_dir, cache, repo) -> str`; markers as 33-03's (`##VERSION`, `##BEGIN <id>`, `##SETUP <id> <rc>`, `##RC <id> <rc>`), no `##EXPORT` | 33-09 |
| `records` | `records(examples, parsed, html_dir, run_dir, twoway_rows) -> list[dict]` (parse the log with `twoway_run.parse_log`) | 33-09 |
| `run_stata` | `run_stata(run_dir, jobs=3, timeout=1800, only=None) -> dict` | 33-08's `make corpus` |
| `CorpusProbe` | `CorpusProbe(path, chrome=None, timeout=60, ready=None)`; `navigate(path, ready=None)`, `eval_async(expr)`, `viewport(w, h)`, `errors_since(n)`, context manager | 33-05 (raster), 33-09 |
| `export_page` | `export_page(probe, path, w, h) -> {"svg": text, "view": dict, "size_matched": bool, "js_errors": list}` | 33-09 |
| `export_pages` | `export_pages(pages: dict[id, html_path], sizes: dict[id, (w_px, h_px)], out_dir, probe=None) -> {id: {"svg": path, "view": path, "size_matched": bool, "js_errors": list, "w": int, "h": int}}` or `{id: {"error": text}}` | 33-09, `run_chrome` |
| `normalise_svg` | `normalise_svg(text) -> str` (D-33-04.e; idempotent) | 33-08 (twoway SVGs copied to docs/gallery/svg/), 33-09 |
| `letterbox` | `letterbox(svg, w, h) -> str` | internal; tested |
| `run_chrome` | `run_chrome(run_dir, only=None) -> dict` | 33-08's `make corpus` |
| CLI | `python3 scripts/corpus/dash_run.py --run <run> [--jobs N] [--timeout S] [--only id,id] [--stata-only \| --chrome-only]` | 33-08's Makefile |
| `<run>/dash.jsonl` | one row per examples.jsonl id, sorted: `{id, rc, first_line, setup_rc, html, skip, svg, view, size_matched, js_errors, w, h, export_error}`; paths relative to the run folder; Chrome fields null until `run_chrome` | 33-05, 33-08, 33-14 |
| `<run>/dash/<id>.html` | the saved page dash wrote for the example | `run_chrome` (33-08 builds its own gallery pages) |
| `<run>/dash/<id>.svg` | the normalised export; 33-08 copies it to `docs/gallery/svg/<id>-dash.svg` unchanged | 33-05, 33-08 |
| `<run>/dash/<id>.view.json` | TR-33-04.2's dump: `{"figures": [{id, bbox, frame, axes: [{side, dim, ticks, labels, title}], titles: [{text, align, side}], legend: [{label, glyphs}], renderers: [{glyph, n, x, y, marker, fill, line, line_width, fill_alpha, line_alpha, visible}]}]}`; `fill`, `line`, `line_width`, `fill_alpha` and `line_alpha` as written (TR-33-04.2: a plain value, `{"value": v}`, `{"field": f}` or `{"expr": <type>}`), `visible` a bool or null | 33-05 (`dash_geometry`) |

## Boundaries

Do not edit `test/range_probe.py`, `test/responsive_probe.py`, `test/test_export_svg.py` (read only); Makefile and docs/ (33-08); 33-12's and 33-13's extract scripts. Never add a browser other than Chrome (R14).

## Stata truth

No fixture. Task 33-04-04 runs the 12-example sample of 33-03-03 (`<scratch>/c3`) through `dash_run.py`.

## TDD test stubs

- Test: saving() appended with and without a top-level comma, with a comma inside `(scatter y x, mc(red))` and inside a quoted title -- test/test_corpus_dash.py::TestWithSaving::test_comma_rules
- Test: the dash do-file opens with the adopath and nobrowser lines and has no graph export -- ::TestDoText::test_dash_lines
- Test: normalisation drops the stroke-only text copies, renumbers ids and references, and is idempotent -- ::TestNormalise::test_texts_and_ids (inline SVG with two clipPaths `id="ngWPXGKbisGz"`/`id="QmKa7"`, `clip-path="url(#ngWPXGKbisGz)"` and a doubled `<text>`)
- Test: letterbox arithmetic (a 900 x 300 grid into 720 x 432: s = 0.8, dy = 96) -- ::TestLetterbox::test_scale_and_offset
- Test: export_pages writes one normalised SVG and one view per page and records a failed page -- ::TestExportPages::test_writes_svg_and_view_per_page (default tier: a stub probe object whose `eval_async`/`navigate`/`viewport`/`js_errors`/`errors_since` return canned values, one page raising: two files for the good id, `{"error": ...}` for the bad one)
- Test: rows from a parsed log -- ::TestRecords::test_rows_from_a_parsed_log (`html == "dash/a.html"` for rc 0 with the file present; a twoway skip carried over)
- Test: a dataset missing from the cache is named once and never run -- ::TestRunStata::test_missing_datasets_are_named_once_and_never_run (default tier; `twoway_run.SLOT_CMD` monkeypatched to a fake that writes a canned log, as 33-03's TestRun does; `DASH_CORPUS_CACHE` an empty tmp folder; examples a (`webuse lbw, clear`), b (`webuse lbw, clear` then `webuse nlswork, clear`) and c (`sysuse auto, clear`), each with a twoway.jsonl row of rc 0 (as if the twoway run had the cache): captured stdout holds `skip: dataset lbw not cached` and `skip: dataset nlswork not cached` once each, in that order; the do-files written hold no line for a or b; dash.jsonl's rows for a and b have `rc` None, `html` None and `skip == "dataset lbw not cached"`; c is run)
- Test: the probe loads a page with no Bokeh and never reads the old page -- ::TestInChrome::test_a_plain_page_with_its_own_ready (release tier: `CorpusProbe(blank, ready="document.readyState === 'complete'")` enters; `navigate` to a second blank page whose title differs returns that title)
- Test: export of a lone figure is exactly W x H and its dump has ticks, titles and renderers -- ::TestInChrome::test_a_lone_figure_at_twoways_size (release tier, skip without Chrome; builds a page with `DashRenderer` from a two-plot scatter spec as test_default_axes_chrome.py's `_page` does, exports at 720 x 432, asserts the root `width="720"` `height="432"`, `size_matched`, at least one axis with ticks, one renderer with n > 0 and `marker == "circle"`, every renderer entry holding exactly TR-33-04.2's keys (`fill_alpha`, `line_alpha` and `visible` among them, `visible` true), and no js error)
- Test: a by() page is letterboxed and marked not size-matched -- ::TestInChrome::test_a_by_grid_is_letterboxed (release tier)
- Test: the same page exported twice gives identical normalised text -- ::TestInChrome::test_the_export_is_deterministic (release tier)
- Function coverage stays green: test/test_corpus_functions.py
- Cert cases: none. Pins: none. Parity: none (no product twin).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Command and do-file rules | pytest test_corpus_dash.py (default tier) | inline | n/a |
| Normaliser, letterbox | pytest test_corpus_dash.py | inline SVG | n/a |
| Export and dump | pytest test_corpus_dash.py::TestInChrome (release tier, `pytestmark` on the class) | DashRenderer pages | saved page |
| Live sample | dash_run.py on 12 examples | 33-03's c3 | saved page |

- AC-33-04.1 `python3 -m pytest test/test_corpus_dash.py test/test_corpus_functions.py -q -n0` passes (the TestInChrome tests run in a targeted run, which keeps the release tier, conftest.py `_covers_whole_suite`).
- AC-33-04.2 The live sample gives a dash record for each of the 12 examples; every rc-0 lone figure's SVG root is `width="720" height="432"` (or its own `xsize()`-derived size), and the hand-added `nosuch` example has rc 198.
- AC-33-04.3 Running `--chrome-only` twice on the sample leaves `git diff --no-index` of the two SVG sets empty.

## Tasks

**Commit boundary.** Tasks 33-04-01..04 form one commit by 33-04-04: `Add the corpus dash runner: saved page, SVG and view dump (WP-33 33-04)`. Branch `wp33-s04` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp33-s04`; every command runs from `$WT`. This section closes no GAPS4 item, so BRIEF's ledger and known-differences steps ("The corpus ledger and the known-differences tables") have nothing to delete here; its commit task pulls from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main) before it commits.

```xml
<task type="auto" id="33-04-01">
  <name>Write the dash runner tests red</name>
  <files>test/test_corpus_dash.py</files>
  <action><![CDATA[ Create test/test_corpus_dash.py with the stubs under TDD (names exactly); mark class TestInChrome `@pytest.mark.release` and `@pytest.mark.skipif(responsive_probe.find_chrome() is None, reason="headless Chrome is not installed")`, as test/test_export_svg.py:354-356 does. Pages for TestInChrome are built in a tmp dir the way test/test_default_axes_chrome.py:69-90 `_page` builds them. ]]></action>
  <verify><![CDATA[ `python3 -m pytest test/test_corpus_dash.py -q -n0 2>&1 | tee <scratch>/33-04-01-failure.txt | tail -3` shows every test failing or erroring on the missing module. Nothing committed. ]]></verify>
  <done>The dash runner's rules have failing tests and the failure text is saved.</done>
</task>

<task type="auto" id="33-04-02">
  <name>Write the Stata half of the runner</name>
  <files>scripts/corpus/dash_run.py</files>
  <action><![CDATA[ Create scripts/corpus/dash_run.py with `with_saving`, `do_text`, `records`, `run_stata` and `main` (TR-33-04.1), reusing `twoway_run.chunks`, `twoway_run.parse_log`, `twoway_run.SLOT_CMD`, `twoway_run.missing_datasets` and `twoway_run.skip_rows` through `from scripts.corpus import twoway_run, datasets` (D-33-02.g); `run_stata` sets aside the missing-dataset examples by D-33-04.g. ]]></action>
  <verify><![CDATA[ `python3 -m pytest test/test_corpus_dash.py -q -n0 -k "WithSaving or DoText or Records or RunStata"` passes. ]]></verify>
  <done>dash commands are run in Stata with their pages saved and their rc and messages parsed.</done>
</task>

<task type="auto" id="33-04-03">
  <name>Write export, dump and normaliser</name>
  <files>scripts/corpus/dash_run.py</files>
  <action><![CDATA[ Add `CorpusProbe` (D-33-04.f), `export_pages`, `SIZE_JS`, `EXPORT_JS` (`(async () => { const root = Bokeh.documents[0].roots()[0]; const v = Bokeh.index.find_one(root) ... ; return v.export("svg").ctx.get_serialized_svg(true); })()`, choosing the lone figure's view under D-33-04.c), `DUMP_JS` (TR-33-04.2), `export_page`, `letterbox`, `normalise_svg` and `run_chrome`. Import RangeProbe with `sys.path.insert(0, <repo>/test)` then `from range_probe import RangeProbe, _READY_JS`. ]]></action>
  <verify><![CDATA[ `python3 -m pytest test/test_corpus_dash.py test/test_corpus_functions.py -q -n0` passes, TestInChrome included; the same under `/opt/anaconda3/bin/python3 -m pytest test/test_corpus_dash.py -q -n0 -p no:randomly` (bokeh 3.8). ]]></verify>
  <done>Pages are exported at twoway's size, dumped and normalised in both Bokeh versions.</done>
</task>

<task type="auto" id="33-04-04">
  <name>Run a live sample and commit</name>
  <files>none</files>
  <action><![CDATA[ Run `python3 scripts/corpus/dash_run.py --run <scratch>/c3` (33-03-03's sample), check AC-33-04.2, copy `<scratch>/c3/dash` aside, run `--chrome-only` again and check AC-33-04.3. Grep every record and SVG for `/Users/`, `/private/` and the user name (`id -un`): nothing. Then `git add scripts/corpus/dash_run.py test/test_corpus_dash.py`, pull from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main), confirm `git merge-base --is-ancestor s3-bugs HEAD`, run `node .gitnexus/run.cjs detect-changes --scope all --repo .` (new files only), and commit (body: failure summary, `Regression:` lines, the sample's size_matched count). ]]></action>
  <verify><![CDATA[ AC-33-04.2 and AC-33-04.3 hold; the privacy grep prints nothing; `git log -1 --format=%B | grep -ciE 'claude|anthropic'` prints 0. ]]></verify>
  <done>The dash runner is committed and has exported a live sample deterministically at twoway's sizes.</done>
</task>
```

## Section completion criteria

AC-33-04.1..3; one commit ending `(WP-33 33-04)`; the hand-back lists the sample's size-matched and letterboxed ids.

## Notes

- **Traps.** (1) Never force a by() grid to a fixed size (it exports empty, [B §1.3]). (2) `export("svg")` returns a canvas-layer object: call `.ctx.get_serialized_svg(true)` on it, inside `awaitPromise` evaluation. (3) Do not set `output_backend="svg"` on shipped pages (breaks the PNG save, dash_render.py:50163-50170). (4) The view dump reads internals: guard every member access. (5) A page over 5k points makes a multi-MB SVG; that is allowed (Q53), but 33-08 should not pick such an example for the README.
- **Merge rules touched:** R14. **Help paragraphs owned:** none.
- **Sizes later.** A-1 (34-04, 45-04) gives every graph twoway's shape and exact size; until those land, by() and multi-figure pages stay letterboxed and `size_matched: false` (PD-17). Nothing here changes when they land: the lone-figure fix-up of D-33-04.c simply agrees with the page's own size.
- **Commit-body line forms:** `Regression: test/test_corpus_dash.py::<Class>::<test> -- failed at <sha> with ModuleNotFoundError`; `Sample: 12 examples, <n> size-matched, <n> letterboxed, <n> refused`.
