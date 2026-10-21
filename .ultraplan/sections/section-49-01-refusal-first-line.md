# Section 49-01: Refusal first lines in twoway's words, typed spelling

> Part of: WP-49 (Messages and notes, audit package 17) · Items: plot:PT-7, plot:PT-6 · Risk: yellow · Batch: 49.1 · Depends on: none (WP-34..48 landed) · Blocks: none (WE) · Tasks: 7, 2 commits · Case-id prefix: Q4901

## Overview

**What is wrong today.**

- **plot:PT-7 (GW-8, ECO-11, sil:SD-9, syn:SD-12, TR-10).** "Refusals add a second line ('twoway does not take this option here', the after-comma hint, 'takes this option once') and a six-line Supported list; value refusals use dash's words; the full option name is printed instead of the typed spelling (bands() for ba())" (audit :830). The maintainer's ruling narrows this (Q43, M12, **PD-11**): *the first line of every refusal is twoway's words naming the option as typed; dash's second and later lines and the Supported list stay*. So the work is every refusal whose FIRST line differs from twoway's:
  - **the canonical name for the typed one** -- `function y = x, ba(3)` and `dropline ..., ba(3)`: twoway "option ba() not allowed", dash "option bands() not allowed" (p6out.log K046/K087). The applicability refusal names the table's option (`display as error "option \`o'() not allowed"`, dash.ado:4869), and so do the one-value check (:4563), the n()/degree() refusals (:4485, :4495), atobs/nofit (:10502-10503), the kernel-option refusal (:10771), pcycle()/seriesid() (:9187, :9192), and the `\`o'`, `\`w'`, `\`kw'`, `\`f'`, `\`tok'` sites (:2614, :2963, :3576, :4805, :9445; re-read each);
  - **value refusals in dash's words** -- about 35 of the 56 same-rc probes of value_truth.json printed "dash: X must be ..." where twoway prints e.g. "bands must be between 1 and 200", "bandwidth must be positive", "invalid kernel function", "option colorlevels() incorrectly specified" (TR-10; `_dash_validate_value`, dash.ado:3828ff). 35-05 (WP-35, D-35-05.a) already prints twoway's rc and first line for every refused probe of value_truth.json and value_codes_truth.json from its generated table `_dash_tw_value_tab()` (`scripts/gen_value_refusal_table.py`), pinned by 33-10's Q3310-1 (`WP33_ONLY=S10`) for value_truth.json's rows and by 35-05's Q3505-1 for value_codes_truth.json's. The audit's TR-10 probes are value_truth.json rows themselves -- `kdensity_bwidth_1` (`kdensity mpg, bwidth(-1)`), `mband_bands_1` (`mband mpg weight, bands(0)`), `kdensity_kernel_1` (`kdensity mpg, kernel(bogus)`), `colorlevels_1` (`scatter mpg weight, colorvar(price) colorlevels(abc)`) and `mlabangle_4` (`scatter mpg weight, mlabel(make) mlabangle(400)`) -- so Q3310-1 already pins their first lines; this section closes the `VALUE_KNOWN` rows keyed `plot:PT-7` that are still in dash's words at the WP-49 base (D-33-10.b keys every same-rc, different-first-line value difference to this item; `python3 test/known_differences.py plot:PT-7` lists them) and checks that the five TR-10 refusals print no line after twoway's (D-49-01.b);
  - **other first lines in dash's words** (syn:SD-12): `[aw=price] is not a twoway plot type` where twoway writes `[ is not a twoway plot type` (E08); "dash: unbalanced parentheses in the plot specification." where twoway writes "parentheses do not balance" (Q14; dash_parse.mata:3457 -- :3635 is the different "unexpected text between plot groups" message); "dash: by(): variable nosuch not found" where twoway writes "variable nosuch not found" (by(), mlabel(), colorvar()); "option line not allowed" for twoway's "option | not allowed"; "option legloc() not allowed" for twoway's "option 6 not allowed" (`legloc(6)`); `useplotregion(1)` where twoway writes "1 is not a plotregion" (S13d, O15-O17, V22, V23).
  The help claims the refusals are exactly twoway's (Differences item 5, dash.sthlp:980-1000: "dash names the word twoway names"; ~:1036 "twoway's line option kernel() not allowed (naming the option given)") -- HR-17, this section's (index Appendix B).
- **plot:PT-6 (plot:PT-8, DG-10).** "Different words, same rc: tsline/tsrline without tsset; a weight glued to the type ('scatter[aw=price]'); a date tline() on a %tb axis" (audit :839). tsline/tsrline: dash "dash: tsline needs a time variable: tsset your data first, as twoway tsline does." where twoway writes "time variable not set, use tsset varname ...", r(111) (dash.ado:6030-6035, :6276-6280). `scatter[aw=price] mpg weight`: dash splits the type at a blank or comma only (`gettoken plottype rest : seg_text, parse(" ,")`, :5868), so "scatter[aw=price] is not a twoway plot type" where twoway (`parse(" ,[")`, twowaygraph_g.class:216) writes "invalid 'mpg'", r(198); the same for `hist[fw=rep78] mpg`. `tline(10nov2011)` on a %tb axis: dash "invalid line argument, 10nov2011" where twoway writes "invalid number, (10nov2011)": `_dash_taxis_unit` gives `"c"` for %tb under family 2 (dash_parse.mata:9264-9279), so `_dash_tdate_lines` takes the %tc branch.

**After this section**, every refusal's first line is twoway's, with the option spelled as typed; dash's advice lines and the Supported list follow it unchanged; the help says exactly that.

**Why one section.** Both items are first lines of refusals; the index makes 49-01 the owner of the refusal programs' first lines (`_dash_refuse_unknown`, `_dash_refuse_foreign`, `_dash_refuse_repeat`), which already print twoway's line, and of every other refusal site's first line.

**Test order and commit rule.** Two commits `(WP-49 plot:PT-7)` then `(WP-49 plot:PT-6)`. 49-01-01 writes the extract script (both items) and plot:PT-7's failing cases; saved failure; no commit. 49-01-02 and 49-01-03 fix and commit plot:PT-7 (with HR-17's test). 49-01-04/05 repeat for plot:PT-6. 49-01-06 browser-free check; 49-01-07 section check.

### Section decisions (binding on the executor)

- **D-49-01.a One helper gives the spelling as typed.** New Mata `string scalar _dash_opt_typed(string scalar opts, string scalar canon, string scalar table)`: the first option word of `opts` (split by `_dash_rep_toks(opts, 0)`, read through `_dash_rep_optname`) whose canonical name under `table` (`"plot"`, `"graph"` or a sub-option table name as `_dash_so_canon` takes it) is `canon`, returned as typed plus `"()"` when it took a value; `canon + "()"`/`canon` when none is found (a spec written by hand). Every site of D-49-01's list calls it with the option text it already holds as typed (`opts_raw`, the `_dash_text_args` local, or the graph-option text) instead of printing the table's name. Sites that already print the typed word (`_dash_refuse_unknown`'s `_uk_nm<k>`, `_dash_refuse_foreign`'s `first`, `_dash_refuse_repeat`'s `nm`, the lowess logit and barwidth paths at :6700, :6712) are left as they are, and so are the refusals WP-35 and WP-42 made for synonyms dash used to accept (35-07's `_dash_dashonly_typed` refusal, 35-04's `bw()`, 42-05's CV-14 words; P4-7): their first line is already twoway's with the typed word, and their second line naming the twoway spelling (P4-9, e.g. "use ytitle(..., axis(2))") is one of dash's kept lines (PD-11) -- this section neither rewrites nor removes it.
- **D-49-01.b Value refusals use 35-05's table (PD-11, REVIEW-5 R5-7).** No second table is made: every value_truth.json row stays covered by 33-10's Q3310-1 (block `S10 TR-11` of test/test_wp33_truth.cscript, run with `WP33_ONLY=S10`), every value_codes_truth.json row by 35-05's Q3505-1 (test_option_validation.cscript), and the generated table by 35-05's in-step test `test/test_value_refusal_table.py::TestTheTable::test_generated_and_in_step` (`gen_value_refusal_table.py --check`); this section runs all three and duplicates none. 35-05 (D-35-05.a) prints twoway's rc and first line from `_dash_tw_value_tab()` with no second line, and that stays so. The TR-10 probes are value_truth.json rows (`kdensity_bwidth_1` (`kdensity mpg, bwidth(-1)`), `mband_bands_1` (`mband mpg weight, bands(0)`), `kdensity_kernel_1` (`kdensity mpg, kernel(bogus)`), `colorlevels_1` (`scatter mpg weight, colorvar(price) colorlevels(abc)`) and `mlabangle_4` (`scatter mpg weight, mlabel(make) mlabangle(400)`)), so the extract makes no `pt7.value.*` key and no value probe is copied into scripts/extract_value_codes_truth.do or value_codes_truth.json (Q3505-1 stays value_codes_truth.json's alone). Case Q4901-2 reads those five rows from test/fixtures/value_truth.json by id, runs each `command` under dash (`twoway` replaced by `dash`) and asserts only that no error line follows dash's first (D-35-05.a: a value refusal has no second line); the rc and the first line are Q3310-1's, cited and not re-asserted. 49-01-02's work list is the `VALUE_KNOWN` rows (test/value_truth_known.py) that `python3 test/known_differences.py plot:PT-7` prints. A row still in dash's words is closed from value_truth.json itself: by regenerating 35-05's table with `python3 scripts/gen_value_refusal_table.py` (it reads value_truth.json) when the generated `tw_value` block lacks the row's (option, types, class) row, or, when the block holds the row, by printing the site's first line through 35-05's lookup `_dash_tw_value_msg` (TR-35-05.2), as `_dash_validate_value` does; the closing commit then deletes the row (step 2). A row the regenerated table still lacks is a gap in 35-05's class rule (TR-35-05.1): stop and report it (35-05's generator is not edited here). xsize()/ysize() are excluded here (D-49-02.e): 45-04's graphsize kind (GW-1, TR-45-04.4) already prints twoway's three lines for a size outside 1-100 inches, pinned by 45-04's Q4504-2 (49-02 cites it and edits nothing there), and 49-02 edits only the non-number note (`xsize(abc)`).
- **D-49-01.c The syn:SD-12 and plot:PT-6 first lines.** Each is replaced by twoway's line from the fixture; whether dash's old sentence is kept as the second line is fixed by this table (REVIEW-5 R5-30) -- it is kept only where it adds advice twoway's line lacks, and is dropped where it only restates twoway's line. Each site is found by grep of dash's current text.

  | Site (anchor at `090d928`) | New first line (fixture key) | dash's old sentence |
  |---|---|---|
  | a `[`-led type word, dash.ado:5897 (the word printed is the text up to and including `[`; the split of D-49-01.e makes this reachable only for a segment that starts with `[`) | `[ is not a twoway plot type` (`sd12.E08`) | the Supported list follows, kept (Q43) |
  | unbalanced parentheses, dash_parse.mata:3457 | `parentheses do not balance` (`sd12.Q14`) | dropped (it restates the line) |
  | by(), mlabel(), colorvar() variable not found, `_dash_validate_value`'s var kind (dash.ado:4325) | `variable <name> not found` (`sd12.by_nosuch`, `mlabel_nosuch`, `colorvar_nosuch`) | dropped (the same words with a `dash: <opt>(): ` prefix) |
  | `\|` read as `line` | `option \| not allowed` (`sd12.bar_word`) | dropped |
  | `legloc(<value>)` | `option <value> not allowed`, as twoway words it (`sd12.legloc`) | dropped |
  | `useplotregion(<n>)` | `<n> is not a plotregion` (`sd12.useplotregion`) | dropped |
  | tsline/tsrline without tsset, dash.ado:6030-6035, :6276-6280 | twoway's line (`pt6.tsline`, `pt6.tsrline`) | kept as the second line (it says to tsset) |
  | a weight glued to the type, dash.ado:5868 | twoway's line (`pt8.scatter`, `pt8.hist`) | none (a new path) |
  | a date `tline()` on a %tb axis | `invalid number, (<tok>)` (`dg10.tb`) | dropped ("invalid line argument" restates it) |
- **D-49-01.d The help states the rule (HR-17).** Differences item 5 (dash.sthlp:980-1000) and the applicability sentence (~:1036): "A refusal's first line is twoway's, naming the option as you typed it (option ba() not allowed for ba()); dash may add a line of advice -- the twoway spelling of a synonym it used to accept, or what to do first -- and after a word that is not a plot type, the list of the plot types it draws." ("may": value refusals and the dropped sentences of D-49-01.c have no second line, REVIEW-5 R5-30.) The phrase "naming the option given" is replaced. `TestHR17` is added to test/test_false_sentences.py (48-04's file; D-48-04.c) in this item's commit.
- **D-49-01.e plot:PT-6's three.** (1) tsline/tsrline: twoway's line from the fixture (`pt6.tsline`, `pt6.tsrline`; expected "time variable not set, use tsset varname ..."), then dash's sentence as the second line (D-49-01.c's table), exit 111. (2) The type word is split at `[` too: `gettoken plottype rest : seg_text, parse(" ,[")` (:5868); when `rest` then starts with `[`, the segment is a weight before the varlist and dash refuses as twoway does, with the fixture's line (`pt8.scatter`: expected `invalid 'mpg'`, naming the first word after the weight's `]`) and r(198). (3) `_dash_taxis_unit(fmt, 2)` returns `""` for a `%tb` format (the business calendar has no literal form in a line: twoway's numeric branch), keeping `"c"` for %tc and %tC; `tline()` on %tb then prints `invalid number, (<tok>)` as twoway (fixture `dg10.tb`), and numeric %tb lines are unchanged (fixture `dg10.tb_number`).

## Risk: [yellow] -- every refusal path's first line, and the type-word split every segment passes

**Why.** Changing first lines touches pins across the cert scripts (test_option_validation.cscript, test_twoway_option_parity.cscript, test_parser.cscript, test_help_claims_*.cscript); the `[` split runs on every plot segment.

**Risk factors.**
1. Many cscript cases compare dash's first line with a recorded dash line, not twoway's (they then pin today's wording).
2. A weight written after the varlist (`scatter mpg weight [aw=price]`) must not be affected by the `[` split.
3. Every new first line that echoes a typed word must not echo unbounded user text (security: bounded lengths where text is echoed).
4. Batch partner 49-02 edits note sites (`_dash_added_text`'s note, `_dash_style_note`, `_dash_require_mata`) and xsize()/ysize()'s non-number note (`xsize(abc)`, where 45-04's graphsize kind leaves the word at the WP-49 base: `_stat_option_float`'s warning in dash_render.py, or the kind itself in `_dash_validate_value`); it edits no refusal line, since the kind's three-line bound refusal is 45-04's, pinned by its Q4504-2 (D-49-02.e). This section edits `_dash_validate_value`'s `var` kind (the variable-not-found line, dash.ado:4325) and `_dash_process_segment` lines outside the per-type block (:5868, :6030, :6276), where 49-02 edits :6982 -- different hunks, named in both hand-backs (REVIEW-5 R5-8, R5-37).

**Mitigation.**
1. 49-01-01 runs the area cscripts once with the new cases and records every existing case that compares a dash-worded first line; each is flipped to twoway's line (from the fixture) with a `Flipped:` line.
2. The split only applies to the first token (`plottype`); `rest` holding `[` later is the weight after the varlist, as today. Q4901-6 covers both orders.
3. `_dash_say` already bounds and escapes echoed text (re-read it); a typed word is cut to 80 characters as the existing messages cut it.
4. No R12 hot block is shared (the per-type check block of `_dash_process_segment`, dash.ado:6826-6930, is touched by neither); merge order 49-01 then 49-02 keeps both sections' hunks.

## Dependencies

- **Depends on:** none in WP-49. 35-05 (basic:PT-9) set twoway's return codes and first lines on value refusals in WP-35 (`_dash_tw_value_tab()`); this section adds no value probe: a value_truth.json row still in dash's words is closed through 35-05's generator, which reads value_truth.json, or its lookup `_dash_tw_value_msg` (D-49-01.b). 44-04 (DG-4) rewrote `_dash_tdate_*`'s tokenizer; re-read before editing `_dash_taxis_unit`.
- **Blocks:** none; WP-49's WE follows.
- **Parallel batch 49.1** with 49-02 (merge order 49-01, 49-02).

## Evidence

```
11019 program define _dash_refuse_repeat
11020     version 19
11021     args nm
11022     mata: _dash_say("err", "option ", st_local("nm"), " not allowed")
11023     display as error "      twoway takes this option once; this command gives it more than once."
```

```
4866         if `: list ptype in types' continue
4867         mata: st_local("_ap_v", strofreal(st_global("s(" + st_local("o") + ")") != ""))
4868         if `_ap_v' {
4869             display as error "option `o'() not allowed"
```

```
5868     gettoken plottype rest : seg_text, parse(" ,")
```

```
5897         mata: _dash_say("err", "", st_local("plottype"), " is not a twoway plot type")
5898         display as error ///
5899             "Supported: scatter line connected area bar spike " _n ///
```

`_dash_refuse_unknown` (:11186-11242) prints `option <typed> not allowed` then a second line (kept); `_dash_refuse_foreign` (:11072-11114) likewise. value_truth.json: 311 rows `{id, option, value, command, rc, message}` (e.g. `bands must be between 1 and 200`, `graph xsize invalid; minimum xsize is 1 inch maximum xsize is 100 inches`). unknown_option_truth.json (`probes`, `orders`, `types`: twoway's messages for unknown options and spellings). Help: dash.sthlp:980-1000 (item 5), :1022-1040.

### Tests that pin today's behaviour (flip, never delete)

- `grep -rn "option bands() not allowed\|dash: by(): variable\|unbalanced parentheses\|needs a time variable\|is not a twoway plot type" test/*.cscript test/*.py` -- each case comparing dash's own first line.
- test_parser.cscript:2091-2093 (P1A-81 tsline compares rc only; extend to the first line).
- Help readers of item 5's "dash names the word twoway names" and "naming the option given".

## User stories

- **US-49-01.1** As a Stata user, I want a refusal's first line to be the one twoway prints, naming the option as I typed it, so I recognise the error.
- **US-49-01.2** As a Stata user, I want dash's extra advice kept after twoway's line, so I still learn what to do.

## Business requirements

- **BR-49-01.1** For every probe in the fixture and in value_truth.json where twoway refuses and dash refuses with the same rc, dash's first error line equals twoway's.
- **BR-49-01.2** dash's second lines and the Supported list are unchanged.
- **BR-49-01.3** The help's refusal sentences say so (HR-17), pinned.

## Technical requirements

- **TR-49-01.1** Mata `_dash_opt_typed` (D-49-01.a) in dash_parse.mata after `_dash_rep_prefix` (grep), header index line, `_needed` entry, program_coverage_map.py row naming `test_option_validation.cscript:Q4901-1`.
- **TR-49-01.2** No new table and no new value probe. A `VALUE_KNOWN` row keyed `plot:PT-7` still in dash's words is closed per D-49-01.b: `python3 scripts/gen_value_refusal_table.py` regenerates 35-05's `_dash_tw_value_tab()` from value_truth.json, or the refusal site prints its first line through `_dash_tw_value_msg`; scripts/extract_value_codes_truth.do and value_codes_truth.json are not touched; the generator's `--check` passes after.
- **TR-49-01.3** The sites of D-49-01.a/c/e edited in dash.ado and dash_parse.mata, each named in the commit body with its old and new first line.
- **TR-49-01.4** `_dash_taxis_unit` (D-49-01.e(3)).
- **TR-49-01.5** Help (R3): item 5 and the applicability sentence (D-49-01.d). No tsline help edit: the phrase "tsset your data first" is only in dash.ado (:6034, :6279), and the help's tsline synopt (`grep -n "drawn against the" dash.sthlp`, :296-299) and its operator sentence (:406, "time variable not set") quote no dash wording (REVIEW-5 R5-31).
- **TR-49-01.6** CHANGELOG under `### Fixed in WP-49`: one line per item (`... first line is twoway's ... (WP-49, plot:PT-7)`, `(WP-49, plot:PT-6)`); results unchanged (rc kept). TWOWAY_COVERAGE_AUDIT.md (M13, REVIEW-5 R5-38): each closing commit greps the file for the item's option names and refusal wording (`not allowed`, `refused`, `tsline`, `tline`) and appends `[WP-49 <id>: corrected -- the first line is twoway's, the option as typed]` to each row that states dash's old words; when no row does, the commit body says so.

## Boundaries

- Do not remove any second line or the Supported list (PD-11, Q43), the P4-9 synonym hint lines included. The only dash sentences that leave are the first-line sentences D-49-01.c's table marks dropped. Do not change any return code (35-05 set them). Do not touch notes (49-02), `_dash_require_mata` (49-02) or the xsize()/ysize() graphsize kind of `_dash_validate_value` (45-04's, its three lines pinned by Q4504-2; 49-02 edits only the non-number note, D-49-02.e).
- No Stata-version text (M2); no browser text.

## Stata truth

New `scripts/extract_refusal_line_truth.do` -> `test/fixtures/refusal_line_truth.json` (frame of `scripts/extract_noted_option_truth.do` as it stands at the WP-49 base; per key: the command, twoway's rc and every error line from a text log, dash's rc and every error line). Keys:
- `pt7.typed.<site>`: one probe per D-49-01.a site with a shortened spelling (e.g. `function y = x, ba(3)`, `dropline mpg weight, ba(3)`, `scatter mpg weight, deg(2)`, `scatter mpg weight, n(5)`, `scatter mpg weight, ato`, `scatter mpg weight, pcyc(2)` twice, the kernel word on scatter, each `\`o'`/`\`w'`/`\`kw'`/`\`f'`/`\`tok'` site's trigger).
- `pt7.kept.*`: `ytitle2` (`scatter mpg weight, ytitle2(Y)`, refused under P4-7 with its P4-9 hint line), `unknown` (`scatter mpg weight, titel(x)`), `repeat` (`lfit mpg weight, atobs atobs`, the second copy `_dash_refuse_repeat` refuses, dash.ado:11013-11016) -- dash's full lines at the base, which Q4901-5 compares byte for byte after the fix.
- No `pt7.value.*` key: the TR-10 probes are value_truth.json rows (D-49-01.b), read by Q4901-2 from that fixture.
- `sd12.*`: E08 (`dash [aw=price] scatter mpg weight` as `twoway [aw=price] scatter mpg weight`), Q14 (`(scatter mpg weight`), `by_nosuch` (`scatter mpg weight, by(nosuch)`), `mlabel_nosuch`, `colorvar_nosuch`, `bar_word` (`scatter mpg weight | line mpg weight`), `legloc` (`scatter mpg weight, legloc(6)` after the plot's comma, and `by(foreign, legloc(6))` -- the extract records both; D-49-01.c follows whichever twoway refuses with "option 6 not allowed"), `useplotregion` (`scatter mpg weight, useplotregion(1)`).
- `pt6.*`: `tsline` (`sysuse auto`, `tsline mpg`), `tsrline`; `pt8.scatter` (`scatter[aw=price] mpg weight`), `pt8.hist` (`hist[fw=rep78] mpg`), `pt8.after` (`scatter mpg weight [aw=price]`, drawn); `dg10.tb` (a business-calendar axis made as test/test_wp31_truth.cscript:13165 makes one: `sysuse sp500`, `quietly bcal create "<work>/u49", from(date) replace`, `gen tb = bofd("u49", date)`, `format tb %tbu49`, then `scatter close tb, tline(10nov2001)` with a date inside the calendar's range), `dg10.tb_number` (`tline(5)` on the same graph).

Run twice through `scripts/stata_slot.sh` with DASH_REPO; `git add -f`. Truth blocks in test/test_wp49_truth.cscript (W0 created it): `* ==== S01 plot:PT-7: first lines in twoway's words ====` and `* ==== S01 plot:PT-6: tsset, glued weights, %tb lines ====`, gate `WP49_ONLY`/`"S01"`, comparing live `capture noisily twoway ...` beside `capture noisily dash ...` first lines. The per-site refusal cases go in test/test_option_validation.cscript (R1) under ids Q4901-1..5; plot:PT-6's in test/test_parser.cscript as Q4901-6..8.

## TDD test stubs

- cscript: Q4901-1 (typed spellings at every D-49-01.a site), Q4901-2 (the five TR-10 rows of value_truth.json, read by id: no error line after dash's first, D-49-01.b; their rc and first line are Q3310-1's), Q4901-3 (syn:SD-12 lines, and the kept or dropped second line of each D-49-01.c row), Q4901-4 (the Supported list still follows "is not a twoway plot type"), Q4901-5 (the second lines of `_dash_refuse_unknown`/`_foreign`/`_repeat` and one P4-9 synonym refusal's hint line, e.g. `ytitle2(Y)`, unchanged); Q4901-6 (tsline, tsrline), Q4901-7 (glued weight refused as twoway; weight after the varlist drawn), Q4901-8 (%tb tline words; numeric %tb line drawn).
- pytest: test/test_refusal_lines_p17.py::TestTheHelp::test_item_five (reads the D-49-01.d sentence); test/test_false_sentences.py::TestHR17::test_refusal_sentences. Run, not duplicated: 35-05's `test/test_value_refusal_table.py::TestTheTable::test_generated_and_in_step` (the value table in step), 33-10's Q3310-1 (`WP33_ONLY=S10`; every value_truth.json row) and 35-05's Q3505-1 (every value_codes_truth.json row).
- Flips: Evidence list.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| typed spellings, syn:SD-12 lines | cscript Q4901-1, Q4901-3; S01 block | refusal_line_truth.json | Stata side (refusals precede any page) |
| value refusal first lines | 33-10's Q3310-1 (`WP33_ONLY=S10`, value_truth.json, the five TR-10 rows among them), 35-05's Q3505-1 (value_codes_truth.json) and test_value_refusal_table.py, run; cscript Q4901-2 (no line after the first, the five TR-10 rows) | value_truth.json (33-10's), value_codes_truth.json (35-05's) | Stata side |
| kept second lines and list | cscript Q4901-4, Q4901-5 | -- | Stata side |
| plot:PT-6 | cscript Q4901-6..8; S01 block | refusal_line_truth.json pt6/pt8/dg10 | Stata side |
| help (HR-17) | pytest TestTheHelp, TestHR17 | dash.sthlp | n/a |

Acceptance criteria:
- **AC-49-01.1** Every fixture probe where both refuse with one rc has dash's first line equal to twoway's.
- **AC-49-01.2** Q4901-4/5: the second lines, the P4-9 hint lines and the Supported list are byte-identical to the base's; Q4901-3: each D-49-01.c row keeps or drops dash's sentence as the table says.
- **AC-49-01.3** 35-05's generator `--check`, its test_value_refusal_table.py and Q3505-1 pass, 33-10's Q3310-1 passes under `WP33_ONLY=S10` with no `VALUE_KNOWN` row keyed `plot:PT-7` left; TestHR17 passes.

## Tasks

**Commit boundary.** plot:PT-7: 49-01-01 (no commit), 49-01-02 (no commit), 49-01-03 (commit `Print twoway's line first, the option as typed (WP-49 plot:PT-7)`). plot:PT-6: 49-01-04 (no commit), 49-01-05 (commit `Print twoway's lines for tsset, glued weights and %tb lines (WP-49 plot:PT-6)`). 49-01-06 runs the area cscripts; 49-01-07 checks.

```xml
<task type="auto" id="49-01-01">
  <name>Measure refusals; write PT-7 failing cases</name>
  <files>scripts/extract_refusal_line_truth.do, test/test_option_validation.cscript, test/test_wp49_truth.cscript</files>
  <action><![CDATA[Create scripts/extract_refusal_line_truth.do with every key of "Stata truth", run it twice through scripts/stata_slot.sh with DASH_REPO set, git add -f test/fixtures/refusal_line_truth.json (staged). Add Q4901-1..5 to test/test_option_validation.cscript (each: capture noisily dash <command> under a text log; compare _rc and the log's first error line with the fixture's twoway values; Q4901-2 instead reads its five rows from test/fixtures/value_truth.json by id and asserts only that no error line follows the first, D-49-01.b; Q4901-4/5 compare the following lines with the base's dash lines recorded in the fixture's dash fields) and the S01 plot:PT-7 block. Run both through two-line drivers on the unmodified tree; save to <scratch>/49-01-01-failure.txt. In the same run, list every existing case whose expectation is a dash-worded first line into <scratch>/49-01-flips.txt, and write 49-01-02's work list with `python3 test/known_differences.py plot:PT-7 > <scratch>/49-01-known.txt`.]]></action>
  <verify><![CDATA[the cscript logs show Q4901-1 and Q4901-3 FAIL and Q4901-2, Q4901-4, Q4901-5 PASS (guards: 35-05 prints no second line on a value refusal, and the kept lines are the base's); the failure, flips and known files exist]]></verify>
  <done>The refusal fixture exists and plot:PT-7's cases fail on the unmodified tree.</done>
</task>

<task type="auto" id="49-01-02">
  <name>Close value refusals left in dash's words</name>
  <files>dash_parse.mata, dash.ado</files>
  <action><![CDATA[Take the work list from the `VALUE_KNOWN` rows (test/value_truth_known.py) in <scratch>/49-01-known.txt (D-49-01.b). For each row, run its value_truth.json `command` under dash (`twoway` replaced by `dash`) and compare dash's first line with the row's `message`: when they agree, nothing changes here (49-01-03 deletes the row); when they differ and the generated `tw_value` block of dash_parse.mata has no (option, types, class) row for it, run `python3 scripts/gen_value_refusal_table.py` (it reads the committed value_truth.json; no probe is added to scripts/extract_value_codes_truth.do and value_codes_truth.json is not touched), and stop and report the row if the block still lacks it (TR-35-05.1's class rule, 35-05's); when the block holds the row, print the refusal site's first line in dash.ado through `_dash_tw_value_msg` as `_dash_validate_value` does (TR-35-05.2), keeping its rc. Record each row and what closed it in <scratch>/49-01-values.txt ("none" when the list is empty).]]></action>
  <verify><![CDATA[python3 scripts/gen_value_refusal_table.py --check -> exit 0; python3 -m pytest test/test_value_refusal_table.py -q -n0 -> pass (35-05's test); Q3505-1 in test_option_validation.cscript -> PASS (value_codes_truth.json); test/test_wp33_truth.cscript with WP33_ONLY=S10 -> Q3310-1's only problems are rule-2 lines ("delete its row: plot:PT-7 fixed it") for the rows of <scratch>/49-01-known.txt, which 49-01-03 deletes; Q4901-2 PASS]]></verify>
  <done>Every value refusal's first line is twoway's, from 35-05's measured table.</done>
</task>

<task type="auto" id="49-01-03">
  <name>Rewrite first lines; flip; commit</name>
  <files>dash.ado, dash_parse.mata, dash.sthlp</files>
  <action><![CDATA[Add _dash_opt_typed and use it at every D-49-01.a site; rewrite the syn:SD-12 sites with the kept or dropped second line of D-49-01.c's table; rewrite item 5 and the applicability sentence (D-49-01.d) and add TestHR17 to test/test_false_sentences.py; create test/test_refusal_lines_p17.py with TestTheHelp. Flip every case in <scratch>/49-01-flips.txt to twoway's line, in the cscripts it names (test/test_option_validation.cscript, test/test_twoway_option_parity.cscript, test/test_parser.cscript and the test/test_help_claims_*.cscript files it lists). Close plot:PT-7 (BUGS names GW-8, ECO-11, sil:SD-9, syn:SD-12, TR-10 and records PD-11's scope and the P4-9 hint lines kept; GAPS4 Closed, commit pending; GAPS4_OPEN (test/test_tracking_documents.py) line deleted; CHANGELOG; TWOWAY_COVERAGE_AUDIT.md per TR-49-01.6). Before the commit take BRIEF's closing steps (1)-(3) for plot:PT-7 (Notes "Before every commit" gives each command in full): (1) delete plot:PT-7's plain rows of `$WT/scripts/corpus/ledger.tsv` (a `plot:PT-7 (documented)` or `plot:PT-7 (residual)` row stays, A-10), rerun `python3 $WT/scripts/corpus/ledger.py`, `git -C $WT add -f test/fixtures/corpus_ledger.json` and run test/test_corpus_ledger.py; (2) run `python3 $WT/test/known_differences.py plot:PT-7` and delete every row it prints from its `*_KNOWN` table (expected: the `VALUE_KNOWN` rows of <scratch>/49-01-known.txt, which 49-01-02 made agree, and any other table's row of a first line this task made twoway's) -- a difference plot:PT-7's ruling keeps moves instead into that table's deliberate dict (`DELIBERATE` for `VALUE_KNOWN`, `<NAME>_DELIBERATE` for any other `<NAME>_KNOWN`) as `"<key>": "<ruling id>: <what is kept>"` -- then run the hygiene command it prints; (3) run the S09 guard block of test/test_wp33_truth.cscript (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example (an improved verdict or a changed field), regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do, `git -C $WT add -f` it and commit it with plot:PT-7. Then take Notes' steps (4)-(6) (`git -C $WT pull --ff-only . main`, detect-changes, the message grep). Run Q4901-1..5, the S01 block, test_option_validation.cscript (Q3505-1 included), test/test_wp33_truth.cscript with WP33_ONLY=S10 (Q3310-1), test_twoway_option_parity.cscript, test_help_claims_*.cscript that hold refusal lines, test_refusal_lines_p17.py, test_false_sentences.py, test_value_refusal_table.py, test_program_coverage_map.py, test_cscript_hygiene.py, test_tracking_documents.py; commit.]]></action>
  <verify><![CDATA[the cscripts show "Q4901-1 PASS" .. "Q4901-5 PASS", "Q3505-1 PASS", "Q3310-1 PASS" and ALL CHECKS PASSED; python3 -m pytest test/test_refusal_lines_p17.py test/test_false_sentences.py test/test_value_refusal_table.py test/test_program_coverage_map.py test/test_tracking_documents.py test/test_corpus_ledger.py -q -n0 -> pass; subject ends "(WP-49 plot:PT-7)"; grep -ci 'claude\|anthropic' on the message -> 0]]></verify>
  <done>Every refusal's first line is twoway's with the typed spelling, dash's lines kept, and plot:PT-7 is committed.</done>
</task>

<task type="auto" id="49-01-04">
  <name>Write plot:PT-6 failing cases</name>
  <files>test/test_parser.cscript, test/test_wp49_truth.cscript</files>
  <action><![CDATA[Add Q4901-6..8 to test/test_parser.cscript (extend P1A-81's tsline row to compare the first line with the fixture) and the S01 plot:PT-6 block. Run on the tree as 49-01-03 left it; save to <scratch>/49-01-04-failure.txt.]]></action>
  <verify><![CDATA[the log shows Q4901-6, Q4901-7 (glued form) and Q4901-8 (%tb) FAIL; Q4901-7's after-varlist weight PASS]]></verify>
  <done>plot:PT-6's cases fail before the fix and are saved.</done>
</task>

<task type="auto" id="49-01-05">
  <name>Print twoway's tsset, weight and %tb lines</name>
  <files>dash.ado, dash_parse.mata</files>
  <action><![CDATA[Apply D-49-01.e (1)-(3), with the second lines of D-49-01.c's table. No help edit (TR-49-01.5). Flip the P1A-81 expectation in test/test_parser.cscript and any pin of "scatter[aw=price] is not a twoway plot type" or "invalid line argument" on %tb. Close plot:PT-6 (BUGS names plot:PT-8 and DG-10; GAPS4; GAPS4_OPEN (test/test_tracking_documents.py); CHANGELOG; TWOWAY_COVERAGE_AUDIT.md per TR-49-01.6). Before the commit take BRIEF's closing steps (1)-(3) for plot:PT-6 (Notes "Before every commit" gives each command in full): (1) delete plot:PT-6's plain rows of `$WT/scripts/corpus/ledger.tsv` (a `plot:PT-6 (documented)` or `plot:PT-6 (residual)` row stays, A-10), rerun `python3 $WT/scripts/corpus/ledger.py`, `git -C $WT add -f test/fixtures/corpus_ledger.json` and run test/test_corpus_ledger.py; (2) run `python3 $WT/test/known_differences.py plot:PT-6` and delete every row it prints from its `*_KNOWN` table -- a difference plot:PT-6's ruling keeps moves instead into that table's deliberate dict (`DELIBERATE` for `VALUE_KNOWN`, `<NAME>_DELIBERATE` for any other `<NAME>_KNOWN`) as `"<key>": "<ruling id>: <what is kept>"` -- then run the hygiene command it prints; (3) run the S09 guard block of test/test_wp33_truth.cscript (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example (an improved verdict or a changed field), regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do, `git -C $WT add -f` it and commit it with plot:PT-6. Then take Notes' steps (4)-(6) (`git -C $WT pull --ff-only . main`, detect-changes, the message grep). Run Q4901-6..8, test_parser.cscript, test_taxis_options.py, test_tracking_documents.py, the S01 block, test_option_validation.cscript; commit.]]></action>
  <verify><![CDATA[test_parser.cscript -> "Q4901-6 PASS", "Q4901-7 PASS", "Q4901-8 PASS", ALL CHECKS PASSED; python3 -m pytest test/test_taxis_options.py test/test_tracking_documents.py test/test_corpus_ledger.py -q -n0 -> pass; subject ends "(WP-49 plot:PT-6)"]]></verify>
  <done>tsline/tsrline, glued weights and %tb lines refuse with twoway's lines and plot:PT-6 is committed.</done>
</task>

<task type="auto" id="49-01-06">
  <name>Run every area cscript holding refusals</name>
  <files>none</files>
  <action><![CDATA[Run, one at a time through scripts/stata_slot.sh, test_option_validation.cscript, test_twoway_option_parity.cscript, test_parser.cscript, test_varlist_expansion.cscript, test_option_surface.cscript, every test_help_claims_*.cscript (grep -l "not allowed" test/*.cscript), test_wp49_truth.cscript with WP49_ONLY=S01, and test_wp33_truth.cscript with WP33_ONLY=S10 (33-10's Q3310-1 over value_truth.json).]]></action>
  <verify><![CDATA[each ends with its ALL CHECKS PASSED line (the WP-49 script with the S01 cases passing; the WP-33 script printing Q3310-1 PASS)]]></verify>
  <done>No refusal pin in any area script is left on dash's old words.</done>
</task>

<task type="auto" id="49-01-07">
  <name>Check the section end to end</name>
  <files>none</files>
  <action><![CDATA[Run test_refusal_lines_p17.py, test_false_sentences.py, test_value_refusal_table.py, test_help_conformance.py, test_tracking_documents.py, test_program_coverage_map.py and python3 scripts/gen_value_refusal_table.py --check; grep both commit messages for claude|anthropic. Write <scratch>/49-01-handback.txt naming the lines a merger may conflict on: _dash_validate_value (this section's var kind; 49-02 edits xsize(abc)'s note there only if 45-04's graphsize kind prints it, D-49-02.e) and _dash_process_segment (49-02 edits :6982; this section :5868, :6030, :6276).]]></action>
  <verify><![CDATA[all pass; grep count 0; the hand-back file exists]]></verify>
  <done>Both commits are green together.</done>
</task>
```

## Section completion criteria

- Two commits `(WP-49 plot:PT-7)`, `(WP-49 plot:PT-6)`; BUGS/GAPS4/CHANGELOG edited; `refusal_line_truth.json` committed by its script and named by a test; 35-05's generated value table current; TestHR17 in place.

## Notes

- **Traps.** (1) `_dash_say` writes in error colour and is the only echo of user text in a refusal: use it for every new first line that holds a typed word or value. (2) The `[` split: `gettoken ..., parse(" ,[")` returns `[` as its own token in `rest`'s head; test `substr(strltrim(rest), 1, 1) == "["`. (3) xsize()/ysize() rows are 49-02's (D-49-02.e: 45-04's three lines, pinned by its Q4504-2, and the non-number note): skip them here. (4) Never add a hint line where twoway prints one line and dash printed one line: PD-11 keeps existing dash lines, it does not add new ones (the dash sentence that becomes a second line is the existing one, D-49-01.c). The P4-9 hint lines WP-35/42 print for refused synonyms are existing lines at the WP-49 base and stay.
- **Help paragraphs this section owns (R3):** dash.sthlp item 5 (:980-1000) and the applicability sentence (~:1036); Appendix B HR-17. (No tsline help edit, TR-49-01.5.)
- **Owns beyond the manifest's cell (for the orchestrator; REVIEW-5 R5-37):** `_dash_process_segment` lines outside the per-type block (:5868, :6030, :6276), `_dash_validate_opts`, `_dash_validate_value`'s `var` kind (:4325), `_dash_taxis_unit`, the dash_parse.mata:3457 message. 49-02 edits xsize(abc)'s note (D-49-02.e; in `_dash_validate_value` only if the graphsize kind prints it) and `_dash_process_segment`'s :6982 in the same batch (different hunks).
- **Merge rules touched:** R1, R3, R4, R5, R6 (one Mata function; 35-05's generated table regenerated only if 49-01-02 regenerates it), R7, R9.
- **Before every commit (BRIEF "The corpus ledger and the known-differences tables" and "Pull form"; CLAUDE.md rules 4 and 6; R13; D-33-05.i, D-33-10.h, 33-09).** `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp49-s01`. Every item's closing task -- Fix, Document or Partly alike -- takes steps (1)-(3) for its lead id `<id>`, then (4)-(6): (1) list the item's plain ledger rows with `awk -F'\t' -v id='<id>' '$1 == id {print NR ": " $0}' $WT/scripts/corpus/ledger.tsv` and delete every line it prints (`<id> (documented)` and `<id> (residual)` rows stay, A-10), `git -C $WT add scripts/corpus/ledger.tsv` when a line was deleted, rerun `python3 $WT/scripts/corpus/ledger.py` (no `--run`: `_meta` is kept, TR-33-05.3), `git -C $WT add -f test/fixtures/corpus_ledger.json` and run `python3 -m pytest $WT/test/test_corpus_ledger.py -q -n0`; (2) run `python3 $WT/test/known_differences.py <id>` (33-10, D-33-10.h) and delete every `<file>:<line>` row it prints from its `*_KNOWN` table, staging each file it edits -- a difference the item's ruling keeps moves instead into that table's deliberate dict, 33-10's companion dict (`DELIBERATE` beside `VALUE_KNOWN` in test/value_truth_known.py; `ABBREV_DELIBERATE`, `SCALE_FRAME_DELIBERATE`, `BY_POSITION_DELIBERATE`, `BY_TYPES_DELIBERATE`, `COLORVAR_DELIBERATE` and `STAT_COMBOS_DELIBERATE` beside `ABBREV_KNOWN`, `SCALE_FRAME_KNOWN`, `BY_POSITION_KNOWN`, `BY_TYPES_KNOWN`, `COLORVAR_KNOWN` and `STAT_COMBOS_KNOWN`), as `"<key>": "<ruling id>: <what is kept>"`, the ruling id a DECISIONS or index id (P4-n, A-n, Q-n, M-n) -- then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`), which passes; (3) run the corpus guard block (test/test_wp33_truth.cscript with `WP33_ONLY=S09`, through BRIEF's two-line driver) and, if Q3309-1 reports any change for a guard example (an improved verdict or a changed field), regenerate the guard fixture with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s09 $WT/scripts/extract_corpus_guard_truth.do` (33-09), `git -C $WT add -f test/fixtures/corpus_guard_truth.json`, rerun the S09 block (Q3309-1 PASS) and add `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)` to the commit body; (4) pull from local main (CLAUDE.md rule 4): `git -C $WT pull --ff-only . main` (a no-op when the batch base already contains main); if it refuses, stop and report to the orchestrator, never a merge commit on a section branch; (5) run `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a `partial` or `truncated` result is run again) and name HIGH, CRITICAL or UNKNOWN risk in the hand-back; (6) grep the message for claude|anthropic before and after committing.
- **Commit-body lines:** `Regression: test/test_option_validation.cscript:Q4901-1 -- failed at <base sha> with <text>`; `Flipped: test/test_parser.cscript:P1A-81 -- dash's own first line was wrong because twoway prints "time variable not set, use tsset varname ..."`; `Fixture: test/fixtures/refusal_line_truth.json (scripts/extract_refusal_line_truth.do)`; `BUGS.md: "<title>" (closed)`; `GAPS4: plot:PT-7 Tracked`.
