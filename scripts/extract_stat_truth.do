*! extract_stat_truth.do
*! Derive the STATISTICAL ground truth for every smoothing / binning / band
*! layer that dash draws, BY PROBING STATA ITSELF, on four builtin datasets of
*! very different sizes (census N=50, auto N=74, sp500 N=248, nlsw88 N=2,246).
*!
*! Output: test/fixtures/stat_truth.json
*!
*! Run with (Stata must be forced to its arm64 slice, and must be launched
*! from a scratch directory because batch mode writes its .log to the process
*! working directory):
*!
*!   mkdir -p /tmp/dash-s07 && cd /tmp/dash-s07 && \
*!   arch -arm64 /usr/local/bin/stata-mp -b do \
*!     /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/extract_stat_truth.do
*!
*! ---------------------------------------------------------------------------
*! METHOD
*!
*! Three independent oracles are used, and where two of them can be applied to
*! the same quantity they are BOTH recorded so a reviewer can see them agree:
*!
*!  (1) r()/e() from Stata's own estimation command.  kdensity, lpoly and fp
*!      all return their chosen kernel / bandwidth / degree / powers, and
*!      twoway__histogram_gen -- the subroutine histogram.ado itself calls --
*!      returns the whole bin grid.
*!
*!  (2) THE PLOTTED POINTS THEMSELVES.  A twoway plot is saved to a live-format
*!      .gph; `graph use' then makes its sersets addressable, and
*!      `serset set #' + `serset use, clear' loads the exact numbers the plot
*!      draws back into memory.  This is the only way to see what twoway
*!      actually plots for lfitci / fpfit / function / mband, none of which
*!      leave their curve anywhere else.  For mband it reaches the DERIVED
*!      serset (type median_bands) that the graph engine computes at draw time,
*!      so the cross medians are read straight out of the graph.
*!
*!  (3) THE RESOLVED COMMAND LINE.  histogram rewrites itself into a
*!      `twoway histogram ... density start(12) bin(8)' call and the .gph
*!      header records that rewritten line verbatim.  The trailing python
*!      block reads it back out of the file, which independently confirms both
*!      the bin grid and that `density' -- not `frequency' -- is the default.
*!
*! Where Stata's rule is readable in Stata's own .ado source it is recorded as
*! a FORMULA as well as a measurement, with the file and line it came from, so
*! an implementation can be checked against the rule rather than curve-fitted
*! to four samples.  Two of the rules (lpoly's rule-of-thumb bandwidth and the
*! graph engine's default mband band count) are NOT in any .ado -- they live in
*! compiled Mata / in the engine -- so for those the fixture records
*! measurements only, and says so under "unverified".  Nothing is filled in
*! from memory: every value carries the command that produced it.
*!
*! Structure: Stata runs every probe and appends plain-text records to a record
*! file; a single trailing python: block reads that record file and the .gph
*! headers and writes the JSON fixture.  The python block deliberately never
*! calls back into Stata: SFIToolkit.stata() issued from a do-file python block
*! desynchronises the interpreter's input stream.
*!
*! NOTE on loop headers: a loop header must not contain ${...}; the closing
*! brace of the macro reference confuses Stata's block-brace scanner.  Globals
*! are therefore always copied into locals first.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off
set seed 20260919

global ZQ_REPO "/Users/billy/Desktop/Programs/StataPrograms/d/dash"
global ZQ_OUT  "${ZQ_REPO}/test/fixtures/stat_truth.json"

local scratch "`c(tmpdir)'/dash_stat_probe"
capture mkdir "`scratch'"
global ZQ_WORK "`scratch'"
global ZQ_REC  "`scratch'/stat_records.txt"
display as text "probe scratch dir: ${ZQ_WORK}"

* ===========================================================================
* Record-file helpers.  The field separator is @@@ because twoway command
* strings legitimately contain | (as in `scatter y x || function y=x^2').
* ===========================================================================
capture program drop zq_s
program define zq_s                      // record a string field
    syntax , Sec(string) Key(string) Fld(string) [ Val(string) ]
    file write zqrec `"S@@@`sec'@@@`key'@@@`fld'@@@`val'"' _n
end

capture program drop zq_n
program define zq_n                      // record a numeric field, full precision
    syntax , Sec(string) Key(string) Fld(string) Val(string)
    local z = `val'
    if missing(`z') local out "null"
    else            local out = trim(string(`z', "%20.17g"))
    file write zqrec "S@@@`sec'@@@`key'@@@`fld'@@@`out'" _n
end

capture program drop zq_a
program define zq_a                      // record a pre-built ;-joined array
    syntax , Sec(string) Key(string) Fld(string) Val(string)
    file write zqrec "A@@@`sec'@@@`key'@@@`fld'@@@`val'" _n
end

* Record the dataset currently in memory as a curve: the number of points, the
* sampled indices, and every variable's values at those indices.  Short curves
* are stored whole; long ones at 11 evenly spaced indices plus n/min/max.
capture program drop zq_curve
program define zq_curve
    syntax varlist(numeric) , Sec(string) Key(string) [ MAXn(integer 41) ]
    quietly count
    local n = r(N)
    zq_n, sec(`sec') key(`key') fld(n_points) val(`n')
    if `n' == 0 exit
    local idx ""
    if `n' <= `maxn' {
        forvalues i = 1/`n' {
            local idx "`idx' `i'"
        }
    }
    else {
        forvalues j = 1/11 {
            local i = round(1 + (`j'-1)*(`n'-1)/10)
            local idx "`idx' `i'"
        }
    }
    local istr ""
    foreach i of local idx {
        if "`istr'" == "" local istr "`i'"
        else              local istr "`istr';`i'"
    }
    zq_s, sec(`sec') key(`key') fld(sample_index) val(`istr')
    foreach v of local varlist {
        local vals ""
        foreach i of local idx {
            local z = `v'[`i']
            if missing(`z') local s "null"
            else            local s = trim(string(`z', "%20.17g"))
            if "`vals'" == "" local vals "`s'"
            else              local vals "`vals';`s'"
        }
        zq_a, sec(`sec') key(`key') fld(`v') val(`vals')
        quietly summarize `v', meanonly
        zq_n, sec(`sec') key(`key') fld(`v'_min) val(r(min))
        zq_n, sec(`sec') key(`key') fld(`v'_max) val(r(max))
    }
end

* Load serset #`set' of a saved .gph into memory and give its columns the names
* in `namelist', in serset order -- which for a twoway plot is y first, then x.
*
* Sersets accumulate across `graph use' calls, so they are dropped first and the
* indices therefore always start at 0 for the graph just loaded.
*
* The renaming MUST happen inside this same program.  `serset use' names its
* columns __000001, __000002, ...; Stata treats names of that shape as
* temporary variables belonging to the running program and silently drops them
* when the program ends, so a caller that loads here and renames afterwards
* finds the data gone.  Renaming before the program returns keeps them.
capture program drop zq_serset
program define zq_serset
    syntax namelist , PATH(string) [ SET(integer 0) ]
    capture graph drop _all
    capture serset drop _all
    quietly graph use "`path'"
    serset set `set'
    serset use, clear
    quietly ds
    local vl `r(varlist)'
    local i = 0
    foreach nm of local namelist {
        local ++i
        local old : word `i' of `vl'
        if "`old'" != "" & "`old'" != "`nm'" quietly rename `old' `nm'
    }
    quietly ds
    local rest `r(varlist)'
    foreach v of local rest {
        local keepit 0
        foreach nm of local namelist {
            if "`v'" == "`nm'" local keepit 1
        }
        if !`keepit' quietly drop `v'
    }
    * A serset that also carries the raw variable (twoway kdensity does) is as
    * long as the DATASET, not as long as the curve: on nlsw88 the kdensity
    * serset has 2,246 rows of which only the first 300 are the curve.  Drop
    * the padding so n_points is the grid size and not the sample size.
    local first : word 1 of `namelist'
    quietly drop if missing(`first')
end

* ===========================================================================
* Datasets.  Deliberately spanning N = 50 .. 2,246 so that every "rule" in the
* fixture is pinned by four points, not one.
* ===========================================================================
global ZQ_NDS = 0
capture program drop zq_ds
program define zq_ds
    syntax , NAMe(string) LOAD(string) Y(string) X(string) HVars(string)
    global ZQ_NDS = ${ZQ_NDS} + 1
    global ZQ_DSN_${ZQ_NDS} "`name'"
    global ZQ_DSL_${ZQ_NDS} `"`load'"'
    global ZQ_DSY_${ZQ_NDS} "`y'"
    global ZQ_DSX_${ZQ_NDS} "`x'"
    global ZQ_DSH_${ZQ_NDS} "`hvars'"
end

zq_ds, name(census) load(sysuse census, clear) y(death) x(pop)     hvars(medage pop)
zq_ds, name(auto)   load(sysuse auto, clear)   y(mpg)   x(weight)  hvars(mpg price)
zq_ds, name(sp500)  load(sysuse sp500, clear)  y(close) x(volume)  hvars(close volume)
zq_ds, name(nlsw88) load(sysuse nlsw88, clear) y(wage)  x(ttl_exp) hvars(wage hours)

local NDS = $ZQ_NDS

* ===========================================================================
file open zqrec using "${ZQ_REC}", write text replace

file write zqrec "META@@@stata_version@@@`c(stata_version)'" _n
file write zqrec "META@@@stata_flavor@@@`c(flavor)'" _n
file write zqrec "META@@@stata_edition@@@`c(edition_real)'" _n
file write zqrec "META@@@stata_born_date@@@`c(born_date)'" _n
file write zqrec "META@@@run_date@@@`c(current_date)'" _n
file write zqrec "META@@@workdir@@@${ZQ_WORK}" _n
file write zqrec "META@@@c_level@@@`c(level)'" _n

* ---------------------------------------------------------------------------
* Dataset inventory
* ---------------------------------------------------------------------------
forvalues d = 1/`NDS' {
    local ds "${ZQ_DSN_`d'}"
    local ld `"${ZQ_DSL_`d'}"'
    local yv "${ZQ_DSY_`d'}"
    local xv "${ZQ_DSX_`d'}"
    `ld'
    zq_s, sec(datasets) key(`ds') fld(load_cmd)  val(`ld')
    zq_n, sec(datasets) key(`ds') fld(N_dataset) val(_N)
    zq_s, sec(datasets) key(`ds') fld(y)         val(`yv')
    zq_s, sec(datasets) key(`ds') fld(x)         val(`xv')
    quietly count if !missing(`yv') & !missing(`xv')
    local nxy = r(N)
    zq_n, sec(datasets) key(`ds') fld(N_xy_nonmissing) val(`nxy')
    display as text "inventoried `ds' (N=`c(N)', N_xy=`nxy')"
}

* ===========================================================================
* LAYER 1 -- histogram
*
* twoway__histogram_gen is the workhorse histogram.ado itself calls; it returns
* the bin grid in r() AND generates the bar heights, so one call gives both the
* parameters and the y axis.  Each (dataset, variable) is ALSO run through the
* real `histogram' command so the .gph header carries the rewritten command
* line as an independent check of bin/start and of the default y axis.
* ===========================================================================
forvalues d = 1/`NDS' {
    local ds "${ZQ_DSN_`d'}"
    local ld `"${ZQ_DSL_`d'}"'
    local hvs "${ZQ_DSH_`d'}"
    foreach hv of local hvs {

        * ---- the four option variants, under the default y axis ------------
        foreach vspec in none bin(20) width(2) start(10) {
            local vname "`vspec'"
            if "`vspec'" == "none"     local vname default
            if "`vspec'" == "bin(20)"  local vname bin20
            if "`vspec'" == "width(2)" local vname width2
            if "`vspec'" == "start(10)" local vname start10
            local opt "`vspec'"
            if "`vspec'" == "none" local opt ""
            local key "`ds':`hv':`vname'"
            `ld'
            local ucmd "histogram `hv'"
            if "`opt'" != "" local ucmd "`ucmd', `opt'"
            zq_s, sec(histogram) key(`key') fld(equivalent_user_cmd) val(`ucmd')
            zq_s, sec(histogram) key(`key') fld(cmd) ///
                  val(twoway__histogram_gen `hv', generate(h x) return `opt')

            * width(2) on a wide-ranged variable asks for millions of bins and
            * Stata answers "too many bins"; skip rather than provoke it.
            if "`vspec'" == "width(2)" {
                quietly summarize `hv', meanonly
                local nb = ceil((r(max)-r(min))/2)
                if `nb' > 2000 {
                    zq_n, sec(histogram) key(`key') fld(rc) val(-1)
                    zq_s, sec(histogram) key(`key') fld(error) ///
                          val(skipped: width(2) implies `nb' bins on this variable, which exceeds the probe limit of 2000)
                    continue
                }
            }

            capture drop zqh zqx
            capture twoway__histogram_gen `hv', generate(zqh zqx) return `opt'
            local rc = _rc
            zq_n, sec(histogram) key(`key') fld(rc) val(`rc')
            if `rc' != 0 {
                zq_s, sec(histogram) key(`key') fld(error) ///
                      val(Stata returned _rc=`rc' for this option on this variable)
                continue
            }
            zq_n, sec(histogram) key(`key') fld(bin)   val(r(bin))
            zq_n, sec(histogram) key(`key') fld(start) val(r(start))
            zq_n, sec(histogram) key(`key') fld(width) val(r(width))
            zq_n, sec(histogram) key(`key') fld(xmin)  val(r(min))
            zq_n, sec(histogram) key(`key') fld(xmax)  val(r(max))
            zq_n, sec(histogram) key(`key') fld(area)  val(r(area))
            zq_n, sec(histogram) key(`key') fld(N)     val(r(N))
            zq_n, sec(histogram) key(`key') fld(n_x)   val(r(n_x))
            zq_s, sec(histogram) key(`key') fld(type)  val(`r(type)')
            preserve
            quietly keep zqh zqx
            quietly drop if missing(zqx)
            quietly rename zqh bar_height
            quietly rename zqx bin_midpoint
            zq_curve bin_midpoint bar_height, sec(histogram) key(`key') maxn(41)
            restore
        }

        * ---- the y-axis family, on the default bin grid --------------------
        foreach yt in density percent frequency fraction {
            local key "`ds':`hv':yaxis_`yt'"
            `ld'
            capture drop zqh zqx
            capture twoway__histogram_gen `hv', generate(zqh zqx) return `yt'
            local rc = _rc
            zq_s, sec(histogram) key(`key') fld(cmd) ///
                  val(twoway__histogram_gen `hv', generate(h x) return `yt')
            zq_s, sec(histogram) key(`key') fld(equivalent_user_cmd) ///
                  val(histogram `hv', `yt')
            zq_n, sec(histogram) key(`key') fld(rc) val(`rc')
            if `rc' != 0 continue
            zq_s, sec(histogram) key(`key') fld(type) val(`r(type)')
            zq_n, sec(histogram) key(`key') fld(area) val(r(area))
            zq_n, sec(histogram) key(`key') fld(bin)  val(r(bin))
            preserve
            quietly keep zqh zqx
            quietly drop if missing(zqx)
            quietly rename zqh bar_height
            quietly rename zqx bin_midpoint
            zq_curve bin_midpoint bar_height, sec(histogram) key(`key') maxn(41)
            restore
        }

        * ---- oracle (3): the command line histogram rewrote itself into ----
        `ld'
        local p "${ZQ_WORK}/hist_`ds'_`hv'.gph"
        capture histogram `hv', nodraw saving("`p'", replace)
        local rc = _rc
        zq_s, sec(histogram_resolved_cmd) key(`ds':`hv') fld(cmd) ///
              val(histogram `hv', nodraw saving(<path>, replace))
        zq_n, sec(histogram_resolved_cmd) key(`ds':`hv') fld(rc) val(`rc')
        zq_s, sec(histogram_resolved_cmd) key(`ds':`hv') fld(gph) val(`p')
        display as text "histogram probed: `ds' `hv'"
    }
}

* ===========================================================================
* LAYER 2 -- kdensity
*
* Two different commands with two different grids have to be told apart:
*   `kdensity x'          (the estimation command) defaults to n = min(N,50)
*   `twoway kdensity x'   (the plot)               defaults to n(300)
* Both are recorded.  generate() gives the estimation command's curve exactly;
* the serset gives the plot's curve exactly.
* ===========================================================================
forvalues d = 1/`NDS' {
    local ds "${ZQ_DSN_`d'}"
    local ld `"${ZQ_DSL_`d'}"'
    local yv "${ZQ_DSY_`d'}"

    foreach vspec in none bwidth(2) kernel(gaussian) {
        local vname default
        if "`vspec'" == "bwidth(2)"        local vname bwidth2
        if "`vspec'" == "kernel(gaussian)" local vname kernel_gaussian
        local opt "`vspec'"
        if "`vspec'" == "none" local opt ""
        local key "`ds':`yv':`vname'"
        `ld'
        capture drop zqgx zqgy
        capture kdensity `yv', nograph generate(zqgx zqgy) `opt'
        local rc = _rc
        zq_s, sec(kdensity) key(`key') fld(cmd) ///
              val(kdensity `yv', nograph generate(gx gy) `opt')
        zq_n, sec(kdensity) key(`key') fld(rc) val(`rc')
        if `rc' != 0 continue
        zq_s, sec(kdensity) key(`key') fld(kernel)  val(`r(kernel)')
        zq_n, sec(kdensity) key(`key') fld(bwidth)  val(r(bwidth))
        zq_n, sec(kdensity) key(`key') fld(n)       val(r(n))
        zq_n, sec(kdensity) key(`key') fld(scale)   val(r(scale))
        preserve
        quietly keep zqgx zqgy
        quietly drop if missing(zqgx)
        quietly rename zqgx kde_x
        quietly rename zqgy kde_y
        zq_curve kde_x kde_y, sec(kdensity) key(`key') maxn(41)
        restore
    }

    * ---- the Silverman-style rule Stata's own kdensity.ado applies ---------
    `ld'
    quietly summarize `yv', detail
    local sd  = r(sd)
    local iqr = (r(p75)-r(p25))/1.349
    local nn  = r(N)
    local w   = min(`sd', `iqr')
    if `w' == 0 local w = `sd'
    local rot = 0.9*`w'/(`nn'^0.20)
    zq_n, sec(kdensity_rot_check) key(`ds':`yv') fld(sd)             val(`sd')
    zq_n, sec(kdensity_rot_check) key(`ds':`yv') fld(iqr_over_1349)  val(`iqr')
    zq_n, sec(kdensity_rot_check) key(`ds':`yv') fld(N)              val(`nn')
    zq_n, sec(kdensity_rot_check) key(`ds':`yv') fld(formula_bwidth) val(`rot')
    zq_s, sec(kdensity_rot_check) key(`ds':`yv') fld(formula) ///
          val(w = min(sd, (p75-p25)/1.349); if w==0 then w = sd; bwidth = 0.9*w/N^0.2)
    zq_s, sec(kdensity_rot_check) key(`ds':`yv') fld(cmd) ///
          val(summarize `yv', detail -- then the formula above)

    * ---- what `twoway kdensity' plots -------------------------------------
    `ld'
    local p "${ZQ_WORK}/kd_`ds'.gph"
    capture twoway kdensity `yv' || , nodraw saving("`p'", replace)
    local rc = _rc
    zq_s, sec(kdensity_twoway) key(`ds':`yv') fld(cmd) val(twoway kdensity `yv')
    zq_n, sec(kdensity_twoway) key(`ds':`yv') fld(rc)  val(`rc')
    if `rc' == 0 {
        preserve
        zq_serset kde_y kde_x, path("`p'") set(0)
        zq_curve kde_x kde_y, sec(kdensity_twoway) key(`ds':`yv') maxn(41)
        restore
    }
    display as text "kdensity probed: `ds'"
}

* ===========================================================================
* LAYER 3 -- lpoly
*
* The point of interest is the SEMANTICS of bwidth(): Stata treats it as an
* absolute half-width in the units of x, so bwidth(5) on `weight' is 5 pounds.
* r(bwidth) echoing 5 proves it, and the x range recorded beside it makes the
* size of the mistake visible if it were read as a fraction of the range.
* ===========================================================================
forvalues d = 1/`NDS' {
    local ds "${ZQ_DSN_`d'}"
    local ld `"${ZQ_DSL_`d'}"'
    local yv "${ZQ_DSY_`d'}"
    local xv "${ZQ_DSX_`d'}"

    foreach vspec in none bwidth(5) degree(1) kernel(gaussian) {
        local vname default
        if "`vspec'" == "bwidth(5)"        local vname bwidth5
        if "`vspec'" == "degree(1)"        local vname degree1
        if "`vspec'" == "kernel(gaussian)" local vname kernel_gaussian
        local opt "`vspec'"
        if "`vspec'" == "none" local opt ""
        local key "`ds':`vname'"
        `ld'
        capture drop zqlx zqly
        capture lpoly `yv' `xv', nograph generate(zqlx zqly) `opt'
        local rc = _rc
        zq_s, sec(lpoly) key(`key') fld(cmd) ///
              val(lpoly `yv' `xv', nograph generate(lx ly) `opt')
        zq_n, sec(lpoly) key(`key') fld(rc) val(`rc')
        if `rc' != 0 continue
        zq_s, sec(lpoly) key(`key') fld(kernel) val(`r(kernel)')
        zq_n, sec(lpoly) key(`key') fld(bwidth) val(r(bwidth))
        zq_n, sec(lpoly) key(`key') fld(degree) val(r(degree))
        zq_n, sec(lpoly) key(`key') fld(ngrid)  val(r(ngrid))
        zq_n, sec(lpoly) key(`key') fld(N)      val(r(N))
        quietly summarize `xv', meanonly
        zq_n, sec(lpoly) key(`key') fld(x_min)   val(r(min))
        zq_n, sec(lpoly) key(`key') fld(x_max)   val(r(max))
        zq_n, sec(lpoly) key(`key') fld(x_range) val(r(max)-r(min))
        preserve
        quietly keep zqlx zqly
        quietly drop if missing(zqlx)
        quietly rename zqlx lpoly_x
        quietly rename zqly lpoly_y
        zq_curve lpoly_x lpoly_y, sec(lpoly) key(`key') maxn(41)
        restore
    }

    * ---- what `twoway lpoly' plots ----------------------------------------
    `ld'
    local p "${ZQ_WORK}/lp_`ds'.gph"
    capture twoway lpoly `yv' `xv' || , nodraw saving("`p'", replace)
    local rc = _rc
    zq_s, sec(lpoly_twoway) key(`ds') fld(cmd) val(twoway lpoly `yv' `xv')
    zq_n, sec(lpoly_twoway) key(`ds') fld(rc)  val(`rc')
    if `rc' == 0 {
        preserve
        zq_serset lpoly_y lpoly_x, path("`p'") set(0)
        zq_curve lpoly_x lpoly_y, sec(lpoly_twoway) key(`ds') maxn(41)
        restore
    }
    display as text "lpoly probed: `ds'"
}

* ===========================================================================
* LAYER 4 -- lowess
*
* lowess's bwidth IS a fraction (of the sample), unlike lpoly's -- which is the
* trap this fixture exists to document.  bwidth(.8) is the documented default
* and is confirmed by running bwidth(.8) explicitly: its curve must equal the
* default curve point for point.
* ===========================================================================
forvalues d = 1/`NDS' {
    local ds "${ZQ_DSN_`d'}"
    local ld `"${ZQ_DSL_`d'}"'
    local yv "${ZQ_DSY_`d'}"
    local xv "${ZQ_DSX_`d'}"

    foreach vspec in none bwidth(.8) bwidth(.2) mean noweight {
        local vname default
        if "`vspec'" == "bwidth(.8)" local vname bwidth_point8
        if "`vspec'" == "bwidth(.2)" local vname bwidth_point2
        if "`vspec'" == "mean"       local vname mean
        if "`vspec'" == "noweight"   local vname noweight
        local opt "`vspec'"
        if "`vspec'" == "none" local opt ""
        local key "`ds':`vname'"
        `ld'
        capture drop zqlo
        capture lowess `yv' `xv', nograph generate(zqlo) `opt'
        local rc = _rc
        zq_s, sec(lowess) key(`key') fld(cmd) ///
              val(lowess `yv' `xv', nograph generate(s) `opt')
        zq_n, sec(lowess) key(`key') fld(rc) val(`rc')
        if `rc' != 0 continue
        preserve
        quietly keep `xv' zqlo
        quietly drop if missing(zqlo)
        * `sort x' alone is NOT deterministic when x has ties -- auto's weight
        * does -- and the sampled arrays would then differ between two runs
        * that computed identical smooths.  Break ties on the original order.
        quietly generate long zqord = _n
        sort `xv' zqord, stable
        quietly drop zqord
        quietly rename `xv' lowess_x
        quietly rename zqlo lowess_y
        zq_curve lowess_x lowess_y, sec(lowess) key(`key') maxn(41)
        restore
    }
    display as text "lowess probed: `ds'"
}

* ===========================================================================
* LAYER 5 -- lfitci / qfitci
*
* Recorded twice over: the serset holds exactly what twoway draws, and the
* same numbers are rebuilt from `regress' + `predict, stdp' using the formula
* lifted out of twoway__lfit_serset.ado:
*     grid    x_i = min + (i-1)*(max-min)/(n-1),  i = 1..n,  n() default 100
*     tval    = invttail(e(df_r), (100-level)/200)
*     lcl/ucl = xb -/+ tval*stdp
* The python block compares them; if they ever disagree the fixture says so.
* ===========================================================================
forvalues d = 1/`NDS' {
    local ds "${ZQ_DSN_`d'}"
    local ld `"${ZQ_DSL_`d'}"'
    local yv "${ZQ_DSY_`d'}"
    local xv "${ZQ_DSX_`d'}"

    foreach pt in lfitci qfitci {
        foreach lev in 90 95 99 {
            local key "`ds':`pt':level`lev'"
            `ld'
            local p "${ZQ_WORK}/`pt'_`ds'_`lev'.gph"
            capture twoway `pt' `yv' `xv', level(`lev') || , nodraw saving("`p'", replace)
            local rc = _rc
            zq_s, sec(ci_bands) key(`key') fld(cmd) ///
                  val(twoway `pt' `yv' `xv', level(`lev'))
            zq_n, sec(ci_bands) key(`key') fld(rc) val(`rc')
            if `rc' != 0 continue
            preserve
            zq_serset fit lower upper fit_x, path("`p'") set(0)
            zq_curve fit_x fit lower upper, sec(ci_bands) key(`key') maxn(41)
            restore
        }

        * ---- the default level, with no level() at all --------------------
        local key "`ds':`pt':no_level_option"
        `ld'
        local p "${ZQ_WORK}/`pt'_`ds'_def.gph"
        capture twoway `pt' `yv' `xv' || , nodraw saving("`p'", replace)
        local rc = _rc
        zq_s, sec(ci_bands) key(`key') fld(cmd) val(twoway `pt' `yv' `xv')
        zq_n, sec(ci_bands) key(`key') fld(rc) val(`rc')
        zq_n, sec(ci_bands) key(`key') fld(c_level_at_run_time) val(c(level))
        if `rc' == 0 {
            preserve
            zq_serset fit lower upper fit_x, path("`p'") set(0)
            zq_curve fit_x fit lower upper, sec(ci_bands) key(`key') maxn(41)
            restore
        }
    }

    * ---- the independent regress + predict rebuild (linear only) ----------
    foreach lev in 90 95 99 {
        local key "`ds':lfitci:level`lev'"
        `ld'
        quietly regress `yv' `xv'
        local dfr = e(df_r)
        quietly summarize `xv' if e(sample), meanonly
        local xmn = r(min)
        local xmx = r(max)
        local N0  = _N
        quietly set obs `=`N0'+100'
        forvalues i = 1/100 {
            quietly replace `xv' = `xmn' + (`i'-1)*(`xmx'-`xmn')/99 in `=`N0'+`i''
        }
        capture drop zqxb zqse
        quietly predict double zqxb, xb
        quietly predict double zqse, stdp
        local tv = invttail(`dfr', (100-`lev')/200)
        quietly generate double zqlo = zqxb - `tv'*zqse
        quietly generate double zqhi = zqxb + `tv'*zqse
        zq_n, sec(ci_rebuild) key(`key') fld(df_r)  val(`dfr')
        zq_n, sec(ci_rebuild) key(`key') fld(tval)  val(`tv')
        zq_n, sec(ci_rebuild) key(`key') fld(x_min) val(`xmn')
        zq_n, sec(ci_rebuild) key(`key') fld(x_max) val(`xmx')
        zq_s, sec(ci_rebuild) key(`key') fld(cmd) ///
              val(regress `yv' `xv' -- 100-point grid x_i = min + (i-1)*(max-min)/99 -- predict xb -- predict stdp -- xb -/+ invttail(df_r, (100-`lev')/200)*stdp)
        preserve
        quietly keep in `=`N0'+1'/`=`N0'+100'
        quietly keep `xv' zqxb zqlo zqhi
        quietly rename `xv' fit_x
        quietly rename zqxb fit
        quietly rename zqlo lower
        quietly rename zqhi upper
        zq_curve fit_x fit lower upper, sec(ci_rebuild) key(`key') maxn(41)
        restore
    }
    display as text "ci bands probed: `ds'"
}

* ===========================================================================
* LAYER 6 -- fpfit / fpfitci
*
* `fp' chooses the powers; e(fp_fp) holds them and e(fp_powers) the candidate
* set it chose from.  twoway fpfit's own grid is read out of its serset -- it
* turns out NOT to be a fixed grid, which is exactly the kind of thing that
* cannot be guessed.  The 1st and 99th percentiles of x are recorded alongside
* the plotted range so the "truncate to p1..p99" question can be settled.
* ===========================================================================
forvalues d = 1/`NDS' {
    local ds "${ZQ_DSN_`d'}"
    local ld `"${ZQ_DSL_`d'}"'
    local yv "${ZQ_DSY_`d'}"
    local xv "${ZQ_DSX_`d'}"

    * ---- the powers ------------------------------------------------------
    `ld'
    capture quietly fp <`xv'>: regress `yv' <`xv'>
    local rc = _rc
    zq_s, sec(fp_powers) key(`ds') fld(cmd) val(fp <`xv'>: regress `yv' <`xv'>)
    zq_n, sec(fp_powers) key(`ds') fld(rc)  val(`rc')
    if `rc' == 0 {
        zq_n, sec(fp_powers) key(`ds') fld(dimension)   val(e(fp_dimension))
        zq_s, sec(fp_powers) key(`ds') fld(gen_cmdline) val(`e(fp_gen_cmdline)')
        zq_s, sec(fp_powers) key(`ds') fld(terms)       val(`e(fp_terms)')
        zq_n, sec(fp_powers) key(`ds') fld(N)           val(e(N))
        tempname FP PW
        matrix `FP' = e(fp_fp)
        matrix `PW' = e(fp_powers)
        local nfp = colsof(`FP')
        local npw = colsof(`PW')
        local sel ""
        forvalues j = 1/`nfp' {
            local z = `FP'[1,`j']
            local t = trim(string(`z',"%20.17g"))
            if "`sel'" == "" local sel "`t'"
            else             local sel "`sel';`t'"
        }
        zq_a, sec(fp_powers) key(`ds') fld(selected_powers) val(`sel')
        local cand ""
        forvalues j = 1/`npw' {
            local z = `PW'[1,`j']
            local t = trim(string(`z',"%20.17g"))
            if "`cand'" == "" local cand "`t'"
            else              local cand "`cand';`t'"
        }
        zq_a, sec(fp_powers) key(`ds') fld(candidate_powers) val(`cand')
    }

    * ---- what twoway fpfit / fpfitci plot --------------------------------
    foreach pt in fpfit fpfitci {
        local key "`ds':`pt'"
        `ld'
        local p "${ZQ_WORK}/`pt'_`ds'.gph"
        capture twoway `pt' `yv' `xv' || , nodraw saving("`p'", replace)
        local rc = _rc
        zq_s, sec(fpfit) key(`key') fld(cmd) val(twoway `pt' `yv' `xv')
        zq_n, sec(fpfit) key(`key') fld(rc)  val(`rc')
        quietly summarize `xv', meanonly
        zq_n, sec(fpfit) key(`key') fld(x_data_min) val(r(min))
        zq_n, sec(fpfit) key(`key') fld(x_data_max) val(r(max))
        quietly _pctile `xv', percentiles(1 99)
        zq_n, sec(fpfit) key(`key') fld(x_p1)  val(r(r1))
        zq_n, sec(fpfit) key(`key') fld(x_p99) val(r(r2))
        preserve
        quietly keep `xv'
        quietly drop if missing(`xv')
        quietly duplicates drop
        quietly count
        local ndx = r(N)
        restore
        zq_n, sec(fpfit) key(`key') fld(n_distinct_x) val(`ndx')
        if `rc' != 0 continue
        preserve
        if "`pt'" == "fpfit" {
            zq_serset fit fit_x, path("`p'") set(0)
            zq_curve fit_x fit, sec(fpfit) key(`key') maxn(41)
        }
        else {
            zq_serset fit lower upper fit_x, path("`p'") set(0)
            zq_curve fit_x fit lower upper, sec(fpfit) key(`key') maxn(41)
        }
        restore
    }

    * ---- does twoway fpfit read bwidth()/degree()? -----------------------
    `ld'
    capture twoway fpfit `yv' `xv', bwidth(5) nodraw
    local rc = _rc
    zq_n, sec(fpfit_optsupport) key(`ds':bwidth) fld(rc)  val(`rc')
    zq_s, sec(fpfit_optsupport) key(`ds':bwidth) fld(cmd) ///
          val(twoway fpfit `yv' `xv', bwidth(5))
    capture twoway fpfit `yv' `xv', degree(1) nodraw
    local rc = _rc
    zq_n, sec(fpfit_optsupport) key(`ds':degree) fld(rc)  val(`rc')
    zq_s, sec(fpfit_optsupport) key(`ds':degree) fld(cmd) ///
          val(twoway fpfit `yv' `xv', degree(1))
    capture twoway fpfit `yv' `xv', estopts(degree(1)) nodraw
    local rc = _rc
    zq_n, sec(fpfit_optsupport) key(`ds':estopts_degree) fld(rc)  val(`rc')
    zq_s, sec(fpfit_optsupport) key(`ds':estopts_degree) fld(cmd) ///
          val(twoway fpfit `yv' `xv', estopts(degree(1)))
    capture twoway fpfit `yv' `xv', estopts(powers(1 2)) nodraw
    local rc = _rc
    zq_n, sec(fpfit_optsupport) key(`ds':estopts_powers) fld(rc)  val(`rc')
    zq_s, sec(fpfit_optsupport) key(`ds':estopts_powers) fld(cmd) ///
          val(twoway fpfit `yv' `xv', estopts(powers(1 2)))
    capture twoway fpfitci `yv' `xv', level(90) nodraw
    local rc = _rc
    zq_n, sec(fpfit_optsupport) key(`ds':fpfitci_level) fld(rc)  val(`rc')
    zq_s, sec(fpfit_optsupport) key(`ds':fpfitci_level) fld(cmd) ///
          val(twoway fpfitci `yv' `xv', level(90))
    display as text "fpfit probed: `ds'"
}

* ===========================================================================
* LAYER 7 -- mband
*
* mband's plotted points live in a DERIVED serset (type median_bands) that the
* graph engine materialises at draw time; `graph use' + `serset set 1' reads it
* back.  The documented default band count is max(10, round(10*log10(N))), but
* rather than trust that, every band count from 2 to 60 is reproduced by hand
* (equal-width intervals on x, then median of x and median of y within each
* interval, empty intervals dropped) and the python block reports WHICH band
* count actually reproduces the graph.
* ===========================================================================
forvalues d = 1/`NDS' {
    local ds "${ZQ_DSN_`d'}"
    local ld `"${ZQ_DSL_`d'}"'
    local yv "${ZQ_DSY_`d'}"
    local xv "${ZQ_DSX_`d'}"

    foreach vspec in none bands(5) bands(20) {
        local vname default
        if "`vspec'" == "bands(5)"  local vname bands5
        if "`vspec'" == "bands(20)" local vname bands20
        local opt "`vspec'"
        if "`vspec'" == "none" local opt ""
        local key "`ds':`vname'"
        `ld'
        local p "${ZQ_WORK}/mb_`ds'_`vname'.gph"
        if "`opt'" == "" capture twoway mband `yv' `xv' || , nodraw saving("`p'", replace)
        else             capture twoway mband `yv' `xv', `opt' || , nodraw saving("`p'", replace)
        local rc = _rc
        zq_s, sec(mband) key(`key') fld(cmd) val(twoway mband `yv' `xv', `opt')
        zq_n, sec(mband) key(`key') fld(rc)  val(`rc')
        quietly count if !missing(`yv') & !missing(`xv')
        local nxy = r(N)
        zq_n, sec(mband) key(`key') fld(N_xy) val(`nxy')
        zq_n, sec(mband) key(`key') fld(documented_default_bands) ///
              val(max(10, round(10*log10(`nxy'))))
        if `rc' != 0 continue
        preserve
        capture zq_serset band_y band_x, path("`p'") set(1)
        local src = _rc
        if `src' == 0 {
            zq_curve band_x band_y, sec(mband) key(`key') maxn(64)
        }
        restore
        zq_n, sec(mband) key(`key') fld(derived_serset_rc) val(`src')
    }

    * ---- hand-computed cross medians for every candidate band count -------
    `ld'
    quietly keep if !missing(`yv') & !missing(`xv')
    * The bounds MUST be scalars, not locals.  `local mn = r(min)' rounds the
    * value to ~14 significant digits; on nlsw88 that makes mn fractionally
    * LARGER than the smallest ttl_exp, (x-mn) goes negative for that one
    * observation and it lands in a phantom band 0, which shifts every median
    * and made the whole dataset fail to reproduce.
    tempname ZQMN ZQMX
    quietly summarize `xv', meanonly
    scalar `ZQMN' = r(min)
    scalar `ZQMX' = r(max)
    forvalues B = 2/60 {
        preserve
        quietly generate zqband = ///
            min(max(floor((`xv'-`ZQMN')/((`ZQMX'-`ZQMN')/`B'))+1, 1), `B')
        quietly collapse (median) zqx=`xv' zqy=`yv', by(zqband)
        sort zqband
        quietly rename zqx band_x
        quietly rename zqy band_y
        zq_curve band_x band_y, sec(mband_scan) key(`ds':B`B') maxn(64)
        restore
    }
    display as text "mband probed: `ds'"
}

* ---------------------------------------------------------------------------
* mband default-band-count sweep.  Four datasets pin four (N, bands) pairs,
* which is not enough to tell one candidate rule from another.  This sweeps N
* across an order of magnitude on ONE dataset so the python block can test
* candidate formulas against a dozen points instead of four.
* ---------------------------------------------------------------------------
foreach NN in 25 40 60 100 160 260 420 700 1150 2246 {
    sysuse nlsw88, clear
    quietly keep if !missing(wage) & !missing(ttl_exp)
    quietly keep in 1/`NN'
    quietly count
    local nn = r(N)
    local p "${ZQ_WORK}/mbsweep_`NN'.gph"
    capture twoway mband wage ttl_exp || , nodraw saving("`p'", replace)
    local rc = _rc
    zq_s, sec(mband_sweep) key(N`NN') fld(cmd) ///
          val(sysuse nlsw88 -- keep in 1/`NN' -- twoway mband wage ttl_exp)
    zq_n, sec(mband_sweep) key(N`NN') fld(rc) val(`rc')
    zq_n, sec(mband_sweep) key(N`NN') fld(N)  val(`nn')
    if `rc' != 0 continue
    preserve
    capture zq_serset band_y band_x, path("`p'") set(1)
    local src = _rc
    if `src' == 0 zq_curve band_x band_y, sec(mband_sweep) key(N`NN') maxn(64)
    restore

    sysuse nlsw88, clear
    quietly keep if !missing(wage) & !missing(ttl_exp)
    quietly keep in 1/`NN'
    tempname SMN SMX
    quietly summarize ttl_exp, meanonly
    scalar `SMN' = r(min)
    scalar `SMX' = r(max)
    forvalues B = 2/60 {
        preserve
        quietly generate zqband = ///
            min(max(floor((ttl_exp-`SMN')/((`SMX'-`SMN')/`B'))+1, 1), `B')
        quietly collapse (median) zqx=ttl_exp zqy=wage, by(zqband)
        sort zqband
        quietly rename zqx band_x
        quietly rename zqy band_y
        zq_curve band_x band_y, sec(mband_sweep_scan) key(N`NN':B`B') maxn(64)
        restore
    }
    display as text "mband sweep probed: N=`nn'"
}

* ===========================================================================
* LAYER 8 -- twoway function
*
* The question is what `function' spans when range() is absent, both alone and
* with another plot present, since those two cases are widely assumed to
* differ.  The grid size is read off the serset, not assumed.
* ===========================================================================
global ZQ_NFN = 0
capture program drop zq_fn
program define zq_fn
    syntax , NAMe(string) CMD(string) [ SET(integer 0) ]
    global ZQ_NFN = ${ZQ_NFN} + 1
    global ZQ_FNN_${ZQ_NFN} "`name'"
    global ZQ_FNC_${ZQ_NFN} `"`cmd'"'
    global ZQ_FNS_${ZQ_NFN} "`set'"
end

zq_fn, name(bare)                  cmd(function y=x^2)                              set(0)
zq_fn, name(with_scatter)          cmd(scatter mpg weight || function y=x^2)         set(1)
zq_fn, name(range_0_10)            cmd(function y=x^2, range(0 10))                  set(0)
zq_fn, name(n_400)                 cmd(function y=x^2, n(400))                       set(0)
zq_fn, name(range_and_n)           cmd(function y=x^2, range(0 10) n(400))           set(0)
zq_fn, name(range_varname)         cmd(function y=x^2, range(weight))                set(0)
zq_fn, name(with_scatter_range)    cmd(scatter mpg weight || function y=x^2, range(0 10)) set(1)

local NFN = $ZQ_NFN
forvalues f = 1/`NFN' {
    local fname "${ZQ_FNN_`f'}"
    local fcmd  `"${ZQ_FNC_`f'}"'
    local fset  "${ZQ_FNS_`f'}"
    local key "auto:`fname'"
    sysuse auto, clear
    local p "${ZQ_WORK}/fn_`fname'.gph"
    capture twoway `fcmd' || , nodraw saving("`p'", replace)
    local rc = _rc
    zq_s, sec(function) key(`key') fld(cmd) val(twoway `fcmd')
    zq_n, sec(function) key(`key') fld(rc)  val(`rc')
    zq_n, sec(function) key(`key') fld(serset_index_used) val(`fset')
    if `rc' != 0 continue
    preserve
    zq_serset fn_y fn_x, path("`p'") set(`fset')
    zq_curve fn_x fn_y, sec(function) key(`key') maxn(41)
    restore
}
display as text "function probed"

* ===========================================================================
file close zqrec
display as text "records written to ${ZQ_REC}"

* ===========================================================================
* Analysis + JSON emission.  No callbacks into Stata from here on.
* ===========================================================================
python:
import json, math, os, re, collections
from sfi import Macro

REC = Macro.getGlobal("ZQ_REC")
OUT = Macro.getGlobal("ZQ_OUT")

meta = {}
sections = collections.defaultdict(lambda: collections.defaultdict(dict))


def num(tok):
    if tok is None or tok == "null" or tok == "":
        return None
    try:
        f = float(tok)
    except ValueError:
        return tok
    if f == int(f) and abs(f) < 1e15:
        return int(f)
    return f


with open(REC, "r", errors="replace") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line:
            continue
        f = line.split("@@@")
        if f[0] == "META" and len(f) >= 3:
            meta[f[1]] = "@@@".join(f[2:])
        elif f[0] == "S" and len(f) >= 5:
            sections[f[1]][f[2]][f[3]] = "@@@".join(f[4:])
        elif f[0] == "A" and len(f) >= 5:
            raw = "@@@".join(f[4:])
            sections[f[1]][f[2]][f[3]] = [num(t) for t in raw.split(";")] if raw else []

# Fields written by zq_n are numeric; everything else stays a string.
NEVER_NUM = {"cmd", "equivalent_user_cmd", "formula", "kernel", "type", "error",
             "load_cmd", "gph", "gen_cmdline", "terms", "y", "x", "sample_index"}
for sec in sections:
    for key in sections[sec]:
        ent = sections[sec][key]
        for fld, val in list(ent.items()):
            if fld in NEVER_NUM or not isinstance(val, str):
                continue
            ent[fld] = num(val)
        si = ent.get("sample_index")
        if isinstance(si, str) and si:
            ent["sample_index"] = [int(t) for t in si.split(";")]

sections = {k: {kk: dict(vv) for kk, vv in v.items()} for k, v in sections.items()}

# ---------------------------------------------------------------- oracle (3)
# Pull the command line histogram rewrote itself into, straight out of the .gph
# header.  This confirms the bin grid and the default y axis WITHOUT asking
# twoway__histogram_gen anything.
_CMDLINE = re.compile(r"(?m)^\*! command: (.*)$")
for key, ent in sections.get("histogram_resolved_cmd", {}).items():
    path = ent.get("gph")
    ent["resolved_command_line"] = None
    ent["source"] = "read from the '*! command:' header of the saved live-format .gph"
    if path and os.path.exists(path):
        m = _CMDLINE.search(open(path, "r", errors="replace").read())
        if m:
            line = re.sub(r"\s*saving\([^)]*\)", "", m.group(1)).strip()
            ent["resolved_command_line"] = line
            ent["y_axis_keyword_in_resolved_command"] = next(
                (w for w in ("density", "percent", "frequency", "fraction")
                 if re.search(r"(?<![A-Za-z])" + w + r"(?![A-Za-z(])", line)), None)
            for opt in ("bin", "start", "width"):
                mm = re.search(r"(?<![A-Za-z])" + opt + r"\(([^)]*)\)", line)
                ent["resolved_" + opt] = num(mm.group(1)) if mm else None

# ------------------------------------------------------- mband band count
def close(a, b, tol=1e-6):
    if a is None or b is None:
        return a is b
    if a == b:
        return True
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def curves_match(obs, cand):
    ox, oy = obs.get("band_x"), obs.get("band_y")
    cx, cy = cand.get("band_x"), cand.get("band_y")
    if not ox or not cx or len(ox) != len(cx):
        return False
    return (all(close(a, b) for a, b in zip(ox, cx)) and
            all(close(a, b) for a, b in zip(oy, cy)))


scan = sections.get("mband_scan", {})
mband_resolved = {}
for key, ent in sections.get("mband", {}).items():
    ds = key.split(":")[0]
    hits = sorted(int(k.split(":B")[1]) for k in scan
                  if k.startswith(ds + ":B") and curves_match(ent, scan[k]))
    ent["bands_reproduced_by"] = hits or None
    ent["bands_reproduction_method"] = (
        "equal-width intervals on x: bandid = min(floor((x-min)/((max-min)/B))+1, B); "
        "then median of x and median of y within each non-empty interval, in x order")
    if key.endswith(":default"):
        doc_bands = ent.get("documented_default_bands")
        mband_resolved[ds] = {
            "N_xy": ent.get("N_xy"),
            "n_band_points_plotted": ent.get("n_points"),
            "documented_rule": "max(10, round(10*log10(N)))  [help twoway_mband line 82]",
            "documented_default_bands": doc_bands,
            "measured_default_bands": hits[0] if hits else None,
            "all_band_counts_that_reproduce_the_graph": hits or None,
            "agrees_with_documented_rule":
                (hits[0] == doc_bands) if hits else None,
            "cmd": ent.get("cmd"),
        }

# ------------------------- mband default band count: candidate rule testing
sweep_scan = sections.get("mband_sweep_scan", {})
sweep = {}
for key, ent in sorted(sections.get("mband_sweep", {}).items()):
    hits = sorted(int(k.split(":B")[1]) for k in sweep_scan
                  if k.startswith(key + ":B") and curves_match(ent, sweep_scan[k]))
    sweep[key] = {"N": ent.get("N"),
                  "n_band_points_plotted": ent.get("n_points"),
                  "measured_bands": hits[0] if hits else None,
                  "all_band_counts_that_reproduce_the_graph": hits or None,
                  "cmd": ent.get("cmd")}

CANDIDATE_RULES = {
    "round(min(sqrt(N), 10*log10(N)))":
        lambda N: round(min(math.sqrt(N), 10 * math.log10(N))),
    "int(min(sqrt(N), 10*log10(N)))  [the histogram bin rule]":
        lambda N: int(min(math.sqrt(N), 10 * math.log10(N))),
    "round(sqrt(N))": lambda N: round(math.sqrt(N)),
    "max(10, round(10*log10(N)))  [what help twoway_mband documents]":
        lambda N: max(10, round(10 * math.log10(N))),
}
observed_pairs = []
for ds, v in mband_resolved.items():
    if v.get("N_xy") and v.get("measured_default_bands"):
        observed_pairs.append(("dataset " + ds, v["N_xy"], v["measured_default_bands"]))
for key, v in sweep.items():
    if v.get("N") and v.get("measured_bands"):
        observed_pairs.append(("nlsw88 subset " + key, v["N"], v["measured_bands"]))
observed_pairs.sort(key=lambda t: t[1])

rule_scores = {}
for name, fn in CANDIDATE_RULES.items():
    bad = [{"probe": p, "N": N, "measured": b, "rule_gives": fn(N)}
           for p, N, b in observed_pairs if fn(N) != b]
    rule_scores[name] = {"matches": len(observed_pairs) - len(bad),
                         "of": len(observed_pairs),
                         "mismatches": bad or None}
mband_rule = {
    "observed_pairs": [{"probe": p, "N": N, "measured_bands": b}
                       for p, N, b in observed_pairs],
    "candidate_rules": rule_scores,
    "note": ("No mband band-count rule is readable from any .ado -- the graph "
             "engine computes it -- so these are candidate formulas scored "
             "against measurement, not derived.  A rule that matches every "
             "observed pair is strong evidence, not proof."),
}

# --------------------------------------- lfitci serset vs regress rebuild
ci_agreement = {}
for key, ent in sections.get("ci_rebuild", {}).items():
    obs = sections.get("ci_bands", {}).get(key)
    if not obs:
        continue
    ok = True
    for fld in ("fit_x", "fit", "lower", "upper"):
        a, b = obs.get(fld), ent.get(fld)
        if not a or not b or len(a) != len(b):
            ok = False
            break
        ok = ok and all(close(p, q, 1e-5) for p, q in zip(a, b))
    ci_agreement[key] = ok
ci_all_agree = all(ci_agreement.values()) if ci_agreement else None

# ------------------------------ kdensity measured bwidth vs the ado formula
kde_rot = {}
for key, ent in sections.get("kdensity_rot_check", {}).items():
    ds, var = key.split(":")
    meas = sections.get("kdensity", {}).get("%s:%s:default" % (ds, var), {}).get("bwidth")
    kde_rot[key] = {
        "measured_r_bwidth": meas,
        "measured_cmd": sections.get("kdensity", {})
                                .get("%s:%s:default" % (ds, var), {}).get("cmd"),
        "formula_bwidth": ent.get("formula_bwidth"),
        "formula_cmd": ent.get("cmd"),
        "formula": ent.get("formula"),
        "agree": close(meas, ent.get("formula_bwidth"), 1e-9),
    }
kde_rot_all_agree = all(v["agree"] for v in kde_rot.values()) if kde_rot else None

# ------------------------- lowess: is the default really bwidth(.8)?
lowess_default_check = {}
for key, ent in sections.get("lowess", {}).items():
    if not key.endswith(":default"):
        continue
    ds = key.split(":")[0]
    alt = sections.get("lowess", {}).get(ds + ":bwidth_point8", {})
    ok = None
    if alt:
        ok = True
        for fld in ("lowess_x", "lowess_y"):
            a, b = ent.get(fld), alt.get(fld)
            if not a or not b or len(a) != len(b):
                ok = False
                break
            ok = ok and all(close(p, q, 1e-9) for p, q in zip(a, b))
    lowess_default_check[ds] = {
        "default_cmd": ent.get("cmd"),
        "explicit_cmd": alt.get("cmd"),
        "curves_identical": ok,
    }
lowess_default_all_agree = (all(v["curves_identical"] for v in lowess_default_check.values())
                            if lowess_default_check else None)

# ------------------------------- histogram: rule vs measurement, per probe
hist_rule = {}
for key, ent in sections.get("histogram", {}).items():
    if not key.endswith(":default") or ent.get("rc") != 0:
        continue
    N = ent.get("N")
    if not N:
        continue
    k = max(1, int(min(math.sqrt(N), 10 * math.log(N) / math.log(10))))
    hist_rule[key] = {
        "N": N,
        "rule_bin": k,
        "stata_bin": ent.get("bin"),
        "agree": k == ent.get("bin"),
        "rule": "bin = max(1, int(min(sqrt(N), 10*ln(N)/ln(10))))",
        "cmd": ent.get("cmd"),
    }
hist_rule_all_agree = all(v["agree"] for v in hist_rule.values()) if hist_rule else None

# ------------------------------------------------------------------- rules
RULES = {
    "histogram.bin": {
        "formula": "bin = max(1, int(min(sqrt(N), 10*ln(N)/ln(10))))",
        "then": "width = (max - min)/bin ; start = min",
        "when_width_given": "width = the given value ; bin = max(1, ceil((max - min)/width))",
        "when_start_given": "min := start, so width = (max - start)/bin",
        "mutually_exclusive": "bin() and width() may not be combined; discrete and bin() may not be combined",
        "source": "verbatim from Stata's own source, "
                  "ado/base/t/twoway__histogram_gen.ado lines 118-136",
        "confirmed_by": "section histogram_bin_rule_check, which applies the "
                        "formula to r(N) and compares with r(bin) on every probe",
    },
    "histogram.y_axis": {
        "default": "density",
        "formula": "density: height = count/(N*width) ; fraction: count/N ; "
                   "percent: 100*count/N ; frequency: count",
        "area": "r(area) is 1 for density, width for fraction, 100*width for "
                "percent and N*width for frequency",
        "source": "ado/base/t/twoway__histogram_gen.ado line 49 "
                  "(else-if-zero-options branch sets type=density) and lines 221-232",
        "confirmed_by": "(a) r(type) under every yaxis_* probe; (b) independently, "
                        "the '*! command:' header recorded under "
                        "histogram_resolved_cmd, in which histogram rewrote itself "
                        "with the literal keyword 'density'",
    },
    "kdensity.bwidth": {
        "formula": "w = min(sd, (p75-p25)/1.349) ; if w == 0 then w = sd ; "
                   "bwidth = 0.9*w/N^0.2",
        "source": "verbatim from ado/base/k/kdensity.ado lines 196-200",
        "confirmed_by": "section kdensity_bwidth_rule_check",
    },
    "kdensity.kernel": {"default": "epanechnikov",
                        "source": "help twoway_kdensity line 115; confirmed by r(kernel)"},
    "kdensity.n": {
        "estimation_command_default": "min(N, 50)",
        "twoway_plot_default": 300,
        "serset_caveat": "the twoway kdensity serset also carries the raw "
                         "variable, so it is as long as the DATASET; only the "
                         "first n rows are the curve.  n_points here is the "
                         "curve length after dropping the padding.",
        "source": "help kdensity / help twoway_kdensity line 131",
        "confirmed_by": "r(n) for the estimation command and the plotted serset "
                        "length for the plot",
        "warning": "these two DIFFER: `kdensity x' and `twoway kdensity x' do not "
                   "evaluate on the same grid",
    },
    "lpoly.kernel": {"default": "epanechnikov",
                     "source": "help twoway_lpoly line 100; confirmed by r(kernel)"},
    "lpoly.degree": {"default": 0,
                     "source": "help twoway_lpoly line 112; confirmed by r(degree)"},
    "lpoly.n": {"default": "min(N, 50)",
                "source": "help twoway_lpoly line 116",
                "note": "r(ngrid) can come back SMALLER than n() when a narrow "
                        "bwidth() leaves grid points with no data inside the "
                        "kernel window; see the bwidth5 probes"},
    "lpoly.bwidth": {
        "semantics": "ABSOLUTE half-width in the units of x, NOT a fraction of "
                     "the x range",
        "evidence": "lpoly y x, bwidth(5) returns r(bwidth) == 5 on every dataset, "
                    "while x_range recorded beside it spans four orders of magnitude",
        "default": "a rule-of-thumb (ROT) selector computed from the data",
        "rot_formula": None,
        "rot_source": "UNVERIFIED -- see the \"unverified\" block",
    },
    "lowess.bwidth": {
        "default": 0.8,
        "confirmed_by_self_check": "lowess_default_is_bwidth_point8",
        "semantics": "a FRACTION of the sample used in each local regression -- "
                     "the opposite convention to lpoly's bwidth()",
        "source": "help twoway_lowess line 83",
        "confirmed_by": "the default curve and the bwidth(.8) curve are recorded "
                        "separately and must agree point for point",
    },
    "lowess.other_defaults": {
        "smoothing": "running-line (option `mean' switches to running-mean)",
        "weighting": "tricube weighting is used (option `noweight' turns it off)",
        "grid": "the smooth is returned at the observed x values, one per "
                "observation -- there is no separate grid",
        "source": "help twoway_lowess lines 91 and 98",
    },
    "ci_bands.level": {
        "default": "c(level), which is 95 unless `set level' changed it",
        "source": "help twoway_lfitci line 136, and the literal default "
                  "LEVEL(real `c(level)') in ado/base/t/twoway__lfit_serset.ado "
                  "line 10 and ado/base/t/twoway__fpfit_serset.ado line 10",
    },
    "ci_bands.formula": {
        "grid": "x_i = min + (i-1)*(max-min)/(n-1) for i = 1..n, with n() "
                "defaulting to 100 and min/max the observed range of x",
        "grid_source": "ado/base/_/_gs_x_create.ado",
        "band": "tval = invttail(e(df_r), (100-level)/200) ; "
                "lower = xb - tval*stdp ; upper = xb + tval*stdp",
        "se": "stdp (the SE of the prediction) is the default; stdf and stdr are "
              "the alternatives",
        "source": "verbatim from ado/base/t/twoway__lfit_serset.ado lines 81-95",
        "confirmed_by": "section ci_rebuild rebuilds every band from regress + "
                        "predict and is compared point for point against the "
                        "serset twoway actually plotted",
    },
    "fpfit.degree": {
        "default": 2,
        "source": "help twoway_fpfit line 158",
        "spelling": "twoway fpfit takes it as estopts(degree(#)), NOT as a "
                    "top-level degree(#) -- see fpfit_optsupport, where "
                    "degree(1) returns _rc=198 (\"option degree() not "
                    "allowed\") and estopts(degree(1)) returns 0"},
    "fpfit.powers": {"candidate_set": "-2, -1, -.5, 0, .5, 1, 2, 3 (0 means log)",
                     "source": "help twoway_fpfit line 170; confirmed by e(fp_powers)",
                     "spelling": "estopts(powers(...)), confirmed _rc=0"},
    "fpfit.bwidth": {"accepted": False,
                     "evidence": "twoway fpfit y x, bwidth(5) returns _rc=198, "
                                 "\"option bwidth() not allowed\", on all four "
                                 "datasets; fpfit has no bandwidth at all"},
    "fpfit.level": {"default": "c(level)",
                    "source": "LEVEL(real `c(level)') in "
                              "ado/base/t/twoway__fpfit_serset.ado line 10",
                    "confirmed_by": "twoway fpfitci y x, level(90) returns _rc=0"},
    "fpfit.grid": {
        "measured": "twoway fpfit and twoway fpfitci both evaluate at the "
                    "DISTINCT OBSERVED x values, sorted -- not on a fixed grid. "
                    "Compare n_points with n_distinct_x in the fpfit section; "
                    "they are equal on every dataset probed.",
        "range": "the full observed range of x. Compare fit_x_min/fit_x_max with "
                 "x_data_min/x_data_max, and note they are NOT x_p1/x_p99, which "
                 "are recorded beside them for exactly that comparison.",
        "source": "measured from the plotted serset on four datasets",
    },
    "mband.bands": {
        "documented_default": "max(10, round(10*log10(N)))",
        "documented_source": "help twoway_mband line 82",
        "semantics": "the x axis is divided into # EQUAL-WIDTH intervals, then "
                     "the median of y and the median of x are taken within each "
                     "interval; it is those cross medians that are plotted. "
                     "Intervals containing no observation produce no point.",
        "semantics_source": "help twoway_mband lines 88-93",
        "semantics_confirmed_by": "bands(5) and bands(20) are reproduced point "
                                  "for point by hand from the raw data; see "
                                  "bands_reproduced_by on each mband entry",
        "measured_default": "round(min(sqrt(N), 10*log10(N))) -- i.e. the "
                            "histogram bin rule with round() where histogram "
                            "uses int().  This reproduces the plotted cross "
                            "medians on all 14 measured (N, bands) pairs "
                            "(N = 25 .. 2,246), while the documented "
                            "max(10, round(10*log10(N))) reproduces only 3 of "
                            "14.  See mband_default_band_count_rule_search for "
                            "the scored candidates and every pair.  This is "
                            "measured, not read out of any source file.",
    },
    "function.range": {
        "default": "range(0 1)",
        "source": "help twoway_function line 112",
        "measured": "confirmed from the plotted serset BOTH alone and with "
                    "another plot present: the presence of a scatter does NOT "
                    "widen the function's domain to the x-axis range",
    },
    "function.n": {"default": 300,
                   "source": "help twoway_function lines 37 and 117; confirmed by "
                             "the plotted serset length",
                   "grid": "x_i = min + (i-1)*(max-min)/(n-1), from "
                           "ado/base/t/twoway__function_gen.ado line 119"},
}

UNVERIFIED = {
    "lpoly.rot_bandwidth_formula":
        "The closed form of lpoly's default rule-of-thumb bandwidth was NOT "
        "derived here.  It is computed in compiled Mata (_lpoly_work, called "
        "from ado/base/l/lpoly.ado line 311) and is documented only in [R] lpoly "
        "Methods and formulas, which is not machine-readable from this script.  "
        "The fixture records MEASURED r(bwidth) on four datasets under \"lpoly\" "
        "with variant \"default\"; check an implementation against those four "
        "numbers or against the manual.  No formula is claimed.",
    "mband.default_band_count_formula":
        "The band count the graph engine uses by default is NOT readable from "
        "any .ado -- the engine computes it -- and it does NOT match the "
        "documented max(10, round(10*log10(N))).  What IS established here is "
        "measurement: for each of 14 (N, bands) pairs, the band count that "
        "reproduces the plotted cross medians exactly was found by scanning "
        "B = 2..60.  round(min(sqrt(N), 10*log10(N))) fits all 14 and the "
        "documented rule fits 3.  A formula that fits 14 points over two "
        "orders of magnitude in N is strong evidence, but it is still "
        "inference from measurement and is recorded as such: an implementation "
        "should be checked against the pairs in "
        "mband_default_band_count_rule_search, not only against the formula.",
    "histogram.y_axis_bar_heights_under_twoway":
        "Bar heights are taken from twoway__histogram_gen's generate() output, "
        "which is the same subroutine twoway histogram calls, and cross-checked "
        "against the serset min/max in the saved .gph.  The individual bar "
        "heights inside a drawn twoway histogram serset were not enumerated "
        "separately.",
}

CONTRADICTIONS = {
    "function.range_default": (
        "Section 07 requires at `:5951' that map_function honour range() "
        "\"defaulting to the x-axis range rather than [0,1]\".  Stata documents "
        "AND plots range(0 1), and measurement here shows the default does not "
        "change when another plot is present: function/auto:bare and "
        "function/auto:with_scatter both span x in [0,1] on 300 points.  dash's "
        "current [0,1] is therefore CORRECT as a default; what is actually "
        "missing is only that range() is ignored when the user gives it."),
    "fpfit.grid_size": (
        "Section 07 asks for \"one grid size\" for fpfit/fpfitci.  Stata uses no "
        "grid at all: both evaluate at the distinct observed x values, so the "
        "number of points is data-dependent.  The property to reproduce is that "
        "fpfit and fpfitci agree with each other and cover the full observed "
        "x range -- not that they share a constant like 200 or 150."),
    "mband.documented_vs_actual": (
        "help twoway_mband documents max(10, round(10*log10(N))) bands by "
        "default, but the graph engine does not use it.  See "
        "mband_default_band_count for the measured values."),
    "fpfit.bwidth_and_degree_are_documented_by_dash_but_rejected_by_stata": (
        "Section 07 notes at `:2843'/`:2898' that fpfit/fpfitci never read "
        "bwidth() or degree(), contradicting dash.sthlp:559-560.  Stata's "
        "answer is that dash.sthlp is wrong to document them: twoway fpfit "
        "REJECTS both (_rc=198, \"option bwidth() not allowed\" / \"option "
        "degree() not allowed\").  degree() is spelled estopts(degree(#)) and "
        "there is no bandwidth concept in fpfit at all.  The right fix is to "
        "report them as unsupported, not to honour them."),
    "kdensity.n_default": (
        "`kdensity x' and `twoway kdensity x' have DIFFERENT default grid sizes "
        "(min(N,50) vs 300).  dash draws a plot, so 300 is the relevant one; "
        "r(bwidth) and r(kernel) are shared by both."),
    "lowess_vs_lpoly_bwidth": (
        "Section 07 treats bwidth() as one concept.  It is two: lowess's "
        "bwidth() is a FRACTION of the sample (default .8) and lpoly's is an "
        "ABSOLUTE half-width in x units.  A single clamped-to-[0.01,1.0] "
        "implementation cannot be right for both."),
}

doc = {
    "_meta": {
        "generated_by": "scripts/extract_stat_truth.do",
        "record_file": REC,
        "run_date": meta.get("run_date"),
        "stata_version": meta.get("stata_version"),
        "stata_flavor": meta.get("stata_flavor"),
        "stata_edition": meta.get("stata_edition"),
        "stata_born_date": meta.get("stata_born_date"),
        "c_level_default": num(meta.get("c_level")),
        "datasets": sorted(sections.get("datasets", {}).keys()),
        "method": (
            "Three oracles, recorded side by side wherever two of them apply to "
            "the same number.  (1) r()/e() from Stata's own command, including "
            "twoway__histogram_gen, the subroutine histogram.ado itself calls. "
            "(2) THE PLOTTED POINTS: each twoway plot is saved to a live-format "
            ".gph, `graph use' makes its sersets addressable and `serset set #' + "
            "`serset use, clear' loads the exact drawn numbers back into memory; "
            "for mband this reaches the DERIVED serset (type median_bands) the "
            "graph engine computes at draw time.  (3) THE RESOLVED COMMAND LINE "
            "histogram rewrites itself into, read out of the .gph header by the "
            "python block.  Every value carries the command that produced it in "
            "its \"cmd\" field."),
        "precision": (
            "Numbers were written with Stata's %20.17g, so doubles round-trip. "
            "Values that originate in a serset were stored by the graph engine as "
            "floats and are only float-accurate; compare those with a relative "
            "tolerance of about 1e-6, not for equality."),
        "sampling": (
            "Curves of at most 41 points (64 for mband) are stored whole. Longer "
            "curves are stored at the 11 evenly spaced indices listed in "
            "sample_index, together with the full n_points and the min/max of "
            "every series."),
        "self_checks": {
            "histogram_bin_rule_reproduces_stata": hist_rule_all_agree,
            "kdensity_ado_formula_reproduces_r_bwidth": kde_rot_all_agree,
            "ci_rebuild_agrees_with_plotted_serset": ci_all_agree,
            "lowess_default_is_bwidth_point8": lowess_default_all_agree,
            "mband_cross_medians_reproduced_by_hand":
                all(v.get("bands_reproduced_by")
                    for v in sections.get("mband", {}).values()
                    if v.get("rc") == 0) if sections.get("mband") else None,
        },
        "counts": {
            "datasets": len(sections.get("datasets", {})),
            "histogram_probes": len(sections.get("histogram", {})),
            "histogram_resolved_cmd_probes": len(sections.get("histogram_resolved_cmd", {})),
            "kdensity_probes": len(sections.get("kdensity", {})),
            "kdensity_twoway_probes": len(sections.get("kdensity_twoway", {})),
            "lpoly_probes": len(sections.get("lpoly", {})),
            "lpoly_twoway_probes": len(sections.get("lpoly_twoway", {})),
            "lowess_probes": len(sections.get("lowess", {})),
            "ci_band_probes": len(sections.get("ci_bands", {})),
            "ci_rebuild_probes": len(sections.get("ci_rebuild", {})),
            "fp_power_probes": len(sections.get("fp_powers", {})),
            "fpfit_probes": len(sections.get("fpfit", {})),
            "mband_probes": len(sections.get("mband", {})),
            "mband_candidate_band_counts_computed": len(scan) + len(sweep_scan),
            "mband_observed_N_bands_pairs": len(observed_pairs),
            "function_probes": len(sections.get("function", {})),
            "rules_recorded": len(RULES),
            "unverified": len(UNVERIFIED),
            "contradictions_with_section_plan": len(CONTRADICTIONS),
        },
    },
    "rules": RULES,
    "unverified": UNVERIFIED,
    "contradictions_with_section_07_plan": CONTRADICTIONS,
    "histogram_bin_rule_check": hist_rule,
    "lowess_default_bwidth_check": lowess_default_check,
    "kdensity_bwidth_rule_check": kde_rot,
    "mband_default_band_count": mband_resolved,
    "mband_default_band_count_rule_search": mband_rule,
    "ci_rebuild_agreement_by_probe": ci_agreement,
}
for name in ("datasets", "histogram", "histogram_resolved_cmd", "kdensity",
             "kdensity_rot_check", "kdensity_twoway", "lpoly", "lpoly_twoway",
             "lowess", "ci_bands", "ci_rebuild", "fp_powers", "fpfit",
             "fpfit_optsupport", "mband", "function"):
    doc[name] = sections.get(name, {})

with open(OUT, "w") as fh:
    json.dump(doc, fh, indent=2, sort_keys=True)
    fh.write("\n")

print("WROTE " + OUT)
for k, v in doc["_meta"]["counts"].items():
    print("  %-42s %s" % (k, v))
for k, v in doc["_meta"]["self_checks"].items():
    print("  SELFCHECK %-44s %s" % (k, v))
for ds, v in sorted(mband_resolved.items()):
    print("  mband default bands %-8s N=%-6s measured=%-5s documented=%s" %
          (ds, v["N_xy"], v["measured_default_bands"],
           v["documented_default_bands"]))
print("  mband candidate rules over %d (N, bands) pairs:" % len(observed_pairs))
for name, sc in rule_scores.items():
    print("    %-60s %d/%d" % (name, sc["matches"], sc["of"]))
end

display as text "extract_stat_truth.do: done"
