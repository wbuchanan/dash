*! extract_user_scheme_rule_truth.do -- WP-31 section 44 (GAPS3 C8c):
*! the default colorvar() colours twoway draws under user schemes that
*! include a shipped one and set (or inherit) zyx2rule contour, color
*! contour_begin/contour_end or a shadestyle contour_begin directive.
*! twoway only.  User schemes and one style file are written to a fresh
*! directory put on the ado-path for this session (adopath ++).
*!
*! Output: test/fixtures/user_scheme_rule_truth.json
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_user_scheme_rule_truth.do
*!
*! PROBES (sysuse auto): for each scheme U<k>,
*!   `twoway scatter mpg weight, colorvar(rep78) colorlevels(2)': the
*!   key's two swatch fills (highest level first), and colordiscrete's
*!   five, read from the exported SVG.

clear all
set more off
set linesize 200
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zu_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zu_bad' {
    display as error "extract_user_scheme_rule_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
capture confirm file `"`repo'/dash.ado"'
if _rc {
    display as error "extract_user_scheme_rule_truth.do: set DASH_REPO to the dash repository"
    exit 601
}
global ZU_OUT "`repo'/test/fixtures/user_scheme_rule_truth.json"
tempfile wb
local work "`wb'_zu"
capture mkdir "`work'"
capture mkdir "`work'/style"
global ZU_WORK "`work'"
quietly shell git -C "`repo'" rev-parse HEAD > "`work'/git_head.txt"
global ZU_VERSION "`c(stata_version)'"
global ZU_BORN "`c(born_date)'"
global ZU_WHEN "`c(current_date)'"
local entry_scheme "`c(scheme)'"

tempname w
foreach p in "scheme-uc1.scheme|#include s2color;zyx2rule contour intensity;color contour_begin green;color contour_end orange" ///
    "scheme-uc2.scheme|#include s2color;color contour_begin green;color contour_end orange" ///
    "scheme-uc3.scheme|#include s1mono" ///
    "scheme-uc4.scheme|#include s2color;shadestyle contour_begin u44s" ///
    "scheme-uc5.scheme|#include economist" ///
    "scheme-uc6.scheme|#include s2color;zyx2rule contour linear;color contour_begin navy;color contour_end gold" ///
    "style/shadestyle-u44s.style|set color red;set intensity inten50" {
    gettoken f body : p, parse("|")
    local body = substr(`"`body'"', 2, .)
    file open `w' using "`work'/`f'", write text replace
    while `"`body'"' != "" {
        gettoken ln body : body, parse(";")
        if `"`ln'"' != ";" file write `w' `"`ln'"' _n
    }
    file close `w'
}
adopath ++ "`work'"

capture program drop _zu_run
program define _zu_run
    gettoken key 0 : 0
    quietly sysuse auto, clear
    capture graph drop _all
    capture noisily `0' name(zu, replace)
    global ZU_RC_`key' = _rc
    if !_rc quietly graph export "${ZU_WORK}/`key'.svg", replace name(zu)
    global ZU_KEYS "${ZU_KEYS} `key'"
end
global ZU_KEYS ""
foreach s in uc1 uc2 uc3 uc4 uc5 uc6 {
    _zu_run S2_`s' twoway scatter mpg weight, colorvar(rep78) colorlevels(2) scheme(`s')
    _zu_run S5_`s' twoway scatter mpg weight, colorvar(rep78) colordiscrete scheme(`s')
}
set scheme `entry_scheme'

python:
import json, os, re
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("ZU_WORK")
_ATTR = re.compile(r'([\w:-]+)="([^"]*)"')
_EL = re.compile(r"<(circle|rect|path|use|polygon)\b([^>]*)/?>")
_TEXT = re.compile(r'<text x="([\d.]+)" y="([\d.]+)"[^>]*>([^<]*)</text>')
_XT = "Weight (lbs.)</text>"


def style(a):
    out = {}
    for part in a.get("style", "").split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip()] = v.strip().lower()
    return out


def read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        txt = fh.read()
    os.remove(path)
    return txt


def log_lines(key):
    p = os.path.join(work, key + ".log")
    with open(p, encoding="utf-8", errors="replace") as fh:
        lines = [ln.rstrip() for ln in fh
                 if ln.strip() and not ln.lstrip().startswith((".", "> "))
                 and "log:" not in ln and "log type:" not in ln
                 and "opened on:" not in ln and "closed on:" not in ln
                 and "name:" not in ln and not ln.startswith("---")
                 and ln.strip() != "{p_end}"]
    os.remove(p)
    return lines


def key_of(txt):
    """The key drawn after the x title: swatches in document order."""
    if _XT not in txt:
        return None
    head, tail = txt.split(_XT, 1)
    sw = []
    kind = None
    frame = None
    for m in _EL.finditer(tail):
        el, a = m.group(1), dict(_ATTR.findall(m.group(2)))
        st = style(a)
        f = st.get("fill")
        if not f or f == "none":
            continue
        if el == "rect":
            frame = f
            continue
        sw.append({"fill": f, "opacity": float(st["fill-opacity"])
                   if "fill-opacity" in st else None})
        kind = "bar" if el in ("use", "path") else "marker"
    texts = [s for _x, _y, s in _TEXT.findall(tail)]
    pos = [(float(x), float(y)) for x, y, _s in _TEXT.findall(tail)]
    return {"fills": [s["fill"] for s in sw],
            "opacities": [s["opacity"] for s in sw],
            "swatch": kind, "texts": texts, "frame": frame,
            "text_pos": pos}



out = {"schemes": {}}
for key in G("ZU_KEYS").split():
    rec = {"rc": int(G("ZU_RC_" + key))}
    svg = os.path.join(work, key + ".svg")
    if os.path.exists(svg):
        rec["key"] = key_of(read(svg))
    out["schemes"].setdefault(key[3:], {})[key[:2]] = rec
for s in out["schemes"]:
    with open(os.path.join(work, "scheme-%s.scheme" % s), encoding="utf-8") as fh:
        out["schemes"][s]["lines"] = [ln.rstrip("\n") for ln in fh]
with open(os.path.join(work, "git_head.txt")) as fh:
    commit = fh.read().strip()
out["_meta"] = {"stata_version": G("ZU_VERSION"), "born_date": G("ZU_BORN"),
                "dash_commit": commit, "extracted": G("ZU_WHEN"),
                "source": "scripts/extract_user_scheme_rule_truth.do"}
with open(G("ZU_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote", G("ZU_OUT"))
end
adopath - "`work'"
