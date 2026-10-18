*! extract_date_axis_truth.do
*! twoway's own date axes for WP-30 P1.23a (section 35): where literal
*! coordinates, range and paired layers, second axes, mixed date/number axes
*! and an explicit base() on a date axis put their scales and labels,
*! BY PROBING STATA ITSELF on sysuse sp500.
*!
*! Output: ${repo}/test/fixtures/date_axis_truth.json, where repo is read
*! from the environment variable DASH_REPO (refused with exit 198 if empty).
*!
*! Run (Stata only through the slot wrapper, never the GUI):
*!
*!   mkdir -p <scratch>/s35/x
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch>/s35/x \
*!       <repo>/scripts/extract_date_axis_truth.do
*!
*! ---------------------------------------------------------------------------
*! METHOD
*!
*!  data   sysuse sp500; gen obs = _n; gen d2 = date + 30 (%td);
*!         gen int m = mofd(date) (%tm); gen int yr = year(date) (%ty).
*!         set scheme s2color.  Every graph is name(g, replace).
*!  case   twoway <cmd>, then .g.plotregion1.xscale/.yscale curmin and curmax
*!         (and .g.plotregion2's for a second axis: the y2 and x2 scales
*!         live there), and graph export <key>.svg, whose <text> elements
*!         the python block reads back in document order.
*!
*! Each key holds x and y (and x2/y2 where a second axis is drawn) as
*! [curmin, curmax], labels (the SVG texts in document order) and
*! dates_shown (which of the axes x, y, x2, y2 show a ddmonCCYY or CCYYmM
*! label).  twoway only: the fixture is the same before and after the fix.
*! The python block never calls back into Stata and starts no subprocess.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off
version 19

local repo : env DASH_REPO
if `"`repo'"' == "" {
    display as error "extract_date_axis_truth.do: set DASH_REPO to the repository root"
    exit 198
}
global ZA_REPO "`repo'"
global ZA_OUT  "`repo'/test/fixtures/date_axis_truth.json"

* A work directory of this run's own: a tempfile's name plus a suffix.
tempfile zawork
local work "`zawork'_da"
capture mkdir "`work'"
if _rc {
    display as error "extract_date_axis_truth.do: cannot make the work directory `work'"
    exit 9
}
global ZA_WORK "`work'"
global ZA_REC  "`work'/date_axis_records.txt"

capture program drop za_s
program define za_s
    syntax , Sec(string) Key(string) Fld(string) [ Val(string asis) ]
    file write zarec `"S@@@`sec'@@@`key'@@@`fld'@@@`val'"' _n
end

capture program drop za_n
program define za_n
    syntax , Sec(string) Key(string) Fld(string) Val(string)
    local z = `val'
    if missing(`z') local out "null"
    else            local out = trim(string(`z', "%21.0g"))
    file write zarec "S@@@`sec'@@@`key'@@@`fld'@@@`out'" _n
end

* One twoway graph: its scales and its SVG.
capture program drop za_case
program define za_case
    syntax , Sec(string) Key(string) Cmd(string asis) [ Opts(string asis) Y2 X2 ]
    local c `cmd'
    local o `opts'
    twoway `c', `o' name(g, replace)
    za_s, sec(`sec') key(`key') fld(cmd) val(twoway `c', `o')
    za_n, sec(`sec') key(`key') fld(x0) val(`.g.plotregion1.xscale.curmin')
    za_n, sec(`sec') key(`key') fld(x1) val(`.g.plotregion1.xscale.curmax')
    za_n, sec(`sec') key(`key') fld(y0) val(`.g.plotregion1.yscale.curmin')
    za_n, sec(`sec') key(`key') fld(y1) val(`.g.plotregion1.yscale.curmax')
    if "`y2'" != "" {
        za_n, sec(`sec') key(`key') fld(y20) val(`.g.plotregion2.yscale.curmin')
        za_n, sec(`sec') key(`key') fld(y21) val(`.g.plotregion2.yscale.curmax')
    }
    if "`x2'" != "" {
        za_n, sec(`sec') key(`key') fld(x20) val(`.g.plotregion2.xscale.curmin')
        za_n, sec(`sec') key(`key') fld(x21) val(`.g.plotregion2.xscale.curmax')
    }
    graph export "${ZA_WORK}/`sec'_`key'.svg", replace name(g)
    za_s, sec(`sec') key(`key') fld(svg) val(${ZA_WORK}/`sec'_`key'.svg)
    graph drop g
end

file open zarec using "${ZA_REC}", write text replace
file write zarec "META@@@stata_version@@@`c(stata_version)'" _n
file write zarec "META@@@born_date@@@`c(born_date)'" _n
file write zarec "META@@@extracted@@@`c(current_date)'" _n

* Fixture provenance: the dash commit this fixture was measured against.
tempfile gitrev
quietly shell git -C "${ZA_REPO}" rev-parse HEAD > "`gitrev'"
file open zagitfh using "`gitrev'", read text
file read zagitfh za_gitline
local dash_commit = trim(`"`za_gitline'"')
file close zagitfh
if !ustrregexm("`dash_commit'", "^[0-9a-f]{40}$") {
    display as error "extract_date_axis_truth.do: git rev-parse HEAD did not return a 40-character hex commit (got `dash_commit')"
    exit 198
}
file write zarec "META@@@dash_commit@@@`dash_commit'" _n

sysuse sp500, clear
gen obs = _n
gen d2 = date + 30
format d2 %td
gen int m = mofd(date)
format m %tm
gen int yr = year(date)
format yr %ty
set scheme s2color

za_case, sec(literals) key(scatteri_td) cmd((line close date) (scatteri 1300 15400))
za_case, sec(literals) key(pci_td) cmd((line close date) (pci 1200 15400 1400 15450))
za_case, sec(literals) key(pcarrowi_td) cmd((line close date) (pcarrowi 1200 15400 1400 15450))
za_case, sec(literals) key(function_range_td) cmd((line close date) (function y=1300, range(15400 15450)))
za_case, sec(literals) key(function_norange_td) cmd((line close date) (function y=1300))
za_case, sec(literals) key(scatteri_tm) cmd((line close m) (scatteri 1300 504))
za_case, sec(literals) key(scatteri_offrange) cmd((line close date) (scatteri 1300 99999999))
za_case, sec(literals) key(scatteri_ty_negative) cmd((line close yr) (scatteri 1300 -500))
za_case, sec(range) key(rarea_datey) cmd(rarea date d2 close)
za_case, sec(range) key(rcap_datey) cmd(rcap date d2 close)
za_case, sec(pc) key(datey) cmd(pcspike date open d2 close)
za_case, sec(pc) key(datex) cmd(pcspike open date close d2)
za_case, sec(axis2) key(datey_y2num) cmd((scatter date close) (scatter volume close, yaxis(2))) y2
za_case, sec(axis2) key(datex_x2num) cmd((scatter close date) (scatter close obs, xaxis(2))) x2
za_case, sec(axis2) key(y2date) cmd((line close date) (line d2 date, yaxis(2))) y2
za_case, sec(axis2) key(y2date_n5) cmd((line close date) (line d2 date, yaxis(2))) opts(ylabel(#5, axis(2))) y2
za_case, sec(axis2) key(y2date_range) cmd((line close date) (line d2 date, yaxis(2))) opts(yline(15200, axis(2)) yscale(range(14900 15500) axis(2))) y2
za_case, sec(axis2) key(y2_lfit) cmd((line close date) (line d2 date, yaxis(2)) (lfit d2 date, yaxis(2))) y2
za_case, sec(mixed) key(date_first) cmd((scatter close date) (scatter close obs))
za_case, sec(mixed) key(obs_first) cmd((scatter close obs) (scatter close date))
za_case, sec(mixed) key(td_tm) cmd((scatter close date) (scatter close m))
za_case, sec(mixed) key(minmax_date_first) cmd((scatter close date) (scatter close obs)) opts(xlabel(minmax))
za_case, sec(mixed) key(minmax_lfit_first) cmd((lfit close date) (scatter close obs)) opts(xlabel(minmax))
za_case, sec(mixed) key(minmax_obs_first) cmd((scatter close obs) (scatter close date)) opts(xlabel(minmax))
za_case, sec(mixed) key(bar_date_y) cmd((bar date obs in 1/20) (scatter close obs in 1/20))
za_case, sec(base) key(bar_date_base) cmd((bar date obs in 1/20, base(14970)))

file close zarec

* ===========================================================================
* Assemble the JSON.  No backtick, no dollar sign and no call back into Stata.
* ===========================================================================
python:
import json, re, collections, html
from sfi import Macro

REC = Macro.getGlobal("ZA_REC")
OUT = Macro.getGlobal("ZA_OUT")

meta = {}
sec = collections.defaultdict(lambda: collections.defaultdict(dict))
with open(REC, "r", errors="replace") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line:
            continue
        f = line.split("@@@")
        if f[0] == "META" and len(f) >= 3:
            meta[f[1]] = "@@@".join(f[2:])
        elif f[0] == "S" and len(f) >= 5:
            sec[f[1]][f[2]][f[3]] = "@@@".join(f[4:])


def num(tok):
    if tok in (None, "", "null", "."):
        return None
    return float(tok)


TD = re.compile(r"-?[0-9]{2}[a-z]{3}-?[0-9]{1,5}")
TM = re.compile(r"-?[0-9]{1,5}m[0-9]{1,2}")
TEXT = re.compile(r"<text[^>]*>([^<]*)</text>")
out = {}
for s, ents in sec.items():
    out[s] = {}
    for key, ent in ents.items():
        svg = open(ent["svg"], "r", errors="replace").read()
        texts = [html.unescape(t).strip() for t in TEXT.findall(svg)]
        texts = [t for t in texts if t]
        rec = {"cmd": ent["cmd"],
               "x": [num(ent["x0"]), num(ent["x1"])],
               "y": [num(ent["y0"]), num(ent["y1"])],
               "labels": texts,
               "dates_shown": any(TD.fullmatch(t) or TM.fullmatch(t)
                                  for t in texts)}
        if "y20" in ent:
            rec["y2"] = [num(ent["y20"]), num(ent["y21"])]
        if "x20" in ent:
            rec["x2"] = [num(ent["x20"]), num(ent["x21"])]
        out[s][key] = rec

out["_meta"] = {
    "generated_by": "scripts/extract_date_axis_truth.do",
    "stata_version": meta.get("stata_version"),
    "born_date": meta.get("born_date"),
    "source": "scripts/extract_date_axis_truth.do",
    "dash_commit": meta.get("dash_commit"),
    "extracted": meta.get("extracted"),
    "method": ("sysuse sp500; obs = _n, d2 = date + 30 (%td), m = mofd(date) "
               "(%tm), yr = year(date) (%ty); scheme s2color. Per case twoway "
               "<cmd>, name(g): .g.plotregion1.xscale/.yscale curmin/curmax "
               "(plotregion2 for a second axis) and the exported SVG's text "
               "elements in document order."),
}
with open(OUT, "w") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote " + OUT)
end
