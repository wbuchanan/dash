*! extract_date_units_truth.do
*! Derive Stata's own numbers for computed layers and KPI statistics of a date
*! variable (WP-29 S05, P0.8 and P0.20), BY PROBING STATA ITSELF on
*! sysuse sp500, so dash can be checked against what twoway computes in the
*! variable's own Stata units (days for %td, ms after 01jan1960 for %tc,
*! weeks/months/quarters/half-years/years for the others).
*!
*! Output: ${repo}/test/fixtures/date_units_truth.json, where repo is read
*! from the environment variable DASH_REPO (refused with exit 198 if empty).
*!
*! Run (Stata only through the slot wrapper, never the GUI):
*!
*!   mkdir -p <scratch>/extract
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch>/extract \
*!       <repo>/scripts/extract_date_units_truth.do
*!
*! ---------------------------------------------------------------------------
*! METHOD
*!
*!  data        sysuse sp500, keep date close; gen m = mofd(date) (%tm),
*!              q = qofd(date) (%tq), w = wofd(date) (%tw),
*!              double tc = cofd(date) + 3600000*mod(_n,24) (%tc),
*!              yr = 1950 + mod(_n,40) (%ty).  Every value at %21.0g.
*!  histogram   twoway__histogram_gen <v> [if], density|frequency
*!              [width() start() bin() discrete] gen(zh zx, replace): r(bin)
*!              r(width) r(start) r(min) r(max) and the (zx, zh) pairs, which
*!              the python block places at bar floor((zx - start)/width) (a
*!              midpoint start+(i+.5)w and a discrete value start+i*w both land
*!              on bar i) to give the full bar array of length r(bin).
*!  kdensity    r(bwidth) of kdensity <v>, nograph; curves from
*!              twoway__kdensity_gen <v> [if], gen(zd zx) n(5) range() [bwidth()].
*!  lpoly       lpoly close <v> [if], nograph gen(zx zs) n(5) bwidth().
*!  fits        fracpoly: regress close date (e(fp_pwrs), predict double at
*!              the first and last date); regress close m; regress date close.
*!  kpi         summarize <v> [if] [in], detail: the value (%21.0g; iqr is
*!              r(p75)-r(p25), cv is r(sd)/r(mean)) and its display text
*!              (strtrim of display %9.0g for sd var iqr cv sum skewness count,
*!              of display <the variable's format> for mean p50 p25 p75 min max).
*!  axis_labels twoway <cmd>, then graph export <case>.svg; the python block
*!              reads every <text> element of the SVG and records whether a
*!              date label (%td ddmonCCYY or %tm CCYYmM) is shown.
*!
*! Structure (as extract_stat_truth.do): Stata appends @@@-separated records
*! to a record file under c(tmpdir); one trailing python: block reads it and
*! the SVGs and writes the JSON.  The python block never calls back into
*! Stata and starts no subprocess.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off
version 19
* Every variable the probes generate (twoway__histogram_gen's, twoway__kdensity_gen's
* and lpoly's gen()) is a double: a float keeps 7 digits, and the heights are
* compared at 1e-9.
set type double

local repo : env DASH_REPO
if `"`repo'"' == "" {
    display as error "extract_date_units_truth.do: set DASH_REPO to the repository root"
    exit 198
}
global ZQ_REPO "`repo'"
global ZQ_OUT  "`repo'/test/fixtures/date_units_truth.json"

local scratch "`c(tmpdir)'/dash_date_units_probe"
capture mkdir "`scratch'"
global ZQ_WORK "`scratch'"
global ZQ_REC  "`scratch'/date_units_records.txt"
display as text "probe scratch dir: ${ZQ_WORK}"

* ===========================================================================
* Record-file helpers (copied from extract_stat_truth.do).
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
    else            local out = trim(string(`z', "%21.0g"))
    file write zqrec "S@@@`sec'@@@`key'@@@`fld'@@@`out'" _n
end

capture program drop zq_a
program define zq_a                      // record a pre-built ;-joined array
    syntax , Sec(string) Key(string) Fld(string) Val(string)
    file write zqrec "A@@@`sec'@@@`key'@@@`fld'@@@`val'" _n
end

capture program drop zq_chunk
program define zq_chunk
    syntax , Sec(string) Key(string) Fld(string) Type(string) First(integer) [ Val(string) ]
    if `first' local tag "`type'"
    else       local tag "`type'+"
    file write zqrec "`tag'@@@`sec'@@@`key'@@@`fld'@@@`val'" _n
end

* Record a numeric variable's non-missing values (in data order, optionally
* restricted by an if condition) as an array, in chunks of 50 values.
capture program drop zq_var
program define zq_var
    syntax varname(numeric) , Sec(string) Key(string) Fld(string) [ Cond(string) ]
    if `"`cond'"' == "" local cond "1"
    tempvar sel
    quietly gen byte `sel' = (`cond')
    local s ""
    local cnt 0
    local first 1
    forvalues i = 1/`=_N' {
        local v = `varlist'[`i']
        if missing(`v') | !`sel'[`i'] continue
        local t = trim(string(`v', "%21.0g"))
        if "`s'" == "" local s "`t'"
        else           local s "`s';`t'"
        local ++cnt
        if `cnt' == 50 {
            zq_chunk, sec(`sec') key(`key') fld(`fld') type(A) first(`first') val(`s')
            local first 0
            local cnt 0
            local s ""
        }
    }
    if `cnt' > 0 | `first' {
        zq_chunk, sec(`sec') key(`key') fld(`fld') type(A) first(`first') val(`s')
    }
end

* ===========================================================================
file open zqrec using "${ZQ_REC}", write text replace

file write zqrec "META@@@stata_version@@@`c(stata_version)'" _n
file write zqrec "META@@@born_date@@@`c(born_date)'" _n
file write zqrec "META@@@extracted@@@`c(current_date)'" _n

* Fixture provenance: the dash commit this fixture was measured against.
tempfile gitrev
quietly shell git -C "${ZQ_REPO}" rev-parse HEAD > "`gitrev'"
file open zqgitfh using "`gitrev'", read text
file read zqgitfh zq_gitline
local dash_commit = trim(`"`zq_gitline'"')
file close zqgitfh
if !ustrregexm("`dash_commit'", "^[0-9a-f]{40}$") {
    display as error "extract_date_units_truth.do: git rev-parse HEAD did not return a 40-character hex commit (got `dash_commit')"
    exit 198
}
file write zqrec "META@@@dash_commit@@@`dash_commit'" _n

* ---------------------------------------------------------------------------
* The data
* ---------------------------------------------------------------------------
capture program drop zq_load
program define zq_load
    sysuse sp500, clear
    keep date close
    gen m = mofd(date)
    format m %tm
    gen q = qofd(date)
    format q %tq
    gen w = wofd(date)
    format w %tw
    gen double tc = cofd(date) + 3600000*mod(_n,24)
    format tc %tc
    gen yr = 1950 + mod(_n,40)
    format yr %ty
end
zq_load

local gens "sysuse sp500, clear; keep date close; gen m = mofd(date); format m %tm; gen q = qofd(date); format q %tq; gen w = wofd(date); format w %tw; gen double tc = cofd(date) + 3600000*mod(_n,24); format tc %tc; gen yr = 1950 + mod(_n,40); format yr %ty"
zq_s, sec(data_meta) key(all) fld(gen_cmds) val(`gens')
foreach v in date close m q w tc yr {
    zq_var `v', sec(data) key(columns) fld(`v')
    local f : format `v'
    zq_s, sec(data_meta) key(formats) fld(`v') val(`f')
}

* ---------------------------------------------------------------------------
* histogram: twoway__histogram_gen
* ---------------------------------------------------------------------------
capture program drop zq_hist
program define zq_hist
    syntax , Key(string) Var(string) [ Opts(string) Cond(string) ]
    if `"`cond'"' == "" local ifc ""
    else                local ifc "if `cond'"
    local cmd "twoway__histogram_gen `var' `ifc', `opts' gen(zh zx, replace)"
    capture drop zh zx
    `cmd'
    zq_s, sec(histogram) key(`key') fld(cmd) val(`cmd')
    foreach r in bin width start min max {
        zq_n, sec(histogram) key(`key') fld(`r') val(r(`r'))
    }
    zq_var zx, sec(histogram) key(`key') fld(pair_x) cond(!missing(zh))
    zq_var zh, sec(histogram) key(`key') fld(pair_h) cond(!missing(zx))
    capture drop zh zx
end

zq_hist, key(td:default)            var(date) opts(density)
zq_hist, key(td:w30s14975)          var(date) opts(density width(30) start(14975))
zq_hist, key(td:bin10)              var(date) opts(density bin(10))
zq_hist, key(td:discrete)           var(date) opts(density discrete)
zq_hist, key(td:frequency)          var(date) opts(frequency)
zq_hist, key(tm:default)            var(m)    opts(density)
zq_hist, key(tm:w2s492)             var(m)    opts(density width(2) start(492))
zq_hist, key(tc:default)            var(tc)   opts(density)
zq_hist, key(tc:w7d)                var(tc)   opts(density start(1294012800000) width(604800000))
zq_hist, key(tw:default)            var(w)    opts(density)
zq_hist, key(ty:default)            var(yr)   opts(density)
zq_hist, key(td:default:if)         var(date) opts(density) cond(close>=1200)
zq_hist, key(td:w30s14975:if)       var(date) opts(density width(30) start(14975)) cond(close>=1200)
zq_hist, key(td:default:fixedgrid:if) var(date) opts(density start(14977) width(24.2)) cond(close>=1200)

* ---------------------------------------------------------------------------
* kdensity: r(bwidth) and twoway__kdensity_gen curves
* ---------------------------------------------------------------------------
foreach p in td:date tm:m tq:q tc:tc ty:yr {
    gettoken k v : p, parse(":")
    local v = substr("`v'", 2, .)
    local cmd "kdensity `v', nograph"
    quietly `cmd'
    zq_s, sec(kdensity) key(bw:`k') fld(cmd) val(`cmd')
    zq_n, sec(kdensity) key(bw:`k') fld(bwidth) val(r(bwidth))
}

capture program drop zq_kd
program define zq_kd
    syntax , Key(string) Var(string) Opts(string) [ Cond(string) ]
    if `"`cond'"' == "" local ifc ""
    else                local ifc "if `cond'"
    capture drop zd zx
    local cmd "twoway__kdensity_gen `var' `ifc', gen(zd zx) `opts'"
    `cmd'
    zq_s, sec(kdensity) key(`key') fld(cmd) val(`cmd')
    zq_var zx, sec(kdensity) key(`key') fld(x) cond(!missing(zx))
    zq_var zd, sec(kdensity) key(`key') fld(y) cond(!missing(zx))
    capture drop zd zx
end
zq_kd, key(td:range:default)    var(date) opts(n(5) range(14900 15400))
zq_kd, key(td:range:bw10)       var(date) opts(n(5) range(14900 15400) bwidth(10))
zq_kd, key(tm:range:bw1)        var(m)    opts(n(5) bwidth(1) range(490 505))
zq_kd, key(td:range:default:if) var(date) opts(n(5) range(14900 15400)) cond(close>=1200)
zq_kd, key(td:range:bw10:if)    var(date) opts(n(5) range(14900 15400) bwidth(10)) cond(close>=1200)

* ---------------------------------------------------------------------------
* lpoly with an explicit bandwidth
* ---------------------------------------------------------------------------
capture program drop zq_lp
program define zq_lp
    syntax , Key(string) Var(string) Bw(string) [ Cond(string) ]
    if `"`cond'"' == "" local ifc ""
    else                local ifc "if `cond'"
    capture drop zx zs
    local cmd "lpoly close `var' `ifc', nograph gen(zx zs) n(5) bwidth(`bw')"
    quietly `cmd'
    zq_s, sec(lpoly) key(`key') fld(cmd) val(`cmd')
    zq_n, sec(lpoly) key(`key') fld(bwidth) val(r(bwidth))
    zq_var zx, sec(lpoly) key(`key') fld(x) cond(!missing(zx))
    zq_var zs, sec(lpoly) key(`key') fld(y) cond(!missing(zx))
    capture drop zx zs
end
zq_lp, key(td:bw30)    var(date) bw(30)
zq_lp, key(tm:bw2)     var(m)    bw(2)
zq_lp, key(tc:bw30d)   var(tc)   bw(2592000000)
zq_lp, key(td:bw30:if) var(date) bw(30) cond(close>=1200)

* ---------------------------------------------------------------------------
* fits
* ---------------------------------------------------------------------------
preserve
sort date
local cmd "fracpoly: regress close date"
quietly `cmd'
local pw "`e(fp_pwrs)'"
capture drop zfp
quietly predict double zfp
zq_s, sec(fits) key(fp:td) fld(cmd) val(`cmd'; predict double)
zq_s, sec(fits) key(fp:td) fld(pwrs) val(`pw')
local x1 = trim(string(date[1], "%21.0g"))
local xN = trim(string(date[_N], "%21.0g"))
local y1 = trim(string(zfp[1], "%21.0g"))
local yN = trim(string(zfp[_N], "%21.0g"))
zq_a, sec(fits) key(fp:td) fld(x) val(`x1';`xN')
zq_a, sec(fits) key(fp:td) fld(y) val(`y1';`yN')
restore

local cmd "regress close m"
quietly `cmd'
zq_s, sec(fits) key(lfit:tm) fld(cmd) val(`cmd')
zq_n, sec(fits) key(lfit:tm) fld(b) val(_b[m])
zq_n, sec(fits) key(lfit:tm) fld(cons) val(_b[_cons])
local y1 = trim(string(_b[m]*492 + _b[_cons], "%21.0g"))
local y2 = trim(string(_b[m]*503 + _b[_cons], "%21.0g"))
zq_a, sec(fits) key(lfit:tm) fld(x) val(492;503)
zq_a, sec(fits) key(lfit:tm) fld(y) val(`y1';`y2')

local cmd "regress date close"
quietly `cmd'
zq_s, sec(fits) key(lfit:ydate) fld(cmd) val(`cmd')
zq_n, sec(fits) key(lfit:ydate) fld(b) val(_b[close])
zq_n, sec(fits) key(lfit:ydate) fld(cons) val(_b[_cons])
quietly summarize close
local c1 = r(min)
local c2 = r(max)
local x1 = trim(string(`c1', "%21.0g"))
local x2 = trim(string(`c2', "%21.0g"))
local y1 = trim(string(_b[close]*`c1' + _b[_cons], "%21.0g"))
local y2 = trim(string(_b[close]*`c2' + _b[_cons], "%21.0g"))
zq_a, sec(fits) key(lfit:ydate) fld(x) val(`x1';`x2')
zq_a, sec(fits) key(lfit:ydate) fld(y) val(`y1';`y2')

* ---------------------------------------------------------------------------
* kpi: summarize, detail
* ---------------------------------------------------------------------------
capture program drop zq_kpi
program define zq_kpi
    syntax , Scope(string) Vars(string) [ Restr(string) ]
    foreach v of local vars {
        quietly summarize `v' `restr', detail
        local f : format `v'
        local val_sd       = r(sd)
        local val_var      = r(Var)
        local val_iqr      = r(p75) - r(p25)
        local val_cv       = r(sd)/r(mean)
        local val_sum      = r(sum)
        local val_skewness = r(skewness)
        local val_mean     = r(mean)
        local val_p50      = r(p50)
        local val_p25      = r(p25)
        local val_p75      = r(p75)
        local val_min      = r(min)
        local val_max      = r(max)
        local val_count    = r(N)
        foreach s in sd var iqr cv sum skewness mean p50 p25 p75 min max count {
            local key "`scope'|`v'|`s'"
            zq_s, sec(kpi) key(`key') fld(cmd) val(summarize `v' `restr', detail)
            zq_n, sec(kpi) key(`key') fld(value) val(`val_`s'')
            if inlist("`s'", "mean", "p50", "p25", "p75", "min", "max") {
                local d : display `f' `val_`s''
            }
            else {
                local d : display %9.0g `val_`s''
            }
            local d = strtrim(`"`d'"')
            zq_s, sec(kpi) key(`key') fld(display) val(`d')
        }
    }
end
zq_kpi, scope(all)           vars(date m q w tc yr)
zq_kpi, scope(if close>=1200) vars(date m q w tc yr) restr(if close>=1200)
zq_kpi, scope(in 1/50)       vars(date m q w tc yr) restr(in 1/50)

preserve
clear
set obs 2
gen m = 492 + 2*(_n-1)
format m %tm
zq_kpi, scope(tm2) vars(m)
restore

* ---------------------------------------------------------------------------
* axis_labels: twoway's tick texts, read from an exported SVG
* ---------------------------------------------------------------------------
capture program drop zq_ax
program define zq_ax
    syntax , Key(string) Axis(string) Cmd(string asis)
    local c `cmd'
    twoway `c', name(zqg, replace)
    graph export "${ZQ_WORK}/`key'.svg", replace name(zqg)
    zq_s, sec(axis_labels) key(`key') fld(cmd) val(twoway `c')
    zq_s, sec(axis_labels) key(`key') fld(date_axis) val(`axis')
    zq_s, sec(axis_labels) key(`key') fld(svg) val(${ZQ_WORK}/`key'.svg)
    graph drop zqg
end
zq_ax, key(hist_td)      axis(x) cmd(histogram date)
zq_ax, key(kd_td)        axis(x) cmd(kdensity date)
zq_ax, key(lfit_td)      axis(x) cmd(lfit close date)
zq_ax, key(qfit_td)      axis(x) cmd(qfit close date)
zq_ax, key(lfitci_td)    axis(x) cmd(lfitci close date)
zq_ax, key(qfitci_td)    axis(x) cmd(qfitci close date)
zq_ax, key(lpoly_td)     axis(x) cmd(lpoly close date)
zq_ax, key(lpolyci_td)   axis(x) cmd(lpolyci close date)
zq_ax, key(lowess_td)    axis(x) cmd(lowess close date)
zq_ax, key(mspline_td)   axis(x) cmd(mspline close date)
zq_ax, key(mband_td)     axis(x) cmd(mband close date)
zq_ax, key(fpfit_td)     axis(x) cmd(fpfit close date)
zq_ax, key(fpfitci_td)   axis(x) cmd(fpfitci close date)
zq_ax, key(kd_then_hist) axis(x) cmd((kdensity date) (histogram date))
zq_ax, key(hist_then_kd) axis(x) cmd((histogram date) (kdensity date))
zq_ax, key(lfit_then_scatter) axis(x) cmd((lfit close date) (scatter close date))
zq_ax, key(scatter_then_lfit) axis(x) cmd((scatter close date) (lfit close date))
zq_ax, key(lfit_then_lowess)  axis(x) cmd((lfit close date) (lowess close date))
zq_ax, key(kd_tm)        axis(x) cmd(kdensity m)
zq_ax, key(hist_tm)      axis(x) cmd(histogram m)
zq_ax, key(lfit_ydate)   axis(y) cmd(lfit date close)
zq_ax, key(scatter_then_lfit_ydate) axis(y) cmd((scatter date close) (lfit date close))

file close zqrec

* ===========================================================================
* Assemble the JSON.  No backtick, no dollar sign and no call back into Stata.
* ===========================================================================
python:
import json, math, os, re, collections, html
from sfi import Macro

REC = Macro.getGlobal("ZQ_REC")
OUT = Macro.getGlobal("ZQ_OUT")

meta = {}
sec = collections.defaultdict(lambda: collections.defaultdict(dict))


def num(tok):
    if tok is None or tok in ("null", "", "."):
        return None
    try:
        return float(tok)
    except ValueError:
        return tok


with open(REC, "r", errors="replace") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line:
            continue
        f = line.split("@@@")
        tag = f[0]
        if tag == "META" and len(f) >= 3:
            meta[f[1]] = "@@@".join(f[2:])
        elif tag in ("S",) and len(f) >= 5:
            sec[f[1]][f[2]][f[3]] = "@@@".join(f[4:])
        elif tag == "A" and len(f) >= 5:
            raw = "@@@".join(f[4:])
            sec[f[1]][f[2]][f[3]] = [num(t) for t in raw.split(";")] if raw else []
        elif tag == "A+" and len(f) >= 5:
            raw = "@@@".join(f[4:])
            sec[f[1]][f[2]][f[3]].extend([num(t) for t in raw.split(";")] if raw else [])

NUMERIC = {"bin", "width", "start", "min", "max", "bwidth", "b", "cons", "value"}
for s in sec.values():
    for ent in s.values():
        for k, v in list(ent.items()):
            if k in NUMERIC and isinstance(v, str):
                ent[k] = num(v)

out = {}

# data
cols = dict(sec["data"]["columns"])
out["data"] = dict(cols)
out["data"]["formats"] = dict(sec["data_meta"]["formats"])
out["data"]["gen_cmds"] = sec["data_meta"]["all"]["gen_cmds"]

# histogram: full bar arrays
hist = {}
for key, ent in sec["histogram"].items():
    nb = int(ent["bin"])
    start, width = ent["start"], ent["width"]
    heights = [0.0] * nb
    for x, h in zip(ent.get("pair_x", []), ent.get("pair_h", [])):
        if x is None or h is None:
            continue
        i = int(math.floor((x - start) / width + 1e-7))
        if i < 0 or i >= nb:
            raise SystemExit("histogram " + key + ": pair at x=" + repr(x) + " lies off the grid")
        heights[i] = h
    hist[key] = {"cmd": ent["cmd"], "bin": nb, "width": width, "start": start,
                 "min": ent["min"], "max": ent["max"], "heights": heights}
out["histogram"] = hist

out["kdensity"] = {k: dict(v) for k, v in sec["kdensity"].items()}
out["lpoly"] = {k: dict(v) for k, v in sec["lpoly"].items()}
out["fits"] = {k: dict(v) for k, v in sec["fits"].items()}

# kpi: scope -> var -> stat -> {value, display, cmd}
kpi = collections.defaultdict(lambda: collections.defaultdict(dict))
for key, ent in sec["kpi"].items():
    scope, var, stat = key.split("|")
    kpi[scope][var][stat] = {"cmd": ent["cmd"], "value": ent["value"], "display": ent["display"]}
out["kpi"] = {s: {v: dict(d) for v, d in vs.items()} for s, vs in kpi.items()}

# axis labels
TD = re.compile(r"[0-9]{2}[a-z]{3}[0-9]{4}")
TM = re.compile(r"[0-9]{4}m[0-9]{1,2}")
TEXT = re.compile(r"<text[^>]*>([^<]*)</text>")
ax = {}
for key, ent in sec["axis_labels"].items():
    svg = open(ent["svg"], "r", errors="replace").read()
    texts = [html.unescape(t).strip() for t in TEXT.findall(svg)]
    texts = [t for t in texts if t]
    shown = any(TD.fullmatch(t) or TM.fullmatch(t) for t in texts)
    if not shown and not ("15000" in texts or "490" in texts):
        raise SystemExit("axis_labels " + key + ": neither date labels nor 15000/490 in " + repr(texts))
    ax[key] = {"cmd": ent["cmd"], "date_axis": ent["date_axis"], "texts": texts,
               "dates_shown": bool(shown)}
out["axis_labels"] = ax

out["_meta"] = {
    "generated_by": "scripts/extract_date_units_truth.do",
    "stata_version": meta.get("stata_version"),
    "born_date": meta.get("born_date"),
    "source": "scripts/extract_date_units_truth.do",
    "dash_commit": meta.get("dash_commit"),
    "extracted": meta.get("extracted"),
    "method": ("sysuse sp500 with m q w tc yr generated from date (data.gen_cmds). "
               "histogram: twoway__histogram_gen <v> [if], density|frequency [width() start() bin() discrete] gen(), "
               "bars placed at floor((x - start)/width). kdensity: r(bwidth) of kdensity <v>, nograph, and "
               "twoway__kdensity_gen <v> [if], gen() n(5) range() [bwidth()]. lpoly: lpoly close <v> [if], nograph "
               "gen() n(5) bwidth(). fits: fracpoly: regress close date with predict double; regress close m; "
               "regress date close. kpi: summarize <v> [if] [in], detail, value and display text. axis_labels: "
               "twoway <cmd> exported to SVG, tick texts read back."),
    "precision": "%21.0g; histogram heights compared at rel 1e-9",
}

with open(OUT, "w") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote " + OUT)
end
