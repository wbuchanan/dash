*! extract_axis_rows_truth.do
*! WP-44 WE (AX-19, AX-20): ground truth for the rows an axis reads -- a
*! layer's variables each over the layer's own rows, a row whose partner
*! is missing included (AX-19), and a baroffset() bar's ticks and range
*! (AX-20) -- for test/fixtures/axis_rows_truth.json.
*!
*! WHY THIS EXISTS
*!
*! The tests compare dash with what twoway does, never with a guess.
*! AX-19 was registered as "a range type widens the x axis over rows
*! where both bounds are missing; twoway leaves those rows out", and
*! twoway measured on 07nov2026 does the opposite for every type.  This
*! script records what twoway draws.
*!
*! Output: test/fixtures/axis_rows_truth.json
*!
*! Run with:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_axis_rows_truth.do
*!
*! METHOD
*!
*! `_ar_run key data cmd' builds data set <data> (_ar_m: 100 rows, y
*! missing past row 20; _ar_q, _ar_n, _ar_d: eight bars on a %tq, plain
*! and %td axis), runs cmd under the stcolor scheme for the session only
*! and exports a drawn graph to SVG.  The trailing python: block reads
*! files only: through scripts/svg_truth.py each axis's labels, their
*! values in Stata units (a %tq or %td label read back) and positions,
*! and the axis's range at the plot region's edges, extrapolated from the
*! outermost two labels.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off
set linesize 255
version 19

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_ar_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_ar_bad' {
    display as error "extract_axis_rows_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _ar_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_ar_rc' | _rc {
    local _ar_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_axis_rows_truth.do: `_ar_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global AR_REPO "`repo'"
global AR_OUT "${AR_REPO}/test/fixtures/axis_rows_truth.json"

local work "`c(tmpdir)'dash_axis_rows_probe"
capture mkdir "`work'"
global AR_WORK "`work'"

quietly shell git -C "${AR_REPO}" rev-parse HEAD > "${AR_WORK}/git_head.txt"
global AR_VERSION "`c(stata_version)'"
global AR_BORN "`c(born_date)'"
global AR_WHEN "`c(current_date)' `c(current_time)'"

* 100 rows: x 1-100; y present on rows 1-20 only, y2 = y + 3, y3 between
* them; yb on rows 1-40; x2 on rows 1-20; yy every row; xd = x + 1; t the
* quarters from 1990q1, tsset.
capture program drop _ar_m
program define _ar_m
    clear
    quietly set obs 100
    quietly generate x = _n
    quietly generate y = cond(_n <= 20, _n, .)
    quietly generate y2 = y + 3
    quietly generate y3 = y + 1
    quietly generate yb = cond(_n <= 40, _n, .)
    quietly generate x2 = cond(_n <= 20, _n, .)
    quietly generate yy = _n
    quietly generate xd = x + 1
    quietly generate t = tq(1990q1) + _n - 1
    format t %tq
    quietly tsset t
end
* Eight bars, y 1-8: on a %tq axis from 2001q1, a plain one from 1, a %td
* one from 1jan2001.
capture program drop _ar_q
program define _ar_q
    clear
    quietly set obs 8
    quietly generate t = tq(2001q1) + _n - 1
    format t %tq
    quietly generate y = _n
    quietly generate y0 = 0
end
capture program drop _ar_n
program define _ar_n
    clear
    quietly set obs 8
    quietly generate t = _n
    quietly generate y = _n
end
capture program drop _ar_d
program define _ar_d
    clear
    quietly set obs 8
    quietly generate t = td(1jan2001) + _n - 1
    format t %td
    quietly generate y = _n
end

capture program drop _ar_run
program define _ar_run
    args key data cmd
    `data'
    set scheme stcolor
    capture graph drop u44r
    capture noisily `macval(cmd)' name(u44r, replace)
    local rc = _rc
    global AR_R_`key' "`rc'"
    global AR_C_`key' `"`macval(cmd)'"'
    global AR_D_`key' "`data'"
    global AR_KEYS "${AR_KEYS} `key'"
    if !`rc' {
        quietly graph export "${AR_WORK}/`key'.svg", replace
    }
end

global AR_KEYS ""

* AX-19: each variable over the layer's own rows, every type dash maps.
foreach t in scatter line connected area bar spike dropline dot tsline {
    if "`t'" == "tsline" _ar_run ax19_`t' _ar_m "twoway tsline y,"
    else _ar_run ax19_`t' _ar_m "twoway `t' y x,"
}
foreach t in rarea rbar rspike rcap rcapsym rline rconnected rscatter {
    _ar_run ax19_`t' _ar_m "twoway `t' y y2 x,"
}
_ar_run ax19_tsrline _ar_m "twoway tsrline y y2,"
foreach t in rpcap rpspike {
    _ar_run ax19_`t' _ar_m "twoway `t' y y2 y3 x,"
}
foreach t in pcspike pccapsym pcarrow pcbarrow pcscatter {
    _ar_run ax19_`t' _ar_m "twoway `t' y x y2 xd,"
}
foreach t in lfit qfit fpfit mspline mband lowess lpoly lfitci qfitci fpfitci lpolyci {
    _ar_run ax19_`t' _ar_m "twoway `t' y x,"
}
* Turned: the variables keep their own rows on the drawn axes.
foreach t in scatter line area bar spike {
    _ar_run ax19_`t'_h _ar_m "twoway `t' y x, horizontal"
}
foreach t in rspike rarea rline {
    _ar_run ax19_`t'_h _ar_m "twoway `t' y y2 x, horizontal"
}
* The y axis over rows whose x is missing.
foreach t in scatter line bar {
    _ar_run ax19_`t'_xmiss _ar_m "twoway `t' yy x2,"
}
* if keeps a layer's rows; two y read each over its own rows.
_ar_run ax19_if _ar_m "twoway scatter y x if x <= 50,"
_ar_run ax19_multi _ar_m "twoway scatter y yb x,"
_ar_run ax19_two _ar_m "twoway (scatter y x) (line yb x),"

* AX-20: a baroffset() bar is ticked over its data and its range widened
* half a bar and |baroffset()| bars each way (yxview.class minmax_range).
_ar_run ax20_q_plain _ar_q "twoway bar y t,"
_ar_run ax20_q_half _ar_q "twoway bar y t, baroffset(0.5)"
_ar_run ax20_q_three _ar_q "twoway bar y t, baroffset(3)"
_ar_run ax20_q_neg _ar_q "twoway bar y t, baroffset(-2) barwidth(0.5)"
_ar_run ax20_q_rbar _ar_q "twoway rbar y0 y t, baroffset(3)"
_ar_run ax20_q_h _ar_q "twoway bar y t, horizontal baroffset(3)"
_ar_run ax20_n_plain _ar_n "twoway bar y t,"
_ar_run ax20_n_three _ar_n "twoway bar y t, baroffset(3)"
_ar_run ax20_d_plain _ar_d "twoway bar y t,"
_ar_run ax20_d_three _ar_d "twoway bar y t, baroffset(3)"


python:
import json, os, re, sys
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


sys.path.insert(0, os.path.join(G("AR_REPO"), "scripts"))
import svg_truth

work = G("AR_WORK")
_MON = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep",
        "oct", "nov", "dec"]


def value(text):
    """A label's value in Stata units: a number, a %tq quarter or a %td
    day; None for anything else (the axis title)."""
    s = str(text).replace(",", "").strip()
    m = re.fullmatch(r"(\d{4})q([1-4])", s)
    if m:
        return (int(m.group(1)) - 1960) * 4 + int(m.group(2)) - 1
    m = re.fullmatch(r"(\d{2})([a-z]{3})(\d{4})", s)
    if m and m.group(2) in _MON:
        import datetime
        d = datetime.date(int(m.group(3)), _MON.index(m.group(2)) + 1,
                          int(m.group(1)))
        return (d - datetime.date(1960, 1, 1)).days
    try:
        return float(s)
    except ValueError:
        return None


def axis(labels, lo_px, hi_px, flip):
    """[[value, position]] and the range at the region's edges."""
    vals = [[value(t), p] for t, p in labels if value(t) is not None]
    vals.sort(key=lambda r: r[1])
    rng = None
    if len(vals) >= 2:
        (v0, p0), (v1, p1) = vals[0], vals[-1]
        k = (v1 - v0) / (p1 - p0)
        a, b = v0 + (lo_px - p0) * k, v0 + (hi_px - p0) * k
        rng = sorted([a, b])
    return vals, rng


def drawn(key):
    doc = svg_truth.svg_document(os.path.join(work, key + ".svg"))
    pr = doc["plotregion"]
    t = [x for x in doc["texts"] if x["x"] is not None and x["y"] is not None]
    xl = [(x["text"], x["x"]) for x in t if x["y"] > pr["bottom"]
          and x["rotate"] is None]
    yl = [(x["text"], x["y"]) for x in t if x["x"] < pr["left"]
          and x["rotate"] is None]
    xv, xr = axis(xl, pr["left"], pr["right"], False)
    yv, yr = axis(yl, pr["top"], pr["bottom"], True)
    return {"plotregion": {k: pr[k] for k in ("left", "top", "right",
                                                "bottom")},
            "x": [v for v, _p in xv], "y": sorted(v for v, _p in yv),
            "x_range": xr, "y_range": yr}


out = {"graphs": {}}
for key in G("AR_KEYS").split():
    rc = int(G("AR_R_" + key))
    row = {"rc": rc, "command": G("AR_C_" + key), "data": G("AR_D_" + key)}
    if not rc:
        row.update(drawn(key))
        os.remove(os.path.join(work, key + ".svg"))
    out["graphs"][key] = row

try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("AR_VERSION"), "born_date": G("AR_BORN"),
                "dash_commit": commit, "extracted": G("AR_WHEN"),
                "scheme": "stcolor",
                "source": "scripts/extract_axis_rows_truth.do"}
with open(G("AR_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True, ensure_ascii=False)
    fh.write("\n")
print("wrote", G("AR_OUT"))
end
