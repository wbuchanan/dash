# Section 10: Sub-option abbreviations (P1.19)

> Part of: WP-30 · Items: P1.19 (entry `P1.19`) · Risk: yellow · Batch: 4 (merge order S10, S11, S12; S10 first) · Depends on: 02 · Blocks: 18, 31, 38, 39, 51, 53, 56 · Tasks: 12, 1 commit · Case prefix: SA (SA-01..SA-15; TP-14a rows 34-39 in an existing case)

## Review amendments

- Fixed (major, M5 and register P1.19.1): the manifest scope says capitalised sub-options are refused as twoway refuses them, and P1.19.1 makes no exception for textboxes. Yet titles and axis titles were left named, as residual R-S10-1. Twoway's two parsers were read: `_fr_title_parse_and_log.ado:17-18,166-172` and `_gs_parse_and_log_axtitle.ado:15-33` both pass their rest to `_fr_sztextbox_parse_and_log` and `_fr_tbstyle_parse_and_log`, then refuse the leftover through FAKE. New TR-10.6a adds two Mata families, `title` and `axtitle`, to the same resolver, plus a `_dash_subopt_check title` pass. It refuses capitals, unknown spellings and in-copy duplicates with r(198) `option <shown> not allowed`, and an axis title's `prefix suffix` with twoway's words. The probes, SA-09/SA-15, BR-10.2, the CHANGELOG line and R-S10-1 (now narrowed to the title prefix+suffix message) follow.
- Fixed (major): `<scratch>` was this planning session's scratchpad path, which does not exist at execution. It is now the orchestrator's WP-30 scratch directory (index "Deltas").
- Fixed (minor): only the three Mata functions dash.ado calls get Public API header lines, because test_file_headers holds the Public API equal to `_needed`. The other seven are described as helpers (TR-10.6).
- Fixed (major, batch boundary): S10 and S12 both edited `_dash_plot` in batch 4, which A139 forbids. S10 now records through its own `_dash_axreq_clear`/`_dash_axreq_add` and keeps one 3-line hunk at the axis check (:5323-5325). S12's hunks are at :5540 and :5560-5568, more than 200 lines away. The remaining overlap is a marked Maintainer question in S12's Notes (recommendation: grant).
- Fixed (minor): the stub header is S01's `* ==== S10 P1.19: Sub-option abbreviations ====` (capital S, as the manifest name gives it).
- Checked: anchors at HEAD (`_dash_rep_cat` dash_parse.mata:4664 with its T, L, I, S families; the help paragraph :780-788 shared with S11; the twoway parser files and lines) match. Batch 4: S11 edits `_dash_parse_plot_opts`, `_dash_plot_opts_to_json`, `_dash_process_segment`, the folds, `_dash_opts_repeats` and `_dash_rep_reduce`, none of which S10 touches. S10's Mata edits stop at `_dash_rep_merge`, whose signature is kept. S12 also edits `_dash_plot` (its saving read and fold), and all three sections append to `_needed`. That overlap is the batch-4 exception below.
- Cross-file (notes file): index R3 lists S10 only under Axis and Display Options. Its help edits also touch Differences (:548-556, :615-632, :780-786) and Stata scheme support (:3352-3353, :3414-3415).
- (cross-file pass) 10-12 verify: added the key-deletion check `grep -c '^    "P1.19": "' $WT/test/test_tracking_documents.py` prints 0 (S01 TR-01.10.1).
- (cross-file pass) 10-12 verify: added the marker check `grep -c '<!-- WP-30 P1.19 -->' $WT/CHANGELOG.md` prints 0.
- The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:130 (P1.19): "This covers legend `c()`, `r()`, `lab()` and `posi()`; axis `labs()`, `glc()` and similar; and xline's `lc()`, `lp()` and `lw()`." GAPS2 B17 (GAPS2.md:528-540), B21 (:579-590) and B22 (:595-605) give the measured symptom: `legend(c(1))`, `r(1)`, `lab(1 "X")` and `posi(6)` are named and ignored; `labs(large)` is ignored; `xline(3000, lc(red) lp(dash) lw(thick))` "draws in the scheme default and names the three abbreviations". Re-measured at `c96facd` in both modes (research p1-19 §3, and the probes quoted under Evidence), the same root cause also:
- loses a label when copies merge: `legend(lab(1 "AA")) legend(lab(2 "BB"))` draws only BB (N2);
- reads the first copy where twoway reads the last: `ylabel(, labsize(small)) ylabel(, labs(large))` is small (N3);
- reads quoted label text as a sub-option: `ylabel(10 "labsize(large)" 20)` draws the labels large (N4);
- leaves textbox `s()` unread: `title("TT", s(small))` is named (N5; the WP-28 B3 table has wrong minimums);
- honours capitals twoway refuses: `legend(OFF)`, `LABSIZE(large)`, `LCOLOR(red)` (N6);
- draws both `cols()` and `rows()` where twoway takes `rows()` (N7);
- draws no legend for `legend(on off)` and no grid for `ylabel(, grid nogrid)`, where twoway's code lets the positive word win (N8, new here);
- silently drops `legend(c(red))`, `cols(red)` and `position(13)` (C3) where twoway refuses or notes.

**After this section**, dash reads the sub-options of `legend()`, of the axis label and tick options (`xlabel()`, `ylabel()`, `xtick()`, `ytick()`, `xmlabel()`, `ymlabel()`, `xmtick()`, `ymtick()`, their `2` forms and `zlabel()`), of `xline()`/`yline()` and of the textboxes exactly as twoway's own parsers read them. A spelling is matched in lower case only, from its minimum abbreviation to its full name, in the order twoway's parser stages try them (so `c()` is `cols()`, `la()` is `lalign()`, `s()` is `size()`, and a second `c()` after `cols()` falls through to `color()`). Copies merge sub-option by sub-option under the full name, the last copy winning; `rows()` beats `cols()`; within one copy a word beats its `no` form. Quoted label text is never read as a sub-option. In `legend()` and the axis-label family, input twoway refuses is refused with twoway's return code and words (M5; register P1.19.1, .2, .4): capitals (`option OFF not allowed`), spellings twoway does not accept (`option po() not allowed`), a sub-option given twice in one copy (`option cols() not allowed`), the wrong form (`option labs incorrectly specified`), a bad `cols()`/`rows()`/`holes()` (`cols() invalid -- invalid number`, r(121)) and a `label()` key that is no positive integer. Where twoway draws and notes (`position(13)`, `ring(x)`, `order(1 x)`), dash draws the default and prints twoway's note, once, from Stata, so both modes get it. Every reading is build-time only, so the saved page and the served app draw the same before and after any filter move.

**Why one section.** One shared canonicaliser and one staged resolver serve every family, one Mata twin keys the repeat merge and the refusals, and S18, S31, S38, S39, S51, S53 and S56 extend these tables. The item is one BUGS.md entry, `P1.19` (index manifest row 10).

**Test order and commit rule (rule 7, D1, index "per-entry cycle").** One cycle, one commit:
- **10-01** writes every regression test, runs it on the unmodified worktree and saves `<scratch>/10-P1.19-failure.txt`; it never commits.
- **10-02** writes the extractor and the fixture.
- **10-03 to 10-11** fix, flip and document.
- **10-12** closes the entry, replaces the two markers, runs the full suite through the queue and makes the one commit, subject ending `(WP-30 P1.19)`.

No test-only commit exists and no commit is red.

## Risk: [yellow] — a CRITICAL parser gains a new reading rule, and new M5 refusals stop do-files that ran before

**Why.** `_dash_parse_axis_spec` (CRITICAL, 8 impacted, 8 processes) stops reading values by regex over the whole text. Mata's repeat merge (`_dash_rep_subs`, reached from every repeated option) changes its keys. New refusals in `legend()` and the axis-label family stop commands that dash drew before.

**Risk factors.**
1. GitNexus (`gitnexus impact <s> -d upstream -r dash`, run 03oct2026):
   - CRITICAL: `_dash_parse_axis_spec`; `_parse_axis_angle` (its input changes, its body does not).
   - HIGH: `_dash_apply_tick_option`, `_dash_apply_z_options`, `_textbox_canon` (11), `_dash_apply_axis_spec` (one note line), `ServerAppBuilder._glyph_layer_lines` (copy lists).
   - LOW: `_dash_legend_parts`, `_dash_legend_unsupported`, `_dash_apply_legend`, `_dash_parse_legend_order`, `_dash_refline_instances`, `_dash_refline_draw`.
   - Called, never edited: `_dash_by_tokens`, `_dash_report_suboptions`, `_dash_subopt_name` (all CRITICAL) and `_dash_expand_numlist` (CRITICAL).
   - Not indexed (UNKNOWN, confirmed by grep): Mata `_dash_rep_subkey` (only caller `_dash_rep_subs`, dash_parse.mata:5672), `_dash_rep_subs` (callers `_dash_rep_merge` :5728, :5743), `_dash_rep_merge` (callers `_dash_rep_merge_locals` :5752 and `_dash_rep_reduce` :5831), `_dash_axreq_add`/`_dash_axreq_check` (dash.ado:5213, :5323-5324) and dash.ado `_dash_plot`.
   - The served app copies every renderer function by source, so the real blast radius is wider than the counts.
2. Two languages hold the same tables: the Python renderer and the Mata merge and refusals.
3. M5 refusals change what runs. The pinned HC1-15 and HC2-21i/j stop passing, and a user's `legend(garbage)` now stops the do-file.
4. Batch-3 drift: S08 (batch 3) has already edited `_dash_apply_legend` (step 7, `size()`), `_dash_apply_z_options` and `_dash_apply_axis_spec`'s `labsize` lines, and S06 has moved notes to its channel. Every anchor below is at `c96facd`; the executor re-greps at `batch-4-base`.
5. One help paragraph (dash.sthlp:780-788) is shared with batch partner S11.

**Mitigation.**
1. The CRITICAL edit is confined to the tail-token loop of `_dash_parse_axis_spec`. The spec keeps every key and gains `typed`. `_parse_axis_angle` is not edited: it is handed `angle(<arg>)` built from the resolved token. Its 7 pins in `test_graph_options.py:1199-1230` stay green.
2. Twin tests: SA-11 compares every Mata table row with the Python table, and SA-12 compares both resolvers on the fixture corpus plus 500 seeded random token lists.
3. Every refusal has a measured twoway twin in the fixture and an SA case asserting rc and words. Each newly refused form has a CHANGELOG "Changed behaviour" line. The scan of tests and help (Evidence, "Blast scan") found only the pins listed there.
4. The tasks name symbols; line numbers are re-derived (`grep -n`) at `batch-4-base`.
5. R3 applies to the shared paragraph: S10 rewrites only its own sentence, and S11, landing second, keeps it.

## Dependencies

- **Depends on: 02.** S02 provides the portable extractor form (the `DASH_REPO` stanza, A130; IR-8), which `scripts/extract_subopt_abbrev_truth.do` copies.
- **Batches 0-3 land first.** They provide:
  - S01: the BUGS.md entry `P1.19`, its `WP30_OPEN` key, the markers `<!-- WP-30 P1.19 -->` in "Changed behaviour" and "Fixed in WP-30", the stub block `* ==== S10 P1.19: … ====` in `test/test_wp30_truth.cscript`, and the map anchors `# WP-30 S10 (P1.19): Sub-option abbreviations (P1.19)`;
  - S03: `version 19` in every new ado program;
  - S06: the note channel;
  - S08: the size resolver behind `size()`/`labsize()`.
- **Blocks: 18, 31, 38, 39, 51, 53, 56.** They extend S10's tables and resolver:
  - S18 tests `for(%td)` through the axis-label table;
  - S31 wires the scale table into `_dash_scale_name` and draws `labc`, `tl`, `tp`, `nolab`, `noli`, `titleg`;
  - S38 adds the region family;
  - S39 adds the xline refusals through the refline twin;
  - S51 folds `t*` options onto these readers;
  - S53 reads `by(, legend())` through the legend table;
  - S56 refuses `text()` sub-options through the textbox table.
- **Parallel batch 4:** S11 (stylelists: `_dash_parse_plot_opts`, `_dash_plot_opts_to_json`, `_dash_process_segment`'s assembly block, the folds, `_dash_opts_repeats`, `_dash_rep_reduce`) and S12 (the `dash` dispatcher, browser deciders, saving blocks, `_dash_validate_path`, `_dash_launch_app`). S10 edits none of their functions. S10's Mata edits stop at `_dash_rep_merge`, whose signature it keeps, so S11's `_dash_rep_reduce` call at :5831 is untouched.

## Evidence

Anchors are at `c96facd` (dash_render.py 37,689 lines; dash.ado 8,487; dash_parse.mata 6,093; dash.sthlp 3,822). Symbols govern if lines drift.

### The renderer's readers

**Legend.** `_DASH_LEGEND_SUBOPTS` (dash_render.py:25823-25825) holds full names plus one alias:
```python
25823 _DASH_LEGEND_SUBOPTS = frozenset({
25824     "on", "off", "position", "pos", "ring", "order", "label", "lastlabel",
25825     "cols", "rows", "size"})
```
`_dash_legend_parts` (:21252) keys each token by `_dash_subopt_name`, which lower-cases (:25817-25819):
```python
21266     for tok in _dash_by_tokens(str(legend_opt or "").strip()):
21267         name = _dash_subopt_name(tok)
21268         if "(" in tok:
21269             arg = tok.split("(", 1)[1]
21270             arg = arg[:-1] if arg.endswith(")") else arg
21271             calls.append((name, arg))
```
`_dash_apply_legend` reads `("position", "pos")` and `ring` (:21550-21551), `cols`/`rows` (:21604-21615; both are applied when both are given), `size` (:21621) and the words (:21637-21638, off wins):
```python
21550     m_pos = _dash_legend_arg(_calls, ("position", "pos"), r"(\d+)")
21604     m_cols = _dash_legend_arg(_calls, ("cols",), r"(\d+)")
21637     forced_on = "on" in _words
21638     turned_off = "off" in _words
21641     show = not (turned_off or (n_keys < 2 and not forced_on))
```
`_dash_legend_unsupported` (:25834-25837) names every token whose lower-cased name is not in the set. `_DASH_LEGEND_LABEL_RE` (:25831) is `\s*(\d{1,6})(\s.*)`, so `label(+1 "A")` is not read. `_dash_parse_legend_order` (about :21290-21345) appends a bare word after a key as that key's text (`elif cur is not None and not closed: cur.append(word)`).

**Axis labels.** `_dash_parse_axis_spec` (:22602) names tail tokens by exact name, then reads values by regex over the WHOLE text, quoted labels included (:22636-22659):
```python
22639             if _nm and len(_nm) >= 3 and "valuelabel".startswith(_nm):
22646             if _nm not in ("format", "labsize", "angle", "grid", "nogrid"):
22649     out["angle"] = _parse_axis_angle(text)
22650     m = re.search(r"\bformat\s*\(\s*([^)]+?)\s*\)", text, re.I)
22653     m = re.search(r"\blabsize\s*\(\s*([^)]+?)\s*\)", text, re.I)
22656     if re.search(r"\bnogrid\b", text, re.I):
22658     elif re.search(r"\bgrid\b", text, re.I):
```
`_parse_axis_angle` (:4998-5024) is `re.search(r'\bangle\s*\(\s*([^)]+)\s*\)', raw, re.IGNORECASE)`. `_dash_apply_tick_option` (:22882) re-splits the tail with a regex that is not quote-aware and names `format`/`labsize`/`angle` by exact name (:22906-22910). `_dash_apply_z_options` (:26106) names honoured values under the canonical name, not as typed:
```python
26155             for _sub, _sv in (("format", spec.get("format")),
26156                               ("labsize", spec.get("labsize"))):
26158                     _bad.append(f"{_sub}({_sv})")
```
`_dash_apply_axis_spec`'s note names `labsize(...)` (:22843).

**xline/yline.** `_DASH_REFLINE_SUBOPTS = frozenset({"lcolor", "lpattern", "lwidth"})` (:26221). `_dash_refline_instances` (:26268) slices the argument by the full name's length, and `_dash_refline_draw`'s note names the canonical name (:26355):
```python
26289             name = _dash_subopt_name(tok)
26290             if "(" in tok and name in _DASH_REFLINE_SUBOPTS:
26291                 style[name] = tok[len(name) + 1:-1].strip() if tok.endswith(")") else ""
```

**Textboxes.** `_TEXTBOX_SUBOPTS` (:4639-4654) has the minimums `("size", "si")`, `("lstyle", "ls")`, `("alignment", "al")`, `("box", "box")` and `("nobox", "nobox")`. `_textbox_canon` (:4657-4669) lower-cases. Stata's parser has `Size`, `LSTyle`, `Alignment`, `Box` and `NOBox` (below).

**Served copies** (index R2), `ServerAppBuilder._glyph_layer_lines`:
- constants at 32931-32944, including `"_DASH_LEGEND_SUBOPTS"`, `"_DASH_TEXTBOX_DEFAULTS", "_DASH_SCALE_SUBOPTS",` (32934) and `"_DASH_REFLINE_SUBOPTS"`;
- functions at 33219-33221 (`_dash_legend_parts`, `_dash_legend_arg`, `_dash_apply_legend`), 33223 (`_parse_axis_angle`), 33230 (`_dash_parse_axis_spec`), 33369-33373 (`_dash_subopt_name`, `_dash_legend_unsupported`, `_textbox_canon`) and 33380-33383 (refline helpers).

`_dash_parse_legend_order` and `_dash_expand_numlist` are already listed (33178, 33236). Constants are copied by `repr` (33040-33056): tuples and frozensets copy as they are, and a compiled pattern is rebuilt (33049-33054).

### The Stata side

`_dash_rep_subkey` (dash_parse.mata:5632-5652) keys a merged word by its typed lower-case name:
```
5642     nm = strlower(strtrim(p ? substr(tok, 1, p - 1) : tok))
5643     if (strlen(nm) > 2 & substr(nm, 1, 2) == "no") nm = substr(nm, 3, .)
5644     if (nm == "pos") nm = "position"
5645     if (nm == "cols" | nm == "rows") nm = "cols|rows"
5647     if ((nm == "label" | nm == "lastlabel") & cat == "I" & p) {
```
`_dash_rep_subs(s1, s2, cat, drop)` (:5662) and `_dash_rep_merge(key, v1, v2)` (:5715) do not pass the option `key` down. Category "I" is also `graphregion`/`plotregion` (`_dash_rep_cat`, :4676), so keying "I" by the legend table would read a region's `c()` as `cols` (critic C1).

`_dash_axreq_add`/`_dash_axreq_check` (:5533-5630) record each x/y axis option from the RAW option text, with 9 columns, and refuse in twoway's order: side, family, segment, place, then within a row the second comma, the axis existence and the bad axis word.

`_dash_ax_parse` (:5391) already returns each option's sub-option `words`. dash.ado calls the axreq functions at `_dash_plot` :5061 (clear), :5213 (per segment) and :5323-5325 (after the comma, then the check). `_dash_check_legend` (dash.ado:1922-1951) refuses `top`/`bottom`/`left`/`right` with a hint line. It is called at :2743 (inside each segment's validation) and :5379 (graph level, after the axis check). `_needed` (dash.ado:244-255) ends with `_dash_axreq_clear _dash_axreq_add _dash_axreq_check`.

### twoway's parsers (StataNow 19.5, `/Applications/StataNow/ado/base/`)

The minimum is the capitalised prefix of each name.

**`_fr_legend_parse_and_log.ado`** (1.0.5 10sep2024) reads each copy in stages, each `syntax … *` passing what it does not take to the next:
1. `POSition RING STYle ORDER SHOWINDEX NOSPAN SPAN *` (:20-23; "accept last seen" across copies, :26-37).
2. Per copy, `_fr_area_parse_and_log … REGion` (:136), then `ParseLogOpts` (:197-212): `NODRAWView DRAWView ALL STYLEONLY HOLes(numlist integer >0 max=300) TEXTWidth XOFFSET(real) YOFFSET(real) STYle Rows(numlist integer >0 min=0 max=1) NOCOLFirst COLFirst Cols(numlist …) NOTEXTFirst TEXTFirst NOSTACked STACked ROWGap COLGap KEYGap SYMPlacement SYMXsize SYMYsize NOFORCESize FORCESize BMargin BPLACEment NOBEXpand BEXpand WIDTH HEIGHT NODRAW DRAW ON OFF *`.
3. That passes its rest to `_fr_tbstyle_parse_and_log` (:221).
4. Over all copies, the titles `R1title R2title L1title L2title T1title T2title B1title B2title NOTE CAPtion SUBtitle Title` (graph_g.class:282-301), each repeatable.
5. `LABel` (:350, :365, repeatable), then `LASTLABel` (:374, :389, repeatable).
6. `syntax [, FAKE_OPT_FOR_BETTER_MSG]` (:159) names the first word left.

In code order the negative word is tested first and the positive last, so the positive wins in one copy: `nodraw`/`off` then `draw`/`on` (:328-335), `nocolfirst`/`colfirst` (:260-263), and likewise `textfirst`, `stacked`, `forcesize` and `bexpand` (:266-313).

**`_fr_tbstyle_parse_and_log.ado`** (1.0.2 11jul2017) :11-24: `TSTYle ANGLE Size Color Justification Alignment Margin LINEGAP NOBox Box BMargin PLACEment BFColor FColor BColor BLSTyle BLWidth BLColor BLPattern BLAlign LSTyle LWidth LColor LPattern LAlign ORIENTation *`.

**Titles.** `_fr_title_parse_and_log.ado` (1.0.6) :17-18 reads `NOSPAN SPAN PREFIX SUFFIX POSition RING STYle *`, then `_fr_sztextbox_parse_and_log.ado` (1.1.0) :10-11 `WIDTH HEIGHT NOASTextbox NOBEXpand ASTextbox BEXpand *`, then the tbstyle list.

**`_gs_parse_and_log_tickset.ado`** (1.1.1 05nov2024):
- :18 `ADD CUSTOM noRESCALE *`;
- `Options` :265-283, with NO `*`: `NOTICKs TICKs NOLABels LABELS NOSHOWLABels SHOWLABels NOVALuelabels VALuelabels ANGle ALTernate ALTGAP STYle TSTYle TLength TPosition LABGAP TLSTYle TLWidth TLColor TLPattern LABSTYle LABSize LABColor LABJustification LABAlignment NOPGMGRID PGMGRID NOGrid Grid GStyle NOGEXtend GEXtend NOGMIN GMIN NOGMAX GMAX GLStyle GLWidth GLColor GLPattern FORmat AXis labelminlen(integer -1) labelkeepleadingzero CUSTOM`;
- the positive word wins: `noticks`/`ticks` :321-324, `novaluelabels`/`valuelabels` :304-307, `nolabels`/`labels` :327-330, `nogextend`/`gextend` :357-361, `nopgmgrid` :390-394, `nogrid`/`grid` :398-402.

**`_gs_parse_and_log_lines.ado`** (1.1.6) :18-23, no `*`: `STyle NOEXtend EXtend LSTyle LColor LWidth LPattern LAlign AXis`.

**`_gs_parse_and_log_axoptions.ado`** (1.0.4):
- :19-32 `NOLOG LOG NOATANH ATANH NOLOGIT LOGIT NOLOG1m LOG1m ALTernate STYle TITLEGap OUTERGap NOLIne LIne NOEXtend EXtend NOFEXtend FEXtend LSTyle LColor LWidth LPattern ON OFF NOFILLspace FILLspace RING(real) NOREVerse REVerse AXis *`;
- then a repeated `Range` (:46, :56);
- then FAKE (:74).

### Measured twoway truth (StataNow 19.5, born 12 Aug 2026, scheme stcolor)

Probes run 03oct2026 with `scripts/stata_slot.sh <scratch>/wp30/s10-probe probeN.do`. Each probe is `capture noisily <cmd> name(zq, replace)`, with rc and the error line read from the log. Bases:
- `L2` = `twoway (scatter mpg weight) (lfit mpg weight),`
- `S1` = `twoway scatter mpg weight,`
- `K3` = `twoway (scatter mpg weight) (lfit mpg weight) (scatter price weight),`

Research p1-19 §4 holds the drawn facts (legend texts at x 4466 y 1401/1558, 112.56 px; `large` 157.44; `small` 89.94).

**Legend refusals:**
```
c(red) r(121) cols() invalid -- invalid number       po(9)  r(198) option po() not allowed
rin(0) pos(5) option rin() not allowed               ord(2 1) / o(2 1)  option ord() / o() not allowed
lastl(1 "XX") option lastl() not allowed             of     option of not allowed
OFF  option OFF not allowed     POS(9) option POS() not allowed     Pos(9) option Pos() not allowed
SIZE(large) option SIZE() not allowed               Cols(1) option Cols() not allowed
c(2) cols(1) option cols() not allowed              pos(9) position(6) option position() not allowed
size(large) size(small) option size() not allowed   size(large) s(small) option s() not allowed
order(1 2) order(2 1) option order() not allowed    on on   option on not allowed
holes(1) holes(2) option holes() not allowed        rows(1) r(2) option r() not allowed
ring(0) pos(5) ring(1) option ring() not allowed    c(2) c(3) c(4) option c() not allowed
cols  option cols not allowed     on(1) option on() not allowed     garbage option garbage not allowed
cols(0) r(125) cols() invalid -- invalid number, outside of allowed range    cols(-1) r(125) (same)
cols(1.5) / cols(0.5) r(126) cols() invalid -- invalid number, noninteger value
cols(1 2) / cols(1/3) / cols(1(1)3) r(123) cols() invalid -- single number required
cols(.) / cols(.a) / cols(1e400) r(127) cols() invalid -- invalid number, missing not allowed
cols(1 x) / cols(x 1) r(121)      rows(x) r(121) rows() invalid -- invalid number   r(0) r(125) rows() invalid -- …
holes(0) r(125) holes() invalid -- invalid numlist has elements outside of allowed range
holes(1.5) r(126) holes() invalid -- invalid numlist has noninteger elements
holes(1/301) r(123) holes() invalid -- invalid numlist has too many elements
xoffset(x) / xoffset() / yoffset(1 2) r(198) option xoffset() / yoffset() not allowed
label(x "A") r(198) x not an integer in option label()       label(1.5 "A") 1.5 not an integer in option label()
label("A") A not an integer in option label()   label(1e0 "A") 1e0 not …   label(1x "A") 1x not …
label(0 "A") / lastlabel(0 "A") r(198) legend.labels[0] invalid name   label(-1 "A") legend.labels[-1] invalid name
lastlab(x "A") / lastlabel("A") x / A not an integer in option lastlabel()
```

**Legend, accepted (rc 0):**
- `cols(1) c(red)` and `c(1) c(red)`: one column, key text #ff0000 (the second `c()` is `color()`).
- `c(1) c(2)`: one column, with the note `(note:  named style 2 not found in class color, default attributes used)`.
- `style(foreground) sty(foreground)`: the second is ParseLogOpts' `STYle`.
- `region(fcolor(red)) reg(lcolor(blue))`: region is repeatable.
- `title("TA") title("TB")`: draws TB.
- `label(1 "AA") lab(1 "BB")`: draws BB.
- `cols(2/2)` and `cols(+2)`: two columns.
- `cols()`, `holes()`, `label()`, `label(01 "A")` (key 1 = A), `label(+1 "A")` (key 1 = A), `pos( 9 )` (left), `ring(-1)` and `ring(1.5)`: accepted.

**Legend notes (rc 0, default drawn):**
- `pos(x)`, `pos(13)`, `pos(-1)`, `pos(06)`, `pos(3.0)`: `(note:  named style <v> not found in class clockdir, default attributes used)`, printed twice.
- `ring(x)`: `(note:  named style x not found in class gridringstyle, default attributes used)` and `(note:  gridringstyle not found in scheme, default attributes used)`.
- `order(x)`, `order(1 x)`, `order(x 1)`, `order(1 "a" x)`, `order(1e0)`: `x not an integer, option order() ignored` (`1e0 …`), and the order is ignored.
- `order(+1 2)` draws keys 1 and 2. `order(-2 1)` draws key 1 alone, silently.
- `legend(pos(x)) legend(pos(3))` and `legend(order(x)) legend(order(2 1))`: silent (only the last copy is applied).

**Legend precedence:**
- `on off`, `off on` (one key and two): a legend is drawn.
- `legend(on) legend(off)`: none.
- `legend(off) legend(on)`: drawn.
- `legend(cols(3) rows(1))` and `legend(rows(1) cols(2))` on K3: one row. Every copy order of rows/cols gives the rows (research k_*).
- `legend(lab(1 "AA")) legend(lab(2 "BB"))`: AA and BB. `legend(c(2)) legend(cols(1))`: one column (last copy).

**Axis-label refusals (S1 unless stated):**
```
ylabel(, lab(large)) option lab() not allowed     LABS(large) option LABS() not allowed   LABSize(large) option LABSize() not allowed
a(0) / an(45) / f(%9.1f) / fo(…) / gl(red)  option a() / an() / f() / fo() / gl() not allowed
nola  option nola not allowed   no  option no not allowed   xlabel(0 1, va) (mpg foreign) option va not allowed
labs  option labs incorrectly specified    labsize  option labsize incorrectly specified
nog(1) option nog() incorrectly specified   nogrid(1) option nogrid() incorrectly specified
angle(45) ang(0) option ang() not allowed   labsize(large) labsize(small) option labsize() not allowed
format(%9.1f) for(%9.2f) option for() not allowed   glc(red) glcolor(blue) option glcolor() not allowed
labs(large) bogus / bogus labs(large) labs(small)  option bogus not allowed
labs(large) labs  option labs not allowed   labs labs(large)  option labs incorrectly specified
labs(large) LABSIZE(small)  option LABSIZE() not allowed
ytick(, a(45)) / ymlabel(, a(45)) / colorvar(price) zlabel(, a(45))  option a() not allowed
colorvar(price) zlabel(, labs(large) labs(small))  option labs() not allowed
labelminlen(x) / (1.5) / ()  option labelminlen() incorrectly specified
```
Accepted:
- `labs`/`labsi(large)`, `ang`, `form`/`for`, `nogr`/`nog`, `g`/`gr`/`gri`, `glc`, `labc`, `nolab`, `notick`, `val`/`valuelabel`/`valuelabels`;
- `ytick(, labs(large))`, `zlabel(, labs(large))`;
- `nogr nogrid` (grid gone: a repeated word is accepted in a stage with no `*`);
- `grid nogrid` and `nogrid grid` (grid drawn, 205 hlines vs 5);
- `valuelabel novaluelabel`.

`ylabel(10 "labsize(large)" 20)` keeps the label text at 112.56.

**Refusal order** (each message shows which came first):
```
legend(po(9)) ylabel(, a(45)) | ylabel(, a(45)) legend(po(9))      option po() not allowed  (legend before axes)
legend(po(9)) ylabel(, axis(3)) | reversed                          option po() not allowed
xlabel(, a(45)) ylabel(, axis(3)) | reversed                        option a() not allowed   (x side first)
xlabel(, f(1)) ylabel(, axis(3))                                    option f() not allowed
ylabel(, axis(3) a(45))                    ylabels(, axis(3) a(45)) not allowed, yaxis3 does not exist
ytick(, a(45)) ylabel(, f(1)) | reversed                            option f() not allowed   (labels before ticks)
ymlabel(, a(45)) ytick(, f(1))                                      option a() not allowed   (mlabels before ticks)
ylabel(, f(1)) xtick(, a(45))                                       option a() not allowed   (x before y)
colorvar(price) zlabel(, a(45)) ylabel(, f(1)) | reversed           option f() not allowed   (z after x/y)
colorvar(price) zlabel(, a(45)) xline(3000, l(red))                 option l() not allowed
colorvar(price) zlabel(, a(45)) legend(po(9))                       option po() not allowed
legend(c(red) po(9)) | legend(pos(9) position(6) c(red))            cols() invalid -- invalid number  (value error before the leftover)
legend(po(9) label(x "A"))                                          x not an integer in option label()
legend(label(x "A") cols(red))                                      cols() invalid -- invalid number
legend(rows(x)) legend(cols(y)) | legend(po(9)) legend(c(red))      rows() / cols() invalid -- invalid number
legend(cols(x) rows(y)) | legend(rows(y) cols(x))                   rows() invalid -- invalid number (declaration order)
legend(holes(x) cols(y))                                            holes() invalid -- invalid numlist
legend(lastlabel(y "b") label(x "a"))                               x not an integer in option label()
```
- A long name is echoed whole: `legend(<80 a's>(1))` gives `option aaaa…() not allowed`.
- `legend(label(2147483648 "A"))` made Stata allocate until the OS killed it, so dash keeps its 6-digit key bound.

**xline, titles, scale:**
- `xline(3000, lc(red) lp(dash) lw(thick))` = the full names: #ff0000, width 25.92, dashed. `lcol`, `lpatte`, `lwid` are accepted. `l()`, `c()`, `color()`, `ls()`, `LC()` give r(198) `option … not allowed`. `xline(3000, lc(red)) xline(4000, lcolor(blue))` draws red and blue.
- `title("TT", s(small))` = `size(small)`: 89.94. `b`, `nob`, `a(top)` and `style(foreground)` are accepted. `ls(foreground)`, `SIZE(small)` and `size(small) s(large)` give `option ls() / SIZE() / s() not allowed`.
- `xscale(r(0 1000)) xscale(range(5000 6000))`: rc 0.

### dash at HEAD (measured)

`python3 <scratch>/wp30/s10-probe/m2.py` (saved renderer through `test_axis_options._fig_with_gopts`, s2color):
```
legend(on off)  one key: visible=False                 legend(position(13)): side right, no note
legend(pos(06)): side below                            legend(cols(red)): ncols 2, no note
legend(OFF): hidden, no note                           legend(cols(3) rows(1)): ncols 3 nrows 1
legend(cols(1) c(red)): ncols 1, c(red) named          ylabel(0(10)40, grid nogrid): grid None
ylabel(10 "labsize(large)" 20): font 15px              ylabel(…, LABSIZE(large)): 15px, no note
ylabel(…, labs(large) labsize(small)): 7px, labs(large) named
```

Research p1-19 §3 shows the rest, served identical:
- `legend(c(1))` gives ncols 2 and is named;
- `legend(lab(1 "X"))` leaves the key unchanged;
- `posi(6)` is named;
- `labs(large)` is 10pt and named;
- `xline(…, lc lp lw)` gives `#c10534 [] 1.5` and is named;
- `title("TT", s(small))` is 14pt and named.

Through Stata (`dash_merge.do`), `legend(lab(1 "AA")) legend(lab(2 "BB"))` names only `lab(2 "BB")`: key 1 is lost in Mata (N2).

### Blast scan of tests and help (prototype resolver, `<scratch>/wp30/s10-proto/scan.py`)

Every single-line `legend(…)` and axis-label body in `test/*.py`, `test/*.cscript`, `test/*.do` and dash.sthlp was run through a prototype of the staged resolver. New refusals appear only for:
- `legend(garbage)`: dash.sthlp:785; `test_help_claims_1.cscript` HC1-15 (:818-849); `test_help_claims_2.cscript` HC2-21i/j (:633-634). The pytest twins `test_help_claims_1.py::test_legend_garbage_is_named_in_both_modes` and `test_help_claims_2.py::TestAnUnknownSubOptionWordIsNamedAndDrawnWithout` are renderer-level and stay green.
- `test_twoway_option_parity.cscript` rows with `AXIS(2)`, two axis words or a second comma. `_dash_axreq_check` already refuses these with the same words, earlier in the row.

### Tests that pin today's behaviour (flip, never delete)

- `test/test_help_claims_7.py::TestTheNewHelpers::test_dash_legend_parts` (:1142-1148). It expects `words == {"off"}` from `OFF` and `("pos", "6")`; it becomes `set()` and `("position", "6", "pos")` (capitals are unread; names are canonical with the typed name kept).
- `test/test_textbox_grammar.py::TestTheTable::test_every_prefix` (:168-195). Its `_TABLE` has the wrong minimums `si`, `ls`, `al`, `box`, `nobox`, and its bogus list holds `s` and `b`. Both are corrected to Stata's parser.
- `test/test_help_claims_1.cscript` HC1-15: `legend(garbage)` is now r(198) `option garbage not allowed`, with `xscale(bogus)` still named, in a separate command.
- `test/test_help_claims_2.cscript` HC2-21i (`legend(garbage)` → 198 with twoway's words) and HC2-21j (nothing is registered).
- Not flipped, re-checked green:
  - `test_help_claims_7.py::TestTheNewHelpers::test_dash_legend_arg`: first-match semantics are kept, and its 2-tuples still unpack;
  - `test_textbox_grammar.py::TestTheTable::test_parse_canonicalises` (`si` is still `size`);
  - `TestForeignWordsAreNamed::test_colour_and_style`;
  - `test_axis_options.py::TestRepeatedReferenceLines::test_the_instances` (full names add no `_typed` key);
  - TP-14a row 26 (`legend(cols(1)) legend(rows(1))` = `legend(rows(1))`);
  - `test_value_labels_drawn.py::TestValueLabelsOnAxes::test_val_is_the_minimum_abbreviation` (`va` stays unread);
  - `test_mode_parity.py` `_MUST_WARN` rows "legend with an unimplemented sub-option", "xline with an unimplemented sub-option", "xlabel with an unimplemented sub-option" and "graph title with sub-options" (`box` is still named).

## User stories

- **US-10.1** As a twoway user, I want `legend(c(2) r(1) lab(1 "A") posi(6) s(small) lastlab(2 "Z"))` to draw what the full names draw, so that my do-files work unchanged.
- **US-10.2** As a twoway user, I want `ylabel(, labs(small) ang(0) for(%9.1f) nog)`, `xlabel(0 1, valuelabels)` and `xtick(, …)`/`zlabel(, …)` spellings read as twoway reads them, with quoted label text kept as text.
- **US-10.3** As a twoway user, I want `xline(5, lc(red) lp(dash) lw(thick))` and `title("T", s(small))` drawn as their full names.
- **US-10.4** As a do-file author, I want a capitalised or misspelt sub-option, or one given twice in one `legend()` or axis-label option, refused with twoway's message and return code, so that a mistake is reported, not silently ignored.
- **US-10.5** As a do-file author, I want repeated `legend()` and axis-label copies merged as twoway merges them (the last copy wins; `rows()` beats `cols()`; every `label()` kept).
- **US-10.6** As a dashboard viewer, I want the saved page and the served app to draw these options the same, before and after a filter move.

## Business requirements

- **BR-10.1** In `legend()`, the axis label and tick options, `xline()`/`yline()` and the textboxes, every spelling from twoway's minimum to the full name draws exactly what the full name draws, in both modes, with no note. Abbreviations of sub-options dash does not draw are named as typed.
- **BR-10.2** Names match in lower case only. In `legend()` and the axis-label family, a capitalised name, a spelling twoway refuses, a second copy in one option, the wrong form, a bad `cols()`/`rows()`/`holes()` and a `label()`/`lastlabel()` key that is no positive integer are refused with twoway's return code and first line, in twoway's order. In the titles (`title()`, `subtitle()`, `note()`, `caption()`, the `t1title()`..`r2title()` family) and the axis titles (`xtitle()`, `ytitle()`, their `2` forms, `ztitle()`), a capitalised name, a spelling twoway does not accept and a second copy in one option are refused r(198) `option <shown> not allowed` (TR-10.6a), and an axis title's `prefix suffix` is refused r(198) `options prefix and suffix may not be combined`. In `xline()`/`yline()` a capitalised name is named, never applied (refusal: S39).
- **BR-10.3** Repeated copies merge by full name, the last copy winning. `rows()` beats `cols()` in and across copies, and within one copy a word beats its `no` form (`on` beats `off`; `grid` beats `nogrid`). Every `label()` key survives the merge.
- **BR-10.4** Quoted label text is never read as a sub-option.
- **BR-10.5** Where twoway draws the default and notes (`position()` outside 0-12, a non-numeric `ring()`, a non-integer `order()` word in the last copy), dash draws the default and prints twoway's note once, in both modes. Where twoway is silent (`ring(-1)`, `order(-2 1)`), dash is silent (M6).
- **BR-10.6** A note names the sub-option as the user typed it (register P1.19.5).
- **BR-10.7** Nothing a filter move does changes these readings, in either mode.

## Technical requirements

### TR-10.1 The tables (dash_render.py, beside `_dash_subopt_name` at :25817)

Each row is `(full, minimum, stage, kind, star, check)`:
- `stage`: int, parse order;
- `kind`: `"w"` word, `"a"` argument taken once per stage, `"r"` argument repeatable;
- `star`: bool, the stage's `syntax` has `*`;
- `check`: `""`, `"N1"` (`numlist integer >0 min=0 max=1`), `"NL"` (`numlist integer >0 max=300`), `"R"` (a real literal) or `"I"` (an integer literal).

Rows are in each parser's declaration order, with a comment citing the file:line above. The tables:
- `_DASH_TBSTYLE_ROWS`: the 26 tbstyle rows `(full, minimum, kind, check)`, used at import only:
  - argument rows: tstyle/tsty, angle/angle, size/s, color/c, justification/j, alignment/a, margin/m, linegap/linegap, bmargin/bm, placement/place, bfcolor/bfc, fcolor/fc, bcolor/bc, blstyle/blst, blwidth/blw, blcolor/blc, blpattern/blp, blalign/bla, lstyle/lst, lwidth/lw, lcolor/lc, lpattern/lp, lalign/la, orientation/orient;
  - word rows: nobox/nob, box/b.
- `_DASH_LEGEND_SUBOPT_TABLE`, seven starred stages:
  1. position/pos a, ring/ring a, style/sty a, order/order a, showindex w, nospan w, span w;
  2. region/reg r;
  3. nodrawview/nodrawv w, drawview/draww w, all w, styleonly w, holes/hol a NL, textwidth/textw a, xoffset a R, yoffset a R, style/sty a, rows/r a N1, nocolfirst/nocolf w, colfirst/colf w, cols/c a N1, notextfirst/notextf w, textfirst/textf w, nostacked/nostac w, stacked/stac w, rowgap/rowg a, colgap/colg a, keygap/keyg a, symplacement/symp a, symxsize/symx a, symysize/symy a, noforcesize/noforces w, forcesize/forces w, bmargin/bm a, bplacement/bplace a, nobexpand/nobex w, bexpand/bex w, width a, height a, nodraw w, draw w, on w, off w;
  4. the tbstyle rows;
  5. r1title/r r, r2title/r r, l1title/l r, l2title/l r, t1title/t r, t2title/t r, b1title/b r, b2title/b r, note/note r, caption/cap r, subtitle/sub r, title/t r;
  6. label/lab r;
  7. lastlabel/lastlab r.

  The fixture probes `l_t_title`, `l_l_title` and `l_b_title` pin stage 5's minimums. If twoway refuses one, the minimum includes the digit (`t1`), and the row follows the fixture.
- `_DASH_AXLABEL_SUBOPT_TABLE`:
  - stage 1 (starred): add w, custom w, norescale w;
  - stage 2 (`star=False`): noticks/notick w, ticks/tick w, nolabels/nolab w, labels w, noshowlabels/noshowlab w, showlabels/showlab w, novaluelabels/noval w, valuelabels/val w, angle/ang a, alternate/alt w, altgap a, style/sty a, tstyle/tsty a, tlength/tl a, tposition/tp a, labgap a, tlstyle/tlsty a, tlwidth/tlw a, tlcolor/tlc a, tlpattern/tlp a, labstyle/labsty a, labsize/labs a, labcolor/labc a, labjustification/labj a, labalignment/laba a, nopgmgrid w, pgmgrid w, nogrid/nog w, grid/g w, gstyle/gs a, nogextend/nogex w, gextend/gex w, nogmin w, gmin w, nogmax w, gmax w, glstyle/gls a, glwidth/glw a, glcolor/glc a, glpattern/glp a, format/for a, axis/ax a, labelminlen a I, labelkeepleadingzero w, custom w.
- `_DASH_REFLINE_SUBOPT_TABLE`, one stage, `star=False`: style/st, noextend/noex w, extend/ex w, lstyle/lst, lcolor/lc, lwidth/lw, lpattern/lp, lalign/la, axis/ax.
- `_DASH_AXSCALE_SUBOPT_TABLE`:
  - stage 1 (starred): nolog w, log w, noatanh w, atanh w, nologit w, logit w, nolog1m/nolog1 w, log1m/log1 w, alternate/alt w, style/sty a, titlegap/titleg a, outergap/outerg a, noline/noli w, line/li w, noextend/noex w, extend/ex w, nofextend/nofex w, fextend/fex w, lstyle/lst a, lcolor/lc a, lwidth/lw a, lpattern/lp a, on w, off w, nofillspace/nofill w, fillspace/fill w, ring a R, noreverse/norev w, reverse/rev w, axis/ax a;
  - stage 2 (starred): range/r r.

  S10 uses it only for Mata merge keys. S31 wires it into `_dash_scale_name` and re-measures its minimums before refusing with it.
- `_DASH_AXLABEL_HONOURED = frozenset({"format", "labsize", "angle", "grid", "nogrid", "valuelabels", "novaluelabels", "norescale"})`.
- `_DASH_LEGEND_SUBOPTS` loses `"pos"` (names are canonical).
- `_DASH_SUBOPT_REAL_RE = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")` and `_DASH_SUBOPT_INT_RE = re.compile(r"[+-]?\d+")`, used with `fullmatch` on the stripped argument. Python's `float()` would accept `1_0`, `inf` and `nan`, so it is not used.
- `_TEXTBOX_SUBOPTS` (:4639) is corrected in place:
  - `("size","s")`, `("lstyle","lst")`, `("alignment","a")`, `("box","b")`, `("nobox","nob")`;
  - add `("angle","angle")`, `("bfcolor","bfc")`, `("blstyle","blst")`, `("blwidth","blw")`, `("blcolor","blc")`, `("blpattern","blp")`, `("blalign","bla")`, `("nobexpand","nobex")`, `("astextbox","ast")`, `("noastextbox","noast")`, `("nospan","nospan")`;
  - `colour` and `style` stay out (their comment is kept).
  - The comment cites the four parsers above in place of the help files.
  - `_textbox_canon` returns `None` for a name that is not all lower case and otherwise keeps its first-match rule.

### TR-10.2 The canonicaliser and the resolver (dash_render.py, new, after `_dash_subopt_name`)

**`_dash_subopt_canon(name, table)`.** `name` is the typed name, the text before `(`, stripped. It returns `None` unless `name` is non-empty and equals `name.lower()`. Otherwise it returns the `full` of the first row (in table order) with `len(name) >= len(minimum)` and `full.startswith(name)`, else `None`.

**`_dash_subopt_resolve(copies, table)`.** It returns `(names, problem)` for twoway's reading of one option's sub-option words, copy by copy.
- *Input.* `copies` is a list of token lists, one per copy in command order. A `str` or a flat token list is one copy.
- *Output.* `names[c][i]` is the full name or `None`. `problem` is `None` or `(c, i, 198, message)`.
- *Algorithm.*
  1. For each stage in ascending order, for each copy, for each still-unnamed token in written order:
     - take the first row of that stage matching `_dash_subopt_canon`'s rule;
     - a token mismatches its row when the row is `w` and the token has `(`, when the row is `a`/`r` and it has none, or when the check is `R`/`I` and the argument fails `_DASH_SUBOPT_REAL_RE`/`_DASH_SUBOPT_INT_RE`.
  2. In a starred stage, an unmatched, mismatched or repeated-`a`/`w` token is left for the next stage.
  3. In an unstarred stage the first such token is the problem, tested in this order:
     - an `a` row already taken → `option <shown> not allowed`;
     - a mismatch → `option <shown> incorrectly specified`;
     - no row → `option <shown> not allowed`.

     A repeated `w` is accepted there.
  4. After the last stage, the first unnamed token (copy order, then written order) is the problem: `option <shown> not allowed`.

  `<shown>` is the typed name, plus `()` when the token has `(`.
- *Cost.* Linear in tokens × rows. No regex over the whole text: tokens come from `_dash_by_tokens`, the quote-aware splitter. A copy of 20,000 tokens resolves in under 2 s.

### TR-10.3 Legend in the renderer

1. `_dash_legend_parts(legend_opt)` resolves the `_dash_by_tokens` tokens as one copy and returns `(words, calls)`:
   - `words` is the set of full names of word tokens;
   - `calls` is a list of `(full, arg, typed_name)` for argument tokens with a name;
   - unnamed tokens are omitted.
2. `_dash_legend_unsupported(legend_opt)` returns, as typed, each token whose name is `None` or not in `_DASH_LEGEND_SUBOPTS`.
3. `_dash_legend_arg` keeps its first-match rule (a resolved copy holds one of each `a` option), iterating `for name, arg, *_ in calls`.
4. `_dash_apply_legend`:
   - **Position.** It reads `("position",)` with pattern `([0-9]|1[0-2])`, fullmatched on the stripped argument, so `13`, `06` and `3.0` are absent: the scheme default, silent in the renderer, with Stata noting them (TR-10.6).
   - **Columns and rows.** `cols()`/`rows()` are read with `_dash_expand_numlist(arg.split(), limit=2)` and used only when it gives exactly one value that is a positive integer. When `rows` is given, `nrows` is set and `ncols="auto"`; otherwise, when `cols` is given, `ncols` is set and `nrows="auto"` (N7).
   - **On and off.** `turned_off = "off" in _words and "on" not in _words` (N8).
   - **Size note.** The note uses the size call's typed name, `legend(<typed>)` (A64, on S08's line).
5. `_DASH_LEGEND_LABEL_RE` becomes `\s*\+?(\d{1,6})(\s.*)` (`label(+1 "A")`).
6. `_dash_parse_legend_order`:
   - a bare word fullmatching `\+?[0-9]+` is a key, kept only when it has at most 6 digits;
   - `-[0-9]+` is a key that never exists (`cur = None`);
   - `-` is a gap;
   - any other bare word makes the function return `[]`, as twoway ignores the whole `order()`.

### TR-10.4 Axis labels in the renderer

`_dash_parse_axis_spec(raw)`:
- It keeps the head/tail split (`_dash_axis_head_split`) and resolves only the tail's `_dash_by_tokens` tokens as one copy with `_DASH_AXLABEL_SUBOPT_TABLE` (N4: label text is never searched). All four whole-text regexes (:22649-22659) are deleted.
- For each named token in `_DASH_AXLABEL_HONOURED`, the argument is the text between the first `(` and the final `)`, stripped:
  - `format` → `out["format"]`;
  - `labsize` → `out["labsize"]`;
  - `angle` → `_parse_axis_angle("angle(" + arg + ")")`;
  - `norescale` → True.
- Grid: `grid` if the copy holds `grid`, else `nogrid` → False (N8). Value labels: `valuelabels` → True, unless only `novaluelabels` is present.
- Every other token, named or not, goes to `out["unsupported"]` as typed.
- A new key `out["typed"]` maps each honoured full name to its token as typed. It is `{}` when there is no tail.

`_dash_apply_tick_option` takes its named extras from `spec["typed"]` for `format`/`labsize`/`angle` and drops its own tail regex (:22906-22910). `_dash_apply_z_options` names `spec["typed"]` tokens for `format`, `labsize`, `angle` and `grid`/`nogrid` instead of `f"{_sub}({_sv})"` (:26155-26162). `_dash_apply_axis_spec`'s `labsize` note names `spec.get("typed", {}).get("labsize", "labsize(%s)" % spec["labsize"])`. `_parse_axis_angle` is not edited.

### TR-10.5 xline/yline and textboxes in the renderer

`_dash_refline_instances`:
- canonicalises each `(`-token's typed name with `_dash_subopt_canon(name, _DASH_REFLINE_SUBOPT_TABLE)`;
- keeps it when the name is in `_DASH_REFLINE_SUBOPTS`, with the argument from `tok.split("(", 1)[1]` less a final `)`, stripped;
- when the typed name differs from the full one, records `style.setdefault("_typed", {})[full] = typed`. Full spellings add no key, so `test_the_instances` stays green.

`_dash_refline_draw` names `f"{opt}({style.get('_typed', {}).get(sub, sub)})"` in its note. A capitalised `LCOLOR()` is named, not drawn; S39 refuses it.

### TR-10.6 Stata: Mata twins, merge keys and refusals (dash_parse.mata, new functions after `_dash_axreq_check`, :5630)

**Tables and resolver.**
- `string matrix _dash_so_rows(string scalar fam)` returns the rows of `"legend"`, `"axlabel"`, `"axscale"`, `"refline"` or `"textbox"`. Its 6 columns are `full min stage kind star check`, with `star` `"1"`/`"0"`, row for row equal to TR-10.1. `"textbox"` is `_TEXTBOX_SUBOPTS` as `(full, min, "1", "a", "1", "")`.
- `_dash_so_canon(name, fam)` and `real scalar _dash_so_resolve(string rowvector toks, real rowvector cid, string scalar fam, string rowvector names, string scalar msg, real scalar at)` are TR-10.2's twins. They use no `regexm` (it follows the caller's version): byte loops, with `_dash_so_isnum(s, int)` for R/I. On a problem they return 198, with `msg` the message and `at` the token's index; otherwise they return 0.

**Merge keys.** `_dash_so_family(key)` maps a merge key to its table:
- `legend` → `"legend"`;
- the L category of `_dash_rep_cat` → `"axlabel"`;
- S → `"axscale"`;
- T → `"textbox"`;
- else `""`: regions (S38's), by, text and lines.

`_dash_rep_merge(key, v1, v2)` keeps its signature and passes `key` to `_dash_rep_subs(s1, s2, cat, drop, key)` at both calls (:5728, :5743).

In `_dash_rep_subs`, when `_dash_so_family(key) != ""`:
1. Resolve s1's tokens as copy 1 and s2's as copy 2 (C1).
2. Within each side, for the legend and axlabel families, drop a `noX` word whose `X` word is on the same side, and drop `off` when `on` is on the same side (N8, the code order above).
3. Key each word with `_dash_rep_subkey(tok, cat, full)`:
   - the full name when resolved, else the lower-case typed name;
   - then `noX` → `X`, `on|off`;
   - `label #`/`lastlabel #` from the resolved name in category I (N2);
   - `cols` and `rows` are separate keys.
4. Keep the last word of each key.
5. For the legend, drop every `cols` word when a `rows` word was kept (C2; TP-14a row 26 stays green).
6. A kept word whose resolved full name differs from `_dash_so_canon` of its typed name alone (a fall-through such as the second `c()` = `color()`) is written as `full(arg)`, so the renderer's resolution of the merged text cannot read it as another option.

The `S` range union and the `drop` list are unchanged.

**Refusals.**
- `_dash_axreq_clear` makes 10 columns; `_dash_axreq_add` and `_dash_axreq_check` test `cols() != 10`.
- `_dash_axreq_add` fills column 10 for the label, mlabel, tick and mtick families with the message `_dash_so_resolve(words, J(1, cols(words), 1), "axlabel", …)` gives, or `""`. `_dash_axreq_check` refuses column 10, r(198), after column 9's test in the same row, so twoway's order (side, family, segment, place; existence, then axis word, then sub-option) holds.
- New `_dash_subreq_clear()`, `_dash_subreq_add(opts, seg)`, `_dash_subreq_check(kind)` and `_dash_subreq_accept()` keep the external `_dash_subreq`, rows `(kind, seg, place, value)`, and the external `_dash_subreq_ok` of accepted values. `_dash_subreq_clear` empties both, at the start of every graph command and after every check or refusal, so no typed text is kept.
  - `_add` records each raw token whose lower-case option name is a ≥3-letter prefix of `legend` (its whole value) or a ≥4-letter prefix of `zlabel` (the words after its first comma, cut at a second comma, as `_dash_ax_parse` cuts).
- `_dash_subreq_check("legend")` resolves all legend copies in (seg, place) order with the legend table. Then:
  1. Value checks, in twoway's order. For each copy, stage-3 rows in declaration order:
     - `holes`/`rows`/`cols` with `NL`/`N1` and a non-blank argument not yet accepted return −1, setting the caller's locals `_so_name` (full name), `_so_value` and `_so_kind` (`N1`/`NL`).
     - Then every `label` token, then every `lastlabel` token, across copies in order. Each key word `w` is the first word of the argument, with one pair of quotes stripped:
       - blank → accepted;
       - `[+-]?[0-9]+` → its value ≥ 1 is accepted, else `legend.labels[<w>] invalid name`;
       - anything else → `<w> not an integer in option label()` (or `lastlabel()`).

       Both are r(198).
  2. Then the resolver's leftover, r(198). A bare lower-case `top`, `bottom`, `left` or `right` leftover returns 0 instead, leaving `_dash_check_legend` its hint line.
  3. When no problem is found, the notes, each once, through S06's Stata-side note helper with twoway's exact text:
     - the last copy's `position` argument, stripped, not in `0`..`12` → `(note:  named style <v> not found in class clockdir, default attributes used)`;
     - the last `ring` argument that is non-blank and fails `_dash_so_isnum` → the two gridringstyle lines;
     - the last `order` with a bare word that is not `-` and does not match `[+-]?[0-9]+` → `<w> not an integer, option order() ignored`.

   Every message goes through `_dash_say("err", …)` or the note helper, never through a macro.
- `_dash_subreq_check("zlabel")` resolves each zlabel copy alone with the axlabel table and refuses the first problem. It then clears the record.
- New ado program `_dash_subopt_check kind` (dash.ado, beside `_dash_check_legend`; `version 19`) runs the check and loops while it returns −1:
  - if `_dash_so_unsafe(_so_value)` (a backtick, `$`, `'`, `"`, `\` or a byte below 32), rc = 121;
  - else ``capture numlist `"`macval(_so_value)'"', integer range(>0) min(0) max(1)`` (max(300) and no min for `NL`);
  - a non-zero rc prints `<_so_name>() invalid -- <text>` and exits with it:

    | rc | N1 text | NL text |
    |---|---|---|
    | 121 | invalid number | invalid numlist |
    | 123 | single number required | invalid numlist has too many elements |
    | 125 | invalid number, outside of allowed range | invalid numlist has elements outside of allowed range |
    | 126 | invalid number, noninteger value | invalid numlist has noninteger elements |
    | 127 | invalid number, missing not allowed | invalid numlist has missing values |
    | other | invalid numlist | invalid numlist |

  - rc 0 calls `_dash_subreq_accept()`, which marks the (copy, place) last returned as validated in the external `_dash_subreq_ok`, so the re-check skips it; then it re-checks.

  Each pass accepts one token, so the loop ends. It exits with a positive rc and clears the record on every refusal.
- Recording runs inside the Mata functions S10 already edits, so that `_dash_plot` (which S12 also edits in batch 4) gets one S10 hunk only. `_dash_axreq_clear()` ends by calling `_dash_subreq_clear()`. `_dash_axreq_add(raw, seg)` ends by calling `_dash_subreq_add(raw, seg)` with the same two arguments, which are exactly what each of its two `_dash_plot` call sites (:5213, :5323) passes.
- dash.ado `_dash_plot`, one hunk around the after-comma axis check (:5323-5325): `_dash_subopt_check legend` directly before the existing `_dash_axreq_check` line, and `_dash_subopt_check zlabel` then `_dash_subopt_check title` directly after its `if `_axrc' exit 198`. No other line of `_dash_plot` is edited by S10. See the batch-4 exception under Boundaries.
- `_needed` (dash.ado:255) gains `_dash_subreq_check _dash_subreq_accept _dash_so_unsafe`, the Mata functions dash.ado (`_dash_subopt_check`) calls.
- The header index (dash_parse.mata after :296) gains one entry per new function, and `_dash_axreq_add`/`_check`'s entries name column 10. `test_file_headers.py::TestTheMataLibraryHeader::test_its_public_api_is_the_list_dash_ado_needs` holds the Public API equal to `_needed`. So only the three functions dash.ado calls (`_dash_subreq_check`, `_dash_subreq_accept`, `_dash_so_unsafe`) get a Public API line with parentheses. `_dash_subreq_clear`, `_dash_subreq_add`, `_dash_so_rows`, `_dash_so_canon`, `_dash_so_isnum`, `_dash_so_family` and `_dash_so_resolve` are described as helpers with no parenthesis, as S11's `_dash_stylelist_elems` is.

### TR-10.6a Titles and axis titles refused as twoway refuses them (M5, P1.19.1)

twoway reads a title option in `_fr_title_parse_and_log.ado`:
- first every copy's `NOSPAN SPAN PREFIX SUFFIX POSition(string) RING(string) STYle(string) *` (:17-18, "accept last seen");
- then, for each copy's rest (:166-172, at most 20 copies), `_fr_sztextbox_parse_and_log` (`WIDTH(string) HEIGHT(string) NOASTextbox NOBEXpand ASTextbox BEXpand *`, :10-11), then the tbstyle list, then `syntax [, FAKE_OPT_FOR_BETTER_MSG]`.

An axis title goes through `_gs_parse_and_log_axtitle.ado`: `PREFIX SUFFIX AXis(passthru) *` (:15), refuses `prefix` with `suffix` r(198) `options prefix and suffix may not be combined` (:17-20), then sztextbox, tbstyle and FAKE (:31-33).

- **Tables.** `_dash_so_rows("title")`: stage 1 `nospan w, span w, prefix w, suffix w, position/pos a, ring a, style/sty a`; stage 2 `width a, height a, noastextbox/noast w, nobexpand/nobex w, astextbox/ast w, bexpand/bex w`; stage 3 the 26 tbstyle rows of TR-10.1. All three stages are starred, and the leftover is refused by the resolver's step 4. `_dash_so_rows("axtitle")` has the same stages 2 and 3, with stage 1 `prefix w, suffix w, axis/ax a`. The Python twins `_DASH_TITLE_SUBOPT_TABLE` and `_DASH_AXTITLE_SUBOPT_TABLE` sit beside TR-10.1's tables. SA-11 compares them, and the renderer does not read them (they are not on the copy list).
- **Recording.** `_dash_subreq_add` also records each raw graph-option token whose key, computed as `_dash_opts_repeats` computes it (`_dash_rep_bare`), has `_dash_rep_cat` "T". It records the words after the token's first top-level comma, as kind `axtitle` for `xtitle`, `ytitle`, `xtitle2`, `ytitle2` and `ztitle`, and as kind `title` otherwise.
- **Check.** `_dash_subreq_check("title")` resolves each option's copies in (seg, place) order with its family's table. It refuses the first problem r(198) with the resolver's message. For `axtitle` it first refuses a copy holding both `prefix` and `suffix` (twoway's words above). It prints no note and clears the record. `_dash_plot` calls `_dash_subopt_check title` directly after `_dash_subopt_check zlabel` (TR-10.6). Twoway checks titles inside the graph's own parse, which comes after the plot options and before the axes, but a title refusal and a legend or axis refusal on one command are both r(198). The order between them is not pinned (residual R-S10-4 covers the in-segment order).
- **Probes** (added to "Stata truth"): `t_ytitle_SIZE` (`ytitle(, SIZE(small))`), `t_ytitle_ls` (`ytitle(, ls(x))`), `t_ytitle_dup` (`ytitle(, size(small) s(large))`), `t_ytitle_pfx_sfx` (`ytitle("Y", prefix suffix)`), `t_note_SIZE` (`note("N", SIZE(small))`) and `t_rep_SIZE` (`title("A") title(, SIZE(small))`), each with rc and first line. Probes `t_SIZE`, `t_ls` and `t_dup` already exist.

### TR-10.7 Served copy lists (R2 row S10; append only, X.1)

- **Constants tuple.** After `"_DASH_TEXTBOX_DEFAULTS", "_DASH_SCALE_SUBOPTS",` (32934), add `"_DASH_LEGEND_SUBOPT_TABLE", "_DASH_AXLABEL_SUBOPT_TABLE", "_DASH_AXSCALE_SUBOPT_TABLE", "_DASH_REFLINE_SUBOPT_TABLE", "_DASH_AXLABEL_HONOURED", "_DASH_SUBOPT_REAL_RE", "_DASH_SUBOPT_INT_RE",`.
- **Functions tuple.** After `"_dash_subopt_name",` (33370), add `"_dash_subopt_canon", "_dash_subopt_resolve",`.
- Every other edited function is already listed and changes in place.

`test_statistical_helpers.py::TestTheServedAppCarriesEveryName::test_every_listed_name_exists` (S01) and `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads` (:1194) guard both.

### TR-10.8 Maps and registries (A148, X.5)

- **`test/function_test_map.py`**, under `# WP-30 S10 (P1.19): Sub-option abbreviations (P1.19)`:
  - `'_dash_subopt_canon': 'test/test_subopt_abbrev.py::TestTheTables::test_every_prefix_from_minimum_to_full'`;
  - `'_dash_subopt_resolve': 'test/test_subopt_abbrev.py::TestTheResolver::test_the_measured_refusals'`.
- **`test/program_coverage_map.py`**, `COVERAGE["dash_parse.mata"]` under the S10 anchor:
  - `_dash_so_rows` and `_dash_so_resolve` → `test_wp30_truth.cscript:SA-11`, `SA-12`;
  - `_dash_so_canon`, `_dash_so_family` → `test_twoway_option_parity.cscript:TP-14`;
  - `_dash_so_isnum`, `_dash_so_unsafe`, `_dash_subreq_clear`, `_dash_subreq_add`, `_dash_subreq_check`, `_dash_subreq_accept` → `test_suboption_reporting.cscript:SA-05`, `SA-06`.

  `COVERAGE["dash.ado"]` gains `_dash_subopt_check` → `test_suboption_reporting.cscript:SA-05`.

### TR-10.9 Security (rule 1)

- Every echoed name and value goes through `_dash_say`/the note helper (SMCL-escaped, control bytes replaced) or through `_dash_report_suboptions` (S06's escaped channel), never through a macro.
- `numlist` runs only on a value free of backtick, `$`, quotes, backslash and control bytes.
- There is no `_stata()`, `eval`, `exec` or `shell=True`.
- Canonical names never reach a Bokeh field or the HTML. Label text stays a DOM text node (`test_label_sinks.py`).
- Both resolvers are linear in tokens × rows. 127 legend copies and a 3,000-word legend are refused or drawn in under 5 s.
- N4 closes a path where quoted label text restyled an axis.

## Boundaries

- **Not edited:**
  - `_dash_subopt_name`, `_dash_by_tokens`, `_dash_report_suboptions`, `_dash_expand_numlist`, `_parse_axis_angle`'s body;
  - `_dash_scale_name`/`_dash_scale_spec` (S31);
  - the `_extract_region_*` readers (S38);
  - `_dash_check_legend`;
  - `_dash_rep_reduce`, `_dash_opts_repeats`, `_dash_process_segment` (S11);
  - the dispatcher and saving blocks (S12);
  - `_dash_route_axis2`, `_dash_ax_parse`;
  - `_make_figure_body`, `_generate_app_source`.
- **Owned by later sections:**
  - drawing `labcolor`, `tlength`, `tposition`, `nolabels`, the scale look and anglestyle names (S31);
  - grid colour/pattern (P2.20);
  - region sub-options and their refusals (S38);
  - xline numlists, refusals and `lstyle` (S39), and `extend`/`style` (S50);
  - `by(, legend())` (S53);
  - `text()` and its refusals (S56);
  - `format()` values and refusals (S18);
  - size units (S08/S13);
  - `add` (S52);
  - the legend sub-options dash names (`holes`, `colfirst`, `region()`, titles; P2.5).
- **Batch-4 exception (Maintainer question, S12 Notes).** `_dash_plot` is edited by S10 (one hunk at :5323-5325) and by S12 (:5540, :5560-5568), and `_dash_require_mata`'s `_needed` list by S10, S11 and S12 (separate continuation lines). S10 lands first; the merger applies S12's hunks with `git apply -3`.
- **Not checked by S10:**
  - a title's `prefix` with `suffix` (twoway prints `option prefix ignored, may not be combined with suffix` as text and draws; residual R-S10-1);
  - a value nested inside `legend(region(…))` or `legend(title(…))`;
  - xscale sub-options (`xscale(bogus)` stays named, help item 5).
- **Tracking documents:** S58 only (A145).
- **Plan files:** never edited (G6).

## Stata truth

**Extractor.** Create `scripts/extract_subopt_abbrev_truth.do`, copying `scripts/extract_text_truth.do`'s frame as S02 converted it:
- S02's `DASH_REPO` stanza, then `global dash_nobrowser 1`, `set scheme stcolor`, `sysuse auto`;
- per probe:
  - `log using "<tmp>/<id>.log", text replace name(_zs)`;
  - `capture noisily <cmd> name(zs, replace)`;
  - the rc;
  - `log close _zs`;
  - when rc is 0, `graph export "<tmp>/<id>.svg", replace name(zs)`.

**Python block.**
- It reads, per probe:
  - from the log, the lines after the echoed command that start with `option`, `(note:`, a probe value word or a name followed by `() invalid` / `not an integer` / `invalid name`, as `messages`;
  - from each SVG via `scripts/svg_truth.py:svg_document`, `texts` `[text, round(x), round(y), size, fill, rotate]` and `hlines`/`vlines` `[[stroke, width, dasharray, count], …]`.
- It writes `test/fixtures/subopt_abbrev_truth.json` as `{"_meta": {...}, "probes": {id: {"cmd", "rc", "messages", "texts", "hlines", "vlines"}}}`.
- `_meta` holds `stata_version`, `born_date`, `dash_commit` (read through `Macro.getLocal` from a `shell git -C <repo> rev-parse HEAD` local), `extracted` and `scheme_in_force`.
- The block never calls Stata, never uses `shell=True`, and writes a backtick as `\x60`.

**Probes** (ids are the fixture keys; bases as in Evidence):
- **Legend:**
  - `l_base`;
  - columns, rows, labels and position: `l_cols2 l_c2 l_co2 l_col2 l_rows1 l_r1 l_r1_k3 l_label l_lab l_labe l_la l_position9 l_pos9 l_posi9 l_pos_sp`;
  - size and lastlabel: `l_size l_si l_s l_siz l_lastlabel l_lastlab l_lastlabe`;
  - colour and fall-through: `l_color_red l_colo_red l_fall_c l_fall_cc l_fall_c3 l_fall_sty`;
  - repeatable stages: `l_rep_region l_rep_title l_rep_label l_t_title l_l_title l_b_title` (`legend(t("TT"))`, `l("TT")`, `b("TT")`);
  - spellings refused: `l_po9 l_rin0 l_ord l_o l_lastl l_of l_OFF l_POS l_Pos l_SIZE l_Cols`;
  - duplicates and forms: `l_c_dup l_pos_dup l_size_dup l_s_dup l_order_dup l_on_dup l_holes_dup l_rows_dup l_ring_dup l_cols_word l_on_arg l_garbage`;
  - columns and rows values: `l_c_red l_cols0 l_cols_neg l_cols15 l_cols05 l_cols12 l_cols13 l_cols113 l_colsdot l_colsdota l_cols_big l_cols22 l_cols_empty l_cols_plus l_cols_1x l_cols_x1 l_rows_x l_r0`;
  - holes and offsets: `l_holes0 l_holes15 l_holes301 l_holes_empty l_xoff_x l_xoff_empty l_yoff12`;
  - label keys: `l_label_x l_label_15 l_label_q l_label_1e0 l_label_1x l_label_0 l_label_m1 l_lastl_0 l_lastl_x l_lastl_q l_label_01 l_label_plus l_label_empty l_label_1`;
  - notes: `l_posx l_pos13 l_posm1 l_pos06 l_pos30 l_ringx l_ringm1 l_ring15 l_orderx l_order1x l_orderx1 l_order1ax l_order1e0 l_order_plus l_order_neg`;
  - on and off: `l_onoff1 l_offon1 l_onoff2` (one key: `S1 legend(on off)`, `legend(off on)`; two: L2).
- **Merges:** `m_posx_pos3 m_orderx_21 m_on_off m_off_on1 m_cc m_cc2 m_pp m_lab_ab m_lab_same m_ll m_ll2 m_t_s m_sc_union`; `k_rowscols k_rowscols1 k_colsrows k_cr k_rc k_one k_r1c2` (K3).
- **Axis:**
  - `a_base`;
  - accepted spellings: `a_labsize a_labs a_labsi a_angle a_ang a_format a_form a_for a_nogrid a_nogr a_nog g_grid g_gr g_g g_gri` (the `g_*` probes under `scheme(s2color)`), `a_glcolor a_glc a_labc a_nolab a_notick f_val f_valuelabel f_valuelabels` (`twoway scatter mpg foreign, xlabel(0 1, …)`);
  - spellings refused: `a_lab_s a_LABS a_LABSize a_a a_an a_f a_fo a_gl a_nola a_no f_va`;
  - forms and duplicates: `a_labs_word a_labsize_word a_nog_arg a_nogrid_arg a_dupang a_duplabs a_dupfor a_dupglc a_bogus a_bogus2 a_labs_labsword a_labsword_labs a_labs_LABSIZE`;
  - accepted pairs: `a_dup_word a_grid_nogrid a_nogrid_grid a_val_noval`;
  - `labelminlen`: `a_lml_x a_lml_15 a_lml_empty`;
  - other families: `a_tick_labs a_tick_a a_mlabel_a z_a z_labs z_dup` (`S1 colorvar(price) zlabel(…)`);
  - quoted text: `n_quoted n_nocomma`.
- **Order:** `o_leg_ax o_ax_leg o_leg_axis3 o_x_y3 o_axis3_a o_lab_tick o_tick_lab o_mlab_tick o_ylab_xtick o_z_y o_y_z o_z_line o_z_leg o_c_po o_triple o_po_label o_label_cols o_copies o_rows_cols o_cols_rows_one o_rows_cols_one o_holes_cols o_lastl_label o_ax_c` (commands in Evidence's order table).
- **xline:** `x_base x_full x_abbr x_lcol x_lpatte x_lwid x_l x_c x_color x_ls x_LC x_lst x_st x_la x_ex x_noex x_rep y_abbr x_tlc`.
- **Titles:** `t_base t_size t_s t_ytitle_s t_ls t_nob t_a t_b t_SIZE t_dup t_style t_ytitle_SIZE t_ytitle_ls t_ytitle_dup t_ytitle_pfx_sfx t_note_SIZE t_rep_SIZE` (TR-10.6a).

Every command is the one quoted in Evidence. A probe not quoted there is that row's natural reading.

**Run.** `DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s10 $WT/scripts/extract_subopt_abbrev_truth.do`. Then `git -C $WT add -f test/fixtures/subopt_abbrev_truth.json` (`.git/info/exclude:58`). It is never patched by hand (R7); a value differing from Evidence is investigated.

**Truth block** (`test/test_wp30_truth.cscript`, S01's stub `* ==== S10 P1.19: Sub-option abbreviations ====`, between its start and end lines, gated `WP30_ONLY=S10`). Helpers sit directly above the header.
- **SA-11:** for each of the seven families (TR-10.6's five and TR-10.6a's `title`/`axtitle`), Mata `_dash_so_rows(fam)` equals `dash_render`'s table row for row, in a `python:` block that reads the rows from locals. Not a captured import probe, so `test_cscript_hygiene.py:322` stays 13.
- **SA-12:** `_dash_so_resolve` and `_dash_subopt_resolve` give the same names and problem on every probe's token list plus 500 random lists (seed 30019) drawn from each table's names, abbreviations, capitals and bogus words.
- **SA-13:** for every refusal probe, twoway's rc and first line now equal the fixture's, and `dash <same command>` gives the same rc and line.
- **SA-14:** three drawn checks on saved pages built by `dash build`:
  - `legend(c(1))` → ncols 1 in the page JSON;
  - `ylabel(, labs(large))` → the label size equals `labsize(large)`'s;
  - `xline(3000, lc(red))` → Span `line_color` red.

## TDD test stubs

The first block is red at `batch-4-base` (10-01). New file `test/test_subopt_abbrev.py`:
- both-mode figures come from `test_axis_label_grammar._figures(mode, …)` with `_MODES`;
- saved moves use `test_saved_filter_layers._render`/`_move`;
- served moves use `test_mode_parity._served_after_move`;
- notes are collected through S06's counting helpers or `warnings.catch_warnings`.

**`TestTheTables`:**
- Test: every prefix from minimum to full of every row canonicalises to its full name in each table: `::test_every_prefix_from_minimum_to_full`. Red at base with `AttributeError: module 'dash_render' has no attribute '_dash_subopt_canon'`.
- Test: the measured shadowing `c→cols`, `la→lalign`, `s→size`, `b→box`, `r→rows`, `t→t1title` (legend); `g→grid`, `nog→nogrid`, `val→valuelabels`, `for→format`, `tl→tlength` (axis); `st→style`, `la→lalign` (refline): `::test_twoways_shadowing`.
- Test: capitals and the measured refused spellings give `None`: `::test_refused_spellings_have_no_name`.
- Test: `_textbox_canon` follows Stata's parser (`s`, `a`, `lst`, `nob`, `b` named; `si` still size; `ls`, `SIZE` give None): `::test_the_textbox_table_is_statas`.

**`TestTheResolver`:**
- Test: each measured refusal of Evidence (legend and axis families) gives twoway's message: `::test_the_measured_refusals`.
- Test: the accepted fall-throughs name `[cols, color]`, `[style, style]`, `[cols, color, None]`; repeated words are accepted in unstarred stages: `::test_fall_through_and_repeats`.
- Test: 20,000 tokens resolve in under 2 s: `::test_linear_on_a_long_copy`.

**`TestLegendAbbreviations`** (parametrised over the two modes):
- `c(1)`/`co(1)`/`col(1)` → ncols 1; `r(1)` → nrows 1 and ncols auto; `lab(1 "XX")` → key 1 XX; `posi(9)` → left; `s(large)`/`si(large)` → the size of `size(large)`; `lastlab(1 "XX")`. No sub-option note: `::test_each_spelling_draws_as_the_full_name`.
- `la(1 "XX")` is named as typed and the key is unchanged: `::test_la_is_lalign_and_named`.

**`TestLegendInOneCopy`:**
- `cols(3) rows(1)` → nrows 1, ncols auto (N7): `::test_rows_beat_cols`.
- One key, `on off` and `off on` → visible (N8): `::test_on_beats_off`.
- `cols(1) c(red)` → ncols 1, `c(red)` named: `::test_a_second_c_is_color`.
- `position(13)`, `pos(06)`, `pos(3.0)` → the scheme default, silent in the renderer; `pos( 9 )` → left: `::test_position_takes_twoways_names`.
- `order(1 x)` → the default key order: `::test_a_non_integer_order_word_voids_order`.
- `label(+1 "A")` → key 1 A: `::test_a_signed_key`.
- `cols(2/2)` → 2 columns: `::test_a_one_value_numlist`.

**`TestAxisAbbreviations`** (both modes):
- `labs(large)`, `ang(45)`, `for(%9.1f)`/`form()`, `nog`/`nogr`, `g`/`gr` (s2color) and `valuelabels`/`val` draw as their full names with no note: `::test_each_spelling_draws_as_the_full_name`.
- `glc(red)` and `xtick(, labs(large))` are named as typed: `::test_undrawn_spellings_are_named_as_typed`.
- `zlabel(, labs(large))` is named `labs(large)` (A64): `::test_zlabel_names_as_typed`.
- `ylabel2(, labs(large))` sizes the second axis: `::test_second_axis`.

**`TestAxisInOneCopy`:**
- `grid nogrid` and `nogrid grid` → grid drawn: `::test_grid_beats_nogrid`.
- `ylabel(10 "labsize(large)" 20)` → the default size and the label text kept: `::test_quoted_text_is_text`.
- `LABSIZE(large)` is named, not drawn: `::test_capitals_are_unread`.
- `ylabel(, labs(bogus))`'s note names `labs(bogus)`: `::test_the_note_names_the_typed_spelling`.

**`TestReflineAbbreviations`** (both modes and after a move):
- `lc(red) lp(dash) lw(thick)` and `lcol`/`lpat`/`lwid` equal the full names' Span: `::test_each_spelling_draws_as_the_full_name`.
- `LCOLOR(red)`, `l(red)`, `c(red)`, `color(red)`, `ls(x)` are named, scheme colour: `::test_refused_spellings_are_named`.
- `xline(3000, lc(bogus))`'s note names `xline(lc)`: `::test_the_note_names_the_typed_spelling`.

**`TestTextboxShortSize`** (both modes): `title("T", s(small))` = `size(small)`; `SIZE(small)` is named: `::test_s_is_size`.

**`TestTheMoveKeepsIt`:**
- No module-level JS string writes `ncols`, `nrows`, `label_text_font_size`, `major_label_text_font_size`, `major_label_orientation`, `grid_line_color`, `line_dash`, `line_width` or `location`: `::test_no_page_script_rewrites_these`.
- The served profile after a foreign dropdown move equals before, for the three families: `::test_served_after_a_move`.
- The saved figures after `_move` equal before: `::test_saved_after_a_move`.

**Guards** (green at base, kept green; listed in the failure file as guards):
- `TestLegendAbbreviations::test_la_is_lalign_and_named`;
- `TestAxisAbbreviations::test_undrawn_spellings_are_named_as_typed` and `::test_zlabel_names_as_typed`;
- `TestReflineAbbreviations::test_refused_spellings_are_named`;
- the three `TestTheMoveKeepsIt` tests.

The rest are red.

**`TestTheFixture`** (10-02; guard, not red): `_meta` holds the four keys plus `scheme_in_force`, and every probe's rc and first message equal the module's expectation table: `::test_meta`, `::test_every_probe_matches_the_measured_truth`.

**`test/test_mode_parity.py` CORPUS** (guards: both modes agree at base): "legend abbreviations", "legend rows beat cols", "legend on beats off", "axis label abbreviations", "quoted axis label text", "xline abbreviations", "title s() is size".

**`test/test_suboption_reporting.cscript`** (red at base unless marked guard):
- SA-01: legend spellings, no legend note.
- SA-02: axis-label spellings, no ylabel/xlabel note.
- SA-03: xline spellings, no xline note.
- SA-04: `legend(lab(1 "AA")) legend(lab(2 "BB"))`: the saved HTML holds AA and BB.
- SA-05: legend refusals and accepted forms, rc and first line each.
- SA-06: axis-label refusals and accepted forms.
- SA-07: refusal order.
- SA-08: notes (`pos(13)`, `ring(x)`, `order(1 x)` once; `legend(pos(x)) legend(pos(3))` silent).
- SA-09: guard: `xline(3000, LCOLOR(red))` is rc 0 and named (its refusal is S39's).
- SA-15: title and axis-title refusals (TR-10.6a): `title("T", SIZE(small))`, `title("T", ls(x))`, `title("T", size(small) s(large))`, `title("A") title(, SIZE(small))`, `note("N", SIZE(small))`, `ytitle(, SIZE(small))`, `ytitle(, size(small) s(large))` and `ytitle("Y", prefix suffix)` each give the fixture's rc and first line; `title("T", s(small))`, `title("T", nob)` and `ytitle(, s(small))` are rc 0 with no title note.
- SA-10: resource and injection: 127 copies of `legend(c(2) lab(1 "A"))` in under 5 s; a 3,000-word legend ending in `po(9)` refused in under 5 s; `legend(a$b(1))` echoes `option a$b() not allowed` unexpanded.

**`test/test_twoway_option_parity.cscript` TP-14a** rows 34-39 (`n14 33 → 39`):
- `legend(lab(1 "A")) legend(lab(2 "B"))` = `legend(lab(1 "A") lab(2 "B"))`;
- `legend(c(1)) legend(r(1))` = `legend(r(1))`;
- `legend(posi(9)) legend(pos(3))` = `legend(pos(3))`;
- `ylabel(, labs(large)) ylabel(, labsize(small))` = `ylabel(, labsize(small))`;
- `title(A, s(large)) title(, size(small))` = `title(A, size(small))`;
- `xscale(r(1000 3000)) xscale(range(2000 6000))` = `xscale(range(1000 6000))`.

Red at base: rows 34-36, 38, 39 (the keys differ). Row 37 is red only if the merged text differs; measured in 10-01.

**Flips:** `test_help_claims_7.py::TestTheNewHelpers::test_dash_legend_parts`; `test_textbox_grammar.py::TestTheTable::test_every_prefix`; HC1-15; HC2-21i/j.

## Test plan

| What | How | Fixture | Both modes / after move |
|---|---|---|---|
| Tables, canonicaliser, resolver | pytest `TestTheTables`, `TestTheResolver` | Evidence (hard-coded) and `subopt_abbrev_truth.json` | n/a |
| Legend, axis, xline, textbox drawing | pytest per family, `mode` parametrised | probes `l_*`, `a_*`, `x_*`, `t_*` | yes / yes (`TestTheMoveKeepsIt`) |
| Parity | `test_mode_parity.py` CORPUS (G3) | — | yes / served move |
| Merge keys | TP-14a rows 34-39 | twoway SVG checksum per row | Stata-side |
| Refusals, order, notes | SA-05..SA-08 through the driver | `messages` of the fixture | Stata-side (both modes share it) |
| Twins | SA-11, SA-12 | tables | n/a |
| Twoway drift and dash parity | SA-13, SA-14 | live twoway | saved page |
| Registries | `test_function_test_map.py`, `test_program_coverage_map.py`, `test_file_headers.py`, `TestTheServedAppCarriesEveryName`, `TestTheServedAppDefinesEveryNameItReads` | — | served |
| Security | SA-10, `test_linear_on_a_long_copy`, `test_label_sinks.py` | — | both |

**Acceptance criteria.**
- **AC-10.1** Every 10-01 test is red at `batch-4-base` and green after 10-11. The guards are green throughout.
- **AC-10.2** For every fixture refusal probe, `dash` gives twoway's rc and first line, and twoway still gives the fixture's (SA-13).
- **AC-10.3** Every accepted spelling in Evidence draws in dash what its full name draws, in both modes, before and after a move. There is no note for honoured ones, and undrawn ones are named as typed.
- **AC-10.4** SA-11 and SA-12 report zero differences between Mata and Python.
- **AC-10.5** TP-14a rows 1-39 pass, row 26 included.
- **AC-10.6** The full suite through the queue shows 0 failed. G4, G5 and G6 pass. `grep -c '<!-- WP-30 P1.19' CHANGELOG.md` prints 0. `WP30_OPEN` has no `P1.19`.

## Tasks

**Commit boundary.** Tasks 10-01 to 10-12 form the one P1.19 commit on `wp30-s10` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s10`, made by 10-12 after one full run through the queue. The subject is `Read twoway's sub-option abbreviations and refuse what twoway refuses in legend() and the axis labels (WP-30 P1.19)`.

The body:
1. opens with `<scratch>/10-P1.19-failure.txt`;
2. gives the measured defect, then what changed and where (both renderers, Mata, dash.ado);
3. then has one line each:
   - `Regression: test/test_subopt_abbrev.py::<Class>::<test> -- failed at <batch-4-base sha> with <text>` (one per red test; the SA cases as `test/test_suboption_reporting.cscript SA-0n -- failed at … with …`);
   - `Flipped: <node> -- <old expectation> was wrong because <why>` (four);
   - `Fixture: test/fixtures/subopt_abbrev_truth.json (scripts/extract_subopt_abbrev_truth.do)`;
   - `BUGS.md: "<title>" (closed)`.

No tool or vendor is named. G7: `grep -Eic 'claude|anthropic'` is 0 before and after. `CLAUDE.md`, `.gitignore`, `AGENTS.md` and plan files are never staged. `<scratch>` is the orchestrator's WP-30 scratch directory (index "Deltas"); S10's own files go under `<scratch>/s10`.

<task type="auto" id="10-01">
  <name>Write and run the failing regression tests</name>
  <files>test/test_subopt_abbrev.py, test/test_mode_parity.py, test/test_suboption_reporting.cscript</files>
  <action><![CDATA[
    Check that `git -C $WT rev-parse HEAD` equals `cat <scratch>/batch-4-base.txt`, that `git -C $WT branch --show-current` prints `wp30-s10`, and that `<scratch>/batch-4-impact.txt` records the CRITICAL `_dash_parse_axis_spec`/`_parse_axis_angle` warning with the maintainer's approval; if not, stop and report. Create `test/test_subopt_abbrev.py` with every class and test of "TDD test stubs" except `TestTheFixture`, with expected values hard-coded from Evidence (module constants `_LEGEND_REFUSALS`, `_AXIS_REFUSALS`, `_ACCEPTED`). Append the seven CORPUS cases to `test/test_mode_parity.py` (R8; no `_MUST_WARN` or `ALLOWED` edit). Append SA-01..SA-10 and SA-15 to `test/test_suboption_reporting.cscript` as one contiguous run after SR-09 (R1), using its `_sr_render`/`_sr_count` helpers; in TP-14a terms they assert rc and the first error line. Run them on the unmodified tree and write `<scratch>/10-P1.19-failure.txt`: base sha, each red test's failure line, each red SA case's FAIL line, and the guards that passed. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_subopt_abbrev.py -q -n0 -p no:cacheprovider` reports at least 25 failed and every guard of "TDD test stubs" passed; `python3 -m pytest test/test_mode_parity.py -q -p no:cacheprovider` passes (the seven new cases are guards); the driver run of `test_suboption_reporting.cscript` (index "The cscript driver") prints `SA-01 FAIL` through `SA-08 FAIL`, `SA-09 PASS` and `SA-15 FAIL`; `test -s <scratch>/10-P1.19-failure.txt`.]]></verify>
  <done>Every regression test existed and was shown failing on the unfixed tree, the guards passed, and the failure text was saved.</done>
</task>

<task type="auto" id="10-02">
  <name>Extract the sub-option truth from twoway</name>
  <files>scripts/extract_subopt_abbrev_truth.do, test/fixtures/subopt_abbrev_truth.json, test/test_subopt_abbrev.py</files>
  <action><![CDATA[
    Create `scripts/extract_subopt_abbrev_truth.do` as "Stata truth" specifies (S02's `DASH_REPO` stanza, then `global dash_nobrowser 1`; per-probe log and SVG; the python block with `_meta`, no `shell=True`, backticks as `\x60`). Run `DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s10 $WT/scripts/extract_subopt_abbrev_truth.do` and read the log. Compare every probe with Evidence; investigate a difference, never patch the fixture (R7). If `l_t_title`, `l_l_title` or `l_b_title` is refused, record which minimum the fixture implies for TR-10.1's stage 5. Run `git -C $WT add -f test/fixtures/subopt_abbrev_truth.json`. Add `TestTheFixture` (`test_meta`, `test_every_probe_matches_the_measured_truth`) to `test/test_subopt_abbrev.py`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_subopt_abbrev.py::TestTheFixture -q -n0 -p no:cacheprovider` passes; `python3 -c "import json;d=json.load(open('test/fixtures/subopt_abbrev_truth.json'));p=d['probes'];assert p['l_c_red']['rc']==121 and p['l_po9']['messages'][0]=='option po() not allowed' and p['a_grid_nogrid']['rc']==0;print(len(p))"` prints at least 150; `git -C $WT ls-files test/fixtures/subopt_abbrev_truth.json` prints the path.]]></verify>
  <done>twoway's own reading of every probe was recorded in a stamped, staged fixture that a test held to Evidence.</done>
</task>

<task type="auto" id="10-03">
  <name>Add the tables, canonicaliser and resolver</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    In dash_render.py after `_dash_subopt_name` (about :25817) add `_DASH_TBSTYLE_ROWS`, the four `_DASH_*_SUBOPT_TABLE` constants, `_DASH_AXLABEL_HONOURED`, `_DASH_SUBOPT_REAL_RE`, `_DASH_SUBOPT_INT_RE`, `_dash_subopt_canon` and `_dash_subopt_resolve` exactly as TR-10.1/TR-10.2 state, each table row block preceded by a comment citing its parser file and lines. Correct `_TEXTBOX_SUBOPTS` (:4639) and make `_textbox_canon` (:4657) lower-case only (TR-10.1); `_textbox_canon` is HIGH: state the warning in the progress output. Add the two map entries of TR-10.8 under the S10 anchor in `test/function_test_map.py`, alphabetical.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_subopt_abbrev.py -q -n0 -p no:cacheprovider -k "TestTheTables or TestTheResolver"` passes; `python3 -m pytest test/test_function_test_map.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>The renderer held twoway's sub-option tables and one resolver that reproduced every measured refusal and fall-through.</done>
</task>

<task type="auto" id="10-04">
  <name>Read legend sub-options by full name</name>
  <files>dash_render.py, test/test_help_claims_7.py</files>
  <action><![CDATA[
    Apply TR-10.3: `_dash_legend_parts` (3-tuples), `_dash_legend_unsupported`, `_dash_legend_arg` (`for name, arg, *_ in calls`), `_DASH_LEGEND_SUBOPTS` without "pos", `_DASH_LEGEND_LABEL_RE` with `\+?`, `_dash_parse_legend_order`'s word rule, and in `_dash_apply_legend` the position pattern, cols/rows through `_dash_expand_numlist` with rows beating cols, `on` beating `off`, and the typed name in the size note (re-grep S08's lines at `batch-4-base`). Flip `test_help_claims_7.py::TestTheNewHelpers::test_dash_legend_parts` to `words == set()` and `calls == [("position", "6", "pos"), ("label", '1 "on top"', "label"), ("order", "2 1", "order")]`, and append its `Flipped:` line to `<scratch>/10-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_subopt_abbrev.py -q -n0 -p no:cacheprovider -k "Legend"` passes; `python3 -m pytest test/test_help_claims_7.py test/test_legend_order.py test/test_server_legend.py test/test_help_claims_5.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>Every legend spelling drew as its full name in the renderer, rows beat cols, on beat off, and the one stale pin was flipped with its reason.</done>
</task>

<task type="auto" id="10-05">
  <name>Read axis-label sub-options from tokens</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn in the progress output: `_dash_parse_axis_spec` and `_parse_axis_angle` are CRITICAL (8 and 7 impacted), `_dash_apply_tick_option`, `_dash_apply_z_options` and `_dash_apply_axis_spec` HIGH. Apply TR-10.4: in `_dash_parse_axis_spec` (:22602) replace the tail loop and delete the four whole-text regexes (:22649-22659) with the resolver reading, add `out["typed"]`; in `_dash_apply_tick_option` (:22904-22910) use `spec["typed"]`; in `_dash_apply_z_options` (:26150-26163) name `spec["typed"]` tokens; in `_dash_apply_axis_spec`'s labsize note use the typed token. Do not edit `_parse_axis_angle`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_subopt_abbrev.py -q -n0 -p no:cacheprovider -k "Axis"` passes; `python3 -m pytest test/test_graph_options.py test/test_axis_label_grammar.py test/test_axis_options.py test/test_value_labels_drawn.py test/test_suboption_warnings.py test/test_colorvar_forms.py test/test_display_format_sites.py test/test_adversarial_matrix.py test/test_axis2_suboptions.py -q -p no:cacheprovider` passes.]]></verify>
  <done>Axis-label sub-options were read only from parsed tail tokens under their full names, and every note named the spelling the user typed.</done>
</task>

<task type="auto" id="10-06">
  <name>Read xline and textbox spellings</name>
  <files>dash_render.py, test/test_textbox_grammar.py</files>
  <action><![CDATA[
    Apply TR-10.5 to `_dash_refline_instances` (:26268) and `_dash_refline_draw` (:26327). Flip `test/test_textbox_grammar.py::TestTheTable::test_every_prefix` (:168-195) to the corrected `_TEXTBOX_SUBOPTS` of 10-03, with a bogus list of `colour`, `style`, `z`, `ls`, `al`, `SIZE`, and append its `Flipped:` line to `<scratch>/10-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_subopt_abbrev.py -q -n0 -p no:cacheprovider -k "Refline or Textbox"` passes; `python3 -m pytest test/test_textbox_grammar.py test/test_axis_options.py test/test_label_sinks.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>Reference lines and textboxes read twoway's spellings in lower case, and the textbox table matched Stata's parser.</done>
</task>

<task type="auto" id="10-07">
  <name>Carry the tables to the served app</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    In `ServerAppBuilder._glyph_layer_lines`, append TR-10.7's constants after `"_DASH_TEXTBOX_DEFAULTS", "_DASH_SCALE_SUBOPTS",` and the two functions after `"_dash_subopt_name",`; reorder nothing (X.1). State the HIGH warning for `_glyph_layer_lines` in the progress output.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads test/test_mode_parity.py -q -p no:cacheprovider` passes; `python3 -m pytest test/test_subopt_abbrev.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>The served app drew every family as the saved page did, before and after a filter move.</done>
</task>

<task type="auto" id="10-08">
  <name>Key the Mata merge by full name</name>
  <files>dash_parse.mata, test/program_coverage_map.py, test/test_twoway_option_parity.cscript</files>
  <action><![CDATA[
    After `_dash_axreq_check` (dash_parse.mata:5630) add `_dash_so_rows`, `_dash_so_canon`, `_dash_so_isnum`, `_dash_so_family` and `_dash_so_resolve` (TR-10.6), with no `regexm`. Change `_dash_rep_subkey(tok, cat)` to `_dash_rep_subkey(tok, cat, full)`, `_dash_rep_subs` to take `key` and resolve, reduce pairs, key, keep, apply rows-over-cols and re-spell fall-throughs as TR-10.6 states, and pass `key` from `_dash_rep_merge`'s two calls (:5728, :5743), keeping `_dash_rep_merge`'s signature. Update the header index. Add TR-10.8's Mata entries to `test/program_coverage_map.py`. Add TP-14a rows 34-39 and set `n14 39`.
  ]]></action>
  <verify><![CDATA[The driver run of `test_twoway_option_parity.cscript` prints `TP-14a row 39:` with no `TP-14a FAIL` and ends with its ALL PASSED line; `python3 -m pytest test/test_program_coverage_map.py test/test_file_headers.py test/test_no_orphans.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>Repeated legend, axis-label, scale and title copies merged sub-option by sub-option under full names, with rows over cols, the positive word in a copy, and every label kept.</done>
</task>

<task type="auto" id="10-09">
  <name>Refuse what twoway refuses in Stata</name>
  <files>dash_parse.mata, dash.ado, test/program_coverage_map.py</files>
  <action><![CDATA[
    Add `_dash_so_unsafe`, `_dash_subreq_clear`, `_dash_subreq_add`, `_dash_subreq_check` (with TR-10.6a's `title` and `axtitle` kinds and their two `_dash_so_rows` families), `_dash_subreq_accept` and column 10 of `_dash_axreq_add`/`_dash_axreq_check`/`_dash_axreq_clear` (TR-10.6). In dash.ado add program `_dash_subopt_check` (`version 19`, after `_dash_check_legend` :1951) with the numlist loop and rc table, the one `_dash_plot` hunk of TR-10.6 (`_dash_subopt_check legend` before the axis check line at :5324, `zlabel` and `title` after its exit line; `_dash_subreq_clear`/`_add` are called from `_dash_axreq_clear`/`_add`, not from dash.ado) and the `_needed` names (:255). Notes go through S06's Stata-side note helper (read its signature at `batch-4-base`). Add `_dash_subopt_check` to `COVERAGE["dash.ado"]` and the rest to `COVERAGE["dash_parse.mata"]` under the S10 anchors.
  ]]></action>
  <verify><![CDATA[The driver run of `test_suboption_reporting.cscript` prints `SA-01 PASS` through `SA-10 PASS`, `SA-15 PASS` and its ALL PASSED line; the driver run of `test_twoway_option_parity.cscript` stays green; `python3 -m pytest test/test_program_coverage_map.py test/test_file_headers.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>dash refused capitals, refused spellings, in-copy repeats, wrong forms and bad values in legend() and the axis labels with twoway's code and words, in twoway's order, and printed twoway's notes once.</done>
</task>

<task type="auto" id="10-10">
  <name>Flip the garbage pins and fill truth</name>
  <files>test/test_help_claims_1.cscript, test/test_help_claims_2.cscript, test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Flip HC1-15 (:818-849): `dash scatter mpg weight, legend(garbage)` expects r(198) with `option garbage not allowed` in the log, and `dash scatter mpg weight, xscale(bogus)` stays rc 0 and named; update its `*!` header line (:66). Flip HC2-21i (:633) to 198 and HC2-21j (:634) to assert that no graph `hc` is registered. Append both `Flipped:` lines to `<scratch>/10-flips.txt`. Fill S01's S10 stub block in `test/test_wp30_truth.cscript` with SA-11..SA-14 between its start and end lines, helpers directly above its header.
  ]]></action>
  <verify><![CDATA[Driver runs of `test_help_claims_1.cscript` and `test_help_claims_2.cscript` print `HC1-15 PASS`, `HC2-21i` and `HC2-21j` passing and their ALL PASSED lines; `WP30_ONLY=S10` driver run of `test_wp30_truth.cscript` prints `SA-11 PASS` .. `SA-14 PASS`, `S10 start`, `S10 end`, and no SKIP.]]></verify>
  <done>The help-claim pins asserted twoway's refusal of legend(garbage), and the truth block held the twins and twoway's live answers to dash's.</done>
</task>

<task type="auto" id="10-11">
  <name>Document the spellings and refusals</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    In dash.sthlp:
    - **:615-632 also:** titles and axis titles refuse a capitalised or unknown sub-option and a second copy in one option, as twoway does (TR-10.6a).
    - **:548-556 (merge paragraph):** add that copies merge sub-option by full name, the last winning; that `rows()` beats `cols()`; that within one copy a word beats its `no` form; and that every `label()` key survives.
    - **:615-632:** for `legend()` and the axis labels and ticks, a sub-option twoway refuses is refused (`option OFF not allowed`, r(198)), and others not drawn are named as typed. The textbox minimums are Stata's (`s()` is `size()`, `a()` `alignment()`, `lst()` `lstyle()`, `nob` `nobox`, `b` `box`); `(colour(), style())` becomes `(colour())`.
    - **:783-786:** the `legend(garbage)` sentence now reads that dash refuses it as twoway does, while `xscale(bogus)` is named. Keep S11's next sentence (R3).
    - **Legend paragraph after :2808:** the spellings, the refusals, rows over cols, on over off, the position names 0-12, and twoway's notes.
    - **:2835-2839:** the axis spellings, and that quoted text is text.
    - **:3018-3022:** "under the same spellings".
    - **:3352-3353:** add `lc()`/`lp()`/`lw()`.
    - **:3414-3415:** `rows()` wins over `cols()`.

    Use `{cmd:}` for spellings, never `{cmdab:}`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_examples.py test/test_help_conformance.py test/test_abbreviations.py test/test_help_claims_1.py test/test_help_claims_2.py test/test_help_claims_8.py -q -p no:cacheprovider` passes; `grep -c "legend(garbage)" dash.sthlp` prints 1 and the line says it is refused.]]></verify>
  <done>The help described every spelling, refusal, merge rule and note this section added, and no longer claimed dash names legend(garbage).</done>
</task>

<task type="auto" id="10-12">
  <name>Close the entry and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    In BUGS.md close the P1.19 entry in place: `- [x]`, then `- Resolution: Fixed <ddmonyyyy> (WP-30, P1.19).` + what changed (TR-10.3..TR-10.6, both renderers, Mata, dash.ado) + `Pinned by test/test_subopt_abbrev.py::TestTheResolver::test_the_measured_refusals, test/test_subopt_abbrev.py::TestLegendAbbreviations::test_each_spelling_draws_as_the_full_name, test/test_suboption_reporting.cscript SA-05; fixture test/fixtures/subopt_abbrev_truth.json.` + `Residual, deferred (WP-30): R-S10-1 (title prefix with suffix prints no text line), R-S10-2 (label(#) with no text), R-S10-3 (values nested in legend(region()/title())).` Delete only `"P1.19"` from `WP30_OPEN`. Replace `<!-- WP-30 P1.19 -->` in "Changed behaviour" and in "Fixed in WP-30" with Notes' two lines. Run the changed files, the driver runs of 10-08..10-10, `git -C $WT merge --no-edit main` (`Already up to date.`), then `<scratch>/full_suite_queue.sh $WT <scratch>/10-full-1.log` in the background and wait for `exit=`. Check G6 and G7, then commit with Commit boundary's message.
  ]]></action>
  <verify><![CDATA[`grep -c "exit=0" <scratch>/10-full-1.log` prints 1 and the log shows 0 failed; `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` passes; `grep -c '<!-- WP-30 P1.19 -->' $WT/CHANGELOG.md` prints 0; `grep -c '^    "P1.19": "' $WT/test/test_tracking_documents.py` prints 0; `git -C $WT log -1 --format=%s` ends `(WP-30 P1.19)`; `git -C $WT log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `git -C $WT diff HEAD~1 --name-only | grep -cE '^(CLAUDE.md|AGENTS.md|\.gitignore|\.ultraplan/)'` prints 0.]]></verify>
  <done>The P1.19 entry was closed with existing tests named, its markers replaced, the suite green, and one commit made on wp30-s10.</done>
</task>

## Section completion criteria

- One commit on `wp30-s10` ending `(WP-30 P1.19)`. Its body opens with the saved failure text and carries the Regression, four Flipped, Fixture and BUGS.md lines.
- AC-10.1 to AC-10.6 hold. The SA cases pass through the driver, and the S10 truth block passes with `WP30_ONLY=S10` and no SKIP.
- `subopt_abbrev_truth.json` is staged with `git add -f` and named by `TestTheFixture`.
- The registries and served guards are green (G4). The full run through the queue shows 0 failed.
- BUGS.md P1.19 is closed in place, `WP30_OPEN` has no `P1.19`, and both markers are replaced (G5).

## Notes

**Traps.**
- Re-grep every anchor at `batch-4-base`. S08 has rewritten the size lines of `_dash_apply_legend`, `_dash_apply_z_options` and `_dash_apply_axis_spec`, and S06 the note channel: notes in Stata use S06's helper, and Python notes stay `warnings` that pytest captures.
- Mata: no `regexm` (it follows the caller's version); echo user text only through `_dash_say` (memory: project_stata_cert_suite).
- `cert_file_has` clobbers `r()`, so read rc before calling it.
- A cscript drops globals.
- Concurrent Stata needs `STATATMP` with a trailing slash; the slot script does this.
- Check `~/.stata19/console/stata19.rc` still holds `python_exec` if a cscript SKIPs: a skip is not a pass.
- `_dash_check_legend` stays and still refuses `top`/`bottom`/`left`/`right`, with its hint, inside a segment before S10's check. Known limitation: in-segment `legend(po(9) top)` names `top` where twoway names `po()`. It predates this section.
- The fall-through re-spelling in `_dash_rep_subs` is what keeps `legend(cols(1) c(red)) legend(cols(2))` from being read as two `cols()` by the renderer. Test it in TP-14a terms if it is touched.
- `labelminlen` and `labelkeepleadingzero` take no abbreviation (lower case in Stata's `syntax`).

**Merge rules.**
- R1: SA cases are appended as one run after SR-09; TP-14a rows are appended in its own case; S10 writes only its own truth block.
- R2: anchors 32934 and 33370 are S10's alone in batch 4.
- R3: dash.sthlp :548-556, :615-632 and :780-786 are outside R3's S10 row (Axis and Display Options). This section edits only those sentences. S11 (merging second) shares the :780-788 paragraph and keeps S10's sentence. The merger records this in `<scratch>/batch-4-merge.log`.
- R4: two markers, replaced in place.
- R5: only S10's key line and entry are edited.
- R6: `version 19`; new Mata functions after `_dash_axreq_check`; `_needed` and the header index updated in place.
- R7: the new fixture is regenerated, never hand-patched.
- R8: CORPUS cases appended only.
- R9: four flips.

**Commit-body line forms.** As BRIEF D1 with WP-30 ids. `Regression:` lines name `<batch-4-base sha>`.

**CHANGELOG lines** (replace the markers in place):
- **Changed behaviour:** "`legend()` and the axis label and tick options (`xlabel()`, `ylabel()`, `xtick()`, `ytick()`, `xmlabel()`, `ymlabel()`, `xmtick()`, `ymtick()`, `zlabel()`) refuse what `twoway` refuses, with its return code and words, where `dash` named and ignored it:
  - a sub-option in capitals (`legend(OFF)`: `option OFF not allowed`, r(198));
  - a spelling `twoway` does not accept (`legend(po(9))`, `ylabel(, a(45))`, `legend(garbage)`);
  - one given twice in one option (`legend(c(2) cols(1))`: `option cols() not allowed`);
  - the wrong form (`ylabel(, labs)`: `option labs incorrectly specified`);
  - a bad `cols()`/`rows()`/`holes()` (`legend(c(red))`: r(121) `cols() invalid -- invalid number`);
  - a `label()` key that is no positive integer (r(198)).

  The titles and axis titles refuse the same three forms (`title("T", SIZE(small))`: `option SIZE() not allowed`, r(198)), and `ytitle("Y", prefix suffix)` is refused with `options prefix and suffix may not be combined`. A capitalised sub-option of `xline()`/`yline()` is no longer applied; it is named. (WP-30, P1.19)"
- **Fixed in WP-30:** "`twoway`'s sub-option abbreviations are read, in both modes and after any filter move:
  - in `legend()`: `c()`, `r()`, `lab()`, `posi()`, `s()`, `lastlab()`;
  - in the axis labels and ticks: `labs()`, `ang()`, `for()`, `g`, `nog`, `val`, `valuelabels`;
  - in `xline()`/`yline()`: `lc()`, `lp()`, `lw()`;
  - in the textboxes: `s()` is `size()`.

  Repeated copies merge by full name, the last winning, so `legend(lab(1 "A")) legend(lab(2 "B"))` keeps both. `rows()` beats `cols()`. In one copy `on` beats `off` and `grid` beats `nogrid`. Quoted label text is never read as a sub-option (`ylabel(10 "labsize(large)" 20)`). `legend(position(13))`, a non-numeric `ring()` and a non-integer `order()` word draw the default with `twoway`'s note. (WP-30, P1.19)"

**Notes for the closeout (S58; A145).**
- **GAPS2 B17 Tracked:** "Partly closed in WP-30 (S10, P1.19), commit <sha>: Stata's abbreviations are read and refused as twoway does. Open: holes(), colfirst, textfirst, stack, key gaps, symbol sizes, textwidth, region(), bplacement(), span and legend titles, still named (P2.5)." Append `(WP-30, GAPS2-B17-a)` to P1.19's Resolution.
- **GAPS2 B21 Tracked:** "Partly closed in WP-30 (S10, P1.19): labs/ang/for/g/nog/val/valuelabels are read; quoted label text is text. Open: labcolor, tick geometry and nolabels/noticks (S31), grid colour and pattern (P2.20)." Append `(WP-30, GAPS2-B21-d)`.
- **GAPS2 B22 Tracked:** "Partly closed in WP-30 (S10, P1.19): lc()/lp()/lw() are read. Open: numlists and refusals (S39), extend and style() (S50)." Append `(WP-30, GAPS2-B22-b)`.
- **REMAINING.md** REM-09-02-LABSIZE-ABBREV: Closed in WP-30, commit <sha>. **P2.20**'s REM-09-02-SUBOPT-IN-LABEL sub-claim (quoted label text read as a sub-option): Closed by S10.
- **DROPIN-REMAINING.md** P1.19: Closed (WP-30 S10).
- **ROADMAP** WP-30 row P1.19: DONE.
- **New P2 residuals:**
  - **R-S10-1.** `title("T", prefix suffix)`: twoway prints `option prefix ignored, may not be combined with suffix` as plain text and draws; dash draws without that line. (The refusals R-S10-1 used to hold are drawn into S10 by TR-10.6a.)
  - **R-S10-2.** `legend(label(1))` with no text blanks key 1 in twoway (probe l_label_1); dash keeps the default text.
  - **R-S10-3.** Values nested in `legend(region(…))` and `legend(title(…))` are not checked.
  - **R-S10-4.** In-segment `legend(po(9) top)` names `top` first.
