# Section 35-02: p1() .. p20() mapped onto their plots

> Part of: WP-35 (Accepted syntax and refusals) · Items: syn:SD-3 · Risk: yellow · Batch: 35.1 · Depends on: none · Blocks: -- · Tasks: 4, 1 commit · Case-id prefix: Q3502

## Overview

**What is wrong today.** Audit syn:SD-3: "p1()..p20(): p3()-p19() are refused, and p1(), p2() and p20() are noted and not drawn". twowaygraph_g.class:145-152 declares `P1(string asis)` .. `P20(string asis)` after the plot groups' comma and hands each to the #th plot (:236-252: `get_plot_count` counts each y of a varlist as a plot; the #th plot's command receives `p<jj>(...)`, jj its index inside that command), and twoway_yxview_parse.class:494-535 applies `p<i>()` to the i-th y of one plot command. Measured: `p1(mcolor(red))` drew 150 red marks; `p2(msymbol(none))` cut the circles from 300 to 150; `p3()`, `p10()`, `p19()` are rc 0; `p21()` is r(103). dash: `_dash_tw_takes_tab` (dash_parse.mata:8013) holds only `("p1","p1","1","*","1")` (:8114) and `("p20","p2","1","*","1")` (:8115), generated from unknown_option_truth.json (which probed p1 and p20 only), so p1(), p2() and p20() are noted and not drawn and p3()..p19() are refused r(198) with the after-comma hint.

**After this section.** `p<k>(opts)` after the plot groups' comma gives `opts` to the k-th plot (each y counted), and `p<j>(opts)` inside one plot's own options gives `opts` to that plot's j-th y, both drawn in both modes; a number above 20 is refused with twoway's measured rc and line; the generated takes table no longer carries p rows.

**Test order and commit rule.** 35-02-01 runs GitNexus impact on the functions it edits, measures twoway (new extract script, fixture) and writes the failing tests (no commit); 35-02-02 adds the parser; 35-02-03 regenerates the takes table and flips the pin; 35-02-04 certifies, documents, commits `(WP-35 syn:SD-3)`.

### Section decisions

- **D-35-02.a Text-level mapping.** p#() is resolved to option text before any segment is parsed: graph-level `p<k>()` texts are handed to the segment holding plot k; inside a segment each `p<j>()` text becomes stylelist elements for the j-th y. No renderer change.
- **D-35-02.b Precedence from the fixture.** Whether `p<k>(mcolor(red))` beats the plot's own `mcolor(blue)` is read from `pnum_truth.json` (`prec_own`, `prec_grp`): when twoway draws red, the p# copy is written AFTER the plot's own options (rightmost); when blue, BEFORE them. The executor writes the branch the fixture gives and records it in the commit body.
- **D-35-02.c Per-y keys.** For a segment with one y a `p1()` text is placed whole (D-35-02.b's side); an own `p<j>()` with j > 1 there is D-35-02.f's. For a segment with n > 1 ys, each p-text option that is a stylelist key (`_dash_stylelist_keys()`, dash_parse.mata:6502) becomes one copy `K(e1 .. en)` where e_i is the segment's own element for y_i (`_dash_stylelist_pick`, written `.` when empty) and e_j the p value; any other option inside a p# for one y of several is named in the note as not drawn (`p<j>(<opt>)`), the residual, documented in the help sentence.
- **D-35-02.d Repeats.** `p1() p1()` follows the fixture key `twice` (rightmost, or twoway's refusal with its rc and line).
- **D-35-02.e Plot numbers are twoway's.** The k of `p<k>()` counts twoway's plot numbers, not dash's plot objects: a ci fit (lfitci, qfitci, fpfitci, lpolyci) takes two numbers, its band and its line, or one under `nofit` (twoway's numbering, which 34-06 PIC-3 gives the renderer's styles). A later plot's p# is placed by that count (fixture keys `ci_after`, `ci_nofit_after`). A `p<k>()` whose k is one of a ci fit's own numbers is named in the note as not drawn (`p<k>()`), part of D-35-02.c's residual and its help sentence.
- **D-35-02.f An own p<j>() beyond the plot's ys.** twoway_yxview_parse.class:494-535 declares `p<i>()` only for i up to `.n`+1, so a plot's own `p<j>()` with j > n is not drawn as `p1()`. dash answers it as the fixture records: j = n + 1 as `plot_n1` reads (`(scatter mpg weight, p2(mcolor(red)))`), j > n + 1 as `plot_over` reads (`(scatter mpg weight, p3(mcolor(red)))`) -- dropped silently, drawn on the y the reading shows, or refused with the recorded rc and line (the option named as typed).
- **D-35-02.g Refusal order (WP-32).** twoway refuses the options after the comma only after every plot group's refusal (dash.ado:8453-8456, `_dash_gopts_checks` deferred to :8898). So `p21()` after the comma is refused after the segment loop, where `_gac_rc`'s deferred refusal is given, not before the loop (fixture key `order_p21`).

## Risk: [yellow] -- a new pre-pass on every command's option text

**Risk factors.** 1. `_dash_plot` (dash.ado:8335) and `_dash_process_segment` (dash.ado:5836) are shared with 35-09 in batch 35.1 (different lines: 35-09 edits the type lines :5868-5937 and the empty-graph checks). 2. Plot-level `P(string)` (dash.ado:1284, twoway's whole-plot style p()) must keep binding the bare `p()`. 3. The generated table must stay in step (`gen_twoway_takes_table.py --check`).

**Mitigation.** 1. This section's `_dash_process_segment` edit is one call inserted directly before `_dash_parse_plot_opts , ...` (:6614) and one `c_local _seg_pnums_out` beside `c_local _seg_nplots_out` (:7163); its `_dash_plot` edit is one call before the first `_dash_parse_graph_opts , ...` (:8452), one running total beside `_dash_nplots` (:8536, :8657), one global set/cleared around the segment loop and one deferred `p21()` refusal directly above `if 0`_gac_rc'` (:8898). 2. `_dash_p_take` matches only `p` followed by one to two digits and `(`; `p(` is left alone. 3. Task 03 regenerates and runs the check. 4. Task 01 runs GitNexus impact on `_dash_plot`, `_dash_process_segment` and `_dash_stylelist_pick` (all high fan-in); the handback names any HIGH, CRITICAL or UNKNOWN risk.

## Dependencies

- **Depends on / Blocks:** none.
- **Parallel batch 35.1:** with 35-01 (`_dash_label_split`, `_dash_contour_split`) and 35-09 (type lines, group splitting, empty graph). Merge after 35-01, before 35-09 (index order); `_dash_plot` hunks are disjoint.

## Evidence

- **twoway.** twowaygraph_g.class:145-152 (`local popts P1(string asis) .. P20(string asis)`, then `syntax [ , `popts' * ]`); :236-252 (`get_plot_count`, `tpopts` built as `p`jj'(`p`jjj'')` and appended to the plot's options); twoway_yxview_parse.class:494-535 (`parse_opts`: `p<i>()` for i up to `.n`+1 become `.plotstyles[i]`/`.plotsettings[i]`).
- **dash.** dash_parse.mata:8114-8115 (the two rows); scripts/gen_twoway_takes_table.py `rows()` (:60-82) emits a row per taken probe; dash.ado:1284 `P(string)` (plot-level p(), WP-30 P1.14a, applied in `_dash_plot_opts_to_json`, :5383-5386); `_dash_stylelist_pick` (dash_parse.mata:6643); `_dash_plot` segment loop (dash.ado:8553-...), running plot total `_dash_nplots`.
- **Fixtures.** unknown_option_truth.json `probes.p1`, `probes.p20` (rc 0); no probe of p2..p19 or p21.
- **Pinned tests.** test/test_option_report_paren.cscript:89-99 (case 3: `p1(mcolor(red) msize(small))` named in the note as ONE name) -- flip to another taken-and-noted option with a several-word value (Task 03). dash.sthlp's Unsupported list does not name p#() (syn:SD-15 is 48-02's; nothing to remove).

## User stories

- **US-35-02.1** As a Stata user with an existing twoway command, I want `(scatter mpg weight) (scatter price weight), p2(mcolor(red))` to colour the second plot red, as twoway does.
- **US-35-02.2** As that user, I want `scatter mpg trunk weight, p2(msymbol(none))` to hide the second y's markers.
- **US-35-02.3** As that user, I want `p21()` refused with twoway's message.

## Business requirements

- **BR-35-02.1** p1()..p20() after the comma style the plot of that number (each y of a varlist counted), as twoway draws it; a number with no such plot changes nothing, silently.
- **BR-35-02.2** p<j>() inside one plot's options styles its j-th y; a j beyond the plot's ys is answered as twoway answers it.
- **BR-35-02.3** The precedence between p#() and the plot's own option, and a repeated p#(), follow twoway's measured answer.
- **BR-35-02.4** p21() and above: twoway's rc and line. Saved and served pages agree.

## Technical requirements

- **TR-35-02.1 `_dash_p_take(string scalar opts, real scalar side)`** (new, dash_parse.mata, after `_dash_tw_refuses_tab`): scans `_dash_opt_tokens(opts)`; a token matching `^p([1-9][0-9]?)\(` (ustrregexm, lower case only) is removed; its number k and inner text (between the first `(` and the matching last `)`) are stored as locals `_pt_n` (count), `_pt_k<i>`, `_pt_v<i>`; a k above 20 sets `_pt_bad` to the token as typed (cut to 80 characters); returns the remaining text joined with single blanks. `side` is unused today (kept 0) -- omit it if the executor prefers; then the signature is `(string scalar opts)`. `_needed` list: the two names dash.ado calls on one new continuation line `        _dash_p_take _dash_p_merge ///` inserted directly before the list's last line (`        _dash_abs_path _dash_graph_names ...`, dash.ado:506; re-read), touching no existing line (35-01 inserts its line after :470 and 35-09 edits :485 and :492 in batch 35.1, so no two insertions share a position; R2-22); `_dash_p_key` is called only from `_dash_p_merge`, so it is in neither `_needed` nor the header index (test_file_headers.py holds the index to `_needed`); header index: one new `*!` entry each for `_dash_p_take` and `_dash_p_merge`, inserted directly after the `*!   _dash_stylelist_keys()` entry's description (dash_parse.mata:245), touching no existing line; program_coverage_map.py rows (every dash_parse.mata function has one) `"_dash_p_take": ("test_wp35_truth.cscript:Q3502-1",)` and the same for `_dash_p_merge` and `_dash_p_key`, inserted directly after the `"_dash_tw_refuses": ...` row (:779), beside their name neighbours (the map groups rows by name), never at the end of the dict; 35-01's row goes after `"_dash_opt_tokens"` (:829), apart from these (R2-22).
- **TR-35-02.2 `_dash_p_merge(string scalar segopts, string scalar ptext, real scalar j, real scalar n, real scalar after)`** (new, dash_parse.mata, after `_dash_p_take`): returns the segment's option text with `ptext` applied to y j of n (1 <= j <= n; the caller answers j > n by D-35-02.f and never passes it) per D-35-02.b/c: n == 1 -> `segopts + " " + ptext` (after = 1) or `ptext + " " + segopts` (after = 0); n > 1 -> for each token of `_dash_opt_tokens(ptext)`, its key from `_dash_p_key(tok)` (TR-35-02.3); a stylelist key K gets the copy `K(e1 .. en)` appended (after = 1) or prepended (after = 0), e_i read with `_dash_stylelist_pick` from the segment's LAST copy of K (resolved the same way), `.` for empty, the p value (`_dash_stylelist_elems` row 1, quoted when it holds a blank) for e_j; any other token is returned through the local `_pm_named` (space-separated `p<j>(<name>)` words) for the caller's note.
- **TR-35-02.3 `_dash_p_key(string scalar tok)`** (new): the full stylelist key a token binds to, or "": a literal two-column table (full key, minimum) of the 45 keys of `_dash_stylelist_keys()`, each minimum copied from the capitals of its declaration in `_dash_parse_plot_opts`'s syntax (dash.ado:1245-1333; e.g. `("mcolor","mc")`, `("msymbol","m")`, `("lwidth","lw")`); a token's name (`_dash_rep_optname(tok)`) of length L matches row r when `L >= strlen(min) & substr(full, 1, L) == name`. A pytest guard checks the table against the declaration text.
- **TR-35-02.4 Graph level.** In `_dash_plot`, before the first `_dash_parse_graph_opts , `macval(gopts_raw)'` (:8452; a second call at :8462 re-parses the same text and a third at :8900 -- all three must see the text after `_dash_p_take`): `mata: st_local("gopts_raw", _dash_p_take(st_local("gopts_raw")))`; keep `_pt_bad` in a local `_pt_gbad` (`local _pt_gbad : copy local _pt_bad`) and go on; set `global dash__pnum` to the valid pairs (`<k>:<text>` joined by char(1)), cleared with `global dash__pnum ""` after the segment loop and at `_dash_plot`'s start beside `dash__pend`. The refusal is deferred (D-35-02.g): directly above the `if 0`_gac_rc'` block after the segment loop (:8898; re-read), `if `: length local _pt_gbad'` -> print the line recorded in pnum_truth.json `g_p21` (copied into dash.ado as a literal, commented `// pnum_truth.json g_p21`; shipped code never reads a fixture; the typed token substituted where the line echoes it, through `_dash_say`, cut to 80 characters) and exit with its recorded rc. So `(scatter mpg weight, bogus), p21(mcolor(red))` names `bogus`, as twoway does (fixture `order_p21`), because the segment's own refusal comes first.
- **TR-35-02.5 Plot level and hand-over.** In `_dash_process_segment`, directly before `_dash_parse_plot_opts , `macval(opts_raw)'` (:6614): (a) `_dash_p_take` over `opts_raw` (its own `p<j>()`); (b) the y count n is `: word count `yvarlist''` when set, else 1 (the `_sl_n` rule at :6724-6725 -- compute it here the same way); (c) the offset T is the number of twoway plot numbers before this segment (D-35-02.e): `_dash_process_segment` sets `c_local _seg_pnums_out` beside `c_local _seg_nplots_out` (dash.ado:7163) -- `2` when `ptype` is lfitci, qfitci, fpfitci or lpolyci and the segment's `nofit` is not set (re-read the local the ci parse sets for `nofit`), else `_nyv` -- and `_dash_plot` keeps `local _dash_pnum_t = 0` beside `_dash_nplots` (:8536), adds `_seg_pnums_out` to it beside the `_dash_nplots` sum (:8657), and passes it in `global dash__poff` set before each `_dash_process_segment` call; (d) for each graph-level pair with T < k <= T + n on a segment that is not a ci fit, and then each own pair with j <= n (a graph-level pair whose k lands on a ci fit's own numbers is added to `_pm_named` as `p<k>()`, D-35-02.e), `opts_raw = _dash_p_merge(opts_raw, v, j, n, <after from the fixture>)`; an own pair with j > n follows D-35-02.f's readings, a literal branch commented `// pnum_truth.json plot_n1: <reading>` for j = n + 1 and `// pnum_truth.json plot_over: <reading>` for j > n + 1 (any j `_dash_p_take` takes, up to 99): dropped silently, merged onto the y the reading shows, or refused with the recorded rc and line, the token's name substituted as typed through `_dash_say`, cut to 80 characters; (e) a non-empty `_pm_named` is added to the note through the segment's catch-all (append the words to `s(_unknown)` after `_dash_parse_plot_opts` returns). A `p<k>()` whose k exceeds every plot is dropped silently (twoway draws nothing for it).
- **TR-35-02.6 Generator.** scripts/gen_twoway_takes_table.py `rows()`: skip probes whose `option` matches `^p[0-9]+\(` with the comment `# p1() .. p20() are read by _dash_p_take before the catch-all (WP-35 syn:SD-3).`; regenerate dash_parse.mata (`python3 scripts/gen_twoway_takes_table.py`), check (`--check` exit 0).
- **TR-35-02.7 Both modes.** No renderer change: the merged option text reaches the spec, which both modes draw.

## Boundaries

- Not here: plot-level `p()` (unchanged), pstyle(), `_dash_plot_opts_to_json`, the renderers, by()-specific behaviour, the Unsupported list (48-02), `_dash_label_split`/`_dash_contour_split` (35-01), the plot-type and group lines of `_dash_process_segment`/`_dash_split_groups` (35-09).

## Stata truth

**New extractor** `scripts/extract_pnum_truth.do` (head -- repo root check, `shell git rev-parse HEAD` into a local read by the python block through `Macro.getLocal`, `_meta` -- and writer modelled on scripts/extract_noted_option_truth.do:1-70 and :182-326), twoway only, `sysuse auto`, each probe `capture noisily twoway <cmd>`, rc and first message line recorded, and when rc 0 `graph export <work>/<id>.svg` read for the count of marker fills equal to `#FF0000` (or `#0000FF`) through `scripts/svg_truth.py`'s marker reader (re-read its function names):

| Key | Command | Recorded |
|---|---|---|
| `g_p1` | `scatter mpg weight, p1(mcolor(red))` | rc, red markers |
| `g_p3` | `(scatter mpg weight) (scatter price weight) (scatter trunk weight), p3(mcolor(red))` | rc, red markers (74 expected) |
| `g_p20`, `g_p19` | `scatter mpg weight, p20(mcolor(red))`, `p19(...)` | rc, red markers (0) |
| `g_p21` | `scatter mpg weight, p21(mcolor(red))` | rc, first line |
| `multi_y` | `scatter mpg trunk weight, p2(mcolor(red))` | rc, red markers |
| `plot_level` | `(scatter mpg trunk weight, p2(mcolor(red)))` | rc, red markers |
| `prec_own` | `scatter mpg weight, mcolor(blue) p1(mcolor(red))` | rc, red and blue markers |
| `prec_grp` | `(scatter mpg weight, mcolor(blue)), p1(mcolor(red))` | rc, red and blue markers |
| `twice` | `scatter mpg weight, p1(mcolor(red)) p1(mcolor(blue))` | rc, first line, red and blue |
| `bad_inner` | `scatter mpg weight, p1(nosuch(1))` | rc, first line |
| `ci_after` | `(lfitci mpg weight) (scatter mpg weight), p3(mcolor(red))` | rc, red markers (74 expected: the scatter is plot 3) |
| `ci_nofit_after` | `(lfitci mpg weight, nofit) (scatter mpg weight), p2(mcolor(red))` | rc, red markers (74 expected: the scatter is plot 2) |
| `plot_n1` | `(scatter mpg weight, p2(mcolor(red)))` | rc, first line, red markers |
| `plot_over` | `(scatter mpg weight, p3(mcolor(red)))` | rc, first line, red markers |
| `order_p21` | `(scatter mpg weight, bogus), p21(mcolor(red))` | rc, first line (expected to name `bogus`) |

Run `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch> $WT/scripts/extract_pnum_truth.do`; `git add -f test/fixtures/pnum_truth.json`.

**Truth block** `* ==== S02 syn:SD-3: p1() .. p20() mapped onto their plots ====`, inserted directly above the first block whose S<MM> is higher than S02 (BRIEF Block order), or above the marker if there is none:
- **Q3502-1** for each fixture key with rc 0 (`ci_after`, `ci_nofit_after`, and `plot_n1` and `plot_over` when rc 0, included): `dash <cmd> name(s02)` rc 0, no `ignoring unsupported` naming `p<k>()`, and the registered spec's colour of the target plot (Mata reading of `dash_json_s02`, the plot object's `mcolor`) is red where the fixture counts red markers and not red where it counts none.
- **Q3502-2** `g_p21`, `bad_inner`, `order_p21` (and `twice`, `plot_n1` and `plot_over` when refused): dash's rc and first line equal the fixture's.
- **Q3502-3** the saved page of `g_p3` and its served app draw the third plot's markers red (read the Bokeh models with the existing `cert_svg.do`/model-reading helper the WP-31 blocks use; re-read one WP-31 block that inspects a saved page before writing this).

## TDD test stubs

Regression tests (red at `090d928`): `test/test_pnum.py::TestTheFixture::test_meta_and_readings` (guard after 01); `::TestTheParser::test_take_and_merge_are_defined` (red; the one existence node for `_dash_p_take` and `_dash_p_merge`, which no pytest can run -- it also asserts both names are in `_needed`; REVIEW R2-47); `::TestTheKeyTable::test_minimums_match_the_declarations` (red; pins `_dash_p_key`'s table to the declarations); `::TestTheTakesTable::test_no_p_rows` (red: rows `("p1"` and `("p20"` present); cscript Q3502-1..3 (red).
Pinned test to flip: test_option_report_paren.cscript case 3 (Task 03).
Parity corpus (R8): none. p#() is resolved to option text before the spec is written and both renderers read that spec, so there is no twin (REVIEW R2-6); Q3502-3 checks the saved page and the served app directly. A `CORPUS` entry is a `_case(...)` spec (test/test_mode_parity.py:1480), never a command string.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| p# drawn on its plot | Q3502-1, Q3502-3 | pnum_truth.json | yes |
| refusals | Q3502-2 | pnum_truth.json | n/a |
| key table, generator | pytest test_pnum.py, `gen_twoway_takes_table.py --check` | unknown_option_truth.json | n/a |

**Acceptance criteria.** **AC-35-02.1** S02 prints Q3502-1..3 PASS, no FAIL/SKIP. **AC-35-02.2** `python3 -m pytest test/test_pnum.py test/test_program_coverage_map.py test/test_file_headers.py test/test_no_orphans.py -q -n0` 0 failed; `python3 scripts/gen_twoway_takes_table.py --check` exits 0. **AC-35-02.3** test_option_report_paren.cscript ends PASS.

## Tasks

**Commit boundary.** 35-02-01..04 are one commit on `wp35-s02` (`$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp35-s02`), subject `Draw p1() to p20() on the plot of that number, as twoway does (WP-35 syn:SD-3)`; body as BRIEF, with `Fixture: test/fixtures/pnum_truth.json (scripts/extract_pnum_truth.do)`, `Flipped: test/test_option_report_paren.cscript case 3 -- p1() named in the note was wrong because twoway draws p1() (syn:SD-3)`, the precedence branch taken (D-35-02.b), `BUGS.md: "<syn:SD-3 title>" (closed)`, `GAPS4: syn:SD-3 Tracked`, the line `TWOWAY_COVERAGE_AUDIT.md: no coverage-audit row` (p#() has no row there; REVIEW R2-9), `Ledger: <n> rows of syn:SD-3 removed; known differences: <m> rows removed`, and the GitNexus risks from `<scratch>/35-02/anchors.txt`.

**Clear the known differences of syn:SD-3** (35-02-04) means BRIEF's closing steps (1)-(3) ("The corpus ledger and the known-differences tables"; D-33-05.i, D-33-10.a/b/h, D-33-09.c), run in `$WT` before staging; syn:SD-3 closes `Closed` and so should have no `(documented)` or `(residual)` row (one would be dead once it closes: hand it back): (1) `awk -F'\t' -v id='syn:SD-3' '$1 == id {print NR ": " $0}' scripts/corpus/ledger.tsv` lists the item's plain rows of the corpus ledger; delete each line it prints (an `syn:SD-3 (documented)` or `syn:SD-3 (residual)` row stays, A-10), run `python3 scripts/corpus/ledger.py` (no run folder: `_meta` is kept, TR-33-05.3), `git add scripts/corpus/ledger.tsv` and `git add -f test/fixtures/corpus_ledger.json`, and run `python3 -m pytest test/test_corpus_ledger.py -q -n0 -p no:cacheprovider` (0 failed); (2) run `python3 test/known_differences.py syn:SD-3` (33-10, D-33-10.h) and delete every `<file>:<line>` row it prints from its `*_KNOWN` table, staging each file edited; a difference the item's ruling keeps moves instead into that table's deliberate dict -- `DELIBERATE` for `VALUE_KNOWN` (test/value_truth_known.py), `ABBREV_DELIBERATE` for `ABBREV_KNOWN` (test/test_abbreviations.py), and `SCALE_FRAME_DELIBERATE`, `BY_TYPES_DELIBERATE`, `BY_POSITION_DELIBERATE`, `STAT_COMBOS_DELIBERATE` or `COLORVAR_DELIBERATE` beside 33-11..33-13's `SCALE_FRAME_KNOWN`, `BY_TYPES_KNOWN`, `BY_POSITION_KNOWN`, `STAT_COMBOS_KNOWN` and `COLORVAR_KNOWN` -- as `"<key>": "<ruling id>: <what is kept>"`, the ruling id a DECISIONS or index id (P4-n, A-n, Q-n, M-n) (no ruling of this section keeps a difference, so nothing is expected to move); then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`), 0 failed; (3) write the driver `printf 'cd "%s/test"\nglobal dash_nobrowser 1\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp33_truth.cscript > <scratch>/run_test_wp33_truth.do`, run `WP33_ONLY=S09 sh $WT/scripts/stata_slot.sh <scratch> <scratch>/run_test_wp33_truth.do` and read `<scratch>/run_test_wp33_truth.log`; if Q3309-1 reports any change for a guard example -- `<example id> improved from ...` or `<example id>: <field> was <old> now <new>` (D-33-09.c) -- regenerate test/fixtures/corpus_guard_truth.json with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s09 $WT/scripts/extract_corpus_guard_truth.do`, run S09 again until it prints `Q3309-1 PASS`, `git add -f test/fixtures/corpus_guard_truth.json` into this item's commit and add `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)` to its body (a verdict this item's change made worse is a regression: fix the code first, then run S09 again). After step (2), also run `WP33_ONLY=S10` of test_wp33_truth.cscript through the same driver: a row keyed to another id that S10 reports as now agreeing (known_problems rule 2: this fix fixed it) is deleted too and named in the body; a deleted row whose difference S10 still reports (rule 1) means the fix is incomplete -- fix the code, never put the row back. Then pull from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main).

<task type="auto" id="35-02-01">
  <name>Measure p# in twoway; write failing tests</name>
  <files>scripts/extract_pnum_truth.do, test/fixtures/pnum_truth.json, test/test_pnum.py</files>
  <action><![CDATA[
    Check the branch is `wp35-s02`. From `$WT` run `node .gitnexus/run.cjs impact "_dash_plot" --direction upstream --repo .` and the same for `_dash_process_segment`, `_dash_stylelist_pick`, `_dash_require_mata` (its `_needed` list gains a line), `rows` (scripts/gen_twoway_takes_table.py) and `_dash_tw_takes_tab` (the generated table loses its p rows), writing callers, processes and risk to `<scratch>/35-02/anchors.txt` (HIGH, CRITICAL or UNKNOWN named in the handback; UNKNOWN confirmed by `grep -n`). Create scripts/extract_pnum_truth.do per "Stata truth", run it through the slot, `git add -f` the fixture; write the `prec_own`, `prec_grp`, `twice`, `g_p21`, `ci_after`, `ci_nofit_after`, `plot_n1`, `plot_over` and `order_p21` readings to `<scratch>/35-02-readings.txt`. Create test/test_pnum.py with the four nodes of "TDD test stubs". Add the S02 block (Q3502-1..3) to test/test_wp35_truth.cscript at the place "Stata truth" names. Run the pytest file and `WP35_ONLY=S02` through the driver; save the FAIL lines to `<scratch>/35-02-01-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/pnum_truth.json'));print(sorted(d['_meta']), d['g_p3']['rc'], d['g_p21']['rc'])"` prints the five meta keys, `0` and `103` (another reading: stop and re-check the probe); `ci_after` and `ci_nofit_after` each count 74 red markers; pytest shows 3 FAILED and 1 passed; the Stata log shows Q3502-1 FAIL; `test -s <scratch>/35-02/anchors.txt`.]]></verify>
  <done>twoway's reading of p1() to p21(), its precedence and its repeat answer were recorded in a stamped fixture, and the tests were shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="35-02-02">
  <name>Take p# and merge it per y</name>
  <files>dash_parse.mata, dash.ado, test/program_coverage_map.py</files>
  <action><![CDATA[
    Make TR-35-02.1 to TR-35-02.5 (with D-35-02.e's count), with the `after` flag and the repeat rule taken from `<scratch>/35-02-readings.txt` (a literal in the code with the comment `// pnum_truth.json prec_own: <reading>`). Run `WP35_ONLY=S02` and `python3 -m pytest test/test_pnum.py test/test_program_coverage_map.py test/test_no_orphans.py -q -n0`.
  ]]></action>
  <verify><![CDATA[Q3502-1 and Q3502-2 PASS; pytest: only `test_no_p_rows` still fails.]]></verify>
  <done>p#() after the comma and inside a plot reached the plot and y of its number, in the order twoway applies it.</done>
</task>

<task type="auto" id="35-02-03">
  <name>Regenerate the takes table; flip the pin</name>
  <files>scripts/gen_twoway_takes_table.py, dash_parse.mata, test/test_option_report_paren.cscript</files>
  <action><![CDATA[
    Make TR-35-02.6. In test_option_report_paren.cscript case 3 (:89-99) replace `p1(mcolor(red) msize(small))` by a row of the regenerated `_dash_tw_takes_tab` that is taken on scatter, noted, and takes a value of two words (e.g. `zvarlabel("a b")`; check it is still a row), keep the "ONE name" assertions with the needles rewritten to that option, and add the comment `// Flipped: WP-35 syn:SD-3 -- p1() is drawn now, so a noted option with a several-word value is used.` Run that cscript through the driver and `python3 scripts/gen_twoway_takes_table.py --check`.
  ]]></action>
  <verify><![CDATA[`grep -c '("p1",\|("p20",' dash_parse.mata` prints 0; `--check` exits 0; test_option_report_paren.cscript passes; `test_no_p_rows` passes.]]></verify>
  <done>The generated table no longer carried p rows and the note test used an option that is still noted.</done>
</task>

<task type="auto" id="35-02-04">
  <name>Certify, document, close syn:SD-3, commit</name>
  <files>dash.sthlp, CHANGELOG.md</files>
  <action><![CDATA[
    Run S02 whole (Q3502-1..3 PASS). dash.sthlp: in the graph-options paragraph that names {cmd:pcycle()} (grep `pcycle()`; re-read), add: `{cmd:p1()} to {cmd:p20()} after the comma give their options to the plot of that number, each y of a varlist counted and a confidence-interval fit counted twice (once under {cmd:nofit}), and {cmd:p}{it:#}{cmd:()} inside a plot gives them to its {it:#}th y, as {cmd:twoway} draws them; for one y of several only the style options are drawn, and any other, or a {cmd:p}{it:#}{cmd:()} that names a confidence-interval fit's own band or line, is named in the note.` Add a one-line Differences entry linking to it ("{cmd:p}{it:#}{cmd:()} for one y of several: style options only; see ..."). CHANGELOG `### Changed behaviour`: `- p1() to p20() are drawn on the plot of that number (p3() to p19() were refused, p1(), p2(), p20() named and not drawn). (WP-35, syn:SD-3)`. Close BUGS.md, GAPS4.md and the `GAPS4_OPEN` line in test/test_tracking_documents.py as 35-01-03 does (TWOWAY_COVERAGE_AUDIT.md has no row for p#(); the commit body says so). Run test_tracking_documents.py, test_help_conformance.py. Clear the known differences of syn:SD-3 (Commit boundary; BRIEF steps (1)-(3): syn:SD-3's plain rows of scripts/corpus/ledger.tsv and test/fixtures/corpus_ledger.json, `python3 test/known_differences.py syn:SD-3` and the hygiene command it prints, the S09 guard and test/fixtures/corpus_guard_truth.json on any Q3309-1 change; then `WP33_ONLY=S10`); pull from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main); stage; run `node .gitnexus/run.cjs detect-changes --scope all --repo .` (rerun a partial or truncated result) and copy its summary to `<scratch>/35-02/detect.txt`; message, grep, commit, re-grep.
  ]]></action>
  <verify><![CDATA[`git log -1 --format=%s` ends `(WP-35 syn:SD-3)`; `grep -c "(WP-35, syn:SD-3)" CHANGELOG.md` prints 1; `test -s <scratch>/35-02/detect.txt`; `test/test_corpus_ledger.py` 0 failed; `WP33_ONLY=S10` prints `Q3310-1 PASS` and `Q3310-2 PASS`; `python3 test/known_differences.py syn:SD-3` prints no `<file>:<line>` row and the hygiene command it prints reports 0 failed; `grep -c "Q3309-1 PASS" <scratch>/run_test_wp33_truth.log` prints 1; the body holds the `Ledger:` line; the grep for claude|anthropic prints 0.]]></verify>
  <done>p1() to p20() were drawn as twoway draws them in both modes, documented, closed, and committed once.</done>
</task>

## Section completion criteria

- `_dash_p_take`, `_dash_p_merge`, `_dash_p_key` exist, registered (R6); the takes table has no p rows; fixture committed and named by test_pnum.py; Q3502-1..3 PASS; `p21()` refused after every plot group's refusal; syn:SD-3's plain rows gone from ledger.tsv and from every `*_KNOWN` table (`python3 test/known_differences.py syn:SD-3` prints none; any key a ruling kept in its table's deliberate dict), the S09 guard at `Q3309-1 PASS`; one commit.

## Notes

- **Traps.** `p(` (plot-level whole-plot style) must not match. Graph-level p#() must be taken out BEFORE `_dash_parse_graph_opts` sees it, or it lands in the catch-all and the after-comma hint refuses p3(). The offset T counts twoway's plot numbers of earlier segments (D-35-02.e): use `_dash_pnum_t`, not `_dash_nplots`, which counts a ci fit once (`_nyv`, dash.ado:7163). A segment with `recast()` keeps its recast type's count; a ci type takes two numbers unless `nofit` (34-06, PIC-3, landed in WP-34).
- **Help paragraph owned (R3):** the p# sentence and its Differences line.
- **Merge rules:** R1, R5, R6 (three Mata functions; the two dash.ado calls on one new `_needed` continuation line), R7 (new fixture), R9 (one flip), R12 (no hot function of the list is edited beyond one call line and one `c_local` in `_dash_process_segment`, away from its per-type check block), R13 (GitNexus impact and detect-changes). No R8 entry (no twin).
- **Functions edited** (for the index's Owns cell): `_dash_p_take`, `_dash_p_merge`, `_dash_p_key` (new), `_dash_plot` (pre-pass, `_dash_pnum_t`, globals, the deferred `p21()` refusal above `if 0`_gac_rc'`), `_dash_process_segment` (one call, `_seg_pnums_out`), generated `_dash_tw_takes_tab`, scripts/gen_twoway_takes_table.py `rows()`, `_dash_require_mata`'s `_needed`.
- **35-07 builds on this.** 35-07 (batch 35.4) scans each `p<k>()` text for the words it refuses where the pair is merged into its plot, and gives its after-comma refusal beside this section's deferred `p21()` refusal.
