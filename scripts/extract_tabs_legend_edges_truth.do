*! extract_tabs_legend_edges_truth.do -- WP-31 section 39 (D14, D16,
*! D16b): measure what twoway does with legend() keywords beside an
*! option it refuses (legend(po(9) top)), title(, prefix suffix), the
*! words inside legend(region()) and legend(title()), legend(label(1))
*! with no text, and a bare quoted string among the options in each
*! place an option list is read.  twoway only: tabs() and layout() are
*! dash's own options and have no twoway half.
*!
*! Output: test/fixtures/tabs_legend_edges_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_tabs_legend_edges_truth.do
*!
*! Each probe runs under a text log; its rc, every line it logged and,
*! when it drew, the texts of its SVG export are recorded.  The git
*! commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200
version 19

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zt_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zt_bad' {
    display as error "extract_tabs_legend_edges_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zt_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zt_rc' | _rc {
    local _zt_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_tabs_legend_edges_truth.do: `_zt_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZT_REPO "`repo'"
global ZT_OUT "${ZT_REPO}/test/fixtures/tabs_legend_edges_truth.json"

local work "`c(tmpdir)'dash_tabs_legend_probe"
capture mkdir "`work'"
global ZT_WORK "`work'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_tabs_legend_edges_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

quietly shell git -C "${ZT_REPO}" rev-parse HEAD > "${ZT_WORK}/git_head.txt"
global ZT_VERSION "`c(stata_version)'"
global ZT_BORN "`c(born_date)'"
global ZT_WHEN "`c(current_date)' `c(current_time)'"
global ZT_KEYS ""

* _zt_run key cmd: run cmd under a log, export the graph to SVG when it
* drew, and keep rc, command, log and SVG for the python block.
capture program drop _zt_run
program define _zt_run
    gettoken key 0 : 0
    capture graph drop _all
    quietly log using "${ZT_WORK}/`key'.log", replace text name(zt)
    capture noisily `0'
    local rc = _rc
    quietly log close zt
    capture erase "${ZT_WORK}/`key'.svg"
    if !`rc' {
        capture quietly graph export "${ZT_WORK}/`key'.svg", replace
    }
    global ZT_R_`key' "`rc'"
    global ZT_C_`key' `"`0'"'
    global ZT_KEYS "${ZT_KEYS} `key'"
    display as text "ZT `key': rc `rc'"
end

sysuse auto, clear
set scheme s2color
global ZT_G "abc"

* legend() keywords beside an option twoway refuses
_zt_run legend_po9_top    twoway scatter mpg weight, legend(po(9) top)
_zt_run legend_top_po9    twoway scatter mpg weight, legend(top po(9))
_zt_run legend_top        twoway scatter mpg weight, legend(top)
* JSE-47's probe holds "' (a compound quote's close) in its text, which
* the program's own parsing would read; run in place.
capture graph drop _all
quietly log using "${ZT_WORK}/legend_jse47.log", replace text name(zt)
capture noisily twoway scatter mpg weight, legend(label(1 "'90s") top)
global ZT_R_legend_jse47 "`=_rc'"
quietly log close zt
global ZT_C_legend_jse47 "twoway scatter mpg weight, legend(label(1 [quote]'90s[quote]) top)"
global ZT_KEYS "${ZT_KEYS} legend_jse47"
display as text "ZT legend_jse47: rc ${ZT_R_legend_jse47}"
* WP-31 D16 follow-up: a plain quote opened by an apostrophe in other
* options, each in place for the same reason.
capture graph drop _all
quietly log using "${ZT_WORK}/quote_title.log", replace text name(zt)
capture noisily twoway scatter mpg weight, title("'90s")
global ZT_R_quote_title "`=_rc'"
quietly log close zt
global ZT_C_quote_title "twoway scatter mpg weight, title([quote]'90s[quote])"
global ZT_KEYS "${ZT_KEYS} quote_title"
capture graph drop _all
quietly log using "${ZT_WORK}/quote_xlabel.log", replace text name(zt)
capture noisily twoway scatter mpg weight, xlabel(3000 "'90s")
global ZT_R_quote_xlabel "`=_rc'"
quietly log close zt
global ZT_C_quote_xlabel "twoway scatter mpg weight, xlabel(3000 [quote]'90s[quote])"
global ZT_KEYS "${ZT_KEYS} quote_xlabel"
capture graph drop _all
quietly log using "${ZT_WORK}/quote_text.log", replace text name(zt)
capture noisily twoway scatter mpg weight, text(30 3000 "'90s")
global ZT_R_quote_text "`=_rc'"
quietly log close zt
global ZT_C_quote_text "twoway scatter mpg weight, text(30 3000 [quote]'90s[quote])"
global ZT_KEYS "${ZT_KEYS} quote_text"
capture graph drop _all
quietly log using "${ZT_WORK}/quote_bytitle.log", replace text name(zt)
capture noisily twoway scatter mpg weight, by(foreign, title("'90s"))
global ZT_R_quote_bytitle "`=_rc'"
quietly log close zt
global ZT_C_quote_bytitle "twoway scatter mpg weight, by(foreign, title([quote]'90s[quote]))"
global ZT_KEYS "${ZT_KEYS} quote_bytitle"
capture graph drop _all
quietly log using "${ZT_WORK}/quote_title_jse47a.log", replace text name(zt)
capture noisily twoway scatter mpg weight, title("' name(jgpwn) saving(x.html) '")
global ZT_R_quote_title_jse47a "`=_rc'"
quietly log close zt
global ZT_C_quote_title_jse47a "twoway scatter mpg weight, title([quote]' name(jgpwn) saving(x.html) '[quote])"
global ZT_KEYS "${ZT_KEYS} quote_title_jse47a"
capture graph drop _all
quietly log using "${ZT_WORK}/quote_note.log", replace text name(zt)
capture noisily twoway scatter mpg weight, note("a'b")
global ZT_R_quote_note "`=_rc'"
quietly log close zt
global ZT_C_quote_note "twoway scatter mpg weight, note([quote]a'b[quote])"
global ZT_KEYS "${ZT_KEYS} quote_note"
_zt_run legend_pos9       twoway scatter mpg weight, legend(pos(9))

* title(, prefix suffix)
_zt_run title_prefix_suffix  twoway scatter mpg weight, title("T", prefix suffix)
_zt_run title_suffix_prefix  twoway scatter mpg weight, title("T", suffix prefix)
_zt_run title_prefix         twoway scatter mpg weight, title("T", prefix)
_zt_run title_suffix         twoway scatter mpg weight, title("T", suffix)
_zt_run title_by_prefix_suffix twoway scatter mpg weight, by(foreign, title("B")) title("T", prefix suffix)

* the words inside legend(region()) and legend(title())
_zt_run nested_region_lcolor_bogus twoway scatter mpg weight, legend(region(lcolor(bogus)))
_zt_run nested_region_fcolor_red   twoway scatter mpg weight, legend(region(fcolor(red)))
_zt_run nested_region_bad_word     twoway scatter mpg weight, legend(region(xx))
_zt_run nested_title_size_bogus    twoway scatter mpg weight, legend(title("T", size(bogus)))
_zt_run nested_title_size_large    twoway scatter mpg weight, legend(title("T", size(large)))
_zt_run nested_title_bad_word      twoway scatter mpg weight, legend(title("T", xx))
_zt_run nested_region_lwidth_bogus twoway scatter mpg weight, legend(region(lwidth(bogus)))
_zt_run nested_title_color_bogus   twoway scatter mpg weight, legend(title("T", color(bogus)))

* label(#) with and without text
_zt_run label_one      twoway scatter mpg weight || scatter price weight, legend(label(1))
_zt_run label_one_text twoway scatter mpg weight || scatter price weight, legend(label(1 "A"))

* a bare quoted string among the options (D16b)
_zt_run bare_plot        twoway scatter mpg weight, "abc"
_zt_run bare_plot_global twoway scatter mpg weight, "$ZT_G" name(zt1, replace)
_zt_run bare_after_opt   twoway scatter mpg weight, msize(small) "abc"
_zt_run bare_line        twoway line mpg weight, "abc"
_zt_run bare_paren       twoway (scatter mpg weight, "abc")
_zt_run bare_paren_graph twoway (scatter mpg weight), "abc"
_zt_run bare_bars_plot   twoway scatter mpg weight, "abc" || scatter price weight
_zt_run bare_bars_graph  twoway scatter mpg weight || scatter price weight, "abc"
_zt_run bare_bars_both   twoway scatter mpg weight || scatter price weight, title(T) "abc"
_zt_run bare_compound    twoway scatter mpg weight, `"abc"'
_zt_run bare_two         twoway scatter mpg weight, "a" "b"
_zt_run bare_empty       twoway scatter mpg weight, ""
_zt_run bare_in_title    twoway scatter mpg weight, title("T") note("N")
_zt_run bare_first_then_opt twoway scatter mpg weight, "abc" msize(small)
_zt_run bare_paren_two   twoway (scatter mpg weight, "a" "b")
_zt_run bare_second_paren twoway (scatter mpg weight) (line mpg weight, "abc")
_zt_run bare_paren_graph_two twoway (scatter mpg weight), "a" "b"
_zt_run bare_paren_then_graph twoway (scatter mpg weight, "abc"), title(T)
_zt_run bare_after_title twoway scatter mpg weight, title("T") "abc"
_zt_run bare_before_title twoway scatter mpg weight, "abc" title("T")
_zt_run bare_bars_two    twoway scatter mpg weight || line mpg weight, "a" "b"
_zt_run bare_bars_ctrl   twoway scatter mpg weight, title(T) || line mpg weight
_zt_run bare_by          twoway scatter mpg weight, by(foreign) "abc"
_zt_run bare_paren_graph_opt twoway (scatter mpg weight), title(T) "abc"
_zt_run bare_paren_graph_first twoway (scatter mpg weight), "abc" title(T)
_zt_run bare_three       twoway scatter mpg weight, "a" "b" "c"
_zt_run bare_sep         twoway scatter mpg weight, "a" msize(small) "b"
_zt_run bare_no_comma    twoway scatter mpg weight "abc"
_zt_run bare_bars_first  twoway scatter mpg weight, "abc" || line mpg weight, title(T)
capture graph drop _all

python:
import json, os, re
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("ZT_WORK")
SKIP = ("name:", "log:", "log type:", "opened on:", "closed on:")


def lines(key):
    """Every line the command logged that is not the echoed command or
    the log banner."""
    path = os.path.join(work, key + ".log")
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            raw = [ln.rstrip() for ln in fh]
    except OSError:
        return []
    out = []
    for ln in raw:
        s = ln.strip()
        if not s or set(s) <= set("-") or s.startswith(SKIP):
            continue
        if s.startswith(". ") or s.startswith("> "):
            continue
        out.append(s)
    return out


_TEXT = re.compile(r"<text[^>]*>(.*?)</text>", re.S)


def svg_texts(key):
    path = os.path.join(work, key + ".svg")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8", errors="replace") as fh:
        txt = fh.read()
    import html
    return [html.unescape(t).strip() for t in _TEXT.findall(txt)]


out = {}
for key in G("ZT_KEYS").split():
    rc = int(G("ZT_R_" + key))
    ls = lines(key)
    grp, _, rest = key.partition("_")
    rec = {"cmd": G("ZT_C_" + key).strip(), "rc": rc, "lines": ls,
           "first": (ls[-2] if rc and len(ls) >= 2 and ls[-1].startswith("r(")
                     else (ls[0] if ls else "")),
           "svg_texts": svg_texts(key)}
    out.setdefault(grp, {})[rest] = rec
for name in os.listdir(work):
    if name.endswith((".log", ".svg")):
        try:
            os.remove(os.path.join(work, name))
        except OSError:
            pass
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZT_VERSION"), "born_date": G("ZT_BORN"),
                "dash_commit": commit, "extracted": G("ZT_WHEN"),
                "source": "scripts/extract_tabs_legend_edges_truth.do"}
with open(G("ZT_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZT_OUT"))
end
