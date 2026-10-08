*! extract_ts_operator_truth.do
*! WP-30 section 42 (P1.7): ground truth for time-series operators in plot
*! varlists, for test/fixtures/ts_operator_truth.json.
*!
*! WHY THIS EXISTS
*!
*! dash refused L.close, D.close and L(1/2).close in every plot varlist,
*! r(101), where twoway draws them on 29 types.  This script asks twoway
*! (StataNow 19.5, scheme stcolor) each probe and records its return code,
*! its error lines, its axis objects' titles, the keys its SVG draws (the
*! bare SVG's texts minus its legend(off) twin's), and the values and
*! storage types of every serset it draws.  For the probes the renderer
*! tests read (flag X) it also records the spec and data file dash writes
*! for the same command (_dash_prepare_spec), so the pytest suite draws
*! exactly what dash exports.
*!
*! Output: test/fixtures/ts_operator_truth.json
*!
*! Run with (the script sets its own directories, so it is handed to the
*! wrapper directly -- CLAUDE.md rule 10):
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_ts_operator_truth.do
*!
*! Never calls back into Stata from the trailing python: block; a backtick
*! inside it is spelled \x60.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off
set linesize 255

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_ts_operator_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_ts_operator_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1
global ZT_REPO "`repo'"
global ZT_OUT  "`repo'/test/fixtures/ts_operator_truth.json"
// dash's own programs, for _dash_prepare_spec (as the cscripts load them).
quietly do "`repo'/dash_parse.mata"
quietly do "`repo'/dash.ado"

local work "`c(tmpdir)'dash_ts_operator_probe"
capture mkdir "`work'"
global ZT_WORK "`work'"
display as text "probe work dir: ${ZT_WORK}"

set scheme stcolor

global ZT_SVER = c(stata_version)
global ZT_BORN = c(born_date)
global ZT_DATE = "`c(current_date)' `c(current_time)'"

// Provenance stamp (D12): shell writes the commit into a file, read back.
tempfile ztgitrev
quietly shell git -C "${ZT_REPO}" rev-parse HEAD > "`ztgitrev'"
tempname ztgfh
file open `ztgfh' using "`ztgitrev'", read text
file read `ztgfh' ztgitline
file close `ztgfh'
global ZT_COMMIT = trim(`"`ztgitline'"')
capture assert ustrregexm(`"${ZT_COMMIT}"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_ts_operator_truth.do: git rev-parse HEAD did not print a 40-character commit"
    exit 498
}

// ---------------------------------------------------------------------------
// The data sets
//   sp   sp500, t = _n, tsset t; y2 unlabelled, c80 an 80-character label,
//        cb a label of blanks, xf a float, volume %12.0fc, g two groups
//   spd  sp, tsset date (the trading days' gaps)
//   us   sp, then sorted by close (not by the time variable)
//   nt   sp500 with t and no tsset
//   xt   2 panels x 10 periods, xtset id tt
//   au   auto, t = _n, tsset t
// ---------------------------------------------------------------------------
capture program drop _zt_data
program define _zt_data
    args ds
    if inlist("`ds'", "sp", "spd", "us", "nt") {
        sysuse sp500, clear
        quietly {
            gen t = _n
            format volume %12.0fc
            gen y2 = close
            gen c80 = close
            label variable c80 "Closing price of the Standard and Poors 500 index on each trading day of 2001 US"
            gen cb = close
            label variable cb "   "
            gen float xf = close / 7
            gen g = t > 124
        }
        if "`ds'" == "sp"  quietly tsset t
        if "`ds'" == "spd" quietly tsset date
        if "`ds'" == "us" {
            quietly tsset t
            sort close
        }
    }
    else if "`ds'" == "xt" {
        clear
        quietly {
            set obs 20
            gen id = ceil(_n / 10)
            gen tt = mod(_n - 1, 10) + 1
            gen y = _n * _n
            label variable y "Y value"
            xtset id tt
        }
    }
    else if "`ds'" == "au" {
        sysuse auto, clear
        quietly gen t = _n
        quietly tsset t
    }
end

// ---------------------------------------------------------------------------
// Registration: id, data set, body, options, flags (S: the SVG's keys; X:
// the serset values and dash's export)
// ---------------------------------------------------------------------------
global ZT_N = 0
capture program drop zt
program define zt
    global ZT_N = ${ZT_N} + 1
    global ZT_ID_${ZT_N}   `"`1'"'
    global ZT_DS_${ZT_N}   `"`2'"'
    global ZT_BODY_${ZT_N} `"`3'"'
    global ZT_OPTS_${ZT_N} `"`4'"'
    global ZT_FL_${ZT_N}   `"`5'"'
end

// Accepted types (E2)
local i 0
foreach p in scatter line connected area bar spike dropline dot lfit qfit lfitci qfitci mspline mband {
    local ++i
    zt A`=string(`i', "%02.0f")' sp "`p' D.close L.close" "" ""
}
foreach p in rarea rbar rspike rcap rline rconnected rcapsym rscatter {
    local ++i
    zt A`=string(`i', "%02.0f")' sp "`p' L.low L.high t" "" ""
}
foreach p in pcspike pcarrow pcbarrow pcscatter pccapsym {
    local ++i
    zt A`=string(`i', "%02.0f")' sp "`p' L.close L.t close t" "" ""
}
zt A28 sp "tsline D.close" "" ""
zt A29 sp "tsrline L.low L.high" "" ""
// Refused types
local i 0
foreach p in fpfit fpfitci lowess lpoly lpolyci {
    local ++i
    zt R0`i' sp "`p' D.close t" "" ""
}
zt R06 sp "histogram D.close" "" ""
zt R07 sp "kdensity D.close" "" ""
// Text (E6)
zt T01 spd "line D.close date" "" "SX"
zt T02 sp "line close L.close t" "" "SX"
zt T03 sp "scatter L(1/2).close t" "" "SX"
zt T04 sp "tsline D.close" "" "SX"
zt T05 sp "line D.y2 t" "" "SX"
zt T06 sp "line l.close L1.close DL.close D2.close L0.close t" "" "SX"
zt T07 sp "line S1.close F2.close L2D.close d.l.close t" "" "SX"
zt T08 sp "line L.c80 t" "" "SX"
zt T09 sp "line L.cb t" "" "SX"
// Values (E3)
zt V01 sp "scatter D.close t if t>5 & t<9" "" "X"
zt V02 sp "lfit close L.close if t>100" "" "X"
zt V03 xt "scatter L.y tt" "" "X"
zt V04 spd "scatter D.close date" "" "X"
zt V05 sp "rarea L.low L.high t" "" "X"
zt V06 sp "pcspike L.close L.t close t" "" "X"
// Formats, value labels and storage types (E3)
zt F01 sp "scatter L.volume t" "" "X"
zt F02 sp "scatter close D.date" "" "X"
zt F03 sp "scatter L.date t" "" "X"
zt F04 au "scatter L.foreign t" "ylabel(, valuelabel)" "SX"
zt G01 sp "scatter D.xf t" "" "X"
zt G02 au "scatter L.mpg t" "" "X"
zt G03 au "scatter D.price t" "" "X"
// Refusals (E2, E4)
zt E01 nt "line L.close t" "" ""
zt E02 au "scatter L.make mpg" "" ""
zt E03 au "scatter i.foreign mpg" "" ""
zt E04 au "scatter X.mpg t" "" ""
zt E05 au "scatter L.nosuch t" "" ""
zt E06 us "scatter L.close t" "" ""
// by() with an operated plot variable (E4)
zt B01 sp "scatter D.close t" "by(g)" ""
zt B02 sp "tsline D.close" "by(g)" ""
zt B03 sp "(scatter close t) (line D.close t)" "by(g)" ""
zt B04 sp "tsline close" "by(g)" ""
zt B05 xt "scatter L.y tt" "by(id)" ""
// A bare sort with an operated x (E4), and with an operated y
local i 0
foreach p in scatter line connected area bar spike dropline dot lfit qfit lfitci qfitci mspline mband {
    local ++i
    zt O`=string(`i', "%02.0f")' sp "`p' close L.t" "sort" ""
}
foreach p in rarea rbar rspike rcap rline rconnected rcapsym rscatter {
    local ++i
    zt O`=string(`i', "%02.0f")' sp "`p' low high L.t" "sort" ""
}
foreach p in pcspike pcarrow pcbarrow pcscatter pccapsym {
    local ++i
    zt O`=string(`i', "%02.0f")' sp "`p' close L.t close t" "sort" ""
}
zt O28 sp "tsline D.close" "sort" ""
zt O29 sp "tsrline L.low L.high" "sort" ""
zt Y01 sp "line D.close t" "sort" ""

// ---------------------------------------------------------------------------
// Mata writers
// ---------------------------------------------------------------------------
mata:
void _zt_put(string scalar file, string scalar text)
{
    real scalar fh
    if (fileexists(file)) unlink(file)
    fh = fopen(file, "w")
    fput(fh, text)
    fclose(fh)
}

// The data in memory (a serset) as JSON: a list of {"name", "type",
// "format", "values"}, a missing value as null.
string scalar _zt_dump()
{
    real scalar      j
    real colvector   x
    string colvector s
    string scalar    out, q

    q   = char(34)
    out = ""
    for (j = 1; j <= st_nvar(); j++) {
        if (st_isstrvar(j)) continue
        x = st_data(., j)
        s = strofreal(x, "%21.17g")
        if (rows(x)) s[selectindex(x :>= .)] = J(sum(x :>= .), 1, "null")
        out = out + (out != "" ? "," : "") + "{" + q + "name" + q + ":" + q +
              st_varname(j) + q + "," + q + "type" + q + ":" + q +
              st_vartype(j) + q + "," + q + "format" + q + ":" + q +
              st_varformat(j) + q + "," + q + "values" + q + ":[" +
              (rows(s) ? invtokens(strtrim(s'), ",") : "") + "]}"
    }
    return("[" + out + "]")
}
end

// ---------------------------------------------------------------------------
// The probes
// ---------------------------------------------------------------------------
local N = ${ZT_N}
forvalues i = 1/`N' {
    local id   "${ZT_ID_`i'}"
    local ds   "${ZT_DS_`i'}"
    local body `"${ZT_BODY_`i'}"'
    local opts `"${ZT_OPTS_`i'}"'
    local fl   "${ZT_FL_`i'}"
    _zt_data `ds'

    // 1. twoway: its rc and error lines, its axis objects' titles
    capture graph drop Graph
    serset clear
    capture log close ztl
    quietly log using "${ZT_WORK}/`id'_tw.log", text replace name(ztl)
    capture noisily twoway `body', `opts' name(Graph, replace)
    local rc = _rc
    quietly log close ztl
    local y1 ""
    local x1 ""
    if `rc' == 0 {
        capture local y1 `"`.Graph.yaxis1.title.text[1]'"'
        capture local x1 `"`.Graph.xaxis1.title.text[1]'"'
        if strpos("`fl'", "S") {
            capture graph export "${ZT_WORK}/`id'_tw.svg", name(Graph) replace
            capture graph drop Graph
            capture noisily twoway `body', `opts' legend(off) name(Graph, replace)
            if _rc == 0 capture graph export "${ZT_WORK}/`id'_off.svg", name(Graph) replace
        }
        if strpos("`fl'", "X") {
            forvalues s = 0/9 {
                capture erase "${ZT_WORK}/`id'_ser`s'.txt"
                capture serset set `s'
                if _rc continue
                preserve
                capture serset use, clear
                if _rc == 0 {
                    mata: _zt_put(st_global("ZT_WORK") + "/" + st_local("id") + "_ser" + st_local("s") + ".txt", _zt_dump())
                }
                restore
            }
        }
    }
    capture graph drop Graph
    mata: _zt_put(st_global("ZT_WORK") + "/" + st_local("id") + "_twrc.txt", st_local("rc"))
    mata: _zt_put(st_global("ZT_WORK") + "/" + st_local("id") + "_y1.txt", st_local("y1"))
    mata: _zt_put(st_global("ZT_WORK") + "/" + st_local("id") + "_x1.txt", st_local("x1"))

    // 2. dash's export of the same command (X probes that twoway draws)
    local drc ""
    if `rc' == 0 & strpos("`fl'", "X") {
        _zt_data `ds'
        capture dash clear
        local dopts `"`opts' name(zt`i')"'
        capture noisily dash `body', `dopts'
        local drc = _rc
        if `drc' == 0 {
            capture erase "${ZT_WORK}/`id'_spec.json"
            capture erase "${ZT_WORK}/`id'_data.json"
            capture noisily _dash_prepare_spec, specpath("${ZT_WORK}/`id'_spec.json") datapath("${ZT_WORK}/`id'_data.json")
            local drc = _rc
        }
        capture dash clear
    }
    mata: _zt_put(st_global("ZT_WORK") + "/" + st_local("id") + "_dashrc.txt", st_local("drc"))
    display as text "probe `id' twoway rc=`rc' dash rc=`drc'"
}

// The probe table, for the reader.
tempname tfh
file open `tfh' using "${ZT_WORK}/probes.txt", write text replace
file close `tfh'
forvalues i = 1/`N' {
    mata: _ztfh = fopen(st_global("ZT_WORK") + "/probes.txt", "a"); fput(_ztfh, st_global("ZT_ID_" + st_local("i")) + char(9) + st_global("ZT_DS_" + st_local("i")) + char(9) + st_global("ZT_BODY_" + st_local("i")) + char(9) + st_global("ZT_OPTS_" + st_local("i")) + char(9) + st_global("ZT_FL_" + st_local("i"))); fclose(_ztfh)
}

// ===========================================================================
// Analysis + JSON emission.  No callbacks into Stata from here on.
// REMINDER: no backtick may appear literally in this block.
// ===========================================================================
python:
import collections
import json
import os
import re
import sys
from sfi import Macro

ZT_REPO = Macro.getGlobal("ZT_REPO")
sys.path.insert(0, os.path.join(ZT_REPO, "scripts"))
import svg_truth

W = Macro.getGlobal("ZT_WORK")
OUT = Macro.getGlobal("ZT_OUT")


def _read(name):
    p = os.path.join(W, name)
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as fh:
        return fh.read().rstrip("\n")


def _texts(path):
    if not os.path.exists(path):
        return []
    doc = svg_truth.svg_document(path)
    return [e for e in doc["texts"]
            if svg_truth.label_value(e["text"]) is None
            and e["text"].strip() != ""]


def _keys(bare, off):
    cnt = collections.Counter(e["text"] for e in bare)
    cnt.subtract(collections.Counter(e["text"] for e in off))
    seen, out = collections.Counter(), []
    for e in sorted(bare, key=lambda e: (float(e.get("y") or 0.0),
                                         float(e.get("x") or 0.0))):
        t = e["text"]
        if seen[t] < cnt.get(t, 0):
            seen[t] += 1
            out.append(t)
    return out


def _err(text):
    """The lines twoway printed: no command echo, no blank line."""
    out = []
    for line in text.splitlines():
        s = line.rstrip()
        if not s.strip() or s.startswith(". ") or s.startswith("> "):
            continue
        out.append(s.strip())
    return out


def _num(s):
    """Stata's %21.17g writes .5 and -.5; JSON needs 0.5 and -0.5."""
    return re.sub(r"(?<=[\[,])(-?)\.(?=[0-9])", r"\g<1>0.", s)


def _json_file(name):
    s = _read(name)
    return json.loads(s) if s.strip() else None


probes = {}
for line in _read("probes.txt").splitlines():
    pid, ds, body, opts, fl = (line.split("\t") + [""] * 5)[:5]
    rc = int(_read(pid + "_twrc.txt") or 0)
    tw = {"rc": rc,
          "err": _err(_read(pid + "_tw.log")) if rc else [],
          "titles": {"y1": _read(pid + "_y1.txt"),
                     "x1": _read(pid + "_x1.txt")}}
    if "S" in fl and rc == 0:
        bare = _texts(os.path.join(W, pid + "_tw.svg"))
        tw["keys"] = _keys(bare, _texts(os.path.join(W, pid + "_off.svg")))
        tw["texts"] = sorted(set(e["text"] for e in bare))
    if "X" in fl and rc == 0:
        tw["sersets"] = [json.loads(_num(_read("%s_ser%d.txt" % (pid, k))))
                         for k in range(10)
                         if _read("%s_ser%d.txt" % (pid, k))]
    rec = {"ds": ds, "body": body, "opts": opts, "flags": fl, "twoway": tw}
    drc = _read(pid + "_dashrc.txt")
    if drc != "":
        rec["dash"] = {"rc": int(drc),
                       "spec": _json_file(pid + "_spec.json"),
                       "data": _json_file(pid + "_data.json")}
    probes[pid] = rec

doc = {
    "_meta": {
        "stata_version": Macro.getGlobal("ZT_SVER"),
        "born_date": Macro.getGlobal("ZT_BORN"),
        "dash_commit": Macro.getGlobal("ZT_COMMIT"),
        "extracted": Macro.getGlobal("ZT_DATE"),
        "scheme": "stcolor",
        "probes": len(probes),
        "method": ("rc and err are twoway's return code and the lines it "
                   "printed; titles are its axis objects "
                   "(.Graph.<axis>.title.text[1]); keys are the bare SVG's "
                   "non-numeric texts minus its legend(off) twin's, by "
                   "multiset, in (y, x) order; texts are every non-numeric "
                   "text the bare SVG draws; sersets are each serset "
                   "twoway drew (serset use), its variables' names, storage "
                   "types, formats and values (null for missing); dash is "
                   "the spec and data file _dash_prepare_spec writes for "
                   "the same command."),
    },
    "probes": probes,
}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, ensure_ascii=False, indent=None, sort_keys=True,
              separators=(",", ":"))
    fh.write("\n")
print("WROTE %s probes=%d" % (OUT, len(probes)))
end

display as text "extract_ts_operator_truth.do: done"
