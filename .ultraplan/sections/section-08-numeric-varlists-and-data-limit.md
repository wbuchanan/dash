# Section 08: Numeric varlists and the data limit (G2, G3)

> Part of: WP-28 · Gaps: G2, G3 · Risk: yellow · Batch: 1 · Depends on: none · Blocks: 19 


## Review amendments (Phase 4, 2026-09-25) — binding; they override any conflicting text below

> Batch **1** · Depends on **none** · Blocks **19** · Risk **yellow** · Commits: two commits: G2 → CHANGELOG `Changed behaviour`; G3 → `Fixed in WP-28`

- D10: run the full pytest suite ONCE, at the end of the section (CLAUDE.md rule 11), not four times.
- State the unverified assumption about twoway's r(109) wording and that the generated cscript measures it at test time; keep `test_adversarial.cscript` P19-11's two-line refusal pin intact.
- D7: split 08-01.

Applies to every section:
- D1 (binding): tasks are work steps; commits are per gap (S01-S04: one each). The failing regression tests are written first and run against the unmodified tree; their output at 91d97be is recorded in the fix commit's message (Q24) and they are committed together with the fix, never alone (CLAUDE.md rule 4).
- D3 (binding): each gap's BUGS.md entry is appended at the END of BUGS.md in the closed form with `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.`
- D2 (binding): each closing task replaces the gap's `<!-- WP-28 <ID> -->` marker(s) that S01 placed in the CHANGELOG list named above; it does not add a new line elsewhere.
- D6 (binding): every Stata run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (see `index.md` step 0); no section launches the full cert suite or the release gate.
- D5 (binding): shared files follow merge rules R1-R6 in `index.md` (cscript registration and hygiene pins, copy lists and maps, help/CHANGELOG/BUGS.md, graph-key lists, fixtures, parity corpus).
- D7: XML fields holding `&`, `<` or `>` are CDATA-wrapped (done mechanically); task names over 8 words are shortened and `done` fields put in the past tense during the detailed fixer pass.

Detailed edits from `../review/consistency.md`, `../review/requirements-security.md` and `../review/feasibility.md` (as adjusted by `../review/DECISIONS.md`) are applied to this file in the fixer pass; until then this block governs.

## Overview

Two gaps about what dash lets through its export. **G2** (S2): twoway refuses a string y or x with r(109) — its y/x parser declares `varlist(numeric ts)` (`$BASE/t/twoway_yxview_parse.class:120`), and histogram and kdensity declare `varname(numeric)` — but dash.ado's four varpart parsers (1273, 1298, 1329, 1358) declare `syntax varlist` without `numeric`, and `_dash_process_segment` has no type check. GAPS2 measured: "a string x produced meaningless Scatter/Line/VBar glyphs with no note, and lfit and histogram crashed with 'could not convert string to float'". After this section every plot variable of every one of the 36 variable-taking plot types is refused by Stata's own `syntax` with twoway's code and twoway's words, measured against twoway at test time; `colorvar()`, `mlabel()`, `hover()` and `by()` keep taking strings; and a hand-written spec that names a string plot column is refused by both renderers with a named error.

**G3** (S2): the limits exist so nothing "can grow without bound" (dash.sthlp:1504-1578), but `_dash_cell_cap` (dash.ado:2735-2754) counts `_N` times every variable exported plus every qualifier column, whatever the page will hold. GAPS2 measured: "`dash histogram x` on 5,000,001 obs is r(134) by default, and nothing can be drawn past 20M obs. Probe at 1e6 x 3: the page was 1.4 MB, but the note said 'roughly 72 MB'." The saved page embeds a histogram's bars, not its rows. After this section the count is what the saved page embeds: a graph made only of computed layers (histogram, kdensity, the fits and smoothers) that no filter, `link()`, `csv` or `hover()` reaches counts its drawn output; every other graph, every KPI card and every filter variable counts its variables times `_N`; the renderer's own refusal follows the same accounting; the size note reports embedded bytes; and the served app — which embeds every row (`_embed_data`, 25092) — keeps the full count and says so. The JSON export itself is unchanged (DISCOVERY Q9).

The two share a section because both are decided in the same place — dash.ado's parsers and the two `_dash_cell_cap`/`_dash_refuse_oversized` sites — on the same object, the exported variables, and each has a renderer-side twin beside `_dash_refuse_oversized` (21100 saved, 24979 served).

**Test order (CLAUDE.md rule 7): tasks 08-01 to 08-03 write every regression test**, run them against the unmodified tree and record the failures; 08-04 to 08-06 close G2 (one commit); 08-07 to 08-10 close G3 (one commit).

## Risk: [yellow] — twoway's r(109) wording is measured, not documented, and a counting rule now lives in two languages

- **Why.** The string-variable message that `syntax varlist(numeric)` prints "is not in any local help or PDF" (research D §12); the cscript must read it from twoway's own run and compare dash's, type by type, and a type whose front-end uses another declaration (`varname(numeric)`; tsline's own parser) may print other words. The relaxed count is a rule with cases (computed-only, touched, `width()`/`discrete`, `lowess`, `by()`) that must give the same number in Mata and in Python or the two refusals disagree.
- **Risk factors.** (a) A per-type message dash cannot reproduce through `syntax` alone. (b) The accounting drifting between dash_parse.mata and dash_render.py. (c) `test_adversarial.cscript` P19-11 asserts `_dash_cell_cap`'s refusal is exactly two lines with exact text; any change to the extra-free message breaks it. (d) The one-line route (`_dash_render_immediate`, 5920) and `_dash_prepare_spec` (6875) must apply the same rule; `build, server` and `serve` must not.
- **Mitigation.** The G2 cscript is generated from the plot-type table, compares rc and message lines byte for byte, and records every measured message in its header; a pytest and the G3 cscript pin the two counts on the same specs; the served and saved refusals differ only by one appended sentence; P19-11's two lines are byte-identical when nothing computed is counted.

## Dependencies

- Depends on: none. Edits are confined to the four `syntax` lines, `_dash_cell_cap` and its two callers, the variable-pooling loop of `_dash_prepare_spec`, new Mata functions, and the renderer's refusal sites after `_load_data`; no batch-1 section touches those regions.
- Blocks: section 19.
- Parallel batch: 1. Can run with every other batch-1 section. **Shared edits to reconcile at the merge:** `test/run_all_cscripts.do` (two new blocks), `test/test_cscript_hygiene.py` (counts at 292 and 308), `test/program_coverage_map.py`, `test/function_test_map.py`, `BUGS.md`, `CHANGELOG.md`, `dash.sthlp`.
- Section 07 renames internal columns; nothing here names one. Section 14 adds a hover text column on graph sources — it is a row-embedding column and G3's rule already counts a `hover()` graph as touched.

## Evidence

### G2 — the four parsers and the dispatch (research C §2)

| Parser | Lines | `syntax` line today | Types (dispatch `_dash_process_segment` 3304-3503) | Variables |
|---|---|---|---|---|
| `_dash_parse_varpart_1v` | 1296-1320 | 1298 `syntax varlist(min=1 max=1) [if] [in] [aweight fweight pweight iweight]` | histogram, kdensity (`_pt_univar`) | 1 |
| `_dash_parse_varpart_3v` | 1327-1350 | 1329 `syntax varlist [if] [in] [...]` | rarea rbar rspike rcap rline rconnected rcapsym rscatter (3), tsrline (2 + tsset) | 3 / 2 |
| `_dash_parse_varpart_4v` | 1356-1376 | 1358 `syntax varlist [if] [in] [...]` | pcspike pcarrow pcbarrow pcscatter pccapsym | 4 |
| `_dash_parse_varpart_std` | 1271-1290 | 1273 `syntax varlist [if] [in] [...]` | scatter line connected area bar spike dot dropline; tsline (1 + tsset); the 11 of `_pt_onefit` (lfit qfit lfitci qfitci fpfit fpfitci mspline mband lowess lpoly lpolyci) | 2 (tsline 1) |
| `_dash_parse_varpart_any` | 1382-1426 | `anything(name=vals equalok)` | scatteri pci pcarrowi function | none |

The table is `_expand_plottype_str` (dash_parse.mata:946-985), **40 rows** (WP-22 added `pccapsym` and `pcarrowi`; GAPS2 and DISCOVERY Q16 say 38); families in `_dash_plottype_families` (dash.ado:2922-2936):

```stata
2924    c_local _pt_univar  "histogram kdensity"
2925    c_local _pt_range   "rarea rbar rspike rcap rline rconnected rcapsym rscatter tsrline"
2926    c_local _pt_pc      "pcspike pcarrow pcbarrow pcscatter pccapsym"
2927    c_local _pt_literal "scatteri pci pcarrowi function"
2928    c_local _pt_imm     "scatteri pci pcarrowi"
2929    c_local _pt_ts      "tsline tsrline"
2933    c_local _pt_onefit  "lfit qfit lfitci qfitci fpfit fpfitci mspline mband lowess lpoly lpolyci"
```

2 + 9 + 5 + 4 + 20 = 40 types; 36 take variables. Each parser's `syntax` line runs before dash's own count checks (3322-3376, 3533-3585), so adding `numeric` gives Stata's r(109) first, the order twoway uses. `colorvar`, `mlabel`, `hover` and `by` are kinds validated in `_dash_validate_value` with `unab` (2149-2233), which checks no type — they keep taking strings. dash's existing r(109) sites: the KPI numeric check (6147-6153) and `confirm string variable` in `_dash_byte_cap` (2793).

**Stata rule** (research D §12). r(109) is "type mismatch" in [P] error; the specific text `syntax varlist(numeric)` prints for a string variable is emitted by the built-in `syntax` and is in no local document: **measure it**. twoway: `varlist(min=2 numeric ts default=none)` / `[varlist(numeric ts default=none)]` (twoway_yxview_parse.class:119-124); `histogram.ado:5`, `twoway__histogram_gen.ado:6`, `kdensity.ado:10,34` use `varname(numeric)`; `colorvar` uses `confirm numeric variable` (twoway_yxview_parse.class:220).

**Renderer.** No string check on plot columns. `string_vars` is known after the data load (`_load_data`, 21162: `self.string_vars = {k for k, v in type_is_string.items() if v}`); `_dash_cap_spec` (1705; called at 21028 saved, 24249 served) runs before the data exist. The refusal belongs after `_load_data`, beside:

```python
21096        self._load_data()
21097        # Refused before anything is drawn from it: dash.ado refuses the
21098        # same data before exporting it, so this is for a spec that reached
21099        # the renderer another way.
21100        _dash_refuse_oversized(self.df.shape[0], self.df.shape[1],
21101                               self.limits, "dashboard")
```

and in the served builder (24978-24981), where the string flags are `_isstr` (24995) and the frame is `self._frame()` (25020-25036, a `DashRenderer._load_data` over the parsed JSON). The plot variable keys are `DashRenderer._VAR_KEYS = ("yvar", "xvar", "var", "yvar1", "yvar2", "y1var", "x1var", "y2var", "x2var")`; the option keys that may be strings are `_DASH_OPT_VAR_KEYS = ("colorvar", "mlabel", "wexp")` (18706; a string weight is already noted at 7883-7889 and the layer drawn unweighted).

### G3 — the cap, its callers, and what the page holds (research C §3)

`_dash_cell_cap`, dash.ado:2735-2754:

```stata
2735 program define _dash_cell_cap
2736     version 16.0
2737     args nvars nobs
2738     if "`nobs'" == "" local nobs = _N
2739     _dash_limit, name(cells)
2740     local lim  = r(value)
2741     local ceil = r(ceiling)
2742     if `nobs' * `nvars' <= `lim' exit
...
2750     display as error "dash: this dashboard would embed `_cells_s' values (`_obs_s' `_obs_w' x `_vars_s' `_vars_w'), more than the `_lim_s' dash embeds."
2751     display as error "      Reduce the data in memory first (keep, drop, sample or collapse, inside preserve/restore), or set global dash_max_cells to a higher value (at most `_ceil_s')."
2752     exit 134
```

Callers: 5920 (`_dash_render_immediate`, the one-line route: `_dash_cell_cap \`=\`_dash_nvars' + \`_dq_n''` over `needed_vars`) and 6875 (`_dash_prepare_spec`: the same over `all_vars`; this program serves `dash build`, `dash build, server` (the `SERVER` option, 6477; `"\`server'" != ""` at 7118/7203) and `dash serve` (called at 7332 with `cmdname("dash serve") inherit …`)). `_dash_limit_table` (2513-2524) is the table `test_resource_limits.py::TestTheTwoLanguagesAgree::test_dash_ado_has_the_same_defaults_and_ceilings` holds equal to `_DASH_LIMITS` (1056-1065); `cells=5000000,20000000`. `test_adversarial.cscript` P19-22 (1184-1188) calls `_dash_cell_cap 1` directly; P19-11 (972-1007) and P19-13 (1018-1044) assert the exact two lines above for a 74 x 2 scatter at `dash_max_cells 100`, and P19-11 asserts the log holds "these two lines and nothing else".

The pooling, `_dash_prepare_spec` 6682-6820: one list `all_vars` over every graph (`_dash_extract_vars` — keys `yvar xvar var yvar1 yvar2 y1var x1var y2var x2var mlabel colorvar wexp`, dash_parse.mata:2114 — plus `_dash_extract_qual_vars`, 2255: `by` and `if_expr` names, read from the rewritten graph `_qg_k` whose qualifiers are now `"qual_col":"__dashq<k>"`), every KPI (`kpi_var`, and its qualifier column `_kqc_k`) and every filter variable (`_fvars`, 6790-6810). No per-graph record of whether the page will hold its rows. The inputs for one exist: `link` (`_dash_link_refusal`, dash_parse.mata:3477; `_all` or graph names), the filter groups and their `exclude()` names (`_dash_filter_refusal` 3416 parses them at ~3430-3447; `_dash_filter_items` 3396 returns a group's variable and sub-options), the `csv` flag (7041: `local _csv_flag = cond("\`csv'" != "", "1", "0")`; the CSV holds every column of `self.df`, 23832-23861), and `hover` in each graph's `graph_options` (`_dash_json_get_str(json, "hover", macro)`, 3548, reads it). A graph's plot types are in its JSON as `"type":"<name><![CDATA["`, and `_dash_spec_types_in(s, allowed)` (5083-5103) is 1 when every plot of `s` is in `allowed`.

What the saved page embeds: a row-drawing layer's source (every variable of the graph, `_make_source` 21383); a computed layer's own source (`map_histogram` 9519, `map_kdensity` 9770, the fits) — the graph source is embedded only when something references it: a filter (`all_graph_sources`, and `agg_source_registry` 24129-24143 recomputes histogram/kdensity bins on a move, so `_AGG_TYPES_RENDER = {"histogram","kdensity"}` variables join the link source, 23161), a `link()` group (one shared source), the CSV (every column), or `hover()`. The served app embeds every row whatever the graphs (`_embed_data` 25092-25102, base64 of the raw JSON).

The renderer's type sets: `_DASH_FIT_TYPES` (19503: lfit qfit fpfit lpoly lowess mband mspline function), `_DASH_CI_TYPES` (19510: lfitci qfitci lpolyci fpfitci), `_AGG_TYPES_RENDER` (23161, a local inside `render()`). `_pt_univar ∪ _pt_onefit` = `_AGG_TYPES_RENDER ∪ _DASH_FIT_TYPES ∪ _DASH_CI_TYPES − {function}` = 13 types.

What each computed layer can draw, from dash.ado's option caps (1866: `n=int,1,300@mspline  n=int,2,10000  bin=int,1,1000 … bands=int,1,200`) and the renderer's constants (`_FIT_GRID = 100` at 208, `_FP_GRID_MAX = 20000` at 134, kdensity's default 300 points at 9845):

| layer | cells drawn, at most | note |
|---|---|---|
| histogram | 4 x bins | bins: `bin(#)`, else `max(1, int(min(sqrt(N), 10*log10(N))))` (Stata's default, research D §6); with `width()` or `discrete` and no `bin()` the count is the data's, so **N** |
| lowess | 2 x N | one smoothed value per observation: never escapes the cap |
| kdensity, lpoly, lpolyci | 2 or 4 x n, n <= 10000 | 40,000 |
| lfit, qfit, lfitci, qfitci | 2 or 4 x n, n <= 10000 | 40,000 |
| fpfit, fpfitci | 2 or 4 x `_FP_GRID_MAX` | 80,000 |
| mspline | 2 x ((bands-1) x n + bands), bands <= 200, n <= 300 | 119,800 |
| mband | 2 x bands | 400 |

So one constant, **`_DASH_COMPUTED_PLOT_CELLS = 120_000`**, bounds every computed layer except a histogram and a lowess, which are counted exactly.

The size note, `_report_dataset_size` (973-991) → `_report_dataset_shape` (994-1015): `cells = rows * cols` over the whole frame, warns above `_LARGE_DATASET_CELLS = 1_000_000` (962) with `mb = cells * _HTML_BYTES_PER_CELL (24) / 1e6`, "dash: {rows:,} observations on {cols} variables is a large dataset to embed; this {mode} will be roughly {mb:,.0f} MB …". Called at 24087 (saved, with `self.df`) and 24981 (served, with the JSON's shape). `_dash_refuse_oversized` (1121-1136) raises `DashLimitError` when `rows * cols > limits["cells"]` with "dash: this {mode} would embed {cells:,} values ({rows:,} observations x {cols} variables), more than the {limit:,} dash embeds. Reduce … or set global dash_max_cells …". A spec lowers the limit through `build_options["limits"] = {"cells": <int>}` (`_dash_limits`, 1069-1108).

**Help.** dash.sthlp:1519-1522 (`$dash_max_cells`: "values embedded, observations times the variables a dashboard uses; default 5,000,000, at most 20,000,000") and the paragraph 1560-1572 "Why the data limit counts every observation".

### Fixtures on disk

None are read. `test/fixtures/stat_truth.json` (from `scripts/extract_stat_truth.do`, whose layer 1 calls `twoway__histogram_gen \`hv', generate(h x) return \`opt'` at 305) shows the call form the G3 cscript uses for its bins; the cscript computes the truth in its own run rather than reading the fixture.

### Existing tests that pin today's behaviour

- `test/test_resource_limits.py::TestAnOversizedDatasetIsRefused::test_at_the_limit_nothing_is_raised` and `::test_over_the_limit_the_message_says_what_and_how` (604-625) call `_dash_refuse_oversized(rows, cols, limits, mode)` and pin the exact wording — **kept green**: the signature gains a keyword `extra=0` and the message is unchanged when `extra == 0`.
- `test/test_resource_limits.py::TestTheTwoLanguagesAgree::test_dash_ado_has_the_same_defaults_and_ceilings` (1447) — **kept green**: `_dash_limit_table` is not changed; the new constant lives in its own function.
- `test/test_dataset_size_warning.py::TestALargeDatasetIsReported::*` and `::TestTheServedAppReportsItToo::test_the_builder_warns_on_the_same_data` — scatter frames; **kept green**.
- `test/test_adversarial.cscript` P19-11, P19-12, P19-13, P19-22, P19-23 — scatters; the two lines are byte-identical when `extra == 0`; **kept green**. P19-11's "nothing else" rule means the served sentence is appended only on the server route, which no P19 case takes.
- `test/test_function_test_map.py` and `test/test_program_coverage_map.py` fail until every new function is mapped (08-05, 08-07, 08-09).
- `test/test_cscript_hygiene.py::…::test_the_glob_finds_every_script` (`== 65`) and `::test_every_script_that_skips_for_python_is_read` (`== 47`) — flip to +2 and +1 (the G3 script needs Python; the G2 script does not).
- No pytest or cscript feeds a string plot column today (`grep -n '"yvar": *"make"' test/*.py` finds only KPI `count(make)` cases in `test_help_claims_4.py:1026`, which are KPIs, not plots, and stay).

## User stories

- **US-08.1** As the Stata user pasting twoway syntax, I want `dash scatter make mpg` to stop with the code and the words `twoway scatter make mpg` stops with, so that a do-file behaves the same under either command.
- **US-08.2** As the Stata user, I want `colorvar(make)`, `mlabel(make)`, `hover(make)` and `by(make)` to keep working, because dash documents them for string variables.
- **US-08.3** As the Stata user with six million observations, I want `dash histogram x` to build a saved page — the page holds the bars, not the rows — while `dash scatter y x` is still refused before anything is exported.
- **US-08.4** As the dash serve operator, I want `dash build, server` and `dash serve` to keep refusing what the app cannot embed and to tell me why the served count differs.
- **US-08.5** As the dashboard viewer of a hand-written spec, I want a string plot column to be refused with a message naming it, never a traceback.
- **US-08.6** As the maintainer, I want the size note to report the bytes the page will actually hold.

## Business requirements

- **BR-08.1** For every plot type that takes variables and every variable position of it, a string variable is refused with the return code and the message twoway gives for the same command; nothing is registered or exported.
- **BR-08.2** `colorvar()`, `mlabel()`, `hover()` and `by()` accept string variables as before.
- **BR-08.3** A spec that names a string variable as a plot variable is refused by the saved renderer and the served builder with an error naming the variable, the layer type and twoway's r(109), before anything is drawn or embedded.
- **BR-08.4** The cells limit counts what the saved page embeds: for a graph that draws rows, or that a filter, `link()`, `csv` or `hover()` reaches, its variables and qualifier columns times the observations; for a graph made only of computed layers that nothing reaches, the values its layers draw; KPI cards and filter variables count their variables times the observations. Over the limit the build is refused with r(134) before any export, naming the count.
- **BR-08.5** The served app counts every variable times the observations, as before, and its refusal says a served app embeds every observation of every variable.
- **BR-08.6** The renderer's own refusal for a spec that did not come through dash.ado gives the same count as dash.ado for the same spec and data.
- **BR-08.7** The size note reports the bytes the page will embed under the same count.
- **BR-08.8** The export (the JSON data file), the bytes limit and every other limit are unchanged; `_dash_limit_table` and `_DASH_LIMITS` stay equal.
- **BR-08.9** dash.sthlp states the count in the words of BR-08.4/BR-08.5 and that a string plot variable is refused as twoway refuses it.

## Technical requirements

- **TR-08.1** dash.ado: `numeric` on the four `syntax` lines — 1273 `syntax varlist(numeric) [if] [in] [aweight fweight pweight iweight]`, 1329 and 1358 the same, 1298 `syntax varname(numeric) [if] [in] [...]` (twoway's histogram and kdensity declaration; `varname` sets `\`varlist'` too, so the sreturns at 1317-1319 stand). If the G2 cscript measures that a family's words still differ from twoway's, change that parser's declaration to the form twoway uses for that family and record the measured text in the cscript header; do not write the message by hand.
- **TR-08.2** dash_render.py: `_dash_refuse_string_plot_vars(spec, string_vars, mode)` beside `_dash_refuse_oversized` (1121): for each graph, each plot, each key of `DashRenderer._VAR_KEYS` whose value is in `string_vars`, raise `DashSpecError(ValueError)` — a new class beside `DashLimitError` (1068) — with "dash: this {mode} names the string variable {var!r} as a plot variable of a {type} layer; twoway takes numeric variables there (r(109)). colorvar(), mlabel(), hover() and by() take a string variable." Called at 21102 after `_dash_refuse_oversized` in `DashRenderer.__init__`, and in `ServerAppBuilder.build` after 24981 with `{k for k, v in _isstr.items() if v}`. Both in `test/function_test_map.py`. The builder runs inside dash_render.py, so no copy-list entry; the generated app is not given the check.
- **TR-08.3** `scripts/gen_string_varlists_cscript.py` (new; runs under the development Python and Stata's, no third-party imports): reads the 40 `("full","min")` rows of `_expand_plottype_str` from dash_parse.mata and the `c_local _pt_*` lists from dash.ado, derives each type's arity (univar 1; range 3, tsrline 2; pc 4; literal skipped; tsline 1; else 2), and writes `test/test_string_varlists.cscript` deterministically: a header stating it is generated and by what, the `cscript` line, `sysuse auto`, `generate t = _n`, `tsset t`, a `_sv_case` program, then one case `SV-<type>-<k>` per (type, position) with `make` at position k and `mpg weight price length` filling the others, and the closing `display` per case. 89 cases (20 x 2 + 2 x 1 + 8 x 3 + 1 x 2 + 5 x 4 + 1 x 1). No Python is needed in the script (the refusal is in `syntax`), so it does not skip for Python.
- **TR-08.4** `_sv_case` (in the generated script): runs `capture noisily twoway <type> <vars>` and `capture noisily dash <type> <vars>, name(sv)` each under `log using <tmpdir>/dash_sv.log, text replace` with `set linesize 255` (the `_adv_p19_run` pattern, test_adversarial.cscript), reads each log through `_cert_read` (cert_helpers.do), drops the command echo lines (starting `. `) and the `r(#);` line, and asserts twoway's rc == dash's rc (109) and the remaining lines are equal byte for byte; also asserts no `dash_json_*` global was written (`: all globals "dash_json_*"` empty). A twoway rc other than 109 for a case is a generator bug (wrong arity): fail loudly naming the type.
- **TR-08.5** `test/test_string_varlists_cscript.py`: `test_the_generated_cscript_is_current` (regenerate to a string, compare with the file), `test_it_covers_every_type_that_takes_variables` (36 types, 89 cases, the four literal types absent), `test_the_arity_table_matches_dash_ado` (the families read from `_dash_plottype_families`).
- **TR-08.6** dash_parse.mata, new functions (each mapped in `test/program_coverage_map.py` to `test_data_limit.cscript` cases):
  - `real scalar _dash_computed_cells(string scalar gjson, real scalar nobs, real scalar bygroups, string scalar types)`: returns −1 unless `_dash_spec_types_in(gjson, types)`; else with `P` = count of `"type":"`, `L` = count of `"type":"lowess"`, `H` = count of `"type":"histogram"`, `wd` = the graph holds `"width":"<non-quote>` or `"discrete":"<non-quote>` and no `"bin":"<digits>"`, `B` = the first `"bin":"<digits>"` value if present else `max(1, floor(min(sqrt(nobs), 10*log10(nobs))))` (`nobs >= 1`; 1 when `nobs == 0`): `cells = L*2*nobs + H*4*(wd ? nobs : B) + (P-L-H)*_dash_computed_plot_cells()`, multiplied by `bygroups` when the graph holds `"by":"<non-quote>`.
  - `real scalar _dash_computed_plot_cells()`: `return(120000)` with the derivation table above as its comment.
  - `real scalar _dash_graph_touched(string scalar gname, string scalar gjson, string scalar filter, string scalar link, string scalar csv)`: 1 when `csv != ""`, or `link == "_all"`, or `anyof(_dash_blank_words(link), gname)`, or the graph's `hover` (via `_dash_json_get_str`) is non-empty, or any filter group's `exclude()` does not name `gname` (a group with no `exclude()` touches every graph); the group and exclude parsing reuses `_dash_filter_split`/`_dash_filter_items` and the exclude reading of `_dash_filter_refusal` (factor it into `string rowvector _dash_filter_excludes(string scalar group)`); 0 otherwise.
  - `string scalar _dash_qual_cols_in(string scalar gjson)`: the distinct `"qual_col":"…"` and `"qual_col_total":"…"` values, blank-separated.
- **TR-08.7** dash.ado `_dash_cell_cap <nvars> [<nobs>] [<extra>] [<served>]`: `args nvars nobs extra served`; empty `extra` is 0; refuse when `nobs*nvars + extra > lim`. Messages: `extra == 0` → the two lines of today, byte for byte; `nvars == 0` → "dash: this dashboard would embed `_cells_s' values (the drawn output of its computed layers), more than the `_lim_s' dash embeds."; both → "(… observations x … variables, and `_extra_s' values of computed layers)"; `served == "1"` → a third line "      A served app embeds every observation of every variable it uses." Second line unchanged. `exit 134`.
- **TR-08.8** `_dash_prepare_spec` (6682-6820): keep `all_vars` as the export list; accumulate beside it `row_vars` (distinct) and `comp_cells`. For each graph k, after `_qg_k` is made: `_dash_plottype_families` once before the loop for `\`_pt_univar' \`_pt_onefit'`; `_dash_limit, name(by_groups)` once for its `r(value)`; `gc = _dash_computed_cells(_qg_k, _N, by_groups, types)`, `gt = _dash_graph_touched(gname, _qg_k, filter, link, csv)`; if `gc >= 0 & !gt` then `comp_cells += gc` else add `gvars`, `qvars` and `_dash_qual_cols_in(_qg_k)` to `row_vars`. KPI: `kpi_var` and `_kqc_k` into `row_vars`. Filter variables (6790-6810) into `row_vars`. At 6875: server route (`"\`server'" != ""`, or `cmdname` is `dash serve` — verify at 7332 that `serve` passes `server`) → `_dash_cell_cap \`=\`_dash_nvars' + \`_dq_n'' "" 0 1`; saved route → `_dash_cell_cap \`: word count \`row_vars'' "" \`comp_cells'`. The `filter` local at that point holds the full names (`_dash_filter_setvars`, 6812).
- **TR-08.9** `_dash_render_immediate` (5920): the same with `filter`, `link` and `csv` empty and `hover` read from `json_spec`; if the immediate route has a server option, keep the full count there too (verify in `_dash_plot`'s syntax, 4422).
- **TR-08.10** dash_render.py: `_DASH_COMPUTED_ONLY_TYPES = frozenset({"histogram","kdensity","lfit","qfit","lfitci","qfitci","fpfit","fpfitci","mspline","mband","lowess","lpoly","lpolyci"})` and `_DASH_COMPUTED_PLOT_CELLS = 120_000` beside `_DASH_LIMITS`; `_dash_embedded_cells(spec, rows, columns, limits) -> (row_cols, extra)` implementing TR-08.6's rule on the parsed spec (graph-level `bin`/`width`/`discrete`/`by` reading over the graph's plots, `hover` from `graph_options`, filters through `_dash_parse_filter_raw(build.filter, warn=False)`, link through `_dash_link_names`, csv through `_dash_csv_wanted`; `row_cols` = the distinct plot columns (`_VAR_KEYS` + `_dash_option_columns`) + `by()` names + qual cols of touched or row-drawing graphs, KPI vars and qual cols, filter variables, each intersected with `columns`; with csv every column). `_dash_refuse_oversized(rows, cols, limits, mode, extra=0)`: `cells = rows*cols + extra`; the message adds ", and {extra:,} values of computed layers" inside the parenthesis when `extra > 0`, "(the drawn output of its computed layers)" when `cols == 0`, and the served sentence when `mode == "server app"`. `_report_dataset_shape(rows, cols, mode, stacklevel=3, extra=0)`: `cells = rows*cols + extra`. Saved call sites: 21100 → `row_cols, extra = _dash_embedded_cells(self.master_spec, self.df.shape[0], list(self.df.columns), self.limits)` then `_dash_refuse_oversized(rows, len(row_cols), self.limits, "dashboard", extra=extra)`; 24087 → `_report_dataset_shape(rows, len(row_cols), "dashboard", extra=extra)` (keep the two results on `self` from `__init__`). Served: unchanged calls; only the sentence. All new functions in `test/function_test_map.py`; none copied into the app.
- **TR-08.11** `test/test_embedded_cells.py::TestTheTwoLanguagesAgree` reads dash.ado's `_pt_univar`/`_pt_onefit` and dash_parse.mata's `return(120000)` and asserts equality with the Python constants, and asserts `_DASH_COMPUTED_PLOT_CELLS >= max(4*bin_cap, 4*n_cap, 4*_FP_GRID_MAX, 2*((bands_cap-1)*mspline_n_cap+bands_cap), 4*_FIT_GRID, 2*300)` with the caps read from dash.ado's option rules at 1866.
- **TR-08.12** dash.sthlp: under `{marker plottypes}` (after 181-193) a sentence that a string variable in a plot's varlist is refused with `{cmd:r(109)}` as `{cmd:twoway}` refuses it, and that `{cmd:colorvar()}`, `{cmd:mlabel()}`, `{cmd:hover()}` and `{cmd:by()}` take one; 1519-1522 and 1560-1572 rewritten for BR-08.4/BR-08.5 (keep the numbers 5,000,000 and 20,000,000 in the synopt: `TestTheHelpDocumentsEveryLimit` reads them). CHANGELOG: G2 under "### Changed behaviour (may need your do-files changed)"; G3 under "### Changed behaviour" (a histogram over the old count now builds) — no number or picture changes for a command that built before, so nothing under "Results that change".
- **TR-08.13** Security (rule 1): the refused variable name and type reach the message only through `_dash_display`; the Mata readers use `strpos`/`ustrregexm` over the JSON and never evaluate it; `_dash_computed_cells` reads `bin` as digits only.

## Boundaries

- Do not change the export: the JSON data file still holds every observation of every variable in `all_vars` (Q9: "the JSON stays"); no binary transport, no temporary frame.
- Do not relax the served app's count (`_embed_data` embeds every row) or the bytes limit (`_dash_byte_cap`, `_dash_refuse_overbytes`).
- Do not change `_dash_limit_table`, `_DASH_LIMITS`, the limit globals or their validation.
- Do not add `ts` to the `syntax` lines (G4, out of scope) and do not change the count checks in `_dash_process_segment` (3322-3376, 3533-3585) or their wording.
- Do not refuse a string `mlabel`, `colorvar`, `hover`, `by` or `wexp` (the weight note at 7883-7889 stays as it is).
- Do not touch `_dash_cap_spec`, the graph/plot limits, or `_dash_take_qual_columns` (section 07 widens it).
- Do not port anything to `_FILTER_JS` (C4 is out of scope); the recount on a filter move already counts as "touched".
- Row-drawing layers stay bounded by the limit (PRD §7, G3 residual).

## Stata truth

No fixture is written. Two truths are measured at run time:

1. **twoway's r(109) and its words**, once per (type, position), by the generated `test/test_string_varlists.cscript`, e.g. `twoway scatter make mpg`, `twoway histogram make`, `twoway rarea make mpg weight`, `twoway pcspike make mpg weight price`, `twoway tsline make` (after `tsset t`), `twoway lfitci mpg make`. The script records nothing to disk; its header lists the measured wording after the first run (task 08-04 pastes it in, marked "measured <date>").
2. **`twoway__histogram_gen`'s bins**, in `test/test_data_limit.cscript`: `twoway__histogram_gen price, bin(10) generate(h x) return` (the form `scripts/extract_stat_truth.do:305` uses) against the page's histogram source.

Invocation, from a scratch directory, one script per session, at most three sessions at once across all batch-1 agents:

```
cd <scratch-dir> && STATATMP=<scratch-dir>/tmp/ arch -arm64 /usr/local/bin/stata-mp -b do /Users/billy/Desktop/Programs/StataPrograms/d/dash/test/<script>.cscript
```

(trailing slash on `STATATMP`; not the log's directory; never the GUI). The generated cscript is committed as an ordinary file; nothing needs `git add -f`.

## TDD test stubs

The regression tests first; each fails at `91d97be` for the reason given.

`test/test_string_plot_variables.py` (new; both modes through `test_mode_parity._spec`/`_standalone`/`_served`, with `monkeypatch.setattr(tp, "_DF", df)` adding a string column `s`):
- Test: `TestAStringPlotVariableIsRefused::test_in_both_modes[type,key]` — parametrised over one type per parser family and each of its variable keys (`scatter` yvar/xvar, `histogram` var, `rarea` yvar1/yvar2/xvar, `pcspike` y1var/x1var/y2var/x2var, `lfit` yvar/xvar, `tsline` yvar): a spec naming `s` there makes `DashRenderer(sp, dp)` and `ServerAppBuilder(sp, dp).build(ap)` raise `dr.DashSpecError` whose text names `s`, the type and `r(109)`. **Pre-fix: `AttributeError` (no `DashSpecError`); with a plain `Exception` catch, the scatter renders garbage and lfit/histogram raise `ValueError: could not convert string to float` from deep in numpy.**
- Test: `test_a_string_in_an_option_is_not_refused[key]` — `colorvar(s)`, `mlabel(s)`, `hover(s)`, `by(s)` render in both modes (control; passes before and after).
- Test: `test_the_message_is_bounded_and_escaped` — a column named `s<script>` 200 characters long: the error text carries `_dash_display`'s bounded form and no raw markup. **Pre-fix: AttributeError.**

`test/test_string_varlists_cscript.py` (new): the three tests of TR-08.5. **Pre-fix: the generator and the cscript do not exist.**

`test/test_embedded_cells.py` (new):
- Test: `TestTheCount::test_a_histogram_over_six_million_rows_passes_and_a_scatter_is_refused` — `_dash_embedded_cells(hist_spec, 6_000_000, ["x"], limits)` → `([], 268)` (default bins at N = 6,000,000: `min(2449.49, 67.78)` → 67, times 4) and `_dash_refuse_oversized(6_000_000, 0, limits, "dashboard", extra=268)` returns; `_dash_embedded_cells(scatter_spec, 6_000_000, ["x","y"], limits)` → `(["x","y"], 0)` and the refusal raises `DashLimitError` naming 12,000,000. No frame of six million rows is built: the function takes the row count as a number and the columns as names, which is how the renderer calls it with `self.df.shape[0]` and `list(self.df.columns)`; the test passes the numbers. **Pre-fix: AttributeError.**
- Test: `test_touched_graphs_count_their_rows[reason]` — the histogram spec with `filter(x, type(range))`, with `link(_all)`, with `csv`, with `hover(x)`, and with a second scatter graph in the same spec: `row_cols` holds `x` (and the scatter's columns). **Pre-fix: AttributeError.**
- Test: `test_a_filter_that_excludes_the_graph_does_not_touch_it` — `filter(x, type(range) exclude(g1))` on the lone histogram `g1` → `([], 268)`.
- Test: `test_width_discrete_lowess_and_by_are_counted_conservatively` — `histogram, width(1)` → `4*N`; `discrete` → `4*N`; `bin(27)` → 108; `lowess` → `2*N`; `kdensity` → 120,000; `histogram, by(g)` → `268 * limits["by_groups"]`.
- Test: `test_kpi_and_filter_variables_always_count` — a KPI `mean(y)` beside the histogram → `row_cols == ["y"]`; a qualifier column named by a KPI counts too.
- Test: `TestTheRefusalAndTheNote::test_the_message_names_the_computed_values` — `_dash_refuse_oversized(74, 2, {"cells": 100}, "dashboard", extra=40)` says "188 values (74 observations x 2 variables, and 40 values of computed layers)"; `(74, 0, {"cells": 30}, "dashboard", extra=40)` says "(the drawn output of its computed layers)"; the served mode appends "A served app embeds every observation of every variable it uses."; and `(51, 2, {"cells": 100}, "dashboard")` is byte-identical to today's text (the existing test's needles). **Pre-fix: TypeError on `extra`.**
- Test: `test_the_note_reports_embedded_bytes` — `_report_dataset_shape(6_000_000, 0, "dashboard", extra=268)` warns nothing; `(6_000_000, 2, "dashboard")` warns "roughly 288 MB". **Pre-fix: TypeError.**
- Test: `TestBothModes::test_the_saved_page_builds_the_histogram_the_served_app_still_refuses` — a 30-row frame, `build_options.limits = {"cells": 40}`: saved `histogram x` renders (bins 5 → 20 cells), saved `scatter y x` raises `DashLimitError` (60 > 40), served `histogram x` raises `DashLimitError` whose text carries the served sentence. **Pre-fix: the saved histogram raises (30 > 40 is false — use 20 rows and `{"cells": 15}`: 20 > 15 refused today, bins 4 → 16 > 15 … choose 24 rows and `{"cells": 22}`: today 24 > 22 refused; after: bins `min(4.9, 13.8)` → 4, 16 <= 22 passes; scatter 48 > 22 refused). Pick the numbers so the pre-fix histogram is refused and the post-fix one passes; write them as named constants with the arithmetic in a comment.**
- Test: `TestTheTwoLanguagesAgree::test_the_computed_types_and_the_constant_are_the_same_in_dash_ado_and_mata` and `::test_the_constant_bounds_every_computed_layer` — TR-08.11. **Pre-fix: AttributeError.**
- Test: `test_the_limits_table_is_untouched` — the existing equality assertion repeated here (control).

Cscripts:
- `test/test_string_varlists.cscript` (generated; SV-<type>-<k>, 89 cases). **Pre-fix: every case fails at the rc assertion — dash is rc 0 (registers the graph) where twoway is 109; histogram/kdensity may be a later Python error on `saving()`, but the script registers with `name()` and never renders.**
- `test/test_data_limit.cscript` (new, DL-01..DL-06; skips 222 without `c(python_exec)`): `sysuse auto` (74 obs). DL-01 `global dash_max_cells 70`; `dash histogram price, bin(10) saving(p.html)` → rc 0, file exists, and the page's histogram source (`top`, `left`, `right` of the Quad, read by a python block as `test_qualifier_in_stata.cscript`'s `_qs_page` reads the page JSON) equals `twoway__histogram_gen price, bin(10) generate(h x) return`'s `h` and `x` at reldif 1e-6. DL-02 the same command with `dash scatter mpg price, saving(p.html)` → r(134), "would embed 148 values (74 observations x 2 variables), more than the 70 dash embeds." — the two lines byte-identical to P19-11's shape. DL-03 the named route: `dash histogram price, bin(10) name(h1)`; `dash build, saving() replace nobrowser` → rc 0; `dash build, saving() replace nobrowser filter(foreign, type(dropdown))` → r(134) "148 values (74 observations x 2 variables)" (touched: price and foreign); `dash build, saving() replace nobrowser link(_all)` → r(134) "74 values"; `dash build, saving() replace nobrowser csv` → r(134); `dash scatter mpg price, hover(foreign) name(h1) replace`-style hover case → r(134). DL-04 `dash kpi mean(price), name(k1)` beside `h1` → r(134) "74 values (74 observations x 1 variable)". DL-05 `dash build, server saving(app.py) replace nobrowser` with only `h1` → r(134) and the third line "A served app embeds every observation of every variable it uses." DL-06 `global dash_max_cells 30`; `dash histogram price, bin(10) saving()` → r(134) "40 values (the drawn output of its computed layers)"; `macro drop dash_max_cells`. **Pre-fix: DL-01 r(134) (74 > 70); DL-03's first build r(134); DL-05 has no third line; DL-06 says "74 values (74 observations x 1 variable)".**

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Every variable position of the 36 types refused as twoway refuses it | cscript `test_string_varlists.cscript` (generated), rc and message equality | none (measured) | n/a (Stata) |
| The generated script is current and complete | pytest `test_string_varlists_cscript.py` | none | n/a |
| Spec-level refusal of a string plot column, named error | pytest `test_string_plot_variables.py` | none | yes |
| String `colorvar/mlabel/hover/by` still accepted | pytest (control) + existing cscripts | none | yes |
| 6M-row histogram passes the count, 6M scatter refused | pytest `test_embedded_cells.py::TestTheCount` (numbers, no frame) | none | n/a |
| Touched/untouched, width/discrete/lowess/by, KPI and filter rules | pytest `test_embedded_cells.py` | none | n/a |
| Refusal text with computed values; served sentence; old text byte-identical | pytest `TestTheRefusalAndTheNote`; cscript DL-02, DL-05, DL-06 | none | yes |
| Note reports embedded bytes | pytest `test_the_note_reports_embedded_bytes` | none | saved |
| Saved histogram builds under a limit that refuses the scatter; served refuses both | pytest `TestBothModes`; cscript DL-01..DL-05 | none | yes |
| Bins equal `twoway__histogram_gen` | cscript DL-01 | none (measured) | saved |
| dash.ado, Mata and Python agree on types and the constant | pytest `TestTheTwoLanguagesAgree` | none | n/a |
| Limits table equality stays green | existing `test_resource_limits.py::TestTheTwoLanguagesAgree` | none | n/a |
| P19-11/13/22/23 unchanged | existing `test_adversarial.cscript` | none | n/a |

Acceptance criteria:
- **AC-08.1** For each of the 89 (type, position) cases, `dash <type> <vars>` returns 109 and prints the lines `twoway <type> <vars>` prints, and registers nothing.
- **AC-08.2** `dash scatter mpg weight, colorvar(make) mlabel(make) hover(make)` and `by(make)` build as before.
- **AC-08.3** A spec with `"yvar": "make"` makes `DashRenderer(...)` and `ServerAppBuilder(...).build()` raise `DashSpecError` naming `make`, the layer and r(109).
- **AC-08.4** `sysuse auto; global dash_max_cells 70; dash histogram price, bin(10) saving(p.html)` builds and its bars equal `twoway__histogram_gen`'s; `dash scatter mpg price, saving(p.html)` is r(134) with the two lines of today; adding `filter()`, `link(_all)`, `csv` or `hover()` to the histogram makes it r(134); `dash build, server` is r(134) with the served sentence.
- **AC-08.5** `_dash_embedded_cells` on a 6,000,000-row histogram spec gives 268 extra cells and no refusal; on a scatter, 12,000,000 and `DashLimitError`.
- **AC-08.6** `test_resource_limits.py::TestTheTwoLanguagesAgree::test_dash_ado_has_the_same_defaults_and_ceilings` and `test_adversarial.cscript` P19-11..P19-23 pass unchanged.
- **AC-08.7** Full pytest green under both interpreters; `test_string_varlists.cscript` and `test_data_limit.cscript` PASS; BUGS.md holds closed G2 and G3 entries naming their tests.

## Tasks

<task type="auto" id="08-01">
  <name>Write the failing pytest files for both gaps]]></name>
  <files>test/test_string_plot_variables.py, test/test_embedded_cells.py, test/test_string_varlists_cscript.py</files>
  <action>
    Write only tests. Create the three files with every test of "TDD test stubs", built on `test_mode_parity._spec`/`_standalone`/`_served` for both-mode cases (rename or extend `tp._DF` through `monkeypatch`), on direct calls for the counting and message tests, and on reading `dash.ado`/`dash_parse.mata` as text for the agreement tests (the pattern of `test_resource_limits.py:1447-1455`). `test_string_varlists_cscript.py` imports the generator by path (`scripts/gen_string_varlists_cscript.py`, `importlib.util.spec_from_file_location`) and fails with "task 08-02 must land first" if it is absent — a `pytest.fail`, not a skip. Put the pre-fix arithmetic of `TestBothModes` in a comment beside its constants. Run the three files against the unmodified tree and paste the failure summary into the commit messages of 08-06 and 08-10.
  </action>
  <verify><![CDATA[`python3 -m pytest test/test_string_plot_variables.py test/test_embedded_cells.py test/test_string_varlists_cscript.py -q 2>&1 | tail -40` collects cleanly; every non-control test fails with `AttributeError`/`TypeError` (the missing functions and keyword) or a wrong-value failure (`test_the_limits_table_is_untouched` and the option-string controls pass).]]></verify>
  <done>Three pytest files exist and every regression test in them fails against the unmodified tree for the documented reason; no source file is modified.</done>
</task>

<task type="auto" id="08-02">
  <name>Generate the string-varlist certification script</name>
  <files>scripts/gen_string_varlists_cscript.py, test/test_string_varlists.cscript, test/run_all_cscripts.do</files>
  <action><![CDATA[
    Write the generator of TR-08.3 (stdlib only; `python3 scripts/gen_string_varlists_cscript.py` rewrites the cscript; `--check` exits 1 when the file differs) and run it. The emitted `_sv_case` implements TR-08.4 exactly, using `cert_helpers.do`'s `_cert_read` and Stata's `log using … text`; give the log a name under `c(tmpdir)` and close it in every path. Cases print `SV-<type>-<k> PASS: …`. Register the script as the next block of `test/run_all_cscripts.do` in the shape of block 64 (1641-1665). Run it once under the rule-10 invocation against the unmodified tree; it must stop at the first case with dash's rc 0 against twoway's 109 — paste twoway's measured lines for scatter, histogram, rarea, pcspike and tsline from the log into the generator's header comment (marked "measured <date>") so the executor of 08-04 knows what to match.
  ]]></action>
  <verify>`python3 scripts/gen_string_varlists_cscript.py --check` exits 0; `grep -c "PASS" test/test_string_varlists.cscript` prints 89; `grep -c "SV-scatteri\|SV-pci\|SV-pcarrowi\|SV-function" test/test_string_varlists.cscript` prints 0; the batch log against the unmodified tree fails at `SV-scatter-1` with dash rc 0.</verify>
  <done>A generated cscript covers every (type, position) of the 36 variable-taking types, is called by the runner, and fails against the unmodified tree because dash accepts what twoway refuses.</done>
</task>

<task type="auto" id="08-03">
  <name>Write the failing data-limit certification script</name>
  <files>test/test_data_limit.cscript, test/run_all_cscripts.do, test/test_cscript_hygiene.py</files>
  <action>
    Create `test/test_data_limit.cscript` in the shape of `test_qualifier_in_stata.cscript`'s header (skip 222 without `c(python_exec)`, `do "../dash_parse.mata"`, `do "../dash.ado"`, `do "cert_helpers.do"`), the `_adv_p19_run`-style log helper, a `python:` block that reads the page's histogram Quad source (`top`, `left`, `right`) into globals, and cases DL-01..DL-06 of the stubs, each ending `display "DL-0k PASS: …"`; drop `dash_max_cells` at the end and in every failure path (`capture` blocks). Register it as the next runner block. Bump `test/test_cscript_hygiene.py` `len(_CSCRIPTS) == 65` to 67 and `len(names) == 47` to 48 (this script skips for Python; the generated one does not), noting in the commit message that the merge reconciles these with other batch-1 sections. Run it against the unmodified tree: DL-01 fails with r(134).
  </action>
  <verify>The batch log stops in DL-01 at the `rc == 0` assertion with "would embed 74 values (74 observations x 1 variable), more than the 70 dash embeds." in the captured log; `python3 -m pytest test/test_cscript_hygiene.py -q` passes with the new counts.</verify>
  <done>The G3 certification script exists, is registered, and fails against the unmodified tree because a small histogram is refused under a limit its bars fit.</done>
</task>

<task type="auto" id="08-04">
  <name>Declare numeric varlists in the four parsers</name>
  <files>dash.ado</files>
  <action>
    TR-08.1: edit the `syntax` lines at 1273, 1298, 1329 and 1358 (`varname(numeric)` at 1298). Update each parser's comment block to say a string variable is refused by `syntax` with twoway's r(109) before any count check. Run `test/test_string_varlists.cscript`; for every family whose lines differ from twoway's, change only that parser's declaration to twoway's form for the family (research D §12 lists them) and re-run until all 89 cases PASS; record the final measured wording per family in the generator's header (08-02) and regenerate so `--check` stays green. Then run `test_parser.cscript` (P1A-31, P1A-43, P1A-52, P1A-56 exercise these parsers), `test_statistical_options.cscript` and `test_twoway_option_parity.cscript` to confirm nothing else changed.
  </action>
  <verify>`test_string_varlists.cscript` prints 89 `PASS` lines and `[ PASS]` in the runner; `test_parser.cscript`, `test_statistical_options.cscript` and `test_twoway_option_parity.cscript` PASS; `python3 scripts/gen_string_varlists_cscript.py --check` exits 0.</verify>
  <done>Every plot variable of every variable-taking type is refused by Stata's own syntax with twoway's code and words, measured, and the option kinds still take strings.</done>
</task>

<task type="auto" id="08-05">
  <name>Refuse a string plot column in both renderers</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action>
    TR-08.2: add `DashSpecError(ValueError)` beside `DashLimitError` and `_dash_refuse_string_plot_vars` beside `_dash_refuse_oversized`; call it at 21102 (saved, after the oversized and overbytes refusals) and after 24981 (served builder). Map the function in `test/function_test_map.py` to `test/test_string_plot_variables.py::TestAStringPlotVariableIsRefused::test_in_both_modes`. Run the full suite once; any test that fed a string plot column and expected a render is flipped with a comment (none is known: `grep -n '"yvar": *"make"' test/*.py` finds only KPI cases).
  </action>
  <verify>`python3 -m pytest test/test_string_plot_variables.py test/test_function_test_map.py -q` passes; `python3 -m pytest test/ -q` is green.</verify>
  <done>A hand-written spec naming a string plot column is refused by both renderers with a named error before anything is drawn, and the function is mapped.</done>
</task>

<task type="auto" id="08-06">
  <name>Document and close G2</name>
  <files>dash.sthlp, CHANGELOG.md, BUGS.md</files>
  <action>
    dash.sthlp: the sentence of TR-08.12 under `{marker plottypes}`. CHANGELOG: under "### Changed behaviour (may need your do-files changed)": a string variable in a plot's varlist is refused with r(109) as twoway refuses it (it was drawn as nonsense or crashed the render). BUGS.md: the closed G2 entry (five fields; Description quoting GAPS2's measured symptom; Resolution naming `test/test_string_varlists.cscript SV-scatter-1` and `test/test_string_plot_variables.py::TestAStringPlotVariableIsRefused::test_in_both_modes`). Run `python3 -m pytest test/test_tracking_documents.py test/test_help_claims_1.py -q -k "Tracking or Closed or help"` and the full suite once; commit G2 (08-01's G2 tests, 08-02, 08-04, 08-05, this task) as one commit with no AI reference.
  </action>
  <verify>Full pytest green; `test_string_varlists.cscript` `[ PASS]`; `git log -1 --format=%B | grep -ci 'claude\|anthropic'` prints 0.</verify>
  <done>G2 is closed and recorded: dash refuses string plot variables as twoway does, in Stata and in both renderers, and the help, changelog and BUGS.md say so.</done>
</task>

<task type="auto" id="08-07">
  <name>Add the per-graph accounting functions in Mata</name>
  <files>dash_parse.mata, test/program_coverage_map.py</files>
  <action>
    TR-08.6: add `_dash_computed_plot_cells`, `_dash_computed_cells`, `_dash_graph_touched`, `_dash_filter_excludes` and `_dash_qual_cols_in` after `_dash_spec_types_in` (5083), each with a comment stating its rule and, for the constant, the derivation table of Evidence; `_dash_filter_refusal` (3416) calls `_dash_filter_excludes` for its exclude() names so the two readers cannot drift. Register each in the file's `*!` index (~225) and in `test/program_coverage_map.py` (`test_data_limit.cscript:DL-01`, `DL-03`, `DL-06` as fits). Run `python3 -m pytest test/test_program_coverage_map.py test/test_no_orphans.py test/test_mata_library_guard.py -q` if the last exists (`ls test | grep mata_library`) and `test_json_escaping.cscript` (JSE-56/58 cover the filter reader).
  </action>
  <verify>The pytest files pass; `test_json_escaping.cscript` PASSes; a `mata: _dash_computed_cells("{\"plots\":[{\"type\":\"histogram\",\"options\":{}}]}", 74, 100, "histogram kdensity")` in a scratch do-file prints 32 and the same with `"type":"scatter"` prints -1.</verify>
  <done>Mata computes a graph's drawn-output count and whether anything reaches its rows, by the rule the renderer will share, and every new function is mapped to a certification case.</done>
</task>

<task type="auto" id="08-08">
  <name>Count what the saved page embeds in dash.ado</name>
  <files>dash.ado</files>
  <action>
    TR-08.7, TR-08.8, TR-08.9: extend `_dash_cell_cap` (2735-2754; keep P19-11's two lines byte for byte when `extra` is 0 and `served` empty; update its comment block 2724-2734); accumulate `row_vars`/`comp_cells` in `_dash_prepare_spec`'s loop (6682-6820) beside `all_vars`, decide the route at 6875, and apply the same rule on the immediate route (5920) with the graph's own JSON. Read `_dash_plottype_families` for the computed-only list (`_pt_univar` + `_pt_onefit`) so dash.ado holds the one list. Run `test_data_limit.cscript` (DL-01..DL-06 pass) and `test_adversarial.cscript` (P19-11..P19-23 unchanged), then `test_qualifier_in_stata.cscript` (the qualifier columns are still made and dropped as before).
  </action>
  <verify>`test_data_limit.cscript` prints six `PASS` lines; `test_adversarial.cscript` and `test_qualifier_in_stata.cscript` `[ PASS]`; `grep -n "computed layers" dash.ado` shows the two new message forms and nothing else changed in the two original lines.</verify>
  <done>dash.ado refuses a saved build on the values the page will embed, keeps the full count for `build, server` and `serve` with the served sentence, and every existing limit case passes unchanged.</done>
</task>

<task type="auto" id="08-09">
  <name>Give the renderer the same accounting and the embedded-bytes note</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action>
    TR-08.10: `_DASH_COMPUTED_ONLY_TYPES`, `_DASH_COMPUTED_PLOT_CELLS`, `_dash_embedded_cells`, the `extra=` keyword on `_dash_refuse_oversized` and `_report_dataset_shape` with the message forms of TR-08.7 mirrored (served sentence when `mode == "server app"`), and the two saved call sites (21100, 24087). The graph-level reading of `bin`/`width`/`discrete`/`by` must mirror Mata's exactly (first `bin` of the graph; any `width`/`discrete`; `by` in `graph_options`). Map `_dash_embedded_cells` in `test/function_test_map.py` to `test/test_embedded_cells.py::TestTheCount::test_a_histogram_over_six_million_rows_passes_and_a_scatter_is_refused`. Run `test/test_embedded_cells.py`, `test/test_resource_limits.py`, `test/test_dataset_size_warning.py`, then the full suite once.
  </action>
  <verify>`python3 -m pytest test/test_embedded_cells.py test/test_resource_limits.py test/test_dataset_size_warning.py test/test_function_test_map.py -q` passes, including `TestTheTwoLanguagesAgree`; `python3 -m pytest test/ -q` is green.</verify>
  <done>The saved renderer refuses and notes on the values the page embeds, by the rule dash.ado applies, the served builder keeps the full count with its sentence, and the two languages' constants and type lists are pinned equal.</done>
</task>

<task type="auto" id="08-10">
  <name>Document and close G3</name>
  <files>dash.sthlp, CHANGELOG.md, BUGS.md</files>
  <action>
    dash.sthlp: rewrite 1519-1522 and 1560-1572 per TR-08.12 (the saved page's count, the served app's, `width()`/`discrete`/`lowess` counting the observations, the 120,000 bound per computed layer, and that the export still writes every observation, so memory during the export is unchanged). CHANGELOG: under "### Changed behaviour": the cells limit counts what the saved page embeds, so `dash histogram x` on more than 5,000,000 observations now builds a saved page while `dash scatter y x` is still refused; the served app's count is unchanged and its refusal says so. BUGS.md: the closed G3 entry (five fields; Resolution naming `test/test_embedded_cells.py::TestTheCount::test_a_histogram_over_six_million_rows_passes_and_a_scatter_is_refused` and `test/test_data_limit.cscript DL-01`, and recording the residual: row-drawing layers, filters, `link()`, `csv` and `hover()` stay bounded by the limit; the export stays JSON). Run `python3 -m pytest test/test_tracking_documents.py test/test_resource_limits.py -q -k "Tracking or Closed or Help"` then the full suite once, `test_data_limit.cscript`, `test_adversarial.cscript`; commit G3 (08-01's G3 tests, 08-03, 08-07, 08-08, 08-09, this task) as one commit with no AI reference.
  </action>
  <verify>Full pytest green under `python3` and under Stata's Python (`make test` and `make test-dev`, or the two `DASH_BASELINE` runs); `test_data_limit.cscript` and `test_adversarial.cscript` `[ PASS]`; `TestTheHelpDocumentsEveryLimit` passes; the commit message has no AI reference.</verify>
  <done>G3 is closed and recorded: the saved page's data limit counts what it embeds, the served app's does not change, and help, changelog and BUGS.md say exactly that.</done>
</task>

## Section completion criteria

- `test/test_string_plot_variables.py`, `test/test_string_varlists_cscript.py` and `test/test_embedded_cells.py` pass; each regression test in them failed at `91d97be`.
- `test/test_string_varlists.cscript` (89 cases, generated, `--check` green) and `test/test_data_limit.cscript` (DL-01..DL-06) PASS; `test_adversarial.cscript` P19-11..P19-23, `test_parser.cscript`, `test_qualifier_in_stata.cscript` PASS unchanged; the runner and the hygiene counts include both scripts.
- `_dash_limit_table` and `_DASH_LIMITS` unchanged and equal; `_DASH_COMPUTED_ONLY_TYPES` equals dash.ado's `_pt_univar` + `_pt_onefit`; `_DASH_COMPUTED_PLOT_CELLS` equals Mata's constant and bounds every computed layer.
- The JSON export is unchanged (no test of `test_string_value_export.py`, `test_data_file_numbers.py` or `test_qualifier_in_stata.cscript` changes).
- BUGS.md holds closed G2 and G3 entries naming existing tests; dash.sthlp and CHANGELOG updated; two commits on `s3-bugs`, one per gap, the full suite green before each, no AI reference anywhere.

## Notes

- **The r(109) wording is measured, never typed.** The generator's header carries the measured lines only as a record; the assertion in every case is equality with twoway's log in the same run. If dash cannot match a family through `syntax` alone (a type whose twoway front-end has its own parser — tsline/tsrline are the likely ones), the fix is still in the parser declaration, family by family, and the reason is recorded in the commit message. Do not special-case the message text in `_dash_process_segment`.
- **`varname(numeric)` at 1298** keeps `\`varlist'` populated (Stata sets both), so the sreturns need no change; the `[if] [in]` and weight clauses stay.
- **P19-11's two-line rule** is byte-exact: the first line's text, the parenthesis and the trailing period must not move when `extra == 0`; the served sentence is a third line only on the server route; the `nvars == 0` form is a different first line and never fires for a scatter.
- **Graph-level reading of `bin`/`width`/`discrete`** is deliberate so Mata and Python read the same thing from different representations (JSON text vs. plot list); a graph holding two histograms with different `bin()` values is counted from the first. Say so in both comments.
- **`by()` on a computed-only graph** multiplies by the by_groups limit (`_dash_limit, name(by_groups)`; `limits["by_groups"]`), not by the actual group count, which is not known before the export.
- **Hover variables are not exported** (BUGS.md:761); the renderer's `row_cols` intersects with `columns`, so a hover-only name never counts on either side, and a graph with `hover()` is "touched" through its plot variables only.
- **The immediate route** builds a saved page; verify at `_dash_plot` (4422) whether it takes a server option before deciding TR-08.9's branch.
- **`_dash_filter_refusal` runs before the pooling** (6790: "read and proven a name by _dash_filter_refusal above"), and `filter` holds full names after `_dash_filter_setvars` (6812); `_dash_graph_touched` reads the same text.
- **Line numbers drift.** 08-05 adds ~30 lines near 1121 and 08-09 ~80 lines near 1056; later anchors are pre-edit and every site is named by symbol.
- **Copy lists.** Nothing in this section is copied into the generated app: the refusals and the count run in dash_render.py's own process (saved renderer, served builder). Do not add the new functions to the served lists; `TestTheServedAppDefinesEveryNameItReads` would then demand their callees too.
- **Hygiene counts and the runner are shared** with every batch-1 section that adds a cscript; reconcile once at the merge (this section: +2 scripts, +1 that skips for Python).
- **Stata sessions.** `test_string_varlists.cscript` runs 89 twoway commands under `graph` (about two minutes); run it alone, never beside two other Stata sessions from this section, and check `display c(python_exec)` before trusting a `[ SKIP]` of `test_data_limit.cscript`.
- **Memory.** No test allocates six million rows; the counting functions take numbers. A manual probe with `set obs 6000000` is fine outside the suites but must not be committed.
- **Silence.** No note is added for a build that passes; only refusals gain text (Q22).
