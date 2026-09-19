*! extract_axis_truth.do
*! Derive AXIS / LEGEND / TITLE / REFERENCE-LINE ground truth for section S09
*! BY PROBING STATA ITSELF.  Nothing in the output fixture is remembered,
*! inferred from documentation, or copied from another implementation: every
*! recorded value carries the command that produced it, and anything the
*! probes could not establish is listed under "unverified" instead of guessed.
*!
*! Output: test/fixtures/axis_truth.json
*!
*! Run with (Stata must be forced to its arm64 slice, and must be launched from
*! a scratch directory because batch mode writes its .log to the process
*! working directory):
*!
*!   mkdir -p /tmp/dash-s09 && cd /tmp/dash-s09 && \
*!   arch -arm64 /usr/local/bin/stata-mp -b do \
*!     /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/extract_axis_truth.do
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

global ZA_REPO "/Users/billy/Desktop/Programs/StataPrograms/d/dash"
global ZA_OUT  "${ZA_REPO}/test/fixtures/axis_truth.json"

local scratch "`c(tmpdir)'/dash_axis_probe"
capture mkdir "`scratch'"
global ZA_WORK "`scratch'"
global ZA_REC  "`scratch'/axis_records.txt"
display as text "probe scratch dir: ${ZA_WORK}"

global ZA_SVER = c(stata_version)
global ZA_FLAV = c(flavor)
global ZA_EDIT = c(edition_real)
global ZA_BORN = c(born_date)
global ZA_DATE = c(current_date)

* ===========================================================================
* Registration.  A probe is (id, group, dataset, body, options).  Body and
* options are kept apart so that name(zqg, replace) can be appended without
* having to guess whether the registered command already carries a comma.
* ===========================================================================
global ZA_N = 0
program define zp
    local id   `"`1'"'
    local grp  `"`2'"'
    local ds   `"`3'"'
    local body `"`4'"'
    local opts `"`5'"'
    global ZA_N = ${ZA_N} + 1
    global ZA_ID_${ZA_N}   `"`id'"'
    global ZA_GRP_${ZA_N}  `"`grp'"'
    global ZA_DS_${ZA_N}   `"`ds'"'
    global ZA_BODY_${ZA_N} `"`body'"'
    global ZA_OPTS_${ZA_N} `"`opts'"'
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
display as text "scheme in force: `c(scheme)'"

* ---- data facts (min / max / N / display format) used to derive the default
*      range-extension rule.  Never taken from memory. -----------------------
foreach ds in auto nlsw88 {
    sysuse `ds', clear
    local vlist ""
    if "`ds'" == "auto"   local vlist mpg weight price turn length gear_ratio headroom trunk displacement
    if "`ds'" == "nlsw88" local vlist wage hours ttl_exp age grade
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

    if "`ds'" != "`curds'" {
        sysuse `ds', clear
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
    if `rc' == 0 {
        capture graph export "`svg'", name(zqg) replace
        local rcx = _rc
        capture graph save zqg "`gph'", replace
        local rcg = _rc
    }
    capture graph drop zqg
    file write `rec' `"PROBE|`id'|`grp'|`ds'|`rc'|`rcx'|`rcg'|`svg'|`gph'|`shown'"' _n
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
import json, os, re, math, html, collections
from sfi import Macro

REC = Macro.getGlobal("ZA_REC")
OUT = Macro.getGlobal("ZA_OUT")

RE_ATTR = re.compile(r'([\w:-]+)="([^"]*)"')
RE_TEXT = re.compile(r'<text ([^>]*?)>(.*?)</text>', re.S)
RE_LINE = re.compile(r'<line ([^/>]*)/>')
RE_RECT = re.compile(r'<rect ([^/>]*)/>')

def attrs(s):
    return dict(RE_ATTR.findall(s))

def fnum(s, default=None):
    try:
        return float(s)
    except Exception:
        return default

def style_of(a):
    out = {}
    for part in a.get("style", "").split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip()] = v.strip()
    return out

# --------------------------------------------------------------------------
# SVG parsing
# --------------------------------------------------------------------------
def parse_svg(path):
    """Structural facts of a Stata-written SVG.

    plotregion  -- the first solid-fill <rect> that is not the whole canvas.
                   Stata writes each region as a fill rect followed by a
                   border rect, outermost first: canvas, graphregion,
                   plotregion, then any legend / by-panel regions.  This
                   identification is INDEPENDENT of the axis lines, which
                   matters because xscale(noextend) shortens the axis line to
                   the outermost tick while leaving the plotregion alone.
    axis_line   -- the extent of the longest black horizontal and vertical
                   <line>, recorded separately so that noextend is measurable.
    """
    if not path or not os.path.exists(path):
        return None
    txt = open(path, "r", errors="replace").read()

    texts = []
    for m in RE_TEXT.finditer(txt):
        a = attrs(m.group(1))
        st = style_of(a)
        rot = None
        mr = re.search(r'rotate\((-?[\d.]+)', a.get("transform", ""))
        if mr:
            rot = float(mr.group(1))
        texts.append({
            "x": fnum(a.get("x")), "y": fnum(a.get("y")),
            "anchor": a.get("text-anchor"),
            "rotate": rot,
            "font_size": fnum(st.get("font-size", "").replace("px", "")),
            "fill": st.get("fill"),
            "font_family": st.get("font-family"),
            "text": html.unescape(m.group(2)),
        })

    hlines, vlines, diag = [], [], []
    for m in RE_LINE.finditer(txt):
        a = attrs(m.group(1))
        st = style_of(a)
        x1, y1 = fnum(a.get("x1")), fnum(a.get("y1"))
        x2, y2 = fnum(a.get("x2")), fnum(a.get("y2"))
        if None in (x1, y1, x2, y2):
            continue
        d = {"x1": x1, "y1": y1, "x2": x2, "y2": y2,
             "stroke": st.get("stroke"),
             "width": fnum(st.get("stroke-width", "")),
             "dasharray": st.get("stroke-dasharray")}
        if abs(y1 - y2) < 0.01:
            hlines.append(d)
        elif abs(x1 - x2) < 0.01:
            vlines.append(d)
        else:
            diag.append(d)

    rects = []
    for m in RE_RECT.finditer(txt):
        a = attrs(m.group(1))
        st = style_of(a)
        rects.append({"x": fnum(a.get("x")), "y": fnum(a.get("y")),
                      "w": fnum(a.get("width")), "h": fnum(a.get("height")),
                      "fill": st.get("fill"), "stroke": st.get("stroke")})

    canvas = None
    mv = re.search(r'viewBox="([\d.\- ]+)"', txt)
    if mv:
        vb = [float(t) for t in mv.group(1).split()]
        canvas = {"x": vb[0], "y": vb[1], "w": vb[2], "h": vb[3]}

    regions = []
    if canvas:
        area = canvas["w"] * canvas["h"]
        for r in rects:
            if not r["w"] or not r["h"]:
                continue
            if r["fill"] in (None, "none"):
                continue
            if r["w"] * r["h"] >= 0.95 * area:
                continue
            regions.append({"left": r["x"], "top": r["y"],
                            "right": r["x"] + r["w"],
                            "bottom": r["y"] + r["h"],
                            "fill": r["fill"]})
    pr = None
    if regions:
        r = regions[0]
        pr = dict(r)
        pr["source"] = ("first solid-fill <rect> inside the graph region "
                        "(Stata writes canvas, graphregion, plotregion, then "
                        "legend / by-panel regions, in that order)")

    def black(d):
        return (d.get("stroke") or "").upper() == "#000000"
    axline = None
    hb = [d for d in hlines if black(d)]
    vb_ = [d for d in vlines if black(d)]
    if hb and vb_:
        bot = max(hb, key=lambda d: abs(d["x2"] - d["x1"]))
        lef = max(vb_, key=lambda d: abs(d["y2"] - d["y1"]))
        axline = {"h_y": bot["y1"], "h_x_from": min(bot["x1"], bot["x2"]),
                  "h_x_to": max(bot["x1"], bot["x2"]),
                  "v_x": lef["x1"], "v_y_from": min(lef["y1"], lef["y2"]),
                  "v_y_to": max(lef["y1"], lef["y2"])}
    if pr is None and axline:
        pr = {"left": axline["v_x"], "right": axline["h_x_to"],
              "top": axline["v_y_from"], "bottom": axline["h_y"],
              "source": "axis-line bounding box (no solid-fill region rect)"}

    return {"texts": texts, "hlines": hlines, "vlines": vlines,
            "diaglines": diag, "rects": rects, "canvas": canvas,
            "regions": regions, "plotregion": pr, "axis_line": axline}

def label_value(s):
    """Parse a rendered tick label back to a number, or None."""
    t = s.strip().replace("−", "-").replace(",", "")
    if re.fullmatch(r'-?(\d+\.?\d*|\.\d+)', t or "x"):
        return float(t)
    return None

def line_groups(lines, coord):
    """Collapse the segments of one drawn line into a single group."""
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

def axis_facts(sv, which):
    """Tick marks, tick labels, gridlines, side, and the data<->pixel map."""
    if sv is None or sv["plotregion"] is None:
        return {"error": "no plotregion could be identified in the SVG"}
    pr = sv["plotregion"]
    tol = 2.5
    out = {}

    def black(d):
        return (d.get("stroke") or "").upper() == "#000000"

    if which == "x":
        marks_below, marks_above = [], []
        for d in sv["vlines"]:
            if not black(d):
                continue
            ylo, yhi = min(d["y1"], d["y2"]), max(d["y1"], d["y2"])
            if (yhi - ylo) > 0.5 * (pr["bottom"] - pr["top"]):
                continue
            if abs(ylo - pr["bottom"]) < tol:
                marks_below.append(round(d["x1"], 2))
            elif abs(yhi - pr["top"]) < tol:
                marks_above.append(round(d["x1"], 2))
        grid = [g for g in line_groups([d for d in sv["vlines"]
                                        if not black(d)], "x1")
                if g["n_segments"] > 3
                and g["span_to"] - g["span_from"] >
                0.8 * (pr["bottom"] - pr["top"])]
        axis_pos = sorted(set(marks_below or marks_above))
        out["tick_side"] = ("below plotregion" if marks_below else
                            ("above plotregion" if marks_above else None))
        cand = [t for t in sv["texts"]
                if t["y"] is not None and
                (t["y"] > pr["bottom"] or t["y"] < pr["top"])]
        keyc, offc = "x", "y"
        near_edge = (pr["bottom"] if marks_below else pr["top"])
    else:
        marks_left, marks_right = [], []
        for d in sv["hlines"]:
            if not black(d):
                continue
            xlo, xhi = min(d["x1"], d["x2"]), max(d["x1"], d["x2"])
            if (xhi - xlo) > 0.5 * (pr["right"] - pr["left"]):
                continue
            if abs(xhi - pr["left"]) < tol:
                marks_left.append(round(d["y1"], 2))
            elif abs(xlo - pr["right"]) < tol:
                marks_right.append(round(d["y1"], 2))
        grid = [g for g in line_groups([d for d in sv["hlines"]
                                        if not black(d)], "y1")
                if g["n_segments"] > 3
                and g["span_to"] - g["span_from"] >
                0.8 * (pr["right"] - pr["left"])]
        axis_pos = sorted(set(marks_left or marks_right))
        out["tick_side"] = ("left of plotregion" if marks_left else
                            ("right of plotregion" if marks_right else None))
        cand = [t for t in sv["texts"]
                if t["x"] is not None and
                (t["x"] < pr["left"] or t["x"] > pr["right"])]
        keyc, offc = "y", "x"
        near_edge = (pr["left"] if marks_left else pr["right"])

    if not axis_pos:
        axis_pos = sorted({g["px"] for g in grid})
    out["tick_px"] = axis_pos
    out["n_ticks"] = len(axis_pos)
    out["gridline_px"] = [g["px"] for g in grid]
    out["n_gridlines"] = len(grid)
    out["gridline_style"] = sorted({(g["stroke"], g["stroke_width"],
                                     g["n_segments"] > 1) for g in grid})

    # ---- tick labels: the row (x axis) / column (y axis) of text nearest the
    #      axis edge.  Clustering first is what keeps the rotated axis TITLE,
    #      which also sits outside the plotregion, out of the tick labels.
    labels, lab_px, lab_objs = [], [], []
    if cand and axis_pos:
        clusters = collections.defaultdict(list)
        for t in cand:
            clusters[round(t[offc], 1)].append(t)
        best = min(clusters, key=lambda c: abs(c - near_edge))
        row = clusters[best]
        used = set()
        for p in axis_pos:
            pick, pd = None, 1e18
            for j, t in enumerate(row):
                if j in used or t[keyc] is None:
                    continue
                dd = abs(t[keyc] - p)
                if dd < pd:
                    pick, pd = j, dd
            if pick is not None and pd < 250:
                used.add(pick)
                labels.append(row[pick]["text"])
                lab_objs.append(row[pick])
            else:
                labels.append(None)
            lab_px.append(p)
        out["label_offaxis_px"] = best
    else:
        labels = [None] * len(axis_pos)
        lab_px = list(axis_pos)
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

    # ---- data <-> pixel map from the numeric labels ------------------------
    pairs = [(px, label_value(l)) for px, l in zip(lab_px, labels)
             if l is not None and label_value(l) is not None]
    out["mapping"] = None
    if len(pairs) >= 2:
        for space in ("linear", "log10"):
            pp = pairs
            if space == "log10":
                if any(v <= 0 for _, v in pairs):
                    continue
                pp = [(px, math.log10(v)) for px, v in pairs]
            (p0, v0), (p1, v1) = pp[0], pp[-1]
            if p1 == p0 or v1 == v0:
                continue
            slope = (v1 - v0) / (p1 - p0)
            resid = max(abs((v - v0) - slope * (px - p0)) for px, v in pp)
            scale = max(abs(v) for _, v in pp) or 1.0
            if resid / scale < 1e-3 or len(pp) == 2:
                def inv(px, v0=v0, p0=p0, slope=slope, space=space):
                    z = v0 + slope * (px - p0)
                    return 10 ** z if space == "log10" else z
                if which == "x":
                    lo, hi = inv(pr["left"]), inv(pr["right"])
                else:
                    lo, hi = inv(pr["bottom"]), inv(pr["top"])
                out["mapping"] = {
                    "space": space,
                    "value_units_per_px": slope,
                    "max_abs_residual_over_ticks": resid,
                    "value_at_plotregion_start": lo,
                    "value_at_plotregion_end": hi,
                    "axis_low": min(lo, hi),
                    "axis_high": max(lo, hi),
                    "reversed": bool(hi < lo),
                }
                break
    if out["mapping"] is None:
        out["mapping_note"] = (
            "fewer than two tick labels parse as numbers, so the pixel<->data "
            "map could not be inverted; the tick pixel positions above are "
            "still exact")
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
            probes[f[1]] = {"group": f[2], "dataset": f[3], "rc": int(f[4]),
                            "export_rc": f[5], "save_rc": f[6],
                            "svg": f[7], "gph": f[8],
                            "command": "|".join(f[9:])}

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
    sv = parse_svg(p["svg"])
    if sv is None:
        e["status"] = "the graph drew but no SVG was written; nothing measured"
        parsed[pid] = e
        continue
    e["status"] = "measured"
    e["plotregion_px"] = sv["plotregion"]
    e["regions_px"] = sv["regions"]
    e["axis_line_px"] = sv["axis_line"]
    e["canvas_px"] = sv["canvas"]
    e["x_axis"] = axis_facts(sv, "x")
    e["y_axis"] = axis_facts(sv, "y")
    e["all_text_elements"] = sv["texts"]
    e["anchorless_texts"] = [t for t in sv["texts"]
                             if t["anchor"] is None and t["rotate"] is None]
    e["svg_line_groups"] = {"vertical": line_groups(sv["vlines"], "x1"),
                            "horizontal": line_groups(sv["hlines"], "y1")}
    e["gph"] = parse_gph(p["gph"])
    parsed[pid] = e

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
    sv = parse_svg(path)
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
for k in disagree:
    unverified["legend verdict for " + k] = (
        "the legend(off) difference and the gph-textbox subtraction disagree; "
        "the fixture reports both and prefers " + legend_cases[k]["verdict_from"])

doc = {
    "_meta": {
        "generated_by": "scripts/extract_axis_truth.do",
        "record_file": REC,
        "run_date": meta_rows.get("run_date"),
        "stata_version": meta_rows.get("stata_version"),
        "stata_flavor": meta_rows.get("stata_flavor"),
        "stata_edition": meta_rows.get("stata_edition"),
        "stata_born_date": meta_rows.get("stata_born_date"),
        "scheme_in_force": meta_rows.get("scheme"),
        "datasets": ["sysuse auto, clear", "sysuse nlsw88, clear"],
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
        "reference_lines": refline_findings},
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
