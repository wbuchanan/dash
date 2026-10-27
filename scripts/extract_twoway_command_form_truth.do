*! extract_twoway_command_form_truth.do -- WP-30 section 12 (P1.27): measure
*! twoway's command form, so dash's prefix strip, saving() grammar and
*! batch rule are proved against twoway itself, not modelled.
*!
*! Output: test/fixtures/twoway_command_form_truth.json
*!
*! Run through the slot wrapper only (CLAUDE.md rule 10):
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_twoway_command_form_truth.do
*!
*! METHOD.  Every case text is set by value from Mata (quotes built with
*! char()), never typed inside Stata quotes.  Each case runs in its own
*! log between CFT-BEGIN and CFT-END, under capture noisily, with its rc;
*! a saving() case runs in an emptied work folder and records the files
*! twoway wrote.  prefix: twoway's command words before `scatter mpg
*! weight'; saving: twoway's saving() texts, with no name() (twoway names
*! an empty saving() name after the graph's name(), Graph when none, as
*! dash's one-line form, which has no name, does); display: set graphics off.
*! It never calls a dash command.  A trailing python: block reads every
*! global through sfi and each case log, and writes the fixture; it never
*! calls Stata and never uses shell=True.  The work folder is a fresh
*! folder named from a tempfile (rule 1) and is erased.

clear all
set more off
set linesize 200

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_twoway_command_form_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_twoway_command_form_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global CF_REPO "`repo'"
global CF_OUT "${CF_REPO}/test/fixtures/twoway_command_form_truth.json"
adopath ++ "${CF_REPO}"
global dash_nobrowser 1


tempfile cfbase
local work "`cfbase'_cf"
capture mkdir "`work'"
if _rc {
    display as error "extract_twoway_command_form_truth.do: cannot create `work'"
    exit 693
}
mkdir "`work'/logs"
mkdir "`work'/out"
global CF_WORK "`work'"
quietly shell git -C "${CF_REPO}" rev-parse HEAD > "`work'/git_head.txt"
global CF_VERSION "`c(stata_version)'"
global CF_BORN "`c(born_date)'"
global CF_WHEN "`c(current_date)' `c(current_time)'"
global CF_MODE "`c(mode)'"
global CF_GRAPHICS "`c(graphics)'"
global CF_OS "`c(os)'"

sysuse auto, clear

* ---- the case texts, by value ----
mata:
q  = char(34)
co = char(96) + char(34)
cc = char(34) + char(39)
heads = ("", "twoway", "tw", "two", "graph twoway", "gr tw", "graph tw",
         "gr twoway", "gr two", "gr twow", "gr twowa", "twow", "twowa",
         "gra two", "grap tw", "TWOWAY", "Twoway", "Graph twoway", "GR tw",
         "two two", "tw twoway", "twoway tw", "twoway twoway",
         "graph twoway twoway", "twoway graph", "twoway twow", "twoway gra",
         "gr tw tw", "gr TW", "graph", "g tw")
np = 0
for (i = 1; i <= cols(heads); i++) {
    np++
    st_global("CF_H" + strofreal(np), heads[i])
    st_global("CF_P" + strofreal(np), strtrim(heads[i] + " scatter mpg weight, name(cfp, replace)"))
}
extra = ("twoway(scatter mpg weight), name(cfp, replace)",
         "twoway (scatter mpg weight) (lfit mpg weight), name(cfp, replace)",
         "gr tw scatter mpg weight || lfit mpg weight, name(cfp, replace)",
         "twoway")
for (i = 1; i <= cols(extra); i++) {
    np++
    st_global("CF_H" + strofreal(np), "")
    st_global("CF_P" + strofreal(np), extra[i])
}
st_global("CF_NP", strofreal(np))
sv = ("n1, asis", "n1, asis replace", "n1, replace asis", "n1, bogus",
      "n1, as", "n1, rep", "n1, REPLACE", "n1, Replace", "n1, replace replace",
      "n1, replace asis asis", "n1, asis(x)", "n1, replace(1)", "n1, bogus(1)",
      "n1,", "n1,,", "n1, replace,", "n1, , replace", "n1, replace , asis",
      "n4,replace", q + "n5.html" + q + ", replace", ", replace", "   ",
      q + q + ", replace", "my file.html", "a b c", q + "a b" + q + " c",
      q + "my file" + q + ", replace", q + "n, replace" + q,
      q + "a,b" + q + ", replace", co + "a b" + cc + ", replace",
      "n1, bogus, replace", "n1, , bogus", "n1, " + q + "replace" + q, "")
for (i = 1; i <= cols(sv); i++) st_global("CF_S" + strofreal(i), sv[i])
st_global("CF_NS", strofreal(cols(sv)))
end

* ---- prefix ----
forvalues i = 1/$CF_NP {
    quietly log using "`work'/logs/p`i'.log", text replace name(cft)
    display "CFT-BEGIN"
    capture noisily ${CF_P`i'}
    global CF_PRC`i' = _rc
    display "CFT-END"
    quietly log close cft
}

* ---- saving ----
local pwd0 "`c(pwd)'"
quietly cd "`work'/out"
forvalues i = 1/$CF_NS {
    local fl : dir "`work'/out" files "*"
    foreach f of local fl {
        erase "`work'/out/`f'"
    }
    quietly log using "`work'/logs/s`i'.log", text replace name(cft)
    display "CFT-BEGIN"
    graph drop _all
    capture noisily twoway scatter mpg weight, saving(${CF_S`i'})
    global CF_SRC`i' = _rc
    display "CFT-END"
    quietly log close cft
    local fl : dir "`work'/out" files "*"
    global CF_F`i' `"`fl'"'
}
local fl : dir "`work'/out" files "*"
foreach f of local fl {
    erase "`work'/out/`f'"
}
quietly cd "`pwd0'"

* ---- display ----
set graphics off
capture twoway scatter mpg weight, name(goff, replace)
global CF_GOFF = _rc
capture graph describe goff
global CF_GOFFD = _rc
set graphics on
graph drop _all

python:
import json, os
from sfi import Macro

G = Macro.getGlobal
work = G("CF_WORK")

def said(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().splitlines()
    out, on = [], False
    for ln in lines:
        if not on:
            if ln.strip() == "CFT-BEGIN":
                on = True
            continue
        if ln.strip() == "CFT-END" or (ln.startswith(". display")
                                         and "CFT-END" in ln):
            break
        if ln.startswith(". ") or ln.startswith("> "):
            continue
        out.append(ln.rstrip())
    while out and out[-1] == "":
        out.pop()
    while out and out[0] == "":
        out.pop(0)
    return out

def esc(s):
    return s.replace("\x60", "\\x60")

with open(os.path.join(work, "git_head.txt"), encoding="utf-8") as fh:
    head = fh.read().strip()

def files(raw):
    out, cur, inq = [], "", False
    for ch in raw:
        if ch == '"':
            if inq:
                out.append(cur)
                cur = ""
            inq = not inq
        elif inq:
            cur += ch
    return sorted(out)

prefix = []
for i in range(1, int(G("CF_NP")) + 1):
    msg = said(os.path.join(work, "logs", "p%d.log" % i))
    prefix.append({"head": G("CF_H%d" % i), "cmd": esc(G("CF_P%d" % i)),
                   "rc": int(G("CF_PRC%d" % i)), "msg": esc("\n".join(msg)),
                   "last": esc(msg[-1] if msg else "")})
saving = []
for i in range(1, int(G("CF_NS")) + 1):
    msg = said(os.path.join(work, "logs", "s%d.log" % i))
    saving.append({"text": esc(G("CF_S%d" % i)), "rc": int(G("CF_SRC%d" % i)),
                   "msg": esc("\n".join(msg)),
                   "last": esc(msg[-1] if msg else ""),
                   "files": files(G("CF_F%d" % i))})
doc = {"_meta": {"stata_version": G("CF_VERSION"), "born_date": G("CF_BORN"),
                 "dash_commit": head, "extracted": G("CF_WHEN"),
                 "mode": G("CF_MODE"), "graphics": G("CF_GRAPHICS"),
                 "os": G("CF_OS"),
                 "source": "scripts/extract_twoway_command_form_truth.do",
                 "scope": "twoway's prefixes, saving() grammar and set graphics off, in batch (WP-30 P1.27)"},
       "prefix": prefix, "saving": saving,
       "display": {"graphics_off_rc": int(G("CF_GOFF")),
                   "graphics_off_describe_rc": int(G("CF_GOFFD"))}}
with open(G("CF_OUT"), "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=1, ensure_ascii=True)
    fh.write("\n")
for d in ("logs", "out"):
    p = os.path.join(work, d)
    for f in os.listdir(p):
        os.remove(os.path.join(p, f))
    os.rmdir(p)
os.remove(os.path.join(work, "git_head.txt"))
os.rmdir(work)
end
display "extract_twoway_command_form_truth.do: wrote ${CF_OUT}"
