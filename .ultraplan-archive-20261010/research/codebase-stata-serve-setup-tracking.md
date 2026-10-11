# Codebase research: Stata side, serve, setup, tracking (G1, G2, G3, G5, F1, K2, infrastructure)

> Researcher: codebase agent C, 2026-09-25, at HEAD `91d97be` on `s3-bugs`. Stata was not run; `c(python_exec)` was read from `~/.stata19/console/stata19.rc`.

## Summary

**Anchors are current.** HEAD is `91d97be` on `s3-bugs`, the audit commit, and none of the four source files has changed since.

- **G1:** `_ROW_ID_COLUMN` dash_render.py:2008; JS `const ROW_ID` 14219 (a hard-coded string) and 23499; `_make_source` 21383, which overwrites a user column at 21416. The `__dash_pc_row__`, `__mlabel_values__`, `__mlabel_x__` and `__mlabel_y__` columns are at 10832-10890 and 11544; `__mlabel__{var}` at 6750 and 6965. The `__dashq` refusal is dash.ado:4255-4261 (r(110)); its callers are 5943 and 6893. The renderer has its own copy of the refusal at 20277-20342, and it must widen to `__dash` too. **Residual:** `_x_jit`/`_y_jit` (5498) and the derived glyph columns `x`, `y`, `x0`… that `_carry_cols` (5573) skips also share the user's namespace. A `__dash` prefix rule alone does not cover them.
- **G2:** The four `syntax varlist` lines are dash.ado:1273, 1298, 1329 and 1358. Dispatch is 3304-3503 and the families are listed at 2922. **The table now has 40 types, not 38:** WP-22 added `pccapsym` and `pcarrowi`. 36 of them take variables. Adding `numeric` to the four lines gives Stata's own r(109). The options `colorvar`, `mlabel`, `hover` and `by` are checked with `unab` (2149-2233), which already accepts strings.
- **G3:** `_dash_cell_cap` 2735, called at 5920 and 6875. dash.ado keeps no per-graph "needs rows" record; it pools every graph's variables into one list. **Three things to plan around:**
  - The renderer refuses again at 21100, using the whole frame.
  - The served app embeds every row (`_embed_data`, 25092), so relaxing the cap is safe for the saved page only.
  - The size note is `_report_dataset_size` (973/994) at 24 bytes per cell.
- **G5:** `_dash_is_name` dash_parse.mata:828 is used for filter variables (3454) and also for layout and option names. The KPI pattern is dash.ado:6094-6097. **Bigger than GAPS2 says:** the renderer's ASCII-only `_DASH_VARNAME_RE` (19207) drops a Unicode name in `by()` (the graph is drawn without panels), in `filter()` and in `hover()`, and `_apply_colorvar` (6365) silently draws no colours. `_dash_is_stata_name` (1183) is a Unicode-aware check that could be reused.
- **F1:** `_dash_serve_spec` 7252, `_dash_serve` 7349, the port refusal at 7307. The launcher is dash_render.py:27670-27715 and never reads the exit code. There are three clamps, not two: the app's own at 27371, `main()` at 27603, and the launcher at 27680. **Tests currently require the clamp** (`test_render_cli_port.py:151,161`, `test_resource_limits.py:1279`, and two entries in `test_adversarial_matrix.py`), and they must be inverted. `_FakeProc` in `test_help_claims_2.py:756` accepts no keyword arguments and has no `returncode`.
- **K2:** `min_bokeh` dash_setup.ado:146, `_dash_pymin` 285/295, messages at 60/73, `dash_setup.sthlp` 40-42/70/80, `dash.pkg` 17, dash.ado 207, `dash.sthlp` 3131-3133, CHANGELOG 330-334. The generated app has no `__future__` import; its header starts at 25198. `CustomJSTicker` is imported at 16877 and 17217.

**Measured versions**

| Interpreter | Python | bokeh | pandas | numpy |
|---|---|---|---|---|
| Stata's `c(python_exec)`: `/opt/anaconda3/bin/python3` (from `~/.stata19/console/stata19.rc`) | 3.13.9 | 3.8.0 | 2.3.3 | 2.3.5 |
| System `python3`: homebrew | 3.14.5 | 3.9.0 | 3.0.1 | 2.4.3 |

So the floor to declare is **Python 3.13, bokeh 3.8, pandas 2.3, numpy 2.3**, which is exactly the "stata" baseline in conftest.py. Tests that assert the old minimums: `test_setup_honesty.cscript`, `test_program_coverage.cscript` (PC-19..21), `test_help_claims_8`, and `test_setup_python_gate.cscript`.

**How severity is read.** The release check is not `release_verdict.py`, which never reads BUGS.md. It is `test/test_tracking_documents.py`, which looks for exactly one `Graded S<n> (WP-NN): <why>` in an open entry's Resolution. That Resolution must also say "not fixed", "still open", "stays open" or "remains open", plus "because". **Any open S1 or S2 entry turns pytest red.** So opening 22 graded entries up front makes `make check` fail until each one closes.

**Other surprises**
- If WP-28 lists GAPS2 ids under `**Gaps closed:**`, or adds them to the main traceability matrix, `TestGapsAndRoadmapAgree` will check them against **GAPS.md** (a different audit) and fail once WP-28 is marked DONE. Its own matrix heading must not contain the text "## Traceability matrix".
- GAPS2.md is untracked. Committing it fails `test_packaging.py:411` unless it is added to `_ROOT_ALSO`.
- Possible gap, not verified: a `hover()` variable that no plot draws matches none of the export keys.

---

# Full report

**Tree state (measured).** Branch `s3-bugs`, HEAD `91d97be`, which is the GAPS2 audit commit. `git status` shows only `CLAUDE.md`, `REMAINING.md` and `.ultraplan/*` modified, plus untracked `GAPS2.md`, `phases/` and `scripts/__pycache__/`. `dash.ado`, `dash_parse.mata`, `dash_setup.ado` and `dash_render.py` are unchanged, so every GAPS2 line number still applies unless noted.

---

## 1. G1: internal column names

### 1.1 Python twin (the served app uses the same code, copied with `inspect.getsource`)

| Name | Where | What happens on a collision |
|---|---|---|
| `_ROW_ID_COLUMN = "__dash_row__"` | dash_render.py:2008 (comment 1998-2007) | — |
| `_make_source` | 21383-21417; `data_dict[_ROW_ID_COLUMN] = self._row_ids_for(frame)` at **21416**, after the user's columns | **Overwrites** a user column `__dash_row__` |
| other `_ROW_ID_COLUMN` uses | 7442-7484, 7808, 10836-10850, 10921, 11170, 11498-11533, 13898 (CSV leaves it out), 21454, 21495-21511, 22191, 23499, 23509, 23688, 23837; the served app gets it through the constant list at 24340 | — |
| `__dash_pc_row__` | 10838, 10849: a pandas `clean` frame built from the 4 coordinate columns (10815-10820) | A coordinate variable of that name is overwritten |
| `__mlabel_values__` | 10832, 10865-10872, 10889 (pc mappers); 11544-11551, 11565 (rscatter) | Same as above, in `clean` |
| `__mlabel_x__`, `__mlabel_y__` | 10861-10863, 10889 | — |
| `__mlabel__{var}` | 6750; written into the **caller's** (graph) source at ~6765, guarded by `if text_col not in source.data` | A user column of that name is **read as the label text** |
| `__mlabel__{var}__fmt_{hex}` | 6965 (same guard) | Same |
| `__{ptype}_label__` | 11345: a fresh source holding literal coordinates only | No risk |
| `_x_jit`, `_y_jit` | `_build_jitter_source` 5450-5500: copies every source column, then **overwrites** `_x_jit`/`_y_jit` (5498-5499). The linked variant 5556-5566 avoids this with suffixes | A user `_x_jit` is overwritten |
| derived glyph columns `x`, `y`, `x0`, `y0`, `x1`, `y1`, `top`, `left`, `right`, `lo`, `hi`, `count`, `density` | rebuilt sources; `_carry_cols` (5573-5613) never overwrites them; 16 call sites (7318 … 11552) | A user variable with one of these names is **not carried**, so `hover()`/`mlabel()` read the derived value |
| `__dashfix<12 hex>` | `_dash_write_stata_data` (1214), lines **1296-1301**: `tk.stata(f"quietly generate strL {tmp} = ustrfix({v})")`, read, `capture drop` | A strL made in the user's data. (1318 `_dashfix<hex>` is a **global macro** name, not a variable) |

These dunder names are layout and model keys, not columns: `__missing__` (6475-6580), `__tabs__` and `__fw_<i>__` (22575-22681), `<name>__by__<i>`. They are already protected by `_dash_reserved_name` (1547), which refuses any registered name containing `__`.

**The renderer's copy of the prefix refusal.** `_DASH_QUAL_PREFIX = "__dashq"` (20277), `_DASH_QUAL_NAME_RE = r"__dashq[1-9][0-9]{0,4}\Z"` (20279), `_dash_qual_cols_named` (20282-20318), `_dash_take_qual_columns` (20321-). The last one raises ValueError for any column starting with `__dashq` that the spec doesn't name (20336-20342). The served app also checks for the prefix at 25002. A `__dash` rule has to change this function too, while still letting `__dashq<k>` through.

### 1.2 JS twin
- `_FILTER_JS` has `const ROW_ID = "__dash_row__";` at **14219**, written as a literal, not filled in from the Python constant. It is used at 14226, 14242, 14312, 14650, 14741 and 14955, and `dash_apply_kpis(..., ROW_ID)` at 14484/14499.
- The brush script prefix at **23499** fills it in: `'const ROW_ID = "%s";\n' % _ROW_ID_COLUMN`.
- The JS names no `mlabel` column; it copies every column by row identity.

### 1.3 Stata side
The refusal is in `_dash_qual_gen` (dash.ado:4251-4308), lines 4255-4261:
```stata
    capture unab _dq_clash : __dashq*
    if _rc == 0 {
        local _dq_first : word 1 of `_dq_clash'
        display as error "`cmdname': variable `_dq_first' is named with the prefix __dashq, which is reserved for the qualifier columns dash exports."
        display as error "      Rename it first, for example: rename `_dq_first' newname"
        exit 110
    }
```
- It is called from 5943 (the one-line route) and 6893 (`_dash_prepare_spec`: `dash build`, `build, server`, `serve`). Both calls sit in the branch that has data, so the refusal runs on every export with data. Dashboards made only of literal plots skip it.
- `_dash_qual_gen_by` is at 4326-4370 (sortpreserve, tempvar `_obs`). The by()-order columns have the same `__dashq<k>` names.
- The only variables dash adds to the user's data are `__dashq<k>` (byte) and `__dashfix<hex>` (strL). Everything else is a tempvar (`__000000` style), which does not begin `__dash`.
- The reservation is documented at dash.sthlp:166-171 and tested by `test_qualifier_in_stata.cscript` QS-06 (lines 491-519). The natural pytest home is `test/test_reserved_names.py`.

---

## 2. G2: string plot variables

**The varlist parsers (dash.ado).**

| Parser | Lines | `syntax` line | Declaration |
|---|---|---|---|
| `_dash_parse_varpart_std` | 1271-1290 | 1273 | `syntax varlist [if] [in] [aweight fweight pweight iweight]` |
| `_dash_parse_varpart_1v` | 1296-1320 | 1298 | `varlist(min=1 max=1)` |
| `_dash_parse_varpart_3v` | 1327-1350 | 1329 | `varlist` |
| `_dash_parse_varpart_4v` | 1356-1376 | 1358 | `varlist` |
| `_dash_parse_varpart_any` | 1382-1426 | — | `anything(name=vals equalok)`; literal types, no variables |

**Plot-type table.** `_expand_plottype_str` (dash_parse.mata:931-1022) holds the table at **946-985**: **40 rows**, not the 38 GAPS2 and ROADMAP cite (WP-22 added `pccapsym` and `pcarrowi`). The families are named in `_dash_plottype_families` (dash.ado:2922-2936), and the renderer has matching sets at dash_render.py:15371-15388.

**Dispatch in `_dash_process_segment` (dash.ado:3164-).**

| Branch | Types | Parser | Count check |
|---|---|---|---|
| 3304 `_pt_univar` | histogram, kdensity | 1v | — |
| 3310 `_pt_range` | rarea, rbar, rspike, rcap, rline, rconnected, rcapsym, rscatter, tsrline | 3v | 3 variables; `tsrline` 2 + tsset (3322-3358) |
| 3361 `_pt_pc` | pcspike, pcarrow, pcbarrow, pcscatter, pccapsym | 4v | 4 variables (3365-3376) |
| 3383 `_pt_literal` | scatteri, pci, pcarrowi, function | any | — |
| 3503 else | scatter, line, connected, area, bar, spike, dot, dropline, tsline, and the 11 of `_pt_onefit` (lfit, qfit, lfitci, qfitci, fpfit, fpfitci, mspline, mband, lowess, lpoly, lpolyci) | std | `tsline` takes x from tsset (3513-3532); a fit takes exactly 1 y + 1 x (3533-3548); otherwise the last variable is x (3549-3571); 1 variable → r(102) (3572-3585) |

That makes 2 + 9 + 5 + 4 + 20 = 40 types, **36 of which take variables**.

**Where r(109) would come from.** Add `numeric` to the four `syntax` lines, e.g. `varlist(min=1 max=1 numeric)`, and Stata's `syntax` emits the error and code itself, before any of dash's count checks. That is the same order as twoway (twoway_yxview_parse.class:120 uses `varlist(numeric ts)`; G4 wants `ts` on the same lines). dash's existing r(109) sites: the KPI numeric check at dash.ado:6147-6153 and `confirm string variable` at 2793 in `_dash_byte_cap`.

**Options that must keep accepting strings.** In `_dash_option_rules` (1853-1936): plot rules `colorvar=var mlabel=var` (1869) and graph rules `hover=varlist by=byvarlist` (1911). The kinds are handled in `_dash_validate_value` at 2149-2233 with `unab`, which checks no type.

**Renderer.** There is no string check on plot columns. String variables are known after the data loads (`string_vars`; `_dash_load_columns` 635). `_dash_cap_spec` (1705; called at 21028 and 24249) runs before the data exists. A spec-level refusal belongs after `_load_data`, next to `_dash_refuse_oversized` (21100 saved, 24979 served).

---

## 3. G3: the data limit

**`_dash_cell_cap`** (dash.ado:2724-2754) refuses when `nobs * nvars > lim` (message at 2750-2752, r(134)). It is called from:
- **5920** (the one-line route): `_dash_cell_cap \`=\`_dash_nvars' + \`_dq_n''`, where `_dash_nvars` is the count of `needed_vars`;
- **6875** (`_dash_prepare_spec`): the same, using `all_vars`.

The limits table is `_dash_limit_table` (2513), which must stay equal to the renderer's `_DASH_LIMITS` (1056); `test_resource_limits.py` checks that. `_dash_byte_cap` is at 2777.

**What is exported.** `needed_vars`/`all_vars` come from `_dash_extract_vars` (dash_parse.mata:2114). It reads the keys `yvar xvar var yvar1 yvar2 y1var x1var y2var x2var mlabel colorvar wexp`. `_dash_extract_qual_vars` (2255) adds `by` and `if_expr` names. For a histogram of x, that means column x for all _N rows plus any `__dashq` columns.
- **Hover, unverified:** no export key reads `hover`, and graph_options holds `"hover":"price"` (dash.ado:4940-4956). BUGS.md:761 mentions "a hover-only variable that is never serialised" as a separate open entry.

**The renderer refuses again** at `_dash_refuse_oversized` (1121), called at **21100** with `self.df.shape` and at 24979 in the served builder. G3's change has to be made here too.

**Size note.** `_report_dataset_size` / `_report_dataset_shape` (973/994) compute `rows * cols * _HTML_BYTES_PER_CELL (24)` over the whole frame. They warn above `_LARGE_DATASET_CELLS = 1_000_000` (962). Called at 24087 (saved) and 24981 (served).

**Is there a per-graph "needs rows" notion?**
- **In dash.ado, no.** It pools variables across graphs, KPIs and filter variables (6682-6820). The inputs to build one exist:
  - `link` is checked by `_dash_link_refusal` (dash_parse.mata:3477);
  - filter groups and their `exclude()` graph names are in `_dash_filter_refusal` (3416) and `_dash_filter_items` (3396). Only the variables come back to Stata (`_fvars`);
  - the `csv` flag is set at dash.ado:7041. The CSV holds **every column of `self.df`** (dash_render.py:23832-23861);
  - `hover` is in each graph's graph_options JSON.
- **In the renderer, partly:**
  - `_AGG_TYPES_RENDER = {"histogram","kdensity"}` (23161): their variables join the link source;
  - `agg_source_registry` (24129-24143): histogram and kdensity bins are recomputed on a filter move;
  - `derived_source_registry` (`_collect_derived_sources` 21419, whose sources carry `_ROW_ID_COLUMN`);
  - `_DASH_FIT_TYPES` 19503 and `_DASH_CI_TYPES` 19510.
- **The served app embeds every row whatever the graphs are** (`_embed_data` 25092-25102, base64 of the raw data JSON). So a relaxed count is only safe for the saved page. The cap at 6875 also covers `build, server` and `serve`.

---

## 4. G5: Unicode variable names

- `_dash_is_name` (dash_parse.mata:827-840) accepts ASCII only. Callers:
  - 891: layout names;
  - **3454: filter() variable**, refused with "not a valid Stata variable name";
  - 4030 and 4123: option words.

  So G5 needs a separate variable-name check, not a change to this function.
- The `by()` check at **2916**: `ustrregexm(w[j], "^[\p{L}_][\p{L}\p{N}_]*$") | ustrlen(w[j]) > 32`.
- The KPI pattern at dash.ado:**6094-6097**: `"^([a-zA-Z0-9.]+)\(([a-zA-Z_][a-zA-Z0-9_]*)\)$"`, message "syntax is stat(varname)", r(198).
- Other ASCII-only name checks on the Stata side: the time-series operator detector at dash.ado:2215 (reached only after `unab` has failed), and graph and KPI names at 5617/5639 and 6172/6184 (on purpose: these become global macro names).
- **The renderer is also ASCII-only, which GAPS2 does not mention.** `_DASH_VARNAME_RE = r"^[A-Za-z_][A-Za-z0-9_]*$"` (19207) is used by:
  - filter parsing (19340; exclude names at 19362);
  - **`_dash_parse_by` (15513)**: a Unicode `by()` is drawn without panels, with a warning, in both modes, even though the Stata side accepts it;
  - hover fields (19932, 20022): left out, with a warning.

  `_apply_colorvar` also has an inline ASCII regex at **6365** that returns silently, so no colours are drawn. `_dash_is_stata_name` (1183-1190: `isidentifier()` and length ≤ 32) is a Unicode-aware check that already exists. The KPI renderer path has no name regex.
- An existing Unicode test: `test_statistical_options.cscript:482-484` (`[aw=größe]`).

---

## 5. F1: `dash serve`

**Stata side**
- `_dash_serve_spec` is dash.ado:7252-7345. The default port is 5006 (7293) and timeout 0.
  - The digits check is at 7299-7303.
  - **The port range refusal is at 7307-7310:** "port() must be between 1024 and 65535", r(198).
  - Timeout must be at most 9 digits (7311-7315) and is in **minutes**.
- `_dash_serve` is 7349-7439:
  - browser decision: `_dash_dashboard_browser, \`_srv_nobr'` (7388; program at 5078);
  - the "starting Bokeh Server" line (7421);
  - `sys.argv` (7430), `--no-browser` appended (7431-7433);
  - **`python: _dash_serve_ns = runpy.run_path(..., run_name="__main__")` (7438)**. No return code is checked.
- Error pattern to copy: `_dash_write_data` (4169-4217) returns an error string through `Macro.setLocal`, then `_dash_say("err", …)` and `exit 198`. An exception escaping `python:` gives r(7102) plus a traceback.

**Launcher (dash_render.py)**
- Argparse: 27612-27657.
- **`main()` also clamps** at 27603: `builder.build(output_path, port=max(1024, min(int(port), 65535)))`. `ServerAppBuilder.build` lets `build_options["port"]` take precedence (24950-24955).
- Launch block 27670-27715:
  - `_port = max(1024, min(args.port, 65535))` at **27680** (unreachable from `dash serve`);
  - the command is `[_sys.executable, args.output, "--port", ...]`, plus `--show` unless `--no-browser` and `--timeout` when > 0;
  - `_proc = _sp.Popen(_cmd)` at **27701**, with no pipes; the child's stderr goes to Stata's process stderr;
  - `FileNotFoundError` → `raise SystemExit(1)` (27709);
  - `_proc.wait()` (27712), and on `KeyboardInterrupt` `terminate()` then `wait()` (27713-27715). **`returncode` is never read.**

**Generated app**
- `_HealthHandler` at 25563-25582: a separate rate limiter (`_HEALTH_LIMIT_RPM = 600` per IP per minute, 25330); returns `{"status":"ok","timestamp":…}`.
- `_dash_arg_parser` at 25610-: `--port type=int default=_port` (25614).
- `__main__` at 27358-27424:
  - **the clamp `_port = max(1024, min(int(_a.port), 65535))` at 27371**;
  - `_dash_server_app` (27296-27355) with `extra_patterns=[('/health', _HealthHandler)]`;
  - `server.start()`; `--show` → `add_callback(_server.show, '/')`;
  - timeout → `call_later(timeout*60, io_loop.stop)`;
  - it prints the URL and the /health URL to **its own stdout**, which never reaches the Results window (see F5);
  - `KeyboardInterrupt` → `pass`, and `finally` stops the server. A normal stop exits 0.

**Tests**
- `test_e2e_serve.cscript` (391 lines, P4-73..83) starts no server: port(99999), port(0) and port(abc) give 198, then it checks the generated app's source.
- `test_serve_launch.cscript` (SRV-01..20) never starts a server; its header says why (timeout is in minutes). SRV-17..20 use a **stub `dash_render.py`** put first on the ado-path (lines 235-265). That pattern suits an F1 cscript.
- Real launches, marked `serve`: `test_help_claims_1.py:576` `TestServeBlocksUntilCtrlC` and `test_help_claims_5.py:1348` `TestServingBlocksUntilInterrupted`. Both poll `/health` and send SIGINT.
- `test_help_claims_2.py:756` has `_FakeProc(cmd)` with `wait()` only (no keyword arguments, no `returncode`) and `TestTheLauncherBehindDashServe` (767). It breaks if Popen gains `stderr=PIPE`.
- **Tests that currently require the clamp:**
  - `test_render_cli_port.py:151` `test_an_out_of_range_port_is_clamped_not_embedded_raw` and 161 `..._in_build_options_is_clamped_too`;
  - `test_resource_limits.py:1279` `test_the_port_is_clamped_in_every_place_it_is_read` (parametrised (99999→65535), (80→1024), driving all three sites);
  - `test_adversarial_matrix.py:860` and 878 name the first of these in the adversarial registry.
- `test_server.py:4000` `TestServerHealthAndRateLimit` only checks the source text. `test_adversarial_matrix.py:2870` checks the launcher uses no shell.

---

## 6. K2: the version floor

**Where the old minimums appear**
- dash_setup.ado: `_dash_pymin` called at 44; messages at **60** ("install Python 3.8+") and 73; comparison at 77; **`local min_bokeh "3.0"` at 146**, numpy "1.23" at 147, pandas "2.0" at 150; `_dash_pymin` at **285-296** returning `"3.8"` (295).
- dash_setup.sthlp:40-42 ("compared with the 3.8 minimum … below 3.8"), **70** ("Python 3.8 or later"), **80** (bokeh 3.0), 81-82.
- dash.pkg:17 `d Requires: Python 3.8+, bokeh>=3.0, numpy>=1.23, pandas>=2.0.`
- dash.ado:201-210 `_dash_require_python`, message at 206-207 ("Python 3.8+").
- dash.sthlp:3131-3134.
- CHANGELOG.md:330-334 (`### Requirements`).

**Generated app.** It opens with the docstring at dash_render.py:25198-25204, then `import argparse as _argparse` (25206) and `from typing import …` (25222). **There is no `from __future__ import annotations`.** (dash_render.py has one at line 61; the app does not.)

**`CustomJSTicker`:** imported at 16877 (`from bokeh.models.tickers import BasicTicker, CustomJSTicker`) and 17217 (inside `_dash_count_axes` 17210; `_dash_finish_count_ticks` 17334).

**Tests that assert the old minimums:**
- `test_setup_python_gate.cscript` (the help must state `r(pymin)`, 80-93; comparator cases with "3.8");
- `test_setup_honesty.cscript` (bokeh "3.0" at 207-245, 504-550);
- `test_program_coverage.cscript` PC-19..21 (668-741: "bokeh>=3.0", "(needs 3.0)");
- `test_help_claims_8.cscript:786` and `test_help_claims_8.py:1647`.

**Measured versions**

| Interpreter | How identified | Python | bokeh | pandas | numpy |
|---|---|---|---|---|---|
| Stata's: `/opt/anaconda3/bin/python3` | `~/.stata19/console/stata19.rc` (`python pyexec_64 /opt/anaconda3/bin/python3`, `pyver_64 3.13.9`); the console binary `/usr/local/bin/stata-mp` links to StataNow; matches the com.stata.stata19 plist and conftest | 3.13.9 | 3.8.0 | 2.3.3 | 2.3.5 |
| Development: `python3` = `/opt/homebrew/bin/python3` (the Makefile's `PYTHON ?= python3`) | measured | 3.14.5 | 3.9.0 | 3.0.1 | 2.4.3 |

"Both interpreters" (WP-25 at ROADMAP.md:3835-3960; the Makefile):
- `make test` runs pytest under Stata's Python with `DASH_STRICT=1 DASH_BASELINE=stata`;
- `make test-dev` runs it under the development interpreter with `DASH_BASELINE=dev`;
- `make cert` runs the certification suite, which uses Stata's Python.

conftest.py `_BASELINES` (190-212): `stata {python 3.13, bokeh 3.8, pandas 2.3, numpy 2.3, scipy 1.16}`, `dev {3.14, 3.9, 3.0, 2.4, 1.17}`.

**Floor to declare: Python 3.13, bokeh 3.8, pandas 2.3, numpy 2.3.**

---

## 7. Tracking formats

**BUGS.md.** 2605 lines, no headings, 428 closed and 4 open entries (2523, 2559, 2595, 2601). The open entry at 2523:
```
- [ ] Title: #N ticks on a %td to %th date axis follow a fitted model that agrees with twoway's on about 60% of ranges, and three natscale ranges miss by a tick
  - File Names and Line Numbers: dash_render.py: `_dash_tsnatscale_ticks', `_dash_natscale_ticks'
  - Description: Left by the S3 batch's tick work. ...
  - Suggested fix: Recover the calendar-step rule _tsnatscale applies ...
  - Resolution: Not fixed: it stays open because both routines are compiled ... Graded S3 (WP-27): tick positions are fidelity; every value is drawn where it belongs.
```

**How "open S1/S2" is decided.** `scripts/release_verdict.py` **does not read BUGS.md**; it judges the release-gate log only. `test/test_cert_verdict.py` only judges the certification runner's log. The guard is **`test/test_tracking_documents.py`**:
- the parser `_ENTRY = r"^- \[(?P<mark>[ x])\] Title: (?P<title>\S.*)$"` and `_FIELD` (98-101); the five fields must appear once each, in order (`_format_problems`);
- open entries (458-471): `_OPEN = r"\b(not fixed|still open|stays open|remains open)\b"` (case-insensitive), and the Resolution must also contain `\bbecause\b`;
- `TestNoOpenEntryBlocksARelease` (475-516):
```python
    _GRADE = re.compile(r"\bGraded (S[1-3]) \(WP-\d{2}\): \S")
    ... exactly one per open entry; any open "S1"/"S2" fails:
        assert not bad, ("open S1/S2 BUGS.md entries block the release:\n" ...
```
- a closed entry must name a test that exists (`TestEveryClosedEntryNamesATestThatExists`).

**ROADMAP.md.** WP-27 is at 4131; the traceability matrix is at **4243**, followed by `## Corrections…` (4330), `## Risks` (4356) and `## Working agreements` (4370). WP-27's layout:
```
## WP-27 · Release closeout — DONE
**Gaps closed:** M2, B4 (verification) · **Severity:** S3 · **Effort:** S · **Depends on:** all
> **User story.** As the maintainer, I want ...
### Business requirements      (- **BR-27.1** ...)
### Technical requirements     (- **TR-27.1** ...)
### Acceptance criteria — release gate   (- **AC-27.1** ...)
### Test plan
### Done, measured (24sep2026)
```
WP-25 also has `#### The plan in detail` with `**US-25.1**`. The matrix is `| Gap | Title | Sev | WP |` with rows like `| A1 | ... | S1 | WP-02 |`.

**Hazards for WP-28 in `test_tracking_documents.py`**
- `_parse_roadmap` (626-651) reads `**Gaps closed:**` items that match `^([A-N]\d{0,2})`. When WP-28 is DONE, `test_every_gap_a_done_package_lists_is_closed_by_it` (766) looks each id up in **GAPS.md**, a different audit.
- `_matrix_gaps` and `_matrix_rows` split on the text "## Traceability matrix". It would also match "### Traceability matrix", and extra or X-prefixed rows break the row count check.

**CHANGELOG.md sections:** `## 2.0, 24sep2026 (release candidate)`, `### Results that change` (10), `### Security` (142), `### New` (178), `### Fixed` (219), `### Changed behaviour (may need your do-files changed)` (280), `### Removed` (321), `### Requirements` (330), `### Fixed after WP-27 (the S3 batch, 24sep2026)` (338), `### Fixed in WP-27` (383). No test checks this structure.

**GAPS2.md is untracked.** `test_packaging.py:411` `_ROOT_ALSO` lists the files allowed at the package root, and GAPS2.md is not on it.

---

## 8. Test infrastructure

**`test/cert_helpers.do` (218 lines).** It sets `global dash_nobrowser 1`. Mata helpers:
- `_cert_read` reads a whole file in 1 MB chunks;
- `_cert_file_has` returns 1/0, or −1 if unreadable;
- `_cert_log_count` rebuilds wrapped log lines (`> `) and 32,768-character pieces, then counts matching lines;
- `_cert_file_count` counts non-overlapping occurrences.

Stata programs (each overwrites `r()`):
- `cert_file_has path, needle() [lower]` → `r(found)`;
- `cert_log_has` → `r(found)`, `r(count)`;
- `cert_file_count` → `r(count)`.

`_dash_say(style, before, value, after)` is **not** in cert_helpers. It lives in dash_parse.mata (~584) and prints user text as literal text (no SMCL).

**`test/run_all_cscripts.do`** (1738 lines, 65 registered scripts, 65 `.cscript` files):
- hard-coded `adopath ++` and `dashdir`, `/Users/billy/...` (K1);
- one block per script: `do` under `capture noisily`, then `[ PASS]`, `[ FAIL] (rc=N)` or `[ SKIP]` (rc 222);
- summary lines "Results: …", "ALL TESTS PASSED (n passed, m skipped)".

`test_cscript_hygiene.py:418` requires every cscript to be registered in the runner.

**`scripts/run_cert_suite.sh`:** `mktemp -d`; `cd $dir && STATATMP="$dir/tmp/" arch -arm64 $STATA -b do $REPO/test/run_all_cscripts.do`; then `scripts/cert_verdict.py` judges the log. It passes only if every registered script PASSed, none SKIPped, and the summary agrees.

**The release gate.** `scripts/run_release_gate.sh` copies the files `dash.pkg` ships, plus `stata.toc`, to `$dir/src`, then runs `scripts/release_gate.do src work examples` (175 lines). That script:
1. `net install`s into a scratch PLUS;
2. checks dash.ado, dash_setup.ado, dash_parse.mata, dash_render.py and the locator resolve inside it;
3. runs every `examples/*.do` with its own log;
4. builds one page per shipped scheme;
5. checks `adoupdate` against the same source and a one-day-newer copy;
6. restores PLUS.

Every result is a `GATE …` line. `scripts/release_verdict.py` judges them, allowing only diagnostics an example declares with `*! release-gate allows:`. `make release` runs `check` then `gate`.

**How Stata truth is recorded: `scripts/extract_axis_truth.do` (1453 lines).**
1. Probes are registered with `zp id group dataset body opts` (106-119).
2. Each probe runs `twoway … name(zqg)`, then `graph export <id>.svg` and `graph save <id>.gph` into `c(tmpdir)/dash_axis_probe`. A pipe-separated record is written to `axis_records.txt` (395-432), and an SVG self-check follows (434-441).
3. One trailing `python:` block (452-1450) parses the SVGs (`RE_TEXT`, `RE_LINE`, `RE_RECT`) and the `.gph` files. It writes `test/fixtures/axis_truth.json` with keys `_meta{…, counts}`, `data_facts`, `probes{id: …}`, `findings{legend_rule, legend_cases, axis_range_extension, titles_notes_captions, …}` and `unverified`.

Gotchas: never call Stata from that Python block, and write a backtick as `\x60`. `.git/info/exclude` hides `*.json`/`*.txt`, so a new fixture needs `git add -f`. `test_fixtures_are_committed.py` requires a test to name each fixture.

**Existing SVG export and parsing.** Each script uses its own private helpers; there is no shared one:
- `extract_axis_truth.do`;
- `test_help_claims_8.cscript` (`_hc_svg_same`, `_hc_svg_maxfont`, `_hc_svg_x_sorted`, `_hc_svg`, 97-456);
- `test_help_claims_2.cscript` (`_hc2_rawhas`, 1022-1027);
- `test_bug_regressions.cscript` (python `_br03_svg`, 494-520);
- `test_help_claims_6.cscript:1013`;
- `test_help_claims_5.cscript:217`;
- `test_twoway_option_parity.cscript` (743-1218);
- `scripts/extract_scheme_truth.py`.

**`python_exec` drop hazard** (memory note `project_stata_cert_suite`). The console binary rewrites `~/.stata19/console/stata19.rc` when each session exits. With about 16 sessions running at once, one wrote it back without its `python py*_64` lines. After that, every Python script SKIPped (rc 222) in 0-1 s. Keep concurrent Stata sessions to two or three. Check `display c(python_exec)` before trusting a run of skips. Restore with `set python_exec /opt/anaconda3/bin/python3, permanently`. (The rc file holds the right values now.)

**STATATMP convention.** Give each concurrent run `cd <dir> && STATATMP=<dir>/tmp/ arch -arm64 /usr/local/bin/stata-mp -b do …`:
- the trailing slash is required;
- STATATMP must not be the directory the batch log goes to (HC4-21 scans `c(tmpdir)`);
- a batch run given arguments names its log after the last argument (`ls -t *.log | head -1`).

**The pytest session lock** (conftest.py 51-138):
- `pytest_sessionstart` takes a non-blocking `fcntl.flock` on `/tmp/dash-full-suite-<uid>.lock` (or `$DASH_SUITE_LOCK`), but only for a whole-suite run (`_covers_whole_suite`: no args or `test/`, and no `-k`, `--lf` or `--collect-only`);
- a second full run raises `pytest.UsageError`, naming who holds the lock;
- xdist workers don't take it;
- in strict mode it first refuses environment drift (`_drift_problem`), and `pytest_sessionfinish` turns any skip red.

A machine-local hook, `.claude/hooks/guard-full-suite.sh`, allows a third full launch per session only with `FULL_SUITE_RERUN=1`.
