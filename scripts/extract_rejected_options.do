*! extract_rejected_options.do -- regenerate the option-surface record
*! test/fixtures/rejected_options.json from live Stata: run the probe corpus
*! test/fixtures/twoway_corpus.do (each probe captures `twoway ..., nodraw'
*! and `dash ..., name(g1)' and writes id, both rcs, the plot spec, options
*! and dash's spec JSON), log it, and fold the results file, the log's
*! per-probe dash line (after the "@@P@@ <id>" marker) and the section-26
*! version results into the record.  Every rc, spec JSON and dash message
*! is measured; the task-05-01 annotations (disposition, reason, takes_
*! argument, the option's 05-01 rejection message, the construct and
*! accepted-but-discarded prose) are constants below, keyed by option or
*! probe id, so a probe dropped from the corpus is reported, not invented.
*! Strings in the python block spell a backtick \x60 and a dollar \x24.
*!
*! Output: test/fixtures/rejected_options.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_rejected_options.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 255

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_rejected_options.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_rejected_options.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'"
global dash_nobrowser 1

local work "`c(tmpdir)'dash_rejected_options_probe"
capture mkdir "`work'"
quietly shell git -C "`repo'" rev-parse HEAD > "`work'/git_head.txt"
quietly shell git -C "`repo'" rev-parse --abbrev-ref HEAD > "`work'/git_branch.txt"

* The corpus writes its results files into the working directory and starts
* with -clear all-; the locals above survive it, the globals are set after.
local here `"`c(pwd)'"'
quietly cd "`work'"
capture log close _zr
log using "`work'/corpus.log", text replace name(_zr)
do "`repo'/test/fixtures/twoway_corpus.do"
log close _zr
quietly cd `"`here'"'
version `=c(stata_version)'

global dash_nobrowser 1
global ZR_OUT "`repo'/test/fixtures/rejected_options.json"
global ZR_WORK "`work'"
global ZR_VERSION "`c(stata_version)'"
global ZR_BORN "`c(born_date)'"
global ZR_WHEN "`c(current_date)' `c(current_time)'"

python:
import datetime, json, os, re
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


# Task 05-01's annotations, keyed by option / probe id (constants).
NOTES = {"schema_version": 1,
 "plan_task": "05-01",
 "purpose": ("Measured record of the twoway options and syntax task 05-01 found dash "
             "refusing: each probe runs one option under twoway and under dash on the "
             "same command and records both return codes, dash\x27s message and dash\x27s "
             "spec JSON, remeasured from test/fixtures/twoway_corpus.do whenever this "
             "script runs."),
 "method": {"per_probe": ("1) run \x60twoway <spec>, <opts> nodraw\x60 under -capture- and "
                          "record rc; a non-zero rc means the probe is not legal Stata and "
                          "was fixed, not recorded. 2) \x60dash clear\x60. 3) run \x60dash "
                          "<spec>, <opts> name(g1)\x60 under -capture noisily- and record rc "
                          "plus the exact error line. 4) on success, record \x24{dash_json_g1}, "
                          "the spec JSON handed to dash_render.py."),
            "attribution": ("Where Stata requires a companion option (droplines needs range(); "
                            "clegend needs colorvar(); mlabangle needs mlabel(); colorlist needs "
                            "colordiscrete), the companion is passed to twoway ONLY, so the dash "
                            "side sees the option under test alone and the dash rc is attributable "
                            "to exactly one option key."),
            "controls": ("41 zero-option plottype controls establish the per-plottype baseline, "
                         "so a non-zero dash rc below is attributable to the option and not "
                         "to the plottype.")},
 "environment_data": ("sysuse auto (cross-sectional probes); synthetic 60-month tsset panel "
                      "(t* probes)"),
 "root_cause": ("dash\x27s option parsers are closed syntax allow-lists that declare every "
                "twoway option this corpus probes, so each probe twoway draws runs in "
                "dash (dash_rc 0) but play(), which dash refuses as its help documents, "
                "and an option dash takes without drawing is named in the command\x27s "
                "note and listed in dash.sthlp\x27s Unsupported section."),
 "dash_only_note": ("Section 27 of the corpus: every key dash once took that twoway does "
                    "not is now refused as twoway refuses it (dash_rc 198), the synonyms "
                    "with a second line naming twoway\x27s spelling (DECISIONS P4-7, D53) and "
                    "mlabwidth(), link() and filter() on a plot as options twoway does not "
                    "take there; blcolor(), bfcolor() and bgcolor() are twoway options, "
                    "taken by both."),
 "accepted_option_keys_probed": ["aspectratio",
                                 "barwidth",
                                 "base",
                                 "bwidth",
                                 "by",
                                 "caption",
                                 "cmissing",
                                 "colorcuts",
                                 "colordiscrete",
                                 "coloruseplegend",
                                 "colorvar",
                                 "connect",
                                 "degree",
                                 "fcolor",
                                 "fintensity",
                                 "graphregion",
                                 "jitter",
                                 "lcolor",
                                 "legend",
                                 "lpattern",
                                 "lwidth",
                                 "mcolor",
                                 "mfcolor",
                                 "mlabcolor",
                                 "mlabel",
                                 "mlabgap",
                                 "mlabposition",
                                 "mlabsize",
                                 "mlcolor",
                                 "msangle",
                                 "msize",
                                 "msymbol",
                                 "name",
                                 "note",
                                 "plotregion",
                                 "pstyle",
                                 "recast",
                                 "saving",
                                 "scheme",
                                 "subtitle",
                                 "title",
                                 "xaxis",
                                 "xlabel",
                                 "xline",
                                 "xscale",
                                 "xtitle",
                                 "yaxis",
                                 "ylabel",
                                 "yline",
                                 "yscale",
                                 "ytitle"],
 "blocking_defect": {"id": "version-regex-blocker",
                     "severity": "blocker",
                     "summary": ("The graph-name check that refused every graph under an "
                                 "older version statement no longer depends on the "
                                 "regular-expression engine that statement selects: dash "
                                 "registers g1 under each version measured below "
                                 "(dash_rc 0)."),
                     "note": ("This must be measured with STRAIGHT-LINE \x60version\x60 statements. "
                              "Inside a -foreach- loop the body is compiled under the ambient version, "
                              "so c(version) reads 16 while regexm() still uses the new engine "
                              "and the bug hides. Section 26 of the corpus does it straight-line.")},
 "rejected_options": [["acolor",
                       True,
                       "option acolor() not allowed",
                       "rc0-at-c96facd",
                       "CI/fit area look (fitarea_options).",
                       ["lfitci_acolor"]],
                      ["adjust",
                       False,
                       "option adjust not allowed",
                       "rc0-at-c96facd",
                       "lowess estimation control.",
                       ["lowess_adjust"]],
                      ["alalign",
                       True,
                       "option alalign() not allowed",
                       "rc0-at-c96facd",
                       "line alignment for a filled outline.",
                       ["lfitci_alalign"]],
                      ["alpattern",
                       True,
                       "option alpattern() not allowed",
                       "rc0-at-c96facd",
                       "CI/fit area look (fitarea_options).",
                       ["lfitci_alpattern"]],
                      ["alstyle",
                       True,
                       "option alstyle() not allowed",
                       "rc0-at-c96facd",
                       ("overall style shorthand (mstyle/lstyle/astyle/bstyle/dstyle/alstyle). "
                        "dash has pstyle() only."),
                       ["lfitci_alstyle"]],
                      ["alwidth",
                       True,
                       "option alwidth() not allowed",
                       "rc0-at-c96facd",
                       "CI/fit area look (fitarea_options).",
                       ["lfitci_alwidth"]],
                      ["area",
                       True,
                       "option area() not allowed",
                       "rc0-at-c96facd",
                       ("kernel-density / local-polynomial estimation parameter. dash recomputes "
                        "the smooth in JS; these are the knobs that decide what is computed."),
                       ["kd_area"]],
                      ["astyle",
                       True,
                       "option astyle() not allowed",
                       "honoured-WP-30-P1.14a",
                       ("overall style shorthand (mstyle/lstyle/astyle/bstyle/dstyle/alstyle). "
                        "dash has pstyle() only."),
                       ["astyle",
                        "lfitci_astyle"]],
                      ["atobs",
                       False,
                       "option atobs not allowed",
                       "rc0-at-c96facd",
                       "fit/CI estimation control (ciopts/fitopts family).",
                       ["lfit_atobs"]],
                      ["b1title",
                       True,
                       "option b1title() not allowed",
                       "rc0-at-c96facd",
                       ("outer title band (t1/t2/b1/b2/l1/l2/r1/r2). dash implements only "
                        "title/subtitle/note/caption."),
                       ["b1title"]],
                      ["b2title",
                       True,
                       "option b2title() not allowed",
                       "rc0-at-c96facd",
                       ("outer title band (t1/t2/b1/b2/l1/l2/r1/r2). dash implements only "
                        "title/subtitle/note/caption."),
                       ["b2title"]],
                      ["bands",
                       True,
                       "option bands() not allowed",
                       "rc0-at-c96facd",
                       ("kernel-density / local-polynomial estimation parameter. dash recomputes "
                        "the smooth in JS; these are the knobs that decide what is computed."),
                       ["mband_bands",
                        "mspline_bands"]],
                      ["barbsize",
                       True,
                       "option barbsize() not allowed",
                       "rc0-at-c96facd",
                       "paired-coordinate arrow look (twoway pcarrow).",
                       ["pcarrow_barbsize"]],
                      ["baroffset",
                       True,
                       "option baroffset() not allowed",
                       "rc0-at-c96facd",
                       "bar geometry beyond barwidth().",
                       ["rbar_baroffset",
                        "bar_baroffset"]],
                      ["bin",
                       True,
                       "option bin() not allowed",
                       "rc0-at-c96facd",
                       ("twoway histogram binning control; dash hard-codes its own binning "
                        "in dash_render.py and cannot honour the user request."),
                       ["hist_bin"]],
                      ["bstyle",
                       True,
                       "option bstyle() not allowed",
                       "honoured-WP-30-P1.14a",
                       ("overall style shorthand (mstyle/lstyle/astyle/bstyle/dstyle/alstyle). "
                        "dash has pstyle() only."),
                       ["bstyle"]],
                      ["ciplot",
                       True,
                       "option ciplot() not allowed",
                       "rc0-at-c96facd",
                       "fit/CI estimation control (ciopts/fitopts family).",
                       ["lfitci_ciplot"]],
                      ["clegend",
                       True,
                       "option clegend() not allowed",
                       "rc0-at-c96facd",
                       "colour legend for a colorvar plot.",
                       ["clegend"]],
                      ["color",
                       True,
                       "option color() not allowed",
                       "rc0-at-c96facd",
                       ("area/bar single-colour shorthand. Stata users reach for color() "
                        "far more often than fcolor()+lcolor(), and it aborts."),
                       ["color_area"]],
                      ["colorend",
                       True,
                       "option colorend() not allowed",
                       "rc0-at-c96facd",
                       ("colorvar colour-mapping control. dash implements a colorvar family "
                        "under partly non-Stata spellings (colpalette/colornlevels/colormissing); "
                        "every real Stata spelling here aborts."),
                       ["colorend"]],
                      ["colorfillonly",
                       False,
                       "option colorfillonly not allowed",
                       "rc0-at-c96facd",
                       ("colorvar colour-mapping control. dash implements a colorvar family "
                        "under partly non-Stata spellings (colpalette/colornlevels/colormissing); "
                        "every real Stata spelling here aborts."),
                       ["colorfillonly"]],
                      ["colorformissing",
                       True,
                       "option colorformissing() not allowed",
                       "rc0-at-c96facd",
                       ("colorvar colour-mapping control. dash implements a colorvar family "
                        "under partly non-Stata spellings (colpalette/colornlevels/colormissing); "
                        "every real Stata spelling here aborts."),
                       ["colorformissing"]],
                      ["colorkeysrange",
                       False,
                       "option colorkeysrange not allowed",
                       "rc0-at-c96facd",
                       ("colorvar colour-mapping control. dash implements a colorvar family "
                        "under partly non-Stata spellings (colpalette/colornlevels/colormissing); "
                        "every real Stata spelling here aborts."),
                       ["colorkeysrange"]],
                      ["colorlevels",
                       True,
                       "option colorlevels() not allowed",
                       "rc0-at-c96facd",
                       ("colorvar colour-mapping control. dash implements a colorvar family "
                        "under partly non-Stata spellings (colpalette/colornlevels/colormissing); "
                        "every real Stata spelling here aborts."),
                       ["colorlevels"]],
                      ["colorlist",
                       True,
                       "option colorlist() not allowed",
                       "rc0-at-c96facd",
                       ("colorvar colour-mapping control. dash implements a colorvar family "
                        "under partly non-Stata spellings (colpalette/colornlevels/colormissing); "
                        "every real Stata spelling here aborts."),
                       ["colorlist"]],
                      ["colorrule",
                       True,
                       "option colorrule() not allowed",
                       "rc0-at-c96facd",
                       ("colorvar colour-mapping control. dash implements a colorvar family "
                        "under partly non-Stata spellings (colpalette/colornlevels/colormissing); "
                        "every real Stata spelling here aborts."),
                       ["colorrule"]],
                      ["colorstart",
                       True,
                       "option colorstart() not allowed",
                       "rc0-at-c96facd",
                       ("colorvar colour-mapping control. dash implements a colorvar family "
                        "under partly non-Stata spellings (colpalette/colornlevels/colormissing); "
                        "every real Stata spelling here aborts."),
                       ["colorstart"]],
                      ["colorvarminmax",
                       False,
                       "option colorvarminmax not allowed",
                       "rc0-at-c96facd",
                       ("colorvar colour-mapping control. dash implements a colorvar family "
                        "under partly non-Stata spellings (colpalette/colornlevels/colormissing); "
                        "every real Stata spelling here aborts."),
                       ["colorvarminmax"]],
                      ["dcolor",
                       True,
                       "option dcolor() not allowed",
                       "rc0-at-c96facd",
                       ("dot-plot look (twoway dot). dash renders dot plots but accepts none "
                        "of the d* look options."),
                       ["dot_dcolor"]],
                      ["density",
                       False,
                       "option density not allowed",
                       "rc0-at-c96facd",
                       ("twoway histogram y-axis scaling family (density/fraction/frequency/percent). "
                        "dash always renders raw counts, so the y axis silently means something "
                        "other than what the user asked for."),
                       ["hist_density"]],
                      ["dfcolor",
                       True,
                       "option dfcolor() not allowed",
                       "rc0-at-c96facd",
                       ("dot-plot look (twoway dot). dash renders dot plots but accepts none "
                        "of the d* look options."),
                       ["dot_dfcolor"]],
                      ["discrete",
                       False,
                       "option discrete not allowed",
                       "rc0-at-c96facd",
                       ("twoway histogram binning control; dash hard-codes its own binning "
                        "in dash_render.py and cannot honour the user request."),
                       ["hist_discrete"]],
                      ["dlalign",
                       True,
                       "option dlalign() not allowed",
                       "rc0-at-c96facd",
                       "line alignment for a filled outline.",
                       ["dot_dlalign"]],
                      ["dlcolor",
                       True,
                       "option dlcolor() not allowed",
                       "rc0-at-c96facd",
                       ("dot-plot look (twoway dot). dash renders dot plots but accepts none "
                        "of the d* look options."),
                       ["dot_dlcolor"]],
                      ["dlstyle",
                       True,
                       "option dlstyle() not allowed",
                       "rc0-at-c96facd",
                       ("dot-plot look (twoway dot). dash renders dot plots but accepts none "
                        "of the d* look options."),
                       ["dot_dlstyle"]],
                      ["dlwidth",
                       True,
                       "option dlwidth() not allowed",
                       "rc0-at-c96facd",
                       ("dot-plot look (twoway dot). dash renders dot plots but accepts none "
                        "of the d* look options."),
                       ["dot_dlwidth"]],
                      ["dotextend",
                       True,
                       "option dotextend() not allowed",
                       "rc0-at-c96facd",
                       ("dot-plot look (twoway dot). dash renders dot plots but accepts none "
                        "of the d* look options."),
                       ["dot_dotextend"]],
                      ["droplines",
                       True,
                       "option droplines() not allowed",
                       "rc0-at-c96facd",
                       ("vertical drop lines from the curve to the base, i.e. added-line "
                        "geometry."),
                       ["fn_droplines"]],
                      ["dsize",
                       True,
                       "option dsize() not allowed",
                       "rc0-at-c96facd",
                       ("dot-plot look (twoway dot). dash renders dot plots but accepts none "
                        "of the d* look options."),
                       ["dot_dsize"]],
                      ["dstyle",
                       True,
                       "option dstyle() not allowed",
                       "rc0-at-c96facd",
                       ("overall style shorthand (mstyle/lstyle/astyle/bstyle/dstyle/alstyle). "
                        "dash has pstyle() only."),
                       ["dot_dstyle"]],
                      ["dsymbol",
                       True,
                       "option dsymbol() not allowed",
                       "rc0-at-c96facd",
                       ("dot-plot look (twoway dot). dash renders dot plots but accepts none "
                        "of the d* look options."),
                       ["dot_dsymbol"]],
                      ["estcmd",
                       True,
                       "option estcmd() not allowed",
                       "rc0-at-c96facd",
                       "fit/CI estimation control (ciopts/fitopts family).",
                       ["fpfit_estcmd"]],
                      ["estopts",
                       True,
                       "option estopts() not allowed",
                       "rc0-at-c96facd",
                       "fit/CI estimation control (ciopts/fitopts family).",
                       ["lfit_estopts",
                        "fpfit_estopts",
                        "fpfit_powers"]],
                      ["fitplot",
                       True,
                       "option fitplot() not allowed",
                       "rc0-at-c96facd",
                       "fit/CI estimation control (ciopts/fitopts family).",
                       ["lfitci_fitplot"]],
                      ["fraction",
                       False,
                       "option fraction not allowed",
                       "rc0-at-c96facd",
                       ("twoway histogram y-axis scaling family (density/fraction/frequency/percent). "
                        "dash always renders raw counts, so the y axis silently means something "
                        "other than what the user asked for."),
                       ["hist_fraction"]],
                      ["frequency",
                       False,
                       "option frequency not allowed",
                       "rc0-at-c96facd",
                       ("twoway histogram y-axis scaling family (density/fraction/frequency/percent). "
                        "dash always renders raw counts, so the y axis silently means something "
                        "other than what the user asked for."),
                       ["hist_frequency"]],
                      ["fxsize",
                       True,
                       "option fxsize() not allowed",
                       "rc0-at-c96facd",
                       "physical graph size / combine sizing / global text-and-marker scaling.",
                       ["fxsize"]],
                      ["fysize",
                       True,
                       "option fysize() not allowed",
                       "rc0-at-c96facd",
                       "physical graph size / combine sizing / global text-and-marker scaling.",
                       ["fysize"]],
                      ["gap",
                       True,
                       "option gap() not allowed",
                       "rc0-at-c96facd",
                       "bar geometry beyond barwidth().",
                       ["hist_gap"]],
                      ["headlabel",
                       False,
                       "option headlabel not allowed",
                       "rc0-at-c96facd",
                       "paired-coordinate arrow look (twoway pcarrow).",
                       ["pcarrow_headlabel"]],
                      ["horizontal",
                       False,
                       "option horizontal not allowed",
                       "honoured-WP-30-P1.9a",
                       ("plot orientation. dash renders bar/spike/dropline/dot/rbar/rcap/histogram/kdensity "
                        "but accepts neither orientation keyword."),
                       ["hist_horizontal",
                        "kd_horizontal",
                        "fn_horizontal",
                        "rbar_horizontal",
                        "bar_horizontal",
                        "dropline_horiz",
                        "rcap_horizontal",
                        "spike_horizontal",
                        "dot_horizontal"]],
                      ["jitterseed",
                       True,
                       "option jitterseed() not allowed",
                       "rc0-at-c96facd",
                       ("reproducible jitter. dash implements jitter() and invented its own "
                        "jseed() spelling; Stata spells it jitterseed(), so the Stata spelling "
                        "aborts."),
                       ["jitterseed"]],
                      ["kernel",
                       True,
                       "option kernel() not allowed",
                       "rc0-at-c96facd",
                       ("kernel-density / local-polynomial estimation parameter. dash recomputes "
                        "the smooth in JS; these are the knobs that decide what is computed."),
                       ["lpoly_kernel",
                        "kd_kernel"]],
                      ["l1title",
                       True,
                       "option l1title() not allowed",
                       "rc0-at-c96facd",
                       ("outer title band (t1/t2/b1/b2/l1/l2/r1/r2). dash implements only "
                        "title/subtitle/note/caption."),
                       ["l1title"]],
                      ["l2title",
                       True,
                       "option l2title() not allowed",
                       "rc0-at-c96facd",
                       ("outer title band (t1/t2/b1/b2/l1/l2/r1/r2). dash implements only "
                        "title/subtitle/note/caption."),
                       ["l2title"]],
                      ["lalign",
                       True,
                       "option lalign() not allowed",
                       "rc0-at-c96facd",
                       "line alignment for a filled outline.",
                       ["lalign"]],
                      ["level",
                       True,
                       "option level() not allowed",
                       "rc0-at-c96facd",
                       "fit/CI estimation control (ciopts/fitopts family).",
                       ["lfitci_level"]],
                      ["logit",
                       False,
                       "option logit not allowed",
                       "rc0-at-c96facd",
                       "lowess estimation control.",
                       ["lowess_logit"]],
                      ["lstyle",
                       True,
                       "option lstyle() not allowed",
                       "honoured-WP-30-P1.14a",
                       ("overall style shorthand (mstyle/lstyle/astyle/bstyle/dstyle/alstyle). "
                        "dash has pstyle() only."),
                       ["lstyle"]],
                      ["mangle",
                       True,
                       "option mangle() not allowed",
                       "rc0-at-c96facd",
                       "paired-coordinate arrow look (twoway pcarrow).",
                       ["pcarrow_mangle"]],
                      ["mean",
                       False,
                       "option mean not allowed",
                       "rc0-at-c96facd",
                       "lowess estimation control.",
                       ["lowess_mean"]],
                      ["mlabangle",
                       True,
                       "option mlabangle() not allowed",
                       "rc0-at-c96facd",
                       "marker-label look beyond the five keys dash implements.",
                       ["mlabangle"]],
                      ["mlabformat",
                       True,
                       "option mlabformat() not allowed",
                       "rc0-at-c96facd",
                       "marker-label look beyond the five keys dash implements.",
                       ["mlabformat"]],
                      ["mlabstyle",
                       True,
                       "option mlabstyle() not allowed",
                       "rc0-at-c96facd",
                       "marker-label look beyond the five keys dash implements.",
                       ["mlabstyle"]],
                      ["mlabtextstyle",
                       True,
                       "option mlabtextstyle() not allowed",
                       "honoured-WP-30-P1.24",
                       "marker-label look beyond the five keys dash implements.",
                       ["mlabtextstyle"]],
                      ["mlabvposition",
                       True,
                       "option mlabvposition() not allowed",
                       "honoured-WP-30-P1.24",
                       "marker-label look beyond the five keys dash implements.",
                       ["mlabvposition"]],
                      ["mlalign",
                       True,
                       "option mlalign() not allowed",
                       "rc0-at-c96facd",
                       ("marker outline look. dash implements mcolor/mfcolor/mlcolor but "
                        "not the outline width/alignment/style."),
                       ["mlalign"]],
                      ["mlstyle",
                       True,
                       "option mlstyle() not allowed",
                       "honoured-WP-30-P1.14a",
                       ("marker outline look. dash implements mcolor/mfcolor/mlcolor but "
                        "not the outline width/alignment/style."),
                       ["mlstyle"]],
                      ["mlwidth",
                       True,
                       "option mlwidth() not allowed",
                       "rc0-at-c96facd",
                       ("marker outline look. dash implements mcolor/mfcolor/mlcolor but "
                        "not the outline width/alignment/style."),
                       ["mlwidth"]],
                      ["mstyle",
                       True,
                       "option mstyle() not allowed",
                       "honoured-WP-30-P1.14a",
                       ("overall style shorthand (mstyle/lstyle/astyle/bstyle/dstyle/alstyle). "
                        "dash has pstyle() only."),
                       ["mstyle",
                        "pcarrow_mstyle"]],
                      ["mwidth",
                       False,
                       "option mwidth not allowed",
                       "rc0-at-c96facd",
                       "bar geometry beyond barwidth().",
                       ["rbar_mwidth"]],
                      ["n",
                       True,
                       "option n() not allowed",
                       "rc0-at-c96facd",
                       ("kernel-density / local-polynomial estimation parameter. dash recomputes "
                        "the smooth in JS; these are the knobs that decide what is computed."),
                       ["lfit_n",
                        "lpoly_n",
                        "mspline_n",
                        "kd_n",
                        "fn_n"]],
                      ["ndots",
                       True,
                       "option ndots() not allowed",
                       "rc0-at-c96facd",
                       ("dot-plot look (twoway dot). dash renders dot plots but accepts none "
                        "of the d* look options."),
                       ["dot_ndots"]],
                      ["nodraw",
                       False,
                       "option nodraw not allowed",
                       "honoured-nobrowser",
                       ("suppresses the Stata graph window. dash honours it by not opening "
                        "the browser window, on an immediate render and on dash build (WP-13); "
                        "it is not named in the note."),
                       ["nodraw"]],
                      ["nodropbase",
                       False,
                       "option nodropbase not allowed",
                       "rc0-at-c96facd",
                       "area baseline suppression.",
                       ["area_nodropbase"]],
                      ["nofit",
                       False,
                       "option nofit not allowed",
                       "rc0-at-c96facd",
                       "fit/CI estimation control (ciopts/fitopts family).",
                       ["lfitci_nofit"]],
                      ["noweight",
                       False,
                       "option noweight not allowed",
                       "rc0-at-c96facd",
                       "lowess estimation control.",
                       ["lowess_noweight"]],
                      ["pcycle",
                       True,
                       "option pcycle() not allowed",
                       "rc0-at-c96facd",
                       "plot-style cycling across layers.",
                       ["pcycle"]],
                      ["percent",
                       False,
                       "option percent not allowed",
                       "rc0-at-c96facd",
                       ("twoway histogram y-axis scaling family (density/fraction/frequency/percent). "
                        "dash always renders raw counts, so the y axis silently means something "
                        "other than what the user asked for."),
                       ["hist_percent"]],
                      ["play",
                       True,
                       "option play() not allowed",
                       "accept-and-report",
                       "replays a Graph Editor recording against a .gph graph. No HTML equivalent.",
                       ["play"]],
                      ["plegend",
                       True,
                       "option plegend() not allowed",
                       "rc0-at-c96facd",
                       "colour legend for a colorvar plot.",
                       ["plegend"]],
                      ["predopts",
                       True,
                       "option predopts() not allowed",
                       "rc0-at-c96facd",
                       "fit/CI estimation control (ciopts/fitopts family).",
                       ["lfit_predopts"]],
                      ["r1title",
                       True,
                       "option r1title() not allowed",
                       "rc0-at-c96facd",
                       ("outer title band (t1/t2/b1/b2/l1/l2/r1/r2). dash implements only "
                        "title/subtitle/note/caption."),
                       ["r1title"]],
                      ["r2title",
                       True,
                       "option r2title() not allowed",
                       "rc0-at-c96facd",
                       ("outer title band (t1/t2/b1/b2/l1/l2/r1/r2). dash implements only "
                        "title/subtitle/note/caption."),
                       ["r2title"]],
                      ["range",
                       True,
                       "option range() not allowed",
                       "rc0-at-c96facd",
                       "estimation range for a fit/smoother plot.",
                       ["lfit_range",
                        "kd_range",
                        "fn_range"]],
                      ["scale",
                       True,
                       "option scale() not allowed",
                       "rc0-at-c96facd",
                       "physical graph size / combine sizing / global text-and-marker scaling.",
                       ["scale"]],
                      ["sort",
                       False,
                       "option sort not allowed",
                       "rc0-at-c96facd",
                       ("sort-before-connect for line/area/connected. Without it a dash line "
                        "plot draws in dataset order; the option that fixes that aborts."),
                       ["line_sort",
                        "area_sort",
                        "connected_sort"]],
                      ["start",
                       True,
                       "option start() not allowed",
                       "rc0-at-c96facd",
                       ("twoway histogram binning control; dash hard-codes its own binning "
                        "in dash_render.py and cannot honour the user request."),
                       ["hist_start"]],
                      ["t1title",
                       True,
                       "option t1title() not allowed",
                       "rc0-at-c96facd",
                       ("outer title band (t1/t2/b1/b2/l1/l2/r1/r2). dash implements only "
                        "title/subtitle/note/caption."),
                       ["t1title"]],
                      ["t2title",
                       True,
                       "option t2title() not allowed",
                       "rc0-at-c96facd",
                       ("outer title band (t1/t2/b1/b2/l1/l2/r1/r2). dash implements only "
                        "title/subtitle/note/caption."),
                       ["t2title"]],
                      ["text",
                       True,
                       "option text() not allowed",
                       "honoured-WP-30-P1.10",
                       "in-plot text annotation at a (y,x) data coordinate.",
                       ["text",
                        "text_suboptions"]],
                      ["tlabel",
                       True,
                       "",
                       "implemented-WP-30-P1.6",
                       ("Declared with twoway\x27s abbreviations and folded onto its x twin "
                        "at registration, date literals read in the axis\x27s unit (WP-30 "
                        "P1.6)."),
                       ["tlabel"]],
                      ["tline",
                       True,
                       "",
                       "implemented-WP-30-P1.6",
                       ("Declared with twoway\x27s abbreviations and folded onto its x twin "
                        "at registration, date literals read in the axis\x27s unit (WP-30 "
                        "P1.6)."),
                       ["tline"]],
                      ["tmlabel",
                       True,
                       "",
                       "stored-and-named-WP-30-P1.6",
                       ("Declared with twoway\x27s abbreviations and folded onto the x minor "
                        "key at registration (WP-30 P1.6); named in the note until minor "
                        "ticks are drawn."),
                       ["tmlabel"]],
                      ["tmtick",
                       True,
                       "",
                       "stored-and-named-WP-30-P1.6",
                       ("Declared with twoway\x27s abbreviations and folded onto the x minor "
                        "key at registration (WP-30 P1.6); named in the note until minor "
                        "ticks are drawn."),
                       ["tmtick"]],
                      ["tscale",
                       True,
                       "",
                       "implemented-WP-30-P1.6",
                       ("Declared with twoway\x27s abbreviations and folded onto its x twin "
                        "at registration, date literals read in the axis\x27s unit (WP-30 "
                        "P1.6)."),
                       ["tscale"]],
                      ["ttext",
                       True,
                       "option ttext() not allowed",
                       "honoured-WP-30-P1.10",
                       ("time-axis spelling of an axis option dash already implements for "
                        "x/y. A tsset dataset plus tsline is the single most likely copy-paste "
                        "source for dash, and every t* option aborts."),
                       ["ttext"]],
                      ["ttick",
                       True,
                       "",
                       "implemented-WP-30-P1.6",
                       ("Declared with twoway\x27s abbreviations and folded onto its x twin "
                        "at registration, date literals read in the axis\x27s unit (WP-30 "
                        "P1.6)."),
                       ["ttick"]],
                      ["ttitle",
                       True,
                       "",
                       "implemented-WP-30-P1.6",
                       ("Declared with twoway\x27s abbreviations and folded onto its x twin "
                        "at registration, date literals read in the axis\x27s unit (WP-30 "
                        "P1.6)."),
                       ["ttitle"]],
                      ["vertical",
                       False,
                       "option vertical not allowed",
                       "honoured-WP-30-P1.9a",
                       ("plot orientation. dash renders bar/spike/dropline/dot/rbar/rcap/histogram/kdensity "
                        "but accepts neither orientation keyword."),
                       ["rbar_vertical",
                        "bar_vertical"]],
                      ["width",
                       True,
                       "option width() not allowed",
                       "rc0-at-c96facd",
                       ("twoway histogram binning control; dash hard-codes its own binning "
                        "in dash_render.py and cannot honour the user request."),
                       ["hist_width"]],
                      ["xmlabel",
                       True,
                       "option xmlabel() not allowed",
                       "rc0-at-c96facd",
                       ("axis tick/minor-tick/minor-label placement. dash implements only "
                        "xlabel()/ylabel() major ticks."),
                       ["xmlabel"]],
                      ["xmtick",
                       True,
                       "option xmtick() not allowed",
                       "rc0-at-c96facd",
                       ("axis tick/minor-tick/minor-label placement. dash implements only "
                        "xlabel()/ylabel() major ticks."),
                       ["xmtick"]],
                      ["xoverhangs",
                       False,
                       "option xoverhangs not allowed",
                       "accept-and-report",
                       "advanced label-overhang control in the graph region. No Bokeh equivalent.",
                       ["xoverhangs"]],
                      ["xsize",
                       True,
                       "option xsize() not allowed",
                       "rc0-at-c96facd",
                       "physical graph size / combine sizing / global text-and-marker scaling.",
                       ["xsize"]],
                      ["xtick",
                       True,
                       "option xtick() not allowed",
                       "rc0-at-c96facd",
                       ("axis tick/minor-tick/minor-label placement. dash implements only "
                        "xlabel()/ylabel() major ticks."),
                       ["xtick"]],
                      ["xvarformat",
                       True,
                       "option xvarformat() not allowed",
                       "honoured-WP-30-P1.5",
                       "axis title / tick format taken from the plotted variable.",
                       ["xvarformat"]],
                      ["xvarlabel",
                       True,
                       "option xvarlabel() not allowed",
                       "rc0-at-c96facd",
                       "axis title / tick format taken from the plotted variable.",
                       ["xvarlabel"]],
                      ["ymlabel",
                       True,
                       "option ymlabel() not allowed",
                       "rc0-at-c96facd",
                       ("axis tick/minor-tick/minor-label placement. dash implements only "
                        "xlabel()/ylabel() major ticks."),
                       ["ymlabel"]],
                      ["ymtick",
                       True,
                       "option ymtick() not allowed",
                       "rc0-at-c96facd",
                       ("axis tick/minor-tick/minor-label placement. dash implements only "
                        "xlabel()/ylabel() major ticks."),
                       ["ymtick"]],
                      ["yoverhangs",
                       False,
                       "option yoverhangs not allowed",
                       "accept-and-report",
                       "advanced label-overhang control in the graph region. No Bokeh equivalent.",
                       ["yoverhangs"]],
                      ["ysize",
                       True,
                       "option ysize() not allowed",
                       "rc0-at-c96facd",
                       "physical graph size / combine sizing / global text-and-marker scaling.",
                       ["ysize"]],
                      ["ytick",
                       True,
                       "option ytick() not allowed",
                       "rc0-at-c96facd",
                       ("axis tick/minor-tick/minor-label placement. dash implements only "
                        "xlabel()/ylabel() major ticks."),
                       ["ytick"]],
                      ["yvarformat",
                       True,
                       "option yvarformat() not allowed",
                       "honoured-WP-30-P1.5",
                       "axis title / tick format taken from the plotted variable.",
                       ["yvarformat"]],
                      ["yvarlabel",
                       True,
                       "option yvarlabel() not allowed",
                       "rc0-at-c96facd",
                       "axis title / tick format taken from the plotted variable.",
                       ["yvarlabel"]]],
 "rejected_syntax_constructs": [["ctl_function_yeq",
                                 "twoway function y=x",
                                 "=exp not allowed",
                                 "implement-S06",
                                 ("dash\x27s own help documents the y= form and dash.ado:630 strips "
                                  "a leading \x27y=\x27 -- but the strip runs AFTER _dash_parse_varpart_any, "
                                  "whose \x60syntax anything(name=vals)\x60 rejects the \x27=\x27 first. "
                                  "\x60dash function y=x\x60 dies with r(101) \x27=exp not allowed\x27; "
                                  "only the bare \x60dash function x\x60 form works.")],
                                ["ctl_aweight",
                                 "twoway scatter mpg weight [aweight=price]",
                                 "weights not allowed",
                                 "implement-S06",
                                 ("Weighted twoway plots abort with r(101) \x22weights not allowed\x22. "
                                  "Weights are extremely common in copy-pasted twoway code.")],
                                ["name_replace",
                                 "name(g1, replace)",
                                 ("dash: invalid graph name \x27g1, replace\x27. Names must start with "
                                  "a letter or under score and contain only letters, digits, and underscores "
                                  "(max 32 chars)."),
                                 "implement-S06",
                                 ("dash.sthlp documents name(name, replace) and _dash_register_graph "
                                  "(dash.ado:867) explicitly greps the raw spec for it -- but the name-format "
                                  "check at dash.ado:857 runs first on the whole string \x27g1, replace\x27 "
                                  "and rejects it with r(198). The documented replace sub-option is "
                                  "unreachable.")]],
 "accepted_but_discarded": [["abd_title_size",
                             "title(\x22T\x22, size(large))",
                             "title",
                             ("CORRUPTED, not merely dropped. title() is declared \x60string\x60 "
                              "(not \x60asis\x60), so -syntax- strips the quotes and dash re-joins "
                              "the remainder: the spec carries title=\x22T , size(large)\x22 and "
                              "the rendered Bokeh figure title literally reads \x60T , size(large)\x60."),
                             ("Rendered abd.html and found the exact text node \x22T , size(large)\x22 "
                              "as the figure title.")],
                            ["abd_legend_order",
                             "legend(order(1 2))",
                             "legend",
                             ("DROPPED. The string survives into the spec as legend=\x22order(1 "
                              "2)\x22, but dash_render.py:6283 only understands off/on/ring/top/bottom/left/right, "
                              "label(N \x22txt\x22), cols(#) and rows(#). order() is never parsed; "
                              "the substring \x22order(1 2)\x22 does not appear anywhere in the "
                              "rendered HTML, and legend item order is whatever the plot layers "
                              "happen to be in."),
                             "Rendered abd.html; searched for \x22order(1 2)\x22 -> absent."],
                            ["abd_ylabel_format",
                             "ylabel(, format(%9.0fc))",
                             "ylabel",
                             ("DROPPED. Spec carries ylabel=\x22, format(%9.0fc)\x22. DashRenderer._parse_axis_label_opt() "
                              "returns ([], {}) for it, so no FixedTicker and no formatter is attached "
                              "and the axis keeps Bokeh default numbering. Only xlabel()/ylabel() "
                              "angle() is honoured from the sub-option block."),
                             ("Executed DashRenderer._parse_axis_label_opt(\x22, format(%9.0fc)\x22) "
                              "-> ([], {}).")],
                            ["abd_xlabel_hash",
                             "xlabel(#10)",
                             "xlabel",
                             ("DROPPED. Spec carries xlabel=\x22#10\x22; the parser accepts only "
                              "bare numbers and quoted labels, so #10 yields ([], {}) and the \x22about "
                              "10 ticks\x22 request is lost."),
                             ("Executed DashRenderer._parse_axis_label_opt(\x22#10\x22) -> ([], "
                              "{}).")],
                            ["abd_xlabel_minmax",
                             "xlabel(minmax)",
                             "xlabel",
                             ("DROPPED. Spec carries xlabel=\x22minmax\x22; parser yields ([], "
                              "{})."),
                             ("Executed DashRenderer._parse_axis_label_opt(\x22minmax\x22) -> ([], "
                              "{}).")],
                            ["abd_xlabel_range",
                             "xlabel(1990(5)2020)",
                             "xlabel",
                             ("DROPPED. Spec carries xlabel=\x221990(5)2020\x22; the parser has "
                              "no numlist expander, so a Stata range-with-step -- the single most "
                              "common xlabel() form -- yields ([], {}). Note xlabel(10 20 30) (explicit "
                              "list) DOES work, which makes the failure silent and inconsistent."),
                             ("Executed DashRenderer._parse_axis_label_opt(\x221990(5)2020\x22) "
                              "-> ([], {}) and (\x2210 20 30 40\x22) -> ([10,20,30,40], {}).")],
                            ["abd_yscale_range",
                             "yscale(range(0 50))",
                             "yscale",
                             ("DROPPED. Spec carries yscale=\x22range(0 50)\x22. dash_render.py:_parse_scale_opt() "
                              "extracts only the words \x22log\x22 and \x22reverse\x22; range() "
                              "is never read, no Range1d is created, and the axis autoscales."),
                             ("Executed _parse_scale_opt(\x22range(0 50)\x22) -> (False, False); "
                              "rendered abd.html contains no Range1d model instance and no end:50.")],
                            ["abd_graphregion",
                             "graphregion(margin(zero))",
                             "graphregion",
                             ("DROPPED. Spec carries graphregion=\x22margin(zero)\x22. _extract_region_color() "
                              "looks only for color()/fcolor(); margin() returns \x22\x22 and nothing "
                              "is applied. graphregion(color(white)) does work, so again the failure "
                              "is silent and partial."),
                             ("Executed _extract_region_color(\x22margin(zero)\x22) -> \x22\x22 "
                              "and (\x22color(white)\x22) -> \x22white\x22.")],
                            ["abd_note_span",
                             "note(\x22n=74\x22, span)",
                             "note",
                             ("CORRUPTED, not merely dropped. note() is \x60string asis\x60, so "
                              "the raw text including the quotes and the sub-option survives verbatim: "
                              "the spec carries note=\x22\x5c\x22n=74\x5c\x22, span\x22 and the "
                              "rendered annotation reads &quot;n=74&quot;, span."),
                             ("Rendered abd.html and found the text node \x27&amp;quot;n=74&amp;quot;, "
                              "span\x27.")]],
 "dash_only_probes": ["only_mlabwidth",
                      "only_malpha",
                      "only_lalpha",
                      "only_falpha",
                      "only_blcolor",
                      "only_bfcolor",
                      "only_jseed",
                      "only_colpalette",
                      "only_colornlevels",
                      "only_colormissing",
                      "only_marker",
                      "only_bgcolor",
                      "only_plotbgcolor",
                      "only_link",
                      "only_filter",
                      "only_ytitle2",
                      "only_ylabel2",
                      "only_yscale2"]}


work = G("ZR_WORK")


def rd(name):
    try:
        with open(os.path.join(work, name), encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


# The corpus results: id, twoway_rc, dash_rc, plotspec, options,
# twoway_only_extra, dash spec JSON (empty unless dash_rc == 0).
rows = []
for ln in rd("twoway_corpus_results.txt").splitlines():
    if not ln.strip():
        continue
    f = ln.split("%%|%%", 6)
    if len(f) != 7:
        raise SystemExit("bad results line: " + ln[:80])
    rows.append(f)

# The log: the dash output after each "@@P@@ <id>" marker, up to the next
# marker or the next echoed command; Stata's "> " continuations re-joined.
out_by_id, cur = {}, None
for ln in rd("corpus.log").splitlines():
    if ln.startswith("@@P@@ "):
        cur = ln[6:].strip()
        out_by_id[cur] = []
        continue
    if cur is None:
        continue
    if ln.startswith(". ") or ln.startswith("@@V@@") or ln.startswith("BAD PROBE"):
        cur = None
        continue
    if ln.startswith("> ") and out_by_id[cur]:
        out_by_id[cur][-1] += ln[2:]
    elif ln.strip():
        out_by_id[cur].append(ln.strip())


def message(pid, rc):
    lines = out_by_id.get(pid, [])
    if rc == 0:
        reg = [x for x in lines if x.startswith("dash: graph ")]
        if reg:
            return reg[-1]
    return lines[-1] if lines else ""


def twoway_command(spec, opts, extra):
    tw = opts
    if extra:
        tw = (tw + " " + extra) if tw else extra
    if tw:
        return "twoway %s, %s%s" % (spec, tw, "" if "nodraw" in tw else " nodraw")
    return "twoway %s, nodraw" % spec


def dash_command(spec, opts):
    if opts:
        return "dash %s, %s%s" % (spec, opts, "" if "name(" in opts else " name(g1)")
    return "dash %s, name(g1)" % spec


probes, by_id = [], {}
for pid, twrc, drc, spec, opts, extra, js in rows:
    p = {"id": pid, "twoway_rc": int(twrc), "dash_rc": int(drc),
         "plotspec": spec, "options": opts, "twoway_only_extra": extra,
         "spec_json": js, "dash_message": message(pid, int(drc))}
    probes.append(p)
    by_id[pid] = p

missing = []


def probe(pid):
    if pid not in by_id:
        missing.append(pid)
        return None
    return by_id[pid]


rejected = []
for opt, takes, msg, disp, reason, ids in NOTES["rejected_options"]:
    sub = []
    for pid in ids:
        p = probe(pid)
        if p is None:
            continue
        sub.append({"id": pid,
                    "command": twoway_command(p["plotspec"], p["options"],
                                              p["twoway_only_extra"]),
                    "dash_command": dash_command(p["plotspec"], p["options"]),
                    "twoway_rc": p["twoway_rc"], "dash_rc": p["dash_rc"]})
    first = lambda k: next((q[k] for q in sub if q[k]), 0)
    rejected.append({"option": opt, "takes_argument": takes,
                     "twoway_rc": first("twoway_rc"), "dash_rc": first("dash_rc"),
                     "dash_message": msg, "disposition": disp, "reason": reason,
                     "probes": sub})

constructs = []
for pid, construct, msg, disp, reason in NOTES["rejected_syntax_constructs"]:
    p = probe(pid) or {}
    constructs.append({"probe_id": pid, "construct": construct,
                       "twoway_rc": p.get("twoway_rc"), "dash_rc": p.get("dash_rc"),
                       "dash_message": msg, "disposition": disp, "reason": reason})

discarded = []
for pid, opt, key, effect, verified in NOTES["accepted_but_discarded"]:
    p = probe(pid) or {}
    spec = json.loads(p["spec_json"]) if p.get("spec_json") else None
    val = (spec or {}).get("graph_options", {}).get(key)
    discarded.append({"probe_id": pid, "option": opt, "dash_rc": p.get("dash_rc"),
                      "graph_option_key": key, "value_in_spec_json": val,
                      "spec_json": spec, "effect": effect, "verified_by": verified})

dash_only = []
for pid in NOTES["dash_only_probes"]:
    p = probe(pid) or {}
    dash_only.append({"probe_id": pid, "options": p.get("options"),
                      "twoway_rc": p.get("twoway_rc"), "dash_rc": p.get("dash_rc"),
                      "is_real_twoway_option": p.get("twoway_rc") == 0})

measured = {}
for ln in rd("twoway_corpus_version_results.txt").splitlines():
    f = ln.split("%%|%%")
    if len(f) == 3:
        measured[f[0]] = {"regexm_matches_g1": int(f[1]), "dash_rc": int(f[2])}
defect = dict(NOTES["blocking_defect"])
defect["measured"] = measured
defect = {k: defect[k] for k in ("id", "severity", "summary", "measured", "note")}

tally = {}
for r in rejected:
    tally[r["disposition"]] = tally.get(r["disposition"], 0) + 1
summary = {
    "commands_probed": len(probes),
    "bad_probes_twoway_rejected": sum(1 for p in probes if p["twoway_rc"]
                                      and not p["id"].startswith("only_")),
    "dash_failures": sum(1 for p in probes if p["dash_rc"]),
    "distinct_rejected_option_keys": len(rejected),
    "rejected_syntax_constructs": len(constructs),
    "accepted_but_discarded": len(discarded),
    "by_disposition": dict(sorted(tally.items())),
}
commit = rd("git_head.txt").strip()
out = {
    "schema_version": NOTES["schema_version"],
    "generated_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "plan_task": NOTES["plan_task"],
    "purpose": NOTES["purpose"],
    "corpus": "test/fixtures/twoway_corpus.do",
    "method": NOTES["method"],
    "environment": {"stata": "Stata %s (born %s), batch through scripts/stata_slot.sh"
                             % (G("ZR_VERSION"), G("ZR_BORN")),
                    "dash_branch": rd("git_branch.txt").strip(),
                    "data": NOTES["environment_data"]},
    "root_cause": NOTES["root_cause"],
    "summary": summary,
    "blocking_defects": [defect],
    "dash_only_option_keys": dash_only,
    "dash_only_note": NOTES["dash_only_note"],
    "rejected_options": rejected,
    "rejected_syntax_constructs": constructs,
    "accepted_but_discarded": discarded,
    "accepted_option_keys_probed": NOTES["accepted_option_keys_probed"],
    "probes": probes,
    "_meta": {"stata_version": G("ZR_VERSION"), "born_date": G("ZR_BORN"),
              "dash_commit": commit, "extracted": G("ZR_WHEN"),
              "source": "scripts/extract_rejected_options.do",
              "corpus": "test/fixtures/twoway_corpus.do",
              "missing_probes": missing},
}
with open(G("ZR_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2)
    fh.write("\n")
for name in ("git_head.txt", "git_branch.txt"):
    try:
        os.remove(os.path.join(work, name))
    except OSError:
        pass
print("wrote", G("ZR_OUT"), len(probes), "probes; missing:", missing)
end
