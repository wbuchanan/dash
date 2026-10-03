*! extract_lpolyci_truth.do
*! Stata's lpoly confidence band -- the smooth, its standard error, the
*! pilot bandwidth and the band -- and twoway lpolyci's drawn serset,
*! recorded for WP-29 S11 (P0.9) by probing Stata itself.
*!
*! Output: ${W29_REPO}/test/fixtures/lpolyci_truth.json.  W29_REPO is a
*! global set by the two-line driver (refused with exit 198 when empty):
*!
*!   global W29_REPO "<repo>"
*!   do "<repo>/scripts/extract_lpolyci_truth.do"
*!
*! run as <repo>/scripts/stata_slot.sh <scratch> <driver>.do (never the GUI).
*!
*! METHOD
*!  cases   capture lpoly y x [w] if <cond>, ci nograph <options>
*!          generate(gx gy) se(gse) generateci(cl cu): rc, r(bwidth),
*!          r(pwidth), r(N), r(ngrid), the level and
*!          z = invnormal(.5*(1-level/100)+level/100), computed in Stata;
*!          idx, the 0-based observations lpoly used; gx gy gse (double)
*!          and cl cu (float, as lpoly generates them).
*!  serset  twoway lpolyci ..., nodraw saving(), graph use, serset set 0,
*!          serset use: every variable of the drawn serset.
*!  no_df   for every case, the grid indices where the
*!          pilot fit of degree p+2 at r(pwidth) has no residual degrees of
*!          freedom: sum K w - tr[(Z'KwZ)^+ Z'diag(K^2 w)Z] <= 1e-10 sum K w,
*!          computed in the final python block with numpy from the
*!          embedded data -- not by dash.
*!  Numbers are held in Stata scalars and variables at full double
*!  precision and read by the python: blocks only through sfi.
version 19
if "${W29_REPO}" == "" {
    display as error "set global W29_REPO to the repository root"
    exit 198
}
adopath ++ "${W29_REPO}/"
global dash_nobrowser 1
set more off
set graphics off
if "`c(python_exec)'" == "" {
    display as error "python is not available (c(python_exec) is empty)"
    exit 222
}

tempfile LC_GITREV
capture shell cd "${W29_REPO}" && git rev-parse HEAD > "`LC_GITREV'"
local LC_DASH_COMMIT ""
capture confirm file "`LC_GITREV'"
if !_rc {
    file open lcgitrev using "`LC_GITREV'", read text
    file read lcgitrev lcgitline
    local LC_DASH_COMMIT = strtrim(`"`lcgitline'"')
    file close lcgitrev
}
global LC_SVER = c(stata_version)
global LC_BORN = c(born_date)
global LC_DATE = c(current_date)
global LC_COMMIT "`LC_DASH_COMMIT'"

python:
import json, math
from sfi import Data, Macro, Scalar

LC = {"datasets": {}, "cases": [], "serset": []}


def _num(v):
    if v is None:
        return None
    v = float(v)
    if not math.isfinite(v) or v >= 8.988465674311579e+307:
        return None
    return v


def _col(name, obs=None):
    vals = Data.get(name, obs=obs, missingval=None)
    return [_num(v[0] if isinstance(v, list) else v) for v in vals]


def _lc_dataset():
    LC["datasets"][Macro.getLocal("ds")] = {
        c: _col(c) for c in Macro.getLocal("cols").split()}


def _lc_rec():
    g = Macro.getLocal
    n = int(Scalar.getValue("LC_NG"))
    obs = list(range(n))
    rec = {"id": g("cid"), "ds": g("ds"), "y": g("y"), "x": g("x"),
           "w": g("wv"), "wtype": g("wtype"), "cond": g("cond"),
           "options": g("opts"),
           "idx": [int(t) for t in g("idx").split()],
           "rc": int(Scalar.getValue("LC_RC")),
           "bwidth": _num(Scalar.getValue("LC_BW")),
           "pwidth": _num(Scalar.getValue("LC_PW")),
           "N": _num(Scalar.getValue("LC_N")),
           "ngrid": _num(Scalar.getValue("LC_NGRID")),
           "degree": int(g("degree")), "kernel": g("kernel"),
           "level": _num(Scalar.getValue("LC_LEVEL")),
           "z": _num(Scalar.getValue("LC_Z")),
           "var": _num(Scalar.getValue("LC_VAR"))}
    for c in ("gx", "gy", "gse", "cl", "cu"):
        rec[c] = _col("lc" + c, obs) if (n and rec["rc"] == 0) else []
    LC["cases"].append(rec)


def _lc_serset():
    names = [Data.getVarName(i) for i in range(Data.getVarCount())]
    LC["serset"].append({"id": Macro.getLocal("cid"),
                         "count": int(Data.getObsTotal()), "vars": names,
                         "values": {nm: _col(nm) for nm in names}})
end

* lc id ds y x wtype wv cond kernel degree opts   (wtype/wv "." for none)
capture program drop lc
program define lc
    version 19
    args cid ds y x wtype wv cond kernel degree opts
    if "`wtype'" == "." local wtype ""
    if "`wv'" == "." local wv ""
    tempvar touse
    quietly gen byte `touse' = (`cond') & !missing(`y', `x')
    local wexp ""
    if "`wv'" != "" {
        quietly replace `touse' = 0 if missing(`wv') | `wv' <= 0
        local wexp "[`wtype'=`wv']"
    }
    mata: st_local("idx", invtokens(strofreal((selectindex(st_data(., "`touse'")) :- 1)', "%12.0f")))
    foreach v in gx gy gse cl cu {
        capture drop lc`v'
    }
    local lvl = c(level)
    if strpos(`"`opts'"', "level(") {
        local lvl = substr(`"`opts'"', strpos(`"`opts'"', "level(") + 6, .)
        local lvl = substr("`lvl'", 1, strpos("`lvl'", ")") - 1)
    }
    scalar LC_VAR = .
    if strpos(`"`opts'"', "var(") {
        local vv = substr(`"`opts'"', strpos(`"`opts'"', "var(") + 4, .)
        scalar LC_VAR = real(substr("`vv'", 1, strpos("`vv'", ")") - 1))
    }
    capture lpoly `y' `x' `wexp' if `cond', ci nograph kernel(`kernel') degree(`degree') `opts' generate(lcgx lcgy) se(lcgse) generateci(lccl lccu)
    scalar LC_RC = _rc
    scalar LC_LEVEL = `lvl'
    scalar LC_Z = invnormal(0.5*(1 - `lvl'/100) + `lvl'/100)
    if _rc == 0 {
        scalar LC_BW = r(bwidth)
        scalar LC_PW = r(pwidth)
        scalar LC_N = r(N)
        scalar LC_NGRID = r(ngrid)
        quietly count if !missing(lcgx)
        scalar LC_NG = r(N)
    }
    else {
        foreach s in BW PW N NGRID {
            scalar LC_`s' = .
        }
        scalar LC_NG = 0
    }
    python: import __main__; __main__._lc_rec()
    foreach v in gx gy gse cl cu {
        capture drop lc`v'
    }
end

* lcs id twoway-lpolyci-arguments: the drawn serset of twoway lpolyci
capture program drop lcs
program define lcs
    version 19
    gettoken cid 0 : 0
    tempfile g
    local comma = cond(strpos(`"`0'"', ","), "", ",")
    twoway lpolyci `0'`comma' nodraw saving("`g'.gph", replace)
    graph use "`g'.gph", nodraw
    serset set 0
    preserve
    serset use, clear
    python: import __main__; __main__._lc_serset()
    restore
    graph drop _all
end

* ---------------------------------------------------------------- auto
sysuse auto, clear
gen double wz = price*(rep78 > 2 & rep78 < .)
gen double r1000 = rep78*1000
gen double cx = 3000
local ds auto
local cols "mpg weight price rep78 foreign wz r1000 cx"
python: _lc_dataset()

local E epanechnikov
forvalues d = 0/3 {
    lc a_d`d' auto mpg weight . . 1 `E' `d'
}
foreach k in rectangle triangle parzen cosine epan2 {
    local t = substr("`k'", 1, 3)
    if "`k'" == "epan2" local t ep2
    lc a_d0_`t'_bw400_pw600 auto mpg weight . . 1 `k' 0 "bwidth(400) pwidth(600)"
}
lc a_d0_bw500 auto mpg weight . . 1 `E' 0 "bwidth(500)"
lc a_d0_bw500_pw800 auto mpg weight . . 1 `E' 0 "bwidth(500) pwidth(800)"
lc a_d1_bw500_pw800 auto mpg weight . . 1 `E' 1 "bwidth(500) pwidth(800)"
lc a_d0_var10 auto mpg weight . . 1 `E' 0 "var(10)"
lc a_d1_bw500_var10 auto mpg weight . . 1 `E' 1 "bwidth(500) var(10)"
lc a_d0_aw auto mpg weight aw price 1 `E' 0
lc a_d0_fw auto mpg weight fw rep78 1 `E' 0
lc a_d1_aw_bw500_pw800 auto mpg weight aw price 1 `E' 1 "bwidth(500) pwidth(800)"
lc a_d1_fw_bw500_pw800 auto mpg weight fw rep78 1 `E' 1 "bwidth(500) pwidth(800)"
lc a_d0_bw100_pw150 auto mpg weight . . 1 `E' 0 "bwidth(100) pwidth(150)"
lc a_d0_bw60_pw60 auto mpg weight . . 1 `E' 0 "bwidth(60) pwidth(60)"
lc a_d0_lvl10 auto mpg weight . . 1 `E' 0 "bwidth(500) pwidth(800) level(10)"
lc a_d0_lvl90 auto mpg weight . . 1 `E' 0 "bwidth(500) pwidth(800) level(90)"
lc a_d0_lvl9999 auto mpg weight . . 1 `E' 0 "bwidth(500) pwidth(800) level(99.99)"
lc a_d0_n20 auto mpg weight . . 1 `E' 0 "n(20)"
lc a_d0_bw500_pw800_n20 auto mpg weight . . 1 `E' 0 "bwidth(500) pwidth(800) n(20)"
lc a_d0_gau auto mpg weight . . 1 gaussian 0
lc a_d1_bi auto mpg weight . . 1 biweight 1
lc a_d0_foreign auto mpg weight . . "foreign==1" `E' 0
lc a_d0_foreign_bw400_pw600 auto mpg weight . . "foreign==1" `E' 0 "bwidth(400) pwidth(600)"
lc a_price_rep78_d0 auto price rep78 . . 1 `E' 0
lc rep_d2_bw06 auto price rep78 . . 1 `E' 2 "bwidth(.6)"
lc r1000_d0 auto price r1000 . . 1 `E' 0
lc r1000_d2_bw600 auto price r1000 . . 1 `E' 2 "bwidth(600)"
forvalues n = 2/9 {
    lc in`n' auto mpg weight . . "_n<=`n'" `E' 0
    lc in`n'_bw1000 auto mpg weight . . "_n<=`n'" `E' 0 "bwidth(1000)"
}
lc cx_n5 auto mpg cx . . 1 `E' 0 "n(5)"
lc a_d0_awz auto mpg weight aw wz 1 `E' 0
lc a_d0_awmiss auto mpg weight aw price "rep78>2&rep78<." `E' 0

lcs a_d1_bw500_pw800 mpg weight, degree(1) bwidth(500) pwidth(800)
lcs a_d0 mpg weight
lcs a_d0_foreign mpg weight if foreign==1
lcs a_d1_bi mpg weight, kernel(biweight) degree(1)
lcs a_d0_lvl90 mpg weight, bwidth(500) pwidth(800) level(90)

* ---------------------------------------------------------------- nlsw88
sysuse nlsw88, clear
local ds nlsw88
local cols "wage ttl_exp hours"
python: _lc_dataset()
forvalues d = 0/2 {
    lc n_d`d' nlsw88 wage ttl_exp . . 1 `E' `d'
}
lc n_d1_bw2_pw3 nlsw88 wage ttl_exp . . 1 `E' 1 "bwidth(2) pwidth(3)"
lc n_d0_aw nlsw88 wage ttl_exp aw hours 1 `E' 0
lc n_d1_aw_bw2_pw3 nlsw88 wage ttl_exp aw hours 1 `E' 1 "bwidth(2) pwidth(3)"
lcs n_d1_bw2_pw3 wage ttl_exp, degree(1) bwidth(2) pwidth(3)

* ---------------------------------------------------------------- write
python:
import os
import numpy as np

KER = {
    "epanechnikov": (math.sqrt(5.0), lambda z: 0.75 * (1.0 - z * z / 5.0) / math.sqrt(5.0)),
    "epan2": (1.0, lambda z: 0.75 * (1.0 - z * z)),
    "biweight": (1.0, lambda z: (15.0 / 16.0) * (1.0 - z * z) ** 2),
    "cosine": (0.5, lambda z: 1.0 + np.cos(2.0 * np.pi * z)),
    "gaussian": (np.inf, lambda z: np.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)),
    "rectangle": (1.0, lambda z: np.full_like(z, 0.5)),
    "triangle": (1.0, lambda z: 1.0 - np.abs(z)),
    "parzen": (1.0, lambda z: np.where(np.abs(z) <= 0.5,
                                       4.0 / 3.0 - 8.0 * z * z + 8.0 * np.abs(z) ** 3,
                                       8.0 / 3.0 * (1.0 - np.abs(z)) ** 3)),
}


def no_df(c):
    """Grid indices whose pilot fit (degree p+2 at r(pwidth), pseudo-
    inverse) has no residual degrees of freedom."""
    if c["rc"] or c["pwidth"] is None or not c["gx"]:
        return []
    D = LC["datasets"][c["ds"]]
    x = np.array([D[c["x"]][i] for i in c["idx"]], dtype=float)
    if c["w"]:
        w = np.array([D[c["w"]][i] for i in c["idx"]], dtype=float)
        if c["wtype"] == "aw":
            w = w * len(w) / w.sum()
    else:
        w = np.ones(len(x))
    sup, k = KER[c["kernel"]]
    hp = c["pwidth"]
    out = []
    for i, x0 in enumerate(c["gx"]):
        if x0 is None:
            continue
        z = (x - x0) / hp
        kp = np.where(np.abs(z) < sup, k(z), 0.0)
        kpw = kp * w
        pos = kpw > 0
        if pos.sum() < 2:
            continue
        Z = np.vander(z[pos], c["degree"] + 3, increasing=True)
        A = (Z * kpw[pos, None]).T @ Z
        B = (Z * (kp[pos] * kpw[pos])[:, None]).T @ Z
        den = kpw.sum() - np.trace(np.linalg.pinv(A, rcond=1e-12) @ B)
        if den <= 1e-10 * kpw.sum():
            out.append(i)
    return out


cases = {c["id"]: c for c in LC["cases"]}
LC["no_df"] = {cid: no_df(c) for cid, c in cases.items()}
LC["divergences"] = [
    {"id": "D4", "rows": {k: v for k, v in LC["no_df"].items() if v},
     "reason": "the pilot fit has no residual degrees of freedom: Stata's se "
               "is round-off or missing there; dash pinches the band (se 0)"},
]
LC["_meta"] = {
    "stata_version": Macro.getGlobal("LC_SVER"),
    "born_date": Macro.getGlobal("LC_BORN"),
    "extracted": Macro.getGlobal("LC_DATE"),
    "dash_commit": Macro.getGlobal("LC_COMMIT"),
    "method": "lpoly, ci se() generateci() and the twoway lpolyci serset",
    "script": "scripts/extract_lpolyci_truth.do",
}
out = os.path.join(Macro.getGlobal("W29_REPO"), "test", "fixtures",
                   "lpolyci_truth.json")
with open(out, "w") as fh:
    json.dump(LC, fh, sort_keys=True)
print("wrote %s: %d cases, %d sersets" % (out, len(LC["cases"]), len(LC["serset"])))
end
