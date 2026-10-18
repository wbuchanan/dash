*! extract_kpi_truth.do -- WP-31 S60 (GAPS3 K3): measure the KPI
*! statistics against Stata's own r() results on sysuse auto: summarize mpg
*! (and , detail) whole and if foreign==1 (kpi_stats, with _pctile and
*! tabstat cross-checks), the plan's anchor mean, a brush of rows 1/30,
*! summarize's r(N) against -count-, the type-2 percentile rule checked by
*! hand against type 7 and -centile-, the moment definitions, what each
*! distinct-count command leaves in r() (dcount, with inspect's cap and a
*! 200,000-value scale probe), Stata's rule for Unicode variable names and
*! what dash does with one.  The dash runs write their pages in the probe
*! directory; the fixture names them by basename.
*!
*! Output: test/fixtures/kpi_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_kpi_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zk_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zk_bad' {
    display as error "extract_kpi_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zk_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zk_rc' | _rc {
    local _zk_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_kpi_truth.do: `_zk_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZK_REPO "`repo'"
global ZK_OUT "${ZK_REPO}/test/fixtures/kpi_truth.json"

adopath ++ "${ZK_REPO}"
quietly do "${ZK_REPO}/dash_parse.mata"
quietly do "${ZK_REPO}/dash.ado"
global dash_nobrowser 1

local work "`c(tmpdir)'dash_kpi_probe"
capture mkdir "`work'"
global ZK_WORK "`work'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_kpi_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

quietly shell git -C "${ZK_REPO}" rev-parse HEAD > "${ZK_WORK}/git_head.txt"
global ZK_VERSION "`c(stata_version)'"
global ZK_BORN "`c(born_date)'"
global ZK_WHEN "`c(current_date)' `c(current_time)'"

* What dash does with Unicode variable names: run here, before the python
* block, since dash runs Python itself.  Every path is in the probe
* directory; the fixture names the files by basename.
sysuse auto, clear
* The names come from Python, written as escapes so this file stays
* ASCII.
python:
from sfi import Macro
Macro.setGlobal("ZK_CAFE", "caf\u00e9")
Macro.setGlobal("ZK_CJK", "\u65e5\u672c\u8a9e")
end
local cafe "${ZK_CAFE}"
local cjk "${ZK_CJK}"
generate `cafe' = mpg
label variable `cafe' "Unicode named mpg"
generate `cjk' = weight
capture program drop _zk_vlprobe
program define _zk_vlprobe
    version 16.0
    syntax varlist
    global ZK_VL "`varlist'"
end
global ZK_VL ""
capture noisily _zk_vlprobe `cafe' weight
global ZK_VL_RC = _rc
foreach f in ctl uni_y uni_both {
    capture erase "${ZK_WORK}/`f'.html"
}
capture noisily dash scatter mpg weight, saving("${ZK_WORK}/ctl.html")
global ZK_CTL_RC = _rc
capture noisily dash scatter `cafe' weight, saving("${ZK_WORK}/uni_y.html")
global ZK_UNIY_RC = _rc
capture confirm file "${ZK_WORK}/uni_y.html"
global ZK_UNIY_FILE = _rc
capture noisily dash scatter `cafe' `cjk', saving("${ZK_WORK}/uni_both.html")
global ZK_UNIB_RC = _rc
capture confirm file "${ZK_WORK}/uni_both.html"
global ZK_UNIB_FILE = _rc
capture noisily dash kpi mean(`cafe'), title("Unicode KPI") name(kuni)
global ZK_KPI_RC = _rc
global ZK_LEVEL "`c(level)'"
sysuse auto, clear

python:
import json, math, os
from fractions import Fraction
from sfi import Data, Macro, Matrix, Missing, Scalar, SFIToolkit


def G(k):
    return Macro.getGlobal(k)


def miss(v):
    return v is None or Missing.isMissing(v)


def num(v):
    """A Stata double as JSON: None for missing, an int when integral."""
    if miss(v):
        return None
    if float(v).is_integer() and abs(v) < 2 ** 53:
        return int(v)
    return float(v)


def ok(cmd):
    """Run *cmd* quietly under capture; True when its rc was 0."""
    SFIToolkit.stata("capture quietly " + cmd)
    return Scalar.getValue("c(rc)") == 0


def rc_of(cmd):
    SFIToolkit.stata("capture quietly " + cmd)
    return int(Scalar.getValue("c(rc)"))


def run(cmd):
    ok(cmd)


def r(name):
    return Scalar.getValue("r(%s)" % name)


def cv(cmd, value):
    return {"cmd": cmd, "value": num(value)}


def show(v):
    v = num(v)
    return "." if v is None else str(v)


def listing(kind):
    """r(scalars) as name=value ..., r(macros) as name={text} ..."""
    names = SFIToolkit.macroExpand((chr(96) + ":r(%s)" + chr(39)) % kind).split()
    if not names:
        return "(none)"
    if kind == "scalars":
        return " ".join("%s=%s" % (n, show(r(n))) for n in names)
    return " ".join("%s={%s}" % (n, SFIToolkit.macroExpand(chr(96) + "r(%s)" % n + chr(39)))
                    for n in names)


def r_listing(cmd):
    run(cmd)
    out = {"cmd": cmd}
    for kind in ("scalars", "macros", "matrices"):
        out["r_" + kind] = listing(kind) if kind != "matrices" else (
            " ".join(SFIToolkit.macroExpand((chr(96) + ":r(matrices)" + chr(39))).split())
            or "(none)")
    return out


def sorted_mpg(cond):
    """mpg's non-missing values, sorted, where *cond* (a Stata if) holds."""
    run("sysuse auto, clear")
    if cond:
        run("keep if " + cond)
    run("drop if missing(mpg)")
    return sorted(Data.get("mpg"))


def main():
    out = {"_meta": {}}

    # anchor: the plan's mean(mpg) if foreign==1.
    run("sysuse auto, clear")
    run("summarize mpg if foreign==1")
    mean1, sum1, n1 = r("mean"), r("sum"), r("N")
    shown = SFIToolkit.formatValue(mean1, "%9.4f").strip()
    frac = Fraction(int(sum1), int(n1))
    out["anchor"] = {
        "claim_in_plan": "mean(mpg) if foreign==1 = 24.7727",
        "confirmed": shown == "24.7727",
        "full_precision": cv("summarize mpg if foreign==1 -> r(mean), "
                             "%20.17g", mean1),
        "as_displayed_9_4f": {"cmd": "summarize mpg if foreign==1 -> "
                              "r(mean), %9.4f", "value": shown},
        "exact_rational": "%d/%d" % (frac.numerator, frac.denominator)}

    # kpi_stats: summarize mpg (and , detail) whole and if foreign==1.
    stats = {}
    checks = {"summarize_detail_matches_pctile": True,
              "tabstat_matches_summarize": True}
    for key, scope, q in (("all", "unconditional", ""),
                          ("foreign1", "if foreign==1", " if foreign==1")):
        summ, det = "summarize mpg" + q, "summarize mpg" + q + ", detail"
        run(summ)
        s = {k: r(k) for k in ("mean", "sum", "N", "min", "max", "sd",
                               "Var", "sum_w")}
        run(det)
        d = {k: r(k) for k in ("p1", "p5", "p10", "p25", "p50", "p75", "p90",
                               "p95", "p99", "skewness", "kurtosis")}
        e = {"_scope": scope,
             "mean": cv(summ + " -> r(mean)", s["mean"]),
             "sum": cv(summ + " -> r(sum)", s["sum"]),
             "count": cv(summ + " -> r(N)", s["N"]),
             "min": cv(summ + " -> r(min)", s["min"]),
             "max": cv(summ + " -> r(max)", s["max"]),
             "median": cv(det + " -> r(p50)", d["p50"]),
             "sd": cv(summ + " -> r(sd)", s["sd"]),
             "p25": cv(det + " -> r(p25)", d["p25"]),
             "p50": cv(det + " -> r(p50)", d["p50"]),
             "p75": cv(det + " -> r(p75)", d["p75"]),
             "var": cv(summ + " -> r(Var)", s["Var"]),
             "iqr": cv(det + " -> r(p75)-r(p25)", d["p75"] - d["p25"]),
             "skewness": cv(det + " -> r(skewness)", d["skewness"]),
             "cv": cv(summ + " -> r(sd)/r(mean)", s["sd"] / s["mean"])}
        e["_also"] = {"sum_w": cv(summ + " -> r(sum_w)", s["sum_w"]),
                      "kurtosis": cv(det + " -> r(kurtosis)", d["kurtosis"])}
        for p in ("p1", "p5", "p10", "p90", "p95", "p99"):
            e["_also"][p] = cv(det + " -> r(%s)" % p, d[p])
        pc = "_pctile mpg%s, p(25 50 75)" % q
        run(pc)
        xc = {}
        for i, p in enumerate(("p25", "p50", "p75")):
            xc["pctile_" + p] = cv(pc + " -> r(r%d)" % (i + 1),
                                   r("r%d" % (i + 1)))
            if xc["pctile_" + p]["value"] != num(d[p]):
                checks["summarize_detail_matches_pctile"] = False
        ts = ("tabstat mpg%s, stat(mean sum count min max median sd var iqr "
              "skewness cv p25 p75) save" % q)
        run(ts)
        col = [row[0] for row in Matrix.get("r(StatTotal)")]
        for name, i in (("mean", 0), ("sd", 6), ("variance", 7), ("iqr", 8),
                        ("skewness", 9), ("cv", 10)):
            xc["tabstat_" + name] = cv(ts + " -> r(StatTotal)", col[i])
        for name, want in (("mean", s["mean"]), ("sd", s["sd"]),
                           ("variance", s["Var"]),
                           ("iqr", d["p75"] - d["p25"]),
                           ("skewness", d["skewness"]),
                           ("cv", s["sd"] / s["mean"])):
            got = xc["tabstat_" + name]["value"]
            if abs(got - want) > 1e-12 * max(1.0, abs(want)):
                checks["tabstat_matches_summarize"] = False
        xc["note_cv_last_bit"] = (
            "tabstat's cv can differ from r(sd)/r(mean) in the 16th "
            "significant digit only; either is correct to double precision. "
            "Compare cv with a relative tolerance of 1e-12, not for "
            "equality.")
        e["_cross_checks"] = xc
        stats[key] = e
    out["kpi_stats"] = stats

    # brush: the first thirty rows.
    run("sysuse auto, clear")
    first30 = " ".join(str(num(v)) for v in Data.get("mpg")[:30])
    run("summarize mpg in 1/30")
    out["brush"] = {
        "_scope": ("in 1/30: the rows a brush of the first thirty rows of "
                   "sysuse auto selects -- indices 0..29 of "
                   "test/fixtures/data/auto.csv, which holds sysuse auto's "
                   "mpg and weight in Stata's row order (its first thirty "
                   "mpg values are the ones this run read: %s)" % first30),
        "measured": ("each command below run by "
                     "scripts/extract_kpi_truth.do and its r() read straight "
                     "after it. The mean agrees with kpi_pctile_truth.json's "
                     "in30 scope."),
        "mean": cv("sysuse auto ; summarize mpg in 1/30 -> r(mean)",
                   r("mean")),
        "count": cv("sysuse auto ; summarize mpg in 1/30 -> r(N)", r("N"))}

    # count_semantics: summarize's r(N) against -count-.
    cs = {"warning": (
        "'count' is ambiguous. summarize's r(N) counts observations with a "
        "NON-MISSING value of the variable; the -count- command counts "
        "observations that satisfy if/in regardless of missingness. They "
        "agree for mpg (no missing) but will not agree for rep78 (5 "
        "missing). dash kpi count() uses summarize r(N), i.e. the "
        "non-missing count.")}
    for key, cmd, what in (
            ("all_summarize_r_N", "summarize mpg", "N"),
            ("all_count_command", "count", "N"),
            ("all_count_nonmissing", "count if !missing(mpg)", "N"),
            ("foreign1_summarize_r_N", "summarize mpg if foreign==1", "N"),
            ("foreign1_count_command", "count if foreign==1", "N"),
            ("foreign1_count_nonmissing",
             "count if foreign==1 & !missing(mpg)", "N")):
        run(cmd)
        cs[key] = cv(cmd + " -> r(N)", r(what))
    run("count")
    cs["dataset_N"] = cv("sysuse auto, clear ; count", r("N"))
    out["count_semantics"] = cs

    # percentile_definition: the type-2 rule by hand, and the two rules
    # that are not Stata's.
    by_hand, type7, cent = {}, {}, {}
    hand_ok = True
    for key, cond, q in (("all", "", ""),
                         ("foreign1", "foreign==1", " if foreign==1")):
        x = sorted_mpg(cond)
        n = len(x)
        block = {"N_nonmissing": cv(
            ("keep if %s ; " % cond if cond else "keep ; ")
            + "drop if missing(mpg) ; count", n)}
        st = stats[key]
        for p in (25, 50, 75):
            j = n * p / 100.0
            if j == int(j):
                j = int(j)
                v = (x[j - 1] + x[j]) / 2.0
                how = ("j=N*p/100=%d is integer -> (x[%d]+x[%d+1])/2 = "
                       "(%s+%s)/2" % (j, j, j, show(x[j - 1]), show(x[j])))
            else:
                k = int(math.ceil(j))
                v = x[k - 1]
                how = "j=N*p/100=%g not integer -> x[ceil(j)]=x[%d]" % (j, k)
            want = st["p%d" % p]
            agrees = num(v) == want["value"]
            hand_ok = hand_ok and agrees
            block["p%d" % p] = {"stata": dict(want),
                                "by_hand": cv(how, v), "agrees": agrees}
        by_hand[key] = block
        for p in (25, 50, 75):
            h = (n - 1) * p / 100.0
            lo = int(math.floor(h))
            t7 = x[lo] + (h - lo) * (x[min(lo + 1, n - 1)] - x[lo])
            type7["%s_p%d" % (key, p)] = (t7, h)
        run("sysuse auto, clear")
        cc = "centile mpg%s, centile(25 50 75)" % q
        run(cc)
        for i, p in enumerate((25, 50, 75)):
            cent["%s_p%d" % (key, p)] = cv(cc + " -> r(c_%d)" % (i + 1),
                                           r("c_%d" % (i + 1)))
    t7 = {"note": (
        "numpy.percentile / pandas .quantile() / .median() default to "
        "linear interpolation (Hyndman-Fan type 7) and DISAGREE with Stata. "
        "dash_render.py and the CustomJS KPI code must reproduce the Stata "
        "rule, not the pandas one.")}
    for key in ("all", "foreign1"):
        v, h = type7["%s_p75" % key]
        t7["%s_p75_stata" % key] = dict(stats[key]["p75"])
        t7["%s_p75_type7" % key] = cv(
            "numpy/pandas default: x[floor(h)] + frac*(x[floor(h)+1]-"
            "x[floor(h)]), h=(N-1)p/100=%g" % h, v)
    t7["all_p25_agrees_by_luck"] = (
        num(type7["all_p25"][0]) == stats["all"]["p25"]["value"])
    t7["medians_agree_here"] = all(
        num(type7["%s_p50" % k][0]) == stats[k]["p50"]["value"]
        for k in ("all", "foreign1"))
    centile = {"note": (
        "-centile- uses a DIFFERENT, interpolating definition and is not "
        "the one summarize,detail uses. Never use centile to produce a dash "
        "KPI percentile.")}
    centile.update(cent)
    out["percentile_definition"] = {
        "definition": (
            "Stata's percentile (summarize, detail; _pctile; pctile; tabstat "
            "p25/p50/p75; egen pctile) is the AVERAGED INVERSE EMPIRICAL "
            "CDF, Hyndman-Fan type 2. With the N non-missing values sorted "
            "x(1) <= ... <= x(N) and j = N*p/100: if j is an integer the "
            "answer is (x(j)+x(j+1))/2, otherwise it is x(ceil(j)). No "
            "interpolation between order statistics other than that "
            "midpoint. Weights change j to the running sum of weights, but "
            "dash passes no weights to its KPI code."),
        "verified_by_hand": by_hand,
        "do_not_use_these": {"numpy_pandas_default_type7": t7,
                             "centile": centile}}

    # moment_definitions.
    x = sorted_mpg("")
    n = len(x)
    xbar = sum(x) / n
    m2 = sum((v - xbar) ** 2 for v in x) / n
    m3 = sum((v - xbar) ** 3 for v in x) / n
    hand = m3 / m2 ** 1.5
    st, sf = stats["all"], stats["foreign1"]
    rel = abs(hand - st["skewness"]["value"]) / abs(st["skewness"]["value"])
    out["moment_definitions"] = {
        "variance_and_sd": {
            "rule": ("summarize r(Var) and r(sd) use the N-1 divisor (sample "
                     "variance). pandas .var()/.std() default to ddof=1 and "
                     "therefore agree; numpy .var()/.std() default to ddof=0 "
                     "and do NOT."),
            "measured": cv("summarize mpg -> r(Var) (divisor N-1)",
                           st["var"]["value"])},
        "skewness": {
            "rule": ("summarize, detail r(skewness) is the BIASED / "
                     "population moment ratio m3 / m2^1.5, where m_k = "
                     "(1/N)*sum((x-xbar)^k) with the N divisor - not the "
                     "sample-corrected g1 that scipy.stats.skew(bias=False) "
                     "or Excel's SKEW() return. scipy.stats.skew(x) with its "
                     "default bias=True matches Stata."),
            "stata": dict(st["skewness"]),
            "hand_computed_m3_over_m2_1p5": cv(
                "m3/m2^1.5 with m_k = mean((x-xbar)^k), N divisor", hand),
            "agree_to": ("%.1e relative (the hand computation accumulates "
                         "in a different order)" % rel)},
        "iqr": {
            "rule": ("IQR is simply p75 - p25 under the same type-2 "
                     "percentile rule; tabstat's iqr agrees exactly."),
            "all": dict(st["iqr"]), "foreign1": dict(sf["iqr"])},
        "cv": {
            "rule": ("Coefficient of variation is r(sd)/r(mean) - the "
                     "sample sd over the mean, NOT a percentage. tabstat's cv "
                     "statistic returns the same number."),
            "all": dict(st["cv"]), "foreign1": dict(sf["cv"])}}

    # dcount: what each command returns, on rep78, make and mpg.
    run("sysuse auto, clear")

    def groups(var, opt=""):
        run("capture drop __zk_g")
        run("egen __zk_g = group(%s)%s" % (var, opt))
        run("summarize __zk_g, meanonly")
        v = 0 if miss(r("N")) or r("N") == 0 else r("max")
        run("drop __zk_g")
        return num(v)

    truth = {}
    uniq_ok = True
    what = {}
    for var in ("rep78", "make"):
        truth[var + "_distinct_nonmissing"] = groups(var)
        truth[var + "_distinct_including_missing"] = groups(var, ", missing")
        run("count if missing(%s)" % var)
        truth[var + "_n_missing"] = cv("count if missing(%s) -> r(N)" % var,
                                       r("N"))
        w = {}
        w["codebook"] = r_listing("codebook %s" % var)
        lv = r_listing("levelsof %s" % var)
        lv["r_r"] = cv("levelsof %s -> r(r)" % var, r("r"))
        run("levelsof %s, missing" % var)
        lv["r_r_with_missing_option"] = cv(
            "levelsof %s, missing -> r(r)" % var, r("r"))
        w["levelsof"] = lv
        w["egen_group"] = {
            "cmd": "egen __grp = group(%s) ; summarize __grp, meanonly -> "
                   "r(max)" % var, "value": groups(var),
            "with_missing_option": {
                "cmd": "egen __grpm = group(%s), missing ; summarize __grpm, "
                       "meanonly -> r(max)" % var,
                "value": groups(var, ", missing")}}
        w["inspect"] = r_listing("inspect %s" % var)
        tb = r_listing("tabulate %s" % var)
        tb["r_r"] = cv("tabulate %s -> r(r)" % var, r("r"))
        w["tabulate"] = tb
        run("capture drop __zk_t")
        run("egen __zk_t = tag(%s)" % var)
        run("count if __zk_t==1 & !missing(%s)" % var)
        w["egen_tag"] = cv("egen __tg = tag(%s) ; count if __tg==1 & "
                           "!missing(%s) -> r(N)" % (var, var), r("N"))
        run("drop __zk_t")
        if var == "make":
            vals = [v for v in Data.get(var) if v != ""]
            mcmd = "mata: rows(uniqrows(sort(non-empty make,1)))"
        else:
            vals = [v for v in Data.get(var) if not miss(v)]
            mcmd = "mata: rows(uniqrows(non-missing rep78))"
        Macro.setGlobal("ZK_MV", var)
        run('mata: st_numscalar("__zk_u", rows(uniqrows('
            + ('select(st_sdata(., st_global("ZK_MV")), st_sdata(., '
               'st_global("ZK_MV")) :!= "")' if var == "make" else
               'select(st_data(., st_global("ZK_MV")), st_data(., '
               'st_global("ZK_MV")) :< .)') + ')))')
        mu = num(Scalar.getValue("__zk_u"))
        w["mata_uniqrows"] = cv(mcmd, mu)
        uniq_ok = uniq_ok and (
            mu == truth[var + "_distinct_nonmissing"] == len(set(vals)))
        what[var] = w
    truth["mpg_distinct_nonmissing"] = cv(
        "sysuse auto ; egen g = group(mpg) ; summarize g, meanonly -> r(max)",
        groups("mpg"))
    run("levelsof mpg")
    truth["mpg_distinct_levelsof"] = cv("sysuse auto ; levelsof mpg -> r(r)",
                                        r("r"))
    run("replace mpg = . in 1/5")
    truth["mpg_missing_in_1_5_distinct_nonmissing"] = cv(
        "sysuse auto ; replace mpg = . in 1/5 ; egen g = group(mpg) ; "
        "summarize g, meanonly -> r(max)", groups("mpg"))
    run("levelsof mpg, missing")
    truth["mpg_missing_in_1_5_distinct_including_missing"] = cv(
        "sysuse auto ; replace mpg = . in 1/5 ; levelsof mpg, missing -> "
        "r(r)", r("r"))
    truth["mpg_measured"] = (
        "egen group() with summarize r(max) is the method dash.ado's "
        "_dash_kpi uses for dcount.")
    truth["note"] = (
        "'distinct' here means distinct non-missing values, which is what "
        "codebook, levelsof, egen group() and pandas .nunique() all mean by "
        "default, and what a JavaScript Set over the non-null values gives.")
    cap = {}
    for k in (5, 50, 98, 99, 100, 101, 500):
        run("clear")
        run("set obs %d" % k)
        run("generate long x = _n")
        run("inspect x")
        ins = show(r("N_unique"))
        run("levelsof x")
        lev = show(r("r"))
        cap["k%d" % k] = "inspect=%s levelsof=%s egengroup=%s" % (
            ins, lev, show(groups("x")))
    run("clear")
    run("set obs 200000")
    run("generate long x = _n")
    run('generate str12 s = "s" + string(_n, "%11.0f")')
    scale = {"setup": ("200,000 observations, 200,000 distinct values; a "
                       "long numeric x and a str12 s."),
             "c_macrolen": cv("c(macrolen)", Scalar.getValue("c(macrolen)"))}
    scale["tabulate"] = {"cmd": "tabulate x  (200,000 distinct)",
                         "value": "rc=%d" % rc_of("tabulate x")}
    for key, var, what_ in (("levelsof_numeric", "x", "levelsof x  (200,000 "
                             "distinct)"),
                            ("levelsof_string", "s", "levelsof s  (200,000 "
                             "distinct str12)")):
        rc = rc_of("levelsof %s" % var)
        scale[key] = {"cmd": what_,
                      "value": "rc=%d r(r)=%s" % (rc, show(r("r")))}
    scale["egen_group_numeric"] = cv(
        "egen __g = group(x) ; summarize __g, meanonly -> r(max)",
        groups("x"))
    scale["egen_group_string"] = cv(
        "egen __gs = group(s) ; summarize __gs, meanonly -> r(max)",
        groups("s"))
    run("inspect x")
    scale["inspect_numeric"] = {"cmd": "inspect x -> r(N_unique)",
                                "value": show(r("N_unique"))}
    out["dcount"] = {
        "truth": truth, "what_each_command_returns": what,
        "inspect_cap": {"finding": (
            "r(N_unique) from -inspect- is exact up to 99 distinct values "
            "and system missing from 100 upward."), "probes": cap},
        "scale": scale}

    # unicode_names: Stata's rule for a variable name.
    run("sysuse auto, clear")
    names = ["caf\u00e9", "\u03b1\u03b2\u03b3", "\u65e5\u672c\u8a9e",
             "na\u00efve", "_\u00fcnder", "\u00f1", "\u03a9mega",
             "\u00fcber2", "\uff33\uff34\uff21\uff34\uff21", "x\U0001F600",
             "caf\u00e9_2", "Stra\u00dfe", "\uff17seven", "2caf\u00e9"]
    acc, rej = [], []
    for nm in names:
        cmd = "generate %s = _n" % nm
        rc = rc_of(cmd)
        e = {"name": nm, "cmd": cmd, "rc": rc,
             "detail": "rc=%d bytes=%d chars=%d"
             % (rc, len(nm.encode("utf-8")), len(nm))}
        (acc if rc == 0 else rej).append(e)
    lim = {}
    for key, nm in (("cjk_32_chars_96_bytes", "\u65e5" * 32),
                    ("cjk_33_chars_99_bytes", "\u65e5" * 33),
                    ("ascii_32_chars", ("abcdefghij" * 4)[:32]),
                    ("ascii_33_chars", ("abcdefghij" * 4)[:33])):
        rc = rc_of("generate %s = _n" % nm)
        lim[key] = {"cmd": "generate <%d-char name> = _n" % len(nm),
                    "value": "rc=%d bytes=%d chars=%d"
                    % (rc, len(nm.encode("utf-8")), len(nm))}
    lim["conclusion"] = (
        "The 32 limit is counted in characters (ustrlen), not bytes: a "
        "32-character / 96-byte CJK name is accepted and a 33-character "
        "name is rejected with rc 198, exactly like ASCII.")
    run("describe, varlist")
    varlist = SFIToolkit.macroExpand(chr(96) + "r(varlist)" + chr(39))
    work = G("ZK_WORK")

    def has(fname, needle):
        try:
            with open(os.path.join(work, fname), encoding="utf-8",
                      errors="replace") as fh:
                return needle in fh.read()
        except OSError:
            return False

    cafe = "caf\u00e9"
    cjk = "\u65e5\u672c\u8a9e"
    out["unicode_names"] = {
        "stata_rules": {
            "summary": (
                "Stata 14+ accepts Unicode letters in variable names. The "
                "rule measured here: the name must start with a Unicode "
                "LETTER or an underscore and may then contain Unicode "
                "letters, ASCII digits and underscores. Length is limited "
                "to 32 CHARACTERS, not 32 bytes."),
            "accepted": acc, "rejected": rej, "length_limit": lim,
            "final_varlist": {"cmd": "describe, varlist -> r(varlist)",
                              "value": varlist}},
        "what_dash_does": {
            "syntax_varlist_accepts_unicode": {
                "cmd": ("program with -version 16.0- and -syntax varlist-: "
                        "_vlprobe %s weight" % cafe),
                "value": "rc=%s varlist=<%s>" % (G("ZK_VL_RC"), G("ZK_VL"))},
            "ascii_control_scatter": {
                "cmd": "dash scatter mpg weight, saving(ctl.html)",
                "value": "rc=" + G("ZK_CTL_RC")},
            "unicode_y_scatter": {
                "cmd": "dash scatter %s weight, saving(uni_y.html)" % cafe,
                "value": "rc=" + G("ZK_UNIY_RC")},
            "unicode_y_html_written": {"cmd": "confirm file uni_y.html",
                                       "value": "rc=" + G("ZK_UNIY_FILE")},
            "unicode_both_axes_scatter": {
                "cmd": "dash scatter %s %s, saving(uni_both.html)"
                % (cafe, cjk), "value": "rc=" + G("ZK_UNIB_RC")},
            "unicode_both_html_written": {
                "cmd": "confirm file uni_both.html",
                "value": "rc=" + G("ZK_UNIB_FILE")},
            "html_evidence": {
                "file": "uni_y.html",
                "column_in_ColumnDataSource": has(
                    "uni_y.html", json.dumps(cafe)),
                "axis_label": has("uni_y.html", "Unicode named mpg"),
                "cjk_column": has("uni_both.html", json.dumps(cjk))},
            "unicode_kpi": {
                "cmd": 'dash kpi mean(%s), title("Unicode KPI") name(kuni)'
                % cafe, "rc": int(G("ZK_KPI_RC"))}}}

    try:
        with open(os.path.join(work, "git_head.txt")) as fh:
            commit = fh.read().strip()
    except OSError:
        commit = ""
    rel_ok = rel < 1e-12
    out["_meta"] = {
        "stata_version": G("ZK_VERSION"), "born_date": G("ZK_BORN"),
        "dash_commit": commit, "extracted": G("ZK_WHEN"),
        "source": "scripts/extract_kpi_truth.do",
        "c_level_default": int(float(G("ZK_LEVEL"))),
        "dataset": "sysuse auto (N=%d)" % cs["dataset_N"]["value"],
        "method": (
            "Every number is Stata's own r() result, read back as a double "
            "immediately after the command that produced it. The command "
            "that produced each number is stored beside it in that entry's "
            "\"cmd\" field. r() contents are enumerated with the "
            ":r(scalars), :r(macros) and :r(matrices) extended macro "
            "functions, so the 'what does this command leave behind' answers "
            "are measured, not remembered."),
        "self_checks": {
            "summarize_detail_matches_pctile":
                checks["summarize_detail_matches_pctile"],
            "tabstat_matches_summarize": checks["tabstat_matches_summarize"],
            "hand_computed_percentile_matches_stata": hand_ok,
            "hand_computed_skewness_matches_stata": rel_ok,
            "mata_uniqrows_matches_egen_group": uniq_ok}}
    order = ["_meta", "anchor", "kpi_stats", "brush", "count_semantics",
             "percentile_definition", "moment_definitions", "dcount",
             "unicode_names"]
    out = {k: out[k] for k in order}
    with open(G("ZK_OUT"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    for f in ("git_head.txt", "ctl.html", "uni_y.html", "uni_both.html"):
        try:
            os.remove(os.path.join(work, f))
        except OSError:
            pass
    print("wrote", G("ZK_OUT"))


main()
end
