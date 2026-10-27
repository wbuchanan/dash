*! extract_scheme_ref_gsize_truth.do -- WP-31 section 44 (GAPS3 E11b):
*! the title size twoway draws for a #-pt gsize heading under user schemes
*! whose smaller graphsize side is 2.392 in (u11a) and the default 4 in
*! (u11b).  twoway only; the schemes are written to a fresh directory put
*! on the ado-path for this session.
*!
*! Output: test/fixtures/scheme_ref_gsize_truth.json
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_scheme_ref_gsize_truth.do
*!
*! Each record: the exported SVG's width and height (in), its viewBox and
*! the title's font-size in viewBox units (720 a inch), so the title's
*! points are font-size / 10.

clear all
set more off
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zg_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zg_bad' {
    display as error "extract_scheme_ref_gsize_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
capture confirm file `"`repo'/dash.ado"'
if _rc {
    display as error "extract_scheme_ref_gsize_truth.do: set DASH_REPO to the dash repository"
    exit 601
}
tempfile wb
local work "`wb'_zg"
capture mkdir "`work'"
quietly shell git -C "`repo'" rev-parse HEAD > "`work'/git_head.txt"
local entry_scheme "`c(scheme)'"
tempname w
file open `w' using "`work'/scheme-u11a.scheme", write text replace
file write `w' "#include s2color" _n "graphsize x 3.12" _n "graphsize y 2.392" _n "gsize heading 12-pt" _n
file close `w'
file open `w' using "`work'/scheme-u11b.scheme", write text replace
file write `w' "#include s2color" _n "gsize heading 12-pt" _n
file close `w'
adopath ++ "`work'"
sysuse auto, clear
foreach s in u11a u11b {
    capture graph drop _all
    quietly twoway scatter mpg weight, title("Tq") scheme(`s') name(zg, replace)
    quietly graph export "`work'/`s'.svg", replace name(zg)
}
set scheme `entry_scheme'
adopath - "`work'"
local stata_version = c(stata_version)
local born_date "`c(born_date)'"
local extracted "`c(current_date)'"
python:
import json, os, re
from sfi import Macro
work = Macro.getLocal("work")
out = {}
for s in ("u11a", "u11b"):
    with open(os.path.join(work, s + ".svg"), encoding="utf-8") as fh:
        txt = fh.read()
    m = re.search(r'width="([\d.]+)in" height="([\d.]+)in" viewBox="0 0 ([\d.]+) ([\d.]+)"', txt)
    f = re.search(r"font-size:([\d.]+)px[^>]*>Tq</text>", txt)
    with open(os.path.join(work, "scheme-%s.scheme" % s), encoding="utf-8") as fh:
        lines = [ln.rstrip("\n") for ln in fh]
    out[s] = {"width_in": float(m.group(1)), "height_in": float(m.group(2)),
              "viewbox": [float(m.group(3)), float(m.group(4))],
              "title_font_units": float(f.group(1)), "lines": lines}
with open(os.path.join(work, "git_head.txt")) as fh:
    commit = fh.read().strip()
out["_meta"] = {"stata_version": Macro.getLocal("stata_version"),
                "born_date": Macro.getLocal("born_date"),
                "dash_commit": commit, "extracted": Macro.getLocal("extracted"),
                "source": "scripts/extract_scheme_ref_gsize_truth.do"}
dst = os.path.join(Macro.getLocal("repo"), "test", "fixtures", "scheme_ref_gsize_truth.json")
with open(dst, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote", dst)
end
