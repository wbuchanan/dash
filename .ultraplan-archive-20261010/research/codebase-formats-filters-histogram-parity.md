# Codebase research: formats, filters, histogram, parity (E1, E3, G6, X1, E2, C2, E14)

> Researcher: codebase agent B, 2026-09-25, at HEAD `91d97be` (the audit commit; no code file has changed since, line numbers moved by at most 1-3 lines).
> All paths relative to the repository root.

## Summary

**Anchors match the audit.**

**Key anchors (dash_render.py unless noted)**
- **Formats (E1/E3/G6):**
  - Numeric format helpers: `_parse_stata_numeric_fmt` 839, `_stata_numeric_pattern` 870, `_format_stata_numeric` 892.
  - Dates: fixed KPI date pictures in `_format_date_value_standalone` 289-332; `_datetime_formatter_for` 335.
  - KPI cards: `_dash_effective_kpi_fmt` 19591, `_dash_format_kpi_value` 19609; `_kpi_js_number_format` 23004 feeds the JavaScript writer `dash_numfmt` (14378-14482).
  - Tooltips: `_dash_hover_row` 19795.
  - `_dash_load_columns` 635 and the served `_NUM_FORMATS` 24930 keep only `%f` formats, so `%g`/`%e` are never carried.
  - dash.ado sends display formats (`_dash_formats_json` 4075) but no storage type. The data writer `_dash_write_stata_data` (1214) would need `sfi.Data.getVarType`.
- **Filters (X1/E2):**
  - Python side: `_dash_option_value` 17413, `_dash_dropdown_values` 1806, `_dash_dropdown_mask` 17669, `_dash_frame_filter_mask` 13950, `_dash_excluded` 17975.
  - Saved-page JavaScript: `_DASH_FILTER_MASK_JS` 14110 (dropdown test at 14131-14140); the saved callback wiring is 23723-23826.
  - Served app: `_on_filter_change` 26760. The trigger widget's exclusions are read at 26767; KPIs are skipped at 26948.
- **Histogram (C2):** continuous edges 9750-9766, `np.histogram` 9577, the JavaScript recount 14818-14826, dash.ado `start()` check 3832. The served `_compute_histogram` no longer exists; the served app redraws through `map_histogram`, so fixing that fixes both modes. Reproduced: ttl_exp `bin(27)` counts 2245 of 2246 rows, census pop `bin(75)` 49 of 50.
- **Presentation parity (E14):** `_dash_served_template` 2169, saved viewport meta 2313, `_apply_nonselection_dimming` 21855 (a method, so the served app can't copy it), served range branch 26012-26024, saved bs filter bar placed at 22726-22731, served bs grid 18606 / reflow 17824.

**Every place a number or date becomes page text:**
1. KPI cards: first paint, after a filter move and after a brush, in both modes.
2. Dropdown option labels.
3. Slider and range labels (Bokeh's default formats).
4. Tooltips, including the fallback precision rule.
5. Date-axis ticks, and numeric axis `format()`.
6. Marker labels and `mlabformat()`.
7. by() panel titles for date variables.
8. The CSV writer.
9. colorvar legend labels (X2's area).

**Where the code no longer matches GAPS2**
- **X1:** the saved snapshot (`_dash_json_value` 13828) turns string codes into numbers: '01' becomes 1.0 and 'nan' becomes missing. So for string codes both modes merge '01'/'1'/'1.0' the same way; "keeps no row" could not be reproduced. The saved-only failures confirmed under node are 5e-05 and 1e21, which select nothing. The same coercion reaches graph snapshots, string marker labels and `dcount` after a move.
- **X1 / Q13:** `""` is already listed as a dropdown option.
- **C2:** there is no `_compute_histogram` left to change.
- **E2:** a node runner that writes its results back into the Python models already exists (`test_saved_filter_layers.py:181`), so moves can already be chained. The runners in `test_filter_exclude.py:156` and `test_statistical_helpers.py:820` do lose state between calls.
- **E1:** `_format_stata_numeric` ignores the width for `%e` (Stata's `%9.3e` of 1234.5678 is `1.23e+03`; dash writes `1.235e+03`).
- **E3:** a missing date on a KPI card reads "" at first paint, '—' after a move, and "." in Stata.
- **E14:** the ALLOWED key in `test_mode_parity.py` can't simply be deleted; only its filter/title clause and the check at 1498-1506 change. The Chrome runner's widths are 375/768/1440, not the 375/900/1440 the plan names, and it renders the served page without the served template.

**Security points for the plan**
- `test_label_sinks.py:856` restricts tooltip fields to a fixed pattern, which will reject `{custom}` formatters.
- The JavaScript KPI card rebuild (14643) inserts its text without escaping. Date pictures can carry the user's own text through `!` escapes, so that text must be escaped.

**Reusable helpers:** `_dash_unix_ms_to_unit` (16214), `_stata_dates_to_datetime` (378), `GlyphMapper._mlabel_number_text` (7033, Stata's `%18.0g` rule), the JavaScript `dash_fixed`/`dash_expo`/`dash_tie_even`, the served copy lists (24326, 24466), and the display outputs in `date_truth.json` (15 numeric formats × 10 values, all 8 date kinds).

---

## 0. State
- Branch `s3-bugs`, HEAD `91d97be` (the audit commit). The only uncommitted changes are under `.ultraplan/`, so the audit's line numbers are nearly exact.
- Tools: Python 3.14.5, Bokeh 3.9.0, pandas 3.0.1, numpy 2.4.3, node v24.13.1. `CustomJSHover` and `CustomJSTickFormatter` take `args` and `code`.

## 1. The shared display-format writer (E1, E3, G6)

### 1.1 Current helpers
- **`_parse_stata_numeric_fmt`** (839-867) reads only `%w.d[f|e][c]`:
  ```python
  m = re.fullmatch(r"%(-)?(\d+)\.(\d+)(f|e)(c)?", fmt.strip())
  ...
  if not 1 <= width <= 2045 or dec >= width: return None
  ```
- **`_stata_numeric_pattern`** (870-889) returns a numbro pattern for `f` formats only; `e` and `g` return None.
- **`_format_stata_numeric`** (892-938) handles `f`/`fc` with Stata's width fallbacks. Its `e` branch is `f"{val:.{dec}e}"`, which ignores the width. `date_truth.json` shows Stata writes `%9.3e` of 1234.5678 as `1.23e+03`.
- **`_format_date_value_standalone`** (289-332) uses one fixed picture per date kind:
  ```python
  if kind in ("tc","tC"): return f"{ts.strftime('%d %b')} {year} {ts.strftime('%H:%M:%S')}"
  if kind in ("tm","tq","th"): return f"{ts.strftime('%b')} {year}"
  return f"{ts.strftime('%d %b')} {year}"
  ```
- **`_datetime_formatter_for`** (335-356) builds one `DatetimeTickFormatter` per kind.
- **`_stata_date_kind`** (359) and `_DATE_FMT_RE` (238).
- **`_stata_dates_to_datetime`** (378-508): Stata values to datetime64[ms].
- **`_dash_unix_ms_to_unit`** (16214-16258): the inverse, milliseconds to Stata units d/w/m/q/h/y with the fraction of the period. Reuse it to turn a stored date back into a Stata value before formatting.
- **`_dash_load_columns`** (635-697) keeps a numeric format only when `_stata_numeric_pattern(fmt)` is not None. So `%g`, `%e` and `%8.0gc` (auto's price) are dropped, and a KPI falls back to `%9.0g`.
- **`_dash_effective_kpi_fmt`** (19591-19606): `fmt()`, else the variable's own format, else `%9.0g`.
- **`_dash_format_kpi_value`** (19609-19680): the date branch comes first, so a date KPI ignores `fmt()`. `%9.0g` and "" become `f"{v:g}"`; any other format goes to Python's `format()`, and a format Python can't apply falls back to `str(value)`:
  ```python
  if fmt in ("", "%9.0g"): return f"{float(value):g}"
  ...
  try: formatted = f"{value:{fmt}}"
  except (ValueError, TypeError): formatted = str(value)
  ```
  Measured: `%10.0g` of 6165.2567 gives `6e+03`, `%9,2f` gives `6165.2567`, `%td` of 15000 gives `15000`.
- **The JavaScript twin** in `_FILTER_JS`: `dash_tie_even`, `dash_fixed`, `dash_py_exp`, `dash_expo`, `dash_py_g`, `dash_pystr`, `dash_py_group`, `dash_numfmt` (14388-14482). `dash_apply_kpis` (14484-14648) has a date branch with fixed pictures (14578-14604; a missing date gives '—') and a number branch (`dash_numfmt`, with dead legacy `k.general`/`toFixed` branches at 14613-14624).
- **`DashRenderer._kpi_js_number_format`** (23004-23042) sets `numfmt` kind f/e/g/str. `_parse_fmt` (22996) only feeds `decimals`/`commas`, which are dead once `numfmt` is set.

### 1.2 Does dash.ado export formats and storage types?
- **Formats: yes.** `_dash_formats_json` (dash.ado 4063-4121) reads `st_varformat` in Mata:
  ```stata
  mata: st_local("_fjv", _json_escape(st_varformat(st_local("v"))))
  mata: st_local("_fdate", strofreal(regexm(st_varformat(st_local("v")), "^%-?t[cCdhmqwy]")))
  ```
  It is called at 5925 (the one-line command route) and 6879 (build). The result goes into `build_options.formats` at 5973 and 7042.
- **Readers:** `DashRenderer._load_data` (21164-21187: `self.formats`, then `self.date_vars` and `self.numeric_formats` through `_dash_load_columns`). The served app's loader is at 25734-25738, and `_NUM_FORMATS` at 24930-24934 uses the same `%f`-only test. `_num_formats`/`_date_vars` are set in `make_document` at 25860-25877.
- **Storage type: no.** `_dash_write_stata_data` (1214-1376, called from dash.ado `_dash_write_data` 4169) writes only `variableIsString` and `float(x)`, so a float 0.1 arrives as 0.10000000149011612. The G6 plan needs `data.getVarType(v)` added to the document and read by both loaders. The test stand-in `FakeSfi` in `test/test_string_value_export.py` (78ff) already carries `types` and needs a `getVarType` method.
- **`dash kpi`:** `fmt()` is validated by `_dash_validate_value … "format"` (dash.ado 2294-2313):
  ```stata
  if regexm(scalar(`V'), "^%[A-Za-z0-9_.,:!/+-]+$") & strlen(scalar(`V')) <= 60 {
      capture confirm numeric format `macval(value)'
  ```
  This accepts `%21x`, `%16H` and presumably `%16L`/`%8H`/`%8L`. The call site is 6230-6239. Stata's own display text is `kpi_display` at 6331-6335 and travels as `"display"` in `kpis_json` (6974). That field is a ready truth value for cert tests.

### 1.3 Every place a number or date becomes page text
| # | Where | Saved page | Served app | Current rule |
|---|---|---|---|---|
| 1 | KPI first paint | `_build_kpi_html` 23374, then `_format_kpi_value` 21354, then `_dash_format_kpi_value` | `_format_kpi` 25789-25803, called at 26644 | Python `format()`; dates by fixed picture |
| 2 | KPI after a filter move | `dash_apply_kpis` 14578-14625, config from `_kpi_callback_config` 23385-23451 | `_on_filter_change` 26956 | JavaScript `dash_numfmt` / Python |
| 3 | KPI after a brush | `_BRUSH_JS` 14935 (slices `_FILTER_JS`, 23483-23486) | brush callback 27038 | same |
| 4 | Dropdown labels | `_dash_filter_widget` 17593-17618 (shared) | same function at 26703 | date `str(d)` shows "2001-12-31 00:00:00"; numbers show the raw option text ("0.10000000149011612", "5e-05") |
| 5 | Slider and range labels | `_dash_filter_widget` 17637-17663 | same | Bokeh defaults: numeric `0[.]00`, date `%d %b %Y`, clock `DatetimeTickFormatter()` (17648); steps from `_whole_number_step` 14959, `_date_slider_step_days` 2033-2054, `_clock_slider_step_ms` 2057 |
| 6 | Tooltips | `_dash_hover_row` 19795-19808 via `_dash_build_hover` 19839 (saved call 22348) | copied, called at 26451 | dates `{%F}` (or `{%F %T}` for tc only); numbers only when `%f` |
| 7 | Tooltip fallback | `_tooltip_precision` 260, used at 20026-20051 | same | spread-based `0.00` |
| 8 | Date-axis ticks | 22029-22034 | 26198-26200 | `_datetime_formatter_for` |
| 9 | Numeric axis `format()` | `_dash_apply_axis_spec` 16800-16810 | same | `%f` only through NumeralTickFormatter (the default axis is G10's gap) |
| 10 | Marker labels | `GlyphMapper._apply_mlabel_opts` 6732-6765 | same mapper | value labels via `_mlabel_value_text`/`_mlabel_number_text` 7033-7104 (twoway's `%18.0g`); dates via `_mlabel_date_texts` 6879-6902; `%f` via `_format_stata_numeric` 6760; otherwise the raw value (6763), which prints the float32 expansion |
| 11 | `mlabformat()` | `_mlabformat_column` 6904-6971 | same | `%f`/`%e` only; `%g` is named and not applied |
| 12 | by() panel titles | `_dash_facet_label` 15549-15615 with `_format_date_value` 21754 | with `_dash_stata_date_text` 15618 (26547-26550) | numbers: twoway's `%18.0g` (keep); dates: fixed picture |
| 13 | CSV | `_DASH_CSV_JS` 14012-14076 (`dash_csv_number` = `String(v)`, `dash_csv_date` = ISO), `_dash_csv_meta` 13880 | `_DASH_CSV_SERVED_JS` 14081, `_dash_csv_payload` 13920 | raw values |
| 14 | colorvar key labels (X2's area) | `_vlookup` `f"{v:g}"` 6417-6420, cut labels 6467-6488, ColorBar 6623 | same | Python `:g` |

Notes and warnings (`_fmt_num` 16956) and the CI legend key `f"{lvl:g}% CI"` (19787) are not data values.

### 1.4 Plumbing the plan needs
- The served app copies helpers by name: constants at 24326-24428 and functions at 24466-24687, using `inspect.getsource`. A new formatter function must be added to the function list. A JavaScript twin kept as a string constant must be added to the constant list, as `_DASH_CSV_SERVED_JS` is.
- Guard tests that will catch a missed name: `test_statistical_helpers.py:1335` (`TestTheServedAppCarriesEveryName`) and `test_resource_limits.py` (`TestTheServedAppDefinesEveryNameItReads`).
- The formatter should take the full format string, not the date kind. `date_vars` holds only the kind, so a custom picture such as `%tdCCYY-NN-DD` is lost today. The served app needs the full `bo['formats']` passed into `make_document`.
- A date column is stored in milliseconds, so the formatter needs the Stata value. Use `_dash_unix_ms_to_unit` and floor it for the period kinds.
- **Period sliders (E3 step 3):** a numeric slider over the Stata period number needs the masks to convert the column the same way: `_dash_frame_filter_mask` 13989-14008 and the JavaScript mask 14141-14160. Suggest a `unit` field in the filter spec, and a JavaScript twin of `_dash_unix_ms_to_unit`.
- **Security:**
  - The JavaScript card rebuild (14637-14645) concatenates `fmt` into HTML without escaping. The Python card escapes it (`_dash_kpi_card_html` 13629).
  - Variable formats come from `st_varformat` without the `fmt()` character check, and date pictures can hold any character through `!`.
  - Tooltip fields are pinned by `test_label_sinks.py:855-857`:
    ```python
    _PLACEHOLDER = r"@\{[^\W\d]\w*\}(?:\{[0-9.,%FT ]+\})?"
    ```
    A CustomJSHover field such as `@{x}{custom}` fails it, so widen it on purpose and carry the format in `args`.
- `function_test_map.py` must name every new function and drop removed ones (for example `_datetime_formatter_for`, `_parse_fmt` and `_kpi_js_number_format` if they go).

### 1.5 Tests that pin today's behaviour (these must change)
- `test_dates.py` `TestNumericDisplayFormats` (~420-490): `test_a_format_dash_does_not_reproduce_returns_none` expects `%9.0g`/`%12.0gc` to return None. `test_every_measured_f_and_fc_value_is_reproduced` asserts exactly 56 cases.
- `test_date_range.py` ~944-958 pins "31 Dec 9999", "01 Jan 0100", "Jan 0100", "01 Jan 0100 00:00:00". Its line 609, `test_served_dates.py` 129/229 and `test_help_claims_4.py` 1706 pin `@{date}{%F}`.
- `test_saved_filter_layers.py` `TestADateDropdown.test_the_option_labels_still_read_as_dates` (~1213) pins "2001-12-31 00:00:00". `TestTheOptionValueOfADate` (1219-1245) pins `_dash_option_value(1.0) == "1"`.
- `test_server_layer_defects.py` 1080-1101 pins the KPI format (21.2973 for `%9.0g`, which Stata agrees with).
- `test_adversarial_matrix.py` 1664-1695 pins format bounds.
- Keep: `test_help_claims_4.py` `TestACardKeepsItsFormatWhenAFilterMoves` (784; `_FORMATS` at 780), which checks the card looks the same before and after a move, and `test_kpi_values.py` `TestKpisUnderFiltering` (327; `_js_format` 420 runs the shipped branch under node).

### 1.6 Fixtures
- **`test/fixtures/date_truth.json`** (written by `scripts/extract_date_truth.do`; format list at 224):
  - `numeric_formats`: 15 formats × 10 values (0, -1, ±1234.5678, ±1234567.891, 0.000123456, 1e12, ., .a), each with Stata's padded `display` text. Formats: `%9.0g %10.0g %8.0g %20.15g %10.0gc %12.0gc %-12.0gc %9.0f %9.0fc %9.2f %9.2fc %-9.2f %12.2fc %9.3e %9.4f`.
  - `date_formats`: all 8 date kinds with `display` and `iso` (for example `%tm -120` gives " 1950m1"; `%ty -50` gives " -50").
  - Also `left_aligned_prefix` and `leap_seconds`.
  - It has no European comma, no `%x`/`%H`, and no custom pictures other than the ISO ones.
- **`test/fixtures/value_truth.json`** (no script in the repo; a 22sep2026 probe; read by `test_option_validation.py`): `formats` holds 28 `confirm numeric format` return codes, for example `%21x`, `%16H` and `%9,2fc` give 0 and `%12s` gives 7. It holds no display text.
- **`test/fixtures/kpi_truth.json`** (made by probe do-files under `/tmp/dash-kpi/`, not in the repo): statistic values and definitions (anchor, kpi_stats, brush, percentile_definition, …) with one display string, `as_displayed_9_4f`.

## 2. Filters (X1, E2)

### 2.1 X1: code
- **`_dash_option_value`** (17413-17441) turns anything that reads as a whole number into integer text, strings included:
  ```python
  s = str(v)
  try:
      f = float(s); i = int(f)
      if f == i: return str(i)
  ```
- **`_dash_dropdown_values`** (1806-1812) drops the categories 'nan', 'None' and 'NaT':
  ```python
  {_dash_option_value(v) for v in series.tolist()
   if v is not None and str(v) not in ("nan", "None", "NaT")}
  ```
- **`_dash_option_sort_key`** 17444. `_dash_filter_effective_type` (1815-1854) calls `_dash_dropdown_values` at 1835.
- **Saved JavaScript** `_DASH_FILTER_MASK_JS` (14110-14164): `if (active[i] && (!present(col[i]) || String(col[i]) !== val))` at 14138. The same code is shared by the CSV button (`_DASH_CSV_SAVED_JS` 14168).
- **Served:** `_dash_dropdown_mask` (17669-17675) maps `_dash_option_value` over both sides and is used by `_dash_frame_filter_mask` 13983-13988.
- **colorvar strings:** 6527, `"" if v is None or str(v) == "nan"`.
- **Snapshot coercion (not in GAPS):** `_to_serialisable` (22983) calls `_dash_json_value` (13828-13862), and `float("01")` becomes 1.0, "nan" and "inf" become None. It is applied to `_orig_data` (23685-23688), to each graph snapshot `_snapshot_of` (23693-23700) and to derived snapshots (23811-23816).
- **Measured today (node against pandas):**
  - String codes: both modes select '01', '1' and '1.0' with option '1', so they agree.
  - Numbers: 5e-05 and 1e21 select nothing on the saved page and one row served.
  - A float 0.1 is listed as '0.10000000149011612'.
  - `""` is already listed and selectable.
- **Consequence of the snapshot coercion:** after a move on the saved page, a string marker label "007" becomes 7, and `dcount` of string codes merges '01' and '1'. The X1 fix must keep string columns as text in every snapshot, not only in `_dash_option_value`.
- **Plan note:** Bokeh `Select` values must be strings. "Numbers compared as numbers" therefore means a per-filter `numeric` flag in `filter_specs_json` (built at 23707-23714), with `Number(val)` compared in JavaScript and `float` compared in pandas.

### 2.2 E2: code
- **`_dash_excluded`** (17975-17985):
  ```python
  return key in excluded or owner_of.get(key) in excluded
  ```
  The saved `_owner_of` map is built at 23719-23721; the served one is `_facet_to_orig` (26656-26659).
- **Saved wiring** (`_build_filter_widgets` 23535-23842): one CustomJS per widget (built by `FilterBuilder.build_*` 14979-15203). For each callback (23723-23826):
  - `_kpi_config_for_cb` leaves out any KPI in that filter's exclude() (23727-23735).
  - `all_graph_sources` holds the sources that filter doesn't exclude (23745-23751); `excluded_sources` 23763-23771; `view_filters` 23776; the snapshots 23785-23787; `agg_sources` skipped when excluded (23789-23798); derived sources the same (23802-23826).
  - The JavaScript uses one mask of all widgets, `const active = dash_filter_mask(orig, filter_specs, all_widgets);` (14186). It writes only the targets it was handed; the fallback write is at 14347-14351.
- **Link group:** one shared source. It is in `all_graph_sources` whenever any member isn't excluded, so the group is excluded only when every member is (dash.sthlp 1130-1137, pinned by `test_help_claims_3.py` `TestAnExcludedMemberOfALinkGroupIsFilteredWithIt` 397).
- **Served `_make_filter_cb` / `_on_filter_change`** (26758-26964):
  ```python
  mask = _dash_frame_filter_mask(_df_ref, _all_widgets)
  fdf = _df_ref[mask]
  excl = getattr(_trig_widget, '_dash_exclude', [])
  for gname, srcs in _all_sources.items():
      if _dash_excluded(gname, excl, _gfac_to_orig): continue
  ```
  - The shared source is written once (26870-26877) through `_dash_refresh_linked` (18058).
  - Aggregates are redrawn by `agg['redraw'](agg_fdf)` (26879-26939).
  - KPIs are skipped with `if kname in excl: continue` (26948).
  - `widget._dash_exclude = fexcl` is set at 26719.
- **Fix outline:**
  - Per-target mask = the AND of the filters whose exclude() doesn't name the target. Group mask = the AND of the filters that don't exclude every member.
  - Served: call `_dash_frame_filter_mask(df, [w for w in widgets if not _dash_excluded(t, w._dash_exclude, owners)])`, caching one mask per exclusion set.
  - Saved: pass every target with its exclusion set, and have the JavaScript compute one mask per distinct set. All widgets can then share one callback.
- **Tests:**
  - `TestExcludeHoldsWhileItsOwnFilterMoves` is in **`test/test_help_claims_3.py:415-497`**. Saved (441-467): it sets both widgets in Python, runs one callback and expects `{"g1":10,"g2":5,"k1":"10"}` then `{"g1":3,"g2":3,"k1":"3"}`. Served (469-497) chains `tp._fire` (`test_mode_parity.py:1649`).
  - Also `TestAKpiCardCanBeExcluded` (351), `test_filter_exclude.py` (whole file; `TestBothModesAgree` 391, `TestThePrimarySourceFallback` 469) and `test_linking_filters.py`.

### 2.3 Node runners (and why chaining fails)
- **`test_statistical_helpers.py:820-856`**, `_run_filter_js_block`, runs only the histogram or kdensity block of `_FILTER_JS` on literal `vals` in a temporary `.mjs` file and prints `src.data`. It has no widgets, sources or registry, so it has no state to carry. `TestFilterJavaScript` 859-884.
- **`test_filter_exclude.py:156-210`**, `_RUNNER` / `_run_callback`: `_encode` (123) turns each Bokeh model into one stand-in in `RAW.models`. Node rebuilds `REG`, runs the CustomJS body with `new Function` and prints row counts. The state is lost because each call re-encodes from the Python models, which still hold the build-time data, and node's writes (`o.data`, Div `text`, `BooleanFilter.booleans`, glyph `width`) disappear when the process exits. Reused by `test_help_claims_3.py` `_RUNNER_DIVS`/`_run_saved` (321-348).
- **`test_saved_filter_layers.py:85-214`**: the same runner, but `_run` writes node's source data, booleans, Div text and width back into the Python models (199-213). Repeated `_run` calls therefore do chain moves. This is the natural base for a stateful mode: all callbacks' args encoded into one `models` dict, a list of steps `{set widget values, run callback}`, dumped at the end.
- Also `test_help_claims_4.py` `_RUNNER`/`_run_js` (85, 168) and `_saved_filter_move` (220), and `test_export.py` `_saved_mask`/`_run_js` (41-77, mask only).

## 3. C2: histogram edge rule
- **`GlyphMapper.map_histogram`** 9519-9627. Discrete branch (9565-9575), already Stata's rule:
  ```python
  idx = np.floor((arr - float(edges[0])) / h)
  idx = np.clip(idx, 0, nb - 1).astype(np.int64)
  counts = np.bincount(idx, weights=w, minlength=nb).astype(float)
  ```
  Otherwise `counts, _ = np.histogram(arr, bins=edges, weights=w)` (9577).
- **The agg config** (9607-9623) carries `bin_edges`, `ymode`, `wvar`, `wtype` and `discrete`. It needs `start`, `width` and `bin` so the JavaScript doesn't rebuild h from the edges.
- **`_histogram_grid`** 9629-9768. Continuous edges (9750-9766):
  ```python
  edges = start + width * np.arange(n_bins + 1, dtype=float)
  _edge_tol = 1e-9 * max(abs(float(a_max)), abs(float(start)), float(width), 1.0)
  if edges[-1] < a_max - _edge_tol:
      edges = np.append(edges, a_max)
  ```
  A value a few ULPs above `edges[-1]` is dropped by `np.histogram`. Reproduced: ttl_exp `bin(27)`/`bin(51)` count 2245 of 2246 (last edge 28.884614944458004 against a maximum of …008); census pop `bin(75)` counts 49 of 50.
- **`_histogram_heights`** 12746 (density per bin width) and **`_stata_bin_count`** 12778.
- **Stata's rule** (`/Applications/StataNow/ado/base/t/twoway__histogram_gen.ado` 198-200):
  ```stata
  gen `midbin' = floor((`v'-`min')/`h') if `touse'
  replace `midbin' = 0 if `touse' & `midbin' < 0
  replace `midbin' = `bin'-1 if `touse' & `midbin' == `bin'
  ```
  Here `min = start` when `start()` is given (102-111), and the last edge is `min + h*bin`.
- **The JavaScript recount** is in `_FILTER_JS` at 14768-14834. The continuous path (14818-14826) drops values outside `[edges[0], edges[last]]`:
  ```js
  if (v < edges[0] || v > edges[edges.length - 1]) continue;
  if (v === edges[edges.length - 1]) { counts[n_bins - 1] += wv; }
  else { for (let b = 0; b < n_bins; b++) { if (v >= edges[b] && v < edges[b + 1]) {...} } }
  ```
  The discrete path (14808-14816) already uses floor and clamp.
- **Served:** `_compute_histogram` was deleted (see the comment at 25760-25769). The served app redraws through the mapper (`agg['redraw']` 26919, registered at 26369-26375), so fixing `map_histogram` fixes the served app too.
- **dash.ado** 3823-3837 lets a `start()` slightly above the minimum through (the reldif check):
  ```stata
  if r(min) < `s(start)' & reldif(r(min), `s(start)') > 1e-5 {
  ```
- **Truth:** `scripts/extract_stat_truth.do` layer 1 (276-380) runs `twoway__histogram_gen … generate(zqh zqx) return` for each dataset × {default, bin(20), width(2), start(10), and the four y-axis types}. It records bin, start, width, xmin, xmax, area, N, n_x, type, `bin_midpoint`, and `bar_height` for non-empty bars only.
  - Keys present include `census:pop:*` and `nlsw88:{wage,hours}:*`. `nlsw88:ttl_exp` and `bin(75)`/`bin(27)` are not recorded.
  - The CSVs `test/fixtures/data/nlsw88.csv` (wage, ttl_exp) and `census.csv` (death, pop) are checked in.
- **Tests:**
  - `test_statistical_truth.py` `TestHistogramAgainstStata` 121-177 (the bin rule and heights of non-empty bars; `_rec` fails loudly) and `TestHistogramDiscrete` 1233.
  - `test_statistical_helpers.py` `_hist` 768, `TestHistogramDiscreteTopBar` 779, `TestFilterJavaScript` 859, `TestHistogramOfOneValue` 902.
  - `test_resource_limits.py` `TestAHistogramWidthCannotOverflow` 65.
  - BUGS.md 1191 (discrete, fixed) and 1215 (`start()` above the minimum, the residual).

## 4. E14: saved and served presentation
1. **Viewport meta.** `_dash_served_template` (2169-2195) adds only the CSP to the preamble:
   ```python
   "{% block preamble %}{{ super() }}    " + _dash_csp_meta(_DASH_CSP_SERVED) + "\n{% endblock %}"
   ```
   The saved page's `_CSP_META` (2307-2314) includes `<meta name="viewport" …>`. The served app sets the template at 25824. The template text is copied into the app, whose source is checked for script tags. Pinned by `test_help_claims_4.py:1643` `test_the_page_has_no_mobile_viewport` (asserts it is absent; flip it).
2. **Dimming.** `DashRenderer._apply_nonselection_dimming` (21855-21874) sets `ns.fill_alpha`/`line_alpha = _NONSELECTION_ALPHA` (0.15, defined at 1996). It is called at 23309 (by() panels) and 23332. It is a method, so it can't be copied; it needs a module-level function in the copy list. `_NONSELECTION_ALPHA` is already copied (24340) but unused. Call it in the served app for linked figures (`_dash_figure_for` 26109; linked names at 25888 and panels at 26566-26570). Pinned by `test_help_claims_4.py` `TestTheModesDifferHere.test_a_brush_dims_unselected_points_less_when_served` (~1668; asserts served == {0.1}) and the docstring of `test_help_claims_5.py` `TestAFacetedGraphInALinkGroup` 846.
3. **rspike and rconnected selection.** `map_rspike` (10070) draws from the `source` it is given; `map_rconnected` (10256) calls `map_scatter` on `source`. The saved page hands them the link source. The served range branch (26012-26024) always builds `_dash_range_source(g_df,…)` (19439-19466), a new source per layer, so a selection never reaches it. Fix: for a linked graph, use the shared source with an IndexFilter view, as `_dash_layer_source` does (19391-19436).
4. **Served bs grid.** `_dash_bs_grid` (18606-18659) uses `GridBox(cols=[_DASH_BS_TRACK]*12, spacing=16)`, then `_dash_reflow` (17824-17876), which adds only the `max-width: 767.98px` stacking rule. The saved page's CSS (`_DASH_GRID_CSS` 2318-2402) has md spans (768-991: `db-col-md-{_md_span(span)}`, where `_md_span` at 5246 turns spans of 4 or less into 6), lg spans from 992 (2363-2376), and KPI min-heights `.db-cell-h-sm/md/lg` 130/150/170, and 120 below 768 (2381-2386). Those classes are applied in `_render_bootstrap_html` 22653-22666 through `_cell_height_class` (5265). Served KPI Divs carry only `_dash_kpi_stylesheets()` (25318; the card's own `min-height:110px`, 13634). Reproducing the md half-row needs per-child CSS on the GridBox; that is a risk for the plan.
5. **bs filter bar position.** The saved page builds `page_body_html = filter_bar_html + header_html + tabs + grid` (22712-22731). The served app puts the header above the filter bar above the content (27242-27263), as the saved non-bs layout does (`_assemble_layout`). The `filterposition(left)` layouts differ too (saved bs: header inside the right column, 22699-22711; served: header above both), which is not in item 5.
- **`test_mode_parity.py`:** `ALLOWED` (105-139). The key `"layout(bs) is standalone markup"` also covers reading the grid from markup (`_render_pair` 845-866, used at 865) and the check that no filter/tabs/title/subtitle is set (`test_same_document_tree` 1489-1508). The fix removes the "filters above the title" clause and relaxes that check; the key stays.
- **`test_served_bs_layout.py`** (grid cells 300, `TestBsGrid` 345, `TestTheServedGridIsTheSavedPagesGrid` 409, `TestTheServedDocument` 437).
- **`test_responsive_layout.py`:** `WIDTHS = (375, 768, 1440)` (53). `_served_page` (195-209) renders with `file_html(doc, INLINE)`, not the served template. `_chrome()` 212 uses `rp.find_chrome()` (`test/responsive_probe.py:102`, `CHROME_CANDIDATES`, `DASH_CHROME` env override; it skips when Chrome is absent, and a skip fails under `DASH_STRICT=1`). `TestPagesFitInChrome` 245, `TestServedDocumentsFitInChrome` 255 (`SERVED` 157), the reflow model tests 316-427, `TestKpiCardMayNarrow` 571.
- **Help text to rewrite:** dash.sthlp 1486-1494 (what the served app lacks) and 1012-1017 (rspike/rconnected).

## 5. Help-text anchors (current)
- `type(dropdown)` 1110-1116
- `exclude()` 1130-1137
- date KPI shown as a date 1242-1245
- `fmt()` 1256-1258
- marker labels "in its display format" 1783-1784
- linking/selection 1012-1017
- served limitations 1486-1494
