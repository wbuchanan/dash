# Section 07: Weight expressions, operators in option varlists, hover() merge, y date literals

> Part of: WP-31 · GAPS3 rows: A5, A6, A7, A8 · Risk: yellow · Batch: 2 · Depends on: 01 · Blocks: -- · Tasks: 4, 4 commits · Case-id prefix: U07

## Overview

**What is wrong today.** Four command-syntax gaps, all in dash.ado's registration path, all pasted-command failures:

- **A5** (GAPS3 4.A): "Weight expressions `[aw=price+1]` and `[aw=L.x]` refused; twoway takes an expression." Evidence dash.ado:5402-5425: the weight must `confirm name` and `unab` to exactly one variable, else `dash: [aweight=price+1] must name one variable; dash cannot evaluate a weight expression.` r(198). twoway evaluates the expression itself (`twoway_yxview_parse.class:185`, `[aw fw pw]`; the serset carries the evaluated weight, `yxview_parse:851-861`).
- **A6**: "Option varlists with operators: `mlabel(L.make)`, `colorvar(L.mpg)`, `by(L.foreign)` are refused r(198); twoway r(111)/r(101) or draws." Evidence dash.ado:3471-3479 (`_dash_validate_value`, kinds `var varlist byvarlist`): a head `unab` refuses and `tsrevar ..., list` accepts is refused as `dash: mlabel() must name a variable, not a time-series expression (got: L.make)` r(198).
- **A7**: "`hover()` written inside a layer's parentheses and again after the comma keeps only the rightmost list." Evidence dash.ado:1085 (graph parser `sreturn local hover`), :1571 (plot parser `g_hover`); the merge at :6956-6968 runs `_dash_rep_merge_locals("hover", g_hover, _gafter_hover)` and `_dash_rep_cat("hover")` (dash_parse.mata:6166-6190) returns `"R"`, "the last copy".
- **A8**: "Date literals in y-options (`ylabel(2000m1)`) accepted; twoway r(198)." Evidence dash.ado:7544-7556: the refusal loop in `_dash_taxis_fold` runs over `xlabel:1 xtick:1 xmlabel:1 xmtick:1 xlabel2:1 xtick2:1 xscale:3 xscale2:3` only, and the `dash__tf_` globals it reads are set for x and t keys only (:7001-7004).

**After this section.** A weight expression is evaluated by Stata at export into a reserved column `__dashw<k>` (one per distinct expression), exactly as time-series expressions in plot varlists become `__dasht<k>` through `_dash_tsop_gen` (dash.ado:6540-6584); `[aw=L.x]` goes through that same time-series route. An operator in `mlabel()`, `colorvar()` or `by()` is drawn where twoway draws it (the column made at export) and refused with twoway's measured rc and words where twoway refuses it. Two `hover()` lists are merged, duplicates dropped, in the order written. A date literal in a y label, tick or scale option is refused with the words twoway prints for it. The four rows share this section because all four are registration-time grammar in `_dash_process_segment`, `_dash_validate_value` and `_dash_taxis_fold`, and A5/A6 share one new helper.

**Test order and commit rule (rule 7, M6).** Four rows, four commits `(WP-31 A5)`, `(WP-31 A6)`, `(WP-31 A7)`, `(WP-31 A8)`, in that order, each made by the task that closes the row: 07-01 writes the extractor, the fixture and every regression test (red at 6370ca4) and never commits; 07-02 lands A5; 07-03 lands A6; 07-04 lands A7 and A8. Each row's failing tests are run again against the tree the previous commit leaves before its fix is written. No test-only commit exists.

### Section decisions (binding on the executor)

- **D-07.a A weight expression is a `generate`, never an `eval`.** At export `_dash_wexp_gen` runs `quietly generate double __dashw<k> = (<expression>)` under `capture`, copying Stata's own rc and message (r(111) "variable x not found", r(198) for a malformed expression, as `generate` itself says them; twoway's words are Stata's, measured in 07-01). Before the `generate` the text passes `_dash_wexp_ok` (Mata): no backtick, dollar sign, double quote, semicolon, newline or tab; at most 512 bytes; else r(198) `dash: [aweight=<expr>] cannot be evaluated` (the expression echoed through `_dash_say`). Stata's `syntax [weight]` has already read the text as an expression, so nothing but an expression reaches `generate`, and the four excluded characters make macro expansion and command splicing impossible (rule 1).
- **D-07.b One registry per column family.** Expressions that are a canonical time-series term (`_dash_tsop_canon`, dash_parse.mata:4015: `L.x`, `D2.x`) take the existing `__dasht<k>` route by adding `"wexp"` to `_dash_tsop_rewrite`'s key list (:4071); every other expression that is not a bare variable name takes the new `__dashw<k>` route (`_dash_wexp_*`, mirroring `_dash_tsop_*`). A bare variable name is unchanged (`unab`, today's path).
- **D-07.c An option variable with an operator is routed only where twoway draws.** 07-01 measures twoway on `mlabel(L.make)`, `mlabel(L.rep78)`, `colorvar(L.mpg)`, `by(L.foreign)`, `mlabvposition(L.pos)` and `hover()` has no twoway twin. For each form twoway draws (rc 0), `_dash_validate_value` keeps the canonical term as the value and `_dash_tsop_rewrite` gains that option key (`mlabel`, `colorvar`, `mlabvposition`, `by`) in **word mode**: each blank-separated word of the value holding a dot is rewritten to its `__dasht<k>` column; for a form twoway refuses, dash prints twoway's measured line and returns its rc, through the fixture's `operators.<form>.rc` and `.text` fields, never a guess.
- **D-07.d hover() is category "H".** `_dash_rep_cat("hover")` returns `"H"`; `_dash_rep_merge` returns `v1 + " " + v2` for `"H"` (blank-joined, trimmed). Duplicates are dropped where the words are read (`_dash_extract_hover_vars`, dash_parse.mata:2914-2951, already keeps a `seen` set), so the merged text needs no dedup of its own.
- **D-07.e y date literals are refused in the x loop's form.** The y keys join the `dash__tf_` round trip (:7001-7004, :7010-7013) and a second loop runs over `ylabel:1 ytick:1 ymlabel:1 ymtick:1 ylabel2:1 ytick2:1 yscale:3 yscale2:3`, with the sentence the fixture holds for the y form. If 07-01 measures that twoway reads a date literal on a `%t`-formatted y variable (rc 0), that case is NOT refused: it is filed as a residual (M12) with an open BUGS.md entry, and the refusal applies only where twoway refuses.

## Risk: [yellow] -- new columns generated in the user's data at export; four refusal texts measured, not guessed

**Why.** `generate` on the user's dataset (r(900) possible at `c(maxvar)`, GAPS3 G3 already notes this for `__dasht`), a new expression sink, and three parsers edited (`_dash_process_segment`, `_dash_validate_value`, `_dash_taxis_fold`).

**Risk factors.**
1. The expression text is user text reaching a Stata command line once (`generate`).
2. The weight column must reach the renderer under the same `wexp` key it reads today (dash_render.py:18023, :18392, :22011) and `_DASH_OPT_VAR_KEYS` (:36465) lists `wexp` as a variable key.
3. An operator word inside `mlabel()`'s stylelist (`mlabel(make L.make)`) must be rewritten per word without touching quoted elements.
4. Each refusal text is twoway's and lives in compiled `syntax`: it must be measured.
5. Parallel batch 2 partners S05 and S06 edit `_dash_option_rules`; S07 does not (R12).

**Mitigation.**
1. D-07.a's character gate plus `capture`; the test `test_a_hostile_weight_text_never_runs` feeds a backtick, a `$`, a `;` and a quote.
2. `_dash_wexp_gen` writes the column name into the spec's `wexp` at export exactly as `_dash_tsop_rewrite` writes `__dasht<k>` into plot keys; `test_the_renderer_reads_the_column` checks `_dash_agg_config["wvar"]`.
3. Word mode skips words beginning with `"` or `` ` ``; `test_quoted_elements_are_not_rewritten`.
4. `scripts/extract_weight_operator_truth.do` writes `test/fixtures/weight_operator_truth.json`; every message dash prints is copied from it.
5. S07 touches none of the rules table, the appliers, `_FILTER_JS` or the template.

## Dependencies

- **Depends on: 01** (BUGS.md entries A5-A8 open, GAPS3 Tracked lines, CHANGELOG markers, `test/test_wp31_truth.cscript` with its `// 70.` registration).
- **Blocks: --.**
- **Parallel batch: 2** with S05 and S06 (both `_dash_option_rules` editors; S07 is batch 2's `dash.ado parsers` owner per the index). Can run with both: S05/S06 edit `_dash_option_rules`, `_dash_validate_value`'s numeric kinds and `_dash_mlabel_list`'s element count; S07 edits `_dash_validate_value`'s `var`/`varlist`/`byvarlist` branch only (:3457-3479), `_dash_process_segment` :5399-5422, `_dash_taxis_fold` :7544-7556, the `dash__tf_` lists, `_dash_rep_cat`/`_dash_rep_merge`, `_dash_tsop_rewrite` and new programs. S06's `mlabel()` several-variables work touches `_dash_mlabel_list` (:3712-3760), not the `var` branch.

## Evidence

Anchors at `6370ca4` (dash.ado 11,039 lines; dash_parse.mata 9,789; dash_render.py 52,280).

### A5 -- the weight gate, dash.ado:5399-5422

```stata
5399    if `"`_seg_weight'"' != "" & `: list ptype in _wt_honoured' {
5410        local _wx ""
5411        capture confirm name `macval(_seg_wexp)'
5412        if !_rc {
5413            capture unab _wx : `macval(_seg_wexp)'
5414        }
5415        if _rc | `: word count `_wx'' != 1 {
5418            mata: _dash_say("err", "dash: [`_seg_weight'=", st_local("_seg_wexp"), "] must name one variable; dash cannot evaluate a weight expression.")
5419            mata: _dash_say("err", "      Generate it first: generate double w = ", st_local("_seg_wexp"), "")
5420            exit 198
5421        }
5422        local _seg_wexp "`_wx'"
```

`_wt_honoured` is `lfit qfit lfitci qfitci lpoly lpolyci fpfit fpfitci histogram kdensity mspline mband` (:5367). The weight reaches s() through `_dash_seg_weight_s` (:4487-4492) at :5580, the spec's `"weight"`/`"wexp"` keys through `_dash_plot_opts_to_json` (:4441-4458, last two keys), and the export's variable list as `_seg_wvar_out` (:5901). The renderer reads `options["wexp"]` as a column name at dash_render.py:18023 (histogram `wvar`), :18392 (kdensity) and :22011 (`_dash_wls`); `_DASH_OPT_VAR_KEYS = ("colorvar", "mlabel", "mlabvposition", "wexp")` (:36465).

### The time-series route to copy, dash.ado:6540-6584 and dash_parse.mata:4000-4135

`_dash_tsop_gen cmdname` (:6540): `_dash_tsop_export()` puts the registry's expressions in `_dts_e1..` and their count in `_dts_n`; refuses a user variable named `__dasht*` r(110) (:6553-6559); per expression checks `_dash_tsop_canon` (:6562), runs `capture noisily tsrevar` (:6568), `generate <type> __dasht<k> = <r(varlist)>` (:6575), copies the base variable's format and value label (:6578-6581); hands the names back in `c_local _dash_tsop_vars`. Its callers: export at :9133 (after `_dash_qual_gen`, `_dash_sort_gen`; the data writer at :9147 takes `_dash_tsop_vars`; the columns are dropped at :9150), the registry rewrite at :8899-8906 and :10040 (`_dash_tsop_rewrite`, keys `yvar xvar yvar1 yvar2 y1var x1var y2var x2var`, dash_parse.mata:4071: "never an option's variable"), and `_dash_tsop_meta` (:9090) writing `"ts_cols"`. `_dash_tsop_reset` (:4001) clears the external `_dash_tsop_list`.

### A6 -- the operator refusal, dash.ado:3457-3479

```stata
3457        local vv ""
3458        capture unab vv : `macval(head)'
3459        if _rc {
3460            capture tsrevar `macval(head)', list
3461            local ists = (_rc == 0)
3472                        if regexm(scalar(`K'), "^[LlFfDdSs][LlFfDdSs0-9()/]*\.[A-Za-z_]") local tsop = 1
3477            if `ists' & `tsop' {
3478                mata: _dash_say("err", "`prefix': `opt'() must name a variable, not a time-series expression (got: ", st_local("value"), ")")
3479                exit 198
```

(The `regexm` at :3472 follows the caller's version, project memory; the fix reads the token through `_dash_tsop_canon` instead.) Kinds reaching this branch: `colorvar=var mlabel=var` (:3005), `hover=varlist by=byvarlist` (:3047); `mlabvposition` goes through `_dash_mlabv_parse` (:2120ff).

### A7 -- hover() merge

Graph parser `HOVer(string)` :946, `sreturn local hover` :1085; plot parser `HOVer(string)` :1219, `sreturn local g_hover` :1571. Segment hand-back `_sg_hover` (list :5781), accumulators :6719, after-comma capture :6753 (`_gafter_hover`), per-segment reset :6854, merge :6929, after-comma merge :6961 (`_dash_rep_merge_locals`), JSON :7344. `_dash_rep_merge` (dash_parse.mata:8838): `if (cat == "R" | strtrim(v1) == "") return(v2)`. Readers of the merged text: `_dash_extract_hover_vars` (:2914-2951; `_dash_blank_words`, a `seen` asarray, r(111)/r(198) through dash.ado:8948-8955), `_dash_build_hover` (dash_render.py:40081). test_option_validation.cscript OV-110 pins `"hover":"price weight"` for `hover(pri wei)`.

### A8 -- the x-only refusal loop, dash.ado:7544-7556, and `_dash_xdate_find`, dash_parse.mata:7632-7665

```stata
7544    foreach c in xlabel:1 xtick:1 xmlabel:1 xmtick:1 xlabel2:1 xtick2:1 xscale:3 xscale2:3 {
7547        mata: st_local("_tf_hit", strofreal(_dash_xdate_find(st_global("dash__tf_`k'"), `f')))
7549            if `f' == 3 {
7550                display as error "range() invalid -- invalid numlist"
7551                exit 121
7553            mata: _dash_say("err", "invalid label specifier, :  ", st_local("_xd_tok"), ":")
7554            exit 198
```

The globals are written at :7001-7004 for `name xlabel xtick xmlabel xmtick xline xscale xtitle xlabel2 xtick2 xline2 xscale2 xtitle2 tlabel ... ttitle2` and read back at :7010-7013; `capture macro drop dash__tf_*` at :7016. The measured x words come from test/fixtures/taxis_truth.json c11, c13 (comment :7496-7498). `yline()` date literals are `_dash_line_check`'s (:7669; c12) and are not this section's.

### Pinned tests that assert today's behaviour (flip, never delete; R9)

| Node | Today | After |
|---|---|---|
| test/test_option_validation.cscript OV-111 (`hover(nosuchvar)` r(111) naming hover()) | unchanged (guard) | unchanged |
| test/test_adversarial.cscript, test/test_abbreviations.cscript `hover` cases | grep in 07-01: `grep -n "hover(" test/*.cscript`; any case asserting the rightmost-wins text is flipped to the merged list | merged list |
| test/fixtures/stat_truth.json `weight_acceptance` readers (test/test_weights*.py; `grep -ln "must name one variable" test/`) | assert the r(198) "cannot evaluate a weight expression" text | assert the column is made and the fit matches `[aw=exp]` |
| test/fixtures/rejected_options.json rows for `mlabel(L.` / `colorvar(L.` if any (`grep -n '"L\.' test/fixtures/rejected_options.json`) | dash r(198) | twoway's rc |

07-01 lists every node it flips in `<scratch>/s07/07-flips.txt`; the grep results are the authority, not this table.

## User stories

- **US-07.1** As a twoway user, I want `dash lfit mpg weight [aw=price+1]` and `[aw=L.price]` to fit as twoway fits them, so a pasted weighted command runs unchanged.
- **US-07.2** As a twoway user, I want `scatter mpg weight, mlabel(L.make)` drawn where twoway draws it and refused with twoway's words where twoway refuses it.
- **US-07.3** As a dashboard publisher, I want `(scatter mpg weight, hover(make)) , hover(price)` to show both make and price in the tooltip.
- **US-07.4** As a twoway user, I want `ylabel(2000m1)` refused as twoway refuses it, so a do-file that fails in Stata does not silently draw in dash.

## Business requirements

- **BR-07.1** On every type of `_wt_honoured`, `[aw|fw|pw=<expression>]` is accepted whenever Stata's `generate double w = <expression>` succeeds, and the layer's fit, histogram or density equals twoway's weighted result (fixture `weights.<case>`), in both modes; a refused expression prints Stata's own line and rc.
- **BR-07.2** `[aw=L.x]` behaves as `[aw=w]` with `w = L.x` generated first; `[aw=price+1]` as with `w = price+1`.
- **BR-07.3** A weight text holding a backtick, dollar sign, quote, semicolon or line break is refused r(198) and nothing is generated.
- **BR-07.4** `mlabel()`, `colorvar()`, `mlabvposition()` and `by()` with a time-series term draw where twoway draws (fixture `operators.<form>.rc == 0`), with the operated values, in both modes, and otherwise return twoway's rc and line.
- **BR-07.5** `hover()` given in a segment and after the comma shows every variable of both lists, in the order written, once each.
- **BR-07.6** `ylabel() ytick() ymlabel() ymtick()` (and `*2`) with a date literal in a position slot are refused with twoway's line and r(198); `yscale(range(<date>))` with r(121) and twoway's line; where twoway accepts the form (D-07.e) dash accepts it.
- **BR-07.7** Nothing else is newly refused or newly accepted.

## Technical requirements

- **TR-07.1 `_dash_wexp_ok(e)`** (Mata, dash_parse.mata, directly after `_dash_tsop_meta`): returns 1 when `e` is non-empty, `strlen(e) <= 512` and `ascii(e)` holds none of 96 (backtick), 36 (`$`), 34 (`"`), 59 (`;`), 10, 13, 9; else 0. Header-index entry after `_dash_tsop_meta`'s (:352): `_dash_wexp_ok(expr)` / "1 when a weight expression may reach generate (no backtick, $, quote, ;, line break; 512 bytes)". Added to `_dash_require_mata`'s `_needed` (dash.ado:458 line, after `_dash_tsop_meta`) and to test/program_coverage_map.py `COVERAGE["dash_parse.mata"]` under a new anchor `# WP-31 S07 (A5): weight expressions`.
- **TR-07.2 Registration (A5).** Replace dash.ado:5410-5422 with: `confirm name` + `unab` as today; if that yields one name, keep it. Else if `_dash_tsop_canon(wexp)` is 1, keep the canonical term as `_seg_wexp` (the export rewrites it, TR-07.4). Else if `_dash_wexp_ok(wexp)` is 0: `_dash_say("err", "dash: [`_seg_weight'=", wexp, "] cannot be evaluated")`, `exit 198`. Else run `tempvar _wt; capture quietly generate double `_wt' = (<wexp>)` through a string scalar (`mata: st_local("_wexp_cmd", ...)` building `generate double <tempvar> = (` + expr + `)`), on failure `exit _rc` after `display as error` of Stata's own message captured via `capture noisily` into a log the way `_p1a_logrun` does (test_parser.cscript:263-290) -- simpler: run `capture noisily generate double `_wt' = (`macval(_seg_wexp)')` directly; Stata prints its own message; `if _rc { drop `_wt' if made; exit _rc }`; then `drop `_wt'` and keep `_seg_wexp` as the expression text. The spec's `"wexp"` carries the expression as typed.
- **TR-07.3 Export (A5): `_dash_wexp_gen cmdname`** (new dash.ado program directly after `_dash_tsop_gen`, `version 19`), the twin of `_dash_tsop_gen`: Mata `_dash_wexp_export()` (new; twin of `_dash_tsop_export`, external `_dash_wexp_list`, `_dash_wexp_reset()`) fills `_dwx_e1..`, `_dwx_n`; refuses a user `__dashw*` variable r(110) with the `_dash_tsop_gen` sentence (:6555-6556) extended to name `__dashw#` ("its weight columns __dashw#" after "its time-series columns __dasht#"); per expression: `_dash_wexp_ok` else r(198); `capture noisily generate double __dashw<k> = (<expr>)`; on failure drop what was made and `exit _rc`; `c_local _dash_wexp_vars`. The spec rewrite: Mata `_dash_wexp_rewrite(json, errmacro)` (twin of `_dash_tsop_rewrite` over the one key `"wexp"`: a value that is not a bare variable name in memory and not `_dash_tsop_canon` is added to `_dash_wexp_list` and replaced by `__dashw<k>`). Call sites mirror `_dash_tsop_*`: reset+rewrite at :8899-8906 and :10040, `_dash_wexp_gen "dash"` directly after `_dash_tsop_gen "dash"` at :9133 (drop list at :9139 and :9147-9150 gains `_dash_wexp_vars`), the `needed_vars` subtraction at :8917 gains the `__dashw` names, `_dash_cell_cap` at :9075 adds `_dwx_n`. `_dash_require_mata` `_needed` gains `_dash_wexp_reset _dash_wexp_rewrite _dash_wexp_export` after the `_dash_tsop_*` names. Header-index entries after `_dash_tsop_meta`'s.
- **TR-07.4 `[aw=L.x]` (A5, D-07.b).** dash_parse.mata:4071 `keys = ("yvar", ..., "x2var", "wexp")`. Nothing else: `_dash_tsop_gen` makes the column, `_dash_tsop_meta` records it in `ts_cols`.
- **TR-07.5 Operators in option varlists (A6, D-07.c).** In `_dash_validate_value` (:3457-3479): when `unab` refuses and `ists` is 1, test each blank-separated word of `head` (outside quotes, as :3467-3475 iterates `head`) with `mata: st_local("_can", strofreal(_dash_tsop_canon(...)))`; if every word is a variable or a canonical term AND the fixture says twoway draws this option (`local _ts_drawn "mlabel colorvar mlabvposition by"` filtered by 07-01's measurement; a local `_dash_tsop_opts` set from the fixture's rc-0 forms, written as a literal list in the code with the fixture key named in its comment), set `norm` to the head as typed and skip the r(198); else refuse with the fixture's text for that option (`operators.<opt>_L.text`) and its rc. `_dash_tsop_rewrite` (:4071) gains **word mode**: a second key list `wkeys = ("mlabel", "colorvar", "mlabvposition", "by")`; for a value under one of these keys, each blank-separated word (split by `_dash_blank_words`; a word beginning with 34 or 96 is kept) holding a dot and passing `_dash_tsop_canon` is replaced by its column; `by`'s value is split at its first top-level comma first (the head only). `_dash_extract_vars`, `_dash_extract_qual_vars` and `_dash_extract_hover_vars` read the rewritten spec, so no change there. The renderer draws `__dasht<k>` as it draws any column; its label text comes from `ts_cols` (dash_render.py reads `ts_cols` for axis titles: `grep -n ts_cols dash_render.py` in 07-03 and reuse the same lookup for the mlabel LabelSet column name and the colorvar legend title).
- **TR-07.6 hover() merge (A7, D-07.d).** dash_parse.mata `_dash_rep_cat`: add `if (k == "hover") return("H")` before `return("R")` (:6189). `_dash_rep_merge` (:8838): after the `"A"` line add `if (cat == "H") return(strtrim(v1) + " " + strtrim(v2))`. Comment at :6160-6165 gains `"H" hover() (the lists joined, blank-separated)`.
- **TR-07.7 y date literals (A8, D-07.e).** dash.ado: the `foreach _tk in name xlabel ...` lists at :7001 and :7010 gain `ylabel ytick ymlabel ymtick ylabel2 ytick2 yscale yscale2`; in `_dash_taxis_fold` after the x loop (:7556) a second loop `foreach c in ylabel:1 ytick:1 ymlabel:1 ymtick:1 ylabel2:1 ytick2:1 yscale:3 yscale2:3` with the same body, its sentence read from the fixture's `ydates.ylabel.text` (expected `invalid label specifier, :  2000m1:`; copied as measured, through `_dash_say` with the token as the middle argument). If the fixture records rc 0 for the `%t`-formatted-y case, that case's key is excluded by `_dash_xdate_find`'s caller testing the y variable's format first: `_dash_axis_fmts` (Mata, `_needed` :471) gives the first y variable's format; refuse only when it is not a `%t`/`%d` format OR the fixture's `ydates.ylabel_tfmt.rc` is 198.
- **TR-07.8 Maps (R2 n/a; A7 of index).** No dash_render.py module helper is added, so no copy-list entry. test/program_coverage_map.py: `_dash_wexp_gen` under `COVERAGE["dash.ado"]` (`"test_wp31_truth.cscript:U07-1"`), `_dash_wexp_ok`, `_dash_wexp_reset`, `_dash_wexp_rewrite`, `_dash_wexp_export` under `COVERAGE["dash_parse.mata"]`. test/test_unsupported_report_is_true.py: no declaration changes.
- **TR-07.9 Security (rule 1).** The only new command-line sink is `generate double __dashw<k> = (<expr>)` behind `_dash_wexp_ok` and `capture`; the expression is also stored in the spec and echoed only through `_dash_say`; `__dashw` joins the reserved-prefix refusal at :6553-6559 (and dash.ado's registration-time reserved-name refusal, `grep -n "__dash" dash.ado | grep -n "reserved"`). No `shell`, no `eval`, no Python change.

### Code to insert (verbatim where marked; line anchors re-read before editing)

**TR-07.1 `_dash_wexp_ok` (dash_parse.mata, after `_dash_tsop_meta`; verbatim):**

```mata
// _dash_wexp_ok(e) -- 1 when a weight expression may reach generate: not
// empty, at most 512 bytes, and holding no backtick, dollar sign, double
// quote, semicolon, tab or line break (WP-31 A5, D-07.a).  Read byte by
// byte: no regex (regexm follows the caller's version).
real scalar _dash_wexp_ok(string scalar e)
{
    real rowvector b
    real scalar    i

    if (strlen(e) == 0 | strlen(e) > 512) return(0)
    b = ascii(e)
    for (i = 1; i <= cols(b); i++) {
        if (b[i] == 96 | b[i] == 36 | b[i] == 34 | b[i] == 59 |
            b[i] == 9 | b[i] == 10 | b[i] == 13) return(0)
    }
    return(1)
}
```

**TR-07.2 the registration gate (dash.ado, replaces :5410-5422; the surrounding `if` at :5399 stays):**

```stata
        local _wx ""
        capture confirm name `macval(_seg_wexp)'
        if !_rc {
            capture unab _wx : `macval(_seg_wexp)'
        }
        if !_rc & `: word count `_wx'' == 1 {
            local _seg_wexp "`_wx'"
        }
        else {
            // An expression (WP-31 A5): a time-series term takes the
            // __dasht route at export; anything else is generated into
            // __dashw<k> there (_dash_wexp_gen).  Checked now so a bad
            // expression is refused at registration, with Stata's words.
            mata: st_local("_wcan", strofreal(_dash_tsop_canon(st_local("_seg_wexp"))))
            if !`_wcan' {
                mata: st_local("_wok", strofreal(_dash_wexp_ok(st_local("_seg_wexp"))))
                if !`_wok' {
                    mata: _dash_say("err", "dash: [`_seg_weight'=", st_local("_seg_wexp"), "] cannot be evaluated")
                    exit 198
                }
                tempvar _wt
                capture noisily generate double `_wt' = (`macval(_seg_wexp)')
                if _rc exit _rc
                capture drop `_wt'
            }
        }
```

**TR-07.3 `_dash_wexp_gen` (dash.ado, after `_dash_tsop_gen`'s `end` at :6584; skeleton -- the executor copies `_dash_tsop_gen`'s reserved-prefix block :6553-6559 with `__dashw*`):**

```stata
// ================================================================
// _dash_wexp_gen <cmdname>  -- the weight-expression columns, made in
// Stata at export (WP-31 A5).  The twin of _dash_tsop_gen: each
// expression of the registry (_dash_wexp_rewrite, _dash_wexp_export)
// becomes one column __dashw<k> = (expression), under capture, with
// Stata's own message and code when generate refuses it.  The names come
// back in the caller's local _dash_wexp_vars.
// ================================================================
program define _dash_wexp_gen
    version 19
    args cmdname
    local _dwx_n = 0
    mata: _dash_wexp_export()
    if `_dwx_n' == 0 {
        c_local _dash_wexp_vars ""
        exit
    }
    // (the __dashw* reserved-prefix refusal, as :6553-6559 for __dasht*)
    local made ""
    forvalues k = 1/`_dwx_n' {
        mata: st_local("_dw_ok", strofreal(_dash_wexp_ok(st_local("_dwx_e`k'"))))
        if !`_dw_ok' {
            if "`made'" != "" drop `made'
            mata: _dash_say("err", "`cmdname': registry entry [", st_local("_dwx_e`k'"), "] cannot be evaluated")
            exit 198
        }
        capture noisily generate double __dashw`k' = (`macval(_dwx_e`k'')')
        if _rc {
            local rc = _rc
            if "`made'" != "" drop `made'
            exit `rc'
        }
        local made `made' __dashw`k'
    }
    c_local _dash_wexp_vars "`made'"
end
```

`_dash_wexp_reset()`, `_dash_wexp_export()` (sets locals `_dwx_n`, `_dwx_e1..`) and `_dash_wexp_rewrite(json, errmacro)` are `_dash_tsop_reset` (:4001-4006), `_dash_tsop_export` and `_dash_tsop_rewrite` (:4058-4135) copied with `_dash_tsop_list` → `_dash_wexp_list`, `keys = ("wexp")`, the dot test replaced by `!(_st_varindex(val, 0) < . ) & !_dash_tsop_canon(val)` (a bare variable or a canonical term is left alone) and the `__dasht` column name → `__dashw`.

**TR-07.6 (dash_parse.mata; two one-line insertions):** in `_dash_rep_cat` before `return("R")` (:6189): `if (k == "hover") return("H")`. In `_dash_rep_merge` after `if (cat == "A") return(v1 + char(30) + v2)` (:8849): `if (cat == "H") return(strtrim(v1) + " " + strtrim(v2))`.

**TR-07.7 the y loop (dash.ado, after the x loop's closing brace at :7556; the body is the x loop's with the fixture's y sentence):**

```stata
    // A date literal in a y option (WP-31 A8): twoway refuses it as it
    // refuses the x form (test/fixtures/weight_operator_truth.json ydates.*).
    foreach c in ylabel:1 ytick:1 ymlabel:1 ymtick:1 ylabel2:1 ytick2:1 yscale:3 yscale2:3 {
        gettoken k f : c, parse(":")
        local f = substr("`f'", 2, .)
        mata: st_local("_tf_hit", strofreal(_dash_xdate_find(st_global("dash__tf_`k'"), `f')))
        if `_tf_hit' {
            if `f' == 3 {
                display as error "range() invalid -- invalid numlist"
                exit 121
            }
            mata: _dash_say("err", "invalid label specifier, :  ", st_local("_xd_tok"), ":")
            exit 198
        }
    }
```

(The two sentences are the x form's; if `ydates.ylabel.text`/`ydates.yscale.text` differ, the fixture's words replace them.)

## Boundaries

- Not S07's: `_dash_option_rules` and every numeric kind (S05/S06); `_dash_mlabel_list` (S06); the weight *drawing* of markers (`[aw]` marker sizing, C9, S20); KPI weights (S50); `yline()` date literals (`_dash_line_check`, already twoway's); `hover()` variables on the data table (S48); `xline`/`tline` loops; any renderer applier; `_FILTER_JS`; the served template.
- PRD §7: no new dependency.

## Stata truth

**New extractor** `scripts/extract_weight_operator_truth.do` → `test/fixtures/weight_operator_truth.json`, in `scripts/extract_default_base_truth.do`'s path-free form (`DASH_REPO` guards :21-43, `adopath ++`, `global dash_nobrowser 1`, `shell git -C "${REPO}" rev-parse HEAD > <work>/git_head.txt`, the python block reading it through `Macro.getLocal`, `_meta` = `stata_version born_date dash_commit extracted source`). Run: `DASH_REPO=$WT $WT/scripts/stata_slot.sh <scratch>/s07/x $WT/scripts/extract_weight_operator_truth.do`; `git add -f` the fixture. Data: `sysuse auto`, `tsset` on a generated `t = _n`, plus `gen double w1 = price+1`, `gen double w2 = L.price`, `gen int pos = mod(_n,12)`, `gen ym = ym(2000, mod(_n,12)+1)` with `%tm`.

| Key | twoway command (`capture noisily twoway ...` under a log) | Recorded |
|---|---|---|
| `weights.lfit_aw_expr`, `lfit_aw_var` | `twoway lfit mpg weight [aw=price+1]` / `[aw=w1]` | rc; `.Graph.plotregion1.plot1.serset` → `serset summarize` of the fitted y (`_dash_serset_values`-style read as scripts/extract_stat_truth.do reads a serset); equality of the two |
| `weights.lfit_aw_ts`, `lfit_aw_ts_var` | `[aw=L.price]` / `[aw=w2]` | the same |
| `weights.hist_fw_expr`, `kde_aw_expr`, `lpoly_aw_expr` | `histogram mpg [fw=rep78+1]`, `kdensity mpg [aw=price+1]`, `lpoly mpg weight [aw=price+1]` | rc, serset summary |
| `weights.bad_expr`, `bad_var`, `bad_syntax` | `[aw=nosuch+1]`, `[aw=nosuch]`, `[aw=price+]` | rc and the message line |
| `operators.mlabel_L`, `mlabel_Lnum`, `colorvar_L`, `mlabvpos_L`, `by_L` | `scatter mpg weight, mlabel(L.make)`, `mlabel(L.rep78)`, `colorvar(L.mpg)`, `mlabvposition(L.pos)`, `by(L.foreign)` | rc and the message line; for rc 0 the serset's variable list (`serset describe` names) |
| `ydates.ylabel`, `ytick`, `ymlabel`, `ymtick`, `ylabel2`, `yscale`, `yscale2` | `scatter mpg weight, ylabel(2000m1)` etc.; `(scatter mpg weight, yaxis(2)), ylabel(2000m1, axis(2))`; `yscale(range(2000m1))` | rc and the line |
| `ydates.ylabel_tfmt`, `ylabel_tfmt_lit` | `scatter ym weight, ylabel(2000m1)`; `scatter ym weight, ylabel(480)` | rc and the line (D-07.e) |

**Truth block** (R1): `test/test_wp31_truth.cscript`, header `* ==== S07 A5: Weight expressions, operators, hover merge, y dates ====` (one block for the section; A6-A8 cases inside it under their ids), `WP31_ONLY` gate, helpers `_u07_*` above the header:
- **U07-1** `dash lfit mpg weight [aw=price+1], name(u071)` and `[aw=w1]`: `_dash_serve_spec` of both, the saved renderer's fitted y (`r._dash_agg_source` is not set for lfit; read the Line's y column) equal to each other and to the fixture's serset values within 1e-9; served the same (generated app `make_document`).
- **U07-2** `[aw=L.price]` equals `[aw=w2]` both modes; the data JSON holds one `__dasht1` column.
- **U07-3** `histogram mpg [fw=rep78+1]`, `kdensity mpg [aw=price+1]`: the renderer's `_dash_agg_config["wvar"]` is `__dashw1` and the drawn heights equal the fixture's.
- **U07-4** `scatter mpg weight, mlabel(L.make)` and the other rc-0 forms: rc 0 and the LabelSet's text column equals `L.make`'s values (python helper reads the saved page's source); the refused forms: rc and logged line equal the fixture's.
- **U07-5** `dash (scatter mpg weight, hover(make)), hover(price) name(u075)`: registry JSON `"hover":"make price"`; the tooltip has three rows (the plotted two and make, price → mpg weight make price) in both modes; `hover(make price)` and `hover(price make)` orders preserved; a duplicate (`hover(make)` twice) appears once.
- **U07-6** `ylabel(2000m1)` and the other ydates forms: rc and line equal the fixture's; `ylabel(480)` rc 0 (guard).

**Block skeleton** (the WP-30 form, test/test_wp30_truth.cscript:2991-3317 is the model; `_w31_expect`/`_w31_done` are S01's tally helpers):

```stata
// S07 helpers (WP-31 A5-A8).  _u07_fit: the fitted y values a registered
// dash graph draws, saved and served; _u07_labels: a LabelSet's text
// column; _u07_hover: the tooltip rows.  Each answers through globals
// u07_s, u07_v and u07_n set inside the block.
python:
(helpers, top level, as _bg_docs at :2996-3010)
end
* ==== S07 A5: Weight expressions, operators, hover merge, y dates ====
local only : env WP31_ONLY
if inlist("`only'", "", "S07") & `: list posof "S07" in w31_run' {
display as text "S07 start"
sysuse auto, clear
dash clear
tsset, clear
generate t = _n
tsset t
generate double w1 = price + 1
// U07-1
capture noisily dash lfit mpg weight [aw=price+1], name(u071a)
_w31_expect U07-1 (_rc == 0) "dash lfit [aw=price+1] rc 0"
capture noisily dash lfit mpg weight [aw=w1], name(u071b)
...
_w31_done U07-1 "a weight expression is fitted as twoway fits it, both modes"
// U07-2 .. U07-6 likewise
dash clear
display as text "S07 end"
}
* ==== end S07 ====
```

Every graph is registered with `name(u07<k><letter>)`, its spec written with `_dash_serve_spec, specpath() datapath()` under the scaffold's work directory and erased at the end; twoway's half is the fixture's value (no second twoway run inside the block).

Refusal cases in `test/test_option_validation.cscript` (R1, appended as one run before `// Summary` at :1271, `_ov_case` form, header `*!` lines added): **U07-7** `[aw=price+1]` rc 0 and no `(note:`; `[aw=nosuch+1]` rc 111 with Stata's line; **U07-8** the hostile weight texts (``[aw=`x']``, `[aw=$x]`, `[aw=price;drop _all]`, `[aw="a"]`) rc 198 and `describe` shows no `__dashw*` variable afterwards; **U07-9** `mlabel(L.make)` on each type of `mlab_unread`/`mlab_refused` (dash.ado:2056-2057) keeps today's answer (guard).

## TDD test stubs

### Regression tests, `test/test_weight_operator_registration.py` (new; red at 6370ca4 unless marked guard)

Helpers: `_spec_from(cmd)` runs no Stata; the Python tests read the fixture and exercise the renderer on hand-written specs (`"wexp": "__dashw1"` columns in the frame) and `js_runner`/served documents as test_statistical_helpers.py:810-848 does. Stata-side behaviour is pinned in the cscripts.

- Test: the fixture exists with `_meta` and every key of the table -- `TestTheFixture::test_meta_is_stamped`, `::test_every_case_was_measured` (guard after 07-01).
- Test: a spec whose `wexp` is `__dashw1` is fitted with that column as the weight, lfit/qfit/lfitci/lpoly/kdensity/histogram, both modes -- `TestTheRendererReadsTheColumn::test_each_type[mode-type]` (guard: the renderer already reads any column name) and `::test_the_served_header_lists_wexp_as_a_var_key` (guard).
- Test: `_dash_tsop_rewrite`'s key list holds `wexp` and the word-mode keys -- read from dash_parse.mata by regex -- `TestTheMataKeyLists::test_wexp_is_rewritten`, `::test_word_mode_keys` (red: AssertionError).
- Test: `_dash_rep_cat` returns `"H"` for hover and `_dash_rep_merge` has an `"H"` branch (source read) -- `TestHoverIsMerged::test_category_and_branch` (red).
- Test: `_dash_taxis_fold` carries the y keys in both `dash__tf_` lists and a y loop -- `TestYDateLiterals::test_the_round_trip_lists`, `::test_the_y_loop_exists` (red).
- Test: the `_needed` list, the header index and program_coverage_map name every new Mata function and program -- `TestTheRegistries::test_needed_and_index_agree` (red).
- Test: twoway's measured rc for each operator form is what dash.ado's literal list `_dash_tsop_opts` encodes (the list read from dash.ado, the fixture's rc-0 forms) -- `TestOperatorForms::test_the_list_matches_the_fixture` (red: no list).

### Cases in cscripts

- `test_wp31_truth.cscript` U07-1..U07-6 (red at base; U07-6's `ylabel(480)` half is a guard).
- `test_option_validation.cscript` U07-7, U07-8 (red), U07-9 (guard).

### Flips

From `<scratch>/s07/07-flips.txt` (Evidence table; measured by grep in 07-01). Each docstring/comment gains "Flipped (WP-31 A5|A6|A7): twoway evaluates the weight / draws the operated variable / merges hover()".

### Parity corpus (R8)

`test/test_mode_parity.py`, under `# WP-31 S07`: `CORPUS` cases "lfit with a weight column" (`plot_for("lfit", {"weight": "aweight", "wexp": "__dashw1"})` with the column added in the case's spec), "hover with two lists merged" (`go={"hover": "make price"}`); `MOVE_CORPUS` "kdensity with a weight column, dropdown". `ALLOWED` is not edited.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Weight expressions fitted as twoway | cscript U07-1..3; pytest `TestTheRendererReadsTheColumn` | `weights.*` | yes |
| Hostile weight text refused, nothing generated | cscript U07-8 | -- | n/a |
| Operators in options | cscript U07-4, U07-9; pytest `TestOperatorForms` | `operators.*` | yes |
| hover() merge | cscript U07-5; pytest `TestHoverIsMerged`; OV-110 guard | -- | yes |
| y date literals | cscript U07-6; pytest `TestYDateLiterals` | `ydates.*` | n/a |
| Registries | pytest `TestTheRegistries`, test_program_coverage_map.py, test_function_test_map.py | -- | -- |

**Acceptance criteria**
- **AC-07.1** For every `weights.*` record with rc 0, dash's fitted values equal twoway's serset values within 1e-9 in both modes; for rc≠0 dash returns the same rc and logs the same line.
- **AC-07.2** `describe __dash*` after any dash command shows no `__dashw*`/`__dasht*` variable (dropped at export).
- **AC-07.3** Every `operators.*` form returns twoway's rc; the rc-0 forms draw the operated values.
- **AC-07.4** `hover()` from both places yields the union in order; OV-110 still passes.
- **AC-07.5** Every `ydates.*` form returns twoway's rc and line; `ylabel(480)` draws.
- **AC-07.6** `test_wp31_truth.cscript` under `WP31_ONLY=S07` prints U07-1..U07-6 PASS; `test_option_validation.cscript` prints U07-7..U07-9 PASS and ALL CHECKS PASSED; no SKIP.

## Tasks

**Commit boundary.** Four commits on `wp31-s07` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp31-s07`: 07-02 `Evaluate weight expressions at export, as twoway does (WP-31 A5)`; 07-03 `Draw time-series terms in option varlists where twoway draws them (WP-31 A6)`; 07-04 `Merge two hover() lists (WP-31 A7)` and `Refuse date literals in y options as twoway does (WP-31 A8)`. Each body: the row's lines from `<scratch>/07-01-failure.txt`, the measured defect, what changed where, then `Regression:`, `Flipped:`, `Fixture: test/fixtures/weight_operator_truth.json (scripts/extract_weight_operator_truth.do)` (A5 and A6 commits), `BUGS.md: "<title>" (closed)`, `GAPS3: <row> Tracked`. No tooling or vendor names (rule 6; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0).

<task type="auto" id="07-01">
  <name>Measure twoway and write failing tests</name>
  <files>scripts/extract_weight_operator_truth.do, test/fixtures/weight_operator_truth.json, test/test_weight_operator_registration.py</files>
  <action><![CDATA[
    Check `git -C $WT rev-parse HEAD` equals `cat <scratch>/batch-2-base.txt` and `git -C $WT branch --show-current` prints `wp31-s07`; `mkdir -p <scratch>/s07/x`. Create scripts/extract_weight_operator_truth.do from the "Stata truth" table in scripts/extract_default_base_truth.do's path-free form (copy its lines 1-60 head, rename the globals ZB_ to ZW_), run it through the slot, `git add -f test/fixtures/weight_operator_truth.json`. Create test/test_weight_operator_registration.py with exactly the classes of "TDD test stubs / Regression tests". Append U07-1..U07-6 to test/test_wp31_truth.cscript above `* ==== append new blocks above this line ====` in the WP-30 block form (helpers `_u07_*` above the header), and U07-7..U07-9 to test/test_option_validation.cscript before `// Summary` (:1271) with `*!` header lines. Run `python3 -m pytest test/test_weight_operator_registration.py -q -n0 -p no:cacheprovider -rf > <scratch>/s07/07-01.log 2>&1`, then both cscripts through the driver (`printf 'global dash_nobrowser 1\ncd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp31_truth.cscript > <scratch>/s07/run_truth.do; WP31_ONLY=S07 scripts/stata_slot.sh <scratch>/s07 <scratch>/s07/run_truth.do`, likewise test_option_validation.cscript). Write `<scratch>/07-01-failure.txt`: the base sha, each failing node and case with its one-line reason, grouped by row A5/A6/A7/A8, then the guards that passed. Write `<scratch>/s07/07-flips.txt` from `grep -rn "cannot evaluate a weight expression\|not a time-series expression" test/` and `grep -n "hover(" test/*.cscript`: one line per node whose assertion today's behaviour is, with its After. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/weight_operator_truth.json'));print(sorted(d['_meta']), sorted(d))"` prints `['born_date', 'dash_commit', 'extracted', 'source', 'stata_version']` and the keys `_meta operators weights ydates`; `grep -c FAILED <scratch>/s07/07-01.log` is at least 6 and no FAILED line names TestTheFixture or TestTheRendererReadsTheColumn; `grep -c "U07-[1-6] FAIL" <scratch>/s07/run_truth.log` is at least 5; `grep -c "U07-[78] FAIL" <scratch>/s07/run_option_validation.log` prints 2 and `grep -c "U07-9 PASS"` prints 1; `grep -c SKIP` on both logs prints 0; `test -s <scratch>/07-01-failure.txt`.]]></verify>
  <done>twoway's weighted fits, operator answers and y date refusals were recorded in a stamped fixture, and every regression test and case was shown failing on the unmodified tree with its failure text saved.</done>
</task>

<task type="auto" id="07-02">
  <name>Evaluate weight expressions and commit A5</name>
  <files>dash.ado, dash_parse.mata, test/program_coverage_map.py</files>
  <action><![CDATA[
    Make TR-07.1 (`_dash_wexp_ok`), TR-07.3 (`_dash_wexp_reset/_dash_wexp_rewrite/_dash_wexp_export` in dash_parse.mata after `_dash_tsop_meta`, with header-index entries; `_dash_wexp_gen` in dash.ado after `_dash_tsop_gen`; the call sites at :8899-8906, :9075, :9133-9150, :10040; `_needed` names after the `_dash_tsop_*` names on line 458), TR-07.2 (the registration gate :5410-5422) and TR-07.4 (`"wexp"` in `_dash_tsop_rewrite`'s keys). Add the program_coverage_map.py entries of TR-07.8 under `# WP-31 S07 (A5): weight expressions`. Flip the A5 nodes of `<scratch>/s07/07-flips.txt` in place with a `Flipped (WP-31 A5)` docstring line. Run `python3 -m pytest test/test_weight_operator_registration.py test/test_program_coverage_map.py test/test_unsupported_report_is_true.py -q -n0 -p no:cacheprovider -k "not Operator and not Hover and not YDate"` and the two cscripts through the driver (`WP31_ONLY=S07`). Then close the row: BUGS.md A5 entry Resolution rewritten in BRIEF's closed form (`- [x]`), GAPS3.md `- **A5 Tracked:** Closed in WP-31, BUGS.md "<title>", commit <sha>.` (the sha filled after the commit by amending the line in the same commit is not possible: write the line with the short sha of `git rev-parse --short HEAD~0` AFTER committing and amend once, as S01's convention says), the `<!-- WP-31 A5 -->` marker in CHANGELOG.md replaced in place by a Results line naming `dash lfit mpg weight [aw=price+1]` (old: r(198) "cannot evaluate a weight expression"; new: fitted as twoway fits it) and a Changed-behaviour line for the hostile-text refusal, dash.sthlp's Weights paragraph (`grep -n "weight expression" dash.sthlp`) rewritten to say an expression is evaluated at export. Stage dash.ado dash_parse.mata dash.sthlp BUGS.md CHANGELOG.md GAPS3.md scripts/extract_weight_operator_truth.do test/test_weight_operator_registration.py test/test_wp31_truth.cscript test/test_option_validation.cscript test/program_coverage_map.py and the flipped files; `git add -f test/fixtures/weight_operator_truth.json`; commit with the boundary's subject and body.
  ]]></action>
  <verify><![CDATA[`grep -c "U07-[1-3] PASS" <scratch>/s07/run_truth.log` prints 3; `grep -c "U07-[789] PASS" <scratch>/s07/run_option_validation.log` prints 3 and the log ends `ALL CHECKS PASSED`; the pytest run reports 0 failed; `git log -1 --format=%s` ends `(WP-31 A5)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-31 A5 -->' CHANGELOG.md` prints 0; `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>Weight expressions were evaluated into __dashw columns at export and time-series weight terms into __dasht columns, refused texts were Stata's own, and A5 was closed in one green commit.</done>
</task>

<task type="auto" id="07-03">
  <name>Route operators in option varlists and commit A6</name>
  <files>dash.ado, dash_parse.mata, test/test_mode_parity.py</files>
  <action><![CDATA[
    Re-run the A6 nodes of test_weight_operator_registration.py (`-k Operator`) and U07-4 against the tree 07-02 left; append their failure lines to `<scratch>/07-01-failure.txt` under `A6 (after A5)`. Make TR-07.5: in `_dash_validate_value` :3457-3479 replace the `regexm` test with `_dash_tsop_canon` per word and the fixture-derived literal list `local _dash_tsop_opts "<rc-0 forms>"` (comment names `weight_operator_truth.json operators.*`), refusing the other forms with the fixture's text and rc; add word mode to `_dash_tsop_rewrite` (`wkeys`, `by` head split at the first top-level comma, quoted words kept). In dash_render.py find the `ts_cols` lookup (`grep -n '"ts_cols"' dash_render.py`) and make the mlabel LabelSet and the colorvar legend title use it for a `__dasht` column, with no new module-level helper (a `GlyphMapper` method if one is needed; R2). Append the parity cases of "TDD test stubs / Parity corpus" to test/test_mode_parity.py. Flip the A6 nodes of 07-flips.txt. Run `python3 -m pytest test/test_weight_operator_registration.py test/test_mode_parity.py -q -n0 -p no:cacheprovider -k "Operator or S07"` and the truth cscript (`WP31_ONLY=S07`) plus test_option_validation.cscript. Close A6 (BUGS.md, GAPS3 Tracked, CHANGELOG marker → a Results line for `scatter mpg weight, mlabel(L.make)` and a Changed-behaviour line for each form now refused with twoway's rc, dash.sthlp's time-series paragraph `grep -n "time-series operator" dash.sthlp` gains the option forms). Commit with the boundary's subject.
  ]]></action>
  <verify><![CDATA[`grep -c "U07-4 PASS" <scratch>/s07/run_truth.log` prints 1 and `grep -c " FAIL\|SKIP"` on both logs prints 0; the pytest run reports 0 failed; `grep -n "regexm(scalar(\`K'), \"^\[LlFfDdSs\]" dash.ado` prints nothing; `git log -1 --format=%s` ends `(WP-31 A6)`; `grep -c '<!-- WP-31 A6 -->' CHANGELOG.md` prints 0.]]></verify>
  <done>Time-series terms in mlabel(), colorvar(), mlabvposition() and by() were drawn where twoway draws them and refused with twoway's words elsewhere, and A6 was closed in one green commit.</done>
</task>

<task type="auto" id="07-04">
  <name>Merge hover lists, refuse y dates, commit A7 and A8</name>
  <files>dash.ado, dash_parse.mata, dash.sthlp</files>
  <action><![CDATA[
    Re-run the A7 and A8 nodes (`-k "Hover or YDate"`) and U07-5, U07-6 against the tree 07-03 left; append their lines to the failure file. A7: make TR-07.6 (`"H"` in `_dash_rep_cat` and `_dash_rep_merge`, the comment line), flip the A7 nodes, run `python3 -m pytest test/test_weight_operator_registration.py -q -n0 -p no:cacheprovider -k Hover` and the truth cscript; close A7 (BUGS.md, GAPS3 Tracked, CHANGELOG `<!-- WP-31 A7 -->` → Results line "hover() in a layer and after the comma kept the rightmost list; both lists are shown now", dash.sthlp's hover() paragraph `grep -n "{opt hover(" dash.sthlp` gains one sentence); commit `Merge two hover() lists (WP-31 A7)`. A8: make TR-07.7 (the two `dash__tf_` lists at :7001 and :7010 gain the eight y keys; the y loop after :7556 with the fixture's sentence; the `%t`-y exception per D-07.e read from `ydates.ylabel_tfmt.rc`), run `-k YDate` and the truth cscript (U07-6), close A8 (CHANGELOG marker → Changed-behaviour line naming `ylabel(2000m1)` and twoway's words; dash.sthlp's axis-options paragraph on date literals `grep -n "date literal" dash.sthlp` says y options too); if the `%t`-y case is rc 0 in the fixture, add the open residual BUGS.md entry in BRIEF's open form graded S3 and make A8's Tracked line the `Partly closed` form. Commit `Refuse date literals in y options as twoway does (WP-31 A8)`. Finally run `python3 -m pytest test/test_weight_operator_registration.py test/test_tracking_documents.py test/test_help_conformance.py -q -n0 -p no:cacheprovider` and the two cscripts once more.
  ]]></action>
  <verify><![CDATA[`grep -c "U07-[1-6] PASS" <scratch>/s07/run_truth.log` prints 6 and `grep -c " FAIL\|SKIP"` prints 0; `grep -c "U07-[789] PASS" <scratch>/s07/run_option_validation.log` prints 3; the final pytest run reports 0 failed; `git log -2 --format=%s` shows `(WP-31 A8)` then `(WP-31 A7)`; `grep -c '<!-- WP-31 A[78] -->' CHANGELOG.md` prints 0; `git log -4 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Two hover() lists were merged in order and y date literals were refused with twoway's words, each row closed in its own green commit on wp31-s07.</done>
</task>

## Section completion criteria

- `[aw=<expr>]` on every `_wt_honoured` type fits as twoway does in both modes; hostile texts refused; no `__dashw*` left in the data.
- Operator forms return twoway's rc; the rc-0 forms draw the operated values in both modes.
- `hover()` lists merged in order, duplicates once; OV-110 green.
- y date literals refused with twoway's lines where twoway refuses them; any accepted form filed (D-07.e).
- `weight_operator_truth.json` stamped and named by `test_weight_operator_registration.py`; U07-1..U07-9 PASS; every flip recorded.
- Four green commits on `wp31-s07`; four BUGS.md entries closed; four Tracked lines rewritten; four markers replaced.

## Notes

- **The `generate` runs once per distinct expression per export**, under the user's sort and after `_dash_qual_gen`/`_dash_sort_gen`/`_dash_tsop_gen`, so a weight expression that names a time-series term inside a larger expression (`L.price+1`) needs `tsset`: Stata's `generate` says "time variable not set" r(111) itself; copy it (BR-07.1).
- **python_exec hazard** (project memory): after each cscript run check `~/.stata19/console/stata19.rc` still holds `python_exec`; a SKIP is not a pass.
- **cscript drops globals**: the truth block's helpers answer through `_u07_` globals set inside the block, as the WP-30 `_bg_` helpers do.
- **Shared files (R1-R13).** R1: one S07 block in the truth script; U07-7..9 in test_option_validation.cscript as one run. R2: no copy-list entry (no module helper). R3: dash.sthlp paragraphs owned: Weights, time-series operators, hover(), date literals in axis options. R4: four markers. R5: four entries and lines. R6: `_needed` gains seven names in the `_dash_tsop_*` line's alphabetical place; `version 19` in `_dash_wexp_gen`; the seven graph key lists are NOT edited (hover is already in all seven). R7: one fixture, `git add -f`. R8: three corpus entries. R9: flips from 07-flips.txt. R12: S07 edits none of the hot functions.
- **For S20 (C9, weighted markers):** the weight column for the glyph types is not exported today (`_seg_wv` only on `_wt_honoured`, :5901); S20 widens that list, and the `__dashw` route then serves it unchanged.
- **For S48 (data table):** a `__dashw<k>`/`__dasht<k>` column's display name is in `ts_cols`; the table should show the expression text, not the column name.
- **Commit-body line forms** are BRIEF's: `Regression: test/test_weight_operator_registration.py::<Class>::<test> -- failed at 6370ca4 with <text>`, `Regression: test/test_wp31_truth.cscript U07-k`, `Flipped: <node> -- <old> was wrong because <why>`, `Fixture: ...`, `BUGS.md: "<title>" (closed)`, `GAPS3: A5 Tracked`.
