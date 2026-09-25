# Section 03: Stateful node runner

> Part of: WP-28 · Gaps: none of its own (the test harness for C2, E2, X1) · Risk: green · Batch: 1 · Depends on: none · Blocks: 04, 05, 12, 17 · Tasks: 5, 1 commit (S03)


## Review amendments (Phase 4, 2026-09-25) — binding; they override any conflicting text below

> Batch **1** · Depends on **none** · Blocks **04, 05, 12, 17** · Risk **green** · Commits: one commit (S03)

- D4/C5: S04 and S05 depend on this section. `test/js_runner.py` exports the fixed names `NODE` (`os.environ.get("DASH_NODE") or shutil.which("node")`), `requires_node`, `run_js`, `run_filter_js_block`, `JsSession` and `mask_parity`. `test_statistical_helpers.py` re-imports `from js_runner import run_filter_js_block as _run_filter_js_block, requires_node, NODE as _NODE` (consistency #8: the two aliases stay as module names). S05's `test_histogram_edge_rule.py` imports `from js_runner import run_filter_js_block, NODE` and `from test_statistical_helpers import _hist`; S04's JS-twin tests use `run_js` and `requires_node`; S12 and S17 use `JsSession` and `mask_parity` by those names.
- feasibility #13/#31: the Risk factors name the S04/S05 imports and the alias rule.
- Q26 (AMEND-1 item G): `mask_parity` passes `filter_specs` and `widget_values` through to both twins unchanged, so it is the hook and needs no edit; S17 owns the grouping mechanism and adds `TestMaskParity::test_two_values_sharing_a_label_select_both` when it ships it. This section adds no grouping.
- D1/F-01 (as refined by AMEND-1 item J): task 03-01 does not commit. The section's one commit is made by 03-05 on the worktree branch `wp28-s03`, subject ending `(WP-28 S03)`; the merger lands it onto `s3-bugs` (index.md step 1).
- feasibility #2: 03-05 is named "Pin the E2 and X1 measurements".

Applies to every section:
- D1 (binding): tasks are work steps; commits are per gap (S01-S04: one each). The failing regression tests are written first and run against the unmodified tree; their output at 91d97be is recorded in the fix commit's message (Q24) and they are committed together with the fix, never alone (CLAUDE.md rule 4).
- D3 (binding): each gap's BUGS.md entry is appended at the END of BUGS.md in the closed form with `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.`
- D2 (binding): each closing task replaces the gap's `<!-- WP-28 <ID> -->` marker(s) that S01 placed in the CHANGELOG list named above; it does not add a new line elsewhere.
- D6 (binding): every Stata run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (see `index.md` step 0); no section launches the full cert suite or the release gate.
- D5 (binding): shared files follow merge rules R1-R6 in `index.md` (cscript registration and hygiene pins, copy lists and maps, help/CHANGELOG/BUGS.md, graph-key lists, fixtures, parity corpus).
- D7: XML fields holding `&`, `<` or `>` are CDATA-wrapped (done mechanically); task names over 8 words are shortened and `done` fields put in the past tense during the detailed fixer pass.

Detailed edits from `../review/consistency.md`, `../review/requirements-security.md` and `../review/feasibility.md` (as adjusted by `../review/DECISIONS.md`) were applied to this file in the fixer pass (2026-09-25); the text below conforms to this block.

## Overview

The saved page's filter logic is JavaScript (`_DASH_FILTER_MASK_JS`, `_FILTER_JS`, `dash_render.py:14110-14164` and `14177`), and the suite runs it under node rather than in a browser. Three runners do that today, each private to its test file, and two of them cannot chain moves: `test_filter_exclude.py:194-210` and `test_statistical_helpers.py:820-856` re-encode the Bokeh models from Python on every call, so node's writes vanish when its process exits and the second call starts from the build-time data (report B §2.3). GAPS2 E2 records the cost: "Served probe: price to [4000,5000], then foreign=1, then price back to its full range gives g1=3, g2=5, k1=3, where the current widgets imply 5 under either rule. The saved page behaves the same by construction; its multi-move sequence is unmeasured because the node harness cannot chain moves." Only `test_saved_filter_layers.py:181-214` writes node's result back into the Python models, so its calls chain; that runner is the base.

X1 has a second need. Its plan (step 3) is "Make `_DASH_FILTER_MASK_JS` and `_dash_dropdown_mask` one rule. Pin it with a pytest that runs both (node and pandas) on the same columns and compares the masks." DISCOVERY Q10 and Q15 settle both: "one pytest runs node and pandas on the same columns and compares masks", and "the node runner keeps ColumnDataSource state between calls so a sequence can be asserted; no browser needed. `TestFilterJavaScript`'s runner gains a stateful mode reused by E2, X1 and C2's recount tests."

After this section there is one module, `test/js_runner.py`, with `NODE`, `requires_node`, `run_js`, `JsSession(models)` (`.set`, `.run`, `.state`), `mask_parity(df, filter_specs, widget_values)` and the fragment runner `run_filter_js_block` the histogram recount tests already use; the three private runners import it and their tests assert exactly what they asserted before; sections 04 (`run_js`, `requires_node`), 05 (`run_filter_js_block`, `NODE`), 12 and 17 (`JsSession`, `mask_parity`) build on those names; and two measurements exist for the first time as tests: the saved page's state after E2's three-move sequence, and the two twins' masks on the same columns for X1's cases, each pinned at today's value with a note saying which section flips it.

**Test order (CLAUDE.md rule 7) and commit rule (D1): task 03-01 writes every failing test for the section**, runs them against the unmodified tree and saves the failure text to `<scratch>/03-01-failure.txt` -- it does not commit (a red tree is never committed, rule 4). Tasks 03-02 to 03-04 turn them green; 03-05 adds the two measurements, runs the full pytest suite once in the worktree and makes the section's ONE commit on the worktree branch `wp28-s03`, subject ending `(WP-28 S03)`, whose body opens with the saved failure text (S01 TR-01.9); the merger lands that commit onto `s3-bugs` (index.md step 1).

## Risk: [green] — test-only code; no renderer, ado or help change

**Why.** Nothing here reaches a user. The renderer's JavaScript and Python are run, not edited. The one way to do harm is to change what a migrated test asserts while claiming it is unchanged.

**Risk factors.**
1. `test_filter_exclude.py::TestThePrimarySourceFallback` (469-496) runs the callback three times on the **same** `primary` source; a runner that writes back would make the second run start from filtered data and the test would fail for a reason that is not a defect.
2. `shutil.which("node")` depends on `PATH`; under `make test` (`DASH_STRICT=1`) a skip is red (`test/conftest.py:127-131`, `297-304`), so a harness that skips when node is missing makes the strict run red on a machine without node, by design.
3. A `"__proto__"` column: written as an object literal it sets the prototype and the column is lost (`test_saved_filter_layers.py:186-189`, `dash_render.py:14211-14217`); the payload must be `JSON.parse`d.
4. Two batch-2 sections import this module's names by their exact spelling (feasibility #13/#31): S04's `test_display_format_writer.py` imports `run_js` and `requires_node`; S05's `test_histogram_edge_rule.py` imports `run_filter_js_block` and `NODE` from `js_runner` and `_hist` from `test_statistical_helpers`. The migration of `test_statistical_helpers.py` deletes its private `_NODE` and `_run_filter_js_block` definitions, so those two names must survive there as aliases of the module's names (C5), or a file written against either spelling fails to collect.

**Mitigation.** `JsSession.run(..., commit=False)` is a dry run that leaves the Python models untouched, and the `_run_callback` shim uses it; `NODE` honours a `DASH_NODE` override and the skip reason names it; the runner keeps the `JSON.parse` form and a test holds a `__proto__` column through a run; the public names are fixed in TR-03.1 (C5), the alias line of TR-03.2 is verbatim, and `TestTheMigratedShims::test_the_aliases_s05_imports_exist` asserts `test_statistical_helpers._NODE is js_runner.NODE` and `_run_filter_js_block is js_runner.run_filter_js_block`.

## Dependencies

- **Depends on:** none. The module runs the JavaScript the tree already ships.
- **Blocks:** 04 (the JS-twin tests run node through `run_js` and skip through `requires_node`), 05 (the histogram recount tests use `run_filter_js_block` and `NODE`), 12 (widget and tooltip format twins run under node; period-slider masks through `mask_parity`), 17 (E2's multi-move tests through `JsSession`; X1's parity test through `mask_parity`).
- **Parallel batch:** 1. **Can run with** every other batch-1 section; it edits four test files no other batch-1 section names in its own tasks (`test_saved_filter_layers.py`, `test_filter_exclude.py`, `test_help_claims_3.py`, `test_statistical_helpers.py`) and adds two. The batch-1 merge order is S01, S03, S02, S06, S07, S08, S09, S10 (C3): S03 lands before S07 and S10, which edit `test_statistical_helpers.py`, `test_saved_filter_layers.py` and `test_help_claims_3.py` after it, and before every batch-2 consumer.

Why: section 17 replaces `TestExcludeHoldsWhileItsOwnFilterMoves` with multi-move sequences (GAPS2 E2 plan 4) and writes X1's parity pin (plan 3); sections 04 and 05 need a runner that is not deleted under them; all need the names fixed here.

## Evidence

### The three runners (report B §2.3)

**`test/test_saved_filter_layers.py:85-214`** — the base. `_node` (85-91) `pytest.fail`s when node is absent; `_plain` (94-104) makes NaN `None` and a Timestamp epoch milliseconds through `dr._dash_json_value`; `_encode` (107-119) writes each Bokeh model once, by id, as a stand-in and references it as `{"__ref__": id}` so identity (`_srcs.includes(source)`) is what the page has; `_stand_in` (123-139) keeps `data` for a `ColumnDataSource`, `booleans` for a `BooleanFilter`, `text` for a `Div`, and `value`, `start`, `end`, `step`, `indices`, `width` for anything else; `_RUNNER` (142-179) rebuilds `REG` from the stand-ins, resolves refs, gives sources `selected` and `change.emit`, runs the body as BokehJS does:

```javascript
 172  new Function(...names, "cb_obj", "cb_data", '"use strict";\n' + RAW.code)(
 173    ...names.map((n) => args[n]), cb_obj, {});
```

and prints `data`/`booleans`/`text`/`width` per model. `_run` (181-214) writes the payload as `JSON.parse(...)` (186-189), runs node, and **writes back** (199-213):

```python
 199    for mid, state in out.items():
 200        m = objs[mid]
 201        if "data" in state:
 202            m.data = {c: [np.nan if v is None else v for v in col]
 203                      for c, col in state["data"].items()}
 204        elif "booleans" in state:
 205            m.booleans = list(state["booleans"])
 206        elif "text" in state:
 207            m.text = state["text"]
 208        elif "width" in state and isinstance(state["width"], (int, float)):
 209            m.width = state["width"]
```

Callers: `_move` (249-263) sets a `Select` by option label or a slider by value and runs `r.filter_callbacks[i]`; brush callbacks at 758 and 798 pass `cb_obj=src.selected`; 1205 (a date dropdown).

**`test/test_filter_exclude.py:103-210`** — `_node` (103-110), `_plain` (112), `_encode` (123-135, no `objs`), `_stand_in` (138-153, no `indices`/`width`), `_RUNNER` (156-192) with `null` for `cb_obj` and an output of **rows and row ids per source**:

```javascript
 185  for (const [id, o] of Object.entries(REG)) {
 186    if (o.__type__ !== "ColumnDataSource") continue;
 187    const cols = Object.keys(o.data);
 188    out[id] = {rows: cols.length ? o.data[cols[0]].length : 0,
 189               ids: o.data[RAW.row_id] || null};
 190  }
```

`_run_callback(args, code)` (194-210) writes `const RAW = <literal>` (not parsed) and returns that dict without writing back. Callers: `_saved` (224-247, one move per render), `TestThePrimarySourceFallback` (469-496, three runs on one `primary` source, expecting the build-time rows each time), and `test_help_claims_3.py` `_RUNNER_DIVS`/`_run_saved` (321-348), which appends Div text to the output and is used at 372 and 454 (`TestExcludeHoldsWhileItsOwnFilterMoves._saved`, 441-467).

**`test/test_statistical_helpers.py:817-884`** — `_NODE = _shutil.which("node")` (817); `_run_filter_js_block(kind, ac, vals, wts)` (820-856) cuts the histogram or kdensity branch out of `dr._FILTER_JS` by string index, runs it on literal `vals` with a stub `src`, and returns `src.data`; `@pytest.mark.skipif(_NODE is None, ...)` on `TestFilterJavaScript` (859-884), whose three tests compare the recount with `_hist` (768). Section 05 (C2) adds recount cases in its own module through `run_filter_js_block` and imports `_hist` from here.

### Other node sites, not migrated here

`test_help_claims_4.py:85-190` (`_RUNNER`, `_run_js`, `_run_js_full`, Div text and source data, no write-back), `test_export.py:34-77` (`_saved_mask` runs the `_FILTER_JS` prefix up to the mask; `_run_js` runs any script), and bare `shutil.which("node")` in `test_kpi_brush.py:246`, `test_kpi_values.py:339-710`, `test_linking_filters.py:50`, `test_scheme_review_fixes.py:620`. They are listed so a later section knows they exist; this section's scope is the three the brief names plus `test_help_claims_3.py`, which is built on the second. New WP-28 modules use `js_runner` (S04 through `run_js`, not `test_export._run_js`: D4).

### The two twins `mask_parity` runs

`_DASH_FILTER_MASK_JS` (14110-14164) defines `dash_filter_mask(orig, filter_specs, all_widgets)`: a dropdown at its sentinel restricts nothing, else `String(col[i]) !== val` drops the row (14138); a slider at its start restricts nothing, else `col[i] >= val` (14141-14146); a range at its full extent restricts nothing, else `lo <= col[i] <= hi` (14148-14156); a missing value fails every comparison. `_FILTER_JS` (14177) is that string plus the callback body, `const active = dash_filter_mask(orig, filter_specs, all_widgets);` (14186). The served twin is `_dash_frame_filter_mask(df, widgets)` (13950-13990): per widget it reads `_dash_var`, `_dash_ftype`, `_dash_sentinel`, `value`, `start`, `end` by `getattr`; a dropdown goes through `_dash_dropdown_mask` (17669-17675), which maps `_dash_option_value` over both sides. The widgets get those attributes at build time (`w._dash_sentinel`, `w._dash_ftype` at 17620-17621, `17634`, `17664`; the served template sets `widget._dash_var` and `_dash_exclude` at 26718-26719). The saved page's `filter_specs_json` (23707-23714) is `[{"varname", "type", "sentinel"}]`, one per widget in order; section 17 adds a `numeric` flag and a `groups` list to it (AMEND-1 item G) and the same dicts pass through `mask_parity` unchanged. The saved snapshot's columns go through `_dash_json_value` (13828-13862): a Timestamp becomes epoch milliseconds, `float("01")` becomes `1.0`, NaN and inf become `None` — the coercion report B §2.1 flags and section 17 changes; `mask_parity` feeds node the columns that way on purpose (TR-03.3), so the parity it reports is the page's, before and after that change.

Measured today (report B §2.1): string codes select the same rows in both modes ('01', '1', '1.0' all match option '1'); numbers 5e-05 and 1e21 select nothing on the saved page and one row served; `""` is listed and selectable.

### Strict mode and node

`test/conftest.py:252-254` (`_strict`), `280-294` (every skip recorded), `297-304` (the verdict: "a skip is not a pass"); `Makefile` sets `DASH_STRICT=1` for `make test` and `make test-dev`. node v24.13.1 is installed at `/Users/billy/.nvm/versions/node/v24.13.1/bin/node` (RESEARCH "Codebase Analysis"); whether `shutil.which` finds it depends on the shell's `PATH`.

### Existing tests that pin today's behaviour

None of this section's migrations changes an expected value. The tests added by 03-05 pin a measurement for section 17 to flip:

- `test/test_js_runner.py::TestMaskParity::test_a_dropdown_on_a_small_number_disagrees_today_x1` — asserts the two twins **differ** on 5e-05 (report B §2.1); section 17 turns it into an equality.
- `test/test_js_runner.py::TestASessionMeasuresE2::test_three_moves_leave_the_saved_page_where_measured` — asserts whatever 03-05 measures for the saved page after E2's sequence; section 17 flips it to `{"g1": 5, "g2": 5, "k1": "5"}` if the measurement differs from that, or keeps it as a regression guard if the saved page already gives it.

## User stories

- **US-03.1** As the maintainer, I want to move a saved page's widgets several times under node and read every source, filter, card and glyph as the page left them, so that a stale-state defect such as E2 is measured on the saved page and not only in the served app.
- **US-03.2** As the maintainer, I want one call that runs the saved page's mask and the served app's mask on the same columns and hands me both, so that X1's "compare numbers as numbers in both modes" is a one-line assertion.
- **US-03.3** As the maintainer, I want the three private runners to share one implementation so that a fix to how models are encoded (identity, `__proto__`, dates) reaches every test at once.
- **US-03.4** As the dashboard viewer, I want the page after several filter moves to show the rows the widgets now select, which this harness makes measurable so that section 17 can prove it.

## Business requirements

- **BR-03.1** A sequence of widget moves on a saved page can be run under node, and after each move every `ColumnDataSource`, `BooleanFilter`, `Div` and glyph width holds what the page's own callback left there, so the next move starts from it.
- **BR-03.2** A run can also be a dry run that leaves the Python models as they were.
- **BR-03.3** The saved page's mask and the served app's mask can be computed on the same data frame and the same widget values and returned side by side, for dropdown, slider and range filters, with missing values present.
- **BR-03.4** Every migrated test asserts the same values it asserted before, with the same test names.
- **BR-03.5** When node is absent, a test that needs it is skipped with a reason naming `DASH_NODE`, and under `DASH_STRICT=1` that skip is red.
- **BR-03.6** A column named `__proto__` survives a run.
- **BR-03.7** The saved page's state after E2's three-move sequence and the two twins' answers on X1's cases are recorded as tests, with the section that changes them named.
- **BR-03.8** The module's public names are the ones sections 04, 05, 12 and 17 are written against (C5), and the two spellings `test_statistical_helpers.py` used before still resolve there.

## Technical requirements

### TR-03.1 `test/js_runner.py` — the module

A helper module in `test/`, imported as `from js_runner import JsSession, mask_parity, run_filter_js_block, run_js, NODE, node, requires_node` after the `sys.path.insert(0, _HERE)` every test file already has (`test_saved_filter_layers.py:41-42`). It imports `dash_render as dr` for `_dash_json_value`, `_DASH_FILTER_MASK_JS`, `_FILTER_JS`, `_dash_frame_filter_mask` and `_ROW_ID_COLUMN`, and Bokeh's `Model`, `ColumnDataSource`, `BooleanFilter`, `Div`, `Select`, `Slider`, `RangeSlider`. It is not a test module (no `test_` prefix), like `test/responsive_probe.py`; `test/function_test_map.py` covers `dash_render.py` only (`test_function_test_map.py:62`), so no entry there; rule 3 is met by `test/test_js_runner.py`.

Public names (fixed, C5):

| Name | Signature | Behaviour |
|---|---|---|
| `NODE` | `str | None` | `os.environ.get("DASH_NODE") or shutil.which("node")`, evaluated at import |
| `node` | `() -> str` | `NODE`, else `pytest.skip("node is not installed; set DASH_NODE to its path (a skip is red under DASH_STRICT=1)")` |
| `requires_node` | `pytest.mark.skipif(NODE is None, reason="node is not installed; set DASH_NODE")` | for classes, as `TestFilterJavaScript` uses it |
| `run_js` | `(source: str, *, timeout=120) -> Any` | writes `source` to a temporary `.cjs`, runs `[node(), path]`, asserts rc 0 with `stderr[:3000]` in the message, returns `json.loads(stdout)`; the temp file is unlinked in `finally` |
| `plain` | `(v) -> Any` | `_plain` of `test_saved_filter_layers.py:94-104` |
| `encode` | `(v, models: dict, objs: dict) -> Any` | `_encode` of 107-119: one stand-in per model id, `{"__ref__": id}` references, lists and dicts recursed, `pd.Series`/`np.ndarray` as lists |
| `stand_in` | `(m, models, objs) -> dict` | `_stand_in` of 123-139 (the superset: `data`, `booleans`, `text`, and `value`, `start`, `end`, `step`, `indices`, `width`) |
| `RUNNER` | `str` | `_RUNNER` of 142-179 verbatim, with `cb_obj` |
| `JsSession` | class | below |
| `mask_parity` | `(df, filter_specs, widget_values, *, raw=False) -> tuple[list[bool], list[bool]]` | below |
| `run_filter_js_block` | `(kind, ac, vals, wts=None)` | `_run_filter_js_block` of `test_statistical_helpers.py:820-856`, verbatim, `node()` in place of `_NODE` |

`JsSession`:

- `JsSession(models)` — `models` is an iterable of Bokeh `Model`s the session reports on: typically `r.filter_callbacks` (each a `CustomJS` whose `args` reach the sources, widgets, filters and Divs), or a list of sources and Divs. The constructor stores them; nothing is encoded until a run. `self.runs` is the list of node outputs so far.
- `.set(widget, value) -> old` — `old = widget.value; widget.value = value; return old`. A `Select` takes its raw option value; label lookup stays in the caller (`_move`, `test_saved_filter_layers.py:254-259`).
- `.run(callback, cb_obj=None, *, commit=True) -> dict` — `self.run_code(callback.code, callback.args, cb_obj, commit=commit)`; asserts `callback.code` is a string.
- `.run_code(code, args, cb_obj=None, *, commit=True) -> dict` — encodes `dict(args)` (and `cb_obj`) into one `models` dict **from the Python models as they now are**, writes `const RAW = JSON.parse(<json of json>);\n` + `RUNNER`, runs node, and, when `commit` is true, writes every returned `data`/`booleans`/`text`/`width` back into the Python model exactly as `_run` does at 199-213 (`None` → `np.nan` in data). Returns node's output `{model id: {...}}` and appends it to `self.runs`. With `commit=False` the Python models are untouched (the dry run `TestThePrimarySourceFallback` needs).
- `.state() -> dict` — read from Python now (so it reflects every committed run): `{"sources": {id: dict(data)}, "booleans": {id: list}, "divs": {id: text}, "widths": {id: width}}` over the constructor's models and every model a committed run reached (`self._seen`, the `objs` of each run).
- `.rows(source) -> int` and `.ids(source) -> list | None` — the row count and `_ROW_ID_COLUMN` of a source as Python holds it now (the shape `test_filter_exclude.py` reports).

`mask_parity(df, filter_specs, widget_values, *, raw=False)`:

- `filter_specs`: the list `filter_specs_json` carries (23707-23714), one dict per widget, passed to both twins unchanged (`varname`, `type`, `sentinel`, and any key a later section adds -- S17's `numeric` and `groups`, AMEND-1 item G -- reaches both twins as given).
- `widget_values`: one entry per spec: a bare value (dropdown text, slider number, range `(lo, hi)`), or a dict `{"value": ..., "start": ..., "end": ...}`; when `start`/`end` are absent for a slider or range they default to the column's finite min and max, as `_dash_build_filter_widget` builds them (17630-17664).
- JS side: `orig = {col: [dr._dash_json_value(v) for v in df[col].tolist()] for col in df.columns}` (the saved snapshot's own encoding; with `raw=True`, `plain(v)` instead, which keeps strings as text); widgets `[{"value": v, "start": s, "end": e}]`; the script is `dr._DASH_FILTER_MASK_JS` + `const orig = <json>; const specs = <json>; const widgets = <json>; process.stdout.write(JSON.stringify(dash_filter_mask(orig, specs, widgets)));`, run through `run_js`.
- pandas side: for each spec a real Bokeh widget — `Select(value=v, options=[(v, str(v))])`, `Slider(start, end, value, step=1)`, `RangeSlider(start, end, value=(lo, hi), step=1)` — with `_dash_var = varname`, `_dash_ftype = type`, `_dash_sentinel = sentinel` set as dash sets them (and, once S17 lands, `_dash_groups` from the spec's `groups`, which this section neither sets nor reads); `dr._dash_frame_filter_mask(df, widgets)` → `.tolist()`.
- Returns `(js_mask, pandas_mask)`, both `list[bool]` of `len(df)`; a caller asserts equality or records a difference. It never itself asserts.
- Q26 (AMEND-1 item G): the case where two distinct numeric values share one display label and the mask must keep both is S17's; S17 adds `TestMaskParity::test_two_values_sharing_a_label_select_both` beside the cases below when it ships the grouping mechanism. This section provides the hook only.

### TR-03.2 Migrations (BR-03.4)

| File | Edit |
|---|---|
| `test/test_saved_filter_layers.py` | Delete `_node`, `_plain`, `_encode`, `_stand_in`, `_RUNNER`, `_run` (85-214); `from js_runner import JsSession`; `_run(code, args, cb_obj=None)` becomes a four-line shim: `return JsSession([]).run_code(code, args, cb_obj)`. The four callers (263, 758, 798, 1205) are unchanged. The module docstring's first paragraph gains one sentence naming `js_runner`. |
| `test/test_filter_exclude.py` | Delete `_node`, `_plain`, `_encode`, `_stand_in`, `_RUNNER` (103-192); `_run_callback(args, code)` becomes: `s = JsSession([]); s.run_code(code, args, commit=False)` then `{mid: {"rows": ..., "ids": ...}}` built from the run's output for every `ColumnDataSource` stand-in (rows = length of the first column, ids = `data.get(dr._ROW_ID_COLUMN)`), so its return is byte-for-byte what 185-190 printed. Keep `_node = js_runner.node` and `_encode = js_runner.encode` as module names because `test_help_claims_3.py` imports them until 03-04 (then drop). |
| `test/test_help_claims_3.py` | Delete `_RUNNER_DIVS` (321-327); `_run_saved(args, code)` becomes: `s = JsSession([]); out = s.run_code(code, args, commit=False)`; return `(sources, divs)` where `sources` is the rows/ids dict as above and `divs` is `{id: text}` for every Div stand-in in `out`. Callers at 372 and 454 unchanged. |
| `test/test_statistical_helpers.py` | Delete the private `_NODE` and `_run_filter_js_block` (812-856, including the four aliased imports) and write, verbatim, `from js_runner import run_filter_js_block as _run_filter_js_block, requires_node, NODE as _NODE`; `@requires_node` on `TestFilterJavaScript` in place of the `skipif`. The two aliases `_NODE` and `_run_filter_js_block` stay as module names (C5; consistency #8): S05's module documents them and any file written against the old spelling collects. Three tests unchanged. |

Each migrated file is run alone before and after its edit; the pass/fail/skip counts and the set of test ids must be identical.

### TR-03.3 `test/test_js_runner.py` — one test per function (rule 3)

Builds pages through `test_filter_exclude`'s helpers (`_write_inputs`, `_graph`, `_spec`, `_renderer_source`) and `conftest.make_data_json`, as `test_help_claims_3.py` does. Classes and tests under TDD test stubs. The E2 measurement uses `TestExcludeHoldsWhileItsOwnFilterMoves.SPEC` (`test_help_claims_3.py:436-445`: g1, g2, k1 counting mpg, a `foreign` dropdown and a `price` range excluding g1 and k1) and the sequence GAPS2 E2 measured served: price to `(4000.0, 5000.0)`, foreign to `"1"`, price back to its full `(w.start, w.end)`.

### TR-03.4 Documentation

No gap closes here: no BUGS.md entry, no `dash.sthlp` and no CHANGELOG line (section 19 records the tooling under WP-28). The module docstring is the documentation: why state must be carried (E2's "unmeasured" line), the `commit=False` case, the `__proto__` rule, the `DASH_NODE` override and the strict-mode consequence, the list of the consumers by section (04, 05, 12, 17) and the names each imports, and the CLAUDE.md rule 11 pytest invocation (`python3 -m pytest test/test_js_runner.py -q` while iterating; the whole suite once before a commit).

## Boundaries

- Do not edit `dash_render.py`: not `_DASH_FILTER_MASK_JS`, `_FILTER_JS`, `_dash_frame_filter_mask`, `_dash_dropdown_mask`, `_dash_option_value`, `_dash_json_value`, `_dash_dropdown_values` (section 17), nor `map_histogram` or the JS recount (section 05).
- Do not change any assertion, expected value or test id in the four migrated files; do not delete a test; do not delete the `_NODE`/`_run_filter_js_block` names from `test_statistical_helpers.py` (they become aliases).
- Do not migrate `test_help_claims_4.py`, `test_export.py` or the four bare `shutil.which("node")` sites; list them, leave them.
- Do not add a browser; DISCOVERY Q15: "no browser needed".
- Do not write the E2 or X1 fix, nor the multi-move sequences that replace `TestExcludeHoldsWhileItsOwnFilterMoves` (GAPS2 E2 plan 4 is section 17's), nor the Q26 grouping or its parity case (S17); this section measures and pins.
- Do not hard-code the nvm path: `DASH_NODE` and `PATH` only (GAPS2 K1 is about machine-local paths).
- No Stata run, no `make cert`, no BUGS.md/CHANGELOG/help edit (TR-03.4).

## Stata truth

None. This section runs dash's own JavaScript and Python; every value it pins is a measurement of dash, named as such. Section 17 adds the Stata counts E2's plan 5 asks for (`count if foreign==1`, `count if foreign==1 & inrange(price,4000,5000)`) as a block of `test/test_gaps2_truth.cscript` (D11).

## TDD test stubs

All in `test/test_js_runner.py`. The first group are the section's regression tests: every one fails at `91d97be` with `ModuleNotFoundError: No module named 'js_runner'` at collection (record that as the failure). Their non-vacuity rests on the mutation table.

- Test: `test_js_runner.py::TestNode::test_node_is_the_override_or_the_path_lookup` — with `monkeypatch.setenv("DASH_NODE", "/x/node")` and `importlib.reload`, `NODE == "/x/node"`; without it, `NODE == shutil.which("node")`.
- Test: `test_js_runner.py::TestNode::test_a_missing_node_skips_with_the_override_named` — `monkeypatch.setattr(js_runner, "NODE", None)`; `pytest.raises(pytest.skip.Exception)` around `node()`, message contains `DASH_NODE`.
- Test: `test_js_runner.py::TestEncoding::test_a_model_is_encoded_once_and_referenced_by_id` — one source in two args → one stand-in, two `{"__ref__": id}`.
- Test: `test_js_runner.py::TestEncoding::test_nan_inf_and_timestamps_are_json_safe` — `plain(np.nan) is None`, a `pd.Timestamp` → epoch ms float (equal to `dr._dash_json_value`).
- Test: `test_js_runner.py::TestEncoding::test_every_stand_in_kind_keeps_its_fields` — source `data`, filter `booleans`, Div `text`, Select `value`, RangeSlider `value`/`start`/`end`/`step`, a glyph model's `width`.
- Test: `test_js_runner.py::TestRunJs::test_it_returns_what_node_printed` — `run_js('process.stdout.write(JSON.stringify({a: 1}))') == {"a": 1}`.
- Test: `test_js_runner.py::TestRunJs::test_a_node_error_is_an_assertion_carrying_stderr` — `run_js("throw new Error('boom')")` raises `AssertionError` whose text contains `boom`.
- Test: `test_js_runner.py::TestASessionCarriesState::test_two_moves_chain_on_one_session` — a page with a `foreign` dropdown and a `price` range; `s = JsSession(r.filter_callbacks)`; `s.set(w_for, "1"); s.run(cb_for)`; `s.set(w_price, (4000.0, 5000.0)); s.run(cb_price)`; `s.rows(source)` equals the count of rows with `foreign == 1 & 4000 <= price <= 5000` (3 of `test_filter_exclude`'s ten), and the second run's node output for that source shows it **started** from 5 rows (assert the encoded `orig` of the second run, captured through `s.runs`, is the first run's result).
- Test: `test_js_runner.py::TestASessionCarriesState::test_a_dry_run_leaves_the_python_models_untouched` — `commit=False`; the source's `data` is identical before and after, while the returned output shows the filtered rows.
- Test: `test_js_runner.py::TestASessionCarriesState::test_state_reports_sources_booleans_divs_and_widths` — after a committed run, `.state()` has the four keys and the Div text of a KPI card holds the moved value.
- Test: `test_js_runner.py::TestASessionCarriesState::test_set_returns_the_old_value_and_sets_the_new`.
- Test: `test_js_runner.py::TestASessionCarriesState::test_a_proto_column_survives_a_run` — a frame with a column named `__proto__`; after `run`, the source still has it with its values (the `JSON.parse` rule, `test_saved_filter_layers.py:186-189`).
- Test: `test_js_runner.py::TestMaskParity::test_a_numeric_range_and_a_slider_agree_in_both_twins` — `price` range `(4000, 5000)` and `mpg` slider 20 on `test_mode_parity._DF`; `js == pandas`, and both equal the pandas expression.
- Test: `test_js_runner.py::TestMaskParity::test_a_string_dropdown_on_exact_text_agrees` — a string column with `'01'`, `'1'`, `'1.0'`, `'x'`; option `'1'`; `js == pandas` (report B §2.1: both select the three today).
- Test: `test_js_runner.py::TestMaskParity::test_a_missing_value_fails_every_range_in_both_twins` — a NaN in `price`; the range drops it in both.
- Test: `test_js_runner.py::TestMaskParity::test_a_widget_at_its_full_extent_restricts_nothing_in_both_twins`.
- Test: `test_js_runner.py::TestMaskParity::test_a_dropdown_on_a_small_number_disagrees_today_x1` (03-05) — a double column holding `5e-05`; option `dr._dash_option_value(5e-05)`; assert `js != pandas` and `sum(pandas) == 1`, `sum(js) == 0`, with a comment naming section 17 as the section that turns this into `js == pandas`. (S17 adds `test_two_values_sharing_a_label_select_both` beside it, Q26.)
- Test: `test_js_runner.py::TestRunFilterJsBlock::test_the_histogram_block_runs_the_shipped_code_on_literal_values` — as `TestFilterJavaScript::test_the_discrete_recount_folds_the_top_value_as_python_does` does, through the module's name.
- Test: `test_js_runner.py::TestTheMigratedShims::test_filter_exclude_run_callback_reports_rows_and_ids_without_writing_back` — call `tfe._run_callback` twice on one source; both outputs equal and the source unchanged (the `TestThePrimarySourceFallback` contract).
- Test: `test_js_runner.py::TestTheMigratedShims::test_help_claims_3_run_saved_reports_rows_and_div_text`.
- Test: `test_js_runner.py::TestTheMigratedShims::test_the_aliases_s05_imports_exist` — `import test_statistical_helpers as tsh`; `tsh._NODE is js_runner.NODE` and `tsh._run_filter_js_block is js_runner.run_filter_js_block` (C5: the names S05 and the old spelling rely on).
- Test: `test_js_runner.py::TestASessionMeasuresE2::test_three_moves_leave_the_saved_page_where_measured` (03-05) — the SPEC and sequence of TR-03.3; assert the final `{g1, g2, k1}` equals the value 03-05 measures, written into the test with the date, and assert separately what the widgets imply (`{"g1": 5, "g2": 5, "k1": "5"}`) in a comment; if the two are equal, the docstring says so and section 17 keeps the test.

**Mutation table** — apply, confirm the named test fails, revert:

| break this | test that must die |
|---|---|
| in `run_code`, skip the write-back when `commit` is true | `TestASessionCarriesState::test_two_moves_chain_on_one_session` |
| in `run_code`, write back when `commit` is false | `test_a_dry_run_leaves_the_python_models_untouched`, `TestTheMigratedShims::test_filter_exclude_run_callback_reports_rows_and_ids_without_writing_back` |
| write `const RAW = <literal>` instead of `JSON.parse` | `test_a_proto_column_survives_a_run` |
| in `mask_parity`, build the pandas widgets without `_dash_ftype` | `TestMaskParity::test_a_numeric_range_and_a_slider_agree_in_both_twins` (pandas mask becomes all-true) |
| in `mask_parity`, run the JS side with `raw=True` always | `test_a_dropdown_on_a_small_number_disagrees_today_x1` |
| in `node()`, `pytest.fail` instead of `pytest.skip` | `TestNode::test_a_missing_node_skips_with_the_override_named` |
| in `test_statistical_helpers.py`, drop `NODE as _NODE` from the import | `TestTheMigratedShims::test_the_aliases_s05_imports_exist` |

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Node lookup, override and skip | pytest `test_js_runner.py::TestNode` | none | n/a |
| Encoding: identity, JSON safety, stand-in fields, `__proto__` | pytest `TestEncoding`, `test_a_proto_column_survives_a_run` | `test_mode_parity._DF` | saved (node) |
| A session chains moves; a dry run does not | pytest `TestASessionCarriesState` (node) | `test_filter_exclude` spec | saved |
| Both twins' masks on the same columns | pytest `TestMaskParity` (node + pandas) | frames built in the test | both (the point) |
| The recount fragment runner | pytest `TestRunFilterJsBlock`, existing `TestFilterJavaScript` | `_AUTO_MPG` | saved |
| Migrated files assert what they asserted; the aliases exist | run each file alone before/after; pytest `TestTheMigratedShims` | as before | as before |
| E2's saved-page state after three moves | pytest `TestASessionMeasuresE2` (node) | `TestExcludeHoldsWhileItsOwnFilterMoves.SPEC` | saved (served is `test_help_claims_3.py::test_served`) |
| X1's small-number dropdown | pytest `TestMaskParity` | frame in the test | both |

Acceptance criteria:

- **AC-03.1** `python3 -m pytest test/test_js_runner.py -q` passes with 0 skipped under both interpreters (the file alone under `/opt/anaconda3/bin/python3` as well) when node is on `PATH` or `DASH_NODE` is set; with neither, every node test skips with a reason naming `DASH_NODE`, and `DASH_STRICT=1` turns the run red.
- **AC-03.2** `test_saved_filter_layers.py`, `test_filter_exclude.py`, `test_help_claims_3.py` and `test_statistical_helpers.py` each report the same test ids and the same pass/fail/skip counts before and after migration, and none of them defines `_RUNNER`, `_encode` or `_stand_in` any more.
- **AC-03.3** `grep -c "shutil.which(\"node\")" test/test_saved_filter_layers.py test/test_filter_exclude.py test/test_statistical_helpers.py` prints 0 for each; `grep -c "NODE as _NODE" test/test_statistical_helpers.py` prints 1.
- **AC-03.4** `test_js_runner.py` holds a pinned measurement of the saved page after E2's sequence and of the 5e-05 dropdown, each naming section 17.
- **AC-03.5** The full suite (`python3 -m pytest test/ -q`) is green once in the worktree before the section's one commit on `wp28-s03`, whose subject ends `(WP-28 S03)`.

## Tasks

Commit boundary: **one commit (S03)** holding 03-01 to 03-05, made by 03-05 on the worktree branch `wp28-s03`, subject ending `(WP-28 S03)`, body per S01 TR-01.9 opening with the saved failure text; the full pytest suite runs green once in the worktree before it (CLAUDE.md rules 4 and 11); the merger lands the commit onto `s3-bugs` with that message (index.md step 1). No task before 03-05 commits. No Stata run in this section. No AI references anywhere.

<task type="auto" id="03-01">
  <name>Write the failing tests for the runner</name>
  <files>test/test_js_runner.py</files>
  <action><![CDATA[
    Create `test/test_js_runner.py` with the header of `test/test_help_claims_3.py` (paths, `import dash_render as dr`, `import test_filter_exclude as tfe`, `from conftest import make_data_json`) and every class and test named under "TDD test stubs" except the two 03-05 tests (`test_a_dropdown_on_a_small_number_disagrees_today_x1`, `TestASessionMeasuresE2`). Module docstring: the E2 "unmeasured because the node harness cannot chain moves" sentence from GAPS2, DISCOVERY Q10/Q15, the rule that a skip for a missing node is red under `DASH_STRICT=1`, and the consumers of the module by section (04, 05, 12, 17) with the names each imports (C5). Write the page-building helper `_page(tmp_path, spec)` on `tfe._write_inputs` and `dr.DashRenderer`, and a `_widgets(r)` that returns the `Select` and `RangeSlider` with their callbacks by type. Write only tests; do not create `js_runner.py`. Run the file against the unmodified tree. Do not commit: save the collection error to the scratch directory as `03-01-failure.txt`; it becomes the opening paragraph of the S03 commit (S01 TR-01.9).
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_js_runner.py -q 2>&1 | tail -5` shows one collection error naming `js_runner`. `git status --short` lists exactly `test/test_js_runner.py`; `<scratch>/03-01-failure.txt` exists.]]></verify>
  <done>The section's tests existed and failed because the module they import did not exist, and nothing was committed.</done>
</task>

<task type="auto" id="03-02">
  <name>Write the shared node runner module</name>
  <files>test/js_runner.py</files>
  <action><![CDATA[
    Create `test/js_runner.py` to TR-03.1. Lift `plain`, `encode`, `stand_in` and `RUNNER` from `test/test_saved_filter_layers.py:94-179` unchanged in behaviour; implement `run_js`, `JsSession` (`__init__`, `set`, `run`, `run_code` with `commit`, `state`, `rows`, `ids`, `runs`), `mask_parity` (JS side through `dr._dash_json_value` unless `raw`, pandas side through real `Select`/`Slider`/`RangeSlider` widgets carrying `_dash_var`, `_dash_ftype`, `_dash_sentinel`; the spec dicts pass through untouched), and copy `run_filter_js_block` from `test/test_statistical_helpers.py:820-856` with `node()` in place of `_NODE`. `NODE` reads `DASH_NODE` first; `node()` skips, never fails; `requires_node` is the `skipif` marker over `NODE is None`. The payload is written as `JSON.parse(<json of json>)`. Docstring per TR-03.4.
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_js_runner.py -q 2>&1 | tail -3` passes every test except the three `TestTheMigratedShims` tests (their shims and aliases do not exist yet), 0 skipped. `DASH_NODE=/nonexistent python3 -m pytest test/test_js_runner.py -q -k proto 2>&1 | tail -2` reports 1 failed (the bad override is used as given, and node fails to start) -- evidence the override is honoured.]]></verify>
  <done>`test/js_runner.py` exposed `NODE`, `node`, `requires_node`, `run_js`, `plain`, `encode`, `stand_in`, `RUNNER`, `JsSession`, `mask_parity` and `run_filter_js_block`, each pinned by a test, and nothing else imported it yet.</done>
</task>

<task type="auto" id="03-03">
  <name>Migrate the saved-layers and histogram runners</name>
  <files>test/test_saved_filter_layers.py, test/test_statistical_helpers.py</files>
  <action><![CDATA[
    Run each file alone first and save `python3 -m pytest <file> -q -rA 2>&1 | grep -E "^(PASSED|FAILED|SKIPPED)"` to the scratch directory. Apply the TR-03.2 edits: in `test_saved_filter_layers.py` delete 85-214 and add the four-line `_run` shim over `JsSession([]).run_code(code, args, cb_obj)`; in `test_statistical_helpers.py` delete 812-856 and write the verbatim line `from js_runner import run_filter_js_block as _run_filter_js_block, requires_node, NODE as _NODE`, replacing the `skipif` at 859 with `@requires_node` (the aliases `_NODE` and `_run_filter_js_block` stay as module names: C5, consistency #8). Re-run both files alone and diff the saved id lists: identical sets, identical counts. Note that a machine without node now sees `test_saved_filter_layers.py` skip where it failed before; under `DASH_STRICT=1` both are red, and the commit-message draft says so.
  ]]></action>
  <verify><![CDATA[The before/after id-and-outcome diffs are empty for both files. `grep -n "_RUNNER\|def _encode\|def _stand_in\|shutil.which" test/test_saved_filter_layers.py test/test_statistical_helpers.py` prints nothing; `grep -c "NODE as _NODE" test/test_statistical_helpers.py` prints 1; `python3 -m pytest test/test_js_runner.py -q -k aliases_s05 2>&1 | tail -2` passes.]]></verify>
  <done>Two of the three runners were the shared module, their tests reported the same outcomes they reported before, and the two names S05 imports from `test_statistical_helpers.py` resolved to the module's.</done>
</task>

<task type="auto" id="03-04">
  <name>Migrate the exclude and help-claims-3 runners</name>
  <files>test/test_filter_exclude.py, test/test_help_claims_3.py</files>
  <action><![CDATA[
    Same before/after procedure. In `test_filter_exclude.py` delete 103-192 and rewrite `_run_callback` as the `commit=False` shim returning `{id: {"rows", "ids"}}` for every `ColumnDataSource` in the run's output (rows from the first column's length, ids from `dr._ROW_ID_COLUMN`, `None` when absent). In `test_help_claims_3.py` delete `_RUNNER_DIVS` and rewrite `_run_saved` as the `commit=False` shim returning `(sources, divs)`; drop its `tfe._RUNNER`, `tfe._encode`, `tfe._node` uses and the local `json`/`subprocess`/`tempfile` imports inside it. Then remove the temporary `_node`/`_encode` aliases from `test_filter_exclude.py`. Run `test_js_runner.py -k TestTheMigratedShims` as well.
  ]]></action>
  <verify><![CDATA[Before/after diffs empty for both files; `python3 -m pytest test/test_js_runner.py -q 2>&1 | tail -2` passes in full, 0 skipped. `python3 -m pytest test/test_filter_exclude.py -q -k PrimarySourceFallback 2>&1 | tail -2` prints `3 passed` (the dry-run contract holds).]]></verify>
  <done>All three runners and their one dependant were the shared module, and every migrated test asserted what it asserted before.</done>
</task>

<task type="auto" id="03-05">
  <name>Pin the E2 and X1 measurements</name>
  <files>test/test_js_runner.py</files>
  <action><![CDATA[
    Add `TestMaskParity::test_a_dropdown_on_a_small_number_disagrees_today_x1` and `TestASessionMeasuresE2::test_three_moves_leave_the_saved_page_where_measured`. For the second, build `TestExcludeHoldsWhileItsOwnFilterMoves.SPEC`'s page, open `JsSession(r.filter_callbacks)`, run the sequence price → `(4000.0, 5000.0)`, foreign → `"1"`, price → `(w_price.start, w_price.end)`, each move through its own callback, and read `{g1, g2, k1}` as `_saved` at `test_help_claims_3.py:441-467` reads them (`_renderer_source`, `_card_value` on the k1 Div's text from `.state()["divs"]`). Print the value once, write it into the assertion with the date, and in the docstring state the widget-implied value `{"g1": 5, "g2": 5, "k1": "5"}` and which section flips or keeps the test; in the X1 test's comment name section 17 and its Q26 case `test_two_values_sharing_a_label_select_both`, which S17 adds beside it. Run `test/test_js_runner.py` alone under both interpreters (the file only), then the full pytest suite once in the worktree, `python3 -m pytest test/ -q` (CLAUDE.md rules 4 and 11; `make test` is S19's gate run); fix any regression in this section's code, never by weakening a test. Grep every changed file and the message draft for `claude|anthropic` (nothing may match). Commit the whole section as ONE commit on the worktree branch `wp28-s03`; the merger lands it onto `s3-bugs` with this message (index.md step 1): subject ending `(WP-28 S03)`, body opening with `<scratch>/03-01-failure.txt` and carrying `Regression: test/test_js_runner.py -- collection failed at 91d97be with ModuleNotFoundError: No module named 'js_runner'` (S01 TR-01.9; no `Flipped:`, `Fixture:` or `BUGS.md:` line: nothing flips, no fixture, no gap). The merge command into `main` is S19's to report; do not run any merge.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_js_runner.py -q 2>&1 | tail -2` passes, 0 skipped. `python3 -m pytest test/ -q 2>&1 | tail -3` reports no failures and no skips beyond those the tree had at `91d97be` under this interpreter. `grep -n "section 17" test/test_js_runner.py` finds both pinned tests. `git log -1 --format=%s | grep -c '(WP-28 S03)'` prints 1; `git log -1 --format=%B | grep -ci 'claude\|anthropic'` prints 0; `git rev-parse --abbrev-ref HEAD` prints `wp28-s03`; `git status --short` prints nothing.]]></verify>
  <done>The saved page's state after E2's sequence and the two twins' answers on X1's small-number case were measured facts held by tests naming the section that changes them, one green commit on `wp28-s03` carried the whole section for the merger, and sections 04, 05, 12 and 17 had `run_js`, `requires_node`, `run_filter_js_block`, `NODE`, `JsSession` and `mask_parity` to build on.</done>
</task>

## Section completion criteria

1. `test/js_runner.py` exposes the public names of TR-03.1 (C5) with the documented behaviour, and `test/test_js_runner.py` has a passing test per function.
2. `test_saved_filter_layers.py`, `test_filter_exclude.py`, `test_help_claims_3.py` and `test_statistical_helpers.py` import the module, define no runner of their own, and report the same test ids and outcomes as before; `test_statistical_helpers.py` keeps `_NODE` and `_run_filter_js_block` as aliases of the module's names.
3. A two-move chain on one `JsSession` starts its second move from the first move's result; a `commit=False` run leaves the Python models untouched; a `__proto__` column survives.
4. `mask_parity` returns both twins' masks for dropdown, slider and range filters on one frame, passing the spec dicts through unchanged, and the X1 and E2 measurements are pinned with section 17 named.
5. A missing node skips with `DASH_NODE` in the reason and is red under `DASH_STRICT=1`; no `pytest.fail` on a missing node remains in the migrated files.
6. One commit on `wp28-s03`, subject ending `(WP-28 S03)`, holding every task's work; no test-only commit exists (D1); the full suite was green once in the worktree before it; no file outside the task lists was modified; no BUGS.md, CHANGELOG or help edit was made.

## Notes

- **The dry run is not optional.** `TestThePrimarySourceFallback` (`test_filter_exclude.py:469-496`) reuses one `primary` source across three runs and expects the build-time rows each time; `_run_callback` must pass `commit=False`. A "stateful by default" shim there is a regression that looks like an exclude() bug.
- **`JSON.parse`, not a literal.** A `__proto__` column in an object literal sets the prototype and loses the column (`test_saved_filter_layers.py:186-189`; the page's own guard is `dash_own_col`, `dash_render.py:14211-14217`). Keep the double-`json.dumps` form.
- **Identity.** `_srcs.includes(source)` in `_FILTER_JS` is an identity test; one stand-in per model id, referenced by `__ref__`, is what makes the fallback tests meaningful. Do not encode a model twice.
- **What write-back covers.** `data`, `booleans`, `text`, `width` — the four things the callbacks write. A test that needs `selected.indices` after a brush reads node's output, as the brush tests at 758 and 798 do; the page's own selection is not replayed into Python.
- **`_dash_json_value` on the JS side of `mask_parity`** is deliberate: it is the saved snapshot's encoding (`_to_serialisable`, 22983), so the parity reported is the page's. Section 17 changes that function to keep string columns as text; the parity test follows without an edit. `raw=True` exists for a test that wants to see the twins without the snapshot's coercion.
- **Skip is red under strict.** `make test` and `make test-dev` set `DASH_STRICT=1`; a node skip there fails the run, which is what CLAUDE.md rule 3 wants. On a machine without node on `PATH`, set `DASH_NODE=/Users/billy/.nvm/versions/node/v24.13.1/bin/node`; never write that path into the code.
- **One process per run.** Each `run_code` starts node once; state lives in the Python models between runs, not in node. A sequence of ten moves is ten processes, about a second each on this machine; keep sequences short.
- **`loadgroup`.** pytest runs `-n auto --dist loadgroup` by default (`pyproject.toml`); node tests need no group marker, but a class that renders one page and chains many moves on it should hold the page in a class-scoped fixture, not re-render per test.
- **Shared files (rules R1-R6).** This section registers no cscript, touches no copy list, map, help, CHANGELOG, BUGS.md, graph-key list or parity corpus, and regenerates no fixture. Its four edited test files are edited again later by S07 and S10 (batch 1, merged after S03 per C3) and by S12 and S17 (batch 2/3); a rejected hunk in them is applied by hand keeping every test.
- **Commit body** uses S01 TR-01.9's line forms verbatim: `Regression: <test> -- failed at <pre-fix tree> with <text>`; no `Flipped:`, `Fixture:` or `BUGS.md:` line here (nothing flips, no fixture, no gap). The commit is made on `wp28-s03` and landed on `s3-bugs` by the merger (AMEND-1 item J).
- **Hand-off for sections 04 and 05.** S04's `test_display_format_writer.py` imports `run_js` and `requires_node`; S05's `test_histogram_edge_rule.py` imports `run_filter_js_block` and `NODE` from `js_runner` and `_hist` from `test_statistical_helpers` (C5). Do not rename anything in TR-03.1 without a decision.
- **Hand-off for section 17.** The pinned E2 value and the X1 inequality are the regression tests E2 and X1 need (rule 7); section 17 flips them in the same commit as each fix and records the flip in its commit message; S17 also adds `mask_parity`'s two-values-one-label case (Q26, AMEND-1 item G) and ships the `groups` key the masks read; `mask_parity` passes it through as it passes every spec key.
