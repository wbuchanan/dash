- [x] Title: Generated server rate limiter is never enforced
  - File Names and Line Numbers: dash_render.py (7397-7414, 9458-9464)
  - Description: The generated server source defines `_RateLimiter` and `_LIMITER`, but no request path calls `_LIMITER.is_allowed(...)`. Because there is no enforcement point, requests are never throttled even though the code advertises rate limiting. This is a security bug (abuse/cost risk), not a feature, because the limiter is implemented but effectively dead code.
  - Suggested fix: Add a real enforcement hook in generated server code (for example, a shared Tornado `prepare()` check for HTTP handlers and a corresponding gate for session/websocket creation) that returns HTTP 429 when `_LIMITER.is_allowed(clientIp)` is false.
  - Resolution: Fixed. Added `prepare()` method to the `_HealthHandler` class in the generated server source that extracts the remote IP and calls `_LIMITER.is_allowed(ip)`, returning 429 JSON on rate-limit. Also added a rate-limit gate at the top of `make_document(doc)` that extracts client IP from `doc.session_context.request` (with X-Forwarded-For fallback) and returns a 429 Div immediately when the IP is rate-limited. Nine regression tests added in `test/test_server.py` class `TestRateLimiterEnforcement` (BUG-RL-1a through BUG-RL-4). All 1208 tests pass.

- [x] Title: Server-mode function expressions reject normal arithmetic operators
  - File Names and Line Numbers: dash_render.py (8856-8867)
  - Description: In generated server code, `_val_node` recursively validates `BinOp`/`UnaryOp` children without excluding operator nodes (`Add`, `Sub`, etc.). Operator nodes then fall into the `else` branch and raise `ValueError("Disallowed node ...")`. This causes valid expressions like `x + 1` to fail in server mode, which is core functionality breakage for function plots.
  - Suggested fix: Mirror the standalone validator logic by explicitly allowing/skipping operator AST node classes before recursing into child expressions.
  - Resolution: Fixed. Added  before the else-raise clause in the generated  function (dash_render.py ~8888). This mirrors the standalone validator which already used  to skip operator nodes. 11 regression tests added in  class  (BUG-FE-1a through BUG-FE-1 safety). All 1219 tests pass.

- [x] Title: Server-mode function `n` option allows unbounded point counts
  - File Names and Line Numbers: dash_render.py (8851-8853, 8872)
  - Description: Generated server code parses `opts['n']` directly into `n_pts` and uses it in `np.linspace(x_lo, x_hi, n_pts)` with no upper bound. A large `n` can allocate very large arrays and drive CPU/memory exhaustion, creating a straightforward resource-exhaustion vector.
  - Suggested fix: Clamp `n_pts` to a safe range (for example `2..10000`) exactly like the standalone path does (`min/max` guard) before calling `np.linspace`.
  - Resolution: Fixed. Changed the `n_pts` parse in the generated server function handler from `n_pts = int(opts['n'])` to `n_pts = max(2, min(int(opts['n']), 10000))` (dash_render.py ~8879), mirroring the standalone path which already had this clamp. 3 regression tests added in `test/test_server.py` class `TestServerFunctionNClamp` (BUG-FE-2a through BUG-FE-2c). All 1222 tests pass.

- [x] Title: `dash serve` invokes unsupported renderer CLI mode/flags and cannot start
  - File Names and Line Numbers: dash.ado (1574-1577), dash_render.py (9525-9530)
  - Description: `_dash_serve` sets `sys.argv` with `--mode "serve"` plus `--port`/`--timeout` flags, but `dash_render.py` only accepts `--mode {standalone,server}` and does not define `--port`, `--timeout`, or `--no-browser`. This is a core functionality bug, not a feature: the serve command path is wired to arguments the renderer rejects. Direct reproduction from this repo: `python3 dash_render.py --spec /tmp/a.json --data /tmp/b.json --output serve --mode serve` returns `invalid choice: 'serve'`.
  - Suggested fix: Align the interface on one side with minimal change. Either (a) update `_dash_serve` to call `--mode server` and launch the generated app separately, or (b) restore `serve` mode and add matching `--port/--timeout/--no-browser` arguments in `dash_render.py`.
  - Resolution: Fixed. (1) Added `--port` (int, default 5006), `--timeout` (int, default 0), and `--no-browser` (store_true) arguments to `dash_render.py`'s argparse block (dash_render.py ~9554). (2) In `__main__`, after `main()` generates the server app, Bokeh Server is launched via `subprocess.Popen([sys.executable, '-m', 'bokeh', 'serve', ...])` with optional timeout auto-shutdown and browser open. (3) Fixed `_dash_serve` in `dash.ado` (line ~1574): changed `--mode serve` → `--mode server` and `--output serve` → a real `.py` temp-file path (`c(tmpdir)dash_serve_app.py`). (4) Also fixed `--no-browser` append to pass the literal `--no-browser` string instead of the macro value. 7 regression tests added in `test/test_server.py` class `TestCLIServeFlagsAccepted` (BUG-CLI-1a through BUG-CLI-1g). All 1229 tests pass.

- [x] Title: Python command injection risk from unescaped file paths in embedded `python:` lines
  - File Names and Line Numbers: dash.ado (131-132, 1574-1578)
  - Description: Stata macros are interpolated directly into single-quoted Python raw string literals (for `spec`, `data`, `output`, `render_py`) without escaping `'` or other Python-literal-breaking characters. A path containing a quote can terminate the literal and inject arbitrary Python statements before `runpy.run_path(...)`. This is a security bug because path values cross a trust boundary into executable Python source.
  - Suggested fix: Stop interpolating raw macro text into Python code strings. Serialize arguments safely (for example via `json.dumps`-style escaping before interpolation, or by passing values through a temporary JSON/args file and loading inside Python) so quotes/backslashes cannot break literal boundaries.
  - Resolution: Fixed. In both `_dash_do_render` and `_dash_serve` in `dash.ado`, each file-path local macro is now processed through `_dash_json_str` (which escapes `\` to `\\` and `"` to `\"`) before interpolation into Python string literals. The Python code was changed from `r"\`macro'"` (raw strings, vulnerable to `"` in path) to `"\`_py_escaped'"` (regular strings with JSON-escaped values). 4 regression tests added in `test/test_server.py` class `TestPathInjectionHardening` (BUG-SEC-1a through BUG-SEC-1d). All 1233 tests pass.

- [x] Title: Immediate render parser truncates valid `if` string expressions containing quotes
  - File Names and Line Numbers: dash.ado (911-915)
  - Description: `_dash_render_immediate` extracts `if_expr` from JSON using `substr(..., 1, strpos(..., '"') - 1)`. This stops at the first quote character even when it is an escaped quote inside the JSON string value. Valid Stata expressions like `if make == "AMC Concord"` are therefore truncated (for example to `make==\`) before `jsonio` runs, breaking legitimate filtered renders. This is a functional bug because quoted string comparisons are valid user input and the extraction logic is not JSON-safe.
  - Suggested fix: Replace substring scanning with JSON-aware extraction (parse the spec JSON and read `if_expr` directly), or reuse existing parser outputs instead of reparsing the JSON text.
  - Resolution: Fixed. Added `_dash_json_get_str(json_str, key, out_macro)` to `dash_parse.mata` — a JSON-aware string value extractor that walks the value char-by-char and handles `\"` → `"` and `\\` → `\` escape sequences instead of stopping at the first `"`. Updated `_dash_render_immediate` in `dash.ado` (lines ~919-931) to call `mata: _dash_json_get_str(...)` for both `if_expr` and `in_expr` instead of the naive `strpos`/`substr` approach. 5 regression tests added in `test/test_server.py` class `TestIfExprQuoteHandling` (BUG-PARSE-1a through BUG-PARSE-1e). All 1238 tests pass.

- [x] Title: Graph-level `if`/`in` qualifiers are dropped for named graphs and never applied in build/server flows
  - File Names and Line Numbers: dash.ado (703-707, 788-797), dash_render.py (4844-4906, 7861-7875)
  - Description: Segment parsing captures `if_expr`/`in_expr` into each plot JSON object, but `_dash_plot` hard-codes graph-level qualifiers to empty strings when creating `graph_json`. The renderer’s filter logic expects graph-level qualifiers (`graph_spec["if_expr"]` or `graph_options["if_expr"]`) and does not read per-plot qualifiers, so named-graph dashboards in `dash build` / generated server mode silently ignore `if`/`in` conditions.
  - Suggested fix: Propagate qualifiers from the first segment into top-level graph JSON (or consistently read per-plot qualifiers in the renderer). The smallest change is to set top-level `if_expr`/`in_expr` during `_dash_plot` assembly and keep renderer behavior unchanged.
  - Resolution: Fixed. (1) In `_dash_plot` in `dash.ado` (lines ~801-808), replaced the hard-coded empty `if_expr`/`in_expr` strings with calls to `mata: _dash_json_get_str(...)` that extract the first segment's qualifiers from `plots_json` and promote them to the top-level graph JSON key. (2) In `dash_render.py` server-mode generated code (line ~7897), added fallback `or g.get('if_expr')` so server graphs check the top-level key when `graph_options.if_expr` is empty. The standalone `_apply_graph_filter` already reads from the top-level key, so no change was needed there. 5 regression tests added in `test/test_server.py` class `TestGraphQualifierPropagation` (BUG-QUAL-1a through BUG-QUAL-1e). All 1243 tests pass.

- [ ] Title: Faceted aggregate layers recompute from global filtered data instead of per-facet data
  - File Names and Line Numbers: dash_render.py (9034-9063, 9094, 9280-9315)
  - Description: Facet-specific aggregate sources are registered with facet keys (for example `(_fac_name, pi)`), and raw source updates correctly compute per-facet `_gdf`. However, aggregate recomputation in `_make_filter_cb` always uses global `fdf` for every aggregate type. This causes faceted histograms/fits/smoothers to drift from the facet’s subgroup after filter changes, which is a core correctness bug.
  - Suggested fix: In the aggregate recompute loop, derive a facet-aware frame (analogous to `_gdf` logic used for raw sources via `_fgvals`) and pass that frame to `_compute_*` calls instead of always using `fdf`.

- [x] Title: Server-mode histogram `bin()` accepts unbounded values and can exhaust memory/CPU
  - File Names and Line Numbers: dash_render.py (7480-7486, 8193-8202, 9288-9290)
  - Description: Generated server code parses `nbins = int(opts.get('bin', 20))` with no bounds and feeds it to `np.histogram(..., bins=nbins)` both initially and during callbacks. Large `bin()` values can force very large array allocations and expensive recomputation, creating a resource-exhaustion vector. This path is also inconsistent with standalone rendering, which clamps histogram bins to a safe maximum.
  - Suggested fix: Clamp server-mode `nbins` to a safe range (for example `1..1000`) and guard the parse with `try/except` to fall back to a default on invalid values before calling `_compute_histogram`.
  - Resolution: Fixed. (1) At the call site in the server histogram handler (dash_render.py ~8224), changed `int(opts.get('bin', 20))` to `max(1, min(int(opts.get('bin', 20)), 1000))` with `try/except` fallback to 20. (2) Added defensive clamp inside `_compute_histogram`: `bins = max(1, min(int(bins), 1000))` as the first statement. Both match the standalone path which clamps to `_MAX_BINS = 1000`. 4 regression tests added in `test/test_server.py` class `TestServerHistogramBinClamp` (BUG-HIST-1a through BUG-HIST-1d). All 1247 tests pass.

- [x] Title: Dual log-scale graphs drop x-axis log mode due figure re-creation
  - File Names and Line Numbers: dash_render.py (5288-5297)
  - Description: `_make_figure` re-creates the Bokeh figure once for `xscale(log)` and then re-creates it again for `yscale(log)` from the original `fig_kwargs`. When both options are set, the second re-creation overwrites the first, so the final figure keeps only y-log scaling. Reproduced from this repo with a minimal `DashRenderer` spec: resulting scales are `LinearScale` (x) and `LogScale` (y), not dual-log. This is a core functionality bug because valid `xscale(log) yscale(log)` input does not render as requested.
  - Suggested fix: Build axis-type kwargs once and create the figure a single time (for example, set both `x_axis_type` and `y_axis_type` in one `fig_kwargs` dict before calling `bokeh_figure`).
  - Resolution: Fixed. In `_make_figure` (dash_render.py ~5290-5297), replaced the two separate conditional figure re-creations (`if _xs_log: fig = bokeh_figure(x_axis_type=log)` then `if _ys_log: fig = bokeh_figure(y_axis_type=log)`) with a single combined block that sets both `x_axis_type` and `y_axis_type` in one `kw` dict and calls `bokeh_figure(**kw)` exactly once when either axis is log-scale. 4 regression tests added in `test/test_server.py` class `TestDualLogScale` (BUG-SCALE-1a through BUG-SCALE-1d). All 1251 tests pass.

- [ ] Title: Server build drops additional filter() clauses joined with `||`
  - File Names and Line Numbers: dash_parse.mata (700-705, 748), dash.ado (1140-1149), dash_render.py (7323-7324)
  - Description: `_dash_extract_filters` intentionally joins multiple `filter()` options with `" || "`, and `_dash_build` stores that raw string in `build_options.filter`. But `ServerAppBuilder._generate_app_source` only splits `filter_raw` on semicolons, so a `||`-joined spec is parsed as one filter and later filters are ignored. Reproduced by building server source with `filter` set to `foreign, type(dropdown) || weight, type(range)`: generated `_filter_specs` contains only the first filter. This is a core functionality bug because multi-filter server dashboards silently lose filters.
  - Suggested fix: Reuse `DashRenderer._parse_filter_raw(...)` (already supports `||` and `;`) or, at minimum, split on both delimiters in `ServerAppBuilder`.

- [ ] Title: saving() path is shell-invoked without shell-metacharacter hardening
  - File Names and Line Numbers: dash.ado (137-150, 1426-1428)
  - Description: `_dash_validate_path` only checks for `..` and `.html`, then `_dash_build` executes `shell open|start|xdg-open "`saving'"` with the raw path. Because this is direct shell invocation with interpolated user-controlled text, shell metacharacters are not explicitly blocked. This is a security bug surface, not a feature: path validation claims safety but does not harden against shell-special input before command execution.
  - Suggested fix: Avoid shell command construction from raw `saving()` text (prefer a non-shell launch path where available), or reject shell metacharacters (`$`, backticks, `;`, `&`, `|`, `<`, `>`, parentheses/newlines`) before invoking `shell`.

- [ ] Title: Generated server unsafe-token regex is corrupted by backspace escapes
  - File Names and Line Numbers: dash_render.py (7873, 8924-8926)
  - Description: In server-app code generation, regex templates embed `\b` inside normal Python string literals (not double-escaped), so the generated source contains literal backspace characters (`\x08`) around tokens like `eval`/`exec`/`open` instead of word-boundary markers. I verified this locally by generating server source and inspecting `repr(...)`, which shows `\x08eval\x08` in `_UNSAFE_G` and `_UNSAFE_BY` patterns. This weakens intended hardening and can allow unsafe token checks to be bypassed in generated server filtering paths.
  - Suggested fix: Escape boundary markers for generated-code strings (use `\\b` in the template literals, or construct the regex from a helper constant and `repr(...)`) so generated source contains literal `\b` sequences, not control characters.

- [ ] Title: Immediate render applies only the first plot qualifier to jsonio extraction
  - File Names and Line Numbers: dash.ado (788-797, 907-925)
  - Description: `_dash_plot` writes top-level `if_expr`/`in_expr` as empty strings, then `_dash_render_immediate` scans the JSON text for the first `"if_expr"`/`"in_expr"` occurrence and applies that single qualifier to `jsonio out`. For multi-plot immediate specs with different qualifiers, one plot’s qualifier is effectively applied to the whole extracted dataset. This is a core correctness bug because valid per-plot qualifier combinations produce incorrect data slices.
  - Suggested fix: Stop deriving `jsonio` qualifiers by first-match text scanning. Either extract and merge qualifiers explicitly before building JSON, or avoid pre-filtering `jsonio` data and let renderer-level filtering handle each plot qualifier consistently.

- [ ] Title: `dash build` validates only the first `filter(..., exclude(...))` group
  - File Names and Line Numbers: dash.ado (1228-1246)
  - Description: Build-time validation finds `exclude(` once via `strpos` and checks only that first parenthesized list. With multiple filter specs, later `exclude()` entries are never validated against the graph registry. This is a bug (not desired behavior) because the code claims to validate filter exclusions but silently skips additional groups.
  - Suggested fix: Iterate over all `exclude(...)` occurrences in the combined filter string (or parse each filter segment first, then validate each segment’s exclude list).

- [ ] Title: Filter callback exclusion metadata can bind to the wrong widget spec
  - File Names and Line Numbers: dash_render.py (6737-6748, 6799-6805)
  - Description: Filter widgets are conditionally skipped when a filter var is missing/invalid, but callback configuration later zips `filters_cfg` with `self.filter_callbacks`. If earlier specs were skipped, callbacks pair with the wrong filter spec, so `exclude()` lists can be applied to the wrong callback. This causes incorrect KPI/graph exclusion behavior after filter changes.
  - Suggested fix: Track and zip only the subset of filter specs that actually produced callbacks (for example, build a `built_filter_specs` list alongside `self.filter_callbacks`).

- [ ] Title: KPI filter callback reintroduces DOM XSS via unescaped title/subtitle
  - File Names and Line Numbers: dash_render.py (4182-4184, 6819-6823)
  - Description: KPI title/subtitle values are pulled from spec JSON into `kpi_config_json` without escaping, then concatenated directly into `kpi_div.text` HTML inside `_FILTER_JS`. Initial KPI rendering escapes these fields, but after any filter change the callback rebuilds the card with raw values, so payloads like `<img src=x onerror=...>` become executable markup in the dashboard DOM. This is a security bug (stored DOM XSS on interaction), not intended behavior.
  - Suggested fix: Escape KPI text before it reaches callback HTML (smallest change: HTML-escape `title`/`subtitle` when building `_kpi_config_for_cb`), and preferably stop string-concatenating HTML in JS by assigning text content to dedicated nodes.

- [ ] Title: Enabling xscale(log)/yscale(log) drops previously applied figure styling
  - File Names and Line Numbers: dash_render.py (5229-5233, 5237-5286, 5290-5297)
  - Description: `_make_figure` creates a figure, applies scheme and region/background styling, then recreates the figure when log scale is requested. The second `bokeh_figure(...)` call discards prior `apply_to_figure` and explicit `bgcolor`/`plotbgcolor`/`plotregion`/`graphregion` assignments. Reproduction from this repo: with `bgcolor(#aabbcc) plotbgcolor(#112233) xscale(log)`, resulting colors revert to defaults (`#ffffff`). This is a core functionality bug because valid style options are silently ignored when log scale is enabled.
  - Suggested fix: Decide axis types before creating the figure and instantiate `bokeh_figure` once (set `x_axis_type`/`y_axis_type` in `fig_kwargs`), then apply scheme and region styling once.

- [ ] Title: Multiple `filter()` extraction fails when first option is written as `,filter(...)`
  - File Names and Line Numbers: dash_parse.mata (729-742, 748-753)
  - Description: `_dash_extract_filters` only accepts a filter keyword when the preceding character is start-of-string or a literal space. In valid Stata usage `dash build,filter(...)` (no space after comma), the first `filter` token is preceded by `,`, so it is not recognized/extracted. Because `_dash_build` depends on this pre-extraction before `syntax`, unextracted `filter()` remains in `0` and can trigger option parsing failures or dropped filter specs. This is a core parsing bug, not a feature.
  - Suggested fix: Treat commas and other whitespace as valid boundaries (for example allow preceding `,`, space, or tab), or replace manual boundary logic with a delimiter-aware tokenizer that accepts standard Stata option formatting.

- [ ] Title: Standalone `filter()` callbacks only update a single graph source in unlinked dashboards
  - File Names and Line Numbers: dash_render.py (7100-7108, 6742-6745, 4115-4118, 4362, 4421, 4473)
  - Description: In standalone mode without `link()`, `render()` creates independent `ColumnDataSource` objects per graph (one per name), but `_build_filter_widgets()` picks only one `fsource` and every filter callback is wired to that single `source`. `_FILTER_JS` then mutates only `source.data`, so the other unlinked graph sources never receive filtered rows. This contradicts the documented behavior that `filter()` applies across all graphs unless excluded, so this is a core functionality bug, not intended behavior.
  - Suggested fix: Pass all graph sources into callback args (not just one `source`) and update each non-excluded source inside `_FILTER_JS`, mirroring the server-mode per-source update loop.

- [ ] Title: Server-mode `exclude()` handling incorrectly unions exclusions across all filter widgets
  - File Names and Line Numbers: dash_render.py (9226-9231, 9250-9254, 9282-9286, 9324-9328)
  - Description: In generated server callbacks, each target graph/aggregate/KPI builds `excl` by concatenating `_dash_exclude` from every widget, then skips the target entirely when its name is in that union. This makes exclusions global: if one widget excludes graph `g1`, `g1` is skipped for all filters, including widgets that were supposed to still affect it. That is a correctness bug in exclusion semantics, not a feature.
  - Suggested fix: Compute exclusions per widget and per target: for each target, build its mask from only widgets that do not exclude that target (rather than unioning all exclusions first), then apply updates.

- [ ] Title: Server-mode filter refresh updates only one raw source per graph and leaves other layers stale
  - File Names and Line Numbers: dash_render.py (8055-8061, 8157, 8167, 8330, 8358, 8371, 8392, 8410, 8490, 8520, 8538, 8568, 8588, 8621, 8645, 8690, 8724, 8749, 8759, 8774, 8826, 9249-9279)
  - Description: During generated server figure construction, each raw plot layer can create its own `ColumnDataSource` and repeatedly overwrite `graph_sources[gname]` with the most recently created source. The filter callback later iterates `graph_sources.items()` and updates only that single stored source per graph. For multi-layer graphs, earlier raw-layer sources are not refreshed after filter changes, so layers can drift out of sync. This is core functionality breakage for multi-layer filtered graphs.
  - Suggested fix: Track all raw-layer sources per graph (for example `graph_sources[gname]` as a list) and update every source in the callback, or enforce one shared per-graph source for all raw layers.

- [ ] Title: Mixed valid/missing filter specs break standalone filter callbacks
  - File Names and Line Numbers: dash_render.py (4078-4096, 6737-6748, 6792-6795)
  - Description: `_build_filter_widgets()` skips any filter whose variable is missing in `fsource`, but `_filter_specs` still includes every original `filters_cfg` entry. `_FILTER_JS` then iterates `filter_specs` and dereferences `all_widgets[fi]` plus `orig[fvar][i]` unconditionally. In mixed cases (some skipped, some built), callback metadata becomes misaligned and the JS callback can throw at runtime (`w` or `orig[fvar]` undefined), so filtering stops working. Local reproduction in this repo confirmed the mismatch (`filter_specs_len=2` while `all_widgets_len=1`) using a spec with `missingvar` + `foreign` filters.
  - Suggested fix: Build `filter_specs_json` from the same successfully-built filter list as `all_widgets`, and add defensive guards in `_FILTER_JS` (`if (!w || !orig[fvar]) continue;`) so skipped specs cannot crash callbacks.

- [ ] Title: Standalone aggregate plots remain stale when filters return zero rows
  - File Names and Line Numbers: dash_render.py (4198-4204, 4227-4229)
  - Description: In `_FILTER_JS`, aggregate recomputation exits early when filtered numeric values are empty (`if (vals.length === 0) continue;`). That path leaves the previous `src.data` untouched, so histogram/kdensity layers continue showing old values even though the active filter selects no rows. This is a core correctness bug because visual aggregates no longer represent the filtered dataset.
  - Suggested fix: When `vals.length === 0` (or `< 2` for kdensity), explicitly assign empty arrays to the aggregate source schema and emit a change so aggregate plots clear instead of staying stale.

- [ ] Title: Server dropdown filters use display labels as keys and lose distinct values
  - File Names and Line Numbers: dash_render.py (9187-9199, 9235-9238)
  - Description: Generated server code populates `Select.options` with labels only (`['All', ...]`) and stores a reverse map keyed by label text (`widget._dash_opts_map = {o[1]: o[0] ...}`). When two raw values share the same display label, the later entry overwrites the earlier one, so one category becomes unreachable. The same mechanism also collides with the reserved `'All'` sentinel used for “no filter”, making real labels equal to `'All'` unfilterable. Reproduced locally by generating a server app where value labels `1 -> Same` and `2 -> Same` produced `map={'All':'All','Same':'2'}`.
  - Suggested fix: Keep stable raw values as widget option values (for example `(raw, label)` tuples) and use a dedicated sentinel value such as `__all__` instead of human-readable `'All'`.

- [ ] Title: Server app crashes when `slider`/`range` filter targets a string variable
  - File Names and Line Numbers: dash_render.py (9180-9181, 9200-9207, 9211-9217)
  - Description: The generated server builder only checks that the filter variable exists in `df`, then unconditionally computes `float(df[fvar].min())`/`float(df[fvar].max())` for `range` and `slider`. For string columns this raises `ValueError` at document build time and prevents the dashboard from loading. Local reproduction in this repo with `filter("group, type(slider)")` on a string column raised `ValueError: could not convert string to float: 'A'`.
  - Suggested fix: Gate `slider`/`range` to numeric dtypes (skip with warning or coerce safely), and fall back to `dropdown` behavior when the target variable is non-numeric.

- [ ] Title: KPI filter callback allows style-attribute injection through unescaped colors
  - File Names and Line Numbers: dash_render.py (4180-4184, 6813-6823)
  - Description: In standalone filter callbacks, KPI `color` and `bgcolor` values are copied into `kpi_config_json` without escaping and then concatenated directly into inline-style HTML (`'color:' + k.color`, `'background:' + k.bgcolor`). A crafted color string containing quotes can break out of the `style` attribute and inject event handlers/markup when the callback rewrites `kpi_div.text`. This is a DOM XSS vector independent of the already-documented unescaped title/subtitle path.
  - Suggested fix: Strictly validate KPI color fields to safe CSS color formats (hex/rgb/named whitelist) and/or HTML-escape before callback HTML assembly; safest small fix is to sanitize both fields when building `_kpi_config_for_cb`.
