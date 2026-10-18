*! extract_kpi_pctile_truth.do -- WP-31 S60 (GAPS3 K3): measure the KPI
*! statistics dash computes against Stata's own r() results: summarize's
*! mean, sum, N, min, max and sd, summarize, detail's Var and skewness,
*! _pctile's percentiles and iqr, and egen group()'s distinct count, on
*! sysuse auto's price, mpg and rep78 under twelve if/in scopes (auto_kpi);
*! _pctile on x = 1..20000 under five scopes (big), on a %td date (dates),
*! counts of a string with blanks (strings), and _pctile x on x = 1..n for
*! each (n, p) of rule_cases.  rule_cases' (n, p) inputs are the committed
*! fixture's (their selection drew a random sample, see
*! _meta.rule_cases_selection), so this run reads them from the fixture it
*! overwrites and re-measures every result.  Stata only: the output is the
*! same before and after dash changes.
*!
*! Output: test/fixtures/kpi_pctile_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_kpi_pctile_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zp_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zp_bad' {
    display as error "extract_kpi_pctile_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zp_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zp_rc' | _rc {
    local _zp_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_kpi_pctile_truth.do: `_zp_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZP_REPO "`repo'"
global ZP_OUT "${ZP_REPO}/test/fixtures/kpi_pctile_truth.json"

adopath ++ "${ZP_REPO}"
quietly do "${ZP_REPO}/dash_parse.mata"
quietly do "${ZP_REPO}/dash.ado"
global dash_nobrowser 1

local work "`c(tmpdir)'dash_kpi_pctile_probe"
capture mkdir "`work'"
global ZP_WORK "`work'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_kpi_pctile_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

quietly shell git -C "${ZP_REPO}" rev-parse HEAD > "${ZP_WORK}/git_head.txt"
global ZP_VERSION "`c(stata_version)'"
global ZP_BORN "`c(born_date)'"
global ZP_WHEN "`c(current_date)' `c(current_time)'"

sysuse auto, clear

python:
import json, os
from sfi import Data, Macro, Missing, Scalar, SFIToolkit


def G(k):
    return Macro.getGlobal(k)


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


def run(cmd):
    ok(cmd)


def miss(v):
    return v is None or Missing.isMissing(v)


def r(name):
    return Scalar.getValue("r(%s)" % name)


def column(var):
    return [num(v) for v in Data.get(var)]


def main():
    """Measure every block and write the fixture.  One top-level
    call: a top-level loop that runs Stata commands confuses the block's
    line reader."""
    fixture = G("ZP_OUT")
    with open(fixture, encoding="utf-8") as fh:
        inputs = [(int(n), str(p)) for n, p, _ in json.load(fh)["rule_cases"]]

    out = {"_meta": {}}
    out["auto"] = {v: column(v) for v in ("price", "mpg", "weight", "foreign",
                                          "rep78")}

    SCOPES = [("all", "", ""), ("f1", "foreign==1", ""), ("f0", "foreign==0", ""),
              ("in50", "", "1/50"), ("rng", "inrange(weight, 2000, 3500)", ""),
              ("sld", "mpg >= 22", ""),
              ("f0rng", "foreign==0 & inrange(weight, 2000, 3500)", ""),
              ("in50sld", "mpg >= 22", "1/50"), ("in30", "", "1/30"),
              ("f1in30", "foreign==1", "1/30"),
              ("empty", "foreign==0 & foreign==1", ""),
              ("one", "mpg >= 22", "1/1")]

    PCTS = ["25", "50", "75", "0.5", "2.5", "10", "12.5", "33.3", "66.7", "90",
            "97.5", "99.5", "99.9", "0.001"]

    rows = []
    for var in ("price", "mpg", "rep78"):
        for scope, ifx, inx in SCOPES:
            q = " ".join(x for x in (("if " + ifx) if ifx else "",
                                     ("in " + inx) if inx else "") if x)
            sp = (" " + q) if q else ""
            # Before a comma the qualifier reads as 'if' 'in' did: a space
            # before the comma when there is no in.
            qc = (("if " + ifx + " ") if ifx else "") + (
                ("in " + inx) if inx else "")

            def add(stat, cmd, value):
                rows.append({"var": var, "scope": scope, "if": ifx, "in": inx,
                             "stat": stat, "cmd": cmd, "value": num(value)})

            def pct(ps):
                done = ok("_pctile %s %s, p(%s)" % (var, qc, ps))
                return [r("r%d" % (i + 1)) if done else None
                        for i in range(len(ps.split()))]

            summ = "summarize %s%s" % (var, sp)
            run(summ)
            s = {k: r(k) for k in ("mean", "sum", "N", "min", "max", "sd")}
            run("summarize %s %s, detail" % (var, qc))
            dvar, dskew = r("Var"), r("skewness")
            run("capture drop __zp_g")
            run("egen __zp_g = group(%s)%s" % (var, sp))
            run("summarize __zp_g, meanonly")
            dc = 0 if miss(r("N")) or r("N") == 0 else r("max")
            run("drop __zp_g")

            add("mean", summ + " -> r(mean)", s["mean"])
            add("sum", summ + " -> r(sum)", s["sum"])
            add("count", summ + " -> r(N)", s["N"])
            add("dcount", "egen group(%s)%s -> max (= tabulate r(r))" % (var, sp),
                dc)
            add("min", summ + " -> r(min)", s["min"])
            add("max", summ + " -> r(max)", s["max"])
            add("median", "_pctile %s %s, p(50) -> r(r1)" % (var, qc),
                pct("50")[0])
            add("sd", summ + " -> r(sd)", s["sd"])
            add("var", "summarize %s %s, detail -> r(Var)" % (var, qc), dvar)
            cv = None
            if not (miss(s["sd"]) or miss(s["mean"])):
                cv = s["sd"] / s["mean"]
            add("cv", summ + " -> r(sd)/r(mean)", cv)
            lo, hi = pct("25 75")
            iqr = None
            if not (miss(lo) or miss(hi)):
                iqr = hi - lo
            add("iqr", "_pctile %s %s, p(25 75) -> r(r2)-r(r1)" % (var, qc), iqr)
            add("skewness", "summarize %s %s, detail -> r(skewness)" % (var, qc),
                dskew)
            for p in PCTS:
                add("p" + p, "_pctile %s %s, p(%s) -> r(r1)" % (var, qc, p),
                    pct(p)[0])

    out["auto_kpi"] = rows

    # big: _pctile on x = 1..20000 under five scopes.
    run("clear")
    run("set obs 20000")
    run("generate double x = _n")
    run("generate byte g = x > 10000")
    big = []
    for p in ("81.93", "81.96", "64.4", "16.1", "97.5", "0.07"):
        for scope, q in (("all", ""), ("g0", "if g == 0"), ("g1", "if g == 1"),
                         ("rng", "if inrange(x, 1, 10000)"),
                         ("sld", "if x >= 10001")):
            cmd = "_pctile x %s, p(%s)" % (q, p)
            done = ok(cmd)
            big.append({"stat": "p" + p, "scope": scope, "cmd": cmd,
                        "value": num(r("r1")) if done else None})

    out["big"] = {"n": 20000, "x": "x = _n", "g": "g = x > 10000",
                  "values": big}

    # dates: a %td date, 01jan2020 on, 100 days.
    run("clear")
    run("set obs 100")
    run("generate double date = 21915 + _n - 1")
    run("format date %td")
    dates = []
    for stat, p in (("p10", "10"), ("p97.5", "97.5"), ("p50", "50"),
                    ("p0.5", "0.5"), ("median", "50")):
        run("_pctile date, p(%s)" % p)
        dates.append({"stat": stat, "cmd": "_pctile date, p(%s) -> r(r1)" % p,
                      "value": num(r("r1"))})

    run("summarize date")
    dates.append({"stat": "min", "cmd": "summarize date -> r(min)",
                  "value": num(r("min"))})

    dates.append({"stat": "max", "cmd": "summarize date -> r(max)",
                  "value": num(r("max"))})

    for e in dates:
        e["td"] = SFIToolkit.formatValue(e["value"], "%td").strip()

    out["dates"] = {"first": 21915, "n": 100, "format": "%td", "values": dates}

    # strings: make with three blanks.
    run("sysuse auto, clear")
    run('replace make = "" in 1/3')
    svals = []
    for scope, q, cq in (("all", "", ""),
                         ("f1", " if foreign == 1", " & foreign == 1")):
        run("count if !missing(make)%s" % cq)
        svals.append({"scope": scope, "stat": "count",
                      "cmd": "count if !missing(make)%s" % cq,
                      "value": num(r("N"))})
        run("tabulate make%s" % q)
        svals.append({"scope": scope, "stat": "dcount",
                      "cmd": "tabulate make%s -> r(r)" % q,
                      "value": num(r("r"))})

    out["strings"] = {"blank": 'sysuse auto; replace make = "" in 1/3',
                      "make": list(Data.get("make")),
                      "foreign": column("foreign"), "values": svals}

    # rule_cases: _pctile x on x = 1..n, each n's p in ascending batches.
    by_n = {}
    for n, p in inputs:
        by_n.setdefault(n, []).append(p)

    got = {}
    for n in sorted(by_n):
        run("clear")
        run("set obs %d" % n)
        run("generate double x = _n")
        uniq = []
        for p in sorted(set(by_n[n]), key=float):
            if uniq and float(uniq[-1][0]) == float(p):
                uniq[-1].append(p)
            else:
                uniq.append([p])
        for i in range(0, len(uniq), 50):
            chunk = uniq[i:i + 50]
            if not ok("_pctile x, p(%s)" % " ".join(c[0] for c in chunk)):
                raise RuntimeError("_pctile failed at n=%d" % n)
            for j, same in enumerate(chunk):
                for p in same:
                    got[(n, p)] = num(r("r%d" % (j + 1)))
        print("rule_cases n=%d: %d p" % (n, len(by_n[n])))

    out["rule_cases"] = [[n, p, got[(n, p)]] for n, p in inputs]

    work = G("ZP_WORK")
    try:
        with open(os.path.join(work, "git_head.txt")) as fh:
            commit = fh.read().strip()
    except OSError:
        commit = ""

    out["_meta"] = {
        "stata_version": G("ZP_VERSION"), "born_date": G("ZP_BORN"),
        "dash_commit": commit, "extracted": G("ZP_WHEN"),
        "source": "scripts/extract_kpi_pctile_truth.do",
        "method": (
            "Each value is Stata's own r() result read right after the command "
            "in its cmd field, as a double. Percentiles are _pctile's (the rule "
            "summarize, detail uses); mean, sum, min, max, sd and count "
            "summarize's; var and skewness summarize, detail's; cv "
            "r(sd)/r(mean); iqr _pctile p(75) - p(25); dcount the number of "
            "groups egen group() forms. rule_cases: _pctile x on x = 1..n, so "
            "an integer result j is x_(j) and j + 0.5 the mean of x_(j) and "
            "x_(j+1)."),
        "percentile_rule": (
            "Measured over 1,643,898 cases (n = 1..300 and 12 larger n up to "
            "1e6 on every p of one and two decimals, 1,296 p one ulp at a time "
            "either side of an exact-integer n*p/100, and 126 more): P = "
            "n*p/100 in double; if |P - round(P)| <= 1e-15 * P, P is an integer "
            "and the percentile is (x_(P) + x_(P+1))/2, clamped to x_(1) and "
            "x_(n); otherwise it is x_(ceil(P)). p must be greater than 0 and "
            "less than 100 (_pctile: percentiles must be between 0 and 100, "
            "r(198), for 0 and 100 themselves)."),
        "rule_cases_selection": (
            "the 1,947 (n, p) of the one- and two-decimal grid where the "
            "absolute 1e-12 rule dash used before WP-23 disagreed with Stata, "
            "1,500 grid rows where it agreed (Python random.seed(20260923)), "
            "every ulp probe and every discriminating probe; this generator "
            "keeps those (n, p) and re-measures each result"),
        "scopes": (
            "all: no qualifier; f1/f0: if foreign==1/0; in50: in 1/50; rng: if "
            "inrange(weight, 2000, 3500) (a range filter); sld: if mpg >= 22 (a "
            "slider filter); f0rng, in50sld: the two combined; in30: in 1/30 (a "
            "brush of the first 30 rows); f1in30: if foreign==1 in 1/30; empty: "
            "if foreign==0 & foreign==1; one: if mpg >= 22 in 1/1")}

    # The committed layout: a row per line, a column on one line.
    D = json.dumps

    def compact(v):
        return json.dumps(v, separators=(",", ":"))

    def rows_of(items):
        return ",\n".join("    " + D(x) for x in items)

    meta = D(out["_meta"], indent=2).replace("\n", "\n  ")
    auto = ",\n".join("    %s: %s" % (D(k), compact(v))
                      for k, v in out["auto"].items())
    big, dates, strs = out["big"], out["dates"], out["strings"]
    text = (
        "{\n"
        '  "_meta": ' + meta + ",\n"
        '  "auto": {\n' + auto + "\n  },\n"
        '  "auto_kpi": [\n' + rows_of(out["auto_kpi"]) + "\n  ],\n"
        '  "big": {"n": %d, "x": %s, "g": %s, "values": [\n'
        % (big["n"], D(big["x"]), D(big["g"])) + rows_of(big["values"])
        + "\n  ]},\n"
        '  "dates": {"first": %d, "n": %d, "format": %s, "values": [\n'
        % (dates["first"], dates["n"], D(dates["format"]))
        + rows_of(dates["values"]) + "\n  ]},\n"
        '  "strings": {"blank": %s, "make": %s,\n'
        % (D(strs["blank"]), compact(strs["make"]))
        + '    "foreign": %s,\n' % compact(strs["foreign"])
        + '    "values": %s\n  },\n' % D(strs["values"])
        + '  "rule_cases": [\n' + rows_of(out["rule_cases"]) + "\n  ]\n}\n")
    json.loads(text)
    with open(fixture, "w", encoding="utf-8") as fh:
        fh.write(text)

    try:
        os.remove(os.path.join(work, "git_head.txt"))
    except OSError:
        pass

    print("wrote", fixture)


main()
end
