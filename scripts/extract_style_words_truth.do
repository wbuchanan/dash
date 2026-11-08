*! extract_style_words_truth.do -- WP-45 section 45-02 (ST-1 with ST-2..ST-6,
*! ST-11): how twoway reads each style word of six classes through the
*! class's _unabbrev program -- compass2dir, tb_orientstyle, clockdir,
*! gridringstyle, anglestyle and connectstyle -- and justification()'s
*! class horizontal.
*!
*! The words are generated here from each class's syntax option names and
*! their minimum abbreviations (the capital letters): every prefix from the
*! minimum to the full name, plus the class's special forms (compass2dir's
*! capitals and clock numbers, connectstyle's L and J, anglestyle's 45 and
*! 270, the style files' own names) and a few words twoway does not take
*! (one letter short of a minimum, capitals, zzz).  "canonical" is the
*! class rule's answer for the word ("" for a word the rule does not take);
*! each word is drawn at each site of its class and compared, by a digest
*! of the exported SVG (its <desc> line left out), with the drawing of the
*! canonical style's full spelling.
*!
*! Rows (key "rows"): class, site, word, canonical, same_as_canonical
*! (1 when the word's SVG equals the canonical drawing's), note (every
*! "(note: ...)" line twoway printed, joined by a newline, or ""), rc, and
*! lines (every line printed when rc is not 0).  Key "drawings": each
*! canonical drawing's digest, class|site|canonical (distinct canonicals of
*! a site draw distinct pictures, so the comparison is not vacuous).  Sites:
*!   compass2dir    text: text(30 3000 "QQ", placement(w));
*!                  aspect: aspectratio(1, placement(w)) xsize(5) ysize(5)
*!   tb_orientstyle text: text(30 3000 "QQ", orientation(w));
*!                  title: title("TT", orientation(w));
*!                  ytitle: ytitle("YY", orientation(w))
*!   clockdir       title: title("TT", position(w));
*!                  legend: legend(position(w)) on two series;
*!                  mlabpos: mlabel(make) mlabposition(w) on 5 cars
*!   gridringstyle  legend: legend(ring(w) position(1));
*!                  title: title("TT", ring(w)) (rc and lines)
*!   anglestyle     mlabangle: mlabel(make) mlabangle(w) on 5 cars;
*!                  msangle: msymbol(T) msangle(w) on 5 cars
*!   connectstyle   connect: connect(w) on the first 20 cars in data order
*!                  (sort would order weight's ties differently each run)
*!   horizontal     title: title("T", justification(w)) (the note only)
*! twoway only: the output does not depend on dash.
*!
*! Output: test/fixtures/style_words_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_style_words_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200
set graphics off
version 19
set scheme stcolor

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zs_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zs_bad' {
    display as error "extract_style_words_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zs_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zs_rc' | _rc {
    local _zs_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_style_words_truth.do: `_zs_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZS_REPO "`repo'"
global ZS_OUT "${ZS_REPO}/test/fixtures/style_words_truth.json"

local work "`c(tmpdir)'dash_style_words_probe"
capture mkdir "`work'"
global ZS_WORK "`work'"

quietly shell git -C "${ZS_REPO}" rev-parse HEAD > "${ZS_WORK}/git_head.txt"
global ZS_VERSION "`c(stata_version)'"
global ZS_BORN "`c(born_date)'"
global ZS_WHEN "`c(current_date)' `c(current_time)'"
global ZS_N 0

* The sites: a twoway command with @ where the word goes.
global ZS_S_compass2dir_text   `"scatter mpg weight, text(30 3000 "QQ", placement(@))"'
global ZS_S_compass2dir_aspect `"scatter mpg weight, aspectratio(1, placement(@)) xsize(5) ysize(5)"'
global ZS_S_tb_orientstyle_text   `"scatter mpg weight, text(30 3000 "QQ", orientation(@))"'
global ZS_S_tb_orientstyle_title  `"scatter mpg weight, title("TT", orientation(@))"'
global ZS_S_tb_orientstyle_ytitle `"scatter mpg weight, ytitle("YY", orientation(@))"'
global ZS_S_clockdir_title   `"scatter mpg weight, title("TT", position(@))"'
global ZS_S_clockdir_legend  `"scatter mpg price weight, legend(position(@))"'
global ZS_S_clockdir_mlabpos `"scatter mpg weight in 1/5, mlabel(make) mlabposition(@)"'
global ZS_S_gridringstyle_legend `"scatter mpg price weight, legend(ring(@) position(1))"'
global ZS_S_gridringstyle_title  `"scatter mpg weight, title("TT", ring(@))"'
global ZS_S_anglestyle_mlabangle `"scatter mpg weight in 1/5, mlabel(make) mlabangle(@)"'
global ZS_S_anglestyle_msangle   `"scatter mpg weight in 1/5, msymbol(T) msize(huge) msangle(@)"'
global ZS_S_connectstyle_connect `"scatter mpg weight in 1/20, connect(@)"'
global ZS_S_horizontal_title `"scatter mpg weight, title("T", justification(@))"'

global ZS_SITES_compass2dir "text aspect"
global ZS_SITES_tb_orientstyle "text title ytitle"
global ZS_SITES_clockdir "title legend mlabpos"
global ZS_SITES_gridringstyle "legend title"
global ZS_SITES_anglestyle "mlabangle msangle"
global ZS_SITES_connectstyle "connect"
global ZS_SITES_horizontal "title"

* Each class: its syntax option names as name:minimum:canonical, in the
* class's order, then its other words as word:canonical ("-" for a word
* the class rule does not take), and the full spelling drawn for each
* canonical (canonical:spelling).
global ZS_O_compass2dir "north:1:n south:1:s east:1:e west:1:w nwest:2:nw neast:2:ne swest:2:sw seast:2:se center:1:c top:1:n bottom:1:s left:1:w right:1:e"
global ZS_X_compass2dir "N:n S:s E:e W:w NE:ne NW:nw SE:se SW:sw T:n B:s R:e L:w 0:c 1:ne 2:ne 3:e 4:se 5:se 6:s 7:sw 8:sw 9:w 10:nw 11:nw 12:n 03:e NOR:- Ne:- 3.0:- 13:- zzz:-"
global ZS_D_compass2dir "n:north ne:neast e:east se:seast s:south sw:swest w:west nw:nwest c:center"
global ZS_O_tb_orientstyle "horizontal:3:horizontal vertical:4:vertical rhorizontal:4:rhorizontal rvertical:5:rvertical"
global ZS_X_tb_orientstyle "ho:- ver:- rho:- rver:- h:- v:- Vertical:- zzz:-"
global ZS_D_tb_orientstyle "horizontal:horizontal vertical:vertical rhorizontal:rhorizontal rvertical:rvertical"
global ZS_O_clockdir "center:1:0 top:1:12 bottom:1:6 left:1:9 right:1:3"
global ZS_X_clockdir "0:0 1:1 2:2 3:3 4:4 5:5 6:6 7:7 8:8 9:9 10:10 11:11 12:12 C:- Top:- 13:- zzz:-"
global ZS_D_clockdir "0:0 1:1 2:2 3:3 4:4 5:5 6:6 7:7 8:8 9:9 10:10 11:11 12:12"
global ZS_O_gridringstyle "inside:1:0 outside:1:1"
global ZS_X_gridringstyle "I:- IN:- Out:- ix:- zzz:-"
global ZS_D_gridringstyle "0:0 1:1"
global ZS_O_anglestyle "horizontal:1:0 vertical:1:90 rhorizontal:2:180 rvertical:2:270"
global ZS_X_anglestyle "45:45 270:270 r:- V:- Vertical:- RV:- zzz:-"
global ZS_D_anglestyle "0:0 90:90 180:180 270:270 45:45"
global ZS_O_connectstyle "connected:1:direct direct:1:direct line:1:direct stairstep:1:stairstep upstairstep:1:stepstair stepstair:4:stepstair ascending:1:ascending none:1:none i:1:none"
global ZS_X_connectstyle "L:ascending J:stairstep stairstep_up:stepstair ste:- j:- N:- D:- zzz:-"
global ZS_D_connectstyle "direct:direct ascending:ascending stairstep:stairstep stepstair:stepstair none:none"
global ZS_O_horizontal "left:4:left center:6:center right:5:right"
global ZS_X_horizontal "l:- le:- r:- c:- zzz:-"
global ZS_D_horizontal "left:left center:center right:right"

* _zs_run key cmd: run one twoway command on auto; record rc, log, SVG.
capture program drop _zs_run
program define _zs_run
    version 19
    gettoken key cmd : 0
    global ZS_N = ${ZS_N} + 1
    local k ${ZS_N}
    global ZS_K_`k' "`key'"
    quietly sysuse auto, clear
    capture graph drop _all
    quietly log using "${ZS_WORK}/p`k'.log", text replace name(zsp) nomsg
    capture noisily twoway `macval(cmd)' name(g, replace)
    local rc = _rc
    quietly log close zsp
    global ZS_RC_`k' `rc'
    capture erase "${ZS_WORK}/p`k'.svg"
    if !`rc' {
        quietly graph export "${ZS_WORK}/p`k'.svg", replace name(g)
    }
    capture graph drop _all
end

* _zs_class cls: the drawings of the canonicals, then every word at every
* site.
capture program drop _zs_class
program define _zs_class
    version 19
    args cls
    foreach site of global ZS_SITES_`cls' {
        local tmpl `"${ZS_S_`cls'_`site'}"'
        foreach d of global ZS_D_`cls' {
            gettoken can spell : d, parse(":")
            local spell = substr("`spell'", 2, .)
            local cmd = subinstr(`"`tmpl'"', "@", "`spell'", 1)
            _zs_run D|`cls'|`site'|`can' `cmd'
        }
        local seen ""
        foreach o of global ZS_O_`cls' {
            tokenize "`o'", parse(":")
            local nm `1'
            local mn `3'
            local can `5'
            forvalues L = `mn'/`=strlen("`nm'")' {
                local w = substr("`nm'", 1, `L')
                if `: list w in seen' continue
                local seen `seen' `w'
                local cmd = subinstr(`"`tmpl'"', "@", "`w'", 1)
                _zs_run W|`cls'|`site'|`w'|`can' `cmd'
            }
        }
        foreach o of global ZS_X_`cls' {
            tokenize "`o'", parse(":")
            local w `1'
            local can `3'
            if "`can'" == "-" local can ""
            if `: list w in seen' continue
            local seen `seen' `w'
            local cmd = subinstr(`"`tmpl'"', "@", "`w'", 1)
            _zs_run W|`cls'|`site'|`w'|`can' `cmd'
        }
    }
end

foreach cls in compass2dir tb_orientstyle clockdir gridringstyle anglestyle connectstyle horizontal {
    _zs_class `cls'
    display as text "ZS `cls' done: ${ZS_N} probes"
}

python:
import hashlib, json, os
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("ZS_WORK")


def lines(k):
    """Every line the command printed, in order."""
    try:
        with open(os.path.join(work, "p%d.log" % k), encoding="utf-8",
                  errors="replace") as fh:
            text = fh.read()
    except OSError:
        return []
    return [ln.rstrip() for ln in text.replace("\n> ", "").splitlines()
            if ln.strip() and not ln.startswith(". ")]


def digest(k):
    svg = os.path.join(work, "p%d.svg" % k)
    if not os.path.exists(svg):
        return ""
    with open(svg, encoding="utf-8", errors="replace") as fh:
        body = [ln for ln in fh.read().splitlines() if "<desc>" not in ln]
    os.remove(svg)
    return hashlib.sha256("\n".join(body).encode("utf-8")).hexdigest()[:16]


drawn = {}
rows = []
for k in range(1, int(G("ZS_N")) + 1):
    key = G("ZS_K_%d" % k).split("|")
    rc = int(G("ZS_RC_%d" % k))
    out = lines(k)
    h = digest(k)
    try:
        os.remove(os.path.join(work, "p%d.log" % k))
    except OSError:
        pass
    if key[0] == "D":
        drawn[(key[1], key[2], key[3])] = h
        continue
    cls, site, word, can = key[1], key[2], key[3], key[4]
    notes = [ln.strip() for ln in out if ln.strip().startswith("(note:")]
    ref = drawn.get((cls, site, can), "") if can else ""
    rows.append({"class": cls, "site": site, "word": word,
                 "canonical": can,
                 "same_as_canonical": int(bool(h) and h == ref),
                 "note": "\n".join(notes), "rc": rc,
                 "lines": [ln.strip() for ln in out] if rc else []})
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
doc = {"rows": rows,
       "drawings": {"|".join(k): v for k, v in sorted(drawn.items())},
       "_meta": {"stata_version": G("ZS_VERSION"), "born_date": G("ZS_BORN"),
                 "dash_commit": commit, "extracted": G("ZS_WHEN"),
                 "source": "scripts/extract_style_words_truth.do"}}
with open(G("ZS_OUT"), "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZS_OUT"), len(rows), "rows")
end
