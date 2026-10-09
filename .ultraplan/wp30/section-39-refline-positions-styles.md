# Section 39: xline/yline positions, refusals and lstyle (P1.21 part a)

> Part of: WP-30 · Items: P1.21 part a (entry `P1.21a`; GAPS2-B22-a, GAPS2-B22-d (the lstyle part), AUDIT-64) · Risk: yellow · Batch: 14 (merge order S39, S40, S41) · Depends on: 10, 13, 30, 32 · Blocks: 43, 50 · Tasks: 12, 1 commit · Case prefix: XP

## Review amendments

- Fixed (major): TR-39.3 told the executor to split copies with a Mata "`_dash_by_commas`-style" loop. No such function exists, and a new one would need `_needed`, header-index and map entries that the section does not list. TR-39.3 now loops on the existing `_dash_comma_pos` (dash_parse.mata:1863).
- Fixed (minor, honesty): the r(134) message said "draws <n>" for an upper-bound count. It now says "asks for up to <n>", and BR-39.7 says how the panels are counted.
- Fixed (minor): `_dash_refline_tally` holds the `seen` set object, so an `id` reused after garbage collection cannot merge two renders' tallies.
- Resolved: Q-39.1. The upper bound is kept (A68, the dash.ado:7520 precedent, rule 1), and the renderer enforces only the ceiling (R12). No maintainer question remains.
- Checked at HEAD: dash.ado :5323-5325, `_dash_limit_table` :2770-2783, `_dash_plot_cap_refuse` :2963; dash_render.py `_DASH_LIMITS` :1064-1073, `DashLimitError` :1157, `_dash_route_line_copies` :2942, `_DASH_REFLINE_SUBOPTS` :26221, `_dash_reference_lines` :26224, `_dash_refline_instances` :26268, the one-at-a-time `add_layout` :26370-26371, the copy list :33381-33383; test_resource_limits.py :569-572 (eight keys). The XP prefix and the new files are free.
- Checked the batch boundary against S40/S41: S39 edits `_dash_plot`'s check block, the `_dash_refline_*` helpers, `_dash_route_line_copies`, `_DASH_LIMITS`/`_dash_limit_table` and `_dash_axreq_*`. Neither partner edits these. `_needed` and the Mata header index are context-only conflicts (R6). The help paragraphs are disjoint (Axis and Display and Resource limits, against S40's Plot types/Unsupported and S41's Server Mode/Dependencies).
- Rejected: "refuse `lalign(nosuch)`". twoway notes it (class alignstroke) and draws, so M5 calls for a note, not a refusal.
- (cross-file pass) TR-39.4, TR-39.8, 39-04: the new panel-counting program is `_dash_refline_panels`, not `_dash_by_panels`, which already exists (dash.ado:3340, rclass `r(kept)`, used by `_dash_plot` :5514 and read by S56) and already has a `program_coverage_map.py` key (:208); the existing program is not edited (g09).
- The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:132 (P1.21) reads: "Numlists such as `xline(2000(500)3000)` draw nothing. `lstyle`, `noextend` and `lalign` are only named." `noextend`, `extend` and `style()` are S50's (P1.21b). Research `.ultraplan/wp30/research/p1-21.md` §1 measured, through `dash scatter mpg weight, <opt> saving(…)` and the page's Span models (both modes agree, both wrong):

| opt | dash at `c96facd` | twoway 19.5 |
|---|---|---|
| `xline(2000(500)3000)` | 0 Spans; "xline() sub-option(s) not implemented and ignored: 2000(500)3000" | 3 lines |
| `xline(2000/2002)`, `yline(10(5)40)` | 0 Spans, named | 3 / 7 lines |
| `xline(2000 2500 to 3500)` | 2000, 2500, 3500; "to" named | 4 lines |
| `xline(2000 (500) 3000)` | 2000, 3000 | 3 lines |
| `xline(3000, lstyle(p1))` | `#c10534` (xyline); named | `#1A476F` |
| `xline(3000, lstyle(foreground) lcolor(red))` | red at xyline's width; lstyle named | red at foreground's width (5.76, not 8.64) |
| `xline(3000, lalign(inside))` | named | rc 0, no visible change |
| `xline(3000 3000)` | 2 Spans | 1 line (`list uniq`) |

The critic added: `yline(20, lcolor(red)) yline(10(5)40, lcolor(blue))` draws one **blue** line at 20 (the numlist copy re-styles the copy before it); `xline(nan 3000)`, `inf`, `1e400` and `1_000` draw at NaN, ±inf and 1000 with no note; the Span's level is `annotation`, so it is drawn over the markers, where twoway draws added lines after the grid and before the plots; and Spans are added one at a time (2,500 take 4.4-5.5 s; one bulk assignment 0.46-1.32 s). dash accepts with rc 0 what twoway refuses r(198)/r(100): `xline(abc)`, `xline(1(0)5)`, `xline(1(1)2501)`, `xline(. 3000)`, `xline(3000, ex ex)`, `xline(3000, s(unextended))`, `xline(3000, NOEXTEND)`, `xline(2000,3000)`.

**After this section**, in the saved page and the served app, before and after every filter move:
- positions are read as twoway reads them: Stata's own `numlist` expands them in dash.ado (`_dash_line_expand`), duplicates within a copy dropped, at most 2,500 per copy; the renderer expands a spec written by hand the same way (`_dash_expand_numlist`), and every copy keeps its own style;
- twoway's refusals are dash's, in twoway's order and words (M5): axis checks (P0.5), `something required` r(100), unknown, short, capitalised or repeated sub-options r(198), then `invalid line argument, <positions>` r(198);
- `lstyle()` takes every line style name through `style_bundle` (S32/S36), with `lcolor()`, `lwidth()`, `lpattern()` winning in any order and `none` drawing nothing; `lalign()` is accepted silently (twoway draws no difference);
- lines are drawn above the grid and below the glyphs (`level="underlay"`), added in bulk, never widen an axis (S21's hull ignores them);
- the new limit `reflines` (default 10,000, ceiling 100,000, `$dash_max_reflines`, A68, ratification row 6) refuses r(134) a dashboard whose positions × by() panels pass it.

**Why one section.** One parse (Mata's axis-request rows), one expansion and one drawing helper serve every `xline`, `yline`, `xline2` and `yline2` copy. The extent (`noextend`, `style()`) needs S21's hull and S47's margin model (S50, batch 17).

**Test order and commit rule (rule 7).** One cycle on `wp30-s39`. 39-01 and 39-02 write the fixture and every regression test and run them against the unmodified batch-14 base, saving `$S/39-P1.21a-failure.txt` (no commit); 39-03 to 39-10 fix, flip and document; 39-11 runs the suites; 39-12 closes the entry and makes the one commit.

## Risk: [yellow] — refusals change accepted input, the Mata axis-request rows serve every axis option, and a new dashboard limit

**Why.**
- `_dash_expand_numlist` is CRITICAL (11 impacted); it is called, not edited (manifest note; batch 14's expected list).
- `_dash_route_line_copies` is HIGH (3 impacted, through `_dash_route_axis_options` into both builders' `__init__`, :29150 and :32809; critic gap 2).
- `ServerAppBuilder._glyph_layer_lines` is HIGH (4).
- `_dash_reference_lines`, `_dash_refline_instances`, `_dash_refline_draw` are LOW (3 each) (re-measured this pass).
- `_dash_report_suboptions` (CRITICAL, 25) and `_dash_style_note` (CRITICAL, 69) are called, not edited.
- Mata `_dash_axreq_add`/`_dash_axreq_check`/`_dash_ax_parse` and dash.ado `_dash_plot`, `_dash_render_immediate`, `_dash_prepare_spec` are UNKNOWN to the index; grep: `_dash_axreq_*` are called only from `_dash_plot` (dash.ado:5061, :5213, :5323-5324 at `c96facd`).

**Risk factors.**
1. Do-files that pass `xline(abc)` or `xline(1(0)5)` now stop (M5); CHANGELOG "Changed behaviour".
2. `_dash_axreq_*` also serve the label, tick, title and scale families (P0.5, S10); a column change there must leave every other family's verdict alone.
3. S51 (batch 18) folds `tline()` onto these rules as explicit numbers; S50 reads S39's parse for the extent.
4. by() multiplies every line per panel (critic gap 5): one graph can reach 1,000 × 2,500 Spans.
5. Positions reach `numlist` on a Stata command line (rule 1).

**Mitigation.**
1. Every refusal is compared with live twoway (XP-01..XP-08) and listed in the CHANGELOG.
2. The new columns are filled only for the line family; `test_axis2_suboptions.py`, `test_suboption_reporting.cscript` and the WP-29 P0.5 cases (`test_twoway_option_parity.cscript` AX-*) run in 39-03.
3. Explicit-number copies pass the new checks unchanged (XP-05); S50's boundary is written below.
4. The `reflines` limit counts positions × panels in dash.ado (r(134)) and the renderer refuses past the ceiling (`DashLimitError`) for a spec that came another way.
5. A copy holding a backtick, `$`, `'`, `"`, `\` or a byte below 32 is never put on `numlist`'s line: it is refused as `invalid line argument` directly (S10's `_dash_so_unsafe`); messages echo through `_dash_say`.

## Dependencies

- **Depends on: 10, 13, 30, 32.**
  - S10 (batch 4): `_DASH_REFLINE_SUBOPT_TABLE` (style/st, noextend/noex w, extend/ex w, lstyle/lst, lcolor/lc, lwidth/lw, lpattern/lp, lalign/la, axis/ax; TR-10.1), `_dash_subopt_canon`, `_dash_refline_instances`' canonicalisation and `_typed` record (TR-10.5), the Mata `_dash_so_rows("refline")`, `_dash_so_resolve`, `_dash_so_unsafe`, and the tenth `_dash_axreq` column (TR-10.6: "S39 adds the xline refusals through the refline twin").
  - S13 (batch 5): line widths on the ladder (`translate_lwidth`, `line_px`), `_dash_refline_draw` changed in place.
  - S30 (batch 10): `_dash_refline_draw` reads `lcolor` through `parse_color_alpha(…, **scheme_colour_context(scheme))` (TR-30.8).
  - S32 (batch 11) and S36 (batch 12): `SchemeParser.style_bundle("line", name)` for all 76 linestyle names (IR-14), an unknown name returning `foreground`'s attributes with S36's note.
  - S01: entry `P1.21a`, its `WP30_OPEN` key, markers `<!-- WP-30 P1.21a -->` in `### Results that change` (WP-30 group) and `### Changed behaviour (may need your do-files changed)`, S39's stub block and map anchors `# WP-30 S39 (P1.21a): xline/yline positions, refusals and lstyle (P1.21 part a)`.
  - Read, not depended on: S06 (notes), S21 (lines are not in the hull; `_dash_range_hull` read only), S35 (date positions through `_dash_axis_positions`).
- **Blocks: 43, 50.** S43 gives a bare `*#`/`%#` in `lcolor()` the xyline base colour. S50 draws `extend`/`noextend`/`style()` from the copies S39 parses, over S21's hull.
- **Parallel batch: 14**, merge order S39, S40, S41.
- **Can run with:** S40 (`_make_figure_body`, `_FILTER_JS`, `_build_filter_widgets`, the mappers, `_dash_process_segment`, `_dash_parse_plot_opts`, Mata `_dash_connect_canon`, `_dash_stylelist_keys`) and S41 (`main`, the launcher part of `_generate_app_source`, `_dash_served_template`, `_dash_harden_origin_check`, `_dash_token_auth`, dash_setup). S39 edits none of them and neither partner edits a `_dash_refline_*` function, `_dash_route_line_copies`, `_dash_axreq_*`, `_dash_plot`'s check block, `_DASH_LIMITS` or `_dash_limit_table`. S39 changes neither call site of `_dash_reference_lines` (inside `_make_figure_body` and `_generate_app_source`). S40 also adds to dash.ado's `_needed` list and the Mata header index: a context-only conflict the merger resolves by keeping both (R6).

## Evidence

Anchors are at `c96facd` (dash_render.py 37,689 lines, dash.ado 8,487, dash_parse.mata 6,093). Batches 4-13 move many; the executor re-finds each by symbol at `batch-14-base`.

### E1. One helper in both modes (dash_render.py)

`_dash_reference_lines(fig, graph_opts, seen=None, key="", scheme=None)` (26224) is called by the saved figure body (30396) and the generated app (35263, `"        _dash_reference_lines(fig, go, _reported_subopts, gname, _DASH_SCHEME)"`). `seen` is a set made fresh for each render: `self._reported_subopts = set()` (32641) and the app's `_reported_subopts = set()` inside `make_document` (34920). A filter move redraws layer sources only (`_dash_redraw_for`, :35039; saved `_FILTER_JS`), so lines are the same before and after a move.

### E2. The copy rule and the float() reads

`_dash_refline_instances` (26268) starts a copy only at a token `float()` accepts:

```python
26294             try:
26295                 pos = float(tok)
26296             except ValueError:
26297                 bad.append(tok)
```

So `10(5)40` goes to *bad* and the next segment's style overwrites the copy before it (critic: `_dash_refline_instances("20, lcolor(red), 10(5)40, lcolor(blue)")` returns `[([20.0], {'lcolor': 'blue'})]`). `float()` also takes `nan`, `inf`, `1e400` and `1_000`. `_dash_route_line_copies` (2942) uses the same float-start rule (`_dash_route_line_copies("20, 10(5)40, axis(2)")` returns `('', '20, 10(5)40', True)`). The legacy `xline_values` list (:26252-26258) reads `float(v)` too.

### E3. One Span at a time, over the glyphs

```python
26370     for v in values:
26371         fig.add_layout(Span(location=v, dimension=dim, **kw))
```

`Span().level` is `"annotation"` (bokeh 3.9.0; critic gap 4). `_DASH_REFLINE_SUBOPTS = frozenset({"lcolor", "lpattern", "lwidth"})` (26221) is on the served constants tuple (:32944); `_dash_reference_lines`, `_dash_refline_instances`, `_dash_by_tokens_commas` and `_dash_refline_draw` on the functions tuple (33381-33383).

### E4. dash.ado and Mata

`xline(string asis)` etc. are declared at dash.ado:739 (plot) and :984 (graph), returned as `g_xline` (:1248) and `g_xline2` (:1271), merged across copies with ", " by `_dash_rep_merge_locals` (:5289, :5313; category "X", dash_parse.mata:4679) and checked by P0.5's axis requests before the graph rules:

```stata
5323    mata: _dash_axreq_add(st_local("_gopts_axraw"), `n_segs' + 1)
5324    mata: st_local("_axrc", strofreal(_dash_axreq_check(st_local("_g_ys"), st_local("_g_xs"))))
5325    if `_axrc' exit 198
```

`_dash_axfam()` (dash_parse.mata:5348) holds the line family `"line", "lines", "line", "3", "7", "line2"`. `_dash_axreq_add` (5560) stores, per row, side, family, segment, place, axis, the option name, the value as typed, the second-comma word and the bad axis word; `_dash_axreq_check` (5587) sorts by side, family, segment, place (x before y) and refuses the axis and comma problems. S10 makes it 10 columns (column 10: the sub-option problem for the label families).

Limits: `_DASH_LIMITS` (dash_render.py:1064-1073) and dash.ado `_dash_limit_table` (:2770-2782) hold the same rows; `test_resource_limits.py::TestTheLimitsTable` (:566) and :1514 check they agree. A renderer limit error (`DashLimitError`, :1157) surfaces in Stata as r(7102); r(134) is dash.ado's (`_dash_plot_cap_refuse`, :2960-2978).

### E5. twoway's parser and truth (StataNow 19.5)

`/Applications/StataNow/ado/base/_/_gs_parse_and_log_lines.ado` (v1.1.6): `syntax anything [, STyle() NOEXtend EXtend LSTyle() LColor() LWidth() LPattern() LAlign() AXis(passthru)]` (:18); positions through `numlist` (:26-35), any failure `invalid line argument, <text>` r(198); `list uniq` (:80); `lstyle` first, then the l-options (:52-66). Re-measured this pass (`q1.do`-`q3.do`):

```
xline(, foo)                                something required           r(100)
xline(,)                                    something required           r(100)
xline(abc, foo)                             option foo not allowed       r(198)   (sub-options before positions)
xline(3000, foo bar(1))                     option foo not allowed       r(198)
xline(abc, lstyle(p1) lstyle(p2))           option lstyle() not allowed  r(198)
xline(1(1)2501)                             invalid line argument, 1(1)2501   r(198)
xline(3000 nan) / xline(1_000)              invalid line argument, 3000 nan / 1_000
xline(abc) yline(def), yline(def) xline(abc)   invalid line argument, abc   (x before y)
xline(3000, lcolor(red)) xline(abc)         invalid line argument, abc
xline(3000, LColor(red))                    option LColor() not allowed  r(198)
xline(3000, lalign(inside) la(outside))     option la() not allowed      r(198)
xline(3000, ex ex)                          option ex not allowed        r(198)
xline(3000, noextend noextend)              rc 0
xline(3000, st(unextended) style(default))  option style() not allowed   r(198)
xline(3000, ax(1) axis(1))                  option axis() not allowed    r(198)   (P0.5)
xline(3000,, lcolor(red))                   invalid 'lcolor'             r(198)   (P0.5)
xline(3000, axis(2))                        xlines(3000, axis(2)) not allowed, xaxis2 does not exist  (P0.5)
xline(3000, lpattern(bogus))                rc 0, (note:  named style bogus not found in class linepattern, …)
xline(3000, lwidth(abc)) / lcolor(bogus)    rc 0, notes (class linewidth / class color)
xline(3000 3000.0 3e3), xline(-.5), xline(.5e3 1e-3), xline(1/3 2), xline(  2000   2500 , lcolor(red))   rc 0
xline(1(1)2500) xline(2501(1)5000)          rc 0, 5,000 lines
numlist "2000.123456789 0.1(0.1)0.3 1e-10 123456789012 -0"  ->  2000.123456789 .1 .2 .3 1.00000000e-10 123456789012 0
numlist "3000 3000 2000"                    ->  3000 3000 2000   (numlist keeps duplicates; uniq is the parser's)
```

Research §2: `lstyle()`: p1 `#1A476F`, p3 `#55752F`, refline `#2D6D66`, xyline `#C10534`, ci `#808080` (width 8.64), foreground `#000000` 5.76, grid `#EAF2F3`; `none` draws no line; unknown (`p16`, `P1`, `nosuch`) rc 0 with `(note: named style <x> not found in class linestyle, default attributes used)`, `#000000` 5.76. `lalign(inside|outside|center)` no visible change; an unknown value notes "class alignstroke". Draw order (critic, t2.svg): grid 233-316, xline 317-344, markers 345-492. by(): every panel draws every line (t4.svg).

### E6. Tests that pin today's behaviour (flipped in place; re-measured by 39-07, 39-08)

- `test/test_suboption_warnings.py` case `"xline lstyle noextend"` (:72-74): expects `lstyle(foreground)` and `noextend` named, `lcolor` honoured.
- `test/test_mode_parity.py` case `"xline with an unimplemented sub-option"` (:1474-1475) and its expected note (:1907-1908, `"…ignored: lstyle(foreground)"`).
- `test/test_suboption_reporting.cscript` SR-06 (:26, :232-240): `xline(3000, lcolor(red) lstyle(foreground))` names `lstyle()` only.
- `test/test_resource_limits.py::TestTheLimitsTable::test_every_limit_has_a_default_within_its_ceiling` (:570-572): the key set gains `reflines`.
- Guards (unchanged): `test/test_graph_options.py::…::test_xline_invalid_value_no_crash` (:288-291, the renderer never crashes on `xline("notanumber")`), `test/test_axis2_suboptions.py::…::test_route_line_copies_unit` (:504-510), `test/test_served_dates.py::test_xline_in_every_unit`, `test/test_server.py::test_xline_and_yline_both_handled`.

## User stories

- **US-39.1** As a twoway user, I want `xline(2000(500)3000)`, `yline(10(5)40)`, `xline(2000/2002)` and `xline(2000 2500 to 3500)` drawn at every position, in the saved page and the served app, before and after I move a filter.
- **US-39.2** As a twoway user, I want each copy of `yline()` to keep its own style, whatever its positions look like.
- **US-39.3** As a twoway user, I want `xline(3000, lstyle(foreground) lcolor(red))`, `lstyle(grid)` and `lstyle(none)` drawn as twoway draws them, and `lalign()` accepted.
- **US-39.4** As a twoway user, I want dash to refuse the reference lines twoway refuses, in twoway's words and order.
- **US-39.5** As a dashboard viewer, I want reference lines behind the data, as in Stata.
- **US-39.6** As a dashboard publisher, I want a bound on how many lines a dashboard can ask for, so one command cannot hang a build or a browser.

## Business requirements

- **BR-39.1** Positions of `xline()`, `yline()`, `xline2()` and `yline2()` take every form Stata's `numlist` takes (`a(b)c`, `a[b]c`, `a/b`, `x y to z`, `x y:z`, spaced steps, negative steps, decimals, exponents, signs), at most 2,500 per copy, each distinct value of a copy drawn once, in both modes.
- **BR-39.2** Each copy keeps its own sub-options; a copy starts at any run of positions.
- **BR-39.3** dash refuses, in twoway's order (x lines before y lines, copies in command order, the P0.5 axis checks first): an empty position list with a comma, `something required` r(100); an unknown, short, capitalised or repeated sub-option and a second `extend`, `option <typed> not allowed` (or `option <typed>() not allowed`) r(198); positions `numlist` refuses (including `nan`, `inf`, `1e400`, `1_000`, `.`, a zero step, more than 2,500), `invalid line argument, <positions as typed>` r(198).
- **BR-39.4** `lstyle()` takes any line style name; its colour, width and pattern are the base, and `lcolor()`, `lwidth()`, `lpattern()` override them in any order; `none` draws nothing unless a colour is given; an unknown name draws `foreground`'s attributes with a note. Without `lstyle()` the line is the scheme's `xyline`.
- **BR-39.5** `lalign(inside|outside|center)` is accepted with no note; another value is noted as twoway notes it and drawn as without it.
- **BR-39.6** Lines are drawn above the grid and below every glyph, never widen an axis, and are the same before and after any filter move.
- **BR-39.7** A dashboard whose reference-line positions × by() panels pass the `reflines` limit (default 10,000, `$dash_max_reflines`, at most 100,000) is refused r(134). The panels are counted over every observation, an upper bound. The message names the count ("up to"), the limit and the global.
- **BR-39.8** A spec not written by dash.ado draws what it can: a run that does not expand is named in the note, a non-finite or `_` position is never drawn, and nothing crashes.
- **BR-39.9** `extend`, `noextend` and `style()` are still parsed and named as not drawn (S50).

## Technical requirements

- **TR-39.1 Mata: line rows** (dash_parse.mata; `_dash_axreq_*` after S10, found by name).
  - `_dash_axreq_clear()` makes 12 columns, and every `cols(…) != 10` test in `_dash_axreq_clear`, `_dash_axreq_add` and `_dash_axreq_check` becomes `!= 12`; the header-index entries name columns 11-12.
  - `_dash_axreq_add`, for a row of the line family only: column 10 = the message of `_dash_so_resolve(words, J(1, cols(words), 1), "refline", names, msg, at)` (S10's twin), or, when it finds none, `option <typed> not allowed` for a second token whose resolved name is `extend` (E5: `ex ex`; a repeated `noextend` stays accepted); column 11 = `body` (the positions before the first comma), stripped; column 12 = `"1"` when `body` is empty, else `""`. An empty `body` with a comma in the value sets column 10 to `100|something required` (it is tested first, BR-39.3).
  - `_dash_axreq_check`, per sorted row, after S10's column-9 test: column 10 → `_dash_say("err", <message>)`, clear, return 198 (or 100 for the `100|` form); then, for a line row whose column 12 is `""`: if `_dash_so_unsafe(column 11)` → `_dash_say("err", "invalid line argument, ", column 11)`, clear, return 198; else set the caller's locals `_ln_text` (column 11) and `_ln_row` (the row's index in the stored matrix) through `st_local` and return −1 without clearing.
  - New `void _dash_axreq_accept_line(real scalar row)` sets that row's column 12 to `"1"`.
  - No `regexm`; byte loops; every message through `_dash_say`.
- **TR-39.2 dash.ado: the check loop** (`_dash_plot`, the three lines E4 quotes, as S10 left them):
  ```stata
  mata: st_local("_axrc", strofreal(_dash_axreq_check(st_local("_g_ys"), st_local("_g_xs"))))
  while `_axrc' == -1 {
      _dash_line_check
      mata: st_local("_axrc", strofreal(_dash_axreq_check(st_local("_g_ys"), st_local("_g_xs"))))
  }
  if `_axrc' exit `_axrc'
  ```
  The loop's call is ``_dash_line_check `_ln_row' `"`macval(_ln_text)'"'``. New program `_dash_line_check` (`version 19`; after `_dash_plot`'s `end`; not rclass; `args row t`): ``capture numlist `"`macval(t)'"'`` (no `max()`: twoway's own 2,500 cap applies); on any rc `mata: _dash_axreq_clear()`, `mata: _dash_say("err", "invalid line argument, ", st_local("t"))`, `exit 198`; else `mata: _dash_axreq_accept_line(`row')`. The text is only ever expanded inside `macval()`, and only after `_dash_so_unsafe` passed (TR-39.1).
- **TR-39.3 dash.ado: `_dash_line_expand`** (new, `version 19`, after `_dash_line_check`). Called in `_dash_plot` directly after the loop of TR-39.2, as `_dash_line_expand g_xline g_yline g_xline2 g_yline2`. For each named local, split its value at top-level commas by calling the existing `mata: _dash_comma_pos(st_local("rest"), "cpos")` (dash_parse.mata:1863, the first comma outside parentheses; 0 when there is none) in a `while` loop on the remainder. No new Mata function is added. Then a segment whose first non-blank byte is a digit, `+`, `-`, `.` or `(` starts a copy and is replaced by the copy's positions: ``numlist `"`macval(seg)'"'`` (already accepted by TR-39.2), then `local nl : list uniq nl`; other segments are kept as typed. The copies are re-joined with ", " and written back with `c_local`. A value with no position segment (S51's folded `tline` numbers are positions) is unchanged. It never refuses (TR-39.2 has).
- **TR-39.4 dash.ado: the `reflines` limit.**
  - `_dash_limit_table` gains `reflines=10000,100000` (after `filters`).
  - New program `_dash_reflines_of` (rclass, `version 19`): `args gjson`; Mata `_dash_reflines_positions(st_local("gjson"))` (new, after `_dash_computed_cells`) counts the position tokens of `xline`, `yline`, `xline2` and `yline2` in the graph JSON (positions already expanded); the panels: none when the JSON has no `by`; else `_dash_refline_panels` (new ado, `version 19`; a new name, because `_dash_by_panels` already exists at dash.ado:3340, rclass `r(kept)`, called by `_dash_plot` at :5514 and read by S56, and stays unedited) parses the `by` value as `syntax varlist [, TOTal MISsing *]` on `` `"`macval(by)'"' `` (names already validated), counts `egen tag()` groups over all observations (`missing` keeps groups with a missing value), adds one for `total`, and caps at `_dash_limit, name(by_groups)`. `return scalar n = positions * max(panels, 1)`. The graph's own if/in is not applied: the count is an upper bound of what is drawn (documented).
  - New program `_dash_reflines_cap` (`version 19`): `args n`; `_dash_limit, name(reflines)`; over the limit it prints, through `_dash_count_fmt`, `dash: this dashboard asks for up to <n> reference lines (positions times by() panels), more than the <lim> one dashboard draws.` ("up to": the panels are counted over every observation, Q-39.1) and `      Draw fewer lines, or set global dash_max_reflines to a higher value (at most <ceil>).`, then `exit 134`.
  - Call sites, each a paragraph of its own (R6): in `_dash_render_immediate`, after the `_dash_cell_cap` block (about :6690), `_dash_reflines_of` on the graph's JSON then `_dash_reflines_cap r(n)`; in `_dash_prepare_spec`'s registry loop (about :7530-7700), the sum over every graph of `r(n)`, then `_dash_reflines_cap` after the loop, before any export.
  - `_needed` (dash.ado:255) gains `_dash_axreq_accept_line _dash_reflines_positions`.
- **TR-39.5 Renderer: copies and positions** (dash_render.py).
  - New `_dash_refline_copies(raw)` (after `_dash_by_tokens_commas`): `[(positions_text, sub_tokens), …]`, one entry per copy, a copy starting at every top-level-comma segment whose first non-blank character is a digit, `+`, `-`, `.` or `(`; the first segment always starts one.
  - New `_dash_refline_positions(text, bad)`: tokens of `text` (blank-split as `_dash_axis_tokens` cuts); a token holding `_`, or one `float()` reads as non-finite, goes to *bad*; `_dash_expand_numlist(tokens, limit=2500)` (called, not edited); `too_many` → the whole text to *bad* and `[]`; `bad` tokens appended; result deduplicated in order and filtered to finite values.
  - `_dash_refline_instances(raw, bad)` rebuilt on these two: each copy's positions from `_dash_refline_positions`, its sub-tokens canonicalised with `_dash_subopt_canon(name, _DASH_REFLINE_SUBOPT_TABLE)` as S10 left it (honoured: `_DASH_REFLINE_SUBOPTS`), the rest (`extend`, `noextend`, `style`, unknown) to *bad* as typed. A copy whose positions are all bad keeps no line but its style never leaks into another copy.
  - `_DASH_REFLINE_SUBOPTS` becomes `frozenset({"lcolor", "lpattern", "lwidth", "lstyle", "lalign"})` in place.
  - `_dash_route_line_copies(raw)` uses `_dash_refline_copies` for its copy split (warn: HIGH); its routing of each copy is unchanged.
  - The legacy `xline_values` list reads each value through `_dash_refline_positions(str(v), bad)`.
- **TR-39.6 Renderer: drawing.**
  - `_dash_refline_draw(fig, opt, dim, values, style, scheme, Span, range_name="default")`: the base is `scheme.style_bundle("line", style["lstyle"])` when `lstyle` is given (with `scheme` `None`, `SchemeParser.fallback()`), else the xyline style as today; then S30's `lcolor` read, then `lpattern`, `lwidth` (S13's `default_px` = the base's width); a `None` colour after all of them draws nothing for that copy. `lalign`: `inside`, `outside`, `center` silent; another value `_dash_warn_once(("refline-lalign", _dash_display(v)), f"dash: named style {_dash_display(v)} not found in class alignstroke, default attributes used")`. Every Span gets `level="underlay"`. The Spans of one call are added with one assignment, `fig.center = [*fig.center, *spans]`.
  - `_dash_reference_lines`: before drawing a figure's copies it counts their positions and calls `_dash_refline_tally(seen, n)`; past `_DASH_LIMITS["reflines"][1]` (the ceiling) it raises `DashLimitError("dash: this dashboard draws more than 100,000 reference lines (positions times by() panels), the most any dashboard draws.")`. The effective `$dash_max_reflines` is dash.ado's (TR-39.4); the renderer's bound is for a spec that came another way (`_dash_refuse_oversized`'s rule).
  - New `_dash_refline_tally(seen, n, _slot=[None, 0])`: a one-slot tally keyed by the identity of the render's `seen` set. The slot holds the set object itself, so its `id` cannot be reused while it is held. It resets when a different set arrives (`is not`), and `seen` `None` counts this call alone. It returns the running total. Docstring: `make_document` and `render` are synchronous, so one slot is enough; S57 audits it under its worker.
  - `_DASH_LIMITS` gains `"reflines": (10_000, 100_000, "dash_max_reflines")`, its comment block one line.
- **TR-39.7 Both modes and the copy list.** No call site changes. R2 row S39: in `_glyph_layer_lines`' functions tuple, directly after `"_dash_refline_draw",` (33383), add `"_dash_refline_copies", "_dash_refline_positions", "_dash_refline_tally",`. `_DASH_REFLINE_SUBOPTS` and `_DASH_LIMITS` are already copied and change in place. No JavaScript twin: a filter move never touches a Span.
- **TR-39.8 Registries.** Under S39's anchor in `test/function_test_map.py`: `'_dash_refline_copies'`, `'_dash_refline_positions'`, `'_dash_refline_tally'` → their `test/test_reference_lines.py` nodes. Under S39's anchors in `test/program_coverage_map.py`: `COVERAGE["dash.ado"]` `_dash_line_check`, `_dash_line_expand`, `_dash_refline_panels`, `_dash_reflines_cap`, `_dash_reflines_of` → `test/test_suboption_reporting.cscript`; `COVERAGE["dash_parse.mata"]` `_dash_axreq_accept_line`, `_dash_reflines_positions` → the same script.
- **TR-39.9 Help** (dash.sthlp; R3 rows S39). Axis and Display Options: the synopsis lines `{cmdab:xli:ne(}…` and `{cmdab:yli:ne(}…` (2755-2756 at `c96facd`) become `xline(linearg)`/`yline(linearg)`, and a paragraph "Reference lines" directly after the `xline2`/`yline2` entries says: numlist positions, uniq per copy, 2,500 per copy, each copy its own style, the sub-options and spellings, `lstyle()` names, `lalign()` accepted, the refusals with their words, drawn under the data and never widening an axis, `extend`/`noextend`/`style()` still named. Resource limits: a `$dash_max_reflines` synopt after `$dash_max_by_groups`'s, stating the count (positions × by() panels, panels counted over every observation), default, ceiling and r(134). Lines ≤ 79 characters; no tool or vendor name.
- **TR-39.10 Security (rule 1).** Positions reach `numlist` only after `_dash_so_unsafe` passes and only inside ``macval()`` in double quotes; nothing else from the text reaches a command line. The renderer reads positions without `float()` on raw text except per token after `_` and non-finite filters; `_dash_expand_numlist` bounds every count before generating values. Spans are bounded by the `reflines` limit (dash.ado) and the ceiling (renderer). Every echo goes through `_dash_say`/`_dash_display`. G9's threat: a do-file or spec that asks for millions of Spans (denial of service), and code on Stata's command line through position text; both closed and pinned (`TestTheLimit`, XP-06).

## Boundaries

- **S50 (P1.21b):** `extend`, `noextend`, `style()`, the scheme's `xyline_extend_*` keys, Arrows and every after-move re-finish; S39 only parses, refuses (the `ex ex` rule) and names them.
- **S51 (P1.6):** `tline()`, the t side of `_dash_axreq`, and writing tline as explicit numbers into `g_xline` before TR-39.2/39.3 run.
- **S35/P1.23:** date positions (`_dash_axis_positions`) unchanged; axis-2 date units are not this section's.
- **S43:** a bare `*#`/`%#` in `lcolor()`.
- **P2.54:** a line outside the range stays clipped at the frame (twoway draws it outside).
- **Not touched:** `_dash_expand_numlist`, `_dash_report_suboptions`, `_dash_style_note`, `_dash_by_tokens_commas` (HIGH, 7 impacted; called), `_dash_range_hull`, `_make_figure_body`, `_generate_app_source`, `_build_sources_and_figures`, S10's tables and resolver, S36's `style_bundle`.

## Stata truth

### `scripts/extract_refline_truth.do` → `test/fixtures/refline_truth.json`

S02's stanza, then `adopath ++ "`repo'/"` and `global dash_nobrowser 1`; S19's `_meta` form (four keys; `shell` into a local; no `shell=True`; backtick `\x60`). Data `sysuse auto`; `twoway scatter mpg weight, <opt>`; each probe `capture noisily` in a named log; SVGs to `c(tmpdir)`, read with `scripts/svg_truth.py` `svg_lines` and `line_groups` (dashed lines grouped), the reference lines told from the grid by their drawing order between the grid and the first marker.
- **P (positions), s2color, SVG:** P01 `xline(2000(500)3000)`, P02 `2000[500]3000`, P03 `2000 (500) 3000`, P04 `2000/2002`, P05 `2000 2500 to 3500`, P06 `2000 2500:3500`, P07 `3500(-500)2000`, P08 `2000(250.5)3000`, P09 `2e3 3e3`, P10 `+2000 -1`, P11 `3000 3000`, P12 `yline(20, lcolor(red)) yline(10(5)40, lcolor(blue))`, P13 `xline(2000(500)3000, lcolor(red)) xline(4000)`, P14 `yline(10(5)40)`, P15 `xline(1(1)2500) xline(2501(1)5000)` (count only). Records: rc, each line's data position (from `svg_axis_reading`), stroke.
- **R (refusals), nodraw:** R01-R24, every refusal line of E5 in its order, plus `xline(1(0)5)`, `xline(.)`, `xline(. 3000)`, `xline(1e400)`, `xline(2000 3000 to)`, `xline(2000,3000)`, `xline(3000, s(unextended))`, `xline(3000, noe)`, `xline(3000, ls(p1))`, `xline(3000, l(red))`, `xline(3000, NOEXTEND)`, `xline(3000, extend extend)`, `xline(3000, ex extend)`, `xline(3000, noex noextend)`; and the accepted spellings `st lst lc lw lp la ax noex ex` (rc 0). Records: rc, first error line.
- **S (styles), SVG, under s2color, stcolor, s1mono:** S01-S16 `xline(3000, lstyle(<n>))` for `p1 p3 p1line refline xyline ci foreground grid none p16 P1 nosuch`, plus `lstyle(foreground) lcolor(red)`, `lcolor(red) lstyle(foreground)`, `lstyle(p1) lpattern(dash)`, `lstyle(none) lcolor(red)`; and L01-L04 `lalign(inside|outside|center|nosuch)` with `lwidth(vthick)`. Records: stroke, width, dasharray, presence, notes.
- **O (order), s2color, SVG:** O01 `xline(3000) ` with the grid on: the line's element index between the grid's last and the first marker's (`above_grid`, `below_markers` booleans).
- **B (by), SVG:** B01 `by(foreign) xline(3000)`: lines per panel.
- Run: `DASH_REPO="$WT" "$SLOT" "$S" "$WT/scripts/extract_refline_truth.do"` (log `$S/extract_refline_truth.log`; about 110 probes, 70 exports). `git add -f test/fixtures/refline_truth.json`.

### Area cases, `test/test_suboption_reporting.cscript` (R1; one contiguous run at the end of its last case block, before its summary lines, after S10's and S31's runs)

Each case runs live twoway (`capture twoway scatter mpg weight, <opt> nodraw`, rc and first error line from a log) and `dash scatter mpg weight, <opt>` in the script's form, printing `XP-nn PASS: …`.
- **XP-01:** the 24 R probes: dash rc and first error line equal twoway's.
- **XP-02:** order: `xline(abc) yline(def)` and `yline(def) xline(abc)` name `abc`; `xline(3000, lcolor(red)) xline(abc)` names `abc`; `xline(abc, foo)` names `foo`; `xline(, foo)` is r(100).
- **XP-03:** accepted spellings and `xline()`, `xline(3000,)`, `noextend noextend`: rc 0 both.
- **XP-04:** the spec of `dash scatter mpg weight, xline(2000(500)3000, lc(red)) xline(4000) yline(10/12 11)` holds `xline` `2000 2500 3000, lc(red), 4000` and `yline` `10 11 12` (`_ztp_hasval`-style read of the JSON).
- **XP-05:** `xline(2000 2500 3000)` written by hand as explicit numbers passes unchanged (S51's form).
- **XP-06:** `xline(`"1 `"x"'"')` and `xline(1$x)` are refused `invalid line argument, …` r(198) without running `numlist` on them (a `set trace` count of `numlist` lines is 0).
- **XP-07:** `global dash_max_reflines 5`, `dash scatter mpg weight, xline(1/6)`: r(134) and the two message lines; `by(foreign) xline(1/3)`: r(134) (3 × 2 panels); `macro drop dash_max_reflines` after.
- **XP-08:** `_dash_line_expand` alone on `"20, lcolor(red), 10(5)40, lcolor(blue)"` gives `"20, lcolor(red), 10 15 20 25 30 35 40, lcolor(blue)"`.

### The S39 block of `test/test_wp30_truth.cscript` (R1)

Fills S01's S39 stub; helper `_s39_spans` (python, above S39's header) returns a saved page's Span `location`, `line_color`, `line_width`, `line_dash`, `level` per figure.
- **XP-20:** P01, P05, P12, P13 drawn by `dash … saving()`: locations and colours equal twoway's (the fixture's values, re-measured live in the block).
- **XP-21:** `lstyle(foreground) lcolor(red)`: colour red, width over the default line's equal to twoway's 5.76/8.64 within 2 %.
- **XP-22:** `lstyle(none)`: no Span; `lalign(inside)`: one Span, no note.
- **XP-23:** every Span's `level` is `underlay`.

## TDD test stubs

### Regression tests, new `test/test_reference_lines.py` (red at the batch-14 base unless marked guard; 39-01)

Harness from `test_mode_parity`: `_standalone`, `_served`, `_served_after_move`, `_MOVES`, `_sc`; from `test_saved_filter_layers`: `_render`, `_move`. `_FIX = json.load(test/fixtures/refline_truth.json)`; `_spans(fig)` → `[(location, line_color, line_width, line_dash, level)]`.
- Test: the fixture is stamped (four keys, `19.`), holds every probe id — `TestTheFixture::test_it_is_stamped`
- Test (both modes): P01-P14's positions and colours equal the fixture's — `TestPositions::test_probe[<id>-saved|served]`
- Test: `_dash_refline_copies("20, lcolor(red), 10(5)40, lcolor(blue)")` is two copies; `"3000, lcolor(red) noextend, 4000"` two; `"(500)3000"` one — `TestPositions::test_a_copy_starts_at_any_position_run` [AttributeError]
- Test: `_dash_refline_positions` on `nan 3000`, `inf`, `1e400`, `1_000`, `1(1)2501`, `abc` → finite values only and the bad tokens; `3000 3000.0 3e3` → `[3000.0]`; 10,000-token text under 0.5 s — `TestPositions::test_the_fallback_reads_as_numlist`
- Test: `_dash_route_line_copies("20, 10(5)40, axis(2)")` is `("20", "10(5)40", True)` — `TestPositions::test_routing_uses_the_same_copies`
- Test (both modes): S01-S16 under three schemes: colour, width ratio to the default line within 2 %, dash pattern and presence equal the fixture; `lcolor()` wins in either order — `TestLstyle::test_probe[<scheme>-<id>-saved|served]`
- Test (both modes): unknown names (`p16`, `P1`, `nosuch`) draw `foreground`'s attributes with one S36 note each — `TestLstyle::test_an_unknown_name_is_noted[<name>]`
- Test (both modes): `lalign(inside|outside|center)` no note, identical Spans to no `lalign`; `lalign(nosuch)` one note "…class alignstroke…" — `TestLalign::test_silent_and_noted[<v>-saved|served]`
- Test (both modes): `noextend`, `extend`, `style(unextended)` are named as not drawn; `lstyle`, `lalign` are not — `TestStillNamed::test_extent_is_s50s[saved|served]`
- Test (both modes): every Span's `level == "underlay"`; a figure with 2,500 positions adds its Spans in one `center` assignment (a spy on `fig.center`'s setter counts 1 per `_dash_reference_lines` call) and renders in under 3 s — `TestDrawing::test_level_and_bulk[saved|served]`
- Test: lines are not in S21's hull: `xline(100000)` leaves the x range as without it, both modes — `TestDrawing::test_a_line_never_widens_an_axis[saved|served]` (guard if S21 already held it)
- Test: saved (node) and served moves keep every Span — `TestAfterAFilterMove::test_lines_survive[saved|served]`
- Test: `_dash_refline_tally`: a new set resets, the same set accumulates, `None` counts one call; `_dash_reference_lines` past the ceiling raises `DashLimitError` in both modes (a spec of 100,001 positions) — `TestTheLimit::test_the_renderer_ceiling[saved|served]`
- Test: `dr._DASH_LIMITS["reflines"] == (10_000, 100_000, "dash_max_reflines")` and dash.ado's `_dash_limit_table` holds `reflines=10000,100000` — `TestTheLimit::test_the_row`
- Test: the generated app defines the three new helpers — `TestTheServedCopy::test_the_app_carries_the_helpers`
- Test: dash.sthlp holds `xline(linearg)`, the `$dash_max_reflines` row and "Reference lines" in Axis and Display Options — `TestTheHelp::test_the_help_documents_it`
- Test (cscript): XP-01..XP-08; XP-20..XP-23.
- Shared: `test/test_mode_parity.py` CORPUS `_case("Reference-line numlists and lstyle (WP-30 P1.21a)", [_sc()], None, {"xline": "2000(500)3000, lc(red) lstyle(foreground), 4000", "yline": "10/12, lstyle(grid)"})`.

### Pinned tests to flip (R9; re-measured)

E6's four: `test_suboption_warnings.py` "xline lstyle noextend" → named `["noextend"]`, honoured `["lcolor", "lstyle"]`; `test_mode_parity.py` "xline with an unimplemented sub-option" → `"3000, lcolor(red) noextend"` and its expected note `"dash: xline() sub-option(s) not implemented and ignored: noextend"`; SR-06 → `xline(3000, lcolor(red) lstyle(foreground) noextend)` names `noextend` only (its header line :26 and PASS text updated); `TestTheLimitsTable`'s key set gains `"reflines"` with `# 8 -> 9 keys: P1.21a reflines`.

## Test plan

| What | How | Fixture / data | Both modes? |
|---|---|---|---|
| Refusals, order, spellings | cscript XP-01..XP-03 vs live twoway | R probes | n/a |
| Expansion and spec | cscript XP-04, XP-05, XP-08 | auto | n/a |
| Positions vs twoway | pytest `TestPositions`; cscript XP-20 | P probes | yes |
| lstyle, lalign | pytest `TestLstyle`, `TestLalign`; cscript XP-21, XP-22 | S, L probes | yes |
| Draw order, bulk, hull | pytest `TestDrawing`; cscript XP-23 | O probe | yes |
| After moves | pytest `TestAfterAFilterMove` (node saved; served) | `_DF` | yes |
| Limit and security | pytest `TestTheLimit`; cscript XP-06, XP-07 | literal | yes |
| Parity | `test_mode_parity.py` CORPUS case | `_DF` | yes |
| Served wiring | `TestTheServedCopy`; G4 guards | generated app | served |
| Help, registries, tracking | `TestTheHelp`, `test_help_conformance.py`, `test_function_test_map.py`, `test_program_coverage_map.py`, `test_resource_limits.py`, `test_tracking_documents.py`, `test_fixtures_are_committed.py` | — | n/a |

**Acceptance criteria.**
- **AC-39.1** (BR-39.1, BR-39.2) `TestPositions` passes for every P probe in both modes; XP-04, XP-08 and XP-20 PASS.
- **AC-39.2** (BR-39.3) XP-01..XP-03 PASS against live twoway: rc and first line equal for all 24 refusals.
- **AC-39.3** (BR-39.4, BR-39.5, BR-39.9) `TestLstyle`, `TestLalign`, `TestStillNamed` pass under s2color, stcolor, s1mono; XP-21, XP-22 PASS.
- **AC-39.4** (BR-39.6) `TestDrawing` and `TestAfterAFilterMove` pass (node not skipped); XP-23 PASS.
- **AC-39.5** (BR-39.7, BR-39.8) `TestTheLimit` passes; XP-06, XP-07 PASS; `test_graph_options.py::…::test_xline_invalid_value_no_crash` still passes.
- **AC-39.6** Every flipped node passes with its `Flipped:` line; none deleted; one full run through the queue reports 0 failed; G7 prints 0 before and after the commit.

## Tasks

**Commit boundary.** Tasks 39-01 to 39-12 form one commit, made by 39-12 on `wp30-s39` with the subject `Draw xline() and yline() numlists and lstyle() as twoway does (WP-30 P1.21a)`; it closes the entry, deletes its key and replaces both markers. `$S` is `/private/tmp/claude-501/-Users-billy-Desktop-Programs-StataPrograms-d-dash/55d6df3b-6200-4eb1-99b7-fa28b88519a2/scratchpad/wp30`, `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s39`, `$SLOT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh`. A cscript runs through the driver: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" "<script>.cscript" > "$S/run_<script>.do"`, then `WP30_ONLY=S39 "$SLOT" "$S" "$S/run_<script>.do"` (log `$S/run_<script>.log`).

<task type="auto" id="39-01">
  <name>Write the refline fixture and tests</name>
  <files>scripts/extract_refline_truth.do, test/test_reference_lines.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Check `git -C "$WT" rev-parse HEAD` equals `cat "$S/batch-14-base.txt"` and `git -C "$WT" branch --show-current` prints `wp30-s39`; stop otherwise. Create `scripts/extract_refline_truth.do` exactly as "Stata truth" describes and run it with `DASH_REPO="$WT" "$SLOT" "$S" "$WT/scripts/extract_refline_truth.do"`; it writes `test/fixtures/refline_truth.json`. Create `test/test_reference_lines.py` with every stub, naming `dr._dash_refline_copies`, `dr._dash_refline_positions` and `dr._dash_refline_tally` so they fail with AttributeError now. Append the CORPUS case to `test/test_mode_parity.py` before `CORPUS`'s closing bracket. Run `python3 -m pytest test/test_reference_lines.py -q -n 6 -p no:cacheprovider -rf > "$S/39-new.log" 2>&1` and the parity file with `-k "P1.21a"` appended. Write `$S/39-P1.21a-failure.txt`: the base sha, one line per failing node, then "Guards (pass at the base)". Edit no shipped file; do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json; d=json.load(open('$WT/test/fixtures/refline_truth.json')); p=d['probes']; print(all(k in d['_meta'] for k in ('stata_version','born_date','dash_commit','extracted')), len(p['P01']['lines']), p['R01']['rc'])"` prints `True 3 100`; `grep -c FAILED "$S/39-new.log"` is at least 20; `git -C "$WT" diff --name-only -- dash.ado dash_parse.mata dash_render.py` prints nothing.]]></verify>
  <done>The twoway reference-line fixture existed and every pytest regression test was shown failing on the unmodified tree, with the failure text saved.</done>
</task>

<task type="auto" id="39-02">
  <name>Write the refusal and truth script cases</name>
  <files>test/test_suboption_reporting.cscript, test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Append XP-01..XP-08 of "Stata truth" to `test/test_suboption_reporting.cscript` as one contiguous run at the end of its last case block (after S10's and S31's runs), before its summary lines, with a header comment line and a `*!` line per case in its header list. Put `_s39_spans` directly above S01's `* ==== S39 P1.21a: …` header of `test/test_wp30_truth.cscript` and XP-20..XP-23 between S39's start and end lines. Run both through the driver on the unmodified shipped files; append every `XP-nn FAIL` line and the twoway line it quotes to `$S/39-P1.21a-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -cE "XP-0[1-8] FAIL" "$S/run_test_suboption_reporting.log"` is at least 6 (XP-03 and XP-05 may pass as guards); `grep -cE "XP-2[0-3] FAIL" "$S/run_test_wp30_truth.log"` is at least 3.]]></verify>
  <done>The live twoway comparisons for refusals, expansion, the limit and drawing were in place and shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="39-03">
  <name>Refuse lines in the Mata axis rows</name>
  <files>dash_parse.mata</files>
  <action><![CDATA[
    The axis-request functions are UNKNOWN to the index; `grep -n "_dash_axreq_" dash.ado dash_parse.mata` confirms `_dash_plot` is their only caller. Apply TR-39.1 (twelve columns, the line rows' columns 10-12, the `100|` form, the −1 return with `_ln_text`/`_ln_row`, the new `_dash_axreq_accept_line`) and TR-39.4's Mata `_dash_reflines_positions` (after `_dash_computed_cells`), with header-index entries. Edit no other family's branch.
  ]]></action>
  <verify><![CDATA[After 39-04 the scripts run; at this task: `python3 -m pytest test/test_file_headers.py -q -n0 -p no:cacheprovider` passes, and a scratch do-file that loads `dash_parse.mata` and runs `_dash_axreq_clear()`, `_dash_axreq_add("xline(abc, foo)", 1)`, `_dash_axreq_check("1","1")` prints `option foo not allowed` and 198.]]></verify>
  <done>Mata judged every line copy as twoway does, in twoway's order, and handed position lists back for Stata's own numlist.</done>
</task>

<task type="auto" id="39-04">
  <name>Check, expand and cap lines in dash.ado</name>
  <files>dash.ado</files>
  <action><![CDATA[
    Apply TR-39.2 (the loop and `_dash_line_check`), TR-39.3 (`_dash_line_expand` and its call), TR-39.4 (`reflines` in `_dash_limit_table`, `_dash_reflines_of`, `_dash_refline_panels`, `_dash_reflines_cap`, the two call paragraphs, `_needed`), each new program with a header comment citing E5 and `version 19`. Positions go on `numlist`'s line only inside `macval()` after `_dash_so_unsafe` passed. Edit no other program and no other paragraph of `_dash_render_immediate` or `_dash_prepare_spec`.
  ]]></action>
  <verify><![CDATA[`test_suboption_reporting.cscript` through the driver prints `XP-01 PASS` to `XP-08 PASS` and its earlier cases still pass except SR-06 (39-08); `test_twoway_option_parity.cscript` through the driver still prints its AX cases PASS; `python3 -m pytest test/test_resource_limits.py -q -n 6 -p no:cacheprovider -k "table or Table"` reports only the key-set pin failing (39-07).]]></verify>
  <done>dash.ado refused what twoway refuses, wrote expanded positions into the spec and refused a dashboard over the reflines limit with r(134).</done>
</task>

<task type="auto" id="39-05">
  <name>Read copies and positions in the renderer</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn in the task log that `_dash_route_line_copies` is HIGH (3 impacted) and that `_dash_expand_numlist` (CRITICAL) is called, not edited. Apply TR-39.5: `_dash_refline_copies` and `_dash_refline_positions` after `_dash_by_tokens_commas`, `_dash_refline_instances` rebuilt on them, `_DASH_REFLINE_SUBOPTS` in place, `_dash_route_line_copies`' copy split, the legacy `xline_values` read. Run `test_axis2_suboptions.py`, `test_graph_options.py`, `test_served_dates.py` with `-n 6`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_reference_lines.py -q -n 6 -p no:cacheprovider -k "TestPositions"` passes; the three files of the action report 0 failed.]]></verify>
  <done>Both modes read every copy's positions as Stata's numlist reads them, each copy keeping its own style.</done>
</task>

<task type="auto" id="39-06">
  <name>Draw lines under the data, in bulk</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn in the task log that `_glyph_layer_lines` is HIGH (4 impacted). Apply TR-39.6 (`lstyle` base through `style_bundle`, `lalign`, `level="underlay"`, the one `center` assignment, `_dash_refline_tally` and the ceiling in `_dash_reference_lines`, `_DASH_LIMITS["reflines"]`) and TR-39.7 (the three names after `"_dash_refline_draw",`). Change neither call site of `_dash_reference_lines`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_reference_lines.py -q -n 6 -p no:cacheprovider` passes except `TestTheHelp`; `python3 -m pytest "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" "test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads" test/test_server.py -q -n 6 -p no:cacheprovider -k "xline or yline or ServedApp"` reports 0 failed.]]></verify>
  <done>Lines took any line style, were drawn above the grid and below the data in one assignment per figure, and the renderer refused a spec past the ceiling.</done>
</task>

<task type="auto" id="39-07">
  <name>Flip the pytest pins</name>
  <files>test/test_suboption_warnings.py, test/test_resource_limits.py</files>
  <action><![CDATA[
    Re-measure and flip E6's two pytest pins as "Pinned tests to flip" says, each with `Flipped (WP-30 P1.21a): <old> was wrong because twoway draws lstyle() (refline_truth.json S probes)` or `… because P1.21a adds the reflines limit (A68)`. Write one `Flipped:` line per node to `$S/39-flips.txt`. Delete no test.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_suboption_warnings.py test/test_resource_limits.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>The tests that pinned lstyle() as ignored and the eight-key limits table asserted the new behaviour, with reasons recorded.</done>
</task>

<task type="auto" id="39-08">
  <name>Flip the parity and SR-06 pins</name>
  <files>test/test_mode_parity.py, test/test_suboption_reporting.cscript</files>
  <action><![CDATA[
    Flip the parity case and its expected note, and SR-06 (case text, header line, PASS text), as "Pinned tests to flip" says, with the same comment form. Append the `Flipped:` lines to `$S/39-flips.txt`. Delete no test.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_mode_parity.py -q -n 6 -p no:cacheprovider` reports 0 failed; `test_suboption_reporting.cscript` through the driver prints `SR-06 PASS` and `test_suboption_reporting: ALL CHECKS PASSED`.]]></verify>
  <done>The parity corpus and SR-06 named only the extent sub-options still not drawn.</done>
</task>

<task type="auto" id="39-09">
  <name>Register the new functions and programs</name>
  <files>test/function_test_map.py, test/program_coverage_map.py</files>
  <action><![CDATA[
    Apply TR-39.8 under S39's anchors, alphabetically.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_function_test_map.py test/test_program_coverage_map.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>Every new function and program was mapped to the tests that run it.</done>
</task>

<task type="auto" id="39-10">
  <name>Document reference lines and the limit</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    Apply TR-39.9 in Axis and Display Options and Resource limits only (R3), finding each place by its text. Every new or changed line is at most 79 characters; no tool or vendor name.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "test/test_reference_lines.py::TestTheHelp" test/test_help_conformance.py test/test_resource_limits.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>The help described numlist positions, the sub-options, the refusals, the drawing order and the reflines limit.</done>
</task>

<task type="auto" id="39-11">
  <name>Run the section and full suites</name>
  <files>none</files>
  <action><![CDATA[
    Run `test_reference_lines.py test_mode_parity.py test_suboption_warnings.py test_resource_limits.py test_axis2_suboptions.py test_graph_options.py test_served_dates.py test_cscript_hygiene.py test_fixtures_are_committed.py` with `-n 6`, and `test_suboption_reporting.cscript`, `test_twoway_option_parity.cscript` and the S39 truth block through the driver. Then `git -C "$WT" merge --no-edit main` (expect `Already up to date.`) and one full run `"$S/full_suite_queue.sh" "$WT" "$S/39-full.log"` in the background, read when its `exit=` line appears, never relaunched (E6).
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/39-full.log"` shows 0 failed and `exit=0`; `grep -c "XP-2[0-3] PASS" "$S/run_test_wp30_truth.log"` prints 4.]]></verify>
  <done>The section's tests, its script cases and one full suite run were green on the worktree.</done>
</task>

<task type="auto" id="39-12">
  <name>Close the entry and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Read the title as `WP30_OPEN["P1.21a"]`. Close that BUGS.md entry in place (`- [x]`) with "Notes: BUGS.md Resolution". Delete the `"P1.21a"` key line of `WP30_OPEN`. Replace both `<!-- WP-30 P1.21a -->` markers in place with "Notes: CHANGELOG lines". Run `test_tracking_documents.py` with `-n0`. Stage exactly dash.ado dash_parse.mata dash_render.py dash.sthlp scripts/extract_refline_truth.do test/test_reference_lines.py test/test_mode_parity.py test/test_suboption_reporting.cscript test/test_wp30_truth.cscript test/test_suboption_warnings.py test/test_resource_limits.py test/function_test_map.py test/program_coverage_map.py BUGS.md CHANGELOG.md test/test_tracking_documents.py, and `git add -f test/fixtures/refline_truth.json`; check `git -C "$WT" diff --cached --name-only` lists those 17 only (G6). Write `$S/39-message.txt` per "Notes: commit message", check G7, confirm the branch, commit, check G7 again, and report the sha and message to the merger.
  ]]></action>
  <verify><![CDATA[`grep -c '<!-- WP-30 P1.21a -->' "$WT/CHANGELOG.md"` prints 0; `grep -c '^    "P1.21a": "' "$WT/test/test_tracking_documents.py"` prints 0; `git -C "$WT" log -1 --format=%s` ends `(WP-30 P1.21a)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Entry P1.21a was closed naming existing tests, its markers carried the measured old and new behaviour, and one green commit on wp30-s39 was ready for the merger.</done>
</task>

## Section completion criteria

- Every numlist form draws twoway's lines in both modes, before and after moves; each copy keeps its style; duplicates in a copy draw once.
- dash refuses every line form twoway refuses, in its words and order (XP-01..XP-03); hostile position text never reaches `numlist`.
- `lstyle()` draws every line style name; `lalign()` is accepted; `extend`/`noextend`/`style()` stay named for S50.
- Lines are under the data, added in bulk, outside the hull.
- `reflines` is a limit in both tables, enforced r(134) by dash.ado and past the ceiling by the renderer.
- New functions and programs are mapped; the three renderer helpers travel to the served app.
- One green commit `(WP-30 P1.21a)` on `wp30-s39` closes the entry, deletes its key and replaces both markers.

## Notes

- **Q-39.1, resolved by the review (no maintainer question).** The `reflines` count takes every observation's by() groups, not the graph's own if/in (TR-39.4). This upper bound is kept for four reasons. Ratification row 6 / A68 reads "counts positions x panels over the dashboard and refuses r(134)". dash.ado's existing build-time caps already bound by the limit rather than the drawn groups (`_dash_prepare_spec`'s computed-cell cap uses `by_groups` as "the LIMIT, not any graph's actual", dash.ado:7520). Evaluating each graph's qualifier before export is what `_dash_prepare_spec` deliberately avoids. Rule 1 prefers the conservative bound for a denial-of-service limit. The refusal says "up to" so it is never false, the help says the panels are counted over every observation, and `$dash_max_reflines` is the remedy. The renderer enforces only the 100,000 ceiling, for specs that bypass dash.ado. Every dash path (`dash build`, `dash serve`, the one-line form) passes `_dash_render_immediate` or `_dash_prepare_spec` first, and S39 may not change the two call sites of `_dash_reference_lines` in batch 14 (R12: S40 owns `_make_figure_body`, S41 `_generate_app_source`). The BUGS residual keeps the upper-bound sentence.
- **Two measured rules that differ from S10's resolver.** A repeated word sub-option is accepted by S10's unstarred stage; twoway refuses `ex ex` but accepts `noextend noextend` (E5). S39 adds the `extend` rule in its own column only.
- **python_exec hazard.** Check `~/.stata19/console/stata19.rc` after each slot run; a SKIP is not a pass.
- **Merge rules for the shared files.**
  - R1: XP-01..XP-08 as one run at the end of `test_suboption_reporting.cscript` (no other batch-14 section appends there); the S39 block in its place.
  - R2: three names after `"_dash_refline_draw",`; `_DASH_REFLINE_SUBOPTS` and `_DASH_LIMITS` in place; S50 later adds after S39's names.
  - R3: Axis and Display Options (the xline entries and a new paragraph), Resource limits.
  - R4/R5: the two `P1.21a` markers, the entry and its key.
  - R6: new programs with `version 19`; separate paragraphs in `_dash_render_immediate` and `_dash_prepare_spec`; `_needed` and the Mata header index also gain S40's names (context conflict, keep both).
  - R8: one CORPUS case; one corpus case flipped (its own); `ALLOWED`/`_MUST_WARN` untouched.
  - R9: E6's flips. R10: no pending-list or declared-count pin moves.
  - R12: S39 edits none of the one-editor symbols.
- **Landing (merger).** `gitnexus detect-changes --scope all --repo dash` must name `_dash_reference_lines`, `_dash_refline_instances`, `_dash_refline_draw`, `_dash_route_line_copies`, `_glyph_layer_lines`, the three new helpers, the constants, and test symbols.
- **Commit message.** Subject as in "Commit boundary". Body, in order: `$S/39-P1.21a-failure.txt`; the measured defect (Overview's table and the critic's findings); what changed and where (TR-39.1-TR-39.9, both modes); the threat closed (G9: unbounded Spans and position text on Stata's command line); then `Regression: test/test_reference_lines.py::TestPositions::test_probe -- failed at <base sha> with <text>` and the other regression nodes (cscripts as `test/test_suboption_reporting.cscript XP-01`, `test/test_wp30_truth.cscript XP-20`); the `Flipped:` lines of `$S/39-flips.txt`; `Fixture: test/fixtures/refline_truth.json (scripts/extract_refline_truth.do)`; `BUGS.md: "<WP30_OPEN["P1.21a"] title>" (closed)`. No tool or vendor name (G7).
- **BUGS.md Resolution** (one line, in place):

  ```
  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.21a). xline(), yline(), xline2() and yline2() positions are expanded by Stata's own numlist in dash.ado (_dash_line_expand, after _dash_line_check), unique within a copy and at most 2,500 per copy, and by _dash_refline_positions over _dash_expand_numlist for a spec written by hand; every copy keeps its own style (_dash_refline_copies, shared by _dash_route_line_copies). twoway's refusals are dash's, in its order and words (Mata _dash_axreq_add/_dash_axreq_check: something required r(100), unknown, short, capitalised or repeated sub-options r(198), invalid line argument r(198)). lstyle() resolves every line style through style_bundle with lcolor()/lwidth()/lpattern() over it, lalign() is accepted, lines are drawn above the grid and below the data in one assignment, in the saved page and the served app, before and after filter moves. A new reflines limit (default 10,000, $dash_max_reflines, at most 100,000) refuses r(134) positions times by() panels over the dashboard. Pinned by test/test_reference_lines.py::TestPositions::test_probe, test/test_reference_lines.py::TestLstyle::test_probe, test/test_reference_lines.py::TestDrawing::test_level_and_bulk, test/test_reference_lines.py::TestTheLimit::test_the_renderer_ceiling, test/test_reference_lines.py::TestAfterAFilterMove::test_lines_survive, test/test_suboption_reporting.cscript XP-01, test/test_wp30_truth.cscript XP-20; fixture test/fixtures/refline_truth.json. Residual, deferred (WP-30): extend, noextend and style() are section 50's; a line outside the axis range is clipped at the frame where twoway draws it outside (P2.54); the reflines count takes every observation's by() groups, not the graph's own if/in.
  ```
- **CHANGELOG lines** (each replaces its marker in place):

  ```
  ### Results that change
  - xline() and yline() draw what twoway draws, in both modes: `xline(2000(500)3000)` drew nothing and named the positions, and draws lines at 2000, 2500 and 3000; `xline(2000 2500 to 3500)` dropped 3000 and draws it; `xline(3000 3000)` drew two lines and draws one; `yline(20, lcolor(red)) yline(10(5)40, lcolor(blue))` drew one blue line and draws a red line at 20 and seven blue ones; `lstyle(foreground)` was named and is drawn in the foreground style; reference lines were drawn over the markers and are drawn behind them. (WP-30, P1.21a)

  ### Changed behaviour (may need your do-files changed)
  - xline() and yline() refuse what twoway refuses, in its words (rc 0 before): `xline(abc)`, `xline(1(0)5)`, `xline(nan)` and more than 2,500 positions in one copy (`invalid line argument, …`, r(198)); `xline(, lcolor(red))` (`something required`, r(100)); an unknown, short, capitalised or repeated sub-option (`option foo not allowed`, `option LColor() not allowed`, r(198)). A dashboard whose reference-line positions times by() panels pass 10,000 is refused r(134); set global dash_max_reflines to draw more (at most 100,000). (WP-30, P1.21a)
  ```
- **Notes for the closeout (S58; A145).**
  - **GAPS2.md B22** (:595-604): `- **Tracked:** Partly closed in WP-30, BUGS.md "<P1.21a title>", commit <sha>: B22-a and the lstyle part of B22-d; B22-e and style() are section 50's (B22-b closed by S10, B22-c by WP-29 P0.5).`
  - **TWOWAY_COVERAGE_AUDIT.md:139** (AUDIT-64, "Unsupported reference-line suboptions warn"): only `extend`, `noextend`, `style()` still warn.
  - **dash.ado:2527-2530**: the comment "bare numlist has NO element cap" is wrong on 19.5 (research §2: `numlist "0(0.000001)1000000"` is r(123)); correct it in the closeout or with its owner.
  - **dash.sthlp:612-620** (Differences, owned by S06/S11/S12/S20/S18): the sentence listing `xline()`/`yline()` among options whose unimplemented sub-options are named is still true for the extent sub-options; no edit needed unless S50 draws them all.
  - **DROPIN-REMAINING.md:132**: "Positions, refusals and lstyle closed by <sha> (WP-30 S39); extent S50."
  - **AGENTS.md invariant:** "reference-line positions are expanded once, by Stata's numlist, in `_dash_line_expand`; the renderer's `_dash_refline_positions` is the fallback; Spans are added in one assignment at level underlay."
  - **Unverified:** the line grammar on Stata 14-18.5 (not run, M2).
