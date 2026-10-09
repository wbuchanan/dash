*! extract_colour_grammar_truth.do -- WP-30 section 30 (P1.13a): measure
*! what twoway draws for every form of Stata's colour grammar -- colour*#,
*! CMYK, HSV, bg/fg, %# beside *#, unknown, wrong-case, malformed and
*! comma-written colours -- in an option and in a scheme file, so dash's
*! colour reader is proved against twoway itself.
*!
*! Output: test/fixtures/colour_grammar_truth.json
*!
*! Run through the slot wrapper only (CLAUDE.md rule 10):
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_colour_grammar_truth.do
*!
*! METHOD.  sysuse auto, lo = mpg - 3, hi = mpg + 3.  Each probe
*! (_cg_probe) runs one twoway command under `capture noisily' inside its
*! own text log, records the rc, the log's (note: lines and its invalid '
*! line, and exports the graph to SVG when rc is 0.  One python block reads
*! every SVG through scripts/svg_truth.py by kind (marker: the markers'
*! dominant fill and opacity; line: the dominant stroke of the series
*! path; bar: the dominant narrow rect fill; text: the fill of the text T;
*! region and refline: the graph region's fill (the second rect;
*! the first is the canvas) and the vertical line
*! strokes) and also the graph region's fill for every probe.  twoway
*! only: dash is never run.  The user schemes scheme-cg*.scheme are
*! written into a tempfile-named directory under c(tmpdir), never into the
*! repository.  The git commit is read from a file `shell' wrote.  Every
*! SVG, log and scheme file is erased.

clear all
set more off
set linesize 200

* Root: DASH_REPO, else the current directory when it is a dash tree.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_colour_grammar_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_colour_grammar_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the dash repository"'
    exit 601
}
global CG_REPO "`repo'"
global CG_OUT "${CG_REPO}/test/fixtures/colour_grammar_truth.json"

adopath ++ "${CG_REPO}/"
global dash_nobrowser 1

version 19
set graphics off

if `"`c(python_exec)'"' == "" {
    display as error "extract_colour_grammar_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

* The work directory: tempfile-named, under c(tmpdir).
tempfile _cg_name
mata: st_global("CG_WORK", pathjoin(st_global("c(tmpdir)"), "dash_cg_" + pathbasename(st_local("_cg_name"))))
mata: st_global("CG_WORK", subinstr(subinstr(st_global("CG_WORK"), ".tmp", ""), ".", "_"))
capture mkdir "${CG_WORK}"
adopath ++ "${CG_WORK}/"
local _cg_home `"`c(pwd)'"'
quietly cd "${CG_WORK}"

quietly shell git -C "${CG_REPO}" rev-parse HEAD > "${CG_WORK}/git_head.txt"
global CG_VERSION "`c(stata_version)'"
global CG_BORN "`c(born_date)'"
global CG_WHEN "`c(current_date)' `c(current_time)'"

sysuse auto, clear
generate lo = mpg - 3
generate hi = mpg + 3

global CG_IDS ""
global CG_SEQ = 0
global CG_SCHEMES ""

capture program drop _cg_scheme
program define _cg_scheme
    * _cg_scheme name `"line"' [`"line"' ...]: #include s2color plus the lines
    gettoken name 0 : 0
    tempname fh
    file open `fh' using "${CG_WORK}/scheme-`name'.scheme", write text replace
    file write `fh' "#include s2color" _n
    while `"`macval(0)'"' != "" {
        gettoken line 0 : 0
        file write `fh' `"`macval(line)'"' _n
    }
    file close `fh'
    global CG_SCHEMES "${CG_SCHEMES} `name'"
end

capture program drop _cg_probe
program define _cg_probe
    * _cg_probe id group context scheme kind owner `"value"' command
    gettoken id 0 : 0
    gettoken group 0 : 0
    gettoken context 0 : 0
    gettoken scheme 0 : 0
    gettoken kind 0 : 0
    gettoken owner 0 : 0
    gettoken value 0 : 0
    local cmd = strtrim(`"`macval(0)'"')
    local opt = cond(strpos(`"`macval(cmd)'"', ","), " ", ", ")
    global CG_SEQ = ${CG_SEQ} + 1
    local f "${CG_WORK}/p${CG_SEQ}"
    global CGF_`id' "p${CG_SEQ}"
    quietly log using "`f'.log", text replace name(cgp)
    capture noisily twoway `macval(cmd)' `opt' scheme(`scheme') name(cg, replace)
    local rc = _rc
    quietly log close cgp
    global CGR_`id' = `rc'
    global CGG_`id' "`group'"
    global CGX_`id' "`context'"
    global CGK_`id' "`kind'"
    global CGS_`id' "`scheme'"
    global CGO_`id' "`owner'"
    global CGV_`id' `"`macval(value)'"'
    global CGC_`id' `"`macval(cmd)'"'
    if `rc' == 0 {
        quietly graph export "`f'.svg", replace
    }
    global CG_IDS "${CG_IDS} `id'"
    capture graph drop cg
end

_cg_probe opt_01 opt option s2color marker - `"navy*.5"' scatter mpg weight, mcolor(navy*.5)
_cg_probe opt_02 opt option s2color marker - `"navy*.25"' scatter mpg weight, mcolor(navy*.25)
_cg_probe opt_03 opt option s2color marker - `"navy*.75"' scatter mpg weight, mcolor(navy*.75)
_cg_probe opt_04 opt option s2color marker - `"navy*.333"' scatter mpg weight, mcolor(navy*.333)
_cg_probe opt_05 opt option s2color marker - `"navy*.1"' scatter mpg weight, mcolor(navy*.1)
_cg_probe opt_06 opt option s2color marker - `"navy*.01"' scatter mpg weight, mcolor(navy*.01)
_cg_probe opt_07 opt option s2color marker - `"navy*0"' scatter mpg weight, mcolor(navy*0)
_cg_probe opt_08 opt option s2color marker - `"navy*1e-5"' scatter mpg weight, mcolor(navy*1e-5)
_cg_probe opt_09 opt option s2color marker - `"navy*1.5"' scatter mpg weight, mcolor(navy*1.5)
_cg_probe opt_10 opt option s2color marker - `"navy*2"' scatter mpg weight, mcolor(navy*2)
_cg_probe opt_11 opt option s2color marker - `"navy*3"' scatter mpg weight, mcolor(navy*3)
_cg_probe opt_12 opt option s2color marker - `"navy*5"' scatter mpg weight, mcolor(navy*5)
_cg_probe opt_13 opt option s2color marker - `"navy*10"' scatter mpg weight, mcolor(navy*10)
_cg_probe opt_14 opt option s2color marker - `"navy*20"' scatter mpg weight, mcolor(navy*20)
_cg_probe opt_15 opt option s2color marker - `"navy*30"' scatter mpg weight, mcolor(navy*30)
_cg_probe opt_16 opt option s2color marker - `"navy*50"' scatter mpg weight, mcolor(navy*50)
_cg_probe opt_17 opt option s2color marker - `"navy*52"' scatter mpg weight, mcolor(navy*52)
_cg_probe opt_18 opt option s2color marker - `"navy*100"' scatter mpg weight, mcolor(navy*100)
_cg_probe opt_19 opt option s2color marker - `"navy*1000"' scatter mpg weight, mcolor(navy*1000)
_cg_probe opt_20 opt option s2color marker - `"maroon*1.25"' scatter mpg weight, mcolor(maroon*1.25)
_cg_probe opt_21 opt option s2color marker - `"gs8*3"' scatter mpg weight, mcolor(gs8*3)
_cg_probe opt_22 opt option s2color marker - `"red*10"' scatter mpg weight, mcolor(red*10)
_cg_probe opt_23 opt option s2color marker - `"gs8*100"' scatter mpg weight, mcolor(gs8*100)
_cg_probe opt_24 opt option s2color marker - `"white*255"' scatter mpg weight, mcolor(white*255)
_cg_probe opt_25 opt option s2color marker - `"red*.5"' scatter mpg weight, mcolor(red*.5)
_cg_probe opt_26 opt option s2color marker - `"fg*.5"' scatter mpg weight, mcolor(fg*.5)
_cg_probe opt_27 opt option s2color marker - `"bg*.5"' scatter mpg weight, mcolor(bg*.5)
_cg_probe opt_28 opt option s2color marker - `"none*.5"' scatter mpg weight, mcolor(none*.5)
_cg_probe opt_29 opt option s2color marker - `""#FF0000*.5""' scatter mpg weight, mcolor("#FF0000*.5")
_cg_probe opt_30 opt option s2color marker - `""0 255 255*1.2""' scatter mpg weight, mcolor("0 255 255*1.2")
_cg_probe opt_31 opt option s2color marker - `""hsv 240 1 1*.5""' scatter mpg weight, mcolor("hsv 240 1 1*.5")
_cg_probe opt_32 opt option s2color marker - `""0 0 0 128*.5""' scatter mpg weight, mcolor("0 0 0 128*.5")
_cg_probe opt_33 opt option s2color marker - `"red*+.5"' scatter mpg weight, mcolor(red*+.5)
_cg_probe opt_34 opt option s2color marker - `"red*5e-1"' scatter mpg weight, mcolor(red*5e-1)
_cg_probe opt_35 opt option s2color marker - `"red*"' scatter mpg weight, mcolor(red*)
_cg_probe opt_36 opt option s2color marker - `""0 0 0 255""' scatter mpg weight, mcolor("0 0 0 255")
_cg_probe opt_37 opt option s2color marker - `""0 0 0 1""' scatter mpg weight, mcolor("0 0 0 1")
_cg_probe opt_38 opt option s2color marker - `""85 40 0 144""' scatter mpg weight, mcolor("85 40 0 144")
_cg_probe opt_39 opt option s2color marker - `"".334 .157 0 .565""' scatter mpg weight, mcolor(".334 .157 0 .565")
_cg_probe opt_40 opt option s2color marker - `""0 255 255 0""' scatter mpg weight, mcolor("0 255 255 0")
_cg_probe opt_41 opt option s2color marker - `""10 10 5 0""' scatter mpg weight, mcolor("10 10 5 0")
_cg_probe opt_42 opt option s2color marker - `""128 0 0 0""' scatter mpg weight, mcolor("128 0 0 0")
_cg_probe opt_43 opt option s2color marker - `""100 100 100 100""' scatter mpg weight, mcolor("100 100 100 100")
_cg_probe opt_44 opt option s2color marker - `""200 0 0 100""' scatter mpg weight, mcolor("200 0 0 100")
_cg_probe opt_45 opt option s2color marker - `""0 0 0 .5""' scatter mpg weight, mcolor("0 0 0 .5")
_cg_probe opt_46 opt option s2color marker - `""0 0 0 .3""' scatter mpg weight, mcolor("0 0 0 .3")
_cg_probe opt_47 opt option s2color marker - `"".5 .5 .5 .5""' scatter mpg weight, mcolor(".5 .5 .5 .5")
_cg_probe opt_48 opt option s2color marker - `"".2 .4 .6 .1""' scatter mpg weight, mcolor(".2 .4 .6 .1")
_cg_probe opt_49 opt option s2color marker - `""1 0 0 0""' scatter mpg weight, mcolor("1 0 0 0")
_cg_probe opt_50 opt option s2color marker - `""1 1 1 1""' scatter mpg weight, mcolor("1 1 1 1")
_cg_probe opt_51 opt option s2color marker - `""0 0 0 2""' scatter mpg weight, mcolor("0 0 0 2")
_cg_probe opt_52 opt option s2color marker - `""0 0 0 128""' scatter mpg weight, mcolor("0 0 0 128")
_cg_probe opt_53 opt option s2color marker - `""0 0 0 300""' scatter mpg weight, mcolor("0 0 0 300")
_cg_probe opt_54 opt option s2color marker - `""0 0 0 127.5""' scatter mpg weight, mcolor("0 0 0 127.5")
_cg_probe opt_55 opt option s2color marker - `""0 0 0 -1""' scatter mpg weight, mcolor("0 0 0 -1")
_cg_probe opt_56 opt option s2color marker - `""0 0 0 1e400""' scatter mpg weight, mcolor("0 0 0 1e400")
_cg_probe opt_57 opt option s2color marker - `""0 0 0 0 0""' scatter mpg weight, mcolor("0 0 0 0 0")
_cg_probe opt_58 opt option s2color marker - `""hsv 240 1 1""' scatter mpg weight, mcolor("hsv 240 1 1")
_cg_probe opt_59 opt option s2color marker - `""hsv 0 0 1""' scatter mpg weight, mcolor("hsv 0 0 1")
_cg_probe opt_60 opt option s2color marker - `""hsv 209 .766 .435""' scatter mpg weight, mcolor("hsv 209 .766 .435")
_cg_probe opt_61 opt option s2color marker - `""hsv 120 1 .502""' scatter mpg weight, mcolor("hsv 120 1 .502")
_cg_probe opt_62 opt option s2color marker - `""hsv 30 .5 .5""' scatter mpg weight, mcolor("hsv 30 .5 .5")
_cg_probe opt_63 opt option s2color marker - `""hsv 0 0 .5""' scatter mpg weight, mcolor("hsv 0 0 .5")
_cg_probe opt_64 opt option s2color marker - `""hsv 180 .5 1""' scatter mpg weight, mcolor("hsv 180 .5 1")
_cg_probe opt_65 opt option s2color marker - `""hsv 300 .25 .75""' scatter mpg weight, mcolor("hsv 300 .25 .75")
_cg_probe opt_66 opt option s2color marker - `""hsv 90 .3 .9""' scatter mpg weight, mcolor("hsv 90 .3 .9")
_cg_probe opt_67 opt option s2color marker - `""hsv 200 .7 .3""' scatter mpg weight, mcolor("hsv 200 .7 .3")
_cg_probe opt_68 opt option s2color marker - `""hsv 15.5 1 1""' scatter mpg weight, mcolor("hsv 15.5 1 1")
_cg_probe opt_69 opt option s2color marker - `""hsv 360 1 1""' scatter mpg weight, mcolor("hsv 360 1 1")
_cg_probe opt_70 opt option s2color marker - `""hsv 400 1 1""' scatter mpg weight, mcolor("hsv 400 1 1")
_cg_probe opt_71 opt option s2color marker - `""hsv -30 1 1""' scatter mpg weight, mcolor("hsv -30 1 1")
_cg_probe opt_72 opt option s2color marker - `""hsv 0 0 0""' scatter mpg weight, mcolor("hsv 0 0 0")
_cg_probe opt_73 opt option s2color marker - `""HSV 240 1 1""' scatter mpg weight, mcolor("HSV 240 1 1")
_cg_probe opt_74 opt option s2color marker - `""hsv 240 2 1""' scatter mpg weight, mcolor("hsv 240 2 1")
_cg_probe opt_75 opt option s2color marker - `""hsv 240 -1 1""' scatter mpg weight, mcolor("hsv 240 -1 1")
_cg_probe opt_76 opt option s2color marker - `""hsv 240 1""' scatter mpg weight, mcolor("hsv 240 1")
_cg_probe opt_77 opt option s2color marker - `""hsv 240 1 1 0""' scatter mpg weight, mcolor("hsv 240 1 1 0")
_cg_probe opt_78 opt option s2color marker - `""hsv 1e400 1 1""' scatter mpg weight, mcolor("hsv 1e400 1 1")
_cg_probe opt_79 opt option s2color marker - `"hsv"' scatter mpg weight, mcolor(hsv)
_cg_probe opt_80 opt option s2color marker - `"bg"' scatter mpg weight, mcolor(bg)
_cg_probe opt_81 opt option s2color marker - `"fg"' scatter mpg weight, mcolor(fg)
_cg_probe opt_82 opt option s2color marker - `"background"' scatter mpg weight, mcolor(background)
_cg_probe opt_83 opt option s2color marker - `"foreground"' scatter mpg weight, mcolor(foreground)
_cg_probe opt_84 opt option s2color marker - `"BG"' scatter mpg weight, mcolor(BG)
_cg_probe opt_85 opt option s2color marker - `"Bg"' scatter mpg weight, mcolor(Bg)
_cg_probe opt_86 opt option s2color marker - `"FOREGROUND"' scatter mpg weight, mcolor(FOREGROUND)
_cg_probe opt_87 opt option s2color marker - `"bogus"' scatter mpg weight, mcolor(bogus)
_cg_probe opt_88 opt option s2color marker - `"Navy"' scatter mpg weight, mcolor(Navy)
_cg_probe opt_89 opt option s2color marker - `"grey"' scatter mpg weight, mcolor(grey)
_cg_probe opt_90 opt option s2color marker - `""300 0 0""' scatter mpg weight, mcolor("300 0 0")
_cg_probe opt_91 opt option s2color marker - `""255 0""' scatter mpg weight, mcolor("255 0")
_cg_probe opt_92 opt option s2color marker - `""1.5 0 0""' scatter mpg weight, mcolor("1.5 0 0")
_cg_probe opt_93 opt option s2color marker - `""255 0 0 0 0""' scatter mpg weight, mcolor("255 0 0 0 0")
_cg_probe opt_94 opt option s2color marker - `"Red*.5"' scatter mpg weight, mcolor(Red*.5)
_cg_probe opt_95 opt option s2color marker - `"Red%50"' scatter mpg weight, mcolor(Red%50)
_cg_probe opt_96 opt option s2color marker - `""#F00""' scatter mpg weight, mcolor("#F00")
_cg_probe opt_97 opt option s2color marker - `""#ff00""' scatter mpg weight, mcolor("#ff00")
_cg_probe opt_98 opt option s2color marker - `""#GG0000""' scatter mpg weight, mcolor("#GG0000")
_cg_probe opt_99 opt option s2color marker - `""#F00%50""' scatter mpg weight, mcolor("#F00%50")
_cg_probe opt_100 opt option s2color marker - `"red%150"' scatter mpg weight, mcolor(red%150)
_cg_probe opt_101 opt option s2color marker - `"red%abc"' scatter mpg weight, mcolor(red%abc)
_cg_probe opt_102 opt option s2color marker - `"navy%50%30"' scatter mpg weight, mcolor(navy%50%30)
_cg_probe opt_103 opt option s2color marker - `"*abc"' scatter mpg weight, mcolor(*abc)
_cg_probe opt_104 opt option s2color marker - `""""' scatter mpg weight, mcolor("")
_cg_probe opt_105 opt option s2color marker - `"bogus%150"' scatter mpg weight, mcolor(bogus%150)
_cg_probe opt_106 opt option s2color marker - `"bogus*abc"' scatter mpg weight, mcolor(bogus*abc)
_cg_probe opt_107 opt option s2color marker - `"red*abc"' scatter mpg weight, mcolor(red*abc)
_cg_probe opt_108 opt option s2color marker - `"red*-1"' scatter mpg weight, mcolor(red*-1)
_cg_probe opt_109 opt option s2color marker - `"red*1e400"' scatter mpg weight, mcolor(red*1e400)
_cg_probe opt_110 opt option s2color marker - `"red*.5*2"' scatter mpg weight, mcolor(red*.5*2)
_cg_probe opt_111 opt option s2color marker - `"red**.5"' scatter mpg weight, mcolor(red**.5)
_cg_probe opt_112 opt option s2color marker - `"red*."' scatter mpg weight, mcolor(red*.)
_cg_probe opt_113 opt option s2color marker - `"red%50*abc"' scatter mpg weight, mcolor(red%50*abc)
_cg_probe opt_114 opt option s2color marker - `""0 255 0*abc""' scatter mpg weight, mcolor("0 255 0*abc")
_cg_probe opt_115 opt option s2color marker - `"red%"' scatter mpg weight, mcolor(red%)
_cg_probe opt_116 opt option s2color marker - `"#ff0000"' scatter mpg weight, mcolor(#ff0000)
_cg_probe opt_117 opt option s2color marker - `"#FF0000"' scatter mpg weight, mcolor(#FF0000)
_cg_probe opt_118 opt option s2color marker - `""#ff0000""' scatter mpg weight, mcolor("#ff0000")
_cg_probe opt_119 opt option s2color marker - `"navy*.5%50"' scatter mpg weight, mcolor(navy*.5%50)
_cg_probe opt_120 opt option s2color marker - `"navy%50*.5"' scatter mpg weight, mcolor(navy%50*.5)
_cg_probe opt_121 opt option s2color marker - `"*.5%50"' scatter mpg weight, mcolor(*.5%50)
_cg_probe opt_122 opt option s2color marker - `""0 255 0%50*.5""' scatter mpg weight, mcolor("0 255 0%50*.5")
_cg_probe opt_123 opt option s2color marker - `""hsv 240 1 1%50""' scatter mpg weight, mcolor("hsv 240 1 1%50")
_cg_probe opt_124 opt option s2color marker - `""0 0 255%50""' scatter mpg weight, mcolor("0 0 255%50")
_cg_probe opt_125 opt option s2color marker - `""hsv 240 1 1%50*.5""' scatter mpg weight, mcolor("hsv 240 1 1%50*.5")
_cg_probe s1r_01 s1r option s1rcolor marker - `"navy*.5"' scatter mpg weight, mcolor(navy*.5)
_cg_probe s1r_02 s1r option s1rcolor marker - `"navy*1.5"' scatter mpg weight, mcolor(navy*1.5)
_cg_probe s1r_03 s1r option s1rcolor marker - `"fg"' scatter mpg weight, mcolor(fg)
_cg_probe s1r_04 s1r option s1rcolor marker - `"bg"' scatter mpg weight, mcolor(bg)
_cg_probe s1r_05 s1r option s1rcolor marker - `"fg*.5"' scatter mpg weight, mcolor(fg*.5)
_cg_probe s1r_06 s1r option s1rcolor marker - `"bg*.5"' scatter mpg weight, mcolor(bg*.5)
_cg_probe s1r_07 s1r option s1rcolor marker - `""hsv 240 1 1*.5""' scatter mpg weight, mcolor("hsv 240 1 1*.5")
_cg_probe s1r_08 s1r option s1rcolor marker - `""0 0 0 128""' scatter mpg weight, mcolor("0 0 0 128")
_cg_probe bgs_01 bgs option stcolor marker - `"bg"' scatter mpg weight, mcolor(bg)
_cg_probe bgs_02 bgs option stcolor marker - `"fg"' scatter mpg weight, mcolor(fg)
_cg_probe bgs_03 bgs option economist marker - `"bg"' scatter mpg weight, mcolor(bg)
_cg_probe bgs_04 bgs option economist marker - `"fg"' scatter mpg weight, mcolor(fg)
_cg_scheme cgs01 `"color p1 navy*.5"'
_cg_probe sch_01 sch scheme cgs01 marker - `"navy*.5"' scatter mpg weight
_cg_scheme cgs02 `"color p1 "0 0 0 255""'
_cg_probe sch_02 sch scheme cgs02 marker - `""0 0 0 255""' scatter mpg weight
_cg_scheme cgs03 `"color p1 "hsv 240 1 1""'
_cg_probe sch_03 sch scheme cgs03 marker - `""hsv 240 1 1""' scatter mpg weight
_cg_scheme cgs04 `"color p1 "0 255 255 0""'
_cg_probe sch_04 sch scheme cgs04 marker - `""0 255 255 0""' scatter mpg weight
_cg_scheme cgs05 `"color p1 "0 0 0 128""'
_cg_probe sch_05 sch scheme cgs05 marker - `""0 0 0 128""' scatter mpg weight
_cg_scheme cgs06 `"color p1 navy*1.5%50"'
_cg_probe sch_06 sch scheme cgs06 marker - `"navy*1.5%50"' scatter mpg weight
_cg_scheme cgs07 `"color p1 navy*+.5"'
_cg_probe sch_07 sch scheme cgs07 marker - `"navy*+.5"' scatter mpg weight
_cg_scheme cgs08 `"color p1 "hsv 240 1 1*.5""'
_cg_probe sch_08 sch scheme cgs08 marker - `""hsv 240 1 1*.5""' scatter mpg weight
_cg_scheme cgs09 `"color p1 "hsv 400 1 1""'
_cg_probe sch_09 sch scheme cgs09 marker - `""hsv 400 1 1""' scatter mpg weight
_cg_scheme cgs10 `"color p1 navy*0"'
_cg_probe sch_10 sch scheme cgs10 marker - `"navy*0"' scatter mpg weight
_cg_scheme cgs11 `"color p1 navy*"'
_cg_probe sch_11 sch scheme cgs11 marker - `"navy*"' scatter mpg weight
_cg_scheme cgs12 `"color p1 "#ff0000""'
_cg_probe sch_12 sch scheme cgs12 marker - `""#ff0000""' scatter mpg weight
_cg_scheme cgs13 `"color p1 "#FF0000""'
_cg_probe sch_13 sch scheme cgs13 marker - `""#FF0000""' scatter mpg weight
_cg_scheme cgs14 `"color p1 "255,0,0""'
_cg_probe sch_14 sch scheme cgs14 marker - `""255,0,0""' scatter mpg weight
_cg_scheme cgs15 `"color p1 "1,2,3,4""'
_cg_probe sch_15 sch scheme cgs15 marker - `""1,2,3,4""' scatter mpg weight
_cg_scheme cgs16 `"color p1 *.5"'
_cg_probe sch_16 sch scheme cgs16 marker - `"*.5"' scatter mpg weight
_cg_scheme cgs17 `"color p1 "#F00""'
_cg_probe sch_17 sch scheme cgs17 marker - `""#F00""' scatter mpg weight
_cg_scheme cgs18 `"color p1 "#0F0""'
_cg_probe sch_18 sch scheme cgs18 marker - `""#0F0""' scatter mpg weight
_cg_scheme cgs19 `"color p1 "#ff00""'
_cg_probe sch_19 sch scheme cgs19 marker - `""#ff00""' scatter mpg weight
_cg_scheme cgs20 `"color p1 "#GG0000""'
_cg_probe sch_20 sch scheme cgs20 marker - `""#GG0000""' scatter mpg weight
_cg_scheme cgs21 `"color p1 navy*abc"'
_cg_probe sch_21 sch scheme cgs21 marker - `"navy*abc"' scatter mpg weight
_cg_scheme cgs22 `"color p1 navy*-1"'
_cg_probe sch_22 sch scheme cgs22 marker - `"navy*-1"' scatter mpg weight
_cg_scheme cgs23 `"color p1 navy*1e400"'
_cg_probe sch_23 sch scheme cgs23 marker - `"navy*1e400"' scatter mpg weight
_cg_scheme cgs24 `"color p1 navy*.5*2"'
_cg_probe sch_24 sch scheme cgs24 marker - `"navy*.5*2"' scatter mpg weight
_cg_scheme cgs25 `"color p1 navy**.5"'
_cg_probe sch_25 sch scheme cgs25 marker - `"navy**.5"' scatter mpg weight
_cg_scheme cgs26 `"color p1 red%150"'
_cg_probe sch_26 sch scheme cgs26 marker - `"red%150"' scatter mpg weight
_cg_scheme cgs27 `"color p1 bogus%150"'
_cg_probe sch_27 sch scheme cgs27 marker - `"bogus%150"' scatter mpg weight
_cg_scheme cgs28 `"color p1 "255,0""'
_cg_probe sch_28 sch scheme cgs28 marker - `""255,0""' scatter mpg weight
_cg_scheme cgs29 `"color p1 red%"'
_cg_probe sch_29 sch scheme cgs29 marker - `"red%"' scatter mpg weight
_cg_scheme cgs30 `"color p1 %50"'
_cg_probe sch_30 sch scheme cgs30 marker - `"%50"' scatter mpg weight
_cg_scheme cgs31 `"color p1 bogus"'
_cg_probe sch_31 sch scheme cgs31 marker - `"bogus"' scatter mpg weight
_cg_scheme cgs32 `"color p1 Navy"'
_cg_probe sch_32 sch scheme cgs32 marker - `"Navy"' scatter mpg weight
_cg_scheme cgs33 `"color p1 grey"'
_cg_probe sch_33 sch scheme cgs33 marker - `"grey"' scatter mpg weight
_cg_scheme cgs34 `"color p1 "255 0""'
_cg_probe sch_34 sch scheme cgs34 marker - `""255 0""' scatter mpg weight
_cg_scheme cgs35 `"color p1 "300 0 0""'
_cg_probe sch_35 sch scheme cgs35 marker - `""300 0 0""' scatter mpg weight
_cg_scheme cgs36 `"color p1 "0 0 0 300""'
_cg_probe sch_36 sch scheme cgs36 marker - `""0 0 0 300""' scatter mpg weight
_cg_scheme cgs37 `"color p1 "hsv 240 2 1""'
_cg_probe sch_37 sch scheme cgs37 marker - `""hsv 240 2 1""' scatter mpg weight
_cg_scheme cgs38 `"color p1 "hsv 240 1""'
_cg_probe sch_38 sch scheme cgs38 marker - `""hsv 240 1""' scatter mpg weight
_cg_scheme cgs39 `"color p1 "1.5 0 0""'
_cg_probe sch_39 sch scheme cgs39 marker - `""1.5 0 0""' scatter mpg weight
_cg_scheme cgs40 `"color p1 "255 0 0 0 0""'
_cg_probe sch_40 sch scheme cgs40 marker - `""255 0 0 0 0""' scatter mpg weight
_cg_scheme cgs41 `"color p1 Navy*.5"'
_cg_probe sch_41 sch scheme cgs41 marker - `"Navy*.5"' scatter mpg weight
_cg_scheme cgs42 `"color p1 bogus%50"'
_cg_probe sch_42 sch scheme cgs42 marker - `"bogus%50"' scatter mpg weight
_cg_scheme cgb01 `"color background "255 0 0""' `"color p1 bg"'
_cg_probe bgfg_01 bgfg scheme cgb01 marker - `"t01: color background "255 0 0"; color p1 bg"' scatter mpg weight
_cg_scheme cgb02 `"color background "hsv 0 1 1""' `"color p1 bg"'
_cg_probe bgfg_02 bgfg scheme cgb02 marker - `"t02: color background "hsv 0 1 1"; color p1 bg"' scatter mpg weight
_cg_scheme cgb03 `"color background "0 255 255 0""' `"color p1 bg"'
_cg_probe bgfg_03 bgfg scheme cgb03 marker - `"t03: color background "0 255 255 0"; color p1 bg"' scatter mpg weight
_cg_scheme cgb04 `"color background red%50"' `"color p1 bg"'
_cg_probe bgfg_04 bgfg scheme cgb04 marker - `"t04: color background red%50; color p1 bg"' scatter mpg weight
_cg_scheme cgb05 `"color background "#ff0000""' `"color p1 bg"'
_cg_probe bgfg_05 bgfg scheme cgb05 marker - `"t05: color background "#ff0000"; color p1 bg"' scatter mpg weight
_cg_scheme cgb06 `"color background navy*.5"'
_cg_probe bgfg_06 bgfg scheme cgb06 marker - `"t06: color background navy*.5 + mcolor(bg)"' scatter mpg weight, mcolor(bg)
_cg_scheme cgb07 `"color background red"'
_cg_probe bgfg_07 bgfg scheme cgb07 marker - `"t20: color background red + mcolor(bg*.5)"' scatter mpg weight, mcolor(bg*.5)
_cg_scheme cgb08 `"color foreground "0 128 0""'
_cg_probe bgfg_08 bgfg scheme cgb08 marker - `"t21: color foreground "0 128 0" + mcolor(fg)"' scatter mpg weight, mcolor(fg)
_cg_scheme cgb09 `"color background bg"'
_cg_probe bgfg_09 bgfg scheme cgb09 marker - `"sa: color background bg"' scatter mpg weight
_cg_scheme cgb10 `"color background fg"'
_cg_probe bgfg_10 bgfg scheme cgb10 marker - `"sb: color background fg"' scatter mpg weight
_cg_scheme cgb11 `"color foreground bg"' `"color p1 fg"'
_cg_probe bgfg_11 bgfg scheme cgb11 marker - `"sc: color foreground bg; color p1 fg"' scatter mpg weight
_cg_scheme cgb12 `"color foreground fg"' `"color p1 fg"'
_cg_probe bgfg_12 bgfg scheme cgb12 marker - `"sd: color foreground fg; color p1 fg"' scatter mpg weight
_cg_scheme cgb13 `"color background navy*.5"' `"color p1 bg"'
_cg_probe bgfg_13 bgfg scheme cgb13 marker - `"si: color background navy*.5; color p1 bg"' scatter mpg weight
_cg_scheme cgb14 `"color background red"' `"color foreground bg"' `"color p1 fg"'
_cg_probe bgfg_14 bgfg scheme cgb14 marker - `"sj: color background red; color foreground bg; color p1 fg"' scatter mpg weight
_cg_probe site_01 site option s2color line - `"line mpg weight, lcolor(navy*.5)"' line mpg weight, lcolor(navy*.5)
_cg_probe site_02 site option s2color line - `"line mpg weight, lcolor(bogus)"' line mpg weight, lcolor(bogus)
_cg_probe site_03 site option s2color bar - `"bar mpg rep78 if rep78<., lcolor(none) fcolor(bogus)"' bar mpg rep78 if rep78<., lcolor(none) fcolor(bogus)
_cg_probe site_04 site option s2color bar - `"bar mpg rep78 if rep78<., lcolor(none) color(navy*.5)"' bar mpg rep78 if rep78<., lcolor(none) color(navy*.5)
_cg_probe site_05 site option s2color text - `"scatter mpg weight, title("T", color(bogus))"' scatter mpg weight, title("T", color(bogus))
_cg_probe site_06 site option s2color text - `"scatter mpg weight, title("T", color(navy*.5))"' scatter mpg weight, title("T", color(navy*.5))
_cg_probe site_07 site option s2color refline - `"scatter mpg weight, xline(3000, lcolor(bogus))"' scatter mpg weight, xline(3000, lcolor(bogus))
_cg_probe site_08 site option s2color region - `"scatter mpg weight, graphregion(color(bogus))"' scatter mpg weight, graphregion(color(bogus))
_cg_probe site_09 site option s2color mlabel S43 `"scatter mpg weight, mlabel(make) mlabcolor(bogus)"' scatter mpg weight, mlabel(make) mlabcolor(bogus)
_cg_probe site_10 site option s2color bar S43 `"bar mpg rep78 if rep78<., color(bogus)"' bar mpg rep78 if rep78<., color(bogus)
_cg_probe comma_01 comma option s2color refusal - `""255,0,128""' scatter mpg weight, mcolor("255,0,128")
_cg_probe comma_02 comma option s2color refusal - `""255, 0, 128""' scatter mpg weight, mcolor("255, 0, 128")
_cg_probe comma_03 comma option s2color refusal - `""1,2,3""' line mpg weight, lcolor("1,2,3")
_cg_probe comma_04 comma option s2color refusal - `""red,blue""' scatter mpg weight, mcolor("red,blue")
_cg_probe comma_05 comma option s2color refusal - `""1,""' scatter mpg weight, mcolor("1,")
_cg_probe comma_06 comma option s2color refusal - `""1,,2""' scatter mpg weight, mcolor("1,,2")
_cg_probe comma_07 comma option s2color refusal - `""1,2,3""' scatter mpg weight, bgcolor("1,2,3")

quietly cd `"`_cg_home'"'

python:
import json, os, re, sys
from collections import Counter
from sfi import Macro

G = Macro.getGlobal
sys.path.insert(0, os.path.join(G("CG_REPO"), "scripts"))
from svg_truth import svg_document  # noqa: E402

work = G("CG_WORK")
written = [os.path.join(work, "git_head.txt")]
written += [os.path.join(work, "scheme-%s.scheme" % s)
            for s in G("CG_SCHEMES").split()]


def _dominant(items):
    c = Counter(items)
    return c.most_common(1)[0][0] if c else (None, None)


def _hex(c):
    return c.lower() if c else c


probes = {}
for pid in G("CG_IDS").split():
    kind = G("CGK_" + pid)
    rec = {"group": G("CGG_" + pid), "context": G("CGX_" + pid),
           "scheme": G("CGS_" + pid), "value": G("CGV_" + pid),
           "command": G("CGC_" + pid), "kind": kind,
           "rc": int(float(G("CGR_" + pid))), "notes": [], "refusal": None,
           "fill": None, "opacity": None, "region": None, "vstrokes": [],
           "owner": None if G("CGO_" + pid) == "-" else G("CGO_" + pid)}
    stem = G("CGF_" + pid)
    logp = os.path.join(work, stem + ".log")
    if os.path.exists(logp):
        with open(logp, encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                s = ln.strip()
                if s.startswith("(note:"):
                    rec["notes"].append(s)
                elif s.startswith("invalid '"):
                    rec["refusal"] = s
        written.append(logp)
    svg = os.path.join(work, stem + ".svg")
    if os.path.exists(svg):
        written.append(svg)
        doc = svg_document(svg)
        rects = doc["rects"]
        # rects[0] is the canvas; rects[1] the graph region (its colour).
        rec["region"] = _hex(rects[1]["fill"]) if len(rects) > 1 else None
        rec["vstrokes"] = sorted({_hex(d["stroke"]) for d in doc["vlines"]
                                  if d.get("stroke")})
        items = []
        if kind == "marker":
            circ = [c for c in doc["circles"]
                    if c.get("fill") and c["fill"] != "none" and c.get("r")]
            if circ:
                rmax = max(c["r"] for c in circ)
                items = [(_hex(c["fill"]), c.get("fill_opacity"))
                         for c in circ if c["r"] == rmax]
        elif kind == "line":
            items = [(_hex(p["stroke"]), p.get("stroke_opacity"))
                     for p in doc["paths"]
                     if (p.get("fill") in (None, "none")) and p.get("stroke")
                     and p["stroke"] != "none"]
        elif kind == "bar":
            w = doc["canvas"]["w"] if doc["canvas"] else 0
            items = [(_hex(r["fill"]), None) for r in rects
                     if r.get("w") and 0 < r["w"] < w / 3.0
                     and r.get("fill") not in (None, "none")]
        elif kind in ("text", "mlabel"):
            items = [(_hex(t["fill"]), None) for t in doc["texts"]
                     if (kind == "text" and t["text"] == "T")
                     or (kind == "mlabel" and t["text"] == "AMC Concord")]
        rec["fill"], rec["opacity"] = _dominant(items)
    probes[pid] = rec

excluded = {}
for pid, rec in probes.items():
    if rec["group"] == "opt" and rec["value"] == "navy*52":
        excluded[pid] = "UNCLEAR clamp at an exact half (research p1-13 section 3)"
    if rec["group"] == "bgfg" and rec["value"].startswith("sj:"):
        excluded[pid] = "UNCLEAR: color foreground bg after color background red"

try:
    with open(os.path.join(work, "git_head.txt"), encoding="utf-8") as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out = {"_meta": {"stata_version": G("CG_VERSION"), "born_date": G("CG_BORN"),
                 "dash_commit": commit, "extracted": G("CG_WHEN"),
                 "excluded": excluded},
       "probes": probes}
with open(G("CG_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
for p in written:
    try:
        os.remove(p)
    except OSError:
        pass
try:
    os.rmdir(work)
except OSError:
    pass
print("colour_grammar_truth: wrote %d probes" % len(probes))
end
