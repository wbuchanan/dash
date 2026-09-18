*! twoway_corpus.do
*! Conformance corpus for the "drop-in twoway" claim in dash.sthlp:668-673:
*!   "No error is produced for unknown options, so existing Stata graph
*!    commands copy-pasted into dash will still run even when they contain
*!    options that have no Bokeh equivalent."
*!
*! WHAT THIS IS
*!   A runnable probe corpus over the documented option surface of -twoway-
*!   and its plottypes (help twoway_options, help scatter, help histogram,
*!   help kdensity, help lpoly, help lowess, help twoway_fpfit,
*!   help twoway_function, and the range / paired-coordinate families).
*!   For every probe the script measures TWO return codes:
*!
*!     twoway_rc : rc from real -twoway-, run with -nodraw-.  A probe whose
*!                 twoway_rc is non-zero is a BAD PROBE (the command is not
*!                 legal Stata); it is flagged in the log and must be fixed,
*!                 not recorded as a dash rejection.
*!     dash_rc   : rc from the identical plot spec + options run through -dash-
*!                 with name(g1) appended.
*!
*!   twoway_rc==0 && dash_rc!=0  =>  an option Stata accepts and dash rejects,
*!   i.e. a counter-example to the claim above.  dash's two -syntax- blocks
*!   (dash.ado:230 and dash.ado:293) are closed allow-lists invoked with no
*!   -capture- and no catch-all, so an unlisted option aborts the caller's
*!   do-file with r(198) "option ... not allowed".
*!
*! HOW TO RUN (from a scratch directory, NOT the repo -- Stata writes its
*! batch .log and the probe by-products into the PROCESS working directory):
*!
*!     mkdir -p /tmp/dash-corpus && cd /tmp/dash-corpus
*!     arch -arm64 /usr/local/bin/stata-mp -b do \
*!         /Users/billy/Desktop/Programs/StataPrograms/d/dash/test/fixtures/twoway_corpus.do
*!
*!   The arch -arm64 prefix is required; the x86_64 slice dies with r(7100) on
*!   libpython.  Stata batch mode exits 0 even on error -- read the .log.
*!
*! DELIBERATELY NO `version` STATEMENT AT THE TOP OF THIS FILE.
*!   See section 26: a leading `version 17.0` or lower makes EVERY dash graph
*!   registration fail, so a corpus run under one would measure nothing but
*!   that one bug.  Section 26 measures it on purpose, last, in isolation.
*!
*! OUTPUT
*!   twoway_corpus_results.txt in the working directory, one line per probe:
*!     id %%|%% twoway_rc %%|%% dash_rc %%|%% plotspec %%|%% options %%|%% twoway_only_extra %%|%% dash spec JSON
*!   The JSON field is populated only when dash_rc==0.  It is what shows which
*!   ACCEPTED options are then silently gutted by the renderer (section 25).
*!   The .log carries a "@@P@@ <id>" marker immediately before each dash
*!   invocation so every rejection message can be attributed to its probe.

clear all
set more off

adopath ++ "/Users/billy/Desktop/Programs/Java/StataJSON"
adopath ++ "/Users/billy/Desktop/Programs/StataPrograms/d/dash"

// ================================================================
// probe harness
//
//   dashprobe <id> <plotspec> <options> [<twoway_only_extra>]
//
// `twoway_only_extra` is appended to the -twoway- command ONLY.  It exists
// so that an option Stata will not accept in isolation (droplines() needs
// range(); clegend() needs colorvar(); mlabangle() needs mlabel(); ...) can
// still be probed against dash on its own, keeping the dash_rc attributable
// to exactly one option key.
// ================================================================
capture program drop dashprobe
program define dashprobe
    args id spec opts twextra

    // ---- 1. real twoway, nodraw ----
    capture graph drop _all
    local twopts `"`opts'"'
    if `"`twextra'"' != "" {
        if `"`twopts'"' != "" local twopts `"`twopts' `twextra'"'
        else                  local twopts `"`twextra'"'
    }
    local twcmd `"twoway `spec'"'
    if `"`twopts'"' != "" {
        local twcmd `"`twcmd', `twopts'"'
        if strpos(`"`twopts'"', "nodraw") == 0 local twcmd `"`twcmd' nodraw"'
    }
    else local twcmd `"`twcmd', nodraw"'
    capture `twcmd'
    local twrc = _rc

    // ---- 2. the same spec + options through dash ----
    capture dash clear
    capture macro drop dash_json_g1
    local dcmd `"dash `spec'"'
    if `"`opts'"' != "" {
        local dcmd `"`dcmd', `opts'"'
        if strpos(`"`opts'"', "name(") == 0 local dcmd `"`dcmd' name(g1)"'
    }
    else local dcmd `"`dcmd', name(g1)"'
    display as text "@@P@@ `id'"
    capture noisily `dcmd'
    local drc = _rc

    local js `"${dash_json_g1}"'
    if `drc' != 0 local js ""

    file write DPOUT `"`id'%%|%%`twrc'%%|%%`drc'%%|%%`spec'%%|%%`opts'%%|%%`twextra'%%|%%`js'"' _n
    if `twrc' != 0 display as error "BAD PROBE (twoway rejected): `id'"
end

// dashonlyprobe -- the mirror image.  Records option keys that DASH accepts but
// that real -twoway- does not have, i.e. dash-only spellings.  A non-zero
// twoway rc is the finding here, not a bad probe, so no warning is emitted.
capture program drop dashonlyprobe
program define dashonlyprobe
    args id spec opts
    capture graph drop _all
    capture twoway `spec', `opts' nodraw
    local twrc = _rc
    capture dash clear
    capture macro drop dash_json_g1
    display as text "@@P@@ `id'"
    capture noisily dash `spec', `opts' name(g1)
    local drc = _rc
    local js `"${dash_json_g1}"'
    if `drc' != 0 local js ""
    file write DPOUT `"`id'%%|%%`twrc'%%|%%`drc'%%|%%`spec'%%|%%`opts'%%|%%%%|%%`js'"' _n
end

// ================================================================
// fixtures
// ================================================================
// A synthetic but valid Graph Recorder file, so play() can be probed without
// a pre-existing recording.  Header format per
// /Applications/StataNow/ado/base/_/_gs_rec_wrfilehdr.ado.
tempname fh
file open `fh' using "dashprobe_rec.grec", write replace text
file write `fh' "StataFileTM:00001:01100:GREC:                          :" _n
file write `fh' "00000:00000:00001:" _n
file write `fh' "*! classname: twowaygraph_g" _n
file write `fh' "*! family: twoway" _n
file write `fh' "*! date: 01 Jan 2020" _n
file write `fh' "*! time: 00:00:00" _n
file write `fh' "*! graph_scheme: s2color" _n
file write `fh' "*! naturallywhite: 1" _n
file write `fh' "*! end" _n
file close `fh'

file open DPOUT using "twoway_corpus_results.txt", write replace text

// ---------------- cross-sectional fixture (1978 auto data) ----------------
sysuse auto, clear
gen lo   = mpg - 3
gen hi   = mpg + 3
gen y1   = mpg
gen x1   = weight
gen y2   = mpg + 5
gen x2   = weight + 300
gen vpos = 12

// ================================================================
// 1. PLOTTYPE CONTROLS -- no options at all.
//    Establishes the per-plottype baseline, so that a later dash_rc!=0 is
//    attributable to the option under test and not to the plottype.
// ================================================================
dashprobe ctl_scatter      "scatter mpg weight"        ""
dashprobe ctl_line         "line mpg weight"           ""
dashprobe ctl_connected    "connected mpg weight"      ""
dashprobe ctl_area         "area mpg weight"           ""
dashprobe ctl_bar          "bar mpg weight"            ""
dashprobe ctl_spike        "spike mpg weight"          ""
dashprobe ctl_dropline     "dropline mpg weight"       ""
dashprobe ctl_dot          "dot mpg weight"            ""
dashprobe ctl_lfit         "lfit mpg weight"           ""
dashprobe ctl_qfit         "qfit mpg weight"           ""
dashprobe ctl_lfitci       "lfitci mpg weight"         ""
dashprobe ctl_qfitci       "qfitci mpg weight"         ""
dashprobe ctl_fpfit        "fpfit mpg weight"          ""
dashprobe ctl_fpfitci      "fpfitci mpg weight"        ""
dashprobe ctl_lowess       "lowess mpg weight"         ""
dashprobe ctl_lpoly        "lpoly mpg weight"          ""
dashprobe ctl_lpolyci      "lpolyci mpg weight"        ""
dashprobe ctl_mband        "mband mpg weight"          ""
dashprobe ctl_mspline      "mspline mpg weight"        ""
dashprobe ctl_histogram    "histogram mpg"             ""
dashprobe ctl_kdensity     "kdensity mpg"              ""
dashprobe ctl_function     "function x"                ""
dashprobe ctl_function_yeq "function y=x"              ""
dashprobe ctl_scatteri     "scatteri 20 3000 30 4000"  ""
dashprobe ctl_rarea        "rarea lo hi weight"        ""
dashprobe ctl_rbar         "rbar lo hi weight"         ""
dashprobe ctl_rspike       "rspike lo hi weight"       ""
dashprobe ctl_rcap         "rcap lo hi weight"         ""
dashprobe ctl_rcapsym      "rcapsym lo hi weight"      ""
dashprobe ctl_rline        "rline lo hi weight"        ""
dashprobe ctl_rconnected   "rconnected lo hi weight"   ""
dashprobe ctl_rscatter     "rscatter lo hi weight"     ""
dashprobe ctl_pcspike      "pcspike y1 x1 y2 x2"       ""
dashprobe ctl_pcarrow      "pcarrow y1 x1 y2 x2"       ""
dashprobe ctl_pcbarrow     "pcbarrow y1 x1 y2 x2"      ""
dashprobe ctl_pcscatter    "pcscatter y1 x1 y2 x2"     ""
dashprobe ctl_pci          "pci 20 3000 30 4000"       ""
dashprobe ctl_multi        "scatter mpg weight || line mpg weight"  ""
dashprobe ctl_ifqual       "scatter mpg weight if foreign==1"   ""
dashprobe ctl_inqual       "scatter mpg weight in 1/40"         ""
dashprobe ctl_aweight      "scatter mpg weight [aweight=price]" ""

// ================================================================
// 2. added_line_options  (help added_line_options)
// ================================================================
dashprobe xline            "scatter mpg weight"  "xline(3000)"
dashprobe yline            "scatter mpg weight"  "yline(20)"
dashprobe xline_suboptions "scatter mpg weight"  "xline(3000, lcolor(red) lpattern(dash))"

// ================================================================
// 3. added_text_options  (help added_text_options)
// ================================================================
dashprobe text             "scatter mpg weight"  `"text(20 3000 "a note")"'
dashprobe text_suboptions  "scatter mpg weight"  `"text(20 3000 "a note", placement(e) size(small))"'

// ================================================================
// 4. axis_label_options  (help axis_label_options)
// ================================================================
dashprobe xlabel_numlist   "scatter mpg weight"  "xlabel(2000(500)5000)"
dashprobe ylabel_numlist   "scatter mpg weight"  "ylabel(10 20 30 40)"
dashprobe xlabel_hash      "scatter mpg weight"  "xlabel(#10)"
dashprobe xlabel_minmax    "scatter mpg weight"  "xlabel(minmax)"
dashprobe xlabel_grid      "scatter mpg weight"  "xlabel(, grid)"
dashprobe xlabel_angle     "scatter mpg weight"  "xlabel(, angle(45))"
dashprobe ylabel_format    "scatter mpg weight"  "ylabel(, format(%9.0fc))"
dashprobe ylabel_labsize   "scatter mpg weight"  "ylabel(, labsize(small))"
dashprobe ylabel_valuelab  "scatter rep78 weight" "ylabel(, valuelabel)"
dashprobe xlabel_custom    "scatter mpg weight"  `"xlabel(2000 "light" 4000 "heavy", custom)"'
dashprobe xtick            "scatter mpg weight"  "xtick(2000(500)5000)"
dashprobe ytick            "scatter mpg weight"  "ytick(10 20 30 40)"
dashprobe xmtick           "scatter mpg weight"  "xmtick(2000(250)5000)"
dashprobe ymtick           "scatter mpg weight"  "ymtick(10(5)40)"
dashprobe xmlabel          "scatter mpg weight"  "xmlabel(2000(250)5000)"
dashprobe ymlabel          "scatter mpg weight"  "ymlabel(10(5)40)"

// ================================================================
// 5. axis_scale_options  (help axis_scale_options)
// ================================================================
dashprobe xscale_log       "scatter mpg weight"  "xscale(log)"
dashprobe yscale_range     "scatter mpg weight"  "yscale(range(0 50))"
dashprobe xscale_reverse   "scatter mpg weight"  "xscale(reverse)"
dashprobe xscale_alt       "scatter mpg weight"  "xscale(alt)"
dashprobe xscale_noline    "scatter mpg weight"  "xscale(noline)"
dashprobe yscale_titlegap  "scatter mpg weight"  "yscale(titlegap(2))"

// ================================================================
// 6. axis_title_options  (help axis_title_options)
// ================================================================
dashprobe xtitle           "scatter mpg weight"  `"xtitle("Weight (lbs)")"'
dashprobe ytitle           "scatter mpg weight"  `"ytitle("Mileage")"'

// ================================================================
// 7. axis_choice_options  (help axis_choice_options)
// ================================================================
dashprobe yaxis            "scatter mpg weight"  "yaxis(1)"
dashprobe xaxis            "scatter mpg weight"  "xaxis(1)"
dashprobe dual_axis        "scatter mpg weight || line price weight" "yaxis(1)"

// ================================================================
// 8. title_options  (help title_options)
// ================================================================
dashprobe title            "scatter mpg weight"  `"title("Mileage vs weight")"'
dashprobe subtitle         "scatter mpg weight"  `"subtitle("1978 autos")"'
dashprobe note             "scatter mpg weight"  `"note("Source: 1978 data")"'
dashprobe caption          "scatter mpg weight"  `"caption("Figure 1")"'
dashprobe title_size       "scatter mpg weight"  `"title("T", size(large))"'
dashprobe title_color      "scatter mpg weight"  `"title("T", color(navy) position(11))"'
dashprobe note_span        "scatter mpg weight"  `"note("n=74", span)"'
dashprobe t1title          "scatter mpg weight"  `"t1title("top 1")"'
dashprobe t2title          "scatter mpg weight"  `"t2title("top 2")"'
dashprobe b1title          "scatter mpg weight"  `"b1title("bottom 1")"'
dashprobe b2title          "scatter mpg weight"  `"b2title("bottom 2")"'
dashprobe l1title          "scatter mpg weight"  `"l1title("left 1")"'
dashprobe l2title          "scatter mpg weight"  `"l2title("left 2")"'
dashprobe r1title          "scatter mpg weight"  `"r1title("right 1")"'
dashprobe r2title          "scatter mpg weight"  `"r2title("right 2")"'

// ================================================================
// 9. legend_options  (help legend_options)
// ================================================================
dashprobe legend_off       "scatter mpg weight"  "legend(off)"
dashprobe legend_on        "scatter mpg weight"  "legend(on)"
dashprobe legend_order     "scatter mpg weight || line mpg weight"  "legend(order(1 2))"
dashprobe legend_label     "scatter mpg weight || line mpg weight"  `"legend(label(1 "points") label(2 "line"))"'
dashprobe legend_cols      "scatter mpg weight || line mpg weight"  "legend(cols(2))"
dashprobe legend_position  "scatter mpg weight"  "legend(position(6) ring(0))"
dashprobe clegend          "scatter mpg weight"  "clegend(off)"   "colorvar(price)"
dashprobe plegend          "scatter mpg weight"  "plegend(off)"   "colorvar(price) colordiscrete coloruseplegend"

// ================================================================
// 10. region_options / scale_option / aspect_option
// ================================================================
dashprobe graphregion      "scatter mpg weight"  "graphregion(color(white))"
dashprobe graphregion_marg "scatter mpg weight"  "graphregion(margin(zero))"
dashprobe plotregion       "scatter mpg weight"  "plotregion(margin(zero))"
dashprobe xsize            "scatter mpg weight"  "xsize(8)"
dashprobe ysize            "scatter mpg weight"  "ysize(5)"
dashprobe fxsize           "scatter mpg weight"  "fxsize(50)"
dashprobe fysize           "scatter mpg weight"  "fysize(50)"
dashprobe scale            "scatter mpg weight"  "scale(1.2)"
dashprobe aspectratio      "scatter mpg weight"  "aspectratio(0.75)"

// ================================================================
// 11. by / name / saving / nodraw / play / scheme
// ================================================================
dashprobe by               "scatter mpg weight"  "by(foreign)"
dashprobe by_total         "scatter mpg weight"  "by(foreign, total)"
dashprobe name             "scatter mpg weight"  "name(g1)"
dashprobe name_replace     "scatter mpg weight"  "name(g1, replace)"
dashprobe saving           "scatter mpg weight"  "saving(dashprobe_gph, replace)"
dashprobe nodraw           "scatter mpg weight"  "nodraw"
dashprobe play             "scatter mpg weight"  "play(dashprobe_rec)"
dashprobe scheme           "scatter mpg weight"  "scheme(s2color)"

// ================================================================
// 12. advanced_options  (help advanced_options)
// ================================================================
dashprobe yvarlabel        "scatter mpg weight"  `"yvarlabel("Mileage")"'
dashprobe xvarlabel        "scatter mpg weight"  `"xvarlabel("Weight")"'
dashprobe yvarformat       "scatter mpg weight"  "yvarformat(%9.2f)"
dashprobe xvarformat       "scatter mpg weight"  "xvarformat(%9.2f)"
dashprobe pcycle           "scatter mpg weight"  "pcycle(3)"
dashprobe xoverhangs       "scatter mpg weight"  "xoverhangs"
dashprobe yoverhangs       "scatter mpg weight"  "yoverhangs"
dashprobe recast           "scatter mpg weight"  "recast(line)"

// ================================================================
// 13. marker_options  (help marker_options)
// ================================================================
dashprobe msymbol          "scatter mpg weight"  "msymbol(Oh)"
dashprobe mcolor           "scatter mpg weight"  "mcolor(navy)"
dashprobe msize            "scatter mpg weight"  "msize(large)"
dashprobe msangle          "scatter mpg weight"  "msangle(45)"
dashprobe mfcolor          "scatter mpg weight"  "mfcolor(none)"
dashprobe mlcolor          "scatter mpg weight"  "mlcolor(black)"
dashprobe mlwidth          "scatter mpg weight"  "mlwidth(thick)"
dashprobe mlalign          "scatter mpg weight"  "mlalign(inside)"
dashprobe mlstyle          "scatter mpg weight"  "mlstyle(p1)"
dashprobe mstyle           "scatter mpg weight"  "mstyle(p1)"
dashprobe pstyle           "scatter mpg weight"  "pstyle(p2)"
dashprobe jitter           "scatter mpg weight"  "jitter(5)"
dashprobe jitterseed       "scatter mpg weight"  "jitterseed(123)"  "jitter(5)"

// ================================================================
// 14. marker_label_options  (help marker_label_options)
// ================================================================
dashprobe mlabel           "scatter mpg weight"  "mlabel(make)"
dashprobe mlabcolor        "scatter mpg weight"  "mlabcolor(red)"        "mlabel(make)"
dashprobe mlabsize         "scatter mpg weight"  "mlabsize(small)"       "mlabel(make)"
dashprobe mlabposition     "scatter mpg weight"  "mlabposition(12)"      "mlabel(make)"
dashprobe mlabgap          "scatter mpg weight"  "mlabgap(2)"            "mlabel(make)"
dashprobe mlabangle        "scatter mpg weight"  "mlabangle(45)"         "mlabel(make)"
dashprobe mlabformat       "scatter mpg weight"  "mlabformat(%9.0fc)"    "mlabel(price)"
dashprobe mlabstyle        "scatter mpg weight"  "mlabstyle(p1)"         "mlabel(make)"
dashprobe mlabtextstyle    "scatter mpg weight"  "mlabtextstyle(body)"   "mlabel(make)"
dashprobe mlabvposition    "scatter mpg weight"  "mlabvposition(vpos)"   "mlabel(make)"

// ================================================================
// 15. cline_options / connect_options / line_options
// ================================================================
dashprobe lcolor           "line mpg weight"  "lcolor(red)"
dashprobe lwidth           "line mpg weight"  "lwidth(thick)"
dashprobe lpattern         "line mpg weight"  "lpattern(dash)"
dashprobe lstyle           "line mpg weight"  "lstyle(p1)"
dashprobe lalign           "area mpg weight"  "lalign(inside)"
dashprobe connect          "line mpg weight"  "connect(l)"
dashprobe cmissing         "line mpg weight"  "cmissing(n)"

// ================================================================
// 16. area_options / barlook_options
// ================================================================
dashprobe color_area       "area mpg weight"  "color(red)"
dashprobe fcolor           "area mpg weight"  "fcolor(ltblue)"
dashprobe fintensity       "area mpg weight"  "fintensity(50)"
dashprobe astyle           "area mpg weight"  "astyle(p1)"
dashprobe bstyle           "bar mpg weight"   "bstyle(p1)"
dashprobe barwidth         "bar mpg weight"   "barwidth(20)"
dashprobe base             "bar mpg weight"   "base(10)"
dashprobe bar_lwidth       "bar mpg weight"   "lwidth(thick)"

// ================================================================
// 17. fit plots: lfit / qfit / lfitci / fpfit  (help twoway_lfit, ...)
//     NOTE fpfit's own options are estcmd() and estopts(); degree(), powers(),
//     noconstant and noscaling live INSIDE estopts() -- twoway rejects them at
//     the top level, so probing them bare would be a bad probe.
// ================================================================
dashprobe lfit_range       "lfit mpg weight"    "range(2000 4000)"
dashprobe lfit_n           "lfit mpg weight"    "n(50)"
dashprobe lfit_atobs       "lfit mpg weight"    "atobs"
dashprobe lfit_estopts     "lfit mpg weight"    "estopts(nocons)"
dashprobe lfit_predopts    "lfit mpg weight"    "predopts(xb)"
dashprobe lfitci_level     "lfitci mpg weight"  "level(90)"
dashprobe lfitci_ciplot    "lfitci mpg weight"  "ciplot(rline)"
dashprobe lfitci_nofit     "lfitci mpg weight"  "nofit"
dashprobe lfitci_fcolor    "lfitci mpg weight"  "fcolor(gs12)"
dashprobe lfitci_alwidth   "lfitci mpg weight"  "alwidth(thin)"
dashprobe lfitci_acolor    "lfitci mpg weight"  "acolor(gs10)"
dashprobe fpfit_estcmd     "fpfit mpg weight"   "estcmd(regress)"
dashprobe fpfit_estopts    "fpfit mpg weight"   "estopts(degree(2))"
dashprobe fpfit_powers     "fpfit mpg weight"   "estopts(powers(1 2))"
dashprobe lfitci_fitplot   "lfitci mpg weight"  "fitplot(line)"
dashprobe lfitci_alpattern "lfitci mpg weight"  "alpattern(dash)"
dashprobe lfitci_alalign   "lfitci mpg weight"  "alalign(inside)"
dashprobe lfitci_alstyle   "lfitci mpg weight"  "alstyle(p1)"
dashprobe lfitci_astyle    "lfitci mpg weight"  "astyle(p1)"

// ================================================================
// 18. smoothers: lowess / lpoly / mband / mspline
// ================================================================
dashprobe lowess_bwidth    "lowess mpg weight"   "bwidth(0.8)"
dashprobe lowess_mean      "lowess mpg weight"   "mean"
dashprobe lowess_noweight  "lowess mpg weight"   "noweight"
dashprobe lowess_logit     "lowess mpg weight"   "logit"
dashprobe lowess_adjust    "lowess mpg weight"   "adjust"
dashprobe lpoly_bwidth     "lpoly mpg weight"    "bwidth(500)"
dashprobe lpoly_degree     "lpoly mpg weight"    "degree(1)"
dashprobe lpoly_kernel     "lpoly mpg weight"    "kernel(epan2)"
dashprobe lpoly_n          "lpoly mpg weight"    "n(50)"
dashprobe mband_bands      "mband mpg weight"    "bands(10)"
dashprobe mspline_bands    "mspline mpg weight"  "bands(10)"
dashprobe mspline_n        "mspline mpg weight"  "n(3)"

// ================================================================
// 19. twoway histogram  (help twoway_histogram)
// ================================================================
dashprobe hist_bin         "histogram mpg"   "bin(20)"
dashprobe hist_width       "histogram mpg"   "width(5)"
dashprobe hist_start       "histogram mpg"   "start(10)"
dashprobe hist_density     "histogram mpg"   "density"
dashprobe hist_fraction    "histogram mpg"   "fraction"
dashprobe hist_frequency   "histogram mpg"   "frequency"
dashprobe hist_percent     "histogram mpg"   "percent"
dashprobe hist_discrete    "histogram rep78" "discrete"
dashprobe hist_gap         "histogram mpg"   "gap(10)"
dashprobe hist_horizontal  "histogram mpg"   "horizontal"
dashprobe hist_fcolor      "histogram mpg"   "fcolor(navy)"

// ================================================================
// 20. twoway kdensity  (help twoway_kdensity)
// ================================================================
dashprobe kd_bwidth        "kdensity mpg"  "bwidth(2)"
dashprobe kd_kernel        "kdensity mpg"  "kernel(epan2)"
dashprobe kd_n             "kdensity mpg"  "n(100)"
dashprobe kd_range         "kdensity mpg"  "range(10 40)"
dashprobe kd_area          "kdensity mpg"  "area(1)"
dashprobe kd_horizontal    "kdensity mpg"  "horizontal"

// ================================================================
// 21. twoway function  (help twoway_function)
//     droplines() is legal only together with range(), hence the twoway-only
//     extra; the dash side still sees droplines() alone.
// ================================================================
dashprobe fn_range         "function x"  "range(0 10)"
dashprobe fn_n             "function x"  "n(50)"
dashprobe fn_horizontal    "function x"  "horizontal"
dashprobe fn_droplines     "function x"  "droplines(2 4 6)"  "range(0 10)"
dashprobe fn_base          "function x"  "base(0)"
dashprobe fn_lcolor        "function x"  "lcolor(red)"

// ================================================================
// 22. range plots, paired coordinates, orientation, sort
// ================================================================
dashprobe rbar_horizontal  "rbar lo hi weight"      "horizontal"
dashprobe rbar_barwidth    "rbar lo hi weight"      "barwidth(20)"
dashprobe rbar_vertical    "rbar lo hi weight"      "vertical"
dashprobe rcap_msize       "rcap lo hi weight"      "msize(large)"
dashprobe rspike_lwidth    "rspike lo hi weight"    "lwidth(thick)"
dashprobe bar_horizontal   "bar mpg weight"         "horizontal"
dashprobe bar_vertical     "bar mpg weight"         "vertical"
dashprobe spike_base       "spike mpg weight"       "base(10)"
dashprobe dropline_horiz   "dropline mpg weight"    "horizontal"
dashprobe line_sort        "line mpg weight"        "sort"
dashprobe area_sort        "area mpg weight"        "sort"
dashprobe connected_sort   "connected mpg weight"   "sort"
dashprobe pcarrow_barbsize "pcarrow y1 x1 y2 x2"    "barbsize(3)"
dashprobe pcarrow_headlabel "pcarrow y1 x1 y2 x2"   "headlabel"
dashprobe pcarrow_mlabel   "pcarrow y1 x1 y2 x2"    "mlabel(make)"
dashprobe pcarrow_mangle   "pcarrow y1 x1 y2 x2"    "mangle(30)"
dashprobe pcarrow_mstyle   "pcarrow y1 x1 y2 x2"    "mstyle(p1)"
dashprobe rbar_mwidth      "rbar lo hi weight"      "mwidth"
dashprobe rbar_baroffset   "rbar lo hi weight"      "baroffset(0.2)"
dashprobe bar_baroffset    "bar mpg weight"         "baroffset(0.2)"
dashprobe rcap_horizontal  "rcap lo hi weight"      "horizontal"
dashprobe area_nodropbase  "area mpg weight"        "nodropbase"
dashprobe area_cmissing    "area mpg weight"        "cmissing(n)"
dashprobe spike_horizontal "spike mpg weight"       "horizontal"
dashprobe dot_dcolor       "dot mpg weight"         "dcolor(red)"
dashprobe dot_dfcolor      "dot mpg weight"         "dfcolor(red)"
dashprobe dot_dlcolor      "dot mpg weight"         "dlcolor(red)"
dashprobe dot_dlwidth      "dot mpg weight"         "dlwidth(thick)"
dashprobe dot_dlstyle      "dot mpg weight"         "dlstyle(p1)"
dashprobe dot_dlalign      "dot mpg weight"         "dlalign(inside)"
dashprobe dot_dsize        "dot mpg weight"         "dsize(large)"
dashprobe dot_dstyle       "dot mpg weight"         "dstyle(p1)"
dashprobe dot_dsymbol      "dot mpg weight"         "dsymbol(Oh)"
dashprobe dot_dotextend    "dot mpg weight"         "dotextend(no)"
dashprobe dot_ndots        "dot mpg weight"         "ndots(50)"
dashprobe dot_horizontal   "dot mpg weight"         "horizontal"

// ================================================================
// 23. colorvar_options  (help colorvar_options)
//     The twoway-only extra supplies colorvar()/colordiscrete where Stata
//     requires them, so the dash side sees only the option under test.
// ================================================================
dashprobe colorvar         "scatter mpg weight"   "colorvar(price)"
dashprobe colordiscrete    "scatter mpg weight"   "colordiscrete"                      "colorvar(price)"
dashprobe colorcuts        "scatter mpg weight"   "colorcuts(4000 6000 8000)"          "colorvar(price)"
dashprobe coloruseplegend  "scatter mpg weight"   "coloruseplegend"                    "colorvar(price) colordiscrete"
dashprobe colorlevels      "scatter mpg weight"   "colorlevels(4)"                     "colorvar(price)"
dashprobe colorlist        "scatter mpg weight"   "colorlist(red blue green orange)"   "colorvar(price) colordiscrete"
dashprobe colorrule        "scatter mpg weight"   "colorrule(linear)"                  "colorvar(price)"
dashprobe colorstart       "scatter mpg weight"   "colorstart(yellow)"                 "colorvar(price) colorend(red)"
dashprobe colorend         "scatter mpg weight"   "colorend(red)"                      "colorvar(price) colorstart(yellow)"
dashprobe colorformissing  "scatter rep78 weight" "colorformissing(gs8)"               "colorvar(rep78)"
dashprobe colorkeysrange   "scatter mpg weight"   "colorkeysrange"                     "colorvar(price)"
dashprobe colorfillonly    "scatter mpg weight"   "colorfillonly"                      "colorvar(price)"
dashprobe colorvarminmax   "scatter mpg weight"   "colorvarminmax"                     "colorvar(price)"

// ================================================================
// 24. TIME-SERIES AXIS FAMILY  (t* options need a tsset dataset)
// ================================================================
clear
set obs 60
gen t = tm(2000m1) + _n - 1
format t %tm
set seed 12345
gen y    = 100 + _n + rnormal()
gen ylo  = y - 5
gen yhi  = y + 5
tsset t

dashprobe ctl_tsline       "tsline y"        ""
dashprobe ctl_tsrline      "tsrline ylo yhi" ""
dashprobe tline            "tsline y"        "tline(2002m1)"
dashprobe ttext            "tsline y"        `"ttext(120 2002m1 "a note")"'
dashprobe tlabel           "tsline y"        "tlabel(2000m1(12)2004m1)"
dashprobe ttick            "tsline y"        "ttick(2000m1(12)2004m1)"
dashprobe tmlabel          "tsline y"        "tmlabel(2000m1(6)2004m1)"
dashprobe tmtick           "tsline y"        "tmtick(2000m1(6)2004m1)"
dashprobe ttitle           "tsline y"        `"ttitle("Month")"'
dashprobe tscale           "tsline y"        "tscale(range(2000m1 2005m1))"

// ================================================================
// 25. ACCEPTED-BUT-DISCARDED
//     Options whose KEY dash accepts -- they are declared `string asis`, so
//     -syntax- lets them through -- but whose CONTENTS the renderer then
//     drops.  Every probe here ends with dash_rc==0; the payload is the spec
//     JSON recorded alongside, which shows exactly what survives.
// ================================================================
sysuse auto, clear
dashprobe abd_title_size     "scatter mpg weight"  `"title("T", size(large))"'
dashprobe abd_legend_order   "scatter mpg weight || line mpg weight"  "legend(order(1 2))"
dashprobe abd_ylabel_format  "scatter mpg weight"  "ylabel(, format(%9.0fc))"
dashprobe abd_xlabel_hash    "scatter mpg weight"  "xlabel(#10)"
dashprobe abd_xlabel_minmax  "scatter mpg weight"  "xlabel(minmax)"
dashprobe abd_xlabel_range   "scatter mpg weight"  "xlabel(1990(5)2020)"
dashprobe abd_yscale_range   "scatter mpg weight"  "yscale(range(0 50))"
dashprobe abd_graphregion    "scatter mpg weight"  "graphregion(margin(zero))"
dashprobe abd_note_span      "scatter mpg weight"  `"note("n=74", span)"'

// ================================================================
// 27. DASH-ONLY OPTION SPELLINGS
//     The mirror image of the corpus above: keys that dash's allow-lists
//     accept but that real -twoway- does not have.  twoway_rc!=0 here is the
//     measurement, not a bad probe.  These matter for the drop-in claim in
//     both directions -- a dash graph written using them is not valid twoway
//     code, and where dash invented a spelling for something Stata already
//     names (jseed vs jitterseed, colornlevels vs colorlevels, colormissing
//     vs colorformissing) the Stata spelling is in the rejected set above.
// ================================================================
dashonlyprobe only_mlabwidth    "scatter mpg weight"    "mlabel(make) mlabwidth(2)"
dashonlyprobe only_malpha       "scatter mpg weight"    "malpha(50)"
dashonlyprobe only_lalpha       "line mpg weight"       "lalpha(50)"
dashonlyprobe only_falpha       "area mpg weight"       "falpha(50)"
dashonlyprobe only_blcolor      "bar mpg weight"        "blcolor(red)"
dashonlyprobe only_bfcolor      "bar mpg weight"        "bfcolor(red)"
dashonlyprobe only_jseed        "scatter mpg weight"    "jitter(5) jseed(42)"
dashonlyprobe only_colpalette   "scatter mpg weight"    "colorvar(price) colpalette(viridis)"
dashonlyprobe only_colornlevels "scatter mpg weight"    "colorvar(price) colornlevels(4)"
dashonlyprobe only_colormissing "scatter rep78 weight"  "colorvar(rep78) colormissing(gs8)"
dashonlyprobe only_marker       "scatter mpg weight"    "marker(1)"
dashonlyprobe only_bgcolor      "scatter mpg weight"    "bgcolor(white)"
dashonlyprobe only_plotbgcolor  "scatter mpg weight"    "plotbgcolor(white)"
dashonlyprobe only_link         "scatter mpg weight"    "link(g2)"
dashonlyprobe only_filter       "scatter mpg weight"    "filter(foreign)"
dashonlyprobe only_ytitle2      "scatter mpg weight"    "ytitle2(Second)"
dashonlyprobe only_ylabel2      "scatter mpg weight"    "ylabel2(0 10 20)"
dashonlyprobe only_yscale2      "scatter mpg weight"    "yscale2(log)"

file close DPOUT

// ================================================================
// 26. VERSION-CONTROL REGRESSION (measured separately; poisons everything
//     above if it runs first, which is why this file has no leading
//     `version` statement).
//
//     _dash_register_graph (dash.ado:857) validates the graph name with
//         regexm("`name'", "^[a-zA-Z_][a-zA-Z0-9_]{0,31}$")
//     The {0,31} interval quantifier is only understood by the regex engine
//     Stata uses under version >= 18.  Under a do-file-level `version 17.0`
//     or lower -- including the `version 16.0` that dash.ado itself declares
//     as its minimum -- regexm() returns 0 for a perfectly legal name and
//     EVERY dash graph registration dies with r(198).
// ================================================================
file open DPVER using "twoway_corpus_version_results.txt", write replace text

// NB: these MUST be straight-line statements.  Inside a -foreach- loop the
// body is compiled under the ambient version, so `version 16.0' there sets
// c(version)==16 yet regexm() still uses the new engine and the bug hides.
version 14.0
capture dash clear
capture dash scatter mpg weight, name(g1)
local vrc = _rc
local vre = regexm("g1", "^[a-zA-Z_][a-zA-Z0-9_]{0,31}$")
display as text "@@V@@ version=14.0 regexm=`vre' dash_rc=`vrc'"
file write DPVER `"version_14.0%%|%%`vre'%%|%%`vrc'"' _n

version 16.0
capture dash clear
capture dash scatter mpg weight, name(g1)
local vrc = _rc
local vre = regexm("g1", "^[a-zA-Z_][a-zA-Z0-9_]{0,31}$")
display as text "@@V@@ version=16.0 regexm=`vre' dash_rc=`vrc'"
file write DPVER `"version_16.0%%|%%`vre'%%|%%`vrc'"' _n

version 17.0
capture dash clear
capture dash scatter mpg weight, name(g1)
local vrc = _rc
local vre = regexm("g1", "^[a-zA-Z_][a-zA-Z0-9_]{0,31}$")
display as text "@@V@@ version=17.0 regexm=`vre' dash_rc=`vrc'"
file write DPVER `"version_17.0%%|%%`vre'%%|%%`vrc'"' _n

version 18.0
capture dash clear
capture dash scatter mpg weight, name(g1)
local vrc = _rc
local vre = regexm("g1", "^[a-zA-Z_][a-zA-Z0-9_]{0,31}$")
display as text "@@V@@ version=18.0 regexm=`vre' dash_rc=`vrc'"
file write DPVER `"version_18.0%%|%%`vre'%%|%%`vrc'"' _n

version 19.0
capture dash clear
capture dash scatter mpg weight, name(g1)
local vrc = _rc
local vre = regexm("g1", "^[a-zA-Z_][a-zA-Z0-9_]{0,31}$")
display as text "@@V@@ version=19.0 regexm=`vre' dash_rc=`vrc'"
file write DPVER `"version_19.0%%|%%`vre'%%|%%`vrc'"' _n

file close DPVER
version `=c(stata_version)'

display as text "twoway_corpus.do: done -> twoway_corpus_results.txt"
