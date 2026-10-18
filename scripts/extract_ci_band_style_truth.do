*! extract_ci_band_style_truth.do -- twoway's own style for a ci fit's
*! band and fit line, read from the graph object, written to
*! test/fixtures/ci_band_style_truth.json (read by test/test_ci_band_style.py).
*!
*! For each scheme of a tier, each option set of that tier and each ci type,
*! `twoway <type> mpg weight, scheme(<s>) nodraw <options>' (sysuse auto) is
*! drawn and these are read:
*!   .Graph.plotregion1.plot1.style.area.shadestyle.color.rgb / .opacity,
*!       .shadestyle.intensity.val (the band's fill)
*!   .Graph.plotregion1.plot1.style.area.linestyle.color.rgb / .opacity,
*!       .linestyle.width.val, .linestyle.pattern.stylename (its outline)
*!   .Graph.plotregion1.plot2.style.line.color.rgb, .width.val,
*!       .pattern.stylename (the fit line)
*! An option set is recorded once with the types it was drawn on; the
*! generator fails when the types disagree or a draw is refused.
*!
*! Run (never the GUI; the slot wrapper of scripts/stata_slot.sh):
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_ci_band_style_truth.do
*! The git commit is read from a file `shell' wrote.

clear all
set more off
set linesize 200

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zb_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zb_bad' {
    display as error "extract_ci_band_style_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zb_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zb_rc' | _rc {
    local _zb_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_ci_band_style_truth.do: `_zb_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZB_REPO "`repo'"
global ZB_SVER = c(stata_version)
global ZB_BORN "`c(born_date)'"
global ZB_DATE "`c(current_date)'"
tempfile gh
shell git -C "`repo'" rev-parse HEAD > "`gh'"
tempname fh
file open `fh' using "`gh'", read text
file read `fh' zb_commit
file close `fh'
global ZB_COMMIT "`zb_commit'"

* The option sets (name: options).
local o_Pcap "pstyle(P3)"
local o_acnone "acolor(none)"
local o_acol_alcol "alcolor(blue) acolor(red)"
local o_acol_fcol "acolor(red) fcolor(blue)"
local o_acol_lcol "acolor(red) lcolor(blue)"
local o_acolop "acolor(red%30)"
local o_acolor "acolor(red)"
local o_alcnone "alcolor(none)"
local o_alcolop "alcolor(red%30)"
local o_alcolor "alcolor(red)"
local o_alp "alpattern(dash)"
local o_alp_bad "alpattern(bogus)"
local o_alw "alwidth(thick)"
local o_alw_bad "alwidth(bogus)"
local o_alw_big "alwidth(20000)"
local o_alw_neg "alwidth(-1)"
local o_alw_num "alwidth(2)"
local o_alwnone "alwidth(none)"
local o_astyle "astyle(p2)"
local o_bogus "pstyle(bogus)"
local o_bogusc "acolor(notacolor)"
local o_ci "pstyle(ci)"
local o_ci2 "pstyle(ci2)"
local o_ci_lw "pstyle(ci) lwidth(thick)"
local o_ciplot "ciplot(rline)"
local o_clcol "clcolor(blue)"
local o_clcol_lcol "clcolor(blue) lcolor(red)"
local o_col_acol "acolor(red) color(blue)"
local o_col_alcol "color(red) alcolor(blue)"
local o_col_fcol "color(red) fcolor(blue)"
local o_col_lcol "color(red) lcolor(blue)"
local o_colnone "color(none)"
local o_colop "color(red%50)"
local o_color "color(red)"
local o_def ""
local o_fcnone "fcolor(none)"
local o_fcol_acol "fcolor(blue) acolor(red)"
local o_fcolor "fcolor(red)"
local o_fcop "fcolor(red%50)"
local o_fcop_fint "fcolor(red%50) fintensity(50)"
local o_fint0 "fintensity(0)"
local o_fint50 "fintensity(50)"
local o_fintinten30 "fintensity(inten30)"
local o_lcnone "lcolor(none)"
local o_lcol_acol "lcolor(blue) acolor(red)"
local o_lcol_alcol "alcolor(green) lcolor(blue)"
local o_lcolor "lcolor(red)"
local o_lp_alp "lpattern(dash) alpattern(solid)"
local o_lpat "lpattern(dash)"
local o_lw_alw "alwidth(vthin) lwidth(thick)"
local o_lwidth "lwidth(thick)"
local o_p1 "pstyle(p1)"
local o_p15 "pstyle(p15)"
local o_p16 "pstyle(p16)"
local o_p3 "pstyle(p3)"
local o_p3_color "pstyle(p3) color(red)"
local o_p3_fint "pstyle(p3) fintensity(100)"
local o_p3col "pstyle(p3) acolor(red)"

* The tiers: which schemes each option set is drawn under, and on which
* ci types.
local all_schemes "economist s1color s1manual s1mono s1rcolor s2color s2color8 s2gcolor s2gmanual s2manual s2mono sj stcolor stcolor_alt stgcolor stgcolor_alt stmono1 stmono2 stsj sttrans"
local t1_schemes "`all_schemes'"
local t1_types   "lfitci qfitci lpolyci fpfitci"
local t1_sets    "acolor alcolor alp alw astyle clcol colop color def fcolor fcop fint50 lcolor lwidth p1 p3 p3col"
local t2_schemes "economist s1rcolor s2color s2mono stcolor sttrans"
local t2_types   "lfitci"
local t2_sets    "ci ci2"
local t3_schemes "economist s2color sttrans"
local t3_types   "lfitci"
local t3_sets    "acol_alcol acol_fcol acolop alcnone alcolop alwnone bogus bogusc col_acol fcnone fcol_acol fint0 fintinten30 lcol_alcol lpat lw_alw p15 p16"
local t4_schemes "s2color"
local t4_types   "lfitci"
local t4_sets    "Pcap acnone acol_lcol alp_bad alw_bad alw_big alw_neg alw_num ci_lw ciplot clcol_lcol col_alcol col_fcol col_lcol colnone fcop_fint lcnone lcol_acol lp_alp p3_color p3_fint"

global ZB_REC "`c(tmpdir)'dash_ci_band_style_records.txt"
tempname rec
file open `rec' using "${ZB_REC}", write text replace
sysuse auto, clear
set graphics off
local A ".Graph.plotregion1.plot1.style.area"
local L ".Graph.plotregion1.plot2.style.line"
forvalues t = 1/4 {
    foreach s of local t`t'_schemes {
        foreach v of local t`t'_sets {
            foreach ty of local t`t'_types {
                capture twoway `ty' mpg weight, scheme(`s') nodraw `o_`v''
                local rc = _rc
                if `rc' {
                    file write `rec' "`s'|`v'|`ty'|`rc'" _n
                    continue
                }
                local r1 "``A'.shadestyle.color.rgb'"
                local r2 "``A'.shadestyle.color.opacity'"
                local r3 "``A'.shadestyle.intensity.val'"
                local r4 "``A'.linestyle.color.rgb'"
                local r5 "``A'.linestyle.color.opacity'"
                local r6 "``A'.linestyle.width.val'"
                local r7 "``A'.linestyle.pattern.stylename'"
                local r8 "``L'.color.rgb'"
                local r9 "``L'.width.val'"
                local r10 "``L'.pattern.stylename'"
                file write `rec' "`s'|`v'|`ty'|0|`r1'|`r2'|`r3'|`r4'|`r5'|`r6'|`r7'|`r8'|`r9'|`r10'" _n
            }
        }
    }
}
file close `rec'
* Drawn (not nodraw): which alwidth() values twoway refuses.
local refused ""
foreach w in -1 20000 10000 0 {
    capture twoway lfitci mpg weight, alwidth(`w')
    local refused "`refused' alwidth(`w'):`=_rc'"
}
global ZB_REFUSED "`refused'"
local opts_all ""
forvalues t = 1/4 {
    foreach v of local t`t'_sets {
        global ZB_O_`v' `"`o_`v''"'
        local opts_all "`opts_all' `v'"
    }
}
global ZB_SETS "`opts_all'"

python:
import json, os
from sfi import Macro
G = Macro.getGlobal
def hexrgb(s):
    r, g, b = (int(x) for x in s.split())
    return "#%02x%02x%02x" % (r, g, b)
cases, bad = {}, []
seen = {}
with open(G("ZB_REC"), encoding="utf-8") as fh:
    for line in fh.read().splitlines():
        f = line.split("|")
        s, v, ty, rc = f[0], f[1], f[2], int(f[3])
        if rc:
            bad.append("%s %s %s: r(%d)" % (s, v, ty, rc))
            continue
        row = {"fill_rgb": hexrgb(f[4]), "fill_opacity": float(f[5]),
               "fill_intensity": float(f[6]), "outline_rgb": hexrgb(f[7]),
               "outline_opacity": float(f[8]), "outline_width": float(f[9]),
               "outline_pattern": f[10], "fit_rgb": hexrgb(f[11]),
               "fit_width": float(f[12]), "fit_pattern": f[13]}
        key = (s, v)
        if key in seen:
            if seen[key] != row:
                bad.append("%s %s: %s differs from %s" % (s, v, ty, cases[s][v]["types"]))
                continue
            cases[s][v]["types"].append(ty)
        else:
            seen[key] = row
            cases.setdefault(s, {})[v] = dict(row, types=[ty])
for s in cases:
    for v in cases[s]:
        cases[s][v]["types"].sort()
if bad:
    raise SystemExit("extract_ci_band_style_truth: " + "; ".join(bad[:10]))
out = {
    "_meta": {
        "stata_version": G("ZB_SVER"), "born_date": G("ZB_BORN"),
        "dash_commit": G("ZB_COMMIT").strip(), "extracted": G("ZB_DATE"),
        "source": "scripts/extract_ci_band_style_truth.do",
        "measured": "batch, `sysuse auto', `twoway <type> mpg weight, scheme(<s>) nodraw <options>'",
        "read_from": ".Graph.plotregion1.plot1.style.area (the band: shadestyle.color.rgb/.opacity, shadestyle.intensity.val, linestyle.color.rgb/.opacity, linestyle.width.val, linestyle.pattern.stylename) and .Graph.plotregion1.plot2.style.line (the fit line)",
        "refused": {w.rsplit(":", 1)[0]: int(w.rsplit(":", 1)[1])
                    for w in G("ZB_REFUSED").split()},
        "svg": ("by hand, 24sep2026, not rerun by this generator: graph "
                "export .svg of the same graphs: the band's fill is the "
                "colour blended towards white by its intensity (red at "
                "fintensity(50) is #FF8080) at fill-opacity = the colour's "
                "opacity, and its outline is a closed path (Z) round the "
                "band, ends included; acolor(none) draws no band; "
                "alwidth(none) strokes 0.00"),
        "types": "every row was measured on each type in `types' and was identical across them",
    },
    "cases": cases,
    "options": {v: G("ZB_O_" + v) for v in G("ZB_SETS").split()},
}
path = os.path.join(G("ZB_REPO"), "test", "fixtures", "ci_band_style_truth.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote " + path)
end
