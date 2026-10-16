*! extract_global_text_truth.do
*! WP-31 section 42 (D13b): twoway's drawing of a global macro typed
*! literally (\$name) in each graph text option, for
*! test/fixtures/global_text_truth.json.
*!
*! WHY THIS EXISTS
*!
*! A text typed with \$name reaches the command as $name.  twoway reads
*! its text options again and expands the global there; dash kept such a
*! title literal (JSE-65) while its text() expanded it (S30, D13).  This
*! script draws each text option holding a global of each kind (plain
*! text, SMCL, a double quote, an =exp, an empty or unset global, the
*! braced form) and records what twoway's SVG writes and its return code.
*!
*! Output: test/fixtures/global_text_truth.json
*!
*! Run with:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_global_text_truth.do
*!
*! Each record: the option, the global's kind, the typed text (with the
*! dollar sign), the global's value, rc, and the texts of the SVG that
*! start with the case's marker "Z<k>:".  The trailing python: block never
*! calls back into Stata; a backtick in it would be spelled \x60.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_global_text_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_global_text_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZT_REPO "`repo'"
global ZT_OUT  "${ZT_REPO}/test/fixtures/global_text_truth.json"
local scratch "`c(tmpdir)'dash_global_text_probe"
capture mkdir "`scratch'"
global ZT_WORK "`scratch'"
global ZT_REC  "`scratch'/global_manifest.txt"
global ZT_SVER = c(stata_version)
global ZT_BORN = c(born_date)
global ZT_DATE = c(current_date)
tempfile ztgitrev
quietly shell git -C "${ZT_REPO}" rev-parse HEAD > "`ztgitrev'"
tempname ztgfh
file open `ztgfh' using "`ztgitrev'", read text
file read `ztgfh' ztgitline
file close `ztgfh'
global ZT_COMMIT = trim(`"`ztgitline'"')
capture assert ustrregexm(`"${ZT_COMMIT}"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_global_text_truth.do: git rev-parse HEAD did not print a 40-character commit"
    exit 498
}

sysuse auto, clear
global ZTG_plain "hello"
global ZTG_smcl "{bf:x}y"
global ZTG_quote `"say "hi""'
global ZTG_eval "\`=1+1'"
global ZTG_empty ""
global ZTG_nest "ZTG_plain"

tempname ztm
file open `ztm' using "${ZT_REC}", write text replace
global ZT_FH `ztm'
global ZT_K = 0
global ZT_T = char(9)

// Each case is typed on its own line, as a user types it (\$ keeps the
// dollar sign), never built in a macro: a command line built from a macro
// is expanded by Stata before twoway reads it, which would measure
// Stata's expansion rather than twoway's.  zt_done exports the SVG and
// writes the case's return code.
capture program drop zt_done
program define zt_done
    args k
    local rc = _rc
    if `rc' == 0 {
        quietly graph export "${ZT_WORK}/gt_`k'.svg", name(ztg) replace as(svg)
        graph drop ztg
    }
    file write ${ZT_FH} "`k'${ZT_T}`rc'" _n
end

capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), title("Z1:a \$ZTG_plain b") name(ztg, replace)
zt_done 1
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), title("Z2:a \${ZTG_plain}b") name(ztg, replace)
zt_done 2
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), title("Z3:a \$ZTG_smcl b") name(ztg, replace)
zt_done 3
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), title("Z4:a \$ZTG_quote b") name(ztg, replace)
zt_done 4
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), title("Z5:a \$ZTG_eval b") name(ztg, replace)
zt_done 5
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), title("Z6:a \$ZTG_empty b") name(ztg, replace)
zt_done 6
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), title("Z7:a \$ZTG_nosuch b") name(ztg, replace)
zt_done 7
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), title("Z8:a \$\$ZTG_nest b") name(ztg, replace)
zt_done 8
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), subtitle("Z9:a \$ZTG_plain b") name(ztg, replace)
zt_done 9
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), subtitle("Z10:a \${ZTG_plain}b") name(ztg, replace)
zt_done 10
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), subtitle("Z11:a \$ZTG_smcl b") name(ztg, replace)
zt_done 11
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), subtitle("Z12:a \$ZTG_quote b") name(ztg, replace)
zt_done 12
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), subtitle("Z13:a \$ZTG_eval b") name(ztg, replace)
zt_done 13
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), subtitle("Z14:a \$ZTG_empty b") name(ztg, replace)
zt_done 14
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), subtitle("Z15:a \$ZTG_nosuch b") name(ztg, replace)
zt_done 15
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), subtitle("Z16:a \$\$ZTG_nest b") name(ztg, replace)
zt_done 16
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), note("Z17:a \$ZTG_plain b") name(ztg, replace)
zt_done 17
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), note("Z18:a \${ZTG_plain}b") name(ztg, replace)
zt_done 18
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), note("Z19:a \$ZTG_smcl b") name(ztg, replace)
zt_done 19
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), note("Z20:a \$ZTG_quote b") name(ztg, replace)
zt_done 20
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), note("Z21:a \$ZTG_eval b") name(ztg, replace)
zt_done 21
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), note("Z22:a \$ZTG_empty b") name(ztg, replace)
zt_done 22
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), note("Z23:a \$ZTG_nosuch b") name(ztg, replace)
zt_done 23
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), note("Z24:a \$\$ZTG_nest b") name(ztg, replace)
zt_done 24
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), caption("Z25:a \$ZTG_plain b") name(ztg, replace)
zt_done 25
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), caption("Z26:a \${ZTG_plain}b") name(ztg, replace)
zt_done 26
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), caption("Z27:a \$ZTG_smcl b") name(ztg, replace)
zt_done 27
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), caption("Z28:a \$ZTG_quote b") name(ztg, replace)
zt_done 28
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), caption("Z29:a \$ZTG_eval b") name(ztg, replace)
zt_done 29
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), caption("Z30:a \$ZTG_empty b") name(ztg, replace)
zt_done 30
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), caption("Z31:a \$ZTG_nosuch b") name(ztg, replace)
zt_done 31
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), caption("Z32:a \$\$ZTG_nest b") name(ztg, replace)
zt_done 32
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), xtitle("Z33:a \$ZTG_plain b") name(ztg, replace)
zt_done 33
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), xtitle("Z34:a \${ZTG_plain}b") name(ztg, replace)
zt_done 34
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), xtitle("Z35:a \$ZTG_smcl b") name(ztg, replace)
zt_done 35
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), xtitle("Z36:a \$ZTG_quote b") name(ztg, replace)
zt_done 36
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), xtitle("Z37:a \$ZTG_eval b") name(ztg, replace)
zt_done 37
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), xtitle("Z38:a \$ZTG_empty b") name(ztg, replace)
zt_done 38
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), xtitle("Z39:a \$ZTG_nosuch b") name(ztg, replace)
zt_done 39
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), xtitle("Z40:a \$\$ZTG_nest b") name(ztg, replace)
zt_done 40
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), ytitle("Z41:a \$ZTG_plain b") name(ztg, replace)
zt_done 41
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), ytitle("Z42:a \${ZTG_plain}b") name(ztg, replace)
zt_done 42
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), ytitle("Z43:a \$ZTG_smcl b") name(ztg, replace)
zt_done 43
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), ytitle("Z44:a \$ZTG_quote b") name(ztg, replace)
zt_done 44
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), ytitle("Z45:a \$ZTG_eval b") name(ztg, replace)
zt_done 45
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), ytitle("Z46:a \$ZTG_empty b") name(ztg, replace)
zt_done 46
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), ytitle("Z47:a \$ZTG_nosuch b") name(ztg, replace)
zt_done 47
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), ytitle("Z48:a \$\$ZTG_nest b") name(ztg, replace)
zt_done 48
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), t1title("Z49:a \$ZTG_plain b") name(ztg, replace)
zt_done 49
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), t1title("Z50:a \${ZTG_plain}b") name(ztg, replace)
zt_done 50
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), t1title("Z51:a \$ZTG_smcl b") name(ztg, replace)
zt_done 51
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), t1title("Z52:a \$ZTG_quote b") name(ztg, replace)
zt_done 52
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), t1title("Z53:a \$ZTG_eval b") name(ztg, replace)
zt_done 53
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), t1title("Z54:a \$ZTG_empty b") name(ztg, replace)
zt_done 54
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), t1title("Z55:a \$ZTG_nosuch b") name(ztg, replace)
zt_done 55
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), t1title("Z56:a \$\$ZTG_nest b") name(ztg, replace)
zt_done 56
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), b2title("Z57:a \$ZTG_plain b") name(ztg, replace)
zt_done 57
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), b2title("Z58:a \${ZTG_plain}b") name(ztg, replace)
zt_done 58
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), b2title("Z59:a \$ZTG_smcl b") name(ztg, replace)
zt_done 59
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), b2title("Z60:a \$ZTG_quote b") name(ztg, replace)
zt_done 60
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), b2title("Z61:a \$ZTG_eval b") name(ztg, replace)
zt_done 61
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), b2title("Z62:a \$ZTG_empty b") name(ztg, replace)
zt_done 62
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), b2title("Z63:a \$ZTG_nosuch b") name(ztg, replace)
zt_done 63
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), b2title("Z64:a \$\$ZTG_nest b") name(ztg, replace)
zt_done 64
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), l1title("Z65:a \$ZTG_plain b") name(ztg, replace)
zt_done 65
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), l1title("Z66:a \${ZTG_plain}b") name(ztg, replace)
zt_done 66
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), l1title("Z67:a \$ZTG_smcl b") name(ztg, replace)
zt_done 67
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), l1title("Z68:a \$ZTG_quote b") name(ztg, replace)
zt_done 68
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), l1title("Z69:a \$ZTG_eval b") name(ztg, replace)
zt_done 69
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), l1title("Z70:a \$ZTG_empty b") name(ztg, replace)
zt_done 70
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), l1title("Z71:a \$ZTG_nosuch b") name(ztg, replace)
zt_done 71
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), l1title("Z72:a \$\$ZTG_nest b") name(ztg, replace)
zt_done 72
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), r1title("Z73:a \$ZTG_plain b") name(ztg, replace)
zt_done 73
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), r1title("Z74:a \${ZTG_plain}b") name(ztg, replace)
zt_done 74
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), r1title("Z75:a \$ZTG_smcl b") name(ztg, replace)
zt_done 75
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), r1title("Z76:a \$ZTG_quote b") name(ztg, replace)
zt_done 76
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), r1title("Z77:a \$ZTG_eval b") name(ztg, replace)
zt_done 77
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), r1title("Z78:a \$ZTG_empty b") name(ztg, replace)
zt_done 78
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), r1title("Z79:a \$ZTG_nosuch b") name(ztg, replace)
zt_done 79
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), r1title("Z80:a \$\$ZTG_nest b") name(ztg, replace)
zt_done 80
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), legend(label(1 "Z81:a \$ZTG_plain b")) name(ztg, replace)
zt_done 81
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), legend(label(1 "Z82:a \${ZTG_plain}b")) name(ztg, replace)
zt_done 82
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), legend(label(1 "Z83:a \$ZTG_smcl b")) name(ztg, replace)
zt_done 83
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), legend(label(1 "Z84:a \$ZTG_quote b")) name(ztg, replace)
zt_done 84
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), legend(label(1 "Z85:a \$ZTG_eval b")) name(ztg, replace)
zt_done 85
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), legend(label(1 "Z86:a \$ZTG_empty b")) name(ztg, replace)
zt_done 86
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), legend(label(1 "Z87:a \$ZTG_nosuch b")) name(ztg, replace)
zt_done 87
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), legend(label(1 "Z88:a \$\$ZTG_nest b")) name(ztg, replace)
zt_done 88
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), xlabel(3000 "Z89:a \$ZTG_plain b") name(ztg, replace)
zt_done 89
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), xlabel(3000 "Z90:a \${ZTG_plain}b") name(ztg, replace)
zt_done 90
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), xlabel(3000 "Z91:a \$ZTG_smcl b") name(ztg, replace)
zt_done 91
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), xlabel(3000 "Z92:a \$ZTG_quote b") name(ztg, replace)
zt_done 92
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), xlabel(3000 "Z93:a \$ZTG_eval b") name(ztg, replace)
zt_done 93
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), xlabel(3000 "Z94:a \$ZTG_empty b") name(ztg, replace)
zt_done 94
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), xlabel(3000 "Z95:a \$ZTG_nosuch b") name(ztg, replace)
zt_done 95
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), xlabel(3000 "Z96:a \$\$ZTG_nest b") name(ztg, replace)
zt_done 96
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), text(30 3000 "Z97:a \$ZTG_plain b") name(ztg, replace)
zt_done 97
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), text(30 3000 "Z98:a \${ZTG_plain}b") name(ztg, replace)
zt_done 98
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), text(30 3000 "Z99:a \$ZTG_smcl b") name(ztg, replace)
zt_done 99
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), text(30 3000 "Z100:a \$ZTG_quote b") name(ztg, replace)
zt_done 100
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), text(30 3000 "Z101:a \$ZTG_eval b") name(ztg, replace)
zt_done 101
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), text(30 3000 "Z102:a \$ZTG_empty b") name(ztg, replace)
zt_done 102
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), text(30 3000 "Z103:a \$ZTG_nosuch b") name(ztg, replace)
zt_done 103
capture graph drop ztg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(2)), text(30 3000 "Z104:a \$\$ZTG_nest b") name(ztg, replace)
zt_done 104
file close `ztm'

python:
import json
import os
import sys
from sfi import Macro

REPO = Macro.getGlobal("ZT_REPO")
sys.path.insert(0, os.path.join(REPO, "scripts"))
import svg_text_runs

WORK = Macro.getGlobal("ZT_WORK")
out = {
    "_meta": {
        "stata_version": Macro.getGlobal("ZT_SVER"),
        "born_date": Macro.getGlobal("ZT_BORN"),
        "dash_commit": Macro.getGlobal("ZT_COMMIT"),
        "extracted": Macro.getGlobal("ZT_DATE"),
        "source": "scripts/extract_global_text_truth.do",
    },
    "globals": {g: Macro.getGlobal("ZTG_" + g)
                for g in ("plain", "smcl", "quote", "eval", "empty", "nest")},
    "cases": [],
}
TABLE = [('title', 'plain', 'a \x24ZTG_plain b'), ('title', 'braced', 'a \x24{ZTG_plain}b'), ('title', 'smcl', 'a \x24ZTG_smcl b'), ('title', 'quote', 'a \x24ZTG_quote b'), ('title', 'eval', 'a \x24ZTG_eval b'), ('title', 'empty', 'a \x24ZTG_empty b'), ('title', 'unset', 'a \x24ZTG_nosuch b'), ('title', 'nested', 'a \x24\x24ZTG_nest b'), ('subtitle', 'plain', 'a \x24ZTG_plain b'), ('subtitle', 'braced', 'a \x24{ZTG_plain}b'), ('subtitle', 'smcl', 'a \x24ZTG_smcl b'), ('subtitle', 'quote', 'a \x24ZTG_quote b'), ('subtitle', 'eval', 'a \x24ZTG_eval b'), ('subtitle', 'empty', 'a \x24ZTG_empty b'), ('subtitle', 'unset', 'a \x24ZTG_nosuch b'), ('subtitle', 'nested', 'a \x24\x24ZTG_nest b'), ('note', 'plain', 'a \x24ZTG_plain b'), ('note', 'braced', 'a \x24{ZTG_plain}b'), ('note', 'smcl', 'a \x24ZTG_smcl b'), ('note', 'quote', 'a \x24ZTG_quote b'), ('note', 'eval', 'a \x24ZTG_eval b'), ('note', 'empty', 'a \x24ZTG_empty b'), ('note', 'unset', 'a \x24ZTG_nosuch b'), ('note', 'nested', 'a \x24\x24ZTG_nest b'), ('caption', 'plain', 'a \x24ZTG_plain b'), ('caption', 'braced', 'a \x24{ZTG_plain}b'), ('caption', 'smcl', 'a \x24ZTG_smcl b'), ('caption', 'quote', 'a \x24ZTG_quote b'), ('caption', 'eval', 'a \x24ZTG_eval b'), ('caption', 'empty', 'a \x24ZTG_empty b'), ('caption', 'unset', 'a \x24ZTG_nosuch b'), ('caption', 'nested', 'a \x24\x24ZTG_nest b'), ('xtitle', 'plain', 'a \x24ZTG_plain b'), ('xtitle', 'braced', 'a \x24{ZTG_plain}b'), ('xtitle', 'smcl', 'a \x24ZTG_smcl b'), ('xtitle', 'quote', 'a \x24ZTG_quote b'), ('xtitle', 'eval', 'a \x24ZTG_eval b'), ('xtitle', 'empty', 'a \x24ZTG_empty b'), ('xtitle', 'unset', 'a \x24ZTG_nosuch b'), ('xtitle', 'nested', 'a \x24\x24ZTG_nest b'), ('ytitle', 'plain', 'a \x24ZTG_plain b'), ('ytitle', 'braced', 'a \x24{ZTG_plain}b'), ('ytitle', 'smcl', 'a \x24ZTG_smcl b'), ('ytitle', 'quote', 'a \x24ZTG_quote b'), ('ytitle', 'eval', 'a \x24ZTG_eval b'), ('ytitle', 'empty', 'a \x24ZTG_empty b'), ('ytitle', 'unset', 'a \x24ZTG_nosuch b'), ('ytitle', 'nested', 'a \x24\x24ZTG_nest b'), ('t1title', 'plain', 'a \x24ZTG_plain b'), ('t1title', 'braced', 'a \x24{ZTG_plain}b'), ('t1title', 'smcl', 'a \x24ZTG_smcl b'), ('t1title', 'quote', 'a \x24ZTG_quote b'), ('t1title', 'eval', 'a \x24ZTG_eval b'), ('t1title', 'empty', 'a \x24ZTG_empty b'), ('t1title', 'unset', 'a \x24ZTG_nosuch b'), ('t1title', 'nested', 'a \x24\x24ZTG_nest b'), ('b2title', 'plain', 'a \x24ZTG_plain b'), ('b2title', 'braced', 'a \x24{ZTG_plain}b'), ('b2title', 'smcl', 'a \x24ZTG_smcl b'), ('b2title', 'quote', 'a \x24ZTG_quote b'), ('b2title', 'eval', 'a \x24ZTG_eval b'), ('b2title', 'empty', 'a \x24ZTG_empty b'), ('b2title', 'unset', 'a \x24ZTG_nosuch b'), ('b2title', 'nested', 'a \x24\x24ZTG_nest b'), ('l1title', 'plain', 'a \x24ZTG_plain b'), ('l1title', 'braced', 'a \x24{ZTG_plain}b'), ('l1title', 'smcl', 'a \x24ZTG_smcl b'), ('l1title', 'quote', 'a \x24ZTG_quote b'), ('l1title', 'eval', 'a \x24ZTG_eval b'), ('l1title', 'empty', 'a \x24ZTG_empty b'), ('l1title', 'unset', 'a \x24ZTG_nosuch b'), ('l1title', 'nested', 'a \x24\x24ZTG_nest b'), ('r1title', 'plain', 'a \x24ZTG_plain b'), ('r1title', 'braced', 'a \x24{ZTG_plain}b'), ('r1title', 'smcl', 'a \x24ZTG_smcl b'), ('r1title', 'quote', 'a \x24ZTG_quote b'), ('r1title', 'eval', 'a \x24ZTG_eval b'), ('r1title', 'empty', 'a \x24ZTG_empty b'), ('r1title', 'unset', 'a \x24ZTG_nosuch b'), ('r1title', 'nested', 'a \x24\x24ZTG_nest b'), ('legend', 'plain', 'a \x24ZTG_plain b'), ('legend', 'braced', 'a \x24{ZTG_plain}b'), ('legend', 'smcl', 'a \x24ZTG_smcl b'), ('legend', 'quote', 'a \x24ZTG_quote b'), ('legend', 'eval', 'a \x24ZTG_eval b'), ('legend', 'empty', 'a \x24ZTG_empty b'), ('legend', 'unset', 'a \x24ZTG_nosuch b'), ('legend', 'nested', 'a \x24\x24ZTG_nest b'), ('xlabel', 'plain', 'a \x24ZTG_plain b'), ('xlabel', 'braced', 'a \x24{ZTG_plain}b'), ('xlabel', 'smcl', 'a \x24ZTG_smcl b'), ('xlabel', 'quote', 'a \x24ZTG_quote b'), ('xlabel', 'eval', 'a \x24ZTG_eval b'), ('xlabel', 'empty', 'a \x24ZTG_empty b'), ('xlabel', 'unset', 'a \x24ZTG_nosuch b'), ('xlabel', 'nested', 'a \x24\x24ZTG_nest b'), ('text', 'plain', 'a \x24ZTG_plain b'), ('text', 'braced', 'a \x24{ZTG_plain}b'), ('text', 'smcl', 'a \x24ZTG_smcl b'), ('text', 'quote', 'a \x24ZTG_quote b'), ('text', 'eval', 'a \x24ZTG_eval b'), ('text', 'empty', 'a \x24ZTG_empty b'), ('text', 'unset', 'a \x24ZTG_nosuch b'), ('text', 'nested', 'a \x24\x24ZTG_nest b')]
with open(Macro.getGlobal("ZT_REC"), encoding="utf-8") as fh:
    rows = [l.rstrip("\n").split("\t", 1) for l in fh if l.strip()]
for (k, rc), (opt, kind, typed) in zip(rows, TABLE):
    rec = {"option": opt, "kind": kind, "rc": int(rc), "typed": typed}
    if int(rc) == 0:
        texts = svg_text_runs.svg_text_runs(os.path.join(WORK, "gt_%s.svg" % k))
        pre = "Z%s:" % k
        drawn = ["".join(r["text"] for r in t["runs"]) for t in texts]
        rec["drawn"] = [d[len(pre):] for d in drawn if d.startswith(pre)]
    out["cases"].append(rec)
with open(Macro.getGlobal("ZT_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2, sort_keys=True, ensure_ascii=True)
    fh.write("\n")
print("wrote", Macro.getGlobal("ZT_OUT"), len(out["cases"]))
end
