*! extract_quote_truth.do -- WP-43 section 43-05 (LT-24): measure how twoway
*! answers option text holding a double quote followed by an apostrophe
*! (the close of a compound quote) -- title("'90s") and its kin in every
*! option and command form -- and, for the record, how dash answers the
*! same line at the extract's commit.  Each row: the command, the rc and
*! every line printed, for twoway and for dash.
*!
*! Output: test/fixtures/quote_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_quote_truth.do
*!
*! Every probe is a literal command line of this file: a command held in a
*! macro splits at its own double-quote-apostrophe, so no probe is routed
*! through a macro or a loop.  The python block reads each command back
*! from this file's text, the line after its _q_open.  The git commit is
*! read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_qt_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_qt_bad' {
    display as error "extract_quote_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _qt_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_qt_rc' | _rc {
    local _qt_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_quote_truth.do: `_qt_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global QT_REPO "`repo'"
global QT_OUT "${QT_REPO}/test/fixtures/quote_truth.json"
global QT_SELF "${QT_REPO}/scripts/extract_quote_truth.do"
adopath ++ "${QT_REPO}/"
global dash_nobrowser 1

local work "`c(tmpdir)'dash_quote_probe"
capture mkdir "`work'"
global QT_WORK "`work'"

quietly shell git -C "${QT_REPO}" rev-parse HEAD > "${QT_WORK}/git_head.txt"
global QT_VERSION "`c(stata_version)'"
global QT_BORN "`c(born_date)'"
global QT_WHEN "`c(current_date)' `c(current_time)'"

set scheme s2color
sysuse auto, clear
capture dash clear

* _q_open key: start the probe's log.  _q_close key who: keep its rc.
capture program drop _q_open
program define _q_open
    args key
    capture graph drop _all
    capture log close qtr
    quietly log using "${QT_WORK}/r.log", text replace name(qtr)
end
capture program drop _q_close
program define _q_close
    local rc = _rc
    args key who
    quietly log close qtr
    quietly copy "${QT_WORK}/r.log" "${QT_WORK}/`who'_`key'.log", replace
    global QT_R_`who'_`key' "`rc'"
    capture dash clear
end

* ==== probes (literal lines; generated once, never through a macro) ====
_q_open title
capture noisily twoway scatter mpg weight, title("'90s")
_q_close title twoway
_q_open title
capture noisily dash scatter mpg weight, title("'90s")
_q_close title dash
_q_open title_blank
capture noisily twoway scatter mpg weight, title("'90s cars")
_q_close title_blank twoway
_q_open title_blank
capture noisily dash scatter mpg weight, title("'90s cars")
_q_close title_blank dash
_q_open subtitle
capture noisily twoway scatter mpg weight, subtitle("'90s")
_q_close subtitle twoway
_q_open subtitle
capture noisily dash scatter mpg weight, subtitle("'90s")
_q_close subtitle dash
_q_open note
capture noisily twoway scatter mpg weight, note("'90s")
_q_close note twoway
_q_open note
capture noisily dash scatter mpg weight, note("'90s")
_q_close note dash
_q_open caption
capture noisily twoway scatter mpg weight, caption("'90s")
_q_close caption twoway
_q_open caption
capture noisily dash scatter mpg weight, caption("'90s")
_q_close caption dash
_q_open xtitle
capture noisily twoway scatter mpg weight, xtitle("'90s")
_q_close xtitle twoway
_q_open xtitle
capture noisily dash scatter mpg weight, xtitle("'90s")
_q_close xtitle dash
_q_open ytitle
capture noisily twoway scatter mpg weight, ytitle("'90s")
_q_close ytitle twoway
_q_open ytitle
capture noisily dash scatter mpg weight, ytitle("'90s")
_q_close ytitle dash
_q_open t1title
capture noisily twoway scatter mpg weight, t1title("'90s")
_q_close t1title twoway
_q_open t1title
capture noisily dash scatter mpg weight, t1title("'90s")
_q_close t1title dash
_q_open leg_label
capture noisily twoway (scatter mpg weight) (scatter trunk weight), legend(label(1 "'90s"))
_q_close leg_label twoway
_q_open leg_label
capture noisily dash (scatter mpg weight) (scatter trunk weight), legend(label(1 "'90s"))
_q_close leg_label dash
_q_open leg_order
capture noisily twoway (scatter mpg weight) (scatter trunk weight), legend(order(1 "'90s"))
_q_close leg_order twoway
_q_open leg_order
capture noisily dash (scatter mpg weight) (scatter trunk weight), legend(order(1 "'90s"))
_q_close leg_order dash
_q_open leg_title
capture noisily twoway (scatter mpg weight) (scatter trunk weight), legend(title("'90s"))
_q_close leg_title twoway
_q_open leg_title
capture noisily dash (scatter mpg weight) (scatter trunk weight), legend(title("'90s"))
_q_close leg_title dash
_q_open leg_subtitle
capture noisily twoway (scatter mpg weight) (scatter trunk weight), legend(subtitle("'90s"))
_q_close leg_subtitle twoway
_q_open leg_subtitle
capture noisily dash (scatter mpg weight) (scatter trunk weight), legend(subtitle("'90s"))
_q_close leg_subtitle dash
_q_open text
capture noisily twoway scatter mpg weight, text(30 3000 "'90s")
_q_close text twoway
_q_open text
capture noisily dash scatter mpg weight, text(30 3000 "'90s")
_q_close text dash
_q_open xlabel
capture noisily twoway scatter mpg weight, xlabel(2000 "'90s")
_q_close xlabel twoway
_q_open xlabel
capture noisily dash scatter mpg weight, xlabel(2000 "'90s")
_q_close xlabel dash
_q_open by_title
capture noisily twoway scatter mpg weight, by(foreign, title("'90s"))
_q_close by_title twoway
_q_open by_title
capture noisily dash scatter mpg weight, by(foreign, title("'90s"))
_q_close by_title dash
_q_open by_note
capture noisily twoway scatter mpg weight, by(foreign, note("'90s"))
_q_close by_note twoway
_q_open by_note
capture noisily dash scatter mpg weight, by(foreign, note("'90s"))
_q_close by_note dash
_q_open group
capture noisily twoway (scatter mpg weight, title("'90s"))
_q_close group twoway
_q_open group
capture noisily dash (scatter mpg weight, title("'90s"))
_q_close group dash
_q_open group_after
capture noisily twoway (scatter mpg weight), title("'90s")
_q_close group_after twoway
_q_open group_after
capture noisily dash (scatter mpg weight), title("'90s")
_q_close group_after dash
_q_open bars
capture noisily twoway scatter mpg weight, title("'90s") || line mpg weight
_q_close bars twoway
_q_open bars
capture noisily dash scatter mpg weight, title("'90s") || line mpg weight
_q_close bars dash
_q_open bars_after
capture noisily twoway scatter mpg weight || line mpg weight, title("'90s")
_q_close bars_after twoway
_q_open bars_after
capture noisily dash scatter mpg weight || line mpg weight, title("'90s")
_q_close bars_after dash
_q_open two_strays
capture noisily twoway scatter mpg weight, title("'a") subtitle("'b")
_q_close two_strays twoway
_q_open two_strays
capture noisily dash scatter mpg weight, title("'a") subtitle("'b")
_q_close two_strays dash
_q_open compound
capture noisily twoway scatter mpg weight, title(`"'90s"')
_q_close compound twoway
_q_open compound
capture noisily dash scatter mpg weight, title(`"'90s"')
_q_close compound dash
_q_open compound_blank
capture noisily twoway scatter mpg weight, title(`"'90s cars"')
_q_close compound_blank twoway
_q_open compound_blank
capture noisily dash scatter mpg weight, title(`"'90s cars"')
_q_close compound_blank dash
_q_open apostrophe
capture noisily twoway scatter mpg weight, title("rock '90s")
_q_close apostrophe twoway
_q_open apostrophe
capture noisily dash scatter mpg weight, title("rock '90s")
_q_close apostrophe dash
_q_open closing
capture noisily twoway scatter mpg weight, title("abc"')
_q_close closing twoway
_q_open closing
capture noisily dash scatter mpg weight, title("abc"')
_q_close closing dash
_q_open closing_more
capture noisily twoway scatter mpg weight, title("abc"'d")
_q_close closing_more twoway
_q_open closing_more
capture noisily dash scatter mpg weight, title("abc"'d")
_q_close closing_more dash
_q_open title_size
capture noisily twoway scatter mpg weight, title("'90s", size(large))
_q_close title_size twoway
_q_open title_size
capture noisily dash scatter mpg weight, title("'90s", size(large))
_q_close title_size dash
_q_open title_then_opt
capture noisily twoway scatter mpg weight, title("'90s") msize(small)
_q_close title_then_opt twoway
_q_open title_then_opt
capture noisily dash scatter mpg weight, title("'90s") msize(small)
_q_close title_then_opt dash
_q_open ch_blank
capture noisily twoway scatter mpg weight, title("'a b")
_q_close ch_blank twoway
_q_open ch_blank
capture noisily dash scatter mpg weight, title("'a b")
_q_close ch_blank dash
_q_open ch_comma
capture noisily twoway scatter mpg weight, title("'a,b")
_q_close ch_comma twoway
_q_open ch_comma
capture noisily dash scatter mpg weight, title("'a,b")
_q_close ch_comma dash
_q_open ch_eq
capture noisily twoway scatter mpg weight, title("'a=b")
_q_close ch_eq twoway
_q_open ch_eq
capture noisily dash scatter mpg weight, title("'a=b")
_q_close ch_eq dash
_q_open ch_minus
capture noisily twoway scatter mpg weight, title("'a-b")
_q_close ch_minus twoway
_q_open ch_minus
capture noisily dash scatter mpg weight, title("'a-b")
_q_close ch_minus dash
_q_open ch_plus
capture noisily twoway scatter mpg weight, title("'a+b")
_q_close ch_plus twoway
_q_open ch_plus
capture noisily dash scatter mpg weight, title("'a+b")
_q_close ch_plus dash
_q_open ch_amp
capture noisily twoway scatter mpg weight, title("'a&b")
_q_close ch_amp twoway
_q_open ch_amp
capture noisily dash scatter mpg weight, title("'a&b")
_q_close ch_amp dash
_q_open ch_dot
capture noisily twoway scatter mpg weight, title("'a.b")
_q_close ch_dot twoway
_q_open ch_dot
capture noisily dash scatter mpg weight, title("'a.b")
_q_close ch_dot dash
_q_open ch_lpar
capture noisily twoway scatter mpg weight, title("'a(b")
_q_close ch_lpar twoway
_q_open ch_lpar
capture noisily dash scatter mpg weight, title("'a(b")
_q_close ch_lpar dash
_q_open ch_rpar
capture noisily twoway scatter mpg weight, title("'a)b")
_q_close ch_rpar twoway
_q_open ch_rpar
capture noisily dash scatter mpg weight, title("'a)b")
_q_close ch_rpar dash
_q_open ch_bslash
capture noisily twoway scatter mpg weight, title("'a\b")
_q_close ch_bslash twoway
_q_open ch_bslash
capture noisily dash scatter mpg weight, title("'a\b")
_q_close ch_bslash dash
_q_open ch_tab
capture noisily twoway scatter mpg weight, title("'a	b")
_q_close ch_tab twoway
_q_open ch_tab
capture noisily dash scatter mpg weight, title("'a	b")
_q_close ch_tab dash
_q_open ch_lt
capture noisily twoway scatter mpg weight, title("'a<b")
_q_close ch_lt twoway
_q_open ch_lt
capture noisily dash scatter mpg weight, title("'a<b")
_q_close ch_lt dash
_q_open ch_gt
capture noisily twoway scatter mpg weight, title("'a>b")
_q_close ch_gt twoway
_q_open ch_gt
capture noisily dash scatter mpg weight, title("'a>b")
_q_close ch_gt dash
_q_open ch_bar
capture noisily twoway scatter mpg weight, title("'a|b")
_q_close ch_bar twoway
_q_open ch_bar
capture noisily dash scatter mpg weight, title("'a|b")
_q_close ch_bar dash
_q_open ch_bang
capture noisily twoway scatter mpg weight, title("'a!b")
_q_close ch_bang twoway
_q_open ch_bang
capture noisily dash scatter mpg weight, title("'a!b")
_q_close ch_bang dash
_q_open ch_star
capture noisily twoway scatter mpg weight, title("'a*b")
_q_close ch_star twoway
_q_open ch_star
capture noisily dash scatter mpg weight, title("'a*b")
_q_close ch_star dash
_q_open ch_slash
capture noisily twoway scatter mpg weight, title("'a/b")
_q_close ch_slash twoway
_q_open ch_slash
capture noisily dash scatter mpg weight, title("'a/b")
_q_close ch_slash dash
_q_open ch_caret
capture noisily twoway scatter mpg weight, title("'a^b")
_q_close ch_caret twoway
_q_open ch_caret
capture noisily dash scatter mpg weight, title("'a^b")
_q_close ch_caret dash
_q_open ch_lbr
capture noisily twoway scatter mpg weight, title("'a[b")
_q_close ch_lbr twoway
_q_open ch_lbr
capture noisily dash scatter mpg weight, title("'a[b")
_q_close ch_lbr dash
_q_open ch_rbr
capture noisily twoway scatter mpg weight, title("'a]b")
_q_close ch_rbr twoway
_q_open ch_rbr
capture noisily dash scatter mpg weight, title("'a]b")
_q_close ch_rbr dash
_q_open ch_tilde
capture noisily twoway scatter mpg weight, title("'a~b")
_q_close ch_tilde twoway
_q_open ch_tilde
capture noisily dash scatter mpg weight, title("'a~b")
_q_close ch_tilde dash
_q_open ch_colon
capture noisily twoway scatter mpg weight, title("'a:b")
_q_close ch_colon twoway
_q_open ch_colon
capture noisily dash scatter mpg weight, title("'a:b")
_q_close ch_colon dash
_q_open ch_semi
capture noisily twoway scatter mpg weight, title("'a;b")
_q_close ch_semi twoway
_q_open ch_semi
capture noisily dash scatter mpg weight, title("'a;b")
_q_close ch_semi dash
_q_open ch_hash
capture noisily twoway scatter mpg weight, title("'a#b")
_q_close ch_hash twoway
_q_open ch_hash
capture noisily dash scatter mpg weight, title("'a#b")
_q_close ch_hash dash
_q_open ch_at
capture noisily twoway scatter mpg weight, title("'a@b")
_q_close ch_at twoway
_q_open ch_at
capture noisily dash scatter mpg weight, title("'a@b")
_q_close ch_at dash
_q_open ch_pct
capture noisily twoway scatter mpg weight, title("'a%b")
_q_close ch_pct twoway
_q_open ch_pct
capture noisily dash scatter mpg weight, title("'a%b")
_q_close ch_pct dash
_q_open ch_qmark
capture noisily twoway scatter mpg weight, title("'a?b")
_q_close ch_qmark twoway
_q_open ch_qmark
capture noisily dash scatter mpg weight, title("'a?b")
_q_close ch_qmark dash
_q_open ch_lbrace
capture noisily twoway scatter mpg weight, title("'a{b")
_q_close ch_lbrace twoway
_q_open ch_lbrace
capture noisily dash scatter mpg weight, title("'a{b")
_q_close ch_lbrace dash
_q_open ch_rbrace
capture noisily twoway scatter mpg weight, title("'a}b")
_q_close ch_rbrace twoway
_q_open ch_rbrace
capture noisily dash scatter mpg weight, title("'a}b")
_q_close ch_rbrace dash
* ==== end probes ====

python:
import json, os, re
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("QT_WORK")
with open(G("QT_SELF"), encoding="utf-8") as fh:
    src = fh.read().split("\n")
probes = []
for i, ln in enumerate(src):
    m = re.fullmatch(r"_q_open (\w+)", ln)
    if m and src[i + 1].startswith("capture noisily twoway "):
        probes.append((m.group(1), src[i + 1][len("capture noisily "):]))


def logged(path):
    with open(path, encoding="utf-8") as fh:
        lines = [ln.rstrip("\n") for ln in fh]
    return [ln.strip() for ln in lines if ln.strip()
            and not ln.startswith(".") and not ln.startswith(">")
            and not ln.lstrip().startswith(("name:", "log:", "log type:",
                                            "opened on:", "closed on:"))
            and not set(ln.strip()) <= set("-")
            # Where dash writes a page names a temporary file: not kept.
            and not ln.startswith("dash: dashboard saved to ")]


out = {}
for key, cmd in probes:
    row = {"command": cmd}
    for who in ("twoway", "dash"):
        lines = logged(os.path.join(work, "%s_%s.log" % (who, key)))
        row[who] = {"rc": int(G("QT_R_%s_%s" % (who, key))),
                    "first": lines[0] if lines else "", "lines": lines}
    out[key] = row
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("QT_VERSION"), "born_date": G("QT_BORN"),
                "dash_commit": commit, "extracted": G("QT_WHEN"),
                "source": "scripts/extract_quote_truth.do",
                "dash_side": "the dash answer at dash_commit, for the record"}
with open(G("QT_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote", G("QT_OUT"), len(probes), "probes")
end
