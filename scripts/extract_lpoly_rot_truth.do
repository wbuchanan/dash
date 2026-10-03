*! extract_lpoly_rot_truth.do
*! Stata's own lpoly default bandwidth (the rule of thumb), its grid count,
*! the column pattern Mata's invsym() keeps on the global raw-power fit, and
*! lpoly curves, recorded for WP-29 S11 (P0.7) by probing Stata itself.
*!
*! Output: ${W29_REPO}/test/fixtures/lpoly_rot_truth.json.  W29_REPO is a
*! global set by the two-line driver (refused with exit 198 when empty):
*!
*!   global W29_REPO "<repo>"
*!   do "<repo>/scripts/extract_lpoly_rot_truth.do"
*!
*! run as <repo>/scripts/stata_slot.sh <scratch> <driver>.do (never the GUI).
*!
*! METHOD
*!  rows      capture lpoly y x [w] if <cond>, nograph kernel() degree():
*!            rc, r(bwidth), r(ngrid), r(N).  On the same sample a Mata
*!            block builds the raw powers X = (1, x, ..., x^(pe+3)) (pe is
*!            the degree if odd, else the degree + 1), G = quadcross(X,w,X),
*!            invsym(G), and records which diagonal elements invsym kept
*!            (kept), the weighted residual variance of that fit (s2_mata)
*!            and of y about its weighted mean (vy).  Weights are lpoly's:
*!            aweights rescaled to mean 1 on the sample, fweights raw.
*!            idx holds the 0-based observations lpoly used.
*!  curves    lpoly ... nograph generate(gx gy) [bwidth() n()].
*!  serset    twoway lpoly mpg weight, kernel(biweight) degree(2) by(foreign)
*!            nodraw saving(), graph use, serset set k, serset use.
*!  Every number is held in a Stata scalar or variable at full double
*!  precision and read by the python: blocks only through sfi (they never
*!  call Stata); json.dump writes every double so it round-trips.
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

tempfile LW_GITREV
capture shell cd "${W29_REPO}" && git rev-parse HEAD > "`LW_GITREV'"
local LW_DASH_COMMIT ""
capture confirm file "`LW_GITREV'"
if !_rc {
    file open lwgitrev using "`LW_GITREV'", read text
    file read lwgitrev lwgitline
    local LW_DASH_COMMIT = strtrim(`"`lwgitline'"')
    file close lwgitrev
}
global LW_SVER = c(stata_version)
global LW_BORN = c(born_date)
global LW_DATE = c(current_date)
global LW_COMMIT "`LW_DASH_COMMIT'"
tempfile LW_S30
global LW_S30 "`LW_S30'.csv"

python:
import json, math
import numpy as np
from sfi import Data, Macro, Scalar

LW = {"datasets": {}, "rows": [], "curves": [], "serset": []}

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

def _lw_dataset():
    ds = Macro.getLocal("ds")
    cols = Macro.getLocal("cols").split()
    LW["datasets"][ds] = {c: _col(c) for c in cols}

def _lw_rec():
    g = Macro.getLocal
    deg = int(g("degree"))
    idx = [int(t) for t in g("idx").split()]
    LW["rows"].append({
        "ds": g("ds"), "y": g("y"), "x": g("x"), "w": g("wv"),
        "wtype": g("wtype"), "cond": g("cond"), "idx": idx,
        "kernel": g("kernel"), "degree": deg,
        "n_grid": int(Scalar.getValue("LW_NG")),
        "rc": int(Scalar.getValue("LW_RC")),
        "bwidth": _num(Scalar.getValue("LW_BW")),
        "ngrid": _num(Scalar.getValue("LW_NGRID")),
        "N": _num(Scalar.getValue("LW_N")),
        "kept": g("kept"),
        "s2_mata": _num(Scalar.getValue("LW_S2")),
        "vy": _num(Scalar.getValue("LW_VY")),
    })

def _lw_curve():
    g = Macro.getLocal
    n = int(Scalar.getValue("LW_CN"))
    gx = _col("lwgx", list(range(n))) if n else []
    gy = _col("lwgy", list(range(n))) if n else []
    LW["curves"].append({
        "id": g("cid"), "ds": g("ds"), "y": g("y"), "x": g("x"),
        "cond": g("cond"), "idx": [int(t) for t in g("idx").split()],
        "kernel": g("kernel"), "degree": int(g("degree")),
        "bwidth_opt": _num(Scalar.getValue("LW_CBWO")),
        "n_opt": _num(Scalar.getValue("LW_CNO")),
        "rc": int(Scalar.getValue("LW_RC")),
        "bwidth": _num(Scalar.getValue("LW_BW")),
        "gx": gx, "gy": gy})

def _lw_serset():
    g = Macro.getLocal
    n = Data.getObsTotal()
    names = [Data.getVarName(i) for i in range(Data.getVarCount())]
    vals = {nm: _col(nm) for nm in names}
    LW["serset"].append({"panel": int(g("k")), "count": int(n),
                         "vars": names, "values": vals})

# test/test_server.py::auto_df, exactly.
rng = np.random.default_rng(42)
n = 30
cols = {"mpg": rng.integers(12, 40, n).astype(float),
        "weight": rng.integers(1800, 4800, n).astype(float),
        "price": rng.integers(3000, 15000, n).astype(float),
        "foreign": rng.integers(0, 2, n).astype(float)}
with open(Macro.getGlobal("LW_S30"), "w") as fh:
    fh.write("mpg,weight,price,foreign\n")
    for i in range(n):
        fh.write(",".join(repr(float(cols[c][i])) for c in
                          ("mpg", "weight", "price", "foreign")) + "\n")
end

mata:
void _lw_fit(string scalar yv, string scalar xv, string scalar wv,
             string scalar wtype, string scalar touse, real scalar degree)
{
    real colvector y, x, w, r, b, idx
    real matrix X, G, Gi
    real scalar pe, d, k, n, sw, ybar
    idx = selectindex(st_data(., touse))
    st_local("idx", invtokens(strofreal((idx :- 1)', "%12.0f")))
    st_local("kept", "")
    st_numscalar("LW_S2", .)
    st_numscalar("LW_VY", .)
    n = rows(idx)
    if (n == 0) return
    y = st_data(idx, yv)
    x = st_data(idx, xv)
    if (wv == "") w = J(n, 1, 1)
    else w = st_data(idx, wv)
    if (wtype == "aw") w = w * n / quadsum(w)
    pe = mod(degree, 2) ? degree : degree + 1
    d = pe + 3
    X = J(n, d + 1, 1)
    for (k = 1; k <= d; k++) X[., k + 1] = x :^ k
    G = quadcross(X, w, X)
    Gi = invsym(G)
    st_local("kept", invtokens(strofreal((diagonal(Gi) :!= 0)'), ""))
    b = Gi * quadcross(X, w, y)
    r = y - X * b
    sw = quadsum(w)
    st_numscalar("LW_S2", quadsum(w :* r :^ 2) / sw)
    ybar = quadsum(w :* y) / sw
    st_numscalar("LW_VY", quadsum(w :* (y :- ybar) :^ 2) / sw)
}
end

* lw ds y x wtype wv cond kernel degree   (wtype/wv "." for none)
capture program drop lw
program define lw
    version 19
    args ds y x wtype wv cond kernel degree
    if "`wtype'" == "." local wtype ""
    if "`wv'" == "." local wv ""
    tempvar touse
    quietly gen byte `touse' = (`cond') & !missing(`y', `x')
    local wexp ""
    if "`wv'" != "" {
        quietly replace `touse' = 0 if missing(`wv') | `wv' <= 0
        local wexp "[`wtype'=`wv']"
    }
    scalar LW_NG = min(50, _N)
    capture lpoly `y' `x' `wexp' if `cond', nograph kernel(`kernel') degree(`degree')
    scalar LW_RC = _rc
    if _rc == 0 {
        scalar LW_BW = r(bwidth)
        scalar LW_NGRID = r(ngrid)
        scalar LW_N = r(N)
    }
    else {
        scalar LW_BW = .
        scalar LW_NGRID = .
        scalar LW_N = .
    }
    local kept ""
    local idx ""
    mata: _lw_fit("`y'", "`x'", "`wv'", "`wtype'", "`touse'", `degree')
    python: import __main__; __main__._lw_rec()
end

* lwc id ds y x cond kernel degree bwidth n   (bwidth/n "." for default)
capture program drop lwc
program define lwc
    version 19
    args cid ds y x cond kernel degree bw nn
    local opt ""
    scalar LW_CBWO = .
    scalar LW_CNO = .
    if "`bw'" != "." {
        local opt "`opt' bwidth(`bw')"
        scalar LW_CBWO = `bw'
    }
    if "`nn'" != "." {
        local opt "`opt' n(`nn')"
        scalar LW_CNO = `nn'
    }
    tempvar touse
    quietly gen byte `touse' = (`cond') & !missing(`y', `x')
    mata: st_local("idx", invtokens(strofreal((selectindex(st_data(., "`touse'")) :- 1)', "%12.0f")))
    capture drop lwgx lwgy
    capture lpoly `y' `x' if `cond', nograph kernel(`kernel') degree(`degree') `opt' generate(lwgx lwgy)
    scalar LW_RC = _rc
    scalar LW_BW = cond(_rc == 0, r(bwidth), .)
    quietly count if !missing(lwgx)
    scalar LW_CN = r(N)
    python: import __main__; __main__._lw_curve()
    capture drop lwgx lwgy
end

local KERN "epanechnikov epan2 biweight cosine gaussian parzen rectangle triangle"

* ---------------------------------------------------------------- auto
sysuse auto, clear
gen double ycon = 5
gen double ysq = (weight/1000)^2
gen double ylin = 2*weight + 1
gen double yw = weight
gen double one = 1
gen double f38 = 3 + 5*foreign
gen double wtd = weight + 20000
gen double wtc = weight*86400000 + 1.9e12
gen double wz = price*(rep78 > 2 & rep78 < .)
gen double r10 = rep78*10
local cols "mpg weight price rep78 trunk headroom foreign ycon ysq ylin yw one f38 wtd wtc wz r10"
foreach k in -100 -60 -40 -20 -10 -9 -8 -7 -6 -5 -4 -3 -2 -1 1 2 3 4 5 6 10 20 22 25 30 35 40 50 75 100 140 200 {
    local nm = cond(`k' < 0, "wkm" + string(-`k'), "wkp" + string(`k'))
    gen double `nm' = weight*10^`k'
    local cols "`cols' `nm'"
}
foreach k in 100 150 160 200 -100 -150 -160 -200 -300 {
    local nm = cond(`k' < 0, "mkm" + string(-`k'), "mkp" + string(`k'))
    gen double `nm' = mpg*10^`k'
    local cols "`cols' `nm'"
}
forvalues a = 1/9 {
    forvalues e = 0/7 {
        gen double wo`a'e`e' = weight + `a'e`e'
        local cols "`cols' wo`a'e`e'"
    }
}
foreach s in 3 4 5 6 7 {
    gen double ws`s' = weight*1e-`s'
    local cols "`cols' ws`s'"
}
local ds auto
python: _lw_dataset()

foreach pr in "mpg weight" "price mpg" "price rep78" "mpg headroom" {
    tokenize `pr'
    foreach k of local KERN {
        forvalues d = 0/5 {
            lw auto `1' `2' . . 1 `k' `d'
        }
    }
}
foreach wv in price rep78 trunk {
    forvalues d = 0/3 {
        lw auto mpg weight aw `wv' 1 epanechnikov `d'
    }
}
foreach wv in rep78 trunk {
    forvalues d = 0/3 {
        lw auto mpg weight fw `wv' 1 epanechnikov `d'
    }
}
forvalues d = 0/3 {
    lw auto mpg weight aw wz 1 epanechnikov `d'
    lw auto mpg weight aw price "rep78>2&rep78<." epanechnikov `d'
}
foreach k in epanechnikov gaussian {
    forvalues d = 0/3 {
        forvalues n = 2/12 {
            lw auto mpg weight . . "_n<=`n'" `k' `d'
        }
        lw auto mpg weight . . "foreign==0" `k' `d'
        lw auto mpg weight . . "foreign==1" `k' `d'
    }
}
forvalues d = 0/3 {
    lw auto mpg wtd . . 1 epanechnikov `d'
    lw auto mpg wtc . . 1 epanechnikov `d'
}
forvalues a = 1/9 {
    forvalues e = 0/7 {
        lw auto mpg wo`a'e`e' . . 1 epanechnikov 0
        lw auto mpg wo`a'e`e' . . 1 epanechnikov 2
    }
}
foreach k in -9 -8 -7 -6 -5 -4 -3 -2 -1 1 2 3 4 5 6 {
    local nm = cond(`k' < 0, "wkm" + string(-`k'), "wkp" + string(`k'))
    forvalues d = 0/3 {
        lw auto mpg `nm' . . 1 epanechnikov `d'
    }
}
foreach k in 10 20 22 25 30 35 40 50 75 100 140 -10 -20 -40 -60 -100 {
    local nm = cond(`k' < 0, "wkm" + string(-`k'), "wkp" + string(`k'))
    lw auto mpg `nm' . . 1 epanechnikov 0
    lw auto mpg `nm' . . 1 epanechnikov 2
}
foreach k in 100 150 160 200 -100 -150 -160 -200 -300 {
    local nm = cond(`k' < 0, "mkm" + string(-`k'), "mkp" + string(`k'))
    lw auto `nm' weight . . 1 epanechnikov 0
    lw auto `nm' weight . . 1 epanechnikov 2
}
forvalues d = 0/3 {
    foreach yv in ycon ysq ylin yw {
        lw auto `yv' weight . . 1 epanechnikov `d'
    }
    lw auto mpg one . . 1 epanechnikov `d'
    lw auto mpg foreign . . 1 epanechnikov `d'
    lw auto mpg f38 . . 1 epanechnikov `d'
    lw auto price rep78 . . "inlist(rep78,3,4)" epanechnikov `d'
    lw auto price rep78 . . "inlist(rep78,2,3,4)" epanechnikov `d'
    lw auto price rep78 . . "rep78>=3" epanechnikov `d'
    lw auto mpg wkp200 . . 1 epanechnikov `d'
}

* curves
lwc bi_d2 auto mpg weight 1 biweight 2 . .
lwc bi_d2_f1 auto mpg weight "foreign==1" biweight 2 . .
lwc bi_d2_f0 auto mpg weight "foreign==0" biweight 2 . .
lwc ep_d0 auto mpg weight 1 epanechnikov 0 . .
lwc ep_d0_f1 auto mpg weight "foreign==1" epanechnikov 0 . .
lwc ga_d1 auto mpg weight 1 gaussian 1 . .
lwc ga_d1_f1 auto mpg weight "foreign==1" gaussian 1 . .
foreach yv in ylin yw {
    forvalues d = 0/3 {
        lwc `yv'_d`d' auto `yv' weight 1 epanechnikov `d' . .
    }
}
foreach yv in ycon ysq {
    forvalues d = 0/3 {
        lwc `yv'_d`d' auto `yv' weight 1 epanechnikov `d' . .
    }
}
forvalues n = 2/12 {
    forvalues d = 0/3 {
        lwc in`n'_d`d' auto mpg weight "_n<=`n'" epanechnikov `d' . .
    }
}
lwc r10_d1 auto price r10 1 epanechnikov 1 3 41
lwc bi_d2_f1_bw auto mpg weight "foreign==1" biweight 2 287.77974373265636 .
lwc ep_d3_bw auto mpg weight 1 epanechnikov 3 120.792907978892 .
forvalues d = 1/3 {
    lwc ws0_d`d' auto mpg weight 1 epanechnikov `d' 300 .
    foreach s in 3 4 5 6 7 {
        local bw = 300*1e-`s'
        lwc ws`s'_d`d' auto mpg ws`s' 1 epanechnikov `d' `bw' .
    }
}

* serset of twoway lpoly ... by(foreign)
tempfile LW_GPH
twoway lpoly mpg weight, kernel(biweight) degree(2) by(foreign) nodraw saving("`LW_GPH'.gph", replace)
graph use "`LW_GPH'.gph", nodraw
forvalues k = 0/1 {
    serset set `k'
    preserve
    serset use, clear
    python: import __main__; __main__._lw_serset()
    restore
}

* ---------------------------------------------------------------- census
sysuse census, clear
local ds census
local cols "death pop"
python: _lw_dataset()
foreach k of local KERN {
    forvalues d = 0/3 {
        lw census death pop . . 1 `k' `d'
    }
}

* ---------------------------------------------------------------- sp500
sysuse sp500, clear
gen double datetc = cofd(date)
local ds sp500
local cols "close volume date datetc"
python: _lw_dataset()
foreach k of local KERN {
    forvalues d = 0/3 {
        lw sp500 close volume . . 1 `k' `d'
    }
}
forvalues d = 0/3 {
    lw sp500 close date . . 1 epanechnikov `d'
    lw sp500 volume date . . 1 biweight `d'
}
lw sp500 close datetc . . 1 epanechnikov 0
lw sp500 close datetc . . 1 epanechnikov 2

* ---------------------------------------------------------------- nlsw88
sysuse nlsw88, clear
local ds nlsw88
local cols "wage ttl_exp hours grade"
python: _lw_dataset()
foreach k of local KERN {
    forvalues d = 0/3 {
        lw nlsw88 wage ttl_exp . . 1 `k' `d'
        lw nlsw88 wage hours . . 1 `k' `d'
    }
}
forvalues d = 0/3 {
    lw nlsw88 wage ttl_exp aw hours 1 epanechnikov `d'
    lw nlsw88 wage ttl_exp fw grade 1 epanechnikov `d'
}

* ---------------------------------------------------------------- uslifeexp
sysuse uslifeexp, clear
local ds uslifeexp
local cols "le le_male year"
python: _lw_dataset()
forvalues d = 0/3 {
    lw uslifeexp le year . . 1 epanechnikov `d'
    lw uslifeexp le_male year . . 1 gaussian `d'
}

* ---------------------------------------------------------------- server30
import delimited using "${LW_S30}", clear asdouble
local ds server30
local cols "mpg weight price foreign"
python: _lw_dataset()
lw server30 mpg weight . . 1 epanechnikov 0

* ---------------------------------------------------------------- write
python:
import datetime, os
TOL = {"exact": 1e-7, "noisy": 5e-5}
# Maintainer ruling (WP-29 batch 2, 01oct2026): these four degree-2 rows of
# the offset sweep get their own 1e-4 tier.  The gap (5.0e-5 to 7.3e-5) is
# Stata's own float64 round-off on raw powers up to x^6: dash's exact rule
# agrees with an all-Fraction computation from the data to 1e-14 there, and
# Stata gives the same r(bwidth) under every row order.
OFFSET_TIER = {"auto-mpg-wo1e3--epanechnikov-d2-n74",
               "auto-mpg-wo5e3--epanechnikov-d2-n74",
               "auto-mpg-wo5e4--epanechnikov-d2-n74",
               "auto-mpg-wo6e4--epanechnikov-d2-n74"}
seen = {}
for r in LW["rows"]:
    col = LW["datasets"][r["ds"]][r["x"]]
    xs = [col[i] for i in r["idx"]]
    if r["bwidth"] is None or r["bwidth"] == 0:
        cls = "missing"
    else:
        ycol = LW["datasets"][r["ds"]][r["y"]]
        ys = [ycol[i] for i in r["idx"]]
        ycon = len(set(ys)) == 1
        # Maintainer ruling (01oct2026): an exact fit is s2 <= 1e-6*var(y)
        # (measured: exact fits at <= 3.2e-10, genuine rows >= 0.012).
        if ycon or (r["s2_mata"] is not None and r["vy"] is not None
                    and r["s2_mata"] <= 1e-6 * r["vy"]):
            cls = "noise"
        else:
            mn, mx = min(xs), max(xs)
            if r["degree"] >= 2 or abs((mn + mx) / 2) > 3 * (mx - mn) / 2:
                cls = "noisy"
            else:
                cls = "exact"
    r["class"] = cls
    wpart = "" if not r["w"] else r["wtype"] + "." + r["w"]
    rid = "%s-%s-%s-%s-%s-d%d-n%d" % (r["ds"], r["y"], r["x"], wpart,
                                      r["kernel"], r["degree"], len(r["idx"]))
    k = seen.get(rid, 0)
    seen[rid] = k + 1
    r["id"] = rid if k == 0 else "%s-%d" % (rid, k + 1)
    if cls in ("missing", "noise"):
        r["tol"] = None
    elif r["id"] in OFFSET_TIER:
        r["tol"] = 1e-4
    elif r["degree"] >= 4:
        r["tol"] = 5e-4
    else:
        r["tol"] = TOL[cls]

LW["divergences"] = [
    {"id": "D1", "rows": ["auto-ylin-weight--epanechnikov-d0-n74"],
     "stata": next((r["bwidth"] for r in LW["rows"]
                    if r["id"] == "auto-ylin-weight--epanechnikov-d0-n74"), None),
     "reason": "y exactly linear in x: Stata's h is round-off of an exact "
               "fit; dash's float emulation gives another h, and the "
               "degree-0 curve differs (up to about 239 on a range of 6160)."},
    {"id": "D2", "rows": ["auto-yw-weight--epanechnikov-d0-n74",
                          "auto-yw-weight--epanechnikov-d1-n74"],
     "stata": next((r["bwidth"] for r in LW["rows"]
                    if r["id"] == "auto-yw-weight--epanechnikov-d0-n74"), None),
     "reason": "y equal to x: Stata's h is round-off (49 points); dash draws "
               "50 and its degree-0 curve differs by up to about 37."},
    {"id": "D3", "rows": ["auto-mkm150-weight--epanechnikov-d2-n74"],
     "stata": next((r["bwidth"] for r in LW["rows"]
                    if r["id"] == "auto-mkm150-weight--epanechnikov-d2-n74"), None),
     "reason": "mpg*1e-150 at degree 2: the squared derivative underflows "
               "in dash's exact rule (NaN, a zero line) where Stata's "
               "arithmetic gives a finite h."},
]
LW["_meta"] = {
    "stata_version": Macro.getGlobal("LW_SVER"),
    "born_date": Macro.getGlobal("LW_BORN"),
    "extracted": Macro.getGlobal("LW_DATE"),
    "dash_commit": Macro.getGlobal("LW_COMMIT"),
    "method": "lpoly r(bwidth)/r(ngrid) and Mata invsym(quadcross()) on raw powers",
    "script": "scripts/extract_lpoly_rot_truth.do",
}
out = os.path.join(Macro.getGlobal("W29_REPO"), "test", "fixtures",
                   "lpoly_rot_truth.json")
with open(out, "w") as fh:
    json.dump(LW, fh, sort_keys=True)
print("wrote %s: %d rows, %d curves" % (out, len(LW["rows"]), len(LW["curves"])))
end
