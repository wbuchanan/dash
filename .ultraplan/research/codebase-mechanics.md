# How the dash codebase works: the facts the GAPS3 work-package briefs need to cite

Everything here was read on the current tree, and read-only: I ran no Stata and no pytest. The only commands I executed were four one-line `python3 -c` probes, all import or metadata checks: bokeh's version and requirements, `figure.contour`, `bokeh.plotting.contour`, and `DataTable`.

Many line numbers have moved since the ones in your request. Every number below is current. The biggest moves:
- `_FILTER_JS` starts at dash_render.py:24612. Line 46229 is `DashRenderer.render()` collecting the aggregate layers.
- `_glyph_layer_lines` is at 46530-47393.
- `_dash_require_deps` is in dash.ado:338-382, not in dash_render.py. The renderer's own guard is `_dash_dep_fail`, dash_render.py:92-127.
- `_dash_option_rules` runs 2987-3079.

## 1. How an option travels from the command to the page

### 1a. A plot option: `barwidth()`

1. **Declaration.** `_dash_parse_plot_opts` (dash.ado:1137) declares it in its `syntax` block (1167-1239): `BARWidth(string asis)` at :1177.
   - Capital letters are the minimum abbreviation.
   - The trailing `*` (:1238) collects anything undeclared into `options`, which becomes `s(_unknown)` at :1401.
   - Before `syntax` runs, `_dash_log_split` (:1166) takes `log`/`nolog` out.
   - After it, the stylelist options are normalised (:1246-1249, list from `_dash_stylelist_keys()`, dash_parse.mata:5283-5292). `barwidth` is on that list as a value list.
   - The plot-level alias folds are at :1264-1299.
2. **sreturn.** `sreturn local barwidth` at :1428. Graph options written inside a segment are returned as `g_<opt>` (:1532-1607). The pending list goes back as `s(_pending)` (:1608) and the unmatched text as `s(_unknown)` (:1609).
3. **The caller.** `_dash_process_segment` (:4843) runs these steps in order (:5486-5619):
   1. `_dash_route_axis2` (:5493; Mata dash_parse.mata:7015)
   2. the parse (:5494)
   3. `_dash_refuse_unbound` (:5498)
   4. the second-`name()` check (:5502)
   5. `_dash_refuse_foreign` (:5507)
   6. `_dash_opts_repeats` (:5510)
   7. `_dash_recast_opt` (:5516)
   8. `_dash_hz_check` (:5526)
   9. `_dash_connect_opt` (:5535)
   10. the logit refusal (:5556-5563)
   11. **the barwidth-on-rcap refusal (:5564-5574)**
   12. `_dash_fold_mlabv` (:5577)
   13. `_dash_fold_bw` (:5578)
   14. the weight into s() (:5579)
   15. **`_dash_validate_opts` (:5584)**
   16. `_dash_stylelist_check` (:5585)
   17. **`_dash_fold_typed` (:5594)**
   18. `_dash_sort_opt` (:5603)
4. **The rules table.** `_dash_option_rules` (:2987-3079) puts its tables into `c_local`s:
   - `plot` tokens (:2990-3008) have the form `opt=kind[,p1,p2,p3][@type|type…]`. barwidth's rule is `barwidth=pos` (:2997).
   - `graph` tokens (:3046-3053).
   - `flags` (:3064-3066), form `flag|flag@type|type`.
   - `values` (:3070), which lists `mlabel jitter base barwidth`. These are checked per element by `_dash_value_list` (:3636).
   - `onevalue` (:3073): `barwidth@rbar|histogram|rcap|rspike  base@rbar|histogram`. On those types twoway refuses a list with "option barwidth() not allowed".

   `_dash_validate_opts` (:3837-4012) applies them:
   - Flags (:3859-3872): a flag on a type outside its list is refused, `display as error "option `f' not allowed"`, `exit 198`.
   - **`@type` precedence** (:3923-3932): a type-specific rule makes the untyped rule for that option skip on that type. The rule loop (:3933-3969) runs `continue` for any `@` rule whose types exclude this type.
   - The graph rules are checked against `s(g_<opt>)` (:3974-3990).

   The kinds are implemented in `_dash_validate_value` (:3098-3620):

   | Kind | Line | Meaning |
   |---|---|---|
   | `num` | :3166 | `,lo,hi[,x]`; `x` means strict |
   | `int` | :3195 | |
   | `pos` | :3218 | `,max` |
   | `colour` | :3234 | refuses a comma-written RGB |
   | `style` | :3261 | `,lo,hi[,u]`; `u` means a line width with gm_linewidth wording |
   | `istyle` | :3308 | |
   | `enum` | :3316 | `,a\|b\|c` |
   | `numlist` | :3331 | `,min[,max]` |
   | `axislist` | :3358 | |
   | `keyformat` | :3383 | |
   | `var` / `varlist` / `byvarlist` | :3408 | r(111) for a variable not found |
   | `scheme` | :3505 | |
   | `format` | :3583 | |

   Where a bound is dash's own rather than twoway's, an extra sentence is added (:3147-3163: yaxis/xaxis "dash draws two axes", degree, bin, n, lowess bwidth). The error form (:3615-3618) is `"dash: <opt>() must be <bad> (got: <value>)<extra>"`, r(198).
5. **The JSON writer.** `_dash_plot_opts_to_json` (:4400-4477) walks a fixed key list (:4441-4458; barwidth at :4443). A stylelist key writes y number k's element through `_dash_stylelist_pick`. Under `p()` the keys in `_dash_p_drops` (:4415-4430) are dropped. **The spec key is the option's full name** inside the plot's `"options"` object: `{"type":"bar","yvar":…,"xvar":…,"options":{"barwidth":".3"},…}` (assembled at :5862-5883).
6. **The renderer.** `GlyphMapper.map_bar` reads `options["barwidth"]`, then `"width"`, through `_stat_option_float` (dash_render.py:15341-15354). `map_rbar` reads them at :18546-18551. `OptionTranslator` (class at :6721) only converts values: colours, symbols, sizes (`resolve_size` :7098, `translate_lwidth` :7602, …). The `GlyphMapper._apply_*` appliers are:
   - `_apply_line_opts` :13143
   - `_apply_marker_opts` :13243
   - `_apply_fill_opts` :13503
   - `_apply_colorvar` :13664
   - `_apply_mlabel_opts` :14104
7. **The served app.** It gets the same code because the whole `OptionTranslator`, `SchemeParser` and `GlyphMapper` classes are copied by source (`_glyph_layer_lines`, class loop at dash_render.py:47281-47283). A method needs no copy-list entry. A **module-level** helper or constant does:
   - the constants tuple is at :46584-46784;
   - the functions tuple is at :46822-47270;
   - helpers that `_shared_stat_lines` already emits are skipped through `_emitted_names` (:46819-46821);
   - `_shared_stat_lines` (:47396-47569) copies the statistical helpers (tuple :47446-47503) and five staticmethods with their `GlyphMapper._` prefix stripped (:47519-47530: `_histogram_grid`, `_default_lpoly_bwidth`, `_compute_lpoly_fit`, `_bootstrap_ci`, `DashRenderer._kpi_statistic`).

   The copy loop skips a misspelt name silently (`getattr(..., None)` then `continue`, :46785-46787 and :47273-47275). `test_statistical_helpers.py::TestTheServedAppCarriesEveryName::test_every_listed_name_exists` catches that.

   The served header has its **own bokeh import list** (`_generate_app_source`, :48014-48035ff). A new Bokeh model, such as `DataTable`, must either be imported inside the function that uses it (the `_dash_reference_lines` pattern, `from bokeh.models import Span` at :38870) or added to both import lists.

### 1b. A graph option: `xline()`

1. It is declared in `_dash_parse_graph_opts` (:933-966) as `XLIne(string asis)` (:937), and again in the plot parser (:1209) so it can be written inside a segment. sreturn: :1056 (graph parser) and :1542 (`g_xline`, plot parser).
2. **Seven identical key lists** in dash.ado must agree; `test_abbreviations.py::TestTheAxisRouteKnowsDashsSpellings::test_the_seven_graph_key_lists_agree` (test/test_abbreviations.py:773) checks this:
   - :5776, the segment hands back `_sg_<key>`
   - :6714, the accumulators are initialised
   - :6748, the after-comma capture
   - :6849, the per-segment reset
   - :6924, the merge
   - :6956, the after-comma merge
   - :7339, the JSON writer
3. **Repeats** are merged by the category in `_dash_rep_cat` (dash_parse.mata:6166; `xline` is category "X", every copy kept, joined with ", ") and by `_dash_rep_merge` (:8838). Options twoway takes only once are in `_dash_rep_unique` (:6200).
4. **Validation** is `_dash_line_check` (dash.ado:7669, called from `_dash_plot` near :6984), then `_dash_line_expand` (:6988-6990), then `_dash_reflines_cap`.
5. **JSON.** The `graph_options` object is built at :7335-7415 with key = option name (`"xline":"…"`). `text()`/`ttext()` are skipped there and written as `added_text` records. The graph JSON itself is at :7451.
6. **The renderer** reads `graph_opts.get("xline")` in `_dash_reference_lines` (dash_render.py:38859; the loop at :38871). It is called from the saved `DashRenderer._make_figure_body` at :43808 and from the served template's `_dash_figure_for` at :49474. The function is on the copy list (:47223).

### 1c. The pending list, the generic note and the foreign-option refusal

- **The pending blocks.** Graph: dash.ado:1010-1042. Plot: :1320-1387. Each line has the form ``if `: length local X' local _dash_pending `"`_dash_pending' X"'``. Tests find these lines with the regex `_dash_pending' (\w+)"` between `program define <parser>` and `local _dash_unknown`. The tests that do so: test_unsupported_report_is_true.py:169, test_help_conformance.py:342, test_help_claims_8.py:1372, test_color_alias.py:140, test_jitter.py:355.
- **`_dash_fold_typed`** (:2201-2272) adds names to `s(_pending)` once the type is known:
  - colorvar and its companions off `cv_types` (scatter, connected, rconnected, dot);
  - jitter on rscatter, rcapsym, pcscatter, pccapsym;
  - a bare `sort` off `sort_types`;
  - the fitarea options are *removed* from the list on the ci types (:2247-2253);
  - lstyle/alstyle/blstyle on area and rarea;
  - mstyle/mlstyle on the arrow types.

  Its comment at :2228-2233 is stale (GAPS3 F5).
- **The generic note.** At the end of each segment, `s(_pending) + s(_unknown) + [weight]` goes into `_seg_ignored_out` (:5735-5738). `_dash_plot` accumulates it and calls `_dash_report_ignored` once (:7307-7309; program :6590-6635). That program cuts the text to option names with Mata `_dash_option_names`, removes duplicates, and prints `dash: ignoring unsupported option(s): a() b()` through `_dash_note`.
- **`_dash_rep_und_tab`** (dash_parse.mata:6250-6324) is **not** a "named, not drawn" list. It lists the options dash does *not* declare that twoway takes **once**. Columns: name, full spelling, shortest spelling, takes a value, types (`*` for all), graph-wide, `no` half. Its readers:
  - `_dash_rep_und_scan` (:6384): refuses a second copy, `option atobs not allowed`, r(198);
  - `_dash_rep_und_cross` (:6432): counts graph-wide options across segments;
  - `_dash_foreign_scan` (:6547-6586): rows an undeclared word may match without being foreign;
  - `_dash_kernel_clash` (:6598) and `_dash_kernel_flag` (:6645).

  Undeclared lower-case words simply fall to the catch-all and are named in the note. **When you declare an option that has a row here, delete the row**, and if twoway takes it only once, add it to `_dash_rep_unique` (dash_parse.mata:6200). The precedent is the colorvarminmax comment at :6294.
- **`_dash_refuse_foreign`** (dash.ado:8569-8610) uses `_dash_foreign_scan`. It refuses an upper-case option, or a plot option written after the plot groups' comma, with "option X not allowed", r(198). Otherwise it re-parses.

### 1d. What a section edits

**(a) To declare a new option:**
1. Add it to the `syntax` of `_dash_parse_plot_opts` (:1167-1239) and/or `_dash_parse_graph_opts` (:933-966), with twoway's minimum shown in capitals.
2. Add an `sreturn local <opt>` (plot :1403-1530, or `g_` :1532-1607; graph :1046-1121).
3. Plot option: add the key to `_dash_plot_opts_to_json`'s list (:4441-4458). If `p()` drops it, add it to `_dash_p_drops` (:4415-4430). If it is a per-y list, add it to `_dash_stylelist_keys()` (dash_parse.mata:5283).
4. Graph option: add it to **all seven** key lists (:5776, 6714, 6748, 6849, 6924, 6956, 7339); `_dash_rep_cat` if it merges; `_dash_rep_unique` if twoway takes it once.
5. Add a rule to `_dash_option_rules` if its value is bounded.
6. Delete any `_dash_rep_und_tab` row for it (dash_parse.mata:6250-6324).
7. Tests:
   - test_unsupported_report_is_true.py: classify it as a pending option with a `PLOT_VALUES` entry (:81), or live with a `LIVE_VALUES` entry (:447ff), or in `ALIASES`/`NOT_IN_FILE`. Bump the declared counts at :725-726 (196/85 now) with a `# a -> b: <id> <why>` comment.
   - test_abbreviations.py: no prefix may be claimed by two options (:406), and the declared minimum must cover Stata's per test/fixtures/abbrev_truth.json (:277).
   - test_help_conformance.py:825: an option twoway lacks, i.e. absent from abbrev_truth.json, must have a help definition entry.

**(b) To draw a pending option:**
1. Delete its `if … _dash_pending` line in **both** parsers where present.
2. Read the spec key in the shared glyph layer or helpers. Any new module-level helper goes in the copy list.
3. Move its test entry from `PLOT_VALUES` to `LIVE_VALUES` (two values that must render differently) and update `test_the_blocks_were_actually_found` (:240-262; counts 43 plot and 24 graph now).
4. Remove it from dash.sthlp's Unsupported section ({marker unsupported} at dash.sthlp:4967 to {marker dependencies} :5136). `TestTheUnsupportedSectionIsTrue` (test_help_conformance.py:938-960) checks this both ways.
5. `test_help_claims_8.py::TestAnUnsupportedOptionIsInertWhenServed` (:1410) derives its list from the pending blocks, so it follows automatically. Add a `_CONTEXT` entry (:1380) if the option needs a host option.
6. Update TWOWAY_COVERAGE_AUDIT.md in the same commit (DISCOVERY Q26).

**(c) To refuse an option on a type with twoway's words.** Today there are four patterns:
- (i) **A flag**: an entry in `flags` (:3064-3066), giving "option X not allowed", r(198).
- (ii) **A typed rule** `opt=kind,…@types` (e.g. :3000-3001, :3006-3007), for a value check per type.
- (iii) **The typed-spelling pattern** used for barwidth on rcap/rcapsym: a Mata `_dash_barwidth_typed(opts)` (dash_parse.mata:6514-6528), built over `_dash_rep_toks` and `_dash_rep_optname` so quoted or nested text is never read, plus a block in `_dash_process_segment` (:5564-5574) that runs `_dash_say("err","option ",typed,"() not allowed")`, `exit 198`. The new Mata function must be added to `_dash_require_mata`'s `_needed` list (dash.ado:448-479), to the dash_parse.mata header index (lines 1-~420), and to test/program_coverage_map.py.
- (iv) **`onevalue`** (:3073), for a list where twoway takes one value.

There is **no per-type applicability column** for value options yet (GAPS3 C3). Such a column would sit beside the `flags` syntax. The natural place to apply it is in `_dash_validate_opts`, before the rule loop (:3923), after recast has fixed the type (`_rc_own`). Every newly refused form needs a CHANGELOG "Changed behaviour (may need your do-files changed)" line (WP-30 M5), and its cscript case goes in the area script (test_option_validation.cscript or test_twoway_option_parity.cscript), comparing against `capture noisily twoway` run in the same session.

## 2. Registering a plot type

- **Families.** `_dash_plottype_families` (dash.ado:4516-4529):
  - `_pt_univar`, `_pt_range`, `_pt_pc`, `_pt_literal`, `_pt_imm` and `_pt_ts` are the routing families;
  - `_pt_onefit` and `_pt_onefit_bare` hold the fits and smoothers.

  The renderer's categories are `_DASH_RANGE_TYPES` (dash_render.py:25958), `_DASH_UNIVARIATE_TYPES` (:25962), `_DASH_PC_TYPES` (:25967) and `_DASH_LITERAL_TYPES` (:25975). `test_plottype_families.py:176-184` requires the two sides to be equal.
- **Abbreviations.** `_expand_plottype_str` (dash_parse.mata:1688-1780) holds a `(full, minimum)` table (:1703-1742) and the two special spellings `mbands`/`fn` (:1757-1758). Minimums dash takes beyond twoway's (GAPS3 A2): `sc li con ar ba sp lfi qfi low lpo fp kde dr tsl tsrl msp rl rcon rsc fun`. The help states twoway's eight short names at dash.sthlp:236-244. `test_mode_parity.py::_mata_expanded_types` parses the table with the regex `\("([a-z]+)","([a-z]+)"\)`.
- **Types refused by name.** `_dash_undrawn_plottype` (dash_parse.mata:1802-1810) holds `contour contourline rpcap rpspike`. dash.ado gives the reasons at :4889-4900. The generic "Supported:" list is at :4901-4909; `test_every_plot_type_draws._advertised_plot_types` parses it.
- **Variable-count branches** in `_dash_process_segment`:
  - univar :4981-4986
  - range :4987-5037 (twoway's words: "too few variables specified" r(102), "`ptype' requires 3 variables: …" r(102)/(103))
  - pc :5038-5059
  - literal :5060-5172
  - standard :5173-5262ff (fits: "too many variables specified" r(103) at :5232-5245)

  JSON fields: :5792-5830 (`var` / `yvar1,yvar2,xvar` / `y1var,x1var,y2var,x2var` / `expr` / `values` / `yvar,xvar`). The axis x variable is chosen at :5761-5765.
- **Other type lists in dash.ado** that a new type must be judged against:

  | List | Line |
  |---|---|
  | `mv_range` | :2132 |
  | `jit_undrawn` | :2218 |
  | `_hz_htypes` / `_hz_vtypes` (also renderer `_DASH_HORIZONTAL_TYPES`, `_DASH_VERTICAL_TYPES`, `_DASH_DERIVED_ORIENT_TYPES`, dash_render.py:31835-31849; test_horizontal.py) | :2301-2302 |
  | `_so_ser` | :2471 |
  | `_rng` / `_sp_rng` (recast) | :2586, :2595 |
  | alwidth and mlabangle type lists in the rules | :3006-3007 |
  | `_wt_honoured` | :5367 |
  | `_pt_nots` | :5195 |
  | `_cap_types` | :5567 |
  | `_ss_types` | :5654 |
  | `_ts_sortx` | :5671 |
- **Spec variable keys.** Mata `_dash_extract_vars` (dash_parse.mata:2847, key list at :2855-2857) and `_DASH_PLOT_VAR_KEYS` (dash_render.py:36470) both list `yvar xvar var yvar1 yvar2 y1var x1var y2var x2var`.
  - rpcap/rpspike (y ylow yhigh x) can reuse `yvar` + `yvar1` + `yvar2` + `xvar` without changing these lists.
  - contour (z y x) needs a new key such as `zvar` in both lists, plus `_dash_hover_layer_vars` (:40053), `_dash_layer_axis_names` (:1252), `_dash_axis_vars` (:1288), `_dash_layer_tick_format` (:1358) and `_dash_layer_series` (:39826).
- **Dispatch in the renderer:**
  - `_dash_glyph_dispatch` (dash_render.py:41883-41935): `dispatch` maps a name to `mapper.map_<name>`; `range_dispatch` handles the range types.
  - `_dash_pc_dispatch` (:41938-41951).
  - `_dash_plot_type_names` (:41954-41985) counts a key only when it maps to `map_<key>`, plus `_DASH_LITERAL_TYPES`. It is in TEST_ONLY and is **not** copied into the app.
  - `_dash_add_glyph` (:42344-42404) passes range types as `(fig, source, y1, y2, x, options, view=, color_idx=)`, univariate types as `(fig, source, y, options, …)`, and the rest as `(fig, source, y, x, options, …)`; `_dash_add_pc_glyph` is at :42407.
  - The family branches that call these: saved `DashRenderer._make_figure_body` (:43644; branches about :43981-44023); served `_dash_draw_layer` in the template (:49137-49225).
  - Also check `_DASH_JOIN_TYPES` (:40665), `_DASH_FIT_TYPES`/`_DASH_CI_TYPES` (:39567-39574), `_DASH_COMPUTED_ONLY_TYPES` (:1884) with Mata `_dash_computed_plot_cells` (dash_parse.mata:9514; test_embedded_cells.py), `_DASH_WEIGHT_ACCEPTS` (:397), `_dash_plot_style_indices` (:39585) and `_dash_legend_entries`.
- **Tests.**
  - test_every_plot_type_draws.py builds `_plot_for` (:181) from the ado families. A new family needs a branch there, and a new literal type raises.
  - test_mode_parity.py `CORPUS` (:1398) begins with a bare `_case(t,[plot_for(t)])` per type. `TestTheCorpusIsComplete` (:3448-3480) checks: a bare entry per dispatched type; no corpus type the code lacks; the code set equals the dash.ado "Supported:" set; it equals the Mata table; the literal set is pinned.
  - `plot_for` lives in test/test_server_layer_defects.py:80 with hard-coded `_RANGE`/`_PC` sets (:68-71); it needs a branch for a new shape.
  - test_help_plot_types.py: the `{marker plottypes}` table (dash.sthlp:235ff) must equal `_dash_plot_type_names()`; `_REFUSED` (:28) must be named after the table and found in `_dash_undrawn_plottype`'s body.
  - test_parser.cscript P1A-49..57 (test_parser.cscript:249-) pin today's refusals and must be flipped.
  - Also `_DASH_HORIZONTAL_TYPES` in test_horizontal.py, test_plottype_families.py and test_no_orphans.py (P1A-76's "no name reaches two rows").
- **Every file rpcap or contour must touch.**
  - Stata side: dash.ado (families, the var-count branch, vfields, Supported list, refusal removal, type lists), dash_parse.mata (abbreviation table, `_dash_undrawn_plottype`, `_dash_extract_vars` if a new key).
  - Renderer: dash_render.py (`map_rpcap`/`map_contour`, a dispatch entry, a `_DASH_*_TYPES` category or new family, family branches in both modes, var-key lists, horizontal tables, copy list for new module helpers).
  - Help: dash.sthlp (Plot types table, the refusal sentence at :573, the help Unsupported section).
  - Tests: test_every_plot_type_draws.py, test_mode_parity.py (CORPUS, MOVE_CORPUS), test_server_layer_defects.py (`plot_for`), test_help_plot_types.py, test_plottype_families.py, test_horizontal.py, test_parser.cscript, function_test_map.py, program_coverage_map.py; plus TWOWAY_COVERAGE_AUDIT.md:14,24,101-103 and dash.pkg's "forty twoway plot types" description.
  - Dependencies: bokeh 3.9 here has `figure.contour` and `bokeh.plotting.contour`, and requires `contourpy>=1.2` (measured).

## 3. The saved page's JavaScript recompute

- **Python side.** A mapper tags its renderer with `r._dash_agg_source` (the curve or bin source), `r._dash_agg_config` (a JSON-safe dict) and `r._dash_agg_rows` (from `_agg_member_ids`, :15675-15696).
  - Histogram config: :18011-18054. Keys: `type, varname, bin_edges, ymode, wvar, wtype, discrete, start, width, bin`, plus the date keys `datekind, unit_edges, bin_first, wdatekind`.
  - Kdensity config: :18380-18412. Keys: `type, varname, x_grid, kernel, bw_rule, bw_fixed, wvar, wtype`, optionally `datekind, x_eval, wdatekind, join`.
  - `DashRenderer.render()` step 3b (:46219-46237) collects these into `agg_source_registry[gname]` as `(source, cfg)`, adding `member_ids` when the layer counts a subset.
  - `_build_filter_widgets` (:45427) adds `use=_use_for(gname)` (the filter indices that reach the graph) and sets every callback's `agg_sources` and `agg_configs_json` (:45706-45717, :45787-45788).
- **JavaScript side.** Inside `_FILTER_JS` (:24612): `const agg_configs = JSON.parse(agg_configs_json)` (:25152). Then, per config:
  - `dash_data_for(ac.use)` (:24768; masks by `dash_mask_for` :24736);
  - a `member_ids` pick;
  - **one variable** `raw_col = _pick(_ac_data[ac.varname])`, with `continue` if absent;
  - values and weights joint-filtered.

  Then the `histogram` branch (:25213-25284) and the `kdensity` branch (:25285-25375), each writing `src.data` and calling `src.change.emit()`. **An x/y estimator needs both its x and y columns, filtered jointly.** The shared prelude reads one variable only, so a fit branch must read `ac.xvar` and `ac.yvar` itself or the prelude must be generalised.
- **Shared JS helpers.**
  - `_DASH_FMT_JS` (:23390): `dash_fmt` :24309, `dash_fmt_text` :24340, `dash_html_escape` :24345, `dash_stata_value_of` :24285.
  - `_DASH_FILTER_MASK_JS` (:24504): `dash_filter_mask`.
  - `dash_join_rebuild` :24665, `dash_pctl` :25085, `dash_wpctl` :25104, `dash_kernel` :25124.
  - The KPI block runs from "// ---- KPI recompute, shared by" (:24904); `dash_apply_kpis` is :24916.
  - The axis re-finish is appended after `_DASH_AXIS_FINISH_JS` (:30933) by the module statement at :31459-31462 (never inside the literal; WP-30 A153).
- **Slicing hazards.**
  - The brush script copies two slices of `_FILTER_JS` by marker: "// ---- KPI recompute, shared by" up to "dash_apply_kpis(new_data,", and "function dash_pctl(" up to "// Stata's kernels ([R] kdensity)" (:45374-45389).
  - `test/js_runner.run_filter_js_block` (:518-556) slices "function dash_pctl" up to "// agg_sources is a Bokeh model list" as helpers, and cuts the branches at `"if (ac.type === 'histogram') {"`, `"} else if (ac.type === 'kdensity') {"`, `"// DASH_KDE_RULE"` and `"src.data = { x: xs, y: ys };"`.
  - **Where to register a JS twin.** Put new estimator helpers as named functions between `dash_kernel` and the "// agg_sources is a Bokeh model list" comment, so run_filter_js_block's helper slice carries them; never between `dash_pctl` and "// Stata's kernels". Add a new `else if (ac.type === '<type>')` branch after kdensity, and extend js_runner with a block runner for it.
- **The stale cue** (WP-29 M3):
  - Constants: `_DASH_STALE_ALPHA`, `_DASH_STALE_SUFFIX`, `_DASH_STALE_CUE_TEXT`, `_DASH_STALE_STATUS_HTML` (:1896-1910). The status line is the only `role="status" aria-live` in the code.
  - `_dash_stale_kind` (:1913-1929) returns "fit" for every non-histogram, non-kdensity computed type.
  - Tags are attached in `_make_figure_body` (:44049-44060, `_frozen_layer_tag` :43040) and collected by `_collect_frozen_layers` (:43078). `_stale_cue_args` (:45817-45899) builds the models.
  - The JS marking block is at :25377ff, inside `_FILTER_JS`.
  - **A type that gains a JS refit** must also make `_dash_stale_kind` return None for itself. Otherwise it is refit and still marked "(unfiltered)". Then flip test/test_saved_stale_cue.py `_FROZEN` (:58), the `_DASH_STALE_STATUS_HTML` text and the help.
- **Why a recast histogram or kdensity is marked stale (GAPS3 C16).** The recast path returns through `_dash_draw_xy_as` before the agg tagging (:17995-18003), so it never gets an `_dash_agg_config`.
- **Python estimators** (all copied into the app):

  | Estimator | Location | Signature |
  |---|---|---|
  | `GlyphMapper._compute_lpoly_fit` | :16960 | `(x, y, bwidth=None, degree=0, n_grid=None, kernel="epanechnikov", w=None, x_grid=None) -> (xg, yg)` |
  | `_fit_grid` | :20969 | `(x, options, layer="fit")`, n default 100, `_FIT_GRID` :474 |
  | `_dash_wls` | :22185 | `(X, y, w=None, wtype=None) -> dict` |
  | `_t_ppf` | :20887 | `(p, df)` |
  | `_fp_grid` / `_fp_report_unsupported` | :21007 / :21042 | |
  | `GlyphMapper._fp_prepare` / `_fp_design` / `_fp_screen` / `_fp_fit` / `_fp_plot_grid` / `_fp_stdp` | :17389 / :17424 / :17451 / :17577 / :17630 / :17677 | `_FP_POWERS` :17378 |
  | `GlyphMapper._stata_lowess` | :16801 | `(x, y, bw=0.8, mean=False, noweight=False)` |
  | `_default_lpoly_bwidth` | :16922 | |
  | `_lpoly_rot_*` | :21459-21621 | |
  | `_lpoly_kernel_weights` / `_lpoly_local_wls` / `_lpoly_se` | :22049 / :22067 / :22103 | |
  | `_mband_default_bands` | :20795 | |
  | `_natural_cubic_spline` | :22385 | mspline |
  | `_qfit_design` | :22293 | |
  | `_dash_fitci_std` / `_dash_fitci_se` | :22342 / :22352 | |
  | `GlyphMapper._fitci_std_for` | :16528 | `(options, wtype, layer)` |
  | `_stata_kde_bandwidth` / `_kde_curve` | :21850 / :21911 | |

  The served app wraps lowess, lpoly and fpfit in `_dash_memo_wrap` (:35168; template :48709-48716).
- **How a parity test compares a JS twin with Python.** The pattern is test_statistical_helpers.py:810-848 (`TestFilterJavaScript`):
  1. draw with `GM().map_<type>(figure(), ColumnDataSource(...), …)`;
  2. take `r._dash_agg_config`;
  3. run the JS branch under node on a subset (`run_filter_js_block`);
  4. compare with the Python mapper's output on the same subset (`np.testing.assert_allclose`).

  For the whole page, `js_runner.JsSession(r.filter_callbacks)` (js_runner.py:302-439) runs a callback's real code and args, commits `data`, `booleans`, `text`, `width`, `muted`, `visible` and `label` back, and supports chained moves. The node prelude stubs `change.emit` and `setv` (:218-275). The timing bound is test_estimator_cost.py (oracles and bounds).

## 4. The served app's move path

All of this lives in the template strings of `ServerAppBuilder._generate_app_source` (:47847-51072).
- **Wiring.** Each widget gets `on_change('value_throttled' or 'value', _dash_event_throttle(doc, _dash_touch(cb)))` (:50465-50473). `_make_filter_cb` is at :50077.
- **One move:**
  1. `_on_filter_change` (:50426-50447): with a server session it calls `_dash_move_plan(True)` (:50107-50133: every target's mask, plus a mapper copy from `_dash_plan_mapper` :48828), bumps `_slot.gen`, submits `_dash_move_job(plan)` (:50415-50425) to `_dash_recompute_worker()` (:48775; `_DashRecomputeWorker.submit` :48740) and shows the "Updating..." cue (`Div` at :50608, no ARIA). Otherwise it calls `_dash_move_apply(plan, None)` inline.
  2. The worker runs `_dash_move_compute` (:50180-50194): `agg['redraw'](_dash_agg_frame(plan,key))` for each aggregate, and `_dash_kpi_value` for each KPI.
  3. `_dash_move_post` hands the result back (:50398, `IOLoop.add_callback`), and `_dash_move_finish` (:50379) runs on the next tick.
  4. `_dash_move_apply` (:50195-50378):
     - step 2 refreshes raw sources with `_dash_refresh_unlinked` per source and `_dash_refresh_linked` for the link group;
     - step 3 copies the fresh aggregate data onto the live sources;
     - step 3b runs `_dash_refinish_axes` (:32271);
     - step 4 sets KPI text through `_compute_kpi` (template :48654) and `_format_kpi` (:48675), then `_dash_kpi_card` (:48112).
- **Redraw lambdas.** `_dash_redraw_for` (:49267-49326) builds `_redraw(frame)`. It applies the graph qualifier, then the layer's own (`_dash_layer_frame`), draws on a throwaway figure through `_dash_draw_layer`, and returns the sources the mapper built. Registration (:49585-49604): **any layer whose mapper built its own source** goes into `agg_sources[(gname,pi)]`, so a new computed type is refit when served with no extra code. The saved page needs the JS twin.
- **Second axes.**
  - `_dash_add_secondary_axes` (:31720-31800ff) is called at saved :43792 and served :49446. It makes `extra_y_ranges['y2']`/`extra_x_ranges['x2']` from `_compute_secondary_range` (:11840).
  - `_dash_finish_secondary_axes` (:32581) is called at saved :44108 and served :49640. It fits the range to the drawn layers.
  - Neither `_dash_refinish_axes` (:32271-32301) nor `_DASH_AXIS_FINISH_JS` touches y2/x2 after a move (GAPS3 D9).

## 5. Test conventions

- **The WP-30 truth script.** test/test_wp30_truth.cscript (12,385 lines):
  - The header lists the blocks filled so far (:1-28).
  - Then `cscript "…" adodir ".."`, the timer, the `c(python_exec)` SKIP with exit 222, `do "cert_helpers.do"`, `do "cert_svg.do"`, the loading of `../dash_parse.mata` and `../dash.ado`, and `global dash_nobrowser 1` (:30-54).
  - Tally helpers `_w30_expect id cond msg` and `_w30_done id msg` (:56-84), and a private work directory made from a tempfile (:90-97).
  - The shard "parts" with per-block seconds (`w30_secs` :112-118) and Mata `_w30_part` (:146-189).
  - Each block has the form `* ==== S<NN> <id>: <name> ====`, then `local only : env WP30_ONLY` and `if inlist("`only'","","S<NN>") & `: list posof "S<NN>" in w30_run' {`, the `S<NN> start`/`end` display lines, and `* ==== end S<NN> ====`. Helpers go above the header. The S14 example is at :2991-3317.
  - The final marker `* ==== append new blocks above this line ====` and the summary (exit 9 on failure or when no case ran).
  - **Truth is measured live in the same run.** Examples: `quietly twoway bar y x1, name(bgt)` then `local bs = `.bgt.plotregion1.plot1.bar_size'` (:3176-3178); `capture twoway …` / `local trc=_rc` against `capture dash …` / `local drc=_rc` (:2973-2978, LN-27). Then `_dash_serve_spec, specpath() datapath()` and a `python:` helper that renders both modes.
  - **Registration.** test/run_all_cscripts.do: the shard table (:84-155, written by scripts/cert_shards.py; `* * *` means the script runs in every shard) and a block per script ("// 69." at :3077-3121). Pins: test_cscript_hygiene.py:299 (68 scripts), :319 (50), :328 (13 probes), `TestTheWp30TruthScript` (:1148); test_cert_shards.py:45 (68). A `test_wp31_truth.cscript` must move all of them.
- **cert_helpers.do.** `cert_file_has path, needle() [lower]` gives r(found) (:159). `cert_log_has` gives r(found) and r(count) with Stata's line wrapping undone (:182). `cert_file_count` (:203). `_hc_logged tag cmd` is **not** in cert_helpers.do. It is local to test/test_help_claims_1.cscript:224-238: it logs the command to `c(tmpdir)dash_hc1_<tag>.log` and returns r(rc) and r(logfile).
- **Extractors and fixtures.** Exemplar: scripts/extract_default_base_truth.do.
  - Header comment; `DASH_REPO` root with guards (:21-43); `adopath ++`, then load the mata and ado, then `global dash_nobrowser 1` (:45-48); a work directory in `c(tmpdir)`; `shell git rev-parse HEAD > file`, never `shell=True`.
  - Probe by class values; a `python:` block writes JSON with `"_meta":{"stata_version","born_date","dash_commit","extracted","source"}` (:181-183), `sort_keys`.
  - Run as `DASH_REPO=<repo> scripts/stata_slot.sh <scratch> <repo>/scripts/extract_X_truth.do`. Add the fixture with `git add -f`. test_fixtures_are_committed.py requires a test to name it.
- **`CORPUS` entry shape.** `_case(name, plots, bo, go, graphs, kpis, if_expr, in_expr, marks)` (test_mode_parity.py:1353) returns `pytest.param(name, spec, id=name)`. The spec comes from `_spec` (:177-204): `{"graphs":[{"name","graph_options","options","plots","if_expr","in_expr"}],"kpis":[…],"build_options":{layout,link,filter,…,"registry":…}}`. Example: `_case("rcap msize(large)", [plot_for("rcap", {"msize":"large"})])`.
- **`MOVE_CORPUS` entry shape.** `_move_case(name, move, plots, go, graphs, kpis, if_expr, bo)` (:2876) returns `pytest.param(name, spec, action, oracle)`, where `move` is an element of `_MOVES` (:2819-2826), e.g. `("dropdown to Foreign","foreign, type(dropdown)",("Select","Foreign"),"foreign == 1")`. Example: `_move_case("lfit, dropdown to Foreign", _MOVES[0], [plot_for("lfit")])`.
  - The move oracle is `_saved_with_qualifier` (:2802), i.e. the **Python saved renderer re-run with an `if`**, never the saved page's JS (GAPS3 H6). Served moves use `_served_after_move` (:2756).
  - `_MOVED_LAYERS` (:2837-2846) and `_EMPTIED_LAYERS` (:2858) expand per type.
- **FUNCTIONS map.** test/function_test_map.py keys are `co_qualname`s (`GlyphMapper.map_x`, `f.<locals>.g`, `app:<qualname>` for template-only functions; examples at :762, :1140). The value is one node id. `test_function_test_map.py` fails on a missing entry, a stale entry, a named test that does not exist, or a function only tests reach (keep it in `TEST_ONLY` with a reason). Ado programs and Mata functions go in test/program_coverage_map.py `COVERAGE` (:42ff) as `"script.cscript:CASE-ID"`. The WP-30 anchors remain at :299-320.
- **The tracking reader (GAPS2).** test/test_tracking_documents.py:725-799:
  - `_GAPS2_HEADING = ^### (?P<id>[A-NX]\d{1,2})\. (?P<title>\S.*)$`;
  - `_GAPS2_TRACKED = ^- \*\*Tracked:\*\* (?P<text>\S.*)$`;
  - `_GAPS2_CLOSED = ^Closed in (WP-\d{2}), BUGS\.md "([^"]+)", commit ([0-9a-f]{7,40})\b`;
  - `_GAPS2_DEFERRED = ^Deferred \((WP-\d{2})\): \S`.
  - `_parse_gaps2` returns `({id:{title,line,tracked,closed,deferred}}, dupes)`; the self-test is `test_the_gaps2_readers` (:1062).
  - The DROPIN P2 reader is `TestNoResidualNamesAClosedRow` (:500-528): rows `^(\d+)\. (.*)$` under a `### P2:` heading, where "Written closed" or "[Closed in" marks a closed row.
  - **GAPS3 rows are table rows (`| A1 | … |`) with no headings and no Tracked lines today**, so a GAPS3 reader needs a new line form. One option: a "Tracked" section with lines such as `- **A1 Tracked:** Closed in WP-31, BUGS.md "<title>", commit <sha>`, keyed by a table-ID regex like `^\| ([A-K]\d{1,2}) \|`.
  - The WP-30 machinery to mirror is `WP30_OPEN` (:1580), `WP30_LISTS` (:1588), `WP30_SECTION` (:1649), `_WP30_MARKER` and `_WP30_OPEN_FORM` (:1711-1714) and `TestWp30Tracking` (:1817). The release guard's allowance is `TestNoOpenEntryBlocksARelease::test_no_open_entry_is_s1_or_s2` (:548ff).
- **BUGS.md format.** Parsed by `_parse_bugs` (:122-176): the header `- [x] Title: …` or `- [ ] Title: …`, then exactly four fields in order (`File Names and Line Numbers`, `Description`, `Suggested fix`, `Resolution`), each starting `  - `, with continuation lines indented four spaces. An open entry's Resolution must carry exactly one `Graded S<n> (WP-NN): <why>`. The WP-30 open form was `Not fixed because WP-30 section NN has not landed. Graded S1|S2|S3 (WP-30): …`.

  One WP-30 entry, verbatim (BUGS.md:3020-3024):
  ```
  - [x] Title: bar and rbar default to 0.8 of the smallest x gap, rbar ignores barwidth() without a note, rcap caps ignore msize(), and rcapsym draws caps twoway does not
    - File Names and Line Numbers: dash_render.py at c96facd: GlyphMapper.map_bar (10122), GlyphMapper.map_rbar (13005), GlyphMapper.map_rcap (13153), GlyphMapper.map_rcapsym (13512), GlyphMapper._tag_spacing (10293), _dash_copy_redraw_geometry (24941)
    - Description: DROPIN-REMAINING.md:121-128 P1.17, the width and cap part, re-verified at c96facd: bar and rbar default to 0.8× the smallest x gap, not 1 x-unit; rbar ignores `barwidth()` with no note; rcap cap width ignores `msize()`, and rcapsym draws caps twoway does not. (WP-29 notes: barwidth() on a date axis is read in ms; P0.18 fixed the served redraw widths only.) Sources: GAPS2-A3-a, GAPS2-A3-b, GAPS2-A3-d, GAPS2-A3-e, AUDIT-44.
    - Suggested fix: WP-30 section 14 (Bar widths and range caps): draw bars one x-unit wide, honour rbar barwidth(), size rcap caps from msize() and draw rcapsym without caps, unchanged by filter moves in both modes.
    - Resolution: Fixed 07oct2026 (WP-30, P1.17a). GlyphMapper.map_bar and map_rbar draw each bar one x unit wide, ... Pinned by test/test_bar_range_geometry.py::TestBarIsOneXUnit::test_the_width_is_twoways, ..., test/test_wp30_truth.cscript BG-01, test/test_twoway_option_parity.cscript BG-07; fixture test/fixtures/bar_geometry_truth.json. Residual, deferred (WP-30): ... (P2.21). Closes GAPS2 A3 (WP-30, A3).
  ```
  (The Resolution is shortened here with "..."; the full text is at BUGS.md:3024.)

## 6. The WP-30 section-brief format

Files: .ultraplan-archive-20261010/wp30/index.md (1,120 lines), section-14-bar-widths-caps.md (656), decision-register.md, and BRIEF.md (.ultraplan-archive-20261010/sections/BRIEF.md, 88 lines).

- **index.md headings:** Overview · Decision record (Maintainer decisions M1-M12; Architect decisions A138-A156; Per-question rulings; Deltas from BRIEF.md; Execution conventions learned in WP-29 (E1-E12); Index reconciliations; Decisions for maintainer ratification) · Section manifest (a table: # / Section / Item / Batch / Depends on / Blocks / Risk / Effort / Case-id prefix) · P1 coverage · Batch execution order (step list k.0-k.5: impact at base → cut worktrees → run → land → G8 gate → close) · Batch 0..20 subsections · Test-writing rule · How to execute (0g queue script, 0a plan commit, per-entry cycle 1-7, landing routine 1-8, closeout S58.1-S58.7) · Full-suite runs · The cscript driver · Merge rules R1-R13 · Verification gates G0-G11 · Risk register.
- **Decision register:** per item, a table `| Id | Question | Ruling | Source | Why |` (e.g. P1.1.1). Source is an M decision or an A ruling. It also has a ratification list, strict readings, new P2 residuals and cross-cutting X rulings.
- **The truth-block spec** (index.md:94 and R1): the header `* ==== S<NN> P1.<n>: <name> ====`, the `WP30_ONLY` gate, start and end lines, helpers above the header, a second block only directly below your own, and the marker kept last. Refusal checks go to the area script, never to the truth script.
- **Merge rules R1-R13:**
  - R1: cscripts.
  - R2: served copy lists and maps appended at named anchors, with a per-section anchor table.
  - R3: help paragraph ownership, a table of help title, lines and sections.
  - R4: CHANGELOG markers replaced in place.
  - R5: BUGS.md and the tracking test.
  - R6: dash.ado, dash_setup.ado and dash_parse.mata (`_needed` is data; `version 19`).
  - R7: fixtures (`_meta`, never hand-patched).
  - R8: the parity corpus (append; `ALLOWED` never edited).
  - R9: pinned tests flipped with a `Flipped:` line, never deleted.
  - R10: combined pins and counts, `# old -> new: id why`, with a table of expected movers.
  - R11: axis finishers.
  - R12: one editor per batch of `_generate_app_source`, `_make_figure_body`, `_build_sources_and_figures`, `_build_filter_widgets` and the four appliers.
  - R13: GitNexus.
- **Section-file layout** (section-14): Review amendments · Overview (with a "Test order and commit rule" paragraph) · Section decisions D-14a.. · Risk ([colour] / Why / factors / Mitigation) · Dependencies · Evidence (measured values; the Blast radius table `Symbol | Risk | Note` from `gitnexus impact`; "Measured red list" from a simulated fix, as a node / today / after table) · User stories US-14.k · Business requirements BR-14.k · Technical requirements TR-14.k (exact functions, line ranges, code blocks to insert, copy-list anchors, map keys) · Boundaries · Stata truth (extractor, key/command/recorded table, measured values, truth-block cases BG-01..) · TDD test stubs (file::Class::test, red or guard) · Test plan (table plus AC-14.k) · Tasks (a "Commit boundary" paragraph, then XML tasks) · Section completion criteria · Notes (traps, R-rule citations, notes for the closeout).
- **The XML task schema** (BRIEF.md:17-29): `<task type="auto|checkpoint" id="NN-MM"><name>verb…</name><files>≤3 paths</files><action><![CDATA[…]]></action><verify><![CDATA[exact commands and expected output]]></verify><done>past tense</done></task>`.
- **What made the briefs executable:**
  - exact symbols and line anchors at a named base sha;
  - quoted measured truth with the commands that produced it;
  - every pinned test listed by node with its flip;
  - copy-list anchors;
  - verify lines with literal `grep -c` and pytest outputs;
  - fixed commit-message line forms;
  - boundaries naming the other sections' functions;
  - one commit per entry, with the failing test first and its failure text saved.

## 7. Dependencies: every place a new one such as scipy must be declared

1. **dash_setup.ado:**
   - `local min_bokeh/max_bokeh/min_numpy/min_pandas` (:57-60);
   - `pkg_list "bokeh numpy pandas"` (:312);
   - the import check loop `foreach m in packaging bokeh numpy pandas` (:210);
   - the ceiling special case (:326, :380, :398);
   - `_dash_setup_venv` takes the minimums positionally (:183; program :1176);
   - `_dash_pip_command` (:747) and `_dash_setup_gate` (:896, packaging-based);
   - the header comment (:7-8).
2. **dash_setup_lib.py:** `VERIFY_CODE`'s package loop `('packaging','bokeh','numpy','pandas')` (:101); the `mins` dict (:769-772); the venv pip list (:819-821); `_SPEC_RE` (:33).
3. **dash.ado** `_dash_require_deps` (:338-382): the find_spec list `("numpy","pandas","bokeh")` at :373.
4. **dash_render.py:**
   - module-scope imports guarded by `_dash_dep_fail` (:92, imports :136-181);
   - `_DASH_MIN_PACKAGES` (:186) and `_dash_dep_versions` (:189);
   - the module docstring's Dependencies section (:55-60);
   - **the served header's own guarded imports** (:48005-48035, which carries a comment "No scipy and no statsmodels").

   A lazily imported scipy inside one estimator would avoid the module-scope guard.
5. **dash.pkg** "Requires: Python 3.11+, bokeh>=3.8,<3.10, numpy>=2.3, pandas>=2.3." (test_version_floor.py:91-93 asserts this exact string).
6. **dash.sthlp:** Dependencies (:5136ff): "Python packages, required" and "optional -- none … no longer use scipy" (:5164-5168), plus :3167. **dash_setup.sthlp:** :102, :151-156 ("Nothing else is needed. Earlier versions listed scipy"), :165-191, :280-286.
7. **Requirements and baselines.** test/requirements-stata.txt and requirements-dev.txt already pin scipy (1.16.3 / 1.17.1). conftest `_BASELINES` (:556-569) and `_running_env` (:583) already track scipy. scripts/floor_matrix.sh:79,107 already install it.
8. **Pins that assert scipy is absent, and must be flipped:**
   - test_version_floor.py:85-119 (pkg, help and CHANGELOG Requirements strings) and :450 (`_DASH_MIN_PACKAGES`);
   - test_help_claims_6.py:1235-1255;
   - test_help_claims_8.py:368-569 ("no layer imports scipy");
   - test_server_optional_deps.py:149-214;
   - test_dependency_guards.py (the per-type no-scipy guards; :575 requires every unguarded top-level import to be the standard library; :594 for the served guard);
   - CHANGELOG "### Requirements".

## 8. Accessibility and widgets today

- **The saved shell.**
  - `_assemble_layout` (:45939) routes `layout(bs)` to `_render_bootstrap_html`, which hashes Bokeh's `components()` scripts at :44466-44472 and writes the head at :44591, sealing at :44606. Otherwise `file_html` is used and hashed at :46125-46139.
  - The header is `_dash_header_models` (:36433, shared).
  - Grid cells come from `_dash_layout_cell` (:35899, shared, on the copy list), `_dash_tab_panels` (:36015) and `_dash_bs_grid` (:36342).
- **KPI cards.** `_dash_kpi_card_html` (:22900-22957, shared) produces `div.db-kpi-card` with no role or aria. `_make_kpi_div` (:44248) wraps it with `disable_math=True` and an `InlineStyleSheet`. The served copy is `_dash_kpi_card` (template :48112); it is rebuilt after moves at :50378.
- **Filter widgets.** `_build_filter_widgets` (:45427) calls `FilterBuilder.build_dropdown/slider/range` (:25525/:25628/:25692). These call the shared `_dash_filter_widget` (:34566), which uses Bokeh `Select`/`Slider`/`RangeSlider`/`Date*Slider` with `title=` from `_dash_filter_title` (:34491; slider titles pass through `_dash_inert_tex`). The served twin is :50001-50015.
- **ARIA.** The only `role`/`aria` markup is `_DASH_STALE_STATUS_HTML` (:1905-1910). The served "Updating..." `Div` (:50608) has none.
- **CSP.**
  - Policies: `_DASH_CSP_STANDALONE` (:4620), `_DASH_CSP_SERVED` (:4641), `_DASH_CSP_SERVED_META` (:4660), `_DASH_CSP_NO_SCRIPTS` (:4685).
  - Helpers: `_dash_csp_meta` (:4688), `_dash_script_hashes` (:4722), `_dash_csp_standalone` (:4794), `_dash_saved_head` (:4830), `_dash_seal_saved_page` (:4843-4885), `_dash_new_nonce` (:4888), `_dash_csp_served` (:4902), `_dash_nonce_scripts` (:4929), `_dash_served_template` (:4967), `_dash_unsigned_scripts` (:5057).
  - Saved pages allow only scripts whose hash is taken **before** dash splices its own HTML, so a new dash-authored inline `<script>` would make the seal refuse the page. New behaviour must be a Bokeh `CustomJS` (allowed by `'unsafe-eval'`), e.g. `doc.js_on_event("document_ready", …)` as `_dash_by_stack_hooks` does (:44448-44464), or an `InlineStyleSheet`. Inline styles are allowed (`style-src 'unsafe-inline'`).
- **The headless-Chrome harness.**
  - test/test_csp_browser.py (`pytestmark = pytest.mark.release`, :57). `_CspProbe` (:183-276) launches `chrome --headless=new --remote-debugging-port --user-data-dir=<tmp> --window-size=1400,1000` and drives it over DevTools: a listener added by `Page.addScriptToEvaluateOnNewDocument`, then `Runtime.evaluate`; it reads `violations()`, `js_errors()` and `read(js)`, and has `in_task()` and `wait_change()`. Chrome comes from `responsive_probe.find_chrome()` (:123; `DASH_CHROME` first). The module skips without Chrome, which is red under `DASH_STRICT=1`.
  - test/test_stale_cue_browser.py runs `chrome --headless=new --virtual-time-budget=9000 --dump-dom file://page.html` (:130-162) and parses a `<pre id="r">` the probe writes.
  - Probe scripts go in through `responsive_probe.admit_script` (:142), which adds a nonce or a sha256 to the policy. This is how an automated accessibility checker script could be injected.

## 9. The CSV download and the hover export

- **`_dash_csv_meta`** (:23223-23271) returns `{columns (minus __dash_row__), strings, dates{var:kind}, labels{var:{code:label}}, storage{var:type}, filename, headers?}`.
- **`_dash_csv_payload`** (:23274-23298) returns the served rows, JSON-safe; strings through `_dash_csv_text_value`, dates through `_stata_dates_to_datetime` and `_dash_json_value`.
- **`_DASH_CSV_JS`** (:24397-24464) has `dash_csv_cell`. It writes **raw** numbers (shortest float, float32 for float storage), ISO dates and value labels, **not Stata display formats**.
- **The two download scripts.** `_DASH_CSV_SAVED_JS` (:24603) masks `orig_source` with `dash_filter_mask`; `_DASH_CSV_SERVED_JS` (:24475). The saved button is `_csv_button` (:45901-45937). The column rule is every dataset column.
- **Hover formatting.**
  - `_dash_hover_row` (:40023) formats one tooltip row in the Stata display format, through `_dash_fmt_hover` (:27986), a CustomJSHover running `_DASH_FMT_JS`'s `dash_fmt`.
  - Value labels come from `_dash_add_hover_text` and `_dash_hover_text_column` (`__dash_hover_<var>`, :39983-40020).
  - `_dash_hover_layer_vars` (:40053) gives each layer's plotted variables.
  - `_dash_build_hover` (:40081) builds the one tool per figure, with `hover()` extras.
  - `GlyphMapper._carry_cols` (:12387-12423) copies the caller's extra columns (hover, mlabel, row id) into derived sources, so the drawn rows carry those values and their row identity.
- **For a per-graph data table:**
  - **Columns:** `_dash_hover_layer_vars(plot)` plus the `hover()` variables. Display text comes from Python `_dash_fmt` / `_dash_fmt_text` and from `_dash_value_labels_for`; the JS twin is `dash_fmt_text` (:24340). Headers can come from `_dash_csv_meta`'s `headers` and `labels`.
  - **Rows:** the drawn sources' `__dash_row__` ids.
  - **Where to attach:** no `DataTable` exists anywhere today. bokeh 3.9 here does have `DataTable` and `TableColumn` (checked with an import probe; `bokeh-tables` is already inlined in the saved page, :4939). The single shared place to add a `column(fig, toggle, DataTable)` for both modes is `_dash_layout_cell` (:35899), which the saved grid, the saved tabs and the served app (template :50633, :50647) all call. Its source must be refreshed in the saved `_FILTER_JS` derived-copy loop and in the served `_dash_move_apply` step 2.
