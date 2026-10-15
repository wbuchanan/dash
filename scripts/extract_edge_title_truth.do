*! extract_edge_title_truth.do -- WP-31 section 27 (D2, A3b): measure how
*! twoway draws its eight edge titles t1title() .. r2title() -- side, ring
*! order against the axes, the legend, note(), caption(), subtitle() and
*! title(), text size, the vertical l/r text, by() -- and how it answers
*! title2(), subtitle2(), the short spellings b() .. t(), b2() .. t2() and
*! nam(), from twoway's own class values and SVG export.  twoway only: the
*! output is the same before and after dash changes.
*!
*! Output: test/fixtures/edge_title_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_edge_title_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_et_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_et_bad' {
    display as error "extract_edge_title_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _et_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_et_rc' | _rc {
    local _et_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_edge_title_truth.do: `_et_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ET_REPO "`repo'"
global ET_OUT "${ET_REPO}/test/fixtures/edge_title_truth.json"

if `"`c(python_exec)'"' == "" {
    display as error "extract_edge_title_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

local work "`c(tmpdir)'dash_edge_title_probe"
capture mkdir "`work'"
global ET_WORK "`work'"

quietly shell git -C "${ET_REPO}" rev-parse HEAD > "${ET_WORK}/git_head.txt"
global ET_VERSION "`c(stata_version)'"
global ET_BORN "`c(born_date)'"
global ET_WHEN "`c(current_date)' `c(current_time)'"

set scheme s2color
sysuse auto, clear

* The members of a graph and of one edge title, for the record.
quietly twoway scatter mpg weight, t1title("T1") name(u27k, replace)
log using "${ET_WORK}/members.log", text replace name(etm)
classutil describe .u27k
classutil describe .u27k.t1title
log close etm

* _et_svg key: export the current graph as SVG to the work directory.
capture program drop _et_svg
program define _et_svg
    args key
    quietly graph export "${ET_WORK}/`key'.svg", replace
end

* _et_styles key: each edge title's textbox style name and size name.
capture program drop _et_styles
program define _et_styles
    args key
    local out ""
    foreach k in t1title t2title b1title b2title l1title l2title r1title r2title {
        local s1 "`.u27k.`k'.style.snm'"
        local s2 "`.u27k.`k'.style.size.snm'"
        if "`s1'" == "" local s1 "-"
        if "`s2'" == "" local s2 "-"
        local out `"`out' `k' `s1' `s2'"'
    }
    global ET_S_`key' `"`out'"'
end

* All eight with the four main boxes and a legend (two plots).
quietly twoway (scatter mpg weight) (scatter trunk weight), t1title("T1") ///
    t2title("T2") b1title("B1") b2title("B2") l1title("L1") l2title("L2") ///
    r1title("R1") r2title("R2") note("N") caption("C") subtitle("S") ///
    title("T") name(u27k, replace)
_et_svg all
_et_styles all

* Each one alone, so its style and size are its own.
foreach k in t1title t2title b1title b2title l1title l2title r1title r2title {
    local lab = upper(substr("`k'", 1, 2))
    quietly twoway scatter mpg weight, `k'("`lab'") name(u27k, replace)
    _et_svg one_`k'
    local s1 "`.u27k.`k'.style.snm'"
    local s2 "`.u27k.`k'.style.size.snm'"
    if "`s1'" == "" local s1 "-"
    if "`s2'" == "" local s2 "-"
    global ET_S_one_`k' "`s1' `s2'"
}

* Two y axes: r1title()/r2title() outside axis 2, l titles outside axis 1.
quietly twoway (scatter mpg weight) (scatter price weight, yaxis(2)), ///
    l1title("L1") l2title("L2") r1title("R1") r2title("R2") name(u27k, replace)
_et_svg yaxis2

* Three y axes on the left (axes 1 and 3) and one on the right (2).
quietly twoway (scatter mpg weight) (scatter price weight, yaxis(2)) ///
    (scatter trunk weight, yaxis(3)), l1title("L1") r1title("R1") ///
    name(u27k, replace)
_et_svg yaxis3

* legend at 12 o'clock: above, outside t1title()/t2title().
quietly twoway (scatter mpg weight) (scatter trunk weight), t1title("T1") ///
    t2title("T2") legend(position(12)) name(u27k, replace)
_et_svg legend12

* Sub-options: size(), color(), prefix and suffix as on title().
quietly twoway scatter mpg weight, t1title("X", size(large) color(red)) ///
    b1title("A") b1title("B", suffix) name(u27k, replace)
_et_svg subopts
global ET_SUFFIX "`.u27k.b1title.text.arrnels'"

* by(): where the eight go on a by() graph.
quietly twoway scatter mpg weight, by(foreign) t1title("T1") b1title("B1") ///
    l1title("L1") r1title("R1") name(u27k, replace)
_et_svg by_tb

* title("A") title("B"): the copies.
quietly twoway scatter mpg weight, title("A") title("B") name(u27k, replace)
global ET_MERGED "`.u27k.title.text.arrnels' `.u27k.title.text[1]'"

* The short spellings: which member each binds to.
capture program drop _et_spell
program define _et_spell
    args key opts
    capture graph drop u27k
    capture noisily twoway scatter mpg weight, `opts' name(u27k, replace)
    local rc = _rc
    local out "rc `rc'"
    if !`rc' {
        foreach k in t1title t2title b1title b2title l1title l2title r1title r2title title {
            local n "`.u27k.`k'.text.arrnels'"
            if "`n'" == "" local n 0
            local v ""
            if `n' > 0 local v "`.u27k.`k'.text[1]'"
            if "`v'" != "" local out "`out' `k' `v'"
        }
    }
    global ET_P_`key' "`out'"
end
foreach c in "b|b(A)" "t|t(A)" "l|l(A)" "r|r(A)" "b2|b2(A)" "t2|t2(A)" ///
    "l2|l2(A)" "r2|r2(A)" "b2t|b2t(A)" "b_b|b(A) b(B)" "b1_b|b1title(A) b(B)" ///
    "t_t|t(A) t(B)" "b2_b|b2title(A) b(B)" "nam|nam(zq)" "na|na(zq)" {
    gettoken key cmd : c, parse("|")
    local cmd = substr(`"`cmd'"', 2, .)
    _et_spell `key' `"`cmd'"'
}

* Refusals: _rc and the logged line, each in its own log.
capture program drop _et_refuse
program define _et_refuse
    args key cmd
    capture log close etr
    quietly log using "${ET_WORK}/r_`key'.log", text replace name(etr)
    capture noisily `cmd'
    local rc = _rc
    quietly log close etr
    global ET_R_`key' "`rc'"
end
_et_refuse title2 `"twoway scatter mpg weight, title2("x")"'
_et_refuse subtitle2 `"twoway scatter mpg weight, subtitle2("x")"'
_et_refuse title2_paren `"twoway (scatter mpg weight, title2("x"))"'
_et_refuse title2_segment `"twoway scatter mpg weight || scatter price weight, title2("x")"'
_et_refuse title2_bare `"twoway scatter mpg weight, title2"'
_et_refuse nam `"twoway scatter mpg weight, nam(zq)"'
_et_refuse nam_bare `"twoway scatter mpg weight, nam"'
_et_refuse na `"twoway scatter mpg weight, na(zq)"'
_et_refuse nam_paren `"twoway (scatter mpg weight, nam(zq))"'

python:
import json, os, re
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("ET_WORK")
_TEXT = re.compile(r"<text\b([^>]*)>([^<]*)</text>")


def svg_texts(key):
    """Every non-numeric text of the SVG: x, y, font size, rotation."""
    with open(os.path.join(work, key + ".svg"), encoding="utf-8") as fh:
        src = fh.read()
    out = []
    for attrs, body in _TEXT.findall(src):
        body = body.replace(" ", " ").strip()
        if not body or re.fullmatch(r"[-0-9.,]+", body):
            continue
        a = dict(re.findall(r'([a-z-]+)="([^"]*)"', attrs))
        fs = re.search(r"font-size:([0-9.]+)px", a.get("style", ""))
        rot = re.search(r"rotate\((-?[0-9.]+)", a.get("transform", ""))
        out.append({"text": body, "x": float(a["x"]), "y": float(a["y"]),
                    "size": float(fs.group(1)) if fs else None,
                    "rotate": float(rot.group(1)) if rot else 0.0,
                    "anchor": a.get("text-anchor", "start")})
    return out


def styles(key):
    w = G("ET_S_" + key).split()
    return {w[i]: {"style": w[i + 1], "size": w[i + 2]}
            for i in range(0, len(w), 3)}


def spell(key):
    w = G("ET_P_" + key).split()
    rec = {"rc": int(w[1]), "bound": {}}
    for i in range(2, len(w), 2):
        rec["bound"][w[i]] = w[i + 1]
    return rec


def refusal(key):
    with open(os.path.join(work, "r_" + key + ".log"), encoding="utf-8") as fh:
        lines = [ln.rstrip() for ln in fh]
    msg = [ln for ln in lines if ln.strip() and not ln.startswith(".")
           and not ln.startswith(">") and not ln.lstrip().startswith("name:")
           and not ln.lstrip().startswith("log:")
           and not ln.lstrip().startswith("log type:")
           and not ln.lstrip().startswith("opened on:")
           and not ln.lstrip().startswith("closed on:")
           and not set(ln.strip()) <= set("-")]
    return {"rc": int(G("ET_R_" + key)), "msg": msg[0] if msg else ""}


with open(os.path.join(work, "members.log"), encoding="utf-8") as fh:
    members = [ln.rstrip() for ln in fh
               if re.match(r"^\s+\S+\s+\.\S+", ln)]

keys = ("t1title", "t2title", "b1title", "b2title",
        "l1title", "l2title", "r1title", "r2title")
out = {
    "all": {"texts": svg_texts("all"), "styles": styles("all")},
    "one": {k: {"texts": svg_texts("one_" + k),
                "style": G("ET_S_one_" + k).split()[0],
                "size": G("ET_S_one_" + k).split()[1]} for k in keys},
    "yaxis2": {"texts": svg_texts("yaxis2")},
    "yaxis3": {"texts": svg_texts("yaxis3")},
    "legend12": {"texts": svg_texts("legend12")},
    "subopts": {"texts": svg_texts("subopts"),
                "b1title_lines": int(G("ET_SUFFIX") or 0)},
    "by_tb": {"texts": svg_texts("by_tb")},
    "merged_title": {"n": int(G("ET_MERGED").split()[0]),
                     "text": G("ET_MERGED").split()[1]},
    "spellings": {k: spell(k) for k in (
        "b", "t", "l", "r", "b2", "t2", "l2", "r2", "b2t", "b_b", "b1_b",
        "t_t", "b2_b", "nam", "na")},
}
for k in ("title2", "subtitle2", "title2_paren", "title2_segment",
          "title2_bare", "nam", "nam_bare", "na", "nam_paren"):
    out["refuse_" + k] = refusal(k)
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ET_VERSION"), "born_date": G("ET_BORN"),
                "dash_commit": commit, "extracted": G("ET_WHEN"),
                "members": members, "scheme": "s2color",
                "source": "scripts/extract_edge_title_truth.do"}
with open(G("ET_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote", G("ET_OUT"))
end
