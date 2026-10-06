*! extract_text_truth.do
*! WP-28 section 13: textbox-grammar ground truth (B3, B6, B7) for
*! test/fixtures/text_truth.json, in scripts/extract_axis_truth.do's shape.
*!
*! WHY THIS EXISTS
*!
*! GAPS2 B3, B6 and B7 are proved against what twoway actually DRAWS, not
*! against a documented rule: whether a sub-option abbreviation (`c(red)`,
*! `si(large)`) is read as text or as a sub-option, whether `axis(2)`
*! titles the second axis, whether an empty string removes a title, and
*! whether `ytitle2()`/`xtitle2()` are read as textboxes at all.  This
*! script runs each probe through real Stata and records what twoway's own
*! SVG export drew, through the shared reader (S02: scripts/svg_truth.py,
*! test/cert_svg.do) -- the same method extract_axis_truth.do uses for the
*! axis family.
*!
*! Output: test/fixtures/text_truth.json
*!
*! Run with (the script sets its own directories, so it is handed to the
*! wrapper directly -- CLAUDE.md rule 10, sections/BRIEF.md "Stata
*! invocation"):
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_text_truth.do
*!
*! METHOD
*!
*! Every probe is registered by `zp id group dataset command option
*! control` (six arguments): `command` is the twoway command WITHOUT the
*! option under test, `option` is that option (e.g. `title("T", c(red))`,
*! empty for a control probe itself), and `control` is the id of the probe
*! whose texts are the baseline -- empty when the probe IS a control.  The
*! probe is run as `command'[, option'] name(zqt, replace)` (a command that
*! already carries its own top-level comma, such as
*! `twoway scatter mpg weight, yaxis(2)`, gets `option' name(...)` appended
*! to that SAME list instead of a second comma: `_zt_has_top_comma` decides
*! which). Only TWO of the 82 title probes below need this
*! (`t_ytitle_axis2_lone`, `t_ytitle_lone_nt_size`).
*!
*! Per probe the fixture records "texts" (every <text> in document order),
*! "fills" (svg_fills' colours, sorted), "added_texts"/"removed_texts" (a
*! Counter difference against the control, keeping the probe's own order),
*! "added_fills" (a set difference) and "text_sizes" ({text: px}).  The
*! trailing python: block keeps each svg_texts() entry's dict (text, x, y,
*! size, ...) until every probe's lists are built, and only then projects
*! to "text", because section 15 (batch 3) sorts legend entries by y then x
*! before it does the same projection (consistency #34) -- do not remove
*! the per-entry dicts on this script's account.
*!
*! Never calls back into Stata from the trailing python: block (it reads
*! files and Stata globals/locals already computed); a backtick inside it
*! is spelled \x60, since Stata expands a backtick/apostrophe pair as a
*! local-macro reference even inside a python: block.
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
    display as error "extract_text_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_text_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZA_REPO "`repo'"
global ZA_OUT  "${ZA_REPO}/test/fixtures/text_truth.json"

local scratch "`c(tmpdir)'dash_text_probe"
capture mkdir "`scratch'"
global ZA_WORK "`scratch'"
global ZA_REC  "`scratch'/text_records.txt"
display as text "probe scratch dir: ${ZA_WORK}"

global ZA_SVER   = c(stata_version)
global ZA_BORN   = c(born_date)
global ZA_DATE   = c(current_date)
global ZA_SCHEME = c(scheme)

// ---------------------------------------------------------------------------
// Provenance stamp (D12), exactly as extract_svg_truth_smoke.do captures
// it: `shell' writes the commit into a file, the do-file reads the file
// back, never a Stata call from Python.
// ---------------------------------------------------------------------------
tempfile zagitrev
quietly shell git -C "${ZA_REPO}" rev-parse HEAD > "`zagitrev'"
tempname zagfh
file open `zagfh' using "`zagitrev'", read text
file read `zagfh' zagitline
file close `zagfh'
local dash_commit = trim(`"`zagitline'"')
capture assert ustrregexm(`"`dash_commit'"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_text_truth.do: git rev-parse HEAD did not print a 40-character commit: `dash_commit'"
    exit 498
}

// Load cert_svg.do: it computes its scripts/ directory from c(pwd), so cd
// into test/, load it, and cd straight back.
local za_cwd `"`c(pwd)'"'
cd "${ZA_REPO}/test"
quietly do "cert_svg.do"
cd `"`za_cwd'"'

// ---------------------------------------------------------------------------
// _zt_has_top_comma: whether *s* has a comma outside every parenthesis --
// so a probe command such as "twoway scatter mpg weight, yaxis(2)" gets
// its option appended to the SAME comma-separated list rather than a
// second, illegal one.
// ---------------------------------------------------------------------------
capture program drop _zt_has_top_comma
program define _zt_has_top_comma, rclass
    version 16.0
    args s
    local depth = 0
    local found = 0
    local n = length(`"`s'"')
    forvalues i = 1/`n' {
        local ch = substr(`"`s'"', `i', 1)
        if `"`ch'"' == "(" local depth = `depth' + 1
        else if `"`ch'"' == ")" local depth = max(`depth' - 1, 0)
        else if `"`ch'"' == "," & `depth' == 0 local found = 1
    }
    return scalar found = `found'
end

// ===========================================================================
// Registration
// ===========================================================================
global ZA_N = 0
program define zp
    local id   `"`1'"'
    local grp  `"`2'"'
    local ds   `"`3'"'
    local cmd  `"`4'"'
    local opt  `"`5'"'
    local ctl  `"`6'"'
    global ZA_N = ${ZA_N} + 1
    global ZA_ID_${ZA_N}  `"`id'"'
    global ZA_GRP_${ZA_N} `"`grp'"'
    global ZA_DS_${ZA_N}  `"`ds'"'
    global ZA_CMD_${ZA_N} `"`cmd'"'
    global ZA_OPT_${ZA_N} `"`opt'"'
    global ZA_CTL_${ZA_N} `"`ctl'"'
end

// ---------------------------------------------------------------------------
// title/axis-title probes (B3, B6, B7).  42 probes, then WP-29 P0.4's 40.
// ---------------------------------------------------------------------------
zp "t_default"          "title" "auto" "twoway scatter mpg weight" "" ""
zp "t_y2_default"       "title" "auto" "twoway (scatter mpg weight) (line price weight, yaxis(2))" "" ""
zp "t_hist_default"     "title" "auto" "twoway histogram mpg" "" ""
zp "t_kdens_default"    "title" "auto" "twoway kdensity mpg" "" ""
zp "t_c_red"            "title" "auto" "twoway scatter mpg weight" `"title("T", c(red))"' "t_default"
zp "t_color_red"        "title" "auto" "twoway scatter mpg weight" `"title("T", color(red))"' "t_default"
zp "t_si_large"         "title" "auto" "twoway scatter mpg weight" `"title("T", si(large))"' "t_default"
zp "t_size_large"       "title" "auto" "twoway scatter mpg weight" `"title("T", size(large))"' "t_default"
zp "t_size_color_abbr"  "title" "auto" "twoway scatter mpg weight" `"title("T", si(large) c(red))"' "t_default"
zp "t_size_c"           "title" "auto" "twoway scatter mpg weight" `"title("T", size(large) c(red))"' "t_default"
zp "t_color_si"         "title" "auto" "twoway scatter mpg weight" `"title("T", color(red) si(large))"' "t_default"
zp "t_j_left"           "title" "auto" "twoway scatter mpg weight" `"title("A" "Bee", j(left))"' "t_default"
zp "t_bc_nobox"         "title" "auto" "twoway scatter mpg weight" `"title("T", bc(red))"' "t_default"
zp "t_box_bc"           "title" "auto" "twoway scatter mpg weight" `"title("T", box bc(red))"' "t_default"
zp "t_subtitle_c"       "title" "auto" "twoway scatter mpg weight" `"subtitle("S", c(red))"' "t_default"
zp "t_note_si"          "title" "auto" "twoway scatter mpg weight" `"note("N", si(large))"' "t_default"
zp "t_caption_c"        "title" "auto" "twoway scatter mpg weight" `"caption("C", c(red))"' "t_default"
zp "t_xtitle_c"         "title" "auto" "twoway scatter mpg weight" `"xtitle("W", c(red))"' "t_default"
zp "t_ytitle_si"        "title" "auto" "twoway scatter mpg weight" `"ytitle("M", si(large))"' "t_default"
zp "t_xtitle_orient"    "title" "auto" "twoway scatter mpg weight" `"xtitle("Weight", orient(vertical))"' "t_default"
zp "t_ytitle_axis2"     "title" "auto" "twoway (scatter mpg weight) (line price weight, yaxis(2))" `"ytitle("Volume", axis(2))"' "t_y2_default"
zp "t_ytitle_axis2_two" "title" "auto" "twoway (scatter mpg weight) (line price weight, yaxis(2))" `"ytitle("a" "b", axis(2))"' "t_y2_default"
zp "t_ytitle_axis2_compound" "title" "auto" "twoway (scatter mpg weight) (line price weight, yaxis(2))" `"ytitle(`"c "q" d"', axis(2))"' "t_y2_default"
zp "t_ytitle_both"      "title" "auto" "twoway (scatter mpg weight) (line price weight, yaxis(2))" `"ytitle("Left") ytitle("Right", axis(2))"' "t_y2_default"
zp "t_ytitle_axis2_size" "title" "auto" "twoway (scatter mpg weight) (line price weight, yaxis(2))" `"ytitle("P2", size(large) axis(2))"' "t_y2_default"
zp "t_ytitle_axis2_empty" "title" "auto" "twoway (scatter mpg weight) (line price weight, yaxis(2))" `"ytitle("", axis(2))"' "t_y2_default"
zp "t_ytitle_axis1"     "title" "auto" "twoway scatter mpg weight" `"ytitle("One", axis(1))"' "t_default"
zp "t_ytitle_axis2_lone" "title" "auto" "twoway scatter mpg weight, yaxis(2)" `"ytitle("Lone", axis(2))"' ""
zp "t_axis3"            "title" "auto" "twoway (scatter mpg weight) (line price weight, yaxis(2))" `"ytitle("T", axis(3))"' "t_y2_default"
zp "t_axis2_no_layer"   "title" "auto" "twoway scatter mpg weight" `"ytitle("T", axis(2))"' "t_default"
zp "t_xtitle_empty"     "title" "auto" "twoway scatter mpg weight" `"xtitle("")"' "t_default"
zp "t_ytitle_empty"     "title" "auto" "twoway scatter mpg weight" `"ytitle("")"' "t_default"
zp "t_both_empty"       "title" "auto" "twoway scatter mpg weight" `"xtitle("") ytitle("")"' "t_default"
zp "t_xtitle_empty_size" "title" "auto" "twoway scatter mpg weight" `"xtitle("", size(large))"' "t_default"
zp "t_hist_ytitle_empty" "title" "auto" "twoway histogram mpg" `"ytitle("")"' "t_hist_default"
zp "t_ytitle_suffix"    "title" "auto" "twoway scatter mpg weight" `"ytitle("extra", suffix)"' "t_default"
zp "t_ytitle_prefix"    "title" "auto" "twoway scatter mpg weight" `"ytitle("pre", prefix)"' "t_default"
zp "t_title_suffix"     "title" "auto" "twoway scatter mpg weight" `"title("T", suffix)"' "t_default"
zp "t_title_two_suffix" "title" "auto" "twoway scatter mpg weight" `"title("A") title("B", suffix)"' "t_default"
zp "t_xtitle_two_suffix" "title" "auto" "twoway scatter mpg weight" `"xtitle("A") xtitle("B", suffix)"' "t_default"
zp "t_colour_refused"   "title" "auto" "twoway scatter mpg weight" `"title("T", colour(red))"' "t_default"
zp "t_style_refused"    "title" "auto" "twoway scatter mpg weight" `"title("T", style(x))"' "t_default"
// WP-29 section 03 (P0.4): title options that give only sub-options,
// trailing and doubled commas, merges, the second axis's default
// title and the colour key's title.  40 probes.
zp "t_ytitle_nt_size" "title" "auto" "twoway scatter mpg weight" `"ytitle(, size(large))"' "t_default"
zp "t_xtitle_nt_color" "title" "auto" "twoway scatter mpg weight" `"xtitle(, color(red))"' "t_default"
zp "t_ytitle_nt_c" "title" "auto" "twoway scatter mpg weight" `"ytitle(, c(red))"' "t_default"
zp "t_ytitle_nt_comma" "title" "auto" "twoway scatter mpg weight" `"ytitle(,)"' "t_default"
zp "t_ytitle_nt_dcomma" "title" "auto" "twoway scatter mpg weight" `"ytitle(,,)"' "t_default"
zp "t_ytitle_trailing" "title" "auto" "twoway scatter mpg weight" `"ytitle(A,)"' "t_default"
zp "t_ytitle_qtrailing" "title" "auto" "twoway scatter mpg weight" `"ytitle("A",)"' "t_default"
zp "t_ytitle_dcomma" "title" "auto" "twoway scatter mpg weight" `"ytitle(A,,)"' "t_default"
zp "t_ytitle_spcomma" "title" "auto" "twoway scatter mpg weight" `"ytitle(A, ,)"' "t_default"
zp "t_ytitle_size_trailing" "title" "auto" "twoway scatter mpg weight" `"ytitle(A, size(large),)"' "t_default"
zp "t_title_nt_comma" "title" "auto" "twoway scatter mpg weight" `"title(,)"' "t_default"
zp "t_title_trailing" "title" "auto" "twoway scatter mpg weight" `"title(A,)"' "t_default"
zp "t_note_qtrailing" "title" "auto" "twoway scatter mpg weight" `"note("N",)"' "t_default"
zp "t_ytitle_nt_orient" "title" "auto" "twoway scatter mpg weight" `"ytitle(, orientation(horizontal))"' "t_default"
zp "t_ytitle_axis1_nt_size" "title" "auto" "twoway scatter mpg weight" `"ytitle(, axis(1) size(large))"' "t_default"
zp "t_ytitle_empty_suffix" "title" "auto" "twoway scatter mpg weight" `"ytitle("", suffix)"' "t_default"
zp "t_ytitle_merge_empty_size" "title" "auto" "twoway scatter mpg weight" `"ytitle("") ytitle(, size(large))"' "t_default"
zp "t_ytitle_merge_size_text" "title" "auto" "twoway scatter mpg weight" `"ytitle(, size(large)) ytitle("A")"' "t_default"
zp "t_ytitle_merge_trailing_size" "title" "auto" "twoway scatter mpg weight" `"ytitle(A,) ytitle(, size(large))"' "t_default"
zp "t_ytitle_merge_comma_size" "title" "auto" "twoway scatter mpg weight" `"ytitle(,) ytitle(, size(large))"' "t_default"
zp "t_by_ytitle_nt_size" "title" "auto" "twoway scatter mpg weight" `"by(foreign) ytitle(, size(large))"' "t_default"
zp "t_ytitle_axis2_nt_size" "title" "auto" "twoway (scatter mpg weight) (line price weight, yaxis(2))" `"ytitle(, axis(2) size(large))"' "t_y2_default"
zp "t_ytitle_axis2_nt" "title" "auto" "twoway (scatter mpg weight) (line price weight, yaxis(2))" `"ytitle(, axis(2))"' "t_y2_default"
zp "t_ytitle_axis2_suffix" "title" "auto" "twoway (scatter mpg weight) (line price weight, yaxis(2))" `"ytitle(, axis(2) suffix)"' "t_y2_default"
zp "t_y2_by" "title" "auto" "twoway (scatter mpg weight) (line price weight, yaxis(2))" `"by(foreign)"' "t_y2_default"
zp "t_y2_by_title" "title" "auto" "twoway (scatter mpg weight) (line price weight, yaxis(2))" `"by(foreign) ytitle(P, axis(2))"' "t_y2_default"
zp "t_x2_default" "title" "auto" "twoway (scatter mpg weight) (scatter mpg length, xaxis(2))" `""' ""
zp "t_y2_hist" "title" "auto" "twoway (scatter mpg weight) (histogram weight, yaxis(2))" `""' ""
zp "t_y2_two_layers" "title" "auto" "twoway (scatter mpg weight) (line price weight, yaxis(2)) (line turn weight, yaxis(2))" `""' ""
zp "t_xtitle_axis2_nt_size" "title" "auto" "twoway (scatter mpg weight) (scatter mpg length, xaxis(2))" `"xtitle(, axis(2) size(large))"' "t_x2_default"
zp "t_ytitle_lone_nt_size" "title" "auto" "twoway scatter mpg weight, yaxis(2)" `"ytitle(, axis(2) size(large))"' ""
zp "t_hist_ytitle_nt_size" "title" "auto" "twoway histogram mpg" `"ytitle(, size(large))"' "t_hist_default"
zp "t_hist_pct_ytitle_nt_size" "title" "auto" "twoway histogram mpg" `"percent ytitle(, size(large))"' "t_hist_default"
zp "t_kdens_ytitle_nt_size" "title" "auto" "twoway kdensity mpg" `"ytitle(, size(large))"' "t_kdens_default"
zp "t_kdens_xtitle_nt_size" "title" "auto" "twoway kdensity mpg" `"xtitle(, size(large))"' "t_kdens_default"
zp "t_z_default" "title" "auto" "twoway scatter mpg weight" `"colorvar(price)"' ""
zp "t_ztitle_nt_size" "title" "auto" "twoway scatter mpg weight" `"colorvar(price) ztitle(, size(large))"' "t_z_default"
zp "t_ztitle_nt_color" "title" "auto" "twoway scatter mpg weight" `"colorvar(price) ztitle(, color(red))"' "t_z_default"
zp "t_ztitle_suffix" "title" "auto" "twoway scatter mpg weight" `"colorvar(price) ztitle("extra", suffix)"' "t_z_default"
zp "t_ztitle_empty" "title" "auto" "twoway scatter mpg weight" `"colorvar(price) ztitle("")"' "t_z_default"

* ---- section 15: legend probes ----
// WP-28 S15 (B5): each legend probe's control is its own legend(off)
// companion, so added_texts are the legend's texts alone (the pairing
// extract_axis_truth.do uses).  44 registrations.
zp "l_two" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "" "l_two__off"
zp "l_two__off" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)" ""
zp "l_order_text" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight) (qfit mpg weight)" `"legend(order(1 "Group 2" 3 "Three"))"' "l_order_text__off"
zp "l_order_text__off" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight) (qfit mpg weight)" "legend(off)" ""
zp "l_order_label" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" `"legend(order(2 1) label(1 "Data"))"' "l_order_label__off"
zp "l_order_label__off" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)" ""
zp "l_label_order" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" `"legend(label(1 "Data") order(2 1))"' "l_label_order__off"
zp "l_label_order__off" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)" ""
zp "l_order_beats_label" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" `"legend(order(1 "O") label(1 "L"))"' "l_order_beats_label__off"
zp "l_order_beats_label__off" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)" ""
zp "l_dash_text" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" `"legend(order(1 - "Note" 2))"' "l_dash_text__off"
zp "l_dash_text__off" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)" ""
zp "l_dash_blank" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" `"legend(order(1 - " " "Note" 2))"' "l_dash_blank__off"
zp "l_dash_blank__off" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)" ""
zp "l_dash_empty" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" `"legend(order(1 - "" 2))"' "l_dash_empty__off"
zp "l_dash_empty__off" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)" ""
zp "l_dash_two_lines" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" `"legend(order(1 - "Line 1" "Line 2" 2))"' "l_dash_two_lines__off"
zp "l_dash_two_lines__off" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)" ""
zp "l_lastlabel_pos" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" `"legend(order(2 1) lastlabel(2 "L"))"' "l_lastlabel_pos__off"
zp "l_lastlabel_pos__off" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)" ""
zp "l_lastlabel_all" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" `"legend(order(2 "Y" 1) label(2 "X") lastlabel(2 "L"))"' "l_lastlabel_all__off"
zp "l_lastlabel_all__off" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)" ""
zp "l_lastlabel_dash" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" `"legend(order(1 - "Note" 2) lastlabel(3 "L"))"' "l_lastlabel_dash__off"
zp "l_lastlabel_dash__off" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)" ""
zp "l_lastlabel_two" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" `"legend(lastlabel(1 "A") lastlabel(2 "B"))"' "l_lastlabel_two__off"
zp "l_lastlabel_two__off" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)" ""
zp "l_lastlabel_repeat" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" `"legend(lastlabel(1 "A")) legend(lastlabel(2 "B"))"' "l_lastlabel_repeat__off"
zp "l_lastlabel_repeat__off" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)" ""
zp "l_label_two_lines" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" `"legend(label(1 "A" "B"))"' "l_label_two_lines__off"
zp "l_label_two_lines__off" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)" ""
zp "l_order_repeat" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" `"legend(order(1 2 1))"' "l_order_repeat__off"
zp "l_order_repeat__off" "legend" "auto" "twoway (scatter mpg weight) (lfit mpg weight)" "legend(off)" ""
zp "l_ci_default" "legend" "auto" "twoway (scatter mpg weight) (lfitci mpg weight) (scatter price weight)" "" "l_ci_default__off"
zp "l_ci_default__off" "legend" "auto" "twoway (scatter mpg weight) (lfitci mpg weight) (scatter price weight)" "legend(off)" ""
zp "l_ci_order_last" "legend" "auto" "twoway (scatter mpg weight) (lfitci mpg weight) (scatter price weight)" `"legend(order(4 1))"' "l_ci_order_last__off"
zp "l_ci_order_last__off" "legend" "auto" "twoway (scatter mpg weight) (lfitci mpg weight) (scatter price weight)" "legend(off)" ""
zp "l_ci_order_band" "legend" "auto" "twoway (scatter mpg weight) (lfitci mpg weight) (scatter price weight)" `"legend(order(2 3))"' "l_ci_order_band__off"
zp "l_ci_order_band__off" "legend" "auto" "twoway (scatter mpg weight) (lfitci mpg weight) (scatter price weight)" "legend(off)" ""
zp "l_one_dash" "legend" "auto" "twoway scatter mpg weight" `"legend(order(1 - "Only"))"' "l_one_dash__off"
zp "l_one_dash__off" "legend" "auto" "twoway scatter mpg weight" "legend(off)" ""

// ===========================================================================
// Export loop (extract_axis_truth.do:392-428's shape, SVG only, no .gph).
// ===========================================================================
tempname zarfh
file open `zarfh' using "${ZA_REC}", write text replace

local N = $ZA_N
local curds ""
forvalues i = 1/`N' {
    local id  "${ZA_ID_`i'}"
    local grp "${ZA_GRP_`i'}"
    local ds  "${ZA_DS_`i'}"
    local cmd `"${ZA_CMD_`i'}"'
    local opt `"${ZA_OPT_`i'}"'
    local ctl "${ZA_CTL_`i'}"

    if "`ds'" != "`curds'" {
        sysuse `ds', clear
        local curds "`ds'"
    }

    if `"`opt'"' == "" {
        local full  `"`cmd', name(zqt, replace)"'
        local shown `"`cmd'"'
    }
    else {
        _zt_has_top_comma `"`cmd'"'
        if r(found) {
            local full  `"`cmd' `opt' name(zqt, replace)"'
            local shown `"`cmd' `opt'"'
        }
        else {
            local full  `"`cmd', `opt' name(zqt, replace)"'
            local shown `"`cmd', `opt'"'
        }
    }

    local svg "${ZA_WORK}/`id'.svg"
    capture erase "`svg'"

    capture graph drop zqt
    capture noisily `full'
    local rc = _rc
    local rcx = .
    if `rc' == 0 {
        capture graph export "`svg'", name(zqt) replace
        local rcx = _rc
    }
    capture graph drop zqt
    file write `zarfh' `"PROBE|`id'|`grp'|`ds'|`rc'|`rcx'|`svg'|`ctl'|`shown'"' _n
    display as text "probe `id' rc=`rc' svg_rc=`rcx'"
}
file close `zarfh'
display as text "records written to ${ZA_REC}"

// ===========================================================================
// Analysis + JSON emission.  No callbacks into Stata from here on.
//
// REMINDER: no backtick may appear literally in this block.
// ===========================================================================
python:
import collections
import json
import os
import sys
from sfi import Macro

ZA_REPO = Macro.getGlobal("ZA_REPO")
sys.path.insert(0, os.path.join(ZA_REPO, "scripts"))
import svg_truth

OUT = Macro.getGlobal("ZA_OUT")
REC = Macro.getGlobal("ZA_REC")
DASH_COMMIT = Macro.getLocal("dash_commit")

probes_raw = {}
with open(REC, encoding="utf-8") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line or not line.startswith("PROBE|"):
            continue
        _, pid, grp, ds, rc, rcx, svgpath, ctl, shown = line.split("|", 8)
        probes_raw[pid] = {
            "group": grp, "dataset": ds, "rc": int(rc),
            "rcx": (int(rcx) if rcx != "." else None),
            "svg": svgpath, "control": ctl, "command": shown,
        }

# ---- each probe's own svg_texts()/svg_fills(), kept as full entries until
#      every probe's lists are built (section 15's legend group needs the
#      x/y positions to sort by; do not project to bare text earlier) ----
entries_cache, fills_cache = {}, {}
for pid, info in probes_raw.items():
    ok = info["rc"] == 0 and info["rcx"] == 0
    entries_cache[pid] = svg_truth.svg_texts(info["svg"]) if ok else []
    fills_cache[pid] = set(svg_truth.svg_fills(info["svg"]).keys()) if ok \
        else set()

probes_out = {}
for pid, info in probes_raw.items():
    entries = entries_cache[pid]
    # normalise a run of Stata's U+00A0 to an ordinary space (already done
    # by svg_truth.normalise_text; re-asserted here, once, for the
    # extracted text -- svg_truth is the one and only place this is done).
    texts = [e["text"] for e in entries]
    text_sizes = {}
    for e in entries:
        if e["size"] is not None:
            text_sizes[e["text"]] = e["size"]
    fills = sorted(fills_cache[pid])

    ctl = info["control"]
    ctl_texts = [e["text"] for e in entries_cache.get(ctl, [])] if ctl else []
    ctl_fills = fills_cache.get(ctl, set()) if ctl else set()

    probe_counts = collections.Counter(texts)
    ctl_counts = collections.Counter(ctl_texts)
    added_counts = probe_counts - ctl_counts
    removed_counts = ctl_counts - probe_counts

    added_texts, seen_added = [], collections.Counter()
    for t in texts:
        if seen_added[t] < added_counts.get(t, 0):
            added_texts.append(t)
            seen_added[t] += 1
    removed_texts, seen_removed = [], collections.Counter()
    for t in ctl_texts:
        if seen_removed[t] < removed_counts.get(t, 0):
            removed_texts.append(t)
            seen_removed[t] += 1
    added_fills = sorted(fills_cache[pid] - ctl_fills)

    rec_extra = {}
    if info["group"] == "legend":
        # WP-28 S15: the added entries, as whole dicts, ordered top to
        # bottom then left to right, and only then projected to text.
        seen_e, added_e = collections.Counter(), []
        for e in entries:
            if seen_e[e["text"]] < added_counts.get(e["text"], 0):
                added_e.append(e)
                seen_e[e["text"]] += 1
        added_e.sort(key=lambda e: (float(e.get("y") or 0.0),
                                    float(e.get("x") or 0.0)))
        rec_extra["keys_in_drawn_order"] = [e["text"] for e in added_e]

    probes_out[pid] = {
        "group": info["group"],
        "command": info["command"],
        "rc": info["rc"] if info["rc"] != 0 else (info["rcx"] or 0),
        "control": ctl,
        "texts": texts,
        "fills": fills,
        "added_texts": added_texts,
        "removed_texts": removed_texts,
        "added_fills": added_fills,
        "text_sizes": text_sizes,
        # WP-29 S03 (D-03b): every text with its size, fill and rotation,
        # in document order -- the maps above keyed by text lose a text
        # drawn twice (b1 draws "Price" rotated at 157.44 and as a key).
        "text_records": [[e["text"], e["size"], e["fill"], e["rotate"]]
                         for e in entries],
    }
    probes_out[pid].update(rec_extra)

doc = {
    "_meta": {
        "stata_version": Macro.getGlobal("ZA_SVER"),
        "born_date": Macro.getGlobal("ZA_BORN"),
        "extracted": Macro.getGlobal("ZA_DATE"),
        "dash_commit": DASH_COMMIT,
        "scheme_in_force": Macro.getGlobal("ZA_SCHEME"),
        "method": ("Each probe's twoway command (plus the option under "
                   "test, if any) is exported to SVG and read through "
                   "scripts/svg_truth.py; added_texts/removed_texts are "
                   "the probe's <text> elements minus its control probe's, "
                   "by multiset (collections.Counter), kept in the "
                   "probe's own document order; added_fills is a set "
                   "difference of svg_fills() colours."),
    },
    "probes": probes_out,
}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2, sort_keys=True)
    fh.write("\n")
print("WROTE %s" % OUT)
print("probes=%d" % len(probes_out))
end

display as text "extract_text_truth.do: done"
