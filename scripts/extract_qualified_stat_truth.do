*! extract_qualified_stat_truth.do -- regenerate
*! test/fixtures/qualified_stat_truth.json from live Stata: what Stata
*! computes and draws for lfit, lpoly and lpolyci of mpg on weight (sysuse
*! auto), on all 74 cars and on `if foreign==1' (22 cars), so a per-plot
*! qualifier is proved to be applied BEFORE the statistic is computed.
*! Two oracles per layer: r()/e() of Stata's own command (regress, lpoly)
*! and the plotted points -- the graph is saved to a .gph, `graph use'
*! makes its serset addressable and `serset set 0' + `serset use, clear'
*! load the drawn numbers back.  Records go to a file under c(tmpdir); the
*! python block reshapes them and computes no statistic beyond the
*! summaries (min, max, counts, widest band, endpoints, headline).
*! Strings in the python block spell a backtick \x60.
*!
*! Output: test/fixtures/qualified_stat_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_qualified_stat_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 255

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zq_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zq_bad' {
    display as error "extract_qualified_stat_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zq_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zq_rc' | _rc {
    local _zq_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_qualified_stat_truth.do: `_zq_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZQ_REPO "`repo'"
global ZQ_OUT "${ZQ_REPO}/test/fixtures/qualified_stat_truth.json"
global dash_nobrowser 1
set graphics off

local work "`c(tmpdir)'dash_qualified_stat_probe"
capture mkdir "`work'"
global ZQ_WORK "`work'"
quietly shell git -C "${ZQ_REPO}" rev-parse HEAD > "${ZQ_WORK}/git_head.txt"
global ZQ_VERSION "`c(stata_version)'"
global ZQ_BORN "`c(born_date)'"
global ZQ_WHEN "`c(current_date)' `c(current_time)'"
global ZQ_LEVEL "`c(level)'"

file open zq using "${ZQ_WORK}/zq_records.txt", write text replace

* _zq_k <key> <value>: one scalar record (%21.17g; "." is missing).
capture program drop _zq_k
program define _zq_k
    args key val
    file write zq `"K|`key'|`=strofreal(`val', "%21.17g")'"' _n
end

* _zq_s <key> <text>: one string record.
capture program drop _zq_s
program define _zq_s
    args key txt
    file write zq `"S|`key'|`txt'"' _n
end

* _zq_plot <prefix> <twoway command>: draw, save, graph use, serset 0;
* every serset column as an array record <prefix>.c<j>.
capture program drop _zq_plot
program define _zq_plot
    args prefix cmd
    capture graph drop _all
    serset clear
    local sep = cond(strpos(`"`cmd'"', ","), " ", ", ")
    capture `cmd'`sep'saving("${ZQ_WORK}/zq.gph", replace)
    _zq_k `prefix'.rc _rc
    _zq_s `prefix'.cmd `"`cmd'"'
    capture graph drop _all
    graph use "${ZQ_WORK}/zq.gph"
    capture serset set 0
    _zq_k `prefix'.serset_rc _rc
    preserve
    serset use, clear
    local j 0
    foreach v of varlist _all {
        local ++j
        local line ""
        forvalues i = 1/`=_N' {
            local line "`line' `=strofreal(`v'[`i'], "%21.17g")'"
        }
        file write zq `"A|`prefix'.c`j'|`line'"' _n
    }
    restore
    capture graph drop _all
end

foreach variant in all foreign1 {
    local q = cond("`variant'" == "all", "", " if foreign==1")
    quietly sysuse auto, clear
    quietly count`q'
    _zq_k `variant'.N_rows r(N)

    * lfit: regress, the estimation sample's x range, the fit there.
    quietly regress mpg weight`q'
    _zq_s lfit.`variant'.regress.cmd `"regress mpg weight`q'"'
    _zq_k lfit.`variant'.regress.N e(N)
    _zq_k lfit.`variant'.regress.df_r e(df_r)
    _zq_k lfit.`variant'.regress.slope _b[weight]
    _zq_k lfit.`variant'.regress.intercept _b[_cons]
    _zq_k lfit.`variant'.regress.se_slope _se[weight]
    _zq_k lfit.`variant'.regress.se_cons _se[_cons]
    _zq_k lfit.`variant'.regress.rmse e(rmse)
    _zq_k lfit.`variant'.regress.r2 e(r2)
    local b1 = _b[weight]
    local b0 = _b[_cons]
    quietly summarize weight if e(sample)
    _zq_k lfit.`variant'.regress.x_min r(min)
    _zq_k lfit.`variant'.regress.x_max r(max)
    local f0 = `b0' + `b1' * r(min)
    local f1 = `b0' + `b1' * r(max)
    _zq_k lfit.`variant'.regress.fit_at_x_min `f0'
    _zq_k lfit.`variant'.regress.fit_at_x_max `f1'
    _zq_plot lfit.`variant'.plotted `"twoway lfit mpg weight`q'"'

    * lpoly: the command's own grid, then the drawn curve.
    quietly sysuse auto, clear
    local lc = "lpoly mpg weight`q', degree(0) nograph generate(gx gy)"
    if "`variant'" == "all" local lc "lpoly mpg weight , degree(0) nograph generate(gx gy)"
    capture quietly `lc'
    _zq_k lpoly.`variant'.estimation.rc _rc
    _zq_s lpoly.`variant'.estimation.cmd `"`lc'"'
    _zq_k lpoly.`variant'.estimation.bwidth r(bwidth)
    _zq_k lpoly.`variant'.estimation.ngrid r(ngrid)
    _zq_k lpoly.`variant'.estimation.degree r(degree)
    _zq_k lpoly.`variant'.estimation.N r(N)
    _zq_s lpoly.`variant'.estimation.kernel `"`r(kernel)'"'
    foreach v in gx gy {
        local line ""
        forvalues i = 1/`=_N' {
            if !missing(gx[`i']) local line "`line' `=strofreal(`v'[`i'], "%21.17g")'"
        }
        file write zq `"A|lpoly.`variant'.estimation.`v'|`line'"' _n
    }
    local pc = cond("`variant'" == "all", "twoway lpoly mpg weight , degree(0)", "twoway lpoly mpg weight if foreign==1, degree(0)")
    quietly sysuse auto, clear
    _zq_plot lpoly.`variant'.plotted `"`pc'"'

    * lpolyci: the drawn band.
    local pc = cond("`variant'" == "all", "twoway lpolyci mpg weight , degree(0)", "twoway lpolyci mpg weight if foreign==1, degree(0)")
    quietly sysuse auto, clear
    _zq_plot lpolyci.`variant' `"`pc'"'
}
file close zq

python:
import json, os
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


NOTES = {
    "lfit": ("Stata draws the line only over the OBSERVED x range of the "
             "estimation sample, so both the coefficients and the endpoints "
             "change with the qualifier."),
    "lpoly": ("lpoly\x27s rule-of-thumb bandwidth is computed from the "
              "estimation sample, so it changes with the qualifier.  Grid "
              "points with no data inside the kernel window carry a MISSING "
              "fit and are not plotted, so on the subset the drawn curve is "
              "shorter than the grid and stops well short of the subset\x27s "
              "largest weight."),
    "lpolyci": ("The lpolyci serset does NOT use the (fit, lower, upper, x) "
                "column order of lfitci/qfitci/fpfitci; its columns are "
                "identified by their values: x is the column with the largest "
                "maximum (the weight range), the fit is the first other "
                "column, and of the remaining two the one with the smaller "
                "maximum is the lower bound.  A band point is "
                "degenerate where upper - lower <= 1e-5 * max(1, |fit|)."),
}
work = G("ZQ_WORK")
K, A = {}, {}
with open(os.path.join(work, "zq_records.txt"), encoding="utf-8") as fh:
    for ln in fh:
        kind, key, val = ln.rstrip("\n").split("|", 2)
        if kind == "K":
            K[key] = None if val.strip() == "." else float(val)
        elif kind == "S":
            K[key] = val
        else:
            A[key] = [None if w == "." else float(w) for w in val.split()]


def num(v):
    if isinstance(v, float) and v == int(v) and abs(v) < 1e15:
        return int(v)
    return v


def k(key):
    return num(K[key])


def mm(name, xs, out):
    vals = [v for v in xs if v is not None]
    out[name + "_min"] = num(min(vals))
    out[name + "_max"] = num(max(vals))


def plotted(prefix, names, keep):
    """The serset columns of <prefix>, rows where column keep is set."""
    cols = [A[prefix + ".c%d" % j] for j in range(1, len(names) + 1)]
    rows = [i for i in range(len(cols[0])) if cols[keep][i] is not None]
    out = {"n_points": len(rows), "sample_index": list(range(1, len(rows) + 1)),
           "serset_rc": k(prefix + ".serset_rc"), "rc": k(prefix + ".rc"),
           "cmd": K[prefix + ".cmd"]}
    for name, col in zip(names, cols):
        out[name] = [col[i] for i in rows]
        mm(name, out[name], out)
    return out


def headline(layer, paths):
    h = {}
    for p in paths:
        h[p] = {}
        for v in ("all", "foreign1"):
            o = layer[v]
            for part in p.split("."):
                o = o[part]
            h[p][v] = o
    return h


VARIANTS = ("all", "foreign1")
layers = {"lfit": {"mapper": "map_lfit", "note": NOTES["lfit"]},
          "lpoly": {"mapper": "map_lpoly", "note": NOTES["lpoly"]},
          "lpolyci": {"mapper": "map_lpolyci", "note": NOTES["lpolyci"]}}
for v in VARIANTS:
    reg = {"cmd": K["lfit.%s.regress.cmd" % v]}
    for f in ("N", "df_r", "slope", "intercept", "se_slope", "se_cons",
              "rmse", "r2", "x_min", "x_max", "fit_at_x_min", "fit_at_x_max"):
        reg[f] = k("lfit.%s.regress.%s" % (v, f))
    # The lfit serset is (fit, x).
    p = plotted("lfit.%s.plotted" % v, ("fit", "fit_x"), 1)
    lp = {key: p[key] for key in ("n_points", "sample_index", "serset_rc",
                                  "rc", "cmd", "fit_x", "fit_x_min",
                                  "fit_x_max", "fit", "fit_min", "fit_max")}
    layers["lfit"][v] = {"regress": reg, "plotted": lp}

    e = "lpoly.%s.estimation." % v
    gx, gy = A[e + "gx"], A[e + "gy"]
    rows = [i for i in range(len(gx)) if gy[i] is not None]
    xs, ys = [gx[i] for i in rows], [gy[i] for i in rows]
    med = len(rows) // 2
    est = {"cmd": K[e + "cmd"], "rc": k(e + "rc"), "bwidth": k(e + "bwidth"),
           "ngrid": k(e + "ngrid"),
           "degree": k(e + "degree"), "N": k(e + "N"), "kernel": K[e + "kernel"],
           "n_grid_points_with_missing_fit": len(gx) - len(rows),
           "idx_median": med, "x_at_first": num(xs[0]),
           "fit_at_first": num(ys[0]), "x_at_median": num(xs[med - 1]),
           "fit_at_median": num(ys[med - 1]), "x_at_last": num(xs[-1]),
           "fit_at_last": num(ys[-1]), "n_points": len(rows),
           "sample_index": list(range(1, len(rows) + 1)), "lpoly_x": xs}
    mm("lpoly_x", xs, est)
    est["lpoly_y"] = ys
    mm("lpoly_y", ys, est)
    # The lpoly serset is (fit, x); a grid point with a missing fit is not drawn.
    p = plotted("lpoly.%s.plotted" % v, ("lp_y", "lp_x"), 0)
    lp = {key: p[key] for key in ("n_points", "sample_index", "serset_rc",
                                  "rc", "cmd", "lp_x", "lp_x_min", "lp_x_max",
                                  "lp_y", "lp_y_min", "lp_y_max")}
    layers["lpoly"][v] = {"estimation": est, "plotted": lp}

    pre = "lpolyci.%s" % v
    cols = [A[pre + ".c%d" % j] for j in range(1, 5)]
    x_col = max(range(4), key=lambda j: max(c for c in cols[j] if c is not None))
    rest = [j for j in range(4) if j != x_col]
    fit_col = rest[0]
    lo_col, hi_col = sorted(rest[1:], key=lambda j: max(
        c for c in cols[j] if c is not None))
    grid = [i for i in range(len(cols[x_col])) if cols[x_col][i] is not None]
    X = [cols[x_col][i] for i in grid]
    F = [cols[fit_col][i] for i in grid]
    L = [cols[lo_col][i] for i in grid]
    U = [cols[hi_col][i] for i in grid]

    def degen(i):
        return U[i] - L[i] <= 1e-5 * max(1.0, abs(F[i]))

    fitted = [i for i in range(len(grid)) if F[i] is not None]
    ci = [i for i in fitted if L[i] is not None and U[i] is not None]
    wide = max(ci, key=lambda i: U[i] - L[i])

    def point(i):
        return {"x": X[i], "fit": F[i], "lower": L[i], "upper": U[i],
                "band_is_degenerate": bool(L[i] is not None and degen(i))}

    layers["lpolyci"][v] = {
        "cmd": K[pre + ".cmd"], "level": int(G("ZQ_LEVEL")),
        "serset_column_roles": {"fit": "c%d" % (fit_col + 1),
                                "x": "c%d" % (x_col + 1),
                                "lower": "c%d" % (lo_col + 1),
                                "upper": "c%d" % (hi_col + 1)},
        "n_grid_rows": len(grid), "n_fitted_points": len(fitted),
        "n_points_with_a_ci": len(ci),
        "n_points_with_a_nondegenerate_ci": sum(1 for i in ci if not degen(i)),
        "grid_x": X, "fit": F, "lower": L, "upper": U,
        "endpoints": {"at_first_fitted_x": point(fitted[0]),
                      "at_last_fitted_x": point(fitted[-1])},
        "widest_band_point": {"x": X[wide], "fit": F[wide], "lower": L[wide],
                              "upper": U[wide], "width": U[wide] - L[wide]},
        "serset_rc": k(pre + ".serset_rc"), "rc": k(pre + ".rc")}

HEAD = {"lfit": ["regress.slope", "regress.intercept", "regress.fit_at_x_min",
                 "regress.fit_at_x_max"],
        "lpoly": ["estimation.bwidth", "estimation.ngrid",
                  "estimation.fit_at_first", "estimation.fit_at_median",
                  "estimation.fit_at_last", "estimation.x_at_last"],
        "lpolyci": ["n_fitted_points", "n_points_with_a_nondegenerate_ci",
                    "endpoints.at_last_fitted_x.x", "widest_band_point.x",
                    "widest_band_point.lower", "widest_band_point.upper"]}
same = []
for name, paths in HEAD.items():
    h = headline(layers[name], paths)
    layers[name]["headline"] = h
    layers[name]["differs_from_unqualified"] = any(
        r["all"] != r["foreign1"] for r in h.values())
    if not layers[name]["differs_from_unqualified"]:
        same.append(name)
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
meta = {"stata_version": G("ZQ_VERSION"), "born_date": G("ZQ_BORN"),
        "dash_commit": commit, "extracted": G("ZQ_WHEN"),
        "source": "scripts/extract_qualified_stat_truth.do",
        "work_package": "WP-02",
        "why": ("Mappers that build their own ColumnDataSource from a computed "
                "grid must mask the INPUT arrays before the statistic is "
                "computed; this fixture records what Stata itself produces "
                "for the subset."),
        "dataset": "sysuse auto", "N_all": k("all.N_rows"),
        "N_foreign1": k("foreign1.N_rows"), "y": "mpg", "x": "weight",
        "qualifier": "foreign==1",
        "variant_keys": {"all": "no qualifier -- the whole dataset",
                         "foreign1": "if foreign==1 -- the foreign cars"},
        "c_level": int(G("ZQ_LEVEL")),
        "precision": ("Numbers are written with Stata\x27s %21.17g so "
                      "doubles round-trip.  Serset values the graph engine "
                      "stored as floats (the lfit line, the lpolyci bounds) "
                      "compare to about 1e-6 relative."),
        "layers_whose_qualified_answer_is_identical": same}
out = {"_meta": meta, "layers": layers}
with open(G("ZQ_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1)
    fh.write("\n")
for name in ("git_head.txt", "zq.gph"):
    try:
        os.remove(os.path.join(work, name))
    except OSError:
        pass
print("wrote", G("ZQ_OUT"))
end
