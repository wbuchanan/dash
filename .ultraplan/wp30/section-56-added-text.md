# Section 56: text() and ttext() annotations (P1.10)

> Part of: WP-30 · Items: P1.10 (entry `P1.10`; REM-§2-S09-text, REM-S09-73-text, GAPS2-B20-a, AUDIT-13, REM-§2-S09-ttext, GAPS2-B20-b) · Risk: yellow · Batch: 19 (merge order S54, S55, S56; lands last, regenerates) · Depends on: 02, 08, 10, 15, 29, 30, 35, 43, 48, 51 · Blocks: none · Tasks: 19, 2 commits (text(), then ttext()) · Case prefix: AT

## Review amendments

- Fixed (major, security and executability): TR-56.3 and TR-56.4 had `_dash_added_text` read `st_local("g_text")` and `_dash_at_opts` read `local opts`. Both are subprograms, which cannot see `_dash_plot`'s locals. Both now take their text the way dash.ado already does, through `_dash_text_args` (dash_parse.mata:406-430; the caller passes `` `"`macval(…)'"' ``), and hand options to `syntax` through `mata: st_local("0", …)`. They return by `c_local` only digits, option names and `_json_escape` output. The unknown-placement note is printed inside `_dash_at_opts`, so a raw name never crosses a program boundary. `_dash_at_json` no longer escapes `opts` twice.
- Fixed (major): by() text would have been scaled twice. S48's `_dash_by_scale_panel` (TR-48.12) already multiplies every `Label`'s font size once per panel in `_dash_layout_cell`, in both modes. The `scale` argument and "S48's panel text scale" are removed, and `TestByPanels` now pins exactly one multiplication.
- Fixed (major): TR-56.17 left S51's converter "to be read at the base". It now calls S51's `_dash_tdate_value(x, _dash_taxis_unit(fmt, 1), val)`, and refuses a missing `val` as twoway does (`. is not a number`), which S51 rates a number.
- Fixed (minor): `added_text_n` is a key read by `_dash_json_first_num`. It is written before `added_text`, and the substring test now carries a hostile `"added_text_n":` line. The limit row goes last, because S39 also anchors "after `filters`". `TestTheLimit::test_parsing_is_linear` was a pytest name for a Mata timing and is now cscript AT-04b.
- Fixed (minor): truth helpers in the reviewed `python:` form; the second block's start, end and header are spelled out; 56-03, 56-15 and 56-16 check for SKIP, both start lines and `ALL CHECKS PASSED`; 56-07's "except" is now a `-k` deselection; partner lists updated (S55 edits only `_dash_build_hover`; S54 also appends to `_DASH_BOKEH_INTERNALS`).
- Resolved: the open question on ratification item 26 (IR-7). TR-56.12 and TR-56.16 already handle both outcomes. The dash.sthlp:598-599 example is recorded as an R3 exception (Notes; g09.md).
- Checked at `c96facd`: dash.ado :726, :807, :859, :971, :1110, :1278, :5214-5217, :5514, :5602-5617, :2770-2782, :8035-8045; dash_parse.mata :4680, :5724; dash_render.py `_DASH_TEXTBOX_DEFAULTS` 25962, `_dash_text_annotations` 25969 and its calls :30400 and :35261, `_reported_subopts` :34920, `_FALLBACK_PROPS` 5728, `_init_properties` 6806; dash.sthlp :598-599, :443, :3736. Batch 19: S56 is the only `_make_figure_body`/`_generate_app_source` editor and the regenerator, and lands last.
- Rejected: drawing `tstyle()` now. Register P1.10.2 notes it, and S37's `textbox_style` is a later item.
- The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:100 (P1.10): "`text()` and `ttext()` annotations are not drawn." Measured at `c96facd` (research `.ultraplan/wp30/research/p1-10.md` §1, critic re-run):

```
. dash scatter mpg weight, text(30 3000 "AAA") saving(d1_1.html, replace)
dash: ignoring unsupported option(s): text()                        rc=0
. dash scatter mpg weight, ttext(30 3000 "TTT") saving(d1_2.html, replace)
dash: ignoring unsupported option(s): ttext()                       rc=0
. dash scatter mpg weight, text(30 3000 "AAA", color(red)) text(20 4000 "BBB") name(g3)
g3: "text":"30 3000 \"AAA\", color(red) 20 4000 \"BBB\""            (the copies merged; BBB would be read as AAA's option)
. dash scatter mpg weight, text(30 "BAD") name(g5)                  rc=0   (twoway: invalid point, BAD 30  r(198))
renderer, both modes, {'text': '30 3000 "AAA"'}: [('Title','')] only -- no Label
```

twoway draws each copy where its point lies in data units, with its own sub-options (AAA red at 157.44, BBB black at 112.56), in every by() panel, on axis 2 when asked, outside the plot region when the point is (axes never widened), and with `ttext()` reads `2001m1` on a `%tm` axis. It refuses a malformed point, a missing axis pair and an unknown sub-option with r(198) (research §2b-§2c).

**After this section**, in the saved page and the served app, before and after every filter move:
- every copy of `text()` and `ttext()`, at graph or plot level, is drawn as one Bokeh `Label` per point at its data position (Stata units on numeric and date axes, S35), with its placement, justification, orientation, size (S08's units), colour (S30/S43), box, fill, outline, margin and axis pair, the scheme's `text_option` defaults otherwise; in every by() panel at S48's `iscale`; never in an axis hull; its text raw until S09/S29's document pass;
- repeated copies keep their own sub-options (the category-A merge fix in `_dash_rep_merge`);
- dash refuses what twoway refuses, in its words and code (M5): `invalid point, BAD 30`, `text() option invalid, specified axis pair (2 1) not in graph`, `option nosuch() not allowed`, and for `ttext()` the date refusals (`2001m13 is not a number`); sub-options Bokeh cannot draw are named once, in Stata, for both modes (A30);
- the count of texts × panels over a dashboard is bounded by a new `added_text` limit (default 1,000, ceiling 100,000, `$dash_max_added_text`, r(134); A28).

**Why one section, two commits (A156).** One item, one entry. Commit 1 (text()) carries the parse, the merge fix, the refusals, the renderer in both modes, the scheme defaults (S56 is batch 19's regenerator, A152), the limit and the help; it leaves the entry, its key and both markers. Commit 2 (ttext()) declares `ttext()`, converts date literals through S51's converter under the first-plot or `xlabel()` format rule, adds twoway's date refusals and closes the entry.

**Test order and commit rule (rule 7, A156).**
- **Commit 1:** 56-01 to 56-03 write the fixture and every commit-1 regression and run them against the unmodified `batch-19-base`, saving `$S/56-P1.10-1-failure.txt` (no commit); 56-04 to 56-12 fix, regenerate, flip and document; 56-13 runs the full suite and makes commit 1.
- **Commit 2:** 56-14 and 56-15 write the ttext regressions against the tree commit 1 leaves and save `$S/56-P1.10-2-failure.txt`; 56-16 to 56-18 fix, flip, document and verify; 56-19 closes the entry, deletes its key, replaces both markers and makes commit 2.

No test-only commit exists, and no commit is red.

## Risk: [yellow] — two CRITICAL/HIGH build symbols, a Stata parser of user text that must not re-expand it, a merge rule shared by every repeated option, and a scheme regeneration

**Why.**
- `DashRenderer._make_figure_body` is CRITICAL (4 impacted) and `ServerAppBuilder._generate_app_source` HIGH (5); `_glyph_layer_lines` HIGH (4) (research §4, critic confirmed). One call is added to each build path and two generated lines to the template.
- `_textbox_size`, `_textbox_color`, `_parse_textbox_opt`, `_dash_axis_positions`, `_dash_axis_date_kind` are CRITICAL and read only.
- `_dash_rep_merge`/`_dash_rep_cat` (Mata, UNKNOWN) decide every repeated option; only category A changes.
- `_dash_parse_graph_opts`, `_dash_parse_plot_opts`, `_dash_plot`, `_dash_process_segment`, `_dash_prepare_spec`, `_dash_limit_table` (Stata, UNKNOWN; grep: 16 and 19 references for the parsers).
- `scripts/extract_scheme_truth.py` and the 26 `dash-*.scheme` files are regenerated (A152).

**Risk factors.**
1. Putting stored text back on a command line expands `$name` and `` `=exp' `` a second time (critic C3; dash.ado:101-114 records `` `=filewrite()' `` running so; JSE-69 pins `text(30 3000 "t\$J6_G")` stored as typed).
2. A separator that a user's text can contain would split one copy into two.
3. Keys of the structured copies could be found by dash_parse.mata's substring readers (`_dash_json_has_value(gjson, "width")`, `_dash_json_first_num(gjson, "bin")`, :5913-5992; critic C8).
4. by() multiplies Labels: 1,000 texts × 1,000 panels would be a million models (critic C6).
5. Notes raised in the served renderer never reach Stata on their own (critic C1).
6. A Label text holding `$$…$$` would load MathJax (critic C2).
7. The served copy loop skips a misspelt name silently (RK-9).

**Mitigation.**
1. Each helper receives the copies through `_dash_text_args` (the caller passes `` `"`macval(…)'"' ``) and reads them by value in Mata (`st_local`). Point tokens are checked in Mata against a strict literal before any Stata command sees them, and `ttext()` date tokens go only to S51's gated converter. The sub-options reach `syntax` only through `mata: st_local("0", ", " + …)`. Values return by `c_local` only as digits, option names or `_json_escape` output, and every echo goes through `_dash_say`/`_dash_note`; AT-13..AT-16 put `$`, backquotes and `` `=exit 1' `` in the point, string and sub-option positions.
2. Copies are joined with `char(30)` and split only at top level (outside simple and compound quotes) by Mata's tokenizer; a `char(30)` inside a quoted string is text and C0 controls are dropped from graph text anyway (A34).
3. Every key carries the prefix `at_`, sub-options stay in one `at_opts` string, numbers are JSON numbers; `TestTheSpec::test_no_key_is_read_by_the_substring_readers` pins it.
4. The `added_text` row counts texts × panels per graph at registration and over the dashboard at build, in Stata, with the renderer's own budget for a hand-written spec.
5. Every added-text note is raised in Stata once, for both modes (register P1.10.5, A30).
6. Labels are built raw and finished by S09/S29's document pass, whose sink table holds `Label` (S09 TR "Label", S29 `_DASH_GT_STYLE_PROPS`); `TestTheText::test_tex_is_inert` pins it.
7. G4 guards run in the task where the names land.

## Dependencies

- **Depends on** (all landed before batch 19):
  - S02: extractor stanza (`DASH_REPO`, path-free), `scripts/stata_slot.sh`; `scripts/regen_option_surface.py` retired if ratification item 26 stands (IR-7).
  - S08: `resolve_size(value, kind, default)` behind `_textbox_size` (numbers and keywords in Stata units, `#pt`, `*#`).
  - S10: `_dash_subopt_canon` and `_TEXTBOX_SUBOPTS`' abbreviations (read; Stata canonicalises here).
  - S15: scheme chrome and `_dash_textbox_place` (read; added text is placed by data position, not by clock).
  - S29: `_dash_graph_text` inside S09's `_dash_finish_graph_text` pass (both modes, after the figures are built); sinks take raw text once.
  - S30, S43: `_textbox_color` (colour grammar; bare `*#` and `%#` from the scheme's base colour).
  - S35: per-axis date kinds (`_dash_axis_date_kind`, `_dash_axis_positions`), y2/x2 date axes.
  - S48: by() `iscale` in Stata units over S08. S48's `_dash_by_scale_panel(fig, m)` (TR-48.12) runs once per panel from `_dash_layout_cell` in both modes. It multiplies every `Label`'s `text_font_size`, `x_offset`, `y_offset` and `border_line_width` by the panel multiplier, guarded by `fig._dash_by_scaled`. So an added-text Label drawn at its unpaneled size is scaled there, and S56 must not scale it again.
  - S51: the gated date-literal converter and the base-format rule for t* options (manifest: "S56 reuses the literal converter for ttext()").
  - S01: entry `P1.10`, its `WP30_OPEN` key, markers `<!-- WP-30 P1.10 -->` at the end of `### New` and of `### Changed behaviour (may need your do-files changed)`, the S56 stub (`* ==== S56 P1.10: text() and ttext() annotations ====`) and the map anchors `# WP-30 S56 (P1.10): text() and ttext() annotations (P1.10)`.
  - Read, not depended on: S06 (`_dash_note`), S21 (hull reads GlyphRenderers only), S23 (served notes relay), S37 (`SchemeParser.textbox_style`, and `gsize/color text_option` if its Q-37.1 regeneration ran), S39 (the `reflines` limit row, the form this section copies), S45, S49.
- **Blocks:** none.
- **Parallel batch: 19**, merge order S54, S55, S56; S56 lands last (A152: regenerator; R12: batch 19's `_make_figure_body` and `_generate_app_source` editor).
- **Can run with:** S54 (`_dash_name_save`, the toolbar help, `test_toolbar.py`, `test_csp_browser.py`, three triples in `_DASH_BOKEH_INTERNALS`) and S55 (`_dash_build_hover` only). Neither edits a symbol S56 edits; all three append to `test_mode_parity.py` (R8), S54 and S56 to `_glyph_layer_lines`' tuples at distinct anchors (R2).

## Evidence

Anchors at `c96facd` (dash.ado 8,487 lines, dash_parse.mata 6,093, dash_render.py 37,689, dash.sthlp 3,822); every earlier section moves them, so the executor re-finds each by symbol at `batch-19-base`.

### E1. Declared, pending, merged (dash.ado, dash_parse.mata)

```stata
 726        FYSIZE(string)            SCALE(string)             TEXT(string asis) ///   (_dash_parse_graph_opts, 682)
 807    if `: length local text' local _dash_pending `"`_dash_pending' text"'
 859    sreturn local text         : copy local text
 971        TEXT(string asis)         XTICk(string asis)        YTICk(string asis) ///  (_dash_parse_plot_opts, 897)
1110    if `: length local text' local _dash_pending `"`_dash_pending' text"'
1278    sreturn local g_text         : copy local text
```

`text` travels from plot groups to the graph through six lists naming `scale text hover` (:4279 in `_dash_process_segment`; :5071, :5105, :5205, :5277, :5309 in `_dash_plot`) and is written by the graph JSON loop (:5602-5617, `foreach gk in … scale text hover …`, `_dash_json_str` per value). `ttext` is declared nowhere (it reaches the `*` catch-all). The merge (dash_parse.mata):

```mata
4680    if (k == "text") return("A")                                  (_dash_rep_cat, 4664)
5724    if (cat == "A") return(v1 + " " + v2)                         (_dash_rep_merge, 5715)
```

### E2. twoway's parser (StataNow 19.5, read as text)

`twowaygraph_g.class:686-800`: `ParseAndLogText` loops `syntax [, TEXT(string asis) TTEXT(string asis) *]`, each copy to `_parse_log_1textbox` (`datesok` for ttext):

```stata
708  syntax [ anything(name=triplets) ] [ , AXes(string) YAXis(integer 1) XAXis(integer 1) TSTYle(string) * ]
...  di as error "text() option invalid, specified axis pair (`yaxis' `xaxis') not in graph"   exit 198
...  capture numlist "`x' `y'" , max(2) min(2)       // ttext: numlist "`y'" then _confirm_number_or_date `x'
...  di as error `"invalid point, `x' `y'"'           exit 198
...  gettoken txtq triplets : triplets , quotes       // quoted tokens are lines; the next bare token is the next y
...  _fr_sztextbox_parse_and_log … , `fullopts'       // then syntax [, FAKE_OPT_FOR_BETTER_MSG]: "option nosuch() not allowed"
```

The sub-option chain (each level passes `*` on): `_fr_sztextbox_parse_and_log` `WIDTH() HEIGHT() NOASTextbox NOBEXpand ASTextbox BEXpand`; `_fr_textbox_parse_and_log` `ORIENTation() DRAWVIEW() XOFFSET(real) YOFFSET(real) ASCIRCLE`; `_fr_tbstyle_parse_and_log` `TSTYle() ANGLE() Size() Color() Justification() Alignment() Margin() LINEGAP() NOBox Box BMargin() PLACEment() BFColor() FColor() BColor() BLSTyle() BLWidth() BLColor() BLPattern() BLAlign() LSTyle() LWidth() LColor() LPattern() LAlign() ORIENTation()`. Each level resolves abbreviations by prefix and minimum, so one `syntax` statement holding all of them, with no `*`, accepts and refuses exactly what the chain does (`c(red)`, `si(large)`, `orient(vert)` accepted; `ori(v)` refused as measured). twoway checks the sub-options only for a copy with a point; the axis pair is checked even for a copy without one.

### E3. twoway's truth (research §2a-§2c; critic C10)

| Case (`scatter mpg weight, …`) | twoway |
|---|---|
| `text(30 3000 "AAA")` | at the (3000, 30) data point, centred, fs 112.56 (= tick-label size, stcolor), black |
| `text(…, color(red) size(large)) text(20 4000 "BBB")` | AAA red 157.44; BBB black 112.56 |
| `text(30 3000 "L1" "L2")` | two lines stacked about the point |
| `text(100 3000 "FAR")`, `text(43 3000 "ABOVE")` | drawn outside the plot region; axes not widened |
| `orientation(vertical)` / `rvertical` / `rhorizontal` | rotate(-90) / (-270) / (-180) |
| `box fcolor(yellow) lcolor(blue) margin(medium)` | box filled #FFFF00, stroke #0000FF |
| plot-group, `||` segment and graph-level copies | all drawn, each with its own options |
| `by(foreign)` | in every panel, fs 95.68 |
| `yaxis(2)` | at axis 2's position |
| `place(n…c)`, `place(12)`, `place(3)`, `place(top)`, `place(neast)`, `place(0)`, `place(r)` | edge or corner on the point; synonyms of n, e, n, ne, c, e |
| `place(zz)` | `(note: named style zz not found in class compass2dir, default attributes used)`, drawn east, rc 0 |
| `just(left)` | lines left-aligned; box still centred |
| `xscale(log)`, `xscale(reverse)` | at the transformed position |
| `size(*2)`, `size(20pt)`, `size(5)`, `size(huge)` | fs 224.94, 199.97, 162.00 (5% of 3240), 224.94 |
| `text(30 3000 "")`, `text(30 3000)`, `text()`, `text(30 3000 "x" 20 4000)` | rc 0; nothing drawn for an empty or absent string; a trailing point with no text is dropped |
| `"<b>x</b>&amp;"` | drawn literally |
| schemes | s2color, s1mono fs 99.99; stcolor 112.56; all inherit `gsize text_option medsmall`, `color text_option black` (s1rcolor white), `compass2dir text_option center`, `yesno text_option no`, `linewidth text_option thin`, `margin text_option zero`, `horizontal text_option center`, `vertical_text text_option middle`, `color text_option_line black`, `color text_option_fill bluishgray` (s2color8 `bluishgray8`; s1rcolor line white, fill gs6) (scheme-s2color.scheme:149-2099) |

Refusals (§2b-§2c): `text(30 "AAA")` → `invalid point, AAA 30`; `text(. 3000 "MISS")` → `invalid point, 3000 .`; `text(a 3000 "x")` → `invalid point, 3000 a`; `text(1+1 3000 "x")` → `invalid point, 3000 1+1`; `text(30 1e400 "x")` → `invalid point, 1e400 30` (`3e3` accepted); `text(30 3000 x)` → `invalid point,  x`; `text(30 3000 "x" 20)` → `invalid point,  20`; `text(30 3000 "x", nosuch(1))` → `option nosuch() not allowed`; `yaxis(2)` with no axis 2 → `text() option invalid, specified axis pair (2 1) not in graph` (`xaxis(2)` → `(1 2)`); `tex(…)` → `option tex() not allowed`; all r(198). ttext: `tsline y, ttext(12 2001m1 "TT1")` drawn at 2001m1 (492); `ttext(12 "2001m1" …)` drawn; `ttext(12 2001q1 …)` on %tm drawn at 492; `text(12 2001m1 …)` → `invalid point, 2001m1 12`; `ttext(12 tm(2001m1) …)` → `invalid point, tm(2001m1) 12`; `ttext(12 2001m13 …)` → `2001m13 is not a number`; `scatter mpg weight, ttext(30 2001m1 …)` → `2001m1 is not a number`; `ttext(30 . …)` → `. is not a number`; %td `ttext(10 01jun2001 …)` drawn at 15127, `ttext(10 2001m6 …)` → `2001m6 is not a number`; `(line y tn) (line y t), ttext(12 2001m1 …)` refused, the reverse drawn (the first plot's x format decides), `line y tn, xlabel(, format(%tm)) ttext(…)` drawn, `line y t, xlabel(, format(%9.0g)) ttext(…)` drawn; `line t y, ttext(2001m1 12 …)` → `invalid point, 12 2001m1`; one bad copy refuses the graph.

### E4. The renderer today (dash_render.py)

- `_dash_text_annotations` (25969-26016) draws note/caption/subtitle as screen-unit `Label`s from `_dash_textbox`; it is called at :30400 (saved, `_make_figure_body`) and generated at :35261 (`_dash_text_annotations(fig, go, _reported_subopts, gname, _DASH_SCHEME)`); `_reported_subopts = set()` is generated at :34920. No reader of `text`/`ttext`/`added_text` exists.
- `_textbox_size` (4819), `_textbox_color` (4839) take the dict `_parse_textbox_opt` (4857) returns. `_dash_axis_positions(values, kind)` (847) converts Stata units to the axis's unit.
- `_DASH_LIMITS` (1064-1073) and `_dash_limit_table` (dash.ado:2770-2782) hold eight rows; `test_resource_limits.py` asserts the two agree; `_dash_cap_spec` (3251) is the renderer's own bound.
- `_dash_by_panels` (dash.ado:3340) returns `r(kept)`, the number of by() panels `_dash_plot` draws (called at :5514).
- User text reaches a dash.ado helper by value through `_dash_text_args(nlead, ntail, optnum)` (dash_parse.mata:406-430). The caller passes the text last, as `` `"`macval(x)'"' ``. The helper's first statement is `mata: _dash_text_args(…)`, which sets `_dash_txt`, the text with one pair of enclosing quotes removed, and `_dash_a1`, `_dash_a2`, … (dash.ado :1930, :2133, :3466, :4956). `args` parses the text as Stata and cuts it at a `"'`. A subprogram cannot read its caller's locals, so `st_local("g_text")` inside a helper reads nothing. `_json_escape` output holds no backtick, `$`, quote or apostrophe (dash.ado:643-669), so it is the only form in which user text is returned by `c_local`.
- Bokeh 3.8.0 (Stata's Python) and 3.9.0 `Label` have `anchor`, `angle`, `padding`, `border_radius`, `background_fill_color/alpha`, `border_line_color/width`, `text_align`, `text_line_height`, `x_range_name`, `y_range_name` (checked this pass with both).

### E5. Tests that pin today's behaviour (flipped in place, never deleted; re-measured by 56-09, 56-12 and 56-17)

- `test/test_unsupported_report_is_true.py` :148 `"text": ('20 3000 "hi"', '25 2500 "yo"', "scatter")` (its dict's pending rows), the counts at :240 (plot pending 48 at `c96facd`), :241 (graph pending 23), :607 (declared plot 169), :608 (declared graph 72), as earlier movers left them (R10).
- `test/test_help_conformance.py` `test_the_ignored_list_was_found`, `test_the_unsupported_section_was_found`; `test/test_help_claims_8.py`'s Unsupported equality pin and `TestTheUnsupportedSectionSaysWhatTwowayDoes`; `test/test_help_claims_8.cscript` HC8-02 (`p_opts`/`g_opts`, `p_names`, :387-428).
- `test/test_json_escaping.cscript` JSE-46 (`jg46g`, `jg46h`: `_jg_stored … "graph_options text"` :1917, :1923; note needles :1877-1880, asserted :1961) and JSE-69 (`jg69b`, :3806, :3859).
- `test/test_help_examples.py:119` (the help example `dash scatter mpg weight, play(x) text(20 3000 "hi")` with one output line) and dash.sthlp:598-599.
- `test/fixtures/twoway_corpus.do:214-215` (`text`, `text_suboptions` probes) and `test/fixtures/rejected_options.json` (text :1980-2000, :3222, :3232; ttext :2092-2107, :5428-5435): S58's (A145), unless a test fails.
- Not flips: TP-14 (the merge's other categories, program_coverage_map.py:532-539) stays green.

### E6. Blast radius (`gitnexus impact <symbol> -d upstream -r dash`, research §4)

| Symbol | Risk | Action |
|---|---|---|
| `DashRenderer._make_figure_body` | CRITICAL (4) | warn; one call after `_dash_text_annotations` |
| `ServerAppBuilder._generate_app_source` | HIGH (5) | warn; two generated lines |
| `ServerAppBuilder._glyph_layer_lines` | HIGH (4) | warn; names at S56's two anchors |
| `SchemeParser._init_properties` | LOW (1) | ten properties added |
| `_textbox_size`, `_textbox_color`, `_parse_textbox_opt`, `_dash_axis_positions`, `_dash_axis_date_kind` | CRITICAL | read only |
| dash.ado programs, Mata functions | UNKNOWN | grep callers (Risk) |

## User stories

- **US-56.1** As a twoway user, I want `text(y x "label")` drawn where twoway draws it, with its placement, size, colour, box and orientation, in the saved page and the served app and after a filter move, so annotated figures survive the move to dash.
- **US-56.2** As a twoway user, I want repeated `text()` copies, from plot groups and the graph, each drawn with its own sub-options, and in every by() panel, on axis 2 and on date axes, as in Stata.
- **US-56.3** As a time-series user, I want `ttext(y 2001m1 "event")` placed at that date, so I can mark events in the axis's own units.
- **US-56.4** As a twoway user, I want a malformed `text()` refused with twoway's words, so a typo fails the same way in both.
- **US-56.5** As a maintainer, I want added text bounded and never run as code, so a dashboard cannot be made to build a million Labels or expand a macro twice.

## Business requirements

- **BR-56.1** Each `text()` point with at least one line is drawn at its (x, y) in data units of its axis pair, with its lines stacked, at graph or plot level, from every copy, each copy with its own sub-options; empty strings and trailing points without text draw nothing; the axes are never widened by a text and a text outside the plot region is still drawn.
- **BR-56.2** placement (n, ne, e, se, s, sw, w, nw, c and twoway's synonyms; an unknown name noted as twoway notes it and drawn east), justification, orientation (horizontal, vertical, rvertical, rhorizontal), size (Stata units, `#pt`, `*#`, keywords), colour (S30's grammar, S43's bare forms), `box`/`nobox`, `fcolor()`/`bfcolor()`, `lcolor()`/`blcolor()`, `bcolor()`, `lwidth()`/`blwidth()` and `margin()` are drawn; the scheme's `text_option` defaults apply otherwise. Every other textbox sub-option twoway accepts is named once in Stata's note and listed in the help.
- **BR-56.3** On a date axis a coordinate is read in Stata units; `yaxis(2)`/`xaxis(2)`/`axes()` place the text on that axis; under `by()` each text is in every panel at the panel text scale (`iscale`); log and reversed axes place it at the transformed position.
- **BR-56.4** Refused r(198) in twoway's words: a malformed point (`invalid point, <x> <y>`), an axis pair the graph lacks, a sub-option twoway does not take, and, for `ttext()`, a date literal that is no date of the axis's format (`<x> is not a number`). One bad copy refuses the command.
- **BR-56.5** `ttext()` takes a number or a date literal (quoted or not) as x, converted with the x axis's time format: a `%t`/`%d` `format()` on the x axis's label or tick options, else the first plot's x variable's format; y is a number.
- **BR-56.6** More than `$dash_max_added_text` (default 1,000, at most 100,000) texts × panels in one graph or one dashboard is refused r(134) with the global named.
- **BR-56.7** Neither option is named in "ignoring unsupported option(s)" any more; the user's text is drawn as typed (SMCL per BR-30.11, TeX inert) and never run.

## Technical requirements

### Commit 1: text()

- **TR-56.1 The merge (dash_parse.mata).** `_dash_rep_merge` (5715): category A returns `v1 + char(30) + v2` (comment: "each copy kept apart by a record separator; `_dash_at_copies` splits only outside quotes"). `_dash_rep_cat` unchanged in commit 1 (`text` is A). The merged value passes `syntax … TEXT(string asis)` again (critic C4); a test runs `_dash_opts_repeats` → `_dash_rep_reduce` on `text(1 1 "a", color(red)) text(2 2 "b")` and reads back two copies.
- **TR-56.2 New Mata functions** (dash_parse.mata, in the part holding `_dash_rep_*`, each with a header comment and a header-index entry, `_needed` entries, X.5):
  - `string colvector _dash_at_copies(string scalar raw)`: split on `char(30)` only outside quotes, with Mata's `tokeninit()` taking `char(30)` as its one parse character and Stata's simple and compound double quotes as its quote pairs; empty pieces dropped.
  - `real scalar _dash_at_isnum(string scalar tok)`: 1 when `tok` matches `^[+-]?([0-9]+[.]?[0-9]*|[.][0-9]+)([eE][+-]?[0-9]+)?$` and `strtoreal(tok)` is not missing (so `.`, `1+1`, `a`, `1e400` fail, `3e3` passes).
  - `real scalar _dash_at_parse(string scalar raw, real scalar datesok)`: for each copy, `_dash_rep_split` (read only) gives body and options; the body is tokenised with quotes kept (`tokens()`); twoway's loop of E2: y, x, then quoted tokens are lines (outer quotes removed, compound or simple), the next bare token is the next y. A point is valid when `_dash_at_isnum(y) & _dash_at_isnum(x)`, or with `datesok` when `_dash_at_isnum(y)` and x is non-empty (x is then marked for conversion). Invalid: `st_local("_at_err", "invalid point, " + x + " " + y)` and return 198. Valid points with at least one non-empty line become records `_at_y<i>`, `_at_x<i>`, `_at_xd<i>` (needs conversion), `_at_l<i>` (the lines as one JSON array built with `_json_escape`), `_at_c<i>` (copy index); copies' options go to `_at_o<k>`, the count to `_at_n`, the copy count to `_at_k`. Returns 0. All reads and writes by value; nothing is executed.
  - `string scalar _dash_at_place(string scalar p)`: the compassdir synonym table transcribed from the fixture's `_meta.compass` (canonical n ne e se s sw w nw c, every synonym twoway took); `""` for an unknown name.
  - `string scalar _dash_at_json(string scalar kind, real scalar y, real scalar x, real scalar ya, real scalar xa, string scalar lines, string scalar opts)`: one record of TR-56.4, numbers with `strofreal(v, "%21.0g")`, `lines` already a JSON array and `opts` already escaped by `_dash_at_opts` (written as they come, never escaped twice); nothing else is written into it.
- **TR-56.3 `_dash_at_opts`** (new dash.ado program, `version 19`, sclass-free). It is called as `` _dash_at_opts `"`macval(_at_o`k'')'"' ``. Its first statements are `mata: _dash_text_args(0, 0, 0)` and `mata: st_local("0", ", " + st_local("_dash_txt"))`, so the copy's options reach `syntax` by value and are never put back on a command line. Then `syntax [, AXes(string) YAXis(integer 1) XAXis(integer 1) TSTYle(string) WIDTH(string) HEIGHT(string) NOASTextbox NOBEXpand ASTextbox BEXpand ORIENTation(string) DRAWVIEW(string) XOFFSET(real -99999) YOFFSET(real -99999) ASCIRCLE ANGLE(string) Size(string) Color(string) Justification(string) Alignment(string) Margin(string) LINEGAP(string) NOBox Box BMargin(string) PLACEment(string) BFColor(string) FColor(string) BColor(string) BLSTyle(string) BLWidth(string) BLColor(string) BLPattern(string) BLAlign(string) LSTyle(string) LWidth(string) LColor(string) LPattern(string) LAlign(string)]` (E2's chain in one statement, no `*`). It returns by `c_local` only values that hold no raw user text. `_ao_y` and `_ao_x` are digits, taken from `axes()` when given (two words, `.` → 1, else `invalid axes(<axes>)` r(198) through `_dash_say`, which reads the value by value). `_ao_canon` is built in Mata from the option locals read with `st_local` and returned as `_json_escape(canon)`, which is safe inside compound quotes. It holds the drawn sub-options rewritten in full names: `size() color() justification() orientation() box|nobox fcolor() lcolor() lwidth() margin()`; `bfcolor()`→`fcolor()`, `blcolor()`→`lcolor()`, `blwidth()`→`lwidth()` when the plain one is absent; `bcolor()` sets both when neither is given; placement as TR-56.2's canonical name or `e`. An unknown placement is noted here, in twoway's words, through Mata `_dash_note` reading `st_local("placement")`, once per command, so the raw name never crosses a program boundary. `_ao_noted` holds option names only, the names given among `width height astextbox noastextbox bexpand nobexpand drawview xoffset yoffset ascircle tstyle angle alignment linegap bmargin lpattern lstyle lalign blpattern blstyle blalign`).
- **TR-56.4 `_dash_added_text`** (new dash.ado program, `version 19`, directly after `_dash_at_opts`). It is called once per kind from `_dash_plot`, as `` _dash_added_text text "`_g_ys'" "`_g_xs'" `"`macval(g_text)'"' `` (commit 2 adds the same call with `ttext` and `g_ttext`). Its first statement is `mata: _dash_text_args(3, 0, 0)`: `_dash_a1` is the kind, `_dash_a2` and `_dash_a3` are the axis lists (dash's own digits), and `_dash_txt` is the copies, by value. Then:
  1. `mata: st_local("_rc", strofreal(_dash_at_parse(st_local("_dash_txt"), <0 for text, 1 for ttext>)))`; on 198 → `mata: _dash_say("err", st_local("_at_err"), "", "")`, `exit 198`.
  2. Per copy k: `` _dash_at_opts `"`macval(_at_o`k'')'"' `` (its `syntax` refusal is twoway's words and r(198)); the pair (`_ao_y`, `_ao_x`) must be in `_dash_a2` × `_dash_a3` (the axes `_dash_plot` collected in `_g_ys`/`_g_xs`, :5214-5217), else `text() option invalid, specified axis pair (Y X) not in graph`, r(198), via `_dash_say` — checked even for a copy with no point (E2).
  3. Notes, once per command (A30), through Mata `_dash_note`: `_ao_noted` names as `dash: text() draws no <name>() <name>(); see help dash##added_text` (the unknown placement is noted by `_dash_at_opts`, step TR-56.3).
  4. Records → JSON through Mata `_dash_at_json(...)`: `{"at_kind":"text","at_y":<%21.0g>,"at_x":<%21.0g>,"at_yaxis":k,"at_xaxis":k,"at_lines":[…],"at_opts":"<escaped canon>"}`. They are returned by `c_local` as `_at_json`, the comma-joined records, which are JSON-escaped and safe inside compound quotes, and as `_at_total`, the record count.
  - `_dash_plot` calls it directly after the graph-options JSON loop (:5617). It writes `"added_text_n":<count>` (TR-56.5) and then `"added_text":[<the records of every kind>]` before the closing `}` of `gopts_json`, in that order, so that `_dash_json_first_num`'s first match is dash's own key. A user line holding `"added_text_n":` is escaped as `\"added_text_n\":` and cannot match. `text` is removed from that loop's key list (one source of truth) and kept in the six propagation lists.
- **TR-56.5 The limit (A28).** `_dash_limit_table`: `added_text=1000,100000` as the last row, after the rows S39 (`reflines`, also placed "after `filters`") and S46 appended; `_DASH_LIMITS["added_text"] = (1_000, 100_000, "dash_max_added_text")` last. In `_dash_plot`, after TR-56.4: panels = `r(kept)` of the `_dash_by_panels` call (:5514, saved to a local right after it) when by() was given, else 1, capped at the `by_groups` limit; count = `_at_total` × panels, written into the graph options as `"added_text_n":<count>`; over the limit → `dash: graph '<name>' draws <count> added texts (text() and ttext() points times by() panels), more than the <limit> dash draws.` / `      Set global dash_max_added_text to draw more (at most 100,000).`, `exit 134` (`_dash_count_fmt`, the form of :8040-8045). In `_dash_prepare_spec`, beside the function-points byte check (:8035-8045), the sum over registered graphs (`_dash_json_first_num(<graph json>, "added_text_n")`) is checked the same way with "this dashboard draws".
- **TR-56.6 Renderer constants** (after `_DASH_TEXTBOX_DEFAULTS`, 25962): `_DASH_ADDED_TEXT_PLACE` (canonical name → Bokeh anchor: n `bottom_center`, ne `bottom_left`, e `center_left`, se `top_left`, s `top_center`, sw `top_right`, w `center_right`, nw `bottom_right`, c `center`), `_DASH_ADDED_TEXT_ORIENT` (horizontal 0, vertical π/2, rvertical −π/2, rhorizontal π, with twoway's abbreviations as the fixture records them), `_DASH_ADDED_TEXT_HONOURED` (the drawn names of TR-56.3).
- **TR-56.7 `_dash_added_text_opts(opts)`** (new module function): `_parse_textbox_opt('"", ' + opts)` (read only) gives the dict; returns `{"anchor", "angle", "align", "px", "color", "box", "fill", "line", "lwidth", "padding"}` with None for "not given". Names outside `_DASH_ADDED_TEXT_HONOURED` (a hand-written spec) are named once through `_dash_report_suboptions("text", …)`.
- **TR-56.8 `_dash_added_text(fig, graph_opts, scheme=None, seen=None, key="", budget=None, limits=None)`** (new module function, after `_dash_text_annotations`):
  - `graph_opts["added_text"]` must be a list of dicts with finite numeric `at_y`/`at_x`, `at_yaxis`/`at_xaxis` in {1, 2}, `at_lines` a list of at most 64 str of at most 4,096 characters, `at_opts` a str of at most 4,096; anything else is skipped and named once (`dash: a hand-written added_text entry was not drawn.`).
  - Position: for each of x and y, the axis's date kind through S35's per-axis helper (`_dash_axis_date_kind` with the range name `"x2"`/`"y2"` when axis 2), then `_dash_axis_positions([v], kind)[0]`; axis 2 sets `x_range_name="x2"`/`y_range_name="y2"` only when `fig.extra_x_ranges`/`extra_y_ranges` holds it, else skip with one note.
  - `Label(x=…, y=…, x_units="data", y_units="data", text="\n".join(lines), anchor=…, angle=…, text_align=…, text_font_size=…, text_color=…, background_fill_color=…, border_line_color=…, border_line_width=…, padding=…, tags=["dash_added_text"])`, added with `fig.add_layout(label)` (centre, never a renderer, so S21's hull never reads it). Defaults from the scheme (TR-56.9) or, with no scheme, s2color's values; size: `_textbox_size` px (S08) or the scheme's pt string, at the unpaneled size (a by() panel's multiplier is applied once, later, by S48's `_dash_by_scale_panel`, which already scales every `Label`); colour `_textbox_color` (S30/S43); box only with `box` or the scheme's `text_option` yes; padding from `margin()` through S08's `resolve_size(…, "gap", …)` per side.
  - Text is raw: no `_dash_graph_text`, no `_dash_inert_tex` here; S09/S29's pass finishes it later in both modes.
  - `budget["n"] += 1` per Label; over `limits["added_text"]` → `DashLimitError` with `_dash_limit_hint("added_text", "draw more", start=True)` (the renderer's bound for a hand-written spec, as `_dash_cap_spec` is).
- **TR-56.9 Scheme defaults.** `SchemeParser._init_properties` (6806) reads, with bounds and `_FALLBACK_PROPS` (5728) entries holding s2color's values: `text_option_font_size` (`gsize text_option`), `text_option_color`, `text_option_line_color`, `text_option_fill_color`, `text_option_placement` (`compass2dir text_option`), `text_option_box` (`yesno text_option`), `text_option_line_width` (`linewidth text_option`, S13's ladder), `text_option_margin` (`margin text_option`), `text_option_justification` (`horizontal text_option`), `text_option_vertical` (`vertical_text text_option`). The served app's SchemeParser state comes from `_props` (unchanged mechanism). `scripts/extract_scheme_truth.py` resolves those ten keys through the include chain with provenance and writes them into all 26 files (keys S37 already wrote are not duplicated); the 26 files and `test/fixtures/scheme_truth.json` are regenerated once, never hand-patched (R7, A152).
- **TR-56.10 Call sites.** Saved: in `_make_figure_body` directly after the `_dash_text_annotations` call (:30400): `_dash_added_text(fig, graph_opts, self.scheme, _seen, _gkey, self.__dict__.setdefault("_dash_at_budget", {"n": 0}), getattr(self, "limits", None))`. Served: one generated line `_at_budget = {'n': 0}` after `_reported_subopts = set()` (:34920) and one generated call after `_dash_text_annotations(fig, go, _reported_subopts, gname, _DASH_SCHEME)` (:35261) with the same arguments (the limits dict the generated app already computes for `by_groups`, read on the tree). No scale is passed: S48's `_dash_by_scale_panel` scales each panel's Labels once in `_dash_layout_cell` (both modes), and `TestByPanels` pins exactly one multiplication. Both sites run before S09's pass and per figure, so every by() panel gets each Label. R12: S56 is batch 19's only editor of both symbols.
- **TR-56.11 Served copy list** (R2 row S56): constants `"_DASH_ADDED_TEXT_PLACE", "_DASH_ADDED_TEXT_ORIENT", "_DASH_ADDED_TEXT_HONOURED",` on a new line after `"_DASH_TEXTBOX_HONOURED",` (32933); functions `"_dash_added_text", "_dash_added_text_opts",` on a new line after `"_dash_text_annotations", "_dash_scale_spec",` (33375).
- **TR-56.12 Option surface.** If ratification item 26 stood (IR-7, `$S/wp30-ratified.txt` row 26), by hand: delete the two pending lines (:807, :1110) and their comments; nothing else changes for `text` in commit 1. If struck, update `scripts/regen_option_surface.py` (`("text", None)`) and run it, then verify the same diff.
- **TR-56.13 Help (commit 1)** (R3: Plot types, Resource limits and Unsupported are S56's): a `{marker added_text}` paragraph "Added text" at the end of Plot types (before `{marker differences}`, :443): what `text()` draws, the drawn and noted sub-options (BR-56.2), dates and axis 2, by() and iscale, filter moves, not widening the axes, the refusals; the Resource limits table gains `added_text` (default, ceiling, global, what it counts, r(134)); Unsupported's `{opt text(# # "string")} -- use note() or caption()` (:3736) is deleted; the Differences example (:598-599, S06's paragraph, no batch-19 owner) becomes `dash scatter mpg weight, play(x)` with `dash: ignoring unsupported option(s): play()` (the sentence would be false otherwise). Lines at most 79 characters.
- **TR-56.14 Registries (commit 1).** `function_test_map.py` under S56's anchor: `_dash_added_text`, `_dash_added_text_opts`. `program_coverage_map.py` `COVERAGE["dash.ado"]` under S56's anchor: `_dash_added_text` (AT-01, AT-20), `_dash_at_opts` (AT-05, AT-06); `COVERAGE["dash_parse.mata"]`: `_dash_at_copies` (AT-04), `_dash_at_isnum` (AT-01), `_dash_at_parse` (AT-01, AT-02), `_dash_at_place` (AT-21), `_dash_at_json` (AT-20), each with its `_needed` entry. `test/test_label_sinks.py`: the added-text Label as a sink with the hostile inputs. `test/test_resource_limits.py`: the new row in both tables.
- **TR-56.15 Security (rule 1; G9: "the `added_text` limit, no `_stata()` on user text").** Threats: user text executed (macro re-expansion, `` `=…' ``), a JSON key read as an option, unbounded models, MathJax on user text, HTML in text. Closed by TR-56.2-56.5 (by-value Mata reads, strict point literals, `syntax` on a copied local, `_dash_say`/`_dash_note` echoes, `at_` keys in one string, the limit in both languages), the S09/S29 pass, Bokeh's canvas text (no HTML sink), the 4,096-character bounds, and linear-time parsing (100,000 copies parse in under one second, a test). No Mata `stata()`/`_stata()` call and no Stata macro expansion ever receives a copy's text.

### Commit 2: ttext()

- **TR-56.16 Declaration.** `TTEXT(string asis)` beside `TEXT(string asis)` in both syntax blocks (:726, :971), `sreturn local ttext`/`g_ttext` beside text's (:859, :1278), `ttext` in the six propagation lists after `text`; IR-7's form as TR-56.12. `_dash_rep_cat`: `if (anyof(("text", "ttext"), k)) return("A")`; `ttext` is in neither pending list (it was never declared).
- **TR-56.17 The date path.** `_dash_added_text` runs the `ttext` copies after the `text` ones with `datesok` 1. For a record with `_at_xd<i>`: the time format is a `%t`/`%d` `format()` of the x axis's `xlabel()`, `xtick()`, `xmlabel()` or `xmtick()` (for `xaxis(2)`, their `…2` forms), else the first plot's x variable's display format on that axis (the tsset time variable for tsline); with no time format, or a token the converter rejects as a date, the refusal is twoway's (E3). The conversion is S51's Mata converter (TR-51.4), called by value from `_dash_at_parse`'s caller: `_dash_tdate_value(x, _dash_taxis_unit(<format>, 1), val)`. A return of 1 with a non-missing `val` gives the record's `at_x`. A return of 2 or 3, or 1 with a missing `val` (`.`, which S51 rates a number, but which twoway refuses as `. is not a number`), is refused as `<x> is not a number`, r(198), through `_dash_say`. The token reaches the converter by value through `st_local` and is never run (S51's whitelist gate). If a fixture case of E3 disagrees with S51's converter, stop and report (S51 owns it). `"at_kind":"ttext"` in the record; the renderer is unchanged.
- **TR-56.18 Help, registries (commit 2).** The "Added text" paragraph gains `ttext()` (BR-56.5); `program_coverage_map.py` entries gain the AT-30.. cases; R10 pins: declared graph (:608) +1, declared plot (:607) +1 if the plot block's count moves (measured), with the `# <old> -> <new>: P1.10 ttext declared` comment.

## Boundaries

- **Batch partners.** S54: `_dash_name_save`, the toolbar help and tests, `_DASH_BOKEH_INTERNALS`. S55: `_dash_build_hover` only. S56 edits none of them; they edit none of S56's symbols, files or help paragraphs.
- **Earlier sections, read only:** S08's resolver, S10's tables, S29/S09's pass and sink table (no new sink kind: `Label` is listed), S30/S43's colour reader, S35's date helpers, S48's `_dash_by_scale_panel`, S51's converter, S37's `textbox_style` (not used: `tstyle()` is noted, register P1.10.2), `_dash_rep_split`, `_dash_by_panels`, `_dash_json_first_num`.
- **Not this section's:** the empty trailing `|| , opts` segment dash refuses (P2.46, A32; AT cases never use it); `tstyle()` drawn from text box styles (a later item; noted now); Bokeh's clipping of a Label outside the frame (Notes); text in the toolbar's SVG (S54's action exports Labels).
- **Never:** `_FILTER_JS`, `_build_filter_widgets`, `_build_sources_and_figures`, the four appliers, `_dash_text_annotations`' own Labels, a generated scheme file by hand, `scripts/regen_option_surface.py` if retired.

## Stata truth

### `scripts/extract_added_text_truth.do` → `test/fixtures/added_text_truth.json` (commit 1; read by both commits)

S02's stanza (`DASH_REPO`), then `adopath ++ "`repo'/"` and `global dash_nobrowser 1`, in `scripts/extract_text_truth.do`'s shape (`zp id group dataset command option control`, SVG through `scripts/svg_truth.py`, `_meta` as S19's: `stata_version`, `born_date`, `dash_commit` via `shell git rev-parse HEAD` into a local read with `Macro.getLocal`, `extracted`; backtick as `\x60`; no `shell=True`). Each probe runs as `capture noisily` inside a named log so its notes and error lines are recorded.
- **Probes:** every row of E3's table (auto data; stcolor unless named), the default under s2color, s1mono, s1rcolor and s2color8, every refusal of E3 (rc and first error line), and the ttext cases (monthly data `t` %tm 1995m1-2004m12, `tn` its plain copy, daily `d` %td, `y` and `y2`).
- **Placement table:** for every spelling in `n north 12 t top 1 2 ne neast 3 e east r right 4 5 se seast 6 s south b bottom 7 8 sw swest 9 w west l left 10 11 nw nwest 0 c center`, the anchor of `text(30 3000 "PX", place(<p>))` and its note, recorded as `_meta.compass` (spelling → canonical or null); `orientation()` spellings and `orientation(bogus)` likewise into `_meta.orient`.
- **Records:** per probe `rc`, `error`, `notes`, and per added `<text>`: x and y in data units (through the probe's own tick positions), font size, fill, text-anchor, transform, line count; per box path fill and stroke.
- Run: `DASH_REPO="$WT" $SLOT "$S" "$WT/scripts/extract_added_text_truth.do"`; `git add -f test/fixtures/added_text_truth.json`.

### Area cases, `test/test_twoway_option_parity.cscript` (R1: one contiguous run at the end of its last case block, before `// Summary`)

Each runs live twoway (`capture twoway … nodraw`, rc and first error line from a log) and dash, in the script's `nfail`/`faillist` form, printing `AT-nn PASS: …`.
- **AT-01** (c1): each E3 point refusal: rc 198 both, the same line.
- **AT-02:** `text(30 3000 "x" 20)`, `text(30 3000 x)`: the same lines, double space included.
- **AT-03:** `text(30 3000 "x", yaxis(2))` and `xaxis(2)` with one axis: the axis-pair line; with `(scatter …) (scatter …, yaxis(2))`: rc 0 both.
- **AT-04:** `text(30 3000 "A", color(red)) text(20 4000 "B")`, the plot-group, `||` and graph-level copies (never `|| ,`): rc 0; the spec holds one record per point, each with its own `at_opts` (`color(red)` on A only).
- **AT-05:** `text(…, nosuch(1))`, `text(…, ori(v))`, `tex(…)`: twoway's line, r(198); `c(red)`, `si(large)`, `orient(vert)`, `place(zz)`: rc 0, and `place(zz)` prints twoway's compass2dir note in both.
- **AT-06:** `text(…, width(5) linegap(2) tstyle(heading))`: rc 0; dash prints one note naming the three.
- **AT-07:** `text()`, `text(30 3000)`, `text(30 3000 "")`: rc 0 both; no record.
- **AT-08:** neither `text()` nor (commit 2) `ttext()` appears in "ignoring unsupported option(s)".
- **AT-30..AT-36** (commit 2): every ttext case of E3: rc and line equal twoway's; drawn cases' `at_x` equal twoway's x (492, 15127).

### Injection cases, `test/test_json_escaping.cscript` (R1; JSE-style, by value)

- **AT-13:** `text(30 3000 "t\$J6_G")` and `text(30 3000 "`=1+1'")` (the latter written so the outer line does not expand it, in JSE-69's form): the record's line is the text as typed.
- **AT-14:** `text(\$J6_P 3000 "x")` and `text(30 3000 "x", color(\$J6_C))`: refused or stored as typed, never expanded (`$J6_*` set to values that would change the outcome).
- **AT-15:** `ttext(30 \$J6_D "x")` on a %tm axis (commit 2): the date token is not expanded.
- **AT-16:** a copy holding `char(30)` inside its quoted string: one record, the character not in the drawn text (A34).

### Limit cases, `test/test_resource_limits.cscript` (R1)

- **AT-40:** 1,001 points in one graph: r(134), the message names `dash_max_added_text`; with `global dash_max_added_text 2000`: rc 0.
- **AT-41:** 11 points with `by(rep78)` (5 panels drawn): 55 counted; with the global at 50: r(134).
- **AT-42:** two graphs of 600 points each and `dash build`: r(134) "this dashboard draws 1,200".

### The S56 blocks of `test/test_wp30_truth.cscript` (R1)

Commit 1 fills S01's S56 stub. Commit 2 adds a second block directly below the first block's `* ==== end S56 ====` line. Its header is `* ==== S56 P1.10: ttext() ====`, it has the same `WP30_ONLY` gate with `S56 start` first and `S56 end` last, and its own `* ==== end S56 ====` line (TR-01.10 item 4). The helpers sit directly above the first S56 header. They are Python functions `_s56_*` in one `python:` block: a reader of a saved page's Labels (text, x, y, anchor, angle, font size, colour, range names) that decodes both page encodings as `_br_saved` does (test_bug_regressions.cscript:159-180). They are called through one-line `python:` statements and return through `sfi.Macro.setLocal`. Any Stata helper program declares `version 19`.
- **AT-20:** `text(30 3000 "AAA")`: dash's Label at (3000, 30) data units; twoway's text at the same data point within 0.5% of the axis span.
- **AT-21:** every placement probe: dash's anchor is the canonical name's, as twoway's.
- **AT-22:** AAA red / BBB black and their size ratio 157.44/112.56 within 1%.
- **AT-23:** `by(foreign)`: one Label per panel, size ratio to the unpaneled 95.68/112.56 within 1%.
- **AT-24:** `yaxis(2)`: `y_range_name` `y2`, y = 10000.
- **AT-25** (commit 2): `tsline y, ttext(12 2001m1 "TT1")`: x = 2001m1 in the axis's unit.

## TDD test stubs

### Commit 1 regression tests, new `test/test_added_text.py` (red at `batch-19-base` unless marked guard; 56-01 to 56-03)

Imports: `dash_render as dr`; from `test_mode_parity`: `_render_pair`, `_annotations`, `_spec`, `_served_after_move`; from `test_saved_filter_layers`: `_render`, `_move`, `_MOVES`; from `test_server_layer_defects`: `plot_for`; `js_runner.requires_node`. `_FIX = json.load(test/fixtures/added_text_truth.json)`; `_at(y, x, lines, opts="", ya=1, xa=1, kind="text")` builds a record; `_labels(fig)` = the Labels tagged `dash_added_text`. Drawing classes are parametrized `mode in ("saved", "served")`.

- Test: the fixture has the four `_meta` keys, `stata_version` `19.`, every probe of "Stata truth", `_meta.compass` and `_meta.orient` — `TestTheFixture::test_it_is_stamped`
- Test: `_DASH_ADDED_TEXT_PLACE`'s keys and the Mata table's canonical names equal the fixture's; `_DASH_ADDED_TEXT_ORIENT` equals `_meta.orient` — `TestTheTables::test_they_are_the_fixtures`
- Test: `_dash_added_text_opts` on `size(large) color(red) placement(ne) justification(left) orientation(vertical) box fcolor(yellow) lcolor(blue) lwidth(thick) margin(medium)` → the anchor, angle π/2, align, px, colours, box, padding of S08's units; `""` → all None; `width(5)` → None and one note — `TestTheOptions::test_each_drawn_sub_option`
- Test (both modes): `text(30 3000 "AAA")` → one Label at (3000, 30) data units, `center` anchor, the scheme's `text_option` size and colour — `TestTheTextIsDrawn::test_one_point[mode]`
- Test (both modes, fixture): every drawn E3 probe: position, anchor, angle, size ratio to the default within 1%, colour, box fill and stroke, line count — `TestAgainstTwoway::test_probe[<probe>-saved|served]`
- Test (both modes): two copies with their own options; a plot-group copy, a `||` copy and a graph copy — `TestRepeatedCopies::test_each_copy_keeps_its_own_suboptions[mode]` (and the Mata unit through `_dash_rep_merge` in AT-04)
- Test (both modes): the default under s2color, s1mono, s1rcolor, s2color8 (fill bluishgray8 when boxed) matches the fixture — `TestSchemeDefaults::test_text_option_keys[<scheme>-mode]`
- Test (both modes): `%td` x and a date y on rbar (S35): the Label at `_dash_axis_positions`'s value; `xscale(log)`, `xscale(reverse)` — `TestAxes::test_dates_log_and_reverse[<case>-mode]`
- Test (both modes): `yaxis(2)` → `y_range_name == "y2"`; a hand-written `at_yaxis: 2` on a figure without y2 → no Label and one note — `TestAxes::test_second_axis[mode]`
- Test (both modes): `by(foreign)`: every panel has each Label, its `text_font_size` equal to the unpaneled size × `dr._dash_by_size_mult(by, 2)` exactly once (not squared) — `TestByPanels::test_every_panel[mode]`
- Test (both modes): the axis ranges equal those of the same graph without text; a Label at y=100 exists — `TestTheHull::test_texts_never_widen_an_axis[mode]`
- Test (node, saved) and served: after each `_MOVES` move the Labels (count, text, position) are unchanged — `TestFilterMove::test_labels_survive[<move>-saved|served]`
- Test (both modes): `$$x$$` and `{bf:B}` in a text: `_model_requires_mathjax` false, the Label text finished by S09/S29's pass exactly once — `TestTheText::test_tex_is_inert_and_smcl_finished[mode]`
- Test (both modes): hostile text (`</script>`, `"'`, backslashes, 4,096 characters) reaches `Label.text` verbatim and the page stays escaped — `TestTheText::test_hostile_text_stays_text[mode]`
- Test: a graph JSON holding a record whose `at_opts` is `width(5) bin(3) by(x)` and whose lines are `"width": 1` and `"added_text_n":0`: `_dash_json_has_value`/`_dash_json_first_num` (through the Mata twin in a cscript run) read as without it, and `added_text_n` reads dash's own count — `TestTheSpec::test_no_key_is_read_by_the_substring_readers` (with AT-04's spec)
- Test: dash.ado has no pending line for `text`, `_dash_rep_merge`'s category A joins with `char(30)`, and the JSON loop at the graph-options assembly no longer names `text` — `TestTheSpec::test_the_parser_writes_records`
- Test: `_DASH_LIMITS["added_text"] == (1000, 100000, "dash_max_added_text")` and dash.ado's row agrees; a hand-written spec of 1,001 records raises `DashLimitError` naming the global in both modes — `TestTheLimit::test_the_row_and_the_renderer_bound[mode]`
- Cscript (not a pytest node; pytest cannot run Mata): **AT-04b** in `test_twoway_option_parity.cscript`, directly after AT-04: 100,000 one-point copies joined by `char(30)` go through `_dash_at_copies` and `_dash_at_parse` in under one second (`timer`), and `_at_n` is 100,000
- Test: the generated app defines `_dash_added_text`, `_dash_added_text_opts` and the three constants — `TestTheServedCopy::test_the_app_defines_the_names`
- Test: dash.sthlp has `{marker added_text}` in Plot types, the `added_text` limit row, no Unsupported `text(` line — `TestTheHelp::test_the_help_documents_it`
- Shared: `test/test_mode_parity.py` `_annotations`' Label branch records `anchor`, `angle`, `text_align`, `x_range_name`, `y_range_name`, `background_fill_color`, `border_line_color`, `padding` and `tags`; CORPUS `_case("Added text (WP-30 P1.10)", [_sc()], go={"added_text": [<three records: plain, boxed ne, vertical on y2>]})` with a `yaxis(2)` second plot; `test/test_saved_filter_layers.py` `_CORPUS` gains one case with added text and `_MOVES[0]`; `test/test_label_sinks.py` gains the sink (TR-56.14).
- Cscript: AT-01..AT-08 (with AT-04b), AT-13, AT-14, AT-16, AT-20..AT-24, AT-40..AT-42.

### Commit 2 regression tests (red on the commit-1 tree; 56-14, 56-15)

- Test: dash.ado declares `TTEXT(string asis)` in both blocks, sets `s(ttext)`/`s(g_ttext)`, lists it in the six propagation lists; `_dash_rep_cat("ttext") == "A"` (through a cscript unit) — `TestTtext::test_it_is_declared`
- Test (both modes, fixture): every drawn ttext probe's Label x equals the fixture's, in the axis's unit — `TestTtext::test_probe[<probe>-saved|served]`
- Test: `scatter mpg weight, ttext(30 3000 "x")` draws as `text()` does — `TestTtext::test_a_number_is_a_number[mode]`
- Cscript: AT-15, AT-25, AT-30..AT-36.

### Pinned tests to flip (R9; re-measured, never trusted)

Commit 1 (56-09, 56-12): E5's `text` rows: `test_unsupported_report_is_true.py` moves `"text"` from its pending dict to `LIVE_VALUES` (`({"text": '20 3000 "hi"'}, {"text": '25 2500 "yo"'}, "scatter", {})` in that file's form) and the plot and graph pending counts −1 each (R10 comments); `test_help_conformance.py`'s two counts −1; HC8-02 `text` from `p_names`/`g_names` to the honoured list; JSE-46/JSE-69 read `"graph_options added_text"` and assert the stored line is the text as typed, the note needles drop `text()`; `test_help_examples.py:119`'s key becomes `'dash scatter mpg weight, play(x)'`; `test_help_claims_8.py`'s Unsupported pin follows the help. Commit 2 (56-17): the declared-graph count +1 (and declared-plot if it moved); any test asserting `ttext()` is an unknown option.

## Test plan

| What | How | Fixture / data | Both modes? |
|---|---|---|---|
| Parse, refusals, words | cscript AT-01..AT-08, AT-30..AT-36 against live twoway | auto, monthly, daily | n/a |
| Injection, separator | cscript AT-13..AT-16 | literal | n/a |
| Drawing against twoway | pytest `TestAgainstTwoway`, `TestSchemeDefaults`, `TestAxes`, `TestByPanels`, `TestTtext`; cscript AT-20..AT-25 | `added_text_truth.json` | yes |
| Moves, hull | pytest `TestFilterMove`, `TestTheHull` | `_DF` | yes |
| Text pass, sinks | `TestTheText`; `test_label_sinks.py` | literal | yes |
| Limit | `TestTheLimit`; cscript AT-40..AT-42; `test_resource_limits.py` | literal | yes |
| Parity | `test_mode_parity.py` CORPUS with the extended `_annotations` | CORPUS | yes |
| Scheme files | `test_scheme_fidelity.py`, `test_scheme_fallback_provenance.py` after regeneration | `scheme_truth.json` | n/a |
| Registries, tracking | map, coverage, hygiene, tracking, fixtures tests | — | n/a |

**Acceptance criteria.**
- **AC-56.1** (BR-56.1-BR-56.3) `TestAgainstTwoway`, `TestSchemeDefaults`, `TestAxes`, `TestByPanels`, `TestTheHull`, `TestFilterMove` pass in both modes; AT-20..AT-24 PASS.
- **AC-56.2** (BR-56.4, BR-56.7) AT-01..AT-08 PASS against live twoway; no `text()`/`ttext()` in any "ignoring unsupported" note of the suite's runs.
- **AC-56.3** (BR-56.5) `TestTtext` and AT-25, AT-30..AT-36 PASS.
- **AC-56.4** (BR-56.6) `TestTheLimit` and AT-40..AT-42 pass.
- **AC-56.5** (TR-56.15) `TestTheText`, `TestTheSpec`, AT-13..AT-16 pass; AT-04b's 100,000-copy parse is under one second.
- **AC-56.6** The 26 scheme files are the extractor's output, every pre-existing property unchanged; every flip has a `Flipped:` line; the full suite reports 0 failed before each commit; G7 prints 0 twice per commit.

## Tasks

**Commit boundary.** Tasks 56-01 to 56-13 form commit 1, made by 56-13 on `wp30-s56` with the subject `Draw text() annotations in both modes, part 1 of 2: text() (WP-30 P1.10)`, leaving the BUGS.md entry, its `WP30_OPEN` key and both markers in place (A156). Tasks 56-14 to 56-19 form commit 2, made by 56-19 with the subject `Draw ttext() at date literals, part 2 of 2: ttext() (WP-30 P1.10)`, which closes all three. `$S` is `/private/tmp/claude-501/-Users-billy-Desktop-Programs-StataPrograms-d-dash/55d6df3b-6200-4eb1-99b7-fa28b88519a2/scratchpad/wp30`, `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s56`, `$SLOT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh`. A cscript runs through the driver: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" "<script>.cscript" > "$S/run_<script>.do"`, then `WP30_ONLY=S56 "$SLOT" "$S" "$S/run_<script>.do"`. Each task appends the files it changed to `$S/56-files-<k>.txt` (k = the commit).

<task type="auto" id="56-01">
  <name>Write the fixture and pytest regressions</name>
  <files>scripts/extract_added_text_truth.do, test/test_added_text.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Check `git -C "$WT" rev-parse HEAD` equals `cat "$S/batch-19-base.txt"` and `git -C "$WT" branch --show-current` prints `wp30-s56`; stop otherwise. Create `scripts/extract_added_text_truth.do` as "Stata truth" describes (S02's stanza, `extract_text_truth.do`'s shape, every probe including the ttext ones, the placement and orientation tables, named logs, `_meta`) and run it with `DASH_REPO="$WT" "$SLOT" "$S" "$WT/scripts/extract_added_text_truth.do"`. Create `test/test_added_text.py` with every commit-1 stub, naming `dr._dash_added_text`, `dr._dash_added_text_opts` and the three constants so they fail with AttributeError now. Extend `test/test_mode_parity.py`'s `_annotations` Label branch and append the CORPUS case. Run `python3 -m pytest test/test_added_text.py -q -n 6 -p no:cacheprovider -rf > "$S/56-new-1.log" 2>&1` and the parity file with `-k "P1.10"`. Write `$S/56-P1.10-1-failure.txt`: the base sha, one line per failing node with its first error line, then "Guards (pass at the base)". Edit no shipped file; do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json; d=json.load(open('$WT/test/fixtures/added_text_truth.json')); m=d['_meta']; print(all(k in m for k in ('stata_version','born_date','dash_commit','extracted')), m['compass']['12'], m['compass']['r'])"` prints `True n e`; `grep -c FAILED "$S/56-new-1.log"` is at least 30; `git -C "$WT" diff --name-only -- dash.ado dash_parse.mata dash_render.py` prints nothing.]]></verify>
  <done>The twoway added-text fixture existed and every commit-1 pytest regression was shown failing on the unmodified tree, with the text saved.</done>
</task>

<task type="auto" id="56-02">
  <name>Write the refusal, injection and limit cases</name>
  <files>test/test_twoway_option_parity.cscript, test/test_json_escaping.cscript, test/test_resource_limits.cscript</files>
  <action><![CDATA[
    Add AT-01..AT-08 as one run at the end of `test_twoway_option_parity.cscript`'s last case block, before `// Summary`; AT-13, AT-14 and AT-16 at the end of `test_json_escaping.cscript`'s last case block, in JSE-69's by-value form; AT-40..AT-42 at the end of `test_resource_limits.cscript`'s last case block. Run the three scripts through the driver on the unmodified shipped files. Append every `AT-nn FAIL` line, with the twoway line it quotes, to `$S/56-P1.10-1-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -cE "AT-0[1-6] FAIL" "$S/run_test_twoway_option_parity.log"` is at least 5; `grep -cE "AT-1[346] FAIL" "$S/run_test_json_escaping.log"` is at least 2; `grep -cE "AT-4[0-2] FAIL" "$S/run_test_resource_limits.log"` prints 3.]]></verify>
  <done>The refusal, injection and limit cases were in their scripts and shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="56-03">
  <name>Write the commit-1 truth cases</name>
  <files>test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Put AT-20..AT-24 between S01's `S56 start` and `S56 end` lines of `test/test_wp30_truth.cscript`, printing `AT-nn PASS: …` through `_w30_expect`/`_w30_done`, files only under `` `w30_work' `` and erased before the end line; the `_s56_*` helper `python:` block of "Stata truth" goes directly above the S56 header. Run the block through the driver with `WP30_ONLY=S56` on the unmodified shipped files and append its `AT-nn FAIL` lines to `$S/56-P1.10-1-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -cE "AT-2[0-4] FAIL" "$S/run_test_wp30_truth.log"` prints 5; the log has no `SKIP`; `python3 -m pytest "$WT/test/test_cscript_hygiene.py" -q -n0 -p no:cacheprovider -k Wp30` reports 0 failed.]]></verify>
  <done>The twoway comparison cases were in S56's truth block and shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="56-04">
  <name>Split, merge and parse copies in Mata</name>
  <files>dash_parse.mata</files>
  <action><![CDATA[
    Apply TR-56.1 (category A joins with `char(30)`, the comment) and TR-56.2 (`_dash_at_copies`, `_dash_at_isnum`, `_dash_at_parse`, `_dash_at_place` from the fixture's `_meta.compass`, `_dash_at_json`, each with a header comment and its header-index entry at dash_parse.mata:1-303). `_dash_rep_merge` and `_dash_rep_cat` are UNKNOWN to the index; grep their callers (`grep -n "_dash_rep_merge\|_dash_rep_cat" dash.ado dash_parse.mata`) and run TP-14 after the edit. Read every user string by value; execute nothing.
  ]]></action>
  <verify><![CDATA[`test_twoway_option_parity.cscript` through the driver prints `TP-14 PASS`; a scratch do-file `$S/56-mata.do` (`adopath ++ "$WT/"`, `global dash_nobrowser 1`, `do "$WT/dash_parse.mata"`, then `mata: rows(_dash_at_copies(<two copies joined by char(30), the second holding char(30) inside its quotes>))`, `mata: _dash_at_isnum("3e3"), _dash_at_isnum("1e400"), _dash_at_isnum(".")`) run through the slot prints `2` and `1 0 0`.]]></verify>
  <done>Repeated text() copies stayed apart, and Mata split, checked and encoded every copy by value.</done>
</task>

<task type="auto" id="56-05">
  <name>Parse and refuse text() in Stata</name>
  <files>dash.ado</files>
  <action><![CDATA[
    Apply TR-56.3 (`_dash_at_opts`, reading its text through `_dash_text_args`), TR-56.4 (`_dash_added_text`, reading its text through `_dash_text_args`, its call in `_dash_plot` after the graph-options loop in the `` `"`macval(g_text)'"' `` form, `text` removed from that loop only), TR-56.5 (the `added_text` row in `_dash_limit_table`, the per-graph count with `r(kept)` saved right after the `_dash_by_panels` call, the dashboard sum in `_dash_prepare_spec`) and TR-56.12 (the two pending lines, by hand if ratification item 26 stood). Each new program opens with `version 19` and a header comment citing E2. Edit no other program.
  ]]></action>
  <verify><![CDATA[`test_twoway_option_parity.cscript` through the driver prints `AT-01 PASS` to `AT-08 PASS`; `test_json_escaping.cscript` prints `AT-13 PASS`, `AT-14 PASS` and `AT-16 PASS`; `test_resource_limits.cscript` prints `AT-40 PASS` to `AT-42 PASS`.]]></verify>
  <done>dash.ado parsed text() copies as twoway does, refused what twoway refuses in its words, named the undrawn sub-options once, bounded the count and wrote structured records.</done>
</task>

<task type="auto" id="56-06">
  <name>Draw added text as Labels</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-56.6 (the three constants after `_DASH_TEXTBOX_DEFAULTS`), TR-56.7 (`_dash_added_text_opts`), TR-56.8 (`_dash_added_text` after `_dash_text_annotations`), TR-56.9's `SchemeParser._init_properties` reads and `_FALLBACK_PROPS` entries, and `_DASH_LIMITS["added_text"]`. Read S35's per-axis date helper and S48's scale names on this tree first; use them, never re-derive. Do not call `_dash_graph_text` or `_dash_inert_tex` (the document pass finishes the text).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "$WT/test/test_added_text.py" -q -n 6 -p no:cacheprovider -k "Tables or Options or Limit"` reports 0 failed; `python3 -m pytest "$WT/test/test_resource_limits.py" -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>The renderer turned added-text records into tagged data-unit Labels with every drawn sub-option, bounded per document.</done>
</task>

<task type="auto" id="56-07">
  <name>Call it in both build paths</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn in the task log that `_make_figure_body` is CRITICAL (4) and `_generate_app_source` HIGH (5). Apply TR-56.10 exactly: one call after `_dash_text_annotations` in `_make_figure_body`; the generated `_at_budget` line after `_reported_subopts = set()` and the generated call after the template's `_dash_text_annotations` line. Apply TR-56.11's two copy-list lines. Edit nothing else in either symbol.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "$WT/test/test_added_text.py" -q -n 6 -p no:cacheprovider -k "not TestSchemeDefaults and not TestTheHelp"` reports 0 failed (those two pass after 56-08 and 56-11); `python3 -m pytest "$WT/test/test_mode_parity.py" "$WT/test/test_saved_filter_layers.py" "$WT/test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" -q -n 6 -p no:cacheprovider` reports 0 failed; the S56 block through the driver prints `AT-20 PASS` to `AT-24 PASS`.]]></verify>
  <done>Both modes drew every added text in every panel, kept through filter moves, finished by the document pass.</done>
</task>

<task type="auto" id="56-08">
  <name>Regenerate the text_option scheme keys</name>
  <files>scripts/extract_scheme_truth.py</files>
  <action><![CDATA[
    Add the ten `text_option` keys of TR-56.9 to the extractor's resolver properties and emitted directives, in its existing form (skip a key S37 already emits). Copy `test/fixtures/scheme_truth.json` and the 26 `dash-*.scheme` files to `$S/56-schemes-old/`, run the extractor as its header says, and compare with `$S/56-cmp.py`: every pre-existing property and directive of every scheme unchanged, only the new keys added; save to `$S/56-schemes-cmp.txt`. Never patch a generated file by hand (R7); the regenerated files go into `$S/56-files-1.txt`.
  ]]></action>
  <verify><![CDATA[`tail -1 "$S/56-schemes-cmp.txt"` reads `unchanged: 26 schemes; added keys only`; `grep -c "^color text_option_fill" "$WT/dash-s2color8.scheme"` prints 1; `python3 -m pytest "$WT/test/test_scheme_fidelity.py" "$WT/test/test_scheme_fallback_provenance.py" "$WT/test/test_added_text.py" -q -n 6 -p no:cacheprovider -k "not Help"` reports 0 failed.]]></verify>
  <done>Every shipped scheme carried its text_option keys, regenerated by the extractor and verified key by key.</done>
</task>

<task type="auto" id="56-09">
  <name>Flip the text() parser pins</name>
  <files>test/test_unsupported_report_is_true.py, test/test_help_claims_8.cscript, test/test_json_escaping.cscript</files>
  <action><![CDATA[
    Re-measure E5 on this tree, then flip commit 1's pins in these three files as "Pinned tests to flip" says: `text` from the pending dict to `LIVE_VALUES` and the plot and graph pending counts with the R10 comment; HC8-02's `text` to the honoured list; JSE-46 and JSE-69 to `"graph_options added_text"` with the stored-as-typed assertion kept and `text()` dropped from the note needles. Write each `Flipped:` line to `$S/56-flips-1.txt`. Delete no test.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "$WT/test/test_unsupported_report_is_true.py" -q -n 6 -p no:cacheprovider` reports 0 failed; `test_help_claims_8.cscript` and `test_json_escaping.cscript` through the driver print their `ALL CHECKS PASSED` lines.]]></verify>
  <done>Every parser pin that held text() as ignored or stored raw asserted it drawn and stored as records, with the reason recorded.</done>
</task>

<task type="auto" id="56-10">
  <name>Register the new names and sinks</name>
  <files>test/function_test_map.py, test/program_coverage_map.py, test/test_label_sinks.py</files>
  <action><![CDATA[
    Add TR-56.14's map entries under S56's anchors (alphabetical), the Mata functions' `_needed` entries in the same commit (X.5), and the added-text Label sink with the hostile inputs to `test/test_label_sinks.py` (inventory and `TEX_PAYLOADS`). Run the registry tests.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "$WT/test/test_function_test_map.py" "$WT/test/test_program_coverage_map.py" "$WT/test/test_label_sinks.py" -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>Every new function, program and sink was registered with a behavioural test.</done>
</task>

<task type="auto" id="56-11">
  <name>Document text() in help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    Apply TR-56.13: the `{marker added_text}` "Added text" paragraph at the end of Plot types, the Resource limits row, the Unsupported `text(` line deleted, the Differences example rewritten. Find each place by its text. Lines at most 79 characters; no tool or vendor name.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "$WT/test/test_added_text.py::TestTheHelp" -q -n0 -p no:cacheprovider` passes; `awk 'length > 79' "$WT/dash.sthlp" | grep -c "text("` prints 0.]]></verify>
  <done>The help documented text(), its drawn and noted sub-options, its refusals and the added_text limit.</done>
</task>

<task type="auto" id="56-12">
  <name>Flip the help-count pins</name>
  <files>test/test_help_conformance.py, test/test_help_examples.py, test/test_help_claims_8.py</files>
  <action><![CDATA[
    Re-measure and flip the pins 56-11's help moved: `test_help_conformance.py`'s ignored-list and Unsupported-section counts (R10 comment form), `test_help_examples.py:119`'s example key (`'dash scatter mpg weight, play(x)'`), and `test_help_claims_8.py`'s Unsupported equality pin. Append the `Flipped:` lines to `$S/56-flips-1.txt`. Delete no test.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "$WT/test/test_help_conformance.py" "$WT/test/test_help_examples.py" "$WT/test/test_help_claims_8.py" "$WT/test/test_resource_limits.py" -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>The help's count and example pins held the help as commit 1 left it, with the reasons recorded.</done>
</task>

<task type="auto" id="56-13">
  <name>Run the suite and make commit 1</name>
  <files>none</files>
  <action><![CDATA[
    Run every test file of `$S/56-files-1.txt` with `-n 6`, the four cscripts and the S56 block through the driver, and `test_cscript_hygiene.py`, `test_fixtures_are_committed.py`, `test_tracking_documents.py`. Then `git -C "$WT" merge --no-edit main` (expect `Already up to date.`) and one full run `"$S/full_suite_queue.sh" "$WT" "$S/56-full-1.log"` in the background, read when `exit=` appears, never relaunched (E6). Stage exactly `$S/56-files-1.txt`, with `git add -f test/fixtures/added_text_truth.json test/fixtures/scheme_truth.json`; check the staged list equals it (G6). Write `$S/56-message-1.txt` per "Notes: commit messages", check G7, confirm the branch, commit, check G7 again.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/56-full-1.log"` shows 0 failed and `exit=0`; `git -C "$WT" log -1 --format=%s` ends `(WP-30 P1.10)`; `grep -c '<!-- WP-30 P1.10 -->' "$WT/CHANGELOG.md"` prints 2; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Commit 1 drew text() in both modes and refused it as twoway does, green, with the entry, key and markers left for commit 2.</done>
</task>

<task type="auto" id="56-14">
  <name>Write the ttext() pytest and script cases</name>
  <files>test/test_added_text.py, test/test_twoway_option_parity.cscript, test/test_json_escaping.cscript</files>
  <action><![CDATA[
    On the tree commit 1 left, add `TestTtext` (commit-2 stubs) to `test/test_added_text.py`, AT-30..AT-36 to the end of S56's run in `test_twoway_option_parity.cscript`, and AT-15 after AT-16 in `test_json_escaping.cscript`. Run them; write `$S/56-P1.10-2-failure.txt` (the commit-1 sha, each failing node and AT line, then the guards). Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -cE "AT-3[0-6] FAIL" "$S/run_test_twoway_option_parity.log"` is at least 5; `grep -c "AT-15 FAIL" "$S/run_test_json_escaping.log"` prints 1; `grep -cE "AT-0[1-8] PASS" "$S/run_test_twoway_option_parity.log"` prints 8.]]></verify>
  <done>The ttext() pytest and script cases were in place and shown failing on the tree commit 1 left, with commit 1's cases still passing.</done>
</task>

<task type="auto" id="56-15">
  <name>Write the ttext() truth block</name>
  <files>test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Add the second S56 block `* ==== S56 P1.10: ttext() ====` with AT-25 directly below the first S56 block's end line, in the `WP30_ONLY` gate form (start line first, end line last). Run both S56 blocks through the driver and append the `AT-25 FAIL` line to `$S/56-P1.10-2-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c "AT-25 FAIL" "$S/run_test_wp30_truth.log"` prints 1; `grep -cE "AT-2[0-4] PASS" "$S/run_test_wp30_truth.log"` prints 5; `grep -c "S56 start" "$S/run_test_wp30_truth.log"` prints 2; `python3 -m pytest "$WT/test/test_cscript_hygiene.py" -q -n0 -p no:cacheprovider -k Wp30` reports 0 failed.]]></verify>
  <done>The ttext() twoway comparison was in its own S56 block and shown failing on the tree commit 1 left.</done>
</task>

<task type="auto" id="56-16">
  <name>Declare and convert ttext() dates</name>
  <files>dash.ado, dash_parse.mata</files>
  <action><![CDATA[
    Apply TR-56.16 (the declarations, `s()` lines, the six propagation lists, `_dash_rep_cat`) and TR-56.17 (the ttext pass of `_dash_added_text` with `datesok`, the time-format rule, S51's converter called as S51 calls it, the token by value). If any AT-30..AT-36 case disagrees with S51's converter, stop and report.
  ]]></action>
  <verify><![CDATA[`test_twoway_option_parity.cscript` through the driver prints `AT-30 PASS` to `AT-36 PASS`; `test_json_escaping.cscript` prints `AT-15 PASS`; the S56 blocks print `AT-20 PASS` to `AT-25 PASS` and `ALL CHECKS PASSED`, with no `SKIP`; `python3 -m pytest "$WT/test/test_added_text.py" -q -n 6 -p no:cacheprovider -k Ttext` reports 0 failed.]]></verify>
  <done>ttext() placed date literals in the axis's own units and refused them where twoway does, never running a date token.</done>
</task>

<task type="auto" id="56-17">
  <name>Flip ttext pins and document</name>
  <files>test/test_unsupported_report_is_true.py, dash.sthlp, test/program_coverage_map.py</files>
  <action><![CDATA[
    Re-measure and flip commit 2's pins (the declared counts with the R10 comment, any unknown-option assertion on `ttext`), writing `$S/56-flips-2.txt`. Extend the "Added text" paragraph with `ttext()` (BR-56.5) and add the AT-30..AT-36 cases to the coverage entries. Lines at most 79 characters.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "$WT/test/test_unsupported_report_is_true.py" "$WT/test/test_program_coverage_map.py" "$WT/test/test_added_text.py" "$WT/test/test_help_conformance.py" -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>The counts, coverage and help held ttext() as declared and drawn.</done>
</task>

<task type="auto" id="56-18">
  <name>Run the section's tests together</name>
  <files>none</files>
  <action><![CDATA[
    Run every test file of `$S/56-files-1.txt` and `$S/56-files-2.txt` with `-n 6`, the four cscripts and both S56 blocks through the driver, and the registry and tracking files. Record each last line in `$S/56-local-2.txt`. A failure is fixed in the task that owns its file first.
  ]]></action>
  <verify><![CDATA[Every line of `$S/56-local-2.txt` reports 0 failed and no skip.]]></verify>
  <done>Every test of both halves passed on the worktree.</done>
</task>

<task type="auto" id="56-19">
  <name>Close the entry and make commit 2</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Read the title as `WP30_OPEN["P1.10"]` ("text() and ttext() annotations are not drawn"). Close that BUGS.md entry in place (`- [x]`) with "Notes: BUGS.md Resolution". Delete the `"P1.10"` key line of `WP30_OPEN`. Replace both `<!-- WP-30 P1.10 -->` markers in place with "Notes: CHANGELOG lines" (New; Changed behaviour), covering both halves. Run `test_tracking_documents.py` with `-n0`; `git -C "$WT" merge --no-edit main` (expect `Already up to date.`); one full run `"$S/full_suite_queue.sh" "$WT" "$S/56-full-2.log"` in the background, read when `exit=` appears. Stage exactly `$S/56-files-2.txt` plus these three; check the staged list (G6). Write `$S/56-message-2.txt`, check G7, confirm the branch, commit, check G7 again, and report both shas and messages to the merger.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/56-full-2.log"` shows 0 failed and `exit=0`; `grep -c '<!-- WP-30 P1.10 -->' "$WT/CHANGELOG.md"` prints 0; `grep -c '^    "P1.10": "' "$WT/test/test_tracking_documents.py"` prints 0; `git -C "$WT" log -2 --format=%s` shows both subjects ending `(WP-30 P1.10)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Entry P1.10 was closed naming existing tests, its markers carried both halves' changes, and two green commits on wp30-s56 were ready for the merger.</done>
</task>

## Section completion criteria

- text() and ttext() are drawn as data-unit Labels in both modes, in every by() panel, on axis 2 and date axes, outside the plot when the point is, never widening an axis, unchanged by filter moves, each copy with its own drawn sub-options and the scheme's `text_option` defaults (fixture probes, AT-20..AT-25).
- dash refuses them where and as twoway does (AT-01..AT-08, AT-30..AT-36) and names undrawn sub-options once in Stata; neither is named as unsupported.
- Copies are parsed by value, never run (AT-13..AT-16); the `added_text` limit holds in both languages (AT-40..AT-42, `TestTheLimit`).
- The 26 scheme files and `scheme_truth.json` are the extractor's; `added_text_truth.json` is stamped and committed with `-f`.
- Every new function, program and Mata function is mapped; every flip has its reason; nothing is deleted.
- Two green commits `(WP-30 P1.10)` exist on `wp30-s56`; the second closes the entry, deletes its key and replaces both markers.

## Notes

- **Notes in Stata, colour and size notes in Python.** Placement, undrawn sub-options and refusals are Stata's (A30). An unreadable `color()` or `size()` value is reported by the shared `_textbox_color`/`_textbox_size` path S30/S08 own, which S23 relays for `dash build, server`; a test pins one note in both modes.
- **Labels outside the frame.** twoway draws `text(100 3000 "FAR")` outside the plot region (research t2m_5). Whether Bokeh clips a data-unit `Label` there is unmeasured (research "UNCLEAR"); batch 19's G8 checks it on the merged tree with S54's Save as SVG (the SVG holds the `<text>` or not). If clipped, it is a P2 row for S58, not a change here.
- **`|| , opts`.** dash refuses the empty trailing segment (P2.46, A32); no AT case uses it.
- **S37's keys.** If S37's Q-37.1 regeneration ran, `gsize text_option` and `color text_option` already exist; 56-08 adds only the missing eight.
- **python_exec hazard.** The extractor and the truth blocks need Stata's Python; check `~/.stata19/console/stata19.rc` after each slot run; a SKIP is not a pass.
- **Merge rules for the shared files.**
  - R1: AT-01..AT-08 and AT-30..AT-36 as one run in `test_twoway_option_parity.cscript`; AT-13..AT-16 in `test_json_escaping.cscript`; AT-40..AT-42 in `test_resource_limits.cscript`; S56's two truth blocks.
  - R2: S56's two anchors (32933, 33375); map entries under S56's anchors; Mata `_needed` entries.
  - R3: Plot types (the "Added text" paragraph), Resource limits and Unsupported are S56's rows. **R3 exception** (orchestrator-allowed): the Differences example at dash.sthlp:598-599. It sits in S06's paragraph, which has no batch-19 owner, and S56 must correct it because it would otherwise be false. index.md's R3 table should name it (review-notes g09.md).
  - R4/R5: both `P1.10` markers, the entry and its key, by commit 2 only.
  - R6: `version 19` in both new programs; Mata functions in the `_dash_rep_*` part with header-index entries.
  - R7: one new fixture and extractor; the scheme regeneration by 56-08's extractor run only, S56 landing last in the batch (A152).
  - R8: one CORPUS case and `_annotations`' Label branch extended (S54's `_tools`/`_grid_toolbar` and S55's cases beside it, all kept).
  - R10: plot and graph pending −1 (commit 1), declared graph +1 and declared plot +1 if measured (commit 2), the help-conformance counts.
  - R12: S56 is batch 19's only editor of `_make_figure_body` and `_generate_app_source`.
- **Landing (merger).** `gitnexus detect-changes --scope all --repo dash` must name, for commit 1, `_dash_added_text`, `_dash_added_text_opts`, `DashRenderer._make_figure_body`, `ServerAppBuilder._generate_app_source`, `ServerAppBuilder._glyph_layer_lines`, `SchemeParser._init_properties`, the constants and the extractor's symbols; for commit 2, nothing in dash_render.py beyond test symbols. At 19.0 the expected warnings are `_make_figure_body` (CRITICAL) and `_generate_app_source` (HIGH).
- **Commit messages.** Subjects as in "Commit boundary". Body, in order: the failure file; the measured defect (Overview's block); what changed and where (TR-56.1-TR-56.15 / TR-56.16-TR-56.18, both modes); the threats closed (G9): "user text is read by value and never run; added Labels are bounded by the added_text limit in Stata and the renderer"; one `Regression: test/test_added_text.py::<Class>::<test> -- failed at <base sha> with <text>` per node, `Regression: test/test_twoway_option_parity.cscript AT-01 -- failed at <base sha> with <text>` and likewise for the other scripts' cases; the `Flipped:` lines of `$S/56-flips-<k>.txt`; `Fixture: test/fixtures/added_text_truth.json (scripts/extract_added_text_truth.do)` and `Fixture: test/fixtures/scheme_truth.json (scripts/extract_scheme_truth.py)` (commit 1); commit 1 `BUGS.md: "text() and ttext() annotations are not drawn" (open; closed by part 2)`, commit 2 `BUGS.md: "text() and ttext() annotations are not drawn" (closed)`. No tool or vendor name (G7).
- **BUGS.md Resolution** (one line, in place):

  ```
  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.10). text() and ttext() are parsed as twoway parses them (dash.ado _dash_added_text and _dash_at_opts; Mata _dash_at_parse, _dash_at_copies, _dash_at_isnum, _dash_at_place, _dash_at_json; repeated copies kept apart by _dash_rep_merge), refused in twoway's words with r(198) for a malformed point, a missing axis pair, an unknown sub-option and a ttext() date the axis format cannot read (S51's converter), and drawn in the saved page and the served app as data-unit Labels (dash_render.py _dash_added_text, _dash_added_text_opts, called from DashRenderer._make_figure_body and the generated make_document) with placement, justification, orientation, size, colour, box, fill, outline, margin and axis pair, the scheme's text_option defaults (26 scheme files regenerated), in every by() panel at iscale, on date and log axes, never widening an axis and unchanged by filter moves; undrawn sub-options are named once in Stata; the added_text limit (default 1,000, ceiling 100,000, dash_max_added_text) refuses r(134). Pinned by test/test_added_text.py::TestAgainstTwoway::test_probe, test/test_added_text.py::TestRepeatedCopies::test_each_copy_keeps_its_own_suboptions, test/test_added_text.py::TestFilterMove::test_labels_survive, test/test_added_text.py::TestTtext::test_probe, test/test_added_text.py::TestTheLimit::test_the_row_and_the_renderer_bound, test/test_twoway_option_parity.cscript AT-01, test/test_json_escaping.cscript AT-13, test/test_wp30_truth.cscript AT-20; fixture test/fixtures/added_text_truth.json. Residual, deferred (WP-30): tstyle() and the other undrawn textbox sub-options are noted, not drawn; an empty trailing || , options segment is refused (P2.46).
  ```
- **CHANGELOG lines** (each replaces its marker in place; the `###` lines only say which list):

  ```
  ### New
  - `text()` and `ttext()` are drawn in both modes and after filter moves: `dash scatter mpg weight, text(30 3000 "AAA")` named `text()` as unsupported and drew nothing, and now draws AAA at that data point as twoway does, with placement, justification, orientation, size, colour, box, axis 2, date axes and every by() panel; repeated copies keep their own options; `ttext(12 2001m1 "event")` places a date literal in the x axis's own units. A new limit, `$dash_max_added_text` (default 1,000 texts times panels), bounds them. (WP-30, P1.10)

  ### Changed behaviour (may need your do-files changed)
  - `text()` and `ttext()` are refused where twoway refuses them, r(198) in twoway's words, where dash accepted them with a note: a malformed point (`invalid point, BAD 30`), an axis pair the graph lacks (`text() option invalid, specified axis pair (2 1) not in graph`), an unknown sub-option (`option nosuch() not allowed`) and a ttext() date the axis cannot read (`2001m13 is not a number`); more than `$dash_max_added_text` texts times panels is refused r(134). (WP-30, P1.10)
  ```
- **Notes for the closeout (S58; A145).**
  - **GAPS2.md B20** (:566-575): `- **Tracked:** Closed in WP-30, BUGS.md "text() and ttext() annotations are not drawn", commits <sha1>, <sha2>`.
  - **REMAINING.md** :128-131, :148, :446, :817 (REM-§2-S09-text, REM-S09-73-text, REM-§2-S09-ttext) and **TWOWAY_COVERAGE_AUDIT.md** :26, :136, :146 (AUDIT-13): closed by `<sha1>`, `<sha2>`.
  - **DROPIN-REMAINING.md:100** (P1.10): "Closed by <sha1>, <sha2> (WP-30 S56)."
  - **test/fixtures/rejected_options.json** text (:1980-2000, :3222, :3232) and ttext (:2092-2107, :5428-5435) rows and `summary.by_disposition`; **test/fixtures/twoway_corpus.do:214-215**'s expectations.
  - **P2 rows:** `tstyle()` drawn through `SchemeParser.textbox_style` (S37's table); Bokeh's clipping of an off-frame Label if G8 finds it.
  - **AGENTS.md invariant:** "added text reaches the renderer only as `added_text` records built by Mata from values read by value; the renderer draws each as a tagged data-unit `Label`, raw until the document pass."
