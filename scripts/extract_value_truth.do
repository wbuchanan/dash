*! extract_value_truth.do -- twoway's own verdict on option VALUES, written
*! to test/fixtures/value_truth.json (read by test/test_option_validation.py;
*! the rules it grounds are dash.ado's _dash_option_rules).
*!
*! twoway: one `capture noisily <command>' per probe (sysuse auto, set
*! graphics off, drawn), its rc and its output's non-blank lines, each with
*! its runs of blanks made one, joined by a blank (the message).  formats: `confirm numeric format <value>' per probe;
*! F90 and F91 `display string(r(mean), <value>)' after `summarize mpg'.
*! vocab: the names `graph query <style>' lists, sorted.
*! A new probe is a new row of the table below (scripts/merge_value_truth.py
*! merges probes measured by scripts/extract_value_truth_additions.do into an
*! existing fixture without remeasuring it).
*!
*! Run (never the GUI; the slot wrapper of scripts/stata_slot.sh):
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_value_truth.do
*! Probe logs go to c(tmpdir).

clear all
set more off
set linesize 255

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zv_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zv_bad' {
    display as error "extract_value_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zv_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zv_rc' | _rc {
    local _zv_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_value_truth.do: `_zv_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZV_REPO "`repo'"
global ZV_SVER = c(stata_version)
global ZV_BORN "`c(born_date)'"
global ZV_DATE "`c(current_date)'"
tempfile gh
shell git -C "`repo'" rev-parse HEAD > "`gh'"
tempname fh
file open `fh' using "`gh'", read text
file read `fh' zv_commit
file close `fh'
global ZV_COMMIT "`zv_commit'"
local work "`c(tmpdir)'dash_value_truth"
capture mkdir "`work'"
global ZV_WORK "`work'"
global ZV_IDS ""
global ZV_FIDS ""
global ZV_VOCAB "colorstyle symbolstyle linepatternstyle markersizestyle linewidthstyle textsizestyle relativesizestyle markerstyle linestyle gsizestyle"

set graphics off
sysuse auto, clear
capture log close _all

capture program drop _vt_probe
program define _vt_probe
    args id option value cmd
    quietly log using `"${ZV_WORK}/probe_`id'.log"', text replace name(vt)
    capture noisily `cmd'
    local rc = _rc
    quietly log close vt
    tempname fh
    file open `fh' using `"${ZV_WORK}/probe_`id'.rc"', write text replace
    file write `fh' "`rc'" _n
    file write `fh' `"`option'"' _n `"`value'"' _n `"`cmd'"' _n
    file close `fh'
    global ZV_IDS "${ZV_IDS} `id'"
end

capture program drop _vt_fmt
program define _vt_fmt
    args id value kind
    quietly log using `"${ZV_WORK}/fmt_`id'.log"', text replace name(vt)
    if "`kind'" == "string" {
        quietly summarize mpg
        capture noisily display string(r(mean), `"`value'"')
    }
    else capture noisily confirm numeric format `value'
    local rc = _rc
    quietly log close vt
    tempname fh
    file open `fh' using `"${ZV_WORK}/fmt_`id'.rc"', write text replace
    file write `fh' "`rc'" _n `"`value'"' _n
    file close `fh'
    global ZV_FIDS "${ZV_FIDS} `id'"
end

* The twoway probes: id, option, value, command.
_vt_probe mcolor_1 `"mcolor"' `"notacolour"' `"twoway scatter mpg weight, mcolor(notacolour)"'
_vt_probe mcolor_2 `"mcolor"' `"red*0.5"' `"twoway scatter mpg weight, mcolor(red*0.5)"'
_vt_probe mcolor_3 `"mcolor"' `"red%50"' `"twoway scatter mpg weight, mcolor(red%50)"'
_vt_probe mcolor_4 `"mcolor"' `"255 0 0"' `"twoway scatter mpg weight, mcolor(255 0 0)"'
_vt_probe mcolor_5 `"mcolor"' `"255,0,0"' `"twoway scatter mpg weight, mcolor(255,0,0)"'
_vt_probe mcolor_6 `"mcolor"' `"#ff0000"' `"twoway scatter mpg weight, mcolor(#ff0000)"'
_vt_probe mcolor_7 `"mcolor"' `"#f00"' `"twoway scatter mpg weight, mcolor(#f00)"'
_vt_probe mcolor_8 `"mcolor"' `"300 0 0"' `"twoway scatter mpg weight, mcolor(300 0 0)"'
_vt_probe mcolor_9 `"mcolor"' `"none"' `"twoway scatter mpg weight, mcolor(none)"'
_vt_probe mcolor_10 `"mcolor"' `"gs10"' `"twoway scatter mpg weight, mcolor(gs10)"'
_vt_probe mcolor_11 `"mcolor"' `"eltblue"' `"twoway scatter mpg weight, mcolor(eltblue)"'
_vt_probe mcolor_12 `"mcolor"' `"dknavy"' `"twoway scatter mpg weight, mcolor(dknavy)"'
_vt_probe mcolor_13 `"mcolor"' `"grey"' `"twoway scatter mpg weight, mcolor(grey)"'
_vt_probe mcolor_14 `"mcolor"' `"red 50"' `"twoway scatter mpg weight, mcolor(red 50)"'
_vt_probe mcolor_15 `"mcolor"' `"1 2 3 4"' `"twoway scatter mpg weight, mcolor(1 2 3 4)"'
_vt_probe mcolor_16 `"mcolor"' `"red*abc"' `"twoway scatter mpg weight, mcolor(red*abc)"'
_vt_probe msymbol_1 `"msymbol"' `"nonsense"' `"twoway scatter mpg weight, msymbol(nonsense)"'
_vt_probe msymbol_2 `"msymbol"' `"Oh"' `"twoway scatter mpg weight, msymbol(Oh)"'
_vt_probe msymbol_3 `"msymbol"' `"circle_hollow"' `"twoway scatter mpg weight, msymbol(circle_hollow)"'
_vt_probe msymbol_4 `"msymbol"' `"i"' `"twoway scatter mpg weight, msymbol(i)"'
_vt_probe msymbol_5 `"msymbol"' `"none"' `"twoway scatter mpg weight, msymbol(none)"'
_vt_probe msymbol_6 `"msymbol"' `"O"' `"twoway scatter mpg weight, msymbol(O)"'
_vt_probe msymbol_7 `"msymbol"' `"smcircle"' `"twoway scatter mpg weight, msymbol(smcircle)"'
_vt_probe msymbol_8 `"msymbol"' `"+"' `"twoway scatter mpg weight, msymbol(+)"'
_vt_probe msize_1 `"msize"' `"huge"' `"twoway scatter mpg weight, msize(huge)"'
_vt_probe msize_2 `"msize"' `"abc"' `"twoway scatter mpg weight, msize(abc)"'
_vt_probe msize_3 `"msize"' `"2"' `"twoway scatter mpg weight, msize(2)"'
_vt_probe msize_4 `"msize"' `"*2"' `"twoway scatter mpg weight, msize(*2)"'
_vt_probe msize_5 `"msize"' `"-1"' `"twoway scatter mpg weight, msize(-1)"'
_vt_probe msize_6 `"msize"' `"0"' `"twoway scatter mpg weight, msize(0)"'
_vt_probe msize_7 `"msize"' `"1e308"' `"twoway scatter mpg weight, msize(1e308)"'
_vt_probe msize_8 `"msize"' `"vhuge"' `"twoway scatter mpg weight, msize(vhuge)"'
_vt_probe msize_9 `"msize"' `"2.5"' `"twoway scatter mpg weight, msize(2.5)"'
_vt_probe mlabsize_1 `"mlabsize"' `"abc"' `"twoway scatter mpg weight, mlabel(make) mlabsize(abc)"'
_vt_probe mlabsize_2 `"mlabsize"' `"*1.5"' `"twoway scatter mpg weight, mlabel(make) mlabsize(*1.5)"'
_vt_probe mlabsize_3 `"mlabsize"' `"small"' `"twoway scatter mpg weight, mlabel(make) mlabsize(small)"'
_vt_probe mlabsize_4 `"mlabsize"' `"3"' `"twoway scatter mpg weight, mlabel(make) mlabsize(3)"'
_vt_probe msangle_1 `"msangle"' `"abc"' `"twoway scatter mpg weight, msangle(abc)"'
_vt_probe msangle_2 `"msangle"' `"45"' `"twoway scatter mpg weight, msangle(45)"'
_vt_probe msangle_3 `"msangle"' `"-30"' `"twoway scatter mpg weight, msangle(-30)"'
_vt_probe msangle_4 `"msangle"' `"400"' `"twoway scatter mpg weight, msangle(400)"'
_vt_probe msangle_5 `"msangle"' `"1e308"' `"twoway scatter mpg weight, msangle(1e308)"'
_vt_probe jitter_1 `"jitter"' `"-3"' `"twoway scatter mpg weight, jitter(-3)"'
_vt_probe jitter_2 `"jitter"' `"31"' `"twoway scatter mpg weight, jitter(31)"'
_vt_probe jitter_3 `"jitter"' `"30"' `"twoway scatter mpg weight, jitter(30)"'
_vt_probe jitter_4 `"jitter"' `"abc"' `"twoway scatter mpg weight, jitter(abc)"'
_vt_probe jitter_5 `"jitter"' `"2.5"' `"twoway scatter mpg weight, jitter(2.5)"'
_vt_probe jitter_6 `"jitter"' `"0"' `"twoway scatter mpg weight, jitter(0)"'
_vt_probe jitter_7 `"jitter"' `"1e308"' `"twoway scatter mpg weight, jitter(1e308)"'
_vt_probe jitterseed_1 `"jitterseed"' `"abc"' `"twoway scatter mpg weight, jitter(5) jitterseed(abc)"'
_vt_probe jitterseed_2 `"jitterseed"' `"-1"' `"twoway scatter mpg weight, jitter(5) jitterseed(-1)"'
_vt_probe jitterseed_3 `"jitterseed"' `"2.5"' `"twoway scatter mpg weight, jitter(5) jitterseed(2.5)"'
_vt_probe jitterseed_4 `"jitterseed"' `"0"' `"twoway scatter mpg weight, jitter(5) jitterseed(0)"'
_vt_probe jitterseed_5 `"jitterseed"' `"12345"' `"twoway scatter mpg weight, jitter(5) jitterseed(12345)"'
_vt_probe jitterseed_6 `"jitterseed"' `"1e12"' `"twoway scatter mpg weight, jitter(5) jitterseed(1e12)"'
_vt_probe mlabposition_1 `"mlabposition"' `"13"' `"twoway scatter mpg weight, mlabel(make) mlabposition(13)"'
_vt_probe mlabposition_2 `"mlabposition"' `"99"' `"twoway scatter mpg weight, mlabel(make) mlabposition(99)"'
_vt_probe mlabposition_3 `"mlabposition"' `"abc"' `"twoway scatter mpg weight, mlabel(make) mlabposition(abc)"'
_vt_probe mlabposition_4 `"mlabposition"' `"-1"' `"twoway scatter mpg weight, mlabel(make) mlabposition(-1)"'
_vt_probe mlabposition_5 `"mlabposition"' `"2.5"' `"twoway scatter mpg weight, mlabel(make) mlabposition(2.5)"'
_vt_probe mlabposition_6 `"mlabposition"' `"0"' `"twoway scatter mpg weight, mlabel(make) mlabposition(0)"'
_vt_probe mlabposition_7 `"mlabposition"' `"12"' `"twoway scatter mpg weight, mlabel(make) mlabposition(12)"'
_vt_probe mlabel_1 `"mlabel"' `"nosuchvar"' `"twoway scatter mpg weight, mlabel(nosuchvar)"'
_vt_probe mlabel_2 `"mlabel"' `"ma"' `"twoway scatter mpg weight, mlabel(ma)"'
_vt_probe mlabel_3 `"mlabel"' `"make"' `"twoway scatter mpg weight, mlabel(make)"'
_vt_probe mlabel_4 `"mlabel"' `"make foreign"' `"twoway scatter mpg weight, mlabel(make foreign)"'
_vt_probe mlabgap_1 `"mlabgap"' `"abc"' `"twoway scatter mpg weight, mlabel(make) mlabgap(abc)"'
_vt_probe mlabgap_2 `"mlabgap"' `"*2"' `"twoway scatter mpg weight, mlabel(make) mlabgap(*2)"'
_vt_probe mlabgap_3 `"mlabgap"' `"2"' `"twoway scatter mpg weight, mlabel(make) mlabgap(2)"'
_vt_probe mlabgap_4 `"mlabgap"' `"-1"' `"twoway scatter mpg weight, mlabel(make) mlabgap(-1)"'
_vt_probe mlabcolor_1 `"mlabcolor"' `"notacolour"' `"twoway scatter mpg weight, mlabel(make) mlabcolor(notacolour)"'
_vt_probe mlabcolor_2 `"mlabcolor"' `"red"' `"twoway scatter mpg weight, mlabel(make) mlabcolor(red)"'
_vt_probe mlwidth_1 `"mlwidth"' `"abc"' `"twoway scatter mpg weight, mlwidth(abc)"'
_vt_probe mlwidth_2 `"mlwidth"' `"vthin"' `"twoway scatter mpg weight, mlwidth(vthin)"'
_vt_probe mlwidth_3 `"mlwidth"' `"*2"' `"twoway scatter mpg weight, mlwidth(*2)"'
_vt_probe mlwidth_4 `"mlwidth"' `"-1"' `"twoway scatter mpg weight, mlwidth(-1)"'
_vt_probe mlwidth_5 `"mlwidth"' `"2"' `"twoway scatter mpg weight, mlwidth(2)"'
_vt_probe mlcolor_1 `"mlcolor"' `"notacolour"' `"twoway scatter mpg weight, mlcolor(notacolour)"'
_vt_probe mlcolor_2 `"mlcolor"' `"navy"' `"twoway scatter mpg weight, mlcolor(navy)"'
_vt_probe mfcolor_1 `"mfcolor"' `"notacolour"' `"twoway scatter mpg weight, mfcolor(notacolour)"'
_vt_probe mfcolor_2 `"mfcolor"' `"none"' `"twoway scatter mpg weight, mfcolor(none)"'
_vt_probe yaxis_1 `"yaxis"' `"3"' `"twoway scatter mpg weight, yaxis(3)"'
_vt_probe yaxis_2 `"yaxis"' `"0"' `"twoway scatter mpg weight, yaxis(0)"'
_vt_probe yaxis_3 `"yaxis"' `"abc"' `"twoway scatter mpg weight, yaxis(abc)"'
_vt_probe yaxis_4 `"yaxis"' `"2"' `"twoway scatter mpg weight, yaxis(2)"'
_vt_probe yaxis_5 `"yaxis"' `"9"' `"twoway scatter mpg weight, yaxis(9)"'
_vt_probe yaxis_6 `"yaxis"' `"10"' `"twoway scatter mpg weight, yaxis(10)"'
_vt_probe yaxis_7 `"yaxis"' `"1.5"' `"twoway scatter mpg weight, yaxis(1.5)"'
_vt_probe xaxis_1 `"xaxis"' `"3"' `"twoway scatter mpg weight, xaxis(3)"'
_vt_probe xaxis_2 `"xaxis"' `"2"' `"twoway scatter mpg weight, xaxis(2)"'
_vt_probe lwidth_1 `"lwidth"' `"abc"' `"twoway line mpg weight, lwidth(abc)"'
_vt_probe lwidth_2 `"lwidth"' `"*2"' `"twoway line mpg weight, lwidth(*2)"'
_vt_probe lwidth_3 `"lwidth"' `"-1"' `"twoway line mpg weight, lwidth(-1)"'
_vt_probe lwidth_4 `"lwidth"' `"vvvthick"' `"twoway line mpg weight, lwidth(vvvthick)"'
_vt_probe lwidth_5 `"lwidth"' `"2"' `"twoway line mpg weight, lwidth(2)"'
_vt_probe lwidth_6 `"lwidth"' `"0"' `"twoway line mpg weight, lwidth(0)"'
_vt_probe lwidth_7 `"lwidth"' `"none"' `"twoway line mpg weight, lwidth(none)"'
_vt_probe lpattern_1 `"lpattern"' `"bogus"' `"twoway line mpg weight, lpattern(bogus)"'
_vt_probe lpattern_2 `"lpattern"' `"-."' `"twoway line mpg weight, lpattern(-.)"'
_vt_probe lpattern_3 `"lpattern"' `"l_"' `"twoway line mpg weight, lpattern(l_)"'
_vt_probe lpattern_4 `"lpattern"' `"solid"' `"twoway line mpg weight, lpattern(solid)"'
_vt_probe lpattern_5 `"lpattern"' `"blank"' `"twoway line mpg weight, lpattern(blank)"'
_vt_probe lpattern_6 `"lpattern"' `"- -"' `"twoway line mpg weight, lpattern(- -)"'
_vt_probe lpattern_7 `"lpattern"' `"dash_dot"' `"twoway line mpg weight, lpattern(dash_dot)"'
_vt_probe lpattern_8 `"lpattern"' `"shortdash"' `"twoway line mpg weight, lpattern(shortdash)"'
_vt_probe lcolor_1 `"lcolor"' `"notacolour"' `"twoway line mpg weight, lcolor(notacolour)"'
_vt_probe lcolor_2 `"lcolor"' `"red"' `"twoway line mpg weight, lcolor(red)"'
_vt_probe connect_1 `"connect"' `"bogus"' `"twoway line mpg weight, connect(bogus)"'
_vt_probe connect_2 `"connect"' `"direct"' `"twoway line mpg weight, connect(direct)"'
_vt_probe connect_3 `"connect"' `"stairstep"' `"twoway line mpg weight, connect(stairstep)"'
_vt_probe fcolor_1 `"fcolor"' `"notacolour"' `"twoway area mpg weight, fcolor(notacolour)"'
_vt_probe fcolor_2 `"fcolor"' `"red"' `"twoway area mpg weight, fcolor(red)"'
_vt_probe fintensity_1 `"fintensity"' `"abc"' `"twoway area mpg weight, fintensity(abc)"'
_vt_probe fintensity_2 `"fintensity"' `"150"' `"twoway area mpg weight, fintensity(150)"'
_vt_probe fintensity_3 `"fintensity"' `"-1"' `"twoway area mpg weight, fintensity(-1)"'
_vt_probe fintensity_4 `"fintensity"' `"inten50"' `"twoway area mpg weight, fintensity(inten50)"'
_vt_probe fintensity_5 `"fintensity"' `"50"' `"twoway area mpg weight, fintensity(50)"'
_vt_probe fintensity_6 `"fintensity"' `"0"' `"twoway area mpg weight, fintensity(0)"'
_vt_probe fintensity_7 `"fintensity"' `"100"' `"twoway area mpg weight, fintensity(100)"'
_vt_probe fintensity_8 `"fintensity"' `"*2"' `"twoway area mpg weight, fintensity(*2)"'
_vt_probe base_1 `"base"' `"abc"' `"twoway area mpg weight, base(abc)"'
_vt_probe base_2 `"base"' `"5"' `"twoway area mpg weight, base(5)"'
_vt_probe base_3 `"base"' `"-5"' `"twoway area mpg weight, base(-5)"'
_vt_probe barwidth_1 `"barwidth"' `"abc"' `"twoway bar mpg foreign, barwidth(abc)"'
_vt_probe barwidth_2 `"barwidth"' `"-1"' `"twoway bar mpg foreign, barwidth(-1)"'
_vt_probe barwidth_3 `"barwidth"' `"0"' `"twoway bar mpg foreign, barwidth(0)"'
_vt_probe barwidth_4 `"barwidth"' `"0.5"' `"twoway bar mpg foreign, barwidth(0.5)"'
_vt_probe barwidth_5 `"barwidth"' `"2"' `"twoway bar mpg foreign, barwidth(2)"'
_vt_probe blcolor_1 `"blcolor"' `"notacolour"' `"twoway bar mpg foreign, blcolor(notacolour)"'
_vt_probe bfcolor_1 `"bfcolor"' `"notacolour"' `"twoway bar mpg foreign, bfcolor(notacolour)"'
_vt_probe level_1 `"level"' `"abc"' `"twoway lfitci mpg weight, level(abc)"'
_vt_probe level_2 `"level"' `"150"' `"twoway lfitci mpg weight, level(150)"'
_vt_probe level_3 `"level"' `"0"' `"twoway lfitci mpg weight, level(0)"'
_vt_probe level_4 `"level"' `"100"' `"twoway lfitci mpg weight, level(100)"'
_vt_probe level_5 `"level"' `"95"' `"twoway lfitci mpg weight, level(95)"'
_vt_probe level_6 `"level"' `"99.9"' `"twoway lfitci mpg weight, level(99.9)"'
_vt_probe level_7 `"level"' `"10.5"' `"twoway lfitci mpg weight, level(10.5)"'
_vt_probe level_8 `"level"' `"-5"' `"twoway lfitci mpg weight, level(-5)"'
_vt_probe degree_1 `"degree"' `"x"' `"twoway lpoly mpg weight, degree(x)"'
_vt_probe degree_2 `"degree"' `"-1"' `"twoway lpoly mpg weight, degree(-1)"'
_vt_probe degree_3 `"degree"' `"1.5"' `"twoway lpoly mpg weight, degree(1.5)"'
_vt_probe degree_4 `"degree"' `"5"' `"twoway lpoly mpg weight, degree(5)"'
_vt_probe degree_5 `"degree"' `"0"' `"twoway lpoly mpg weight, degree(0)"'
_vt_probe degree_6 `"degree"' `"3"' `"twoway lpoly mpg weight, degree(3)"'
_vt_probe lpoly_bwidth_1 `"bwidth"' `"-1"' `"twoway lpoly mpg weight, bwidth(-1)"'
_vt_probe lpoly_bwidth_2 `"bwidth"' `"0"' `"twoway lpoly mpg weight, bwidth(0)"'
_vt_probe lpoly_bwidth_3 `"bwidth"' `"abc"' `"twoway lpoly mpg weight, bwidth(abc)"'
_vt_probe lpoly_bwidth_4 `"bwidth"' `"400"' `"twoway lpoly mpg weight, bwidth(400)"'
_vt_probe lpoly_bwidth_5 `"bwidth"' `"0.5"' `"twoway lpoly mpg weight, bwidth(0.5)"'
_vt_probe lpoly_kernel_1 `"kernel"' `"bogus"' `"twoway lpoly mpg weight, kernel(bogus)"'
_vt_probe lpoly_kernel_2 `"kernel"' `"epan2"' `"twoway lpoly mpg weight, kernel(epan2)"'
_vt_probe lpoly_kernel_3 `"kernel"' `"epanechnikov"' `"twoway lpoly mpg weight, kernel(epanechnikov)"'
_vt_probe lpoly_kernel_4 `"kernel"' `"gaussian"' `"twoway lpoly mpg weight, kernel(gaussian)"'
_vt_probe lpoly_kernel_5 `"kernel"' `"rectangle"' `"twoway lpoly mpg weight, kernel(rectangle)"'
_vt_probe lpoly_kernel_6 `"kernel"' `"triangle"' `"twoway lpoly mpg weight, kernel(triangle)"'
_vt_probe lpoly_kernel_7 `"kernel"' `"biweight"' `"twoway lpoly mpg weight, kernel(biweight)"'
_vt_probe lpoly_kernel_8 `"kernel"' `"cosine"' `"twoway lpoly mpg weight, kernel(cosine)"'
_vt_probe lpoly_kernel_9 `"kernel"' `"parzen"' `"twoway lpoly mpg weight, kernel(parzen)"'
_vt_probe lpoly_n_1 `"n"' `"-5"' `"twoway lpoly mpg weight, n(-5)"'
_vt_probe lpoly_n_2 `"n"' `"1"' `"twoway lpoly mpg weight, n(1)"'
_vt_probe lpoly_n_3 `"n"' `"2.5"' `"twoway lpoly mpg weight, n(2.5)"'
_vt_probe lpoly_n_4 `"n"' `"abc"' `"twoway lpoly mpg weight, n(abc)"'
_vt_probe lpoly_n_5 `"n"' `"50000"' `"twoway lpoly mpg weight, n(50000)"'
_vt_probe lpoly_n_6 `"n"' `"2"' `"twoway lpoly mpg weight, n(2)"'
_vt_probe lpoly_n_7 `"n"' `"0"' `"twoway lpoly mpg weight, n(0)"'
_vt_probe lowess_bwidth_1 `"bwidth"' `"5"' `"twoway lowess mpg weight, bwidth(5)"'
_vt_probe lowess_bwidth_2 `"bwidth"' `"0.8"' `"twoway lowess mpg weight, bwidth(0.8)"'
_vt_probe lowess_bwidth_3 `"bwidth"' `"abc"' `"twoway lowess mpg weight, bwidth(abc)"'
_vt_probe lowess_bwidth_4 `"bwidth"' `"0"' `"twoway lowess mpg weight, bwidth(0)"'
_vt_probe lowess_bwidth_5 `"bwidth"' `"1"' `"twoway lowess mpg weight, bwidth(1)"'
_vt_probe lowess_bwidth_6 `"bwidth"' `"-0.5"' `"twoway lowess mpg weight, bwidth(-0.5)"'
_vt_probe kdensity_kernel_1 `"kernel"' `"bogus"' `"twoway kdensity mpg, kernel(bogus)"'
_vt_probe kdensity_n_1 `"n"' `"-5"' `"twoway kdensity mpg, n(-5)"'
_vt_probe kdensity_n_2 `"n"' `"1"' `"twoway kdensity mpg, n(1)"'
_vt_probe kdensity_bwidth_1 `"bwidth"' `"-1"' `"twoway kdensity mpg, bwidth(-1)"'
_vt_probe kdensity_bwidth_2 `"bwidth"' `"0"' `"twoway kdensity mpg, bwidth(0)"'
_vt_probe kdensity_bwidth_3 `"bwidth"' `"abc"' `"twoway kdensity mpg, bwidth(abc)"'
_vt_probe kdensity_range_1 `"range"' `"abc"' `"twoway kdensity mpg, range(abc)"'
_vt_probe kdensity_range_2 `"range"' `"10 40"' `"twoway kdensity mpg, range(10 40)"'
_vt_probe kdensity_range_3 `"range"' `"40 10"' `"twoway kdensity mpg, range(40 10)"'
_vt_probe kdensity_range_4 `"range"' `"10"' `"twoway kdensity mpg, range(10)"'
_vt_probe histogram_bin_1 `"bin"' `"0"' `"twoway histogram mpg, bin(0)"'
_vt_probe histogram_bin_2 `"bin"' `"abc"' `"twoway histogram mpg, bin(abc)"'
_vt_probe histogram_bin_3 `"bin"' `"2.5"' `"twoway histogram mpg, bin(2.5)"'
_vt_probe histogram_bin_4 `"bin"' `"5000"' `"twoway histogram mpg, bin(5000)"'
_vt_probe histogram_bin_5 `"bin"' `"1"' `"twoway histogram mpg, bin(1)"'
_vt_probe histogram_bin_6 `"bin"' `"-3"' `"twoway histogram mpg, bin(-3)"'
_vt_probe histogram_width_1 `"width"' `"-1"' `"twoway histogram mpg, width(-1)"'
_vt_probe histogram_width_2 `"width"' `"abc"' `"twoway histogram mpg, width(abc)"'
_vt_probe histogram_width_3 `"width"' `"0"' `"twoway histogram mpg, width(0)"'
_vt_probe histogram_width_4 `"width"' `"2"' `"twoway histogram mpg, width(2)"'
_vt_probe histogram_start_1 `"start"' `"abc"' `"twoway histogram mpg, start(abc)"'
_vt_probe histogram_start_2 `"start"' `"5"' `"twoway histogram mpg, start(5)"'
_vt_probe histogram_start_3 `"start"' `"100"' `"twoway histogram mpg, start(100)"'
_vt_probe histogram_freqpct_1 `"frequency percent"' `"frequency percent"' `"twoway histogram mpg, frequency percent"'
_vt_probe mband_bands_1 `"bands"' `"0"' `"twoway mband mpg weight, bands(0)"'
_vt_probe mband_bands_2 `"bands"' `"abc"' `"twoway mband mpg weight, bands(abc)"'
_vt_probe mband_bands_3 `"bands"' `"2.5"' `"twoway mband mpg weight, bands(2.5)"'
_vt_probe mband_bands_4 `"bands"' `"2000"' `"twoway mband mpg weight, bands(2000)"'
_vt_probe mband_bands_5 `"bands"' `"1"' `"twoway mband mpg weight, bands(1)"'
_vt_probe mspline_bands_1 `"bands"' `"0"' `"twoway mspline mpg weight, bands(0)"'
_vt_probe mspline_bands_2 `"bands"' `"abc"' `"twoway mspline mpg weight, bands(abc)"'
_vt_probe xsize_1 `"xsize"' `"abc"' `"twoway scatter mpg weight, xsize(abc)"'
_vt_probe xsize_2 `"xsize"' `"-1"' `"twoway scatter mpg weight, xsize(-1)"'
_vt_probe xsize_3 `"xsize"' `"0"' `"twoway scatter mpg weight, xsize(0)"'
_vt_probe xsize_4 `"xsize"' `"101"' `"twoway scatter mpg weight, xsize(101)"'
_vt_probe xsize_5 `"xsize"' `"20"' `"twoway scatter mpg weight, xsize(20)"'
_vt_probe xsize_6 `"xsize"' `"2.5"' `"twoway scatter mpg weight, xsize(2.5)"'
_vt_probe xsize_7 `"xsize"' `"100"' `"twoway scatter mpg weight, xsize(100)"'
_vt_probe ysize_1 `"ysize"' `"-2"' `"twoway scatter mpg weight, ysize(-2)"'
_vt_probe ysize_2 `"ysize"' `"abc"' `"twoway scatter mpg weight, ysize(abc)"'
_vt_probe ysize_3 `"ysize"' `"0"' `"twoway scatter mpg weight, ysize(0)"'
_vt_probe ysize_4 `"ysize"' `"100"' `"twoway scatter mpg weight, ysize(100)"'
_vt_probe aspectratio_1 `"aspectratio"' `"abc"' `"twoway scatter mpg weight, aspectratio(abc)"'
_vt_probe aspectratio_2 `"aspectratio"' `"-1"' `"twoway scatter mpg weight, aspectratio(-1)"'
_vt_probe aspectratio_3 `"aspectratio"' `"0"' `"twoway scatter mpg weight, aspectratio(0)"'
_vt_probe aspectratio_4 `"aspectratio"' `"2"' `"twoway scatter mpg weight, aspectratio(2)"'
_vt_probe aspectratio_5 `"aspectratio"' `"100"' `"twoway scatter mpg weight, aspectratio(100)"'
_vt_probe aspectratio_6 `"aspectratio"' `"101"' `"twoway scatter mpg weight, aspectratio(101)"'
_vt_probe scheme_1 `"scheme"' `"nonsense"' `"twoway scatter mpg weight, scheme(nonsense)"'
_vt_probe scheme_2 `"scheme"' `"s2color"' `"twoway scatter mpg weight, scheme(s2color)"'
_vt_probe scheme_3 `"scheme"' `"economist"' `"twoway scatter mpg weight, scheme(economist)"'
_vt_probe by_1 `"by"' `"nosuchvar"' `"twoway scatter mpg weight, by(nosuchvar)"'
_vt_probe by_2 `"by"' `"for"' `"twoway scatter mpg weight, by(for)"'
_vt_probe by_3 `"by"' `"foreign"' `"twoway scatter mpg weight, by(foreign)"'
_vt_probe by_4 `"by"' `"foreign rep78"' `"twoway scatter mpg weight, by(foreign rep78)"'
_vt_probe by_5 `"by"' `"foreign, total"' `"twoway scatter mpg weight, by(foreign, total)"'
_vt_probe xline_1 `"xline"' `"abc"' `"twoway scatter mpg weight, xline(abc)"'
_vt_probe xline_2 `"xline"' `"3000"' `"twoway scatter mpg weight, xline(3000)"'
_vt_probe xline_3 `"xline"' `"1000 2000"' `"twoway scatter mpg weight, xline(1000 2000)"'
_vt_probe xlabel_1 `"xlabel"' `"abc"' `"twoway scatter mpg weight, xlabel(abc)"'
_vt_probe xlabel_2 `"xlabel"' `"#5"' `"twoway scatter mpg weight, xlabel(#5)"'
_vt_probe xlabel_3 `"xlabel"' `"1000(1000)5000"' `"twoway scatter mpg weight, xlabel(1000(1000)5000)"'
_vt_probe legend_1 `"legend"' `"garbage"' `"twoway scatter mpg weight, legend(garbage)"'
_vt_probe legend_2 `"legend"' `"off"' `"twoway scatter mpg weight, legend(off)"'
_vt_probe xscale_1 `"xscale"' `"bogus"' `"twoway scatter mpg weight, xscale(bogus)"'
_vt_probe xscale_2 `"xscale"' `"log"' `"twoway scatter mpg weight, xscale(log)"'
_vt_probe xscale_3 `"xscale"' `"reverse"' `"twoway scatter mpg weight, xscale(reverse)"'
_vt_probe title_1 `"title"' `"T, size(bogus)"' `"twoway scatter mpg weight, title("T", size(bogus))"'
_vt_probe title_2 `"title"' `"T, size(large)"' `"twoway scatter mpg weight, title("T", size(large))"'
_vt_probe title_3 `"title"' `"T, color(notacolour)"' `"twoway scatter mpg weight, title("T", color(notacolour))"'
_vt_probe plotregion_1 `"plotregion"' `"color(notacolour)"' `"twoway scatter mpg weight, plotregion(color(notacolour))"'
_vt_probe plotregion_2 `"plotregion"' `"lwidth(abc)"' `"twoway scatter mpg weight, plotregion(lwidth(abc))"'
_vt_probe plotregion_3 `"plotregion"' `"lwidth(thick)"' `"twoway scatter mpg weight, plotregion(lwidth(thick))"'
_vt_probe graphregion_1 `"graphregion"' `"color(notacolour)"' `"twoway scatter mpg weight, graphregion(color(notacolour))"'
_vt_probe graphregion_2 `"graphregion"' `"color(white)"' `"twoway scatter mpg weight, graphregion(color(white))"'
_vt_probe xtitle_1 `"xtitle"' `"T, size(bogus)"' `"twoway scatter mpg weight, xtitle("T", size(bogus))"'
_vt_probe ytitle_1 `"ytitle"' `"T, orientation(bogus)"' `"twoway scatter mpg weight, ytitle("T", orientation(bogus))"'
_vt_probe clwidth_1 `"clwidth"' `"abc"' `"twoway line mpg weight, clwidth(abc)"'
_vt_probe clwidth_2 `"clwidth"' `"*2"' `"twoway line mpg weight, clwidth(*2)"'
_vt_probe clwidth_3 `"clwidth"' `"-1"' `"twoway line mpg weight, clwidth(-1)"'
_vt_probe clwidth_4 `"clwidth"' `"vvvthick"' `"twoway line mpg weight, clwidth(vvvthick)"'
_vt_probe clwidth_5 `"clwidth"' `"2"' `"twoway line mpg weight, clwidth(2)"'
_vt_probe clwidth_6 `"clwidth"' `"0"' `"twoway line mpg weight, clwidth(0)"'
_vt_probe clwidth_7 `"clwidth"' `"none"' `"twoway line mpg weight, clwidth(none)"'
_vt_probe clwidth_8 `"clwidth"' `"-1"' `"twoway bar mpg weight, clwidth(-1)"'
_vt_probe mlabangle_1 `"mlabangle"' `"abc"' `"twoway scatter mpg weight, mlabel(make) mlabangle(abc)"'
_vt_probe mlabangle_2 `"mlabangle"' `"45"' `"twoway scatter mpg weight, mlabel(make) mlabangle(45)"'
_vt_probe mlabangle_3 `"mlabangle"' `"-30"' `"twoway scatter mpg weight, mlabel(make) mlabangle(-30)"'
_vt_probe mlabangle_4 `"mlabangle"' `"400"' `"twoway scatter mpg weight, mlabel(make) mlabangle(400)"'
_vt_probe mlabangle_5 `"mlabangle"' `"1e308"' `"twoway scatter mpg weight, mlabel(make) mlabangle(1e308)"'
_vt_probe mlabangle_6 `"mlabangle"' `"Vertical"' `"twoway scatter mpg weight, mlabel(make) mlabangle(Vertical)"'
_vt_probe mlabangle_7 `"mlabangle"' `"vertical"' `"twoway scatter mpg weight, mlabel(make) mlabangle(vertical)"'
_vt_probe mlabangle_8 `"mlabangle"' `"400"' `"twoway line mpg weight, mlabel(make) mlabangle(400)"'
_vt_probe alwidth_1 `"alwidth"' `"abc"' `"twoway lfitci mpg weight, alwidth(abc)"'
_vt_probe alwidth_2 `"alwidth"' `"*2"' `"twoway lfitci mpg weight, alwidth(*2)"'
_vt_probe alwidth_3 `"alwidth"' `"-1"' `"twoway lfitci mpg weight, alwidth(-1)"'
_vt_probe alwidth_4 `"alwidth"' `"vvvthick"' `"twoway lfitci mpg weight, alwidth(vvvthick)"'
_vt_probe alwidth_5 `"alwidth"' `"2"' `"twoway lfitci mpg weight, alwidth(2)"'
_vt_probe alwidth_6 `"alwidth"' `"0"' `"twoway lfitci mpg weight, alwidth(0)"'
_vt_probe alwidth_7 `"alwidth"' `"none"' `"twoway lfitci mpg weight, alwidth(none)"'
_vt_probe alwidth_8 `"alwidth"' `"20000"' `"twoway lfitci mpg weight, alwidth(20000)"'
_vt_probe alwidth_9 `"alwidth"' `"10000"' `"twoway lfitci mpg weight, alwidth(10000)"'
_vt_probe alwidth_10 `"alwidth"' `"-1"' `"twoway scatter mpg weight, alwidth(-1)"'
_vt_probe alwidth_11 `"alwidth"' `"-1"' `"twoway line mpg weight, alwidth(-1)"'
_vt_probe alwidth_12 `"alwidth"' `"-1"' `"twoway rarea mpg turn weight, alwidth(-1)"'
_vt_probe colorlevels_1 `"colorlevels"' `"abc"' `"twoway scatter mpg weight, colorvar(price) colorlevels(abc)"'
_vt_probe colorlevels_2 `"colorlevels"' `"1"' `"twoway scatter mpg weight, colorvar(price) colorlevels(1)"'
_vt_probe colorlevels_3 `"colorlevels"' `"2"' `"twoway scatter mpg weight, colorvar(price) colorlevels(2)"'
_vt_probe colorlevels_4 `"colorlevels"' `"4"' `"twoway scatter mpg weight, colorvar(price) colorlevels(4)"'
_vt_probe colorlevels_5 `"colorlevels"' `"256"' `"twoway scatter mpg weight, colorvar(price) colorlevels(256)"'
_vt_probe colorlevels_6 `"colorlevels"' `"257"' `"twoway scatter mpg weight, colorvar(price) colorlevels(257)"'
_vt_probe colorlevels_7 `"colorlevels"' `"-1"' `"twoway scatter mpg weight, colorvar(price) colorlevels(-1)"'
_vt_probe colorlevels_8 `"colorlevels"' `"2.5"' `"twoway scatter mpg weight, colorvar(price) colorlevels(2.5)"'
_vt_probe xlabel2_1 `"xlabel2"' `"abc"' `"twoway scatter mpg weight, xaxis(1 2) xlabel2(abc)"'
_vt_probe xlabel2_2 `"xlabel2"' `"#5"' `"twoway scatter mpg weight, xaxis(1 2) xlabel2(#5)"'
_vt_probe xlabel2_3 `"xlabel2"' `"1000(1000)5000"' `"twoway scatter mpg weight, xaxis(1 2) xlabel2(1000(1000)5000)"'
_vt_probe xmlabel_1 `"xmlabel"' `"abc"' `"twoway scatter mpg weight,  xmlabel(abc)"'
_vt_probe xmlabel_2 `"xmlabel"' `"#5"' `"twoway scatter mpg weight,  xmlabel(#5)"'
_vt_probe xmlabel_3 `"xmlabel"' `"1000(1000)5000"' `"twoway scatter mpg weight,  xmlabel(1000(1000)5000)"'
_vt_probe xmtick_1 `"xmtick"' `"abc"' `"twoway scatter mpg weight,  xmtick(abc)"'
_vt_probe xmtick_2 `"xmtick"' `"#5"' `"twoway scatter mpg weight,  xmtick(#5)"'
_vt_probe xmtick_3 `"xmtick"' `"1000(1000)5000"' `"twoway scatter mpg weight,  xmtick(1000(1000)5000)"'
_vt_probe xtick_1 `"xtick"' `"abc"' `"twoway scatter mpg weight,  xtick(abc)"'
_vt_probe xtick_2 `"xtick"' `"#5"' `"twoway scatter mpg weight,  xtick(#5)"'
_vt_probe xtick_3 `"xtick"' `"1000(1000)5000"' `"twoway scatter mpg weight,  xtick(1000(1000)5000)"'
_vt_probe ylabel_1 `"ylabel"' `"abc"' `"twoway scatter mpg weight,  ylabel(abc)"'
_vt_probe ylabel_2 `"ylabel"' `"#5"' `"twoway scatter mpg weight,  ylabel(#5)"'
_vt_probe ylabel_3 `"ylabel"' `"10(5)40"' `"twoway scatter mpg weight,  ylabel(10(5)40)"'
_vt_probe ylabel2_1 `"ylabel2"' `"abc"' `"twoway scatter mpg weight, yaxis(1 2) ylabel2(abc)"'
_vt_probe ylabel2_2 `"ylabel2"' `"#5"' `"twoway scatter mpg weight, yaxis(1 2) ylabel2(#5)"'
_vt_probe ylabel2_3 `"ylabel2"' `"10(5)40"' `"twoway scatter mpg weight, yaxis(1 2) ylabel2(10(5)40)"'
_vt_probe ymlabel_1 `"ymlabel"' `"abc"' `"twoway scatter mpg weight,  ymlabel(abc)"'
_vt_probe ymlabel_2 `"ymlabel"' `"#5"' `"twoway scatter mpg weight,  ymlabel(#5)"'
_vt_probe ymlabel_3 `"ymlabel"' `"10(5)40"' `"twoway scatter mpg weight,  ymlabel(10(5)40)"'
_vt_probe ymtick_1 `"ymtick"' `"abc"' `"twoway scatter mpg weight,  ymtick(abc)"'
_vt_probe ymtick_2 `"ymtick"' `"#5"' `"twoway scatter mpg weight,  ymtick(#5)"'
_vt_probe ymtick_3 `"ymtick"' `"10(5)40"' `"twoway scatter mpg weight,  ymtick(10(5)40)"'
_vt_probe ytick_1 `"ytick"' `"abc"' `"twoway scatter mpg weight,  ytick(abc)"'
_vt_probe ytick_2 `"ytick"' `"#5"' `"twoway scatter mpg weight,  ytick(#5)"'
_vt_probe ytick_3 `"ytick"' `"10(5)40"' `"twoway scatter mpg weight,  ytick(10(5)40)"'

* The format probes.
_vt_fmt F1 `"%9.2f"'
_vt_fmt F2 `"%9.0gc"'
_vt_fmt F3 `"%-12.3e"'
_vt_fmt F4 `"%09.2f"'
_vt_fmt F5 `"%9,2fc"'
_vt_fmt F6 `"%12.0fc"'
_vt_fmt F7 `"%tdCCYY-NN-DD"'
_vt_fmt F8 `"%tcHH:MM:SS"'
_vt_fmt F9 `"%21x"'
_vt_fmt F10 `"%16H"'
_vt_fmt F11 `"%12s"'
_vt_fmt F12 `"bogus"'
_vt_fmt F13 `"9.2f"'
_vt_fmt F14 `"%9.2"'
_vt_fmt F15 `"%9.2f_n"'
_vt_fmt F16 `"%tc"'
_vt_fmt F17 `"%td"'
_vt_fmt F18 `"%tm"'
_vt_fmt F19 `"%9.2fc"'
_vt_fmt F20 `"%-9.2f"'
_vt_fmt F21 `"%10.0g"'
_vt_fmt F22 `"%8.0e"'
_vt_fmt F23 `"%9.2f%9.2f"'
_vt_fmt F24 `"%c"'
_vt_fmt F25 `"%"'
_vt_fmt F26 `"%%9.2f"'
_vt_fmt F90 `"%9.2f"' string
_vt_fmt F91 `"bogus"' string

* The vocabularies.
* relativesizestyle and gsizestyle are no type of their own to graph query
* ("there is no type relativesize"): a size of either is a textsizestyle
* name (the gsize class), so they are listed from textsizestyle; any other
* refusal fails the run.
foreach s of global ZV_VOCAB {
    quietly log using `"${ZV_WORK}/vocab_`s'.log"', text replace name(vt)
    capture noisily graph query `s'
    local qrc = _rc
    quietly log close vt
    if `qrc' & inlist("`s'", "relativesizestyle", "gsizestyle") {
        quietly log using `"${ZV_WORK}/vocab_`s'.log"', text replace name(vt)
        graph query textsizestyle
        quietly log close vt
        global ZV_ALIAS_`s' textsizestyle
    }
    else if `qrc' exit `qrc'
}

python:
import json, os, re
from sfi import Macro
G = Macro.getGlobal
work = G("ZV_WORK")
def lines(path):
    with open(path, encoding="utf-8") as fh:
        return [ln.strip() for ln in fh.read().splitlines()]
tw = []
for pid in G("ZV_IDS").split():
    with open(os.path.join(work, "probe_%s.rc" % pid), encoding="utf-8") as fh:
        rc, option, value, command = fh.read().split("\n")[:4]
    msg = " ".join(" ".join(ln.split()) for ln in lines(os.path.join(work, "probe_%s.log" % pid)) if ln)
    tw.append({"id": pid, "option": option, "value": value,
               "command": command, "rc": int(rc), "message": msg})
fm = []
for fid in G("ZV_FIDS").split():
    with open(os.path.join(work, "fmt_%s.rc" % fid), encoding="utf-8") as fh:
        rc, value = fh.read().split("\n")[:2]
    msg = " ".join(" ".join(ln.split()) for ln in lines(os.path.join(work, "fmt_%s.log" % fid)) if ln)
    fm.append({"id": fid, "value": value, "rc": int(rc), "message": msg})
vocab = {}
for s in G("ZV_VOCAB").split():
    ls = lines(os.path.join(work, "vocab_%s.log" % s))
    q = G("ZV_ALIAS_" + s) or s
    i = next(k for k, ln in enumerate(ls) if ln == q + " may be")
    j = next((k for k, ln in enumerate(ls)
              if k > i and ln.startswith("For information")), len(ls))
    vocab[s] = sorted({w for ln in ls[i + 1:j] for w in ln.split()})
n0 = sum(1 for p in tw if p["rc"] == 0)
out = {
    "_meta": {
        "stata_version": G("ZV_SVER"), "born_date": G("ZV_BORN"),
        "dash_commit": G("ZV_COMMIT").strip(), "extracted": G("ZV_DATE"),
        "source": "scripts/extract_value_truth.do",
        "stata": "console binary (stata_slot.sh), set graphics off, sysuse auto",
        "purpose": "twoway's own verdict on bad option VALUES, so dash refuses what twoway refuses and reports what twoway notes. Read by test/test_option_validation.py; the rules it grounds are the table in dash.ado (_dash_option_rules).",
        "how": "one \x60capture noisily twoway ...\x60 per probe, rc and the joined message recorded; \x60graph query <style>\x60 output parsed for the vocabularies (this Stata stores nothing in r() for it); \x60confirm numeric format\x60 for the format probes",
        "finding": "twoway never rejects a bad style NAME: it prints \x60(note: named style X not found in class Y, default attributes used)\x60 and draws with the default (rc 0). It rejects bad numbers, ranges, enums and unknown variables (rc 198/125/126/121/122/111/4026).",
        "counts": {"twoway": len(tw), "twoway_rc0": n0,
                   "twoway_rejected": len(tw) - n0, "formats": len(fm),
                   "vocab": {s: len(v) for s, v in vocab.items()}},
    },
    "vocab": vocab, "formats": fm, "twoway": tw,
}
path = os.path.join(G("ZV_REPO"), "test", "fixtures", "value_truth.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, ensure_ascii=False)
    fh.write("\n")
print("wrote %s: %d twoway, %d formats" % (path, len(tw), len(fm)))
end
