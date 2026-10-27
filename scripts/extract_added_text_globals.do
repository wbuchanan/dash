*! extract_added_text_globals.do -- WP-31 section 30 (D13): what dash
*! registers for a text() whose line names a global, $name or ${name},
*! which twoway expands when it draws (test/fixtures/textbox_truth.json
*! global_plain, global_dollars, global_braces).  dash's side only: each
*! row is the line dash.ado wrote to the graph's added_text record, read
*! back out of the registered spec; test_added_text_style.py compares it
*! with twoway's text and with the globals' raw values.
*!
*! Output: test/fixtures/added_text_globals.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_added_text_globals.do
*!
*! Each probe escapes its dollar signs and runs through macval(), so the
*! do-file's own macro expansion leaves `$u30x' for dash to read; each row
*! records the command dash ran.  The git commit is read from a file `shell' wrote,
*! never with shell=True.

clear all
set more off
set linesize 200

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_ag_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_ag_bad' {
    display as error "extract_added_text_globals.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _ag_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_ag_rc' | _rc {
    local _ag_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_added_text_globals.do: `_ag_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global AG_REPO "`repo'"
global AG_OUT "${AG_REPO}/test/fixtures/added_text_globals.json"
adopath ++ "${AG_REPO}"
quietly do "${AG_REPO}/dash_parse.mata"
quietly do "${AG_REPO}/dash.ado"
global dash_nobrowser 1

local work "`c(tmpdir)'dash_added_text_globals"
capture mkdir "`work'"
global AG_WORK "`work'"
quietly shell git -C "${AG_REPO}" rev-parse HEAD > "${AG_WORK}/git_head.txt"
global AG_VERSION "`c(stata_version)'"
global AG_BORN "`c(born_date)'"
global AG_WHEN "`c(current_date)' `c(current_time)'"

sysuse auto, clear
global u30x "hello"
global u30f "F"
* Two globals whose values a macro expansion would evaluate.
mata: st_global("u30e", char(96) + "=1+1" + char(39) + "!")
mata: st_global("u30p", char(96) + "c(pwd)" + char(39))

* _ag_reg key: register the command in global AG_C_<key>, keep its rc and
* the graph's registered JSON.
capture program drop _ag_reg
program define _ag_reg
    args key
    capture dash clear
    mata: st_local("cmd", st_global("AG_C_`key'"))
    capture noisily dash `macval(cmd)' name(u30g)
    global AG_R_`key' = _rc
    mata: st_global("AG_J_`key'", st_global("dash_json_u30g"))
    capture dash clear
end

global AG_C_global_plain `"scatter mpg weight, text(30 2000 "\$u30x")"'
global AG_C_global_dollars `"scatter mpg weight, text(30 2000 "\$\$u30f\$\$")"'
global AG_C_global_braces `"scatter mpg weight, text(30 2000 "\${u30x}!")"'
global AG_C_eval_expr `"scatter mpg weight, text(30 2000 "\$u30e")"'
global AG_C_eval_pwd `"scatter mpg weight, text(30 2000 "\$u30p")"'
global AG_C_unset `"scatter mpg weight, text(30 2000 "a\$u30nosuch b")"'
global AG_C_two_lines `"scatter mpg weight, text(30 2000 "\$u30x" "x\$u30f")"'
foreach k in global_plain global_dollars global_braces eval_expr eval_pwd unset two_lines {
    _ag_reg `k'
}

python:
import json, os
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


keys = ("global_plain", "global_dollars", "global_braces", "eval_expr",
        "eval_pwd", "unset", "two_lines")
out = {}
for k in keys:
    rec = {"command": G("AG_C_" + k), "rc": int(float(G("AG_R_" + k)))}
    lines = None
    if rec["rc"] == 0:
        g = json.loads(G("AG_J_" + k))
        at = (g.get("graph_options") or g.get("options") or {}).get(
            "added_text") or g.get("added_text") or []
        lines = at[0]["at_lines"] if at else None
    rec["at_lines"] = lines
    out[k] = rec
try:
    with open(os.path.join(G("AG_WORK"), "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("AG_VERSION"), "born_date": G("AG_BORN"),
                "dash_commit": commit, "extracted": G("AG_WHEN"),
                "globals": {"u30x": G("u30x"), "u30f": G("u30f"),
                            "u30e": G("u30e"), "u30p": G("u30p")},
                "source": "scripts/extract_added_text_globals.do"}
with open(G("AG_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote", G("AG_OUT"))
end
