* extract_scheme_lookup_truth.do -- where twoway finds a scheme it does not
* ship (WP-30 P1.25b, section 34), written to
* test/fixtures/scheme_lookup_truth.json for test/test_scheme_lookup.py.
*
* Stata's setscheme runs `findfile scheme-NAME.scheme' and then `findfile
* NAME.scheme' (BASE/s/scheme.class:172-173); each walks the ado-path,
* every directory followed by its first-letter subdirectory.  Each of the
* 22 cases builds its own directories under a fresh directory below
* c(tmpdir), applies its setup (adopath +, sysdir set), and records:
*   twoway_rc, twoway_bg, twoway_marker  `twoway scatter mpg weight,
*       scheme(NAME)': rc, the first <rect> fill and the commonest marker
*       fill of its SVG (upper-case hex, as Stata writes it)
*   note           a "(note: ...)" line the twoway call logged, or ""
*   set_scheme_rc  `capture set scheme NAME'
*   findfile_rel   findfile's r(fn) relative to the case root (./x is
*       cwd/x, a BASE hit BASE/<file>), "" when neither name is found
*   adopath        the ado-path after the setup: codewords kept, the
*       repository REPO, case directories relative
* R files are `#include s2color', `color background red', `color p1
* green'; B files the same with blue.  Every NAME is used once per session,
* because Stata caches a loaded scheme by name.  Only twoway runs, never
* dash.
*
* Run (never the GUI; the slot wrapper of scripts/stata_slot.sh):
*   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_scheme_lookup_truth.do

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_scheme_lookup_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_scheme_lookup_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1

clear all
set more off
set linesize 255
version 19
local entry_scheme "`c(scheme)'"
set scheme s2color

* What every case may change, saved and restored at the end.
local sd_site     "`c(sysdir_site)'"
local sd_personal "`c(sysdir_personal)'"
local sd_plus     "`c(sysdir_plus)'"
local sd_oldplace "`c(sysdir_oldplace)'"
local pwd0        "`c(pwd)'"
global LK_ADO0 `"$S_ADO"'

tempfile tf
local work "`tf'_s34lk"
mkdir "`work'"
global LK_WORK "`work'"
global LK_REPO "`repo'"

shell git -C "`repo'" rev-parse HEAD > "`work'/git_head.txt"
global LK_STATA "`c(stata_version)' `c(edition_real)'"
global LK_BORN  "`c(born_date)'"
global LK_WHEN  "`c(current_date)' `c(current_time)'"

sysuse auto, clear

python:
import json, os, sys
from sfi import Macro, SFIToolkit
sys.path.insert(0, os.path.join(Macro.getGlobal("LK_REPO"), "scripts"))
import svg_truth

LK = {}
BT = chr(96)


def _rel(p, root, base):
    p = p.strip()
    if not p:
        return ""
    if p.startswith("./"):
        return "cwd/" + p[2:]
    if p.startswith(root + "/"):
        return p[len(root) + 1:]
    if p.startswith(base):
        return "BASE/" + p[len(base):].lstrip("/")
    if not os.path.isabs(p):
        return "cwd/" + p
    return p


def _entries(ado):
    out, cur, i = [], "", 0
    s = ado
    while i < len(s):
        if s.startswith(BT + '"', i):
            j = s.index("\"'", i + 2)
            cur += s[i + 2:j]
            i = j + 2
        elif s[i] == ";":
            out.append(cur)
            cur = ""
            i += 1
        else:
            cur += s[i]
            i += 1
    out.append(cur)
    return [e for e in out if e]


def _lk_rec():
    g = Macro.getGlobal
    key = g("LK_KEY")
    root = g("LK_ROOT")
    base = SFIToolkit.macroExpand(BT + "c(sysdir_base)'")
    repo = g("LK_REPO").rstrip("/")
    ado = []
    for e in _entries(g("S_ADO")):
        if e.rstrip("/") == repo:
            ado.append("REPO")
        elif e.startswith(root + "/") or e == root:
            ado.append(_rel(e, root, base).rstrip("/"))
        else:
            ado.append(e)
    bg = marker = ""
    svg = g("LK_SVG")
    if svg and os.path.exists(svg):
        doc = svg_truth.svg_document(svg)
        bg = doc["rects"][0]["fill"].upper() if doc["rects"] else ""
        fills = svg_truth.svg_marker_fills(svg)
        marker = max(fills, key=lambda c: fills[c]["n"]).upper() if fills else ""
    note = ""
    with open(g("LK_LOG"), encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            if ln.strip().startswith("(note:"):
                note = ln.strip()
                break
    LK[key] = {
        "files": json.loads(g("LK_FILES")),
        "setup": [s for s in g("LK_SETUP").split("|") if s],
        "name": g("LK_NAME"),
        "adopath": ado,
        "twoway_rc": int(g("LK_TWRC")),
        "twoway_bg": bg,
        "twoway_marker": marker,
        "note": note,
        "set_scheme_rc": int(g("LK_SSRC")),
        "findfile_rel": _rel(g("LK_FN"), root, base),
    }
    print("LK %s rc=%s bg=%s marker=%s ss=%s fn=%s note=%s" % (
        key, LK[key]["twoway_rc"], bg, marker, LK[key]["set_scheme_rc"],
        LK[key]["findfile_rel"], note))
end

capture program drop _lk_file
program _lk_file
    // _lk_file path kind: R, B, or the include-and-green text of lk17.
    args path kind
    tempname fh
    file open `fh' using `"`path'"', write text replace
    if "`kind'" == "R" | "`kind'" == "B" {
        local col = cond("`kind'" == "R", "red", "blue")
        file write `fh' "#include s2color" _n "color background `col'" _n "color p1 green" _n
    }
    else {
        file write `fh' "#include lk17p" _n "color p1 green" _n
    }
    file close `fh'
end

capture program drop _lk_run
program _lk_run
    // _lk_run key name: twoway, set scheme and findfile under the setup.
    args key name
    global LK_KEY "`key'"
    global LK_NAME "`name'"
    local root "$LK_ROOT"
    capture log close lklog
    log using "`root'/tw.log", text replace name(lklog)
    capture noisily twoway scatter mpg weight, scheme(`name') name(lk, replace)
    local rc = _rc
    log close lklog
    global LK_TWRC `rc'
    global LK_LOG "`root'/tw.log"
    global LK_SVG ""
    if `rc' == 0 {
        quietly graph export "`root'/tw.svg", name(lk) replace
        global LK_SVG "`root'/tw.svg"
    }
    capture graph drop _all
    capture set scheme `name'
    global LK_SSRC = _rc
    set scheme s2color
    global LK_FN ""
    capture findfile "scheme-`name'.scheme"
    if _rc {
        capture findfile "`name'.scheme"
    }
    if !_rc global LK_FN `"`r(fn)'"'
end

capture program drop _lk_case
program _lk_case
    // _lk_case key: a fresh case root with cwd/ in it, made current.
    args key
    global LK_ROOT "$LK_WORK/`key'"
    mkdir "$LK_ROOT"
    mkdir "$LK_ROOT/cwd"
    quietly cd "$LK_ROOT/cwd"
end

capture program drop _lk_restore
program _lk_restore
    // Back to the entry ado-path, sysdirs and directory.
    args site personal plus oldplace pwd0
    quietly sysdir set SITE "`site'"
    quietly sysdir set PERSONAL "`personal'"
    quietly sysdir set PLUS "`plus'"
    quietly sysdir set OLDPLACE "`oldplace'"
    global S_ADO `"$LK_ADO0"'
    quietly cd "`pwd0'"
    set scheme s2color
end

local R "$LK_WORK"
local restore `""`sd_site'" "`sd_personal'" "`sd_plus'" "`sd_oldplace'" "`pwd0'""'

* lk01: cwd/scheme-lk01.scheme R
capture noisily {
    _lk_case lk01
    _lk_file "`R'/lk01/cwd/scheme-lk01.scheme" R
    global LK_FILES `"{"cwd/scheme-lk01.scheme": "R"}"'
    global LK_SETUP ""
    _lk_run lk01 lk01
    python: _lk_rec()
}
_lk_restore `restore'

* lk02: cwd/lk02.scheme B
capture noisily {
    _lk_case lk02
    _lk_file "`R'/lk02/cwd/lk02.scheme" B
    global LK_FILES `"{"cwd/lk02.scheme": "B"}"'
    global LK_SETUP ""
    _lk_run lk02 lk02
    python: _lk_rec()
}
_lk_restore `restore'

* lk03: both forms in cwd
capture noisily {
    _lk_case lk03
    _lk_file "`R'/lk03/cwd/scheme-lk03.scheme" R
    _lk_file "`R'/lk03/cwd/lk03.scheme" B
    global LK_FILES `"{"cwd/scheme-lk03.scheme": "R", "cwd/lk03.scheme": "B"}"'
    global LK_SETUP ""
    _lk_run lk03 lk03
    python: _lk_rec()
}
_lk_restore `restore'

* lk04: cwd/lk04.scheme B, add/scheme-lk04.scheme R (form-major)
capture noisily {
    _lk_case lk04
    mkdir "`R'/lk04/add"
    _lk_file "`R'/lk04/cwd/lk04.scheme" B
    _lk_file "`R'/lk04/add/scheme-lk04.scheme" R
    adopath + "`R'/lk04/add"
    global LK_FILES `"{"cwd/lk04.scheme": "B", "add/scheme-lk04.scheme": "R"}"'
    global LK_SETUP "adopath + add"
    _lk_run lk04 lk04
    python: _lk_rec()
}
_lk_restore `restore'

* lk05: add/s/scheme-lk05.scheme R
capture noisily {
    _lk_case lk05
    mkdir "`R'/lk05/add"
    mkdir "`R'/lk05/add/s"
    _lk_file "`R'/lk05/add/s/scheme-lk05.scheme" R
    adopath + "`R'/lk05/add"
    global LK_FILES `"{"add/s/scheme-lk05.scheme": "R"}"'
    global LK_SETUP "adopath + add"
    _lk_run lk05 lk05
    python: _lk_rec()
}
_lk_restore `restore'

* lk06: add/l/lk06.scheme R
capture noisily {
    _lk_case lk06
    mkdir "`R'/lk06/add"
    mkdir "`R'/lk06/add/l"
    _lk_file "`R'/lk06/add/l/lk06.scheme" R
    adopath + "`R'/lk06/add"
    global LK_FILES `"{"add/l/lk06.scheme": "R"}"'
    global LK_SETUP "adopath + add"
    _lk_run lk06 lk06
    python: _lk_rec()
}
_lk_restore `restore'

* lk07: add/9/9lk07.scheme R
capture noisily {
    _lk_case lk07
    mkdir "`R'/lk07/add"
    mkdir "`R'/lk07/add/9"
    _lk_file "`R'/lk07/add/9/9lk07.scheme" R
    adopath + "`R'/lk07/add"
    global LK_FILES `"{"add/9/9lk07.scheme": "R"}"'
    global LK_SETUP "adopath + add"
    _lk_run lk07 9lk07
    python: _lk_rec()
}
_lk_restore `restore'

* lk08: add/_/_lk08_.scheme R
capture noisily {
    _lk_case lk08
    mkdir "`R'/lk08/add"
    mkdir "`R'/lk08/add/_"
    _lk_file "`R'/lk08/add/_/_lk08_.scheme" R
    adopath + "`R'/lk08/add"
    global LK_FILES `"{"add/_/_lk08_.scheme": "R"}"'
    global LK_SETUP "adopath + add"
    _lk_run lk08 _lk08_
    python: _lk_rec()
}
_lk_restore `restore'

* lk09: an earlier directory's letter subdirectory beats a later directory
capture noisily {
    _lk_case lk09
    mkdir "`R'/lk09/add"
    mkdir "`R'/lk09/add/s"
    mkdir "`R'/lk09/addb"
    _lk_file "`R'/lk09/add/s/scheme-lk09.scheme" R
    _lk_file "`R'/lk09/addb/scheme-lk09.scheme" B
    adopath + "`R'/lk09/add"
    adopath + "`R'/lk09/addb"
    global LK_FILES `"{"add/s/scheme-lk09.scheme": "R", "addb/scheme-lk09.scheme": "B"}"'
    global LK_SETUP "adopath + add|adopath + addb"
    _lk_run lk09 lk09
    python: _lk_rec()
}
_lk_restore `restore'

* lk10: a directory beats its own subdirectory
capture noisily {
    _lk_case lk10
    mkdir "`R'/lk10/add"
    mkdir "`R'/lk10/add/s"
    _lk_file "`R'/lk10/add/scheme-lk10.scheme" R
    _lk_file "`R'/lk10/add/s/scheme-lk10.scheme" B
    adopath + "`R'/lk10/add"
    global LK_FILES `"{"add/scheme-lk10.scheme": "R", "add/s/scheme-lk10.scheme": "B"}"'
    global LK_SETUP "adopath + add"
    _lk_run lk10 lk10
    python: _lk_rec()
}
_lk_restore `restore'

* lk11: SITE's subdirectory beats the working directory
capture noisily {
    _lk_case lk11
    mkdir "`R'/lk11/site"
    mkdir "`R'/lk11/site/s"
    _lk_file "`R'/lk11/site/s/scheme-lk11.scheme" R
    _lk_file "`R'/lk11/cwd/scheme-lk11.scheme" B
    sysdir set SITE "`R'/lk11/site"
    global LK_FILES `"{"site/s/scheme-lk11.scheme": "R", "cwd/scheme-lk11.scheme": "B"}"'
    global LK_SETUP "sysdir set SITE site"
    _lk_run lk11 lk11
    python: _lk_rec()
}
_lk_restore `restore'

* lk12: PERSONAL
capture noisily {
    _lk_case lk12
    mkdir "`R'/lk12/personal"
    _lk_file "`R'/lk12/personal/scheme-lk12.scheme" R
    sysdir set PERSONAL "`R'/lk12/personal"
    global LK_FILES `"{"personal/scheme-lk12.scheme": "R"}"'
    global LK_SETUP "sysdir set PERSONAL personal"
    _lk_run lk12 lk12
    python: _lk_rec()
}
_lk_restore `restore'

* lk13: PLUS/s
capture noisily {
    _lk_case lk13
    mkdir "`R'/lk13/plus"
    mkdir "`R'/lk13/plus/s"
    _lk_file "`R'/lk13/plus/s/scheme-lk13.scheme" R
    sysdir set PLUS "`R'/lk13/plus"
    global LK_FILES `"{"plus/s/scheme-lk13.scheme": "R"}"'
    global LK_SETUP "sysdir set PLUS plus"
    _lk_run lk13 lk13
    python: _lk_rec()
}
_lk_restore `restore'

* lk14: OLDPLACE
capture noisily {
    _lk_case lk14
    mkdir "`R'/lk14/oldplace"
    _lk_file "`R'/lk14/oldplace/scheme-lk14.scheme" R
    sysdir set OLDPLACE "`R'/lk14/oldplace"
    global LK_FILES `"{"oldplace/scheme-lk14.scheme": "R"}"'
    global LK_SETUP "sysdir set OLDPLACE oldplace"
    _lk_run lk14 lk14
    python: _lk_rec()
}
_lk_restore `restore'

* lk15: a relative ado-path entry, joined to the working directory
capture noisily {
    _lk_case lk15
    mkdir "`R'/lk15/cwd/rel"
    _lk_file "`R'/lk15/cwd/rel/scheme-lk15.scheme" R
    adopath + rel
    global LK_FILES `"{"cwd/rel/scheme-lk15.scheme": "R"}"'
    global LK_SETUP "adopath + rel"
    _lk_run lk15 lk15
    python: _lk_rec()
}
_lk_restore `restore'

* lk16: a shipped name: BASE comes first
capture noisily {
    _lk_case lk16
    _lk_file "`R'/lk16/cwd/scheme-s1mono.scheme" R
    _lk_file "`R'/lk16/cwd/s1mono.scheme" R
    global LK_FILES `"{"cwd/scheme-s1mono.scheme": "R", "cwd/s1mono.scheme": "R"}"'
    global LK_SETUP ""
    _lk_run lk16 s1mono
    python: _lk_rec()
}
_lk_restore `restore'

* lk17: an #include resolved along the ado-path
capture noisily {
    _lk_case lk17
    mkdir "`R'/lk17/add"
    _lk_file "`R'/lk17/cwd/lk17.scheme" I
    _lk_file "`R'/lk17/add/scheme-lk17p.scheme" R
    adopath + "`R'/lk17/add"
    global LK_FILES `"{"cwd/lk17.scheme": "#include lk17p\ncolor p1 green\n", "add/scheme-lk17p.scheme": "R"}"'
    global LK_SETUP "adopath + add"
    _lk_run lk17 lk17
    python: _lk_rec()
}
_lk_restore `restore'

* lk18: a theme name that is a file Stata finds
capture noisily {
    _lk_case lk18
    mkdir "`R'/lk18/add"
    _lk_file "`R'/lk18/add/scheme-mono.scheme" R
    adopath + "`R'/lk18/add"
    global LK_FILES `"{"add/scheme-mono.scheme": "R"}"'
    global LK_SETUP "adopath + add"
    _lk_run lk18 mono
    python: _lk_rec()
}
_lk_restore `restore'

* lk19: a link out of its directory (twoway follows it; dash does not)
capture noisily {
    _lk_case lk19
    mkdir "`R'/lk19/add"
    mkdir "`R'/lk19/outside"
    _lk_file "`R'/lk19/outside/x.scheme" R
    shell ln -s "`R'/lk19/outside/x.scheme" "`R'/lk19/add/scheme-lk19.scheme"
    adopath + "`R'/lk19/add"
    global LK_FILES `"{"outside/x.scheme": "R", "add/scheme-lk19.scheme": "->outside/x.scheme"}"'
    global LK_SETUP "adopath + add"
    _lk_run lk19 lk19
    python: _lk_rec()
}
_lk_restore `restore'

* lk20: found nowhere
capture noisily {
    _lk_case lk20
    global LK_FILES `"{}"'
    global LK_SETUP ""
    _lk_run lk20 lk20none
    python: _lk_rec()
}
_lk_restore `restore'

* lk21: a hyphen in the name
capture noisily {
    _lk_case lk21
    _lk_file "`R'/lk21/cwd/scheme-lk2-1.scheme" R
    global LK_FILES `"{"cwd/scheme-lk2-1.scheme": "R"}"'
    global LK_SETUP ""
    _lk_run lk21 lk2-1
    python: _lk_rec()
}
_lk_restore `restore'

* lk22: a dot in the name
capture noisily {
    _lk_case lk22
    _lk_file "`R'/lk22/cwd/scheme-lk.22.scheme" R
    global LK_FILES `"{"cwd/scheme-lk.22.scheme": "R"}"'
    global LK_SETUP ""
    _lk_run lk22 lk.22
    python: _lk_rec()
}
_lk_restore `restore'

python:
import datetime
with open(os.path.join(Macro.getGlobal("LK_WORK"), "git_head.txt")) as fh:
    head = fh.read().strip()
out = {"_meta": {"stata_version": Macro.getGlobal("LK_STATA"),
                 "born_date": Macro.getGlobal("LK_BORN"),
                 "dash_commit": head,
                 "extracted": Macro.getGlobal("LK_WHEN")}}
for k in sorted(LK):
    out[k] = LK[k]
dest = os.path.join(Macro.getGlobal("LK_REPO"), "test", "fixtures",
                    "scheme_lookup_truth.json")
text = json.dumps(out, indent=2, sort_keys=True).replace(BT, "\\u0060")
with open(dest, "w", encoding="utf-8") as fh:
    fh.write(text + "\n")
print("wrote %d records to %s" % (len(LK), dest))
end

quietly cd "`pwd0'"
shell rm -rf "`work'"
set scheme `entry_scheme'
