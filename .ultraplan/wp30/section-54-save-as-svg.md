# Section 54: Client-side Save as SVG (P1.28 part b, M8)

> Part of: WP-30 · Items: P1.28b (entry `P1.28b`; GAPS2-E10b) · Risk: yellow · Batch: 19 (merge order S54, S55, S56) · Depends on: 04, 22, 41 · Blocks: none · Tasks: 9, 1 commit · Case prefix: SVA

## Review amendments

- Fixed (major): TR-54.6 and 54-05 hedged on the form of S41's internals list ("docstring block or tuple"). S41's TR-41.18 fixes it as a tuple of `(internal, guard, test)` string triples checked by `TestTheInternalsList`. The three triples are now written out in that form, with the `browser test` guard S41 uses for its BokehJS entries. 54-05's verify now counts them and runs S41's test; it previously used a grep that the JS constant alone would satisfy.
- Fixed (minor): TR-54.3 said both "set `args["name"]`" and "assign a new dict". It now assigns `{**args, "grid": model, "name": filename}`.
- Fixed (minor): `bokeh.util.paths.bokehjsdir()` is deprecated (it warns on 3.8.0 and 3.9.0, measured). `TestTheBundle` now uses `bokehjs_path()`, and is marked as a guard because the calls already exist at the base. 54-01 lists it among the guards.
- Fixed (minor): the truth helper was "a python block that declares `version 19`". It is now a `python:` block above the header, in S31's reviewed form. It reads both page encodings (a `layout(bs)` page embeds `docs_json` in a JS string) and is called through one-line `python:` statements. SVA-03 is marked as a guard. 54-02 and 54-08 now check `ALL CHECKS PASSED` and that no SKIP appeared.
- Fixed (minor): 54-06's verify said "0 failed except the two help tests", which is not runnable. It now deselects them with `-k`.
- Fixed (minor): the merge rules record the R3 exception (the Server Mode table's `Toolbar, save as SVG` row, allowed by the orchestrator) and S22's handed-over "Images" sentence. index.md's R2 row (ICON missing; anchor 33027-33028) and R3 row are reported in g09.md. The landing note names `_DASH_BOKEH_INTERNALS`.
- Checked at `c96facd`: `_dash_name_save` 24445-24462, its callers (25020, 25083, 30963, 32533, 36293, 36346), copy-list lines 33027-33028 and 33352, `backend =` at 30241, help :1206, :1225-1233 and :1505, `_assert_nine_tools` :194-197, `_grid_toolbar` :654-664, and `CustomAction.icon` accepting a `data:image` URI (bokeh 3.8.0). Batch 19: S55 and S56 edit none of `_dash_name_save`, the new constants or S54's tests. S56's `_glyph_layer_lines` anchors are distinct (R2).
- Rejected: factoring the action into `_dash_svg_save_action`. It would add a copy-list function and a map key for no behaviour gain (Notes).
- The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:162 (P1.28) reads "There is no `r(filename)` and no SVG backend". S22 (P1.28a, batch 8) closed the `r(filename)` and stale-graph half; this section is the SVG half, GAPS2-E10b ("no SVG backend; figures are canvas or webgl only", GAPS2.md:1205-1219). Measured at `c96facd` (research `.ultraplan/wp30/research/p1-28.md` §1d, §3):

```
dash_render.py:30241  backend = "webgl" if n_rows > _WEBGL_THRESHOLD else "canvas"
d2.html (dash scatter mpg weight, saving()): no output_backend serialised -> canvas
toolbar: pan,wheel_zoom,box_zoom,box_select,lasso_select,undo,redo,reset,save -> PNG only, at devicePixelRatio
```

The obvious remedy, `output_backend="svg"`, was measured to **break today's PNG save**: a grid's SaveTool composes on a canvas (`LayoutDOMView.export("auto")`), and svg figures inside a `gridplot` give `TypeError: Failed to execute 'drawImage' on 'CanvasRenderingContext2D'` on bokeh 3.8.0 and 3.9.0 (research §3, `svgbackend.py`; critic re-run). M8 and register P1.28.2 reject it.

**After this section**, every toolbar that holds a save button, in the saved page and the served app, also holds one "Save as SVG" action. Clicking it asks BokehJS for a vector SVG of exactly what that toolbar's save button would write as PNG (the whole grid, a tab's grid, a by() graph's panels, or one `layout(bs)` item) and downloads it as `dashboard.svg` or `<name>.svg`. The research's in-page probe gave `{"name":"dashboard.svg","type":"image/svg+xml","len":24554,"paths":44,"texts":44}` on bokeh 3.8.0 under dash's own CSP (24,444 bytes on 3.9.0), a 20,000-row WebGL page gave a vector SVG (8,304,932 bytes, 20,018 `<path>`, 0 `<image>`), and a two-graph grid gave one SVG of 92,471 bytes with 0 `<image>`. It exports what is on screen: after a saved filter move the filtered views, after a served move the recomputed sources, as the PNG does. No figure changes backend; the PNG save is untouched.

**Why one section.** M8 gives P1.28 two parts; S22 owns the Stata half, this section the browser half. It edits one helper that both modes already share (`_dash_name_save`, copied into the served app by name), one new JS constant and its copy-list entry, the toolbar help, and S41's internals list.

**Test order and commit rule (rule 7).** One cycle on `wp30-s54`: 54-01 and 54-02 write every regression test and run them against the unmodified batch-19 base, saving `$S/54-P1.28b-failure.txt` (no commit); 54-03 to 54-08 fix, flip and document; 54-09 closes the entry, deletes its `WP30_OPEN` key, replaces its one marker and makes the one commit. No test-only commit exists, and no commit is red.

## Risk: [yellow] — one CRITICAL helper reaches every toolbar of both modes, and the action must run under S04's hashed and nonced policies

**Why.**
- `_dash_name_save` is CRITICAL: `gitnexus impact _dash_name_save -d upstream -r dash` gives 11 impacted (`_assemble_layout`, `_dash_layout_cell`, `_dash_tab_panels`, `_render_bootstrap_html`, `_build_tabs_widget`, `_cell_of`, `render`; flows `render`, `regen_dashboard`), research §6, re-verified by the critic.
- `ServerAppBuilder._glyph_layer_lines` (the copy lists) is HIGH: 4 impacted (`_generate_app_source`, `build`).
- `_DASH_FIGURE_TOOLS` and `_dash_save_filename` are read, not edited (UNKNOWN / CRITICAL via `_dash_name_save`).
- The action relies on three BokehJS internals (`Bokeh.index.find_one`, `View.export("svg")`, `CanvasLayer.to_blob`), which a Bokeh release may change.

**Risk factors.**
1. `_dash_name_save` is called twice on one model in some layouts (critic 7, `dup_probe.py`): a by() facet sub-grid is named by `_dash_layout_cell` (dash_render.py:25020) and again at :30963 (saved) or by the served `_dash_cell` lambda (:36293). A naive append would put two actions on that toolbar.
2. A plain graph's `layout(bs)` cell is a bare figure (:25021-25022), so the action lands in `fig.tools`, which `_assert_nine_tools` (test/test_toolbar.py:194-197) forbids.
3. A CSP that blocks the callback would leave a dead button with no sign.
4. A Bokeh release that renames an internal would leave a button that throws.
5. The served copy loop skips a misspelt name silently (RK-9).

**Mitigation.**
1. The action is tagged `dash_svg_save` and `_dash_name_save` replaces its `name` arg when one is already there (last name wins, as for `SaveTool.filename`); `TestTheAction::test_a_second_call_adds_nothing` pins it.
2. The action is added only where a `SaveTool` sits on the model's own toolbar; `_assert_nine_tools` is flipped (register P1.28.7) to admit exactly one tagged action after the nine.
3. The callback is a `CustomJS`, run through `new Function` under the kept `'unsafe-eval'`, never an inline script, so S04's hash set and nonce are unchanged; `test_csp_browser.py` gains a class that clicks it in both modes and requires zero violations.
4. The JS wraps every call in try/catch and on failure shows one `window.alert` naming the PNG button; the three calls join S41's internals list with their guard and their Chrome test, run under every verified minor.
5. G4 (`test_every_listed_name_exists`, `TestTheServedAppDefinesEveryNameItReads`) runs in 54-03, where the names land.

## Dependencies

- **Depends on: 04, 22, 41.**
  - S04 (batch 2): the saved page's script-src is `'unsafe-eval'` plus the SHA-256 of each inline script (no `'unsafe-inline'`), the served meta policy is nonce-only (`_DASH_CSP_SERVED_META`, `_dash_csp_served`), `img-src` keeps `data: blob:` in both, and `test/test_csp_browser.py` holds `_CspProbe` (violation listener, `inject()`, `in_task(js)`) and the saved and served page builders (S04 TDD stubs). The saved page's seal refuses an unhashed inline script (A98), which this section never adds.
  - S22 (batch 8): `r(filename)`, the Exporting help's "Images" paragraph (which states there is no SVG drawing mode, a sentence this section keeps) and the Stored results section. S22 hands this section the toolbar row and one sentence in "Images" (S22 Boundaries).
  - S41 (batch 14): the bokeh window (`>=3.8,<3.10`, or `<3.11` if 3.10 was verified), `VERIFIED_BOKEH`, and the internals list (research name `_DASH_BOKEH_INTERNALS`: each entry names its guard and its test) "that S54 extends".
  - S01 provides the open entry `P1.28b`, its `WP30_OPEN` key, the marker `<!-- WP-30 P1.28b -->` at the end of `### New`, the S54 stub block of `test/test_wp30_truth.cscript` (header `* ==== S54 P1.28b: Client-side Save as SVG ====`) and the map anchors `# WP-30 S54 (P1.28b): Client-side Save as SVG (P1.28 part b, M8)`.
  - Read, not depended on: S09 (TeX inert, so a `$$…$$` title is plain text and the SVG holds no MathJax `<image>`), S21 (the Reset row's sentence), S48/S53 (by() grids, still named through `_dash_name_save`).
- **Blocks:** none.
- **Parallel batch: 19**, merge order S54, S55, S56.
- **Can run with:** S55 edits `_dash_build_hover` and tests; S56 edits `_make_figure_body`, `_generate_app_source`, SchemeParser, the scheme files and dash.ado. Neither edits `_dash_name_save`, `_dash_save_filename`, `_DASH_FIGURE_TOOLS`, the toolbar help or `test_toolbar.py`. S56 also appends to `_glyph_layer_lines`' constants tuple, at its own anchor (`"_DASH_TEXTBOX_HONOURED",`, 32933), far from this section's (33028-33029); R2 allows both.

## Evidence

Anchors at `c96facd` (dash_render.py 37,689 lines, dash.sthlp 3,822). S04, S21, S22, S41, S48 and S53 move lines; the executor re-finds each by symbol at `batch-19-base`.

### E1. The save button's helper (dash_render.py:24418-24460)

```python
24418 _DASH_FIGURE_TOOLS = ("pan,wheel_zoom,box_zoom,box_select,lasso_select,"
24419                       "undo,redo,reset,save")
24423 _DASH_SAVE_NAME = "dashboard"
24428 _DASH_SAVE_NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,31}")
24431 def _dash_save_filename(name=None):
...
24445 def _dash_name_save(model, name=None):
24456     from bokeh.models import SaveTool
24457     filename = _dash_save_filename(name)
24458     toolbar = getattr(model, "toolbar", None)
24459     for tool in (getattr(toolbar, "tools", None) or ()):
24460         if isinstance(tool, SaveTool):
24461             tool.filename = filename
24462     return model
```

Callers (grep): saved :25020 (`_dash_layout_cell`, facet grid), :25083 (tab panels), :30963 (`all_models.append(_dash_name_save(cell, name))`, layout(bs) cells), :32533 (the main grid); served, generated: :36293 (`lambda _n: _dash_name_save(_dash_cell(_n), _n)`) and :36346 (the main grid). The served app copies the helper and its constants by name (`_glyph_layer_lines`):

```python
33024                       # The toolbar every figure carries and the names its
33025                       # save button writes (WP-21), read by the figure
33026                       # block and by _dash_save_filename.
33027                       "_DASH_FIGURE_TOOLS", "_DASH_SAVE_NAME",
33028                       "_DASH_SAVE_NAME_RE",
...
33352                      "_dash_save_filename", "_dash_name_save",
```

(The R2 table cites the anchor line as 33028; at `c96facd` the pair sits on 33027 and its continuation `"_DASH_SAVE_NAME_RE",` on 33028.)

### E2. What can export a vector image (research §3, measured, Chrome 154, bokeh 3.8.0 and 3.9.0)

| Route | Result |
|---|---|
| `bokeh.io.export_svg` | needs selenium; absent from both Pythons |
| `output_backend="svg"` in a grid | grid PNG save throws `drawImage` TypeError (3.8.0 and 3.9.0) |
| `Bokeh.index.find_one(grid).export("svg").to_blob()` in a `CustomAction`'s `CustomJS`, page under `_DASH_CSP_STANDALONE`, `_DASH_FIGURE_TOOLS` figures in a gridplot | `dashboard.svg`, `image/svg+xml`, 24,554 bytes, 44 `<path>`, 44 `<text>`; webgl 20,000 rows: vector, 0 `<image>`; a KPI Div is not in it; each text appears twice in Bokeh's SVG (cosmetic) |

A `fetch()` of the blob URL is blocked by the saved page's `connect-src 'none'`, so a test captures the blob by patching `URL.createObjectURL` (research `svgaction.py`) or through `Browser.setDownloadBehavior` (S04's `test_exports_still_work`).

### E3. Where a toolbar sits (critic 7, `dup_probe.py`; both modes the same)

- A grid's merged toolbar holds ONE new `SaveTool` (`gridplot()`), named by `_dash_name_save`.
- A facet sub-grid is named twice (risk 1); a plain graph's `layout(bs)` cell is a bare figure, named once; a KPI Div has no toolbar and is skipped (`getattr(model, "toolbar", None)` is None).

### E4. The toolbar's tests and help (pinned today)

- `test/test_toolbar.py::_assert_nine_tools` (:194-197): `set(names[9:]) <= {"HoverTool"}`; used at :236 (`TestTheToolList::test_each_figure_built_from_it_owns_new_tools`), :370 (`TestTheSavedPage::test_every_figure_has_the_nine_tools_in_order`), :440 (`TestTheBootstrapPage::test_a_graph_s_save_is_named_after_it`, the bare figure that fails once the action lands) and :508 (`TestTheServedApp::test_every_figure_has_the_nine_tools_in_order`).
- `test/test_toolbar.py::TestTheHelpDocumentsTheToolbar::test_every_tool_has_a_row_in_order` (:734-738): the `{synopt:…}` rows of the toolbar section equal the nine labels; the new row breaks it.
- `test/test_toolbar.py::TestTheHelpDocumentsTheToolbar::test_the_mode_table_lists_the_toolbar_in_both_modes` (:748): finds one `Toolbar, save as PNG` row with `Yes Yes`; kept, and a sibling assertion for the SVG row is added.
- `test/test_mode_parity.py::_grid_toolbar` (:654-664) records `(type, filename)` of a grid's non-proxy tools; `_tools` (:620) records each figure tool's type. Both see the action's type only; the harness gains its description and its `name` arg so parity covers it.
- Baseline (research): `python3 -m pytest test/test_toolbar.py -q -n0 -p no:cacheprovider` → `107 passed in 18.68s`.
- dash.sthlp "The toolbar" (:1183-1234): nine `{synopt:}` rows ending `{synopt:Save}write the figures to a PNG image; see below.{p_end}` (:1206), and "{ul:Saving an image.}" (:1225-1233). The mode table (:1505): `{col 5}Toolbar, save as PNG{col 38}Yes{col 59}Yes`.

### E5. Blast radius (`gitnexus impact <symbol> -d upstream -r dash`, index at `c96facd`, research §6)

| Symbol | Risk | Action |
|---|---|---|
| `_dash_name_save` | CRITICAL (11) | warn; additive: one tagged action beside an existing SaveTool |
| `ServerAppBuilder._glyph_layer_lines` | HIGH (4) | warn; two constant names appended at S54's anchor |
| `_dash_save_filename`, `_DASH_FIGURE_TOOLS` | CRITICAL (via the above) / UNKNOWN | read only |
| `_generate_app_source`, `_make_figure_body` | HIGH / CRITICAL | **not edited** (the served app reaches the helper through the copy list) |

## User stories

- **US-54.1** As a twoway user who publishes figures, I want a "Save as SVG" button beside the PNG save on every dashboard, in the saved page and the served app, so I can put a vector figure in a paper without a browser plug-in.
- **US-54.2** As a dashboard viewer, I want the SVG to hold what I see, after the filters I moved, as the PNG does, so the file matches the screen.
- **US-54.3** As a maintainer, I want the button to keep working under the page's Content-Security-Policy and across the verified Bokeh versions, or to say plainly that it cannot, so a hardened page never carries a dead button.

## Business requirements

- **BR-54.1** Every toolbar that holds a save button, in both modes, holds exactly one "Save as SVG" action, after the save button: the dashboard's grid, each tab's grid, each by() graph's panels, and each graph `layout(bs)` places on its own. A KPI card has none.
- **BR-54.2** The action downloads one vector SVG (no raster `<image>` for plain-text figures) of the figures its toolbar's PNG save writes, named `dashboard.svg`, or `<name>.svg` for a `layout(bs)` item named by a Stata name; the KPI cards, title, filters and tab strip are left out, as for the PNG.
- **BR-54.3** The SVG reflects the current view: after a saved-page filter move, the filtered views; after a served move, the recomputed data; a WebGL figure (over 10,000 rows) exports as vector.
- **BR-54.4** It runs under the saved page's hashed policy and the served page's nonced policy with zero CSP violations, and adds no inline script, no hash and no policy change.
- **BR-54.5** If the browser or the Bokeh version cannot produce the SVG, one visible message says so and names the PNG button; nothing fails silently.
- **BR-54.6** No figure is drawn with an SVG backend; the PNG save behaves exactly as before.
- **BR-54.7** The help's toolbar section, its mode table and the Exporting text name the action, the file names and what the image holds.

## Technical requirements

- **TR-54.1 `_DASH_SVG_SAVE_JS`** (new module constant, directly after `_DASH_SAVE_NAME_RE`, 24428, with a `#:` comment block citing M8, P1.28.2 and research §3). Its args are `grid` (the model whose toolbar holds the action) and `name` (the stem). The code, verbatim in intent:
  1. `const stem = (typeof name === "string" && /^[A-Za-z_][A-Za-z0-9_]{0,31}$/.test(name)) ? name : "dashboard";` (the Python rule again; never trust the arg).
  2. `const say = () => window.alert("dash: this browser could not write an SVG of these figures; use the save button for a PNG.");`
  3. `try { const view = Bokeh.index.find_one(grid); if (view == null) { say(); return; } view.export("svg").to_blob().then((blob) => { const url = URL.createObjectURL(blob); const a = document.createElement("a"); a.href = url; a.download = stem + ".svg"; a.style.display = "none"; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 30000); }, say); } catch (e) { say(); }`
  - No string from data is concatenated into code; no `eval`, `Function`, `innerHTML` or `fetch`. It is a plain Python string constant (no `.replace` tokens).
- **TR-54.2 `_DASH_SVG_SAVE_ICON`** (new constant, directly after TR-54.1's): a `data:image/svg+xml;base64,` URI of a fixed 18×18 icon (a page outline with the letters "SVG"), built at import from a literal SVG string with `base64.b64encode`; at most 1,024 characters (a test pins it). Both policies admit it (`img-src data:`).
- **TR-54.3 `_dash_name_save`** (CRITICAL, warn; in place, both modes through the copy list). After the SaveTool loop, only when that loop found a SaveTool on `model.toolbar.tools`:
  - find an existing tool that is a `CustomAction` with `"dash_svg_save" in tool.tags`; if found, assign a new dict, `tool.callback.args = {**tool.callback.args, "grid": model, "name": filename}` (Bokeh sees a reassignment, not an in-place mutation), and stop;
  - else append `CustomAction(description="Save as SVG", icon=_DASH_SVG_SAVE_ICON, tags=["dash_svg_save"], callback=CustomJS(args={"grid": model, "name": filename}, code=_DASH_SVG_SAVE_JS))` to `toolbar.tools` (a new list assigned).
  - Import `CustomAction, CustomJS` inside the function beside `SaveTool`. The docstring gains one paragraph: why an action and not a backend (E2), the idempotence rule (E3), and that `name` is `_dash_save_filename`'s. The return value and every existing branch are unchanged.
- **TR-54.4 Served copy list** (R2 row S54). In `_glyph_layer_lines`' constants tuple, a new line `"_DASH_SVG_SAVE_JS", "_DASH_SVG_SAVE_ICON",` directly after `"_DASH_SAVE_NAME_RE",` (the continuation of the anchor `"_DASH_FIGURE_TOOLS", "_DASH_SAVE_NAME",`, 33027-33028 at `c96facd`), keeping the WP-21 group together, with the comment extended by "and the SVG action beside it (WP-30 P1.28b)". `_dash_name_save` is already listed (33352). `_generate_app_source` is not edited: both served call sites already go through `_dash_name_save`.
- **TR-54.5 Both modes and filter moves.** Saved: the four saved callers reach the edit. Served: the two generated callers reach it through the copied helper. The action exports the live view, so nothing is added to `_FILTER_JS`, `_on_filter_change` or the redraw; the tests prove the SVG changes with a move (TestInChrome).
- **TR-54.6 S41's internals list** (BokehJS half). S41's TR-41.18 makes `_DASH_BOKEH_INTERNALS` a literal-evaluable tuple of `(internal, guard, test)` string triples, directly after `_DASH_BOKEH_VERIFIED`, and its BokehJS entries (8, 9) use the guard text `browser test`; `test/test_bokeh_internals.py::TestTheInternalsList::test_every_entry_names_a_guard_and_a_test` checks every test node by AST. Append, at the tuple's end and in that form, exactly:
  1. `("BokehJS Bokeh.index.find_one(model) (S54's _DASH_SVG_SAVE_JS)", "browser test", "test/test_export_svg.py::TestInChrome::test_a_failure_is_said_once")`;
  2. `("BokehJS LayoutDOMView.export('svg') (S54's _DASH_SVG_SAVE_JS)", "browser test", "test/test_export_svg.py::TestInChrome::test_saved_page_before_and_after_a_move")`;
  3. `("BokehJS CanvasLayer.to_blob() (S54's _DASH_SVG_SAVE_JS)", "browser test", "test/test_export_svg.py::TestTheBundle::test_the_calls_exist_in_the_shipped_bokehjs")`.
  The tuple is already on the served copy list (S41 commit 2), so no copy-list line is added for it. S41's test is not edited. The Chrome classes of TR-54.8 run under every verified minor installed on this Mac (54-04).
- **TR-54.7 Help** (`dash.sthlp`; R3: "Exporting; The toolbar" lists S54 for the toolbar row; S22 assigned the one "Images" sentence):
  - The toolbar's synopt table: `{synopt:Save as SVG}write the same figures as a vector SVG file; see below.{p_end}` directly after the `Save` row.
  - "{ul:Saving an image.}": one sentence after the PNG file names: "Save as SVG writes the same figures as a vector image, {cmd:dashboard.svg} or {cmd:g1.svg}, drawn from what is on screen, after any filter you moved; a figure with more than 10,000 points makes a large file."
  - The mode table (the Server Mode comparison, :1505): a row `{col 5}Toolbar, save as SVG{col 38}Yes{col 59}Yes` directly after the PNG row. This is a toolbar row of the scope's "help toolbar row"; no batch-19 section edits Server Mode (R3).
  - S22's "{ul:Images.}" paragraph: after "The toolbar's save button writes the figures as a PNG image at the screen's resolution.", add "Its Save as SVG button writes them as a vector SVG file." The sentence "dash has no SVG drawing mode, because a figure drawn as SVG cannot be saved by the toolbar's button" stays.
  - Every new or changed line at most 79 characters; no tool or vendor name.
- **TR-54.8 Tests** (TDD stubs). New `test/test_export_svg.py`; extended `test/test_csp_browser.py` (S04's), `test/test_toolbar.py`, `test/test_mode_parity.py` (harness only).
- **TR-54.9 Registries.** `test/function_test_map.py`: `_dash_name_save` keeps its entry (a behaviour test of the new branch is added, not renamed). No function is added, so no new key under S54's anchor; the anchor stays empty and S58 removes it (A148). No program is added to `test/program_coverage_map.py`.
- **TR-54.10 JS twins: none.** The action is client-only and has no Python counterpart; `_dash_save_filename`'s rule is restated in JS and a node test runs both on the same 12 inputs (`TestTheAction::test_js_and_python_agree_on_the_stem`).
- **TR-54.11 Security (rule 1; G9: "the SVG action under CSP").**
  - Threat: a page script that runs page data as code, or a policy relaxed to let a button work. Closed by: a constant callback (no data in code), args holding a model reference and a validated Stata name (validated twice), no inline script (hash set and nonce unchanged, so S04's seal and A98 are untouched), no new CSP source, no network request (`connect-src` unchanged), a download only through a `blob:` URL the page made, revoked after 30 s.
  - The icon is a constant `data:` URI, never user text.
  - A huge page's SVG costs the viewer's browser memory only (8.3 MB at 20,000 rows, measured); nothing reaches Stata or the server.

## Boundaries

- **Batch partners.** S55 (P1.9b): `_dash_build_hover`, hover tests, parity CORPUS cases. S56 (P1.10): `_make_figure_body`, `_generate_app_source`, SchemeParser, the extractor and 26 scheme files, dash.ado, Mata, its own copy-list anchors. S54 edits none of their symbols, and they edit none of S54's (`_dash_name_save`, the two new constants, `test_toolbar.py`, `test_export_svg.py`, `test_csp_browser.py`, the toolbar help).
- **Earlier sections, read only:** S04's policies, seal, `_CspProbe` and page builders (extended by a new class, never edited in place); S22's help paragraphs (one sentence added); S41's window and list (entries appended).
- **Not this section's:** a scripted `dash export` from a do-file (GAPS2-E10c; the deferred platform package, M8, P1.34.6); KPI cards and the header in the image (P3.11, with the print stylesheet, register P1.28.5); `output_backend` (rejected, P1.28.2); the duplicated `<text>` in Bokeh's SVG (cosmetic, Bokeh's).
- **Never:** `_DASH_FIGURE_TOOLS` (the nine-tool contract, `TestTheToolList`), `_generate_app_source`, `_make_figure_body`, `_FILTER_JS`, either CSP constant, `_dash_csp_meta`.

## Stata truth

No twoway comparison exists (twoway has no browser toolbar), so no fixture or extractor. One truth block, S01's S54 stub of `test/test_wp30_truth.cscript`, between its start and end lines:

- **SVA-01:** `sysuse auto, clear`; `dash scatter mpg weight, saving("`w30_work'/sva1.html", replace)`; a `python:` block (the scaffold's gate) reads the page's embedded document JSON and counts `CustomAction` objects whose `tags` hold `dash_svg_save`: 1, with `description` `Save as SVG`, and the SaveTool's `filename` `dashboard`.
- **SVA-02:** the same for `dash scatter mpg weight, name(g1)`, `dash kpi mean(mpg), name(k1)`, `dash build, layout(bs) saving(…)`: one action on g1's bare figure, `name` arg `g1`, none for k1.
- **SVA-03 (guard; passes at the base, S22 landed in batch 8):** `r(filename)` (S22) of SVA-01 names the page read, so the do-file path a user follows finds the button.
- **Helper (TR-01.10 item 4).** One `python:` block directly above the S54 header defines the Python function `_sva_actions()` (its own imports of `html`, `json`, `re`, `warnings`, `bokeh.document.Document` and `sfi.Macro`). It reads the page path from the local `sva_page` (`Macro.getLocal`), parses the embedded document both ways `_br_saved` does (test_bug_regressions.cscript:159-180: the `application/json` script element, or the `const docs_json = '…'` string a `layout(bs)` page uses), walks every model that has a `toolbar`, and sets the locals `sva_n` (tagged actions), `sva_desc`, `sva_name` (`|`-joined `name` args) and `sva_save` (`|`-joined SaveTool filenames) with `Macro.setLocal`. The cases call it through one-line `python: _sva_actions()` statements inside the gated block. It runs no Stata command, no shell and no `eval`, and echoes no page text.

## TDD test stubs

### Regression tests, new `test/test_export_svg.py` (red at `batch-19-base` unless marked guard; 54-01)

Imports: `dash_render as dr`; from `test_toolbar`: `_names`, `_NINE`; from `test_mode_parity`: `_render_pair`, `_spec`; from `test_server_layer_defects`: `plot_for`; from `test_saved_filter_layers`: `_render`, `_move`, `_MOVES`; from `test_mode_parity`: `_served_after_move`; `js_runner.requires_node`; Chrome classes import S04's `_CspProbe` from `test_csp_browser` and skip only as that module does (red under `DASH_STRICT=1`).

- Test: `dr._DASH_SVG_SAVE_JS` is a str holding `find_one`, `export("svg")`, `to_blob`, `URL.createObjectURL`, `window.alert` and no `eval(`, `Function(`, `innerHTML`, `fetch(` — `TestTheConstants::test_the_code_is_fixed_and_plain`
- Test: `dr._DASH_SVG_SAVE_ICON` starts `data:image/svg+xml;base64,`, decodes to an `<svg` document, is at most 1,024 characters — `TestTheConstants::test_the_icon_is_a_small_data_uri`
- Test: `_dash_name_save(gridplot([[f1, f2]]))` leaves one SaveTool named `dashboard` and one `CustomAction` tagged `dash_svg_save`, `description == "Save as SVG"`, `callback.args["grid"] is grid`, `callback.args["name"] == "dashboard"`, `callback.code == dr._DASH_SVG_SAVE_JS`, placed after the SaveTool — `TestTheAction::test_a_grid_gains_one_action`
- Test: a bare `figure(tools=dr._DASH_FIGURE_TOOLS)` named `g1` gains one action with `name` `g1`, after the nine tools — `TestTheAction::test_a_bare_figure_gains_one_action`
- Test: calling `_dash_name_save` twice (`"g1"` then `"g2"`) leaves one action whose `name` is `g2` — `TestTheAction::test_a_second_call_adds_nothing`
- Test: a toolbar without a SaveTool, a `Div`, and `None` are returned unchanged with no action — `TestTheAction::test_no_save_button_no_action`
- Test: `"a/b"`, `"../x"`, `"<s>"`, 33 characters, `5` → `name` `dashboard` — `TestTheAction::test_only_a_stata_name_reaches_the_arg`
- Test (node): the JS stem rule and `_dash_save_filename` agree on 12 inputs (the five above, `"g1"`, `"_x"`, `"A9"`, `""`, `None`, `"é"`, `"a b"`) — `TestTheAction::test_js_and_python_agree_on_the_stem`
- Test (both modes): every toolbar holding a SaveTool holds exactly one tagged action and its `name` equals that SaveTool's `filename`, over the saved cases of `test_toolbar.TestTheSavedPage` (plain, tabs, by(), layout(bs), a KPI grid) and the served cases of `TestTheServedApp` — `TestEveryToolbar::test_one_action_beside_each_save[<case>-saved|served]`
- Test (both modes): a KPI card's Div carries no action; a tab strip carries none — `TestEveryToolbar::test_no_action_without_a_save[saved|served]`
- Guard: no figure in either mode has `output_backend == "svg"` — `TestNoSvgBackend::test_figures_keep_canvas_or_webgl[saved|served]`
- Test: the generated app, executed, defines `_DASH_SVG_SAVE_JS` and `_DASH_SVG_SAVE_ICON` equal to the module's — `TestTheServedCopy::test_the_app_defines_the_names`
- Guard (passes at the base): the installed BokehJS bundle (`bokeh.util.paths.bokehjs_path() / "js" / "bokeh.min.js"`; `bokehjsdir()` is deprecated since Bokeh 3.4 and warns) contains `find_one`, `to_blob` and `export(` — `TestTheBundle::test_the_calls_exist_in_the_shipped_bokehjs`
- Test (Chrome): saved page `scatter mpg weight, mcolor(#123456)` with a `filter(foreign)` dropdown: click the action in a page task (`_CspProbe.in_task`), capture the blob (patched `URL.createObjectURL` records type, size and text); `image/svg+xml`, download name `dashboard.svg`, 0 `<image>`, 74 marker paths (elements whose fill is `#123456` or `rgb(18,52,86)`; ticks and axes, which a move re-finishes, are not counted); move the dropdown to Foreign and click again: 22 — `TestInChrome::test_saved_page_before_and_after_a_move`
- Test (Chrome): served doc (`_served_page` pattern of test/test_by_scales_chrome.py:48, with `_DASH_CSP_SERVED_META` and a nonce injected as S04's builder does) before and after `_served_after_move` to Foreign: 74 and 22 marker paths, counted as above — `TestInChrome::test_served_doc_before_and_after_a_move`
- Test (Chrome): 12,000 rows (WebGL): vector, 0 `<image>`, at least 12,000 `<path>` — `TestInChrome::test_a_webgl_figure_exports_as_vector`
- Test (Chrome): `layout(bs)` with `g1` and a by() graph `g2`: downloads `g1.svg` and `g2.svg`; a subtitle and a note Label appear as `<text>` — `TestInChrome::test_layout_bs_items_and_labels`
- Test (Chrome): with `Bokeh.index.find_one` patched to return null, a click raises exactly one alert (Page.javascriptDialogOpening) naming the save button, and no exception escapes — `TestInChrome::test_a_failure_is_said_once`

### Extensions

- `test/test_csp_browser.py` (S04's file), new class `TestSaveAsSvgUnderThePolicy`: saved pages `auto`, `bs`, `rich` and the served launcher app (`rich`): click each action in a page task; a blob of type `image/svg+xml` is created; `_CspProbe.violations()` is empty before and after; an injection afterwards is still blocked — `::test_the_action_runs_with_no_violation[auto|bs|rich|served]` (red: no action).
- `test/test_mode_parity.py` harness (not a new test): `_grid_toolbar` records `(type, filename, description, tags, sorted(callback.args) minus "grid", args["name"])` for a `CustomAction`, and `_tools` adds `description` and `tags` for a `CustomAction`, so a drift between modes fails `TestBothModesAgree`.

### Pinned tests to flip (R9; re-measured, never trusted)

- `test/test_toolbar.py::_assert_nine_tools`: after the nine, `HoverTool` any number and at most one `CustomAction` whose tags hold `dash_svg_save` (`Flipped: test/test_toolbar.py::_assert_nine_tools -- only HoverTool after the nine was wrong because a layout(bs) item's own toolbar now carries the Save as SVG action (register P1.28.7)`). Its four callers keep their assertions.
- `test/test_toolbar.py::TestTheHelpDocumentsTheToolbar::test_every_tool_has_a_row_in_order`: `rows == want + ["Save as SVG"]`.
- `test/test_toolbar.py::TestTheHelpDocumentsTheToolbar::test_the_mode_table_lists_the_toolbar_in_both_modes`: also one `Toolbar, save as SVG` row with `Yes Yes` (an added assertion, the PNG one kept).
- Re-measure at the base: any other test that counts a grid toolbar's non-proxy tools (`grep -n "toolbar.tools" test/*.py`) and flip it in place with its reason.

## Test plan

| What | How | Fixture / data | Both modes? |
|---|---|---|---|
| Constants, idempotence, name rule | pytest `TestTheConstants`, `TestTheAction` (node for the JS rule) | literal | n/a |
| Every toolbar | pytest `TestEveryToolbar`; `test_toolbar.py` flips | `test_toolbar` cases | yes |
| No backend | `TestNoSvgBackend` | toolbar cases | yes |
| Download and content, moves, WebGL, bs | Chrome `TestInChrome` | auto data, 12,000-row frame | yes |
| CSP | Chrome `test_csp_browser.py::TestSaveAsSvgUnderThePolicy` | S04's pages | yes |
| Bokeh internals | `TestTheBundle`; S41's list; Chrome under each verified minor | installed BokehJS | n/a |
| Parity | `test_mode_parity.py` with the extended harness | CORPUS | yes |
| Stata route | truth block SVA-01..03 | auto | saved |
| Help | `test_toolbar.py::TestTheHelpDocumentsTheToolbar`; S22's help tests | dash.sthlp | n/a |

**Acceptance criteria.**
- **AC-54.1** (BR-54.1, BR-54.2) `TestTheAction`, `TestEveryToolbar` and SVA-01..03 pass; `TestInChrome::test_layout_bs_items_and_labels` downloads the named files.
- **AC-54.2** (BR-54.3) `TestInChrome`'s move and WebGL tests pass in both modes, with no skip.
- **AC-54.3** (BR-54.4) `TestSaveAsSvgUnderThePolicy` reports zero violations on all four pages; `test_csp.py` (S04's hash and nonce tests) passes unchanged.
- **AC-54.4** (BR-54.5) `test_a_failure_is_said_once` passes; `TestTheBundle` passes under bokeh 3.8.0 (Stata's Python) and 3.9.0.
- **AC-54.5** (BR-54.6) `TestNoSvgBackend` and the unchanged PNG tests (`test_toolbar.py`, S04's `test_exports_still_work`) pass.
- **AC-54.6** (BR-54.7) the help tests pass; no line over 79 characters.
- **AC-54.7** Every flip has a `Flipped:` line, nothing is deleted, the full suite reports 0 failed, G7 prints 0 twice.

## Tasks

**Commit boundary.** Tasks 54-01 to 54-09 form the one commit, made by 54-09 on `wp30-s54` with the subject `Add a Save as SVG action to every dashboard toolbar in both modes (WP-30 P1.28b)`. `$S` is `/private/tmp/claude-501/-Users-billy-Desktop-Programs-StataPrograms-d-dash/55d6df3b-6200-4eb1-99b7-fa28b88519a2/scratchpad/wp30`, `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s54`, `$SLOT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh`. A cscript runs through the driver: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" "<script>.cscript" > "$S/run_<script>.do"`, then `WP30_ONLY=S54 "$SLOT" "$S" "$S/run_<script>.do"`. Each task appends the files it changed to `$S/54-files.txt`.

<task type="auto" id="54-01">
  <name>Write the failing pytest regressions</name>
  <files>test/test_export_svg.py, test/test_csp_browser.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Check `git -C "$WT" rev-parse HEAD` equals `cat "$S/batch-19-base.txt"` and `git -C "$WT" branch --show-current` prints `wp30-s54`; stop otherwise. Create `test/test_export_svg.py` with every stub of "Regression tests", naming `dr._DASH_SVG_SAVE_JS` and `dr._DASH_SVG_SAVE_ICON` so they fail with AttributeError now; Chrome classes reuse S04's `_CspProbe` and page builders from `test/test_csp_browser.py` and follow its skip rule. Append the class `TestSaveAsSvgUnderThePolicy` to `test/test_csp_browser.py` without editing S04's classes. Extend `test/test_mode_parity.py`'s `_grid_toolbar` and `_tools` as "Extensions" says (harness only; no CORPUS case). Run `python3 -m pytest test/test_export_svg.py "test/test_csp_browser.py::TestSaveAsSvgUnderThePolicy" -q -n0 -p no:cacheprovider -rf > "$S/54-new.log" 2>&1` with Chrome present. Write `$S/54-P1.28b-failure.txt`: the base sha, one line per failing node with its first error line, then "Guards (pass at the base)" with `TestNoSvgBackend` and `TestTheBundle`. Edit no shipped file; do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED "$S/54-new.log"` is at least 15; `grep -c "SKIPPED" "$S/54-new.log"` prints 0; `python3 -m pytest "$WT/test/test_mode_parity.py" -q -n 6 -p no:cacheprovider` reports 0 failed (the harness change alone is green at the base); `git -C "$WT" diff --name-only -- dash_render.py dash.sthlp` prints nothing.]]></verify>
  <done>Every pytest regression of this section existed and was shown failing on the unmodified tree, with the failure text saved.</done>
</task>

<task type="auto" id="54-02">
  <name>Write the Stata route truth cases</name>
  <files>test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Between S01's `S54 start` and `S54 end` lines of `test/test_wp30_truth.cscript`, add SVA-01..SVA-03 of "Stata truth", printing `SVA-nn PASS: …` through `_w30_expect`/`_w30_done`, writing only under `` `w30_work' `` and erasing what they wrote before the end line; the "Helper" `python:` block of "Stata truth" goes directly above the S54 header (any Stata helper program there declares `version 19`). Run the block through the driver with `WP30_ONLY=S54` on the unmodified shipped files. Append each `SVA-nn FAIL` line to `$S/54-P1.28b-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -cE "SVA-0[12] FAIL" "$S/run_test_wp30_truth.log"` prints 2; `grep -c "SVA-03 PASS" "$S/run_test_wp30_truth.log"` prints 1; the log has no `SKIP`; `python3 -m pytest "$WT/test/test_cscript_hygiene.py" -q -n0 -p no:cacheprovider -k Wp30` reports 0 failed.]]></verify>
  <done>The Stata-route cases were in S54's truth block and shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="54-03">
  <name>Add the action to the save helper</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn in the task log that `_dash_name_save` is CRITICAL (11 impacted) and `_glyph_layer_lines` HIGH (4). Add TR-54.1's `_DASH_SVG_SAVE_JS` and TR-54.2's `_DASH_SVG_SAVE_ICON` directly after `_DASH_SAVE_NAME_RE`, each with its `#:` comment. Edit `_dash_name_save` exactly as TR-54.3 says (the tagged action only beside a SaveTool, replaced not duplicated, docstring paragraph). Add TR-54.4's constants line after `"_DASH_SAVE_NAME_RE",` in `_glyph_layer_lines`' constants tuple. Edit nothing else in dash_render.py.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "$WT/test/test_export_svg.py" -q -n0 -p no:cacheprovider -k "Constants or Action or EveryToolbar or ServedCopy or Bundle or NoSvgBackend"` reports 0 failed; `python3 -m pytest "$WT/test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" "$WT/test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads" -q -n0 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>Every toolbar holding a save button carried exactly one Save as SVG action in both modes, and the served app defined the new constants.</done>
</task>

<task type="auto" id="54-04">
  <name>Prove the action in Chrome</name>
  <files>none</files>
  <action><![CDATA[
    Run `python3 -m pytest "$WT/test/test_export_svg.py::TestInChrome" "$WT/test/test_csp_browser.py" -q -n0 -p no:cacheprovider -rA > "$S/54-chrome-39.log" 2>&1` (bokeh 3.9.0), then the same with `/opt/anaconda3/bin/python3` (bokeh 3.8.0, Stata's Python) into `$S/54-chrome-38.log`. If S41 verified bokeh 3.10 and left its scratch venv, run once more with that venv's python into `$S/54-chrome-310.log`. A failure in the callback is fixed in `_DASH_SVG_SAVE_JS` only (TR-54.1's shape kept), never by relaxing a policy; a CSP violation stops the task and is reported.
  ]]></action>
  <verify><![CDATA[Each log ends with `passed` and no `failed`, `skipped` or `error`; `grep -c "TestSaveAsSvgUnderThePolicy" "$S/54-chrome-38.log"` is at least 4 PASSED lines under `-rA`.]]></verify>
  <done>The action downloaded a vector SVG that followed filter moves in both modes, under both policies with no violation, on every verified Bokeh installed here.</done>
</task>

<task type="auto" id="54-05">
  <name>Extend the Bokeh internals list</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Check `grep -n "^_DASH_BOKEH_INTERNALS" "$WT/dash_render.py"` finds S41's tuple; if it is absent or not a tuple of string triples, stop and report to the orchestrator (S41's TR-41.18 promised it). Append TR-54.6's three triples verbatim at the tuple's end. Edit nothing else in dash_render.py and do not edit `test/test_bokeh_internals.py`.
  ]]></action>
  <verify><![CDATA[`python3 -c 'import sys; sys.path.insert(0, sys.argv[1]); import dash_render as d; print(sum("S54" in e[0] for e in d._DASH_BOKEH_INTERNALS))' "$WT"` prints 3; `python3 -m pytest "$WT/test/test_bokeh_internals.py::TestTheInternalsList" -q -n0 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>S41's internals list named the three BokehJS calls the action uses, each with its guard and its test.</done>
</task>

<task type="auto" id="54-06">
  <name>Flip the nine-tool and help pins</name>
  <files>test/test_toolbar.py</files>
  <action><![CDATA[
    Flip `_assert_nine_tools` and the two help tests exactly as "Pinned tests to flip" says, each with a comment naming WP-30 P1.28b and the reason, and re-measure `grep -n "toolbar.tools" "$WT"/test/*.py` for any other count of a grid's non-proxy tools; flip each failing one in place. Write the `Flipped:` lines to `$S/54-flips.txt`. Delete no test.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "$WT/test/test_toolbar.py" -q -n 6 -p no:cacheprovider -k "not test_every_tool_has_a_row_in_order and not test_the_mode_table_lists_the_toolbar_in_both_modes"` reports 0 failed (the two help tests pass after 54-07); `wc -l < "$S/54-flips.txt"` is at least 3.]]></verify>
  <done>The nine-tool contract admitted exactly one tagged action on a layout(bs) item's toolbar, with the reason recorded.</done>
</task>

<task type="auto" id="54-07">
  <name>Document the action in help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    Apply TR-54.7: the `Save as SVG` synopt row after `Save`; the sentence in "{ul:Saving an image.}"; the mode-table row after `Toolbar, save as PNG`; the sentence in S22's "{ul:Images.}" paragraph. Find each place by its text. Edit no other paragraph (R3); keep S22's "no SVG drawing mode" sentence; every new or changed line at most 79 characters; no tool or vendor name.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "$WT/test/test_toolbar.py" "$WT/test/test_help_conformance.py" -q -n 6 -p no:cacheprovider` reports 0 failed; S22's help test file (`grep -l "it_states_there_is_no_svg_drawing_mode" "$WT"/test/*.py`) passes; `awk 'length > 79' "$WT/dash.sthlp" | grep -ci "svg"` prints 0.]]></verify>
  <done>The help's toolbar table, image paragraph, mode table and Exporting text named the Save as SVG action and its files.</done>
</task>

<task type="auto" id="54-08">
  <name>Run the section's tests together</name>
  <files>none</files>
  <action><![CDATA[
    Run `test_export_svg.py`, `test_toolbar.py`, `test_csp.py`, `test_csp_browser.py`, `test_mode_parity.py`, `test_function_test_map.py`, `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `test_cscript_hygiene.py` and `test_tracking_documents.py` with `-n 6` (the Chrome files with `-n0`), and S54's truth block through the driver. Record each command's last line in `$S/54-local.txt`. Any failure is fixed in the task that owns its file before going on.
  ]]></action>
  <verify><![CDATA[Every line of `$S/54-local.txt` reports 0 failed and no skip; `grep -cE "SVA-0[1-3] PASS" "$S/run_test_wp30_truth.log"` prints 3; `grep -c "ALL CHECKS PASSED" "$S/run_test_wp30_truth.log"` prints 1; the log has no `SKIP`.]]></verify>
  <done>Every test of the section passed on the worktree, Chrome included, with no skip.</done>
</task>

<task type="auto" id="54-09">
  <name>Close the entry and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Read the title as `WP30_OPEN["P1.28b"]` ("Neither mode offers a vector export: the toolbar saves only a PNG at the screen's resolution"). Close that BUGS.md entry in place (`- [x]`) with "Notes: BUGS.md Resolution", today's date as `ddmonyyyy`. Delete the `"P1.28b"` key line of `WP30_OPEN`. Replace the one `<!-- WP-30 P1.28b -->` marker under `### New` in place with "Notes: CHANGELOG line". Run `test_tracking_documents.py` with `-n0`. Then `git -C "$WT" merge --no-edit main` (expect `Already up to date.`) and one full run `"$S/full_suite_queue.sh" "$WT" "$S/54-full.log"` in the background, read when its `exit=` line appears, never relaunched (E6 for the known flaky tests). Stage exactly the files in `$S/54-files.txt` plus these three and check `git -C "$WT" diff --cached --name-only` equals that list (G6). Write `$S/54-message.txt` per "Notes: commit message", check G7, confirm the branch, commit, check G7 again, and report the sha and message to the merger.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/54-full.log"` shows 0 failed and `exit=0`; `grep -c '<!-- WP-30 P1.28b -->' "$WT/CHANGELOG.md"` prints 0; `grep -c '^    "P1.28b": "' "$WT/test/test_tracking_documents.py"` prints 0; `git -C "$WT" log -1 --format=%s` ends `(WP-30 P1.28b)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Entry P1.28b was closed naming existing tests, its marker carried the change, and one green commit on wp30-s54 was ready for the merger.</done>
</task>

## Section completion criteria

- Every toolbar that holds a save button, in the saved page and the served app, holds exactly one tagged "Save as SVG" action named like its PNG, and no other toolbar does (`TestEveryToolbar`, SVA-01..03).
- The action downloads a vector SVG of the current view, before and after saved and served filter moves, WebGL included, with zero CSP violations under S04's policies, on every verified Bokeh installed (logs of 54-04).
- A failure shows one message; no figure has an SVG backend; the PNG save is unchanged.
- S41's internals list names the three BokehJS calls with their guards and tests.
- The help documents the action; `_assert_nine_tools` and the help tests are flipped with reasons; nothing is deleted.
- One green commit `(WP-30 P1.28b)` exists on `wp30-s54`; it closes the entry, deletes its key and replaces its marker.

## Notes

- **No new function.** The action is built inside `_dash_name_save`, so the served app gains no function name (R2 row S54: "`_dash_name_save`, 33352, in place") and S54's map anchors stay empty (S58 removes them, A148). If a reviewer wants a factored `_dash_svg_save_action`, it needs a functions-tuple entry after `"_dash_save_filename", "_dash_name_save",` and a map entry; not planned.
- **The anchor line.** R2 cites 33028 for `"_DASH_FIGURE_TOOLS", "_DASH_SAVE_NAME",`; at `c96facd` that line is 33027 and 33028 is `"_DASH_SAVE_NAME_RE",`. The new line goes after the latter so the WP-21 group reads as one; no other section uses this anchor.
- **Text in the SVG.** Bokeh writes each `<text>` twice in its SVG (research §3, cosmetic). S56's `text()` Labels are `Label` models, the class `TestInChrome::test_layout_bs_items_and_labels` already exports (subtitle, note); S56 lands after this section in the same batch, so its own Labels are first exported on the merged tree at batch 19's G8.
- **python_exec hazard.** SVA-01..03 use the scaffold's python gate; many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`. Check it after the slot run; a SKIP is not a pass.
- **Merge rules for the shared files.**
  - R1: S54's own truth block; no area cscript.
  - R2: `"_DASH_SVG_SAVE_JS", "_DASH_SVG_SAVE_ICON",` at S54's anchor (index.md's R2 row names only `_DASH_SVG_SAVE_JS` and cites 33028; both are reported in review-notes g09.md); `_dash_name_save` in place; three triples appended to S41's `_DASH_BOKEH_INTERNALS` (already copy-listed); no map key.
  - R3: "The toolbar" (S54's row and the "Saving an image" sentence), one sentence in S22's "Images" paragraph (S22's Boundaries hand it over), and **an R3 exception**: the `Toolbar, save as SVG` row of the Server Mode comparison table (:1505), whose owners (S04, S23, S41, S46) list no batch-19 section. The orchestrator allowed it; index.md's R3 table should name it (review-notes g09.md).
  - R4/R5: the one `P1.28b` marker under `### New`, the entry and its key.
  - R8: `test_mode_parity.py`'s `_grid_toolbar`/`_tools` harness extended; `ALLOWED`/`_MUST_WARN` untouched; no CORPUS case (S55 and S56 append theirs later in merge order; the merger keeps all).
  - R9: the three flips of `test_toolbar.py`. R10: no count pin moves. R12: no one-editor symbol is edited.
- **Landing (merger).** `gitnexus detect-changes --scope all --repo dash` must name `_dash_name_save`, `_glyph_layer_lines` and the two constants, plus `_DASH_BOKEH_INTERNALS` (S41's tuple, three triples appended), and test symbols of the staged files only. At 19.0, `_dash_name_save` is the expected CRITICAL.
- **Commit message.** Subject as in "Commit boundary". Body, in order: `$S/54-P1.28b-failure.txt`; the measured defect (Overview's block and the backend's `drawImage` TypeError); what changed and where (TR-54.1-TR-54.7, both modes through the shared helper); the threat closed (G9): "a hardened page carries a working vector export without any relaxed policy, inline script or data-to-code path"; then one line each: `Regression: test/test_export_svg.py::<Class>::<test> -- failed at <base sha> with <text>` per regression node, `Regression: test/test_csp_browser.py::TestSaveAsSvgUnderThePolicy::test_the_action_runs_with_no_violation -- failed at <base sha> with <text>`, `Regression: test/test_wp30_truth.cscript SVA-01 -- failed at <base sha> with <text>`; the `Flipped:` lines of `$S/54-flips.txt`; `BUGS.md: "Neither mode offers a vector export: the toolbar saves only a PNG at the screen's resolution" (closed)`. No tool or vendor name (G7).
- **BUGS.md Resolution** (one line, in place):

  ```
  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.28b). Every toolbar that holds a save button now holds one Save as SVG action (dash_render.py _dash_name_save, _DASH_SVG_SAVE_JS, _DASH_SVG_SAVE_ICON; copied into the served app by name), which asks BokehJS for a vector SVG of the figures that toolbar's PNG save writes and downloads it as dashboard.svg or <name>.svg, from the current view after saved and served filter moves, WebGL figures included, under the saved page's hashed and the served page's nonced Content-Security-Policy with no violation; no figure is drawn with an SVG backend, which breaks the grid's PNG save; the three BokehJS calls are on the Bokeh internals list. Pinned by test/test_export_svg.py::TestEveryToolbar::test_one_action_beside_each_save, test/test_export_svg.py::TestInChrome::test_saved_page_before_and_after_a_move, test/test_export_svg.py::TestInChrome::test_served_doc_before_and_after_a_move, test/test_csp_browser.py::TestSaveAsSvgUnderThePolicy::test_the_action_runs_with_no_violation, test/test_wp30_truth.cscript SVA-01. Residual, deferred (WP-30): a do-file cannot write an image of a dashboard (the deferred platform package, M8); the image leaves out KPI cards, the title, filters and tab strip, as the PNG does (P3.11).
  ```
- **CHANGELOG line** (replaces the marker in place, under `### New`):

  ```
  - Every dashboard toolbar, saved and served, has a Save as SVG button beside the PNG save: it downloads a vector SVG of the same figures (dashboard.svg, or g1.svg for a layout(bs) item), drawn from what is on screen after any filter move. Before, the only image was a PNG at the screen's resolution. dash draws no figure with an SVG backend, which would break the PNG save. (WP-30, P1.28b)
  ```
- **Notes for the closeout (S58; A145).**
  - **GAPS2.md E10** (:1205-1219): E10b is closed by `<sha>`: `- **Tracked:** Partly closed in WP-30, BUGS.md "<P1.28b title>", commit <sha>: Save as SVG on every toolbar; E10c (scripted export at a chosen size) stays in the deferred platform package.` E10a (KPIs and header in the image) stays with P3.11.
  - **GAPS2.md J7** (:1742-1752): its "SVG backend" step (J7-b) is answered by the action and recorded as rejected as written (register P1.28.2).
  - **DROPIN-REMAINING.md:162** (P1.28): "Closed by <S22 sha> and <sha> (WP-30 S22, S54); scripted export deferred (M8)."
  - **ROADMAP.md**: P3.11 notes the SVG has the PNG's omissions; the platform package keeps P1.28 B3.
  - **AGENTS.md invariant:** "the vector export is a client-side CustomAction added only by `_dash_name_save`; never set `output_backend='svg'` on a figure in a grid."
  - **Unverified:** the action on Windows, Linux and Safari (the deferred platform package, M4); Bokeh 3.10 unless S41 verified it.
