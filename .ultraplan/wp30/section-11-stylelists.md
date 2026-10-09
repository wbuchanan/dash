# Section 11: Stylelists of style options across an expanded varlist (P1.1 part a)

> Part of: WP-30 · Items: P1.1 part a (entry P1.1a) · Risk: yellow · Batch: 4 · Depends on: 02 · Blocks: 20, 32, 37, 40 · Tasks: 11, 1 commit · Case prefix: SL

## Review amendments

- Fixed (major): Q-11.1 is now a marked "Maintainer question" with a recommendation. M5 would refuse a used blank element, but twoway's words for it are an internal class path that changes with the option (B1-B5), so the plan's lenient default is an M5 exception the maintainer must ratify. Superseded: the maintainer answered Q-11.1 on 06oct2026 (see the ratification lines below).
- Fixed (minor): how `<cmd>` takes `nodraw name(g, replace)` and `saving()` is now stated: appended inside the command's own options, never after a second comma. The truth block erases its work files and drops its graphs before its end line.
- Fixed (minor): the shared-program note for `_dash_require_mata`'s `_needed` list. S10 appends after `_dash_axreq_check` (:255) and S11 after :250, which are separate lines, so the conflict is in context only. The merger keeps both.
- Checked: anchors at HEAD (`_dash_parse_plot_opts` syntax :924-926, `_dash_validate_opts` at :4125, the `_yi` loop at :4355-4359, `_needed` :245-255, the comment-count pin at test_abbreviations.py:624-625) match. Batch 4: no partner edits `_dash_parse_plot_opts`, `_dash_plot_opts_to_json`, `_dash_process_segment` or `_dash_opts_repeats`. S10's Mata edits are `_dash_rep_subkey`/`_subs`/`_merge` and new functions after `_dash_axreq_check`; S11 adds after `_dash_rep_toks`. M5: the misplaced `..` is refused in twoway's words; M6: padding is silent; M1: twoway's padding rule.
- The review pass applied both lenses.
- Changed (ratification 06oct2026): Q-11.1 answered "Refuse r(198)" (index.md row 32). A used blank (non-empty, whitespace-only) quoted stylelist element is refused r(198) with `dash: <option>() element <j> is blank; use . for the default (got: <value>)`, echoed through `_dash_say`; the lenient `.` reading, its SL-06/SL-09/SL-24 expectations, its help sentence, its BUGS residual and its S58 residual line are removed (BR-11.4, new BR-11.12, AC-11.11, US-11.5).
- Changed (ratification 06oct2026): scope is used elements only, as twoway refuses the blank form (R14 r(198), R15/B6 rc 0); a whole value of only `""` stays no value (BR-11.10).
- Changed (ratification 06oct2026): where it sits. New Mata `_dash_stylelist_blank(raw, n)` (TR-11.2; header and `_needed` entries, now six; coverage map SL-25) and a second pass in `_dash_stylelist_check` after the `..` pass and before the bounds rules (TR-11.7), so the refusal comes before any options object is written or drawn (TR-11.8). `_dash_stylelist_norm` now empties only a lone `""`/`` `""' `` and `_dash_stylelist_pick` no longer judges blanks.
- Changed (ratification 06oct2026): tests. SL-24 rewritten as the failing-first refusal case (leading, middle, compound-quoted, several blanks, blanks-only on another key, abbreviated trailing, single-y, `..`-first order; guards for unused, whole-`""` and empty `""` elements); SL-25 added (`_dash_stylelist_blank` unit); pytest `test_twoway_refuses_a_used_blank_element_only` and `test_the_blank_check_follows_the_dotdot_check` added, `test_the_five_are_public_and_needed` renamed `_six_`; two mutation rows. Counts: SL run SL-01..SL-25 (11-02 red 23, 11-05/11-06 unit PASS 12, 11-07 PASS 25), coverage entries eight, Mata functions seven. Tasks unchanged at 11.
- Changed (ratification 06oct2026, correction): the refusal is narrowed to a blank element, non-empty and whitespace-only (`" "`, `` `" "' ``). A used empty `""` element keeps twoway's reading, `.` (M5, IR-5; P10, T21, T22): T21/T22 are back in SL-15, SL-33 and `test_quoted_elements`, `"" ""` is back in SL-09's emptied list, `_dash_stylelist_blank` ignores empty text (SL-25), SL-24 tests `mcolor("" blue)` and ``mcolor(red `""')`` as rc 0 guards, and the help and CHANGELOG no longer state a `""` difference.
- Changed (ratification 06oct2026): CHANGELOG. The "Changed behaviour" line gains the blank-element refusal; S11 still writes two CHANGELOG lines (one per list), so no list count moves.

## Overview

**What is wrong today.** DROPIN-REMAINING.md P1.1 reads: "`scatter mpg turn weight, mcolor(red blue) msymbol(O T)` gives every y the whole list. The renderer then refuses "red blue" and draws scheme defaults, with a misleading note. The same holds for line style lists, the `.`/`=` shorthands, and a single-y list (where `twoway` uses the first element)." Sources: REM-S06-c, GAPS2-D8-a..e. GAPS2 D8 measured it: "dash.ado:4018-4030 copies the same options JSON onto every y's plot, so both series draw the scheme defaults with notes such as 'mcolor(red blue) is not a recognised colour'."

Measured at `c96facd` (probe `p7.do`, quoted under Evidence), the spec dash.ado writes:
- `mcolor(red blue) msymbol(O T)` on two y gives both plot objects `{'mcolor': 'red blue', 'msymbol': 'O T'}`. Both modes draw two navy-and-maroon circle series and print `dash: mcolor(red blue) is not a recognised colour; using the scheme's default.` twoway draws red circles, then blue triangles.
- `mcolor(red)` on two y colours both series red. twoway colours the first and pads the rest with `.` (the second is p2, #90353B).
- `mcolor("255 0 0" "0 0 255")` loses its quotes at `syntax MColor(string)`: both plots carry `255 0 0 0 0 255`.
- `mcolor(red .. blue)` is drawn with a note. twoway refuses it, `mcolor(red .. blue):  invalid syntax`, r(198).
- A single-y `mcolor(red blue)` draws the scheme's navy with a note. twoway draws red.
- An unquoted `mcolor(255 0 0)` draws red. twoway reads three elements and draws both series black with `named style 255 not found in class color` notes.

**After this section** dash reads every style option of `_dash_stylelist_keys()` as twoway reads a stylelist:
- element *k* styles the *k*-th y of an expanded varlist;
- `.` is the default, `=` repeats the previous element (`.` when first), and `..`/`...` repeat it to the end, glued forms (`red..`) included;
- a short list is padded with `.`, so a lone value styles only the first y (D1, M1, silent per M6), and extra elements are ignored;
- a quoted or compound-quoted element is one element (`"hsv 240 1 1"`, `*.5` and `navy*.5%50` stay whole);
- a plot type that takes one y uses the first element;
- a misplaced `..` is refused r(198) in twoway's words (M5);
- an unquoted RGB is three elements (D2);
- an element a y uses is held to the option's bounds as one value is;
- a quoted element that is blank (only blanks, not empty: `" "`, `` `" "' ``) and that a y uses is refused r(198) in dash's own words (Q-11.1, ratified 06oct2026). An empty quoted element, `""`, is `.`, as twoway reads it.

dash.ado writes one options object per expanded series. The renderers already draw each series from its own object, in both modes and after a filter move (measured), so nothing in `dash_render.py` changes.

**Why one section.** This is P1.1's style half (A138: P1.1a in S11, P1.1b in S20). The value lists `mlabel()`, `jitter()`, `base()` and `barwidth()` (sub-claim h) are S20's, and S20 builds on this section's splitter. S11 is the foundation S20, S32 (pstyle and the named styles), S37 (mlabtextstyle) and S40 (connect, cmissing) join: each adds its keys to `_dash_stylelist_keys()` and its declarations to the asis set.

**Test order and commit rule (rule 7, D1).** There is one cycle and one commit, `(WP-30 P1.1a)`.
- **11-01 to 11-03** write the regression tests (a new pytest module, an `SL` run in `test/test_varlist_expansion.cscript`, and S11's block of `test/test_wp30_truth.cscript`). Each runs against the unmodified tree, and the red text is saved to `<scratch>/11-P1.1a-failure.txt`. Nothing is committed.
- **11-04** writes the twoway fixture through a new extractor.
- **11-05 to 11-07** make the fix (Mata splitter, parser, check and writer).
- **11-08** flips the pinned count and appends the parity corpus and coverage-map entries. **11-09** turns everything green. **11-10** writes the help.
- **11-11** closes the entry and makes the one commit after one full run.

No test-only commit exists, and no commit is red.

## Risk: [yellow] — the parser every plot segment goes through gains 28 asis declarations, and every multi-y dashboard with one style value changes look

**Why.**
- `_dash_parse_plot_opts` parses every segment, and is re-run by `_dash_refuse_unbound`, `_dash_refuse_foreign` and `_dash_opts_repeats`.
- `string asis` keeps quotes and blanks, so `("")` becomes non-empty and `" large "` keeps its blanks (measured, Evidence).
- Every dashboard that gives one style value to several y changes: twoway styles the first y only, with no note (M1, M6).

**Risk factors.**
1. An emptiness test that sees `""` as "given": the pending list (`acolor()`..`alpattern()`), the folds, the JSON writer, and the repeats probe of `_dash_opts_repeats`, which reads the *last* copy of each name (`_dash_rep_scan`).
2. Quote stripping and JSE-69: a `$` or backtick inside an element must stay literal.
3. A new refusal (misplaced `..`; a used element out of bounds; a used blank quoted element) stops do-files that ran (M5, Q-11.1; CHANGELOG "Changed behaviour").
4. Comparisons with twoway that drift for reasons other than S11. P1.2, P1.4 and P1.12 change marker size, alpha and label defaults, and S08 has already landed (critic C8).
5. Batch-partner edits in the same files: dash.ado's `_needed` list and dash_parse.mata's header (S10, S12).

**Mitigation.**
1. One normaliser (`_dash_stylelist_norm`) runs right after `syntax`, before every emptiness test. The probe in `_dash_opts_repeats` re-keys an empty style copy. SL-09, SL-20 and SL-21 pin it.
2. The Mata functions read and write by value (`st_local`/`st_global`). SL-11 and JSE-69 run.
3. Only measured twoway refusals are added, each with its rc and words (SL-18, SL-19, SL-38), plus the one ratified refusal in dash's own words, a used blank quoted element (Q-11.1, SL-24). The CHANGELOG states them.
4. Tests compare colour, marker symbol, dash presence and key presence with twoway, never size or alpha.
5. Mata functions go after `_dash_rep_toks` (dash_parse.mata:4417), away from S10's `_dash_rep_subkey` (:5637). `_needed` gets its own continuation line. Notes cite R1, R3-R6.

## Dependencies

- **Depends on: 02.** S02 makes the extractors path-free (`DASH_REPO`, A130; IR-8). This section's new `scripts/extract_stylelist_truth.do` copies that converted form, and S02's guard test must pass on it. S01 provides:
  - the BUGS.md entry `P1.1a` and its `WP30_OPEN` key;
  - the markers `<!-- WP-30 P1.1a -->` in "Results that change" and "Changed behaviour" (`WP30_LISTS`);
  - the stub block `* ==== S11 P1.1a: … ====` in `test/test_wp30_truth.cscript`;
  - the map anchors `# WP-30 S11 (P1.1a): …` in `test/program_coverage_map.py`.
- **Landed before batch 4, and relied on:**
  - S03's `version 19` sweep (quoted programs below read `version 16.0` at `c96facd`);
  - S06's note channel: notes are `(note: …)` through `_dash_emit_note`, and tests count note text through S06's helpers (A150);
  - S08's size forms in `_dash_option_rules`/`_dash_validate_value`, which this section calls per element, unchanged.
- **Blocks: 20, 32, 37, 40.**
  - S20 adds `mlabel jitter base barwidth` to the list, with their per-element value checks and the mlabel shorthand rules (P1.1.6, P1.1.7).
  - S32 adds `pstyle mstyle lstyle mlstyle` (and S36's names).
  - S37 adds `mlabtextstyle`.
  - S40 adds `connect cmissing`.

  Each adds its names to `_dash_stylelist_keys()` and its declarations to the asis set, and calls nothing new.
- **Parallel batch: 4**, merge order S10, S11, S12.
  - **S10** edits the renderer's sub-option readers, the sub-option tables and Mata `_dash_rep_subkey`.
  - **S12** edits the `dash` dispatcher, the browser deciders, the `saving()` blocks, `_dash_validate_path` and `_dash_launch_app`.
- **Can run with:** S10 and S12. No partner edits `_dash_parse_plot_opts`, `_dash_plot_opts_to_json`, `_dash_process_segment`'s validation and assembly paragraphs, `_dash_opts_repeats` or `_dash_rep_toks`.

## Evidence

Anchors are at `c96facd` (dash.ado 8,487 lines; dash_parse.mata 6,093; dash_render.py 37,689; dash.sthlp 3,822). S01-S09 shift dash.ado lines a little (S03's guard at the top of `dash`, S08's rules). Symbols are authoritative when lines drift.

### What dash writes today (probe `p7.do`, 03oct2026, run as `scripts/stata_slot.sh <scratch>/s11-probe p7.do`; each graph registered with `name()` and its `$dash_json_<name>` written by Mata `fput`)

```
a1  scatter mpg turn weight, mcolor(red blue) msymbol(O T)
      [{'mcolor': 'red blue', 'msymbol': 'O T'}, {'mcolor': 'red blue', 'msymbol': 'O T'}]
a2  scatter mpg turn weight, mcolor(red)          [{'mcolor': 'red'}, {'mcolor': 'red'}]
a3  ... mcolor("255 0 0" "0 0 255")               [{'mcolor': '255 0 0 0 0 255'}, (same)]
a4  ... mcolor(red .. blue)       rc=0            [{'mcolor': 'red .. blue'}, (same)]
a5  line mpg turn weight, lwidth(thick 20000) rc=0 [{'lwidth': 'thick 20000'}, (same)]
a6  ... mcolor("")                                [{}, {}]
a7  ... acolor("")                                [{}, {}]            (no note)
a8  ... mcolor(red) mcolor("")                    [{'mcolor': 'red'}, {'mcolor': 'red'}]
                                                  + "dash: ignoring unsupported option(s): mcolor()"
a9  scatter mpg weight, mcolor(red blue)          [{'mcolor': 'red blue'}]
a10 ... mcolor(255 0 0)                           [{'mcolor': '255 0 0'}, (same)]
a11 ... mcolor(" " blue)                          [{'mcolor': '  blue'}, (same)]
```

The research's render of a1 (`.ultraplan/wp30/research/p1-01.md` §1, D01) gives glyphs #1a476f and #90353b, both circles, with `dash_render.py:8679: … mcolor(red blue) is not a recognised colour; using the scheme's default.` D10 (`line …, sort lpattern(solid dash) lcolor(red blue)`) draws both lines solid in scheme colours, with two notes.

### The code

The declarations, `_dash_parse_plot_opts` (program at dash.ado:897; `syntax` at :924-987):

```
925        MColor(string)            Msymbol(string)           MSIze(string) ///
926        MSAngle(string)           MFColor(string)           MLColor(string) ///
927        MLabel(string)            MLABColor(string)         MLABSize(string) ///
928        MLABPosition(string)      MLABGap(string)           MLABWidth(string) ///
929        MALpha(string)            MARKER(string)            LColor(string) ///
930        LWidth(string)            LPattern(string)          LALpha(string) ///
931        FColor(string)            FIntensity(string)        FAlpha(string) ///
932        AColor(string)            ALColor(string)           ALWidth(string) ///
```

They continue with `ALPattern(string)` (:933), `BLColor(string)` (:934), `BFColor(string)` (:935), `COLor(string) MLWidth(string)` (:951), `CLColor(string) CLPattern(string)` (:955) and `CLWidth(string) MLABANGle(string) MLABFormat(string)` (:956). The closing `]` is at :987 and `/* ---- plot-level ---- */` at :988.

`syntax`'s `string` strips quotes and blanks, and `string asis` keeps them. Probe `p2.do`, a two-option program `syntax [, A(string) B(string asis) *]`:

```
a("") b("")                    A=[] (0)            B=[""] (2)
a(`""') b(`""')                A=[] (0)            B=[`""'] (4)
a("" "") b("" "")              A=[ ] (1)           B=["" ""] (5)
a(red "0 0 255") b(same)       A=[red 0 0 255]     B=[red "0 0 255"]
a(`"red"' blue) b(same)        A=[red blue]        B=[`"red"' blue]
a(  red   blue  ) b(same)      A=[red blue]        B=[  red   blue  ] (14)
b("red)                        unmatched quote, r(198)   (string: the same)
```

The pending tests read emptiness, for example (dash.ado:1054-1056 and :1092):

```
1054    local _dash_pending ""
1055    if `: length local at' local _dash_pending `"`_dash_pending' at"'
1092    if `: length local acolor' local _dash_pending `"`_dash_pending' acolor"'
```

`alcolor`, `alwidth` and `alpattern` follow at :1093-1095. The folds read s() by value: `_dash_fold_bw` (:1545), `_dash_fold_cl` (:1654), `_dash_fold_mlab` (:1691), `_dash_fold_typed` (:1749).

The JSON writer, `_dash_plot_opts_to_json` (dash.ado:3131-3170), writes one value per key. The key list is at :3144-3157 and covers all 28 keys of this section:

```
3133    args out_macro
3144    foreach key in mcolor msymbol msize msangle mfcolor mlcolor mlabel mlabcolor ///
3145                   mlabsize mlabposition mlabgap mlabwidth malpha marker lcolor ///
3162        mata: st_local("val", st_global("s(" + st_local("key") + ")"))
3163        if `: length local val' {
3164            _dash_json_str `"`macval(val)'"' _jv
```

The assembly, `_dash_process_segment` (program at :3454), builds the object once at :4330 and repeats it for each y (:4355-4370):

```
4330    _dash_plot_opts_to_json _opts_json
4355    if `"`yvarlist'"' != "" {
4357        local _nyv : word count `yvarlist'
4358        forvalues _yi = 1/`_nyv' {
4364            local seg_json `"`seg_json'{"type":"`ptype'",`vfields',"options":`_opts_json',…}"'
4368    else {
4369        local seg_json `"{"type":"`ptype'",`vfields',"options":`_opts_json',…}"'
```

`yvarlist` is set before the options are parsed:
- tsline's series at :3826;
- the standard varlist's first `nv-1` words at :3856-3861;
- empty on every other path.

The validation call site (:4121-4126):

```
4121        _dash_fold_bw "`ptype'"
4125        _dash_validate_opts "`ptype'"
```

The rules (`_dash_option_rules`, :2025) give these keys a `style` kind: `msize=style mlabsize=style mlabgap=style lwidth=style,0,10000 mlwidth=style,0,10000 msangle=style,-360,360 mlabposition=style fintensity=style clwidth=style,0,10000`, plus the typed `alwidth=style,0,10000@…` and `mlabangle=style,-360,360@…`.

The `style` validator (:2261-2274) bounds only a value that reads as one number. A list such as `thick 20000` or `0 500` holds a blank, so it is neither a number nor "numlike", and it passes:

```
2268        if "`p1'" != "" & "`p2'" != "" {
2269            if `isnum' {
2270                if `R' < `p1' | `R' > `p2' local bad "a name or a number between `p1' and `p2'"
2272            else if `numlike' local bad "a name or a number between `p1' and `p2'"
```

The repeats probe, `_dash_opts_repeats` (:6110; loop at :6136-6143), keys each distinct option name by parsing its *last* copy alone (`_dash_rep_scan`, dash_parse.mata, `last[k] = toks[i]`):

```
6136    forvalues i = 1/`_rp_n' {
6139        capture `parser' , `macval(_rp_tok`i')'
6141        local _rp_sm : s(macros)
6142        mata: st_local("_rp_key`i'", _dash_rep_keyof(st_local("_rp_sm")))
```

That is why a8 (`mcolor(red) mcolor("")`) is misread. The last copy `mcolor("")` sets no s(), so it gets no key. Neither copy is reduced, `-syntax-` binds the first, and the second is named "unsupported". twoway draws both series at the default (probe `p2.do`, SVG `p2_2`).

Reused unchanged, Mata (dash_parse.mata):
- `_dash_rep_toks(s, 0)` (:4376-4417): words split at blanks outside quotes and parentheses, linear;
- `_dash_quote_step` (:1762);
- `_dash_rep_optname` (:4531), `_dash_rep_value` (:4546);
- `_dash_say` (echo by value, SMCL-escaped);
- `_dash_validate_value` (dash.ado:2125; rclass, never touches s()).

### Both modes read each plot's own options (no renderer change)

- Saved, `DashRenderer._make_figure_body` (dash_render.py:30203), per plot at :30428: `popts = plot.get("options", {})`.
- Served, the generated layer code in `ServerAppBuilder._generate_app_source` (:33915), emitted at :34935 `"        opts = plot.get('options', {})"`, and per by() panel at :35296.
- The research's `modes.py` (`p1-01.md` §3) rendered a hand-split spec (`lcolor` red/blue, `lpattern` solid/dash) in both modes. Both give `#ff0000 []` and `#0000ff [8, 4]` and no note.
- `move.py` fired a served RangeSlider move on per-series scatters (red T, blue O). Before and after: `[('#ff0000','triangle'), ('#0000ff','circle')]`.
- No module-level JavaScript string of `dash_render` assigns a glyph style. A scan for `.fill_color =`, `.line_color =`, `.marker =`, `.line_dash =`, `.fill_alpha =` and `.size =` over every module string longer than 200 characters found 0 hits (03oct2026).

So the saved filter JS never restyles a glyph, and there is no JS twin to write.

### twoway truth (StataNow 19.5)

From the research (`p1-01.md` §2, s2color: p1 #1A476F, p2 #90353B, p3 #55752F): T01-T45, U01-U41, W01-W36 and Y01, as listed there. The critic (C1-C8) adds:
- quoted `""` behaves as `.`;
- extras are ignored for style kinds;
- `msangle(0 500)` is rc 0 on one y and r(198) on two.

Probes run for this section (`<scratch>/s11-probe/p1.do`, `p3.do`-`p6.do`, 03oct2026, `twoway … , name(g, replace)`; the SVGs read with `scripts/svg_truth.py` `svg_marker_fills`):

```
P1  scatter mpg turn weight, mc(red .. blue)         mcolor(red .. blue):  invalid syntax   r(198)   (canonical name)
P2  scatter mpg weight, mcolor(red .. blue)           same words, r(198)                      (single y too)
P3  ... msymbol(O .. T)                               msymbol(O .. T):  invalid syntax        r(198)
P5  ... mcolor(red .. ..)                             r(198)        F5 mcolor(red.. ..): r(198)    F3 mcolor(.. red): r(198)
F2  ... mcolor("red" .. "blue")                       mcolor("red" .. "blue"):  invalid syntax (quotes echoed)
F1  ... mcolor(  red   ..   blue  )                   mcolor( red ..  blue ):  invalid syntax (blank runs not kept as typed)
P15 ... mcolor(red ..) mcolor(blue .. green)          mcolor(blue .. green):  invalid syntax  r(198)
P16 ... mcolor(red .. blue) mcolor(green)             rc 0   (only the copy twoway reads is checked)
P7  line mpg turn weight, lwidth(thick 20000)         gm_linewidth must be between 0.000 and  1.0e+04  r(198)
P8  line mpg weight, lwidth(thick 20000)              rc 0   (the extra is not used)
F9  scatter mpg turn trunk weight, msangle(0 0 500)   symbolangle must be between -360.000 and 360.000  r(198)
P10 scatter mpg turn weight, mcolor("" blue)          rc 0: #1a85ff (p1, stcolor), #0000ff
P11 ... mcolor("")                                    rc 0          p2_2 mcolor(red) mcolor(""): p1, p2
F12 ... mcolor(red `""')                              red, p2 (s2color)
P14 ... mcolor(red "..")                              rc 0, "(note:  named style .. not found in class color, …)" x2
p3_7 ... mcolor(255 0 0)                              both #000000; notes "named style 255 …" x2, "named style 0 …" x2
p3_8 ... mcolor("255 0 0" "0 0 255")                  #ff0000, #0000ff
p3_4 lfitci mpg weight, acolor(red blue) …            band #ff0000 (first element)
p3_5 bar mpg turn weight, bfcolor(red blue)           two fills, red-based then blue-based (positional)
E4  scatter mpg turn trunk weight, mcolor(red...)     all red        E5 mcolor(red....): "red." x3 (notes), black
E6  ... mcolor(red...blue)                            one element red...blue (black, note), then p2, p3
F4  ... mcolor(..)                                    p1, p2, p3     F6 mcolor(red = = blue): red x3
F7  ... mcolor(red . =)                               red, p2, p3
E7  ... mcolor(navy*.5 red%50)                        #8da3b7, #ff0000 at opacity 0.5, p3
B1-B5 a used blank quoted element: scatter …, mcolor(" " blue) / msymbol(" " T) / msize(" " large) / line … lcolor(" " blue)
      r(198) "option(s) marker(fillcolor(`')  linestyle(color(`'))) not allowed" (the class path differs by option:
      marker(symbol(`')), marker(size(`')), line(color(`')) area(linestyle(color(`'))))
B6  scatter mpg weight, mcolor(red " ")               rc 0  (the blank element is not used)
E1  ... mcolor(red=blue)  p1 p2 p3, no note;  E2 mcolor(red= blue): p1, blue, p3;  E3 mcolor(red =blue): "color.editstyle invalid name" r(198)
C11 ... mcolor((red) blue)                            option(s) ( red ) not allowed  r(198)
```

The dash side of the same forms at `c96facd` (`p1.do`):
- P18 `dash scatter mpg weight, msangle(500)` gives `dash: msangle() must be a name or a number between -360 and 360 (got: 500)`, r(198);
- P20 `lwidth(20000)` gives `dash: lwidth() must be a name or a number between 0 and 10000 (got: 20000)`, r(198);
- P21 `msangle(0 500)` on two y is rc 0 with `msangle(0 500) is not a recognised angle`.

### Blast radius (E4; the batch-4 base impact file records it)

| Symbol | Where | Callers | Risk |
|---|---|---|---|
| `_dash_parse_plot_opts` | dash.ado:897 | :4088, :4092 (`_dash_refuse_unbound`), :4101 (`_dash_refuse_foreign`), :4104 (`_dash_opts_repeats`), :6235; the parsers inside :6054, :6116, :6217 | `gitnexus impact … -d upstream -r dash`: "Target '_dash_parse_plot_opts' not found", UNKNOWN; HIGH by grep: every plot segment |
| `_dash_plot_opts_to_json` | :3131 | :4330 only | not found, UNKNOWN; MEDIUM by grep: every plot's JSON |
| `_dash_process_segment` (validation and assembly paragraphs) | :3454; :4125, :4330-4370 | :5210 | not found, UNKNOWN; HIGH by grep |
| `_dash_opts_repeats` (probe loop) | :6110; :6136-6143 | :4104, :5097 (graph parser; the new lines run for the plot parser only) | UNKNOWN; MEDIUM |
| `_dash_require_mata` (`_needed`) | :229; list :237-256 | every command | UNKNOWN; LOW (a list) |
| `_dash_stylelist_check` (new) | dash.ado, after `_dash_fold_typed`'s program | :4125+ | new |
| `_dash_stylelist_*` (new Mata) | dash_parse.mata after :4417 | dash.ado | new |
| `_dash_rep_toks`, `_dash_rep_optname`, `_dash_rep_value`, `_dash_say`, `_dash_validate_value`, `_dash_option_rules` | — | reused, not edited | — |
| `_apply_marker_opts`, `_dash_style_note` (dash_render.py) | — | not edited | impact: CRITICAL, 12 and 69 impacted (03oct2026) |

### Tests that pin today's behaviour

- **Flipped:** `test/test_abbreviations.py::test_the_tr_23_6_scans_see_what_they_look_for` pins `comments == {"_dash_parse_plot_opts": 108, "_dash_parse_graph_opts": 71}` (:619-620). The parser gains comment lines.
- **Guards that must stay green, unchanged:**
  - `test/test_help_claims_2.cscript` HC2-16e/f (`lwidth(())` stored `"()"`), HC2-16h, HC2-16p/q (`mcolor(255,0,0)` stored `"255,0,0"`; S30 flips them later);
  - `test/test_help_claims_2.py::TestTheHelpSaysWhatWasMeasured::test_the_values_dash_accepts_are_all_named` (needs `{cmd:mcolor(255,0,0)}` in the validation section);
  - `test/test_help_claims_2.py::TestAColourWrittenWithCommasIsReadAsTheTriplet::test_both_modes_draw_red_and_say_nothing`;
  - `test/test_json_escaping.cscript` JSE-69 (`mcolor("\$J6_G")` kept as typed);
  - `test/test_twoway_option_parity.cscript` TP-14 (repeats: `mcolor(red) mcolor(blue)`, `mc(red) mcolor(blue)`, `msymbol(O) msymbol(T)`);
  - `test/test_varlist_expansion.cscript` V2-01..V2-12;
  - `test/test_string_values.cscript` SV-04 (`mlabel(s)` on five y: mlabel is S20's, unchanged here);
  - `test/test_unsupported_report_is_true.py` (pending lists unchanged: no key leaves or joins the pending block).
- **Re-measured, not trusted:**
  - `grep` over `test/*.cscript`, `test/*.do` and `examples/*.do` finds no multi-y command with a style list or a lone style value (03oct2026). The only multi-y option use is SV-04's `mlabel`.
  - `_SINGLE_Y_BASELINE_SHA256` (`test_varlist_expansion.py:393-403`) is built from a Python spec, so this section does not move it.

## User stories

- **US-11.1** As a twoway user, I want `scatter mpg turn weight, mcolor(red blue) msymbol(O T)` to draw mpg in red circles and turn in blue triangles, so a pasted do-file draws as in Stata.
- **US-11.2** As a twoway user, I want `.`, `=`, `..` and `...` (glued too) to mean what they mean in twoway, and a lone value or short list to style only the leading y, so my lists behave as `[G-4] stylelists` says.
- **US-11.3** As a twoway user, I want a quoted RGB, `"hsv 240 1 1"`, `navy*.5` or `red%50` to stay one element, and an unquoted `255 0 0` read as three, as twoway reads them.
- **US-11.4** As a twoway user, I want a single-y plot type to take the first element of a list, as twoway does, instead of a note and the scheme's default.
- **US-11.5** As a twoway user, I want `mcolor(red .. blue)` refused in twoway's words, a used element out of bounds refused as a single value is, and a used blank quoted element (`mcolor(" " blue)`) refused with a message that tells me to write `.`, so a typo never draws silently.
- **US-11.6** As a dashboard publisher, I want each series' style kept in the saved page and the served app, before and after any filter move and in every by() panel.

## Business requirements

- **BR-11.1** For each style option the help's Style lists paragraph names (28 options), the *k*-th y of an expanded varlist is styled by the *k*-th element. Both modes draw twoway's colour, symbol and dash presence per series.
- **BR-11.2** The shorthands resolve as twoway resolves them:
  - `.` is the default;
  - `=` repeats the previous element, and as the first element means `.`;
  - `..` and `...` repeat the previous element to the end, as a word or glued to the end of an element (`red..`, `red...`; `red....` is `red.` then `...`);
  - a short list is padded with `.`, and elements past the last y are ignored.
- **BR-11.3** A lone value or a short list over several y styles only the leading y, and prints nothing (P1.1.1, M1, M6).
- **BR-11.4** A plain- or compound-quoted element is one element with one level of quotes removed. A quoted `"."` or `".."` is a literal element. An empty quoted element (`""`, `` `""' ``) is `.`, as twoway reads it (P10, T21, T22); a blank one is BR-11.12's. Colour arithmetic and opacity (`navy*.5%50`) and text with blanks inside quotes (`"hsv 240 1 1"`) reach the renderer whole.
- **BR-11.5** An unquoted `255 0 0` is three elements (P1.1.2). The help says to quote RGB.
- **BR-11.6** A plot type that draws one series (every type but the standard multi-y and tsline paths) takes the first element.
- **BR-11.7** A `..` or `...` that is not the last element of the copy twoway reads is refused with rc 198 and `<option>(<value>):  invalid syntax`. The option name is the full name whatever was typed; the value is as typed, quotes kept (P1.1.5, M5). Earlier copies that a later copy outranks are not checked.
- **BR-11.8** An element a y uses is held to its option's rule as a single value is (same message, rc 198). Elements that no y uses are not checked (P1.1.7).
- **BR-11.9** `malpha()`, `lalpha()`, `falpha()` and `jseed()` stay one value applied to every y (P1.1.3). So do `recast()`, `sort`, `yaxis()`, `xaxis()`, the colorvar family and every estimation option. The value lists of S20 and the named styles of S32/S36 are unchanged here.
- **BR-11.10** An option written twice keeps twoway's rightmost copy whole. An empty rightmost copy (`mcolor(red) mcolor("")`) gives the default, with no "unsupported" note.
- **BR-11.11** Everything above holds in the saved page and the served app, before and after a filter move, and in every by() panel. Plot numbering across segments is unchanged.
- **BR-11.12** (Q-11.1, ratified 06oct2026: "Refuse r(198)".) A plain- or compound-quoted element whose text is blank, meaning non-empty and only blanks (`" "`, `"   "`, `` `" "' ``), and that a y uses (its position *j* is at most the number of y; 1 on a single-y type) is refused with rc 198 before anything is drawn or written, with exactly one error line in dash's own words:
  `dash: <option>() element <j> is blank; use . for the default (got: <value>)`
  - `<option>` is the full name whatever was typed (`mc(" " blue)` echoes `mcolor()`), `<j>` the element's position, and `<value>` the value as stored, quotes kept, echoed through `_dash_say`. Example: `dash scatter mpg turn weight, mcolor(" " blue)` prints `dash: mcolor() element 1 is blank; use . for the default (got: " " blue)`, r(198).
  - Scope, "refuse what twoway refuses" for the blank form: twoway refuses a used blank element (B1-B5, R14) and accepts an unused one (B6, R15), so an element past the last y is not checked (`scatter mpg weight, mcolor(red " ")` draws red, rc 0), as BR-11.8 treats bounds.
  - An empty quoted element is not blank: `mcolor("" blue)` and ``mcolor(red `""')`` keep twoway's reading, `.`, drawn at the default (P10, F12, T21, T22; M5, IR-5: dash refuses only what twoway refuses).
  - A whole value of one empty quoted element and nothing else (`mcolor("")`, ``mcolor(`""')``) is an empty option, not a list element: it stays no value (BR-11.10, SL-20, SL-21), as twoway reads it (P11, p2_2).
  - A misplaced `..` in the same command is refused first, in twoway's words (BR-11.7).

## Technical requirements

- **TR-11.1 The key list, one place.** New Mata `string scalar _dash_stylelist_keys()` in dash_parse.mata, directly after `_dash_rep_toks` (after :4417). It returns these 28 names, blank-separated, in this order:
  `mcolor msymbol msize msangle mfcolor mlcolor mlwidth mlabcolor mlabsize mlabposition mlabgap mlabangle mlabformat lcolor lwidth lpattern clcolor clpattern clwidth color fcolor fintensity bfcolor blcolor acolor alcolor alwidth alpattern`
  - A comment above it names who adds later: S20 `mlabel jitter base barwidth`, S32 `pstyle mstyle lstyle mlstyle`, S37 `mlabtextstyle`, S40 `connect cmissing`.
  - Every name must be in `_dash_plot_opts_to_json`'s key list.
- **TR-11.2 The splitter** (Mata, after TR-11.1, in this order):
  - `string matrix _dash_stylelist_elems(string scalar raw)` returns a 2 x *k* matrix: row 1 the element's text, row 2 `"1"` when it came quoted and `"0"` when bare. A 2 x 0 matrix when raw is blank.
    - Tokens are `_dash_rep_toks(raw, 0)`.
    - A bare token longer than three characters that ends in `...` is cut into its stem and `...`. Otherwise a bare token longer than two that ends in `..` is cut into its stem and `..`. The cut is made before quotes are judged.
    - A token that is one plain-quoted string (`"…"`) or one compound-quoted string (`` `"…"' ``), judged by `_dash_quote_step`, loses one level of quotes and is marked quoted.
    - Nothing else is split: `..blue`, `red...blue`, `red=blue` and `(red)` stay whole.
  - `string scalar _dash_stylelist_norm(string scalar raw)` returns `""` when raw is blank or every element is quoted with empty text (`""`, `` `""' ``, `"" ""`). Otherwise it returns raw unchanged, so a value holding a blank element (`" "`, `" " blue`) reaches `_dash_stylelist_blank` (Q-11.1, ratified 06oct2026).
  - `string scalar _dash_stylelist_pick(string scalar raw, real scalar i)` returns the *i*-th y's element, `""` meaning "not given". It walks elements *j* = 1..*k* keeping `prev` (the previous resolved value, `""` at the start):
    - a bare `..` or `...` returns `prev` for every *i* ≥ *j*;
    - a bare `=` gives `prev`;
    - a bare `.` gives `""`;
    - any other element, quoted or bare, gives its text, so a quoted empty element gives `""` (`.`, as twoway reads it). Pick does not judge blanks: a used blank quoted element never reaches it, because `_dash_stylelist_check` refuses it first (BR-11.12).

    When *j* = *i* it returns that value; *i* > *k* returns `""`. It reads and returns by value. It is O(len(raw)).
  - `real scalar _dash_stylelist_bad(string scalar raw)` returns 1 when a bare `..` or `...` element (glued forms included) is not the last element; else 0.
  - `real scalar _dash_stylelist_blank(string scalar raw, real scalar n)` (Q-11.1, ratified 06oct2026) returns the smallest column *j* ≤ min(*n*, *k*) of `_dash_stylelist_elems(raw)` whose row 2 is `"1"` (quoted) and whose row-1 text is non-empty but `""` after `strtrim` (an empty `""` is not blank); 0 when there is none. A missing *n* or *n* < 1 reads as 1. It reads by value and is O(len(raw)). Columns count elements after the glued `..`/`...` cut; since a cut is only valid on the last token (else `_bad` refuses first), *j* equals the element's position as typed whenever the check reaches it.
  - `string scalar _dash_stylelist_probe(string scalar tok)` returns `<name>(x)` when `tok` is `<name>(<value>)` (`_dash_rep_optname` non-empty) and `_dash_stylelist_norm(<value>) == ""`; else `""`.
- **TR-11.3 Header and `_needed`.**
  - dash_parse.mata's Public API (`*!` header, after the `_dash_rep_reduce` entry at :110-113) gains six three-blank entries: `_dash_stylelist_keys()`, `_dash_stylelist_norm(raw)`, `_dash_stylelist_pick(raw, i)`, `_dash_stylelist_bad(raw)`, `_dash_stylelist_blank(raw, n)` and `_dash_stylelist_probe(tok)`. Each has a one- or two-line description. The pick entry ends "Helper _dash_stylelist_elems." (no parenthesis, so it is not a Public API line).
  - dash.ado's `_needed` (:237-256) gains one continuation line after :250 (`_dash_rep_keyof _dash_rep_reduce _dash_rep_merge_locals ///`): `        _dash_stylelist_keys _dash_stylelist_norm _dash_stylelist_pick _dash_stylelist_bad _dash_stylelist_blank _dash_stylelist_probe ///`.
  - `test_file_headers.py` and `test_program_coverage_map.py` then hold.
- **TR-11.4 Declarations.** In `_dash_parse_plot_opts`'s `syntax`, the 28 declarations of TR-11.1 become `(string asis)`: MColor, Msymbol, MSIze, MSAngle, MFColor, MLColor, MLWidth, MLABColor, MLABSize, MLABPosition, MLABGap, MLABANGle, MLABFormat, LColor, LWidth, LPattern, CLColor, CLPattern, CLWidth, COLor, FColor, FIntensity, BFColor, BLColor, AColor, ALColor, ALWidth, ALPattern. The capitalised minimums stay exactly as they are.
  - Nothing else changes type. In particular MLabel, JITter, BASE, BARWidth, PSTYle, MSTyle, LStyle, MLStyle, MLABTextstyle, Connect, CMISSing, MALpha, LALpha, FAlpha, JSEed, MLABWidth, MLPattern, MARKER and the dash alias MLG stay `(string)`.
- **TR-11.5 Normalise once, first.** Directly after the `syntax` block's `]` (:987) and before `/* ---- plot-level ---- */`, add:

  ```
  mata: st_local("_dash_slk", _dash_stylelist_keys())
  foreach _dash_slo of local _dash_slk {
      mata: st_local(st_local("_dash_slo"), _dash_stylelist_norm(st_local(st_local("_dash_slo"))))
  }
  ```

  It sits under a comment of at most six `//` lines saying why: asis keeps quotes so a stylelist's quoted elements survive; a value of empty quotes is no value, as `string` made it; and every emptiness test below, the folds, `_dash_validate_opts` and the JSON writer read the normalised value.
  - The fold forms (`_FOLD`, test_abbreviations.py:564) are not used, so `len(folds) == 11` holds.
  - The comment count of the plot parser moves from 108 (R9).
- **TR-11.6 The repeats probe.** In `_dash_opts_repeats`' loop (:6136-6143), after `_dash_rep_keyof`, re-key an empty style copy:
  - The condition: `_rp_key`i'` is empty and `parser` is `_dash_parse_plot_opts`.
  - Then: `_dash_stylelist_probe(_rp_tok`i')` is non-empty. Parse it alone (`sreturn clear`, `capture`) and take its `_dash_rep_keyof` key when that key is one word in `_dash_stylelist_keys()`.
  - `_dash_rep_reduce`, `_dash_rep_scan` and `_dash_rep_keyof` are not edited.
  - Result: `mcolor(red) mcolor("")` reduces to `mcolor("")`, which normalises to none, giving the default and no note (twoway, `p2_2`). `mcolor("") mcolor(red)` stays red.
- **TR-11.7 The check program.** New `program define _dash_stylelist_check` (not rclass or sclass; opens `version 19`; `args ptype nser`). It goes directly after `_dash_fold_typed`'s `end`.
  1. For each key of `_dash_stylelist_keys()` whose `s(<key>)` is non-empty (read with `st_global`), when `_dash_stylelist_bad` is 1: print `mata: _dash_say("err", "<key>(", <value>, "):  invalid syntax")`, where the value is as stored (asis, quotes and blanks kept), and `exit 198`. Keys are checked in list order.
  2. (Q-11.1, ratified 06oct2026.) Then a second pass over the same keys in list order, so every refusal in twoway's words comes first: when `j = _dash_stylelist_blank(s(<key>), nser)` is non-zero, print `mata: _dash_say("err", "dash: <key>() element <j> is blank; use . for the default (got: ", st_global("s(<key>)"), ")")` and `exit 198`. `<key>` comes from the fixed key list and `<j>` is a number, so only the value is user text, and it is read by value and SMCL-escaped by `_dash_say` (BR-11.12).
  3. Then `_dash_option_rules`. For each rule token of `_dash_rules_plot` whose option is in the list, with exactly `_dash_validate_opts`' applicability (a typed `@type` rule applies to its types and suppresses the untyped rule for them):
     - for *i* = 1..`nser`, take `e = _dash_stylelist_pick(s(<key>), i)`;
     - when `e` is non-empty, call `_dash_validate_value "dash" "<key>" "<spec>" `"`macval(e)'"' "`ptype'"`.

     So the message and rc are the single value's. Nothing is written back to s().
  - It reads by value and never puts an element on a command line except through `macval()` in the call form `_dash_validate_opts` already uses.
- **TR-11.8 Wiring.** In `_dash_process_segment`, directly after `_dash_validate_opts "`ptype'"` (:4125):

  ```
  local _sl_n 1
  if `"`yvarlist'"' != "" local _sl_n : word count `yvarlist'
  _dash_stylelist_check "`ptype'" `_sl_n'
  ```

  `_sl_n` is the standard varlist's y count or tsline's series count, and 1 on every other path (TR-11.10). The check therefore runs before `_dash_plot_opts_to_json` writes any options object, so a refused command registers no `$dash_json_<name>` and reaches neither renderer.
- **TR-11.9 One object per series.**
  - `_dash_plot_opts_to_json` takes `args out_macro series`, with `series` defaulting to 1. For a key in `_dash_stylelist_keys()` it reads `_dash_stylelist_pick(st_global("s(<key>)"), series)`. Every other key is read as today.
  - Key order and the "write when non-empty" rule are unchanged. A single plain value therefore gives byte-identical JSON (SL-21).
  - In `_dash_process_segment`: :4330 becomes `_dash_plot_opts_to_json _opts_json 1`, and the `_yi` loop (:4358) calls `_dash_plot_opts_to_json _opts_json `_yi'` as its first statement.
- **TR-11.10 Single-y types.** Every path whose `yvarlist` is empty writes series 1:
  - range, pc, univariate, immediate, function;
  - the fits, which have one y;
  - a standard varlist of one y.

  `_dash_stylelist_pick(raw, 1)` is the first element.
- **TR-11.11 Renderers.**
  - No change to `dash_render.py`.
  - No served copy-list change (index R2 row "S11: —"): `_glyph_layer_lines` constants (:32884-33039), functions (:33077-33425) and `_shared_stat_lines` (:33536-33590) are untouched.
  - No JS twin: `_FILTER_JS` and the saved CustomJS write no glyph style (Evidence).
- **TR-11.12 Maps.**
  - `test/program_coverage_map.py`, under S01's anchors `# WP-30 S11 (P1.1a): …`, alphabetically:
    - `COVERAGE["dash.ado"]["_dash_stylelist_check"] = ("test_varlist_expansion.cscript:SL-18", "test_varlist_expansion.cscript:SL-19", "test_varlist_expansion.cscript:SL-24")`;
    - `COVERAGE["dash_parse.mata"]`: `_dash_stylelist_bad` → SL-08, `_dash_stylelist_blank` → SL-25, `_dash_stylelist_elems` → SL-02, `_dash_stylelist_keys` → SL-01, `_dash_stylelist_norm` → SL-09, `_dash_stylelist_pick` → SL-03, `_dash_stylelist_probe` → SL-10 (each `"test_varlist_expansion.cscript:SL-nn"`).
  - `test/function_test_map.py` gains nothing (no Python function is added; S58 removes the empty anchor).
- **TR-11.13 Fixture.** New `scripts/extract_stylelist_truth.do` in S02's converted form (`DASH_REPO`, no maintainer path, no `arch` literal) writes `test/fixtures/stylelist_truth.json` ("Stata truth").
- **TR-11.14 Help.** `dash.sthlp`, "Differences from twoway" only (R3):
  - :786-789's last sentence becomes "A colour written with commas, {cmd:mcolor(255,0,0)}, which {cmd:twoway} refuses, {cmd:dash} reads as the triplet {cmd:255 0 0}; a triplet written with blanks is quoted, {cmd:mcolor("255 0 0")}, as in {cmd:twoway} (see {help dash##stylelists:Style lists})." The comma clause is kept for S30, which owns it.
  - A new `{phang2}` paragraph "Style lists" goes after :789 and before `{phang2}6.` (:791), with `{marker stylelists}` (Tasks 11-10 gives the text).
- **TR-11.15 Security (rule 1).**
  - Elements are user text. They are read by value in Mata and written to JSON only through `_dash_json_str`, so the renderer escapes them as today. They are never a Bokeh field name, never evaluated, never on a shell line.
  - Both refusals (the misplaced `..` and the blank element) echo the value through `_dash_say` (SMCL-escaped), read by value with `st_global`; the blank refusal's own words hold only the fixed key name and a number.
  - The splitter is linear, and the per-segment work is O(28 x `nser` x len). `nser` is bounded by the plots limit (`_dash_limit plots`, refused r(134) above it before any option is read).

## Boundaries

- **Not this section's (later sections, by the manifest):**
  - **S20 (P1.1b):** `mlabel()` lists, `jitter()`, `base()`, `barwidth()` and `mlabposition()` per-element value checks; the mlabel shorthand rules (P1.1.6) and extra-variable checks (P1.1.7's mlabel half); HC2-18b; help :740-742 and :3233.
  - **S32/S36:** pstyle and the named styles.
  - **S37:** mlabvposition and mlabtextstyle.
  - **S40:** connect() and cmissing().
  - **S30 (P1.13a):** colour grammar. It owns how an element is drawn: `navy*.5`, HSV, the comma form `"255,0,0"` (HC2-16p flip) and an unknown colour drawn black (P1.1.4's colour part, P1.13.1).
  - **S08/S13:** an unknown size drawn medium (P1.12.2) and the size and width units.
  - S11 only makes each element reach the renderer alone.
- **Batch 4 partners.**
  - S10's sub-option canonicaliser, its tables, `_dash_rep_subkey`, `_dash_apply_legend` and the axis readers.
  - S12's dispatcher prefix strip, `_dash_saving_parse`, browser deciders, `_dash_validate_path`, `_dash_launch_app` and the help's :452-470 and Dashboard Options paragraphs.
  - S11 touches none of them.
- **Not edited here:**
  - `dash_render.py` (`_apply_marker_opts`, `_apply_line_opts`, `_dash_style_note`: CRITICAL);
  - `_dash_validate_value`, `_dash_option_rules`, `_dash_validate_opts`, the folds;
  - Mata `_dash_rep_reduce`, `_dash_rep_scan`, `_dash_rep_keyof`, `_dash_rep_toks`;
  - `_dash_parse_graph_opts`;
  - the tracking documents (A145).
- **Out of scope, measured, left as residuals (Notes for the closeout):**
  - an unknown `msymbol` element draws the scheme's p# symbol where twoway draws a circle (P1.1.4's symbol part; no WP-30 section owns it);
  - glued `=` forms (`red=blue`: twoway draws p1-p3 silently; `red=`: default) and parenthesised elements (`(red)`: twoway r(198) "option(s) ( red ) not allowed") reach the renderer as one unknown element;
  - a refusal echo of `..` with runs of blanks differs from twoway's in blank count only (F1).
- **Decisions applied:** M1 (match the look: padding), M5 (misplaced `..`), M6 (no transition note), Q-11.1 as ratified 06oct2026 (a used blank quoted element refused r(198) in dash's words; BR-11.12), P1.1.1-P1.1.5 and P1.1.7 of the register; P1.1.6 is S20's.

## Stata truth

**Extractor** `scripts/extract_stylelist_truth.do` (new, committed):
- **Header.** It opens with the S02 form of `scripts/extract_join_order_truth.do`: `local repo : env DASH_REPO`, handled when unset exactly as S02's converted form handles it (no maintainer-path default). Then `adopath ++ "`repo'/"`, `global dash_nobrowser 1`, `clear all`, `set more off`, `version 19`, then `local entry_scheme "`c(scheme)'"` and `set scheme s2color`.
- **Provenance.** The `_meta` locals: `stata_version`, `born_date`, `dash_commit` (`shell git -C "`repo'" rev-parse HEAD > tempfile`, read with `file read`), `extracted`.
- **Data.**
  - `sysuse auto, clear` for every case;
  - `sysuse sp500, clear` then `tsset date` for U40;
  - the 2-y cases use `mpg turn weight` and the 3-y cases `mpg turn trunk weight`.
- **Per case.**
  - Open a text log under `c(pwd)` and run `capture noisily twoway <cmd> name(g, replace)`, where ` name(g, replace)` is appended inside `<cmd>`'s own options (after its comma; a comma is added first only when `<cmd>` has none). On by() cases `name()` goes after `by()`'s own options.
  - Close the log and record `_rc`.
  - When rc is 0, `graph export <id>.svg, replace`.
  - A pipe-separated record line `id|rc|cmd|svg|log` goes to a tempfile, as the join-order extractor does.
- **Python block** (`python:` … `end`; `sfi.Macro`; never `shell=True`; a backtick written as `\x60`). It reads each record and the log, and keeps:
  - `message`: the first line after the command echo that is not a note, not `r(…);` and not blank;
  - `notes`: every `(note: …)` line, kept as text.

  From the SVG (`sys.path` gets `<repo>/scripts`; `import svg_truth`) it keeps:
  - `markers`: `svg_marker_fills` as a list in document order, `[colour, n, {kind: count}]`;
  - `fills`: `svg_fills(elements=("rect","path"))` colours with n < 1,000, in document order;
  - `strokes`: every `<line>`/`<path>` stroke from `svg_document`, grouped in document order as `[colour, n_line, n_path]`, chrome colours included (`#000000`, `#ffffff`, `#eaf2f3`);
  - `radii`: the distinct circle radii per fill colour.

  It writes `{"cases": {id: record}, "scheme": "s2color", "_meta": {...}}` with `indent=2, sort_keys=True` to `<repo>/test/fixtures/stylelist_truth.json`. The block ends with `set scheme `entry_scheme'`.

**Cases** (`id: command`; the expected twoway reading from the measurements above in brackets, which the fixture must show):
- **Markers, two and three y:**
  - CTRL3 `scatter mpg turn trunk weight` [p1 p2 p3 = #1a476f #90353b #55752f];
  - T01 `scatter mpg turn weight, mcolor(red blue) msymbol(O T)` [red circle, blue path];
  - T02 `… mcolor(red)` [red, p2];
  - T03 `scatter mpg turn trunk weight, mcolor(red blue)` [red, blue, p3];
  - T04 `scatter mpg turn weight, mcolor(red blue green)` [red, blue];
  - T05 `mcolor(. blue)` [p1, blue];
  - T06 3-y `mcolor(red = blue)` [red red blue];
  - T07 3-y `mcolor(red ..)` [red x3];
  - T08 3-y `mcolor(red ...)` [red x3];
  - T12 `mcolor(= blue)` [p1, blue];
  - T13 3-y `mcolor(red..)` [red x3];
  - T14 3-y `mcolor(red....)` [3 notes naming `red.`];
  - T15 3-y `mcolor(. ..)` [p1 p2 p3];
  - T16 3-y `mcolor(red . =)` [red p2 p3];
  - T17 3-y `mcolor(red = = blue)` [red x3];
  - T18 3-y `mcolor(..)` [p1 p2 p3].
- **Quoted elements:**
  - T11 `mcolor("255 0 0" "0 0 255")` [red, blue];
  - T20 ``mcolor(`"red"' blue)`` [red, blue];
  - T21 `mcolor("" blue)` [p1, blue];
  - T22 ``mcolor(red `""')`` [red, p2];
  - T23 `mcolor(red) mcolor("")` [p1, p2];
  - T24 `mcolor(red "..")` [note `..`];
  - T25 `mcolor(navy*.5 red%50)` [#8da3b7, red at 0.5].
- **Other forms:**
  - Y01 `mcolor(255 0 0)` [black x2, notes 255 and 0];
  - U20 `mcolor(red blue) mfcolor(green)` [fills green, blue];
  - U21 `msize(large)` [two radii];
  - U19 `mcolor(red) mcolor(blue green)` [blue, green];
  - W21 `mcolor(red blue) mcolor(green)` [green, p2];
  - P16 `mcolor(red .. blue) mcolor(green)` [rc 0, green, p2];
  - BY `scatter mpg turn weight, mcolor(red blue) by(foreign)` [red, blue];
  - PN `(scatter mpg turn weight, mcolor(red blue)) (scatter price weight)` [red, blue, p3].
- **Lines:**
  - T10 `line mpg turn weight, sort lpattern(solid dash) lcolor(red blue)` [red solid, blue dashed];
  - W30 `connected mpg turn weight, sort lcolor(red) clcolor(. blue)` [red, blue lines];
  - W36 `line mpg turn trunk weight, sort lcolor(red) lpattern(. dash)` [red solid, p2 dashed, p3 solid];
  - U40 (sp500) `tsline open close, lcolor(red blue) lpattern(solid dash)` [red solid, blue dashed].
- **Single y:**
  - T09 `scatter mpg weight, mcolor(red blue)` [red];
  - T19 `scatter mpg weight, msymbol(T O)` [path];
  - T26 `lfit mpg weight, lcolor(red blue)` [red];
  - T27 `area mpg weight, sort color(red blue)` [red fill];
  - T28 `rcap mpg turn weight, lcolor(red blue)` [red];
  - T29 `lfitci mpg weight, lcolor(red green) fcolor(green red)` [fit red, band green];
  - T30 `lfitci mpg weight, acolor(red blue)` [band red];
  - T31 `histogram mpg, color(red blue)` [red];
  - T32 `scatteri 20 3000 25 4000, mcolor(red blue)` [red];
  - T33 `function y=x, range(0 1) lcolor(red blue)` [red];
  - T34 `bar mpg turn weight, bfcolor(red blue)` [two fills, positional].
- **Refusals and acceptances:**
  - R01 `mcolor(red .. blue)`;
  - R02 `mc(red .. blue)`;
  - R03 single-y `mcolor(red .. blue)`;
  - R04 `msymbol(O .. T)`;
  - R05 `mcolor(red .. ..)`;
  - R06 `mcolor(red.. ..)`;
  - R07 `mcolor(.. red)`;
  - R08 `mcolor("red" .. "blue")`;
  - R09 `mcolor(red ..) mcolor(blue .. green)`;
  - R10 `line mpg turn weight, lwidth(thick 20000)`;
  - R11 `line mpg weight, lwidth(thick 20000)` [rc 0];
  - R12 `msangle(0 500)` [r(198)];
  - R13 `scatter mpg weight, msangle(0 500)` [rc 0];
  - R14 `mcolor(red " ")` [r(198), the class-path message];
  - R15 `scatter mpg weight, mcolor(red " ")` [rc 0];
  - R16 `mcolor(  red   ..   blue  )` [the F1 echo].
- **Residual records:**
  - G01 3-y `mcolor(red=blue)`;
  - G02 3-y `mcolor(red= blue)`;
  - G03 `mcolor((red) blue)`.

**Run.**

```
mkdir -p <scratch>/s11/truth
DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s11/truth $WT/scripts/extract_stylelist_truth.do
```

The log is `<scratch>/s11/truth/extract_stylelist_truth.log`, and the run prints `wrote …stylelist_truth.json`. Then `git -C $WT add -f test/fixtures/stylelist_truth.json` (`.git/info/exclude:58`). `test/test_stylelists.py` names the fixture, so `test_fixtures_are_committed.py` passes unedited. The fixture is never patched by hand: a wrong record means re-running the extractor (R7).

**Truth block** (`test/test_wp30_truth.cscript`, between S01's `S11 start` and `S11 end` lines, gate `WP30_ONLY=S11`). Python helpers `_s11_page()`, `_s11_app()` and `_s11_svg()` sit at top level directly above `* ==== S11 P1.1a:`, copying the WP-29 `_jo_page_doc`/`_jo_app` pattern. They read:
- the saved page's Bokeh document;
- the generated served app, executed without serving: `make_document` on a fresh `Document`;
- the live twoway SVG through `svg_truth`.

Each helper sets the global `s11_dash`/`s11_tw` to the per-series list `colour/kind` (markers: `circle`, `triangle`, …; lines: `solid`/`dashed`). Stata program `_s11_case id cmd` runs `twoway <cmd>` with ` nodraw name(g, replace)` appended inside its options, then `graph export`. It then runs `dash <cmd>` with `` saving("`w30_work'/s11.html", replace) `` appended, then `dash <cmd>` with ` name(g1)` appended, then `` dash build, server saving("`w30_work'/s11.py") replace nobrowser ``, and compares. (Every option is appended after `<cmd>`'s own comma, never after a second one; a comma is added only when `<cmd>` has none.) The block erases its SVG, page and app files and drops `g` and `g1` before its end line. Cases (the scheme is set to s2color at the start of the block and restored at its end):
- **SL-30** T01 both modes: fills and marker kinds equal twoway's.
- **SL-31** T02, T03, T04: padding and extras, colours.
- **SL-32** T05-T08, T12, T13, T15-T18: shorthands, colours.
- **SL-33** T11, T20, T21, T22: quoted elements, colours.
- **SL-34** T10, W30, W36, U40: line colours and dashed/solid.
- **SL-35** T09, T19, T26-T33: single-y first element, colour or symbol.
- **SL-36** BY: each by() panel's two series, both modes.
- **SL-37** none of SL-30..SL-36's builds prints a note containing `not a recognised`, saved or served (S06's needle helpers).
- **SL-38** R01-R09: dash's rc and first error line equal twoway's, captured live. R16 equals in rc and in the words after `):`.

## TDD test stubs

### Regression tests, `test/test_stylelists.py` (new; red at the cycle's base unless marked guard)

Module constants:
- `_STYLE_KEYS` (the 28 of TR-11.1);
- `_NOT_YET` = `("mlabel","jitter","base","barwidth","pstyle","mstyle","lstyle","mlstyle","mlabtextstyle","connect","cmissing","malpha","lalpha","falpha","jseed","mlabwidth","mlpattern","marker")`;
- `_FIX = test/fixtures/stylelist_truth.json`;
- `_SERIES`: case id → `(ptype, yvars, xvar, [per-series option dicts], graph_options)`. These are the objects dash.ado writes, identical to the SL-12..SL-23 expectations. Examples:
  - T01 `[{"mcolor":"red","msymbol":"O"},{"mcolor":"blue","msymbol":"T"}]`;
  - T02 `[{"mcolor":"red"},{}]`;
  - T06 `[{"mcolor":"red"},{"mcolor":"red"},{"mcolor":"blue"}]`;
  - T11 `[{"mcolor":"255 0 0"},{"mcolor":"0 0 255"}]`;
  - T10 `[{"lcolor":"red","lpattern":"solid","sort":"sort"},{"lcolor":"blue","lpattern":"dash","sort":"sort"}]`.

  Every spec sets `scheme(s2color)`.

- `TestTheFixture`
  - `test_meta_is_stamped`: the four `_meta` keys exist and `stata_version` starts `19.`.
  - `test_every_case_is_recorded`: every id of "Stata truth" is present.
  - `test_twoway_styles_each_y_with_its_element`: T01's markers are red then blue, circle then path.
  - `test_a_lone_value_styles_the_first_y_only`: T02 red then p2.
  - `test_a_misplaced_dotdot_is_refused_by_its_full_name`: R01 and R02 rc 198 and message `mcolor(red .. blue):  invalid syntax`.
  - `test_twoway_refuses_a_used_blank_element_only` (Q-11.1, ratified 06oct2026): R14 (`mcolor(red " ")`, two y) rc 198 and R15 (one y) rc 0, the ground for BR-11.12's used-only scope.
- `TestTheParserKeepsQuotes`
  - `test_each_style_option_is_declared_asis`: the syntax block of `_dash_parse_plot_opts` declares each of `_STYLE_KEYS` with `(string asis)`.
  - `test_the_later_lists_are_not_yet_asis`: guard; each of `_NOT_YET` still `(string)`.
  - `test_empty_quotes_are_normalised_before_any_test`: the `_dash_stylelist_norm` loop is the first statement after the syntax block, before the first `: length local`.
- `TestOneList`
  - `test_the_mata_key_list_is_the_declared_set`: `_dash_stylelist_keys()`'s literal splits to `_STYLE_KEYS`.
  - `test_every_listed_key_reaches_the_json_writer`.
  - `test_the_six_are_public_and_needed`: header and `_needed`, `_dash_stylelist_blank` included.
- `TestOneOptionsObjectPerSeries`
  - `test_the_writer_takes_the_series`: `args out_macro series`.
  - `test_the_writer_is_called_inside_the_y_loop`: inside `forvalues _yi`, with `` `_yi' ``.
  - `test_the_check_runs_after_validation`: `_dash_stylelist_check` follows `_dash_validate_opts` in `_dash_process_segment`.
  - `test_the_repeats_probe_rekeys_an_empty_style_copy`: `_dash_stylelist_probe` inside `_dash_opts_repeats`' loop.
  - `test_the_blank_check_follows_the_dotdot_check` (Q-11.1, ratified 06oct2026): in `_dash_stylelist_check`'s body, `_dash_stylelist_blank` appears after `_dash_stylelist_bad` and before `_dash_option_rules`; its refusal line goes through `_dash_say("err", "dash: ` with the words `is blank; use . for the default (got: ` and is followed by `exit 198`; and `_dash_stylelist_check`'s call in `_dash_process_segment` precedes the first `_dash_plot_opts_to_json` call.
- `TestBothModesDrawTwowaysSeries` (renderer guards; red at base only because `_FIX` is absent)
  - `test_marker_lists` (T01, T03);
  - `test_padding_and_extras` (T02, T04);
  - `test_shorthands` (T05-T08, T12, T13, T15-T18);
  - `test_quoted_elements` (T11, T20-T22);
  - `test_line_lists` (T10, W30, W36);
  - `test_single_y_takes_the_first` (T09, T19, T26, T27, T31, T32);
  - `test_no_unrecognised_note`.

  Each builds `_SERIES[id]` through `DashRenderer` and `ServerAppBuilder` + `make_document` (`test_mode_parity._spec`/`_served`). It asserts the per-series fill or line colour (lower-case hex) and the marker (`circle` for an SVG circle, `triangle` for T) or dash presence (`line_dash` non-empty ⇔ twoway's colour has more `<line>` segments than `<path>` elements). It never asserts size, alpha or label style (critic C8).
- `TestAfterAFilterMove` (guards)
  - `test_served_range_move_keeps_each_series_style`: T01's series with `filter(weight, type(range))`, then `test_served_filter_move._move(doc, "RangeSlider", (2500.0, 4000.0))`; the before and after profiles are equal and the rows changed.
  - `test_saved_page_writes_no_glyph_style`: every `CustomJS.code` of the saved T01 page holds none of `.fill_color =`, `.line_color =`, `.marker =`, `.line_dash =`.
- `TestByPanels` (guard): `test_every_panel_draws_each_series_style`; T01's series under `by: foreign`, both modes; every panel red/circle then blue/triangle.
- `TestTheHelpSaysSo`
  - `test_the_stylelists_paragraph`: `{marker stylelists}`, `{cmd:mcolor(red .. blue):  invalid syntax}`, "is refused when a y uses it", "padded with {cmd:.}", "{cmd:malpha()}, {cmd:lalpha()}, {cmd:falpha()} and {cmd:jseed()}".
  - `test_rgb_is_quoted`: `{cmd:mcolor("255 0 0")}` in the validation section, and `{cmd:mcolor(255,0,0)}` still there.

### `SL` run in `test/test_varlist_expansion.cscript` (red at base unless marked guard)

One contiguous run before `// Summary`, headed `// SL: style lists (WP-30 P1.1a)`. Each case uses the script's `capture { … }` / `nfail` / `faillist` pattern and prints `SL-nn PASS: …`. A Mata helper `_sl_opts(spec, k)` (defined in the run's own `mata:` block) returns plot *k*'s options text: the text between its `"options":` and the following `,"if_expr"`. Specs are read by value, `st_global("dash_json_<name>")`. Quotes in Mata literals are `char(34)`.

- **SL-01** `_dash_stylelist_keys()`: 28 words, equal to TR-11.1's list, and none of `_NOT_YET`.
- **SL-02** `_dash_stylelist_elems`:
  - `red  blue` gives `red|0 blue|0`;
  - `"255 0 0" "0 0 255"` gives `255 0 0|1 0 0 255|1`;
  - `` `"red"' blue `` gives `red|1 blue|0`;
  - `red..` gives `red|0 ..|0`; `red...` gives `red ...`; `red....` gives `red. ...`;
  - `..blue`, `red...blue`, `red=blue` and `(red)` each stay one element;
  - `".."` gives `..|1`;
  - `navy*.5%50 "hsv 240 1 1"` gives `navy*.5%50|0 hsv 240 1 1|1`;
  - a blank raw gives 0 columns;
  - `" " blue` gives a one-blank text marked `1`, then `blue|0` (the blank kept; `_dash_stylelist_blank` judges it).
- **SL-03** pick, plain:
  - `red blue` at 1 and 2 gives red and blue, and at 3 gives `""`;
  - `red` at 2 gives `""`;
  - `red blue green` at 2 gives blue;
  - `""` raw at 1 gives `""`.
- **SL-04** pick, `.` and `=`:
  - `. blue` gives `""`, blue;
  - `red = blue` at 2 and 3 gives red, blue;
  - `= blue` at 1 gives `""`;
  - `red . =` at 3 gives `""`;
  - `red = =` at 3 gives red.
- **SL-05** pick, repeats:
  - `red ..` at 5 gives red; `red ...` at 2 gives red; `red..` at 3 gives red;
  - `. ..` at 3 gives `""`; `..` at 2 gives `""`;
  - `red....` at 2 gives `red.`.
- **SL-06** pick, quotes:
  - `"255 0 0" "0 0 255"` at 2 gives `0 0 255`;
  - `` `"red"' blue `` at 1 gives red;
  - `"." blue` at 1 gives `.`;
  - `"" blue` at 1 gives `""`;
  - `" " blue` at 1 gives the one-blank text ` ` (pick does not judge blanks; the check refuses first, BR-11.12);
  - `".." blue` at 1 gives `..`.
- **SL-07** pick, whole forms:
  - `255 0 0` at 1 and 2 gives 255 and 0;
  - `255,0,0` at 1 gives `255,0,0`;
  - `navy*.5%50 red` at 1 gives `navy*.5%50`.
- **SL-08** `_dash_stylelist_bad`:
  - 1 for `red .. blue`, `red ... blue`, `red.. ..`, `.. red` and `red .. ..`;
  - 0 for `red ..`, `red..`, `..`, `red "..." blue` and `red`.
- **SL-09** `_dash_stylelist_norm`:
  - `""` for `""`, `"" ""`, `` `""' `` and a blank raw;
  - unchanged for `" "` and `" " blue` (Q-11.1, ratified 06oct2026: they reach the blank check), and for `"" blue`, `red` and `.`.
- **SL-10** `_dash_stylelist_probe`:
  - `mcolor("")` gives `mcolor(x)`; `mc()` gives `mc(x)`;
  - `mcolor(red)`, `mcolor(" ")` (a non-empty copy keys itself), `mcolor` and `)(` give `""`.
- **SL-11** by value: an element holding `char(36)+"G"` and one holding a backtick come back literally. A raw of 20,000 `red` words gives element 20,000 at `red` and 20,001 at `""`, within 5 seconds.
- **SL-12** T01 spec (`dash scatter mpg turn weight, mcolor(red blue) msymbol(O T) name(sl12)`): plot 1 `{"mcolor":"red","msymbol":"O"}`, plot 2 `{"mcolor":"blue","msymbol":"T"}`.
- **SL-13** padding and extras:
  - `mcolor(red)` gives `{"mcolor":"red"}`, `{}`;
  - `line mpg turn weight, lwidth(thick)` gives `{"lwidth":"thick"}`, `{}`;
  - 3-y `mcolor(red blue)` gives red, blue, `{}`;
  - 2-y `mcolor(red blue green)` gives red, blue.
- **SL-14** shorthands: T05, T06, T07, T08, T12, T13 and T16 give the `_SERIES` objects.
- **SL-15** quoted: T11 gives `"255 0 0"`, `"0 0 255"`; `mcolor(navy*.5%50 "hsv 240 1 1")` gives `navy*.5%50`, `hsv 240 1 1`; T21 gives `{}`, blue.
- **SL-16** single y, one object with the first element:
  - `scatter … mcolor(red blue)`, `lfit … lcolor(red blue)`, `area … color(red blue)`, `rcap mpg turn weight, lcolor(red blue)`;
  - `lfitci … acolor(red blue)` gives `"acolor":"red"`;
  - `histogram mpg, color(red blue)`, `scatteri 20 3000 25 4000, mcolor(red blue)`, `function y=x, range(0 1) lcolor(red blue)`.
- **SL-17** unquoted RGB: 2-y `mcolor(255 0 0)` gives `"255"`, `"0"`; 1-y gives `"255"`.
- **SL-18** misplaced `..`: rc 198 and the first error line exactly:
  - `mcolor(red .. blue):  invalid syntax` for `mcolor(red .. blue)`, `mc(red .. blue)` and single-y;
  - `msymbol(O .. T):  invalid syntax`;
  - `mcolor(red.. ..):  invalid syntax`;
  - `mcolor("red" .. "blue"):  invalid syntax`;
  - `mcolor(red ..) mcolor(blue .. green)` gives `mcolor(blue .. green):  invalid syntax`;
  - guard inside: `mcolor(red .. blue) mcolor(green)` is rc 0.
- **SL-19** used elements:
  - `line mpg turn weight, lwidth(thick 20000)` gives rc 198, `dash: lwidth() must be a name or a number between 0 and 10000 (got: 20000)`;
  - `line mpg weight, lwidth(thick 20000)` gives rc 0 and `{"lwidth":"thick"}`;
  - 2-y `msangle(0 500)` gives r(198); 1-y gives rc 0;
  - 2-y `msize(small 1e400)` gives r(198) (the single value's own rule).
- **SL-20** repeats:
  - `mcolor(red) mcolor("")` gives `{}`, `{}` and no "ignoring unsupported" line in the log;
  - U19 gives blue, green;
  - W21 gives green, `{}`.
- **SL-21** guards (green at base):
  - `mcolor("")` gives `{}`, `{}`;
  - `acolor("")` on scatter: no note;
  - `lwidth(())` gives `"lwidth":"()"`;
  - `mcolor(255,0,0)` gives `"mcolor":"255,0,0"`;
  - `mcolor("\$G")` is stored as `$G` (with `$` in JSON);
  - single `mcolor(navy)` JSON is byte-identical to the base's.
- **SL-22** guard: `scatter mpg turn weight, malpha(50) recast(line) yaxis(2) sort` gives both plots carrying `malpha`, `recast`, `yaxis` and `sort` with equal values.
- **SL-23** by() and numbering:
  - `mcolor(red blue) by(foreign)` gives two plots red, blue;
  - PN gives plot 3 `{}`.
- **SL-24** used blank (whitespace-only) quoted element (Q-11.1, ratified 06oct2026; BR-11.12): rc 198 and the first error line exactly, through `cert_log_has` (saving `r()` first), and no `dash_json_sl24*` global set afterwards (refused before any options object is written, so nothing reaches either renderer):
  - leading, `dash scatter mpg turn weight, mcolor(" " blue) name(sl24a)`: `dash: mcolor() element 1 is blank; use . for the default (got: " " blue)`;
  - middle, `dash scatter mpg turn trunk weight, mcolor(red " " blue) name(sl24b)`: `dash: mcolor() element 2 is blank; use . for the default (got: red " " blue)`;
  - compound-quoted, ``dash scatter mpg turn weight, mcolor(`" "' blue) name(sl24c)``: ``dash: mcolor() element 1 is blank; use . for the default (got: `" "' blue)``;
  - several blanks, `dash scatter mpg turn weight, mcolor(red "   " blue) name(sl24d)` on three y (`mpg turn trunk weight`): `dash: mcolor() element 2 is blank; use . for the default (got: red "   " blue)`;
  - only blanks, another key, `dash scatter mpg turn weight, msymbol("   " T) name(sl24e)`: `dash: msymbol() element 1 is blank; use . for the default (got: "   " T)`;
  - trailing but used (twoway's R14), abbreviated, `dash scatter mpg turn weight, mc(red " ") name(sl24f)`: `dash: mcolor() element 2 is blank; use . for the default (got: red " ")`;
  - single y, `dash scatter mpg weight, mcolor(" ") name(sl24g)`: `dash: mcolor() element 1 is blank; use . for the default (got: " ")`;
  - order, `dash scatter mpg turn weight, mcolor(" " .. blue) name(sl24h)`: `mcolor(" " .. blue):  invalid syntax` (twoway's words first);
  - guards inside (rc 0): `dash scatter mpg weight, mcolor(red " ") name(sl24i)` gives `{"mcolor":"red"}` (unused, twoway's R15); `dash scatter mpg turn weight, mcolor(red blue " ") name(sl24j)` gives red, blue; `dash scatter mpg turn weight, mcolor("") name(sl24k)` gives `{}`, `{}`; `dash scatter mpg turn weight, mcolor("" blue) name(sl24l)` gives `{}`, `{"mcolor":"blue"}` and ``dash scatter mpg turn weight, mcolor(red `""') name(sl24m)`` gives `{"mcolor":"red"}`, `{}` (an empty element is `.`, as twoway reads it: P10, T21, T22).

  Red at base: `mcolor(" " blue)` is rc 0 there (probe `p7.do` a11).
- **SL-25** `_dash_stylelist_blank` (Q-11.1, ratified 06oct2026):
  - `" " blue` with *n* 2 gives 1; `red " " blue` with *n* 3 gives 2; `` `" "' blue `` gives 1; `"   " T` gives 1;
  - `red " "` with *n* 1 gives 0 and with *n* 2 gives 2; `red blue " "` with *n* 2 gives 0;
  - `" " blue` with *n* 0 or missing gives 1 (read as 1);
  - `"" blue`, ``red `""'``, `red blue`, `"." blue`, `".." blue`, `"hsv 240 1 1" red` and a blank raw give 0 (empty is not blank);
  - an element holding `char(36)+"G"` beside `" "` gives the blank's column, and the `$` text comes back literally from `_dash_stylelist_elems`.

### Truth block, `test/test_wp30_truth.cscript` S11

SL-30 to SL-38 as listed under "Stata truth". All are red at base except the twoway half of SL-38 (dash rc 0 at base).

### Flips (in place; R9; red at base after the edit where they assert new values)

- `test/test_abbreviations.py::test_the_tr_23_6_scans_see_what_they_look_for`: `"_dash_parse_plot_opts": 108` becomes the measured count, with `# 108 -> <n>: P1.1a explains the asis style options and their normalisation`. The docstring's measured-history sentence gains "and <n> after P1.1a's note on the style options' quotes (03oct2026)".

### Guards appended (green at base and after)

- `test/test_mode_parity.py`, appended at the end of each list under `# WP-30 P1.1a: one options object per expanded series` (R8):
  - `CORPUS`: `_case("stylelist series, markers", [plot_for("scatter", {"mcolor":"red","msymbol":"O"}, yvar="mpg"), plot_for("scatter", {"mcolor":"blue","msymbol":"T"}, yvar="turn")])` and `_case("stylelist series, lines", [plot_for("line", {"lcolor":"red","lpattern":"solid"}, yvar="mpg"), plot_for("line", {"lcolor":"blue","lpattern":"dash"}, yvar="turn")])`;
  - `MOVE_CORPUS`: `_move_case("stylelist series, dropdown", _MOVES[0], <the markers pair>)`.

  If `plot_for`'s default data lack `turn`, use the corpus's own second numeric column.

### Mutation table (each must turn a named test red)

| Mutation | Killed by |
|---|---|
| JSON written once again (call back outside the loop) | SL-12, `test_the_writer_is_called_inside_the_y_loop`, SL-30 |
| Recycle the last element instead of padding | SL-03, SL-13, SL-31 |
| Declare the keys `(string)` again | `test_each_style_option_is_declared_asis`, SL-15, SL-33 |
| `=` first repeats nothing and `.` is sent as text | SL-04, SL-14 |
| Normalisation removed | SL-09, SL-21 (`acolor("")` named) |
| Bounds checked on every element | SL-19 (single-y `lwidth(thick 20000)` rc 0) |
| Glued `..` not seen by `_bad` | SL-08, SL-18 (`red.. ..`) |
| Probe re-key removed | SL-20 |
| Blank check removed, or run on unused elements, or before the `..` check (Q-11.1) | SL-24 (leading and middle refused; `mcolor(red " ")` on one y rc 0; `mcolor(" " .. blue)` gives twoway's words), SL-25 |
| `_dash_stylelist_norm` still empties `" "` | SL-09, SL-24 (`mcolor(" ")` refused) |
| Blank test also catches an empty `""` | SL-25 (`"" blue` gives 0), SL-24 (`mcolor("" blue)` rc 0), SL-15, SL-33 (T21) |

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Mata splitter units | cscript SL-01..SL-11, SL-25 (`test_varlist_expansion.cscript`) | — | n/a |
| Spec per series, shorthands, quotes, single y, RGB | cscript SL-12..SL-17, SL-23 | — | spec feeds both |
| Refusals, used-element bounds, used blank elements | cscript SL-18, SL-19, SL-24; pytest `test_the_blank_check_follows_the_dotdot_check`, `test_twoway_refuses_a_used_blank_element_only` | — | n/a (refused before either mode) |
| Repeats and guards | cscript SL-20..SL-22 | — | n/a |
| Parser, list, writer structure | pytest `TestTheParserKeepsQuotes`, `TestOneList`, `TestOneOptionsObjectPerSeries` | — | n/a |
| Renderer draws twoway's series | pytest `TestBothModesDrawTwowaysSeries` | `stylelist_truth.json` | yes |
| After a filter move | pytest `TestAfterAFilterMove`; `test_mode_parity.py` MOVE_CORPUS | — | yes (saved JS scan; served move) |
| by() panels | pytest `TestByPanels`; truth SL-36 | fixture BY | yes |
| End to end against live twoway | truth SL-30..SL-38 | live SVG | yes (saved page and served app) |
| Help | pytest `TestTheHelpSaysSo`; `test_help_claims_2.py`; `test_help_examples.py` | — | n/a |
| Registries | `test_program_coverage_map.py`, `test_file_headers.py`, `test_no_orphans.py`, `test_function_test_map.py`, `test_fixtures_are_committed.py`, `test_tracking_documents.py` | — | n/a |
| Neighbours | cscripts `test_twoway_option_parity` (TP-14), `test_json_escaping` (JSE-69), `test_help_claims_2` (HC2-16); pytest `test_abbreviations.py`, `test_option_validation.py`, `test_twoway_option_parity.py`, `test_unsupported_report_is_true.py`, `test_mode_parity.py` | — | — |

**Acceptance criteria.**
- **AC-11.1** `dash scatter mpg turn weight, mcolor(red blue) msymbol(O T)` writes two options objects, red/O and blue/T. Both modes draw red circles then blue triangles, equal to twoway's SVG, with no note (SL-12, SL-30, SL-37).
- **AC-11.2** Every shorthand case of the fixture gives twoway's per-series colours in both modes (SL-32, `test_shorthands`).
- **AC-11.3** A lone value over several y styles only the first y and prints nothing (SL-13, SL-31).
- **AC-11.4** Quoted, compound-quoted and arithmetic elements reach the spec whole, and an unquoted RGB is three elements (SL-15, SL-17, SL-33).
- **AC-11.5** Each single-y type of SL-16 writes its first element and draws twoway's colour (SL-35).
- **AC-11.6** The misplaced-`..` refusals print twoway's line with rc 198, and a later outranking copy is not checked (SL-18, SL-38).
- **AC-11.7** A used out-of-bounds element is refused as the single value is. An unused one is accepted (SL-19).
- **AC-11.8** `mcolor(red) mcolor("")` draws the default with no note. The guards of SL-21 and SL-22 hold (SL-20).
- **AC-11.9** A served filter move and the saved filter JS leave every series' style unchanged, and by() panels draw each series' style in both modes (`TestAfterAFilterMove`, `TestByPanels`, SL-36).
- **AC-11.10** `dash_render.py` is unchanged (`git diff --stat` lists none), and the full suite and the S11 truth block are green.
- **AC-11.11** (Q-11.1, ratified 06oct2026) A used blank (whitespace-only) quoted element, leading, middle or compound-quoted, is refused r(198) with `dash: <option>() element <j> is blank; use . for the default (got: <value>)` before anything is written; an unused one, and an empty `""` element (`.`, as twoway reads it), are accepted; a misplaced `..` in the same value is refused first in twoway's words (SL-24, SL-25).

## Tasks

**Commit boundary.** Tasks 11-01 to 11-11 form the one P1.1a commit. Its subject is `Style each y of an expanded varlist with its own stylelist element (WP-30 P1.1a)`, made by 11-11 on `wp30-s11` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s11`, after one full run through the queue.
- The body opens with `<scratch>/11-P1.1a-failure.txt`, then gives the measured defect (Overview) and what changed where.
- It then carries one line each of:
  - `Regression: test/test_stylelists.py::<Class>::<test> -- failed at <batch-4 base sha> with <text>` (one per red pytest node);
  - `Regression: test/test_varlist_expansion.cscript SL-nn -- failed at <sha> with <text>` and `Regression: test/test_wp30_truth.cscript SL-nn -- …` (one per red case);
  - `Flipped: test/test_abbreviations.py::test_the_tr_23_6_scans_see_what_they_look_for -- 108 comment lines was wrong because the plot parser now explains its asis style options`;
  - `Fixture: test/fixtures/stylelist_truth.json (scripts/extract_stylelist_truth.do)`;
  - `BUGS.md: "<title of WP30_OPEN["P1.1a"]>" (closed)`.

Every command runs from `$WT`. `<scratch>` is the WP-30 scratch directory the orchestrator hands over. No body, BUGS or CHANGELOG line names a tool or vendor (G7).

<task type="auto" id="11-01">
  <name>Write the failing pytest module</name>
  <files>test/test_stylelists.py</files>
  <action><![CDATA[
    Check the cut: `git -C $WT rev-parse HEAD` equals `cat <scratch>/batch-4-base.txt`, and `git -C $WT branch --show-current` prints `wp30-s11`. Run `mkdir -p <scratch>/s11`. Confirm that `<scratch>/batch-4-impact.txt` holds the rows of Evidence "Blast radius", each UNKNOWN with its grep; append any missing row from `gitnexus impact <symbol> -d upstream -r dash` in the main checkout plus `grep -n`.

    Create `test/test_stylelists.py` with exactly the constants, classes and tests of "TDD test stubs / Regression tests, test/test_stylelists.py". Use these helpers:
    - `test_mode_parity._spec`, `_served`, `_standalone`;
    - `test_server_layer_defects.plot_for`;
    - `test_served_filter_move._figures`, `_move`;
    - S06's note-count helper for notes;
    - dash.ado and dash_parse.mata read as text with the program-body reader `test_abbreviations._program_body`.

    The module docstring quotes the defect (probe `p7.do`'s a1, a2, a3, a4, a9 lines) and the twoway reading (T01, T02, T23 of p1-01.md). `_SERIES` is the table of per-series objects, written out case by case, never computed. The fixture is read lazily by a module function `_fixture()` called inside each test (never at import), so a missing fixture fails those tests and lets the rest collect. Run `python3 -m pytest test/test_stylelists.py -q -n0 -p no:cacheprovider -rf > <scratch>/s11/11-01.log 2>&1`. Write `<scratch>/11-P1.1a-failure.txt` with the base sha, each failing node and its one-line reason, and the guard nodes that passed. Do not commit, and do not weaken a test to make it pass.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/s11/11-01.log` is at least 20; `grep -E "TestAfterAFilterMove|TestByPanels" <scratch>/s11/11-01.log | grep -c FAILED` prints 0 (the guards pass at base); `test -s <scratch>/11-P1.1a-failure.txt`.]]></verify>
  <done>The pytest regression module existed, its regression tests were shown failing on the unmodified tree with its renderer guards passing, and the failure text was saved.</done>
</task>

<task type="auto" id="11-02">
  <name>Write the failing SL cscript run</name>
  <files>test/test_varlist_expansion.cscript</files>
  <action><![CDATA[
    Append SL-01 to SL-25 of "TDD test stubs / SL run" as one contiguous run directly above the `// Summary` block (R1), headed `// SL: style lists (WP-30 P1.1a)`.
    - Define the run's own `mata:` block with `_sl_opts(spec, k)`, and read every spec by value with `st_global`.
    - Each dash command is `capture noisily` with its own log where a message is compared (`cert_log_has`, saving `r()` first).
    - Add the SL line to the header comment (`Tests: V2-01 through V2-12, SL-01 through SL-25`).

    Write the driver (`printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_varlist_expansion.cscript > <scratch>/s11/run_test_varlist_expansion.do`) and run it with `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s11 <scratch>/s11/run_test_varlist_expansion.do`. Append the `SL-nn FAIL` lines to `<scratch>/11-P1.1a-failure.txt` under `test_varlist_expansion.cscript`, and the passing guards under "guards".
  ]]></action>
  <verify><![CDATA[In `<scratch>/s11/run_test_varlist_expansion.log`: `grep -c "SL-[0-9][0-9] FAIL"` prints 23 (every case but the guards SL-21 and SL-22; SL-24 is red because base draws `mcolor(" " blue)`, SL-25 because `_dash_stylelist_blank` is absent); `grep -c "SL-2[12] PASS"` prints 2; `grep -c "V2-[0-9][0-9] FAIL"` prints 0.]]></verify>
  <done>The style-list cases were in the area script, every regression case failed on the unmodified tree, the guards passed, and V2-01..V2-12 were untouched.</done>
</task>

<task type="auto" id="11-03">
  <name>Write the S11 truth block red</name>
  <files>test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Put the python helpers `_s11_page`, `_s11_app` and `_s11_svg` (top-level `python:` block) and the Stata program `_s11_case` (opening `version 19`) directly above `* ==== S11 P1.1a:` (R1).
    - The python helpers follow the WP-29 `_jo_page_doc`/`_jo_app` pattern.
    - No Python line inside the gate holds a brace.

    Write SL-30 to SL-38 between S01's `S11 start` and `S11 end` lines. Each case ends `_w30_done SL-3k "<what>"`.
    - At the block's start, record `c(scheme)` and `set scheme s2color`; restore it at the end.
    - Every file goes under the scaffold's work directory.

    Run the driver for `test_wp30_truth.cscript` with `WP30_ONLY=S11` through `stata_slot.sh <scratch>/s11 …`, and append the `SL-3k FAIL` lines to the failure file.
  ]]></action>
  <verify><![CDATA[`grep -c "SL-3[0-8] FAIL" <scratch>/s11/run_test_wp30_truth.log` prints 9; `grep -c "S11 end" <scratch>/s11/run_test_wp30_truth.log` prints 1 (the block ran to its end); `grep -c "^r(9[0-9][0-9]);" <scratch>/s11/run_test_wp30_truth.log` prints 0.]]></verify>
  <done>twoway's own drawing was compared with both of dash's modes in one block that failed on the unmodified tree and ran to its end.</done>
</task>

<task type="auto" id="11-04">
  <name>Extract the stylelist truth fixture</name>
  <files>scripts/extract_stylelist_truth.do, test/fixtures/stylelist_truth.json</files>
  <action><![CDATA[
    Create `scripts/extract_stylelist_truth.do` as "Stata truth / Extractor" says, copying S02's converted `scripts/extract_join_order_truth.do` header form (`DASH_REPO`, the `_meta` capture, the record file, the python block). Its comment header names WP-30 P1.1a, the fixture and the run line. Write every case of "Cases" in that order. Run it with the "Run" command and `git -C $WT add -f test/fixtures/stylelist_truth.json`. Check the records against the bracketed expectations:
    - T01 markers `#ff0000` circle then `#0000ff` path;
    - T02 `#ff0000` then `#90353b`;
    - R01 and R02 message `mcolor(red .. blue):  invalid syntax`;
    - R10 message `gm_linewidth must be between 0.000 and  1.0e+04`;
    - R11 and R13 rc 0;
    - R14 rc 198 and R15 rc 0 (the used-only scope of Q-11.1's refusal);
    - Y01 two `#000000`-only series with notes naming 255 and 0;
    - T10's blue stroke has more `<line>` than `<path>`.

    A mismatch is reported, never patched: fix the extractor and re-run. Then run `python3 -m pytest test/test_stylelists.py -q -n0 -p no:cacheprovider -k "TestTheFixture or TestBothModes"`.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/stylelist_truth.json'));print(sorted(d['_meta']), len(d['cases']))"` prints the four `_meta` keys and 65; the pytest selection above reports 0 failed; `grep -c "arch -arm64\|/Users/billy" scripts/extract_stylelist_truth.do` prints 0; S02's path guard (its test over scripts/, test/ and the Makefile) passes.]]></verify>
  <done>twoway's stylelist readings were recorded in a stamped fixture by a path-free extractor, and the renderer guards passed against it in both modes.</done>
</task>

<task type="auto" id="11-05">
  <name>Add the Mata stylelist splitter</name>
  <files>dash_parse.mata</files>
  <action><![CDATA[
    Add, directly after `_dash_rep_toks`' closing brace (dash_parse.mata:4417), under a comment block naming WP-30 P1.1a, [G-4] stylelists' rules and the measured cases they follow (and, above `_dash_stylelist_blank`, that Q-11.1 was ratified 06oct2026 as a refusal in dash's own words, used elements only):
    - `_dash_stylelist_keys`, `_dash_stylelist_elems`, `_dash_stylelist_norm`, `_dash_stylelist_pick`, `_dash_stylelist_bad`, `_dash_stylelist_blank` and `_dash_stylelist_probe`, exactly as TR-11.1 and TR-11.2 specify;
    - quote detection through `_dash_quote_step`;
    - tokens from `_dash_rep_toks(raw, 0)`;
    - names from `_dash_rep_optname`/`_dash_rep_value`.

    Add the six Public API header entries of TR-11.3 after the `_dash_rep_reduce` entry. Edit nothing else in the file; in particular `_dash_rep_subkey` (S10) and `_dash_rep_reduce` are untouched. Re-run the SL cscript run with the driver of 11-02.
  ]]></action>
  <verify><![CDATA[In the new log, `grep -c "SL-\(0[1-9]\|1[01]\|25\) PASS"` prints 12; `python3 -m pytest test/test_file_headers.py test/test_no_orphans.py -q -n0 -p no:cacheprovider` reports only the failures naming the six new public functions as not in `_needed` (fixed by 11-06).]]></verify>
  <done>The splitter, key list and probe existed in Mata, documented in the header, and their unit cases passed.</done>
</task>

<task type="auto" id="11-06">
  <name>Declare the style options asis</name>
  <files>dash.ado</files>
  <action><![CDATA[
    In `_dash_parse_plot_opts`' `syntax`, change exactly the 28 declarations of TR-11.4 to `(string asis)`, keeping their names and minimums and the `///` continuations. Insert TR-11.5's normalisation loop and its comment (at most six `//` lines) directly after the syntax block's `]` and before `/* ---- plot-level ---- */`. In `_dash_opts_repeats`' loop, add TR-11.6's re-key of an empty style copy, with a three-line comment citing p2_2 (`mcolor(red) mcolor("")` draws the default). Add TR-11.3's continuation line to `_needed` after the `_dash_rep_keyof _dash_rep_reduce _dash_rep_merge_locals ///` line. Run `python3 -m pytest test/test_stylelists.py -q -n0 -p no:cacheprovider -k "TestTheParserKeepsQuotes or TestOneList"`, then the SL run.
  ]]></action>
  <verify><![CDATA[The pytest selection reports 0 failed; in the SL log `grep -c "SL-\(0[1-9]\|1[01]\|25\) PASS"` still prints 12 and `grep -c "V2-[0-9][0-9] FAIL"` prints 0 (the spec cases stay red until 11-07 writes one object per series; the raw asis value reaches the JSON in between, so no commit is made here).]]></verify>
  <done>The style options kept their quotes, empty quotes meant no value before every emptiness test, and an empty rightmost copy was reduced as twoway reduces it.</done>
</task>

<task type="auto" id="11-07">
  <name>Write one options object per series</name>
  <files>dash.ado</files>
  <action><![CDATA[
    Add the program `_dash_stylelist_check` of TR-11.7 directly after `_dash_fold_typed`'s `end`, opening `version 19`, under a comment that names the rule (twoway's misplaced-`..` words; then a used blank quoted element refused in dash's own words, Q-11.1 ratified 06oct2026; the single value's rule on each used element; extras unchecked). Wire it in `_dash_process_segment` as TR-11.8 says. Give `_dash_plot_opts_to_json` its `series` argument and the pick for listed keys (TR-11.9), adding to its header comment one sentence on the series argument. Make the :4330 call pass 1, and call the writer with `` `_yi' `` as the first statement of the `_yi` loop. Run the SL run and the truth block (`WP30_ONLY=S11`).
  ]]></action>
  <verify><![CDATA[`grep -c "SL-[0-9][0-9] FAIL" <scratch>/s11/run_test_varlist_expansion.log` prints 0 and `grep -c "SL-[0-9][0-9] PASS"` prints 25; `grep -c "SL-3[0-8] PASS" <scratch>/s11/run_test_wp30_truth.log` prints 9; `python3 -m pytest test/test_stylelists.py -q -n0 -p no:cacheprovider` reports 0 failed except TestTheHelpSaysSo.]]></verify>
  <done>dash wrote one options object per expanded series, refused a misplaced `..` in twoway's words and a used blank quoted element in its own, and held each used element to its rule, and both modes drew twoway's series.</done>
</task>

<task type="auto" id="11-08">
  <name>Flip the count and extend registries</name>
  <files>test/test_abbreviations.py, test/test_mode_parity.py, test/program_coverage_map.py</files>
  <action><![CDATA[
    Measure the plot parser's `//` comment lines (`python3 -c` with test_abbreviations' `_bodies`) and flip `test_the_tr_23_6_scans_see_what_they_look_for`'s 108 to it, with the R9/R10 comment and docstring sentence of "Flips". Append one `Flipped:` line to `<scratch>/s11/11-flips.txt`. Append the two `CORPUS` and one `MOVE_CORPUS` case of "Guards appended" at the end of each list under the comment `# WP-30 P1.1a: one options object per expanded series`. Do not edit `ALLOWED` or `_MUST_WARN`. Add TR-11.12's eight entries under S01's S11 anchors in `test/program_coverage_map.py`, alphabetically.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_abbreviations.py test/test_program_coverage_map.py test/test_file_headers.py test/test_no_orphans.py test/test_function_test_map.py -q -n0 -p no:cacheprovider` reports 0 failed; `python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider -k "stylelist"` reports 0 failed and at least 3 passed.]]></verify>
  <done>The pinned comment count named its new value with the reason, the parity corpus held the per-series objects in both modes and after a move, and the coverage map named each new unit's case.</done>
</task>

<task type="auto" id="11-09">
  <name>Run the neighbouring tests green</name>
  <files>none</files>
  <action><![CDATA[
    Run the pytest neighbours: `python3 -m pytest test/test_stylelists.py test/test_option_validation.py test/test_twoway_option_parity.py test/test_unsupported_report_is_true.py test/test_help_claims_2.py test/test_varlist_expansion.py test/test_fixtures_are_committed.py -q -n0 -p no:cacheprovider`. Then run through the driver, one at a time:
    - `test_twoway_option_parity.cscript` (TP-14);
    - `test_json_escaping.cscript` (JSE-69);
    - `test_help_claims_2.cscript` (HC2-16);
    - `test_string_values.cscript` (SV-04).

    Any red node outside the help test belongs to this section: diagnose it and fix the code, never the test, unless it is a pin listed under "Flips". In that case stop and report, because no other flip is planned. Write a one-line pass record per run to `<scratch>/s11/11-09.txt`.
  ]]></action>
  <verify><![CDATA[Every pytest run reports 0 failed apart from `TestTheHelpSaysSo` (green after 11-10); each cscript log shows its own pass summary and `grep -c " FAIL"` prints 0.]]></verify>
  <done>The parsers' neighbours, the repeat merge, the escaping guards and the help-claim cscripts stayed green with the style options asis.</done>
</task>

<task type="auto" id="11-10">
  <name>Write the style lists help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    Rewrite the last sentence of the paragraph at dash.sthlp:781-789 as TR-11.14 says. Insert after :789, before `{phang2}6.`, this paragraph (SMCL, wrapped as its neighbours are):

    `{phang2}    {marker stylelists}{ul:Style lists.}  A style option given a list styles the y variables of an expanded varlist in turn, as {cmd:twoway}'s {help stylelists:stylelists} do: {cmd:scatter mpg turn weight, mcolor(red blue) msymbol(O T)} draws {cmd:mpg} in red circles and {cmd:turn} in blue triangles.  {cmd:.} leaves that y at its default, {cmd:=} repeats the element before it ({cmd:.} when it comes first), and {cmd:..} or {cmd:...}, written alone or at the end of an element, repeats the element before it to the last y.  A list shorter than the y variables is padded with {cmd:.}, so a lone value styles only the first y ({cmd:line mpg turn weight, lwidth(thick)} thickens {cmd:mpg}'s line alone), and elements past the last y are ignored, values and all.  A plot type that draws one y uses the first element.  A quoted element is one element: an RGB colour is quoted, {cmd:mcolor("255 0 0")}, because {cmd:mcolor(255 0 0)} is a list of three colours, as in {cmd:twoway}.  {cmd:..} or {cmd:...} anywhere but at the end is refused as {cmd:twoway} refuses it, {cmd:mcolor(red .. blue):  invalid syntax}, r(198), and an element that a y uses is held to the option's bounds as a single value is.  An empty quoted element, {cmd:""}, is a {cmd:.}, as in {cmd:twoway}.  A quoted element of blanks, {cmd:" "}, is refused when a y uses it: {cmd:scatter mpg turn weight, mcolor(" " blue)} stops with {cmd:dash: mcolor() element 1 is blank; use . for the default (got: " " blue)}, r(198); write {cmd:.} for the default.  {cmd:twoway} also refuses a used blank element, with a different message; an element past the last y is not checked.  The options read this way are {cmd:mcolor()}, {cmd:msymbol()}, {cmd:msize()}, {cmd:msangle()}, {cmd:mfcolor()}, {cmd:mlcolor()}, {cmd:mlwidth()}, {cmd:mlabcolor()}, {cmd:mlabsize()}, {cmd:mlabposition()}, {cmd:mlabgap()}, {cmd:mlabangle()}, {cmd:mlabformat()}, {cmd:lcolor()}, {cmd:lwidth()}, {cmd:lpattern()}, {cmd:clcolor()}, {cmd:clpattern()}, {cmd:clwidth()}, {cmd:color()}, {cmd:fcolor()}, {cmd:fintensity()}, {cmd:bfcolor()}, {cmd:blcolor()}, {cmd:acolor()}, {cmd:alcolor()}, {cmd:alwidth()} and {cmd:alpattern()}; {cmd:malpha()}, {cmd:lalpha()}, {cmd:falpha()} and {cmd:jseed()}, which {cmd:twoway} does not have, apply one value to every y.`

    The blank-element sentence is Q-11.1's ratified ruling (06oct2026: refuse r(198) in dash's own words, used elements only). Then run `python3 -m pytest test/test_stylelists.py test/test_help_claims_2.py test/test_help_examples.py -q -n0 -p no:cacheprovider`.
  ]]></action>
  <verify><![CDATA[That run reports 0 failed; `grep -c "{marker stylelists}" dash.sthlp` prints 1; `grep -c '{cmd:mcolor(255,0,0)}' dash.sthlp` is at least 1.]]></verify>
  <done>The help said how style lists are read, what is refused (a misplaced `..`, an out-of-bounds or blank used element), which options take them and that RGB is quoted, and the help-claim tests held it.</done>
</task>

<task type="auto" id="11-11">
  <name>Close the entry and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Close the BUGS.md entry whose title is `WP30_OPEN["P1.1a"]`, in place: `- [x]`, and its Resolution `- Resolution: Fixed <ddmonyyyy> (WP-30, P1.1a).` followed by the text of "Notes / BUGS.md Resolution". Delete only the `"P1.1a"` key line of `WP30_OPEN` (R5).

    Replace the two `<!-- WP-30 P1.1a -->` markers in place with the lines of "Notes / CHANGELOG lines": the "Results that change" line and the "Changed behaviour" line, each ending `(WP-30, P1.1a)`.

    Then, in order:
    1. Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`.
    2. Run `git -C $WT merge --no-edit main`, expecting `Already up to date.`.
    3. Run one full suite through the queue, `<scratch>/full_suite_queue.sh $WT <scratch>/11-full-1.log`, launched in the background. Wait for its `exit=` line and read the log (E1, E6).
    4. Check G6 (`git -C $WT diff --cached --name-status` holds only this section's files) and G7 on the message file.
    5. `git -C $WT add -f test/fixtures/stylelist_truth.json` plus the other changed files.
    6. Commit once with the subject and body of "Commit boundary", then run G7 on `git -C $WT log -1 --format=%B`.
  ]]></action>
  <verify><![CDATA[`grep -c "exit=0" <scratch>/11-full-1.log` prints 1 and the log shows 0 failed; `grep -c '<!-- WP-30 P1.1a -->' CHANGELOG.md` prints 0; `grep -c '^    "P1.1a": "' test/test_tracking_documents.py` prints 0; `git -C $WT log -1 --format=%s` ends `(WP-30 P1.1a)`; `git -C $WT log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `git -C $WT show --stat --format= HEAD -- dash_render.py` prints nothing.]]></verify>
  <done>The P1.1a entry was closed with tests that exist, its CHANGELOG markers carried the before and after, and one green commit landed the section on its branch.</done>
</task>

## Section completion criteria

- [ ] One commit on `wp30-s11`, subject ending `(WP-30 P1.1a)`, made after one green full run through the queue. Its body carries the failure text, the regression lines, the flip line, the fixture line and the BUGS line.
- [ ] `test/test_stylelists.py` green. SL-01..SL-25 print PASS in `test_varlist_expansion.cscript`. SL-30..SL-38 print PASS with `WP30_ONLY=S11`, with no SKIP.
- [ ] `test/fixtures/stylelist_truth.json` committed with `git add -f`, its `_meta` holding the four keys, written by the committed `scripts/extract_stylelist_truth.do` (path-free).
- [ ] dash.ado:
  - 28 `string asis` declarations and the normalisation loop;
  - the repeats re-key;
  - `_dash_stylelist_check`;
  - `_dash_plot_opts_to_json`'s series argument and the per-`_yi` call;
  - `_needed`.
- [ ] dash_parse.mata: seven functions and six header entries. dash_render.py unchanged.
- [ ] `test_abbreviations.py` count flipped with its reason. `test_mode_parity.py` corpus extended. `program_coverage_map.py` entries under S11's anchors.
- [ ] dash.sthlp: the Style lists paragraph and the quoted-RGB sentence.
- [ ] BUGS.md entry closed, `WP30_OPEN["P1.1a"]` deleted, both CHANGELOG markers replaced.
- [ ] No file of S10 or S12 touched. No plan file, `CLAUDE.md`, `.gitignore` or `AGENTS.md` staged.

## Notes

**Traps for the executor.**
- **Anchors are at `c96facd`.** S03 changed every `version 16.0` to `version 19`. S06 moved notes to `_dash_emit_note` and the `(note: …)` form, so test needles follow S06's helpers. S08 changed `_dash_option_rules`/`_dash_validate_value` for size forms. Re-read those programs at the batch-4 base before 11-06 and 11-07. Symbols govern, not line numbers.
- **`string asis` keeps blanks** (`" large "`) and quotes. Everything downstream must read `_dash_stylelist_pick`'s element, never the raw value, except the `..` and blank-element refusal echoes, which are the raw value on purpose (twoway echoes quotes).
- **The blank check is a second pass, used elements only** (Q-11.1, ratified 06oct2026). It runs after every key's `..` test and before the bounds rules, and it takes `nser`, never the element count: `scatter mpg weight, mcolor(red " ")` must stay rc 0 (twoway's R15). Do not move it into `_dash_stylelist_norm` (that would refuse unused elements and the whole-value `""` that BR-11.10 keeps), and do not let `_dash_stylelist_pick` return `""` for a blank element (that was the struck lenient reading).
- **`_dash_rep_scan` keeps the last copy of each name.** This is why the probe re-key exists. Do not "fix" it in `_dash_rep_scan` or `_dash_rep_reduce`: S10 edits the neighbouring `_dash_rep_subkey` in the same batch, and both are Mata hot spots.
- **`_dash_validate_value` is called per element through the same compound-quote call form `_dash_validate_opts` uses.** It reads its arguments by value (`_dash_text_args`), so an element holding `"'` is safe. Never build the call from a plain-quoted element.
- **No `s()` side effects.** `_dash_stylelist_check` is neither rclass nor sclass and calls no sclass command. `_dash_validate_value` is rclass and does not touch s(). The JSON writer runs after the check, so s() must arrive intact (SL-12..SL-17 catch a loss).
- **Size, alpha and label defaults move in other sections** (S08 landed; P1.2, P1.4 and P1.12b come later). Never compare `msize`, `lwidth` values, alpha or label style with twoway. Compare key presence, colour, symbol and dash only.
- **twoway's default scheme on this Mac is stcolor** (probe `p2.do` drew #1a85ff/#d41159). The extractor and the truth block set `s2color` and restore the entry scheme. The pytest specs set `scheme(s2color)`.
- **No served copy-list entry and no JS twin**, because no renderer code changes. If a test shows a renderer difference, stop and report (R12: `_apply_marker_opts` and `_apply_line_opts` have one editor per batch, and S11 is not it in batch 4).
- **Merge rules.**
  - R1: the SL run is one contiguous block at the end of `test_varlist_expansion.cscript`. Helpers go only above S11's own truth header. If S12 appends to the same area script, S11 lands first.
  - R3: help edits only in "Differences from twoway", at :786-789 and the new paragraph. S12 edits :452-470 of the same title, S20 :740-742 later.
  - R4: only the two P1.1a markers.
  - R5: only the P1.1a entry and key line.
  - R6: the 28 keys and six Mata functions are added by no partner. If S12 adds a Mata function, `_needed` conflicts in context only, and the merger keeps both lines.
  - R7: the fixture is regenerated only by its extractor.
  - R8: append-only corpus.
  - R9: the one flip.
  - R10 does not apply: the single-y digest does not move, and no pending or declared count moves, because no option is added or removed.
- **Maintainer question Q-11.1 — answered 06oct2026 (index.md row 32), CHANGED: "Refuse r(198)".** A used quoted element that is blank, non-empty and only blanks (`mcolor(" " blue)`, ``mcolor(`" "' blue)``), is refused with rc 198 and dash's own message, `dash: <option>() element <j> is blank; use . for the default (got: <value>)`, not twoway's per-option internal class-path words (B1-B5: `option(s) marker(fillcolor(`')  linestyle(color(`'))) not allowed` for mcolor, `marker(symbol(`'))` for msymbol, `line(color(`')) area(linestyle(color(`')))` for lcolor), and is never read as `.`. Scope follows "refuse what twoway refuses" for the blank form: only an element some y uses is refused (twoway: R14 r(198) on two y, R15/B6 rc 0 on one y). An empty element, `""`, is not blank and keeps twoway's reading, `.` (P10, F12, T21, T22; M5, IR-5), and a whole value of only `""` is no value (BR-11.10). Where: Mata `_dash_stylelist_blank` finds the element; the ado check `_dash_stylelist_check` refuses it in a second pass after the `..` pass, before the bounds rules and before `_dash_plot_opts_to_json` writes anything, so nothing is drawn in either mode (TR-11.7, TR-11.8, BR-11.12). Tests: SL-24 (refusals, guards), SL-25 (unit), `test_twoway_refuses_a_used_blank_element_only`, `test_the_blank_check_follows_the_dotdot_check`.
- **Commit-body line forms** are those under "Commit boundary". The failure file is `<scratch>/11-P1.1a-failure.txt`, and flips are in `<scratch>/s11/11-flips.txt`.

**BUGS.md Resolution** (11-11; one line after `Fixed <ddmonyyyy> (WP-30, P1.1a).`): "dash.ado declares the 28 style options that `_dash_stylelist_keys()` lists as `string asis` in `_dash_parse_plot_opts` and reads a value of only empty quotes as none there and in `_dash_opts_repeats`' probe. `_dash_stylelist_check` refuses a `..` or `...` that is not last, as twoway does, `<option>(<value>):  invalid syntax`, r(198), then refuses a blank (whitespace-only) quoted element that a y uses, `dash: <option>() element <j> is blank; use . for the default (got: <value>)`, r(198), and holds every element a y uses to the option's rule. `_dash_plot_opts_to_json` writes one options object per expanded series through the Mata splitter `_dash_stylelist_pick` (`.`, `=`, `..`, `...`, padding with `.`, quoted elements whole, the first element on a single-y type). The renderers are unchanged and draw each series' own element in the saved page and the served app, before and after a filter move and in every by() panel. Pinned by test/test_stylelists.py::TestOneOptionsObjectPerSeries::test_the_writer_is_called_inside_the_y_loop, test/test_stylelists.py::TestBothModesDrawTwowaysSeries::test_marker_lists, test/test_stylelists.py::TestBothModesDrawTwowaysSeries::test_shorthands, test/test_stylelists.py::TestAfterAFilterMove::test_served_range_move_keeps_each_series_style, test/test_varlist_expansion.cscript SL-12, test/test_varlist_expansion.cscript SL-18, test/test_varlist_expansion.cscript SL-24, test/test_wp30_truth.cscript SL-30; fixture test/fixtures/stylelist_truth.json. Residual, deferred (WP-30): mlabel(), jitter(), base(), barwidth() and mlabposition() value checks are P1.1b; pstyle(), mstyle(), lstyle() and mlstyle() join with P1.14a, mlabtextstyle() with P1.24, connect() and cmissing() with P1.8a; an unknown msymbol element draws the scheme's symbol where twoway draws a circle; glued = forms (red=blue, red=) and parenthesised elements reach the renderer as one unknown element."

**CHANGELOG lines** (11-11; each replaces its marker in place):
- **Results that change:** "`dash scatter mpg turn weight, mcolor(red blue) msymbol(O T)` now draws mpg in red circles and turn in blue triangles, as twoway's stylelists do. Each series used to get the whole list, so both fell back to the scheme's colour and symbol with "not a recognised colour" notes. A lone value or a short list over several y now styles only the leading y, silently, as in twoway: `dash line mpg turn weight, lwidth(thick)` thickened both lines and now thickens mpg's alone. `.`, `=`, `..` and `...` mean what they mean in twoway, and a quoted element is one element. A plot type that draws one y uses the first element: `dash scatter mpg weight, mcolor(red blue)` drew the scheme's colour with a note and now draws red. An unquoted `mcolor(255 0 0)` is now three colours, as twoway reads it: it drew red, and now draws the series with the unknown colour 255 and a note; write `mcolor("255 0 0")`. (WP-30, P1.1a)"
- **Changed behaviour (may need your do-files changed):** "A `..` or `...` anywhere but at the end of a style list is refused as twoway refuses it: `dash scatter mpg turn weight, mcolor(red .. blue)` was drawn with a note and is now `mcolor(red .. blue):  invalid syntax`, r(198). An element of a style list that a y uses is held to the option's bounds as one value is: `dash line mpg turn weight, lwidth(thick 20000)` was drawn and is now refused, r(198), as twoway refuses it. A quoted element of a style list that holds only blanks and that a y uses is refused: `dash scatter mpg turn weight, mcolor(" " blue)` was drawn and is now `dash: mcolor() element 1 is blank; use . for the default (got: " " blue)`, r(198); write `.` for the default. (WP-30, P1.1a)"

**Notes for the closeout (S58; A145).**
- **GAPS2.md D8.** Sentences a-e of D8 are closed for style options by the P1.1a commit `<sha>`. D8 as a whole is recorded closed by P1.1b (S20), whose commit closes the value lists. The S58 Tracked line for D8 names both commits.
- **REMAINING.md row 06** ("positional plot-options across an expanded varlist"): the style half was closed by P1.1a `<sha>`; the row closes with P1.1b. REM-S06-c is cited by both.
- **ROADMAP.md.** Record that TR-28.1's claim that a short list "recycles the last value" was measured wrong (twoway pads with `.`: T02, T42, T43, U21, W28 in `research/p1-01.md`), so PHASE-28 item 2 is superseded by WP-30 P1.1a/P1.1b.
- **DROPIN-REMAINING.md** P1.1: part a closed by S11 `<sha>`.
- **New P2 residuals to file:**
  - an unknown `msymbol()` element draws the scheme's p# symbol where twoway draws a circle (P1.1.4's symbol part; `_apply_marker_opts`, CRITICAL; not owned by any WP-30 section);
  - glued `=` forms (`mcolor(red=blue)`, which twoway draws as p1-p3 silently; `mcolor(red= blue)`, whose first element twoway draws at the default) and parenthesised elements (`mcolor((red) blue)`, which twoway refuses r(198) `option(s) ( red ) not allowed`) reach the renderer as one unknown element;
  - the echo of a misplaced `..` written with runs of blanks matches twoway's rc and words but not its blank count (F1).
- **TWOWAY_COVERAGE_AUDIT.md.** Tag stylelists ([G-4] stylelists) "honoured for style options (WP-30 P1.1a); value lists P1.1b".
