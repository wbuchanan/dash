# Section 52: Saved-page JavaScript errors surfaced and sliders throttled

> Part of: WP-31 · GAPS3 rows: H1 (E11, E12 parts) · Risk: green · Batch: 17 · Depends on: 10 · Blocks: -- · Tasks: 3, 1 commit · Case-id prefix: U52

## Overview

**What is wrong today.** GAPS3 H1 (GAPS3.md:238): "saved-page JS errors fail silently (no `window.onerror`, the only catches swallow); saved sliders fire on every drag step (served uses `value_throttled`)." Evidence: `_FILTER_JS` (dash_render.py:24612-25467) and `_BRUSH_JS` (:25467ff) run as the bodies of `CustomJS` callbacks with no try/catch; an exception thrown inside -- a column renamed by a hand-edited spec, a `TypeError` on an unexpected value -- propagates into BokehJS's signal dispatch and is logged to the browser console only, while the widgets and sources stay half-updated with no visible sign. `FilterBuilder.build_dropdown`, `build_slider`, `build_range` wire `widget.js_on_change("value", callback)` (:25624, :25688, :25753), so a slider drag runs the whole recompute -- now including S10-S28's refits -- at every pixel; the served app wires `value_throttled` where the widget has it (:50465-50473) and wraps the callback in `_dash_event_throttle` (:34781). The two brush gaps of H1 (a selection on bars/histograms; intersecting concurrent brushes) are S51's (E5, E9).

**After this section** every saved-page callback body (`_FILTER_JS`, and the brush script assembled in `_wire_brush_callbacks` :45345-45395) runs inside `try { ... } catch (e) { <write the escaped message into the error status Div>; throw e; }`: the first failure writes a one-line message into a hidden `Div` that becomes visible, carries `role="status" aria-live="polite" aria-atomic="true"`, and is placed in the filter row before the stale-cue status (or where it would be); the exception is rethrown so the console still shows it. A `window.onerror` and `unhandledrejection` handler registered through `doc.js_on_event("document_ready", CustomJS(...))` -- the existing nonce/hash path (`_dash_by_stack_hooks` :38391, wired at :44464 and :46123) -- writes any error outside a callback into the same Div. Saved sliders and range sliders fire on `value_throttled`; dropdowns keep `value`. No raw `<script>` is added; `_dash_seal_saved_page` (:4843) and test_csp.py stay green.

**Why these rows share this section.** Both are saved-page robustness fixes that touch the callback WIRING and the body WRAPPER, not the arithmetic; they are small enough for one green section and, being `_FILTER_JS`'s last editor in WP-31, they land after every estimator port (S10-S28) so the wrapper encloses the finished script.

**Test order and commit rule.** One cycle, one commit `(WP-31 H1)` (the index's entry id for this section's part of H1 is `H1`; S51's brush parts are `H2l`'s E5/E9 -- index manifest row 51 lists them there): 52-01 failing tests; 52-02 the wrapper, the Div, the document hooks, the throttle; 52-03 flips, cscript, help, close, commit.

### Section decisions (binding on the executor)

- **D-52.a. The wrapper lives INSIDE the `_FILTER_JS` literal**, as its first and last lines, so `cb.code == dr._FILTER_JS` (asserted by test_saved_filter_layers.py `_move` :140) stays true and every marker `js_runner` and the brush builder slice by is unmoved (they lie strictly inside the try block). The catch reads an arg `dash_error_status` guarded by `typeof dash_error_status !== "undefined" && dash_error_status` so a hand-built test harness without the arg still runs. The brush script is wrapped at its ASSEMBLY site (`code = (...)` at :45389-45393) by a new module function `_dash_js_guarded(body)` that returns `"try {\n" + body + "\n} catch (e) { dash_report_js_error(e); throw e; }"`, because `_BRUSH_JS` is S51's (batch 17's owner table: "link/brush machinery (`_dash_link_names`, `_BRUSH_JS`): 51"). `dash_report_js_error(e)` is declared in `_DASH_FMT_JS` (:23390; shared by both scripts; it already holds `dash_html_escape`) and uses `dash_html_escape`.
- **D-52.b. One Div per page, built in Python**, `Div(text="", visible=False, tags=["dash_error_status"], css_classes=["dash-error-status"])`, appended to `filter_row_widgets` by `_stale_cue_args`'s caller (`_build_filter_widgets` :45427 is R12-owned by S49 in batch 16, so S52 adds the Div in the same place `_stale_args` is merged: the loop at :45787-45795 sets `_cb.args["dash_error_status"] = _err_div` for every callback -- S52 edits ONLY those lines of `_build_filter_widgets`, as batch 17's owner of that function (the owner table names no other batch-17 editor; recorded in Notes). The Div's text is written by JS as `_DASH_JS_ERROR_HTML` (a module constant; `%s` replaced by the escaped message, bounded to 300 characters) -- `<p role="status" aria-live="polite" aria-atomic="true" style="margin:0;padding:2px 6px;background:#fde7e9;color:#5c0011;font-size:12px">The page's filter script stopped with an error: %s. Reload the page; if it recurs, rebuild the dashboard.</p>`; #5c0011 on #fde7e9 is about 10.5:1. The constant travels to JS by a `.replace("__DASH_JS_ERROR_HTML__", json.dumps(_DASH_JS_ERROR_HTML))` on `_DASH_FMT_JS`.
- **D-52.c. The window handlers are a `CustomJS` on `document_ready`**, built by `_dash_error_hooks(err_div)` returning `[CustomJS(args={"d": err_div}, code=...)]` that sets `window.onerror` and adds an `unhandledrejection` listener writing `d.text`/`d.visible` through `dash_report_js_error`; both saved assemblers (`_render_bootstrap_html` :44440-44466, `_assemble_layout` :46100-46125) build the `_hook_doc` when `_by_hooks or _err_hooks` and pass `*_by_hooks, *_err_hooks`. The `CustomJS` is serialised in the Bokeh JSON, so no new inline script and no CSP change (bokeh-web §8).
- **D-52.d. Sliders fire on release.** `build_slider` and `build_range` wire `js_on_change("value_throttled", callback)`; `build_dropdown` keeps `"value"`. The callback reads every widget's `.value` (`dash_filter_mask`), equal to `value_throttled` at release. The served app is unchanged.

## Risk: [green] -- wiring and a wrapper; the arithmetic is untouched

**Risk factors.** (1) A test asserting `change:value` on a slider's `js_property_callbacks`. (2) The brush builder slices `_FILTER_JS` by markers; the wrapper's `try {` line must precede `// ---- KPI recompute, shared by` and its `} catch` follow the stale block. (3) `html_attributes` is not used (the role lives in the Div's inner `<p>`, as `_DASH_STALE_STATUS_HTML` does), so Bokeh 3.8 compatibility holds.

**Mitigation.** (1) grep `js_property_callbacks` in test/ (test_help_claims_4.py:1862, test_filter_exclude.py:253, filter_truth_check.py:129/237 read both keys) and flip the one that pins `change:value` on a slider. (2) `TestTheWrapper::test_markers_lie_inside_the_try`. (3) `test_csp.py` and `test_saved_stale_cue.py::TestTheCueArgs` re-run.

## Dependencies

- **Depends on: 10** (the script's shape with the fit branches; S52 must land after S28 so the wrapper encloses the final script -- batch 17 is after batch 9).
- **Blocks: none.** S54 (accessibility, batch 18) may add `html_attributes` to the Div's host; it reads the tag `dash_error_status`.
- **Parallel batch: 17** with S50 (KPI statistics) and S51 (link/brush machinery). Merge order 50, 51, 52 (index). S52 is batch 17's `_FILTER_JS` editor and the only one touching `_build_filter_widgets`' arg loop and the two assemblers' hook lines; S51 edits `_BRUSH_JS`'s body and `_dash_link_names`, not `_wire_brush_callbacks`' `code = (...)` assembly? It may: `_wire_brush_callbacks` (:45345) is where the brush callbacks are built. D-52.a's wrap is one line around the existing `code = (...)` expression (`code = _dash_js_guarded(...)`) -- if S51's diff touches the same statement the merger applies S52's line after S51's (merge order 51 then 52) and the wrap encloses S51's text.

## Evidence

- `_FILTER_JS` :24612 opens `_FILTER_JS = (_DASH_FILTER_MASK_JS + """` and closes at :25467 `""").replace("__DASH_ROW_ID__", json.dumps(_ROW_ID_COLUMN))`; the body's first statement is `const orig = orig_source.data;` (:24616) and its last block is the stale marking (:25377-25466).
- `_wire_brush_callbacks` :45345-45395: `code = ('const ROW_ID = "%s";\n' % _ROW_ID_COLUMN + "const kpi_config = JSON.parse(kpi_config_json);\n" + _DASH_FMT_JS + _helpers + _pctl + _BRUSH_JS)`.
- `FilterBuilder.build_dropdown` :25525 (`js_on_change("value", callback)` :25624), `build_slider` :25627 (:25688), `build_range` :25692 (:25753).
- Served wiring :50465-50473 (`value_throttled` when the widget has it).
- `_dash_by_stack_hooks` :38391; its wiring :44455-44464 and :46114-46123 (`_hook_doc.js_on_event("document_ready", *_by_hooks)`).
- `_stale_cue_args` :45817-45899 builds the stale status Div (`tags=["dash_stale_status"]`? -- read the tag at :45880-45899 and cite it) and `_build_filter_widgets` merges `_stale_args` into every callback's args at :45790-45795.
- `_DASH_FMT_JS` :23390-24500 holds `dash_html_escape` (:24345).
- bokeh-web.md §8: "wrap each `_FILTER_JS` body in try/catch writing a `role="status"` Div; BokehJS does not swallow CustomJS exceptions; `CustomJS` runs via `new Function`, already permitted by the policy."
- test_csp_browser.py:239 listens to `Runtime.exceptionThrown` -- the harness a Chrome check can reuse.
- Pins to flip: any test asserting a saved slider's callback key is `change:value` (grep); `test_help_conformance` pin of the table line `A slider recomputes{col 38}at every step{col 59}when released` (dash.sthlp:1947).

## User stories

- **US-52.1** As a reader of the saved file, I want to be told when a filter move failed so that I do not read a half-updated dashboard as the truth.
- **US-52.2** As a screen-reader user, I want that message announced.
- **US-52.3** As a reader dragging a slider, I want the page to recompute when I release it, not at every pixel.

## Business requirements

- **BR-52.1** When a saved-page callback throws, a visible status line names the failure in plain words, is announced (`role="status" aria-live="polite"`), and the error still reaches the console.
- **BR-52.2** An error outside a callback (a Bokeh load fault, a rejected promise) is reported the same way.
- **BR-52.3** A saved slider or range slider recomputes once per release; a dropdown on each change.
- **BR-52.4** The help's table says a slider recomputes "when released" in both modes.
- **BR-52.5** No new inline script; the page's CSP hashes are unchanged in kind; `_dash_seal_saved_page` accepts the page.

## Technical requirements

- **TR-52.1** `_DASH_JS_ERROR_HTML` (module constant after `_DASH_STALE_STATUS_HTML` :1910; copy-list entry after `"_DASH_LOWESS_JS_MAX_OPS",`): D-52.b's text with `%s`.
- **TR-52.2** In `_DASH_FMT_JS`, after `dash_html_escape` (:24345-24353):
  ```js
  // WP-31 H1: a callback's failure, written into the page's error status
  // Div (built in Python; `d' is the model) as escaped text, at most 300
  // characters of the message; the error is rethrown by the caller.
  const _DASH_JS_ERROR_HTML = JSON.parse('__DASH_JS_ERROR_HTML__');
  function dash_report_js_error(e, d) {
      const div = d || ((typeof dash_error_status !== "undefined") ? dash_error_status : null);
      if (!div) return;
      let msg = "";
      try { msg = String((e && e.message) ? e.message : e); } catch (_x) { msg = "error"; }
      if (msg.length > 300) msg = msg.slice(0, 297) + "...";
      div.text = _DASH_JS_ERROR_HTML.replace("%s", dash_html_escape(msg));
      div.visible = true;
  }
  ```
  and `_DASH_FMT_JS`'s definition gains `.replace("__DASH_JS_ERROR_HTML__", json.dumps(_DASH_JS_ERROR_HTML))` -- check how `_DASH_FMT_JS` is closed (:24500) and whether it already has a `.replace` chain; `json.dumps` of the constant yields a double-quoted JSON string, which inside the single-quoted `JSON.parse('...')` is safe only if the constant holds no `'`: it does not (D-52.b's text uses no apostrophe except "page's" -- REWRITE the constant to avoid apostrophes: "The filter script of this page stopped with an error: %s. Reload the page; if it recurs, rebuild the dashboard.").
- **TR-52.3** `_FILTER_JS`: the body (after `_DASH_FILTER_MASK_JS +`, i.e. the first line of the triple-quoted literal) opens with `try {` on its own line and closes, after the stale block's final `}` (:25466), with `} catch (e) { dash_report_js_error(e); throw e; }`. `_DASH_FILTER_MASK_JS` (function declarations) stays outside the try. `dash_own_col` and `dash_join_rebuild` are function DECLARATIONS inside the try block: in strict mode a block-level function declaration is block-scoped -- the brush builder's slice and js_runner's harness copy them into their own scope, unaffected; the page's own script declares and uses them inside the same block. Verify with `TestTheWrapper::test_the_page_script_runs_under_node_wrapped` (a full `JsSession` move).
- **TR-52.4** `_dash_js_guarded(body)` (module function after `_dash_seal_saved_page`? No -- after `_DASH_FMT_JS`'s definition, as a plain function; copy-list entry not needed: only the saved builder calls it) and its use in `_wire_brush_callbacks`: `code = _dash_js_guarded('const ROW_ID = ...' + ... + _BRUSH_JS)`.
- **TR-52.5** `_dash_error_hooks(err_div)` (module function beside `_dash_by_stack_hooks` :38391): returns `[CustomJS(args={"d": err_div}, code=_DASH_FMT_JS + "\nwindow.onerror = function (msg, src, line, col, err) { dash_report_js_error(err || msg, d); };\nwindow.addEventListener('unhandledrejection', function (ev) { dash_report_js_error(ev && ev.reason ? ev.reason : ev, d); });")]`. Both assemblers: `_err_hooks = _dash_error_hooks(_err_div) if _err_div is not None else []`, build the hook doc when `_by_hooks or _err_hooks`, and `js_on_event("document_ready", *_by_hooks, *_err_hooks)`. The Div is found by tag among `all_models`' descendants (`[m for m in _dummy_col.references() if "dash_error_status" in getattr(m, "tags", [])]`, read before `_dummy_col.children = []`).
- **TR-52.6** `_build_filter_widgets` (:45427): after `_stale_args` is built, `_err_div = Div(text="", visible=False, tags=["dash_error_status"], css_classes=["dash-error-status"])` is created when the page has at least one filter callback, appended to `filter_row_widgets` directly BEFORE the stale status Div when present (else where the stale Div would go, before the CSV button -- read `_stale_cue_args`'s placement at :45890-45899), and `_cb.args["dash_error_status"] = _err_div` is set in the per-callback loop at :45787. `_wire_brush_callbacks` sets the same arg on each brush callback (it has access to `self.filter_row_widgets`? -- read where the Div can be reached; store it as `self.error_status_div` on the renderer in `_build_filter_widgets`, None when no filter).
- **TR-52.7** `build_slider` (:25688) and `build_range` (:25753): `widget.js_on_change("value_throttled", callback)`. Docstrings: "fires on release, as the served app's does (WP-31 H1)".
- **TR-52.8 Flips**: the `change:value` pin on a saved slider (grep); the help conformance pin for the table line.
- **TR-52.9 Help**: dash.sthlp:1947 `{col 5}A slider recomputes{col 38}when released{col 59}when released`; add to the Server Mode table a line `{col 5}Script errors shown{col 38}status line{col 59}status line` after "Health endpoint"? -- the served app's error path is Bokeh's own logging plus the "Updating..." cue; write `{col 5}Script errors shown{col 38}status line{col 59}server log` instead. Add one sentence to the paragraph after the table: `If the page's script fails during a move, a status line under the filters says so (a screen reader announces it) and the browser console holds the error.`
- **TR-52.10 Tests**: `test/test_saved_page_errors.py` (new; see stubs). `function_test_map.py`: `_dash_js_guarded`, `_dash_error_hooks` -> their tests.

## Boundaries

Do not edit `_BRUSH_JS`'s text (S51), `_dash_link_names`, `dash_filter_mask`, any estimator branch, `_stale_cue_args`' models, the served template (`_generate_app_source`), the CSP constants (`test_csp.py::TestThePolicyConstants` pins them), `_dash_seal_saved_page`.

## Stata truth

No twoway truth (a dashboard behaviour). Cases in `test/test_e2e_filters.cscript` (the saved-page filter area script), ids `U52-k`, appended after its last case block:
- **U52-01** `sysuse auto; dash scatter mpg weight, filter(price, type(slider)) saving(<work>/u52.html)`: the saved HTML holds exactly one `dash-error-status` class and one `"change:value_throttled"` callback key (`cert_file_has` on the file with `needle(change:value_throttled)` and `needle(dash-error-status)`), and no `"change:value"` key for a Slider (grep the serialised JSON for `"Slider"` and the key: use the python block to parse the Bokeh JSON out of the page and assert the Slider's `js_property_callbacks` keys are `["change:value_throttled"]`).
- **U52-02** the same with `type(dropdown)`: the Select keeps `"change:value"`.
- **U52-03** the page passes `_dash_seal_saved_page` (it was written: the file exists and `dash build` returned rc 0) and holds no `<script` without a hash the policy names (the python block runs `dash_render._dash_script_hashes` on the page and compares with the policy meta's hashes).

## TDD test stubs

### Regression tests, `test/test_saved_page_errors.py` (new; red at the batch-17 base)

Helpers from test_saved_filter_layers (`_render`, `_MOVES`), js_runner (`JsSession`, `run_js`, `requires_node`), test_mode_parity (`_spec`, `plot_for`, `_sc`).

- Test: the page has one Div tagged `dash_error_status`, hidden, before the stale status Div (or before the CSV button), and every filter callback and brush callback has `args["dash_error_status"]` as that Div -- `TestTheErrorDiv::test_one_div_per_page`, `::test_every_callback_carries_it`, `::test_no_div_without_a_filter`.
- Test: `_FILTER_JS` starts with `try {` and ends with the catch; every js_runner and brush marker lies between -- `TestTheWrapper::test_shape`, `::test_markers_lie_inside_the_try`; the full page script runs under node through `JsSession` after a move -- `::test_the_page_script_runs_under_node_wrapped` (guard after the fix: a `SyntaxError` in the wrapper would fail it).
- Test: a callback whose code is `_FILTER_JS` with an injected throw (`code.replace("const orig = orig_source.data;", "throw new TypeError(\"boom <b>\");")`) run under `JsSession` leaves the Div visible with text holding `boom &lt;b&gt;` and the `role="status"` paragraph, and node exits non-zero (rethrown) -- `TestAThrowingCallback::test_the_div_reports_it` (the runner's `assert res.returncode == 0` must be relaxed for this test: add `JsSession.run_code(..., expect_error=True)` returning the output written BEFORE the throw -- the RUNNER must write `out` in a `finally`; S52 owns js_runner this batch: wrap the `new Function(...)` call in `try { ... } finally { <write out> }` and set `process.exitCode = 1` in a catch, and give `run_code` the `expect_error` flag).
- Test: a message over 300 characters is cut to 297 and "..." -- `::test_long_message_is_bounded`; a message with `__proto__` or HTML is escaped text -- `::test_hostile_message_is_text`.
- Test: the brush callback's code is wrapped (`code.startswith("try {")`, ends with the catch) -- `TestTheBrushWrapper::test_shape`.
- Test: `_dash_error_hooks` returns one CustomJS with the Div as arg `d` whose code sets `window.onerror` and adds `unhandledrejection`; both saved assemblers wire it on `document_ready` (read the rendered page's JSON for the `document_ready` event callback list; one entry per hook) -- `TestTheWindowHooks::test_the_hook_model`, `::test_wired_in_both_layouts[layout]`; under node, a stubbed `window` object receives `onerror` and calling it writes the Div -- `::test_onerror_writes_the_div`.
- Test: the saved Slider and RangeSlider callbacks are under `change:value_throttled`, the Select under `change:value` -- `TestSlidersFireOnRelease::test_keys[kind]` (red: `change:value`).
- Test: a `JsSession` move through `w.value = ...` still recomputes (the test harness runs the callback directly) -- `::test_a_programmatic_move_still_runs` (guard).
- Test: the page's CSP hashes are unchanged in count and the page seals -- `TestTheCspIsUnchanged::test_no_new_inline_script` (compares `_dash_script_hashes(page)` count before/after: equal; runs the seal).
- Test: `_DASH_JS_ERROR_HTML` holds `role="status"`, `aria-live="polite"`, `aria-atomic="true"`, no apostrophe, exactly one `%s` -- `TestTheConstant::test_shape`.

### Cases in cscripts

- `test_e2e_filters.cscript` U52-01..U52-03.

### Flips

- The saved slider `change:value` pin (file found by grep in 52-01); the help table pin.

### Parity corpus

None (the served app is unchanged); `MOVE_CORPUS` already covers slider moves in both modes.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Div, args, wrapper shape | pytest `TestTheErrorDiv`, `TestTheWrapper`, `TestTheBrushWrapper` | -- | saved |
| A throwing callback | node `TestAThrowingCallback` | -- | saved |
| Window hooks | pytest + node `TestTheWindowHooks` | -- | saved |
| Slider keys | pytest `TestSlidersFireOnRelease`; cscript U52-01/02 | -- | saved (served unchanged) |
| CSP | `TestTheCspIsUnchanged`; test_csp.py; U52-03 | -- | saved |
| Optional Chrome check | test_csp_browser.py's harness: inject a throw and read `Runtime.exceptionThrown` plus the Div's text (only if the harness is available locally; not a gate) | -- | saved |

**Acceptance criteria**
- **AC-52.1** A throwing filter or brush callback leaves the error Div visible with the escaped message and rethrows.
- **AC-52.2** `window.onerror` and `unhandledrejection` are wired on `document_ready` in both saved layouts through CustomJS; no new inline `<script>`; test_csp.py green.
- **AC-52.3** Saved sliders fire on `value_throttled`; dropdowns on `value`; every existing saved-move test is green.
- **AC-52.4** U52-01..03 pass; help updated.

## Tasks

**Commit boundary.** 52-01 to 52-03 form the H1 commit (this section's part), subject `Report saved-page script errors in a status line and recompute sliders on release (WP-31 H1)`, on `wp31-s52`. Body: `<scratch>/52-01-failure.txt`; the measured defect (a thrown callback leaves no visible sign; a slider fires per step); the change (`_DASH_JS_ERROR_HTML`, `dash_report_js_error`, the wrapper, `_dash_js_guarded`, `_dash_error_hooks`, the Div in `_build_filter_widgets`, `value_throttled`); `Regression: test/test_saved_page_errors.py::TestAThrowingCallback::test_the_div_reports_it -- failed at <base> with <text>`; `Regression: test/test_saved_page_errors.py::TestSlidersFireOnRelease::test_keys[Slider] -- failed at <base> with change:value`; `Regression: test/test_e2e_filters.cscript U52-01`; `Flipped: <the slider key pin> -- change:value was the saved wiring; the served app fires on release, and now so does the page (H1)`; `Fixture: none`; `BUGS.md: "<H1 title>" (closed; the brush parts are S51's entries)`; `GAPS3: H1 Tracked` (Partly closed when S51 has not landed; Closed when both have -- S52 merges last in batch 17, so write Closed only if S51's commit is on the branch, else Partly closed naming S51's entries).

<task type="auto" id="52-01">
  <name>Write the failing error and throttle tests</name>
  <files>test/test_saved_page_errors.py, test/js_runner.py</files>
  <action><![CDATA[Create test/test_saved_page_errors.py with every stub (module docstring "WP-31 H1: saved-page script errors reach a status line; sliders recompute on release"). In test/js_runner.py: in `RUNNER`, wrap the `new Function(...)(...)` call as `let _err = null; try { new Function(...)(...); } catch (e) { _err = e; process.exitCode = 1; }` and keep the `out` collection and `process.stdout.write(JSON.stringify(out))` after it, then `if (_err) { process.stderr.write(String(_err && _err.stack || _err)); }`; give `JsSession.run_code` a keyword `expect_error=False`: when True, a non-zero exit is accepted and the parsed stdout returned (commit still applies); when False the existing assert holds. Add `test_js_runner.py::TestExpectError::test_a_throwing_callback_still_reports_state`. grep -n "change:value" test/*.py and record the file:line of any assertion on a saved Slider/RangeSlider in `<scratch>/52-flips.txt`. Run `python3 -m pytest test/test_saved_page_errors.py test/test_js_runner.py -q -n0 2>&1 | tee <scratch>/52-01-failure.txt`. Do not commit.]]></action>
  <verify><![CDATA[grep -c "FAILED\|ERROR" <scratch>/52-01-failure.txt is at least 12; test_js_runner.py's new test passes; nothing staged.]]></verify>
  <done>Every H1 regression test exists and fails at the batch-17 base; the node runner can report state from a throwing callback.</done>
</task>

<task type="auto" id="52-02">
  <name>Wrap the scripts, add the Div and hooks, throttle sliders</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[(1) `_DASH_JS_ERROR_HTML` after `_DASH_STALE_STATUS_HTML` (TR-52.1, no apostrophe) and its copy-list entry. (2) `dash_report_js_error` in `_DASH_FMT_JS` after `dash_html_escape` with the `JSON.parse('__DASH_JS_ERROR_HTML__')` constant, and the `.replace` on `_DASH_FMT_JS`'s definition (TR-52.2). (3) `_FILTER_JS`: `try {` as the literal's first line and `} catch (e) { dash_report_js_error(e); throw e; }` as its last (TR-52.3). (4) `_dash_js_guarded(body)` and its use in `_wire_brush_callbacks` (TR-52.4); set `_cb.args["dash_error_status"] = self.error_status_div` on each brush callback when the attribute is not None. (5) `_dash_error_hooks(err_div)` beside `_dash_by_stack_hooks` and the two assemblers' hook-doc edits (TR-52.5). (6) `_build_filter_widgets`: the Div, its placement, `self.error_status_div`, the per-callback arg (TR-52.6). (7) `build_slider`/`build_range`: `value_throttled` (TR-52.7). (8) function_test_map.py entries for `_dash_js_guarded` (`test/test_saved_page_errors.py::TestTheBrushWrapper::test_shape`), `_dash_error_hooks` (`::TestTheWindowHooks::test_the_hook_model`). Run `python3 -m pytest test/test_saved_page_errors.py test/test_js_runner.py test/test_saved_filter_layers.py test/test_saved_stale_cue.py test/test_filter_exclude.py test/test_statistical_helpers.py test/test_help_claims_4.py test/test_csp.py test/test_js_fit_refit.py -q`.]]></action>
  <verify><![CDATA[Green except the slider-key pin named in <scratch>/52-flips.txt and the help pin (flipped in 52-03); `python3 -c "import dash_render as d; js=d._FILTER_JS; b=js[len(d._DASH_FILTER_MASK_JS):]; print(b.lstrip().startswith('try {'), b.rstrip().endswith('} catch (e) { dash_report_js_error(e); throw e; }'))"` prints `True True`; `grep -c 'js_on_change("value_throttled"' dash_render.py` prints 2.]]></verify>
  <done>Every saved-page callback reports a failure into the status Div and rethrows, window errors are caught on document_ready, and sliders recompute on release.</done>
</task>

<task type="auto" id="52-03">
  <name>Flip, certify, document and commit H1</name>
  <files>test/test_e2e_filters.cscript, dash.sthlp, BUGS.md</files>
  <action><![CDATA[Flip the pin(s) in `<scratch>/52-flips.txt` in place (expected key `change:value_throttled` for Slider/RangeSlider; docstring reason). Append U52-01..03 to test/test_e2e_filters.cscript after its last case block (the script's own `*! U52-01..U52-03` header lines added to its case list; python helpers `_u52_keys(path)` parsing the Bokeh JSON out of the saved page -- the `<script type="application/json">` block -- and returning the widgets' `js_property_callbacks` keys by type, `_u52_hashes(path)`); run `scripts/stata_slot.sh <scratch>/s52 <scratch>/run_test_e2e_filters.do` with the two-line driver and `global dash_nobrowser 1`. dash.sthlp TR-52.9 and the conformance pin. Run `python3 -m pytest test/test_saved_page_errors.py test/test_help_conformance.py test/test_e2e_* -q` (the pytest mirrors of the e2e area, if any) and `python3 -m pytest test/test_saved_filter_layers.py test/test_mode_parity.py -k "slider or range" -q`. Close BUGS.md H1 (this section's part: Resolution names the wrapper, the Div, the hooks, `value_throttled`; "the brush parts are tracked by the H2l entries (section 51)"), rewrite the GAPS3 H1 Tracked line (Closed if S51's commit is on the branch, else Partly closed), replace the `<!-- WP-31 H1 -->` markers (Changed behaviour: `A saved page's slider recomputes when released, not at every step; a failing filter script shows a status line (WP-31, H1)`). Grep for `claude|anthropic`; commit.]]></action>
  <verify><![CDATA[pytest green; the slot log holds `U52-01 ok`..`U52-03 ok`; `git log -1 --format=%s` ends `(WP-31 H1)`; `grep -c "when released{col 59}when released" dash.sthlp` prints 1.]]></verify>
  <done>H1's error-surfacing and throttle parts are one green commit; the saved page reports script failures and sliders fire on release.</done>
</task>

## Section completion criteria

- AC-52.1 to AC-52.4; `_FILTER_JS` wrapped once; the brush code wrapped; one Div per page; two `value_throttled` wirings; the CSP tests green; the js_runner `expect_error` path tested.
- BUGS.md H1 closed (this part); GAPS3 H1 Tracked rewritten; marker replaced; help updated; one commit.

## Notes

- **Renderer order.** Saved only: the served app already throttles (`value_throttled` + `_dash_event_throttle`) and logs exceptions through Bokeh; nothing in the template changes. `_DASH_JS_ERROR_HTML` needs its copy-list entry only because `TestTheServedAppCarriesEveryName` walks module names GlyphMapper reads -- it does not read this one; the entry is still added for consistency with the stale constants (R2) and harmless.
- **R12 and the owner table.** Batch 17's table names `_FILTER_JS` error wrapper + slider throttle: 52. S52 also edits `_build_filter_widgets` (the per-callback arg loop and the Div) -- no other batch-17 section is listed as its editor (S49 edited it in batch 16); and the two saved assemblers' hook lines. Record both in the batch-17 merge note.
- **Strict mode and block-scoped functions (TR-52.3).** BokehJS wraps a CustomJS body as a strict function; a function declaration inside `try { }` is block-scoped there. Every call to `dash_own_col`, `dash_join_rebuild`, `dash_mask_for`, `dash_pctl`, `dash_kernel` and the S10-S28 helpers is INSIDE the same block, so nothing changes for the page; the harnesses copy the declarations into their own scope. `test_the_page_script_runs_under_node_wrapped` is the guard.
- **Security (rule 1).** The message is escaped by `dash_html_escape` and bounded to 300 characters; the constant holds no user text; no `javascript:` URL, no inline handler; the hooks are CustomJS models, hashed with Bokeh's JSON, not a `<script>`.
- **Decisions for maintainer ratification.** D-52.a (wrapper inside the literal; brush wrapped at assembly), D-52.c (window hooks via `document_ready` CustomJS), D-52.d (dropdowns keep `value`).
- **Cscript**: `cert_file_has` clobbers r(); read `r(found)` into a local at once. The saved page's JSON block is large: the python helper parses it with `json`, never regex over the whole file.
