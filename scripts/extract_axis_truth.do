*! extract_axis_truth.do
*! Derive AXIS / LEGEND / TITLE / REFERENCE-LINE ground truth for section S09
*! BY PROBING STATA ITSELF.  Nothing in the output fixture is remembered,
*! inferred from documentation, or copied from another implementation: every
*! recorded value carries the command that produced it, and anything the
*! probes could not establish is listed under "unverified" instead of guessed.
*!
*! Output: test/fixtures/axis_truth.json
*!
*! Run with (the slot wrapper starts Stata from a scratch directory, because
*! batch mode writes its .log to the process working directory):
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_axis_truth.do
*!
*! ---------------------------------------------------------------------------
*! METHOD -- and why the .gph oracle is not enough on its own
*!
*! scripts/extract_abbrev_truth.do establishes ground truth by comparing
*! live-format .gph files, which are plain-text graph-object scripts.  That
*! oracle answers "which option did this abbreviation resolve to".  It CANNOT
*! answer "what ticks did Stata choose", because a .gph records the REQUEST,
*! not the result.  xlabel(#10) is stored as
*!
*!     .xaxis1.major.clear
*!     .xaxis1.style.editstyle majorstyle(numticks(10)) editcopy
*!     .xaxis1.major.suggest_ticks 10
*!
*! -- the word "suggest" is Stata's own.  Tick positions are computed at render
*! time and never written to the .gph, drawn or not: a .gph saved from a fully
*! DRAWN graph was checked and contains no tick, major or axis member at all.
*!
*! So this script uses TWO oracles and records both:
*!
*!   1. .gph (live format, saved without asis) -- the DECLARATIVE record.
*!      Authoritative for structure: which ring a title/note/caption is
*!      inserted at, which side of the plotregion, and the verbatim editstyle
*!      directives an option produced.  Per-run object ids (K<hex>), the echoed
*!      command and the wall-clock stamps are normalised away, exactly as in
*!      extract_abbrev_truth.do.
*!
*!   2. SVG (graph export, Stata's own vector writer) -- the RENDERED record.
*!      A Stata SVG is plain text in which
*!        * the plotregion is a solid-fill <rect> written before its border,
*!        * every tick mark is a short black <line> touching a plotregion edge,
*!        * every tick label is a <text> whose x (x axis) or y (y axis) is at
*!          that tick,
*!        * every gridline is a dashed multi-segment <line> group at a tick,
*!        * the legend sits in its own <rect> region and its keys are <text>
*!          elements with no text-anchor attribute.
*!      Fitting (tick pixel -> tick value) over the numeric tick labels gives
*!      the exact data<->pixel map; inverting it at the plotregion edges gives
*!      the axis range Stata actually used, which is what makes the default
*!      range extension measurable.
*!
*! Legend presence is decided by a DIFFERENCE, never by an eyeball: every
*! legend case is run twice, once bare and once with legend(off), and the
*! anchorless <text> elements that disappear are the legend.  Where legend(off)
*! turns out to have no effect (it does not, under by()), the pair is flagged
*! and a second, independent classifier is used: the anchorless texts minus
*! every string the .gph records in an mtextq() textbox.  Both verdicts are
*! written to the fixture and any disagreement is reported.
*!
*! Structure follows extract_abbrev_truth.do: Stata runs every probe and
*! records (id, group, command, rc, svg path, gph path) into a plain-text
*! record file; a single trailing python: block reads that record file, parses
*! the SVGs and .gphs, and writes the JSON fixture.  The python block never
*! calls back into Stata -- SFIToolkit.stata() issued from a do-file python
*! block desynchronises the interpreter's input stream.
*!
*! TRAP, found the hard way and worth keeping: Stata expands a backtick/
*! apostrophe pair as a local macro reference INSIDE a python: block in a
*! do-file.  A regex written with a literal backtick silently loses everything
*! up to the next apostrophe and then matches nothing.  Every regex below that
*! needs a backtick spells it \x60.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off
set linesize 200

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_axis_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zr_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zr_rc' | _rc {
    local _zr_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_axis_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZA_REPO "`repo'"
global ZA_OUT  "${ZA_REPO}/test/fixtures/axis_truth.json"

local scratch "`c(tmpdir)'/dash_axis_probe"
capture mkdir "`scratch'"
global ZA_WORK "`scratch'"
global ZA_REC  "`scratch'/axis_records.txt"
display as text "probe scratch dir: ${ZA_WORK}"

* WP-28 S18: Section 02's programs, for cert_graph_scale (the .Graph scale
* members read beside each b2_extent export).  cert_svg.do computes its
* scripts directory from c(pwd), so it is loaded from test/ and the
* working directory restored.  It exits 222 when c(python_exec) is empty,
* which the python: block below needs anyway.
local za_here "`c(pwd)'"
quietly cd "${ZA_REPO}/test"
quietly do "cert_svg.do"
quietly cd "`za_here'"

global ZA_SVER = c(stata_version)
global ZA_FLAV = c(flavor)
global ZA_EDIT = c(edition_real)
global ZA_BORN = c(born_date)
global ZA_DATE = c(current_date)

* WP-28 S14 (D12): the fixture's _meta carries the commit this run was
* measured against, captured with shell (never a Stata call from the
* trailing python: block) into a tempfile and read back through a local.
tempfile ZA_GITREV
capture shell cd "${ZA_REPO}" && git rev-parse HEAD > "`ZA_GITREV'"
local ZA_DASH_COMMIT ""
capture confirm file "`ZA_GITREV'"
if !_rc {
    file open zagitrev using "`ZA_GITREV'", read text
    file read zagitrev zagitline
    local ZA_DASH_COMMIT = strtrim(`"`zagitline'"')
    file close zagitrev
}

* ===========================================================================
* Registration.  A probe is (id, group, dataset, body, options).  Body and
* options are kept apart so that name(zqg, replace) can be appended without
* having to guess whether the registered command already carries a comma.
* ===========================================================================
global ZA_N = 0
program define zp
    // WP-28 S14: two optional trailing arguments, `ticks' (the positions
    // the option asks for, ascending -- for the SVG fit through
    // scripts/svg_truth.py when the drawn labels are not plain numbers,
    // as a %tm axis's are not) and `hull' (Section 18's; always empty
    // here).  Both default to "" so every pre-existing zp call, which
    // gives only 5 arguments, is unaffected.
    local id   `"`1'"'
    local grp  `"`2'"'
    local ds   `"`3'"'
    local body `"`4'"'
    local opts `"`5'"'
    local ticks `"`6'"'
    local hull  `"`7'"'
    global ZA_N = ${ZA_N} + 1
    global ZA_ID_${ZA_N}   `"`id'"'
    global ZA_GRP_${ZA_N}  `"`grp'"'
    global ZA_DS_${ZA_N}   `"`ds'"'
    global ZA_BODY_${ZA_N} `"`body'"'
    global ZA_OPTS_${ZA_N} `"`opts'"'
    global ZA_TICKS_${ZA_N} `"`ticks'"'
    global ZA_HULL_${ZA_N}  `"`hull'"'
end

* ---------------------------------------------------------------------------
* A. Axis label forms
* ---------------------------------------------------------------------------
zp "a_default"        "axis_label" "auto" "twoway scatter mpg weight" ""
zp "a_hash10"         "axis_label" "auto" "twoway scatter mpg weight" "xlabel(#10)"
zp "a_hash3"          "axis_label" "auto" "twoway scatter mpg weight" "xlabel(#3)"
zp "a_hash20"         "axis_label" "auto" "twoway scatter mpg weight" "xlabel(#20)"
zp "a_hash1"          "axis_label" "auto" "twoway scatter mpg weight" "xlabel(#1)"
zp "a_hash2"          "axis_label" "auto" "twoway scatter mpg weight" "xlabel(#2)"
zp "a_hash4"          "axis_label" "auto" "twoway scatter mpg weight" "xlabel(#4)"
zp "a_hash5"          "axis_label" "auto" "twoway scatter mpg weight" "xlabel(#5)"
zp "a_hash6"          "axis_label" "auto" "twoway scatter mpg weight" "xlabel(#6)"
zp "a_hash8"          "axis_label" "auto" "twoway scatter mpg weight" "xlabel(#8)"
zp "a_hash15"         "axis_label" "auto" "twoway scatter mpg weight" "xlabel(#15)"
zp "a_hash30"         "axis_label" "auto" "twoway scatter mpg weight" "xlabel(#30)"
zp "a_minmax"         "axis_label" "auto" "twoway scatter mpg weight" "xlabel(minmax)"
zp "a_none"           "axis_label" "auto" "twoway scatter mpg weight" "xlabel(none)"
zp "a_incr"           "axis_label" "auto" "twoway scatter mpg weight" "xlabel(1000(500)5000)"
zp "a_incr_inside"    "axis_label" "auto" "twoway scatter mpg weight" "xlabel(2000(500)4500)"
zp "a_list"           "axis_label" "auto" "twoway scatter mpg weight" "xlabel(2000 3000 4000)"
zp "a_pairs"          "axis_label" "auto" "twoway scatter mpg weight" `"xlabel(2000 "low" 4000 "high")"'
zp "a_ymm"            "axis_label" "auto" "twoway scatter mpg weight" "ylabel(minmax)"
zp "a_yhash10"        "axis_label" "auto" "twoway scatter mpg weight" "ylabel(#10)"
zp "a_ydefault_price" "axis_label" "auto" "twoway scatter price weight" ""
zp "a_yfmt_price_c"   "axis_label" "auto" "twoway scatter price weight" "ylabel(, format(%9.0fc))"
zp "a_yfmt_price_noc" "axis_label" "auto" "twoway scatter price weight" "ylabel(, format(%9.0f))"
zp "a_yfmt_price_2dp" "axis_label" "auto" "twoway scatter price weight" "ylabel(, format(%12.2fc))"
zp "a_yfmt_mpg"       "axis_label" "auto" "twoway scatter mpg weight" "ylabel(, format(%9.2f))"
zp "a_yfmt_mpg_c"     "axis_label" "auto" "twoway scatter price weight" "ylabel(, format(%9.1fc))"
zp "a_xfmt_weight"    "axis_label" "auto" "twoway scatter mpg weight" "xlabel(, format(%9.0f))"
zp "a_labsize_large"  "axis_label" "auto" "twoway scatter mpg weight" "xlabel(, labsize(large))"
zp "a_labsize_small"  "axis_label" "auto" "twoway scatter mpg weight" "xlabel(, labsize(small))"
zp "a_labsize_huge"   "axis_label" "auto" "twoway scatter mpg weight" "xlabel(, labsize(huge))"
zp "a_labcolor"       "axis_label" "auto" "twoway scatter mpg weight" "xlabel(, labcolor(red))"
zp "a_angle45"        "axis_label" "auto" "twoway scatter mpg weight" "xlabel(, angle(45))"
zp "a_angle90"        "axis_label" "auto" "twoway scatter mpg weight" "xlabel(, angle(90))"
zp "a_angle_vert"     "axis_label" "auto" "twoway scatter mpg weight" "xlabel(, angle(vertical))"
zp "a_angle_hor"      "axis_label" "auto" "twoway scatter mpg weight" "ylabel(, angle(horizontal))"
zp "a_grid"           "axis_label" "auto" "twoway scatter mpg weight" "xlabel(, grid)"
zp "a_nogrid"         "axis_label" "auto" "twoway scatter mpg weight" "xlabel(, nogrid)"
zp "a_ygrid"          "axis_label" "auto" "twoway scatter mpg weight" "ylabel(, grid)"
zp "a_ynogrid"        "axis_label" "auto" "twoway scatter mpg weight" "ylabel(, nogrid)"
zp "a_bothnogrid"     "axis_label" "auto" "twoway scatter mpg weight" "xlabel(, nogrid) ylabel(, nogrid)"
zp "a_hash10_grid"    "axis_label" "auto" "twoway scatter mpg weight" "xlabel(#10, grid)"
zp "a_hash10_fmt"     "axis_label" "auto" "twoway scatter mpg weight" "xlabel(#10, format(%9.0f))"
zp "a_ticks_only"     "axis_label" "auto" "twoway scatter mpg weight" "xtick(2500 3500)"
zp "a_mticks"         "axis_label" "auto" "twoway scatter mpg weight" "xmtick(2250 2750 3250)"
zp "a_mlabel"         "axis_label" "auto" "twoway scatter mpg weight" "xmlabel(2500 3500)"
* bigger N / different magnitudes
zp "a_nl_default"     "axis_label" "nlsw88" "twoway scatter wage hours" ""
zp "a_nl_hash10"      "axis_label" "nlsw88" "twoway scatter wage hours" "xlabel(#10)"
zp "a_nl_hash3"       "axis_label" "nlsw88" "twoway scatter wage hours" "xlabel(#3)"
zp "a_nl_hash20"      "axis_label" "nlsw88" "twoway scatter wage hours" "xlabel(#20)"
zp "a_nl_minmax"      "axis_label" "nlsw88" "twoway scatter wage hours" "xlabel(minmax)"
zp "a_nl_ttl_default" "axis_label" "nlsw88" "twoway scatter wage ttl_exp" ""
zp "a_nl_ttl_hash10"  "axis_label" "nlsw88" "twoway scatter wage ttl_exp" "xlabel(#10)"
zp "a_nl_age_default" "axis_label" "nlsw88" "twoway scatter wage age" ""
zp "a_nl_age_hash10"  "axis_label" "nlsw88" "twoway scatter wage age" "xlabel(#10)"
zp "a_nl_age_minmax"  "axis_label" "nlsw88" "twoway scatter wage age" "xlabel(minmax)"

* ---------------------------------------------------------------------------
* A2. WP-28 S14 (GAPS2 B1): the numlist/label forms the old parser misread,
* read straight from twoway's own SVG.  Group b1_label; auto unless noted;
* the "rep78" probes use mpg/rep78 (values 1-5) so the tick range is small.
* ---------------------------------------------------------------------------
zp "a1_pairs3"     "b1_label" "auto" "twoway scatter mpg rep78" `"xlabel(1 "2019" 2 "2020" 3 "2021")"'
zp "a1_twolines"   "b1_label" "auto" "twoway scatter mpg weight" `"xlabel(2000 "low" "end" 4000 "high")"'
zp "a1_compound"   "b1_label" "auto" "twoway scatter mpg weight" `"xlabel(2000 `"c "q" d"' 4000 "high")"'
zp "a1_to"         "b1_label" "auto" "twoway scatter mpg weight" "xlabel(2000 2500 to 4000)"
zp "a1_colon"      "b1_label" "auto" "twoway scatter mpg weight" "xlabel(2000 2500:4000)"
zp "a1_colon_sp"   "b1_label" "auto" "twoway scatter mpg weight" "xlabel(2000 2500 : 4000)"
zp "a1_slash"      "b1_label" "auto" "twoway scatter mpg rep78" "xlabel(1/5)"
zp "a1_slash_down" "b1_label" "auto" "twoway scatter mpg rep78" "xlabel(5/1)"
zp "a1_bracket"    "b1_label" "auto" "twoway scatter mpg rep78" "xlabel(1[1]3)"
zp "a1_step2"      "b1_label" "auto" "twoway scatter mpg rep78" "xlabel(1(2)10)"
zp "a1_negstep"    "b1_label" "auto" "twoway scatter mpg weight" "ylabel(40(-10)10)"
zp "a1_frac"       "b1_label" "auto" "twoway scatter mpg weight" "ylabel(10(2.5)20)"
zp "a1_hash_list"  "b1_label" "auto" "twoway scatter mpg weight" `"xlabel(#5 3000 "three")"'
zp "a1_hash_incr"  "b1_label" "auto" "twoway scatter mpg weight" "xlabel(#3 2000(1000)4000)"
zp "a1_run_label"  "b1_label" "auto" "twoway scatter mpg weight" `"xlabel(2000(1000)4000 "top")"'
zp "a1_commas"     "b1_label" "auto" "twoway scatter mpg weight" "xlabel(2000,3000,4000)"
zp "a1_commas_grid" "b1_label" "auto" "twoway scatter mpg weight" "xlabel(2000,3000,4000, grid)"
zp "a1_spaces_incr" "b1_label" "auto" "twoway scatter mpg weight" "xlabel(2000 (500) 4000)"
zp "a1_single_quote" "b1_label" "auto" "twoway scatter mpg weight" "xlabel(2000 'a' 4000)"
zp "a1_str_first"  "b1_label" "auto" "twoway scatter mpg weight" `"xlabel("a" 2000)"'
zp "a1_bad_step"   "b1_label" "auto" "twoway scatter mpg weight" "xlabel(1(0)5)"
zp "a1_bad_word"   "b1_label" "auto" "twoway scatter mpg weight" "xlabel(2000 abc 4000)"
zp "a1_mixed"      "b1_label" "auto" "twoway scatter mpg rep78" "xlabel(1 2 3/5 8(2)12)"

* ---------------------------------------------------------------------------
* A3. WP-28 S14 (E3 probe for section 12): a %tm axis's default tick text
* and its text under an explicit xlabel(..., format(%tm)), so section 12
* can hold dash's date-axis formatter to twoway's own reading.  Dataset
* sp500_tm (a new branch of the export loop, below).
* ---------------------------------------------------------------------------
zp "e3_tm_axis"     "b1_label" "sp500_tm" "twoway line close m" "" ""
zp "e3_tm_axis_lab" "b1_label" "sp500_tm" "twoway line close m" "xlabel(492(3)501, format(%tm))" "492 495 498 501"

* ---------------------------------------------------------------------------
* A4. WP-28 S14 (GAPS2 G16): xlabel(valuelabel) and its abbreviation, read
* through the value-labelled dataset auto_vl (a new branch, below).
* ---------------------------------------------------------------------------
zp "g16_vl_slash"      "g16_valuelabel" "auto_vl" "twoway scatter mpg rep78" "xlabel(1/5, valuelabel)"
zp "g16_vl_abbrev"     "g16_valuelabel" "auto_vl" "twoway scatter mpg rep78" "xlabel(1/5, val)"
zp "g16_vl_unlabelled" "g16_valuelabel" "auto_vl" "twoway scatter mpg rep78" "xlabel(0/6, valuelabel)"
zp "g16_vl_mixed"      "g16_valuelabel" "auto_vl" "twoway scatter mpg rep78" `"xlabel(1 "one" 2/5, valuelabel)"'
zp "g16_vl_default"    "g16_valuelabel" "auto_vl" "twoway scatter mpg rep78" "xlabel(, valuelabel)"
zp "g16_vl_y"          "g16_valuelabel" "auto_vl" "twoway scatter rep78 mpg" "ylabel(1/5, valuelabel)"
zp "g16_vl_by"         "g16_valuelabel" "auto_vl" "twoway scatter mpg rep78" "by(foreign) xlabel(1/5, valuelabel)"
zp "g16_vl_off"        "g16_valuelabel" "auto_vl" "twoway scatter mpg rep78" "xlabel(1/5)"

* ---------------------------------------------------------------------------
* B. Axis scale
* ---------------------------------------------------------------------------
zp "b_default"        "axis_scale" "auto" "twoway scatter mpg weight" ""
zp "b_range_0_50"     "axis_scale" "auto" "twoway scatter mpg weight" "yscale(range(0 50))"
zp "b_range_0"        "axis_scale" "auto" "twoway scatter mpg weight" "yscale(range(0))"
zp "b_range_60"       "axis_scale" "auto" "twoway scatter mpg weight" "yscale(range(60))"
zp "b_range_narrow"   "axis_scale" "auto" "twoway scatter mpg weight" "yscale(range(20 30))"
zp "b_xrange"         "axis_scale" "auto" "twoway scatter mpg weight" "xscale(range(0 6000))"
zp "b_log"            "axis_scale" "auto" "twoway scatter mpg weight" "yscale(log)"
zp "b_xlog"           "axis_scale" "auto" "twoway scatter mpg weight" "xscale(log)"
zp "b_log_price"      "axis_scale" "auto" "twoway scatter price weight" "yscale(log)"
zp "b_reverse"        "axis_scale" "auto" "twoway scatter mpg weight" "yscale(reverse)"
zp "b_xreverse"       "axis_scale" "auto" "twoway scatter mpg weight" "xscale(reverse)"
zp "b_noextend"       "axis_scale" "auto" "twoway scatter mpg weight" "yscale(noextend)"
zp "b_xnoextend"      "axis_scale" "auto" "twoway scatter mpg weight" "xscale(noextend)"
zp "b_bothnoextend"   "axis_scale" "auto" "twoway scatter mpg weight" "xscale(noextend) yscale(noextend)"
zp "b_alt"            "axis_scale" "auto" "twoway scatter mpg weight" "yscale(alt)"
zp "b_xalt"           "axis_scale" "auto" "twoway scatter mpg weight" "xscale(alt)"
zp "b_bothalt"        "axis_scale" "auto" "twoway scatter mpg weight" "xscale(alt) yscale(alt)"
zp "b_off"            "axis_scale" "auto" "twoway scatter mpg weight" "yscale(off)"
zp "b_range_log"      "axis_scale" "auto" "twoway scatter price weight" "yscale(log range(1000 20000))"
* extension-rule evidence: several variables, several magnitudes
zp "b_ext_price"      "axis_scale" "auto" "twoway scatter price weight" ""
zp "b_ext_turn"       "axis_scale" "auto" "twoway scatter turn length" ""
zp "b_ext_gear"       "axis_scale" "auto" "twoway scatter gear_ratio displacement" ""
zp "b_ext_head"       "axis_scale" "auto" "twoway scatter headroom trunk" ""
zp "b_ext_nl_wage"    "axis_scale" "nlsw88" "twoway scatter wage hours" ""
zp "b_ext_nl_grade"   "axis_scale" "nlsw88" "twoway scatter grade age" ""
zp "b_size_wide"      "axis_scale" "auto" "twoway scatter mpg weight" "xsize(10) ysize(3)"
zp "b_size_tall"      "axis_scale" "auto" "twoway scatter mpg weight" "xsize(3) ysize(8)"
zp "b_size_square"    "axis_scale" "auto" "twoway scatter mpg weight" "xsize(5) ysize(5)"
zp "b_ext_ticklist"   "axis_scale" "auto" "twoway scatter mpg weight" "xlabel(2000 3000 4000)"
zp "b_ext_ticklist_ne" "axis_scale" "auto" "twoway scatter mpg weight" "xlabel(2000 3000 4000) xscale(noextend)"

* ---------------------------------------------------------------------------
* B2. WP-28 S18 (GAPS2 B2): what widens an axis -- label and tick values
* (unless norescale) and every range() value, never narrowing.  Group
* b2_extent.  ticks = the labelled positions, for the SVG fit where the
* labels are not plain numbers; hull = the axis, then the values the
* option asks the axis to include.
* ---------------------------------------------------------------------------
zp "b2_ylab_0_100"     "b2_extent" "auto" "twoway scatter mpg weight" "ylabel(0(20)100)" "0 20 40 60 80 100" "y 0 100"
zp "b2_ylab_0_100_nr"  "b2_extent" "auto" "twoway scatter mpg weight" "ylabel(0(20)100, norescale)" "0 20 40 60 80 100" "y 0 100"
* measured 30sep2026: twoway records a lone a(b)c rule as ".major.range_ticks
* 0 100 20" and drops norescale with it, where a list is ".add_ticks ...,
* norescale" -- these two tell the forms apart.
zp "b2_ylab_list_nr"   "b2_extent" "auto" "twoway scatter mpg weight" "ylabel(0 20 40 60 80 100, norescale)" "0 20 40 60 80 100" "y"
zp "b2_ytick_rule_nr"  "b2_extent" "auto" "twoway scatter mpg weight" "ytick(0(20)100, norescale)" "" "y 0 100"
zp "b2_ylab_pair"      "b2_extent" "auto" "twoway scatter mpg weight" `"ylabel(0 "zero" 60 "sixty")"' "0 60" "y 0 60"
zp "b2_ytick_50"       "b2_extent" "auto" "twoway scatter mpg weight" "ytick(50)" "" "y 50"
zp "b2_ytick_50_nr"    "b2_extent" "auto" "twoway scatter mpg weight" "ytick(50, norescale)" "" "y"
zp "b2_range_100"      "b2_extent" "auto" "twoway scatter mpg weight" "yscale(range(100))" "" "y 100"
zp "b2_range_0"        "b2_extent" "auto" "twoway scatter mpg weight" "yscale(range(0))" "" "y 0"
zp "b2_range_20_30"    "b2_extent" "auto" "twoway scatter mpg weight" "yscale(range(20 30))" "" "y 20 30"
zp "b2_r_0_100"        "b2_extent" "auto" "twoway scatter mpg weight" "yscale(r(0 100))" "" "y 0 100"
zp "b2_range_dot_60"   "b2_extent" "auto" "twoway scatter mpg weight" "yscale(range(. 60))" "" "y 60"
zp "b2_range_60_dot"   "b2_extent" "auto" "twoway scatter mpg weight" "yscale(range(60 .))" "" "y 60"
zp "b2_range_unsorted" "b2_extent" "auto" "twoway scatter mpg weight" "yscale(range(100 0))" "" "y 0 100"
zp "b2_range_three"    "b2_extent" "auto" "twoway scatter mpg weight" "yscale(range(0 50 100))" "" "y 0 50 100"
zp "b2_range_bad"      "b2_extent" "auto" "twoway scatter mpg weight" "yscale(range(abc))" "" "y"
zp "b2_log_range"      "b2_extent" "auto" "twoway scatter price weight" "yscale(log range(1000 20000))" "" "y 1000 20000"
zp "b2_log_r_one"      "b2_extent" "auto" "twoway scatter price weight" "yscale(log r(100000))" "" "y 100000"
zp "b2_rev_range"      "b2_extent" "auto" "twoway scatter mpg weight" "yscale(reverse range(0 50))" "" "y 0 50"
zp "b2_rev_abbrev"     "b2_extent" "auto" "twoway scatter mpg weight" "yscale(rev)" "" "y"
zp "b2_hash5_range100" "b2_extent" "auto" "twoway scatter mpg weight" "ylabel(#5) yscale(range(100))" "" "y 100"
zp "b2_xlab_wide"      "b2_extent" "auto" "twoway scatter mpg weight" "xlabel(0(1000)6000)" "0 1000 2000 3000 4000 5000 6000" "x 0 6000"
zp "b2_xtick_nr"       "b2_extent" "auto" "twoway scatter mpg weight" "xtick(0 6000, norescale)" "" "x"
zp "b2_lfit_range0"    "b2_extent" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "yscale(range(0))" "" "y 0"
zp "b2_bar_xrange0"    "b2_extent" "auto" "twoway bar mpg weight" "xscale(range(0))" "" "x 0"
zp "b2_td_range"       "b2_extent" "sp500" "twoway scatter close date" "xscale(range(14900 15400))" "" "x 14900 15400"
zp "b2_by_range0"      "b2_extent" "auto" "twoway scatter mpg weight" "by(foreign) yscale(range(0))" "" "y 0"

* ---------------------------------------------------------------------------
* C. Legend.  Every case is a PAIR: <id> bare and <id>__off with legend(off)
* (or by(..., legend(off)) where by() is in play).  The anchorless <text>
* elements present bare and absent off ARE the legend.
* ---------------------------------------------------------------------------
zp "c_scatter1"       "legend" "auto" "twoway scatter mpg weight" ""
zp "c_scatter1__off"  "legend" "auto" "twoway scatter mpg weight" "legend(off)"
zp "c_scatter_lfit"   "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" ""
zp "c_scatter_lfit__off" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)"
zp "c_legend_on"      "legend" "auto" "twoway scatter mpg weight" "legend(on)"
zp "c_legend_on__off" "legend" "auto" "twoway scatter mpg weight" "legend(off)"
zp "c_two_if"         "legend" "auto" "twoway (scatter mpg weight if foreign==0) (scatter mpg weight if foreign==1)" ""
zp "c_two_if__off"    "legend" "auto" "twoway (scatter mpg weight if foreign==0) (scatter mpg weight if foreign==1)" "legend(off)"
zp "c_two_y"          "legend" "auto" "twoway scatter mpg price weight" ""
zp "c_two_y__off"     "legend" "auto" "twoway scatter mpg price weight" "legend(off)"
zp "c_three"          "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight) (qfit mpg weight)" ""
zp "c_three__off"     "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight) (qfit mpg weight)" "legend(off)"
zp "c_four"           "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight) (qfit mpg weight) (mband mpg weight)" ""
zp "c_four__off"      "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight) (qfit mpg weight) (mband mpg weight)" "legend(off)"
zp "c_line1"          "legend" "auto" "twoway line mpg weight" "sort"
zp "c_line1__off"     "legend" "auto" "twoway line mpg weight" "sort legend(off)"
zp "c_bar1"           "legend" "auto" "twoway bar mpg weight" ""
zp "c_bar1__off"      "legend" "auto" "twoway bar mpg weight" "legend(off)"
zp "c_area1"          "legend" "auto" "twoway area mpg weight" "sort"
zp "c_area1__off"     "legend" "auto" "twoway area mpg weight" "sort legend(off)"
zp "c_hist1"          "legend" "auto" "twoway histogram mpg" ""
zp "c_hist1__off"     "legend" "auto" "twoway histogram mpg" "legend(off)"
zp "c_kdens1"         "legend" "auto" "twoway kdensity mpg" ""
zp "c_kdens1__off"    "legend" "auto" "twoway kdensity mpg" "legend(off)"
zp "c_lfitci"         "legend" "auto" "twoway lfitci mpg weight" ""
zp "c_lfitci__off"    "legend" "auto" "twoway lfitci mpg weight" "legend(off)"
zp "c_rarea1"         "legend" "auto" "twoway rarea turn mpg weight" "sort"
zp "c_rarea1__off"    "legend" "auto" "twoway rarea turn mpg weight" "sort legend(off)"
zp "c_connected1"     "legend" "auto" "twoway connected mpg weight" "sort"
zp "c_connected1__off" "legend" "auto" "twoway connected mpg weight" "sort legend(off)"
zp "c_spike1"         "legend" "auto" "twoway spike mpg weight" ""
zp "c_spike1__off"    "legend" "auto" "twoway spike mpg weight" "legend(off)"
zp "c_hist_by"        "legend" "auto" "twoway histogram mpg" "by(foreign)"
zp "c_hist_by__off"   "legend" "auto" "twoway histogram mpg" "by(foreign, legend(off))"
zp "c_scatter_by"     "legend" "auto" "twoway scatter mpg weight" "by(foreign)"
zp "c_scatter_by__off" "legend" "auto" "twoway scatter mpg weight" "by(foreign, legend(off))"
zp "c_two_by"         "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "by(foreign)"
zp "c_two_by__off"    "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "by(foreign, legend(off))"
zp "c_two_by_legoff"  "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "by(foreign) legend(off)"
zp "c_two_by_legoff__off" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "by(foreign, legend(off))"
* one plot, one key: does a user-supplied label or order force a legend?
zp "c_one_label"      "legend" "auto" "twoway scatter mpg weight" `"legend(label(1 "mpg"))"'
zp "c_one_label__off" "legend" "auto" "twoway scatter mpg weight" `"legend(label(1 "mpg") off)"'
zp "c_one_order"      "legend" "auto" "twoway scatter mpg weight" "legend(order(1))"
zp "c_one_order__off" "legend" "auto" "twoway scatter mpg weight" "legend(order(1) off)"
zp "c_one_pos"        "legend" "auto" "twoway scatter mpg weight" "legend(position(6))"
zp "c_one_pos__off"   "legend" "auto" "twoway scatter mpg weight" "legend(position(6) off)"
zp "c_one_on_pos"     "legend" "auto" "twoway scatter mpg weight" "legend(on position(6))"
zp "c_one_on_pos__off" "legend" "auto" "twoway scatter mpg weight" "legend(off)"

* legend control options, on the two-plot case (which draws one by default)
zp "c_pos_off"        "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(pos(6) off)"
zp "c_pos_off__off"   "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)"
zp "c_off_pos"        "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off pos(6))"
zp "c_off_pos__off"   "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)"
zp "c_order21"        "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(order(2 1))"
zp "c_order21__off"   "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)"
zp "c_order1"         "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(order(1))"
zp "c_order1__off"    "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)"
zp "c_order_relab"    "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" `"legend(order(2 "FIT" 1 "RAW"))"'
zp "c_order_relab__off" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)"
zp "c_cols2"          "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight) (qfit mpg weight) (mband mpg weight)" "legend(cols(2))"
zp "c_cols2__off"     "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight) (qfit mpg weight) (mband mpg weight)" "legend(off)"
zp "c_cols1"          "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight) (qfit mpg weight) (mband mpg weight)" "legend(cols(1))"
zp "c_cols1__off"     "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight) (qfit mpg weight) (mband mpg weight)" "legend(off)"
zp "c_cols4"          "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight) (qfit mpg weight) (mband mpg weight)" "legend(cols(4))"
zp "c_cols4__off"     "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight) (qfit mpg weight) (mband mpg weight)" "legend(off)"
zp "c_rows1"          "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight) (qfit mpg weight) (mband mpg weight)" "legend(rows(1))"
zp "c_rows1__off"     "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight) (qfit mpg weight) (mband mpg weight)" "legend(off)"
zp "c_rows2"          "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight) (qfit mpg weight) (mband mpg weight)" "legend(rows(2))"
zp "c_rows2__off"     "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight) (qfit mpg weight) (mband mpg weight)" "legend(off)"
zp "c_ring0"          "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(ring(0))"
zp "c_ring0__off"     "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)"
zp "c_ring0_pos1"     "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(ring(0) position(1))"
zp "c_ring0_pos1__off" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)"
zp "c_ring0_pos11"    "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(ring(0) position(11))"
zp "c_ring0_pos11__off" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)"
zp "c_ring0_pos5"     "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(ring(0) position(5))"
zp "c_ring0_pos5__off" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)"
zp "c_ring1_pos3"     "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(ring(1) position(3))"
zp "c_ring1_pos3__off" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)"
zp "c_size_large"     "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(size(large))"
zp "c_size_large__off" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)"
zp "c_size_small"     "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(size(small))"
zp "c_size_small__off" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)"
zp "c_region"         "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(region(lcolor(red)))"
zp "c_region__off"    "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)"
zp "c_legtitle"       "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" `"legend(title("LEGTITLE"))"'
zp "c_legtitle__off"  "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)"

forvalues p = 1/12 {
    zp "c_pos`p'"      "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(position(`p'))"
    zp "c_pos`p'__off" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)"
}

* ---------------------------------------------------------------------------
* D. Titles, subtitles, notes, captions
* ---------------------------------------------------------------------------
zp "d_none"           "titles" "auto" "twoway scatter mpg weight" ""
zp "d_title_plain"    "titles" "auto" "twoway scatter mpg weight" `"title("T")"'
zp "d_title_styled"   "titles" "auto" "twoway scatter mpg weight" `"title("T", size(large) color(red))"'
zp "d_title_sizeonly" "titles" "auto" "twoway scatter mpg weight" `"title("T", size(large))"'
zp "d_title_coloronly" "titles" "auto" "twoway scatter mpg weight" `"title("T", color(red))"'
zp "d_title_amp"      "titles" "auto" "twoway scatter mpg weight" `"title("R&D spend")"'
zp "d_title_apos"     "titles" "auto" "twoway scatter mpg weight" `"title("Owner cost")"'
zp "d_title_lt"       "titles" "auto" "twoway scatter mpg weight" `"title("a < b & c > d")"'
zp "d_note_plain"     "titles" "auto" "twoway scatter mpg weight" `"note("n=74")"'
zp "d_note_span"      "titles" "auto" "twoway scatter mpg weight" `"note("n=74", span)"'
zp "d_note_styled"    "titles" "auto" "twoway scatter mpg weight" `"note("n=74", size(large) color(blue))"'
zp "d_caption_plain"  "titles" "auto" "twoway scatter mpg weight" `"caption("C")"'
zp "d_caption_span"   "titles" "auto" "twoway scatter mpg weight" `"caption("C", span)"'
zp "d_note_caption"   "titles" "auto" "twoway scatter mpg weight" `"note("NOTEXT") caption("CAPTEXT")"'
zp "d_all_four"       "titles" "auto" "twoway scatter mpg weight" `"title("TITLETEXT") subtitle("SUBTEXT") note("NOTEXT") caption("CAPTEXT")"'
zp "d_all_six"        "titles" "auto" "twoway scatter mpg weight" `"title("TITLETEXT") subtitle("SUBTEXT") note("NOTEXT") caption("CAPTEXT") xtitle("XTEXT") ytitle("YTEXT")"'
zp "d_subtitle_plain" "titles" "auto" "twoway scatter mpg weight" `"subtitle("S")"'
zp "d_subtitle_styled" "titles" "auto" "twoway scatter mpg weight" `"subtitle("S", size(large) color(green))"'
zp "d_title_pos11"    "titles" "auto" "twoway scatter mpg weight" `"title("T", position(11))"'
zp "d_title_pos5"     "titles" "auto" "twoway scatter mpg weight" `"title("T", position(5))"'
zp "d_bt_family"      "titles" "auto" "twoway scatter mpg weight" `"t1title("T1TEXT") t2title("T2TEXT") b1title("B1TEXT") b2title("B2TEXT") l1title("L1TEXT") l2title("L2TEXT") r1title("R1TEXT") r2title("R2TEXT")"'
zp "d_title_multiline" "titles" "auto" "twoway scatter mpg weight" `"title("LINE1" "LINE2")"'
zp "d_xtitle_styled"  "titles" "auto" "twoway scatter mpg weight" `"xtitle("XT", size(large) color(red))"'

* ---------------------------------------------------------------------------
* E. Reference lines
* ---------------------------------------------------------------------------
zp "e_baseline"       "refline" "auto" "twoway scatter mpg weight" ""
zp "e_xline_default"  "refline" "auto" "twoway scatter mpg weight" "xline(3000)"
zp "e_xline_offtick"  "refline" "auto" "twoway scatter mpg weight" "xline(2750)"
zp "e_xline_styled"   "refline" "auto" "twoway scatter mpg weight" "xline(3000, lcolor(red) lpattern(solid) lwidth(thick))"
zp "e_xline_color"    "refline" "auto" "twoway scatter mpg weight" "xline(3000, lcolor(red))"
zp "e_xline_pattern"  "refline" "auto" "twoway scatter mpg weight" "xline(3000, lpattern(solid))"
zp "e_xline_dash"     "refline" "auto" "twoway scatter mpg weight" "xline(3000, lpattern(dash))"
zp "e_xline_width"    "refline" "auto" "twoway scatter mpg weight" "xline(3000, lwidth(thick))"
zp "e_xline_vthin"    "refline" "auto" "twoway scatter mpg weight" "xline(3000, lwidth(vthin))"
zp "e_xline_multi"    "refline" "auto" "twoway scatter mpg weight" "xline(2500 3500)"
zp "e_xline_outside"  "refline" "auto" "twoway scatter mpg weight" "xline(6000)"
zp "e_yline_default"  "refline" "auto" "twoway scatter mpg weight" "yline(20)"
zp "e_yline_offtick"  "refline" "auto" "twoway scatter mpg weight" "yline(25)"
zp "e_yline_styled"   "refline" "auto" "twoway scatter mpg weight" "yline(20, lcolor(blue) lpattern(dash) lwidth(vthick))"
zp "e_both_lines"     "refline" "auto" "twoway scatter mpg weight" "xline(3000) yline(20)"

* ===========================================================================
* Probe loop
* ===========================================================================
tempname rec
file open `rec' using "${ZA_REC}", write text replace
file write `rec' "META|stata_version|${ZA_SVER}" _n
file write `rec' "META|stata_flavor|${ZA_FLAV}" _n
file write `rec' "META|stata_edition|${ZA_EDIT}" _n
file write `rec' "META|stata_born_date|${ZA_BORN}" _n
file write `rec' "META|run_date|${ZA_DATE}" _n
file write `rec' "META|workdir|${ZA_WORK}" _n
file write `rec' "META|scheme|`c(scheme)'" _n
* WP-28 S14 (D12): the fixture provenance stamp, beside every existing key.
file write `rec' "META|born_date|${ZA_BORN}" _n
file write `rec' "META|extracted|${ZA_DATE}" _n
file write `rec' `"META|dash_commit|`macval(ZA_DASH_COMMIT)'"' _n
display as text "scheme in force: `c(scheme)'"

* ---- data facts (min / max / N / display format) used to derive the default
*      range-extension rule.  Never taken from memory. -----------------------
foreach ds in auto nlsw88 sp500 {
    sysuse `ds', clear
    local vlist ""
    if "`ds'" == "auto"   local vlist mpg weight price turn length gear_ratio headroom trunk displacement
    if "`ds'" == "nlsw88" local vlist wage hours ttl_exp age grade
    if "`ds'" == "sp500"  local vlist close date
    foreach v of local vlist {
        quietly summarize `v'
        local fmt : format `v'
        local vlab : variable label `v'
        file write `rec' `"DATA|`ds'|`v'|`r(min)'|`r(max)'|`r(N)'|`fmt'|`vlab'"' _n
    }
}

local N = $ZA_N
local curds ""
forvalues i = 1/`N' {
    local id   "${ZA_ID_`i'}"
    local grp  "${ZA_GRP_`i'}"
    local ds   "${ZA_DS_`i'}"
    local body `"${ZA_BODY_`i'}"'
    local opts `"${ZA_OPTS_`i'}"'
    local ticks `"${ZA_TICKS_`i'}"'
    local hull  `"${ZA_HULL_`i'}"'

    if "`ds'" != "`curds'" {
        // WP-28 S14: two datasets beyond plain sysuse -- auto_vl carries a
        // value label on rep78 (G16's probes), sp500_tm a %tm variable
        // (E3's probe for section 12).
        if "`ds'" == "auto_vl" {
            sysuse auto, clear
            label define alrep 1 "Poor" 2 "Fair" 3 "Average" 4 "Good" 5 "Excellent"
            label values rep78 alrep
        }
        else if "`ds'" == "sp500_tm" {
            sysuse sp500, clear
            generate m = mofd(date)
            format m %tm
        }
        else {
            sysuse `ds', clear
        }
        local curds "`ds'"
    }

    if `"`opts'"' == "" local full `"`body', name(zqg, replace)"'
    else                local full `"`body', `opts' name(zqg, replace)"'
    if `"`opts'"' == "" local shown `"`body'"'
    else                local shown `"`body', `opts'"'

    local svg "${ZA_WORK}/`id'.svg"
    local gph "${ZA_WORK}/`id'.gph"
    capture erase "`svg'"
    capture erase "`gph'"

    capture graph drop zqg
    capture noisily `full'
    local rc = _rc
    local rcx = .
    local rcg = .
    if `rc' == 0 & "`grp'" == "b2_extent" {
        // WP-28 S18: the .Graph scale members beside the export -- the
        // four candidates (permanent min/max, temporary curmin/curmax)
        // and twoway's major-tick triple -- read at once (the program
        // clobbers r()); one GSCALE record per axis.  The SVG stays the
        // truth; these are recorded to settle which member matches it.
        foreach gax in y x {
            capture cert_graph_scale, axis(`gax') name(zqg)
            if _rc == 0 {
                local g1 : display %21.0g r(min)
                local g2 : display %21.0g r(max)
                local g3 : display %21.0g r(curmin)
                local g4 : display %21.0g r(curmax)
                local g5 : display %21.0g r(major_min)
                local g6 : display %21.0g r(major_max)
                local g7 : display %21.0g r(major_delta)
                file write `rec' "GSCALE|`id'|`gax'|`g1'|`g2'|`g3'|`g4'|`g5'|`g6'|`g7'" _n
            }
        }
        if strpos(`"`opts'"', "by(") {
            forvalues gk = 1/2 {
                local gq1 "`.zqg.graphs[`gk'].plotregion1.yscale.min'"
                local gq2 "`.zqg.graphs[`gk'].plotregion1.yscale.max'"
                local gq3 "`.zqg.graphs[`gk'].plotregion1.yscale.curmin'"
                local gq4 "`.zqg.graphs[`gk'].plotregion1.yscale.curmax'"
                file write `rec' "GSCALE|`id'|y@graphs`gk'|`gq1'|`gq2'|`gq3'|`gq4'|||" _n
            }
        }
    }
    if `rc' == 0 {
        capture graph export "`svg'", name(zqg) replace
        local rcx = _rc
        capture graph save zqg "`gph'", replace
        local rcg = _rc
    }
    capture graph drop zqg
    file write `rec' `"PROBE|`id'|`grp'|`ds'|`rc'|`rcx'|`rcg'|`svg'|`gph'|`ticks'|`hull'|`shown'"' _n
    display as text "probe `id' rc=`rc' svg_rc=`rcx'"
}

* ---- oracle self-check: the same command exported twice, more than a second
*      apart, must give an identical text inventory -------------------------
sysuse auto, clear
capture graph drop _all
twoway scatter mpg weight, name(zqa, replace)
graph export "${ZA_WORK}/selfchk_a.svg", name(zqa) replace
sleep 1100
twoway scatter mpg weight, name(zqb, replace)
graph export "${ZA_WORK}/selfchk_b.svg", name(zqb) replace
capture graph drop _all
file write `rec' "SELFCHK|${ZA_WORK}/selfchk_a.svg|${ZA_WORK}/selfchk_b.svg" _n

file close `rec'
display as text "records written to ${ZA_REC}"

* ===========================================================================
* Analysis + JSON emission.  No callbacks into Stata from here on.
*
* REMINDER: no backtick may appear literally in this block -- Stata expands a
* backtick/apostrophe pair as a local macro reference even inside python:.
* Regexes that need one spell it \x60.
* ===========================================================================
python:
import json, os, re, math, html, collections, sys
from sfi import Macro

REC = Macro.getGlobal("ZA_REC")
OUT = Macro.getGlobal("ZA_OUT")
REPO = Macro.getGlobal("ZA_REPO")

# WP-28 S18 (D10): every SVG, for every group, is read through the shared
# reader scripts/svg_truth.py (S02).  The private parse_svg/axis_facts
# this block carried until then are gone; the two adapters below only
# RESHAPE svg_truth's reading into the record this fixture has always
# held, so every pre-existing probe's record is unchanged:
#   * svg_truth lower-cases colours and turns U+00A0 into a space; the
#     fixture has always recorded each colour as Stata's writer spells it
#     (svg_document(as_written=True) keeps that spelling) and each text
#     as html.unescape of its raw content;
#   * svg_truth names a text's size "size"; the fixture, "font_size".
sys.path.insert(0, os.path.join(REPO, "scripts"))
from svg_truth import (svg_texts, svg_axis_extent, svg_document,
                       svg_axis_reading, label_value)

def fnum(s, default=None):
    try:
        return float(s)
    except Exception:
        return default

def legacy_text(t):
    return {"x": t["x"], "y": t["y"], "anchor": t["anchor"],
            "rotate": t["rotate"], "font_size": t["size"],
            "fill": t["fill_raw"], "font_family": t["font_family"],
            "text": html.unescape(t["raw"])}

def legacy_line(d):
    return {"x1": d["x1"], "y1": d["y1"], "x2": d["x2"], "y2": d["y2"],
            "stroke": d["stroke_raw"], "width": d["width"],
            "dasharray": d["dasharray"]}

def read_svg(path):
    """svg_document's reading of *path* (colours as written), in the
    record's shape; None when no SVG was written.  "_doc" keeps the shared
    reader's own reading and "_as_written" maps each lower-cased colour
    back to the writer's spelling."""
    if not path or not os.path.exists(path):
        return None
    doc = svg_document(path, as_written=True)
    as_written = {}
    for d in doc["hlines"] + doc["vlines"] + doc["diaglines"]:
        as_written.setdefault(d["stroke"], d["stroke_raw"])
    rect_fill = {}
    for r in doc["rects"]:
        if None in (r["x"], r["y"], r["w"], r["h"]):
            continue
        rect_fill.setdefault((r["x"], r["y"], r["x"] + r["w"],
                              r["y"] + r["h"], r["fill"]), r["fill_raw"])

    def region(r):
        out = dict(r)
        out["fill"] = rect_fill.get((r["left"], r["top"], r["right"],
                                     r["bottom"], r["fill"]), r["fill"])
        return out
    regions = [region(r) for r in doc["regions"]]
    pr = None
    if doc["plotregion"] is not None:
        pr = dict(doc["plotregion"])
        if "axis-line" in (pr.get("source") or ""):
            pr.pop("fill", None)
        else:
            pr["fill"] = region(pr)["fill"]
    return {"texts": [legacy_text(t) for t in doc["texts"]],
            "hlines": [legacy_line(d) for d in doc["hlines"]],
            "vlines": [legacy_line(d) for d in doc["vlines"]],
            "diaglines": [legacy_line(d) for d in doc["diaglines"]],
            "canvas": doc["canvas"], "regions": regions,
            "plotregion": pr, "axis_line": doc["axis_line"], "_doc": doc,
            "_as_written": as_written}

def line_groups(lines, coord):
    """Collapse the segments of one drawn line into a single group (the
    record's own summary of svg_truth's lines: first segment and gap)."""
    g = collections.defaultdict(list)
    for d in lines:
        g[(round(d[coord], 2), d["stroke"], d["width"])].append(d)
    out = []
    for k, segs in sorted(g.items()):
        span = "x" if coord in ("y1", "y2") else "y"
        a = "x1" if span == "x" else "y1"
        b = "x2" if span == "x" else "y2"
        segs = sorted(segs, key=lambda d: min(d[a], d[b]))
        lo = min(min(d[a], d[b]) for d in segs)
        hi = max(max(d[a], d[b]) for d in segs)
        first_len = abs(segs[0][b] - segs[0][a])
        first_gap = None
        if len(segs) > 1:
            first_gap = min(segs[1][a], segs[1][b]) - max(segs[0][a], segs[0][b])
        out.append({"px": k[0], "stroke": k[1], "stroke_width": k[2],
                    "n_segments": len(segs), "dashed": len(segs) > 1,
                    "span_from": lo, "span_to": hi,
                    "first_segment_len": round(first_len, 2),
                    "first_gap": (round(first_gap, 2)
                                  if first_gap is not None else None)})
    return out

MAPPING_NOTE = (
    "fewer than two tick labels parse as numbers, so the pixel<->data "
    "map could not be inverted; the tick pixel positions above are "
    "still exact")

def legacy_mapping(fit):
    """svg_truth's fit, under the record's names."""
    lo, hi = fit["low"], fit["high"]
    start, end = (hi, lo) if fit["reversed"] else (lo, hi)
    return {"space": fit["space"],
            "value_units_per_px": fit["units_per_px"],
            "max_abs_residual_over_ticks": fit["residual"],
            "value_at_plotregion_start": start,
            "value_at_plotregion_end": end,
            "axis_low": lo, "axis_high": hi,
            "reversed": bool(fit["reversed"])}

def axis_record(sv, which):
    """Tick marks, tick labels, gridlines, side and the data<->pixel map of
    one axis, from svg_axis_reading."""
    if sv is None or sv["plotregion"] is None:
        return {"error": "no plotregion could be identified in the SVG"}
    r = svg_axis_reading(None, which, doc=sv["_doc"])
    out = {"tick_side": r["tick_side"], "tick_px": r["tick_px"],
           "n_ticks": r["n_ticks"],
           "gridline_px": [g["px"] for g in r["grid"]],
           "n_gridlines": len(r["grid"]),
           "gridline_style": sorted({(sv["_as_written"].get(g["stroke"], g["stroke"]), g["width"],
                                      g["n_segments"] > 1)
                                     for g in r["grid"]})}
    objs = r["label_objs"]
    if r["label_offaxis_px"] is not None:
        out["label_offaxis_px"] = r["label_offaxis_px"]
    labels = [html.unescape(o["raw"]) if o is not None else None
              for o in objs]
    lab_objs = [legacy_text(o) for o in objs if o is not None]
    pr = sv["plotregion"]
    out["tick_labels"] = labels
    out["tick_values"] = [label_value(l) if l is not None else None
                          for l in labels]
    out["label_style"] = None
    if lab_objs:
        out["label_style"] = {
            "font_size_px": sorted({t["font_size"] for t in lab_objs}),
            "fill": sorted({t["fill"] for t in lab_objs if t["fill"]}),
            "rotate": sorted({t["rotate"] for t in lab_objs},
                             key=lambda z: (z is None, z)),
            "anchor": sorted({t["anchor"] for t in lab_objs},
                             key=lambda z: (z is None, str(z))),
        }
        if which == "x":
            out["label_side"] = ("below plotregion"
                                 if lab_objs[0]["y"] > pr["bottom"]
                                 else "above plotregion")
        else:
            out["label_side"] = ("left of plotregion"
                                 if lab_objs[0]["x"] < pr["left"]
                                 else "right of plotregion")
    out["mapping"] = (legacy_mapping(r["fit"]) if r["fit"] is not None
                      else None)
    if out["mapping"] is None:
        out["mapping_note"] = MAPPING_NOTE
    return out

# --------------------------------------------------------------------------
# .gph parsing -- the declarative record
# --------------------------------------------------------------------------
_K = re.compile(r"K[0-9a-fA-F]{6,}")
_BANG = re.compile(r"(?m)^\*!.*$")
_CMD = re.compile(r"(?m)^\.(command|date|time) = .*$")
KEEP = re.compile(r"(axis|legend|title|note|caption|gridline|xyline|scale|"
                  r"tick|major|minor|grid|create_axes)")

# \x60 is the backtick: writing one literally here would be eaten by Stata's
# macro expander before python ever sees it.
RE_BOX = re.compile(
    r"\.insert \((\w+) = \.sized_textbox\.new, mtextq\(\x60\"(.*?)\"'\) "
    r"style\(scheme (\w+)\)(.*?)\) (above|below|leftof|rightof) (\w+) , "
    r"ring\((\d+)\)")
RE_LEG = re.compile(
    r"\.insert \(legend = \.legend_g\.new, graphs\(\x60\.objkey'\) "
    r"style\(scheme\)\) (\w+) (\w+) , ring\((\d+)\)")

def parse_gph(path):
    if not path or not os.path.exists(path):
        return None
    txt = open(path, "r", errors="replace").read()
    txt = _BANG.sub("", txt)
    txt = _CMD.sub("", txt)
    txt = _K.sub("K#", txt)
    keep = []
    for ln in txt.splitlines():
        s = ln.strip()
        if not s or s.startswith("<"):
            continue
        if KEEP.search(s):
            keep.append(s)
    placement = {}
    for m in RE_BOX.finditer(txt):
        name, text, style, extra, side, target, ring = m.groups()
        placement.setdefault(name, []).append({
            "text_mtextq": text, "scheme_style": style,
            "side": side, "relative_to": target, "ring": int(ring),
            "extra": extra.strip() or None})
    legend_ins = None
    ml = RE_LEG.search(txt)
    if ml:
        legend_ins = {"side": ml.group(1), "relative_to": ml.group(2),
                      "ring": int(ml.group(3))}
    else:
        m2 = re.search(r"\.insert \(legend = \.legend_g\.new.*?ring\((\d+)\)",
                       txt)
        if m2:
            legend_ins = {"ring": int(m2.group(1)),
                          "note": "side/target not parsed"}
    return {"directives": keep,
            "textbox_placement": placement,
            "legend_insert": legend_ins,
            "editstyle_lines": re.findall(r"(?m)^(\.[\w.]+\.style\.editstyle .*)$",
                                          txt),
            "xyline_lines": re.findall(r"(?m)^(.*declare_xyline.*)$", txt),
            "gridlinestyle_lines": re.findall(r"(?m)^(.*gridlinestyle.*)$", txt),
            "axis_directives": re.findall(r"(?m)^(\.(?:x|y)axis\d+\..*)$", txt)}

# --------------------------------------------------------------------------
# Read the record file
# --------------------------------------------------------------------------
meta_rows, probes, data_facts, selfchk = {}, {}, {}, None
gscale = {}
with open(REC, "r", errors="replace") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line:
            continue
        f = line.split("|")
        t = f[0]
        if t == "META":
            meta_rows[f[1]] = "|".join(f[2:])
        elif t == "SELFCHK":
            selfchk = (f[1], f[2])
        elif t == "DATA":
            data_facts.setdefault(f[1], {})[f[2]] = {
                "min": fnum(f[3]), "max": fnum(f[4]), "N": fnum(f[5]),
                "display_format": f[6], "variable_label": "|".join(f[7:]),
                "source": "quietly summarize, plus the variable display format"}
        elif t == "PROBE":
            # WP-28 S14: two fields inserted before the command text --
            # ticks (the positions the option asks for, ascending; "" when
            # none) and hull (Section 18's; always "" here).
            probes[f[1]] = {"group": f[2], "dataset": f[3], "rc": int(f[4]),
                            "export_rc": f[5], "save_rc": f[6],
                            "svg": f[7], "gph": f[8],
                            "ticks": f[9], "hull": f[10],
                            "command": "|".join(f[11:])}
        elif t == "GSCALE":
            # WP-28 S18: the .Graph scale members of one axis of a
            # b2_extent probe ("." or "" when the member was empty).
            gscale.setdefault(f[1], {})[f[2]] = {
                k: fnum(v) for k, v in zip(
                    ("min", "max", "curmin", "curmax", "major_min",
                     "major_max", "major_delta"), f[3:10])}

# --------------------------------------------------------------------------
# Per-probe record
# --------------------------------------------------------------------------
parsed = {}
for pid, p in sorted(probes.items()):
    e = {"command": p["command"], "group": p["group"],
         "dataset": "sysuse " + p["dataset"] + ", clear", "rc": p["rc"]}
    if p["rc"] != 0:
        e["status"] = ("twoway rejected this command (_rc=%d); nothing measured"
                       % p["rc"])
        parsed[pid] = e
        continue
    sv = read_svg(p["svg"])
    if sv is None:
        e["status"] = "the graph drew but no SVG was written; nothing measured"
        parsed[pid] = e
        continue
    e["status"] = "measured"
    e["plotregion_px"] = sv["plotregion"]
    e["regions_px"] = sv["regions"]
    e["axis_line_px"] = sv["axis_line"]
    e["canvas_px"] = sv["canvas"]
    e["x_axis"] = axis_record(sv, "x")
    e["y_axis"] = axis_record(sv, "y")
    e["all_text_elements"] = sv["texts"]
    e["anchorless_texts"] = [t for t in sv["texts"]
                             if t["anchor"] is None and t["rotate"] is None]
    e["svg_line_groups"] = {"vertical": line_groups(sv["vlines"], "x1"),
                            "horizontal": line_groups(sv["hlines"], "y1")}
    e["gph"] = parse_gph(p["gph"])
    if p["group"] in ("b1_label", "g16_valuelabel"):
        # WP-28 S14 (B1, G16; the E3 probe for section 12): every <text>
        # element's normalised text, in document order, through the
        # shared reader -- axis_record() above answers only
        # the label-parsing fit and cannot see a non-numeric label
        # ("2019", "Poor", "2001m1"); the tests read texts directly.
        e["texts"] = [t["text"] for t in svg_texts(p["svg"])]
        ticks_raw = (p.get("ticks") or "").split()
        if ticks_raw:
            tick_values = [fnum(v) for v in ticks_raw]
            for axis_key, axis_name in (("x_axis", "x"), ("y_axis", "y")):
                try:
                    mapping = svg_axis_extent(p["svg"], axis_name,
                                              tick_values=tick_values)
                except ValueError as exc:
                    e[axis_key]["mapping"] = None
                    e[axis_key]["mapping_note"] = (
                        "svg_axis_extent(tick_values=%r) raised %s"
                        % (tick_values, exc))
                    continue
                if mapping is not None:
                    e[axis_key]["mapping"] = mapping
    parsed[pid] = e

# --------------------------------------------------------------------------
# B2. WP-28 S18: what widens an axis (group b2_extent)
#
# The drawn extent is the SVG's (DISCOVERY Q14 amendment): the tick fit
# inverted at the plotregion edges, over the given tick positions when the
# labels are not plain numbers, else over the numeric labels, else over
# twoway's own major ticks (.Graph's major min/max/delta) when their count
# matches the tick marks.  Stata's margin is 71.2 SVG units a side
# (findings.axis_range_extension), so the INNER hull is the extent less
# that margin; stata_inner is the data joined with every drawn tick (the
# extension finding's own method).  .Graph's four scale candidates are
# recorded beside the extent to settle, once, which of them it equals.
# --------------------------------------------------------------------------
MARGIN_PX = 71.2
B2_TWIN = {("auto", "mpg", "y"): "b_default",
           ("auto", "weight", "x"): "b_default",
           ("auto", "price", "y"): "b_log_price"}

def b2_vars(cmd):
    m = re.search(r"(?:scatter|bar)\s+(\w+)\s+(\w+)", cmd.split(",")[0])
    return (m.group(1), m.group(2)) if m else (None, None)

def to_space(v, space):
    return math.log10(v) if space == "log10" else v

def from_space(v, space):
    return 10 ** v if space == "log10" else v

def near(a, b, span):
    return (a is not None and b is not None
            and abs(a - b) <= 1e-3 * abs(span))

def b2_extent(p, e, axis, ticks):
    """(extent dict, drawn tick values) or (None, reason)."""
    ak = axis + "_axis"
    if e.get("status") != "measured" or ak not in e:
        return None, e.get("status") or "not measured"
    tried = []
    if ticks:
        tv = sorted(ticks, reverse=(axis == "y"))
        try:
            r = svg_axis_reading(p["svg"], axis, tick_values=tv)
        except ValueError as exc:
            r = None
            tried.append("tick positions: %s" % exc)
        if r is not None and r["fit"] is not None:
            e[ak]["mapping"] = legacy_mapping(r["fit"])
            e[ak].pop("mapping_note", None)
            return dict(e[ak]["mapping"], extent_from="tick positions"), tv
        if r is not None:
            tried.append("tick positions: %s" % r["reason"])
    m = e[ak].get("mapping")
    if m:
        vals = [v for v in e[ak].get("tick_values") or [] if v is not None]
        return dict(m, extent_from="numeric tick labels"), vals
    tried.append("numeric tick labels: " + e[ak].get("mapping_note", "none"))
    gs = gscale.get(p["id"], {}).get(axis) or {}
    lo, hi, st = gs.get("major_min"), gs.get("major_max"), gs.get("major_delta")
    if None not in (lo, hi, st) and st > 0:
        n = int(round((hi - lo) / st)) + 1
        tv = [lo + i * st for i in range(n)]
        if len(tv) == e[ak].get("n_ticks"):
            tv = sorted(tv, reverse=(axis == "y"))
            try:
                r = svg_axis_reading(p["svg"], axis, tick_values=tv)
            except ValueError as exc:
                r = None
                tried.append("graph major ticks: %s" % exc)
            if r is not None and r["fit"] is not None:
                return (dict(legacy_mapping(r["fit"]),
                             extent_from="graph major ticks"), tv)
        else:
            tried.append("graph major ticks: %d values for %s tick marks"
                         % (len(tv), e[ak].get("n_ticks")))
    return None, "; ".join(tried)

range_per_probe, gs_per_probe, b2_unverified = {}, {}, {}
gs_inner_per_probe = {}
for pid in sorted(probes):
    p = dict(probes[pid], id=pid)
    if p["group"] != "b2_extent":
        continue
    e = parsed[pid]
    e["graph_scale"] = gscale.get(pid, {})
    if p["rc"] != 0:
        range_per_probe[pid] = {"rc": p["rc"], "twoway_rejected": True}
        continue
    hull_tok = (p.get("hull") or "").split()
    axis = hull_tok[0] if hull_tok else "y"
    hull_vals = [fnum(v) for v in hull_tok[1:]]
    ticks = [fnum(v) for v in (p.get("ticks") or "").split()]
    yv, xv = b2_vars(p["command"])
    var = yv if axis == "y" else xv
    df = (data_facts.get(p["dataset"]) or {}).get(var) or {}
    dmin, dmax = df.get("min"), df.get("max")
    requested = [min([dmin] + hull_vals), max([dmax] + hull_vals)]
    e["hull_values"] = {axis: hull_vals}
    e["requested"] = {axis: requested}
    is_by = "by(" in p["command"]
    ext, drawn = b2_extent(p, e, axis, ticks)
    if ext is None or is_by:
        why = (drawn if ext is None else
               "a by() graph: the SVG holds one plotregion per panel and the "
               "reader fits the first it finds; the .Graph panel members "
               "(graph_scale y@graphs1, y@graphs2) are the record")
        range_per_probe[pid] = {"axis": axis, "unverified": why}
        gs_per_probe[pid] = "unverified"
        gs_inner_per_probe[pid] = "unverified"
        b2_unverified[pid + " (b2 " + axis + " extent)"] = why
        continue
    space = ext.get("space")
    lo, hi = ext["axis_low"], ext["axis_high"]
    L, H = to_space(lo, space), to_space(hi, space)
    s = H - L
    pr = e.get("plotregion_px") or {}
    px = ((pr["bottom"] - pr["top"]) if axis == "y"
          else (pr["right"] - pr["left"]))
    f = MARGIN_PX / px
    inner_m = [from_space(L + f * s, space), from_space(H - f * s, space)]
    # norescale is honoured only where twoway kept it (a list: no hull
    # values registered); there the option's own positions sit outside.
    norescale = "norescale" in p["command"] and not hull_vals
    drawn = [v for v in drawn if v is not None]
    inner_vals = [dmin, dmax] + hull_vals + [
        v for v in drawn if not (norescale and v in ticks)]
    si = [min(inner_vals), max(inner_vals)]
    rq = [to_space(v, space) for v in requested]
    rspan = (rq[1] - rq[0]) or 1.0
    si_is_req = bool(near(to_space(si[0], space), rq[0], rspan)
                     and near(to_space(si[1], space), rq[1], rspan))
    tol = 1e-6 * abs(s)
    contains = bool(L <= rq[0] + tol and H >= rq[1] - tol)
    narrower = bool(L > to_space(dmin, space) + tol
                    or H < to_space(dmax, space) - tol)
    twin = B2_TWIN.get((p["dataset"], var, axis))
    widened = None
    if twin and twin != pid:
        tm = ((parsed.get(twin) or {}).get(axis + "_axis") or {}).get("mapping")
        if tm:
            TL, TH = (to_space(tm["axis_low"], space),
                      to_space(tm["axis_high"], space))
            widened = bool(L < TL - 1e-3 * s or H > TH + 1e-3 * s)
    e["drawn_extent"] = {axis: ext}
    e["drawn_ticks"] = {axis: drawn}
    e["stata_inner"] = {axis: si}
    e["inner_from_margin"] = {axis: inner_m}
    e["stata_inner_is_requested"] = {axis: si_is_req}
    range_per_probe[pid] = {
        "axis": axis, "extent_from": ext["extent_from"],
        "contains_requested": contains, "narrower_than_data": narrower,
        "widened_vs_default": widened, "default_twin": twin,
        "stata_inner_is_requested": si_is_req}
    g = (e["graph_scale"] or {}).get(axis) or {}
    def _m(a, b):
        return all(v is not None for v in (a, b)) and (
            (near(a, lo, hi - lo) and near(b, hi, hi - lo))
            or (space == "log10" and near(a, L, s) and near(b, H, s)))
    mm, cm = _m(g.get("min"), g.get("max")), _m(g.get("curmin"),
                                                 g.get("curmax"))
    gs_per_probe[pid] = ("both" if mm and cm else "min/max" if mm
                         else "curmin/curmax" if cm else "none")
    # ... and against the extent less the measured margin (the inner hull)
    IL, IH = to_space(inner_m[0], space), to_space(inner_m[1], space)
    def _mi(a, b):
        if a is None or b is None:
            return False
        a, b = to_space(a, space), to_space(b, space)
        return abs(a - IL) <= 5e-3 * s and abs(b - IH) <= 5e-3 * s
    mmi = _mi(g.get("min"), g.get("max"))
    cmi = _mi(g.get("curmin"), g.get("curmax"))
    gs_inner_per_probe[pid] = ("both" if mmi and cmi else "min/max" if mmi
                               else "curmin/curmax" if cmi else "none")

_ok = {k: v for k, v in range_per_probe.items()
       if "contains_requested" in v}
# norescale with a list (twoway: ".add_ticks ..., norescale") versus a
# lone a(b)c rule (".range_ticks a c b", norescale dropped).
NR_LIST = ("b2_ylab_list_nr", "b2_ytick_50_nr", "b2_xtick_nr")
NR_RULE = ("b2_ylab_0_100_nr", "b2_ytick_rule_nr")
_nr = [_ok[k]["widened_vs_default"] for k in NR_LIST if k in _ok]
_nrr = [_ok[k]["widened_vs_default"] for k in NR_RULE if k in _ok]
range_rule = {
    "question": ("Which values widen a twoway axis, and does range() ever "
                 "narrow it?  (axis_label_options.sthlp:344-350, "
                 "axis_scale_options.sthlp:144-148, 336-341)"),
    "per_probe": range_per_probe,
    "all_contain_requested": all(v["contains_requested"]
                                 for v in _ok.values()) and bool(_ok),
    "none_narrower_than_data": not any(v["narrower_than_data"]
                                       for v in _ok.values()),
    "norescale_not_widened": bool(_nr) and all(w is False for w in _nr),
    "norescale_probes_listed": list(NR_LIST),
    "norescale_dropped_by_a_lone_rule": bool(_nrr)
        and all(w is True for w in _nrr),
    "norescale_rule_probes": list(NR_RULE),
    "norescale_note": (
        "twoway records ylabel(0(20)100, norescale) as .major.range_ticks "
        "0 100 20 with no norescale, and draws it widened exactly as "
        "without the option; a list, ylabel(0 20 40 60 80 100, norescale), "
        "is .add_ticks ..., norescale and is not widened.  ytick() alike."),
}
def gs_verdict(per):
    """The candidate that matches on every verified probe ("both" when
    both always do), "none" when neither ever does, else "mixed"."""
    a = [v for v in per.values() if v != "unverified"]
    if not a or all(v == "none" for v in a):
        return "none"
    if all(v == "both" for v in a):
        return "both"
    for cand in ("curmin/curmax", "min/max"):
        if all(v in (cand, "both") for v in a):
            return cand
    return "mixed"
graph_scale_matches_svg = {
    "question": (".Graph has no range member; which of plotregion1."
                 "<axis>scale's min/max (permanent) and curmin/curmax "
                 "(temporary) equals the drawn extent the SVG shows?"),
    "per_probe": gs_per_probe,
    "verdict": gs_verdict(gs_per_probe),
    "per_probe_inner": gs_inner_per_probe,
    "verdict_inner": gs_verdict(gs_inner_per_probe),
    "inner_note": (
        "per_probe compares with the drawn extent (the SVG's plotregion "
        "edges); per_probe_inner with that extent less the measured margin "
        "(71.2 SVG units a side, findings.axis_range_extension), within "
        "0.5% of the span."),
}

# --------------------------------------------------------------------------
# C. THE LEGEND RULE
# --------------------------------------------------------------------------
def anchorless(pid):
    return collections.Counter(t["text"]
                               for t in parsed.get(pid, {})
                               .get("anchorless_texts", []))

def all_texts(pid):
    return collections.Counter(t["text"]
                               for t in parsed.get(pid, {})
                               .get("all_text_elements", []))

def gph_box_texts(pid):
    """Every string the .gph records inside an mtextq() textbox -- the note,
    caption, title, subtitle and the tNtitle family.  Used as the second,
    legend(off)-independent classifier."""
    out = set()
    gp = (parsed.get(pid) or {}).get("gph") or {}
    for name, rows in (gp.get("textbox_placement") or {}).items():
        for r in rows:
            raw = r.get("text_mtextq") or ""
            for piece in re.findall(r'"([^"]*)"', raw):
                if piece:
                    out.add(piece)
    return out

legend_cases = {}
for pid in sorted(parsed):
    if parsed[pid]["group"] != "legend" or pid.endswith("__off"):
        continue
    e = parsed[pid]
    off = pid + "__off"
    bare = anchorless(pid)
    have_off = off in parsed and parsed[off].get("status") == "measured"
    off_changed = None
    if have_off:
        off_changed = bool(all_texts(pid) != all_texts(off))
        diff_keys = bare - anchorless(off)
    else:
        diff_keys = collections.Counter()

    # independent classifier: anchorless texts that the .gph does not record as
    # a note / caption / title / subtitle textbox
    boxed = gph_box_texts(pid)
    gph_keys = collections.Counter({k: v for k, v in bare.items()
                                    if k not in boxed})

    if have_off and off_changed:
        keys, basis = diff_keys, (
            "anchorless <text> elements present in probe " + pid +
            " and absent from " + off + " (the same command with the legend "
            "switched off)")
        verdict_source = "legend(off) difference"
    else:
        keys, basis = gph_keys, (
            "anchorless <text> elements minus every string the .gph records "
            "in an mtextq() textbox" +
            (" -- used because legend(off) changed nothing in " + off
             if have_off else " -- no legend(off) companion probe exists"))
        verdict_source = "gph-textbox subtraction"

    keyobjs = [t for t in e.get("anchorless_texts", [])
               if keys.get(t["text"], 0) > 0]
    pr = e.get("plotregion_px") or {}
    placement = None
    legrect = None
    if keyobjs and pr:
        cx = sum(t["x"] for t in keyobjs) / len(keyobjs)
        cy = sum(t["y"] for t in keyobjs) / len(keyobjs)
        for r in (e.get("regions_px") or [])[1:]:
            if r["left"] <= cx <= r["right"] and r["top"] <= cy <= r["bottom"]:
                legrect = r
                break
        inside = (pr["left"] <= cx <= pr["right"] and
                  pr["top"] <= cy <= pr["bottom"])
        if cx > pr["right"]:
            side = "right of plotregion"
        elif cx < pr["left"]:
            side = "left of plotregion"
        elif cy > pr["bottom"]:
            side = "below plotregion"
        elif cy < pr["top"]:
            side = "above plotregion"
        else:
            side = "inside plotregion"
        hf = ((cx - pr["left"]) / (pr["right"] - pr["left"])
              if pr["right"] != pr["left"] else None)
        vf = ((cy - pr["top"]) / (pr["bottom"] - pr["top"])
              if pr["bottom"] != pr["top"] else None)
        placement = {
            "key_centroid_px": {"x": round(cx, 2), "y": round(cy, 2)},
            "side_relative_to_plotregion": side,
            "inside_plotregion": inside,
            "horizontal_fraction_of_plotregion": (round(hf, 3)
                                                  if hf is not None else None),
            "vertical_fraction_of_plotregion": (round(vf, 3)
                                                if vf is not None else None),
            "legend_region_rect_px": legrect,
            "distinct_key_x_px": sorted({round(t["x"], 2) for t in keyobjs}),
            "distinct_key_y_px": sorted({round(t["y"], 2) for t in keyobjs}),
            "n_columns": len({round(t["x"], 2) for t in keyobjs}),
            "n_rows": len({round(t["y"], 2) for t in keyobjs}),
        }
    legend_cases[pid] = {
        "command": e["command"],
        "legend_drawn": bool(keyobjs),
        "n_keys": len(keyobjs),
        "keys_in_drawn_order": [t["text"] for t in
                                sorted(keyobjs, key=lambda t: (t["y"], t["x"]))],
        "key_font_size_px": sorted({t["font_size"] for t in keyobjs}) or None,
        "verdict_from": verdict_source,
        "evidence": basis,
        "off_companion": off if have_off else None,
        "off_companion_changed_the_graph": off_changed,
        "legend_drawn_by_off_difference": bool(diff_keys) if have_off else None,
        "legend_drawn_by_gph_subtraction": bool(gph_keys),
        "classifiers_agree": (None if not have_off
                              else bool(bool(diff_keys) == bool(gph_keys))),
        "placement": placement,
    }

drawn = sorted(k for k, v in legend_cases.items() if v["legend_drawn"])
nodraw = sorted(k for k, v in legend_cases.items() if not v["legend_drawn"])
disagree = sorted(k for k, v in legend_cases.items()
                  if v["classifiers_agree"] is False)
off_noop = sorted(k for k, v in legend_cases.items()
                  if v["off_companion_changed_the_graph"] is False)

clock_map = {}
for p in range(1, 13):
    pid = "c_pos%d" % p
    if pid in legend_cases and legend_cases[pid]["placement"]:
        pl = legend_cases[pid]["placement"]
        clock_map[str(p)] = {
            "command": legend_cases[pid]["command"],
            "side_relative_to_plotregion": pl["side_relative_to_plotregion"],
            "horizontal_fraction_of_plotregion":
                pl["horizontal_fraction_of_plotregion"],
            "vertical_fraction_of_plotregion":
                pl["vertical_fraction_of_plotregion"],
            "legend_region_rect_px": pl["legend_region_rect_px"],
            "n_rows": pl["n_rows"], "n_columns": pl["n_columns"]}

legend_rule = {
    "question": "When does twoway draw a legend at all?",
    "oracle": (
        "Every case was run twice -- bare and with the legend switched off -- "
        "exported to SVG, and the anchorless <text> elements that disappear "
        "were counted as legend keys.  Where switching the legend off changed "
        "nothing (it does not under by(..., legend(off)) for the enclosing "
        "graph), a second classifier was used instead: anchorless texts minus "
        "every mtextq() textbox string recorded in the .gph.  Both verdicts "
        "are stored per case and any disagreement is listed."),
    "cases_with_a_legend": drawn,
    "cases_without_a_legend": nodraw,
    "key_counts": {k: legend_cases[k]["n_keys"] for k in sorted(legend_cases)},
    "classifier_disagreements": disagree,
    "cases_where_legend_off_changed_nothing": off_noop,
    "clock_position_map": clock_map,
}

# --------------------------------------------------------------------------
# B. DEFAULT AXIS-RANGE EXTENSION
# --------------------------------------------------------------------------
VARS_FOR = {
    "a_default": ("auto", "weight", "mpg"),
    "b_default": ("auto", "weight", "mpg"),
    "b_ext_price": ("auto", "weight", "price"),
    "b_ext_turn": ("auto", "length", "turn"),
    "b_ext_gear": ("auto", "displacement", "gear_ratio"),
    "b_ext_head": ("auto", "trunk", "headroom"),
    "b_ext_nl_wage": ("nlsw88", "hours", "wage"),
    "b_ext_nl_grade": ("nlsw88", "age", "grade"),
    "a_nl_default": ("nlsw88", "hours", "wage"),
    "a_nl_ttl_default": ("nlsw88", "ttl_exp", "wage"),
    "a_nl_age_default": ("nlsw88", "age", "wage"),
    "a_ydefault_price": ("auto", "weight", "price"),
    "b_size_wide": ("auto", "weight", "mpg"),
    "b_size_tall": ("auto", "weight", "mpg"),
    "b_size_square": ("auto", "weight", "mpg"),
}
extension_rows = []
for pid, (ds, xv, yv) in sorted(VARS_FOR.items()):
    e = parsed.get(pid)
    if not e or e.get("status") != "measured":
        continue
    for which, v in (("x", xv), ("y", yv)):
        ax = e.get(which + "_axis", {})
        mp = ax.get("mapping")
        df = data_facts.get(ds, {}).get(v)
        tv = [t for t in (ax.get("tick_values") or []) if t is not None]
        if not mp or not df or not tv:
            continue
        lo_in, hi_in = min(df["min"], min(tv)), max(df["max"], max(tv))
        span = hi_in - lo_in
        alo, ahi = mp["axis_low"], mp["axis_high"]
        pr = e.get("plotregion_px") or {}
        row = {
            "probe": pid, "command": e["command"], "axis": which,
            "variable": v, "data_min": df["min"], "data_max": df["max"],
            "tick_min": min(tv), "tick_max": max(tv),
            "inner_low": lo_in, "inner_high": hi_in, "inner_span": span,
            "axis_low": alo, "axis_high": ahi,
            "low_extension": lo_in - alo, "high_extension": ahi - hi_in,
            "low_extension_frac_of_inner_span": ((lo_in - alo) / span
                                                 if span else None),
            "high_extension_frac_of_inner_span": ((ahi - hi_in) / span
                                                  if span else None)}
        # the same thing in pixels: how far inside the plotregion edge the
        # extreme DATA/TICK value is drawn
        if pr and mp and mp["space"] == "linear" and mp["value_units_per_px"]:
            edge = pr["left"] if which == "x" else pr["bottom"]
            far = pr["right"] if which == "x" else pr["top"]
            def px_of(val, edge=edge, mp=mp):
                return (edge + (val - mp["value_at_plotregion_start"]) /
                        mp["value_units_per_px"])
            plo, phi = px_of(lo_in), px_of(hi_in)
            full = abs(far - edge)
            row["canvas_px"] = e.get("canvas_px")
            row["plotregion_px_extent"] = round(full, 2)
            row["low_margin_px"] = round(abs(plo - edge), 2)
            row["high_margin_px"] = round(abs(far - phi), 2)
            row["low_margin_frac_of_plotregion"] = round(abs(plo - edge) / full, 5)
            row["high_margin_frac_of_plotregion"] = round(abs(far - phi) / full, 5)
        extension_rows.append(row)
fr = [r["low_extension_frac_of_inner_span"] for r in extension_rows
      if r["low_extension_frac_of_inner_span"] is not None]
fr += [r["high_extension_frac_of_inner_span"] for r in extension_rows
       if r["high_extension_frac_of_inner_span"] is not None]
margin_px = sorted({(r["probe"], r["axis"], r.get("low_margin_px"),
                     r.get("high_margin_px"), r.get("plotregion_px_extent"),
                     (r.get("canvas_px") or {}).get("w"),
                     (r.get("canvas_px") or {}).get("h"))
                    for r in extension_rows if "low_margin_px" in r})
extension_finding = {
    "method": (
        "axis_low / axis_high are the DATA values at the two plotregion edges, "
        "obtained by inverting the tick-pixel -> tick-value map.  inner_low / "
        "inner_high are min/max over (data min/max, tick min/max): Stata first "
        "widens the axis to include every tick it decided to draw, then adds "
        "the margin.  The extension is the difference between the two."),
    "rows": extension_rows,
    "observed_extension_fraction_min": (min(fr) if fr else None),
    "observed_extension_fraction_max": (max(fr) if fr else None),
    "observed_extension_fraction_mean": (sum(fr) / len(fr) if fr else None),
    "pixel_margin_rows": [
        {"probe": a, "axis": b, "low_margin_px": c, "high_margin_px": d,
         "plotregion_px_extent": ee, "canvas_w": f, "canvas_h": g,
         "margin_over_min_canvas_dimension":
             (round(((c + d) / 2.0) / min(f, g), 5)
              if None not in (c, d, f, g) and min(f, g) else None)}
        for (a, b, c, d, ee, f, g) in margin_px],
    "margin_over_min_canvas_dimension_values": sorted(
        {round(((c + d) / 2.0) / min(f, g), 4)
         for (a, b, c, d, ee, f, g) in margin_px
         if None not in (c, d, f, g) and min(f, g)}),
    "pixel_margin_note": (
        "low_margin_px / high_margin_px are the gap, in SVG user units, "
        "between a plotregion edge and the extreme value the axis had to "
        "contain.  Probes b_size_wide / b_size_tall / b_size_square vary "
        "xsize()/ysize() so that a margin fixed in absolute units can be told "
        "apart from one that is a fixed fraction of the plotregion.  Across "
        "all four graph shapes probed the margin is the same on all four "
        "sides and is a constant fraction of min(canvas width, canvas "
        "height) -- see margin_over_min_canvas_dimension_values."),
}

# --------------------------------------------------------------------------
# D. TITLES / NOTES / CAPTIONS
# --------------------------------------------------------------------------
def title_report(pid):
    e = parsed.get(pid)
    if not e or e.get("status") != "measured":
        return None
    gp = e.get("gph") or {}
    return {"command": e["command"],
            "gph_textbox_placement": gp.get("textbox_placement"),
            "gph_editstyle_lines": gp.get("editstyle_lines"),
            "rendered_texts": e["all_text_elements"],
            "plotregion_px": e["plotregion_px"]}

title_findings = {pid: title_report(pid) for pid in sorted(parsed)
                  if parsed[pid]["group"] == "titles"}

# BR-09.2: sub-option text must never reach the rendered output.  For every
# titles probe, the strings the user typed inside title()/subtitle()/note()/
# caption()/xtitle()/ytitle() are compared with what was actually drawn.
LEAK = re.compile(r"(size\(|color\(|position\(|\bspan\b|orientation\(|"
                  r"justification\(|margin\()")
for pid, v in title_findings.items():
    if v is None:
        continue
    cmd = v["command"]
    wanted = []
    for m in re.finditer(r"\b(title|subtitle|note|caption|xtitle|ytitle|"
                         r"[tblr][12]title)\(", cmd):
        i = m.end()
        depth, buf = 1, ""
        while i < len(cmd) and depth:
            ch = cmd[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if not depth:
                    break
            buf += ch
            i += 1
        wanted += re.findall(r'"([^"]*)"', buf)
    drawn_txt = [t["text"] for t in v["rendered_texts"]]
    v["requested_strings"] = wanted
    v["requested_strings_all_rendered_verbatim"] = all(w in drawn_txt
                                                       for w in wanted)
    v["missing_from_output"] = [w for w in wanted if w not in drawn_txt]
    v["rendered_strings_containing_sub_option_syntax"] = [
        t for t in drawn_txt if LEAK.search(t)]
    v["sub_option_text_leaked"] = bool(
        v["rendered_strings_containing_sub_option_syntax"])
title_leaks = sorted(pid for pid, v in title_findings.items()
                     if v and v["sub_option_text_leaked"])
title_missing = sorted(pid for pid, v in title_findings.items()
                       if v and not v["requested_strings_all_rendered_verbatim"])

# note-vs-caption placement, stated as a fact rather than left to the reader
nc = parsed.get("d_note_caption") or {}
note_caption = None
if nc.get("status") == "measured":
    pr = nc["plotregion_px"]
    ranks = {}
    for t in nc["all_text_elements"]:
        if t["text"] in ("NOTEXT", "CAPTEXT"):
            ranks[t["text"]] = {"x": t["x"], "y": t["y"],
                                "font_size_px": t["font_size"],
                                "fill": t["fill"], "anchor": t["anchor"]}
    gpl = (nc.get("gph") or {}).get("textbox_placement") or {}
    note_caption = {
        "command": nc["command"],
        "rendered": ranks,
        "plotregion_px": pr,
        "gph_rings": {k: [r for r in v if r.get("text_mtextq")]
                      for k, v in gpl.items() if k in ("note", "caption")},
        "verdict": None}
    if "NOTEXT" in ranks and "CAPTEXT" in ranks:
        note_caption["verdict"] = (
            "note is drawn at y=%.2f and caption at y=%.2f, both below the "
            "plotregion (bottom=%.2f); the %s is nearer the plot.  They do "
            "not share a position." % (
                ranks["NOTEXT"]["y"], ranks["CAPTEXT"]["y"], pr["bottom"],
                "note" if ranks["NOTEXT"]["y"] < ranks["CAPTEXT"]["y"]
                else "caption"))

# default sizes / colours of each textbox under the scheme in force
default_styles = {}
src = parsed.get("d_all_six")
if src and src.get("status") == "measured":
    want = {"TITLETEXT": "title", "SUBTEXT": "subtitle", "NOTEXT": "note",
            "CAPTEXT": "caption", "XTEXT": "xtitle", "YTEXT": "ytitle"}
    for t in src["all_text_elements"]:
        if t["text"] in want:
            default_styles[want[t["text"]]] = {
                "font_size_px": t["font_size"], "fill": t["fill"],
                "font_family": t["font_family"], "anchor": t["anchor"],
                "rotate": t["rotate"], "x": t["x"], "y": t["y"]}
    default_styles["_source"] = {
        "command": src["command"],
        "note": ("sizes are SVG user units on a 7.5in x 4.5in graph "
                 "(viewBox 0 0 5400 3240); divide by 14.4 for points"),
        "tick_label_font_size_px": (src["x_axis"].get("label_style") or {}).get(
            "font_size_px")}

# --------------------------------------------------------------------------
# E. REFERENCE LINES -- style read by differencing against the no-option graph
# --------------------------------------------------------------------------
def group_key(g):
    return (g["px"], g["stroke"], g["stroke_width"], g["n_segments"])

refline_findings = {}
base = parsed.get("e_baseline")
for pid in sorted(parsed):
    if parsed[pid]["group"] != "refline" or pid == "e_baseline":
        continue
    e = parsed[pid]
    if e.get("status") != "measured" or not base or base.get("status") != "measured":
        refline_findings[pid] = {"command": e["command"],
                                 "status": e.get("status")}
        continue
    out = {"command": e["command"],
           "evidence": ("<line> groups present in this graph and absent from "
                        "the identical graph with no reference line "
                        "(probe e_baseline)"),
           "gph_xyline_lines": (e.get("gph") or {}).get("xyline_lines"),
           "gph_gridlinestyle_lines": (e.get("gph") or {}).get("gridlinestyle_lines"),
           "gph_editstyle_lines": (e.get("gph") or {}).get("editstyle_lines")}
    for orient, axis in (("vertical", "x"), ("horizontal", "y")):
        bk = {group_key(g) for g in base["svg_line_groups"][orient]}
        new = [g for g in e["svg_line_groups"][orient]
               if group_key(g) not in bk]
        if not new:
            continue
        mp = (e.get(axis + "_axis") or {}).get("mapping")
        for g in new:
            g = dict(g)
            if mp:
                z = (mp["value_at_plotregion_start"] +
                     mp["value_units_per_px"] *
                     (g["px"] - (e["plotregion_px"]["left"] if axis == "x"
                                 else e["plotregion_px"]["bottom"])))
                g["data_value"] = (10 ** z if mp["space"] == "log10" else z)
            out.setdefault(orient + "_lines_added", []).append(g)
    refline_findings[pid] = out

# --------------------------------------------------------------------------
# self-check
# --------------------------------------------------------------------------
def inventory(path):
    sv = read_svg(path)
    if sv is None:
        return None
    return sorted((t["text"], t["x"], t["y"], t["font_size"], t["fill"])
                  for t in sv["texts"])
sc = "NOT RUN"
if selfchk:
    ia, ib = inventory(selfchk[0]), inventory(selfchk[1])
    sc = "PASS" if (ia is not None and ia == ib) else "FAIL"

# --------------------------------------------------------------------------
# UNVERIFIED register
# --------------------------------------------------------------------------
unverified = {}
for pid, e in sorted(parsed.items()):
    if e.get("status") != "measured":
        unverified[pid] = e.get("status")
        continue
    for w in ("x", "y"):
        ax = e.get(w + "_axis", {})
        if ax.get("error"):
            unverified[pid + " (" + w + " axis)"] = ax["error"]
        elif ax.get("mapping_note"):
            unverified[pid + " (" + w + " axis values)"] = ax["mapping_note"]
unverified.update(b2_unverified)
for k in disagree:
    unverified["legend verdict for " + k] = (
        "the legend(off) difference and the gph-textbox subtraction disagree; "
        "the fixture reports both and prefers " + legend_cases[k]["verdict_from"])

doc = {
    "_meta": {
        "generated_by": "scripts/extract_axis_truth.do",
        "source": "scripts/extract_axis_truth.do",
        "record_file": os.path.basename(REC),
        "run_date": meta_rows.get("run_date"),
        "stata_version": meta_rows.get("stata_version"),
        "stata_flavor": meta_rows.get("stata_flavor"),
        "stata_edition": meta_rows.get("stata_edition"),
        "stata_born_date": meta_rows.get("stata_born_date"),
        "scheme_in_force": meta_rows.get("scheme"),
        # D12 (WP-28): the provenance stamp every new or regenerated
        # fixture carries, beside the keys above (kept for the tests that
        # already read them, e.g. test_axis_options.py:637's
        # scheme_in_force).
        "born_date": meta_rows.get("born_date"),
        "dash_commit": meta_rows.get("dash_commit"),
        "extracted": meta_rows.get("extracted"),
        "datasets": ["sysuse auto, clear", "sysuse nlsw88, clear",
                     "sysuse auto, clear (value-labelled rep78)",
                     "sysuse sp500, clear (m = mofd(date), %tm)",
                     "sysuse sp500, clear"],
        "method": (
            "Two oracles.  (1) The live-format .gph -- a plain-text "
            "graph-object script -- is authoritative for STRUCTURE: ring "
            "numbers, which side of the plotregion a textbox sits, and the "
            "verbatim editstyle directives an option produced.  It is NOT an "
            "oracle for tick positions: xlabel(#10) is stored as "
            "'.xaxis1.major.suggest_ticks 10' and the positions are computed "
            "at render time and never written to the file, drawn or not.  "
            "(2) Stata's own SVG writer gives the RENDERED result: the "
            "plotregion is the first solid-fill <rect> inside the graph "
            "region, tick marks are short black <line>s at a plotregion edge, "
            "tick labels are the row/column of <text> nearest that edge, "
            "gridlines are dashed multi-segment <line> groups, and legend "
            "keys are <text> elements with no text-anchor attribute.  "
            "Inverting the tick-pixel -> tick-value fit at the plotregion "
            "edges yields the axis range Stata actually used."),
        "legend_oracle": (
            "Legend presence is a DIFFERENCE, never an inspection: every "
            "legend case is run twice, bare and with the legend off, and the "
            "anchorless <text> elements that disappear are the legend.  A "
            "second classifier (anchorless texts minus every mtextq() textbox "
            "string in the .gph) is recorded alongside, and is the one used "
            "where switching the legend off changed nothing."),
        "oracle_selfcheck": (
            "the same twoway command exported twice, more than a second "
            "apart, yields an identical text inventory: " + sc),
        "caveats": [
            "All measurements are under the scheme reported in "
            "scheme_in_force.  A different scheme moves default sizes, "
            "colours, gridlines and the default legend position.",
            "Tick VALUES are recovered by parsing the rendered tick LABEL "
            "back to a number.  Where a label is not numeric (explicit "
            "value \"label\" pairs) the value is null and only the exact "
            "pixel position is reported.",
            "Pixel measurements are SVG user units on a 7.5in x 4.5in graph "
            "(viewBox 0 0 5400 3240); 14.4 units = 1 point.",
            "xscale(noextend) shortens the drawn axis LINE to the outermost "
            "tick; it does not move the plotregion.  Compare axis_line_px "
            "with plotregion_px on those probes.",
        ],
        "counts": {
            "probes": len(parsed),
            "measured": len([1 for e in parsed.values()
                             if e.get("status") == "measured"]),
            "legend_cases": len(legend_cases),
            "unverified": len(unverified)},
    },
    "data_facts": data_facts,
    "probes": parsed,
    "findings": {
        "legend_rule": legend_rule,
        "legend_cases": legend_cases,
        "axis_range_extension": extension_finding,
        "titles_notes_captions": title_findings,
        "note_vs_caption_placement": note_caption,
        "title_text_fidelity": {
            "question": ("does twoway ever render the sub-option text, and is "
                         "the requested string always drawn verbatim?"),
            "probes_where_sub_option_syntax_reached_the_canvas": title_leaks,
            "probes_where_a_requested_string_was_not_drawn": title_missing},
        "default_textbox_styles": default_styles,
        "reference_lines": refline_findings,
        # WP-28 S18 (B2)
        "range_rule": range_rule,
        "graph_scale_matches_svg": graph_scale_matches_svg},
    "unverified": unverified,
}

with open(OUT, "w") as fh:
    json.dump(doc, fh, indent=2, sort_keys=True, default=str)
    fh.write("\n")
print("WROTE " + OUT)
print("probes=%d measured=%d legend_cases=%d unverified=%d selfcheck=%s" %
      (len(parsed),
       len([1 for e in parsed.values() if e.get("status") == "measured"]),
       len(legend_cases), len(unverified), sc))
print("--- legend DRAWN ---")
for k in drawn:
    print("   %-26s keys=%d %-3s %s" % (k, legend_cases[k]["n_keys"],
          legend_cases[k]["verdict_from"][:3], legend_cases[k]["command"][:80]))
print("--- legend NOT drawn ---")
for k in nodraw:
    print("   %-26s %s" % (k, legend_cases[k]["command"][:80]))
print("--- title sub-option leaks: %s" % (title_leaks or "none"))
print("--- requested title strings not drawn: %s" % (title_missing or "none"))
print("--- classifier disagreements: %s" % (disagree or "none"))
print("--- legend(off) changed nothing in: %s" % (off_noop or "none"))
end

display as text "extract_axis_truth.do: done"
