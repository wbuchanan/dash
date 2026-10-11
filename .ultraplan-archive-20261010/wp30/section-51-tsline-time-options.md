# Section 51: tsline time-axis options (P1.6)

> Part of: WP-30 · Items: P1.6 (entry `P1.6`; REM-§2-S09-tlabel, REM-§2-S09-ttick, REM-§2-S09-tline, REM-§2-S09-ttitle, REM-S09-73-tsaxis-a, REM-S09-73-tsaxis-b, REM-05-04-S09-a, REM-05-04-S09-b, GAPS2-A4-q, GAPS2-B14-a, GAPS2-B14-b, GAPS2-B14-c, REM-15-03-E5) · Risk: yellow · Batch: 18 (merge order S51, S52, S53) · Depends on: 10, 18, 35 · Blocks: 56 · Tasks: 14, 2 commits (6a the fold on x axis 1, 6b axis(2), the format state and the `%-t` quirk) · Case prefix: TA

## Review amendments

- Fixed (major, executability): the unit-freeze row was added to TA-04 by 51-06 ("only if 51-02 did not already write it"), but 51-05's verify required TA-04 to pass before 51-06 wrote the freeze; it is now its own red-first case TA-16, written by 51-02 and turned green by 51-06, with every verify, AC-51.5 and the test plan updated.
- Fixed (major, batch boundary): S52's `tlabel(…, add)` cross case cannot run in S52's worktree, which lacks S51's fold. TA-02 now pins the fold of `tsline y, tlabel(2001m1, add)` to `"xlabel":"492, add"`, and S52 draws that spec (S52 amended to match); the Note explains the pair.
- Fixed (minor): `tscale(log)`'s note (BR-51.8) had no case; it is a TA-04 row.
- Fixed (minor): Notes name the adjacent `_dash_rep_subs`/`_dash_rep_merge` hunks shared with S52 (R6).
- Checked at HEAD: dash.ado pending blocks :786 and :1054, the seven key lists (:4274, :5066, :5100, :5200, :5272, :5304, :5602), the axis check :5318 and "Validate the graph-level values (WP-15)" :5327, `dash_fpts_` drops :6412 and :6875; Mata `_dash_rep_cat` 4664, `_dash_rep_subs` 5662, `_dash_axfam` 5352, `_dash_ax_parse` 5391, `_dash_route_axis2` 5486.
- Checked: M5 (each E4 refusal in twoway's rc and words; `tm()`/`ts()`), M6 (no note where twoway is silent), rule 1 (no token reaches `_stata()` or a command line; whitelist first; only numbers reach `numlist`); the truth block form; both commits' A156 handling of entry, key and markers.
- Checked (batch 18): S51 edits no function of S52 (`_dash_rep_merge`, `_dash_axis_pieces`, `_dash_axis_expand`'s comment, renderer axis code) or S53 (renderer by() code, extractor, scheme files); the pending and declared counts it moves are batch 18's alone.
- Cross-file (notes file): index R10's `:607` declared-plot row should list S51 (18), which declares the seven t-options in the plot parser too.
- Rejected: `<files>none</files>` in 51-09 (BRIEF allows the word none).
- The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:96 (P1.6): "`tlabel`, `ttick`, `tmlabel`, `tmtick`, `ttitle`, `tscale` and `tline` are undeclared and only named in the note. They need folding onto the x equivalents, with date-literal expansion." Measured at `c96facd` (research `.ultraplan/wp30/research/p1-06.md` §2 b, critic k1.do):

```
dash tsline y, tlabel(2000m1(12)2004m1) ttitle("Month") tline(2002m1) tscale(range(1999m1 2006m1)) ttick(2000m7(12)2004m7) name(g8)
  -> rc 0; "dash: ignoring unsupported option(s): tlabel() ttitle() tline() tscale() ttick()"; spec "graph_options":{"name":"g8"}
twoway: labels 2000m1..2004m1 at 480..528, x title Month, a line at 504, range widened to 466.69..553.31, ticks at 486..522 (c01, c05-c09)
dash tsline y, xlabel(2000m1)   -> rc 0 (twoway r(198) "invalid label specifier, :  2000m1(12)2004m1:" for c11's form)
dash tsline y, xline(2002m1)    -> rc 0 (twoway r(198) "invalid line argument, 2002m1", c12)
```

twoway honours the t-options on every twoway graph, not only tsline (c20, c21, c63-c65), reads date literals in the unit of the x axis's label format (`_date2elapsed.ado`), takes the T options after the X ones whatever the typing order (c14, c15, c35), and refuses them in measured words where the first plot makes the axis numeric (m6.do). `test/fixtures/rejected_options.json` still records `dash_rc 198` for them (stale; claim f).

**After this section**, in the saved page and the served app, before and after every filter move:
- `tlabel()`, `ttick()`, `ttitle()`, `tscale()` and `tline()` (and `tmlabel()`, `tmtick()`, stored and named until minor ticks are drawn, P2.2) are accepted on every twoway graph, with twoway's abbreviations, folded at registration onto `xlabel`, `xtick`, `xtitle`, `xscale`, `xline` (and `xmlabel`, `xmtick`) of x axis 1, after the X copies, with each date literal written as the Stata number twoway reads (`2002m1` → 504 on a `%tm` axis);
- the unit is the base format's (the first plot on the axis; numeric for lfit, qfit, lfitci, qfitci, lpoly, lpolyci, kdensity, function, scatteri, pci, pcarrowi, D1), then twoway's tickset format rules (`format()` overrides, D3) and its `%-t` quirk (D2);
- `tlabel2()`, `ttick2()`, `ttitle2()`, `tscale2()`, `tline2()` and `axis(2)` forms route to the second x axis with its own unit, and axis errors come in twoway's X, T, Y order and words;
- every input twoway refuses is refused with its rc and words (M5): date literals in x-options (r(198), r(198), r(121)), literals where the axis is numeric, invalid literals, `tm()`/`ts()` (P1.6.5), `%-t` lines and ranges, too many line positions (r(123));
- a date token is evaluated by Mata's string date functions only; no user text reaches `_stata()` or a command line;
- a later `format` change of the axis variable before `dash build` is noted (P1.6.7).

**Why one section, two commits.** All of it is P1.6 and lives in the Stata/Mata option path (manifest: "Stata and Mata only"); the renderer already draws Stata numbers on date axes in both modes and keeps them after a move (research §4, render_fold.py/render_move.py), and S35 makes mixed axes Stata-unit (p1-06 critic C1, register P1.6.9). Commit 1 (6a) declares, converts and folds onto x axis 1; commit 2 (6b) adds the axis-2 keys and routing, the X/T/Y order, the format state machine and the `%-t` quirk (research §8 split; A156).

**Test order and commit rule (rule 7, A156).** Two cycles on `wp30-s51`.
- **Commit 1:** 51-01 and 51-02 write the fixture and every commit-1 regression test and run them on the unmodified batch-18 base, saving `$S/51-P1.6-1-failure.txt` (no commit); 51-03 to 51-08 fix, flip and document; 51-09 runs the full suite and commits, leaving the BUGS.md entry, its `WP30_OPEN` key and both markers in place.
- **Commit 2:** 51-10 writes the commit-2 tests on the tree commit 1 left and saves `$S/51-P1.6-2-failure.txt`; 51-11 to 51-13 fix and document; 51-14 closes the entry, deletes the key, replaces both markers and commits.

No test-only commit exists, and no commit is red.

## Risk: [yellow] — the option path every dash command runs, in Stata and Mata only

**Why.** Every symbol edited is Stata or Mata, UNKNOWN to GitNexus (research §6: "Symbol not found"), confirmed by grep reference counts (dash.ado / dash_parse.mata / tests): `_dash_parse_graph_opts` 16/0/14, `_dash_parse_plot_opts` 19/0/16, `_dash_process_segment` 24/1/8, `_dash_plot` 23/3/12, `_dash_rep_cat` 0/5/1, `_dash_rep_subs` (inside `_dash_rep_merge`), `_dash_ax_parse` 0/6/1, `_dash_route_axis2` 4/3/4, `_dash_axreq_add`/`_dash_axreq_check` 3/5/1 and 2/5/1, `_dash_prepare_spec` (the build path). Treated as HIGH: every dash command parses options through them. Renderer readers relied on and not edited: `_dash_parse_axis_spec` CRITICAL (8), `_dash_date_axis_spec` HIGH (5).

**Risk factors.**
1. A new declaration can steal an abbreviation from an existing option (`t()` is `T1title`'s; `tti()` must read as ttitle; `tm()`/`ts()` must stay undeclared).
2. Converting user text by building Stata commands would be a command-injection path (critic C3).
3. "Number first": `01012001` is a number to twoway (critic C2); a converter that tries dates first would move it.
4. The seven graph-key lists of dash.ado must stay in step (`test_abbreviations.py::…::test_the_seven_graph_key_lists_agree`).
5. Pending and declared counts are pinned (R10) and moved by S56 in batch 19 too.
6. A mixed x axis (a `%tm` layer beside a numeric one) needs S35's Stata-unit drawing (critic C1).

**Mitigation.**
1. TA-03 replays twoway's abbreviation table (research §3.3) with `-syntax-` on both parsers; `t()`, `tm()`, `ts()` are pinned.
2. Mata's `date()`, `weekly()`, `monthly()`, `quarterly()`, `halfyearly()`, `yearly()` take the token as a string (same values on 78 tokens, critic C3); a whitelist gate precedes them; `TestNoStataCallTakesUserText` scans the new functions for `_stata(`/`stata(`.
3. `_dash_tdate_value` tries `strtoreal` first; TA-08 holds critic C2's `tlabel(15000 01012001)`.
4. 51-03 edits all seven lists in one task; the guard runs there.
5. Each count is re-derived on the worktree with a `# <old> -> <new>: P1.6 …` comment; the merger re-derives after S56 (R10).
6. Hard dependency on S35 (batch 12); `TestAMixedAxis` covers both modes.

## Dependencies

- **Depends on: 10, 18, 35.**
  - S10 (batch 4): the sub-option tables and abbreviations the folded values are read with (`tline(…, lc(red))` reaches `xline` as typed and is resolved there).
  - S18 (batch 6): `format()` on date and numeric axes (D3's labels: `line y n, xlabel(, format(%tm)) tline(2002m1)` labels in `%tm` only with S18; critic C7).
  - S35 (batch 12): Stata units on a mixed axis and on y2/x2 date kinds; S35's Notes: "a `t*` option with `axis(2)` reads `_dash_axis_date_kind(fig, "x2")`, and a folded date literal on a mixed axis is a Stata value".
  - Landed before and read here: S03 (`version 19` in every new program), S06 (notes' `(note: …)` form), S31 (`axislist` validation the folded keys inherit; S31's draw-time bounds `_dash_axbound_list` read `g_xlabel` after the fold), S39 (`xline` positions, refusals and `lstyle`; the fold writes explicit numbers, research claim "P1.21 is live"), S42 (operators: an operated x keeps its base variable's format, measured below).
  - S01 provides the entry `P1.6`, its `WP30_OPEN` key, the markers `<!-- WP-30 P1.6 -->` at the end of `### New` and of `### Changed behaviour (may need your do-files changed)`, the S51 stub `* ==== S51 P1.6: tsline time-axis options ====` and the anchors `# WP-30 S51 (P1.6): tsline time-axis options (P1.6)`.
- **Blocks: 56.** S56's `ttext()` reuses `_dash_tdate_value` and the unit rule (manifest notes).
- **Parallel batch: 18**, merge order S51, S52, S53. S51 lands first.
- **Can run with:** S52 (renderer `add`; Mata `_dash_rep_merge`, `_dash_axis_pieces`; dash.ado `_dash_axis_expand`'s comment) and S53 (renderer by() axes and keys). S51 edits none of their functions; S52 edits none of S51's (`_dash_rep_cat`, `_dash_rep_subs` and the axis-request functions stay S51's). A folded `tlabel(…, add)` inherits S52's merge and union once S52 lands; the cross case is S51's TA-02 fold pin with S52's AD-22 (Notes).

## Evidence

Anchors are at `c96facd` (dash.ado 8,487 lines, dash_parse.mata 6,093, dash.sthlp 3,822); S03-S50 move many. The executor re-finds each by symbol at `batch-18-base`.

### E1. Undeclared (dash.ado)

`grep -w` for tlabel/ttick/tmlabel/tmtick/ttitle/tscale/tline in dash.ado, dash_parse.mata and dash_render.py finds 0 hits (claim a; critic re-confirmed). The graph parser's syntax (`_dash_parse_graph_opts` 682, block :714-740) and the plot parser's (`_dash_parse_plot_opts` 897, :924-985) end in the catch-all `*` (:817, :1134), and the pending blocks begin at :786 (graph) and :1054 (plot):

```stata
786    local _dash_pending ""
787    if `: length local b1title' local _dash_pending `"`_dash_pending' b1title"'
```

The seven key lists (`foreach gkey in` :4274; `foreach gk in` :5066, :5100, :5200, :5272, :5304, :5602) name every graph key; the merge loops at :5272-5287 (segments) and :5304-5312 (after the comma) call `_dash_rep_merge_locals`. The axis check is at :5318-5325, then "Validate the graph-level values (WP-15)" at :5327.

### E2. The merge categories and the axis family table (dash_parse.mata)

`_dash_rep_cat` (:4664) maps xlabel…zlabel to "L", titles to "T", scales to "S", lines to "X" and everything else to "R"; the t keys fall to "R" today. `_dash_rep_subs` (:5662-5710) unions numeric `range()`s on "S" and keeps only the last `range()` when one is not a number (`ok = 0`), which would lose `tscale(range(1999m1)) tscale(range(2006m1))`. `_dash_axfam` (:5352) holds the seven families with twoway's minimums; `_dash_ax_parse` (:5391) accepts the side letters x and y; `_dash_route_axis2` (:5486) writes `<side><fam>2`; `_dash_axreq_add` (:5560) codes the side for the X-then-Y order of `_dash_axreq_check`.

### E3. The renderer already draws Stata numbers on date axes (research §4, quoted)

```
fold_all  saved   spans=['2002m1'] extra=['2000m7','2001m7','2002m7','2003m7'] range=(463.81, 556.23) title='Month'
fold_all  served  spans=['2002m1'] extra=['2000m7','2001m7','2002m7','2003m7'] range=(463.81, 556.23) title='Month'
xline_rule saved/served  spans=[]  note 'dash: xline() sub-option(s) not implemented and ignored: 492(12)516'
served before/after a move (['2002m1'], ['2000m1',…,'2004m1'], (463, 556), 'Month')
```

So the fold writes explicit numbers for lines (a rule is expanded with `numlist`), and `A(d)B` rules for labels and ticks, which `_dash_parse_axis_spec` expands.

### E4. twoway's truth (StataNow 19.5; research §3, critic additions)

- Behaviour: c00-c65 (labels, titles, ranges, lines), §3.2 order (X, then T, then Y; a later copy replaces unless `add`; lines accumulate), §3.3 abbreviations (`tl`/`tlab`/`tlabels`, `tt`/`tti`/`ttit`, `tli`/`tlin`/`tlines`, `ttic`/`ttick`/`tticks`, `tsc`/`tsca`, `tml`, `tmt`; `tm` and `ts` r(198) "option tm() not allowed"/"option ts() not allowed").
- Units (§3.4): `%td` d(), `%tw` w(), `%tm` m(), `%tq` q(), `%th` h(), `%ty` numbers; `%tc`, `%tC`, `%tb` and numeric formats take numbers only (`invalid ticklist "2000m1" must be number`; `tline`: `invalid number, (2002m1)` on a numeric axis f01); `%tmMon_CCYY` still reads m() literals (e31); the first plot decides (m6.do: rc 198 when it is lfit, qfit, lfitci, qfitci, lpoly, lpolyci, kdensity, function, scatteri, pci or pcarrowi; rc 0 for the other 29 types); pc types take x1's unit (critic C4).
- format() (§3.4, m5.do k01-k06): `line y n, xlabel(, format(%tm)) tline(2002m1)` works on an unformatted n; `tsline y, xlabel(, format(%td)) tline(2002m1)` is r(198) with the d() message; `tlabel(2001m1 2003m1, format(%tm))` on n is r(198) (an option's own format applies after its positions); `tlabel(, format(%tm)) tline(2002m1)` works (labels before lines). axis.class:1046-1057 `get_time_format` and tickset_g.class:1129-1180.
- `%-t` (m4.do): with `format t %-tm`, `tlabel(2001m1 2003m1)` works (g01); `tline(2002m1)` r(198) "invalid number, (2002m1)" (g02, g04); `tscale(range(2006m1))` r(121) (g03).
- Leniency (§3.5): `2000x1`, `2000/1`, `2000-1`, `2000+1`, `2000*1`, `2000@1`, `2000=1`, `2000M1` → 480; `1+jan+2000`, `1january2000`, `01JAN2000` → 14610; rejected `2000m13`, `2000m0`, `99m1`, `2000m1x`, `-2000m1`, `10000m1`, `2000-01-01`, `2000w53`.
- Refusals (§3.6): e01 `tlabel(foo)` `invalid label specifier, :  foo:`; e04 `tlabel(2000m13)` `invalid ticklist "2000m13" must be a number or valid argument for m() function`; e10, e19, e27, e28; e02 `tline(foo)` `invalid line argument, foo`; e08; e05 `tline(2000m13)` `invalid argument "2000m13" must be a number or valid argument for m() function`; e18; f01; e03 `tscale(range(foo))` r(121) `range() invalid -- invalid numlist`; f09 `tlabels(2001m1, axis(3)) not allowed, xaxis3 does not exist`; f10 `tlines(2002m1, axis(2)) not allowed, xaxis2 does not exist`; f14 `invalid 'foo'`; f11/k08 r(133) (twoway's own `xtitle(…, axis(2))` bug, handled for xtitle); m8 `tline(2000m1(1)2400m1)` r(123) `invalid numlist has too many elements` (1,201 positions are rc 0).
- Number first (critic C2): `tlabel(15000 01012001)` keeps 1012001; `tline(01012001 01jul2001)` equals `tline(1012001 01jul2001)`.
- x-options (§2 new findings): `xlabel(2000m1(12)2004m1)` r(198) `invalid label specifier, :  2000m1(12)2004m1:` (c11); `xline(2002m1)` r(198) `invalid line argument, 2002m1` (c12); `xscale(range(1999m1 2006m1))` r(121) `range() invalid -- invalid numlist` (c13).

Measured for this file (`$S/s51-53/probe.do` through `scripts/stata_slot.sh`, 04oct2026; the operator x the research left UNCLEAR, critic C7):

```
tsset t (%tm), y = 100+_n:
T|line y L.t, tline(2002m1)|0              xaxis1 major 480 498 516 534
T|line y L.t, tlabel(2001m1 2003m1)|0      xaxis1 major 492 516
T|line y D.t, tlabel(2001m1)|0             xaxis1 major 492
```

An operated x keeps its base variable's `%tm` unit.

### E5. Stale records and tests

- `test/fixtures/rejected_options.json`: `rejected_options[91]`-`[95]`, `[97]`, `[98]` (tlabel, tline, tmlabel, tmtick, tscale, ttick, ttitle; `[96]` is ttext, S56's) and `probes[264]`, `[266]`-`[271]` record `dash_rc 198`, `dash_message "option tlabel() not allowed"`, disposition `implement-S09-axes-text`; `summary.by_disposition["implement-S09-axes-text"]` is 28. O2-03 of `test_option_surface.cscript` reads only `accept-and-report` rows (:575), so it is unaffected.
- No test names a t-option today (`grep -rn 'tlabel\|ttitle(\|tline(\|tscale(\|ttick(' test/` finds none at `c96facd`).
- Pins that move (R10; re-measured at 51-07/51-13, never trusted): `test/test_unsupported_report_is_true.py::TestTheListIsCoveredAndHonest::test_the_blocks_were_actually_found` (:240 plot pending, :241 graph pending), the declared counts (:607 plot, :608 graph); `test/test_help_conformance.py::TestTheParsersFoundSomething` (:590 declarations, :598 ignored, :604 unsupported); `test/test_help_claims_8.py`'s Unsupported equality pin; `test_abbreviations.py::…::test_the_seven_graph_key_lists_agree` (kept green, not flipped).

## User stories

- **US-51.1** As a twoway user with time series, I want `tsline y, tlabel(2000m1(12)2004m1) ttitle("Month") tline(2002m1) tscale(range(1999m1 2006m1))` drawn as Stata draws it, in the saved page and the served app and after a filter move.
- **US-51.2** As a twoway user, I want the t-options on any twoway graph (`scatter mpg weight, tlabel(2000 3000 4000)`), since twoway accepts them there.
- **US-51.3** As a twoway user, I want dash to refuse what twoway refuses (a date literal in `xlabel()`, `tline(2000m13)`, `tlabel(2001m1)` after an lfit first plot) with twoway's words, so a do-file fails the same way in both.
- **US-51.4** As a twoway user with two time axes, I want `tlabel(…, axis(2))` and `tline2()` on the second x axis in its own unit.
- **US-51.5** As a maintainer, I want no user-typed date token ever evaluated as Stata code.

## Business requirements

- **BR-51.1** The seven t-options are accepted on every twoway graph with twoway's abbreviations (E4 §3.3), in a plot segment or after the comma, and act on x axis 1 as the matching x-option would, taking effect after every x copy; `tlabel`/`ttick`/`ttitle`/`tscale` copies replace or merge as twoway's do, `tline` copies accumulate.
- **BR-51.2** A date literal is read in the unit of the axis's label format: the first plot's x variable's format, numeric for the eleven E4 types, x1's for the pc types, the base variable's for an operated x; numbers stay numbers (number first); twoway's lenient literals are accepted and its invalid ones refused.
- **BR-51.3** `tmlabel()`/`tmtick()` are stored on the x minor keys and named as not drawn until minor ticks are (P2.2).
- **BR-51.4** Refused with twoway's rc and words: the §3.6 table; date literals in `xlabel`/`xtick`/`xmlabel`/`xmtick`/`xline`/`xscale(range())` and their axis-2 forms; `tm()` and `ts()`; date literals on a numeric axis.
- **BR-51.5** (commit 2) `axis(2)` and the `t…2()` spellings route to x axis 2 with its own unit; axis errors come in X, T, Y order with twoway's words; `format()` overrides follow twoway's tickset rules; `%-t` is accepted in labels and ticks and refused in lines and ranges.
- **BR-51.6** A token is evaluated without running user text as Stata code.
- **BR-51.7** When a t-option was folded and the axis variable's date kind at `dash build` differs from the one at registration, dash notes it once and draws the registered values.
- **BR-51.8** `tscale(log)` on a date axis is noted as `xscale(log)` is today (P1.6.8); `tscale(reverse)`, two-line and empty `ttitle()` match twoway (critic C6).
- **BR-51.9** The help lists every t-option, the unit rule and the refusals.

## Technical requirements

### Commit 1 (6a): the fold on x axis 1

- **TR-51.1 Declarations** (dash.ado; both syntax blocks, beside the X options, in the hand-edited form the parser's header comment requires, never through `scripts/regen_option_surface.py`): `TLabel(string asis) TTICk(string asis) TMLabel(string asis) TMTick(string asis) TSCale(string asis) TTitle(string asis) TLIne(string asis)`. The capitals are twoway's measured minimums (`tl`, `ttic`, `tml`, `tmt`, `tsc`, `tt`, `tli`); `tti` reads as ttitle (TTICk needs `ttic`); `t()` still reaches `T1title`; `tm()` and `ts()` still fall to `*`. Each gets `sreturn local <name> : copy local <name>` in both sreturn blocks, beside `xlabel`'s, and joins all seven key lists (E1) after `xmlabel ymlabel`. Pending lines (graph block :786, plot block :1054): `tmlabel` and `tmtick`, with a comment "stored on xmlabel/xmtick; drawn when minor ticks are (P2.2)".
- **TR-51.2 `_seg_xvar_out`** (`_dash_process_segment`, in place): a new `c_local _seg_xvar_out` beside `_seg_xaxis_out`, the variable the x axis takes its format from: `xvar` for yx types and range types (tsrline: the tsset variable, as the tsline branch sets it, :3801-3812); `var` for histogram and kdensity; `x1var` for pc types (critic C4); `""` for function, scatteri, pci, pcarrowi; for an S42 operator expression the base variable's name (E4's operator probe). `_dash_plot` collects per segment `_tx_var<k>`, `_tx_type<k>`, `_tx_ax<k>` (x axis number).
- **TR-51.3 Mata, merge categories** (dash_parse.mata, in place): `_dash_rep_cat` maps tlabel, ttick, tmlabel, tmtick to "L", ttitle to "T", tline to "X", tscale to "S" (and, in commit 2, their `2` forms alike). `_dash_rep_subs`: on "S", when `nr > 1` and `!ok` (a non-numeric `range()`), the kept `range()` word is `range(` + every range word's value tokens in order + `)` instead of the last one; numeric unions are unchanged. For xscale the joined word is then refused by TR-51.6 exactly as one non-numeric range is. `_dash_rep_merge` is not edited (S52's).
- **TR-51.4 Mata, the converter** (new functions in dash_parse.mata directly after `_dash_axreq_check`, each with a comment block in the file's form, a header-index entry and a `_needed` name; no regex; linear in the value's length; values read with `st_local`, results written with `st_local`; never `_stata()` or `stata()`):
  - `string scalar _dash_taxis_unit(string scalar fmt, real scalar family)`: family 1 (label/tick ticksets, `_date2elapsed`'s map) or 2 (lines and scale, `get_time_format`). Strip one leading `%`; family 2 returns `""` unless the first two characters of `fmt` are `%t` or `%d`; then `-` is skipped for family 1 only; `d`/`td` → `"d"`, `tw` → `"w"`, `tm` → `"m"`, `tq` → `"q"`, `th` → `"h"`, `ty` → `"y"`; `tc`, `tC`, `tb` and every numeric format → `""`.
  - `real scalar _dash_tdate_value(string scalar tok, string scalar unit, real scalar val)` → 1 number or date (sets `val`), 2 a date in some unit but not in `unit` (or `unit` empty), 3 neither. Order (critic C2, C3): `strtoreal(tok)` not missing, or `tok` a missing-value literal (`.`, `.a`-`.z`) → 1. Gate: length 1-40 and every character in `0-9 A-Z a-z . + - * / @ = _` (whitelist; anything else → 3, never evaluated). Then `v = (unit == "d" ? date(tok, "DMY") : unit == "w" ? weekly(tok, "YW") : unit == "m" ? monthly(tok, "YM") : unit == "q" ? quarterly(tok, "YQ") : unit == "h" ? halfyearly(tok, "YH") : .)` (`unit == "y"` has no literal form: numbers only); an integer `v` → 1. Otherwise 2 when any of the five functions gives an integer for `tok`, else 3.
  - `void _dash_tdate_ticks(string scalar opt, string scalar unit)`: reads the caller's local `_td_in` (a label/tick option value), writes `_td_out` (the converted value), `_td_rc` (0, 198) and `_td_msg` (twoway's first error line). Grammar (twoway's tickset: Rules then NumTextList with datesok): the head (before the sub-option comma, cut as `_dash_axis_pieces` cuts it) is `#N`, `##N`, `minmax`, `none`, `.` (copied), or a list of: a position (optionally in parentheses), an `A(d)B` rule whose ends are positions (`2000m1(12)2004m1`, `(2000m1)(12)(2004m1)`), and a quoted label after a single position. Each position goes through `_dash_tdate_value`; 1 writes `strofreal(val, "%21.0g")`; 2 and 3 set the measured messages (E4: a token that is neither → `invalid label specifier, :  <tok>:`; a date not of this unit → `invalid ticklist "<tok>" must be a number or valid argument for <u>() function`, or on a numeric axis `invalid ticklist "<tok>" must be number`). The tail (sub-options) is copied unchanged.
  - `void _dash_tdate_lines(string scalar unit)`: reads `_td_in` (a tline value), writes `_td_out` as a numlist text (`A(d)B` rules with converted ends, positions converted), `_td_rc`/`_td_msg` (E4: `invalid line argument, <list>`, `invalid argument "<tok>" must be a number or valid argument for <u>() function`, `invalid number, (<tok>)` on a numeric or `%-t` axis); the tail is copied.
  - `void _dash_tdate_range(string scalar unit)`: reads `_td_in` (a tscale value); every `range()` word's tokens converted; their union becomes one `range(lo hi)`; other words copied; a failure sets `_td_rc` 121 and `range() invalid -- invalid numlist`.
  - `real scalar _dash_xdate_find(string scalar v, real scalar family)`: 1 when the value of an x label/tick (family 1), line (2) or scale (3) option holds, in a position slot, a token that `_dash_tdate_value(tok, "", val)` rates 2 (a date literal); it sets the caller's local `_xd_tok` to the token (the whole rule for an `A(d)B` rule, c11).
- **TR-51.5 New ado `_dash_taxis_fold`** (dash.ado, directly after `_dash_plot`'s `end`; `version 19`; not sclass; never touches `s()`), called in `_dash_plot` after the axis check (:5318-5325) and before "Validate the graph-level values (WP-15)" (:5327):
  1. **x-option literals (M5, P1.6.4).** For each of `g_xlabel`, `g_xtick`, `g_xmlabel`, `g_xmtick` (family 1), `g_xline` (2), `g_xscale` (3) and the axis-2 x keys `g_xlabel2`, `g_xtick2`, `g_xline2`, `g_xscale2`: `_dash_xdate_find`; a hit → twoway's message through `_dash_say("err", …)` (`invalid label specifier, :  <tok>:`, `invalid line argument, <tok>`, `range() invalid -- invalid numlist`) and `exit 198` (121 for the scale). This runs before the T keys are folded, so converted T values never meet it.
  2. **Base unit per x axis a ∈ {1, 2}.** The first segment with `_tx_ax<k> == a`: its type in `lfit qfit lfitci qfitci lpoly lpolyci kdensity function scatteri pci pcarrowi` or an empty `_tx_var<k>` → base format `""`; otherwise `: format <var>`. (Commit 1 uses the base format for every family; commit 2 adds TR-51.12.)
  3. **Families in twoway's order** scale, label, mlabel, tick, mtick, title, line, each only when `g_t<fam>` is non-blank: a value holding an axis word (`ax`, `axi`, `axis` then `(`) is left unfolded in commit 1 and its option named in the ignoring note (commit 2 routes it); otherwise `local _td_in : copy local g_t<fam>`, the converter for the family (`_dash_tdate_range`, `_dash_tdate_ticks`, `_dash_tdate_lines`; title copied) with `_dash_taxis_unit(base, family)`; `_td_rc` non-zero → `_dash_say` the message, `exit _td_rc`. Lines: the converted list is expanded by `capture noisily numlist "<_td_out head>"` (converted numbers only reach the command line; numlist's own default limit gives twoway's r(123) `invalid numlist has too many elements`, m8), and the result written back with the tail.
  4. **Merge into x.** `mata: _dash_rep_merge_locals("<x key>", "g_x<fam>", "_td_out", "g_x<fam>")` (T after X, c14/c15/c35; lines accumulate, c36/c46), then `local g_t<fam> ""`, so the spec never carries a t key.
  5. **`tm()`/`ts()`** (P1.6.5). Before the ignoring note is printed (`_dash_plot`'s report of `_dash_ignored_acc`), an ignored token whose name is exactly `tm` or `ts` (case as typed, before `(`) → `display as error "option tm() not allowed"` (or `ts()`) and `exit 198`.
  6. **Unit freeze (P1.6.7, A18).** When any family was folded with a non-empty unit, `global dash_tunit_<name> "<a>:<var>:<unit> …"`; dropped with `capture macro drop dash_tunit_<name>` where `dash_fpts_<name>` is dropped on re-registration (:6412) and with `capture macro drop dash_tunit_*` beside :6875 (`dash clear`). In `_dash_prepare_spec`'s graph loop (:7589-7619), for each stored triple, `_dash_taxis_unit(: format <var>, 1)` differing from `<unit>` (or the variable gone) → once per graph: `_dash_say("txt", "(note: graph <name>: the t-options' dates were read as <unit>() dates when it was registered; <var> now has another date format, and they are drawn at the registered values)", …)`. The name and variable are Stata names; the message goes through `_dash_say`.
- **TR-51.6 Help** (R3: Axis and Display Options and Unsupported, S51's in batch 18; S52 edits other sentences of Axis and Display and lands after):
  - A new `{marker taxis}{...}` paragraph group "Time-axis options" after the axis-title paragraphs: the seven options and twoway's abbreviations; that they act on x axis 1 on every twoway graph and are read after the x options; date literals in the unit of the axis's format, numbers first, the first-plot rule (the eleven types), pc types' x1; `tmlabel()`/`tmtick()` stored and named until minor ticks are drawn; `tscale(log)` on a date axis noted as `xscale(log)` is; the refusals (x-option literals, `tm()`, `ts()`); the build-time note of BR-51.7. Commit 2 adds the `axis(2)`/`t…2()` forms, the `format()` rule and the `%-t` rule.
  - Unsupported "Minor ticks and minor labels." (:3629): `{opt tmlabel()}` and `{opt tmtick()}` beside `xmlabel()`/`xmtick()`.
  - Every line at most 79 characters; no tool or vendor name.
- **TR-51.7 Records** (A145: S51 owns its own stale rows). `test/fixtures/rejected_options.json` (not generated by any script; edited in place, values only, pretty-printing kept): `rejected_options[91]`-`[95]`, `[97]`, `[98]` and `probes[264]`, `[266]`-`[271]`: `dash_rc` 0, `dash_message` `""`, disposition `"implemented-WP-30-P1.6"` (tmlabel and tmtick: `"stored-and-named-WP-30-P1.6"`), `reason` one sentence naming WP-30 P1.6; `summary.by_disposition["implement-S09-axes-text"]` 28 → 21 with the two new keys counted; `summary.dash_failures` re-derived from `probes`. Located by `id`/`option`, never by index alone.
- **TR-51.8 Registries.** `test/program_coverage_map.py` `COVERAGE["dash.ado"]` under S51's anchor: `"_dash_taxis_fold": ("test_twoway_option_parity.cscript:TA-01", "test_twoway_option_parity.cscript:TA-05")`; `COVERAGE["dash_parse.mata"]` under S51's anchor: `_dash_taxis_unit` (TA-04), `_dash_tdate_value` (TA-08, TA-09), `_dash_tdate_ticks` (TA-01), `_dash_tdate_lines` (TA-05), `_dash_tdate_range` (TA-02), `_dash_xdate_find` (TA-15), each as `("test_twoway_option_parity.cscript:TA-nn",)`. `_needed` (dash.ado:237-255) gains the six Mata names. No `function_test_map.py` entry (no Python function); no served copy list change (R2 row S51).
- **TR-51.9 Security (rule 1; G9).** The threat closed is command injection through a date token: no token reaches `_stata()`, `stata()`, a macro expansion or a command line; Mata's string date functions read it as data; the whitelist gate runs first; the only command line built is `numlist` over numbers `strofreal` wrote. Every echo goes through `_dash_say` (user text shown as typed). The converter is linear and regex-free; `TestTheConverterIsLinear` bounds 10,000 positions under 2 s through the cscript TA-09.

### Commit 2 (6b): axis(2), the X/T/Y order, format() and `%-t`

- **TR-51.10 Axis-2 keys** (dash.ado): `TLABEL2(string asis) TTICK2(string asis) TLINE2(string asis) TSCALE2(string asis) TTITLE2(string asis)` in both syntax blocks (dash's spellings, as `XLABEL2` is), sreturn, the seven key lists, and the fold for axis 2 into `g_xlabel2`, `g_xtick2`, `g_xline2`, `g_xscale2`, `g_xtitle2` with axis 2's own base unit (f07/f08).
- **TR-51.11 Mata routing** (in place): `_dash_ax_parse` accepts the side letter `t` (outside `_dash_axfam`, whose rows are unchanged, so `test_abbreviations.py`'s `_dash_axfam` assertions stand) and returns twoway's plural name for messages (`tlabels`, `tlines`); `_dash_route_axis2` renames the plurals (`tlabels(` → `tlabel(`) and writes `t<fam>2(` for axis 2 (axis 1 drops the word); `_dash_axreq_add` codes the side 1 = x, 2 = t, 3 = y, reads t rows against the x axes and words them `t<fam>s(<v>) not allowed, xaxis<n> does not exist` (f09, f10, f12, f13); `_dash_axreq_check` orders by that code. `ttitle(…, axis(2))` follows `xtitle`'s existing route for twoway's r(133) (f11/k08).
- **TR-51.12 The format state** (D3; in `_dash_taxis_fold`): per x axis, four tickset formats {major, minor, majornl, minornl} start at the base format; the last `format()` in the merged `g_xlabel`, `g_xmlabel`, `g_xtick`, `g_xmtick` (axis-matched) replaces its tickset's; each label/tick family converts in its own tickset's format, then its own option's `format()` replaces that tickset's (k03, k04); lines and the scale take `get_time_format`: the first of major, minor, majornl, minornl whose first two characters are `%t` or `%d`, through `_dash_taxis_unit(…, 2)`.
- **TR-51.13 `%-t`** (D2): falls out of TR-51.4's family rule: family 1 reads `%-tm` as m (g01); family 2 does not, so `tline(2002m1)` is r(198) `invalid number, (2002m1)` and `tscale(range(2006m1))` r(121) (g02-g04).
- **TR-51.14 Help (commit 2):** the `taxis` group gains the axis-2 forms, the format rule and the `%-t` rule; Unsupported is unchanged.

## Boundaries

- **Batch partners:** S52 owns `_dash_rep_merge`, `_dash_axis_pieces`, `_dash_axis_expand`'s comment, the renderer `add` and the finishers; S53 owns the by() renderer code, the extractor and scheme files. S51 edits none.
- **Not edited:** dash_render.py (no renderer, template or copy-list change; manifest), `_dash_parse_axis_spec`, `_dash_date_axis_spec`, `_dash_rep_merge`, `_dash_axis_expand`, `_dash_axfam`'s rows, `scripts/regen_option_surface.py` (IR-7), S31's `_dash_axbound_list`.
- **Not this section's:** `ttext()` (S56, reusing `_dash_tdate_value`); drawing minor ticks (P2.2); `xlabel(#3)`'s date counts (P2.19, S44); y-options with date literals (the same refusal for `ylabel(2000m1)` is not swept, P2.21); `tscale(log)` drawn (inherited divergence).
- **Tracking documents:** S58 only (A145), except the rows of TR-51.7.

## Stata truth

New extractor `scripts/extract_taxis_truth.do` → `test/fixtures/taxis_truth.json`, in S02's path-free form (TR-02.9 stanza; `adopath ++ "`repo'/"`, `global dash_nobrowser 1`, `set graphics off`, `version 19`), `_meta` as S37's extractors write it (`stata_version`, `born_date`, `dash_commit` via `shell` into a tempfile, `extracted`; python never calls Stata, no `shell=True`, a backtick as `\x60`). Written in commit 1 with every probe both commits read.

- **Data:** research m1.do's 60 months (`t = tm(2000m1)+_n-1`, `%tm`, `tsset t`, `y = 100+_n`, `n = _n`, `d = dofm(t)` `%td`, `t2 = t` `%-tm`); `sysuse auto` for c20-c22, c63-c65.
- **Probes:** every id of E4 (c00-c65, e01-e36, f01-f14, g01-g04, h05-h06, k01-k08, m6.do's 40 first-plot types, m8, the §3.5 literals via `scalar s = m(…)`, critic C2's d1/e1/e3 and C4's pc case, the three operator probes), each `capture noisily twoway …` inside a named log (`log using … name(_ta)`), recording `rc` and the first error line; plus the x-option literal probes `xlabel(2000m1)`, `xtick(2000m1)`, `xmlabel(2000m1)`, `xmtick(2000m1)`, `xline(2002m1)`, `xscale(range(1999m1 2006m1))` and their axis-2 forms on a two-x-axis graph.
- **Records for rc 0:** `.Graph.xaxis1.major.dlg_tickpos` and `majornl` (research p1-18's `_rec`), `.Graph.plotregion1.xscale.curmin/curmax`, the x title text, and the vertical reference lines read from the exported SVG through `scripts/svg_truth.py` (`svg_lines` or its nearest reader).
- **Run:** `DASH_REPO="$WT" "$SLOT" "$S" "$WT/scripts/extract_taxis_truth.do"` (log `$S/extract_taxis_truth.log`; about 230 probes). `git add -f test/fixtures/taxis_truth.json`.

**Area cases, `test/test_twoway_option_parity.cscript`** (R1; one contiguous run after the last case block before `// Summary`, headed `// TA: the t-options, read as twoway reads them (WP-30 P1.6)`). Each case runs live twoway (`capture twoway … nodraw`, rc and first error line from a log) and dash (`_ztp_run`, the spec from `$dash_json_<name>`), in the script's `nfail`/`faillist` form:
- **TA-01** the Overview's command: each option folds to its x key with converted values, as stored after `_dash_axis_expand` (`"xlabel":"480 492 504 516 528"`, `"xtick":"486 498 510 522 534"`, `"xline":"504"`, `"xscale":"range(468 552)"`, and `xtitle` exactly as `xtitle("Month")` stores it), and the note names none of tlabel ttick ttitle tscale tline. **TA-02** order and merging (c14, c15, c34, c35, c35b, c36, c46, two tscale ranges, c44, c45), and `tsline y, tlabel(2001m1, add)` stored as `"xlabel":"492, add"` (c16's fold; S52 draws that spec, so the pair is the batch's tlabel-with-add cross case). **TA-03** abbreviations (§3.3); `tm()`, `ts()` r(198) as twoway. **TA-04** units (`%td %tw %tm %tq %th %ty`, `%tc` numbers only, unformatted, `%tmMon_CCYY`, the operator x), and `tscale(log)` on a date axis giving the note `xscale(log)` gives (BR-51.8). **TA-05** the §3.6 refusals except axis ones: dash rc and line equal twoway's. **TA-06** the first-plot rule over the 40 types. **TA-07** non-tsline graphs (c20, c21, c63-c65). **TA-08** lenient literals and number first (C2). **TA-09** security: `tlabel(2000m1 \`x')`, `tline($foo)`, `tlabel("a" 2000m1)` with a global set beforehand: refused or drawn as twoway, the global untouched, nothing registered on refusal; 10,000 positions in under 2 s. **TA-10** tmlabel and tmtick folded onto xmlabel/xmtick and named. **TA-15** x-option literals refused as twoway (c11-c13 and the tick and axis-2 forms). **TA-16** the unit freeze (BR-51.7): register on `%tm`, `format t %td`, `dash build`: the note once, the Span at 504 in the page's spec.
- Commit 2: **TA-11** axis(2) routing and the axis(3) messages, X/T/Y order (f07-f10, f12, f13). **TA-12** format() overrides (k01-k06). **TA-13** `%-t` (g01-g04).

**S51 block of `test/test_wp30_truth.cscript`** (fills S01's stub; helpers `_s51_*` above its header): **TA-20** c01 + c05 + c07 drawn by twoway (recorder) and by `dash … saving()` (the saved page's x ticker and Span locations): same positions and title. **TA-21** c06's range contains twoway's measured range. **TA-22** k01 (commit 2).

## TDD test stubs

New `test/test_taxis_options.py`. Imports: `dash_render as dr`; `test_mode_parity` `_render_pair`; `test_saved_filter_layers` `_render`, `_move`; `test_served_filter_move` `_move as _served_move`; `test_date_range` `_saved`, `_served`. `_FIX = json.load(test/fixtures/taxis_truth.json)`; the 60-month frame `_TS` and its formats `{"t": "%tm"}`.

Commit 1 regression tests (red at the base unless marked guard):
- Test: the fixture has the four `_meta` keys, `stata_version` starting `19.`, every probe id of "Stata truth" — `TestTheFixture::test_it_is_stamped`
- Test: both syntax blocks of dash.ado declare the seven names with twoway's capitals, each has an `sreturn local`, the seven key lists hold them, the pending blocks name `tmlabel` and `tmtick` — `TestTheDeclarations::test_declared_returned_and_listed`
- Test: the new Mata functions and `_dash_taxis_fold` contain no `_stata(`, `stata(` or macro expansion of a token — `TestNoStataCallTakesUserText::test_static_scan`
- Test: the spec the fold writes for c01, c05-c09 (literal `graph_options`, as TA-01 expects), drawn in both modes, gives twoway's tick positions, Span positions, title and a range containing twoway's — `TestTheFoldedSpecDrawsAsTwoway::test_probe[mode-<id>]` (guard: green at the base, since the renderer is unchanged; red until the fold exists is shown by the cscript)
- Test: the same specs after a saved `_move` and a served `_served_move` — `TestAfterAFilterMove::test_probe[mode-<id>]` (guard)
- Test: `(tsline y t) (line z n)` and `(tsline y t) (line z d)` with the folded `xline: "504"`, `xlabel: "480(12)528"`: the Span and ticks sit at 2002m1 and 2000m1..2004m1 among the layers in both modes — `TestAMixedAxis::test_layers[mode-<case>]` (guard after S35)
- Test: a by(g) graph with the folded keys draws the Span and ticks in every panel, before and after a move — `TestUnderBy::test_each_panel[mode]` (guard)
- Test: the seven rows of `rejected_options.json` have `dash_rc` 0 and the new dispositions; the summary tallies equal a recount — `TestTheRecordsAreCurrent::test_rows`
- Test: dash.sthlp has `{marker taxis}` naming the seven options and the refusals; "Minor ticks and minor labels" names tmlabel and tmtick — `TestTheHelp::test_it_documents_the_t_options`

Commit 2 regression tests (red on the tree commit 1 leaves):
- Test: both syntax blocks declare `TLABEL2 TTICK2 TLINE2 TSCALE2 TTITLE2` and the key lists hold them — `TestTheDeclarations::test_the_axis2_forms`
- Test: `{marker taxis}` documents axis(2), format() and `%-t` — `TestTheHelp::test_it_documents_axis2_format_and_left_aligned`
- (cscript) TA-11..TA-13, TA-22.

`test/test_mode_parity.py`: one `CORPUS` and one `MOVE_CORPUS` case tagged `"WP-30 P1.6"` (the c01+c05+c07 folded spec on the 60-month frame).

### Pinned tests to flip (R9; re-measured, never trusted)

Counts only (R10), each written with `# <old> -> <new>: P1.6 <why>`: commit 1 `test_unsupported_report_is_true.py` :240 (+2 plot pending), :241 (+2 graph pending), :607 and :608 (+7 declared each; the index table lists S51 for :608 only, and no batch-18 partner moves :607); `test_help_conformance.py` :590, :598, :604 as measured; `test_help_claims_8.py`'s Unsupported pin kept equal by the help edit. Commit 2: :607 and :608 (+5 each), :590.

## Test plan

| What | How | Fixture / data | Both modes? |
|---|---|---|---|
| Declarations, lists, pending | pytest `TestTheDeclarations`; `test_abbreviations.py`; cscript TA-03 | dash.ado | n/a |
| Conversion, units, refusals, freeze | cscript TA-01..TA-10, TA-15, TA-16 against live twoway | tsline frame, auto | n/a |
| Security | cscript TA-09; pytest `TestNoStataCallTakesUserText` | — | n/a |
| Drawing of the folded keys | `TestTheFoldedSpecDrawsAsTwoway`, `TestAMixedAxis`, `TestUnderBy`; truth TA-20, TA-21 | `taxis_truth.json` | yes |
| After moves | `TestAfterAFilterMove`; parity MOVE_CORPUS | tsline frame | yes |
| axis(2), order, format(), `%-t` | cscript TA-11..TA-13; truth TA-22 | tsline frame | n/a |
| Records, help | `TestTheRecordsAreCurrent`, `TestTheHelp`, help conformance | json, dash.sthlp | n/a |
| Registries, tracking | coverage map, `_needed`, cscript hygiene, tracking | — | n/a |

**Acceptance criteria.**
- **AC-51.1** (BR-51.1, BR-51.2, BR-51.3) TA-01..TA-04, TA-06..TA-08, TA-10 PASS against live twoway; `TestTheFoldedSpecDrawsAsTwoway` passes in both modes.
- **AC-51.2** (BR-51.4) TA-05, TA-15 and TA-03's `tm()`/`ts()` rows PASS (dash rc and first line equal twoway's).
- **AC-51.3** (BR-51.5) TA-11..TA-13, TA-22 PASS.
- **AC-51.4** (BR-51.6) TA-09 and `TestNoStataCallTakesUserText` pass.
- **AC-51.5** (BR-51.7, BR-51.8) TA-16 prints the note once; TA-04's `tscale(log)` row gives `xscale(log)`'s note.
- **AC-51.6** Both modes agree before and after moves (`TestAfterAFilterMove`, parity), node not skipped; every count moved with its comment; the full suite reports 0 failed before each commit; G7 prints 0 twice per commit.

## Tasks

**Commit boundary.** Tasks 51-01 to 51-09 form commit 1, made by 51-09 on `wp30-s51` with the subject `Fold the tsline time-axis options onto the x axis, part 1 of 2: x axis 1 and date literals (WP-30 P1.6)`; it leaves the BUGS.md entry, its `WP30_OPEN` key and both markers in place (A156). Tasks 51-10 to 51-14 form commit 2, made by 51-14 with the subject `Fold the tsline time-axis options onto the x axis, part 2 of 2: axis(2), format() and %-t (WP-30 P1.6)`; it closes all three. `$S` is `/private/tmp/claude-501/-Users-billy-Desktop-Programs-StataPrograms-d-dash/55d6df3b-6200-4eb1-99b7-fa28b88519a2/scratchpad/wp30`, `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s51`, `$SLOT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh`. A cscript runs through the driver: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" "<script>.cscript" > "$S/run_<script>.do"`, then `WP30_ONLY=S51 "$SLOT" "$S" "$S/run_<script>.do"`.

<task type="auto" id="51-01">
  <name>Write the fixture and pytest tests</name>
  <files>scripts/extract_taxis_truth.do, test/test_taxis_options.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Check `git -C "$WT" rev-parse HEAD` equals `cat "$S/batch-18-base.txt"` and `git -C "$WT" branch --show-current` prints `wp30-s51`; stop otherwise. Create `scripts/extract_taxis_truth.do` as "Stata truth" describes (every probe both commits read) and run it with `DASH_REPO="$WT" "$SLOT" "$S" "$WT/scripts/extract_taxis_truth.do"`; it writes `test/fixtures/taxis_truth.json`. Compare its rc and first lines with E4 probe by probe; a difference stops the section. Create `test/test_taxis_options.py` with every commit-1 stub and append the two parity cases. Run `python3 -m pytest test/test_taxis_options.py -q -n 6 -p no:cacheprovider -rf > "$S/51-new-1.log" 2>&1`. Write `$S/51-P1.6-1-failure.txt`: the base sha, one line per failing node, then "Guards (pass at the base)" listing the drawing guards. Edit no shipped file; do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json; d=json.load(open('$WT/test/fixtures/taxis_truth.json')); p=d['probes']; print(all(k in d['_meta'] for k in ('stata_version','born_date','dash_commit','extracted')), p['c01']['ticks'], p['f01']['rc'], p['m8']['rc'])"` prints `True [480.0, 492.0, 504.0, 516.0, 528.0] 198 123` (ints acceptable); `grep -c FAILED "$S/51-new-1.log"` is at least 4; `git -C "$WT" diff --name-only -- dash.ado dash_parse.mata` prints nothing.]]></verify>
  <done>The t-option fixture existed and every commit-1 pytest regression test was shown failing on the unmodified tree, with the drawing guards listed.</done>
</task>

<task type="auto" id="51-02">
  <name>Write the twoway comparison cases</name>
  <files>test/test_twoway_option_parity.cscript, test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Add the TA run of "Stata truth" (TA-01..TA-10, TA-15, TA-16; commit 1's) to `test/test_twoway_option_parity.cscript` as one contiguous run before `// Summary`, each case comparing live twoway with dash in the script's `nfail`/`faillist` form, spec values read from `$dash_json_<name>` through Mata. Fill S01's S51 stub of `test/test_wp30_truth.cscript` with TA-20 and TA-21 (helpers `_s51_*` above the S51 header). Run both through the driver on the unmodified shipped files and append each `TA-nn FAIL` line with the twoway line it quotes to `$S/51-P1.6-1-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -cE "TA-(0[1-9]|1[056]) FAIL" "$S/run_test_twoway_option_parity.log"` is at least 9 (TA-06 and TA-07 may pass partly); `grep -cE "TA-2[01] FAIL" "$S/run_test_wp30_truth.log"` prints 2; no earlier case of either script newly fails.]]></verify>
  <done>The live twoway comparisons for commit 1 were in place and shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="51-03">
  <name>Declare the seven time-axis options</name>
  <files>dash.ado, test/test_abbreviations.py</files>
  <action><![CDATA[
    Apply TR-51.1 in both syntax blocks, both sreturn blocks, all seven key lists (E1 anchors re-found by `grep -n "foreach gk"`) and both pending blocks, by hand (never the generator, IR-7). Do not edit `test_abbreviations.py` unless its seven-lists guard names lists by line; run it and TA-03 through the driver; `t()`, `tti()`, `tm()`, `ts()` must read as E4 says (tm/ts still named until 51-05).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_abbreviations.py "test/test_taxis_options.py::TestTheDeclarations::test_declared_returned_and_listed" -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>dash.ado declared, returned and listed the seven t-options with twoway's abbreviations, with tmlabel and tmtick pending.</done>
</task>

<task type="auto" id="51-04">
  <name>Add the Mata date converter</name>
  <files>dash_parse.mata, test/program_coverage_map.py</files>
  <action><![CDATA[
    Apply TR-51.3 to `_dash_rep_cat` and `_dash_rep_subs` in place. Add the six functions of TR-51.4 directly after `_dash_axreq_check`, each with a comment block citing E4's measurement it reproduces and critic C2/C3, plus their header-index entries; use only Mata string functions, `strtoreal`, `strofreal` and the six date functions, never `_stata()`, `stata()` or `regexm`. Add the six COVERAGE entries under S51's dash_parse.mata anchor (TR-51.8). Run `TestNoStataCallTakesUserText` and `test_program_coverage_map.py`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "test/test_taxis_options.py::TestNoStataCallTakesUserText" test/test_program_coverage_map.py -q -n 6 -p no:cacheprovider` reports 0 failed for the Mata half (the ado half waits for 51-05); `grep -cE "_stata\(|regexm" <(sed -n "/_dash_taxis_unit(/,/_dash_xdate_find(/p" "$WT/dash_parse.mata")` prints 0.]]></verify>
  <done>Mata converted every date token through its string date functions behind a whitelist, with twoway's messages, and the t keys had their merge categories.</done>
</task>

<task type="auto" id="51-05">
  <name>Fold the options onto x axis 1</name>
  <files>dash.ado</files>
  <action><![CDATA[
    Add `_seg_xvar_out` to `_dash_process_segment` and the per-segment collection in `_dash_plot` (TR-51.2). Add `_dash_taxis_fold` (TR-51.5 steps 1-5) with a header comment citing E4, call it after the axis check and before "Validate the graph-level values (WP-15)", add the `tm()`/`ts()` refusal before the ignoring note, and the six Mata names to `_needed` (S52 adds none; R6). Run TA-01..TA-10 and TA-15 through the driver.
  ]]></action>
  <verify><![CDATA[`grep -cE "TA-(0[1-9]|10|15) PASS" "$S/run_test_twoway_option_parity.log"` prints 11; `grep -E "[A-Z]+-[0-9]+[a-z]? FAIL" "$S/run_test_twoway_option_parity.log" | grep -vc "TA-16"` prints 0 (TA-16 is 51-06's).]]></verify>
  <done>The t-options were folded onto x axis 1 in twoway's units and order and refused where twoway refuses them.</done>
</task>

<task type="auto" id="51-06">
  <name>Note a changed axis unit at build</name>
  <files>dash.ado</files>
  <action><![CDATA[
    Apply TR-51.5 step 6: write `dash_tunit_<name>` in `_dash_taxis_fold`, drop it beside the `dash_fpts_` drops (re-registration and `dash clear`), and add the once-per-graph note in `_dash_prepare_spec`'s graph loop through `_dash_say`. Run the TA run through the driver.
  ]]></action>
  <verify><![CDATA[`grep -cE "TA-(04|16) PASS" "$S/run_test_twoway_option_parity.log"` prints 2; `grep -cE "[A-Z]+-[0-9]+[a-z]? FAIL" "$S/run_test_twoway_option_parity.log"` prints 0; `grep -c "dash_tunit_\*" "$WT/dash.ado"` prints 1.]]></verify>
  <done>A t-option's registration unit was kept and a later change of the variable's date format was noted at build.</done>
</task>

<task type="auto" id="51-07">
  <name>Move the pinned option counts</name>
  <files>test/test_unsupported_report_is_true.py, test/test_help_conformance.py, test/test_help_claims_8.py</files>
  <action><![CDATA[
    Run the three files on the worktree and re-derive each pinned count of E5 (plot and graph pending, declared plot and graph, declarations, ignored, unsupported); write each new value in place with `# <old> -> <new>: P1.6 <why>` (R10). Leave every test name and assertion form as it is; record each change in `$S/51-flips-1.txt` as a `Flipped:` line.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_unsupported_report_is_true.py -q -n 6 -p no:cacheprovider` reports 0 failed (the help-side pins go green in 51-08); `grep -c "P1.6" "$WT/test/test_unsupported_report_is_true.py"` is at least 3.]]></verify>
  <done>Every count the new declarations and pending options moved was re-derived with its reason.</done>
</task>

<task type="auto" id="51-08">
  <name>Document the options and update records</name>
  <files>dash.sthlp, test/fixtures/rejected_options.json</files>
  <action><![CDATA[
    Add TR-51.6's `{marker taxis}` group after the axis-title paragraphs of "Axis and Display Options" (re-grep the title; R3) and the Unsupported "Minor ticks and minor labels." names. Edit the rows of TR-51.7 in place by `id`/`option`, keeping the file's indentation and key order, and re-derive the summary tallies with a short `python3 -c` count printed to `$S/51-records.txt` (the file is edited by hand, values only). Run `TestTheHelp`, `TestTheRecordsAreCurrent`, the three count files and `test_option_surface.cscript` through the driver.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "test/test_taxis_options.py::TestTheHelp::test_it_documents_the_t_options" "test/test_taxis_options.py::TestTheRecordsAreCurrent" test/test_help_conformance.py test/test_help_claims_8.py -q -n 6 -p no:cacheprovider` reports 0 failed; `grep -c "O2-03 PASS" "$S/run_test_option_surface.log"` prints 1.]]></verify>
  <done>The help documented the t-options and the stale rejected-option rows recorded what dash now does.</done>
</task>

<task type="auto" id="51-09">
  <name>Run the suite and make commit 1</name>
  <files>none</files>
  <action><![CDATA[
    Run `test_taxis_options.py`, `test_mode_parity.py`, `test_abbreviations.py`, the three count files, `test_program_coverage_map.py`, `test_cscript_hygiene.py`, `test_fixtures_are_committed.py`, `test_tracking_documents.py` with `-n 6`, and `test_twoway_option_parity.cscript`, `test_option_surface.cscript` and the S51 truth block through the driver (a SKIP is not a pass; check `~/.stata19/console/stata19.rc` holds `python_exec`). `git -C "$WT" merge --no-edit main` (expect `Already up to date.`); one full run `"$S/full_suite_queue.sh" "$WT" "$S/51-full-1.log"` in the background, waited for on its `exit=` line, never relaunched (E6). Stage exactly the files 51-01 to 51-08 changed, `git add -f test/fixtures/taxis_truth.json test/fixtures/rejected_options.json`; check the staged names (G6). Write `$S/51-message-1.txt` ("Notes: commit messages"), check G7, confirm the branch, commit, check G7 again.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/51-full-1.log"` shows 0 failed and `exit=0`; `git -C "$WT" log -1 --format=%s` ends `(WP-30 P1.6)`; `grep -c '<!-- WP-30 P1.6 -->' "$WT/CHANGELOG.md"` prints 2; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Commit 1 folded the t-options onto x axis 1 with twoway's units and refusals, green, leaving the entry, key and markers for commit 2.</done>
</task>

<task type="auto" id="51-10">
  <name>Write the commit-2 failing tests</name>
  <files>test/test_taxis_options.py, test/test_twoway_option_parity.cscript, test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    On the tree commit 1 left, add the commit-2 pytest stubs, TA-11..TA-13 at the end of the TA run (before `// Summary`) and TA-22 at the end of S51's truth block. Run the new pytest nodes with `-rf` into `$S/51-new-2.log` and both scripts through the driver. Write `$S/51-P1.6-2-failure.txt`: the commit-1 sha, the failing nodes and `TA-nn FAIL` lines, then the guards. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED "$S/51-new-2.log"` is at least 2; `grep -cE "TA-1[1-3] FAIL" "$S/run_test_twoway_option_parity.log"` prints 3; `grep -cE "TA-(0[1-9]|1[056]) PASS" "$S/run_test_twoway_option_parity.log"` prints 12.]]></verify>
  <done>The axis(2), format() and %-t cases were shown failing on the tree commit 1 left, with commit 1's cases still passing.</done>
</task>

<task type="auto" id="51-11">
  <name>Route time-axis options to axis 2</name>
  <files>dash_parse.mata</files>
  <action><![CDATA[
    Apply TR-51.11: side letter `t` in `_dash_ax_parse` (outside `_dash_axfam`), plural renaming and `t<fam>2` in `_dash_route_axis2`, side codes and twoway's `t<fam>s(…) not allowed, xaxis<n> does not exist` words in `_dash_axreq_add`, the X/T/Y order in `_dash_axreq_check`; update their comment blocks and header-index entries in place. Run `test_abbreviations.py` and the axis-request cases of `test_twoway_option_parity.cscript` (AX blocks) through the driver: none newly fails.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_abbreviations.py -q -n 6 -p no:cacheprovider` reports 0 failed; `grep -cE "AX-[0-9]+ FAIL" "$S/run_test_twoway_option_parity.log"` prints 0.]]></verify>
  <done>Mata routed t-options with axis(2) and their plurals and ordered axis errors X, T, Y in twoway's words.</done>
</task>

<task type="auto" id="51-12">
  <name>Fold axis 2, format() and %-t</name>
  <files>dash.ado</files>
  <action><![CDATA[
    Apply TR-51.10 (the five `…2` declarations, sreturn, key lists, axis-2 fold with its own base unit), remove commit 1's "axis word left unfolded" branch, and apply TR-51.12 (the four tickset formats, the own-option format after its positions, `get_time_format` for lines and scale); TR-51.13 then holds through `_dash_taxis_unit`'s family rule. Run TA-01..TA-16 and TA-22 through the driver.
  ]]></action>
  <verify><![CDATA[`grep -cE "TA-(0[1-9]|1[0-356]) PASS" "$S/run_test_twoway_option_parity.log"` prints 15; `grep -c "TA-22 PASS" "$S/run_test_wp30_truth.log"` prints 1.]]></verify>
  <done>The t-options reached the second x axis in its own unit and followed twoway's format() and %-t rules.</done>
</task>

<task type="auto" id="51-13">
  <name>Document axis 2 and move counts</name>
  <files>dash.sthlp, test/test_unsupported_report_is_true.py, test/test_help_conformance.py</files>
  <action><![CDATA[
    Add TR-51.14's sentences to the `taxis` group. Re-derive the declared counts (:607, :608) and :590 with their `# <old> -> <new>: P1.6 …` comments and record `Flipped:` lines in `$S/51-flips-2.txt`. Run `TestTheHelp`, `TestTheDeclarations`, both count files and `test_help_claims_8.py`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_taxis_options.py test/test_unsupported_report_is_true.py test/test_help_conformance.py test/test_help_claims_8.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>The help documented the axis-2 forms and the format rules, and the counts the five new declarations moved were re-derived.</done>
</task>

<task type="auto" id="51-14">
  <name>Close the entry and make commit 2</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Read the title as `WP30_OPEN["P1.6"]`. Close that BUGS.md entry in place (`- [x]`) with "Notes: BUGS.md Resolution". Delete only the `"P1.6"` key line. Replace both `<!-- WP-30 P1.6 -->` markers in place with "Notes: CHANGELOG lines" (New, then Changed behaviour). Run the files of 51-09 and both scripts and the S51 block through the driver; `git -C "$WT" merge --no-edit main` (expect `Already up to date.`); one full run `"$S/full_suite_queue.sh" "$WT" "$S/51-full-2.log"` waited for on `exit=`. Stage exactly the files 51-10 to 51-14 changed; check G6; write `$S/51-message-2.txt`, check G7, confirm the branch, commit, check G7 again, and report both shas and messages to the merger.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/51-full-2.log"` shows 0 failed and `exit=0`; `grep -c '<!-- WP-30 P1.6 -->' "$WT/CHANGELOG.md"` prints 0; `grep -c '^    "P1.6": "' "$WT/test/test_tracking_documents.py"` prints 0; `git -C "$WT" log -2 --format=%s` shows both subjects ending `(WP-30 P1.6)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Entry P1.6 was closed naming existing tests, both markers carried the new options and refusals, and two green commits on wp30-s51 were ready for the merger.</done>
</task>

## Section completion criteria

- The seven t-options and the five `…2` forms are declared, returned, listed and folded onto the x keys in twoway's units and order, on every twoway graph; the spec never carries a t key.
- Every E4 refusal, the x-option literal refusals and `tm()`/`ts()` are dash's in twoway's rc and words (TA-03, TA-05, TA-11..TA-13, TA-15).
- No date token reaches `_stata()`, `stata()` or a command line (TA-09, static scan).
- Both modes draw the folded keys as twoway does, before and after moves, on mixed axes and under by().
- The fixture is generated, stamped and committed with `-f`; the stale rejected-option rows are current; every moved count carries its reason.
- Two green commits `(WP-30 P1.6)` on `wp30-s51`; the second closes the entry, deletes its key and replaces both markers.

## Notes

- **Unknown symbols.** The 18.0 impact run reports every symbol edited here as UNKNOWN; the merger records the grep counts of the Risk block.
- **The renderer is untouched by design** (manifest). If a drawing guard turns red at the base (a later section changed date drawing), stop and report: a renderer fix is not this section's.
- **S52's merge rule and the cross case.** `tlabel(2001m1, add)` with no `xlabel()` folds to `"xlabel":"492, add"` (`_dash_rep_merge` returns the second value whole when the first is empty, before and after S52's edit); TA-02 pins that spec, and S52's `TestOnADateAxis` and AD-22 draw it. S52 cannot run S51's fold in its own worktree (both are cut from the batch-18 base), so the cross case is this pair; G8 runs both scripts on the merged tree. With an earlier `xlabel()` copy the merged `add` follows S52's merge rule.
- **Adjacent hunks with S52.** S51 edits `_dash_rep_subs` (dash_parse.mata:5662-5711) and S52 edits `_dash_rep_merge` directly below it (:5713-5745): distinct functions whose hunks may touch in context; the merger keeps both (R6).
- **python_exec hazard.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`; the extractor, TA-09's static scan through Stata and the truth block then fail or SKIP. Check after each slot run.
- **Merge rules for the shared files.**
  - R1: the TA run at the end of `test_twoway_option_parity.cscript` (no batch-18 partner appends there); S51's truth block and its helpers.
  - R2: no copy-list change (R2 row S51); coverage keys under S51's anchors.
  - R3: Axis and Display Options (the new `taxis` group) and Unsupported (pending mover); S52 edits other sentences of Axis and Display after S51 lands.
  - R4/R5: the two `P1.6` markers, the entry and its key, by commit 2 only.
  - R6: `version 19` in `_dash_taxis_fold`; six new Mata functions with their `_needed` names and header-index entries (S52 adds no Mata function; it edits `_dash_rep_merge` and `_dash_axis_pieces` in place, whose header-index lines S51 does not touch).
  - R7: one new extractor and fixture; `rejected_options.json` is not generated and is edited in place, values only.
  - R8: one CORPUS and one MOVE_CORPUS case. R9: counts only. R10: :240, :241, :607, :608, :590, :598, :604, each with its comment; S56 moves :241 and :608 again in batch 19.
- **Commit messages.** Subjects as in "Commit boundary". Body, in order: the failure file (`$S/51-P1.6-1-failure.txt` / `-2-`); the measured defect (Overview's block); what changed and where (TR-51.1-TR-51.9 / TR-51.10-TR-51.14; both modes drawn by the unchanged renderer); the threat closed (G9: no date token is evaluated as Stata code); then one line each: `Regression: test/test_taxis_options.py::<Class>::<test> -- failed at <base sha> with <text>`, and `test/test_twoway_option_parity.cscript TA-01`-style lines; the `Flipped:` lines of `$S/51-flips-<k>.txt`; `Fixture: test/fixtures/taxis_truth.json (scripts/extract_taxis_truth.do)`; commit 1 `BUGS.md: "<title>" (open; closed by part 2)`, commit 2 `BUGS.md: "<WP30_OPEN["P1.6"] title>" (closed)`. No tool or vendor name (G7).
- **BUGS.md Resolution** (one line, in place):

  ```
  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.6). tlabel(), ttick(), tmlabel(), tmtick(), ttitle(), tscale() and tline() and their axis-2 forms are declared with twoway's abbreviations on every twoway graph and folded at registration onto the x keys (dash.ado _dash_taxis_fold, _seg_xvar_out; Mata _dash_rep_cat, _dash_rep_subs), after the x copies, with each date literal written as the Stata number twoway reads in the unit of the axis's label format: the first plot's (numeric for lfit, qfit, lfitci, qfitci, lpoly, lpolyci, kdensity, function, scatteri, pci, pcarrowi), twoway's format() tickset rules and its %-t quirk, numbers first (Mata _dash_taxis_unit, _dash_tdate_value with Mata's string date functions behind a whitelist, never _stata(); _dash_tdate_ticks, _dash_tdate_lines, _dash_tdate_range); axis(2) routes to the second x axis and axis errors come X, T, Y (_dash_ax_parse, _dash_route_axis2, _dash_axreq_add); twoway's refusals are dash's, including date literals in x-options (_dash_xdate_find) and tm()/ts(); a changed date format before dash build is noted; the renderer draws the folded keys in the saved page and the served app and after filter moves. Pinned by test/test_taxis_options.py::TestTheFoldedSpecDrawsAsTwoway::test_probe, test/test_taxis_options.py::TestNoStataCallTakesUserText::test_static_scan, test/test_taxis_options.py::TestAMixedAxis::test_layers, test/test_twoway_option_parity.cscript TA-01, test/test_twoway_option_parity.cscript TA-05, test/test_twoway_option_parity.cscript TA-11, test/test_wp30_truth.cscript TA-20; fixture test/fixtures/taxis_truth.json. Residual, deferred (WP-30): tmlabel() and tmtick() are stored and named until minor ticks are drawn (P2.2); tscale(log) on a date axis is noted, as xscale(log) is; date literals in y-options are not refused (P2.21).
  ```
- **CHANGELOG lines** (each replaces its marker in place; the `###` lines only say which list and are not written):

  ```
  ### New
  - The time-axis options `tlabel()`, `ttick()`, `ttitle()`, `tscale()` and `tline()` (and `tlabel2()`-style and `axis(2)` forms) are drawn on every twoway graph, with date literals in the axis's own unit: `dash tsline y, tlabel(2000m1(12)2004m1) tline(2002m1)` named them in a note and drew neither, and now draws labels at 2000m1-2004m1 and a line at 2002m1, as twoway does, before and after filter moves; `tmlabel()` and `tmtick()` are accepted and named until minor ticks are drawn. (WP-30, P1.6)

  ### Changed behaviour (may need your do-files changed)
  - Date literals and time-axis forms twoway refuses are refused in twoway's words (all rc 0 before): a date literal in `xlabel()`, `xtick()`, `xmlabel()`, `xmtick()` (`invalid label specifier, :  2000m1:`, r(198)), `xline()` (`invalid line argument, 2002m1`, r(198)) or `xscale(range())` (`range() invalid -- invalid numlist`, r(121)); a t-option date literal when the first plot is lfit, qfit, lfitci, qfitci, lpoly, lpolyci, kdensity, function, scatteri, pci or pcarrowi, or on a numeric or `%tc` axis; an invalid literal (`tline(2000m13)`); `tline()` or `tscale(range())` literals on a `%-t` axis; `tm()` and `ts()` (`option tm() not allowed`, r(198)). (WP-30, P1.6)
  ```
- **Notes for the closeout (S58; A145).**
  - **GAPS2.md A4:** the t-option part (A4-q) is closed by `<sha1>`, `<sha2>`; **B14** (the help's full list) closed by the same commits: `- **Tracked:** Closed in WP-30, BUGS.md "<P1.6 title>", commits <sha1>, <sha2>`.
  - **REMAINING.md:** REM-§2-S09-tlabel/-ttick/-tline/-ttitle (:128-131, :148), REM-05-04-S09-a/-b (:445-447, :816-817), the S09 "73 options" row (:308) and 15-03's downstream row (:733): closed for the t-options; `ttext()` stays with S56.
  - **DROPIN-REMAINING.md:96 (P1.6):** "Closed by <sha1>, <sha2> (WP-30 S51)."
  - **test/fixtures/rejected_options.json:** the `ttext` row ([96], probes[265]) is S56's; every other stale row is S58's.
  - **New P2 row:** date literals in y-options (`ylabel(2000m1)`) are accepted by dash and refused by twoway (r(198)); not swept here (P2.21's surface).
  - **AGENTS.md invariant:** "a date token typed by the user is converted only by Mata's string date functions in `_dash_tdate_value`, behind its whitelist; the spec never carries a t key."
  - **Unverified:** Stata 14-18.5 (not run, M2); Windows and Linux (Stata-side logic only).
