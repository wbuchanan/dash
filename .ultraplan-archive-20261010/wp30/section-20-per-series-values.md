# Section 20: Per-series value lists (P1.1 part b)

> Part of: WP-30 · Items: P1.1 part b (entry `P1.1b`) · Risk: yellow · Batch: 7 (merge order S19, S20, S21; S20 second) · Depends on: 11 · Blocks: — · Tasks: 13, 1 commit · Case prefix: PS (PS-01..PS-16 in `test_varlist_expansion.cscript`, PS-30..PS-34 in `test_wp30_truth.cscript`)

## Review amendments

- Fixed (major, batch boundary): S19 and S20 both edit dash.ado's `_dash_process_segment` (S19 its function branch and JSON fields; S20 the `_dash_validate_opts` call, TR-20.5). Recorded in Dependencies as a bounded A139 exception (disjoint hunks, S19 lands first, `git apply -3`, neither touches the other's lines); index.md fix filed in review-notes/g04.md.
- Fixed (major): 20-13 checked G6 before anything was staged. It now stages the 16 named files (the fixture with `-f`), then checks the staged list, then G7.
- Fixed (minor): the truth block set and restored the scheme "at the block's start/end", which would put statements outside S01's start/end lines (TR-01.10 item 4). They now sit directly after the start line and before the end line.
- Fixed (minor): the Results line is placed after the last `(WP-30, P1.1a)` line of the WP-30 group (S11 may write several); the commit's BUGS line quotes Appendix B's title verbatim.
- Fixed (minor, M5): the Changed-behaviour line now names every newly refused form: histogram/function `mlabel(nosuch ..)`, histogram `mlabel(= make)`, and mspline/mband's earlier twoway checks.
- Resolved Q-20.1 by register P1.1.5's precedent (dash's stricter per-element checks stay; "dash refuses what twoway accepts" is P2.14); no maintainer answer needed.
- Checked: dash.ado anchors (:924-935, :2025-2043, :2125-2133, :2410-2413, :2577, :2685-2700, :1691-1713, :1755-1775, :4110-4134) and `_dash_text_args`' argument form match `c96facd`; `_dash_fold_typed` runs after `_dash_validate_opts` (:4134), so `jitter(.)` written back as empty leaves no note (PS-08). No renderer, copy list or map other than program_coverage_map is touched.
- Rejected: "refusing 2-y `jitter(2 200)` breaks M5" (register P1.1.5 keeps dash's documented bounds on used elements).
- The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:66 (P1.1) says a stylelist over an expanded varlist "gives every y the whole list". Research p1-01 sub-claim h is the value-list half of that item. Measured at `c96facd` (probe `d1.do`, quoted under Evidence):
- `dash scatter mpg turn weight, mlabel(make rep78)` is refused r(198), `dash: mlabel() must name one variable (got: make rep78)`.
- `jitter(2 3)`, `base(10 20)` and `barwidth(1 2)` are each refused r(198), for example `dash: base() must be a number (got: 10 20)`.

twoway accepts each of these and applies them by series:
- series 1 is labelled by make and series 2 by rep78 (T40);
- each series is jittered by its own amount (U05/U06);
- bars stand on bases 10 and 20 at widths 0.4 and 0.8 (G01, measured here).

dash also gets the forms around these wrong:
- A lone value over several y applies to every y. twoway pads it with `.`, so only the first y takes it: `mlabel(make)` (U01), `jitter(5)` (J01), `base(50)` (G03).
- A single-y plot refuses a list where twoway uses the first element: `scatter mpg weight, mlabel(make foreign)` is HC2-18b.
- The shorthands give the wrong return codes:
  - `mlabel(make ..)` and `mlabel(make =)` are r(111) `variable .. not found`; twoway refuses them r(198) `.. not allowed in option mlabel()` and r(101) `=exp not allowed`.
  - `mlabel(.)` is r(111) where twoway says r(102) `too few variables specified`.
  - `histogram mpg, mlabel(nosuch ..)` is accepted where twoway refuses it.

GAPS2 D8 (GAPS2.md:931-950) lists `mlabel` among "the other list-taking options" its plan splits.

**After this section,** `mlabel()`, `jitter()`, `base()` and `barwidth()` are read as stylelists, through S11's splitter, one element per y of an expanded varlist:
- `.`, `=`, `..` and `...` resolve as in twoway.
- A short list is padded with `.`, so a lone value styles only the first y, silently (M1, M6, register P1.1.1).
- Extra elements are ignored, and a single-y type takes the first element.

The value checks hold for each element a y uses, after the shorthands resolve:
- `jitter()` is held to 0-100 and `barwidth()` to positive (dash's documented bounds; register P1.1.5); `base()` must be a number.
- `jitter(2 ..)`, `jitter(. 3)`, `base(10 =)` and `barwidth(. 200)` draw.
- Elements past the last y are not checked.

`mlabel()` follows twoway's own reading, in its order and words (register P1.1.6, P1.1.7; M5):
- `=` is refused r(101) `=exp not allowed`.
- Every variable named is checked, past the last y too: r(111) `variable X not found`.
- A list with no variable is refused r(102) `too few variables specified`.
- `..` or `...` anywhere is refused r(198) `.. not allowed in option mlabel()`.
- `.` leaves that y unlabelled.

A list where twoway takes one value is refused in twoway's words, `option barwidth() not allowed`, r(198): `barwidth()` on rbar, histogram, rcap and rspike, and `base()` on rbar and histogram. A lowess `bwidth()` list stays refused, r(198), unchanged.

`mlabposition()` was already split and checked per element by S11 (it is one of S11's 28 keys). This section pins that with guards and adds no code for it.

The renderers are not edited. Each series' own value reaches its own options object, so the saved page and the served app draw each series' labels, jitter, base and width, before and after a filter move and in every by() panel.

**Why one section.** This is P1.1's value half (A138: P1.1a in S11, P1.1b in S20). It needs S11's splitter, key list and per-series JSON writer, and it is the only section that edits the value rules of `_dash_validate_opts`, `_dash_option_rules` and `_dash_fold_mlab` for these four options. It is one BUGS.md entry, `P1.1b` (index manifest row 20).

**Test order and commit rule (rule 7, D1, index "per-entry cycle").** One cycle, one commit:
- **20-01 to 20-03** write the regression tests (pytest module, the PS cscript run, the S20 truth block). Each is run on the unmodified worktree and its failures are appended to `<scratch>/20-P1.1b-failure.txt`. None commits.
- **20-04** writes the extractor and the fixture.
- **20-05 to 20-12** fix, flip, register and document.
- **20-13** closes the entry, replaces the two markers and adds the Results line. It runs the full suite through the queue and makes the one commit, whose subject ends `(WP-30 P1.1b)`.

## Risk: [yellow] — four common options change reading on every multi-y plot, and mlabel's refusals change return code

**Why.**
- Every multi-y do-file that gives `mlabel()`, `jitter()`, `base()` or `barwidth()` one value now styles only the first y. This is a silent look change (M1/M6, a CHANGELOG "Results that change" line).
- The `mlabel()` refusals move from r(111) and r(198) to twoway's r(101), r(102), r(111) and r(198). A `capture` that tests `_rc` sees a new code.
- The work sits in the validation chain every plot segment passes through.

**Risk factors.**
1. `_dash_validate_opts` writes normalised values back into `s()` and restores lost keys from a snapshot. A list rewritten to "not given" (`jitter(.)`) could be restored to its raw text by a later rule's restore loop.
2. S11's `_dash_stylelist_check` runs after `_dash_validate_opts` and re-checks every listed key. The two passes must agree, and S11's misplaced-`..` refusal must still fire for `jitter(2 .. 5)`.
3. `mlabel()` reaches `_dash_extract_vars` (dash_parse.mata:2229). A variable only an unused element names must not be exported, and one a used element names must be.
4. The validator charter (test_option_validation.py `TestTheNewProgramsKeepTheirConstraints`) forbids Mata calls beyond its allow-list inside `_dash_validate_opts`, `_dash_validate_value` and `_dash_option_rules`.
5. SV-04 (`mlabel(s)` on five y; test_string_values.cscript:369) and TP-08/TP-12 (mlabel per type, adversarial mlabel on mspline) pin neighbouring behaviour.
6. `jitter(5; import os)` (test_adversarial.cscript P9-01) must stay refused, naming jitter().

**Mitigation.**
1. When `_dash_validate_opts` writes a value back, it also sets that key's snapshot to the written value, so a later restore can only bring back the normalised text, and an emptied key stays empty. PS-08 pins `rscatter … jitter(.)`, which leaves no jitter note.
2. `_dash_value_list` leaves a value with a misplaced `..` untouched (`_dash_stylelist_bad`), so S11's check refuses it next with twoway's words. A rewritten value is the resolved list, which S11's pick reads identically. PS-09 and PS-11 pin both.
3. `_dash_mlabel_list` writes back exactly `nser` resolved names, with `.` for unlabelled series. The JSON writer emits one name per series, which `_dash_extract_vars` reads (PS-02, PS-03).
4. The new splitting work runs in two new programs that `_dash_validate_opts` calls. `_dash_validate_opts` itself calls no new Mata, which is S11's precedent for `_dash_stylelist_check`. The charter test is unchanged and green.
5. SV-04, TP-08, TP-12, OV-23/42/44/45/100/101/124/133 and JSE-69 are re-run as guards in 20-11.
6. P9-01 stays a guard: the first element `5;` is not a number.

## Dependencies

- **Depends on: 11 (P1.1a, batch 4).** S11 provides, at the batch-7 base (its TR-11.1 to TR-11.9):
  - Mata `_dash_stylelist_keys()`: 28 names, with a comment naming S20's `mlabel jitter base barwidth`;
  - `_dash_stylelist_elems(raw)` (a 2 x *k* matrix: text, quoted flag);
  - `_dash_stylelist_norm`, `_dash_stylelist_pick(raw, i)` and `_dash_stylelist_bad(raw)` (dash_parse.mata, after `_dash_rep_toks`);
  - the normaliser loop after `_dash_parse_plot_opts`' `syntax` (over `_dash_stylelist_keys()`);
  - `_dash_stylelist_check ptype nser` after `_dash_validate_opts`, with `local _sl_n …` computed just before it;
  - `_dash_plot_opts_to_json out_macro series`, called with `` `_yi' `` inside the `_yi` loop;
  - `_needed` holding `_dash_stylelist_keys _dash_stylelist_norm _dash_stylelist_pick _dash_stylelist_bad _dash_stylelist_probe`.

  S11 also provides:
  - `test/test_stylelists.py` with `_STYLE_KEYS` and `_NOT_YET`;
  - the `// SL: style lists (WP-30 P1.1a)` run of `test_varlist_expansion.cscript` with its Mata helper `_sl_opts(spec, k)`;
  - S11's paragraph `{marker stylelists}` in dash.sthlp's "Differences from twoway".

  20-01 checks every name here at the base and stops if any is missing or different.
- **Also relies on (earlier batches):**
  - S01's `P1.1b` BUGS.md entry, its `WP30_OPEN["P1.1b"]` key, its two `<!-- WP-30 P1.1b -->` markers (Changed behaviour; Fixed in WP-30), its `WP30_LISTS["P1.1b"]` row and its stub block `* ==== S20 P1.1b: Per-series value lists ====`;
  - S02's path-free extractor form;
  - S03's `version 19`;
  - S06's note channel (note needles through S06's helpers);
  - S14's bar width path and its `rcap barwidth()` refusal (IR-17).
- **Blocks:** none (manifest).
- **Parallel batch: 7.** Merge order S19, S20, S21. S20 lands second. It is Stata-only and edits no renderer, axis, key or title function.
- **Can run with:**
  - **S19.** S19 edits `_dash_process_segment`'s function branch (the yname capture at :3679-3683 and the `"yname"` field at :4309-4312). S20 edits only the three lines around the `_dash_validate_opts` call (:4121-4126 at `c96facd`), a hunk about 190 lines from either of S19's. This is the one function the two share, a recorded exception to A139 (one editor per function per batch): GitNexus does not index Stata, the hunks are disjoint, and merge order lands S19 first, so S20's patch applies with `git apply --index -3`. A conflict there is resolved by keeping both hunks unchanged; neither section edits the other's lines. In dash.sthlp S19 owns "Statistical Layer Options" and S20 never edits that title. So the `base(#)` synopt (:2358) stays as it is, and the base and barwidth lists are documented in the Stylelists paragraph instead.
  - **S21.** S21 edits only `dash_render.py`, the scheme files and "Axis and Display Options".

## Evidence

Anchors are at `c96facd` (dash.ado 8,487 lines; dash_parse.mata 6,093; dash.sthlp 3,822). S03, S06, S08, S11 and S14 move lines before batch 7, so symbols govern and 20-01 re-reads each one at the base.

### The declarations (dash.ado:924-935, `_dash_parse_plot_opts`)

```stata
927        MLabel(string)            MLABColor(string)         MLABSize(string) ///
934        BARWidth(string)          BASE(string)              BLColor(string) ///
935        BFColor(string)           JITter(string)            JSEed(string) ///
```

S11 (TR-11.4) leaves these four `(string)`. Its `test_the_later_lists_are_not_yet_asis` pins that, with all four in `_NOT_YET`.

### The value rules (dash.ado:2025-2043, `_dash_option_rules`)

```stata
2028    local plot ///
2029        msize=style  mlabsize=style  mlabgap=style ///
2031        msangle=style,-360,360  mlabposition=style  fintensity=style ///
2032        jitter=num,0,100  jitterseed=int,0  jseed=int,0 ///
2035        base=num  barwidth=pos  level=num,0,100,x ///
2036        degree=int,0,3  bwidth=pos,1@lowess  bwidth=pos ///
2042        colorcuts=numlist,1  colorvar=var  mlabel=var  range=numlist,2,2 ///
```

These rules see the whole value. The `var` kind refuses more than one name (dash.ado:2410-2413):

```stata
2410        if "`kind'" == "var" & `: word count `vv'' > 1 {
2411            mata: _dash_say("err", "`prefix': `opt'() must name one variable (got: ", st_local("value"), ")")
2412            exit 198
2413        }
```

`_dash_validate_opts` (:2577) applies each rule once per segment and writes the normalised value back (:2685-2700):

```stata
2685        mata: st_local("v", st_global("s(" + st_local("o") + ")"))
2691        if !`: length local v' continue
2692        _dash_validate_value "dash" "`o'" "`spec'" `"`macval(v)'"' "`ptype'"
2693        foreach _k of local _keys {
2694            if !`: length local _snap_`_k'' continue
2695            mata: st_local("_lost", strofreal(st_global("s(" + st_local("_k") + ")") == ""))
2696            if `_lost' sreturn local `_k' : copy local _snap_`_k'
2697        }
2698        mata: st_local("_chg", strofreal(st_local("_dash_vnorm") != st_local("v")))
2699        if `_chg' {
2700            sreturn local `o' `"`macval(_dash_vnorm)'"'
```

It is called once (dash.ado:4125), after `_dash_fold_bw` (:4121), which calls `_dash_fold_mlab` (:1549):

```stata
4121        _dash_fold_bw "`ptype'"
4125        _dash_validate_opts "`ptype'"
```

`test_option_validation.py::TestTheNewProgramsKeepTheirConstraints::test_validate_opts_follows_fold_bw` reads the literal `_dash_validate_opts "`ptype'"`. A trailing argument keeps that substring.

### mlabel by plot type (dash.ado:1691-1713, `_dash_fold_mlab`)

```stata
1698    mata: st_local("v", st_global("s(mlabel)"))
1700    local mlab_unread  "histogram function"
1701    local mlab_refused "mspline mband"
1702    if `: list ptype in mlab_unread' {
1703        sreturn local mlabel ""
1706    if `: list ptype in mlab_refused' {
1707        capture confirm variable `macval(v)'
1708        if !_rc {
1709            display as error "dash: mlabel() is not allowed on `ptype' (twoway: too many variables specified)"
1710            exit 103
```

### Readers of these keys

- `s(mlabel)`: :1698 only.
- `s(jitter)`: :1767 (`_dash_fold_typed`, names jitter on rscatter, rcapsym, pcscatter and pccapsym).
- `s(barwidth)`: :1615 (`_dash_fold_bw`, the `bw()` copy).
- `s(base)`: no reader.
- The JSON writer's key list (dash.ado:3144-3147) holds all four: `mlabel`, `barwidth base`, `jitter`.
- `_dash_extract_vars` (dash_parse.mata:2229-2243) collects every plot's `"mlabel":` value for export.
- In the renderer, `_dash_mlabel_names` (dash_render.py:25515-25528; GitNexus impact CRITICAL, 27 impacted) splits a hand-written multi-name mlabel. Its docstring premise, "dash.ado validates mlabel() as one variable", still holds per series and it is not edited.

### What dash writes and refuses today (probe `d1.do`, 03oct2026)

Command: `scripts/stata_slot.sh <scratch>/s20-probe <scratch>/s20-probe/d1.do`. Each case runs `dash <cmd> name(<id>)` and prints rc, the first error line and `$dash_json_<id>`.

```
h01 scatter mpg turn weight, mlabel(make rep78)   rc=198  dash: mlabel() must name one variable (got: make rep78)
h02 scatter mpg weight, mlabel(make foreign)       rc=198  (same words)
h03 … mlabel(make ..)                              rc=111  dash: mlabel(): variable .. not found
h04 … mlabel(make =)                               rc=111  dash: mlabel(): variable = not found
h05 … mlabel(.)                                    rc=111  dash: mlabel(): variable . not found
h06 … mlabel(make)                                 rc=0    both plots {"mlabel":"make"}
h07 … jitter(2 3)                                  rc=198  dash: jitter() must be a number between 0 and 100 (got: 2 3)
h08 … jitter(.)                                    rc=198  (got: .)
h09 bar mpg turn weight, base(10 20)               rc=198  dash: base() must be a number (got: 10 20)
h10 bar … barwidth(1 2)                            rc=198  dash: barwidth() must be a positive number (got: 1 2)
h11 bar … barwidth(.)                              rc=198  (got: .)
h12 rbar mpg turn weight, barwidth(50 100)         rc=198  dash: barwidth() must be a positive number (got: 50 100)
h13 lowess mpg weight, bwidth(.5 .8)               rc=198  dash: bwidth() must be a positive number no greater than 1 (got: .5 .8). …
h14 … mlabel(mak) jitter(1d1)                      rc=0    both plots {"mlabel":"make","jitter":"10"}  (normalised)
h15 … mlabel(make) mlabposition(3 9)               rc=0    both plots "mlabposition":"3 9"   (S11 splits this)
h16 histogram mpg, mlabel(nosuch ..)               rc=0    options {}
h17 mspline mpg weight, mlabel(make ..)            rc=111  dash: mlabel(): variable .. not found
h18 rbar mpg turn weight, base(10)                 rc=0    {"base":"10"}   (twoway refuses: residual, P2.21)
h19 histogram mpg, base(10)                        rc=0    {"base":"10"}   (twoway refuses: residual, P2.21)
h20 … mlabel(t*)                                   rc=198  dash: mlabel() must name one variable (got: t*)
```

Both modes render the spec dash.ado writes, so both modes are wrong in the same way. Research p1-01 §3 (`modes.py`, `move.py`) measured that the renderers draw a hand-split per-series spec correctly in both modes and keep each series' options across a served RangeSlider move. The saved filter JS writes no glyph style. The fix belongs at spec emission.

### twoway's rule (StataNow 19.5, s2color)

`[G-4] stylelists` (stylelists.sthlp:36-55) gives the shorthands, the padding and the ignored extras. The value-list readings were measured with `p1.do` to `p8.do` (Stata truth) and research p1-01 §2:
- **mlabel, by series:**
  - T40/M01 `mlabel(make rep78)`: series 1 labelled by make (74 labels), series 2 by rep78.
  - U01/M05 `mlabel(make)` on 2 y: series 1 only.
  - R09 `mlabel(. rep78)`: series 2 only.
  - P04 `mlabel(make rep78 foreign)`: rc 0, the extra ignored.
  - P07 `mlabel(mak rep7)`: abbreviations read.
  - P09 `mlabel(rep*)`: series 1 rep78.
  - H1 `mlabel("make" "rep78")`: rc 0.
  - P13 `mlabel(make "")`: series 2 none.
  - P36 `mlabel(make) mlabel(rep78 foreign)`: the rightmost copy whole.
  - P05 `scatter mpg weight, mlabel(make foreign)`: make.
- **mlabel refusals** (rc, then the line):
  - P10 `make ..` r(198) `.. not allowed in option mlabel()`;
  - P03 `make ...` r(198) `... not allowed in option mlabel()`;
  - P01 `make .. rep78` r(198);
  - P12/P02/P32 `make =`, `= make`, `make = rep78` r(101) `=exp not allowed`;
  - Q04/Q05/Q10/Q17 `.`, `. ..`, `mlabel(make) mlabel(.)` r(102) `too few variables specified`;
  - X09/P30/R07 a missing variable, also past the last y, r(111) `variable nosuch not found`.
- **The order of mlabel's checks:**
  - left to right, `=` and a missing variable stop at the first one met: Q08 `nosuch =` r(111), Q09 `= nosuch` r(101);
  - then "no variable" (Q10 `. ..` r(102));
  - then `..` (Q07 `make .. nosuch` r(111); P31 `nosuch ..` r(111)).
- **mlabel by type:**
  - histogram and function never read the variables (T03 rc 0, T05 `nosuch =` rc 0), but refuse a spaced `..` (S08, T04 r(198)); histogram also refuses `=` (T01 r(198) `invalid syntax`).
  - mspline and mband run the same checks first, then r(103): S06 `make rep78` r(103), S07 `. make` r(103), T08 `make ..` r(198), T10 `nosuch rep78` r(111).
- **Value lists:**
  - U05/U06 `jitter(0 5)`, `jitter(5 0)`: per series.
  - J01 `jitter(5)` on 2 y: series 1 only (31 against 7 distinct positions); J02 `jitter(. 5)`; J03 `jitter(5 ..)`.
  - W06 `base(10 20)`.
  - G01 `bar y1 y2 x, barwidth(0.4 0.8) base(10 20)`: widths 0.4 and 0.8, bases 10.0 and 20.0, axis-calibrated.
  - G02 `barwidth(0.4 ..) base(10 =)`: both 0.4 and 10.
  - G03 `base(50)`: series 1 from 50, series 2 from its default; G04 `base(. 50)`: the reverse.
  - U10 `barwidth(1 2)`.
  - H2/H3 `jitter(2 =)`, `base(10 =)`; P18 `barwidth(1 ..)`; Q28/Q29 `barwidth(.)`, `jitter(.)` rc 0.
  - W25, X11 and X12 dropline, spike and area `base(10 20)`: rc 0.
  - S03, S04 and S11 `barwidth(1 2)` on spike, dot and dropline: rc 0.
- **Lists twoway refuses:**
  - W35/P17/V02/V11/S14 rbar `barwidth(50 100)`, `(50 ..)`, `(50 .)`, `(" 50")`, `barwidth(50) barwidth(10 20)`;
  - S01/V03 histogram `barwidth(1 2)`, `(1 ..)`;
  - S09/S10 rcap and rspike `barwidth(1 2)`.

  Each is r(198) `option barwidth() not allowed`. S05 rbar and V08 histogram `base(10 20)` are r(198) `option base() not allowed`. W11 lowess `bwidth(.5 .8)` is r(198) `option bwidth() not allowed`.
- **Misplaced `..`:** P28 `jitter(2 .. 5)` r(198) `jitter(2 .. 5):  invalid syntax`; P29 `base(10 .. 20)` likewise (S11's rule).
- **twoway's lax checks:** X05, X06, X07, Q25 and P15 `jitter(2 abc)`, `jitter(2 200)` on 1 and 2 y: rc 0. X08/S13 `barwidth(1 -2)`, `(1 0)`: rc 0. Q12 single-y `base(10 abc)`: rc 0. dash keeps its documented bounds on used elements (P1.1.5).

### Existing tests that pin today's behaviour (flipped in 20-09/20-10, never deleted)

- `test/test_help_claims_2.cscript` HC2-18b (:566): `_hc2_dash "HC2-18b" 198 … mlabel(make foreign) … "mlabel() must name one variable"`. It becomes rc 0. Its header lines :49-51 ("mlabel() with two variables") are reworded.
- `test/test_help_claims_2.py::TestTheHelpSaysWhatWasMeasured::test_the_forms_dash_refuses_are_named` (:268-276) asserts `{cmd:mlabel()} with more than one variable`.
- S11's `test/test_stylelists.py::TestTheParserKeepsQuotes::test_the_later_lists_are_not_yet_asis`: mlabel, jitter, base and barwidth leave `_NOT_YET`.
- S11's `test/test_stylelists.py::TestOneList::test_the_mata_key_list_is_the_declared_set`: the literal becomes `_STYLE_KEYS + _VALUE_KEYS`.
- S11's `test/test_varlist_expansion.cscript` SL-01: 28 words becomes 32, and none of the reduced `_NOT_YET`.

### Guards (green before and after; re-run in 20-11)

- `test_option_validation.cscript`:
  - OV-22 to OV-30 (jitter);
  - OV-41 to OV-45 (base, barwidth);
  - OV-61, OV-62 (`bw()`);
  - OV-100 (`mlabel(mak)` registers `"mlabel":"make"`);
  - OV-101 (r(111));
  - OV-121 to OV-124 (OV-124: `mlabel(L.mpg)` r(198));
  - OV-133 (tab-padded `jitter()` registers `"jitter":"5"`).
- `test_twoway_option_parity.cscript` TP-08 (mlabel per type against live twoway) and TP-12 (`mak`, `make make` and 400 names on mspline r(103); `{bf:ZQINJ}` echoed as text).
- `test_json_escaping.cscript` JSE-69 (`mlabel("\`jgnone'")` r(111) shown as typed; dropped on histogram).
- `test_adversarial.cscript` P9-01.
- `test_string_values.cscript` SV-04.
- pytest:
  - `test_option_validation.py` (charter, table, `TestMlabelWithSeveralNamesUsesTheFirst` on hand-written specs);
  - `test_marker_label_parity.py`;
  - `test_abbreviations.py` (its `_dash_parse_plot_opts` comment-count pin must not move: S20 adds no `//` line there);
  - `test_stylelists.py` (the rest).

### Blast radius (E4; the batch-7 base impact file records it)

GitNexus does not index Stata or Mata. `gitnexus impact _dash_validate_opts -d upstream -r dash` (likewise `_dash_fold_mlab` and `_dash_option_rules`) returned `"error": "Target … not found"`, `"risk": "UNKNOWN"` (run 03oct2026). Callers were confirmed by grep:

| Symbol | File:line | Callers (grep) | Risk |
|---|---|---|---|
| `_dash_parse_plot_opts` syntax (4 declarations) | dash.ado:927, 934, 935 | every plot segment | UNKNOWN; HIGH by grep |
| `_dash_option_rules` (two new locals) | dash.ado:2025 | :2580, :5341, S11's check | UNKNOWN; LOW |
| `_dash_validate_opts` (args, routing, snapshot) | dash.ado:2577 | :4125 only | UNKNOWN; MEDIUM |
| `_dash_process_segment` (3 lines at the call) | dash.ado:4121-4126 | :5210 | UNKNOWN; HIGH by grep |
| `_dash_fold_mlab` | dash.ado:1691 | :1549 only | UNKNOWN; LOW |
| `_dash_require_mata` `_needed` | dash.ado:237 | every command | UNKNOWN; LOW (one name) |
| Mata `_dash_stylelist_keys()` (literal) | S11's, dash_parse.mata after `_dash_rep_toks` | S11's normaliser, writer, check and repeats probe | UNKNOWN; MEDIUM |
| `_dash_value_list`, `_dash_mlabel_list` (new ado), `_dash_stylelist_locals` (new Mata) | — | new | none |
| `_dash_validate_value` | dash.ado:2125 | called, not edited | — |
| `dash_render.py` `_dash_mlabel_names`, `_apply_mlabel_opts` | :25515 | — | CRITICAL; not edited |

## User stories

- **US-20.1** As a twoway user, I want `scatter mpg turn weight, mlabel(make rep78)` to label mpg's markers by make and turn's by rep78, so a multi-y do-file labels each series as in Stata.
- **US-20.2** As a twoway user, I want `jitter()`, `base()` and `barwidth()` lists, `.`, `=`, `..` and `...` included, read one element per y, so `bar y1 y2 x, base(10 20) barwidth(0.4 0.8)` draws each series from its own base at its own width.
- **US-20.3** As a twoway user, I want a lone value over several y to style only the first y, and a single-y plot to take a list's first element, as twoway does, with no note.
- **US-20.4** As a twoway user, I want the `mlabel()` forms twoway refuses refused with twoway's return code and words, so `capture` and `_rc` behave as in Stata.
- **US-20.5** As a dashboard publisher, I want each series' labels, jitter, base and width kept in the saved page and the served app, after any filter move and in every by() panel.
- **US-20.6** As the maintainer, I want every rule pinned by a test that failed first, by twoway's measured truth, and by guards over the neighbouring refusals.

## Business requirements

- **BR-20.1** `mlabel()`, `jitter()`, `base()` and `barwidth()` given a list over an expanded varlist apply their k-th element to the k-th y. A short list is padded with `.`, so a lone value applies to the first y only. Elements past the last y are ignored. Nothing is printed.
- **BR-20.2** `.` gives that y the default (no labels, no jitter, the default base or width). `=` repeats the previous element (`.` when first). `..` or `...` at the end repeats it to the last y.
- **BR-20.3** A plot type that draws one y uses the first element, except where BR-20.7 refuses the list.
- **BR-20.4** Each `jitter()`, `base()` or `barwidth()` element a y uses is held to the option's rule as a lone value is (jitter 0-100, base a number, barwidth positive), and refused with that rule's words and r(198). An unused element is never checked.
- **BR-20.5** In `mlabel()`, every element other than `.` and an empty quoted element must name exactly one variable. The checks run left to right:
  - `=` → r(101) `=exp not allowed`;
  - a missing variable, also past the last y → r(111), naming it;
  - a list naming no variable → r(102) `too few variables specified`;
  - `..` or `...` anywhere → r(198) `.. not allowed in option mlabel()` (or `...`).
- **BR-20.6** On histogram and function `mlabel()` stays unread and is dropped, but a `..` or `...` element is refused as in BR-20.5, and on histogram a `=` is refused r(198) `invalid syntax`. On mspline and mband the checks of BR-20.5 run first, then the existing r(103) refusal.
- **BR-20.7** A list (more than one element, or one quoted element) is refused r(198) `option barwidth() not allowed` in `barwidth()` on rbar, histogram, rcap and rspike, and `option base() not allowed` in `base()` on rbar and histogram. A lowess `bwidth()` list stays refused r(198).
- **BR-20.8** A misplaced `..` in `jitter()`, `base()` or `barwidth()` is refused as S11 refuses it for style options: `<opt>(<value>):  invalid syntax`, r(198).
- **BR-20.9** `mlabposition()` lists keep S11's reading. Each series' clock position is its own element.
- **BR-20.10** BR-20.1 to BR-20.9 hold in the saved page and the served app, before and after a filter move, and in every by() panel.

## Technical requirements

- **TR-20.1 The key list.** In S11's Mata `_dash_stylelist_keys()`, append `mlabel jitter base barwidth`, in that order, after `alpattern`. Update its comment so it no longer names S20 as a later adder. Every name is already in `_dash_plot_opts_to_json`'s key list (:3144-3147), so S11's normaliser, per-series writer, repeats probe and misplaced-`..` check now cover the four.
- **TR-20.2 Declarations.** In `_dash_parse_plot_opts`' `syntax`, `MLabel(string)`, `JITter(string)`, `BASE(string)` and `BARWidth(string)` become `(string asis)`. The capitalised minimums are unchanged, and no `//` line is added to that program (`test_abbreviations.py`'s comment-count pin stays put).
- **TR-20.3 The tables** (`_dash_option_rules`, under the existing `local flags` block, each with a comment of at most five `//` lines; no `word=word` text in either comment):
  - `local values "mlabel jitter base barwidth"` with `c_local _dash_rules_values "`values'"`: the plot rules checked one element per y.
  - `local onevalue "barwidth@rbar|histogram|rcap|rspike  base@rbar|histogram"` with `c_local _dash_rules_onevalue "`onevalue'"`: where twoway takes one value and refuses a list.

  The `local plot` rule tokens are unchanged, so `CONTRACT_PLOT_RULES` and `KINDS` (test_option_validation.py) hold.
- **TR-20.4 `_dash_validate_opts`.**
  - `args ptype nser`, then `if "`nser'" == "" local nser 1`.
  - In the plot-rule loop, the call at :2692 becomes a branch: when `` `: list o in _dash_rules_values' `` holds, call `_dash_value_list "dash" "`o'" "`spec'" `"`macval(v)'"' "`ptype'" `nser'`; otherwise make the existing `_dash_validate_value` call unchanged. The restore loop and the `_chg` write-back follow either branch as today.
  - Inside the `_chg` block, after `sreturn local`, add `local _snap_`o' : copy local _dash_vnorm`. A later restore then brings back the written value, and an emptied value stays empty.
  - No Mata call is added to this program (the charter).
- **TR-20.5 Wiring** (`_dash_process_segment`). Move S11's two lines `local _sl_n 1` and `` if `"`yvarlist'"' != "" local _sl_n : word count `yvarlist' `` to directly before `_dash_validate_opts`. That call becomes `_dash_validate_opts "`ptype'" `_sl_n'`. `_dash_stylelist_check "`ptype'" `_sl_n'` stays where S11 put it.
- **TR-20.6 `_dash_value_list`** (new; `program define _dash_value_list, rclass`; `version 19`; directly after `_dash_validate_value`'s `end`; a header comment naming the rule and the twoway cases):
  - `mata: _dash_text_args(3, 2, 0)` gives prefix, opt, spec, the value (`_dash_txt`), ptype and nser. It then calls `_dash_option_rules` for its own `_dash_rules_onevalue` (the locals land in the caller, so it cannot read `_dash_validate_opts`').
  - When opt is `mlabel`: `_dash_mlabel_list `"`macval(prefix)'"' `"`macval(value)'"' "`ptype'" `nser'`, then `c_local _dash_vnorm` with its result. Done.
  - `mata: _dash_stylelist_locals(st_local("value"), "_vl")` gives `_vln`, `_vlt<j>` and `_vlq<j>`.
  - For each `_dash_rules_onevalue` token whose option is opt and whose types hold ptype: when `_vln` > 1 or `_vlq1` is 1, `display as error "option `opt'() not allowed"` and `exit 198`. Otherwise call `_dash_validate_value` on the whole value as today, `c_local` its `_dash_vnorm`, and stop.
  - When `_dash_stylelist_bad(value)` is 1, `c_local _dash_vnorm` the value unchanged and stop (S11's check refuses it next).
  - For *i* = 1..nser: `e = _dash_stylelist_pick(value, i)`. When e is empty, *r_i* is `.`. Otherwise `_dash_validate_value "`prefix'" "`opt'" "`spec'" `"`macval(e)'"' "`ptype'"` (which refuses with the single value's words, echoing the element) and *r_i* is its `_dash_vnorm`.
  - `c_local _dash_vnorm` gets the *r_i* joined by one blank, or `""` when every *r_i* is `.`.
  - Every value and element is read by value (`st_local`/`st_global`, `macval()`).
- **TR-20.7 `_dash_mlabel_list`** (new rclass program after `_dash_value_list`; `version 19`). `mata: _dash_text_args(1, 2, 0)` gives prefix, the value, ptype and nser. Then `_dash_stylelist_locals` with stub `_ml`. Steps, in this order:
  1. For *j* = 1..`_mln`:
     - a bare `=` → `display as error "=exp not allowed"`, `exit 101`;
     - a bare `.`, or a quoted element blank after `strtrim` → skip;
     - a bare `..` or `...` → remember the first one's text, skip;
     - any other element (quotes already stripped) is a name. Unless it is already in the checked list (Mata `anyof(tokens(…))`, by value), call `_dash_validate_value "`prefix'" "mlabel" "var" `"`macval(t)'"' "`ptype'"`. That gives r(111) `…variable X not found`, r(198) for a time-series expression or several variables (`t*`), or the full name, which is appended to the checked list and stored as element *j*'s name.
  2. No name element → `display as error "too few variables specified"`, `exit 102`.
  3. A remembered `..`/`...` → `display as error "<tok> not allowed in option mlabel()"`, `exit 198` (tok is dash's literal `..` or `...`).
  4. For *i* = 1..nser, *r_i* is element *i*'s full name, or `.` when element *i* is `.`, blank or absent. `c_local _dash_vnorm` gets the *r_i* joined by one blank, or `""` when all are `.`.
- **TR-20.8 `_dash_fold_mlab`.** Keep the header comment, extended by three lines naming the new checks.
  - On histogram and function:
    - run `_dash_stylelist_locals` (stub `_fm`);
    - a bare `..`/`...` element → `display as error "<tok> not allowed in option mlabel()"`, `exit 198`;
    - on histogram only, a bare `=` → `display as error "invalid syntax"`, `exit 198`;
    - then `sreturn local mlabel ""` as today.
  - On mspline and mband, `capture confirm variable` is replaced by `_dash_mlabel_list "dash" `"`macval(v)'"' "`ptype'" 1`. When it returns, keep today's r(103) line.
  - `_dash_mlabel_list` is rclass and touches no s(), and this branch exits either way.
- **TR-20.9 Mata `_dash_stylelist_locals`** (new; dash_parse.mata, directly after S11's `_dash_stylelist_probe`). The signature is `void _dash_stylelist_locals(string scalar raw, string scalar stub)`:
  - `e = _dash_stylelist_elems(raw)`;
  - `st_local(stub + "n", strofreal(cols(e)))`;
  - for each *j*, `st_local(stub + "t" + strofreal(j), e[1, j])` and `st_local(stub + "q" + strofreal(j), e[2, j])`.

  It reads and writes by value and is linear in `strlen(raw)`. Add a three-blank Public API entry after S11's `_dash_stylelist_probe(tok)` entry, and add the name to `_needed` on S11's continuation line (TR-11.3).
- **TR-20.10 Renderers and JS.** No change to `dash_render.py`. There is no served copy-list change (index R2 row "S20: —"); the constants tuple (dash_render.py:32884-33039), the functions tuple (33077-33425) and `_shared_stat_lines` (33536-33590) are untouched. There is no JS twin: `_FILTER_JS` and the saved CustomJS write no label text, base, width or jitter column per series (S11 Evidence; S14 removed the width writer).
- **TR-20.11 Maps** (A148, X.5). `test/program_coverage_map.py`, under S01's anchor `# WP-30 S20 (P1.1b): Per-series value lists (P1.1 part b)`, alphabetically:
  - `COVERAGE["dash.ado"]["_dash_mlabel_list"] = ("test_varlist_expansion.cscript:PS-05", "test_varlist_expansion.cscript:PS-06")`;
  - `COVERAGE["dash.ado"]["_dash_value_list"] = ("test_varlist_expansion.cscript:PS-08", "test_varlist_expansion.cscript:PS-12")`;
  - `COVERAGE["dash_parse.mata"]["_dash_stylelist_locals"] = ("test_varlist_expansion.cscript:PS-01",)`.

  `test/function_test_map.py` gains nothing (no Python function).
- **TR-20.12 Fixture.** New `scripts/extract_value_list_truth.do` writes `test/fixtures/value_list_truth.json` (Stata truth). Its header is copied from S11's `scripts/extract_stylelist_truth.do` (S02's form). It is never run by another section (R7).
- **TR-20.13 Help** (R3: "Differences from twoway" and "Marker and Transparency Options" only; 20-12 gives the text):
  - :711 "Variables: {cmd:mlabel()} and {cmd:colorvar()} name one" becomes "{cmd:colorvar()} names one, {cmd:mlabel()} one per y".
  - :740-742's clause "{cmd:mlabel()} with more than one variable ({cmd:twoway} labels the markers with the first)" becomes "an element of {cmd:mlabel()} that names several variables, such as {cmd:t*} ({cmd:twoway} draws no labels for that y)".
  - One paragraph of sentences is appended at the end of S11's `{marker stylelists}` paragraph.
  - The `jit:ter(#)` synopt (:3236-3238; index R3 cites :3233) says "or a list, one per y".
- **TR-20.14 Security (rule 1).**
  - Every value and element is read by value through Mata `st_local`/`st_global` and passed only with `macval()` in compound quotes, the call form `_dash_validate_opts` uses. A `$`, a backtick or `"'` in an element stays literal (PS-15, JSE-69).
  - Refusals that echo user text go through `_dash_validate_value`'s `_dash_say`. The new refusals print only fixed text (`=exp not allowed`, `.. not allowed in option mlabel()`, `too few variables specified`, `option barwidth() not allowed`).
  - Only element *i* of a used series reaches the JSON, through `_dash_json_str`. Extras never do (`jitter(5 ; import os)` writes `"5"`).
  - Work is bounded: the pick is O(len) per series, nser is held to the plots limit (r(134) before options are read), and mlabel names are checked once each (TP-12's 400 names: one `unab`).
  - The extractor's Python block never calls Stata and never uses `shell=True`. A backtick is `\x60`.

## Boundaries

- **S11 (landed, batch 4)** owns the splitter, the 28 style keys, the normaliser, the per-series writer and `_dash_stylelist_check`. S20 edits these S11 lines and nothing else of S11's:
  - the key literal (TR-20.1);
  - the position of the two `_sl_n` lines (TR-20.5);
  - `_needed`'s continuation line (TR-20.9);
  - the Public API header (one entry);
  - S11's Stylelists help paragraph (appended to);
  - S11's tests named under Flips.
- **Batch-7 partners:**
  - S19: `_dash_layer_series`, `_dash_legend_key(s)`, `map_scatteri`, `_DASH_FIT_KEYS`, `_dash_axis_default_titles`, `_dash_axis_labels`, `_dash_add_secondary_axes`, `_dash_process_segment`'s function branch, and help "Statistical Layer Options" (which holds the `base(#)` and `barwidth()` synopts).
  - S21: the ticker, margin and finishers, `_FILTER_JS`, `build_dropdown`/`build_slider`/`build_range`, the scheme files and help "Axis and Display Options".
  - S20 touches none of them.
- **Later or other sections:**
  - S14 (landed) owns bar width drawing and `rcap barwidth()`.
  - S27 owns default bases (a padded series' base is S27's default, never compared with twoway here).
  - S32/S36 own pstyle and the named styles; S37 mlabvposition/mlabtextstyle; S40 connect/cmissing.
  - S33 owns marker-label chrome (so tests compare a series' label placement with dash's own single-series rendering, never with twoway's pixels).
  - S06 owns the note channel.
  - S42 owns time-series operators in plot varlists (`mlabel(L.mpg)` keeps today's r(198)).
- **Not edited:**
  - `dash_render.py`;
  - `_dash_validate_value`, `_dash_fold_bw`, `_dash_fold_typed`, `_dash_plot_opts_to_json`, `_dash_stylelist_check`, `_dash_opts_repeats`, `_dash_refuse_unbound`;
  - the Mata `_dash_rep_*` family and S11's Mata bodies;
  - the tracking documents (A145).

  The manifest names `_dash_fold_bw` and `_dash_validate_value`. Both are reached only through their outputs: `bw()`'s copy into `barwidth` feeds the new per-element check unchanged, and `_dash_validate_value` is called per element.
- **Out of scope, measured, left as residuals** (Notes for the closeout):
  - multi-variable elements (Q-20.1);
  - glued `make..` (twoway r(101), dash r(198));
  - `mlabel(L.mpg)` (twoway r(111), dash r(198));
  - `base(abc)` (twoway r(4026), dash r(198)) and rbar `barwidth(.)` (twoway r(199), dash r(198));
  - scalar `base()` on rbar and histogram and `barwidth()` on rspike, accepted where twoway refuses them;
  - lowess and kdensity `bwidth()`, `level()` and `degree()` lists, refused in dash's words where twoway says `option bwidth() not allowed`;
  - `jitterseed(1 2)`, refused where twoway accepts it.
- **Decisions applied:**
  - M1, M6: padding, silent;
  - M5: twoway's rc and words for every new refusal;
  - register P1.1.1 (lone value), P1.1.5 (dash's bounds on used elements, after the shorthands), P1.1.6 (mlabel shorthands), P1.1.7 (extras: style kinds unchecked, every mlabel variable checked).

## Stata truth

**Probes already run (03oct2026).** Each is under `<scratch>/s20-probe/`, run as `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s20-probe <scratch>/s20-probe/pN.do`. Each opens with `adopath ++ "/Users/billy/Desktop/Programs/StataPrograms/d/dash/"`, `global dash_nobrowser 1`, `version 19.5`, `set scheme s2color` and `set graphics off`, and runs `capture noisily twoway <cmd> name(g, replace)` then `graph export <id>.svg`. The results are quoted under Evidence (P01-P36, Q01-Q29, R01-R10, S01-S16, T01-T10, V01-V13). The geometry was read with `scripts/svg_truth.py`:
- **G01-G04.** Data: `set obs 5; gen x=_n; gen y1=30+_n; gen y2=40+_n`. Bars are the `<rect>` elements in the series fills `#486c8c`/`#a65d62`. Width is `w * x.units_per_px`; base is `fit.low + (plotregion.bottom - (y+h)) * |y.units_per_px|`.
  - G01 `barwidth(0.4 0.8) base(10 20)`: `{#486c8c: (0.4, 10.0), #a65d62: (0.8, 20.0)}`.
  - G02 `barwidth(0.4 ..) base(10 =)`: both `(0.4, 10.0)`.
  - G03 `base(50)`: series 1 spans 50 down to 31/32, series 2 30 up to 41/42.
  - G04 `base(. 50)`: the reverse.
- **J01-J03.** Data: `set obs 30; gen x=mod(_n,3); gen y1=mod(_n,2); gen y2=2+mod(_n,2)`. Distinct circle positions per fill: `jitter(5) jitterseed(1)` `{#1a476f: 31, #90353b: 7}`; `jitter(. 5)` `{7, 30}`; `jitter(5 ..)` `{31, 30}`.

**Extractor** `scripts/extract_value_list_truth.do` (new, committed; 20-04):
- **Header.** Copy S11's `scripts/extract_stylelist_truth.do` header: S02's `DASH_REPO` stanza (TR-02.9) with the file's own name, then:
  - `adopath ++ "`repo'/"` and `global dash_nobrowser 1`;
  - `clear all`, `set more off`, `version 19`;
  - `local entry_scheme "`c(scheme)'"` and `set scheme s2color`.
- **Provenance.** `_meta`: `stata_version` (`c(stata_version)`), `born_date` (`c(born_date)`), `dash_commit` (``shell git -C "`repo'" rev-parse HEAD > `tf'``, read with `file read`), `extracted` (`c(current_date)`). The python block reads them with `Macro.getLocal`.
- **Data per case.** The auto cases run `sysuse auto, clear`. The G cases rebuild the 5-observation data, and the J cases the 30-observation data, before each case.
- **Per case.** A text log under `c(pwd)`, then `capture noisily twoway <cmd> name(g, replace)` (a `name()` joins an existing comma list without a second comma, the S11 harness rule), then the log is closed and `_rc` recorded. At rc 0, `graph export <id>.svg, replace name(g)`. A record line `id|rc|cmd|svg|log` goes to a tempfile.
- **Python block** (`sfi.Macro`; `sys.path` gets `<repo>/scripts`; `import svg_truth`). Per record it keeps:
  - `message`: the first log line after the echoed command that is not blank, not a note and not `r(…);`, with U+00A0 read as a blank;
  - `labels` (M cases at rc 0): for each text fill colour other than `#000000`, in document order, `[fill, count, first three texts]`, from `svg_texts` (axis and title texts are black in s2color);
  - `bars` (G cases): per series fill, the distinct `[width, base]` pairs in data units by the reading above, rounded to 0.01, with legend-key rects (outside the plotregion) excluded;
  - `jitter` (J cases): per marker fill, the count of distinct `(cx, cy)` rounded to 0.1.

  It writes `{"cases": {id: record}, "scheme": "s2color", "_meta": {...}}` with `indent=2, sort_keys=True` to `<repo>/test/fixtures/value_list_truth.json`. The block ends `set scheme `entry_scheme'`.

**Cases** (`id: command`; the measured reading in brackets, which the fixture must show).

**mlabel on auto, accepted:**
- M01 `scatter mpg turn weight, mlabel(make rep78)` [labels: make 74 in #1a476f, rep78 74 in #90353b];
- M02 `scatter mpg weight, mlabel(make foreign)` [make only];
- M03 `… mlabel(. rep78)` [rep78 only, #90353b];
- M04 `… mlabel(make .)`;
- M05 `… mlabel(make)` [make, #1a476f only];
- M06 `… mlabel(make rep78 foreign)`;
- M07 `… mlabel(mak rep7)`;
- M08 `… mlabel(make "")`;
- M09 `… mlabel(rep*)`;
- M10 `… mlabel(t*)` [rc 0, no labels];
- M11 `… mlabel(make) mlabel(rep78 foreign)` [rep78, foreign];
- M35 `connected mpg turn weight, mlabel(make rep78) mlabposition(3 9)` [rc 0].

**mlabel on auto, refused:**
- M12 `… mlabel(make ..)` [198, `.. not allowed in option mlabel()`];
- M13 `make ...` [198, `...`];
- M14 `make .. rep78` [198];
- M15 `make =`, M16 `= make` [101, `=exp not allowed`];
- M17 `.`, M18 `. ..` [102, `too few variables specified`];
- M19 `make rep78 nosuch` [111, `variable nosuch not found`];
- M20 `scatter mpg weight, mlabel(rep78 nosuch)` [111];
- M21 `nosuch ..`, M22 `make .. nosuch`, M23 `nosuch =` [111];
- M24 `= nosuch` [101].

**mlabel by plot type:**
- M25 `histogram mpg, mlabel(nosuch ..)` [198];
- M26 `histogram mpg, mlabel(= make)` [198, `invalid syntax`];
- M27 `histogram mpg, mlabel(nosuch)` [0];
- M28 `function y=x, mlabel(make ..)` [198];
- M29 `function y=x, mlabel(nosuch =)` [0];
- M30 `mspline mpg weight, mlabel(make rep78)` [103];
- M31 `mspline mpg weight, mlabel(make ..)` [198];
- M32 `mband mpg weight, mlabel(nosuch rep78)` [111].

**mlabel residual records:**
- M33 `scatter mpg turn weight, mlabel(make..)` [101, `factor-variable and time-series operators not allowed`];
- M34 `… mlabel(L.mpg)` [111, `variable L not found`].

**jitter** (2 y on auto unless marked):
- V01 `jitter(2 3)`, V02 `jitter(2 ..)`, V03 `jitter(. 3)`, V04 `jitter(2 =)` [0];
- V05 `jitter(2 .. 5)` [198, `jitter(2 .. 5):  invalid syntax`];
- V06 `jitter(2 200)` [0];
- V07 `scatter mpg weight, jitter(2 200)` [0];
- V08 `jitter(.)` [0];
- V09 `jitter(2 abc)` [0];
- V10 `scatter mpg weight, jitter(2 abc)` [0].

**base and barwidth:**
- B01 `bar mpg turn weight, base(10 20)`, B02 `base(10 ..)`, B03 `base(10 =)` [0];
- B04 `base(10 .. 20)` [198];
- B05 `barwidth(1 2)`, B06 `barwidth(. 200)`, B07 `barwidth(1 ..)`, B08 `barwidth(.)` [0];
- B09 `dropline mpg turn weight, base(10 20)`, B10 `spike …`, B11 `area mpg turn weight, sort base(10 20)` [0];
- B12 `bar mpg weight, barwidth(1 2)`, B13 `bar mpg weight, base(10 20)` [0].

**Lists twoway refuses:**
- B14 `rbar mpg turn weight, barwidth(50 100)`, B15 `barwidth(50 ..)`, B16 `barwidth(50) barwidth(10 20)` [198, `option barwidth() not allowed`];
- B17 `histogram mpg, barwidth(1 2)`, B18 `rcap mpg turn weight, barwidth(1 2)`, B19 `rspike mpg turn weight, barwidth(1 2)` [198, the same];
- B20 `rbar mpg turn weight, base(10 20)`, B21 `histogram mpg, base(10 20)` [198, `option base() not allowed`];
- B22 `lowess mpg weight, bwidth(.5 .8)` [198, `option bwidth() not allowed`].

**Residual records:**
- B23 `bar mpg turn weight, base(10 abc)` [4026];
- B24 `rbar mpg turn weight, barwidth(.)` [199].

**Geometry:** G01-G04 and J01-J03 as above.

**Run.**

```
mkdir -p <scratch>/s20/truth
DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s20/truth $WT/scripts/extract_value_list_truth.do
git -C $WT add -f test/fixtures/value_list_truth.json
```

The run prints `wrote …value_list_truth.json`. `.git/info/exclude:58` ignores `*.json`, hence `-f`. `test/test_value_lists.py` names the fixture, so `test_fixtures_are_committed.py` passes unedited. A wrong record means re-running the extractor, never a hand edit (R7).

**Truth block** (`test/test_wp30_truth.cscript`, between S01's `S20 start` and `S20 end` lines, gate `WP30_ONLY=S20`; `local s20_scheme "`c(scheme)'"` and `set scheme s2color` are the first statements after the start line, and `set scheme `s20_scheme'` is the last before the end line, so the start and end lines stay the block's first and last statements, TR-01.10 item 4).
- **Helpers.** Python helpers `_s20_page()`, `_s20_app()` and `_s20_svg()` sit at top level directly above `* ==== S20 P1.1b:`, copying the WP-29 `_jo_page_doc`/`_jo_app` pattern (test_wp29_truth.cscript:297-360) as S11's `_s11_*` do:
  - the saved page's Bokeh document, read from its embedded JSON;
  - the generated served app, executed without serving: `make_document` on a fresh `Document`;
  - the live twoway SVG through `svg_truth`.
- **Driver.** Stata program `_s20_case id kind cmd` runs:
  - `twoway <cmd> name(g, replace)` and `graph export`;
  - `dash <cmd> saving(<w30_work>/s20.html, replace)`;
  - `dash <cmd> name(g1)` and `dash build, server saving(<w30_work>/s20.py) replace nobrowser`.

  Then it compares. Files go under `` `w30_work' `` only and are erased before the end line.
- **PS-30** refusals: for M12-M26, M28, M30-M32 and B14-B22, dash's rc equals twoway's, captured live.
  - The first error line is equal, except that for r(111) dash's line ends with twoway's (`… variable nosuch not found`), and for r(103), B18 (S14 may refuse rcap's barwidth() first) and B22 only the rc is compared.
- **PS-31** acceptances: M01-M09, M11, M27, M29, M35, V01-V04, V06 (2 y: dash refuses, the recorded difference: assert twoway 0 and dash 198 with `(got: 200)`), V07, V08, V10, B01-B03 and B05-B13 give rc 0 in both, except as stated. M10 asserts twoway rc 0 and dash r(198) `(got: t*)` (Q-20.1).
- **PS-32** labels per series, both modes, for M01, M02, M03, M05, M06 and M11. Taking twoway's label groups in series order (p1 colour, then p2), the k-th series' first label text and count equal those of dash's k-th LabelSet, in the saved page and in the served document.
- **PS-33** bars per series, both modes:
  - G01 and G02: dash's k-th bar glyph has twoway's width and base, to 0.01;
  - G03 and G04: the series given `base(50)` has base 50, and the padded series' base is not 50.
- **PS-34** jitter per series, both modes, for J01-J03. A series is jittered in dash (its drawn x or y column differs from the data) exactly when twoway's distinct-position count for that series exceeds 7.

## TDD test stubs

### Regression tests, `test/test_value_lists.py` (new; red at the cycle's base unless marked guard)

Module constants:
- `_FIX = test/fixtures/value_list_truth.json`, read lazily by `_fixture()` inside tests;
- `_VALUE_KEYS = ("mlabel", "jitter", "base", "barwidth")`;
- `_SERIES`: case id → list of per-series plot dicts, written out by hand. These are the objects dash.ado now writes (PS-02..PS-10 assert the same), built with `test_server_layer_defects.plot_for` on `test_mode_parity._DF`:
  - `"LAB"` `[plot_for("scatter", {"mlabel": "rep"}, yvar="mpg"), plot_for("scatter", {"mlabel": "foreign"}, yvar="price")]`;
  - `"LAB2"` `[plot_for("scatter", {}, yvar="mpg"), plot_for("scatter", {"mlabel": "foreign"}, yvar="price")]`;
  - `"BAR"` `[plot_for("bar", {"base": "10", "barwidth": "0.4"}, yvar="mpg", xvar="rep"), plot_for("bar", {"base": "20", "barwidth": "0.8"}, yvar="price", xvar="rep")]`;
  - `"DROP"`, `"SPIKE"`, `"AREA"`: the same `base` pair on dropline, spike and area (area with `{"sort": "sort"}`);
  - `"JIT"` `[plot_for("scatter", {"jitterseed": "1"}, yvar="mpg"), plot_for("scatter", {"jitter": "5", "jitterseed": "1"}, yvar="price")]`;
  - `"POS"` `[plot_for("scatter", {"mlabel": "rep", "mlabposition": "3"}, yvar="mpg"), plot_for("scatter", {"mlabel": "rep", "mlabposition": "9"}, yvar="price")]`.

Every spec sets `scheme(s2color)`.

- `TestTheFixture`
  - `test_meta_is_stamped`: the four `_meta` keys exist and `stata_version` starts `19.`.
  - `test_every_case_is_recorded`: every id of "Stata truth" is present.
  - `test_twoway_labels_each_y_with_its_own_variable`: M01's two groups are make then rep78; M03 rep78 in p2 only; M05 make in p1 only.
  - `test_twoway_refuses_the_mlabel_shorthands_in_its_words`: M12-M18 and M24, rc and message.
  - `test_twoway_checks_every_mlabel_variable`: M19-M23.
  - `test_twoway_draws_each_series_from_its_own_base_and_width`: G01 `{(0.4, 10.0)}`, `{(0.8, 20.0)}`; G02 both `(0.4, 10.0)`.
  - `test_twoway_jitters_only_the_series_given`: J01 31/7, J02 7/30, J03 31/30.
  - `test_twoway_refuses_a_list_where_it_takes_one_value`: B14-B21.
- `TestTheParserReadsValueLists` (dash.ado and dash_parse.mata read as text with `test_abbreviations._program_body`)
  - `test_the_four_are_declared_asis`;
  - `test_the_key_list_ends_with_the_four`: the `_dash_stylelist_keys()` literal splits to S11's `_STYLE_KEYS` followed by `_VALUE_KEYS`;
  - `test_the_rules_name_the_value_lists`: `_dash_rules_values` is exactly `_VALUE_KEYS`, and a subset of the key literal;
  - `test_the_onevalue_rules`: `barwidth@rbar|histogram|rcap|rspike` and `base@rbar|histogram`;
  - `test_validate_opts_takes_the_series_count`: `args ptype nser`; in `_dash_process_segment` the `_sl_n` lines precede `_dash_validate_opts "`ptype'" `_sl_n'`;
  - `test_the_value_lists_go_to_value_list`: the branch on `_dash_rules_values` calls `_dash_value_list`;
  - `test_a_write_back_updates_the_snapshot`: `local _snap_`o' : copy local _dash_vnorm` inside the `_chg` block;
  - `test_the_locals_reader_is_public_and_needed`: header entry and `_needed`.
- `TestBothModesDrawEachSeriesValue` (renderer guards, green at base: the renderers already draw a hand-split spec correctly, research p1-01 §3; both modes through `test_mode_parity._spec`, `_standalone` and `_served`)
  - `test_labels_per_series`: in "LAB" the first LabelSet's texts are `rep`'s values and the second's `foreign`'s value labels; in "LAB2" the first series has none.
  - `test_base_and_width_per_series`: in "BAR" the k-th bar glyph's resolved `bottom` is 10/20 and `width` 0.4/0.8. A property given as a field resolves to its column's single distinct value. The same holds for `bottom` on "DROP", "SPIKE" and "AREA".
  - `test_jitter_per_series`: in "JIT" series 1's glyph `x` is `"weight"`; series 2's is not, and its column differs from weight.
  - `test_label_position_per_series`: in "POS" each series' LabelSet (`text_align`, `text_baseline`, the signs of `x_offset`/`y_offset`) equals that of a one-series spec with the same `mlabposition`.
- `TestAfterAFilterMove` (guards, green at base)
  - `test_served_move_keeps_each_series_value`: "LAB", "BAR" and "JIT" with `filter(price, type(range))`, then `test_served_filter_move._move(doc, "RangeSlider", (4500.0, 11385.0))`. After the move each series keeps its own label variable, base, width and (un)jittered x for the kept rows, and the rows changed.
  - `test_saved_move_keeps_each_series_value`: the same specs saved. Set the RangeSlider and run its filter callback with `js_runner.JsSession(...).run_code(r.filter_callbacks[i].code, r.filter_callbacks[i].args)`, the test_colorvar_forms.py:867-871 pattern. The same assertions hold over the rows the page keeps: each series' label texts are its own variable's, and each bar glyph's resolved bottom and width are what they were before the run.
- `TestByPanels` (guard, green at base)
  - `test_every_panel_draws_each_series_value`: "LAB" and "BAR" under `{"by": "foreign"}`. In both modes every panel's k-th series has its own labels, base and width.
- `TestTheHelpSaysSo`
  - `test_the_value_list_sentences`: the 20-12 sentences are in the "Differences from twoway" section;
  - `test_the_old_clause_is_gone`: `{cmd:mlabel()} with more than one variable` is absent;
  - `test_jitter_takes_a_list`: the synopt says "or a list, one per y".

### `PS` run in `test/test_varlist_expansion.cscript` (red at base unless marked guard)

One contiguous run directly after S11's SL run and before `// Summary`, headed `// PS: per-series value lists (WP-30 P1.1b)`.
- Each case uses the script's `capture { … }` / `nfail` / `faillist` pattern and prints `PS-nn PASS: …`.
- Plot *k*'s options text is read with S11's `_sl_opts(st_global("dash_json_<name>"), k)`.
- Each refusal's first error line is read from its own log (`cert_log_has`, saving `r()` first).

The cases:
- **PS-01** `_dash_stylelist_locals`:
  - `make "" rep78 ..` gives n 4, t1 `make` q1 0, t2 `` q2 1, t3 `rep78`, t4 `..`;
  - `` "make" `"rep78"' `` gives q1 1, q2 1;
  - a blank raw gives n 0;
  - an element `char(36)+"G"` and one holding a backtick come back literally;
  - 5,000 `make` elements read within 5 seconds.
- **PS-02** `scatter mpg turn weight, mlabel(make rep78)`: plot 1 `{"mlabel":"make"}`, plot 2 `{"mlabel":"rep78"}`. `_dash_extract_vars` on the spec yields both names.
- **PS-03** padding and forms:
  - `mlabel(make)` gives make, `{}`;
  - `(. rep78)` gives `{}`, rep78;
  - `(make .)` and `(make "")` give make, `{}`;
  - `(make rep78 foreign)` gives make, rep78, and `foreign` is not in `_dash_extract_vars`' list;
  - `(mak rep7)` gives make, rep78;
  - `(rep*)` gives rep78, `{}`;
  - `("make" "rep78")` gives make, rep78;
  - `mlabel(make) mlabel(rep78 foreign)` gives rep78, foreign.
- **PS-04** single y: `scatter mpg weight, mlabel(make foreign)` gives `{"mlabel":"make"}` (HC2-18b's reading); `rscatter mpg turn weight, mlabel(make rep78)` gives make.
- **PS-05** mlabel refusals, rc and exact first line:
  - `make ..`, `make ...` and `make .. rep78` give 198 with `.. not allowed in option mlabel()` (`...` for the second);
  - `make =`, `= make` and `make = rep78` give 101 `=exp not allowed`;
  - `.` and `. ..` give 102 `too few variables specified`;
  - nothing is registered.
- **PS-06** mlabel variables:
  - `make rep78 nosuch`, single-y `rep78 nosuch`, `nosuch ..`, `make .. nosuch` and `nosuch =` give 111 with a line ending `variable nosuch not found`;
  - `= nosuch` gives 101;
  - `t*` gives 198 `dash: mlabel() must name one variable (got: t*)` (Q-20.1 default);
  - `L.mpg` gives 198 (today's words, guard);
  - glued `make..` gives 198 `.. not allowed in option mlabel()` (residual record).
- **PS-07** by type:
  - histogram `(nosuch ..)` gives 198;
  - histogram `(= make)` gives 198 `invalid syntax`;
  - histogram `(nosuch)` gives 0 and no `"mlabel"` in the spec (guard);
  - function `(make ..)` gives 198;
  - function `(nosuch =)` gives 0 (guard);
  - mspline `(make rep78)` and `(. make)` give 103;
  - mspline `(make ..)` gives 198;
  - mband `(nosuch rep78)` gives 111.
- **PS-08** jitter, specs:
  - `jitter(2 3)` gives `{"jitter":"2"}`, `{"jitter":"3"}`;
  - `(2 ..)` and `(2 =)` give 2, 2;
  - `(. 3)` gives `{}`, 3;
  - `(5)` gives 5, `{}`;
  - `(1d1 2)` gives `"10"`, `"2"`;
  - `(.)` gives rc 0, `{}`, `{}`;
  - single-y `(2 200)` and `(2 abc)` give rc 0 and `{"jitter":"2"}`;
  - `rscatter mpg turn weight, jitter(.)` gives rc 0, and no note names `jitter`.
- **PS-09** jitter refusals:
  - 2-y `(2 200)` gives 198 `dash: jitter() must be a number between 0 and 100 (got: 200)`;
  - 2-y `(2 abc)` gives 198 `(got: abc)`;
  - `(2 .. 5)` gives 198 `jitter(2 .. 5):  invalid syntax`;
  - single-y `jitter(5; import os)` gives 198 naming `jitter()`, with nothing registered.
- **PS-10** base and barwidth, specs:
  - `bar mpg turn weight, base(10 20) barwidth(1 2)` gives `{"barwidth":"1","base":"10"}`, `{"barwidth":"2","base":"20"}` in the writer's key order;
  - `base(10 ..)` and `(10 =)` give 10, 10;
  - `barwidth(. 200)` gives `{}`, 200;
  - `barwidth(1 ..)` gives 1, 1;
  - `barwidth(.)` gives `{}`, `{}`;
  - `base(10)` gives 10, `{}`;
  - dropline, spike and `area … sort` `base(10 20)` give 10, 20;
  - single-y `bar mpg weight, barwidth(1 2) base(10 20)` gives 1 and 10;
  - `bar mpg turn weight, bw(1 2)` gives barwidth 1, 2.
- **PS-11** base and barwidth refusals:
  - `base(10 .. 20)` gives 198 `base(10 .. 20):  invalid syntax`;
  - 2-y `barwidth(1 -2)` gives 198 `(got: -2)`;
  - 2-y `barwidth(1 0)` gives 198;
  - 2-y `base(10 abc)` gives 198 `(got: abc)`.
- **PS-12** one-value types:
  - rbar `barwidth(50 100)`, `(50 ..)`, `barwidth(50) barwidth(10 20)` and `(" 50")` give 198 `option barwidth() not allowed`;
  - histogram `barwidth(1 2)` and rspike `barwidth(1 2)` give the same;
  - rcap `barwidth(1 2)` gives 198 (rc only; S14 may refuse it first);
  - rbar and histogram `base(10 20)` give 198 `option base() not allowed`;
  - guards: rbar `barwidth(50)` gives rc 0 `{"barwidth":"50"}`, histogram `barwidth(1)` rc 0, and lowess `bwidth(.5 .8)` 198 with today's words.
- **PS-13** guard (S11): `mlabel(make rep78) mlabposition(3 9)` gives make/3, rep78/9; `mlabposition(3 ..)` gives 3, 3.
- **PS-14** by(): `scatter mpg turn weight, mlabel(make rep78) by(foreign)` and `bar mpg turn weight, base(10 20) by(foreign)` give two plot objects with their own values.
- **PS-15** guard, by value (green at base, where both are already refused as typed): `mlabel("\`jgnone'" rep78)` gives 111 with the line ending `` `jgnone' not found ``; `jitter("\$G")` gives 198 with `$G` in the line; nothing is registered.
- **PS-16** guard: a single plain value's JSON is byte-identical to the base's for `mlabel(make)` on one y, `jitter(5)`, `base(5)` on area and `barwidth(20)` on bar.

### Truth block, `test/test_wp30_truth.cscript` S20

PS-30 to PS-34 as listed under "Stata truth". All are red at base, except the twoway halves and M27/M29.

### Flips (in place; R9; each with a `Flipped:` line)

- `test/test_help_claims_2.cscript` HC2-18b: `198 … "mlabel() must name one variable"` becomes `0`, with no needle. Header :49-51 "mlabel() with two variables" becomes "an mlabel() element that names several variables".
- `test/test_help_claims_2.py::TestTheHelpSaysWhatWasMeasured::test_the_forms_dash_refuses_are_named`: the first string becomes `an element of {cmd:mlabel()} that names several variables`.
- `test/test_stylelists.py::TestTheParserKeepsQuotes::test_the_later_lists_are_not_yet_asis`: `_NOT_YET` loses `mlabel`, `jitter`, `base` and `barwidth`.
- `test/test_stylelists.py::TestOneList::test_the_mata_key_list_is_the_declared_set`: the expected literal is `_STYLE_KEYS + ("mlabel", "jitter", "base", "barwidth")`.
- `test/test_varlist_expansion.cscript` SL-01: 32 words, equal to TR-11.1's list followed by the four, and none of the reduced `_NOT_YET`.

### Guards appended (green at base and after)

`test/test_mode_parity.py`, appended at the end of each list under `# WP-30 P1.1b: per-series value lists` (R8):
- `CORPUS`: `_case("value lists, labels", _SERIES_LAB)` and `_case("value lists, bars", _SERIES_BAR)`, the "LAB" and "BAR" pairs written out inline;
- `MOVE_CORPUS`: `_move_case("value lists, labels, dropdown", _MOVES[0], <LAB>)` and `_move_case("value lists, bars, range", _MOVES[1], <BAR>)`.

No jitter case goes in either corpus: a re-jitter of the kept rows is not the saved oracle's subset, and `test_value_lists.py` covers jitter by column identity.

### Mutation table (each must turn a named test red)

| Mutation | Killed by |
|---|---|
| The four left out of `_dash_stylelist_keys()` (one value for every series) | PS-02, PS-08, PS-10, `test_the_key_list_ends_with_the_four` |
| `_dash_value_list` checks every element, extras too | PS-08 (single-y `jitter(2 200)` rc 0) |
| mlabel extras not checked | PS-06 (`make rep78 nosuch`) |
| `..` checked before the variables | PS-06 (`nosuch ..` is 111) |
| No write-back of normalised elements | PS-08 (`1d1` gives `10`), PS-03 (`mak rep7`) |
| Snapshot not updated after a write-back | PS-08 (`rscatter … jitter(.)` names nothing) |
| onevalue table removed | PS-12 (rbar words) |
| mlabel `=` read as `.` | PS-05 (r(101)) |
| `_dash_value_list` rewrites a misplaced-`..` value | PS-09, PS-11 (`invalid syntax`) |

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Mata locals reader | cscript PS-01 | — | n/a |
| Spec per series, padding, shorthands, single y, by() | cscript PS-02..PS-04, PS-08, PS-10, PS-13, PS-14, PS-16 | — | spec feeds both |
| Refusals, words and order | cscript PS-05..PS-07, PS-09, PS-11, PS-12, PS-15 | — | n/a |
| Parser, tables, wiring | pytest `TestTheParserReadsValueLists` | — | n/a |
| Renderer draws each series' value | pytest `TestBothModesDrawEachSeriesValue` | `value_list_truth.json` | yes |
| After a filter move | pytest `TestAfterAFilterMove`; `test_mode_parity.py` MOVE_CORPUS | — | yes (saved under node, served `_move`) |
| by() panels | pytest `TestByPanels`; cscript PS-14 | — | yes |
| End to end against live twoway | truth PS-30..PS-34 | live SVG | yes (saved page and served app) |
| Help | pytest `TestTheHelpSaysSo`; `test_help_claims_2.py` | — | n/a |
| Registries | `test_program_coverage_map.py`, `test_file_headers.py`, `test_no_orphans.py`, `test_fixtures_are_committed.py`, `test_tracking_documents.py`, `test_option_validation.py` (charter) | — | n/a |
| Neighbours | cscripts `test_option_validation`, `test_twoway_option_parity` (TP-08, TP-12), `test_json_escaping` (JSE-69), `test_adversarial` (P9), `test_string_values` (SV-04), `test_help_claims_2`; pytest `test_stylelists.py`, `test_abbreviations.py`, `test_marker_label_parity.py`, `test_mode_parity.py` | — | — |

**Acceptance criteria.**
- **AC-20.1** `dash scatter mpg turn weight, mlabel(make rep78)` writes `{"mlabel":"make"}` and `{"mlabel":"rep78"}`, and both modes label each series as twoway does (PS-02, PS-32).
- **AC-20.2** `jitter()`, `base()` and `barwidth()` lists, with `.`, `=`, `..` and `...`, write one element per series. Both modes draw twoway's per-series bases and widths, and jitter exactly the series twoway jitters (PS-08, PS-10, PS-33, PS-34).
- **AC-20.3** A lone value over several y applies to the first y only, and a single-y plot takes the first element, with no note (PS-03, PS-04, PS-08, PS-10).
- **AC-20.4** Every mlabel refusal of the fixture matches twoway's rc and first line, in twoway's order (PS-05..PS-07, PS-30).
- **AC-20.5** A used element out of jitter's or barwidth's bounds is refused with the single value's words. An unused one is accepted (PS-08, PS-09, PS-11).
- **AC-20.6** rbar, histogram, rcap and rspike `barwidth()` lists and rbar and histogram `base()` lists are refused in twoway's words. A lowess `bwidth()` list stays refused (PS-12, PS-30).
- **AC-20.7** A served move and the saved filter JS keep each series' labels, base, width and jitter. Every by() panel draws them in both modes (`TestAfterAFilterMove`, `TestByPanels`, PS-14).
- **AC-20.8** HC2-18b and the four S11 pins are flipped with reasons. Every guard of Evidence is green. `dash_render.py` is unchanged.

## Tasks

**Commit boundary.** Tasks 20-01 to 20-13 form the one P1.1b commit. Its subject is `Read mlabel, jitter, base and barwidth lists one element per series (WP-30 P1.1b)`. 20-13 makes it on `wp30-s20` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s20`, after one full run through the queue.
- The body opens with `<scratch>/20-P1.1b-failure.txt`, then gives the measured defect (Overview) and what changed where.
- It then carries one line each of:
  - `Regression: test/test_value_lists.py::<Class>::<test> -- failed at <batch-7 base sha> with <text>` (one per red pytest node);
  - `Regression: test/test_varlist_expansion.cscript PS-nn -- failed at <sha> with <text>` and `Regression: test/test_wp30_truth.cscript PS-nn -- …` (one per red case);
  - the five `Flipped: <node> -- <old expectation> was wrong because <why>` lines of "Flips";
  - `Fixture: test/fixtures/value_list_truth.json (scripts/extract_value_list_truth.do)`;
  - `BUGS.md: "Per-series value lists such as mlabel(make rep78), jitter(2 3), base(10 20) and barwidth(1 2) are refused r(198), where twoway applies them series by series" (closed)` (section-01 Appendix B's title, verbatim; 20-13 checks it equals `WP30_OPEN["P1.1b"]`).

Every command runs from `$WT`. `<scratch>` is the WP-30 scratch directory the orchestrator hands over. No body, BUGS, CHANGELOG or help line names a tool or vendor (G7).

<task type="auto" id="20-01">
  <name>Check the base and write pytest</name>
  <files>test/test_value_lists.py</files>
  <action><![CDATA[
    Check the cut: `git -C $WT rev-parse HEAD` equals `cat <scratch>/batch-7-base.txt`, and `git -C $WT branch --show-current` prints `wp30-s20`. Run `mkdir -p <scratch>/s20`.

    Check S11's interface (Dependencies) with `grep -n "_dash_stylelist_keys\|_dash_stylelist_elems\|_dash_stylelist_pick\|_dash_stylelist_bad\|_dash_stylelist_check\|_sl_n" $WT/dash.ado $WT/dash_parse.mata`:
    - the five Mata functions and `_dash_stylelist_check` exist;
    - `_dash_stylelist_keys()`'s literal holds 28 names, none of them mlabel, jitter, base or barwidth;
    - the `_sl_n` lines follow `_dash_validate_opts "`ptype'"`;
    - `_dash_plot_opts_to_json` takes `series`.

    If any differs, stop and report to the orchestrator before writing anything. Confirm that `<scratch>/batch-7-impact.txt` holds the rows of Evidence "Blast radius", each UNKNOWN with its grep.

    Create `test/test_value_lists.py` with the constants, classes and tests of "TDD test stubs / Regression tests". Helpers:
    - `test_mode_parity._spec`, `_standalone`, `_served`, `_DF`;
    - `test_server_layer_defects.plot_for`;
    - `test_served_filter_move._move`;
    - `js_runner.JsSession`;
    - `test_abbreviations._program_body`;
    - S06's note-count helper.

    The module docstring quotes the defect (Evidence h01, h07, h09) and the twoway reading (M01, G01). Run `python3 -m pytest test/test_value_lists.py -q -n0 -p no:cacheprovider -rf > <scratch>/s20/20-01.log 2>&1`. Write `<scratch>/20-P1.1b-failure.txt` with the base sha, each failing node and its one-line reason, and the guard nodes that passed. Do not commit, and do not weaken a test to make it pass.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/s20/20-01.log` is at least 15; `grep -E "TestTheParserReadsValueLists" <scratch>/s20/20-01.log | grep -c FAILED` is at least 6; `grep -E "TestBothModesDrawEachSeriesValue|TestAfterAFilterMove|TestByPanels" <scratch>/s20/20-01.log | grep -c FAILED` prints 0 (the guards pass at base); `test -s <scratch>/20-P1.1b-failure.txt`; `git -C $WT status --porcelain` lists only `test/test_value_lists.py`.]]></verify>
  <done>S11's interface was confirmed at the base, the pytest module existed, and its regression tests failed on the unmodified tree with the failures recorded.</done>
</task>

<task type="auto" id="20-02">
  <name>Write the failing PS cscript run</name>
  <files>test/test_varlist_expansion.cscript</files>
  <action><![CDATA[
    Append PS-01 to PS-16 of "TDD test stubs / PS run" as one contiguous run directly after S11's SL run and above the `// Summary` block (R1), headed `// PS: per-series value lists (WP-30 P1.1b)`.
    - Reuse S11's `_sl_opts(spec, k)`. Read every spec by value with `st_global`.
    - Each refusal runs under its own `log using` and compares its first error line with `cert_log_has`, saving `r()` first.
    - Extend the header's test list with `PS-01 through PS-16`.

    Write the driver: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_varlist_expansion.cscript > <scratch>/s20/run_test_varlist_expansion.do`. Run it with `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s20 <scratch>/s20/run_test_varlist_expansion.do`. Append the `PS-nn FAIL` lines to `<scratch>/20-P1.1b-failure.txt` under `test_varlist_expansion.cscript`, and the passing guards under "guards".
  ]]></action>
  <verify><![CDATA[In `<scratch>/s20/run_test_varlist_expansion.log`: `grep -c "PS-[0-9][0-9] FAIL"` prints 13; `grep -cE "PS-1[356] PASS"` prints 3 (the guards PS-13, PS-15, PS-16); `grep -cE "(V2|SL)-[0-9][0-9] FAIL"` prints 0.]]></verify>
  <done>The value-list cases were in the area script, the regression cases failed on the unmodified tree, the guards passed, and the V2 and SL cases were untouched.</done>
</task>

<task type="auto" id="20-03">
  <name>Write the S20 truth block red</name>
  <files>test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Directly above `* ==== S20 P1.1b: Per-series value lists ====`, add the top-level python helpers `_s20_page()`, `_s20_app()` and `_s20_svg()` and the Stata program `_s20_case` (`version 19`) of "Stata truth / Truth block", copying the WP-29 `_jo_page_doc`/`_jo_app` pattern (test_wp29_truth.cscript:297-360).

    Between S01's `S20 start` and `S20 end` lines, write PS-30 to PS-34. Each case is closed by `_w30_done` and its checks use `_w30_expect`. Files go only under `` `w30_work' `` and are erased before the end line. Set the scheme to s2color directly after the start line and restore the entry scheme directly before the end line (the start and end lines stay the block's first and last statements).

    Run the block alone through the driver: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp30_truth.cscript > <scratch>/s20/run_test_wp30_truth.do`, then `WP30_ONLY=S20 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s20 <scratch>/s20/run_test_wp30_truth.do`. Append the `PS-3n FAIL` lines to the failure file.
  ]]></action>
  <verify><![CDATA[In `<scratch>/s20/run_test_wp30_truth.log`: `grep -cE "PS-3[0-4] FAIL"` is at least 4; `grep -c "S20 start"` and `grep -c "S20 end"` each print 1; no other section's start line appears.]]></verify>
  <done>The S20 truth block compared dash with live twoway in both modes and failed on the unmodified tree.</done>
</task>

<task type="auto" id="20-04">
  <name>Extract the value-list truth fixture</name>
  <files>scripts/extract_value_list_truth.do, test/fixtures/value_list_truth.json</files>
  <action><![CDATA[
    Create `scripts/extract_value_list_truth.do` as "Stata truth / Extractor" says: the header copied from `scripts/extract_stylelist_truth.do`, the `_meta` provenance, data per case, one log and record per case, and the python block with `message`, `labels`, `bars` and `jitter`. Its header comment gives the run line with `DASH_REPO=<repo>` and names the fixture.

    Run it as "Stata truth / Run" says, then `git -C $WT add -f test/fixtures/value_list_truth.json`. Re-run `python3 -m pytest test/test_value_lists.py -q -n0 -p no:cacheprovider -k TestTheFixture`. Every TestTheFixture test passes, because the fixture records twoway, not dash.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('$WT/test/fixtures/value_list_truth.json'));print(sorted(d['_meta']), d['cases']['M15']['rc'], d['cases']['M17']['message'], d['cases']['B14']['message'], d['cases']['G01']['bars'])"` prints the four meta keys, `101`, `too few variables specified`, `option barwidth() not allowed` and the G01 pairs (0.4, 10.0) and (0.8, 20.0); `grep -c "arch -arm64\|/Users/billy" $WT/scripts/extract_value_list_truth.do` prints 0; TestTheFixture passes.]]></verify>
  <done>The committed extractor wrote the stamped fixture of twoway's value-list readings, and the fixture tests passed.</done>
</task>

<task type="auto" id="20-05">
  <name>Add the keys and locals reader</name>
  <files>dash_parse.mata, dash.ado, test/test_varlist_expansion.cscript</files>
  <action><![CDATA[
    In dash_parse.mata:
    - In `_dash_stylelist_keys()`'s literal, append `mlabel jitter base barwidth` after `alpattern` (TR-20.1), and reword the comment above it so it names S32, S37 and S40 as the later adders.
    - Add `_dash_stylelist_locals(raw, stub)` directly after `_dash_stylelist_probe` (TR-20.9), with a three-line comment.
    - Add its Public API entry after S11's `_dash_stylelist_probe(tok)` entry.

    In dash.ado, add `_dash_stylelist_locals` to `_needed` on S11's stylelist continuation line.

    Flip SL-01 in `test/test_varlist_expansion.cscript` (Flips) in the same task, since the key list moves here, and add its line to `<scratch>/s20/20-flips.txt`. Do not run the PS run yet: dash.ado's declarations still bind the four as `string`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_value_lists.py -q -n0 -p no:cacheprovider -k "key_list_ends or locals_reader"` passes; `python3 -m pytest test/test_file_headers.py test/test_program_coverage_map.py -q -n0 -p no:cacheprovider` fails only on `_dash_stylelist_locals` (not yet called or mapped; 20-07 and 20-10 finish it).]]></verify>
  <done>The four value keys joined S11's list, SL-01 counted them, and the locals reader existed, was public and was required.</done>
</task>

<task type="auto" id="20-06">
  <name>Declare and route the value lists</name>
  <files>dash.ado</files>
  <action><![CDATA[
    In `_dash_parse_plot_opts`' syntax, `MLabel`, `JITter`, `BASE` and `BARWidth` become `(string asis)` (TR-20.2). Add no `//` line to that program.

    In `_dash_option_rules`, add the `values` and `onevalue` locals and their `c_local`s under the `local flags` block, each with a comment of at most five lines (TR-20.3).

    In `_dash_validate_opts`:
    - `args ptype nser` with the default of 1;
    - the branch on `_dash_rules_values` calling `_dash_value_list` and otherwise `_dash_validate_value`, unchanged;
    - the snapshot update inside the `_chg` block (TR-20.4).

    In `_dash_process_segment`, move S11's two `_sl_n` lines above the call and pass `` `_sl_n' `` (TR-20.5).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_value_lists.py -q -n0 -p no:cacheprovider -k TestTheParserReadsValueLists` passes; `python3 -m pytest test/test_option_validation.py test/test_abbreviations.py -q -n0 -p no:cacheprovider` passes (the charter, the contract table and the comment-count pin unchanged). No cscript is run until 20-07 defines `_dash_value_list`.]]></verify>
  <done>The four options kept their quotes, the tables named the value lists and the one-value types, and the validator knew the series count.</done>
</task>

<task type="auto" id="20-07">
  <name>Write the value and mlabel checks</name>
  <files>dash.ado</files>
  <action><![CDATA[
    Add `program define _dash_value_list, rclass` (TR-20.6) and `program define _dash_mlabel_list, rclass` (TR-20.7) directly after `_dash_validate_value`'s `end`, in that order.
    - Each opens `version 19` and reads its arguments with `_dash_text_args`.
    - Each has a header comment of at most twelve lines naming twoway's measured cases (M12-M24, B14-B21, P1.1.5-P1.1.7).
    - Every refusal is one `display as error` line of fixed text, or `_dash_validate_value`'s echo.
    - The mlabel name cache is a local list tested with `anyof(tokens(...))` in Mata, by value.

    Run the PS run through the driver of 20-02.
  ]]></action>
  <verify><![CDATA[In `<scratch>/s20/run_test_varlist_expansion.log`: PS-01 to PS-06 and PS-08 to PS-16 print PASS; PS-07 may still fail (20-08); `grep -cE "(V2|SL)-[0-9][0-9] FAIL"` prints 0.]]></verify>
  <done>Each used element of jitter, base and barwidth was checked after the shorthands resolved, and mlabel was read in twoway's order and words.</done>
</task>

<task type="auto" id="20-08">
  <name>Apply mlabel checks per type</name>
  <files>dash.ado</files>
  <action><![CDATA[
    In `_dash_fold_mlab` (TR-20.8):
    - On histogram and function, refuse a bare `..`/`...` element (and `=` on histogram alone) through `_dash_stylelist_locals`, then drop as today.
    - On mspline and mband, call `_dash_mlabel_list "dash" ... "`ptype'" 1` in place of `capture confirm variable`, then keep the r(103) line.

    Extend the header comment by three lines naming the measured cases (S08, T01, T04, S06, S07, T08, T10). Run the PS run, then `test_twoway_option_parity.cscript` through a driver written as in 20-02.
  ]]></action>
  <verify><![CDATA[In the PS log every `PS-[0-9][0-9]` line prints PASS; in `<scratch>/s20/run_test_twoway_option_parity.log` `grep -cE "TP-(08|12) PASS"` prints 2 and `grep -c "ALL CHECKS PASSED"` prints 1.]]></verify>
  <done>mlabel was refused per plot type as twoway refuses it, and the mspline and mband refusal kept its r(103) after twoway's earlier checks.</done>
</task>

<task type="auto" id="20-09">
  <name>Flip the pinned help claims</name>
  <files>test/test_help_claims_2.cscript, test/test_help_claims_2.py, test/test_stylelists.py</files>
  <action><![CDATA[
    Flip, in place, with a trailing comment `// P1.1b: twoway labels with the first variable (HC2-18a)` or `# P1.1b: …`:
    - HC2-18b to `_hc2_dash "HC2-18b" 0 ... ` with no needle, and header lines :49-51;
    - `test_the_forms_dash_refuses_are_named`'s first string;
    - `_NOT_YET` and `test_the_mata_key_list_is_the_declared_set` in `test/test_stylelists.py` (Flips).

    Record each node and its old expectation in `<scratch>/s20/20-flips.txt` for the commit's `Flipped:` lines. Run the pytest files, then `test_help_claims_2.cscript` through a driver.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_claims_2.py test/test_stylelists.py -q -n0 -p no:cacheprovider` passes except the help assertions written for 20-12 (listed as such); in `<scratch>/s20/run_test_help_claims_2.log` `grep -c "HC2-18b PASS"` prints 1.]]></verify>
  <done>Each pin that asserted the old refusal or the old key list was flipped with its reason recorded.</done>
</task>

<task type="auto" id="20-10">
  <name>Register units and parity cases</name>
  <files>test/program_coverage_map.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Under S01's `# WP-30 S20 (P1.1b): Per-series value lists (P1.1 part b)` anchors, add the three entries of TR-20.11, alphabetically. Append the CORPUS and MOVE_CORPUS cases of "Guards appended" (R8), under the comment `# WP-30 P1.1b: per-series value lists`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_program_coverage_map.py test/test_file_headers.py test/test_no_orphans.py test/test_function_test_map.py test/test_mode_parity.py -q -n0 -p no:cacheprovider` passes; the PS and SL runs print no FAIL.]]></verify>
  <done>The new programs and the Mata reader were mapped to their cases, and the parity corpus drew each series' value alike in both modes before and after a move.</done>
</task>

<task type="auto" id="20-11">
  <name>Run the neighbouring tests green</name>
  <files>none</files>
  <action><![CDATA[
    Run, through two-line drivers as in 20-02, each from `$WT`:
    - `test_option_validation.cscript`, `test_json_escaping.cscript`, `test_adversarial.cscript`, `test_string_values.cscript`, `test_varlist_expansion.cscript`;
    - `test_wp30_truth.cscript` with `WP30_ONLY=S20`, then with `WP30_ONLY=S11`.

    Run `python3 -m pytest test/test_value_lists.py test/test_stylelists.py test/test_option_validation.py test/test_marker_label_parity.py test/test_twoway_option_parity.py test/test_abbreviations.py -q -n0 -p no:cacheprovider`. A failure is fixed in the section's own files, never by weakening a test.
  ]]></action>
  <verify><![CDATA[Each cscript log ends with its `ALL CHECKS PASSED` line and holds no `SKIP`; the truth logs print PS-30 to PS-34 PASS (S20) and SL-30 to SL-38 PASS (S11); the pytest run shows 0 failed apart from `TestTheHelpSaysSo` (20-12).]]></verify>
  <done>Every neighbouring certification script and pytest file passed with the value lists in place.</done>
</task>

<task type="auto" id="20-12">
  <name>Write the value-list help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    Edit "Differences from twoway" and "Marker and Transparency Options" only (R3):

    1. :711, `Variables: {cmd:mlabel()} and {cmd:colorvar()} name one,` becomes `Variables: {cmd:colorvar()} names one, {cmd:mlabel()} one per y (see {help dash##stylelists:Style lists}),`.

    2. :741-742, the clause `{cmd:mlabel()} with more than one variable ({cmd:twoway} labels the markers with the first);` becomes `an element of {cmd:mlabel()} that names several variables, such as {cmd:t*} ({cmd:twoway} draws no labels for that y);`.

    3. Append to the end of S11's `{marker stylelists}` paragraph:

    `{cmd:mlabel()}, {cmd:jitter()}, {cmd:base()} and {cmd:barwidth()} are read the same way, one element per y: {cmd:scatter mpg turn weight, mlabel(make rep78)} labels {cmd:mpg}'s markers with {cmd:make} and {cmd:turn}'s with {cmd:rep78}, and {cmd:bar y1 y2 x, base(10 20) barwidth(0.4 0.8)} draws each series from its own base at its own width.  A lone value applies to the first y, so {cmd:mlabel(make)} labels the first y alone.  In {cmd:mlabel()}, {cmd:.} leaves that y unlabelled, and {cmd:twoway}'s refusals are kept, in its words: {cmd:..} or {cmd:...} anywhere ({cmd:.. not allowed in option mlabel()}, r(198)), {cmd:=} ({cmd:=exp not allowed}, r(101)), a list of {cmd:.} alone ({cmd:too few variables specified}, r(102)), and a variable that does not exist, even past the last y, r(111).  A list in {cmd:barwidth()} on {cmd:rbar}, {cmd:histogram}, {cmd:rcap} or {cmd:rspike}, or in {cmd:base()} on {cmd:rbar} or {cmd:histogram}, is refused as {cmd:twoway} refuses it ({cmd:option barwidth() not allowed}, r(198)).  Each {cmd:jitter()} or {cmd:barwidth()} element a y uses is held to 0 to 100 or to positive, which {cmd:twoway} does not check; elements past the last y are not checked.`

    4. The `jit:ter(#)` synopt (:3236-3238): `{it:#} must be a number from 0 to 100.` becomes `{it:#} must be a number from 0 to 100, or a list of them, one per y (see {help dash##stylelists:Style lists}).`

    Write no runnable `{cmd:. dash` example.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_value_lists.py test/test_help_claims_2.py test/test_stylelists.py test/test_help_examples.py -q -n0 -p no:cacheprovider` passes; `grep -c "with more than one variable ({cmd:twoway} labels" $WT/dash.sthlp` prints 0; `grep -Eic "claude|anthropic" $WT/dash.sthlp` prints the same count as at the base.]]></verify>
  <done>The help said how the value lists are read per y, which forms are refused in twoway's words, and that jitter() takes a list.</done>
</task>

<task type="auto" id="20-13">
  <name>Close the entry and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Close the BUGS.md entry whose title is `WP30_OPEN["P1.1b"]`, in place: `- [x]`, and its Resolution line `  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.1b).` (two-space indent, TR-01.10 item 1) followed by the text of "Notes / BUGS.md Resolution". Delete only the `"P1.1b"` key line of `WP30_OPEN` (R5).

    Replace the two `<!-- WP-30 P1.1b -->` markers in place with the "Changed behaviour" and "Fixed in WP-30" lines of "Notes / CHANGELOG lines". Add the "Results that change" line in the `**WP-30 (drop-in P1, 03oct2026)**` group, directly after the last line of that group ending `(WP-30, P1.1a)` (entry order; R4: a section that needs another list edits its own `WP30_LISTS` row in the same commit). In `test/test_tracking_documents.py`, `WP30_LISTS["P1.1b"]` gains "Results that change" first, in the index's list order (R4).

    Then, in order:
    1. Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`.
    2. Run `git -C $WT merge --no-edit main`, expecting `Already up to date.`.
    3. Run one full suite through the queue, `<scratch>/full_suite_queue.sh $WT <scratch>/20-full-1.log`, in the background. Wait for its `exit=` line and read the log (E1, E6).
    4. Stage: `git -C $WT add -f test/fixtures/value_list_truth.json`, then `git -C $WT add` dash.ado dash_parse.mata dash.sthlp BUGS.md CHANGELOG.md scripts/extract_value_list_truth.do test/test_value_lists.py test/test_varlist_expansion.cscript test/test_wp30_truth.cscript test/test_help_claims_2.cscript test/test_help_claims_2.py test/test_stylelists.py test/program_coverage_map.py test/test_mode_parity.py test/test_tracking_documents.py.
    5. Check G6: `git -C $WT diff --cached --name-only` lists exactly those 16 files. Write the message file and check G7 on it.
    6. Commit once with the subject and body of "Commit boundary", then run G7 on `git -C $WT log -1 --format=%B`.
  ]]></action>
  <verify><![CDATA[`grep -c "exit=0" <scratch>/20-full-1.log` prints 1 and the log shows 0 failed; `grep -c '<!-- WP-30 P1.1b -->' CHANGELOG.md` prints 0; `grep -c '(WP-30, P1.1b)' CHANGELOG.md` prints 3; `python3 -c "import sys; sys.path.insert(0, '$WT/test'); import test_tracking_documents as t; print('P1.1b' in t.WP30_OPEN, t.WP30_LISTS['P1.1b'])"` prints `False` and a row whose first list is "Results that change"; `git -C $WT log -1 --format=%s` ends `(WP-30 P1.1b)`; `git -C $WT log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `git -C $WT show --stat --format= HEAD -- dash_render.py` prints nothing.]]></verify>
  <done>The P1.1b entry was closed with tests that exist, its CHANGELOG lines carried the before and after in three lists, and one green commit landed the section on its branch.</done>
</task>

## Section completion criteria

- [ ] One commit on `wp30-s20`, subject ending `(WP-30 P1.1b)`, made after one green full run through the queue. Its body carries the failure text, the regression lines, the five flip lines, the fixture line and the BUGS line.
- [ ] `test/test_value_lists.py` green. PS-01..PS-16 print PASS in `test_varlist_expansion.cscript`. PS-30..PS-34 print PASS with `WP30_ONLY=S20`. There is no SKIP.
- [ ] `test/fixtures/value_list_truth.json` committed with `git add -f`, its `_meta` holding the four keys, written by the committed, path-free `scripts/extract_value_list_truth.do`.
- [ ] dash.ado:
  - the four `string asis` declarations;
  - the `values`/`onevalue` tables;
  - `_dash_validate_opts`' series count, routing and snapshot update;
  - `_dash_value_list` and `_dash_mlabel_list`;
  - `_dash_fold_mlab`'s per-type checks;
  - `_needed`.
- [ ] dash_parse.mata: the 32-name key literal; `_dash_stylelist_locals` with its header entry.
- [ ] HC2-18b, its pytest mirror, S11's two pytest pins and SL-01 are flipped. Every guard of Evidence is green.
- [ ] dash.sthlp: :711, :741-742, the Stylelists sentences and the jitter synopt.
- [ ] BUGS.md entry closed, `WP30_OPEN["P1.1b"]` deleted, both markers replaced, the Results line added and `WP30_LISTS["P1.1b"]` extended.
- [ ] `dash_render.py` and every copy list unchanged.

## Notes

- **Anchors are at `c96facd`.** S03 changed `version 16.0` to `version 19`. S06 moved notes to `_dash_emit_note`. S08 changed the size forms of `_dash_option_rules`/`_dash_validate_value`. S11 inserted its normaliser, `_dash_stylelist_check` and the writer's series argument. S14 changed bar widths. Re-read the touched programs at the batch-7 base; symbols govern, not line numbers.
- **Two passes, one rule.** For the four value keys, `_dash_validate_opts` (through `_dash_value_list`) validates and normalises, and S11's `_dash_stylelist_check` re-validates the normalised list. Never rewrite a value `_dash_stylelist_bad` flags, or S11's twoway-worded refusal is lost (PS-09, PS-11).
- **Write-back form.** A rewritten value is exactly `nser` blank-separated elements, `.` for "not given", or `""` when none is given. No element holds a blank: numbers are trimmed by `_dash_validate_value`, and names are single variables.
- **The snapshot.** `_snap_<o>` is set to the written value in the same block that writes it. Without that, `jitter(.)` is restored to `.` by the next rule's loop.
- **Merge rules touched.**
  - R1: the area script `test_varlist_expansion.cscript` (after S11's run; S20 is its only batch-7 editor) and S20's own truth block.
  - R2: no copy-list change.
  - R3: dash.sthlp, only "Differences from twoway" and the jitter synopt.
  - R4: three CHANGELOG lines.
  - R5: BUGS.md and `WP30_OPEN`.
  - R6: dash.ado and dash_parse.mata. No batch partner adds an option key or a Mata function; `version 19` on the new programs.
  - R7: one new extractor and fixture.
  - R8: `test_mode_parity.py` appends.
  - R9: five flips.
- **Commit-body line forms** are those under "Commit boundary". The failure file is `<scratch>/20-P1.1b-failure.txt`; the flips are in `<scratch>/s20/20-flips.txt`.
- **Python under Stata.** The truth block's helpers run in Stata's Python. They import only what `_jo_*` imports, and are guarded by the script's `c(python_exec)` gate (S01). No new SKIP line is added.
- **Q-20.1 (resolved by the register's P1.1.5 precedent, review pass).** P1.1.5 keeps dash's stricter per-element checks and files "dash refuses what twoway accepts" under P2.14; the same ruling governs this case, so the default below stands and no maintainer answer is needed. An `mlabel()` element that names several variables (`t*`, `make-price`, `mpg-rep78`) is rc 0 in twoway, which silently draws no labels for that y (Q01-Q03, R01, R02). This section is written on the default: keep today's refusal per element, `dash: mlabel() must name one variable (got: t*)`, r(198). That is a "dash refuses what twoway accepts" difference (P2.14 family) and is documented in the help. The alternative matches twoway: the element is read as `.`, silently. That needs `_dash_mlabel_list` to call `unab` itself and to test the count instead of using the `var` kind. Then PS-06's `t*` case and PS-31's M10 flip to rc 0, and the help clause at :741-742 is removed.

**BUGS.md Resolution** (20-13; one line after `Fixed <ddmonyyyy> (WP-30, P1.1b).`): "dash.ado declares mlabel(), jitter(), base() and barwidth() `string asis` and lists them in `_dash_stylelist_keys()`, so `_dash_plot_opts_to_json` writes each expanded series its own element through `_dash_stylelist_pick`, with `.`, `=`, `..` and `...`, padding with `.` and the first element on a single-y type. `_dash_validate_opts` takes the series count and hands those four to the new `_dash_value_list`. It checks each element a y uses with the single value's rule after the shorthands resolve, writes the normalised list back, and refuses a list in barwidth() on rbar, histogram, rcap and rspike and in base() on rbar and histogram in twoway's words (`_dash_option_rules`' onevalue table). The new `_dash_mlabel_list` reads mlabel() in twoway's order and words: = r(101), every named variable checked once and past the last y r(111), no variable r(102), `..` r(198). `_dash_fold_mlab` applies it before mspline's and mband's r(103), and refuses `..` on histogram and function and = on histogram. The renderers are unchanged and draw each series' labels, jitter, base and width in the saved page and the served app, before and after a filter move and in every by() panel. Pinned by test/test_value_lists.py::TestTheParserReadsValueLists::test_the_key_list_ends_with_the_four, test/test_value_lists.py::TestBothModesDrawEachSeriesValue::test_labels_per_series, test/test_value_lists.py::TestBothModesDrawEachSeriesValue::test_base_and_width_per_series, test/test_value_lists.py::TestAfterAFilterMove::test_served_move_keeps_each_series_value, test/test_varlist_expansion.cscript PS-02, test/test_varlist_expansion.cscript PS-05, test/test_varlist_expansion.cscript PS-12, test/test_wp30_truth.cscript PS-30; fixture test/fixtures/value_list_truth.json. Residual, deferred (WP-30): an mlabel() element naming several variables (t*) is refused where twoway draws no labels for that y; glued make.. in mlabel() is r(198) where twoway gives r(101); mlabel(L.mpg) stays r(198) where twoway gives r(111); scalar base() on rbar and histogram and barwidth() on rspike are accepted where twoway refuses them; lowess and kdensity bwidth(), level() and degree() lists keep dash's words."

**CHANGELOG lines** (20-13):
- **Results that change** (new line after P1.1a's): "A lone `mlabel()`, `jitter()`, `base()` or `barwidth()` value over several y now applies to the first y only, as twoway pads a list with `.`. `dash scatter mpg turn weight, mlabel(make)` labelled both series and now labels mpg's alone, and `dash bar mpg turn weight, base(50)` drew both series from 50 and now draws turn from its default base. Nothing is printed, as in twoway. (WP-30, P1.1b)"
- **Changed behaviour (may need your do-files changed):** "mlabel() now refuses what twoway refuses, with twoway's codes and words. `..` or `...` anywhere is `.. not allowed in option mlabel()`, r(198), and `=` is `=exp not allowed`, r(101); both were r(111), `variable .. not found`. A list of `.` alone is `too few variables specified`, r(102), where it was r(111). Every variable named must exist, even past the last y, r(111). On histogram and function, `mlabel(nosuch ..)` was dropped and is now refused, r(198), and on histogram `mlabel(= make)` is now refused `invalid syntax`, r(198). On mspline and mband the same checks now run before the r(103) refusal, so `mspline mpg weight, mlabel(make ..)` is r(198) where it was r(111). A list in barwidth() on rbar, histogram, rcap or rspike, or in base() on rbar or histogram, is now refused in twoway's words, `option barwidth() not allowed`, r(198), where dash said `must be a positive number`. (WP-30, P1.1b)"
- **Fixed in WP-30:** "`mlabel()`, `jitter()`, `base()` and `barwidth()` take a list, one element per y of an expanded varlist, as in twoway. `dash scatter mpg turn weight, mlabel(make rep78)` labels mpg's markers with make and turn's with rep78, and `dash bar mpg turn weight, base(10 20) barwidth(1 2)` draws each series from its own base at its own width; each was refused r(198). `.`, `=`, `..` and `...` resolve as in twoway, so `jitter(2 ..)` and `base(10 =)` draw. A single-y plot takes the first element: `dash scatter mpg weight, mlabel(make foreign)` labels with make, where it was refused. `jitter(.)` and `barwidth(.)` now mean the default; they were refused. Elements past the last y are not checked: `dash scatter mpg weight, jitter(2 200)` draws. (WP-30, P1.1b)"

**Notes for the closeout (S58; A145)** (the tracking-document text this section hands over).
- **GAPS2.md D8.** Record D8 Closed: sentences a-e for style options by the P1.1a commit `<sha>`, and the value lists by the P1.1b commit `<sha>`. The Tracked line names both: `- **Tracked:** Closed in WP-30, BUGS.md "<P1.1a title>", commit <sha>; BUGS.md "<P1.1b title>", commit <sha>`. `(WP-30, GAPS2-D8)` is appended to both Resolutions.
- **REMAINING.md row 06.** "positional plot-options across an expanded varlist" is closed by P1.1a `<sha>` (style options) and P1.1b `<sha>` (value lists). REM-S06-c is cited by both. The row's remaining open items (`horizontal`, `vertical`, no S06 CHANGELOG entry) are untouched here.
- **DROPIN-REMAINING.md P1.1.** Closed: part a S11 `<sha>`, part b S20 `<sha>`.
- **TWOWAY_COVERAGE_AUDIT.md.** Tag stylelists ([G-4] stylelists): "honoured for style options (WP-30 P1.1a) and for mlabel(), jitter(), base() and barwidth() value lists (WP-30 P1.1b)".
- **New P2 residuals to file** (or add to the named existing items):
  - (P2.14, dash refuses what twoway accepts) an mlabel() element naming several variables (`t*`, `make-price`; per Q-20.1's answer), and the per-element jitter 0-100 and barwidth > 0 bounds and `jitterseed(1 2)` (twoway draws `jitter(2 abc)`, `barwidth(1 -2)`, `jitterseed(1 2)`);
  - (P2.21, refuse-vs-note sweep) scalar `base()` on rbar and histogram and `barwidth()` on rspike, which twoway refuses `option base() not allowed`/`option barwidth() not allowed` and dash accepts;
  - lowess and kdensity `bwidth()`, `level()` and `degree()` lists, which keep dash's words where twoway says `option <opt>() not allowed`;
  - `base(abc)`, r(198) where twoway gives r(4026) `abc not found` / `rvalue invalid`;
  - rbar `barwidth(.)`, r(198) where twoway gives r(199);
  - glued `mlabel(make..)`, r(198) `.. not allowed in option mlabel()` where twoway gives r(101) `factor-variable and time-series operators not allowed` (and rc 0 on histogram);
  - `mlabel(L.mpg)`, r(198) where twoway gives r(111) `variable L not found` (with S42's operator work if it reaches option varlists);
  - `mlabposition(13)`'s note words and default differ from twoway's `named style 13 not found in class clockdir` (S06/S33 territory).
